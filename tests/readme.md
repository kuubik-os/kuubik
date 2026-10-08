# integration tests

pytest suite run over SSH against a VM booted from a built image. Covers core runtime behavior only: kernel, nvidia kmod, desktop session, update settings, brew, flatpak.

```bash
just test-vm [nvidia]
```
