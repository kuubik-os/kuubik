import pytest

from defaults import TEST_USER

DISTROBOX = "kuubik-test-box"


def test_git(ssh_command):
    ssh_command("git --version")


def test_container_policy_requires_kuubik_signatures(ssh_command):
    policy = "/etc/containers/policy.json"
    assert ssh_command(f"jq -r '.default[0].type' {policy}").stdout.strip() == "reject"
    # one namespace rule covers every kuubik-os image
    result = ssh_command(f"jq -r '.transports.docker[\"ghcr.io/kuubik-os\"][0].type' {policy}")
    assert result.stdout.strip() == "sigstoreSigned", "ghcr.io/kuubik-os is not signature checked"


def test_rootless_podman_runs_unsigned_image(ssh_command):
    # default reject must not block ordinary registries
    ssh_command(f"grep -q '^{TEST_USER}:' /etc/subuid")
    result = ssh_command("podman run --rm docker.io/library/alpine:latest echo ok")
    assert result.stdout.strip() == "ok", f"unexpected output: {result.stdout}"


def test_distrobox(ssh_command):
    ssh_command(f"distrobox create --yes --name {DISTROBOX} --image docker.io/library/alpine:latest")
    try:
        result = ssh_command(f"distrobox enter {DISTROBOX} -- cat /etc/os-release")
        assert "Alpine" in result.stdout, f"not inside the box: {result.stdout}"
    finally:
        ssh_command(f"distrobox rm --force {DISTROBOX}", check=False)


def test_zsh_config_loads_cleanly(ssh_command):
    result = ssh_command("ZDOTDIR=/etc/skel zsh -i -c 'echo ok' </dev/null")
    assert result.stdout.strip().endswith("ok"), f"unexpected output: {result.stdout}"
    assert result.stderr.strip() == "", f"zsh errors: {result.stderr}"


@pytest.mark.parametrize("font", ["JetBrainsMono Nerd Font", "UbuntuMono Nerd Font"])
def test_nerd_fonts(ssh_command, font):
    result = ssh_command("fc-list : family")
    assert font in result.stdout, f"{font} not installed"


def test_tailscale_installed_but_disabled(ssh_command):
    ssh_command("tailscale version")
    result = ssh_command("systemctl is-enabled tailscaled.service", check=False)
    assert result.stdout.strip() == "disabled", f"tailscaled: {result.stdout.strip()}"
