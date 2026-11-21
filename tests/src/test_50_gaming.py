def test_max_map_count(ssh_command):
    # many games under proton crash below this
    value = int(ssh_command("sysctl -n vm.max_map_count").stdout)
    assert value >= 1048576, f"vm.max_map_count is {value}"


def test_open_files_hard_limit(ssh_command):
    # esync needs a high fd limit
    value = int(ssh_command("ulimit -Hn").stdout)
    assert value >= 524288, f"open files hard limit is {value}"


def test_ntsync_available(ssh_command):
    ssh_command("sudo modprobe ntsync && test -c /dev/ntsync")


def test_vulkan_drivers_present(ssh_command):
    result = ssh_command("ls /usr/share/vulkan/icd.d/")
    for icd in ("radeon_icd", "intel_icd"):
        assert icd in result.stdout, f"{icd} vulkan driver missing: {result.stdout}"
