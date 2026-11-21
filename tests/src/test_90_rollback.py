import json

# runs last: reboots the vm and leaves an extra deployment behind

KARG = "kuubik.test.rollback=1"


def _status(ssh_command) -> dict:
    return json.loads(ssh_command("rpm-ostree status --json").stdout)


def _booted(status: dict) -> dict:
    return next(d for d in status["deployments"] if d["booted"])


def test_kctl_rollback_boots_previous_image(ssh_command, reboot_vm):
    original = _booted(_status(ssh_command))

    # a karg change makes a second deployment of the same image without needing a registry
    ssh_command(f"sudo rpm-ostree kargs --append={KARG}")
    reboot_vm()
    assert KARG in ssh_command("cat /proc/cmdline").stdout.split()
    status = _status(ssh_command)
    assert _booted(status)["id"] != original["id"]
    assert [d["id"] for d in status["deployments"]][1] == original["id"]

    result = ssh_command("printf '2\\ny\\n' | kctl rollback")
    assert "Done. Reboot" in result.stdout, f"unexpected output:\n{result.stdout}"
    assert _status(ssh_command)["deployments"][0]["id"] == original["id"]

    reboot_vm()
    assert KARG not in ssh_command("cat /proc/cmdline").stdout.split()
    assert _booted(_status(ssh_command))["id"] == original["id"]
    factory = ssh_command(
        "ostree rev-parse --repo=/sysroot/ostree/repo kuubik/factory"
    ).stdout.strip()
    assert factory == original["checksum"], "factory ref changed across deployments"
