import pytest

from defaults import TEST_USER

BREW = "/home/linuxbrew/.linuxbrew/bin/brew"


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
