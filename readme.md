# kuubik: minimal OS

list of changes: https://kuubik-os.github.io/


## install
to use it firstly install fedora kinoite, and switch to unsigned image first:

```bash
rpm-ostree rebase ostree-unverified-registry:ghcr.io/kuubik-os/kuubik
```

and then after reboot switch to signed version:
```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/kuubik-os/kuubik
```

## nvidia
for nvidia version, use nvidia image name:

```bash
rpm-ostree rebase ostree-unverified-registry:ghcr.io/kuubik-os/kuubik-nvidia
```

reboot, and then:
```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/kuubik-os/kuubik-nvidia
```

## credits

all of that work is based on other OSS projects. Huge thanks to:

https://github.com/ublue-os/bazzite/

https://fedoraproject.org/atomic-desktops/kinoite/download/

https://rpmfusion.org/

