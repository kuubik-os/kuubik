import os
import subprocess
import time
from pathlib import Path
from typing import Callable

import pytest

from defaults import TEST_USER as DEFAULT_TEST_USER

TEST_HOST = os.getenv("TEST_SSH_HOST", "127.0.0.1")
TEST_PORT = os.getenv("TEST_SSH_PORT", "2222")
TEST_USER = os.getenv("TEST_SSH_USER", DEFAULT_TEST_USER)
TEST_KEY = Path(os.getenv("TEST_SSH_KEY", "/ssh/test_user"))

# same signal 60-nvidia.sh images ship, copied from system_files/nvidia
NVIDIA_FLAVOR_MARKER = "/usr/lib/dracut/dracut.conf.d/99-nvidia.conf"

assert TEST_KEY.is_file(), f"SSH key not found: {TEST_KEY}"


def _ssh(command: str, *options: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "ssh",
            "-i", str(TEST_KEY),
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            *options,
            "-p", TEST_PORT,
            f"{TEST_USER}@{TEST_HOST}",
            command,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="session")
def wait_for_ssh() -> None:
    """wait until the test vm accepts ssh logins"""

    deadline = time.time() + int(os.getenv("TEST_SSH_WAIT_SECONDS", "1800"))
    while time.time() < deadline:
        if _ssh("true", "-o", "ConnectTimeout=5").returncode == 0:
            return
        time.sleep(5)

    raise TimeoutError("SSH host did not become available")


@pytest.fixture(scope="session")
def ssh_command(wait_for_ssh: None) -> Callable[..., subprocess.CompletedProcess[str]]:
    """run a shell command on the test vm, fail on non-zero exit unless check is false"""

    def run(command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = _ssh(command)
        if check and result.returncode != 0:
            raise AssertionError(
                f"Command failed: {command}\n"
                f"Return code: {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )
        return result

    return run


@pytest.fixture(scope="session")
def wait_for(ssh_command) -> Callable[..., subprocess.CompletedProcess[str]]:
    """poll a command on the test vm until it exits 0"""

    def run(command: str, timeout: int = 60, interval: int = 2) -> subprocess.CompletedProcess[str]:
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            last = ssh_command(command, check=False)
            if last.returncode == 0:
                return last
            time.sleep(interval)
        raise AssertionError(
            f"condition never became true within {timeout}s: {command}\n"
            f"last stdout: {last.stdout if last else ''}\n"
            f"last stderr: {last.stderr if last else ''}"
        )

    return run


@pytest.fixture(scope="session")
def reboot_vm(ssh_command) -> Callable[[], None]:
    """reboot the test vm and wait until it is back with a new boot id"""

    def run(timeout: int = 900) -> None:
        old_boot_id = ssh_command("cat /proc/sys/kernel/random/boot_id").stdout.strip()
        # the connection drops mid-command, so the exit code means nothing
        _ssh("sudo systemctl reboot", "-o", "ConnectTimeout=5")
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(5)
            result = _ssh("cat /proc/sys/kernel/random/boot_id", "-o", "ConnectTimeout=5")
            if result.returncode == 0 and result.stdout.strip() != old_boot_id:
                return
        raise TimeoutError("VM did not come back after reboot")

    return run


@pytest.fixture(scope="session")
def is_nvidia(ssh_command) -> bool:
    """whether the vm runs an nvidia flavor"""
    return ssh_command(f"test -f {NVIDIA_FLAVOR_MARKER}", check=False).returncode == 0


@pytest.fixture(scope="session")
def is_lts(ssh_command) -> bool:
    """whether the vm runs an lts (el based) flavor"""
    return ssh_command("grep -qx ID=fedora /usr/lib/os-release", check=False).returncode != 0


@pytest.fixture(scope="session")
def desktop_session(wait_for) -> None:
    """wait until the autologin plasma session is up"""
    wait_for("pgrep -u test_user -x plasmashell", timeout=600, interval=5)
