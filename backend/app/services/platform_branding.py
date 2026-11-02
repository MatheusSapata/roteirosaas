"""Marca, SEO e textos dos e-mails do sistema, editáveis em Admin master.

Campo vazio = vale o padrão do código. A leitura fica guardada por alguns segundos (vale para todos os
e-mails e para o HTML das telas) e é zerada quando alguém salva na tela.
"""
from __future__ import annotations

import html
import logging
import re
import threading
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.platform_settings import PlatformSettings

logger = logging.getLogger(__name__)

CACHE_SECONDS = 30
BRAND_FIELDS = (
    "logo_url",
    "logo_dark_url",
    "favicon_url",
    "email_logo_url",
    "site_title",
    "site_description",
    "share_image_url",
    "theme_color",
)
IMAGE_FIELDS = ("logo_url", "logo_dark_url", "favicon_url", "email_logo_url", "share_image_url")
DEFAULT_SITE_TITLE = "Roteiro Online"
DEFAULT_SITE_DESCRIPTION = "Crie e compartilhe roteiros profissionais com o Roteiro Online."
DEFAULT_THEME_COLOR = "#12B981"

_lock = threading.Lock()
_cache: dict[str, Any] = {"at": 0.0, "data": None}


# ---------------------------------------------------------------- leitura


def get_row(db: Session) -> PlatformSettings:
    row = db.get(PlatformSettings, 1)
    if row is None:
        row = PlatformSettings(id=1)
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            row = db.get(PlatformSettings, 1)
        db.refresh(row)
    return row


def _snapshot(row: PlatformSettings | None) -> dict[str, Any]:
    data: dict[str, Any] = {name: None for name in BRAND_FIELDS}
    data["email_templates"] = {}
    if row is not None:
        for name in BRAND_FIELDS:
            value = getattr(row, name)
            data[name] = value.strip() if isinstance(value, str) and value.strip() else None
        data["email_templates"] = row.email_templates_json if isinstance(row.email_templates_json, dict) else {}
    return data


def current() -> dict[str, Any]:
    """Configuração atual, guardada por alguns segundos. Sem banco, valem os padrões."""
    now = time.monotonic()
    with _lock:
        if _cache["data"] is not None and now - _cache["at"] < CACHE_SECONDS:
            return _cache["data"]
    try:
        from app.db import session as db_session

        db = db_session.SessionLocal()
        try:
            data = _snapshot(db.get(PlatformSettings, 1))
        finally:
            db.close()
    except Exception:  # pragma: no cover - tabela ainda não criada, banco fora
        logger.debug("Configurações da plataforma indisponíveis; usando os padrões.", exc_info=True)
        data = _snapshot(None)
    with _lock:
        _cache["data"], _cache["at"] = data, now
    return data


def clear_cache() -> None:
    with _lock:
        _cache["data"], _cache["at"] = None, 0.0


def absolute_url(value: str | None) -> str | None:
    """Endereço completo (e-mails e buscadores não entendem /uploads/...)."""
    if not value:
        return None
    if value.startswith(("http://", "https://")):
        return value
    return f"{get_settings().resolved_webapp_base_url}/{value.lstrip('/')}"


def public_branding() -> dict[str, Any]:
    data = current()
    return {
        "logo_url": data["logo_url"],
        "logo_dark_url": data["logo_dark_url"],
        "favicon_url": data["favicon_url"],
        "site_title": data["site_title"] or DEFAULT_SITE_TITLE,
        "site_description": data["site_description"] or DEFAULT_SITE_DESCRIPTION,
        "share_image_url": data["share_image_url"],
        "theme_color": data["theme_color"] or DEFAULT_THEME_COLOR,
    }


# ---------------------------------------------------------------- HTML das telas (SEO)


def head_meta_block() -> str:
    """Título, descrição, cor, favicon e imagem de compartilhamento das telas da plataforma."""
    brand = public_branding()
    esc = lambda value: html.escape(str(value), quote=True)  # noqa: E731
    lines = [
        "<!--default-meta-->",
        f"<title>{esc(brand['site_title'])}</title>",
        f'<meta name="description" content="{esc(brand["site_description"])}" />',
        f'<meta name="theme-color" content="{esc(brand["theme_color"])}" />',
        f'<meta property="og:title" content="{esc(brand["site_title"])}" />',
        f'<meta property="og:description" content="{esc(brand["site_description"])}" />',
        '<meta property="og:type" content="website" />',
    ]
    share = absolute_url(brand["share_image_url"])
    if share:
        lines.append(f'<meta property="og:image" content="{esc(share)}" />')
        lines.append('<meta name="twitter:card" content="summary_large_image" />')
    favicon = brand["favicon_url"]
    if favicon:
        lines.append(f'<link rel="icon" href="{esc(favicon)}" />')
        lines.append(f'<link rel="apple-touch-icon" href="{esc(favicon)}" />')
    lines.append("<!--/default-meta-->")
    return "\n    ".join(lines)


def apply_head_meta(index_html: str) -> str:
    """Troca o bloco padrão do index.html pelo configurado. Sem configuração, devolve igual."""
    data = current()
    if not any(data[name] for name in ("site_title", "site_description", "share_image_url", "favicon_url", "theme_color")):
        return index_html
    start = index_html.find("<!--default-meta-->")
    end = index_html.find("<!--/default-meta-->", start + 1) if start >= 0 else -1
    if start < 0 or end < 0:
        return index_html
    before = index_html[:start]
    after = index_html[end + len("<!--/default-meta-->"):]
    if data["favicon_url"]:
        # O favicon do build fica logo depois do bloco: sai para valer o configurado.
        after = re.sub(r"\s*<link[^>]+rel=\"icon\"[^>]*>", "", after, count=1)
    return before + head_meta_block() + after


# ---------------------------------------------------------------- e-mails do sistema


@dataclass(frozen=True)
class SystemEmail:
    key: str
    label: str
    description: str
    variables: tuple[tuple[str, str], ...]
    defaults: dict[str, str]
    sample: dict[str, str]


EMAIL_FIELDS = ("subject", "eyebrow", "title", "body", "button_label", "note")
_WELCOME_VARS = (("nome", "Nome do cliente"), ("plano", "Plano"), ("ciclo", "Ciclo (mensal, anual…)"), ("link", "Link para criar a senha"))
_WELCOME_SAMPLE = {"nome": "Maria Souza", "plano": "plano Essencial", "ciclo": "ciclo anual", "link": "https://roteiroonline.com/create-password"}

SYSTEM_EMAILS: tuple[SystemEmail, ...] = (
    SystemEmail(
        key="boas_vindas_checkout",
        label="Boas-vindas (compra pelo checkout)",
        description="Cliente novo que acabou de pagar no checkout: confirma a compra e leva a criar a senha.",
        variables=_WELCOME_VARS,
        defaults={
            "subject": "Pagamento confirmado: bem-vindo ao Roteiro Online",
            "eyebrow": "Pagamento confirmado",
            "title": "Bem-vindo ao Roteiro Online, {{nome}}!",
            "body": (
                "Recebemos o seu pagamento e a sua assinatura já está ativa. "
                "Falta só um passo: criar a sua senha para entrar no painel e montar o seu primeiro roteiro."
            ),
            "button_label": "Criar minha senha",
            "note": "Precisa de ajuda? É só responder este e-mail que a nossa equipe te atende.",
        },
        sample=_WELCOME_SAMPLE,
    ),
    SystemEmail(
        key="boas_vindas_cakto",
        label="Boas-vindas (compra pela Cakto)",
        description="Cliente que comprou pela Cakto: leva a criar a senha.",
        variables=_WELCOME_VARS,
        defaults={
            "subject": "Bem-vindo ao Roteiro Online",
            "eyebrow": "Compra confirmada",
            "title": "Bem-vindo ao Roteiro Online, {{nome}}!",
            "body": "A sua assinatura já está ativa. Falta só um passo: criar a sua senha para entrar no painel.",
            "button_label": "Criar minha senha",
            "note": "Precisa de ajuda? É só responder este e-mail que a nossa equipe te atende.",
        },
        sample=_WELCOME_SAMPLE,
    ),
    SystemEmail(
        key="convite_equipe",
        label="Convite de equipe",
        description="Pessoa convidada para a equipe de uma agência.",
        variables=(
            ("nome", "Nome de quem foi convidado"),
            ("quem_convidou", "Quem convidou"),
            ("agencia", "Nome da agência"),
            ("dias", "Dias de validade do convite"),
            ("link", "Link do convite"),
        ),
        defaults={
            "subject": "Convite para acessar a equipe da {{agencia}}",
            "eyebrow": "Convite de equipe",
            "title": "Olá, {{nome}}. Você foi convidado!",
            "body": (
                "*{{quem_convidou}}* convidou você para fazer parte da equipe da *{{agencia}}* no Roteiro Online. "
                "Aceite o convite para criar a sua senha e acessar a conta."
            ),
            "button_label": "Aceitar convite",
            "note": "*O convite vale por {{dias}} dias.* Se você não esperava este convite, pode ignorar este e-mail.",
        },
        sample={
            "nome": "João Lima",
            "quem_convidou": "Maria Souza",
            "agencia": "Viagens Exemplo",
            "dias": "7",
            "link": "https://roteiroonline.com/accept-invite?token=exemplo",
        },
    ),
    SystemEmail(
        key="redefinir_senha",
        label="Redefinir senha",
        description="Link de “Esqueci minha senha”.",
        variables=(("nome", "Nome do cliente"), ("validade", "Validade do link (ex.: 1 hora)"), ("link", "Link para redefinir")),
        defaults={
            "subject": "Redefinir a sua senha do Roteiro Online",
            "eyebrow": "Recuperar acesso",
            "title": "Olá, {{nome}}. Vamos criar uma nova senha?",
            "body": "Recebemos um pedido para redefinir a senha da sua conta. Clique no botão abaixo para escolher uma nova.",
            "button_label": "Redefinir minha senha",
            "note": (
                "*O link vale por {{validade}}.* Se você não pediu a redefinição, pode ignorar este e-mail: "
                "a sua senha continua a mesma."
            ),
        },
        sample={"nome": "Maria Souza", "validade": "1 hora", "link": "https://roteiroonline.com/reset-password?token=exemplo"},
    ),
)
EMAIL_BY_KEY = {item.key: item for item in SYSTEM_EMAILS}

_VAR_RE = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def email_texts(key: str) -> dict[str, str]:
    """Textos do e-mail: os salvos na tela, ou o padrão campo a campo."""
    spec = EMAIL_BY_KEY[key]
    saved = current()["email_templates"].get(key)
    saved = saved if isinstance(saved, dict) else {}
    return {name: (str(saved.get(name) or "").strip() or spec.defaults[name]) for name in EMAIL_FIELDS}


def clean_email_templates(raw: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    """Guarda só o que difere do padrão."""
    result: dict[str, dict[str, str]] = {}
    for key, values in (raw or {}).items():
        spec = EMAIL_BY_KEY.get(key)
        if spec is None or not isinstance(values, dict):
            continue
        kept = {}
        for name in EMAIL_FIELDS:
            text = str(values.get(name) or "").strip()
            if text and text != spec.defaults[name]:
                kept[name] = text[:4000]
        if kept:
            result[key] = kept
    return result


def render_plain(template: str, values: dict[str, Any]) -> str:
    return _VAR_RE.sub(lambda m: str(values.get(m.group(1), m.group(0))), template or "")


def render_html(template: str, values: dict[str, Any]) -> str:
    """Texto da tela → HTML seguro: o texto e as variáveis são escapados; *negrito* vira <b>."""
    escaped = html.escape(template or "")
    escaped = _VAR_RE.sub(lambda m: html.escape(str(values.get(m.group(1), m.group(0)))), escaped)
    return re.sub(r"\*([^*\n]+)\*", r"<b>\1</b>", escaped)


def _strip_bold(text: str) -> str:
    return re.sub(r"\*([^*\n]+)\*", r"\1", text)


def build_system_email(
    key: str,
    values: dict[str, Any],
    *,
    button_url: str,
    highlight: str | None = None,
    texts: dict[str, str] | None = None,
) -> tuple[str, str, str]:
    """(assunto, html, texto) do e-mail do sistema com os textos atuais."""
    from app.services.email import _email_layout, _paragraph

    texts = texts or email_texts(key)
    subject = _strip_bold(render_plain(texts["subject"], values)).strip()
    paragraphs = [block.strip() for block in re.split(r"\n\s*\n", texts["body"]) if block.strip()]
    body_html = "".join(_paragraph(render_html(block, values).replace("\n", "<br>")) for block in paragraphs)
    html_body = _email_layout(
        eyebrow=render_html(texts["eyebrow"], values),
        title=render_html(texts["title"], values),
        body_html=body_html,
        highlight=highlight,
        button_url=html.escape(button_url, quote=True),
        button_label=render_html(texts["button_label"], values),
        note_html=render_html(texts["note"], values).replace("\n", "<br>"),
    )
    text_body = "\n\n".join(
        part
        for part in (
            _strip_bold(render_plain(texts["title"], values)),
            _strip_bold(render_plain(texts["body"], values)),
            f"{_strip_bold(render_plain(texts['button_label'], values))}: {button_url}",
            _strip_bold(render_plain(texts["note"], values)),
            "Equipe Roteiro Online",
        )
        if part.strip()
    )
    return subject, html_body, text_body
