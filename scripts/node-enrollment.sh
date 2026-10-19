#!/usr/bin/env bash
# One-time node provisioning. Machine secrets stay in owner-only files.
write_enrollment_ca() {
  local encoded="$1" destination="$2" temporary
  [ -n "$encoded" ] || return 0
  temporary=$(mktemp "${destination}.XXXXXX")
  if ! printf '%s' "$encoded" | openssl base64 -d -A > "$temporary" ||
    ! openssl x509 -in "$temporary" -noout >/dev/null 2>&1; then
    rm -f "$temporary"
    echo 'Error: invalid TLS CA certificates.' >&2
    return 1
  fi
  chmod 600 "$temporary"
  mv "$temporary" "$destination"
}

# @lat: [[installation#One-time node enrollment]]
prepare_node_enrollment() {
  set +x
  local node="$1" endpoint="$2" secrets credential identity temporary digest
  local code="${FLUXOMNI_ENROLLMENT_CODE:-}" url="${FLUXOMNI_ENROLLMENT_URL:-}"
  local had_credential=false
  local -a trust=()
  umask 077
  case "$node" in ''|*[!A-Za-z0-9._-]*) echo 'Error: invalid node ID.' >&2; return 1 ;; esac
  case "$endpoint" in https://*) ;; *) echo 'Error: outbound control requires an HTTPS endpoint.' >&2; return 1 ;; esac
  command -v openssl >/dev/null || { echo 'Error: install openssl before enrolling a node.' >&2; return 1; }
  secrets="${FLUXOMNI_DIR}/node-secrets"
  credential="$secrets/credential"
  identity=$(printf '%s\n%s' "$node" "$endpoint")
  [ ! -L "$secrets" ] || { echo 'Error: node-secrets must be an owned directory.' >&2; return 1; }
  mkdir -p "$secrets"
  chmod 700 "$secrets"
  local file
  for file in credential identity enrolled ca.crt enrollment-ca.crt; do
    [ ! -L "$secrets/$file" ] || { echo 'Error: node secret files must not be symlinks.' >&2; return 1; }
  done
  if [ -s "$credential" ] && [ -f "$secrets/identity" ] && [ "$(cat "$secrets/identity")" != "$identity" ]; then
    echo 'Error: saved credential belongs to another node or control endpoint. Keep the original identity and reuse its credential.' >&2
    return 1
  fi
  write_enrollment_ca "${FLUXOMNI_CONTROL_TLS_CA_PEM_BASE64:-}" "$secrets/ca.crt"
  write_enrollment_ca "${FLUXOMNI_ENROLLMENT_TLS_CA_PEM_BASE64:-}" "$secrets/enrollment-ca.crt"
  [ ! -s "$credential" ] || had_credential=true
  if [ -f "$secrets/enrolled" ] && [ ! -s "$credential" ]; then
    echo 'Error: restore the missing credential from backup; do not replace it.' >&2
    return 1
  fi
  if [ ! -s "$credential" ]; then
    temporary=$(mktemp "$secrets/.credential.XXXXXX")
    openssl rand -hex 32 > "$temporary"
    # Concurrent retries keep the first saved secret.
    ln "$temporary" "$credential" 2>/dev/null || [ -s "$credential" ]
    rm -f "$temporary"
  fi
  chmod 600 "$credential"
  local credential_size
  credential_size=$(wc -c < "$credential" | tr -d ' ')
  if { [ "$credential_size" != 64 ] && [ "$credential_size" != 65 ]; } ||
    ! LC_ALL=C grep -Eq '^[a-f0-9]{64}$' "$credential"; then
    echo 'Error: saved node credential is damaged. Keep the file and follow the credential recovery procedure.' >&2
    return 1
  fi
  temporary=$(mktemp "$secrets/.identity.XXXXXX")
  printf '%s\n' "$identity" > "$temporary"
  if ! ln "$temporary" "$secrets/identity" 2>/dev/null && [ "$(cat "$secrets/identity")" != "$identity" ]; then
    rm -f "$temporary"
    echo 'Error: another installer saved a different node identity. Reuse the original identity.' >&2
    return 1
  fi
  rm -f "$temporary"
  digest=$(tr -d '\r\n' < "$credential" | openssl dgst -sha256 | sed 's/^.*= //')
  if [ -f "$secrets/enrolled" ] && [ "$(cat "$secrets/enrolled")" = "$digest" ]; then
    echo 'Reusing saved node credential.'
  elif [ "$had_credential" = true ] && [ -z "$code" ]; then
    echo 'Checking the saved credential through the outbound control connection.'
  else
    if [[ ! "$url" =~ ^https://[^[:space:]\"\\]+$ ]] || [[ ! "$code" =~ ^[A-Za-z0-9._-]+$ ]]; then
      echo 'Error: run a fresh HTTPS join command from Fleet. The saved credential is kept for retry.' >&2
      return 1
    fi
    [ ! -s "$secrets/enrollment-ca.crt" ] || trust=(--cacert "$secrets/enrollment-ca.crt")
    temporary=$(mktemp "$secrets/.receipt.XXXXXX")
    local status
    status=$(printf '{"nodeId":"%s","code":"%s","credentialHash":"%s"}' "$node" "$code" "$digest" |
      curl --silent --show-error --proto '=https' --tlsv1.2 --connect-timeout 10 --max-time 30 \
        "${trust[@]}" --request POST --header 'Content-Type: application/json' --data-binary @- --output "$temporary" --write-out '%{http_code}' "$url") || status=000
    case "$status" in
      4*)
        rm -f "$temporary"
        echo 'Error: enrollment was rejected. Rerun the original command first; use a new Fleet code only if no credential was committed. The saved credential is kept.' >&2
        return 1
        ;;
    esac
    if [ "$status" = 200 ] && grep -Eq '"enrolled"[[:space:]]*:[[:space:]]*true' "$temporary"; then
      confirm_node_enrollment
    else
      echo 'Enrollment response was not confirmed. Checking the saved credential through the outbound control connection.'
    fi
    rm -f "$temporary"
  fi
  unset FLUXOMNI_ENROLLMENT_CODE FLUXOMNI_ENROLLMENT_URL FLUXOMNI_CONTROL_TLS_CA_PEM_BASE64 FLUXOMNI_ENROLLMENT_TLS_CA_PEM_BASE64
  echo 'Node credential saved. Starting the outbound control connection.'
}

# A successful redemption or this boot's Hello/Welcome confirms the saved hash.
confirm_node_enrollment() {
  local secrets="${FLUXOMNI_DIR}/node-secrets" temporary digest
  digest=$(tr -d '\r\n' < "$secrets/credential" | openssl dgst -sha256 | sed 's/^.*= //')
  temporary=$(mktemp "$secrets/.enrolled.XXXXXX")
  printf '%s\n' "$digest" > "$temporary"
  mv "$temporary" "$secrets/enrolled"
}
