#!/usr/bin/env bash

set -ouex pipefail

# https://rpmfusion.org/Howto/Multimedia
dnf5 -y install \
	"https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
	"https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"

dnf5 -y swap ffmpeg-free ffmpeg --allowerasing
dnf5 -y install @multimedia --setopt="install_weak_deps=False" --exclude=PackageKit-gstreamer-plugin

dnf5 -y install intel-media-driver

# terra mesa is newer than fedora's and built with all video codecs, so no freeworld swap.
# terra-mesa has priority 80, so steam's i686 mesa comes from terra too
dnf5 -y install --nogpgcheck --repofrompath "terra,https://repos.fyralabs.com/terra\$releasever" terra-release terra-release-mesa
dnf5 -y upgrade --from-repo=terra-mesa 'mesa*'
dnf5 -y install --from-repo=terra-mesa mesa-dri-drivers.i686 mesa-vulkan-drivers.i686
dnf5 -y install --from-repo=terra steam

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

dnf5 -y remove rpmfusion-free-release rpmfusion-nonfree-release terra-release terra-release-mesa terra-gpg-keys
