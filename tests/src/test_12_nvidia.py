import pytest

# same signal 00-base.sh itself uses to detect the nvidia flavor at build time
NVIDIA_FLAVOR_MARKER = "/usr/lib/dracut/dracut.conf.d/99-nvidia.conf"


def _is_nvidia_flavor(ssh_command):
    result = ssh_command(f"test -f {NVIDIA_FLAVOR_MARKER}", check=False)
    return result.returncode == 0


# only asserts anything on a kuubik-nvidia VM; on plain kuubik it skips
# outright. We can't check the driver actually works this way -- the VM these
# tests run against has no GPU passthrough (VM_GPU=FALSE) -- so this only
# confirms the kmod was actually built for the running kernel.
def test_nvidia_kernel_module_built(ssh_command):
    if not _is_nvidia_flavor(ssh_command):
        pytest.skip(f"not nvidia flavor -- {NVIDIA_FLAVOR_MARKER} not present")

    result = ssh_command("uname -r")
    kernel_version = result.stdout.strip()

    result = ssh_command(f"find /usr/lib/modules/{kernel_version} -name 'nvidia.ko*'")
    assert result.stdout.strip() != "", (
        f"no nvidia.ko* found under /usr/lib/modules/{kernel_version} -- "
        "akmods can exit 0 even when the kmod build actually failed, see AGENTS.md"
    )
