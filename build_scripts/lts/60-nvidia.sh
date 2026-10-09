#!/usr/bin/env bash

set -ouex pipefail

# akmodsbuild needs writable scratch dirs in both
mkdir -p /var/tmp /tmp
chmod 1777 /var/tmp /tmp

KERNEL_VERSION=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f\n' -quit)

# a real repo file, not --enablerepo: akmods runs its own dnf transactions
dnf config-manager --add-repo https://negativo17.org/repos/epel-nvidia.repo

dnf -y install akmods nvtop
# akmod-nvidia's %post builds via akmodsbuild, which refuses to run as root.
# install it without scriptlets before the driver stack pulls it in normally
dnf -y install --setopt=tsflags=noscripts akmod-nvidia
dnf -y install nvidia-driver nvidia-driver-cuda nvidia-settings nvidia-xconfig libnvidia-fbc
akmods --force --kernels "${KERNEL_VERSION}" --kmod nvidia

# akmods exits 0 even when the build fails
if ! find "/usr/lib/modules/${KERNEL_VERSION}" -iname 'nvidia.ko*' -print -quit | grep -q .; then
	echo "ERROR: nvidia kmod build failed for kernel ${KERNEL_VERSION}" >&2
	find /var/cache/akmods -iname '*.log' -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; >&2
	exit 1
fi

dnf config-manager --add-repo https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo
dnf -y install nvidia-container-toolkit nvidia-container-toolkit-base libnvidia-container-tools libnvidia-container1

dnf -y remove akmods akmod-nvidia
rm -fv /etc/yum.repos.d/nvidia-container-toolkit.repo /etc/yum.repos.d/epel-nvidia.repo
