import re

VERSION_RE = re.compile(r"^[0-9]{8}\.[0-9]+$")


def test_rpm_ostree_version_label_surfaced(ssh_command):
    # confirms the org.opencontainers.image.version label survives the
    # image build -> ostree import -> deploy pipeline and is readable the
    # same way kctl-update-check reads it
    result = ssh_command(
        "rpm-ostree status --json | jq -r '.deployments[] | select(.booted) | .version'"
    )
    version = result.stdout.strip()
    assert VERSION_RE.match(version), (
        f"booted deployment version {version!r} does not match the YYYYMMDD.N scheme"
    )
