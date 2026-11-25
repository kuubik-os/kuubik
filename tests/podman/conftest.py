import subprocess
from typing import Callable

import pytest

# same signal the vm suite uses, shipped by system_files/nvidia
NVIDIA_FLAVOR_MARKER = "/usr/lib/dracut/dracut.conf.d/99-nvidia.conf"


def _run(command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["bash", "-c", command], capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed: {command}\n"
            f"Return code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result


@pytest.fixture(scope="session")
def run() -> Callable[..., subprocess.CompletedProcess[str]]:
    """run a shell command in the image, fail on non-zero exit unless check is false"""
    return _run


@pytest.fixture(scope="session")
def kernel_version(run) -> str:
    """the image's kernel, uname -r would show the host's"""
    return run("ls /usr/lib/modules").stdout.strip()


@pytest.fixture(scope="session")
def is_nvidia(run) -> bool:
    """whether the image is an nvidia flavor"""
    return run(f"test -f {NVIDIA_FLAVOR_MARKER}", check=False).returncode == 0
