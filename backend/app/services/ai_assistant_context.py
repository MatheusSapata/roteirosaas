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
# Nome de cada seção no editor (o mesmo que o usuário vê e que a IA usa na resposta).
SECTION_EDITOR_NAMES = {
    "header": "Menu do topo", "hero": "Banner Inicial", "banner_card": "Banner em Card", "video_vsl": "Vídeo de Vendas (VSL)",
    "story": "Texto e Imagens", "reasons": "Diferenciais", "biography": "Artigo", "itinerary": "Roteiro dia a dia",
    "gallery": "Galeria de fotos", "flight_details": "Voos", "links": "Links/Roteiros", "photo": "Foto em destaque",
    "featured_video": "Vídeo", "prices": "Preços e pacotes", "viajeon_checkout": "Compra Online (Viaje On)",
    "countdown": "Contagem regressiva", "cta": "Faixa de chamada", "testimonials": "Depoimentos",
    "faq": "Dúvidas frequentes", "internal_form": "Formulário de contato", "agency_footer": "Rodapé da agência",
}
SECTION_TITLE_KEYS = ("title", "label", "caption", "headingLabel", "badge")


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


def _sections_summary(sections: list[dict[str, Any]]) -> list[str]:
    lines = []
    for number, section in enumerate(sections, 1):
        kind = str(section.get("type") or "")
        if kind == "free_footer_brand" or not kind:
            continue
        name = SECTION_EDITOR_NAMES.get(kind, kind)
        title = next((_plain(section.get(key)) for key in SECTION_TITLE_KEYS if _plain(section.get(key))), "")
        anchor = str(section.get("anchorId") or f"secao-{number}")
        hidden = "" if section.get("enabled", True) else " (oculta)"
        style = ""
        if kind == "reasons":
            # Estilo atual dos cards, para a IA manter (ou trocar, se pedirem).
            style = " (com emojis)" if section.get("iconMode") == "emoji" else " (com ícones)"
        lines.append(f'{number}. {anchor}: {name}{style}{hidden}' + (f' · "{_short(title, 70)}"' if title else ""))
    return lines


def build_agency_context(db: Session, page: Page, page_sections: list[dict[str, Any]] | None = None) -> str:
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
    # Seções como estão no editor agora (inclui o que ainda não foi salvo); sem elas, as salvas.
    if page_sections is None:
        config = page.config_json if isinstance(page.config_json, dict) else {}
        page_sections = [section for section in config.get("sections") or [] if isinstance(section, dict)]
    summary = _sections_summary(page_sections)
    if summary:
        lines.append('SEÇÕES DESTA PÁGINA (na ordem; para trocar uma, use "Substitui: identificador" com o que vem antes dos dois-pontos):')
        lines.extend(summary)
    else:
        lines.append("SEÇÕES DESTA PÁGINA: nenhuma ainda.")

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
