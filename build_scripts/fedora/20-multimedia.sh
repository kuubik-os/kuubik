#!/usr/bin/env bash

set -ouex pipefail

dnf5 -y install \
	"https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
	"https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"

dnf5 -y swap ffmpeg-free ffmpeg --allowerasing
dnf5 -y install intel-media-driver mesa-va-drivers-freeworld
dnf5 -y swap mesa-vulkan-drivers{,-freeworld}
dnf5 -y install @multimedia --setopt="install_weak_deps=False" --exclude=PackageKit-gstreamer-plugin

# 32-bit freeworld mesa for steam, otherwise it pulls fedora's i686 mesa that conflicts with the x86_64 freeworld ones
dnf5 -y install --enable-repo=rpmfusion-nonfree-steam steam mesa-va-drivers-freeworld.i686 mesa-vulkan-drivers-freeworld.i686

# proton-cachyos, steam picks it up from the system compatibilitytools.d
proton_url="https://github.com/CachyOS/proton-cachyos/releases/download/cachyos-11.0-20261015-slr/proton-cachyos-11.0-20261015-slr-x86_64.tar.xz"
proton_sha512="0b46e290b08bc7b45265742cd72debbd69644875f99beef5f699aa06f61848c2e340a83d8ca0f570074d6faadf8acd0827c090c68b9688ed493a41858505365f"
curl -fsSL "$proton_url" -o /tmp/proton-cachyos.tar.xz
echo "${proton_sha512}  /tmp/proton-cachyos.tar.xz" | sha512sum --check
mkdir -p /usr/share/steam/compatibilitytools.d
tar -xJf /tmp/proton-cachyos.tar.xz -C /usr/share/steam/compatibilitytools.d
rm -f /tmp/proton-cachyos.tar.xz

dnf5 -y remove rpmfusion-free-release rpmfusion-nonfree-release
