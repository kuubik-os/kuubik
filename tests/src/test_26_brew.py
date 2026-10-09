import time

from defaults import TEST_USER

BREW = "/home/linuxbrew/.linuxbrew/bin/brew"


def _wait_for(ssh_command, command, timeout=60, interval=2):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = ssh_command(command, check=False)
        if last.returncode == 0:
            return last
        time.sleep(interval)
    raise AssertionError(
        f"condition never became true within {timeout}s: {command}\n"
        f"last stdout: {last.stdout if last else ''}\n"
        f"last stderr: {last.stderr if last else ''}"
    )


# brew-setup.service unpacks a ~150MB tarball on first boot; SSH can become
# reachable before it finishes, so wait for its completion marker rather than
# assuming it's already done.
def test_brew_installed_and_owned_by_test_user(ssh_command):
    _wait_for(ssh_command, "test -f /etc/.linuxbrew")

    ssh_command(f"test -x {BREW}")

    result = ssh_command("stat -c %U /home/linuxbrew/.linuxbrew")
    assert result.stdout.strip() == TEST_USER, (
        f"/home/linuxbrew/.linuxbrew expected to be owned by {TEST_USER}, "
        f"actual owner: {result.stdout.strip()}"
    )


def test_brew_package_install_run_uninstall(ssh_command):
    _wait_for(ssh_command, "test -f /etc/.linuxbrew")

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
