#!/usr/bin/env bash

set -ouex pipefail

packages_to_remove=(
	kde-connect kdeconnectd kcharselect plasma-welcome kdebugsettings
	kjournald kfind khelpcenter krfb krdp kde-partitionmanager
	cockpit cockpit-bridge cockpit-packagekit cockpit-storaged cockpit-system cockpit-ws cockpit-ws-selinux
	plasma-discover-offline-updates
)

dnf -y remove "${packages_to_remove[@]}"
