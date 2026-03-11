#!/usr/bin/env bash
# Ubuntu 24.04 provisioning script for FluxOmni self-hosted deployment.
# Intended for cloud-init/user-data or manual execution on a fresh server.

set -euo pipefail

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "Error: run this script as root."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

WITH_INITIAL_UPGRADE="${WITH_INITIAL_UPGRADE:-0}"
WITH_FIREWALLD="${WITH_FIREWALLD:-0}"
ALLOWED_IPS="${ALLOWED_IPS:-*}"

FLUXOMNI_VERSION="${FLUXOMNI_VERSION:-latest}"
FLUXOMNI_IMAGE="${FLUXOMNI_IMAGE:-ghcr.io/fluxomnia-systems/fluxomni}"
FLUXOMNI_DIR="${FLUXOMNI_DIR:-/opt/fluxomni}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' not found"
    exit 1
  fi
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

configure_firewall() {
  local ports=(80 443 1935 8000)
  local ips
  ips="$(split_allowed_ips "$ALLOWED_IPS")"

  if [ "$WITH_FIREWALLD" = "1" ]; then
    apt-get -qy update
    apt-get -qy install firewalld
    systemctl enable --now firewalld

    firewall-cmd --zone=public --permanent --add-service=ssh

    if [ "$ips" = "*" ]; then
      for port in "${ports[@]}"; do
        firewall-cmd --zone=public --permanent --add-port="${port}/tcp"
      done
    else
      while IFS= read -r ip; do
        [ -z "$ip" ] && continue
        for port in "${ports[@]}"; do
          firewall-cmd --permanent --zone=public --add-rich-rule="rule family='ipv4' source address='${ip}' port port='${port}' protocol='tcp' accept"
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
    for port in "${ports[@]}"; do
      ufw allow "${port}/tcp"
    done
  else
    while IFS= read -r ip; do
      [ -z "$ip" ] && continue
      for port in "${ports[@]}"; do
        ufw allow from "$ip" to any port "$port" proto tcp
      done
    done <<< "$ips"
  fi

  ufw --force enable
}

if [ "$WITH_INITIAL_UPGRADE" = "1" ]; then
  apt-get -qy update
  apt-get -qy upgrade
fi

require_cmd curl
install_docker_if_missing
systemctl enable --now docker || true

configure_firewall

echo "Running FluxOmni installer..."
FLUXOMNI_DIR="$FLUXOMNI_DIR" \
FLUXOMNI_VERSION="$FLUXOMNI_VERSION" \
FLUXOMNI_IMAGE="$FLUXOMNI_IMAGE" \
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost/main/install.sh)"

echo "Provisioning complete"
