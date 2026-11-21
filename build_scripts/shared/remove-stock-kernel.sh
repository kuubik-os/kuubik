#!/usr/bin/env bash

# removes the base image kernel, called by {fedora,rhel}/10-kernel.sh before the cachyos install

set -ouex pipefail

# dnf5 on fedora, dnf4 on the lts base
DNF=$(command -v dnf5 || command -v dnf)

# stub out kernel-install hooks, initramfs is built in 90-finalize.sh
pushd /usr/lib/kernel/install.d
printf '%s\n' '#!/bin/sh' 'exit 0' >05-rpmostree.install
printf '%s\n' '#!/bin/sh' 'exit 0' >50-dracut.install
chmod +x 05-rpmostree.install 50-dracut.install
popd

for pkg in kernel kernel-core kernel-modules kernel-modules-core kernel-modules-extra kernel-uki-virt; do
	if rpm -q "$pkg" >/dev/null 2>&1; then
		"$DNF" -y remove "$pkg"
	fi
done
find /usr/lib/modules -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
find /boot -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
