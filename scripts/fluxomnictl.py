#!/usr/bin/env python3
"""Fluxomni local admin tool for self-hosted installs.

One tool serves every install on this host. It finds the install folder by
itself, so it works from any directory.
"""

import argparse
import os
import re
import sys
from pathlib import Path

TARGETS = ("full", "media-node")
DEFAULT_FOLDERS = {"full": "fluxomni", "media-node": "fluxomni-media-node"}


class CtlError(Exception):
    """A safe, credential-free failure shown to the operator."""


class Install:
    """One existing install folder and its target."""

    def __init__(self, path, target):
        self.path = Path(path)
        self.target = target

    def __repr__(self):
        return f"{self.path} ({self.target})"


def service_pattern(name):
    return re.compile(r"^[ \t]*[\"']?" + re.escape(name) + r"[\"']?[ \t]*:", re.MULTILINE)


CONTROL_PLANE = service_pattern("control-plane")
MEDIA_NODE = service_pattern("media-node")


def compose_text(path):
    """Read every regular Compose file in an install folder, ignoring bad ones."""
    texts = []
    for item in sorted(path.glob("*.yml")):
        if not (item.name.startswith(("docker-compose", "compose"))):
            continue
        try:
            if item.is_file() and not item.is_symlink():
                texts.append(item.read_text(errors="replace"))
        except OSError:
            continue
    return "\n".join(texts)


def install_target(path):
    """Return the target of an install folder, or None when it is not one.

    Reads all Compose files because the installer splits them into release,
    defaults, and overlay files. Needs a media-node service in every install.
    """
    path = Path(path)
    try:
        if not (path / ".env").is_file():
            return None
        text = compose_text(path)
    except OSError:
        return None
    if not MEDIA_NODE.search(text):
        return None
    return "full" if CONTROL_PLANE.search(text) else "media-node"


def home_directory(environ):
    home = environ.get("HOME")
    return Path(home) if home else Path.home()


def candidate_folders(home, target):
    names = [target] if target else list(TARGETS)
    return [(home / DEFAULT_FOLDERS[name]) for name in names]


def describe(installs):
    return ", ".join(str(item.path) for item in installs)


def select_install(directory=None, target=None, cwd=None, environ=None, interactive=False, ask=input):
    """Pick one install by explicit folder, current folder, or default folders.

    Order: --dir, FLUXOMNI_DIR, current folder, then the default folders.
    Two matches ask on a terminal and fail with both paths otherwise.
    """
    environ = os.environ if environ is None else environ
    cwd = Path(cwd or os.getcwd())
    source = "--dir" if directory is not None else "FLUXOMNI_DIR"
    explicit = directory if directory is not None else environ.get("FLUXOMNI_DIR")
    if explicit is not None and not explicit.strip():
        raise CtlError(f"{source} is empty")
    if explicit:
        if explicit == "~" or explicit.startswith("~/"):
            explicit = str(home_directory(environ) / explicit[2:])
        explicit = str(Path(explicit).resolve())
        found = install_target(explicit)
        if found is None:
            raise CtlError(f"{explicit} (from {source}) is not a Fluxomni install folder: it needs .env and Compose files with a media-node service")
        if target and found != target:
            raise CtlError(f"{explicit} is a {found} install, not {target}")
        return Install(explicit, found)
    found = install_target(cwd.resolve())
    if found and (not target or found == target):
        return Install(cwd.resolve(), found)
    home = home_directory(environ)
    installs = []
    seen = set()
    for folder in candidate_folders(home, target):
        real = folder.resolve()
        kind = install_target(real)
        if kind and (not target or kind == target) and real not in seen:
            seen.add(real)
            installs.append(Install(real, kind))
    if not installs:
        checked = ", ".join(str(folder) for folder in candidate_folders(home, target))
        raise CtlError(f"no Fluxomni install found. Checked: {checked}. Use --dir to select one")
    if len(installs) == 1:
        return installs[0]
    if not interactive:
        raise CtlError(f"more than one install found: {describe(installs)}. Use --dir or --target to select one")
    for number, item in enumerate(installs, 1):
        print(f"  {number}) {item.path} ({item.target})", file=sys.stderr)
    try:
        answer = ask("Select an install [1-%d]: " % len(installs)).strip()
    except (EOFError, KeyboardInterrupt):
        raise CtlError("no install selected") from None
    if not answer.isdigit() or not 1 <= int(answer) <= len(installs):
        raise CtlError("no install selected")
    return installs[int(answer) - 1]


def build_parser():
    parser = argparse.ArgumentParser(prog="fluxomnictl", description=__doc__)
    parser.add_argument("--dir", help="install folder (default: find it automatically)")
    parser.add_argument("--target", choices=TARGETS, help="only consider installs of this target")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    commands.add_parser("where", help="print the selected install folder and target")
    return parser


def main(argv=None, environ=None, cwd=None, interactive=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    interactive = sys.stdin.isatty() and sys.stderr.isatty() if interactive is None else interactive
    try:
        install = select_install(args.dir, args.target, cwd, environ, interactive)
        if args.command == "where":
            print(f"{install.path} {install.target}")
    except CtlError as error:
        print(f"Error: {error}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
