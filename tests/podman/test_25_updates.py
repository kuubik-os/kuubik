import json
import shlex

import pytest

@pytest.mark.parametrize(
    "unit",
    ["rpm-ostreed-automatic.timer", "flatpak-system-update.timer"],
)
def test_auto_update_timer_disabled(run, unit):
    # flatpak timers don't exist on every base, anything but enabled is fine
    result = run(f"systemctl is-enabled {unit}", check=False)
    assert result.stdout.strip() != "enabled", f"{unit} is enabled"


def test_flatpak_user_auto_update_disabled(run):
    result = run("systemctl --global is-enabled flatpak-user-update.timer", check=False)
    assert result.stdout.strip() != "enabled", "flatpak-user-update.timer is enabled"


def test_kctl_update_notify_timer_enabled(run):
    result = run("systemctl --global is-enabled kctl-update-notify.timer")
    assert result.stdout.strip() == "enabled", (
        f"kctl-update-notify.timer expected enabled, actual: {result.stdout.strip()}"
    )


SIGNED = "ostree-image-signed:docker://ghcr.io/kuubik-os/kuubik:latest"
UNVERIFIED_NVIDIA = "ostree-unverified-registry:ghcr.io/kuubik-os/kuubik-nvidia:latest"
LOCAL = "ostree-unverified-image:containers-storage:localhost/kuubik:latest"
LAUNCH = "systemd-run --user konsole --hold -e kctl upgrade"


# rpm-ostree and skopeo stubs look like an install from ref, notify-send answers with click
@pytest.mark.parametrize(
    ("ref", "current", "latest", "click", "pulled", "notified", "launched"),
    [
        pytest.param(SIGNED, "20260101.0", "20260131.0", "update",
                     "ghcr.io/kuubik-os/kuubik:latest", True, True, id="30-days-update-clicked"),
        pytest.param(SIGNED, "20260101.0", "20260130.2", "update",
                     "ghcr.io/kuubik-os/kuubik:latest", False, False, id="29-days"),
        pytest.param(UNVERIFIED_NVIDIA, "20260101.0", "20260201.0", "",
                     "ghcr.io/kuubik-os/kuubik-nvidia:latest", True, False, id="nvidia-dismissed"),
        pytest.param(LOCAL, "20260101.0", "20260201.0", "update", None, False, False, id="local-image"),
        pytest.param(SIGNED, "44.20260101.0", "20260201.0", "update", None, False, False,
                     id="not-a-kuubik-version"),
        pytest.param(SIGNED, "20260101.0", None, "update",
                     "ghcr.io/kuubik-os/kuubik:latest", False, False, id="registry-unreachable"),
    ],
)
def test_kctl_update_check(stubs, ref, current, latest, click, pulled, notified, launched):
    status = json.dumps(
        {"deployments": [{"booted": True, "version": current, "container-image-reference": ref}]}
    )
    stubs.add("rpm-ostree", f"echo {shlex.quote(status)}")
    if latest is None:
        stubs.add("skopeo", "exit 1")
    else:
        inspect = json.dumps({"Labels": {"org.opencontainers.image.version": latest}})
        stubs.add("skopeo", f"echo {shlex.quote(inspect)}")
    stubs.add("notify-send", f"echo {click}")
    stubs.add("systemd-run")

    result = stubs.run("timeout 30 /usr/libexec/kctl-update-check")
    assert result.returncode == 0, result.stderr
    calls = stubs.calls()
    inspected = [call for call in calls if call.startswith("skopeo ")]
    assert inspected == ([f"skopeo inspect --no-tags docker://{pulled}"] if pulled else []), calls
    assert any(call.startswith("notify-send ") for call in calls) == notified, calls
    assert (LAUNCH in calls) == launched, calls
