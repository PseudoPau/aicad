#!/usr/bin/env bash
set -euo pipefail
PORT=8766
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="${2:?missing port}"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Project environment not found. Run ./setup_env.sh --profile Base first." >&2
  exit 1
fi
"$PY" -c 'import dotenv, jsonschema'
"$PY" -c 'import importlib.util; print("CAD: " + ("available - preview and STEP enabled" if importlib.util.find_spec("cadquery") else "not installed - manifest preview only")); print("Vision CLI: " + ("available" if importlib.util.find_spec("zhipuai") else "not installed (optional)"))'
echo "Open http://127.0.0.1:${PORT}"
exec "$PY" "$ROOT/ui_server.py" --port "$PORT"
