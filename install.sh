#!/usr/bin/env bash
# FluxOmni self-host installer.
# Downloads compose assets from this repository and starts the stack.

set -euo pipefail

FLUXOMNI_DIR="${FLUXOMNI_DIR:-$HOME/fluxomni}"
FLUXOMNI_VERSION="${FLUXOMNI_VERSION:-latest}"
FLUXOMNI_IMAGE="${FLUXOMNI_IMAGE:-ghcr.io/fluxomnia-systems/fluxomni}"
SELFHOST_REPO="${FLUXOMNI_SELFHOST_REPO:-fluxomnia-systems/fluxomni-selfhost}"
SELFHOST_REF_OVERRIDE="${FLUXOMNI_SELFHOST_REF:-}"
REPO_RAW="${FLUXOMNI_REPO_RAW:-}"
DOCKER_CMD=(docker)
DOCKER_DISPLAY="docker"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' was not found."
    exit 1
  fi
}

repo_raw_for_ref() {
  local selfhost_ref="$1"
  printf 'https://raw.githubusercontent.com/%s/%s\n' "$SELFHOST_REPO" "$selfhost_ref"
}

remote_asset_exists() {
  local asset_base="$1"
  local asset_path="$2"
  curl -fsSL "${asset_base}/${asset_path}" -o /dev/null >/dev/null 2>&1
}

run_privileged() {
  if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    "$@"
    return
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
    return
  fi

  echo "Error: Docker installation requires root or sudo access."
  exit 1
}

install_docker_if_missing() {
  if command -v docker >/dev/null 2>&1; then
    return
  fi

  if [ "$(uname -s)" != "Linux" ] || ! command -v apt-get >/dev/null 2>&1; then
    echo "Error: Docker is not installed."
    echo "Automatic Docker installation is only supported on Debian/Ubuntu hosts."
    echo "Manual install guide: https://docs.docker.com/engine/install/"
    exit 1
  fi

  echo "Docker not found. Installing Docker..."
  run_privileged apt-get -qy update
  curl -fsSL https://get.docker.com | run_privileged bash -s
  run_privileged systemctl enable --now docker || true
}

configure_docker_access() {
  if docker info >/dev/null 2>&1; then
    DOCKER_CMD=(docker)
    DOCKER_DISPLAY="docker"
    return
  fi

  if command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
    DOCKER_CMD=(sudo docker)
    DOCKER_DISPLAY="sudo docker"
    return
  fi

  echo "Error: Docker is installed but cannot be used."
  echo "If Docker was just installed, re-run the installer or start a new shell session."
  exit 1
}

detect_host_ip() {
  local ip

  if command -v hostname >/dev/null 2>&1; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  fi

  if [ -z "${ip:-}" ] && command -v ip >/dev/null 2>&1; then
    ip="$(ip route get 1 2>/dev/null | awk '/src/ {for (i=1; i<=NF; i++) if ($i == "src") {print $(i+1); exit}}')"
  fi

  if [ -z "${ip:-}" ]; then
    ip="127.0.0.1"
  fi

  printf '%s\n' "$ip"
}

resolve_selfhost_ref() {
  if [ -n "$SELFHOST_REF_OVERRIDE" ]; then
    printf '%s\n' "$SELFHOST_REF_OVERRIDE"
    return
  fi

  case "$FLUXOMNI_VERSION" in
    latest|edge)
      printf '%s\n' "main"
      ;;
    *)
      printf '%s\n' "$FLUXOMNI_VERSION"
      ;;
  esac
}

resolve_repo_raw() {
  local selfhost_ref
  local candidate_repo_raw
  local fallback_repo_raw

  if [ -n "$REPO_RAW" ]; then
    printf '%s\n' "$REPO_RAW"
    return
  fi

  selfhost_ref="$(resolve_selfhost_ref)"
  candidate_repo_raw="$(repo_raw_for_ref "$selfhost_ref")"

  if [ -n "$SELFHOST_REF_OVERRIDE" ] || [ "$selfhost_ref" = "main" ]; then
    printf '%s\n' "$candidate_repo_raw"
    return
  fi

  if remote_asset_exists "$candidate_repo_raw" "docker-compose.yml" &&
    remote_asset_exists "$candidate_repo_raw" ".env.example"; then
    printf '%s\n' "$candidate_repo_raw"
    return
  fi

  fallback_repo_raw="$(repo_raw_for_ref "main")"
  if remote_asset_exists "$fallback_repo_raw" "docker-compose.yml" &&
    remote_asset_exists "$fallback_repo_raw" ".env.example"; then
    echo "Warning: self-host assets for '${FLUXOMNI_VERSION}' were not found." >&2
    echo "Falling back to self-host ref 'main'. Set FLUXOMNI_SELFHOST_REF to force a different ref." >&2
    printf '%s\n' "$fallback_repo_raw"
    return
  fi

  printf '%s\n' "$candidate_repo_raw"
}

download_asset() {
  local asset_path="$1"
  local destination="$2"

  if curl -fsSL "${REPO_RAW}/${asset_path}" -o "$destination" >/dev/null 2>&1; then
    return
  fi

  echo "Error: failed to download '${asset_path}' from '${REPO_RAW}'." >&2
  if [ -n "$SELFHOST_REF_OVERRIDE" ]; then
    echo "Check FLUXOMNI_SELFHOST_REF='${SELFHOST_REF_OVERRIDE}' or use FLUXOMNI_REPO_RAW." >&2
  elif [ "$FLUXOMNI_VERSION" != "latest" ] && [ "$FLUXOMNI_VERSION" != "edge" ]; then
    echo "Publish matching self-host assets for '${FLUXOMNI_VERSION}' or override with FLUXOMNI_SELFHOST_REF/FLUXOMNI_REPO_RAW." >&2
  fi
  exit 1
}

echo "Installing FluxOmni to ${FLUXOMNI_DIR}"

require_cmd curl
install_docker_if_missing
configure_docker_access

REPO_RAW="$(resolve_repo_raw)"

if ! "${DOCKER_CMD[@]}" compose version >/dev/null 2>&1; then
  echo "Error: Docker Compose v2 is required."
  echo "Install instructions: https://docs.docker.com/compose/install/"
  exit 1
fi

mkdir -p "${FLUXOMNI_DIR}" "${FLUXOMNI_DIR}/data/videos" "${FLUXOMNI_DIR}/data/dvr"

echo "Downloading deployment files..."
download_asset "docker-compose.yml" "${FLUXOMNI_DIR}/docker-compose.yml"
download_asset ".env.example" "${FLUXOMNI_DIR}/.env.example"

if [ ! -f "${FLUXOMNI_DIR}/.env" ]; then
  HOST_IP="$(detect_host_ip)"
  cat > "${FLUXOMNI_DIR}/.env" <<ENVVARS
# Created by install.sh
FLUXOMNI_IMAGE=${FLUXOMNI_IMAGE}
FLUXOMNI_VERSION=${FLUXOMNI_VERSION}
FLUXOMNI_PUBLIC_HOST=${HOST_IP}
ENVVARS
  echo "Created ${FLUXOMNI_DIR}/.env"
else
  echo "Keeping existing ${FLUXOMNI_DIR}/.env"
fi

touch "${FLUXOMNI_DIR}/data/state.json" "${FLUXOMNI_DIR}/data/srs.conf"

cd "${FLUXOMNI_DIR}"

echo "Pulling image and starting containers..."
"${DOCKER_CMD[@]}" compose pull
"${DOCKER_CMD[@]}" compose up -d

HOST="$(grep -E '^FLUXOMNI_PUBLIC_HOST=' .env | cut -d= -f2 || true)"
HOST="${HOST:-127.0.0.1}"

echo
echo "FluxOmni is starting"
echo "Web UI: http://${HOST}"
echo "RTMP : rtmp://${HOST}:1935/app"
echo "Data : ${FLUXOMNI_DIR}/data"
echo
echo "Common commands:"
echo "  Update: cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose pull && ${DOCKER_DISPLAY} compose up -d"
echo "  Logs  : cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose logs -f"
echo "  Stop  : cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose down"
