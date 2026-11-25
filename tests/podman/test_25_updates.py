import shlex

import pytest

STUB_DIR = "/tmp/kctl-update-check-stubs"


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


# stub rpm-ostree and skopeo to look like a ghcr install, notify-send to record
# whether it fired and click "Update now", and systemd-run to record what the click launches
@pytest.mark.parametrize(("latest", "notified"), [("20260131.0", True), ("20260130.2", False)])
def test_kctl_update_check_notifies_after_30_days(run, latest, notified):
    status = (
        '{"deployments":[{"booted":true,"version":"20260101.0",'
        '"container-image-reference":"ostree-image-signed:docker://ghcr.io/kuubik-os/kuubik:latest"}]}'
    )
    inspect = f'{{"Labels":{{"org.opencontainers.image.version":"{latest}"}}}}'
    stubs = {
        "rpm-ostree": f"#!/bin/sh\necho {shlex.quote(status)}\n",
        "skopeo": f"#!/bin/sh\necho {shlex.quote(inspect)}\n",
        "notify-send": f'#!/bin/sh\necho "$*" >{STUB_DIR}/notified\necho update\n',
        "systemd-run": f'#!/bin/sh\necho "$*" >{STUB_DIR}/launched\n',
    }
    run(
        f"rm -rf {STUB_DIR} && mkdir -p {STUB_DIR} && "
        + " && ".join(
            f"printf %s {shlex.quote(body)} >{STUB_DIR}/{name} && chmod +x {STUB_DIR}/{name}"
            for name, body in stubs.items()
        )
    )
    run(f"PATH={STUB_DIR}:$PATH timeout 30 /usr/libexec/kctl-update-check")
    fired = run(f"test -f {STUB_DIR}/notified", check=False).returncode == 0
    assert fired == notified, f"latest {latest}: notification fired={fired}, expected {notified}"
    launched = run(f"cat {STUB_DIR}/launched", check=False).stdout.strip()
    expected = "--user konsole --hold -e kctl upgrade" if notified else ""
    assert launched == expected, f"latest {latest}: launched {launched!r}"
