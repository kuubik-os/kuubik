import pytest

# the VM has no GPU (VM_GPU=N), so these only prove the driver stack is in
# place for the running kernel, not that it drives a card


@pytest.fixture(autouse=True)
def _nvidia_only(is_nvidia):
    if not is_nvidia:
        pytest.skip("not an nvidia flavor")


def test_nvidia_kernel_module_built(ssh_command):
    # akmods can exit 0 even when the kmod build failed
    result = ssh_command("modinfo -k $(uname -r) -F vermagic nvidia")
    kernel_version = ssh_command("uname -r").stdout.strip()
    assert result.stdout.startswith(kernel_version), (
        f"nvidia kmod vermagic {result.stdout!r} does not match {kernel_version}"
    )


def test_nvidia_kargs_applied(ssh_command):
    cmdline = ssh_command("cat /proc/cmdline").stdout.split()
    for karg in ("rd.driver.blacklist=nouveau", "modprobe.blacklist=nouveau", "nvidia-drm.modeset=1"):
        assert karg in cmdline, f"{karg} missing from /proc/cmdline: {cmdline}"


def test_nvidia_in_initramfs(ssh_command):
    result = ssh_command("sudo lsinitrd /usr/lib/modules/$(uname -r)/initramfs.img")
    for mod in ("nvidia.ko", "nvidia-drm.ko", "nvidia-modeset.ko"):
        assert mod in result.stdout, f"{mod} not in the initramfs"


def test_nvidia_container_toolkit(ssh_command):
    ssh_command("nvidia-ctk --version")
