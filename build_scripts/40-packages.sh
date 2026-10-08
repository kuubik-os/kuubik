#!/usr/bin/env bash

set -ouex pipefail

dnf5 -y install distrobox

# tailscale ships disabled, enable with: systemctl enable --now tailscaled
dnf5 -y config-manager addrepo --from-repofile=https://pkgs.tailscale.com/stable/fedora/tailscale.repo
dnf5 -y install tailscale
rm -fv /etc/yum.repos.d/tailscale.repo
systemctl disable tailscaled.service
printf '%s\n' 'TS_NO_LOGS_NO_SUPPORT=true' >>/etc/default/tailscaled

dnf5 -y install --nogpgcheck --repofrompath "terra,https://repos.fyralabs.com/terra\$releasever" terra-release
dnf5 -y --setopt=terra.gpgcheck=0 install ubuntumono-nerd-fonts jetbrainsmono-nerd-fonts
dnf5 -y remove terra-release terra-gpg-keys
