from defaults import TEST_USER

DISTROBOX = "kuubik-test-box"


def test_rootless_podman_runs_unsigned_image(ssh_command):
    # default reject must not block ordinary registries
    ssh_command(f"grep -q '^{TEST_USER}:' /etc/subuid")
    result = ssh_command("podman run --rm docker.io/library/alpine:latest echo ok")
    assert result.stdout.strip() == "ok", f"unexpected output: {result.stdout}"


def test_distrobox(ssh_command):
    ssh_command(f"distrobox create --yes --name {DISTROBOX} --image docker.io/library/alpine:latest")
    try:
        result = ssh_command(f"distrobox enter {DISTROBOX} -- cat /etc/os-release")
        assert "Alpine" in result.stdout, f"not inside the box: {result.stdout}"
    finally:
        ssh_command(f"distrobox rm --force {DISTROBOX}", check=False)
