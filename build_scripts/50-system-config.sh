#!/usr/bin/env bash

set -ouex pipefail

# fetched to /etc, /var is tmpfs during build
curl -fsSL https://dl.flathub.org/repo/flathub.flatpakrepo -o /etc/flatpak/remotes.d/flathub.flatpakrepo

# plasma's own default wallpaper instead of fedora's. Fedora links to Default, which plasmalogin,
# the lock screen and fedora's look-and-feel use
ln -sfn Next /usr/share/wallpapers/Default
rm -rf /usr/share/wallpapers/F[0-9]* \
	/usr/share/backgrounds/f[0-9]* /usr/share/backgrounds/fedora-* \
	/usr/share/backgrounds/default* /usr/share/backgrounds/desktop-backgrounds-default.xml

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

# keeps the first booted image for kctl rollback, see kuubik-factory-image
systemctl enable kuubik-factory-image.service
