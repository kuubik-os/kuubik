from defaults import KERNEL_VERSION


def test_kernel(ssh_command):
    result = ssh_command("uname --kernel-release")
    assert KERNEL_VERSION in result.stdout, (
        f"{KERNEL_VERSION} kernel not used. Full response {result.stdout}"
    )
