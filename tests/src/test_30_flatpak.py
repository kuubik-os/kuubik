import time

from defaults import SESSION_ENV

APP = "org.kde.okular"


def test_flatpak_usable_without_root(ssh_command):
    result = ssh_command("flatpak remotes --columns=name")
    assert "flathub" in result.stdout.split(), f"flathub remote missing: {result.stdout}"
    ssh_command("flatpak list")


def test_flatpak_app_install_launch_uninstall(ssh_command, wait_for, desktop_session):
    ssh_command(f"sudo flatpak install --noninteractive --assumeyes flathub {APP}")
    try:
        ssh_command(f"flatpak info {APP}")
        ssh_command(f"{SESSION_ENV} setsid -f flatpak run {APP} >/tmp/{APP}.log 2>&1 </dev/null")
        wait_for(f"flatpak ps --columns=application | grep -qx {APP}", timeout=60)
        # still up after a few seconds means it didn't crash on start
        time.sleep(5)
        result = ssh_command(f"flatpak ps --columns=application | grep -qx {APP}", check=False)
        log = ssh_command(f"cat /tmp/{APP}.log", check=False).stdout
        assert result.returncode == 0, f"{APP} exited right after start:\n{log}"
    finally:
        ssh_command(f"flatpak kill {APP}", check=False)
        ssh_command(f"sudo flatpak uninstall --noninteractive --assumeyes {APP}")
