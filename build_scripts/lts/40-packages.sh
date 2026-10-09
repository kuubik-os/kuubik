#!/usr/bin/env bash

set -ouex pipefail

dnf -y install distrobox zsh

# tailscale ships disabled, enable with: systemctl enable --now tailscaled
dnf config-manager --add-repo "https://pkgs.tailscale.com/stable/rhel/$(rpm -E %rhel)/tailscale.repo"
dnf -y install tailscale
rm -fv /etc/yum.repos.d/tailscale.repo
systemctl disable tailscaled.service
printf '%s\n' 'TS_NO_LOGS_NO_SUPPORT=true' >>/etc/default/tailscaled

dnf -y install --nogpgcheck --repofrompath "terra,https://repos.fyralabs.com/terrael\$releasever" terra-release
dnf -y install ananicy-cpp ubuntumono-nerd-fonts jetbrainsmono-nerd-fonts
dnf -y remove terra-release
systemctl enable ananicy-cpp.service
