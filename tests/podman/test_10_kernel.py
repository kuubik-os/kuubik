import shlex

import pytest

STOCK_KERNEL = [
    "kernel",
    "kernel-core",
    "kernel-modules",
    "kernel-modules-core",
    "kernel-modules-extra",
    "kernel-uki-virt",
]


def test_kernel_is_cachyos(run, kernel_version):
    assert "cachyos" in kernel_version, f"unexpected kernel {kernel_version}"
    run(f"test -s /usr/lib/modules/{kernel_version}/vmlinuz")
    result = run(f"rpm -q {' '.join(STOCK_KERNEL)}", check=False)
    installed = [line for line in result.stdout.splitlines() if "is not installed" not in line]
    assert installed == [], f"stock kernel packages installed: {installed}"


def test_kernel_packages_versionlocked(run):
    # a dnf5 upgrade in a derived image must not swap the kernel the initramfs was built for
    installed = run("rpm -qa --qf '%{name} %{evr}\\n' 'kernel-cachyos*'").stdout.splitlines()
    assert installed, "no cachyos kernel packages installed"
    locks = run("dnf5 versionlock list").stdout
    for line in installed:
        name, evr = line.split()
        assert f"Package name: {name}\nevr = {evr}" in locks, f"{name}-{evr} not versionlocked:\n{locks}"


def test_kernel_devel_removed(run):
    # only kept until 90-finalize.sh for the nvidia kmod build
    result = run("rpm -qa 'kernel-cachyos*-devel*'")
    assert result.stdout.strip() == "", f"kernel devel left installed: {result.stdout}"


# a generic initramfs has to boot any install: luks with tpm2 or fido2 unlock, btrfs or lvm, nvme or sata
INITRAMFS_DRACUT_MODULES = [
    "ostree", "crypt", "systemd-cryptsetup", "tpm2-tss", "fido2", "btrfs", "lvm", "plymouth",
]
INITRAMFS_FILES = [
    "nvme.ko", "ahci.ko", "dm-crypt.ko", "i915.ko", "amdgpu.ko",
    "kernel/x86/microcode/GenuineIntel.bin", "kernel/x86/microcode/AuthenticAMD.bin",
]


@pytest.fixture(scope="module")
def initramfs(run, kernel_version) -> tuple[list[str], str]:
    """dracut modules and file listing of the image's initramfs"""
    image = f"/usr/lib/modules/{kernel_version}/initramfs.img"
    return run(f"lsinitrd -m {image}").stdout.split(), run(f"lsinitrd {image}").stdout


@pytest.mark.parametrize("module", INITRAMFS_DRACUT_MODULES)
def test_initramfs_dracut_module(initramfs, module):
    assert module in initramfs[0], f"dracut module {module} missing from the initramfs"


@pytest.mark.parametrize("path", INITRAMFS_FILES)
def test_initramfs_file(initramfs, path):
    assert path in initramfs[1], f"{path} missing from the initramfs"


def test_bootc_kargs_parse(run):
    # bootc refuses to deploy an image with a broken kargs.d file
    script = (
        "import pathlib, tomllib\n"
        "for f in pathlib.Path('/usr/lib/bootc/kargs.d').glob('*.toml'):\n"
        "    kargs = tomllib.loads(f.read_text())['kargs']\n"
        "    assert all(isinstance(k, str) and ' ' not in k for k in kargs), f\n"
    )
    run(f"python3 -c {shlex.quote(script)}")


@pytest.mark.parametrize("module", ["ntsync", "kvm", "kvm_amd", "kvm_intel"])
def test_kernel_module_present(run, kernel_version, module):
    run(f"modinfo -k {kernel_version} -F filename {module}")


def test_ananicy_enabled(run):
    result = run("systemctl is-enabled ananicy-cpp.service")
    assert result.stdout.strip() == "enabled", result.stdout
