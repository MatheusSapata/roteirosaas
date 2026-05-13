#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"
ADMIN_WEB_ROOT="/var/www/roteiro-admin"

cd "$FRONTEND_DIR"
npm ci
npx vite build --mode admin --outDir dist-admin

sudo mkdir -p "$ADMIN_WEB_ROOT"
sudo rsync -a --delete "$FRONTEND_DIR/dist-admin/" "$ADMIN_WEB_ROOT/"

cd "$BACKEND_DIR"
docker compose -f docker-compose.admin.yml --env-file .env.admin up -d --build

echo "[admin] done"
