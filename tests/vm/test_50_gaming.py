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

