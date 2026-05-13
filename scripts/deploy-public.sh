#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"
PUBLIC_WEB_ROOT="/var/www/roteiro-public"

cd "$FRONTEND_DIR"
npm ci
npx vite build --mode public --outDir dist-public

sudo mkdir -p "$PUBLIC_WEB_ROOT"
sudo rsync -a --delete "$FRONTEND_DIR/dist-public/" "$PUBLIC_WEB_ROOT/"

cd "$BACKEND_DIR"
docker compose -f docker-compose.public.yml --env-file .env.public up -d --build

echo "[public] done"
