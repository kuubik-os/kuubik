KERNEL_VERSION = "cachy"
TEST_USER = "test_user"

# lets ssh commands talk to the autologin plasma session
SESSION_ENV = (
    'export XDG_RUNTIME_DIR="/run/user/$(id -u)" '
    'DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"; '
    # socket name differs between bases, take it from the running session
    'eval "$(systemctl --user show-environment | sed -n \'s/^WAYLAND_DISPLAY=/export WAYLAND_DISPLAY=/p\')";'
)
