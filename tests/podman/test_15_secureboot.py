CERT = "/usr/share/kuubik/secureboot/kuubik.der"
SIGNER = "kuubik secure boot"


def test_secureboot_cert_and_mokutil(run):
    result = run(f"openssl x509 -inform der -in {CERT} -noout -subject")
    assert SIGNER in result.stdout, f"unexpected cert subject: {result.stdout}"
    run("command -v mokutil")


def test_kernel_modules_signed_with_kernel(run, kernel_version, is_nvidia):
    # the signature embeds the cert, so its subject shows up in the vmlinuz bytes
    signed = run(
        f"grep -aqF '{SIGNER}' /usr/lib/modules/{kernel_version}/vmlinuz", check=False
    ).returncode == 0
    assert signed, "kernel is not signed with the kuubik secure boot key"

    result = run(
        f"find /usr/lib/modules/{kernel_version}/extra -name '*.ko*' "
        "-exec sh -c 'echo \"$1 $(modinfo -F signer \"$1\")\"' _ {} \\;",
        check=False,
    )
    # an empty list would pass when the nvidia kmods are missing altogether
    assert result.stdout.strip() or not is_nvidia, "no out of tree modules in the nvidia flavor"
    unsigned = [line for line in result.stdout.splitlines() if not line.endswith(SIGNER)]
    assert unsigned == [], f"out of tree modules not signed by {SIGNER}: {unsigned}"
