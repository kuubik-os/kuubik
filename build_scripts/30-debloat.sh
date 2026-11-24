#!/usr/bin/env bash

set -ouex pipefail

groups_to_remove=(
	libreoffice
)

packages_to_remove=(
	akregator
	cockpit-system
	digikam
	dragon
	elisa-player
	fedora-flathub-remote
	# users install a browser of choice via flatpak
	firefox
	firefox-langpacks
	gcdmaster
	gnome-abrt
	headerthemeeditor
	im-chooser
	k3b
	kaddressbook
	kamoso
	kcharselect
	kde-connect
	kdebugsettings
	kdeconnect
	kfind
	khelpcenter
	kjournald
	kleopatra
	kmahjongg
	kmail
	kmines
	kmousetool
	kmouth
	kolourpaint
	korganizer
	kpat
	krusader
	ktn
	ktorrent
	libreoffice-core
	mediawriter
	neochat
	nwg-panel
	pimdataexporter
	plasma-discover-rpm-ostree
	plasma-welcome
	qrca
	showfoto
	sieveeditor
	skanpage
	uuctl
)

dnf5 -y group remove "${groups_to_remove[@]}"
dnf5 -y remove "${packages_to_remove[@]}"

rm -fv /usr/share/applications/org.kde.kinfocenter.desktop
