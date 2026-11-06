#!/usr/bin/env bash
# Fluxomni release launcher. Keep installer code and assets on the same ref.
set -euo pipefail

arguments=("$@")
target="${FLUXOMNI_INSTALL_TARGET:-full}"
while [ "$#" -gt 0 ]; do
  case "$1" in
    full|media-node) target="$1" ;;
    --install-target)
      [ "$#" -ge 2 ] || { echo 'Error: --install-target requires a value.' >&2; exit 1; }
      target="$2"
      shift
      ;;
    --help|-h)
      cat <<'USAGE'
Usage:
  install.sh [full|media-node]
  install.sh --install-target <full|media-node>
  install.sh full --capacity-upgrade initial --confirm-execution-stopped
  install.sh full --capacity-upgrade drained
  install.sh media-node --capacity-upgrade node --confirm-control-plane-ready

Defaults:
  - No argument installs the full single-host stack.
  - media-node installs a standalone remote media node.

Existing installs:
  - Updating needs one --capacity-upgrade mode (see the capacity upgrade guide).
  - To change offline preparation limits, use fluxomnictl preparation
    (run "install.sh tools" first when the command is missing).
USAGE
      exit 0
      ;;
  esac
  shift
done
case "$target" in full|media-node) ;; *) echo 'Error: unsupported install target.' >&2; exit 1 ;; esac

home_dir="${HOME:-}"
if [ -z "$home_dir" ]; then
  home_dir=$(getent passwd "$(id -u)" 2>/dev/null | cut -d: -f6 || true)
  if [ -z "$home_dir" ] && [ "$(id -u)" -eq 0 ]; then home_dir=/root; fi
  home_dir="${home_dir:-/tmp}"
fi
if [ "$target" = media-node ]; then default_dir="$home_dir/fluxomni-media-node"; else default_dir="$home_dir/fluxomni"; fi
install_dir="${FLUXOMNI_DIR:-$default_dir}"
saved_version=""
if [ -f "$install_dir/.env" ]; then
  saved_version=$(grep '^FLUXOMNI_VERSION=' "$install_dir/.env" | tail -n1 | cut -d= -f2- || true)
fi
version="${FLUXOMNI_VERSION:-${saved_version:-latest}}"
repo="${FLUXOMNI_SELFHOST_REPO:-fluxomnia-systems/fluxomni-selfhost}"
raw_root="https://raw.githubusercontent.com/$repo"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT

# "tools" installs fluxomnictl and the doctor.sh wrapper for existing installs.
# It never pulls images, restarts services, or touches capacity state.
install_tools() {
  local tool_root bin_dir dir found=() checked=()
  tool_root="${FLUXOMNI_REPO_RAW:-$raw_root/main}"
  if [ -n "${FLUXOMNI_DIR:-}" ]; then
    checked=("$FLUXOMNI_DIR")
  else
    checked=("$home_dir/fluxomni" "$home_dir/fluxomni-media-node")
  fi
  for dir in "${checked[@]}"; do
    if [ -f "$dir/.env" ] && [ -f "$dir/docker-compose.yml" ]; then found+=("$dir"); fi
  done
  if [ "${#found[@]}" -eq 0 ]; then
    echo "Error: no existing install found. Checked: ${checked[*]}. Set FLUXOMNI_DIR to the install folder." >&2
    return 1
  fi
  command -v python3 >/dev/null 2>&1 || { echo 'Error: python3 is required for fluxomnictl.' >&2; return 1; }
  case "$tool_root" in
    https://*) ;;
    *) [ -n "${FLUXOMNI_REPO_RAW:-}" ] || { echo 'Error: tools needs an https download source.' >&2; return 1; } ;;
  esac
  curl -fsSL "$tool_root/scripts/fluxomnictl.py" -o "$temporary/fluxomnictl" || { echo 'Error: cannot download fluxomnictl. No files were changed.' >&2; return 1; }
  curl -fsSL "$tool_root/doctor.sh" -o "$temporary/doctor.sh" || { echo 'Error: cannot download doctor.sh. No files were changed.' >&2; return 1; }
  python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read())' "$temporary/fluxomnictl" || return 1
  bash -n "$temporary/doctor.sh" || return 1
  # Refuse unsupported installed versions before writing anything.
  local support
  for dir in "${found[@]}"; do
    support=$(python3 "$temporary/fluxomnictl" --dir "$dir" check-support 2>&1) || {
      printf '%s\n' "$support" >&2
      echo 'No files were changed.' >&2
      return 1
    }
  done
  if [ "$(id -u)" -eq 0 ]; then bin_dir=/usr/local/bin; else bin_dir="$home_dir/.local/bin"; fi
  bin_dir="${FLUXOMNI_CTL_BIN_DIR:-$bin_dir}"
  if [ -L "$bin_dir" ] || [ -L "$bin_dir/fluxomnictl" ]; then
    echo "Error: $bin_dir or its fluxomnictl is a symlink. No files were changed." >&2
    return 1
  fi
  mkdir -p "$bin_dir"
  install -m 0755 "$temporary/fluxomnictl" "$bin_dir/fluxomnictl"
  for dir in "${found[@]}"; do
    install -m 0755 "$temporary/doctor.sh" "$dir/doctor.sh" || { echo "Error: cannot update $dir/doctor.sh. fluxomnictl is installed; rerun after fixing permissions." >&2; return 1; }
    echo "Updated $dir/doctor.sh"
  done
  echo "Installed fluxomnictl to $bin_dir/fluxomnictl"
  case ":$PATH:" in *":$bin_dir:"*) ;; *) echo "Warning: $bin_dir is not on PATH. Add it to PATH, or run $bin_dir/fluxomnictl directly." >&2 ;; esac
}

if [ "${arguments[0]:-}" = tools ]; then
  [ "${#arguments[@]}" -eq 1 ] || { echo 'Error: "tools" takes no other arguments.' >&2; exit 1; }
  install_tools || exit 1
  exit 0
fi

load_version_map() {
  curl -fsSL "$raw_root/main/scripts/generated-version-map.sh" -o "$temporary/version-map.sh" || {
    echo 'Error: cannot resolve the stable installer release.' >&2; return 1;
  }
  bash -n "$temporary/version-map.sh"
  # shellcheck source=/dev/null
  source "$temporary/version-map.sh"
}

ref="${FLUXOMNI_SELFHOST_REF:-}"
if [ -n "${FLUXOMNI_REPO_RAW:-}" ]; then
  asset_root="$FLUXOMNI_REPO_RAW"
else
  load_version_map
  if [ -z "$ref" ]; then
    case "$version" in
      latest)
        ref=$(generated_latest_public_release)
        [[ "$ref" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Error: invalid stable release ref.' >&2; exit 1; }
        ;;
      edge|main) ref=main ;;
      *) ref="v${version#v}" ;;
    esac
  fi
  if [ -z "${FLUXOMNI_SELFHOST_REF:-}" ]; then ref=$(generated_installer_bundle_ref "$ref"); fi
  asset_root="$raw_root/$ref"
fi

# The release map declares historical installers. Unknown and development refs
# must provide the current implementation; missing files never fall back to main.
installer_path=scripts/install-runtime.sh
if [ -n "$ref" ] && [ -z "${FLUXOMNI_REPO_RAW:-}" ]; then installer_path=$(generated_installer_path "$ref"); fi
status=$(curl -sSL --write-out '%{http_code}' "$asset_root/$installer_path" -o "$temporary/install.sh")
if [ "$status" = 404 ] && [ "$installer_path" = install.sh ] && [ -z "${FLUXOMNI_SELFHOST_REF:-}" ]; then
  alias_ref=$(generated_public_release_alias "$ref" || true)
  if [ -n "$alias_ref" ] && [ "$alias_ref" != "$ref" ]; then
    ref="$alias_ref"
    version="$alias_ref"
    asset_root="$raw_root/$ref"
    installer_path=$(generated_installer_path "$ref")
    status=$(curl -sSL --write-out '%{http_code}' "$asset_root/$installer_path" -o "$temporary/install.sh")
  fi
fi
if [ "$status" != 200 ] || grep -q '^# Fluxomni release launcher\.' "$temporary/install.sh"; then
  echo "Error: matching installer is not published at $asset_root. No installation files were changed." >&2
  exit 1
fi
if [ "$installer_path" = install.sh ] && { [ -n "${FLUXOMNI_ENROLLMENT_CODE:-}${FLUXOMNI_ENROLLMENT_URL:-}${FLUXOMNI_CREDENTIAL_MODE:-}" ] || [ -f "$install_dir/node-secrets/credential" ]; }; then
  echo 'Error: this release predates Fleet enrollment. Select a matching enrollment-capable release in Fleet; use edge while the feature is unreleased.' >&2
  exit 1
fi
bash -n "$temporary/install.sh"
export FLUXOMNI_VERSION="$version"
export FLUXOMNI_DIR="$install_dir"
if [ -n "$ref" ]; then export FLUXOMNI_SELFHOST_REF="$ref"; fi
bash "$temporary/install.sh" "${arguments[@]}"
