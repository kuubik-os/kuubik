#!/usr/bin/env bash

set -ouex pipefail

# a real repo file, not --enablerepo: akmods runs its own dnf transactions
dnf5 -y config-manager addrepo --from-repofile=https://negativo17.org/repos/fedora-nvidia.repo

dnf5 -y install akmods nvtop
# akmod-nvidia's %post builds via akmodsbuild, which refuses to run as root.
# install it without scriptlets before the driver stack pulls it in normally
dnf5 -y install --setopt=tsflags=noscripts --from-repo=fedora-nvidia akmod-nvidia
dnf5 -y install --from-repo=fedora-nvidia nvidia-driver nvidia-driver-cuda xorg-x11-nvidia nvidia-settings nvidia-xconfig libnvidia-fbc

# build and sign the nvidia kmod for the cachyos kernel
# akmodsbuild needs writable scratch dirs in both
mkdir -p /var/tmp /tmp
chmod 1777 /var/tmp /tmp

KERNEL_VERSION=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f\n' -quit)
SB_KEY=/run/secrets/secureboot_key
CERT=/usr/share/kuubik/secureboot/kuubik.der

# akmods signs the kmod with the key pair in /etc/pki/akmods, use the kuubik secure boot key when the build has it
if [ -s "$SB_KEY" ]; then
	install -D -m 0640 -g akmods "$SB_KEY" /etc/pki/akmods/private/private_key.priv
	install -D -m 0644 "$CERT" /etc/pki/akmods/certs/public_key.der
fi
akmods --force --kernels "${KERNEL_VERSION}" --kmod nvidia

# akmods exits 0 even when the build fails
if ! find "/usr/lib/modules/${KERNEL_VERSION}" -iname 'nvidia.ko*' -print -quit | grep -q .; then
	echo "ERROR: nvidia kmod build failed for kernel ${KERNEL_VERSION}" >&2
	find /var/cache/akmods -iname '*.log' -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; >&2
	exit 1
fi

if [ -s "$SB_KEY" ]; then
	# sign whatever akmods left unsigned
	sign_file="/usr/src/kernels/${KERNEL_VERSION}/scripts/sign-file"
	while read -r mod; do
		if [ -z "$(modinfo -F signer "$mod")" ]; then
			case "$mod" in
			*.ko.xz)
				xz -d "$mod"
				"$sign_file" sha256 "$SB_KEY" "$CERT" "${mod%.xz}"
				# kernel xz decoder only supports crc32
				xz --check=crc32 "${mod%.xz}"
				;;
			*.ko) "$sign_file" sha256 "$SB_KEY" "$CERT" "$mod" ;;
			*)
				echo "ERROR: unsupported module compression: ${mod}" >&2
				exit 1
				;;
			esac
		fi
		signer=$(modinfo -F signer "$mod")
		if [ "$signer" != "kuubik secure boot" ]; then
			echo "ERROR: ${mod} not signed with the kuubik secure boot key (signer: '${signer}')" >&2
			exit 1
		fi
	done < <(find "/usr/lib/modules/${KERNEL_VERSION}/extra" -name '*.ko*')
	rm -f /etc/pki/akmods/private/private_key.priv
fi

dnf5 -y config-manager addrepo --from-repofile=https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo
dnf5 -y install --from-repo=nvidia-container-toolkit nvidia-container-toolkit nvidia-container-toolkit-base libnvidia-container-tools libnvidia-container1

dnf5 -y remove akmods akmod-nvidia
rm -fv /etc/yum.repos.d/nvidia-container-toolkit.repo /etc/yum.repos.d/fedora-nvidia.repo
rm -fv /usr/share/applications/nvtop.desktop
