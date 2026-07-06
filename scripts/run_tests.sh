#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m unittest discover -s tests -p "test_*.py" -v

if command -v npm >/dev/null 2>&1; then
  cd "$ROOT_DIR/frontend"
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  npm run build
fi
