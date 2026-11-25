import pytest


@pytest.fixture(autouse=True)
def _nvidia_only(is_nvidia):
    if not is_nvidia:
        pytest.skip("not an nvidia flavor")


def test_nvidia_kernel_module_built(run, kernel_version):
    # akmods can exit 0 even when the kmod build failed
    result = run(f"modinfo -k {kernel_version} -F vermagic nvidia")
    assert result.stdout.startswith(kernel_version), (
        f"nvidia kmod vermagic {result.stdout!r} does not match {kernel_version}"
    )


def test_nvidia_in_initramfs(run, kernel_version):
    result = run(f"lsinitrd /usr/lib/modules/{kernel_version}/initramfs.img")
    for mod in ("nvidia.ko", "nvidia-drm.ko", "nvidia-modeset.ko"):
        assert mod in result.stdout, f"{mod} not in the initramfs"


def test_nvidia_container_toolkit(run):
    run("nvidia-ctk --version")
