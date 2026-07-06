#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-43.163.87.9}"
SSH_USER="${SSH_USER:-ubuntu}"

cat <<'MSG'
This helper shows common commands for stopping an existing service.
It does not know the mini-program service name, so it lists likely processes first.
MSG

ssh "$SSH_USER@$HOST" '
  set -e
  echo "Listening ports:"
  sudo ss -lntp || true
  echo
  echo "Node/Python/PM2 processes:"
  ps -ef | grep -E "node|python|pm2|nginx" | grep -v grep || true
'
