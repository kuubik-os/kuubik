#!/usr/bin/env bash

set -ouex pipefail

dnf5 -y install distrobox zsh zsh-syntax-highlighting eza bat ripgrep fd-find

# vm-curator, latest release rpm, with qemu/kvm, uefi and tpm for its vms
vmc_tag=$(curl -fsSLI -o /dev/null -w '%{url_effective}' https://github.com/mroboff/vm-curator/releases/latest)
vmc_tag=${vmc_tag##*/}
dnf5 -y install qemu-system-x86 qemu-img edk2-ovmf swtpm virt-viewer \
	"https://github.com/mroboff/vm-curator/releases/download/${vmc_tag}/vm-curator-${vmc_tag#v}-1.x86_64.rpm"

rm -fv /usr/share/applications/remote-viewer.desktop

# tailscale ships disabled, enable with: systemctl enable --now tailscaled
dnf5 -y config-manager addrepo --from-repofile=https://pkgs.tailscale.com/stable/fedora/tailscale.repo
dnf5 -y install tailscale
rm -fv /etc/yum.repos.d/tailscale.repo
systemctl disable tailscaled.service
printf '%s\n' 'TS_NO_LOGS_NO_SUPPORT=true' >>/etc/default/tailscaled

dnf5 -y install --nogpgcheck --repofrompath "terra,https://repos.fyralabs.com/terra\$releasever" terra-release
dnf5 -y install ubuntumono-nerd-fonts jetbrainsmono-nerd-fonts
dnf5 -y remove terra-release terra-gpg-keys
