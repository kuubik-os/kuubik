#!/usr/bin/env bash

set -ouex pipefail

# fetched to /etc, /var is tmpfs during build
curl -fsSL https://dl.flathub.org/repo/flathub.flatpakrepo -o /etc/flatpak/remotes.d/flathub.flatpakrepo

# use git upstream as they are not paclaged for el. use same path as fedora packages
zsh_plugins=(
	"zsh-autosuggestions https://github.com/zsh-users/zsh-autosuggestions/archive/refs/tags/v0.7.1.tar.gz 0df7affff21cd87ed298e6a3970ed08a1dd66a6efa676454ee5b091ad503badf"
	"zsh-syntax-highlighting https://github.com/zsh-users/zsh-syntax-highlighting/archive/refs/tags/0.8.0.tar.gz 5981c19ebaab027e356fe1ee5284f7a021b89d4405cc53dc84b476c3aee9cc32"
)
for plugin in "${zsh_plugins[@]}"; do
	read -r name url sha256 <<<"$plugin"
	curl -fsSL "$url" -o "/tmp/${name}.tar.gz"
	echo "${sha256}  /tmp/${name}.tar.gz" | sha256sum --check
	mkdir -p "/tmp/${name}" "/usr/share/${name}"
	tar -xzf "/tmp/${name}.tar.gz" -C "/tmp/${name}" --strip-components=1
	cp -a "/tmp/${name}/${name}.zsh" "/usr/share/${name}/"
	if [ -d "/tmp/${name}/highlighters" ]; then
		cp -a "/tmp/${name}/highlighters" "/tmp/${name}/.version" "/tmp/${name}/.revision-hash" "/usr/share/${name}/"
	fi
done

systemctl enable brew-setup.service
systemctl enable kuubik-flatpak-init.service
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
