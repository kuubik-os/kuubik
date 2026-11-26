import pytest

NVIDIA_FILES = [
    "/usr/lib/bootc/kargs.d/00-nvidia.toml",
    "/usr/lib/dracut/dracut.conf.d/99-nvidia.conf",
    "/usr/lib/modprobe.d/00-nouveau-blacklist.conf",
    "/usr/lib/modprobe.d/nvidia-modeset.conf",
]


@pytest.fixture
def nvidia_only(is_nvidia):
    if not is_nvidia:
        pytest.skip("not an nvidia flavor")


@pytest.fixture
def plain_only(is_nvidia):
    if is_nvidia:
        pytest.skip("nvidia flavor")


@pytest.mark.usefixtures("plain_only")
def test_plain_flavor_has_no_nvidia(run, kernel_version):
    result = run(f"modinfo -k {kernel_version} nvidia", check=False)
    assert result.returncode != 0, "nvidia kmod in the plain flavor"
    present = run(f"ls {' '.join(NVIDIA_FILES)}", check=False).stdout.strip()
    assert present == "", f"nvidia config in the plain flavor: {present}"
    assert run("rpm -q nvidia-driver", check=False).returncode != 0, "nvidia-driver installed"


@pytest.mark.usefixtures("nvidia_only")
def test_nvidia_kernel_module_built(run, kernel_version):
    # akmods can exit 0 even when the kmod build failed
    result = run(f"modinfo -k {kernel_version} -F vermagic nvidia")
    assert result.stdout.startswith(kernel_version), (
        f"nvidia kmod vermagic {result.stdout!r} does not match {kernel_version}"
    )


@pytest.mark.usefixtures("nvidia_only")
def test_nvidia_in_initramfs(run, kernel_version):
    result = run(f"lsinitrd /usr/lib/modules/{kernel_version}/initramfs.img")
    for mod in ("nvidia.ko", "nvidia-drm.ko", "nvidia-modeset.ko"):
        assert mod in result.stdout, f"{mod} not in the initramfs"


@pytest.mark.usefixtures("nvidia_only")
def test_nvidia_container_toolkit(run):
    run("nvidia-ctk --version")


@pytest.mark.usefixtures("nvidia_only")
def test_nvidia_compute_stack(run):
    run("command -v nvidia-smi")
    libs = run("ldconfig -p").stdout
    for lib in ("libcuda.so.1", "libnvidia-ml.so.1"):
        assert lib in libs, f"{lib} not in the linker cache"
    # regenerates the podman cdi spec when the driver loads
    assert run("systemctl is-enabled nvidia-cdi-refresh.path").stdout.strip() == "enabled"


@pytest.mark.usefixtures("nvidia_only")
def test_nvidia_config_shipped(run):
    run(f"ls {' '.join(NVIDIA_FILES)}")
    kargs = run("cat /usr/lib/bootc/kargs.d/00-nvidia.toml").stdout
    for karg in ("rd.driver.blacklist=nouveau", "modprobe.blacklist=nouveau", "nvidia-drm.modeset=1"):
        assert f'"{karg}"' in kargs, f"{karg} missing from kargs: {kargs}"
    run("grep -qx 'blacklist nouveau' /usr/lib/modprobe.d/00-nouveau-blacklist.conf")
    # the nvidia packages ship their own 99-nvidia.conf, ours has to win
    run("grep -q 'force_drivers.*nvidia_drm' /usr/lib/dracut/dracut.conf.d/99-nvidia.conf")


@pytest.mark.usefixtures("nvidia_only")
def test_nvidia_vulkan_icd(run):
    run("ls /usr/share/vulkan/icd.d/nvidia_icd.x86_64.json")


@pytest.mark.usefixtures("nvidia_only")
def test_containers_can_use_gpu_devices(run):
    # without it selinux blocks /dev/nvidia* in containers
    result = run("semanage boolean -l | grep '^container_use_devices '")
    assert "(on" in result.stdout, result.stdout


@pytest.mark.usefixtures("nvidia_only")
def test_nvidia_build_leftovers_removed(run):
    result = run("rpm -q akmods akmod-nvidia", check=False)
    installed = [line for line in result.stdout.splitlines() if "is not installed" not in line]
    assert installed == [], f"build only packages installed: {installed}"
    # akmods signs with this key, it is the secure boot private key
    assert run("find /etc/pki/akmods -type f", check=False).stdout.strip() == ""
    for path in (
        "/etc/xdg/autostart/nvidia-settings-load.desktop",
        "/usr/share/applications/nvtop.desktop",
    ):
        assert run(f"test -e {path}", check=False).returncode != 0, f"{path} not removed"
