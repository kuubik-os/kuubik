"""Replace the fedora install entry in netinstall grub configs with one entry per kuubik flavor."""

import re
import sys

FLAVORS = [
    ("kuubik", "kuubik"),
    ("kuubik-nvidia", "kuubik (nvidia)"),
    ("kuubik-lts", "kuubik LTS"),
    ("kuubik-lts-nvidia", "kuubik LTS (nvidia)"),
]


def edit(cfg: str) -> str:
    """Return cfg with a menu entry per flavor, defaulting to the first one."""
    entry = re.search(r"^menuentry 'Install Fedora \d+'.*?^}\n", cfg, re.M | re.S)
    if not entry:
        sys.exit("install menu entry not found")
    entries = ""
    for image, title in FLAVORS:
        new = re.sub(r"'Install Fedora \d+'", f"'Install {title}'", entry.group(0))
        new = re.sub(r"^(\s*linux\S* .*)$", rf"\1 kuubik.image={image}", new, flags=re.M)
        entries += new
    cfg = cfg[: entry.start()] + entries + cfg[entry.end() :]
    cfg = re.sub(r'^set default=".*"$', 'set default="0"', cfg, flags=re.M)
    # remaining entries (media test, troubleshooting) install the default flavor
    return re.sub(r"(menuentry '[^']*)Fedora \d+", r"\1kuubik", cfg)


def main() -> None:
    """Edit every grub config passed on the command line in place."""
    for path in sys.argv[1:]:
        with open(path) as f:
            cfg = f.read()
        with open(path, "w") as f:
            f.write(edit(cfg))


if __name__ == "__main__":
    main()
