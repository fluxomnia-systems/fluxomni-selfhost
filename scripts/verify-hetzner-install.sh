#!/usr/bin/env bash
set -euo pipefail

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' was not found." >&2
    exit 1
  fi
}

for cmd in curl jq ssh ssh-keygen grep mktemp timeout; do
  require_cmd "$cmd"
done

HCLOUD_API="${HCLOUD_API:-https://api.hetzner.cloud/v1}"
HCLOUD_TOKEN="${HCLOUD_TOKEN:?Set HCLOUD_TOKEN}"
HCLOUD_SERVER_TYPE="${HCLOUD_SERVER_TYPE:-cpx11}"
HCLOUD_LOCATION="${HCLOUD_LOCATION:-nbg1}"
HCLOUD_IMAGE="${HCLOUD_IMAGE:-ubuntu-24.04}"
FLUXOMNI_VERSION="${FLUXOMNI_VERSION:-latest}"
WITH_UFW="${WITH_UFW:-1}"
INSTALL_SCRIPT_URL="${INSTALL_SCRIPT_URL:?Set INSTALL_SCRIPT_URL}"
REPO_RAW="${REPO_RAW:?Set REPO_RAW}"
PROVISION_TIMEOUT_SECS="${PROVISION_TIMEOUT_SECS:-1800}"
SERVER_STATUS_TIMEOUT_SECS="${SERVER_STATUS_TIMEOUT_SECS:-300}"
SSH_TIMEOUT_SECS="${SSH_TIMEOUT_SECS:-300}"
SERVER_NAME="${SERVER_NAME:-fluxomni-ci-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}}"
SSH_KEY_NAME="${SSH_KEY_NAME:-${SERVER_NAME}-ssh}"
RUN_ID_LABEL="${GITHUB_RUN_ID:-local}"
WORKFLOW_LABEL="fluxomni-selfhost-verify"

WORK_DIR="$(mktemp -d "${RUNNER_TEMP:-/tmp}/fluxomni-hetzner-XXXXXX")"
KNOWN_HOSTS_FILE="${WORK_DIR}/known_hosts"
SSH_PRIVATE_KEY_PATH="${WORK_DIR}/id_ed25519"
SSH_PUBLIC_KEY_PATH="${SSH_PRIVATE_KEY_PATH}.pub"
USER_DATA_PATH="${WORK_DIR}/user-data.sh"
HTTP_BODY_PATH="${WORK_DIR}/http-index.html"
HCLOUD_SERVER_ID=""
HCLOUD_SSH_KEY_ID=""
SERVER_IP=""

touch "$KNOWN_HOSTS_FILE"

api_request() {
  local method="$1"
  local path="$2"
  local data="${3:-}"
  local response http_code body

  if [ -n "$data" ]; then
    response="$(curl -sS -X "$method" \
      -H "Authorization: Bearer ${HCLOUD_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$data" \
      -w $'\n%{http_code}' \
      "${HCLOUD_API}${path}")"
  else
    response="$(curl -sS -X "$method" \
      -H "Authorization: Bearer ${HCLOUD_TOKEN}" \
      -w $'\n%{http_code}' \
      "${HCLOUD_API}${path}")"
  fi

  http_code="${response##*$'\n'}"
  body="${response%$'\n'*}"

  if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 300 ]; then
    echo "Hetzner API ${method} ${path} failed with HTTP ${http_code}" >&2
    echo "$body" >&2
    return 1
  fi

  printf '%s' "$body"
}

ssh_base_args() {
  printf '%s\n' \
    -i "$SSH_PRIVATE_KEY_PATH" \
    -o BatchMode=yes \
    -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile="$KNOWN_HOSTS_FILE" \
    -o ConnectTimeout=10
}

ssh_cmd() {
  local args=()
  while IFS= read -r arg; do
    args+=("$arg")
  done < <(ssh_base_args)

  # shellcheck disable=SC2029
  ssh "${args[@]}" "root@${SERVER_IP}" "$@"
}

collect_remote_diagnostics() {
  if [ -z "$SERVER_IP" ] || [ ! -f "$SSH_PRIVATE_KEY_PATH" ]; then
    return 0
  fi

  echo
  echo "Collecting remote diagnostics from ${SERVER_IP}"

  ssh_cmd 'cloud-init status --long || true' || true
  ssh_cmd 'tail -n 200 /var/log/cloud-init-output.log || true' || true
  ssh_cmd 'tail -n 200 /var/log/fluxomni-provision.log || true' || true
  ssh_cmd 'docker ps -a || true' || true
  ssh_cmd 'cd /root/fluxomni && docker compose ps || true' || true
  ssh_cmd 'cd /root/fluxomni && docker compose logs --tail=80 control-plane media-node || true' || true
}

write_summary() {
  if [ -z "${GITHUB_STEP_SUMMARY:-}" ]; then
    return 0
  fi

  {
    echo "## Hetzner provisioning verification passed"
    echo
    printf -- "- Server ID: \`%s\`\n" "$HCLOUD_SERVER_ID"
    printf -- "- Server IP: \`%s\`\n" "$SERVER_IP"
    printf -- "- Hetzner location: \`%s\`\n" "$HCLOUD_LOCATION"
    printf -- "- Hetzner image: \`%s\`\n" "$HCLOUD_IMAGE"
    printf -- "- Hetzner server type: \`%s\`\n" "$HCLOUD_SERVER_TYPE"
    printf -- "- FluxOmni version: \`%s\`\n" "$FLUXOMNI_VERSION"
    printf -- "- Install script: \`%s\`\n" "$INSTALL_SCRIPT_URL"
    printf -- "- Asset base: \`%s\`\n" "$REPO_RAW"
  } >> "$GITHUB_STEP_SUMMARY"
}

cleanup() {
  local exit_code=$?

  if [ "$exit_code" -ne 0 ]; then
    collect_remote_diagnostics || true
  fi

  if [ -n "$HCLOUD_SERVER_ID" ]; then
    echo "Deleting Hetzner server ${HCLOUD_SERVER_ID}"
    api_request DELETE "/servers/${HCLOUD_SERVER_ID}" >/dev/null || true
  fi

  if [ -n "$HCLOUD_SSH_KEY_ID" ]; then
    echo "Deleting Hetzner SSH key ${HCLOUD_SSH_KEY_ID}"
    api_request DELETE "/ssh_keys/${HCLOUD_SSH_KEY_ID}" >/dev/null || true
  fi

  rm -rf "$WORK_DIR"

  exit "$exit_code"
}
trap cleanup EXIT

generate_temp_ssh_key() {
  echo "Generating temporary SSH key"
  ssh-keygen -q -t ed25519 -N "" -C "$SSH_KEY_NAME" -f "$SSH_PRIVATE_KEY_PATH"
}

register_temp_ssh_key() {
  local public_key payload response

  echo "Registering temporary SSH key in Hetzner Cloud"
  public_key="$(cat "$SSH_PUBLIC_KEY_PATH")"
  payload="$(jq -n \
    --arg name "$SSH_KEY_NAME" \
    --arg public_key "$public_key" \
    '{name: $name, public_key: $public_key}')"
  response="$(api_request POST "/ssh_keys" "$payload")"
  HCLOUD_SSH_KEY_ID="$(jq -r '.ssh_key.id // empty' <<<"$response")"

  if [ -z "$HCLOUD_SSH_KEY_ID" ]; then
    echo "Error: failed to parse Hetzner SSH key id" >&2
    echo "$response" >&2
    exit 1
  fi
}

create_user_data() {
  local install_script_url_q repo_raw_q fluxomni_version_q with_ufw_q

  install_script_url_q="$(printf '%q' "$INSTALL_SCRIPT_URL")"
  repo_raw_q="$(printf '%q' "$REPO_RAW")"
  fluxomni_version_q="$(printf '%q' "$FLUXOMNI_VERSION")"
  with_ufw_q="$(printf '%q' "$WITH_UFW")"

  cat > "$USER_DATA_PATH" <<EOF
#!/bin/bash
set -euxo pipefail
exec > >(tee -a /var/log/fluxomni-provision.log) 2>&1
export DEBIAN_FRONTEND=noninteractive

INSTALL_SCRIPT_URL=${install_script_url_q}
REPO_RAW=${repo_raw_q}
FLUXOMNI_VERSION=${fluxomni_version_q}
WITH_UFW=${with_ufw_q}

apt-get update
apt-get install -y curl
curl -fsSL "\$INSTALL_SCRIPT_URL" -o /root/install.sh
chmod +x /root/install.sh
FLUXOMNI_VERSION="\$FLUXOMNI_VERSION" \
FLUXOMNI_REPO_RAW="\$REPO_RAW" \
WITH_UFW="\$WITH_UFW" \
bash /root/install.sh
EOF
}

create_server() {
  local payload response

  echo "Creating temporary Hetzner server ${SERVER_NAME}"
  create_user_data

  payload="$(jq -n \
    --arg name "$SERVER_NAME" \
    --arg server_type "$HCLOUD_SERVER_TYPE" \
    --arg image "$HCLOUD_IMAGE" \
    --arg location "$HCLOUD_LOCATION" \
    --arg run_id "$RUN_ID_LABEL" \
    --arg workflow "$WORKFLOW_LABEL" \
    --argjson ssh_keys "[$HCLOUD_SSH_KEY_ID]" \
    --rawfile user_data "$USER_DATA_PATH" \
    '{
      name: $name,
      server_type: $server_type,
      image: $image,
      location: $location,
      ssh_keys: $ssh_keys,
      user_data: $user_data,
      labels: {
        "managed-by": "github-actions",
        "purpose": "fluxomni-provision-verify",
        "run-id": $run_id,
        "workflow": $workflow
      }
    }')"

  response="$(api_request POST "/servers" "$payload")"
  HCLOUD_SERVER_ID="$(jq -r '.server.id // empty' <<<"$response")"
  SERVER_IP="$(jq -r '.server.public_net.ipv4.ip // empty' <<<"$response")"

  if [ -z "$HCLOUD_SERVER_ID" ]; then
    echo "Error: failed to parse Hetzner server id" >&2
    echo "$response" >&2
    exit 1
  fi
}

wait_for_server_running() {
  local deadline response status ip

  echo "Waiting for server to reach running state"
  deadline=$((SECONDS + SERVER_STATUS_TIMEOUT_SECS))
  while [ "$SECONDS" -lt "$deadline" ]; do
    response="$(api_request GET "/servers/${HCLOUD_SERVER_ID}")"
    status="$(jq -r '.server.status // empty' <<<"$response")"
    ip="$(jq -r '.server.public_net.ipv4.ip // empty' <<<"$response")"

    if [ "$status" = "running" ] && [ -n "$ip" ]; then
      SERVER_IP="$ip"
      echo "Server is running at ${SERVER_IP}"
      return 0
    fi

    sleep 5
  done

  echo "Error: timed out waiting for Hetzner server ${HCLOUD_SERVER_ID} to enter running state" >&2
  exit 1
}

wait_for_ssh() {
  local deadline args=()

  echo "Waiting for SSH on ${SERVER_IP}"
  while IFS= read -r arg; do
    args+=("$arg")
  done < <(ssh_base_args)

  deadline=$((SECONDS + SSH_TIMEOUT_SECS))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if ssh "${args[@]}" "root@${SERVER_IP}" true >/dev/null 2>&1; then
      echo "SSH is ready"
      return 0
    fi
    sleep 5
  done

  echo "Error: timed out waiting for SSH on ${SERVER_IP}" >&2
  exit 1
}

verify_provisioning() {
  local deadline http_ok=0
  local args=()

  while IFS= read -r arg; do
    args+=("$arg")
  done < <(ssh_base_args)

  echo "Waiting for cloud-init provisioning to complete"
  timeout --foreground "$PROVISION_TIMEOUT_SECS" \
    ssh "${args[@]}" "root@${SERVER_IP}" 'cloud-init status --wait'

  echo "Verifying FluxOmni installation on the server"
  ssh_cmd 'test -f /root/fluxomni/.env'
  ssh_cmd 'docker inspect -f "{{.State.Status}}" fluxomni-control-plane | grep -qx running'
  ssh_cmd 'docker inspect -f "{{.State.Status}}" fluxomni-media-node | grep -qx running'
  ssh_cmd 'docker logs --since 20m fluxomni-media-node 2>&1 | grep -q "Registered media node with control plane"'
  ssh_cmd 'cd /root/fluxomni && docker compose ps'

  echo "Checking public HTTP endpoint"
  deadline=$((SECONDS + 180))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if curl -fsSL --connect-timeout 5 "http://${SERVER_IP}/" -o "$HTTP_BODY_PATH"; then
      if grep -Eqi '<!doctype html|<html|fluxomni' "$HTTP_BODY_PATH"; then
        http_ok=1
        break
      fi
    fi
    sleep 5
  done

  if [ "$http_ok" -ne 1 ]; then
    echo "Error: FluxOmni UI did not become reachable at http://${SERVER_IP}/" >&2
    exit 1
  fi
}

generate_temp_ssh_key
register_temp_ssh_key
create_server
wait_for_server_running
wait_for_ssh
verify_provisioning
write_summary

echo "Hetzner provisioning verification passed for ${SERVER_NAME} (${SERVER_IP})"
