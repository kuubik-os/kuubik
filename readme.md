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

## lts
lts images built on rhel/alma 10 instead of fedora. rebase same way, using `kuubik-lts` or `kuubik-lts-nvidia`:

```bash
rpm-ostree rebase ostree-unverified-registry:ghcr.io/kuubik-os/kuubik-lts
```

reboot, and then:
```bash
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/kuubik-os/kuubik-lts
```

## credits

all of that work is based on other OSS projects. Huge thanks to:

https://github.com/ublue-os

https://fedoraproject.org/atomic-desktops/kinoite

https://rpmfusion.org

https://negativo17.org/
