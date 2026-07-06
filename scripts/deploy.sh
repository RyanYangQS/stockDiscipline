#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-43.163.87.9}"
SSH_USER="${SSH_USER:-ubuntu}"
REMOTE_DIR="${REMOTE_DIR:-/home/ubuntu/stockDiscipline}"
PORT="${PORT:-8080}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Deploying to $SSH_USER@$HOST:$REMOTE_DIR"
echo "This script does not store passwords. Use your SSH password or configure an SSH key."

ssh "$SSH_USER@$HOST" "mkdir -p '$REMOTE_DIR'"
rsync -az --delete \
  --exclude '.git' \
  --exclude '.DS_Store' \
  --exclude 'frontend/node_modules' \
  --exclude 'stock-discipline.pid' \
  --exclude 'stock-discipline.log' \
  "$ROOT_DIR/" "$SSH_USER@$HOST:$REMOTE_DIR/"

ssh "$SSH_USER@$HOST" "cd '$REMOTE_DIR' && chmod +x start.sh stop.sh && ./stop.sh || true && PORT='$PORT' HOST='0.0.0.0' ./start.sh"

echo "Deployed. Open: http://$HOST:$PORT"
