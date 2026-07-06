#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/stock-discipline.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No pid file found."
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "Stopped Stock Discipline pid $PID"
else
  echo "Process $PID is not running."
fi
rm -f "$PID_FILE"

