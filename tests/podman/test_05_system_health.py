import fnmatch
import re
from pathlib import Path

import pytest

# copied in by tests/podman.Containerfile
SYSTEM_FILES = Path("/tests/data/system_files")

# dirs where a file no package owns must be one we ship
UNOWNED_DIRS = [
    "/usr/bin",
    "/usr/libexec",
    "/usr/lib/systemd/system",
    "/usr/lib/systemd/user",
    "/usr/lib/systemd/system-preset",
    "/usr/lib/systemd/user-preset",
]
UNOWNED_ALLOWED = [
    # from ghcr.io/ublue-os/brew, see Containerfile
    "/usr/lib/systemd/system/brew-setup.service",
    # shipped unowned by the kinoite base image
    "*/fedora-*",
    "/usr/lib/systemd/system-preset/82-kinoite.preset",
    # linked by nvidia-container-toolkit's %post
    "/usr/bin/nvidia-container-toolkit",
]

# package files whose content differs from the rpm on purpose
MODIFIED_ALLOWED = {
    "/usr/lib/os-release",  # version from 90-finalize.sh
    "/usr/share/plasma/look-and-feel/org.kde.breeze.desktop/contents/layouts/org.kde.plasma.desktop-layout.js",
    "/usr/lib/dracut/dracut.conf.d/99-nvidia.conf",  # system_files/nvidia replaces the driver's
    # changed by the kinoite base image
    "/usr/lib/systemd/system-preset/81-atomic-desktop.preset",
    "/usr/lib/kernel/install.conf",
    "/usr/lib/fedora-third-party/conf.d/fedora-workstation.conf",
    "/etc/selinux/targeted/contexts/files/file_contexts.subs_dist",
}

# a new setuid binary is a security decision, review it before adding it here
SETUID_ALLOWED = {
    "/usr/bin/chage",
    "/usr/bin/chfn",
    "/usr/bin/chsh",
    "/usr/bin/fusermount3",
    "/usr/bin/gpasswd",
    "/usr/bin/grub2-set-bootflag",
    "/usr/bin/lockdev",
    "/usr/bin/mount",
    "/usr/bin/mount.nfs",
    "/usr/bin/newgrp",
    "/usr/bin/pam_timestamp_check",
    "/usr/bin/passwd",
    "/usr/bin/pkexec",
    "/usr/bin/su",
    "/usr/bin/sudo",
    "/usr/bin/umount",
    "/usr/bin/unix_chkpwd",
    "/usr/bin/userhelper",
    "/usr/bin/vmware-user-suid-wrapper",
    "/usr/lib/polkit-1/polkit-agent-helper-1",
    "/usr/libexec/dbus-1/dbus-daemon-launch-helper",
    "/usr/libexec/qemu-bridge-helper",  # vm-curator bridged networking
    "/usr/libexec/spice-gtk-x86_64/spice-client-glib-usb-acl-helper",
    "/usr/libexec/utempter/utempter",
}
SETUID_NVIDIA = {"/usr/bin/nvidia-modprobe", "/usr/libexec/Xorg.wrap"}

SELINUX_LABELS = {
    "/usr/bin/kctl": "bin_t",
    "/usr/libexec/kctl-update-check": "bin_t",
    "/usr/libexec/kuubik-factory-image": "bin_t",
    "/usr/lib/systemd/system/kuubik-factory-image.service": "systemd_unit_file_t",
    "/usr/lib/systemd/user/kctl-update-notify.timer": "systemd_unit_file_t",
    "/etc/containers/policy.json": "etc_t",
}


# services


@pytest.mark.parametrize("scope", ["", "--global"], ids=["system", "user"])
def test_presets_keep_enabled_units(run, scope):
    # anything running preset-all would otherwise turn off what the build scripts enabled
    result = run(f"systemctl {scope} preset-all --dry-run", check=False)
    removed = [line for line in (result.stdout + result.stderr).splitlines() if line.startswith("Removed")]
    assert removed == [], "units enabled without a matching preset:\n" + "\n".join(removed)


def test_boot_target_verifies(run):
    # loads every unit graphical.target pulls in, so an enabled unit whose binary is gone fails
    result = run("systemd-analyze verify --man=no graphical.target", check=False)
    assert result.returncode == 0, result.stderr


def test_no_dangling_unit_links(run):
    result = run("find /etc/systemd /usr/lib/systemd -xtype l")
    assert result.stdout.strip() == "", f"links to missing units:\n{result.stdout}"


def test_tmpfiles_and_sysusers_clean(run):
    output = run("systemd-tmpfiles --dry-run --create 2>&1; systemd-sysusers --dry-run 2>&1").stdout
    # containers have no initialized /etc/machine-id and no audit socket
    known = ("uninitialized /etc/", "unresolvable specifiers", "audit log")
    errors = [
        line
        for line in output.splitlines()
        if re.search(r"\b(failed|error|invalid)\b", line, re.IGNORECASE)
        and not any(k in line for k in known)
    ]
    assert errors == [], "\n".join(errors)


# package integrity


def test_binaries_find_their_libraries(run):
    # catches debloat removing a library something still links to
    result = run(
        "find /usr/bin /usr/libexec -type f -perm -u+x -print0 | xargs -0 -P\"$(nproc)\" -n 50 sh -c '"
        'for f; do head -c4 "$f" | grep -q ELF || continue; '
        'ldd "$f" 2>/dev/null | grep -q "not found" && echo "$f: $(ldd "$f" | grep "not found" | xargs)"; '
        "done' _",
        check=False,
    )
    assert result.stdout.strip() == "", f"missing shared libraries:\n{result.stdout}"


def test_package_files_unmodified(run, expect_signed, kernel_version):
    # a build script or system_files overwriting a file a package owns
    result = run(
        "rpm -Va --nomtime --nouser --nogroup --nomode --nordev --nolinkto 2>/dev/null"
        " | awk '$1 ~ /5/ && $2 != \"c\" {print $NF}'",
        check=False,
    )
    modified = {
        path for path in result.stdout.split() if "/__pycache__/" not in path
    } - MODIFIED_ALLOWED
    if expect_signed:
        # 90-finalize.sh sbsigns the kernel in place
        modified.discard(f"/lib/modules/{kernel_version}/vmlinuz")
    assert modified == set(), f"package files changed in the image: {sorted(modified)}"


def _shipped_files() -> set[str]:
    """paths system_files puts into the image"""
    return {
        "/" + str(path.relative_to(flavor_dir))
        for flavor_dir in SYSTEM_FILES.iterdir()
        for path in flavor_dir.rglob("*")
        if not path.is_dir()
    }


def test_unowned_files_are_ours(run):
    shipped = _shipped_files()
    assert "/usr/bin/kctl" in shipped, "system_files not copied into the test image"
    dirs = " ".join(UNOWNED_DIRS)
    candidates = run(f"find {dirs} -maxdepth 1 \\( -type f -o -type l \\)").stdout.split()
    result = run(f"rpm -qf {' '.join(candidates)}", check=False)
    unowned = [
        line.split()[1]
        for line in result.stdout.splitlines()
        if line.endswith("is not owned by any package")
    ]
    stray = [
        path
        for path in unowned
        if path not in shipped and not any(fnmatch.fnmatch(path, p) for p in UNOWNED_ALLOWED)
    ]
    assert stray == [], f"files no package or system_files ships: {stray}"


# security


def test_setuid_binaries(run, is_nvidia):
    allowed = SETUID_ALLOWED | SETUID_NVIDIA if is_nvidia else SETUID_ALLOWED
    found = set(run("find /usr -xdev -perm /6000 -type f").stdout.split())
    assert found - allowed == set(), f"new setuid/setgid binaries: {sorted(found - allowed)}"
    assert allowed - found == set(), f"gone, drop from the list: {sorted(allowed - found)}"


def test_selinux_enforcing_targeted(run):
    config = run("cat /etc/selinux/config").stdout.splitlines()
    assert "SELINUX=enforcing" in config and "SELINUXTYPE=targeted" in config, config
    run("ls /etc/selinux/targeted/policy/policy.*")


@pytest.mark.parametrize(("path", "label"), SELINUX_LABELS.items())
def test_selinux_label_of_our_files(run, path, label):
    # labels come from the policy at deploy, files in odd places get odd types
    result = run(f"matchpathcon {path}")
    assert f":{label}:" in result.stdout, result.stdout


def test_crypto_defaults(run):
    assert run("update-crypto-policies --show").stdout.strip() == "DEFAULT"
    anchors = int(run("trust list --filter=ca-anchors | grep -c 'type: certificate'").stdout)
    assert anchors > 100, f"only {anchors} ca anchors"

