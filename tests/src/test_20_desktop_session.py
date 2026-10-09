import subprocess
from typing import Callable


def test_graphical_session_exists(ssh_command):
    result = ssh_command(
        "loginctl show-session $(loginctl | awk '/seat0/ {print $1}') -p Type"
    )
    assert "Type=wayland" in result.stdout, (
        f"No active graphical session found: {result.stdout}"
    )


def test_ananicy_running(ssh_command):
    result = ssh_command("systemctl is-active ananicy-cpp")
    actual_state = result.stdout.strip()
    assert actual_state == "active", (
        f"ananicy-cpp expected to be active, actual state: {actual_state}. Full response: {result.stdout}"
    )


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
    assert failed == [], f"unexpected failed system units: {result.stdout}"


def test_no_failed_user_units(ssh_command):
    result = ssh_command("systemctl --user --failed --no-legend")
    assert result.stdout.strip() == "", (
        f"unexpected failed user units: {result.stdout}"
    )
