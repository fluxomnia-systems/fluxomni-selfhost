#!/usr/bin/env bash
# Type check the Python helpers and their tests with ty, using the test requirements.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
exec uv run --no-project --with-requirements scripts/requirements-test.txt --with ty sh -c '
  site="$(python -c "import os, pytest; print(os.path.dirname(os.path.dirname(pytest.__file__)))")"
  exec ty check --extra-search-path "$site" "$@"
' sh scripts/capacity-upgrade.py tests/test_capacity_upgrade.py scripts/node-credentials.py tests/test_node_credentials.py scripts/fluxomnictl.py tests/test_fluxomnictl.py
