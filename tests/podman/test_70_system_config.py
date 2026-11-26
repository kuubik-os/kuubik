import pytest

FLATHUB = "/etc/flatpak/remotes.d/flathub.flatpakrepo"
SKEL_FILES = [
    ".zshrc",
    ".config/konsolerc",
    ".config/gtk-3.0/settings.ini",
    ".config/gtk-4.0/settings.ini",
    ".local/share/konsole/kuubik.profile",
]


def test_flathub_remote_shipped(run):
    # in /etc, not via flatpak remote-add which writes to /var
    result = run(f"cat {FLATHUB}")
    assert "Url=https://dl.flathub.org/repo/" in result.stdout, result.stdout
    assert "GPGKey=" in result.stdout, "flathub remote has no gpg key"
    dropin = run(
        "systemctl cat flatpak-add-fedora-repos.service | grep '^ExecStart=/'"
    ).stdout.strip()
    assert FLATHUB in dropin, f"first boot does not add flathub: {dropin}"


def test_plasma_wallpaper_is_default(run):
    assert run("readlink /usr/share/wallpapers/Default").stdout.strip() == "Next"
    leftover = run(
        "ls -d /usr/share/wallpapers/F[0-9]* /usr/share/backgrounds/f[0-9]* "
        "/usr/share/backgrounds/fedora-* 2>/dev/null",
        check=False,
    ).stdout.strip()
    assert leftover == "", f"fedora wallpapers left: {leftover}"


def test_gtk_theme_default_is_breeze(run):
    # the override only applies once glib-compile-schemas ran
    result = run("GSETTINGS_BACKEND=memory gsettings get org.gnome.desktop.interface gtk-theme")
    assert result.stdout.strip() == "'Breeze'", result.stdout


def test_plasma_look_and_feel_packages_exist(run):
    result = run("grep -E '^(LookAndFeelPackage|Default(Light|Dark)LookAndFeel)=' /etc/xdg/kdeglobals")
    packages = [line.split("=", 1)[1] for line in result.stdout.split()]
    assert "org.kde.breeze.desktop" in packages, result.stdout
    for package in packages:
        run(f"test -f /usr/share/plasma/look-and-feel/{package}/metadata.json")


@pytest.mark.parametrize("gtk", ["gtk-3.0", "gtk-4.0"])
def test_gtk_theme_exists(run, gtk):
    result = run(f"grep -m1 '^gtk-theme-name=' /etc/skel/.config/{gtk}/settings.ini")
    theme = result.stdout.strip().split("=", 1)[1]
    run(f"test -d /usr/share/themes/{theme}/{gtk}")


@pytest.mark.parametrize("unit", ["brew-setup.service", "kuubik-factory-image.service"])
def test_system_unit_enabled(run, unit):
    assert run(f"systemctl is-enabled {unit}").stdout.strip() == "enabled"


def test_signed_pulls_configured(run):
    key = run("jq -r '.transports.docker[\"ghcr.io/kuubik-os\"][0].keyPath' /etc/containers/policy.json")
    run(f"openssl pkey -pubin -in {key.stdout.strip()} -noout")
    # without it the cosign .sig tags are ignored and signed pulls fail
    result = run("cat /etc/containers/registries.d/ghcr.yaml")
    assert "use-sigstore-attachments: true" in result.stdout, result.stdout


@pytest.mark.parametrize("path", SKEL_FILES)
def test_skel_file(run, path):
    run(f"test -s /etc/skel/{path}")


def test_konsole_default_profile_exists(run):
    result = run("grep -m1 '^DefaultProfile=' /etc/skel/.config/konsolerc")
    profile = result.stdout.strip().split("=", 1)[1]
    run(f"test -f /etc/skel/.local/share/konsole/{profile}")



def test_konsole_profile_font_and_shell_exist(run):
    profile = run("cat /etc/skel/.local/share/konsole/kuubik.profile").stdout
    settings = dict(line.split("=", 1) for line in profile.splitlines() if "=" in line)
    family = settings["Font"].split(",")[0]
    # fontconfig lists every name of a font comma separated, konsole needs an exact one
    families = {name for line in run("fc-list : family").stdout.splitlines() for name in line.split(",")}
    assert family in families, f"konsole font {family!r} not installed"
    run(f"command -v {settings['Command']}")
