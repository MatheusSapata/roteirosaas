#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"
PUBLIC_WEB_ROOT="/var/www/roteiro-public"

cd "$FRONTEND_DIR"
npm ci
VITE_API_URL="/api/v1" VITE_PLATFORM_HOSTS="roteiroonline.com,www.roteiroonline.com,localhost,127.0.0.1" npx vite build --mode public --outDir dist-public

sudo mkdir -p "$PUBLIC_WEB_ROOT"
sudo rsync -a --delete "$FRONTEND_DIR/dist-public/" "$PUBLIC_WEB_ROOT/"

cd "$BACKEND_DIR"
docker compose -f docker-compose.public.yml --env-file .env.public up -d --build

echo "[public] health check"
curl -fsS http://127.0.0.1:8002/health >/dev/null

echo "[public] done"