#!/usr/bin/env bash

set -ouex pipefail

# akmodsbuild needs writable scratch dirs in both
mkdir -p /var/tmp /tmp
chmod 1777 /var/tmp /tmp

KERNEL_VERSION=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f\n' -quit)

# a real repo file, not --enablerepo: akmods runs its own dnf transactions
dnf5 -y config-manager addrepo --from-repofile=https://negativo17.org/repos/fedora-nvidia.repo

dnf5 -y install akmods nvtop
# akmod-nvidia's %post builds via akmodsbuild, which refuses to run as root.
# install it without scriptlets before the driver stack pulls it in normally
dnf5 -y install --setopt=tsflags=noscripts --from-repo=fedora-nvidia akmod-nvidia
dnf5 -y install --from-repo=fedora-nvidia nvidia-driver nvidia-driver-cuda xorg-x11-nvidia nvidia-settings nvidia-xconfig libnvidia-fbc
akmods --force --kernels "${KERNEL_VERSION}" --kmod nvidia

# akmods exits 0 even when the build fails
if ! find "/usr/lib/modules/${KERNEL_VERSION}" -iname 'nvidia.ko*' -print -quit | grep -q .; then
	echo "ERROR: nvidia kmod build failed for kernel ${KERNEL_VERSION}" >&2
	find /var/cache/akmods -iname '*.log' -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; >&2
	exit 1
fi

dnf5 -y config-manager addrepo --from-repofile=https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo
dnf5 -y install --from-repo=nvidia-container-toolkit nvidia-container-toolkit nvidia-container-toolkit-base libnvidia-container-tools libnvidia-container1

dnf5 -y remove akmods akmod-nvidia
rm -fv /etc/yum.repos.d/nvidia-container-toolkit.repo /etc/yum.repos.d/fedora-nvidia.repo
