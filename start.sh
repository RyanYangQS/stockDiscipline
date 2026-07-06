#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8080}"
HOST="${HOST:-127.0.0.1}"
PID_FILE="$ROOT_DIR/stock-discipline.pid"
LOG_FILE="$ROOT_DIR/stock-discipline.log"
ENV_FILE="$ROOT_DIR/.env.local"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Stock Discipline is already running: pid $(cat "$PID_FILE")"
  exit 0
fi

cd "$ROOT_DIR"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi
export ROOT_DIR HOST PORT LOG_FILE PID_FILE
python3 - <<'PY'
import os
import subprocess
from pathlib import Path

root = Path(os.environ["ROOT_DIR"])
log_path = Path(os.environ["LOG_FILE"])
pid_path = Path(os.environ["PID_FILE"])
log = log_path.open("ab", buffering=0)
process = subprocess.Popen(
    ["python3", "-u", "backend/run.py", "--host", os.environ["HOST"], "--port", os.environ["PORT"]],
    cwd=root,
    stdin=subprocess.DEVNULL,
    stdout=log,
    stderr=subprocess.STDOUT,
    start_new_session=True,
)
pid_path.write_text(str(process.pid), encoding="utf-8")
PY

sleep 1
if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Stock Discipline failed to start. Log:"
  tail -80 "$LOG_FILE" || true
  rm -f "$PID_FILE"
  exit 1
fi

if command -v curl >/dev/null 2>&1; then
  if ! curl -fsS --max-time 3 "http://127.0.0.1:$PORT/api/health" >/dev/null; then
    echo "Stock Discipline process started but health check failed. Log:"
    tail -80 "$LOG_FILE" || true
    exit 1
  fi
fi

echo "Stock Discipline started at http://$HOST:$PORT, pid $(cat "$PID_FILE")"
