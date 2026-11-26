# integration tests

two pytest suites against a built image.

## podman

`tests/podman/` runs inside the image under test (`tests/podman.Containerfile` adds pytest), so it only covers what needs no booted system: system health (presets, unit verification, missing libraries, package integrity, unowned and setuid files, selinux policy labels), kernel and initramfs contents, kernel modules and signing, nvidia driver stack (and its absence in the plain flavor), debloat, repos, rpm dependencies, unit enablement and unit files, shipped config, multimedia codecs, gaming, dev tooling (rootless subids, brew unpacked by its own unit, zsh as a user, distrobox, toolbox, qemu, python venvs), container policy, and every `kctl`/`kctl-update-check` path with stubbed commands. Runs on every PR in about a minute.

The image under test is described, not guessed: the flavor defaults from the image name and `version` checks `os-release`. CI passes both. Images are always secure boot signed, so an unsigned kernel fails.

```bash
just test-podman localhost/kuubik:latest
just test-podman localhost/raw-img:latest kuubik-nvidia 20261126.1
```

## vm

`tests/vm/` runs over SSH against a VM booted from the image. `tests/vm.Containerfile` adds sshd, passwordless sudo and autologin for `test_user`, so tests see a real plasma session.

Covers: booted kernel, nvidia kargs, desktop session and audio, system health (selinux, coredumps, failed units), version label, brew, flatpak, gaming tunables, podman and distrobox, factory image and `kctl rollback`. Runs only for releases (schedule or manual dispatch).

`test_90_rollback.py` reboots the VM twice and runs last.

```bash
just test-vm [nvidia]
```
