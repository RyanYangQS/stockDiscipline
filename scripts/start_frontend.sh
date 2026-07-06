#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
PID_FILE="$ROOT_DIR/frontend-vite.pid"
LOG_FILE="$ROOT_DIR/frontend-vite.log"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Frontend dev server is already running: pid $(cat "$PID_FILE")"
  exit 0
fi

cd "$FRONTEND_DIR"
if [[ ! -d node_modules ]]; then
  npm install
fi

export FRONTEND_DIR LOG_FILE PID_FILE
python3 - <<'PY'
import os
import subprocess
from pathlib import Path

frontend = Path(os.environ["FRONTEND_DIR"])
log = Path(os.environ["LOG_FILE"]).open("ab", buffering=0)
process = subprocess.Popen(
    ["npm", "run", "dev"],
    cwd=frontend,
    stdin=subprocess.DEVNULL,
    stdout=log,
    stderr=subprocess.STDOUT,
    start_new_session=True,
)
Path(os.environ["PID_FILE"]).write_text(str(process.pid), encoding="utf-8")
PY

sleep 2
if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Frontend dev server failed to start. Log:"
  tail -80 "$LOG_FILE" || true
  rm -f "$PID_FILE"
  exit 1
fi

echo "Frontend dev server started at http://127.0.0.1:5173, pid $(cat "$PID_FILE")"

