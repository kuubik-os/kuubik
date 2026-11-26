import pytest

PROTON_DIR = "/usr/share/steam/compatibilitytools.d"


@pytest.mark.parametrize("arch", ["x86_64", "i686"])
@pytest.mark.parametrize("icd", ["radeon_icd", "intel_icd"])
def test_vulkan_drivers_present(run, icd, arch):
    # steam's 32 bit games need the i686 drivers
    run(f"test -f /usr/share/vulkan/icd.d/{icd}.{arch}.json")


def test_steam_installed(run):
    run("rpm -q steam")


def test_proton_cachyos_installed(run):
    result = run(f"find {PROTON_DIR} -mindepth 2 -maxdepth 2 -name compatibilitytool.vdf")
    tools = result.stdout.split()
    assert len(tools) == 1, f"expected one proton-cachyos in {PROTON_DIR}, found {tools}"
    tool_dir = tools[0].rsplit("/", 1)[0]
    assert "proton-cachyos" in tool_dir, f"unexpected compatibility tool {tool_dir}"
    run(f"test -x {tool_dir}/proton")
