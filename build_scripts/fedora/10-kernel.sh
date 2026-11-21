#!/usr/bin/env bash

set -ouex pipefail

# per-RUN tmpfs mounts don't come up 1777 
mkdir -p /var/tmp /tmp
chmod 1777 /var/tmp /tmp

dnf5 -y copr enable bieszczaders/kernel-cachyos-lto

dnf5 -y config-manager setopt '*fedora*.exclude=kernel-core-* kernel-modules-* kernel-uki-virt-*'
dnf5 -y config-manager setopt '*updates*.exclude=kernel-core-* kernel-modules-* kernel-uki-virt-*'

"$(dirname "$0")/../shared/remove-stock-kernel.sh"

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
