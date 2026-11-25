def test_vulkan_drivers_present(run):
    result = run("ls /usr/share/vulkan/icd.d/")
    for icd in ("radeon_icd", "intel_icd"):
        assert icd in result.stdout, f"{icd} vulkan driver missing: {result.stdout}"
