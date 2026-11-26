import os
import shlex
import subprocess
from pathlib import Path
from typing import Callable, Iterator

import pytest

FLAVORS = ("kuubik", "kuubik-nvidia")


def pytest_configure(config: pytest.Config) -> None:
    """refuse to run without knowing which image is under test"""
    # guessing the flavor from the image would skip every nvidia test when the nvidia bits go missing
    flavor = os.environ.get("KUUBIK_FLAVOR", "")
    if flavor not in FLAVORS:
        raise pytest.UsageError(f"KUUBIK_FLAVOR must be one of {FLAVORS}, got {flavor!r}")


def _run(
    command: str, check: bool = True, input: str | None = None
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, check=False, input=input
    )
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
    kernels = run("ls /usr/lib/modules").stdout.split()
    assert len(kernels) == 1, f"expected exactly one kernel, found {kernels}"
    return kernels[0]


@pytest.fixture(scope="session")
def flavor() -> str:
    """image target under test, kuubik or kuubik-nvidia"""
    return os.environ["KUUBIK_FLAVOR"]


@pytest.fixture(scope="session")
def is_nvidia(flavor) -> bool:
    """whether the image is an nvidia flavor"""
    return flavor == "kuubik-nvidia"


@pytest.fixture(scope="session")
def image_version() -> str:
    """IMAGE_VERSION the image was built with, empty for local builds"""
    return os.environ.get("KUUBIK_IMAGE_VERSION", "")


@pytest.fixture(scope="session")
def fedora_version() -> str:
    """FEDORA_VERSION the image was built from"""
    return os.environ.get("KUUBIK_FEDORA_VERSION", "")


class Stubs:
    """fake commands on PATH that log their arguments, for testing scripts without a booted system"""

    def __init__(self, root: Path) -> None:
        self.bin = root / "bin"
        self.bin.mkdir()
        self.log = root / "calls"
        self.log.touch()
        self.extra: list[Path] = []

    def add(self, name: str, body: str = "", path: str | None = None, log: bool = True) -> None:
        """install a stub that logs "name args" and then runs body"""
        target = Path(path) if path else self.bin / name
        if path:
            self.touch(path)
        logline = f'echo "{name} $*" >>{shlex.quote(str(self.log))}\n' if log else ""
        target.write_text(f"#!/bin/bash\n{logline}{body}\n")
        target.chmod(0o755)

    def touch(self, path: str) -> None:
        """create a file outside the test's tmp dir, removed after the test"""
        target = Path(path)
        # resolve: /home is a symlink to /var/home, which may not exist yet
        target.parent.resolve().mkdir(parents=True, exist_ok=True)
        target.touch()
        self.extra.append(target)

    def calls(self) -> list[str]:
        """logged stub calls, in order"""
        return self.log.read_text().splitlines()

    def run(self, command: str, input: str = "") -> subprocess.CompletedProcess[str]:
        """run a command with the stubs first on PATH, never fails by itself"""
        return _run(f"PATH={shlex.quote(str(self.bin))}:$PATH {command}", check=False, input=input)


@pytest.fixture
def stubs(tmp_path) -> Iterator[Stubs]:
    """per test stub commands, sudo just runs its arguments"""
    stubs = Stubs(tmp_path)
    stubs.add("sudo", 'exec "$@"', log=False)
    yield stubs
    for path in stubs.extra:
        path.unlink(missing_ok=True)
