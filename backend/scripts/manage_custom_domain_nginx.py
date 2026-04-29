#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

LOGGER = logging.getLogger("custom-domain-nginx")
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)

SITES_AVAILABLE_BASE = Path("/etc/nginx/sites-available/custom-domains")
SITES_ENABLED_BASE = Path("/etc/nginx/sites-enabled")
ASSETS_ALIAS = "/opt/roteirosaas/frontend/dist/assets/"
UPSTREAM_NAME = "roteiro_backend"
NGINX_BIN = os.environ.get("NGINX_BIN", "nginx")
SYSTEMCTL_BIN = os.environ.get("SYSTEMCTL_BIN", "systemctl")


class NginxDomainError(RuntimeError):
    pass


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def ensure_valid_domain(value: str, field_name: str) -> str:
    candidate = value.strip().lower()
    if not DOMAIN_RE.fullmatch(candidate):
        raise NginxDomainError(
            f"{field_name} invalido: '{value}'. Use apenas dominios validos (ex.: bmsfly.com.br)."
        )
    return candidate


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=True)


def nginx_test() -> None:
    try:
        run_cmd([NGINX_BIN, "-t"])
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise NginxDomainError(f"nginx -t falhou: {stderr or exc}") from exc


def reload_nginx() -> None:
    try:
        run_cmd([SYSTEMCTL_BIN, "reload", "nginx"])
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise NginxDomainError(f"Falha ao recarregar Nginx: {stderr or exc}") from exc


def render_nginx_config(domain: str, cert_name: str, www_domain: str | None = None) -> str:
    server_names = domain if not www_domain else f"{domain} {www_domain}"
    return f"""server {{
    listen 80;
    listen [::]:80;
    server_name {server_names};

    location ^~ /.well-known/acme-challenge/ {{
        root /var/www/roteiroonline;
        try_files $uri =404;
    }}

    location / {{
        return 301 https://$host$request_uri;
    }}
}}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {server_names};

    ssl_certificate /etc/letsencrypt/live/{cert_name}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{cert_name}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

    location = /favicon.ico {{
        access_log off;
        log_not_found off;
        expires 30d;
    }}

    location ^~ /api/v1/public/pages/ {{
        proxy_pass http://{UPSTREAM_NAME}/api/v1/public/pages/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_redirect off;
    }}

    location ^~ /admin/ {{
        deny all;
        return 403;
    }}

    location ^~ /api/ {{
        deny all;
        return 403;
    }}

    location ^~ /assets/ {{
        alias {ASSETS_ALIAS};
        access_log off;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }}

    location / {{
        proxy_pass http://{UPSTREAM_NAME};
        proxy_redirect off;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""


def atomic_write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def ensure_cert_files(cert_name: str) -> None:
    cert_dir = Path("/etc/letsencrypt/live") / cert_name
    fullchain = cert_dir / "fullchain.pem"
    privkey = cert_dir / "privkey.pem"
    if not fullchain.exists() or not privkey.exists():
        raise NginxDomainError(
            f"Certificado nao encontrado para cert_name '{cert_name}' em {cert_dir}."
        )
    LOGGER.info("Certificado encontrado: %s", cert_dir)


def enable_domain(domain: str, cert_name: str, www_domain: str | None = None) -> None:
    ensure_cert_files(cert_name)

    available_path = SITES_AVAILABLE_BASE / f"{domain}.conf"
    enabled_path = SITES_ENABLED_BASE / f"{domain}.conf"
    temp_available_path = SITES_AVAILABLE_BASE / f".{domain}.conf.candidate"
    temp_enabled_path = SITES_ENABLED_BASE / f"__candidate_{domain}.conf"

    content = render_nginx_config(domain=domain, www_domain=www_domain, cert_name=cert_name)
    atomic_write_file(temp_available_path, content)

    previous_target: Path | None = None
    if enabled_path.is_symlink():
        previous_target = enabled_path.resolve(strict=False)

    if temp_enabled_path.exists() or temp_enabled_path.is_symlink():
        temp_enabled_path.unlink()
    temp_enabled_path.symlink_to(temp_available_path)
    try:
        nginx_test()
    finally:
        if temp_enabled_path.exists() or temp_enabled_path.is_symlink():
            temp_enabled_path.unlink()

    atomic_write_file(available_path, content)
    if temp_available_path.exists():
        temp_available_path.unlink()
    LOGGER.info("Arquivo Nginx criado/atualizado: %s", available_path)

    if enabled_path.exists() or enabled_path.is_symlink():
        enabled_path.unlink()
    enabled_path.symlink_to(available_path)
    LOGGER.info("Symlink criado/atualizado: %s -> %s", enabled_path, available_path)

    try:
        nginx_test()
        LOGGER.info("Teste Nginx OK apos ativacao.")
        reload_nginx()
        LOGGER.info("Reload Nginx OK.")
    except Exception as exc:
        LOGGER.error("Falha apos ativacao, iniciando rollback: %s", exc)
        if enabled_path.exists() or enabled_path.is_symlink():
            enabled_path.unlink()
        if previous_target:
            enabled_path.symlink_to(previous_target)
        nginx_test()
        LOGGER.info("Rollback concluido e estado anterior validado com nginx -t.")
        raise


def disable_domain(domain: str, keep_available: bool) -> None:
    available_path = SITES_AVAILABLE_BASE / f"{domain}.conf"
    enabled_path = SITES_ENABLED_BASE / f"{domain}.conf"

    previous_target: Path | None = enabled_path.resolve(strict=False) if enabled_path.is_symlink() else None
    had_enabled = enabled_path.exists() or enabled_path.is_symlink()

    if had_enabled:
        enabled_path.unlink()
        LOGGER.info("Symlink removido: %s", enabled_path)
    else:
        LOGGER.info("Symlink nao existia: %s", enabled_path)

    if not keep_available and available_path.exists():
        available_path.unlink()
        LOGGER.info("Arquivo removido de sites-available: %s", available_path)

    try:
        nginx_test()
        LOGGER.info("Teste Nginx OK apos desativacao.")
        reload_nginx()
        LOGGER.info("Reload Nginx OK.")
    except Exception as exc:
        LOGGER.error("Falha na desativacao, restaurando estado anterior: %s", exc)
        if had_enabled and previous_target and not enabled_path.exists():
            enabled_path.symlink_to(previous_target)
        nginx_test()
        LOGGER.info("Rollback concluido e estado anterior validado com nginx -t.")
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gerencia configuracoes Nginx para custom domains.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enable_parser = subparsers.add_parser("enable", help="Cria/atualiza configuracao do dominio.")
    enable_parser.add_argument("--domain", required=True, help="Dominio principal. Ex.: bmsfly.com.br")
    enable_parser.add_argument("--www-domain", required=False, help="Dominio adicional opcional. Ex.: www.bmsfly.com.br")
    enable_parser.add_argument("--cert-name", required=True, help="Nome do certificado no Let's Encrypt.")

    disable_parser = subparsers.add_parser("disable", help="Desativa configuracao do dominio.")
    disable_parser.add_argument("--domain", required=True, help="Dominio principal. Ex.: bmsfly.com.br")
    disable_parser.add_argument(
        "--remove-available",
        action="store_true",
        help="Tambem remove o arquivo em sites-available/custom-domains.",
    )

    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()
    try:
        if args.command == "enable":
            domain = ensure_valid_domain(args.domain, "domain")
            www_domain = ensure_valid_domain(args.www_domain, "www_domain") if args.www_domain else None
            cert_name = ensure_valid_domain(args.cert_name, "cert_name")
            enable_domain(domain=domain, www_domain=www_domain, cert_name=cert_name)
        elif args.command == "disable":
            domain = ensure_valid_domain(args.domain, "domain")
            disable_domain(domain=domain, keep_available=not args.remove_available)
        else:
            raise NginxDomainError("Comando invalido.")
    except NginxDomainError as exc:
        LOGGER.error("%s", exc)
        return 1
    except Exception as exc:
        LOGGER.exception("Erro inesperado: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
