#!/usr/bin/env bash
set -euo pipefail

PROFILE="CAD"
WITH_VISION=0
PYTHON_BIN="python3"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="${2:?missing profile}"; shift 2 ;;
    --with-vision) WITH_VISION=1; shift ;;
    --python) PYTHON_BIN="${2:?missing python path}"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ "$PROFILE" != "Base" && "$PROFILE" != "CAD" ]]; then
  echo "Profile must be Base or CAD" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"
REQ="$ROOT/requirements.txt"
if [[ "$PROFILE" == "CAD" ]]; then REQ="$ROOT/requirements-cad.txt"; fi

if [[ ! -x "$PY" ]]; then
  echo "Creating project environment: $VENV"
  "$PYTHON_BIN" -m venv "$VENV"
fi

"$PY" -m pip install --disable-pip-version-check --timeout 300 --retries 5 -r "$REQ"
if [[ "$WITH_VISION" == "1" ]]; then
  "$PY" -m pip install --disable-pip-version-check --timeout 300 --retries 5 -r "$ROOT/requirements-vision.txt"
fi
"$PY" -m pip check
echo "Setup complete. Start with: ./start_local.sh"
