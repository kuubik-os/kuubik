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
