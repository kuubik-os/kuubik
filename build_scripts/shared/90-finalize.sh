#!/usr/bin/env bash

set -ouex pipefail

KERNEL_VERSION=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f\n' -quit)

mkdir -p /var/tmp
chmod 1777 /var/tmp

# grub titles entries from os-release, keep it in sync with the image version label
if [ -n "${IMAGE_VERSION:-}" ]; then
	sed -i \
		-e "s|^VERSION=.*|VERSION=\"${IMAGE_VERSION} (kuubik)\"|" \
		-e "s|^PRETTY_NAME=.*|PRETTY_NAME=\"kuubik Linux ${IMAGE_VERSION}\"|" \
		-e "s|^OSTREE_VERSION=.*|OSTREE_VERSION='${IMAGE_VERSION}'|" \
		/usr/lib/os-release
fi

depmod -a "$KERNEL_VERSION"
DRACUT_NO_XATTR=1 /usr/bin/dracut \
	--no-hostonly \
	--kver "$KERNEL_VERSION" \
	--reproducible \
	--zstd -v \
	--add ostree \
	-f "/usr/lib/modules/$KERNEL_VERSION/initramfs.img"
chmod 0600 "/usr/lib/modules/$KERNEL_VERSION/initramfs.img"

# dnf5 on fedora, dnf4 on the lts base
DNF=$(command -v dnf5 || command -v dnf)
"$DNF" -y remove "kernel-cachyos-*-devel-matched"
"$DNF" -y clean all

rm -rfv /etc/yum.repos.d/*cachyos*
rm -rfv /run/akmods /run/dnf /run/selinux-policy /tmp/*
rm -fv /usr/lib/kernel/install.d/05-rpmostree.install /usr/lib/kernel/install.d/50-dracut.install
