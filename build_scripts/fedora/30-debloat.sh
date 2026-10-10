#!/usr/bin/env bash

set -ouex pipefail

groups_to_remove=(
	libreoffice
)

packages_to_remove=(
	libreoffice-core
	kmahjongg kmines kpat
	akregator kmail headerthemeeditor ktn neochat pimdataexporter sieveeditor
	kmousetool kmouth im-chooser korganizer kaddressbook khelpcenter
	dragon elisa-player kamoso kolourpaint skanpage k3b gcdmaster qrca ktorrent
	kdeconnect nwg-panel mediawriter krusader digikam showfoto uuctl
	kleopatra kcharselect kde-connect plasma-welcome kdebugsettings
	kjournald gnome-abrt kfind cockpit-system
	fedora-flathub-remote plasma-discover-rpm-ostree
	# users install a browser of choice via flatpak
	firefox firefox-langpacks
)

dnf5 -y group remove "${groups_to_remove[@]}"
dnf5 -y remove "${packages_to_remove[@]}"
