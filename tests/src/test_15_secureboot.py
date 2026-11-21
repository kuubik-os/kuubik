import pytest

CERT = "/usr/share/kuubik/secureboot/kuubik.der"
SIGNER = "kuubik secure boot"


def test_secureboot_cert_and_mokutil(ssh_command):
    result = ssh_command(f"openssl x509 -inform der -in {CERT} -noout -subject")
    assert SIGNER in result.stdout, f"unexpected cert subject: {result.stdout}"
    ssh_command("command -v mokutil")


def test_kernel_modules_signed_with_kernel(ssh_command):
    # builds without the secureboot_key secret (fork PRs) are unsigned on purpose.
    # the signature embeds the cert, so its subject shows up in the vmlinuz bytes
    signed = ssh_command(
        f"grep -aqF '{SIGNER}' /usr/lib/modules/$(uname -r)/vmlinuz", check=False
    ).returncode == 0
    if not signed:
        pytest.skip("kernel is not signed, image built without the secure boot key")

    result = ssh_command(
        "find /usr/lib/modules/$(uname -r)/extra -name '*.ko*' "
        "-exec sh -c 'echo \"$1 $(modinfo -F signer \"$1\")\"' _ {} \\;",
        check=False,
    )
    unsigned = [line for line in result.stdout.splitlines() if not line.endswith(SIGNER)]
    assert unsigned == [], f"out of tree modules not signed by {SIGNER}: {unsigned}"
