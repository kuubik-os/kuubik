import subprocess
from typing import Callable

import pytest

from defaults import SESSION_ENV, TEST_USER


pytestmark = pytest.mark.usefixtures("desktop_session")


def test_graphical_session_is_user_plasma(ssh_command):
    session = ssh_command(f"loginctl show-user {TEST_USER} -p Display --value").stdout.strip()
    assert session, f"{TEST_USER} has no graphical session"
    result = ssh_command(f"loginctl show-session {session} -p Type -p Class -p Active")
    props = dict(line.split("=", 1) for line in result.stdout.split())
    assert props == {"Type": "wayland", "Class": "user", "Active": "yes"}, (
        f"unexpected graphical session: {props}"
    )


@pytest.mark.parametrize("process", ["plasmashell", "kwin_wayland", "xdg-desktop-portal-kde"])
def test_desktop_process_running(ssh_command, wait_for, process):
    # the portal is dbus activated, so poke it first
    if process == "xdg-desktop-portal-kde":
        ssh_command(
            f"{SESSION_ENV} busctl --user call org.freedesktop.portal.Desktop "
            "/org/freedesktop/portal/desktop org.freedesktop.DBus.Peer Ping",
            check=False,
        )
    # comm is cut at 15 chars and older procps rejects longer -x names
    if len(process) > 15:
        match = f"-f '^([^ ]*/)?{process}( |$)'"
    else:
        match = f"-x {process}"
    wait_for(f"pgrep -u {TEST_USER} {match}", timeout=60)


def test_notification_delivered(ssh_command):
    # kctl-update-check relies on this
    ssh_command(f"{SESSION_ENV} notify-send --transient --expire-time=1000 kuubik-test hello")


@pytest.mark.parametrize("unit", ["pipewire.service", "pipewire-pulse.service", "wireplumber.service"])
def test_audio_stack_active(ssh_command, unit):
    result = ssh_command(f"{SESSION_ENV} systemctl --user is-active {unit}", check=False)
    assert result.stdout.strip() == "active", f"{unit}: {result.stdout.strip()}"


def test_audio_server_responds(ssh_command):
    result = ssh_command(f"{SESSION_ENV} wpctl status")
    assert "PipeWire" in result.stdout, f"unexpected wpctl status: {result.stdout}"


def test_ananicy_running(ssh_command):
    result = ssh_command("systemctl is-active ananicy-cpp", check=False)
    assert result.stdout.strip() == "active", f"ananicy-cpp: {result.stdout.strip()}"


def test_bluetooth_enabled(ssh_command):
    result = ssh_command("systemctl is-enabled bluetooth.service", check=False)
    assert result.stdout.strip() == "enabled", f"bluetooth.service: {result.stdout.strip()}"


def test_selinux_enforcing(ssh_command):
    result = ssh_command("getenforce")
    assert result.stdout.strip() == "Enforcing", f"selinux: {result.stdout.strip()}"


def test_no_selinux_denials(ssh_command):
    # ausearch exits 1 when nothing matches
    result = ssh_command("sudo ausearch -m AVC,USER_AVC -ts boot -i", check=False)
    assert "type=AVC" not in result.stdout and "type=USER_AVC" not in result.stdout, (
        f"selinux denials this boot:\n{result.stdout}"
    )


def test_no_coredumps(ssh_command):
    result = ssh_command("sudo coredumpctl list --no-legend --no-pager", check=False)
    assert result.stdout.strip() == "", f"crashes this boot:\n{result.stdout}"


# nvidia-cdi-refresh runs nvidia-smi, which always fails without GPU
NO_GPU_EXPECTED_FAILED_UNITS = ("nvidia-cdi-refresh.path", "nvidia-cdi-refresh.service")


def test_no_failed_system_units(
    ssh_command: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    result = ssh_command("systemctl --failed --no-legend --plain")
    failed = [
        line
        for line in result.stdout.splitlines()
        if line.strip() and line.split()[0] not in NO_GPU_EXPECTED_FAILED_UNITS
    ]
    details = ""
    if failed:
        units = " ".join(line.split()[0] for line in failed)
        # status exits non-zero for failed units
        details = ssh_command(
            f"systemctl status --no-pager --full {units}; "
            f"sudo journalctl -b --no-pager -o short-precise -u {units.replace(' ', ' -u ')}",
            check=False,
        ).stdout
    assert failed == [], f"unexpected failed system units: {result.stdout}\n{details}"


# nvidia-settings --load-config-only fails without GPU
NO_GPU_EXPECTED_FAILED_USER_UNITS = (r"app-nvidia\x2dsettings\x2dload@autostart.service",)


def test_no_failed_user_units(
    ssh_command: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    result = ssh_command("systemctl --user --failed --no-legend --plain")
    failed = [
        line
        for line in result.stdout.splitlines()
        if line.strip() and line.split()[0] not in NO_GPU_EXPECTED_FAILED_USER_UNITS
    ]
    assert failed == [], f"unexpected failed user units: {result.stdout}"
