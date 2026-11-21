# kuubik: minimal OS

list of changes: https://kuubik-os.github.io/


## images
- `kuubik`: fedora kinoite based
- `kuubik-nvidia`: `kuubik` with nvidia driver
- `kuubik-lts`: rhel/alma based
- `kuubik-lts-nvidia`: `kuubik-lts` with nvidia driver

## install
### iso
download the [netinstall ISO](https://github.com/kuubik-os/kuubik/releases/download/netinstall/kuubik-netinstall-amd64.iso), boot it and pick the image in the boot menu. it installs that image over the network, so it needs internet. works with secure boot on, see [secure boot](#secure-boot).

### rebase
from an existing fedora kinoite install (almalinux atomic desktop kde for lts images), switch to the unsigned image first (replace `kuubik` with the image you want):

```bash
rpm-ostree rebase ostree-unverified-registry:ghcr.io/kuubik-os/kuubik
```

and then after reboot switch to signed version:
```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/kuubik-os/kuubik
```

## secure boot
kernel and nvidia driver are signed with the kuubik key, which has to be enrolled once:
- ISO install: the key is queued during install. on first reboot pick "Enroll MOK" and enter password `kuubik`.
- rebase install: run `kctl enroll-secure-boot-key`, reboot, enroll, then enable secure boot.

## credits

all of that work is based on other OSS projects. Huge thanks to:

https://github.com/ublue-os

https://fedoraproject.org/atomic-desktops/kinoite

https://rpmfusion.org

https://negativo17.org/
