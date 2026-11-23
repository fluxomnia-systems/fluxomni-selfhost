#!/usr/bin/env python3
"""Check public self-host tags and installer assets before publishing release docs."""

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

REPO = "https://github.com/fluxomnia-systems/fluxomni-selfhost.git"
RAW = "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost"
TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+")


def published_tags():
    refs = subprocess.check_output(["git", "ls-remote", "--refs", "--tags", REPO], text=True, timeout=30)
    return {line.split()[1].removeprefix("refs/tags/") for line in refs.splitlines()}


def asset_available(ref, path):
    try:
        with urlopen(f"{RAW}/{ref}/{path}", timeout=10) as response:
            return response.status == 200
    except (URLError, OSError):
        return False


def publication_errors(manifest, tags, available):
    releases = manifest["releases"]
    latest = manifest["latestStable"]
    if not isinstance(latest, str) or not TAG.fullmatch(latest) or latest not in releases:
        return ["latestStable must name a stable release entry"]
    errors = []
    if latest not in tags:
        errors.append(f"latestStable {latest} has no published self-host tag")
    for version, release in releases.items():
        ref = release["selfhostRef"]
        if not isinstance(ref, str) or not TAG.fullmatch(ref):
            errors.append(f"{version}: invalid stable selfhostRef")
            continue
        if ref not in tags:
            errors.append(f"{version}: selfhostRef {ref} has no published tag")
            continue
        bundle = release.get("installerBundleRef", ref)
        path = release.get("installerPath", "scripts/install-runtime.sh")
        if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+|[0-9a-f]{40}", bundle) or path not in {"install.sh", "scripts/install-runtime.sh"}:
            errors.append(f"{version}: invalid installer bundle ref or path")
        elif not available(bundle, path):
            errors.append(f"{version}: {RAW}/{bundle}/{path} did not return HTTP 200")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        errors = publication_errors(json.loads(args.manifest.read_text()), published_tags(), asset_available)
    except (KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Error: could not verify release publication: {error}\n")
    for error in errors:
        print(f"Error: {error}")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
