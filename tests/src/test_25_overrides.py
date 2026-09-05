import json
import re

VERSION_RE = re.compile(r"^[0-9]+\.[0-9]{8}\.[0-9]+$")


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


def test_rpm_ostree_status_human_output(ssh_command):
    # we deliberately don't run a real `rpm-ostree upgrade` here -- on a
    # local/CI test VM the deployment's origin is a scratch/local image tag,
    # not a real published ghcr.io ref, so there's nothing valid for it to
    # actually pull; this just confirms the status command itself runs
    # cleanly and reports an idle state (no stuck/failed transaction)
    result = ssh_command("rpm-ostree status")
    assert "State: idle" in result.stdout, (
        f"unexpected rpm-ostree status output: {result.stdout}"
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
