#!/usr/bin/env bash
# Fluxomni self-host doctor. The checks live in fluxomnictl; this wrapper keeps ./doctor.sh working.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Root only trusts the system copy, never a user-writable one.
if [ "$(id -u)" -eq 0 ]; then
  candidates=(/usr/local/bin/fluxomnictl)
else
  candidates=("${FLUXOMNICTL:-}" /usr/local/bin/fluxomnictl "${HOME:-/nonexistent}/.local/bin/fluxomnictl" "$(command -v fluxomnictl 2>/dev/null || true)")
fi
for tool in "${candidates[@]}"; do
  if [ -n "$tool" ] && [ -x "$tool" ]; then
    exec "$tool" --dir "$here" doctor
  fi
done
echo "Error: fluxomnictl is not installed. Run: bash install.sh tools" >&2
exit 1
