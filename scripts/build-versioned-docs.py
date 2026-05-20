#!/usr/bin/env python3
"""Create versioned mdBook aliases from the public release manifest."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def copy_book_tree(source: Path, destination: Path, skip_names: set[str]) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    for item in source.iterdir():
        if item.name in skip_names:
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(".DS_Store"))
        elif item.name != ".DS_Store":
            shutil.copy2(item, target)


def render_versions_json(manifest: dict[str, Any]) -> str:
    latest = manifest["latestStable"]
    releases = []
    for version, release in sorted(manifest.get("releases", {}).items(), reverse=True):
        releases.append(
            {
                "version": version,
                "coreVersion": release.get("coreVersion"),
                "releasedAt": release.get("releasedAt"),
                "path": release.get("docsStablePath", "/")
                if version == latest
                else release.get("docsVersionPath", f"/{version}/"),
                "latest": version == latest,
            }
        )
    payload = {
        "schemaVersion": 1,
        "latestStable": latest,
        "releases": releases,
        "edge": manifest.get("edge"),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book-dir", default="docs/book")
    parser.add_argument("--manifest", default="docs/src/release-manifest.json")
    args = parser.parse_args()

    book_dir = Path(args.book_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path)
    releases = manifest.get("releases", {})
    version_names = set(releases)
    skip_names = {*version_names, "edge"}

    if not book_dir.exists():
        raise SystemExit(f"{book_dir} does not exist. Run mdbook build first.")

    versions_json = render_versions_json(manifest)
    (book_dir / "versions.json").write_text(versions_json, encoding="utf-8")

    for version in sorted(version_names):
        copy_book_tree(book_dir, book_dir / version, skip_names)
        (book_dir / version / "versions.json").write_text(versions_json, encoding="utf-8")

    print("Generated versioned docs:")
    print("- /")
    for version in sorted(version_names, reverse=True):
        print(f"- /{version}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
