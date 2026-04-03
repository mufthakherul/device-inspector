#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -x "$PROJECT_ROOT/venv/bin/python" ]]; then
  PYTHON="$PROJECT_ROOT/venv/bin/python"
else
  PYTHON="python3"
fi

exec "$PYTHON" "$PROJECT_ROOT/scripts/launch_inspecta.py" "$@"
