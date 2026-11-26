import re
import shlex
import subprocess
import tomllib
from collections.abc import Iterator
from pathlib import Path

import pytest

CLI_TOOLS = [
    "git", "distrobox", "zsh", "eza", "bat", "rg", "fd", "jq",
    "podman", "buildah", "skopeo", "swtpm", "vm-curator", "tailscaled",
]
# vm-curator runs its vms with these
VM_PACKAGES = ["vm-curator", "qemu-system-x86", "qemu-img", "edk2-ovmf", "swtpm", "virt-viewer"]
# the firmware vm-curator looks for first, secure boot variants for windows 11 guests
OVMF = [
    "OVMF_CODE_4M.qcow2", "OVMF_VARS_4M.qcow2", "OVMF_CODE_4M.secboot.qcow2", "OVMF_VARS_4M.secboot.qcow2",
]
DEV_USER = "devuser"
BREW_PREFIX = "/home/linuxbrew/.linuxbrew"


@pytest.fixture(scope="module")
def dev_user(run) -> Iterator[str]:
    """a regular user with uid 1000, like the first account an install creates"""
    # /home links to /var/home, which only exists on a booted system
    run(f"mkdir -p /var/home && useradd -u 1000 -m {DEV_USER}")
    yield DEV_USER
    run(f"userdel -r {DEV_USER}", check=False)


@pytest.mark.parametrize("tool", CLI_TOOLS)
def test_cli_tool_runs(run, tool):
    run(f"{tool} --version")


def test_vm_packages(run):
    run(f"rpm -q {' '.join(VM_PACKAGES)}")


def test_container_trust_policy(run):
    # as podman reads policy.json: kuubik images signed, everything else pullable
    rows = [line.split() for line in run("podman image trust show").stdout.splitlines()[1:]]
    assert ["all", "default", "reject"] in rows, rows
    assert ["repository", "ghcr.io/kuubik-os", "sigstoreSigned", "N/A"] in rows, rows
    assert ["repository", "accept"] in rows, "other registries are not pullable"


def test_short_image_names_resolve():
    # distrobox and podman users type "fedora" or "ubuntu", not full references
    conf = tomllib.loads(Path("/etc/containers/registries.conf").read_text())
    search = conf["unqualified-search-registries"]
    assert "registry.fedoraproject.org" in search and "docker.io" in search, search


def test_new_user_gets_subids(run, dev_user):
    # without them rootless podman and distrobox fail for the account
    for db in ("/etc/subuid", "/etc/subgid"):
        entry = run(f"grep '^{dev_user}:' {db}").stdout.strip()
        assert int(entry.split(":")[2]) >= 65536, f"{db}: {entry}"


def test_distrobox_create_dry_run(run):
    image = "registry.fedoraproject.org/fedora-toolbox:latest"
    result = run(f"distrobox create --dry-run --name kuubik-test --image {image}")
    assert "podman create" in result.stdout and image in result.stdout, result.stdout


def test_toolbox_runs(run):
    # toolbox links against /run/host/usr/lib64/ld-linux, its tmpfiles entry creates /run/host at boot
    run("systemd-tmpfiles --create /usr/lib/tmpfiles.d/toolbox.conf && toolbox --version")


@pytest.fixture(scope="module")
def brew(run, dev_user) -> Iterator[str]:
    """brew unpacked by running brew-setup.service's own commands, as on first boot"""
    commands = run("grep '^ExecStart=' /usr/lib/systemd/system/brew-setup.service").stdout
    for line in commands.splitlines():
        run(line.split("=", 1)[1])
    yield f"{BREW_PREFIX}/bin/brew"
    run(f"rm -rf {BREW_PREFIX} /etc/.linuxbrew", check=False)


def test_brew_setup_unpacks_for_first_user(run, brew, dev_user):
    owner = run(f"stat -c %U {BREW_PREFIX} {brew}").stdout.split()
    assert owner == [dev_user, dev_user], f"brew prefix owned by {owner}"
    run("test -f /etc/.linuxbrew")


def test_brew_runs_for_user(run, brew, dev_user):
    run("grep -qx 'HOMEBREW_NO_AUTO_UPDATE=1' /etc/environment")
    # login shell, so /etc/profile.d/brew.sh puts it on PATH
    result = run(
        f"runuser -u {dev_user} -- env -i HOME=/home/{dev_user} HOMEBREW_NO_AUTO_UPDATE=1 "
        "bash -lc 'command -v brew && brew --version'"
    )
    assert result.stdout.splitlines()[0] == brew, result.stdout
    assert result.stdout.splitlines()[1].startswith("Homebrew "), result.stdout


def _user_zsh(run, user: str, command: str) -> subprocess.CompletedProcess[str]:
    """interactive zsh as user, home set up from /etc/skel by useradd"""
    return run(f"runuser -u {user} -- env -i HOME=/home/{user} TERM=dumb zsh -i -c {shlex.quote(command)} </dev/null")


# as the user: brew's zsh completions are owned by them, compinit refuses them for root
def test_zsh_config_loads_cleanly(run, dev_user, brew):
    result = _user_zsh(run, dev_user, "echo ok")
    assert result.stdout.strip().endswith("ok"), f"unexpected output: {result.stdout}"
    assert result.stderr.strip() == "", f"zsh errors: {result.stderr}"


def test_zsh_plugins_loaded(run, dev_user, brew):
    result = _user_zsh(run, dev_user, "whence -w _zsh_highlight compdef")
    assert result.stdout.split() == ["_zsh_highlight:", "function", "compdef:", "function"], result.stdout


def test_zsh_aliases_point_to_installed_tools(run):
    zshrc = Path("/etc/skel/.zshrc").read_text()
    aliases = dict(re.findall(r'^alias (\S+?)="(.*)"$', zshrc, re.MULTILINE))
    assert aliases, "no aliases found in .zshrc"
    for name, value in aliases.items():
        words = [w for w in shlex.split(value) if not re.match(r"^\w+=", w)]
        if words[0] not in aliases:
            run(f"command -v {words[0]}")


def test_qemu_accelerators(run):
    accels = run("qemu-system-x86_64 -accel help").stdout.split()
    assert "kvm" in accels and "tcg" in accels, accels


@pytest.mark.parametrize("firmware", OVMF)
def test_ovmf_firmware(run, firmware):
    run(f"test -s /usr/share/edk2/ovmf/{firmware}")


def test_python_on_host(run, tmp_path):
    run("python3 -c 'import ssl, sqlite3, venv'")
    # no pip on the host, venvs are how users get one
    run(f"python3 -m venv {tmp_path}/venv && {tmp_path}/venv/bin/python -m pip --version")


@pytest.mark.parametrize("font", ["JetBrainsMono Nerd Font", "UbuntuMono Nerd Font"])
def test_nerd_fonts(run, font):
    result = run("fc-list : family")
    assert font in result.stdout, f"{font} not installed"


def test_tailscale_installed_but_disabled(run):
    run("tailscale version")
    verify = run("systemd-analyze verify --man=no tailscaled.service", check=False)
    assert verify.returncode == 0 and "tailscaled" not in verify.stderr, verify.stderr
    result = run("systemctl is-enabled tailscaled.service", check=False)
    assert result.stdout.strip() == "disabled", f"tailscaled: {result.stdout.strip()}"
    result = run("grep -cx 'TS_NO_LOGS_NO_SUPPORT=true' /etc/default/tailscaled")
    assert result.stdout.strip() == "1", "TS_NO_LOGS_NO_SUPPORT not set exactly once"
