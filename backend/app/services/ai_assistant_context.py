"""Dados da conta que o assistente de IA recebe a cada conversa: agência, contatos, redes
sociais e as páginas já criadas, para não perguntar o que já está cadastrado e poder ligar
cards e links a páginas que existem."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.page import Page

MAX_PAGES = 40
NETWORK_NAMES = {"instagram": "Instagram", "facebook": "Facebook", "youtube": "YouTube", "tiktok": "TikTok", "linkedin": "LinkedIn"}
STATUS_NAMES = {"published": "publicada", "draft": "rascunho"}


def _plain(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("pt") or value.get("es") or next(iter(value.values()), "")
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _date_br(value: Any) -> str:
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return ""


def _price_br(value: float) -> str:
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").removesuffix(",00")


def _page_summary(page: Page) -> str:
    config = page.config_json if isinstance(page.config_json, dict) else {}
    sections = [section for section in config.get("sections") or [] if isinstance(section, dict)]
    hero = next((section for section in sections if section.get("type") == "hero"), {})
    details: list[str] = [STATUS_NAMES.get(page.status, page.status)]
    departure = _date_br(hero.get("departureDate"))
    if departure:
        back = _date_br(hero.get("returnDate"))
        details.append(f"saída {departure}" + (f", volta {back}" if back else ""))
    prices = [
        float(item.get("price") or 0)
        for section in sections
        if section.get("type") == "prices" and section.get("enabled", True)
        for item in section.get("items") or []
        if isinstance(item, dict) and float(item.get("price") or 0) > 0
    ]
    if prices:
        details.append(f"a partir de {_price_br(min(prices))}")
    subtitle = _short(_plain(hero.get("subtitle")), 90)
    line = f'- {page.slug}: "{_plain(page.title)}" ({", ".join(details)})'
    return f"{line} · {subtitle}" if subtitle else line


def build_agency_context(db: Session, page: Page) -> str:
    """Bloco de texto com o que já está cadastrado, para ir junto das instruções da IA."""
    from app.api.v1.endpoints.public_pages import build_agency_profile  # evita import circular

    agency = page.agency
    if agency is None:
        return ""
    profile = build_agency_profile(agency)
    lines = [
        "DADOS JÁ CADASTRADOS NA PLATAFORMA",
        "Use estes dados sem perguntar de novo. Logo, redes sociais, contatos e rodapé aparecem sozinhos nas seções certas.",
        f"Agência: {agency.name}",
    ]
    if profile.get("description"):
        lines.append(f"Descrição da agência: {_short(_plain(profile['description']), 400)}")
    address = profile.get("address") or {}
    city = ", ".join(part for part in (address.get("city"), address.get("state")) if part)
    if city:
        lines.append(f"Cidade: {city}")
    contacts = [f"WhatsApp {profile['phone']}" if profile.get("phone") else "", f"e-mail {profile['email']}" if profile.get("email") else ""]
    if any(contacts):
        lines.append("Contatos: " + ", ".join(part for part in contacts if part))
    networks = [NETWORK_NAMES.get(link["network"], link["network"]) for link in profile.get("social_links") or [] if link.get("url")]
    lines.append("Redes sociais cadastradas: " + (", ".join(networks) if networks else "nenhuma"))
    lines.append(f"Logo: {'cadastrado' if agency.logo_url else 'não cadastrado'}")
    lines.append(f'Página que está sendo editada: "{_plain(page.title)}"')

    others = (
        db.query(Page)
        .filter(Page.agency_id == agency.id, Page.id != page.id, Page.status.in_(tuple(STATUS_NAMES)))
        .order_by(Page.updated_at.desc())
        .limit(MAX_PAGES)
        .all()
    )
    if others:
        lines.append(
            "Outras páginas da agência (quando o usuário falar de uma viagem que já tem página, ligue a ela com "
            '"Página: identificador" no card da VITRINE DE VIAGENS; o identificador é o que vem antes dos dois-pontos):'
        )
        lines.extend(_page_summary(other) for other in others)
    else:
        lines.append("Outras páginas da agência: nenhuma.")
    return "\n".join(lines)
