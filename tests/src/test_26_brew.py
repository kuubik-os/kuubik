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


def test_brew_runs(ssh_command):
    _wait_for(ssh_command, "test -f /etc/.linuxbrew")

    result = ssh_command(f"{BREW} --version")
    assert "Homebrew" in result.stdout, (
        f"unexpected `brew --version` output: {result.stdout}"
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


def test_brew_service_start_listens_stop_uninstall(ssh_command):
    _wait_for(ssh_command, "test -f /etc/.linuxbrew")

    pkg = "syncthing"
    port = 8384  # syncthing's default web GUI port

    ssh_command(f"{BREW} install {pkg}")

    ssh_command(f"{BREW} services start {pkg}")
    _wait_for(
        ssh_command, f"{BREW} services list | grep -E '^{pkg}[[:space:]]+started'"
    )
    _wait_for(ssh_command, f"ss -ltn | grep -q ':{port} '")

    ssh_command(f"{BREW} services stop {pkg}")
    _wait_for(ssh_command, f"! ss -ltn | grep -q ':{port} '")

    ssh_command(f"{BREW} uninstall {pkg}")

    result = ssh_command(f"{BREW} list --versions {pkg}", check=False)
    assert result.returncode != 0, (
        f"{pkg} still listed by brew after uninstall: {result.stdout}"
    )


def test_brew_auto_update_disabled(ssh_command):
    result = ssh_command("grep -Fx HOMEBREW_NO_AUTO_UPDATE=1 /etc/environment")
    assert result.stdout.strip() == "HOMEBREW_NO_AUTO_UPDATE=1"


def test_brew_own_update_timers_not_shipped(ssh_command):
    # we never copy brew-update.timer/brew-upgrade.timer out of the upstream
    # brew image in the first place -- see Containerfile's "overrides" stage
    result = ssh_command(
        "systemctl --user list-unit-files 'brew-*' --no-legend", check=False
    )
    assert result.stdout.strip() == "", (
        f"unexpected brew systemd units present: {result.stdout}"
    )
