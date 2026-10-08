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

These tests add runtime validation for the produced image itself, helping catch regressions that only appear after boot.

Current coverage includes:
1. SSH connectivity and correct user context

2. CachyOS kernel is installed and present in the boot cmdline

3. NVIDIA flavor validation (skipped on the plain flavor)
   - the negativo17 userspace driver packages are installed
   - the nvidia kernel module was actually built for the running kernel
   - no GPU passthrough in the test VM, so the driver itself isn't exercised -- this only checks the build produced what it should

4. Plasma desktop session
   - graphical.target is the default systemd target
   - display-manager.service is active
   - plasmalogin.service is active and selected as the display manager
   - Wayland session is running
   - Required plasma packages are installed
   - no failed system or user systemd units

5. Flatpak functionality
   - flatpak command is available
   - remote add/remove works
   - application install/uninstall works

6. Homebrew functionality
   - brew is installed, owned by the test user, and runs
   - package install/run/uninstall works
   - service install/start/uninstall works, including that the service's port is actually listening while started and closed once stopped

7. rpm-ostree state
   - the booted deployment's version label matches the expected scheme
   - exactly one deployment is present, booted, and tracks our own image
   - `rpm-ostree status` reports an idle state (no real `rpm-ostree upgrade` is run -- on a local/CI test VM the origin is a scratch image tag with nothing valid to pull)

8. Basic CLI file operations (create, touch, test, rm, rmdir)

9. IPv4 network connectivity (outbound ping)

The long-term goal is to expand coverage for critical user workflows and common failure scenarios.