#!/usr/bin/env python3
"""Check or update the public API docs source snapshot.

The self-host docs are hand-written, but they mirror source material from the
main Fluxomni repository. This script records the upstream commit and content
hashes for the Fluxomni files that public API docs depend on.

Modes:
- check: fail when upstream source files differ from the recorded snapshot.
- update: refresh the recorded snapshot used by the sync workflow.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_REPO = "https://github.com/fluxomnia-systems/fluxomni.git"
DEFAULT_REF = "main"

SOURCE_FILES = [
    "api/schema.graphql",
    "api/clients/typescript/README.md",
    "api/examples/typescript/session-raw-subscription.ts",
    "api/examples/typescript/ensure-route-desired-state.ts",
    "api/examples/typescript/manage-route-controls.ts",
    "api/examples/typescript/manage-playlist-artifacts-settings-fleet.ts",
    "docs/public-api/contract-inventory.md",
    "docs/public-api/error-taxonomy.md",
    "docs/public-api/fleet-command-safety.md",
    "docs/public-api/compatibility-policy.md",
    "docs/public-api/selfhost-docs-handoff.md",
    "lat.md/public-api.md",
]

STATE_PATH = Path("docs/src/api/.fluxomni-source-sync.json")


def run(command: list[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_state() -> dict[str, Any] | None:
    if not STATE_PATH.exists():
        return None
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def source_root(args: argparse.Namespace, tmpdir: Path) -> Path:
    if args.fluxomni_root:
        root = Path(args.fluxomni_root).resolve()
        if not (root / ".git").exists():
            raise SystemExit(f"{root} does not look like a git checkout")
        return root

    checkout = tmpdir / "fluxomni"
    run(["git", "clone", "--filter=blob:none", "--no-checkout", args.repo, str(checkout)])
    run(["git", "fetch", "--depth", "1", "origin", args.fluxomni_ref], cwd=checkout)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=checkout)
    return checkout


def collect_snapshot(root: Path, repo: str, requested_ref: str) -> dict[str, Any]:
    resolved_sha = run(["git", "rev-parse", "HEAD"], cwd=root)
    files: dict[str, Any] = {}

    for relative in SOURCE_FILES:
        path = root / relative
        if not path.exists():
            files[relative] = {"present": False}
            continue
        files[relative] = {
            "present": True,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }

    return {
        "schemaVersion": 1,
        "repo": repo,
        "requestedRef": requested_ref,
        "resolvedSha": resolved_sha,
        "updatedAt": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "files": files,
    }


def compare_snapshots(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> list[str]:
    if previous is None:
        return ["No recorded upstream snapshot exists."]

    drift: list[str] = []
    previous_files = previous.get("files", {})
    current_files = current.get("files", {})

    for relative in SOURCE_FILES:
        old = previous_files.get(relative)
        new = current_files.get(relative)
        if old != new:
            drift.append(relative)

    if previous.get("resolvedSha") != current.get("resolvedSha") and not drift:
        drift.append("Upstream commit changed, but tracked file hashes are unchanged.")

    return drift


def write_step_summary(mode: str, drift: list[str], snapshot: dict[str, Any]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    short_sha = snapshot["resolvedSha"][:12]
    if drift:
        body = [
            "### API Docs Source Drift",
            "",
            f"Mode: `{mode}`",
            f"Upstream commit: `{short_sha}`",
            "",
            "Changed tracked sources:",
            "",
            *[f"- `{item}`" for item in drift],
            "",
        ]
    else:
        body = [
            "### API Docs Source Sync",
            "",
            f"Mode: `{mode}`",
            f"Upstream commit: `{short_sha}`",
            "",
            "No tracked source drift detected.",
            "",
        ]

    with Path(summary_path).open("a", encoding="utf-8") as handle:
        handle.write("\n".join(body))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["check", "update"], default="check")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--fluxomni-ref", default=DEFAULT_REF)
    parser.add_argument("--fluxomni-root")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory() as temp:
        root = source_root(args, Path(temp))
        repo = args.repo
        requested_ref = args.fluxomni_ref
        if args.fluxomni_root:
            repo = run(["git", "remote", "get-url", "origin"], cwd=root)
            requested_ref = run(["git", "branch", "--show-current"], cwd=root) or "HEAD"
        snapshot = collect_snapshot(root, repo, requested_ref)

    previous = load_state()
    drift = compare_snapshots(previous, snapshot)
    write_step_summary(args.mode, drift, snapshot)

    if args.mode == "update":
        if not drift and previous is not None:
            snapshot["updatedAt"] = previous.get("updatedAt", snapshot["updatedAt"])
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if drift:
            print("Updated API docs source snapshot:")
            for item in drift:
                print(f"- {item}")
        else:
            print("API docs source snapshot is already current.")
        return 0

    if drift:
        print("API docs source drift detected:", file=sys.stderr)
        for item in drift:
            print(f"- {item}", file=sys.stderr)
        print(
            "Run this workflow with mode=update or run the script locally with "
            "--mode update after reviewing docs.",
            file=sys.stderr,
        )
        return 1

    print("API docs source snapshot is current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
