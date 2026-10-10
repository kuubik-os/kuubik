#!/usr/bin/env bash
# make live image same way it done in
# https://github.com/ublue-os/bazzite/tree/main/installer

set -ouex pipefail

INSTALL_IMAGE_PAYLOAD=${INSTALL_IMAGE_PAYLOAD:?}

mkdir -p "$(realpath /root)"

podman pull "${INSTALL_IMAGE_PAYLOAD}"

cp -a /src/system_files/. /

# live initramfs for the cachyos kernel shipped in the image
dnf5 -y install dracut-live
KERNEL_VERSION=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f\n' -quit)
DRACUT_NO_XATTR=1 dracut -v --force --zstd --reproducible --no-hostonly \
	--add "dmsquash-live dmsquash-live-autooverlay" \
	"/usr/lib/modules/${KERNEL_VERSION}/initramfs.img" "${KERNEL_VERSION}"

dnf5 -y install livesys-scripts
sed -i "s/^livesys_session=.*/livesys_session=kde/" /etc/sysconfig/livesys
systemctl enable livesys.service livesys-late.service

# anaconda web ui needs native browser
dnf5 -y install --enable-repo=fedora-cisco-openh264 --allowerasing firefox anaconda-live libblockdev-{btrfs,lvm,dm}
mkdir -p /var/lib/rpm-state

cat <<KSEOF >>/usr/share/anaconda/interactive-defaults.ks

%pre
mkdir -p /tmp/anaconda_custom_logs
%end

ostreecontainer --url=${INSTALL_IMAGE_PAYLOAD} --transport=containers-storage --no-signature-verification
%include /usr/share/anaconda/post-scripts/switch-to-signed.ks
%include /usr/share/anaconda/post-scripts/restore-selinux-labels.ks
%include /usr/share/anaconda/post-scripts/zsh-default-shell.ks
KSEOF

# point installed system at signed registry image for updates
cat <<KSEOF >/usr/share/anaconda/post-scripts/switch-to-signed.ks
%post --erroronfail --log=/tmp/anaconda_custom_logs/bootc-switch.log
bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry ${INSTALL_IMAGE_PAYLOAD}
%end
KSEOF

for unit in brew-setup.service flatpak-add-fedora-repos.service; do
	if systemctl list-unit-files "${unit}" &>/dev/null; then
		systemctl disable "${unit}"
	fi
done
systemctl --global disable kctl-update-notify.timer

# image-builder needs gcdx64.efi and expects the efi dir in /boot/efi
dnf5 -y install grub2-efi-x64-cdboot
mkdir -p /boot/efi
cp -av /usr/lib/efi/*/*/EFI /boot/efi/
cp -v /boot/efi/EFI/fedora/grubx64.efi /boot/efi/EFI/BOOT/fbx64.efi

rm -f /etc/localtime
systemd-firstboot --timezone UTC

# live / is an overlay backed by a small /run tmpfs, ostree needs much more room in /var/tmp
rm -rf /var/tmp
mkdir /var/tmp
cat >/etc/systemd/system/var-tmp.mount <<'UNITEOF'
[Unit]
Description=Larger tmpfs for /var/tmp on live system

[Mount]
What=tmpfs
Where=/var/tmp
Type=tmpfs
Options=size=50%%,nr_inodes=1m,x-systemd.graceful-option=usrquota

[Install]
WantedBy=local-fs.target
UNITEOF
systemctl enable var-tmp.mount

mkdir -p /usr/lib/bootc-image-builder
cp /src/iso.yaml /usr/lib/bootc-image-builder/iso.yaml

dnf5 -y clean all
