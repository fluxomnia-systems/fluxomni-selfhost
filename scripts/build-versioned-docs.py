#!/usr/bin/env python3
"""Build the Pages site from released self-host tags and the current checkout."""

import argparse
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"v\d+\.\d+\.\d+")


def version_key(version):
    return tuple(map(int, version[1:].split(".")))


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def snapshot(ref, dest):
    with tempfile.TemporaryFile() as archive:
        subprocess.run(["git", "archive", ref, "docs"], cwd=ROOT, stdout=archive, check=True)
        archive.seek(0)
        with tarfile.open(fileobj=archive) as files:
            files.extractall(dest, filter="data")
    return dest / "docs"


def build(source, output, url, ref):
    env = dict(os.environ, MDBOOK_OUTPUT__HTML__SITE_URL=url)
    if ref:
        # Readers of a release should see its source. Editing happens on main.
        env["MDBOOK_OUTPUT__HTML__EDIT_URL_TEMPLATE"] = (
            f"https://github.com/fluxomnia-systems/fluxomni-selfhost/blob/{ref}/docs/src/{{path}}"
        )
    subprocess.run(["mdbook", "build", str(source), "-d", str(output)], env=env, check=True)


def add_navigation(site, books, latest):
    # Index each book before walking it so the root book cannot absorb nested versions.
    pages = {
        slug: {
            path.relative_to(site / slug): path
            for path in (site / slug).rglob("*.html")
            if slug or path.relative_to(site).parts[0] not in books
        }
        for slug in books
    }
    for slug, chapters in pages.items():
        for chapter, page in chapters.items():
            html = page.read_text(encoding="utf-8")
            if slug == "edge":
                html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)
            if "<main>" not in html:  # mdBook's generated redirect pages
                if slug == "edge":
                    page.write_text(html, encoding="utf-8")
                continue
            links = []
            for target, label in books.items():
                if target == slug:
                    links.append(f'<strong aria-current="true">{escape(label)}</strong>')
                else:
                    destination = pages[target].get(chapter, site / target / "index.html")
                    href = escape(os.path.relpath(destination, page.parent), quote=True)
                    links.append(f'<a href="{href}">{escape(label)}</a>')
            note = (
                "Edge follows development. Features and commands can change before release."
                if slug == "edge"
                else f"These docs describe {slug or latest}."
            )
            if chapter.as_posix() == "getting-started/quick-start.html":
                version = slug or latest
                note += f" To install the version shown here, set <code>FLUXOMNI_VERSION={version}</code> on the installer command."
            nav = (
                '<nav aria-label="Documentation version" style="margin: 1em 0">'
                'Docs version: ' + ' · '.join(links) + f'<p>{note}</p></nav>'
            )
            page.write_text(html.replace("<main>", "<main>\n" + nav, 1), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-path", default="/", help="Pages URL path, e.g. /project/")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error("--output must be a new or empty directory")
    base = "/" + args.base_path.strip("/") + "/" if args.base_path.strip("/") else "/"

    manifest = json.loads((ROOT / "docs/src/release-manifest.json").read_text())
    latest = manifest["latestStable"]
    tags = set(git("tag", "--list").splitlines())
    refs = {}
    for version, release in manifest["releases"].items():
        ref = release["selfhostRef"]
        if VERSION.fullmatch(version) and VERSION.fullmatch(ref) and ref in tags:
            if git("ls-tree", ref, "--", "docs/book.toml", "docs/src/SUMMARY.md").count("\n") == 2:
                refs[version] = ref
    versions = sorted(refs, key=version_key, reverse=True)
    if latest not in refs:
        # Release sync can merge before the matching self-host tag is published.
        previous = next((v for v in versions if version_key(v) < version_key(latest)), None)
        if previous is None:
            parser.error(f"no tagged docs snapshot for {latest} or an earlier release; fetch tags")
        print(f"{latest} has no tagged docs snapshot yet; keeping {previous} at the root.", file=sys.stderr)
        latest = previous
    books = {"": f"Latest stable ({latest})", "edge": "Edge", **{v: v for v in versions}}
    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        site = work / "site"
        for version in versions:
            source = snapshot(refs[version], work / version)
            if version == latest:
                build(source, site, base, refs[version])
            build(source, site / version, base + version + "/", refs[version])
        build(ROOT / "docs", site / "edge", base + "edge/", None)
        add_navigation(site, books, latest)
        shutil.copytree(site, output, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
