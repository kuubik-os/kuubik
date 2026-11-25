import pytest

# the VM has no GPU (VM_GPU=N), so this only proves the boot config is in place.
# the driver stack itself is checked by the podman tests


@pytest.fixture(autouse=True)
def _nvidia_only(is_nvidia):
    if not is_nvidia:
        pytest.skip("not an nvidia flavor")


def test_nvidia_kargs_applied(ssh_command):
    cmdline = ssh_command("cat /proc/cmdline").stdout.split()
    for karg in ("rd.driver.blacklist=nouveau", "modprobe.blacklist=nouveau", "nvidia-drm.modeset=1"):
        assert karg in cmdline, f"{karg} missing from /proc/cmdline: {cmdline}"
