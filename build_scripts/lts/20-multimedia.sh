#!/usr/bin/env bash

set -ouex pipefail

dnf -y install --nogpgcheck \
	"https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-$(rpm -E %rhel).noarch.rpm" \
	"https://mirrors.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-$(rpm -E %rhel).noarch.rpm"

dnf -y install --allowerasing \
	ffmpeg \
	intel-media-driver \
	gstreamer1-plugin-libav \
	gstreamer1-plugins-bad-freeworld \
	gstreamer1-plugins-ugly

dnf -y remove rpmfusion-free-release rpmfusion-nonfree-release
