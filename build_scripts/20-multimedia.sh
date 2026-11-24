#!/usr/bin/env bash

set -ouex pipefail

dnf5 -y install \
	"https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
	"https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"

dnf5 -y swap ffmpeg-free ffmpeg --allowerasing
# i686 for steam, otherwise it pulls fedora's 32-bit mesa that conflicts with freeworld
dnf5 -y install intel-media-driver mesa-va-drivers-freeworld mesa-va-drivers-freeworld.i686
dnf5 -y swap mesa-vulkan-drivers{,-freeworld}
dnf5 -y install mesa-vulkan-drivers-freeworld.i686
dnf5 -y install @multimedia --setopt="install_weak_deps=False" --exclude=PackageKit-gstreamer-plugin

dnf5 -y install --enable-repo=rpmfusion-nonfree-steam steam

# latest proton-cachyos release, steam picks it up from the system compatibilitytools.d
proton_tag=$(curl -fsSLI -o /dev/null -w '%{url_effective}' https://github.com/CachyOS/proton-cachyos/releases/latest)
proton_tag=${proton_tag##*/}
proton="proton-${proton_tag}-x86_64"
proton_url="https://github.com/CachyOS/proton-cachyos/releases/download/${proton_tag}/${proton}"
curl -fsSL "${proton_url}.tar.xz" -o "/tmp/${proton}.tar.xz"
curl -fsSL "${proton_url}.sha512sum" -o "/tmp/${proton}.sha512sum"
(cd /tmp && sha512sum --check "${proton}.sha512sum")
mkdir -p /usr/share/steam/compatibilitytools.d
tar -xJf "/tmp/${proton}.tar.xz" -C /usr/share/steam/compatibilitytools.d
rm -f "/tmp/${proton}.tar.xz" "/tmp/${proton}.sha512sum"

dnf5 -y remove rpmfusion-free-release rpmfusion-nonfree-release
