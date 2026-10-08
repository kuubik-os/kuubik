# Functional / Integration Tests

Build checks alone are not enough to verify that an OS image actually works at runtime.

For example:
- Steam could crash on launch after an upstream regression
- a dependency update could break desktop startup
- Flatpak integration could silently stop working

Traditional build validation mainly confirms that:
- the image builds successfully
- dependencies resolve correctly
- packages install without conflicts

Fedora already provides strong guarantees in those areas. However, those checks do not validate the final integrated system behavior.

These tests add runtime validation for the produced image itself, helping catch regressions that only appear after boot. They cover core functionality only.

Current coverage includes:
1. CachyOS kernel is running, present in the boot cmdline, and versionlocked

2. NVIDIA flavor: the nvidia kernel module was built for the running kernel (skipped on the plain flavor; no GPU passthrough in the test VM, so the driver itself isn't exercised)

3. Desktop session
   - Wayland session is running
   - ananicy-cpp is active
   - no failed system or user systemd units

4. Update overrides
   - rpm-ostree automatic updates are disabled
   - flathub is the default flatpak remote
   - the booted deployment's version label matches the expected scheme
   - `kctl-update-check` runs cleanly and its notify timer is enabled

5. Homebrew: installed, owned by the test user, and package install/run/uninstall works

6. Flatpak: application install/uninstall works
