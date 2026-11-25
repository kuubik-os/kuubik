FACTORY_REF = "kuubik/factory"
REPO = "/sysroot/ostree/repo"


def test_factory_ref_is_first_booted_image(ssh_command, wait_for):
    wait_for(f"test -e {REPO}/refs/heads/{FACTORY_REF}", timeout=120)
    factory = ssh_command(f"ostree rev-parse --repo={REPO} {FACTORY_REF}").stdout.strip()
    booted = ssh_command(
        "rpm-ostree status --json | jq -r '.deployments[] | select(.booted) | .checksum'"
    ).stdout.strip()
    assert factory == booted
    result = ssh_command("systemctl show -p Result --value kuubik-factory-image.service")
    assert result.stdout.strip() == "success", f"factory service result: {result.stdout}"


def test_factory_service_skips_once_ref_exists(ssh_command):
    ssh_command("sudo systemctl start kuubik-factory-image.service")
    result = ssh_command("systemctl show -p ConditionResult --value kuubik-factory-image.service")
    assert result.stdout.strip() == "no", "factory service ran again although the ref exists"


def test_factory_ref_survives_cleanup(ssh_command):
    ssh_command("sudo rpm-ostree cleanup --base --rollback")
    ssh_command(f"ostree ls --repo={REPO} {FACTORY_REF} /usr/bin/kctl")


def test_kctl_rollback_lists_images(ssh_command):
    result = ssh_command("echo q | kctl rollback")
    version = ssh_command(
        "rpm-ostree status --json | jq -r '.deployments[] | select(.booted) | .version'"
    ).stdout.strip()
    assert f"{version}  running now" in result.stdout, f"booted image not listed:\n{result.stdout}"
    assert "Factory image:" in result.stdout, f"factory image not listed:\n{result.stdout}"
    assert "Aborted." in result.stdout


def test_kctl_rollback_to_current_default_is_noop(ssh_command):
    result = ssh_command("echo 1 | kctl rollback")
    assert "already boots by default" in result.stdout, f"unexpected output:\n{result.stdout}"


def test_kctl_rollback_to_factory_not_available_yet(ssh_command):
    n = int(ssh_command(
        "rpm-ostree status --json | jq '[.deployments[] | select(.staged | not)] | length'"
    ).stdout)
    result = ssh_command(f"echo {n + 1} | kctl rollback", check=False)
    assert result.returncode == 1, f"exited {result.returncode}:\n{result.stdout}"
    assert "issues/54" in result.stdout, f"unexpected output:\n{result.stdout}"
