import pytest

from defaults import TEST_USER

BREW = "/home/linuxbrew/.linuxbrew/bin/brew"
UBLUE_TAP = "ublue-os/tap"
# only in ublue-os/tap, a single static binary
TAP_ONLY_CASK = "framework-tool"


# brew-setup.service unpacks a ~150MB tarball on first boot; SSH can become
# reachable before it finishes, so wait for its completion marker rather than
# assuming it's already done.
@pytest.fixture(autouse=True)
def _brew_ready(wait_for):
    wait_for("test -f /etc/.linuxbrew")


def test_brew_installed_and_owned_by_test_user(ssh_command):
    ssh_command(f"test -x {BREW}")

    result = ssh_command("stat -c %U /home/linuxbrew/.linuxbrew")
    assert result.stdout.strip() == TEST_USER, (
        f"/home/linuxbrew/.linuxbrew expected to be owned by {TEST_USER}, "
        f"actual owner: {result.stdout.strip()}"
    )


def test_brew_package_install_run_uninstall(ssh_command):
    pkg = "hello"

    ssh_command(f"{BREW} install {pkg}")

    result = ssh_command(f"{BREW} list --versions {pkg}")
    assert result.stdout.strip().startswith(pkg), (
        f"unexpected `brew list --versions {pkg}` output: {result.stdout}"
    )

    result = ssh_command("/home/linuxbrew/.linuxbrew/bin/hello")
    assert "Hello, world!" in result.stdout, (
        f"unexpected `hello` output: {result.stdout}"
    )

    ssh_command(f"{BREW} uninstall {pkg}")

    result = ssh_command(f"{BREW} list --versions {pkg}", check=False)
    assert result.returncode != 0, (
        f"{pkg} still listed by brew after uninstall: {result.stdout}"
    )


def test_kctl_adds_ublue_tap(ssh_command):
    ssh_command("kctl help")
    result = ssh_command(f"{BREW} tap")
    assert UBLUE_TAP in result.stdout.split(), f"{UBLUE_TAP} not tapped: {result.stdout}"


def test_brew_install_from_ublue_tap(ssh_command):
    ssh_command("kctl help")
    # unqualified name, so it only resolves through the tap kctl added
    ssh_command(f"{BREW} install --cask {TAP_ONLY_CASK}")
    try:
        result = ssh_command(f"{BREW} info --cask --json=v2 {TAP_ONLY_CASK} | jq -r '.casks[0].tap'")
        assert result.stdout.strip() == UBLUE_TAP, f"installed from {result.stdout.strip()!r}"
        ssh_command("/home/linuxbrew/.linuxbrew/bin/framework_tool --help")
    finally:
        ssh_command(f"{BREW} uninstall --cask {TAP_ONLY_CASK}", check=False)
