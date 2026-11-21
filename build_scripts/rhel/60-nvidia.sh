#!/usr/bin/env bash

set -ouex pipefail

# a real repo file, not --enablerepo: akmods runs its own dnf transactions
dnf config-manager --add-repo https://negativo17.org/repos/epel-nvidia.repo

dnf -y install akmods nvtop
# akmod-nvidia's %post builds via akmodsbuild, which refuses to run as root.
# install it without scriptlets before the driver stack pulls it in normally
dnf -y install --setopt=tsflags=noscripts akmod-nvidia
dnf -y install nvidia-driver nvidia-driver-cuda nvidia-settings libnvidia-fbc
"$(dirname "$0")/../shared/nvidia-kmod.sh"

dnf config-manager --add-repo https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo
dnf -y install nvidia-container-toolkit nvidia-container-toolkit-base libnvidia-container-tools libnvidia-container1

dnf -y remove akmods akmod-nvidia
rm -fv /etc/yum.repos.d/nvidia-container-toolkit.repo /etc/yum.repos.d/epel-nvidia.repo
