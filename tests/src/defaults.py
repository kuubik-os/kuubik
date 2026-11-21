KERNEL_VERSION = "cachy"
TEST_USER = "test_user"

# lets ssh commands talk to the autologin plasma session
SESSION_ENV = (
    'export XDG_RUNTIME_DIR="/run/user/$(id -u)" WAYLAND_DISPLAY=wayland-0 '
    'DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus";'
)
