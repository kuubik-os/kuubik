def test_kctl_help_and_unknown_command(run):
    run("kctl help")
    result = run("kctl no-such-command", check=False)
    assert result.returncode == 1, f"unknown command exited {result.returncode}"


def test_kctl_upgrade_can_be_declined(run):
    result = run("echo n | kctl upgrade")
    assert "Aborted." in result.stdout, f"unexpected output: {result.stdout}"
