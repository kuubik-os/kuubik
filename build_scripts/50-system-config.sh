#!/usr/bin/env bash

set -ouex pipefail

# fetched to /etc, /var is tmpfs during build
curl -fsSL https://dl.flathub.org/repo/flathub.flatpakrepo -o /etc/flatpak/remotes.d/flathub.flatpakrepo

systemctl enable brew-setup.service
echo 'HOMEBREW_NO_AUTO_UPDATE=1' >>/etc/environment

# updates are manual via kctl, the timer only notifies
if systemctl list-unit-files rpm-ostreed-automatic.timer &>/dev/null; then
	systemctl disable rpm-ostreed-automatic.timer
fi

if systemctl list-unit-files flatpak-system-update.timer &>/dev/null; then
	systemctl disable flatpak-system-update.timer
fi

if systemctl --global list-unit-files flatpak-user-update.timer &>/dev/null; then
	systemctl --global disable flatpak-user-update.timer
fi

systemctl --global enable kctl-update-notify.timer
