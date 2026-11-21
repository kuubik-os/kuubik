#!/usr/bin/env bash

set -ouex pipefail

# per-RUN tmpfs mounts don't come up 1777
mkdir -p /var/tmp /tmp
chmod 1777 /var/tmp /tmp

dnf -y install python3-dnf-plugin-versionlock
dnf -y copr enable bieszczaders/kernel-cachyos-lto

dnf config-manager --save --setopt='baseos.excludepkgs=kernel-core-* kernel-modules-* kernel-uki-virt-*'

"$(dirname "$0")/../shared/remove-stock-kernel.sh"

kernel_packages=(
	kernel-cachyos-lts-lto
	kernel-cachyos-lts-lto-core
	kernel-cachyos-lts-lto-devel-matched
	kernel-cachyos-lts-lto-modules
)

dnf -y install "${kernel_packages[@]}"
dnf versionlock add "${kernel_packages[@]}"
