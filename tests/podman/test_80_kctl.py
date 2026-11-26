import json
import re
import shlex

import pytest

BREW = "/home/linuxbrew/.linuxbrew/bin/brew"
FACTORY_REF = "/sysroot/ostree/repo/refs/heads/kuubik/factory"
CERT = "/usr/share/kuubik/secureboot/kuubik.der"


def _status(*deployments: dict) -> str:
    """rpm-ostree status --json output, shell quoted"""
    return shlex.quote(json.dumps({"deployments": list(deployments)}))


def _deployment(id: str, version: str, booted: bool = False, staged: bool = False) -> dict:
    """one rpm-ostree deployment"""
    return {"id": id, "version": version, "checksum": f"{id}0000000000", "booted": booted, "staged": staged}


def test_kctl_help_and_unknown_command(run):
    run("kctl help")
    result = run("kctl no-such-command", check=False)
    assert result.returncode == 1, f"unknown command exited {result.returncode}"


# upgrade


def _upgrade_stubs(stubs, rpm_ostree_rc: int = 0, flatpak_rc: int = 0) -> None:
    """rpm-ostree, flatpak and an installed brew, exiting with the given codes"""
    stubs.add("rpm-ostree", f"exit {rpm_ostree_rc}")
    stubs.add("flatpak", f"exit {flatpak_rc}")
    stubs.add("brew", path=BREW)


def test_kctl_upgrade_can_be_declined(stubs):
    _upgrade_stubs(stubs)
    result = stubs.run("kctl upgrade", input="n\n")
    assert "Aborted." in result.stdout, f"unexpected output: {result.stdout}"
    assert stubs.calls() == []


def test_kctl_upgrade_updates_everything(stubs):
    _upgrade_stubs(stubs)
    # enter takes the default yes
    result = stubs.run("kctl upgrade", input="\n")
    assert result.returncode == 0, result.stderr
    assert stubs.calls() == [
        "rpm-ostree upgrade",
        "flatpak update -y",
        "brew update",
        "brew upgrade",
    ]
    assert "Reboot to apply" in result.stdout


def test_kctl_upgrade_stops_when_image_update_fails(stubs):
    _upgrade_stubs(stubs, rpm_ostree_rc=1)
    result = stubs.run("kctl upgrade", input="y\n")
    assert result.returncode == 1
    assert stubs.calls() == ["rpm-ostree upgrade"]


def test_kctl_upgrade_continues_when_flatpak_fails(stubs):
    _upgrade_stubs(stubs, flatpak_rc=1)
    result = stubs.run("kctl upgrade", input="y\n")
    assert result.returncode == 0, result.stderr
    assert "brew upgrade" in stubs.calls()
    assert "flatpak update failed" in result.stderr


# rollback

BOOTED = _deployment("a", "20261120.0", booted=True)
PREVIOUS = _deployment("b", "20261101.0")
STAGED = _deployment("s", "20261125.0", staged=True)


def _rollback_stubs(stubs, tmp_path, before: str, after: str | None = None) -> None:
    """rpm-ostree status before and after cleanup -p, ostree with a factory version"""
    # after rpm-ostree cleanup -p the staged deployment is gone
    cleaned = tmp_path / "cleaned"
    stubs.add(
        "rpm-ostree",
        f'case "$1" in\n'
        f'status) if [ -e {cleaned} ]; then echo {after or before}; else echo {before}; fi ;;\n'
        f"cleanup) touch {cleaned} ;;\n"
        f"esac",
    )
    stubs.add("ostree", "[ \"$1\" != show ] || echo \"'20261001.0'\"")


def _menu(stdout: str) -> list[str]:
    """numbered menu entries kctl rollback printed"""
    return [line.strip() for line in stdout.splitlines() if re.match(r"\s*\d+\) ", line)]


def test_kctl_rollback_lists_boot_menu(stubs, tmp_path):
    _rollback_stubs(stubs, tmp_path, _status(BOOTED, PREVIOUS))
    result = stubs.run("kctl rollback", input="q\n")
    assert result.returncode == 0, result.stderr
    assert _menu(result.stdout) == ["1) 20261120.0  running now", "2) 20261101.0"]
    assert "Factory image" not in result.stdout
    assert "Aborted." in result.stdout


@pytest.mark.parametrize("reply", ["q", "", "0", "3", "abc"])
def test_kctl_rollback_invalid_pick_aborts(stubs, tmp_path, reply):
    _rollback_stubs(stubs, tmp_path, _status(BOOTED, PREVIOUS))
    result = stubs.run("kctl rollback", input=f"{reply}\n")
    assert result.returncode == 0 and "Aborted." in result.stdout, result.stdout
    assert not any(call.startswith("ostree admin") for call in stubs.calls())


def test_kctl_rollback_to_default_is_noop(stubs, tmp_path):
    _rollback_stubs(stubs, tmp_path, _status(BOOTED, PREVIOUS))
    result = stubs.run("kctl rollback", input="1\n")
    assert "20261120.0 already boots by default." in result.stdout, result.stdout
    assert not any(call.startswith("ostree admin") for call in stubs.calls())


def test_kctl_rollback_can_be_declined(stubs, tmp_path):
    _rollback_stubs(stubs, tmp_path, _status(BOOTED, PREVIOUS))
    result = stubs.run("kctl rollback", input="2\nn\n")
    assert "Aborted." in result.stdout, result.stdout
    assert not any(call.startswith("ostree admin") for call in stubs.calls())


def test_kctl_rollback_sets_previous_default(stubs, tmp_path):
    _rollback_stubs(stubs, tmp_path, _status(BOOTED, PREVIOUS))
    result = stubs.run("kctl rollback", input="2\ny\n")
    assert result.returncode == 0, result.stderr
    assert "ostree admin set-default 1" in stubs.calls()
    assert "rpm-ostree cleanup -p" not in stubs.calls()
    assert "Done. Reboot to start 20261101.0." in result.stdout


def test_kctl_rollback_discards_staged_update(stubs, tmp_path):
    # the staged update is no boot menu entry, and would boot next unless discarded
    _rollback_stubs(stubs, tmp_path, _status(STAGED, BOOTED, PREVIOUS), _status(BOOTED, PREVIOUS))
    result = stubs.run("kctl rollback", input="1\ny\n")
    assert result.returncode == 0, result.stderr
    assert _menu(result.stdout) == ["1) 20261120.0  running now", "2) 20261101.0"]
    calls = [call for call in stubs.calls() if not call.startswith("rpm-ostree status")]
    # the index is looked up again after cleanup, the staged entry no longer shifts it
    assert calls == ["rpm-ostree cleanup -p", "ostree admin set-default 0"], calls


def test_kctl_rollback_factory_image_not_available_yet(stubs, tmp_path):
    _rollback_stubs(stubs, tmp_path, _status(BOOTED, PREVIOUS))
    stubs.touch(FACTORY_REF)
    result = stubs.run("kctl rollback", input="3\n")
    assert "3) 20261001.0" in _menu(result.stdout), result.stdout
    assert result.returncode == 1
    assert "not available yet" in result.stdout
    assert not any(call.startswith("ostree admin") for call in stubs.calls())


# overrides


def _overrides_stubs(stubs, deployment: dict, config_diff: str) -> None:
    """booted deployment status and /etc config-diff"""
    stubs.add("rpm-ostree", f"echo {_status(deployment)}")
    stubs.add("ostree", f"printf %s {shlex.quote(config_diff)}")


def test_kctl_overrides_lists_local_changes(stubs):
    deployment = {
        "version": "20261120.0",
        "requested-packages": ["htop"],
        "requested-base-removals": ["firefox"],
        "base-remote-replacements": {"repo:fedora": ["mesa-dri-drivers"]},
        "unlocked": "development",
        "regenerate-initramfs": True,
        "initramfs-args": ["--add", "foo"],
        "initramfs-etc": ["/etc/crypttab"],
    }
    # passwd and ssh host keys differ on every install and are filtered
    config_diff = (
        "M    passwd\nM    containers/policy.json\nA    foo.conf\nD    bar.conf\nA    ssh/ssh_host_rsa_key\n"
    )
    _overrides_stubs(stubs, deployment, config_diff)
    result = stubs.run("kctl overrides")
    assert result.returncode == 0, result.stderr
    expected = ["Local changes on top of 20261120.0:"] + [
        f"  {kind:<10} {item}"
        for kind, item in [
            ("layered", "htop"),
            ("removed", "firefox"),
            ("replaced", "mesa-dri-drivers"),
            ("unlocked", "/usr (development)"),
            ("initramfs", "regenerated locally --add foo"),
            ("initramfs", "includes /etc/crypttab"),
            ("modified", "/etc/containers/policy.json"),
            ("added", "/etc/foo.conf"),
            ("deleted", "/etc/bar.conf"),
        ]
    ]
    assert result.stdout.splitlines() == expected, result.stdout


def test_kctl_overrides_clean_install(stubs):
    _overrides_stubs(stubs, {"version": "20261120.0"}, "M    passwd\nA    machine-id\nM    hostname\n")
    result = stubs.run("kctl overrides")
    assert result.stdout.strip() == "No local changes on top of the system image.", result.stdout


# notify and secure boot


def test_kctl_disable_update_notify(stubs):
    stubs.add("systemctl")
    result = stubs.run("kctl disable-update-notify")
    assert result.returncode == 0, result.stderr
    assert stubs.calls() == ["systemctl --user mask --now kctl-update-notify.timer"]


def test_kctl_enroll_secure_boot_key(stubs, run):
    stubs.add("mokutil")
    result = stubs.run("kctl enroll-secure-boot-key")
    assert result.returncode == 0, result.stderr
    assert stubs.calls() == [f"mokutil --import {CERT}"]
    run(f"test -s {CERT}")
