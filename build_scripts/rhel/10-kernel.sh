#!/usr/bin/env bash

set -ouex pipefail

# per-RUN tmpfs mounts don't come up 1777
mkdir -p /var/tmp /tmp
chmod 1777 /var/tmp /tmp

dnf -y install python3-dnf-plugin-versionlock
dnf -y copr enable bieszczaders/kernel-cachyos-lto

dnf config-manager --save --setopt='baseos.excludepkgs=kernel-core-* kernel-modules-* kernel-uki-virt-*'

# stub out kernel-install hooks, initramfs is built in 90-finalize.sh
pushd /usr/lib/kernel/install.d
printf '%s\n' '#!/bin/sh' 'exit 0' >05-rpmostree.install
printf '%s\n' '#!/bin/sh' 'exit 0' >50-dracut.install
chmod +x 05-rpmostree.install 50-dracut.install
popd

for pkg in kernel kernel-core kernel-modules kernel-modules-core kernel-modules-extra kernel-uki-virt; do
	if rpm -q "$pkg" >/dev/null 2>&1; then
		dnf -y remove "$pkg"
	fi
done
find /usr/lib/modules -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
find /boot -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +

kernel_packages=(
	kernel-cachyos-lts-lto
	kernel-cachyos-lts-lto-core
	kernel-cachyos-lts-lto-devel-matched
	kernel-cachyos-lts-lto-modules
)

dnf -y install "${kernel_packages[@]}"
dnf versionlock add "${kernel_packages[@]}"
