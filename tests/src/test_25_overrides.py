import re
import time

from defaults import TEST_USER

VERSION_RE = re.compile(r"^[0-9]+\.[0-9]{8}\.[0-9]+$")


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

    ssh_command("test -x /home/linuxbrew/.linuxbrew/bin/brew")

    result = ssh_command("stat -c %U /home/linuxbrew/.linuxbrew")
    assert result.stdout.strip() == TEST_USER, (
        f"/home/linuxbrew/.linuxbrew expected to be owned by {TEST_USER}, "
        f"actual owner: {result.stdout.strip()}"
    )


def test_brew_runs(ssh_command):
    _wait_for(ssh_command, "test -f /etc/.linuxbrew")

    result = ssh_command("/home/linuxbrew/.linuxbrew/bin/brew --version")
    assert "Homebrew" in result.stdout, (
        f"unexpected `brew --version` output: {result.stdout}"
    )


def test_brew_package_install_run_uninstall(ssh_command):
    _wait_for(ssh_command, "test -f /etc/.linuxbrew")

    brew = "/home/linuxbrew/.linuxbrew/bin/brew"
    pkg = "hello"

    ssh_command(f"{brew} install {pkg}")

    result = ssh_command(f"{brew} list --versions {pkg}")
    assert result.stdout.strip().startswith(pkg), (
        f"unexpected `brew list --versions {pkg}` output: {result.stdout}"
    )

    result = ssh_command("/home/linuxbrew/.linuxbrew/bin/hello")
    assert "Hello, world!" in result.stdout, (
        f"unexpected `hello` output: {result.stdout}"
    )

    ssh_command(f"{brew} uninstall {pkg}")

    result = ssh_command(f"{brew} list --versions {pkg}", check=False)
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


def test_rpm_ostree_auto_update_disabled(ssh_command):
    result = ssh_command(
        "systemctl is-enabled rpm-ostreed-automatic.timer", check=False
    )
    assert result.stdout.strip() == "disabled", (
        f"rpm-ostreed-automatic.timer expected disabled, actual: {result.stdout.strip()}"
    )


def test_flatpak_system_auto_update_disabled(ssh_command):
    result = ssh_command(
        "systemctl is-enabled flatpak-system-update.timer", check=False
    )
    assert result.stdout.strip() in ("disabled", "not-found"), (
        f"flatpak-system-update.timer expected disabled or absent, actual: {result.stdout.strip()}"
    )


def test_flatpak_user_auto_update_disabled(ssh_command):
    result = ssh_command(
        "systemctl --user is-enabled flatpak-user-update.timer", check=False
    )
    assert result.stdout.strip() in ("disabled", "not-found"), (
        f"flatpak-user-update.timer expected disabled or absent, actual: {result.stdout.strip()}"
    )


def test_flathub_is_default_remote(ssh_command):
    # must run before test_30_runtime's flatpak tests, which add flathub
    # themselves if it's missing and would otherwise mask this check
    result = ssh_command("flatpak remotes")
    assert "flathub" in result.stdout, (
        f"flathub not present as a default flatpak remote: {result.stdout}"
    )


def test_rpm_ostree_version_label_surfaced(ssh_command):
    # confirms the org.opencontainers.image.version label (set by Justfile's
    # build recipe for test builds, and by CI's real build) survives the
    # image build -> ostree import -> deploy pipeline and is readable the
    # same way kctl-update-check reads it
    result = ssh_command(
        "rpm-ostree status --json | jq -r '.deployments[] | select(.booted) | .version'"
    )
    version = result.stdout.strip()
    assert VERSION_RE.match(version), (
        f"booted deployment version {version!r} does not match the NN.YYYYMMDD.N scheme"
    )


def test_kctl_update_check_runs_cleanly(ssh_command):
    # on a locally-built test image the tracked pullspec is a local tag, not
    # a real ghcr.io one, so this always takes the safe early-exit path --
    # this just proves the script itself doesn't error or hang
    ssh_command("timeout 30 /usr/libexec/kctl-update-check")


def test_kctl_help(ssh_command):
    result = ssh_command("kctl help")
    assert "upgrade" in result.stdout
    assert "disable-update-notify" in result.stdout


def test_kctl_no_args_shows_help(ssh_command):
    result = ssh_command("kctl")
    assert "upgrade" in result.stdout


def test_kctl_unknown_command_fails(ssh_command):
    result = ssh_command("kctl bogus-command", check=False)
    assert result.returncode != 0, "kctl accepted an unknown command"


def test_kctl_update_notify_timer_enabled(ssh_command):
    result = ssh_command("systemctl --user is-enabled kctl-update-notify.timer")
    assert result.stdout.strip() == "enabled", (
        f"kctl-update-notify.timer expected enabled, actual: {result.stdout.strip()}"
    )


# mutates state (disables the timer) -- keep last so it runs after the check above
def test_kctl_disable_update_notify_command(ssh_command):
    ssh_command("kctl disable-update-notify")

    result = ssh_command(
        "systemctl --user is-enabled kctl-update-notify.timer", check=False
    )
    assert result.stdout.strip() == "masked", (
        f"kctl-update-notify.timer expected masked after `kctl disable-update-notify`, "
        f"actual: {result.stdout.strip()}"
    )
