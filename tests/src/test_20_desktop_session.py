from defaults import PLASMA_DE_PACKAGES, REMOVED_PACKAGES_SAMPLE


def test_graphical_target_is_default(ssh_command):
    result = ssh_command("systemctl get-default")
    assert result.stdout.strip() == "graphical.target", (
        f"graphical.target not set as default systemd target, actual state: {result.stdout.strip()}. Full response: {result.stdout}"
    )


def test_display_manager_is_active(ssh_command):
    result = ssh_command("systemctl is-active display-manager.service")
    actual_state = result.stdout.strip()
    assert actual_state == "active", (
        f"display-manager.service expected to be active, actual state: {actual_state}. Full response: {result.stdout}"
    )


def test_plasmalogin_is_active(ssh_command):
    result = ssh_command("systemctl is-active plasmalogin.service")
    actual_state = result.stdout.strip()
    assert actual_state == "active", (
        f"plasmalogin expected to be active, actual state: {actual_state}. Full response: {result.stdout}"
    )


def test_plasmalogin_is_selected_display_manager(ssh_command):
    result = ssh_command("readlink -f /etc/systemd/system/display-manager.service")
    actual_target = result.stdout.strip()
    assert actual_target.endswith("/plasmalogin.service"), (
        f"display-manager.service expected to point to plasmalogin.service, actual target: {actual_target}. Full response: {result.stdout}"
    )


def test_plasma_de_packages_installed(ssh_command):
    for package in PLASMA_DE_PACKAGES:
        ssh_command(f"rpm -q {package}")


def test_firewall_running(ssh_command):
    result = ssh_command("systemctl is-active firewalld")
    actual_state = result.stdout.strip()
    assert actual_state == "active", (
        f"firewalld expected to be active, actual state: {actual_state}. Full response: {result.stdout}"
    )


def test_networkmanager_running(ssh_command):
    result = ssh_command("systemctl is-active NetworkManager")
    actual_state = result.stdout.strip()
    assert actual_state == "active", (
        f"NetworkManager expected to be active, actual state: {actual_state}. Full response: {result.stdout}"
    )


def test_polkit_running(ssh_command):
    result = ssh_command("systemctl is-active polkit")
    actual_state = result.stdout.strip()
    assert actual_state == "active", (
        f"polkit expected to be active, actual state: {actual_state}. Full response: {result.stdout}"
    )


def test_graphical_session_exists(ssh_command):
    result = ssh_command(
        "loginctl show-session $(loginctl | awk '/seat0/ {print $1}') -p Type"
    )
    assert "Type=wayland" in result.stdout, (
        f"No active graphical session found: {result.stdout}"
    )


def test_ananicy_running(ssh_command):
    result = ssh_command("systemctl is-active ananicy-cpp")
    actual_state = result.stdout.strip()
    assert actual_state == "active", (
        f"ananicy-cpp expected to be active, actual state: {actual_state}. Full response: {result.stdout}"
    )


def test_removed_packages_absent(ssh_command):
    for package in REMOVED_PACKAGES_SAMPLE:
        result = ssh_command(f"rpm -q {package}", check=False)
        assert result.returncode != 0, (
            f"{package} expected to be removed from the image, but rpm -q found it: {result.stdout}"
        )


def test_no_failed_system_units(ssh_command):
    result = ssh_command("systemctl --failed --no-legend")
    assert result.stdout.strip() == "", (
        f"unexpected failed system units: {result.stdout}"
    )


def test_no_failed_user_units(ssh_command):
    result = ssh_command("systemctl --user --failed --no-legend")
    assert result.stdout.strip() == "", (
        f"unexpected failed user units: {result.stdout}"
    )
