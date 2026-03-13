#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <dominio> [email]" >&2
  exit 1
fi

DOMAIN="$1"
EMAIL="${2:-${CERTBOT_EMAIL:-admin@roteiroonline.com}}"
WEBROOT="${CERTBOT_WEBROOT:-/var/www/roteiroonline}"
NGINX_RELOAD_CMD="${NGINX_RELOAD_CMD:-systemctl reload nginx}"

if ! command -v certbot >/dev/null 2>&1; then
  echo "certbot nao encontrado no PATH. Instale-o antes de usar este script." >&2
  exit 2
fi

echo "Emitindo certificado para ${DOMAIN} usando webroot ${WEBROOT}"

certbot certonly \
  --webroot -w "${WEBROOT}" \
  --non-interactive --agree-tos \
  -d "${DOMAIN}" \
  -m "${EMAIL}" \
  --deploy-hook "${NGINX_RELOAD_CMD}"

CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

if [[ ! -f "${CERT_DIR}/fullchain.pem" ]]; then
  echo "Certificado nao encontrado em ${CERT_DIR}" >&2
  exit 3
fi

echo "Certificado emitido em ${CERT_DIR}. Recarregando Nginx..."
$NGINX_RELOAD_CMD >/dev/null 2>&1 || true

echo "Concluido para ${DOMAIN}."
