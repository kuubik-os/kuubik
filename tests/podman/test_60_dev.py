import pytest


def test_git(run):
    run("git --version")


def test_container_policy_requires_kuubik_signatures(run):
    policy = "/etc/containers/policy.json"
    assert run(f"jq -r '.default[0].type' {policy}").stdout.strip() == "reject"
    # one namespace rule covers every kuubik-os image
    result = run(f"jq -r '.transports.docker[\"ghcr.io/kuubik-os\"][0].type' {policy}")
    assert result.stdout.strip() == "sigstoreSigned", "ghcr.io/kuubik-os is not signature checked"


def test_zsh_config_loads_cleanly(run):
    result = run("ZDOTDIR=/etc/skel zsh -i -c 'echo ok' </dev/null")
    assert result.stdout.strip().endswith("ok"), f"unexpected output: {result.stdout}"
    assert result.stderr.strip() == "", f"zsh errors: {result.stderr}"


@pytest.mark.parametrize("font", ["JetBrainsMono Nerd Font", "UbuntuMono Nerd Font"])
def test_nerd_fonts(run, font):
    result = run("fc-list : family")
    assert font in result.stdout, f"{font} not installed"


def test_tailscale_installed_but_disabled(run):
    run("tailscale version")
    result = run("systemctl is-enabled tailscaled.service", check=False)
    assert result.stdout.strip() == "disabled", f"tailscaled: {result.stdout.strip()}"
