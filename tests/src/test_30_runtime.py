def test_flatpak_app_management(ssh_command):

    ssh_command(
        "flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo"
    )
    ssh_command("flatpak remotes | grep flathub")

    app = "org.kde.okular"

    ssh_command(f"sudo flatpak install --noninteractive --assumeyes flathub {app}")
    ssh_command(f"flatpak list | grep {app}")
    ssh_command(f"sudo flatpak uninstall --noninteractive --assumeyes {app}")
