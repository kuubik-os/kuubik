#!/usr/bin/env bash

set -ouex pipefail

KERNEL_VERSION=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f\n' -quit)

mkdir -p /var/tmp
chmod 1777 /var/tmp

depmod -a "$KERNEL_VERSION"
DRACUT_NO_XATTR=1 /usr/bin/dracut \
	--no-hostonly \
	--kver "$KERNEL_VERSION" \
	--reproducible \
	--zstd -v \
	--add ostree \
	-f "/usr/lib/modules/$KERNEL_VERSION/initramfs.img"
chmod 0600 "/usr/lib/modules/$KERNEL_VERSION/initramfs.img"

# after dracut: the initramfs copies os-release, a version in it would change the initramfs every build.
# grub titles entries from os-release, keep it in sync with the image version label
if [ -n "${IMAGE_VERSION:-}" ]; then
	sed -i \
		-e "s|^VERSION=.*|VERSION=\"${IMAGE_VERSION} (kuubik)\"|" \
		-e "s|^PRETTY_NAME=.*|PRETTY_NAME=\"kuubik Linux ${IMAGE_VERSION}\"|" \
		-e "s|^OSTREE_VERSION=.*|OSTREE_VERSION='${IMAGE_VERSION}'|" \
		/usr/lib/os-release
fi

# mokutil enrolls the kuubik secure boot key, see kctl enroll-secure-boot-key
dnf5 -y install mokutil

# shim only boots kernels signed by a key in db or mok, cachyos kernel is not
SB_KEY=/run/secrets/secureboot_key
if [ ! -s "$SB_KEY" ]; then
	echo "ERROR: secureboot_key build secret is missing, images are always secure boot signed" >&2
	exit 1
fi
dnf5 -y install sbsigntools openssl
openssl x509 -inform der -in /usr/share/kuubik/secureboot/kuubik.der -out /tmp/kuubik.pem
VMLINUZ="/usr/lib/modules/$KERNEL_VERSION/vmlinuz"
sbsign --key "$SB_KEY" --cert /tmp/kuubik.pem --output "$VMLINUZ" "$VMLINUZ"
sbverify --cert /tmp/kuubik.pem "$VMLINUZ"
dnf5 -y remove sbsigntools

dnf5 -y remove "kernel-cachyos-*-devel-matched"
dnf5 -y clean all

rm -rfv /etc/yum.repos.d/*cachyos*
rm -rfv /run/akmods /run/dnf /run/selinux-policy /tmp/*
rm -fv /usr/lib/kernel/install.d/05-rpmostree.install /usr/lib/kernel/install.d/50-dracut.install
