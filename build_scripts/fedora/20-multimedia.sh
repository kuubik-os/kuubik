#!/usr/bin/env bash

set -ouex pipefail

dnf5 -y install \
	"https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
	"https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"

dnf5 -y swap ffmpeg-free ffmpeg --allowerasing
dnf5 -y install intel-media-driver mesa-va-drivers-freeworld
dnf5 -y swap mesa-vulkan-drivers{,-freeworld}
dnf5 -y install @multimedia --setopt="install_weak_deps=False" --exclude=PackageKit-gstreamer-plugin

dnf5 -y remove rpmfusion-free-release rpmfusion-nonfree-release
