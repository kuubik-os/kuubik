#!/usr/bin/env bash

set -ouex pipefail

# per-RUN tmpfs mounts don't come up 1777
mkdir -p /var/tmp /tmp
chmod 1777 /var/tmp /tmp

dnf5 -y copr enable bieszczaders/kernel-cachyos-lto

dnf5 -y config-manager setopt '*fedora*.exclude=kernel-core-* kernel-modules-* kernel-uki-virt-*'
dnf5 -y config-manager setopt '*updates*.exclude=kernel-core-* kernel-modules-* kernel-uki-virt-*'

# stub out kernel-install hooks, initramfs is built in 90-finalize.sh
pushd /usr/lib/kernel/install.d
printf '%s\n' '#!/bin/sh' 'exit 0' >05-rpmostree.install
printf '%s\n' '#!/bin/sh' 'exit 0' >50-dracut.install
chmod +x 05-rpmostree.install 50-dracut.install
popd

for pkg in kernel kernel-core kernel-modules kernel-modules-core kernel-modules-extra kernel-uki-virt; do
	if rpm -q "$pkg" >/dev/null 2>&1; then
		dnf5 -y remove "$pkg"
	fi
done
find /usr/lib/modules -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
find /boot -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +

kernel_packages=(
	kernel-cachyos-lto
	kernel-cachyos-lto-core
	kernel-cachyos-lto-devel-matched
	kernel-cachyos-lto-modules
)

dnf5 -y install "${kernel_packages[@]}"
dnf5 versionlock add "${kernel_packages[@]}"

dnf5 -y copr enable bieszczaders/kernel-cachyos-addons
dnf5 -y install ananicy-cpp
systemctl enable ananicy-cpp.service
