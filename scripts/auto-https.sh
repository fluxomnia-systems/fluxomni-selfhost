#!/bin/sh
# Classify FLUXOMNI_PUBLIC_HOST and render the auto-HTTPS Caddy assets.
#   domain      -> ordinary ACME for the DNS name
#   public-ip   -> short-lived (160-hour) Let's Encrypt profile for the IP
#   local       -> stay on plain HTTP, no certificate is attempted
# Commands:
#   classify <host>                 prints domain|public-ip|local
#   render-caddyfile <host> <out>   writes the Caddyfile for a public host
#   compose-override <dir>          writes docker-compose.https.yml into <dir>
set -eu

fail() {
  printf 'auto-https: %s\n' "$*" >&2
  exit 1
}

is_ipv4() {
  printf '%s' "$1" | grep -Eq '^([0-9]{1,3}\.){3}[0-9]{1,3}$' || return 1
  old_ifs=$IFS
  IFS=.
  # shellcheck disable=SC2086
  set -- $1
  IFS=$old_ifs
  [ "$#" -eq 4 ] || return 1
  for octet in "$@"; do
    case "$octet" in
      ''|*[!0-9]*) return 1 ;;
    esac
    stripped=$octet
    while [ "${stripped#0}" != "$stripped" ] && [ "${#stripped}" -gt 1 ]; do
      stripped=${stripped#0}
    done
    [ "$octet" = "$stripped" ] || return 1
    [ "$stripped" -le 255 ] || return 1
  done
}

ipv4_is_public() {
  old_ifs=$IFS
  IFS=.
  # shellcheck disable=SC2086
  set -- $1
  IFS=$old_ifs
  o1=$1
  o2=$2
  o3=$3
  [ "$o1" -eq 0 ] || [ "$o1" -eq 10 ] || [ "$o1" -eq 127 ] && return 1
  [ "$o1" -eq 169 ] && [ "$o2" -eq 254 ] && return 1
  [ "$o1" -eq 172 ] && [ "$o2" -ge 16 ] && [ "$o2" -le 31 ] && return 1
  [ "$o1" -eq 192 ] && [ "$o2" -eq 168 ] && return 1
  [ "$o1" -eq 192 ] && [ "$o2" -eq 0 ] && { [ "$o3" -eq 0 ] || [ "$o3" -eq 2 ]; } && return 1
  [ "$o1" -eq 198 ] && { [ "$o2" -ge 18 ] && [ "$o2" -le 19 ]; } && return 1
  [ "$o1" -eq 198 ] && [ "$o2" -eq 51 ] && [ "$o3" -eq 100 ] && return 1
  [ "$o1" -eq 203 ] && [ "$o2" -eq 0 ] && [ "$o3" -eq 113 ] && return 1
  [ "$o1" -eq 100 ] && [ "$o2" -ge 64 ] && [ "$o2" -le 127 ] && return 1
  [ "$o1" -ge 224 ] && return 1
  return 0
}

hex_value() {
  awk -v value="$1" 'BEGIN {
    digits = "0123456789abcdef"
    number = 0
    text = tolower(value)
    if (length(text) == 0) exit 1
    for (i = 1; i <= length(text); i++) {
      position = index(digits, substr(text, i, 1))
      if (position == 0) exit 1
      number = number * 16 + position - 1
    }
    printf "%d", number
  }'
}

count_ipv6_groups() {
  if [ -z "$1" ]; then
    printf '0'
    return
  fi
  old_ifs=$IFS
  IFS=:
  # shellcheck disable=SC2086
  set -- $1
  IFS=$old_ifs
  printf '%s' "$#"
}

ipv6_groups_ok() {
  if [ -z "$1" ]; then
    return 0
  fi
  old_ifs=$IFS
  IFS=:
  # shellcheck disable=SC2086
  set -- $1
  IFS=$old_ifs
  for group in "$@"; do
    printf '%s' "$group" | grep -Eq '^[0-9A-Fa-f]{1,4}$' || return 1
  done
}

is_ipv6() {
  printf '%s' "$1" | grep -Eq '^[0-9A-Fa-f:]+$' || return 1
  case "$1" in
    *:*) ;;
    *) return 1 ;;
  esac
  case "$1" in
    *:::*) return 1 ;;
  esac
  doubles=$(printf '%s' "$1" | awk -F'::' '{print NF}')
  case "$doubles" in
    1)
      count=$(count_ipv6_groups "$1")
      [ "$count" -eq 8 ] || return 1
      ipv6_groups_ok "$1"
      ;;
    2)
      left=${1%%::*}
      right=${1#*::}
      total=$(( $(count_ipv6_groups "$left") + $(count_ipv6_groups "$right") ))
      [ "$total" -le 7 ] || return 1
      ipv6_groups_ok "$left" && ipv6_groups_ok "$right"
      ;;
    *) return 1 ;;
  esac
}

expand_ipv6() {
  value=$1
  case "$value" in
    ::) printf '0:0:0:0:0:0:0:0'; return ;;
    ::*) value=0${value} ;;
  esac
  case "$value" in
    *::) value=${value}0 ;;
  esac
  left=${value%%::*}
  if [ "$left" = "$value" ]; then
    printf '%s' "$value"
    return
  fi
  right=${value#*::}
  missing=$((8 - $(count_ipv6_groups "$left") - $(count_ipv6_groups "$right")))
  zeros=
  i=0
  while [ "$i" -lt "$missing" ]; do
    zeros=${zeros}:0
    i=$((i + 1))
  done
  printf '%s%s:%s' "$left" "$zeros" "$right"
}

ipv6_is_public() {
  value=$(printf '%s' "$1" | tr 'A-F' 'a-f')
  case "$value" in
    ::|::1|::*) return 1 ;;
  esac
  first=${value%%:*}
  first_n=$(hex_value "$first") || return 1
  # fe80::/10, fc00::/7, ff00::/8 are not public.
  [ "$first_n" -ge 65152 ] && [ "$first_n" -le 65215 ] && return 1
  [ "$first_n" -ge 64512 ] && [ "$first_n" -le 65023 ] && return 1
  [ "$first_n" -ge 65280 ] && return 1
  second=$(printf '%s' "$value" | awk -F: '{print $2}')
  if [ "$first" = "2001" ] && [ -n "$second" ]; then
    second_n=$(hex_value "$second") || return 1
    [ "$second_n" -eq 3512 ] && return 1 # 2001:db8::/32 documentation
  fi
  expanded=$(expand_ipv6 "$value")
  g1=$(printf '%s' "$expanded" | awk -F: '{print $1}')
  g2=$(printf '%s' "$expanded" | awk -F: '{print $2}')
  g3=$(printf '%s' "$expanded" | awk -F: '{print $3}')
  g4=$(printf '%s' "$expanded" | awk -F: '{print $4}')
  g1_n=$(hex_value "$g1") || return 1
  g2_n=$(hex_value "$g2") || return 1
  g3_n=$(hex_value "$g3") || return 1
  g4_n=$(hex_value "$g4") || return 1
  # 100::/64 discard-only, 2001:2::/48 benchmarking.
  [ "$g1_n" -eq 256 ] && [ "$g2_n" -eq 0 ] && [ "$g3_n" -eq 0 ] && [ "$g4_n" -eq 0 ] && return 1
  [ "$g1" = "2001" ] && [ "$g2_n" -eq 2 ] && [ "$g3_n" -eq 0 ] && return 1
  # 3fff::/20 documentation.
  [ "$g1" = "3fff" ] && [ "$g2_n" -lt 4096 ] && return 1
  # 64:ff9b:1::/48 local-use translation; 64:ff9b::/96 stays public.
  [ "$g1_n" -eq 100 ] && [ "$g2_n" -eq 65435 ] && [ "$g3_n" -eq 1 ] && return 1
  return 0
}

is_special_dns() {
  name=$(printf '%s' "$1" | tr 'A-Z' 'a-z')
  case "$name" in
    localhost|*.localhost|*.local|*.internal|*.test|*.example|*.invalid|*.alt|home.arpa|*.home.arpa)
      return 0
      ;;
  esac
  return 1
}

is_dns_name() {
  printf '%s' "$1" | grep -Eq '^[A-Za-z0-9.-]+$' || return 1
  case "$1" in
    .*|*.) return 1 ;;
  esac
  old_ifs=$IFS
  IFS=.
  # shellcheck disable=SC2086
  set -- $1
  IFS=$old_ifs
  [ "$#" -ge 2 ] || return 1
  for label in "$@"; do
    [ -n "$label" ] || return 1
    [ "${#label}" -le 63 ] || return 1
    case "$label" in
      -*|*-) return 1 ;;
    esac
    printf '%s' "$label" | grep -Eq '^[A-Za-z0-9-]+$' || return 1
  done
}

classify() {
  host=$1
  [ -n "$host" ] || fail "empty host"
  case "$host" in
    *[!A-Za-z0-9.:_-]*|*[\"\']*) fail "invalid host: $host" ;;
  esac
  if is_ipv4 "$host"; then
    if ipv4_is_public "$host"; then
      printf 'public-ip'
    else
      printf 'local'
    fi
    return 0
  fi
  if is_ipv6 "$host"; then
    if ipv6_is_public "$host"; then
      printf 'public-ip'
    else
      printf 'local'
    fi
    return 0
  fi
  if is_special_dns "$host"; then
    printf 'local'
    return 0
  fi
  if is_dns_name "$host"; then
    printf 'domain'
    return 0
  fi
  fail "cannot classify host: $host"
}

display_host() {
  if is_ipv6 "$1"; then
    printf '[%s]' "$1"
  else
    printf '%s' "$1"
  fi
}

render_caddyfile() {
  host=$1
  out=$2
  mode=$(classify "$host")
  case "$mode" in
    local) fail "$host is not public; stay on HTTP" ;;
  esac
  {
    if [ "$mode" = "public-ip" ]; then
      printf '{\n  default_sni "%s"\n}\n\n' "$host"
    fi
    printf '%s {\n' "$(display_host "$host")"
    if [ "$mode" = "public-ip" ]; then
      printf '  tls {\n    issuer acme {\n      profile shortlived\n      disable_tlsalpn_challenge\n    }\n  }\n'
    fi
    printf '  reverse_proxy frontend:80\n}\n'
  } >"$out"
}

compose_override() {
  dir=$1
  cat >"$dir/docker-compose.https.yml" <<'YAML'
# Added by install.sh WITH_AUTO_HTTPS=1. Terminates TLS in front of the
# frontend; remove this file and unset WITH_AUTO_HTTPS to roll back.
services:
  caddy:
    image: caddy:2
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile.auto-https:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    depends_on:
      - frontend
volumes:
  caddy_data:
YAML
}

command_name=${1:-}
case "$command_name" in
  classify)
    [ -n "${2:-}" ] || fail "usage: auto-https.sh classify <host>"
    classify "$2"
    ;;
  render-caddyfile)
    [ -n "${2:-}" ] && [ -n "${3:-}" ] || fail "usage: auto-https.sh render-caddyfile <host> <out>"
    render_caddyfile "$2" "$3"
    ;;
  compose-override)
    [ -n "${2:-}" ] || fail "usage: auto-https.sh compose-override <dir>"
    compose_override "$2"
    ;;
  *) fail "usage: auto-https.sh classify <host> | render-caddyfile <host> <out> | compose-override <dir>" ;;
esac
