#!/usr/bin/env bash

set -ouex pipefail

# a real repo file, not --enablerepo: akmods runs its own dnf transactions
dnf5 -y config-manager addrepo --from-repofile=https://negativo17.org/repos/fedora-nvidia.repo

dnf5 -y install akmods nvtop
# akmod-nvidia's %post builds via akmodsbuild, which refuses to run as root.
# install it without scriptlets before the driver stack pulls it in normally
dnf5 -y install --setopt=tsflags=noscripts --from-repo=fedora-nvidia akmod-nvidia
dnf5 -y install --from-repo=fedora-nvidia nvidia-driver nvidia-driver-cuda xorg-x11-nvidia nvidia-settings nvidia-xconfig libnvidia-fbc
"$(dirname "$0")/../shared/nvidia-kmod.sh"

dnf5 -y config-manager addrepo --from-repofile=https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo
dnf5 -y install --from-repo=nvidia-container-toolkit nvidia-container-toolkit nvidia-container-toolkit-base libnvidia-container-tools libnvidia-container1

dnf5 -y remove akmods akmod-nvidia
rm -fv /etc/yum.repos.d/nvidia-container-toolkit.repo /etc/yum.repos.d/fedora-nvidia.repo
