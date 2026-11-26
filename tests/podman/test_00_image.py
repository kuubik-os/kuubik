import re

import pytest

# build scripts add third party repos and must remove them again. fedora's own disabled
# third party repos (google-chrome, rpmfusion steam/nvidia) are fine
ALLOWED_REPO_PREFIXES = ("fedora", "updates")

# elsewhere broken links are expected: runtime paths, and the kernel devel tree 90-finalize.sh removes
BIN_DIRS = "/usr/bin /usr/sbin /usr/libexec"

OUR_UNITS = {
    "system": [
        "kuubik-factory-image.service",
        "brew-setup.service",
        "flatpak-add-fedora-repos.service",
    ],
    "user": ["kctl-update-notify.service", "kctl-update-notify.timer"],
}


def test_only_fedora_repos_enabled(run):
    result = run("dnf5 repolist --enabled 2>/dev/null | awk 'NR > 1 {print $1}'")
    repos = result.stdout.split()
    assert repos, "no repos listed, the check is broken"
    leftover = [repo for repo in repos if not repo.startswith(ALLOWED_REPO_PREFIXES)]
    assert leftover == [], f"third party repos enabled in the image: {leftover}"


def test_rpm_dependencies_intact(run):
    # catches debloat removing something an installed package still needs
    result = run("dnf5 check", check=False)
    assert result.returncode == 0 and result.stdout.strip() == "", result.stdout + result.stderr


def test_no_broken_symlinks_in_bin_dirs(run):
    result = run(f"find {BIN_DIRS} -xtype l")
    assert result.stdout.strip() == "", f"broken symlinks:\n{result.stdout}"


def test_visible_launchers_have_their_binary(run):
    # debloat removing a package but not its .desktop leaves a dead menu entry
    script = r"""
    for f in /usr/share/applications/*.desktop; do
        grep -qE '^(NoDisplay|Hidden)=true' "$f" && continue
        cmd=$(grep -m1 '^TryExec=' "$f" | cut -d= -f2-)
        [ -n "$cmd" ] || cmd=$(grep -m1 '^Exec=' "$f" | cut -d= -f2- | awk '{print $1}')
        cmd=${cmd//\"/}
        [ -n "$cmd" ] && [ "$cmd" != env ] || continue
        command -v "$cmd" >/dev/null || echo "$f: $cmd"
    done
    """
    result = run(script)
    assert result.stdout.strip() == "", f"launchers without their binary:\n{result.stdout}"


@pytest.mark.parametrize("scope", ["system", "user"])
def test_our_units_verify(run, tmp_path, scope):
    units = " ".join(f"/usr/lib/systemd/{scope}/{unit}" for unit in OUR_UNITS[scope])
    flag = "--user" if scope == "user" else ""
    # systemd-analyze --user needs a runtime dir, containers have none
    result = run(
        f"XDG_RUNTIME_DIR={tmp_path} systemd-analyze verify --man=no {flag} {units}",
        check=False,
    )
    # warnings about units pulled in as dependencies are not ours to fix
    ours = [line for line in result.stderr.splitlines() if any(u in line for u in OUR_UNITS[scope])]
    assert result.returncode == 0 and ours == [], result.stderr


def test_os_release_version_matches_image(run, image_version):
    if not image_version:
        pytest.skip("built without IMAGE_VERSION")
    assert re.fullmatch(r"\d{8}\.\d+", image_version), f"bad IMAGE_VERSION {image_version!r}"
    release = run("cat /usr/lib/os-release").stdout
    for line in (
        f'VERSION="{image_version} (kuubik)"',
        f'PRETTY_NAME="kuubik Linux {image_version}"',
        f"OSTREE_VERSION='{image_version}'",
    ):
        assert line in release.splitlines(), f"{line} missing from os-release:\n{release}"


def test_os_release_identifies_fedora(run, fedora_version):
    # bootc, dnf and toolbox key off these, kuubik only rebrands VERSION and PRETTY_NAME
    release = run("cat /usr/lib/os-release").stdout.splitlines()
    assert "ID=fedora" in release and "VARIANT_ID=kinoite" in release, release
    if fedora_version:
        assert f"VERSION_ID={fedora_version}" in release, release


def test_no_private_keys_left(run):
    # the secure boot key is mounted as a build secret and copied for akmods, it must not ship
    result = run(
        "find /etc /usr/share/kuubik /usr/lib/modules /root -type f -size -64k 2>/dev/null "
        "| xargs -r grep -lE -- '-----BEGIN ([A-Z]+ )?PRIVATE KEY-----'",
        check=False,
    )
    assert result.stdout.strip() == "", f"private keys in the image:\n{result.stdout}"


def test_build_leftovers_cleaned(run):
    # pytest's own tmp_path dirs live in /tmp too
    leftover = run("ls -A /tmp | grep -v '^pytest-of-'", check=False).stdout.strip()
    assert leftover == "", f"/tmp not empty: {leftover}"
    run("! rpm -q sbsigntools")
    result = run("ls /usr/lib/kernel/install.d/05-rpmostree.install "
                 "/usr/lib/kernel/install.d/50-dracut.install", check=False)
    assert result.stdout.strip() == "", f"stubbed kernel-install hooks left: {result.stdout}"
