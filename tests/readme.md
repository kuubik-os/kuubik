# integration tests

pytest suite run over SSH against a VM booted from a built image. `tests/vm.Containerfile` adds sshd, passwordless sudo and autologin for `test_user`, so tests see a real plasma session.

Covers: kernel, nvidia driver stack, secure boot signing, desktop session and audio, system health (selinux, coredumps, failed units), update settings and `kctl-update-check`, brew, flatpak, multimedia codecs, gaming tunables, dev tooling (podman, distrobox, zsh, fonts), factory image and `kctl rollback`.

`test_90_rollback.py` reboots the VM twice and runs last.

```bash
just test-vm [nvidia|lts|lts-nvidia]
```
