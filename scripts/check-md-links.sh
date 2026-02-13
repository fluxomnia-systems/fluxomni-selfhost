#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_ROOT="${1:-docs/src}"

if [ ! -d "$ROOT_DIR/$DOCS_ROOT" ]; then
  echo "Error: docs directory not found: $ROOT_DIR/$DOCS_ROOT"
  exit 1
fi

if ! command -v rg >/dev/null 2>&1; then
  echo "Error: ripgrep (rg) is required for link lint."
  exit 1
fi

errors=0

while IFS= read -r file; do
  while IFS= read -r raw; do
    target="${raw#*](}"
    target="${target%)}"

    # Skip external links, anchors, mailto, and root-path site links.
    if [[ -z "$target" || "$target" == http* || "$target" == mailto:* || "$target" == \#* || "$target" == /* ]]; then
      continue
    fi

    target_no_anchor="${target%%#*}"
    target_no_query="${target_no_anchor%%\?*}"

    if [[ -z "$target_no_query" ]]; then
      continue
    fi

    dir="$(dirname "$file")"
    if [[ -e "$dir/$target_no_query" || -e "$ROOT_DIR/$target_no_query" ]]; then
      continue
    fi

    echo "Missing link target: $file -> $target"
    errors=$((errors + 1))
  done < <(rg -o '\]\([^)]*\)' "$file")
done < <(find "$ROOT_DIR/$DOCS_ROOT" -type f -name '*.md' | sort)

if [[ "$errors" -gt 0 ]]; then
  echo "Found $errors broken local markdown link(s)."
  exit 1
fi

echo "Local markdown links OK."
