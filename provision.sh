#!/usr/bin/env bash
# Ubuntu 24.04 provisioning script for FluxOmni self-hosted deployment.
# Intended for cloud-init/user-data or manual execution on a fresh server.

set -euo pipefail

INSTALL_TARGET_ARG=""

usage() {
  cat <<'EOF'
Usage:
  provision.sh [full|media-node]
  provision.sh --install-target <full|media-node>

Defaults:
  - No argument provisions the full single-host stack.
  - media-node provisions a standalone remote media node.
  - FLUXOMNI_INSTALL_TARGET can also select the target when no CLI argument is passed.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    full|media-node)
      if [ -n "$INSTALL_TARGET_ARG" ]; then
        echo "Error: install target was specified more than once." >&2
        usage
        exit 1
      fi
      INSTALL_TARGET_ARG="$1"
      shift
      ;;
    --install-target)
      if [ "$#" -lt 2 ]; then
        echo "Error: --install-target requires a value." >&2
        usage
        exit 1
      fi
      if [ -n "$INSTALL_TARGET_ARG" ]; then
        echo "Error: install target was specified more than once." >&2
        usage
        exit 1
      fi
      INSTALL_TARGET_ARG="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unsupported argument '$1'." >&2
      usage
      exit 1
      ;;
  esac
done

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "Error: run this script as root."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

WITH_INITIAL_UPGRADE="${WITH_INITIAL_UPGRADE:-0}"
WITH_FIREWALLD="${WITH_FIREWALLD:-0}"
ALLOWED_IPS="${ALLOWED_IPS:-*}"
FLUXOMNI_INSTALL_TARGET="${INSTALL_TARGET_ARG:-${FLUXOMNI_INSTALL_TARGET:-full}}"

FLUXOMNI_VERSION="${FLUXOMNI_VERSION:-latest}"
FLUXOMNI_IMAGE="${FLUXOMNI_IMAGE:-}"
FLUXOMNI_CONTROL_PLANE_IMAGE="${FLUXOMNI_CONTROL_PLANE_IMAGE:-}"
FLUXOMNI_MEDIA_NODE_IMAGE="${FLUXOMNI_MEDIA_NODE_IMAGE:-}"
if [ -n "${FLUXOMNI_DIR:-}" ]; then
  FLUXOMNI_DIR="${FLUXOMNI_DIR}"
elif [ "$FLUXOMNI_INSTALL_TARGET" = "media-node" ]; then
  FLUXOMNI_DIR="/opt/fluxomni-media-node"
else
  FLUXOMNI_DIR="/opt/fluxomni"
fi
SELFHOST_REPO="${FLUXOMNI_SELFHOST_REPO:-fluxomnia-systems/fluxomni-selfhost}"
FLUXOMNI_SELFHOST_REF="${FLUXOMNI_SELFHOST_REF:-}"
FLUXOMNI_REPO_RAW="${FLUXOMNI_REPO_RAW:-}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' not found"
    exit 1
  fi
}

validate_install_target() {
  case "$FLUXOMNI_INSTALL_TARGET" in
    full|media-node)
      ;;
    *)
      echo "Error: unsupported install target '${FLUXOMNI_INSTALL_TARGET}'." >&2
      usage
      exit 1
      ;;
  esac
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

repo_raw_has_install_assets() {
  local asset_base="$1"

  remote_asset_exists "$asset_base" "install.sh" &&
    remote_asset_exists "$asset_base" "docker-compose.yml" &&
    remote_asset_exists "$asset_base" ".env.example"
}

install_docker_if_missing() {
  if command -v docker >/dev/null 2>&1; then
    return
  fi

  apt-get -qy update
  apt-get -qy install curl ca-certificates
  curl -fsSL https://get.docker.com | sh
}

split_allowed_ips() {
  local input="$1"
  if [ "$input" = "*" ]; then
    printf '*\n'
    return
  fi
  echo "$input" | tr ',' ' ' | xargs -n1 echo
}

resolve_selfhost_ref() {
  if [ -n "$FLUXOMNI_SELFHOST_REF" ]; then
    printf '%s\n' "$FLUXOMNI_SELFHOST_REF"
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

  if [ -n "$FLUXOMNI_REPO_RAW" ]; then
    printf '%s\n' "$FLUXOMNI_REPO_RAW"
    return
  fi

  selfhost_ref="$(resolve_selfhost_ref)"
  candidate_repo_raw="$(repo_raw_for_ref "$selfhost_ref")"

  if [ -n "$FLUXOMNI_SELFHOST_REF" ] || [ "$selfhost_ref" = "main" ]; then
    printf '%s\n' "$candidate_repo_raw"
    return
  fi

  if repo_raw_has_install_assets "$candidate_repo_raw"; then
    printf '%s\n' "$candidate_repo_raw"
    return
  fi

  fallback_repo_raw="$(repo_raw_for_ref "main")"
  if repo_raw_has_install_assets "$fallback_repo_raw"; then
    echo "Warning: self-host assets for '${FLUXOMNI_VERSION}' were not found." >&2
    echo "Falling back to self-host ref 'main'. Set FLUXOMNI_SELFHOST_REF to force a different ref." >&2
    printf '%s\n' "$fallback_repo_raw"
    return
  fi

  printf '%s\n' "$candidate_repo_raw"
}

download_installer() {
  local installer_repo_raw="$1"

  if curl -fsSL "${installer_repo_raw}/install.sh" 2>/dev/null; then
    return
  fi

  echo "Error: failed to download 'install.sh' from '${installer_repo_raw}'." >&2
  if [ -n "$FLUXOMNI_SELFHOST_REF" ]; then
    echo "Check FLUXOMNI_SELFHOST_REF='${FLUXOMNI_SELFHOST_REF}' or use FLUXOMNI_REPO_RAW." >&2
  elif [ "$FLUXOMNI_VERSION" != "latest" ] && [ "$FLUXOMNI_VERSION" != "edge" ]; then
    echo "Publish matching self-host assets for '${FLUXOMNI_VERSION}' or override with FLUXOMNI_SELFHOST_REF/FLUXOMNI_REPO_RAW." >&2
  fi
  exit 1
}

configure_firewall() {
  local tcp_ports
  local udp_ports
  local ips

  case "$FLUXOMNI_INSTALL_TARGET" in
    media-node)
      tcp_ports=(1935 8000 50051)
      udp_ports=(8000 10080)
      ;;
    *)
      tcp_ports=(80 443 1935 8000 50052)
      udp_ports=(8000 10080)
      ;;
  esac

  ips="$(split_allowed_ips "$ALLOWED_IPS")"

  if [ "$WITH_FIREWALLD" = "1" ]; then
    apt-get -qy update
    apt-get -qy install firewalld
    systemctl enable --now firewalld

    firewall-cmd --zone=public --permanent --add-service=ssh

    if [ "$ips" = "*" ]; then
      for port in "${tcp_ports[@]}"; do
        firewall-cmd --zone=public --permanent --add-port="${port}/tcp"
      done
      for port in "${udp_ports[@]}"; do
        firewall-cmd --zone=public --permanent --add-port="${port}/udp"
      done
    else
      while IFS= read -r ip; do
        [ -z "$ip" ] && continue
        for port in "${tcp_ports[@]}"; do
          firewall-cmd --permanent --zone=public --add-rich-rule="rule family='ipv4' source address='${ip}' port port='${port}' protocol='tcp' accept"
        done
        for port in "${udp_ports[@]}"; do
          firewall-cmd --permanent --zone=public --add-rich-rule="rule family='ipv4' source address='${ip}' port port='${port}' protocol='udp' accept"
        done
      done <<< "$ips"
    fi

    firewall-cmd --reload
    return
  fi

  apt-get -qy update
  apt-get -qy install ufw

  ufw allow 22/tcp
  if [ "$ips" = "*" ]; then
    for port in "${tcp_ports[@]}"; do
      ufw allow "${port}/tcp"
    done
    for port in "${udp_ports[@]}"; do
      ufw allow "${port}/udp"
    done
  else
    while IFS= read -r ip; do
      [ -z "$ip" ] && continue
      for port in "${tcp_ports[@]}"; do
        ufw allow from "$ip" to any port "$port" proto tcp
      done
      for port in "${udp_ports[@]}"; do
        ufw allow from "$ip" to any port "$port" proto udp
      done
    done <<< "$ips"
  fi

  ufw --force enable
}

if [ "$WITH_INITIAL_UPGRADE" = "1" ]; then
  apt-get -qy update
  apt-get -qy upgrade
fi

validate_install_target
require_cmd curl
install_docker_if_missing
systemctl enable --now docker || true

configure_firewall

echo "Running FluxOmni installer..."
INSTALLER_REPO_RAW="$(resolve_repo_raw)"
FLUXOMNI_DIR="$FLUXOMNI_DIR" \
FLUXOMNI_INSTALL_TARGET="$FLUXOMNI_INSTALL_TARGET" \
FLUXOMNI_VERSION="$FLUXOMNI_VERSION" \
FLUXOMNI_IMAGE="$FLUXOMNI_IMAGE" \
FLUXOMNI_CONTROL_PLANE_IMAGE="$FLUXOMNI_CONTROL_PLANE_IMAGE" \
FLUXOMNI_MEDIA_NODE_IMAGE="$FLUXOMNI_MEDIA_NODE_IMAGE" \
FLUXOMNI_SELFHOST_REPO="$SELFHOST_REPO" \
FLUXOMNI_SELFHOST_REF="$FLUXOMNI_SELFHOST_REF" \
FLUXOMNI_REPO_RAW="$INSTALLER_REPO_RAW" \
  bash -c "$(download_installer "${INSTALLER_REPO_RAW}")"

echo "Provisioning complete"
