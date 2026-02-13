#!/usr/bin/env bash
# FluxOmni self-host installer.
# Downloads compose assets from this repository and starts the stack.

set -euo pipefail

FLUXOMNI_DIR="${FLUXOMNI_DIR:-$HOME/fluxomni}"
FLUXOMNI_VERSION="${FLUXOMNI_VERSION:-edge}"
FLUXOMNI_IMAGE="${FLUXOMNI_IMAGE:-ghcr.io/fluxomnia-systems/fluxomni}"
REPO_RAW="${FLUXOMNI_REPO_RAW:-https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' was not found."
    exit 1
  fi
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

echo "Installing FluxOmni to ${FLUXOMNI_DIR}"

require_cmd curl
require_cmd docker

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: Docker Compose v2 is required."
  echo "Install instructions: https://docs.docker.com/compose/install/"
  exit 1
fi

mkdir -p "${FLUXOMNI_DIR}" "${FLUXOMNI_DIR}/data/videos" "${FLUXOMNI_DIR}/data/dvr"

echo "Downloading deployment files..."
curl -fsSL "${REPO_RAW}/docker-compose.yml" -o "${FLUXOMNI_DIR}/docker-compose.yml"
curl -fsSL "${REPO_RAW}/.env.example" -o "${FLUXOMNI_DIR}/.env.example"

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
docker compose pull
docker compose up -d

HOST="$(grep -E '^FLUXOMNI_PUBLIC_HOST=' .env | cut -d= -f2 || true)"
HOST="${HOST:-127.0.0.1}"

echo
echo "FluxOmni is starting"
echo "Web UI: http://${HOST}"
echo "RTMP : rtmp://${HOST}:1935/app"
echo "Data : ${FLUXOMNI_DIR}/data"
echo
echo "Common commands:"
echo "  Update: cd ${FLUXOMNI_DIR} && docker compose pull && docker compose up -d"
echo "  Logs  : cd ${FLUXOMNI_DIR} && docker compose logs -f"
echo "  Stop  : cd ${FLUXOMNI_DIR} && docker compose down"
