import subprocess

# copied in by tests/podman.Containerfile, so new removals are covered without touching this file
DEBLOAT_SCRIPT = "/tests/data/30-debloat.sh"

REMOVED_LAUNCHERS = [
    "/usr/share/applications/org.kde.kinfocenter.desktop",
    "/usr/share/applications/remote-viewer.desktop",
]


def _removed_packages() -> list[str]:
    """packages_to_remove from 30-debloat.sh, without running its dnf calls"""
    script = (
        f"eval \"$(sed -n '/^packages_to_remove=(/,/^)/p' {DEBLOAT_SCRIPT})\" && "
        'printf "%s\\n" "${packages_to_remove[@]}"'
    )
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True)
    return result.stdout.split()


def test_debloated_packages_absent(run):
    packages = _removed_packages()
    assert len(packages) > 10, f"could not read the debloat list: {packages}"
    result = run(f"rpm -q {' '.join(packages)}", check=False)
    installed = [line for line in result.stdout.splitlines() if "is not installed" not in line]
    assert installed == [], f"debloated packages are back: {installed}"


def test_hidden_launchers_removed(run):
    present = run(f"ls {' '.join(REMOVED_LAUNCHERS)}", check=False).stdout.strip()
    assert present == "", f"removed launchers are back: {present}"
