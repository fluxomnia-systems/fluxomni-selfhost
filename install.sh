#!/usr/bin/env bash
# FluxOmni self-host installer.
# Downloads compose assets from this repository and starts the stack.

set -euo pipefail

INSTALL_TARGET_ARG=""

usage() {
  cat <<'EOF'
Usage:
  install.sh [full|media-node]
  install.sh --install-target <full|media-node>

Defaults:
  - No argument installs the full single-host stack.
  - media-node installs a standalone remote media node.
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

resolve_home_dir() {
  if [ -n "${HOME:-}" ]; then
    printf '%s\n' "$HOME"
    return
  fi

  if command -v getent >/dev/null 2>&1; then
    local passwd_home
    passwd_home="$(getent passwd "$(id -u)" | cut -d: -f6 || true)"
    if [ -n "$passwd_home" ]; then
      printf '%s\n' "$passwd_home"
      return
    fi
  fi

  if [ "$(id -u)" -eq 0 ]; then
    printf '/root\n'
    return
  fi

  printf '/tmp\n'
}

HOME="${HOME:-$(resolve_home_dir)}"
export HOME

FLUXOMNI_INSTALL_TARGET="${INSTALL_TARGET_ARG:-${FLUXOMNI_INSTALL_TARGET:-full}}"

if [ -n "${FLUXOMNI_DIR:-}" ]; then
  FLUXOMNI_DIR="${FLUXOMNI_DIR}"
elif [ "$FLUXOMNI_INSTALL_TARGET" = "media-node" ]; then
  FLUXOMNI_DIR="$HOME/fluxomni-media-node"
else
  FLUXOMNI_DIR="$HOME/fluxomni"
fi

REQUESTED_FLUXOMNI_VERSION="${FLUXOMNI_VERSION:-}"
LEGACY_FLUXOMNI_IMAGE="${FLUXOMNI_IMAGE:-}"
FLUXOMNI_CONTROL_PLANE_IMAGE="${FLUXOMNI_CONTROL_PLANE_IMAGE:-}"
FLUXOMNI_MEDIA_NODE_IMAGE="${FLUXOMNI_MEDIA_NODE_IMAGE:-}"
REQUESTED_PUBLIC_URL="${FLUXOMNI_PUBLIC_URL:-}"
REQUESTED_PUBLIC_HOST="${FLUXOMNI_PUBLIC_HOST:-}"
REQUESTED_CONTROL_PLANE_HTTP_PORT="${FLUXOMNI_CONTROL_PLANE_HTTP_PORT:-}"
REQUESTED_CONTROL_PLANE_RPC_PORT="${FLUXOMNI_CONTROL_PLANE_RPC_PORT:-}"
REQUESTED_MEDIA_NODE_PUBLIC_HOST="${FLUXOMNI_MEDIA_NODE_PUBLIC_HOST:-}"
REQUESTED_MEDIA_NODE_RTMP_PORT="${FLUXOMNI_MEDIA_NODE_RTMP_PORT:-}"
REQUESTED_MEDIA_NODE_HLS_PORT="${FLUXOMNI_MEDIA_NODE_HLS_PORT:-}"
REQUESTED_MEDIA_NODE_SRT_PORT="${FLUXOMNI_MEDIA_NODE_SRT_PORT:-}"
REQUESTED_MEDIA_NODE_SRS_CALLBACK_PORT="${FLUXOMNI_MEDIA_NODE_SRS_CALLBACK_PORT:-}"
REQUESTED_MEDIA_NODE_GRPC_PORT="${FLUXOMNI_MEDIA_NODE_GRPC_PORT:-}"
REQUESTED_MEDIA_NODE_ID="${FLUXOMNI_MEDIA_NODE_ID:-}"
REQUESTED_MEDIA_NODE_NAME="${FLUXOMNI_MEDIA_NODE_NAME:-}"
REQUESTED_MEDIA_NODE_LABELS="${FLUXOMNI_MEDIA_NODE_LABELS:-}"
REQUESTED_MEDIA_NODE_ZONE="${FLUXOMNI_MEDIA_NODE_ZONE:-}"
REQUESTED_CONTROL_PLANE_DATA_DIR="${FLUXOMNI_CONTROL_PLANE_DATA_DIR:-}"
REQUESTED_MEDIA_NODE_DATA_DIR="${FLUXOMNI_MEDIA_NODE_DATA_DIR:-}"
REQUESTED_SHARED_VIDEO_DIR="${FLUXOMNI_SHARED_VIDEO_DIR:-}"
REQUESTED_CONTROL_PLANE_CONTAINER_NAME="${FLUXOMNI_CONTROL_PLANE_CONTAINER_NAME:-}"
REQUESTED_MEDIA_NODE_CONTAINER_NAME="${FLUXOMNI_MEDIA_NODE_CONTAINER_NAME:-}"
REQUESTED_WATCHTOWER_CONTAINER_NAME="${FLUXOMNI_WATCHTOWER_CONTAINER_NAME:-}"
WITH_INITIAL_UPGRADE="${WITH_INITIAL_UPGRADE:-0}"
WITH_FIREWALLD="${WITH_FIREWALLD:-0}"
WITH_UFW="${WITH_UFW:-0}"
ALLOWED_IPS="${ALLOWED_IPS:-*}"
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

compose_asset_name() {
  case "$FLUXOMNI_INSTALL_TARGET" in
    media-node)
      printf '%s\n' "docker-compose.media-node.yml"
      ;;
    *)
      printf '%s\n' "docker-compose.yml"
      ;;
  esac
}

derive_split_image_repo() {
  local base_repo="$1"
  local suffix="$2"

  if [[ "$base_repo" == */* ]]; then
    printf '%s/%s-%s\n' "${base_repo%/*}" "${base_repo##*/}" "$suffix"
    return
  fi

  printf '%s-%s\n' "$base_repo" "$suffix"
}

resolve_control_plane_image() {
  local base_repo="${1:-${LEGACY_FLUXOMNI_IMAGE:-ghcr.io/fluxomnia-systems/fluxomni}}"

  if [ -n "$FLUXOMNI_CONTROL_PLANE_IMAGE" ]; then
    printf '%s\n' "$FLUXOMNI_CONTROL_PLANE_IMAGE"
    return
  fi

  derive_split_image_repo "$base_repo" "control-plane"
}

resolve_media_node_image() {
  local base_repo="${1:-${LEGACY_FLUXOMNI_IMAGE:-ghcr.io/fluxomnia-systems/fluxomni}}"

  if [ -n "$FLUXOMNI_MEDIA_NODE_IMAGE" ]; then
    printf '%s\n' "$FLUXOMNI_MEDIA_NODE_IMAGE"
    return
  fi

  derive_split_image_repo "$base_repo" "media-node"
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

split_allowed_ips() {
  local input="$1"
  if [ "$input" = "*" ]; then
    printf '*\n'
    return
  fi
  echo "$input" | tr ',' ' ' | xargs -n1 echo
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
    run_privileged apt-get -qy update
    run_privileged apt-get -qy install firewalld
    run_privileged systemctl enable --now firewalld

    run_privileged firewall-cmd --zone=public --permanent --add-service=ssh

    if [ "$ips" = "*" ]; then
      for port in "${tcp_ports[@]}"; do
        run_privileged firewall-cmd --zone=public --permanent --add-port="${port}/tcp"
      done
      for port in "${udp_ports[@]}"; do
        run_privileged firewall-cmd --zone=public --permanent --add-port="${port}/udp"
      done
    else
      while IFS= read -r ip; do
        [ -z "$ip" ] && continue
        for port in "${tcp_ports[@]}"; do
          run_privileged firewall-cmd --permanent --zone=public --add-rich-rule="rule family='ipv4' source address='${ip}' port port='${port}' protocol='tcp' accept"
        done
        for port in "${udp_ports[@]}"; do
          run_privileged firewall-cmd --permanent --zone=public --add-rich-rule="rule family='ipv4' source address='${ip}' port port='${port}' protocol='udp' accept"
        done
      done <<< "$ips"
    fi

    run_privileged firewall-cmd --reload
    return
  fi

  run_privileged apt-get -qy update
  run_privileged apt-get -qy install ufw

  run_privileged ufw allow 22/tcp
  if [ "$ips" = "*" ]; then
    for port in "${tcp_ports[@]}"; do
      run_privileged ufw allow "${port}/tcp"
    done
    for port in "${udp_ports[@]}"; do
      run_privileged ufw allow "${port}/udp"
    done
  else
    while IFS= read -r ip; do
      [ -z "$ip" ] && continue
      for port in "${tcp_ports[@]}"; do
        run_privileged ufw allow from "$ip" to any port "$port" proto tcp
      done
      for port in "${udp_ports[@]}"; do
        run_privileged ufw allow from "$ip" to any port "$port" proto udp
      done
    done <<< "$ips"
  fi

  run_privileged ufw --force enable
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

generate_internal_auth_token() {
  if [ -r /proc/sys/kernel/random/uuid ]; then
    tr -d '-' < /proc/sys/kernel/random/uuid
    return
  fi

  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 24
    return
  fi

  date +%s%N
}

read_env_file_value() {
  local key="$1"
  local env_file="$2"

  if [ ! -f "$env_file" ]; then
    return
  fi

  grep -E "^${key}=" "$env_file" | tail -n1 | cut -d= -f2- || true
}

upsert_env_value() {
  local env_file="$1"
  local key="$2"
  local value="$3"
  local tmp_file

  tmp_file="$(mktemp)"

  if [ -f "$env_file" ]; then
    awk -F= -v key="$key" -v value="$value" '
      BEGIN { replaced=0 }
      $1 == key {
        if (!replaced) {
          print key "=" value
          replaced=1
        }
        next
      }
      { print }
      END {
        if (!replaced) {
          print key "=" value
        }
      }
    ' "$env_file" > "$tmp_file"
  else
    printf '%s=%s\n' "$key" "$value" > "$tmp_file"
  fi

  mv "$tmp_file" "$env_file"
}

format_host_for_url() {
  local host="$1"

  if [[ "$host" == *:* && "$host" != \[*\] ]]; then
    printf '[%s]' "$host"
    return
  fi

  printf '%s' "$host"
}

derive_http_endpoint() {
  local host="$1"
  local port="$2"

  printf 'http://%s:%s\n' "$(format_host_for_url "$host")" "$port"
}

derive_browser_http_url() {
  local host="$1"
  local port="$2"

  if [ "$port" = "80" ]; then
    printf 'http://%s\n' "$(format_host_for_url "$host")"
    return
  fi

  derive_http_endpoint "$host" "$port"
}

sanitize_identifier() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

default_media_node_id() {
  local host_label

  host_label="$(hostname 2>/dev/null || true)"
  host_label="$(sanitize_identifier "${host_label:-node}")"

  if [ -z "$host_label" ]; then
    host_label="node"
  fi

  printf 'media-node-%s\n' "$host_label"
}

default_media_node_name() {
  local host_label

  host_label="$(hostname 2>/dev/null || true)"
  host_label="${host_label:-Node}"

  printf 'Media Node %s\n' "$host_label"
}

resolve_media_node_endpoint_default() {
  local requested_endpoint="$1"
  local existing_endpoint="$2"
  local existing_public_host="$3"
  local existing_grpc_port="$4"
  local current_public_host="$5"
  local current_grpc_port="$6"
  local previous_derived_endpoint current_derived_endpoint

  if [ -n "$requested_endpoint" ]; then
    printf '%s\n' "$requested_endpoint"
    return
  fi

  current_derived_endpoint="$(derive_http_endpoint "$current_public_host" "$current_grpc_port")"

  if [ -z "$existing_endpoint" ]; then
    printf '%s\n' "$current_derived_endpoint"
    return
  fi

  if [ -n "$existing_public_host" ]; then
    previous_derived_endpoint="$(derive_http_endpoint "$existing_public_host" "${existing_grpc_port:-50051}")"
    if [ "$existing_endpoint" = "$previous_derived_endpoint" ]; then
      printf '%s\n' "$current_derived_endpoint"
      return
    fi
  fi

  printf '%s\n' "$existing_endpoint"
}

require_media_node_value() {
  local key="$1"
  local value="$2"

  if [ -n "$value" ]; then
    return
  fi

  echo "Error: ${key} is required when installing a standalone media node." >&2
  exit 1
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

assert_install_assets_match_target() {
  local compose_file="$1"
  local env_example_file="$2"

  if ! grep -q 'FLUXOMNI_MEDIA_NODE_IMAGE' "$compose_file" ||
    ! grep -q 'FLUXOMNI_MEDIA_NODE_IMAGE' "$env_example_file"; then
    echo "Error: downloaded self-host assets from '${REPO_RAW}' do not match the split-runtime installer contract." >&2
    exit 1
  fi

  if [ "$FLUXOMNI_INSTALL_TARGET" = "media-node" ]; then
    if grep -q '^  control-plane:' "$compose_file" ||
      ! grep -q 'FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT' "$compose_file"; then
      echo "Error: downloaded self-host assets from '${REPO_RAW}' do not include the media-node-only install bundle." >&2
      echo "If you are testing a non-main installer ref, set FLUXOMNI_SELFHOST_REF to that same ref." >&2
      exit 1
    fi
    return
  fi

  if ! grep -q '^  control-plane:' "$compose_file" ||
    ! grep -q '^  media-node:' "$compose_file"; then
    echo "Error: downloaded self-host assets from '${REPO_RAW}' are missing the full control-plane/media-node install bundle." >&2
    exit 1
  fi
}

compose_services() {
  "${DOCKER_CMD[@]}" compose config --services
}

assert_compose_services_match_target() {
  local services

  services="$(compose_services)"

  if [ "$FLUXOMNI_INSTALL_TARGET" = "media-node" ]; then
    if printf '%s\n' "$services" | grep -qx 'control-plane'; then
      echo "Error: media-node installs must not include a control-plane service." >&2
      exit 1
    fi
    if ! printf '%s\n' "$services" | grep -qx 'media-node'; then
      echo "Error: media-node installs must include a media-node service." >&2
      exit 1
    fi
    return
  fi

  if ! printf '%s\n' "$services" | grep -qx 'control-plane' ||
    ! printf '%s\n' "$services" | grep -qx 'media-node'; then
    echo "Error: full installs must include both control-plane and media-node services." >&2
    exit 1
  fi
}

parse_http_endpoint() {
  local endpoint="$1"
  local authority host port

  authority="${endpoint#*://}"
  authority="${authority%%/*}"

  if [[ "$authority" == \[*\]:* ]]; then
    host="${authority%%]*}"
    host="${host#[}"
    port="${authority##*\]:}"
  elif [[ "$authority" == *:* ]]; then
    host="${authority%:*}"
    port="${authority##*:}"
  else
    host="$authority"
    port="80"
  fi

  printf '%s\n%s\n' "$host" "$port"
}

probe_tcp_endpoint() {
  local host="$1"
  local port="$2"
  local normalized_host="$host"

  normalized_host="${normalized_host#[}"
  normalized_host="${normalized_host%]}"

  if command -v nc >/dev/null 2>&1; then
    nc -z -w 3 "$normalized_host" "$port" >/dev/null 2>&1
    return
  fi

  if command -v timeout >/dev/null 2>&1; then
    timeout 3 bash -lc ">/dev/tcp/${normalized_host}/${port}" >/dev/null 2>&1
    return
  fi

  return 2
}

preflight_media_node_connectivity() {
  local endpoint="$1"
  local host port
  local parsed

  mapfile -t parsed < <(parse_http_endpoint "$endpoint")
  host="${parsed[0]}"
  port="${parsed[1]}"

  if probe_tcp_endpoint "$host" "$port"; then
    echo "Verified control-plane RPC reachability at ${endpoint}"
    return
  fi

  if [ "$?" -eq 2 ]; then
    echo "Skipping control-plane RPC preflight because neither nc nor timeout is available."
    return
  fi

  echo "Error: could not connect to the control-plane RPC endpoint at ${endpoint}." >&2
  exit 1
}

container_health_status() {
  local container_name="$1"

  "${DOCKER_CMD[@]}" inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_name" 2>/dev/null || printf 'missing\n'
}

wait_for_container_ready() {
  local container_name="$1"
  local label="$2"
  local timeout_secs="${3:-90}"
  local deadline status

  deadline=$((SECONDS + timeout_secs))

  while [ "$SECONDS" -lt "$deadline" ]; do
    status="$(container_health_status "$container_name")"
    case "$status" in
      healthy|running)
        return 0
        ;;
      exited|dead|missing)
        echo "Error: ${label} container is not running (status: ${status})." >&2
        return 1
        ;;
    esac
    sleep 2
  done

  echo "Error: timed out waiting for ${label} to become ready." >&2
  return 1
}

wait_for_media_node_registration() {
  local container_name="$1"
  local timeout_secs="${2:-90}"
  local deadline

  deadline=$((SECONDS + timeout_secs))

  while [ "$SECONDS" -lt "$deadline" ]; do
    if "${DOCKER_CMD[@]}" logs "$container_name" 2>&1 | grep -q "Registered media node with control plane"; then
      return 0
    fi

    if "${DOCKER_CMD[@]}" logs "$container_name" 2>&1 | grep -q "Failed to register media node with control plane"; then
      sleep 2
    else
      sleep 2
    fi
  done

  echo "Error: media node did not confirm registration with the control plane within ${timeout_secs}s." >&2
  return 1
}

print_recent_service_logs() {
  local service="$1"

  echo
  echo "Recent ${service} logs:"
  "${DOCKER_CMD[@]}" compose logs --tail=80 "$service" || true
}

echo "Installing FluxOmni (${FLUXOMNI_INSTALL_TARGET}) to ${FLUXOMNI_DIR}"

validate_install_target
require_cmd curl

if [ "$WITH_INITIAL_UPGRADE" = "1" ]; then
  echo "Running initial system upgrade..."
  run_privileged apt-get -qy update
  run_privileged apt-get -qy upgrade
fi

install_docker_if_missing

if [ "$WITH_FIREWALLD" = "1" ] || [ "$WITH_UFW" = "1" ]; then
  echo "Configuring firewall..."
  configure_firewall
fi

configure_docker_access

CANDIDATE_ENV_FILE="${FLUXOMNI_DIR}/.env"
EXISTING_FLUXOMNI_VERSION="$(read_env_file_value "FLUXOMNI_VERSION" "$CANDIDATE_ENV_FILE")"
FLUXOMNI_VERSION="${REQUESTED_FLUXOMNI_VERSION:-${EXISTING_FLUXOMNI_VERSION:-latest}}"

REPO_RAW="$(resolve_repo_raw)"
COMPOSE_ASSET="$(compose_asset_name)"

if ! "${DOCKER_CMD[@]}" compose version >/dev/null 2>&1; then
  echo "Error: Docker Compose v2 is required."
  echo "Install instructions: https://docs.docker.com/compose/install/"
  exit 1
fi

mkdir -p "${FLUXOMNI_DIR}" "${FLUXOMNI_DIR}/data/videos" "${FLUXOMNI_DIR}/data/dvr" "${FLUXOMNI_DIR}/data/srs-http"

echo "Downloading deployment files..."
download_asset "$COMPOSE_ASSET" "${FLUXOMNI_DIR}/docker-compose.yml"
download_asset ".env.example" "${FLUXOMNI_DIR}/.env.example"
assert_install_assets_match_target "${FLUXOMNI_DIR}/docker-compose.yml" "${FLUXOMNI_DIR}/.env.example"

ENV_FILE="${CANDIDATE_ENV_FILE}"
HOST_IP="$(detect_host_ip)"
LEGACY_IMAGE_BASE="${LEGACY_FLUXOMNI_IMAGE:-$(read_env_file_value "FLUXOMNI_IMAGE" "$ENV_FILE")}"
CONTROL_PLANE_IMAGE_DEFAULT="$(resolve_control_plane_image "$LEGACY_IMAGE_BASE")"
MEDIA_NODE_IMAGE_DEFAULT="$(resolve_media_node_image "$LEGACY_IMAGE_BASE")"

EXISTING_PUBLIC_URL="$(read_env_file_value "FLUXOMNI_PUBLIC_URL" "$ENV_FILE")"
EXISTING_PUBLIC_HOST="$(read_env_file_value "FLUXOMNI_PUBLIC_HOST" "$ENV_FILE")"
EXISTING_MEDIA_NODE_PUBLIC_HOST="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_PUBLIC_HOST" "$ENV_FILE")"
EXISTING_AUTH_TOKEN="$(read_env_file_value "FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN" "$ENV_FILE")"
EXISTING_CONTROL_PLANE_HTTP_PORT="$(read_env_file_value "FLUXOMNI_CONTROL_PLANE_HTTP_PORT" "$ENV_FILE")"
EXISTING_CONTROL_PLANE_RPC_PORT="$(read_env_file_value "FLUXOMNI_CONTROL_PLANE_RPC_PORT" "$ENV_FILE")"
EXISTING_CONTROL_PLANE_RPC_ENDPOINT="$(read_env_file_value "FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT" "$ENV_FILE")"
EXISTING_MEDIA_NODE_GRPC_PORT="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_GRPC_PORT" "$ENV_FILE")"
EXISTING_MEDIA_NODE_ENDPOINT="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_ENDPOINT" "$ENV_FILE")"
EXISTING_MEDIA_NODE_ID="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_ID" "$ENV_FILE")"
EXISTING_MEDIA_NODE_NAME="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_NAME" "$ENV_FILE")"
EXISTING_MEDIA_NODE_LABELS="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_LABELS" "$ENV_FILE")"
EXISTING_MEDIA_NODE_ZONE="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_ZONE" "$ENV_FILE")"
EXISTING_MEDIA_NODE_RTMP_PORT="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_RTMP_PORT" "$ENV_FILE")"
EXISTING_MEDIA_NODE_HLS_PORT="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_HLS_PORT" "$ENV_FILE")"
EXISTING_MEDIA_NODE_SRT_PORT="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_SRT_PORT" "$ENV_FILE")"
EXISTING_MEDIA_NODE_SRS_CALLBACK_PORT="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_SRS_CALLBACK_PORT" "$ENV_FILE")"
EXISTING_CONTROL_PLANE_DATA_DIR="$(read_env_file_value "FLUXOMNI_CONTROL_PLANE_DATA_DIR" "$ENV_FILE")"
EXISTING_MEDIA_NODE_DATA_DIR="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_DATA_DIR" "$ENV_FILE")"
EXISTING_SHARED_VIDEO_DIR="$(read_env_file_value "FLUXOMNI_SHARED_VIDEO_DIR" "$ENV_FILE")"

AUTH_TOKEN_DEFAULT="${FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN:-${EXISTING_AUTH_TOKEN:-}}"
PUBLIC_URL_DEFAULT="${REQUESTED_PUBLIC_URL:-${EXISTING_PUBLIC_URL:-}}"
PUBLIC_HOST_DEFAULT="${REQUESTED_PUBLIC_HOST:-${EXISTING_PUBLIC_HOST:-$HOST_IP}}"
MEDIA_NODE_PUBLIC_HOST_DEFAULT="${REQUESTED_MEDIA_NODE_PUBLIC_HOST:-${EXISTING_MEDIA_NODE_PUBLIC_HOST:-${REQUESTED_PUBLIC_HOST:-${EXISTING_PUBLIC_HOST:-$HOST_IP}}}}"
CONTROL_PLANE_HTTP_PORT_DEFAULT="${REQUESTED_CONTROL_PLANE_HTTP_PORT:-${EXISTING_CONTROL_PLANE_HTTP_PORT:-80}}"
CONTROL_PLANE_RPC_PORT_DEFAULT="${REQUESTED_CONTROL_PLANE_RPC_PORT:-${EXISTING_CONTROL_PLANE_RPC_PORT:-50052}}"
MEDIA_NODE_GRPC_PORT_DEFAULT="${REQUESTED_MEDIA_NODE_GRPC_PORT:-${EXISTING_MEDIA_NODE_GRPC_PORT:-50051}}"
MEDIA_NODE_RTMP_PORT_DEFAULT="${REQUESTED_MEDIA_NODE_RTMP_PORT:-${EXISTING_MEDIA_NODE_RTMP_PORT:-1935}}"
MEDIA_NODE_HLS_PORT_DEFAULT="${REQUESTED_MEDIA_NODE_HLS_PORT:-${EXISTING_MEDIA_NODE_HLS_PORT:-8000}}"
MEDIA_NODE_SRT_PORT_DEFAULT="${REQUESTED_MEDIA_NODE_SRT_PORT:-${EXISTING_MEDIA_NODE_SRT_PORT:-10080}}"
MEDIA_NODE_SRS_CALLBACK_PORT_DEFAULT="${REQUESTED_MEDIA_NODE_SRS_CALLBACK_PORT:-${EXISTING_MEDIA_NODE_SRS_CALLBACK_PORT:-8081}}"
MEDIA_NODE_ID_DEFAULT="${REQUESTED_MEDIA_NODE_ID:-${EXISTING_MEDIA_NODE_ID:-}}"
MEDIA_NODE_NAME_DEFAULT="${REQUESTED_MEDIA_NODE_NAME:-${EXISTING_MEDIA_NODE_NAME:-}}"
MEDIA_NODE_LABELS_DEFAULT="${REQUESTED_MEDIA_NODE_LABELS:-${EXISTING_MEDIA_NODE_LABELS:-selfhost}}"
MEDIA_NODE_ZONE_DEFAULT="${REQUESTED_MEDIA_NODE_ZONE:-${EXISTING_MEDIA_NODE_ZONE:-local}}"
CONTROL_PLANE_DATA_DIR_DEFAULT="${REQUESTED_CONTROL_PLANE_DATA_DIR:-${EXISTING_CONTROL_PLANE_DATA_DIR:-./data}}"
MEDIA_NODE_DATA_DIR_DEFAULT="${REQUESTED_MEDIA_NODE_DATA_DIR:-${EXISTING_MEDIA_NODE_DATA_DIR:-./data}}"
SHARED_VIDEO_DIR_DEFAULT="${REQUESTED_SHARED_VIDEO_DIR:-${EXISTING_SHARED_VIDEO_DIR:-./data/videos}}"

if [ "$FLUXOMNI_INSTALL_TARGET" = "media-node" ]; then
  require_media_node_value "FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT" "${FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT:-${EXISTING_CONTROL_PLANE_RPC_ENDPOINT:-}}"
  require_media_node_value "FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN" "$AUTH_TOKEN_DEFAULT"
  require_media_node_value "FLUXOMNI_MEDIA_NODE_PUBLIC_HOST" "${REQUESTED_MEDIA_NODE_PUBLIC_HOST:-${EXISTING_MEDIA_NODE_PUBLIC_HOST:-}}"

  CONTROL_PLANE_RPC_ENDPOINT_DEFAULT="${FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT:-${EXISTING_CONTROL_PLANE_RPC_ENDPOINT:-}}"

  if [ -z "$MEDIA_NODE_ID_DEFAULT" ]; then
    MEDIA_NODE_ID_DEFAULT="$(default_media_node_id)"
  fi

  if [ -z "$MEDIA_NODE_NAME_DEFAULT" ]; then
    MEDIA_NODE_NAME_DEFAULT="$(default_media_node_name)"
  fi

  MEDIA_NODE_ENDPOINT_DEFAULT="$(
    resolve_media_node_endpoint_default \
      "${FLUXOMNI_MEDIA_NODE_ENDPOINT:-}" \
      "${EXISTING_MEDIA_NODE_ENDPOINT:-}" \
      "${EXISTING_MEDIA_NODE_PUBLIC_HOST:-}" \
      "${EXISTING_MEDIA_NODE_GRPC_PORT:-}" \
      "$MEDIA_NODE_PUBLIC_HOST_DEFAULT" \
      "$MEDIA_NODE_GRPC_PORT_DEFAULT"
  )"

  if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<ENVVARS
# Created by install.sh
FLUXOMNI_VERSION=${FLUXOMNI_VERSION}
FLUXOMNI_MEDIA_NODE_IMAGE=${MEDIA_NODE_IMAGE_DEFAULT}
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=${MEDIA_NODE_PUBLIC_HOST_DEFAULT}
FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT=${CONTROL_PLANE_RPC_ENDPOINT_DEFAULT}
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=${AUTH_TOKEN_DEFAULT}
FLUXOMNI_MEDIA_NODE_ENDPOINT=${MEDIA_NODE_ENDPOINT_DEFAULT}
FLUXOMNI_MEDIA_NODE_GRPC_PORT=${MEDIA_NODE_GRPC_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_ID=${MEDIA_NODE_ID_DEFAULT}
FLUXOMNI_MEDIA_NODE_NAME=${MEDIA_NODE_NAME_DEFAULT}
FLUXOMNI_MEDIA_NODE_LABELS=${MEDIA_NODE_LABELS_DEFAULT}
FLUXOMNI_MEDIA_NODE_ZONE=${MEDIA_NODE_ZONE_DEFAULT}
FLUXOMNI_MEDIA_NODE_RTMP_PORT=${MEDIA_NODE_RTMP_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_HLS_PORT=${MEDIA_NODE_HLS_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_SRT_PORT=${MEDIA_NODE_SRT_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_SRS_CALLBACK_PORT=${MEDIA_NODE_SRS_CALLBACK_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_DATA_DIR=${MEDIA_NODE_DATA_DIR_DEFAULT}
ENVVARS
    echo "Created ${FLUXOMNI_DIR}/.env"
  else
    echo "Updating existing ${FLUXOMNI_DIR}/.env for media-node mode"
  fi

  upsert_env_value "$ENV_FILE" "FLUXOMNI_VERSION" "$FLUXOMNI_VERSION"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_IMAGE" "$MEDIA_NODE_IMAGE_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_PUBLIC_HOST" "$MEDIA_NODE_PUBLIC_HOST_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT" "$CONTROL_PLANE_RPC_ENDPOINT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN" "$AUTH_TOKEN_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_ENDPOINT" "$MEDIA_NODE_ENDPOINT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_GRPC_PORT" "$MEDIA_NODE_GRPC_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_ID" "$MEDIA_NODE_ID_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_NAME" "$MEDIA_NODE_NAME_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_LABELS" "$MEDIA_NODE_LABELS_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_ZONE" "$MEDIA_NODE_ZONE_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_RTMP_PORT" "$MEDIA_NODE_RTMP_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_HLS_PORT" "$MEDIA_NODE_HLS_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_SRT_PORT" "$MEDIA_NODE_SRT_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_SRS_CALLBACK_PORT" "$MEDIA_NODE_SRS_CALLBACK_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_DATA_DIR" "$MEDIA_NODE_DATA_DIR_DEFAULT"

  if [ -n "$REQUESTED_MEDIA_NODE_CONTAINER_NAME" ]; then
    upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_CONTAINER_NAME" "$REQUESTED_MEDIA_NODE_CONTAINER_NAME"
  fi
  if [ -n "$REQUESTED_WATCHTOWER_CONTAINER_NAME" ]; then
    upsert_env_value "$ENV_FILE" "FLUXOMNI_WATCHTOWER_CONTAINER_NAME" "$REQUESTED_WATCHTOWER_CONTAINER_NAME"
  fi
else
  if [ -z "$AUTH_TOKEN_DEFAULT" ]; then
    AUTH_TOKEN_DEFAULT="$(generate_internal_auth_token)"
  fi

  if [ -z "$MEDIA_NODE_ID_DEFAULT" ]; then
    MEDIA_NODE_ID_DEFAULT="media-node-1"
  fi

  if [ -z "$MEDIA_NODE_NAME_DEFAULT" ]; then
    MEDIA_NODE_NAME_DEFAULT="Media Node 1"
  fi

  if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<ENVVARS
# Created by install.sh
FLUXOMNI_VERSION=${FLUXOMNI_VERSION}
FLUXOMNI_PUBLIC_HOST=${PUBLIC_HOST_DEFAULT}
FLUXOMNI_MEDIA_NODE_PUBLIC_HOST=${MEDIA_NODE_PUBLIC_HOST_DEFAULT}
FLUXOMNI_CONTROL_PLANE_IMAGE=${CONTROL_PLANE_IMAGE_DEFAULT}
FLUXOMNI_MEDIA_NODE_IMAGE=${MEDIA_NODE_IMAGE_DEFAULT}
FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=${AUTH_TOKEN_DEFAULT}
FLUXOMNI_CONTROL_PLANE_HTTP_PORT=${CONTROL_PLANE_HTTP_PORT_DEFAULT}
FLUXOMNI_CONTROL_PLANE_RPC_PORT=${CONTROL_PLANE_RPC_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_ID=${MEDIA_NODE_ID_DEFAULT}
FLUXOMNI_MEDIA_NODE_NAME=${MEDIA_NODE_NAME_DEFAULT}
FLUXOMNI_MEDIA_NODE_RTMP_PORT=${MEDIA_NODE_RTMP_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_HLS_PORT=${MEDIA_NODE_HLS_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_SRT_PORT=${MEDIA_NODE_SRT_PORT_DEFAULT}
FLUXOMNI_MEDIA_NODE_DATA_DIR=${MEDIA_NODE_DATA_DIR_DEFAULT}
FLUXOMNI_CONTROL_PLANE_DATA_DIR=${CONTROL_PLANE_DATA_DIR_DEFAULT}
FLUXOMNI_SHARED_VIDEO_DIR=${SHARED_VIDEO_DIR_DEFAULT}
ENVVARS
    echo "Created ${FLUXOMNI_DIR}/.env"
  else
    echo "Updating existing ${FLUXOMNI_DIR}/.env"
  fi

  upsert_env_value "$ENV_FILE" "FLUXOMNI_VERSION" "$FLUXOMNI_VERSION"
  if [ -n "$PUBLIC_URL_DEFAULT" ]; then
    upsert_env_value "$ENV_FILE" "FLUXOMNI_PUBLIC_URL" "$PUBLIC_URL_DEFAULT"
  fi
  upsert_env_value "$ENV_FILE" "FLUXOMNI_PUBLIC_HOST" "$PUBLIC_HOST_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_PUBLIC_HOST" "$MEDIA_NODE_PUBLIC_HOST_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_CONTROL_PLANE_IMAGE" "$CONTROL_PLANE_IMAGE_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_IMAGE" "$MEDIA_NODE_IMAGE_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN" "$AUTH_TOKEN_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_CONTROL_PLANE_HTTP_PORT" "$CONTROL_PLANE_HTTP_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_CONTROL_PLANE_RPC_PORT" "$CONTROL_PLANE_RPC_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_ID" "$MEDIA_NODE_ID_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_NAME" "$MEDIA_NODE_NAME_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_RTMP_PORT" "$MEDIA_NODE_RTMP_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_HLS_PORT" "$MEDIA_NODE_HLS_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_SRT_PORT" "$MEDIA_NODE_SRT_PORT_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_CONTROL_PLANE_DATA_DIR" "$CONTROL_PLANE_DATA_DIR_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_DATA_DIR" "$MEDIA_NODE_DATA_DIR_DEFAULT"
  upsert_env_value "$ENV_FILE" "FLUXOMNI_SHARED_VIDEO_DIR" "$SHARED_VIDEO_DIR_DEFAULT"

  if [ -n "$REQUESTED_CONTROL_PLANE_CONTAINER_NAME" ]; then
    upsert_env_value "$ENV_FILE" "FLUXOMNI_CONTROL_PLANE_CONTAINER_NAME" "$REQUESTED_CONTROL_PLANE_CONTAINER_NAME"
  fi
  if [ -n "$REQUESTED_MEDIA_NODE_CONTAINER_NAME" ]; then
    upsert_env_value "$ENV_FILE" "FLUXOMNI_MEDIA_NODE_CONTAINER_NAME" "$REQUESTED_MEDIA_NODE_CONTAINER_NAME"
  fi
  if [ -n "$REQUESTED_WATCHTOWER_CONTAINER_NAME" ]; then
    upsert_env_value "$ENV_FILE" "FLUXOMNI_WATCHTOWER_CONTAINER_NAME" "$REQUESTED_WATCHTOWER_CONTAINER_NAME"
  fi
fi

touch "${FLUXOMNI_DIR}/data/state.db"

cd "${FLUXOMNI_DIR}"

assert_compose_services_match_target

if [ "$FLUXOMNI_INSTALL_TARGET" = "media-node" ]; then
  preflight_media_node_connectivity "$(read_env_file_value "FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT" .env)"
fi

echo "Pulling images and starting containers..."
"${DOCKER_CMD[@]}" compose pull
"${DOCKER_CMD[@]}" compose up -d --remove-orphans

CONTROL_PLANE_CONTAINER_NAME="${REQUESTED_CONTROL_PLANE_CONTAINER_NAME:-$(read_env_file_value "FLUXOMNI_CONTROL_PLANE_CONTAINER_NAME" .env)}"
MEDIA_NODE_CONTAINER_NAME="${REQUESTED_MEDIA_NODE_CONTAINER_NAME:-$(read_env_file_value "FLUXOMNI_MEDIA_NODE_CONTAINER_NAME" .env)}"
CONTROL_PLANE_CONTAINER_NAME="${CONTROL_PLANE_CONTAINER_NAME:-fluxomni-control-plane}"
MEDIA_NODE_CONTAINER_NAME="${MEDIA_NODE_CONTAINER_NAME:-fluxomni-media-node}"

if [ "$FLUXOMNI_INSTALL_TARGET" = "media-node" ]; then
  if ! wait_for_container_ready "$MEDIA_NODE_CONTAINER_NAME" "media-node"; then
    print_recent_service_logs "media-node"
    exit 1
  fi

  if ! wait_for_media_node_registration "$MEDIA_NODE_CONTAINER_NAME"; then
    print_recent_service_logs "media-node"
    exit 1
  fi

  MEDIA_HOST="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_PUBLIC_HOST" .env)"
  MEDIA_NODE_ENDPOINT="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_ENDPOINT" .env)"
  MEDIA_NODE_ID="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_ID" .env)"

  echo
  echo "Media node is connected"
  echo "Node ID : ${MEDIA_NODE_ID}"
  echo "Node RPC: ${MEDIA_NODE_ENDPOINT}"
  echo "RTMP    : rtmp://${MEDIA_HOST}:1935/app"
  echo "Data    : ${FLUXOMNI_DIR}/data"
  echo
  echo "Common commands:"
  echo "  Update: cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose pull && ${DOCKER_DISPLAY} compose up -d"
  echo "  Logs  : cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose logs -f media-node"
  echo "  Stop  : cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose down"
  exit 0
fi

if ! wait_for_container_ready "$CONTROL_PLANE_CONTAINER_NAME" "control-plane"; then
  print_recent_service_logs "control-plane"
  exit 1
fi

if ! wait_for_container_ready "$MEDIA_NODE_CONTAINER_NAME" "media-node"; then
  print_recent_service_logs "media-node"
  exit 1
fi

HOST="$(read_env_file_value "FLUXOMNI_PUBLIC_HOST" .env)"
MEDIA_HOST="$(read_env_file_value "FLUXOMNI_MEDIA_NODE_PUBLIC_HOST" .env)"
HTTP_PORT="$(read_env_file_value "FLUXOMNI_CONTROL_PLANE_HTTP_PORT" .env)"
HOST="${HOST:-127.0.0.1}"
MEDIA_HOST="${MEDIA_HOST:-$HOST}"
HTTP_PORT="${HTTP_PORT:-80}"

echo
echo "FluxOmni is ready"
echo "Web UI: $(derive_browser_http_url "$HOST" "$HTTP_PORT")"
echo "RTMP : rtmp://${MEDIA_HOST}:1935/app"
echo "Data : ${FLUXOMNI_DIR}/data"
echo
echo "Common commands:"
echo "  Update: cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose pull && ${DOCKER_DISPLAY} compose up -d"
echo "  Logs  : cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose logs -f control-plane media-node"
echo "  Stop  : cd ${FLUXOMNI_DIR} && ${DOCKER_DISPLAY} compose down"
