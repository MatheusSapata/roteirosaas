"""Dados da conta que o assistente de IA recebe a cada conversa: agência, contatos, redes
sociais e as páginas já criadas, para não perguntar o que já está cadastrado e poder ligar
cards e links a páginas que existem."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.page import Page
from app.services.stock_images import curated_catalog

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
    "inclusions": "Resumo do pacote", "redirect": "Redirecionamento",
}
SECTION_TITLE_KEYS = ("title", "label", "caption", "headingLabel", "badge")
# Jeito de escrever: banners e chamadas das páginas mais recentes. História: seção "Sobre" de
# qualquer página (Artigo ou Texto e Imagens com título de quem somos / nossa história).
VOICE_PAGES = 6
VOICE_SAMPLES = 6
HISTORY_TITLE = re.compile(
    r"quem somos|sobre n[óo]s|sobre a (ag[êe]ncia|empresa|equipe)|nossa (hist[óo]ria|equipe|trajet[óo]ria)"
    r"|conhe[çc]a a (ag[êe]ncia|empresa|equipe)|a ag[êe]ncia",
    re.I,
)


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


HEADER_MODES = {"solid": "sólido", "transparent": "transparente", "blurred": "desfocado"}
HEADER_ACTIONS = {"social": "redes sociais", "contact": "botão", "none": "nada"}


def _header_summary(section: dict[str, Any]) -> str:
    parts = [f"aparência {HEADER_MODES.get(str(section.get('mode') or 'solid'), 'sólido')}"]
    parts.append("fixo ao rolar" if section.get("stickyEnabled", True) else "solto (não fixa ao rolar)")
    action = HEADER_ACTIONS.get(str(section.get("actionType") or "none"), "nada")
    label = _plain(section.get("contactLabel"))
    parts.append(f'lado direito: {action}' + (f' "{_short(label, 40)}"' if action == "botão" and label else ""))
    items = []
    for link in section.get("links") or []:
        if not isinstance(link, dict):
            continue
        name = _short(_plain(link.get("label")), 30)
        target = str(link.get("target") or "").strip()
        if name:
            items.append(f"{name} → {target}" if target else name)
    parts.append("itens: " + ("; ".join(items[:8]) if items else "nenhum"))
    return " · " + " · ".join(parts)


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
        if kind == "header":
            # O menu não tem título: vai como está, para a IA mexer só no que pedirem.
            style = _header_summary(section)
        lines.append(f'{number}. {anchor}: {name}{style}{hidden}' + (f' · "{_short(title, 70)}"' if title else ""))
    return lines


def _agency_voice(pages: list[Page], agency_name: str = "") -> list[str]:
    """Trechos das outras páginas da agência: como ela escreve e a história dela."""
    samples: list[str] = []
    history = ""
    name = _plain(agency_name).lower()
    for position, page in enumerate(pages):
        config = page.config_json if isinstance(page.config_json, dict) else {}
        for section in config.get("sections") or []:
            if not isinstance(section, dict) or section.get("enabled") is False:
                continue
            kind = section.get("type")
            title = _plain(section.get("title"))
            if kind in ("biography", "story"):
                heading = f"{title} {_plain(section.get('badge'))} {_plain(section.get('label'))}"
                body = _plain(section.get("text") if kind == "biography" else section.get("subtitle"))
                about = HISTORY_TITLE.search(heading) or (len(name) >= 4 and name in heading.lower())
                if about and len(body) > len(history):
                    history = f"{title}: {body}" if title else body
            if position >= VOICE_PAGES or len(samples) >= VOICE_SAMPLES:
                continue
            if kind == "hero" and title:
                subtitle = _plain(section.get("subtitle"))
                samples.append(_short(f"{title} — {subtitle}" if subtitle else title, 170))
            elif kind == "cta" and _plain(section.get("label")):
                description = _plain(section.get("description"))
                label = _plain(section.get("label"))
                samples.append(_short(f"{label} — {description}" if description else label, 170))
    lines: list[str] = []
    if samples:
        lines.append(
            "COMO A AGÊNCIA ESCREVE (trechos das outras páginas dela): siga o mesmo tom, o tratamento "
            "(você, vocês, a gente...), o jeito de chamar para a ação e o uso de emojis. Não copie frases "
            "inteiras nem preços, datas ou detalhes de outras viagens:"
        )
        lines.extend(f'- "{sample}"' for sample in dict.fromkeys(samples))
    if history:
        lines.append(
            "HISTÓRIA DA AGÊNCIA (da seção sobre a agência em outra página; use em seções sobre a agência, "
            f"com as mesmas informações, sem inventar fatos novos): {_short(history, 700)}"
        )
    return lines


def build_agency_context(
    db: Session, page: Page, page_sections: list[dict[str, Any]] | None = None, *, include_images: bool = True
) -> str:
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

    if not include_images:
        lines.append(
            'Imagens: DESLIGADAS pelo usuário (opção "Inserir imagens" do assistente). Não escreva "Busca de imagem" '
            "e não prometa fotos; as seções novas ficam com a imagem provisória e as atuais mantêm as fotos."
        )
    catalog = curated_catalog(db) if include_images else []
    if catalog:
        lines.append(
            "Fotos cadastradas no banco da plataforma (quando a seção falar de um destes lugares ou atrações, "
            'comece a "Busca de imagem" com o termo exato, ex.: "beto carrero nerf | family theme park"): '
            + "; ".join(catalog)
        )

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
        lines.extend(_agency_voice(others, agency.name))
    else:
        lines.append("Outras páginas da agência: nenhuma.")
    return "\n".join(lines)
