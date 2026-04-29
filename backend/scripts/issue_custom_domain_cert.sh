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
WWW_DOMAIN="${WWW_DOMAIN_OVERRIDE:-}"
INCLUDE_WWW="${INCLUDE_WWW:-false}"
CERT_NAME="${CERT_NAME_OVERRIDE:-${DOMAIN}}"
NGINX_DOMAIN_SCRIPT="${CUSTOM_DOMAIN_NGINX_SCRIPT_PATH:-}"

if ! command -v certbot >/dev/null 2>&1; then
  echo "certbot nao encontrado no PATH. Instale-o antes de usar este script." >&2
  exit 2
fi

echo "Emitindo certificado para ${DOMAIN} usando webroot ${WEBROOT}"

CERTBOT_ARGS=(
  certonly
  --webroot -w "${WEBROOT}"
  --non-interactive --agree-tos
  -d "${DOMAIN}"
  --cert-name "${CERT_NAME}"
  -m "${EMAIL}"
)

if [[ -n "${WWW_DOMAIN}" ]]; then
  CERTBOT_ARGS+=(-d "${WWW_DOMAIN}")
elif [[ "${INCLUDE_WWW}" == "true" ]]; then
  CERTBOT_ARGS+=(-d "www.${DOMAIN}")
  WWW_DOMAIN="www.${DOMAIN}"
fi

if [[ -z "${NGINX_DOMAIN_SCRIPT}" ]]; then
  CERTBOT_ARGS+=(--deploy-hook "${NGINX_RELOAD_CMD}")
fi

certbot "${CERTBOT_ARGS[@]}"

CERT_DIR="/etc/letsencrypt/live/${CERT_NAME}"

if [[ ! -f "${CERT_DIR}/fullchain.pem" ]]; then
  echo "Certificado nao encontrado em ${CERT_DIR}" >&2
  exit 3
fi

echo "Certificado emitido em ${CERT_DIR}."

if [[ -n "${NGINX_DOMAIN_SCRIPT}" ]]; then
  if [[ ! -x "${NGINX_DOMAIN_SCRIPT}" ]]; then
    echo "Script de Nginx custom domain nao executavel: ${NGINX_DOMAIN_SCRIPT}" >&2
    exit 4
  fi
  if [[ -n "${WWW_DOMAIN}" ]]; then
    echo "Aplicando configuracao Nginx para ${DOMAIN} e ${WWW_DOMAIN}..."
    "${NGINX_DOMAIN_SCRIPT}" enable \
      --domain "${DOMAIN}" \
      --www-domain "${WWW_DOMAIN}" \
      --cert-name "${CERT_NAME}"
  else
    echo "Aplicando configuracao Nginx para ${DOMAIN}..."
    "${NGINX_DOMAIN_SCRIPT}" enable \
      --domain "${DOMAIN}" \
      --cert-name "${CERT_NAME}"
  fi
else
  echo "CUSTOM_DOMAIN_NGINX_SCRIPT_PATH nao definido. Pulando criacao automatica de vhost."
  echo "Recarregando Nginx..."
  $NGINX_RELOAD_CMD >/dev/null 2>&1 || true
fi

echo "Concluido para ${DOMAIN}."
