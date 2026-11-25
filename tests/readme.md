# integration tests

two pytest suites against a built image.

## podman

`tests/podman/` runs inside the image under test (`tests/podman.Containerfile` adds pytest), so it only covers what needs no booted system: kernel modules and signing, nvidia driver stack, unit enablement, `kctl-update-check`, multimedia codecs, vulkan drivers, dev tooling, container policy, `kctl` basics. Runs on every PR in about a minute.

```bash
just test-podman localhost/kuubik:latest
```

## vm

`tests/vm/` runs over SSH against a VM booted from the image. `tests/vm.Containerfile` adds sshd, passwordless sudo and autologin for `test_user`, so tests see a real plasma session.

Covers: booted kernel, nvidia kargs, desktop session and audio, system health (selinux, coredumps, failed units), version label, brew, flatpak, gaming tunables, podman and distrobox, factory image and `kctl rollback`. Runs only for releases (schedule or manual dispatch).

`test_90_rollback.py` reboots the VM twice and runs last.

```bash
just test-vm [nvidia]
```
