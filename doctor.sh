#!/usr/bin/env bash
# FluxOmni Self-Host Doctor — installation health check
set -euo pipefail

PASS="✅"
FAIL="❌"
WARN="⚠️ "
INFO="ℹ️ "

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

required_fail=0

check() {
  local status="$1" label="$2" hint="${3:-}"
  if [ "$status" = "pass" ]; then
    printf "  %s  %-45s %s\n" "$PASS" "$label" ""
  elif [ "$status" = "warn" ]; then
    printf "  %s  %-45s %b%s%b\n" "$WARN" "$label" "$YELLOW" "$hint" "$NC"
  elif [ "$status" = "info" ]; then
    printf "  %s  %-45s %b%s%b\n" "$INFO" "$label" "$BLUE" "$hint" "$NC"
  else
    printf "  %s  %-45s %b%s%b\n" "$FAIL" "$label" "$RED" "$hint" "$NC"
    required_fail=1
  fi
}

echo "═══════════════════════════════════════════════════════════════"
echo " FluxOmni Self-Host Doctor"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# --- PREREQUISITES ---
echo -e "${BLUE}--- Prerequisites ---${NC}"

# Docker check
if command -v docker >/dev/null 2>&1; then
  docker_ver=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "running but inaccessible")
  check pass "Docker installed" "$docker_ver"
else
  check fail "Docker not installed" "Install from https://docs.docker.com/engine/install/"
fi

# Docker Compose check
if docker compose version >/dev/null 2>&1; then
  compose_ver=$(docker compose version --short)
  check pass "Docker Compose installed" "$compose_ver"
else
  check fail "Docker Compose not installed" "Required for self-hosting"
fi

# --- CONFIGURATION ---
echo -e "\n${BLUE}--- Configuration ---${NC}"

# .env check
if [ -f .env ]; then
  check pass ".env file exists"
  
  # Basic parsing for checks
  read_env() { grep "^$1=" .env | cut -d= -f2- | tr -d '"' | tr -d "'" || true; }
  
  AUTH_TOKEN=$(read_env FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN)
  if [ -n "$AUTH_TOKEN" ]; then
    check pass "Internal Auth Token configured"
  else
    check fail "Internal Auth Token MISSING" "Set FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN in .env"
  fi
  
  PUBLIC_HOST=$(read_env FLUXOMNI_PUBLIC_HOST)
  if [ -n "$PUBLIC_HOST" ]; then
    check info "Public Host" "$PUBLIC_HOST"
    
    # Network reachability hint
    if [[ "$OSTYPE" == "darwin"* ]]; then
      host_ips=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
    elif command -v hostname >/dev/null 2>&1 && hostname -I >/dev/null 2>&1; then
      host_ips=$(hostname -I 2>/dev/null || echo "")
    else
      host_ips=$(ip addr show 2>/dev/null | grep -Po 'inet \K[\d.]+' | grep -v '127.0.0.1' || echo "")
    fi
    
    if [ -n "$host_ips" ]; then
      found=0
      for ip in $host_ips; do
        if [ "$ip" = "$PUBLIC_HOST" ]; then
          found=1
          break
        fi
      done
      
      if [ "$found" -eq 0 ] && [ "$PUBLIC_HOST" != "127.0.0.1" ] && [ "$PUBLIC_HOST" != "localhost" ]; then
        check warn "PUBLIC_HOST ($PUBLIC_HOST) NOT found in host IPs ($host_ips)" "Verify reachability from your client network"
      elif [ "$PUBLIC_HOST" = "127.0.0.1" ] || [ "$PUBLIC_HOST" = "localhost" ]; then
        echo -e "\n${YELLOW}💡 Hint: To access the Web UI from another machine, set FLUXOMNI_PUBLIC_HOST to one of these IPs in .env:${NC}"
        for ip in $host_ips; do
          echo -e "   - $ip"
        done
        echo -e "   Run: ${BLUE}sed -i 's/FLUXOMNI_PUBLIC_HOST=.*/FLUXOMNI_PUBLIC_HOST=<chosen-ip>/' .env && docker compose up -d${NC}"
      fi
    fi
  else
    check warn "FLUXOMNI_PUBLIC_HOST unset" "Defaults to 127.0.0.1 (local access only)"
    echo -e "\n${YELLOW}💡 Hint: To access the Web UI from another machine, set FLUXOMNI_PUBLIC_HOST to your server's IP in .env:${NC}"
    for ip in $host_ips; do
      echo -e "   - $ip"
    done
  fi
else
  check fail ".env file missing" "Run install.sh or create .env from .env.example"
fi

# docker-compose.yml check
if [ -f docker-compose.yml ]; then
  check pass "docker-compose.yml exists"
else
  check fail "docker-compose.yml missing" "This script should be run from the fluxomni install directory"
fi

# --- PORT AVAILABILITY ---
echo -e "\n${BLUE}--- Port Availability ---${NC}"

check_port() {
  local port=$1 label=$2
  if lsof -iTCP:"$port" -sTCP:LISTEN -P -n >/dev/null 2>&1; then
    # Check if it's docker holding the port
    if lsof -iTCP:"$port" -sTCP:LISTEN -P -n | grep -q "docker"; then
      check pass "Port $port ($label) is used by Docker"
    else
      check warn "Port $port ($label) in use by another process" "$(lsof -iTCP:"$port" -sTCP:LISTEN -P -n | tail -1 | awk '{print $1}')"
    fi
  else
    check pass "Port $port ($label) available"
  fi
}

CP_HTTP_PORT=${FLUXOMNI_CONTROL_PLANE_HTTP_PORT:-80}
MN_RTMP_PORT=${FLUXOMNI_MEDIA_NODE_RTMP_PORT:-1935}
MN_HLS_PORT=${FLUXOMNI_MEDIA_NODE_HLS_PORT:-8000}
CP_RPC_PORT=${FLUXOMNI_CONTROL_PLANE_RPC_PORT:-50052}

check_port "$CP_HTTP_PORT" "Web UI"
check_port "$MN_RTMP_PORT" "RTMP Ingest"
check_port "$MN_HLS_PORT" "HLS Playback"
check_port "$CP_RPC_PORT" "Internal RPC"

# --- CONTAINER STATUS ---
echo -e "\n${BLUE}--- Container Status ---${NC}"

if command -v docker >/dev/null 2>&1 && [ -f docker-compose.yml ]; then
  services=$(docker compose ps --format json 2>/dev/null || echo "")
  if [ -n "$services" ]; then
    # Try to find control-plane and media-node
    cp_status=$(docker compose ps control-plane --format "{{.Status}}" 2>/dev/null || echo "missing")
    mn_status=$(docker compose ps media-node --format "{{.Status}}" 2>/dev/null || echo "missing")
    
    if [[ "$cp_status" == "running"* ]] || [[ "$cp_status" == "Up"* ]]; then
      check pass "control-plane container" "$cp_status"
    else
      check fail "control-plane container NOT running" "$cp_status"
    fi
    
    if [[ "$mn_status" == "running"* ]] || [[ "$mn_status" == "Up"* ]]; then
      check pass "media-node container" "$mn_status"
    else
      check fail "media-node container NOT running" "$mn_status"
    fi
  else
    check info "No containers currently managed by docker-compose" "Run: docker compose up -d"
  fi
fi

# --- DISK & DATA ---
echo -e "\n${BLUE}--- Disk & Data ---${NC}"

# Disk space
df_output=$(df -h . | tail -1 | awk '{print $4}')
check info "Available disk space" "$df_output"

# Data directory
if [ -d data ]; then
  check pass "data/ directory exists"
  if [ -f data/state.db ]; then
    check pass "SQLite database (state.db) found"
  else
    check warn "SQLite database NOT found" "Will be created on first start"
  fi
else
  check warn "data/ directory missing" "Will be created on first start"
fi

echo ""
if [ "$required_fail" -eq 0 ]; then
  echo -e "${GREEN}🎉 FluxOmni self-host environment looks good!${NC}"
else
  echo -e "${RED}❌ Some issues were detected in your self-host setup.${NC}"
  exit 1
fi
