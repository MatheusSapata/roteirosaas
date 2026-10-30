"""Tags de páginas e a seção Links/Roteiros no modo "Por tag".

No modo por tag a seção guarda só a regra (quais tags, ordem, limite...). Os cards são montados
aqui, na hora de servir a página, a partir das páginas publicadas da mesma agência. Assim um
roteiro novo com a tag aparece sozinho e foto, título, datas e preço vêm sempre da versão atual.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, selectinload

from app.models.agency import Agency
from app.models.agency_domain import AgencyDomain
from app.models.page import Page, PageStatus
from app.models.page_tag import PageTag

TAG_COLORS = ("blue", "amber", "rose", "violet", "teal", "orange", "slate", "green")
TAG_NAME_MAX = 60
GRID_MAX_ITEMS = 8
DEFAULT_TAG_LIMIT = 12
SORTS = ("departure", "recent", "title")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CURRENCY_PREFIX = {"BRL": "R$", "USD": "US$", "EUR": "€", "GBP": "£"}


def slugify_tag(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")[:80]


def clean_tag_name(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())[:TAG_NAME_MAX]


def is_tag_section(section: Any) -> bool:
    return isinstance(section, dict) and section.get("type") == "links" and section.get("mode") == "tag"


def section_tag_ids(section: dict) -> list[int]:
    ids: list[int] = []
    for raw in section.get("tagIds") or []:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value not in ids:
            ids.append(value)
    return ids


def _today() -> date:
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()


def _plain(value: Any) -> str:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()
    if isinstance(value, dict):
        return _plain(value.get("pt") or value.get("es") or next(iter(value.values()), ""))
    return ""


def _timestamp(value: Optional[datetime]) -> float:
    return value.timestamp() if value else 0.0


def _valid_date(value: Any) -> str:
    return value if isinstance(value, str) and _DATE_RE.match(value) else ""


def _format_price(value: float, currency: str) -> str:
    whole = abs(value - round(value)) < 0.005
    text = f"{value:,.0f}" if whole else f"{value:,.2f}"
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{_CURRENCY_PREFIX.get(currency, currency)} {text}"


def _sections(config: Any) -> list[dict]:
    if not isinstance(config, dict):
        return []
    return [section for section in config.get("sections") or [] if isinstance(section, dict)]


def page_card_data(page: Page) -> dict[str, Any]:
    """Dados do card de um roteiro: os mesmos que o formulário de Links usa ao escolher a página à mão."""
    config = page.config_json if isinstance(page.config_json, dict) else {}
    sections = _sections(config)
    hero = next((section for section in sections if section.get("type") == "hero"), {})
    general = config.get("general") if isinstance(config.get("general"), dict) else {}
    description = _plain(hero.get("subtitle")) or _plain(general.get("shortDescription")) or (page.seo_description or "")
    if len(description) > 220:
        description = description[:217].rstrip() + "…"

    # Menor preço entre a seção Preços e os pacotes do Checkout (valores em reais).
    candidates: list[tuple[Any, str]] = []
    excursion: dict = {}
    for section in sections:
        if section.get("enabled") is False:
            continue
        if section.get("type") == "prices":
            candidates += [
                (item.get("price"), str(item.get("currency") or "BRL"))
                for item in section.get("items") or []
                if isinstance(item, dict)
            ]
        elif section.get("type") == "viajeon_checkout":
            snapshot = section.get("checkoutSnapshot") if isinstance(section.get("checkoutSnapshot"), dict) else {}
            candidates += [
                (item.get("price"), "BRL")
                for item in snapshot.get("packages") or []
                if isinstance(item, dict) and item.get("active") is not False
            ]
            if not excursion and isinstance(snapshot.get("excursion"), dict):
                excursion = snapshot["excursion"]
    lowest: Optional[tuple[float, str]] = None
    for raw_price, currency in candidates:
        try:
            price = float(raw_price or 0)
        except (TypeError, ValueError):
            continue
        if price <= 0 or (lowest and currency != lowest[1]):
            continue
        if not lowest or price < lowest[0]:
            lowest = (price, currency)

    # Datas do Banner; sem elas, as da excursão do Checkout.
    departure = _valid_date(hero.get("departureDate"))
    return_date = _valid_date(hero.get("returnDate"))
    if not departure and not return_date:
        departure = _valid_date(str(excursion.get("departure_date") or "")[:10])
        return_date = _valid_date(str(excursion.get("return_date") or "")[:10])

    return {
        "title": (page.seo_title or page.title or "").strip(),
        "description": description,
        "image": hero.get("backgroundImage") or page.cover_image_url or "",
        "departureDate": departure,
        "returnDate": return_date,
        "price": _format_price(*lowest) if lowest else "",
    }


def agency_page_base(db: Session, agency: Agency) -> str:
    """Começo do link das páginas: "/" com domínio próprio ativo, "/slug-da-agencia/" sem ele.

    É a mesma regra do painel (buildPublicPagePath) para os cards escolhidos à mão.
    """
    has_domain = (
        db.query(AgencyDomain.id)
        .filter(AgencyDomain.agency_id == agency.id, AgencyDomain.is_active.is_(True), AgencyDomain.is_verified.is_(True))
        .first()
    )
    return "/" if has_domain or not agency.slug else f"/{agency.slug}/"


def resolve_tag_section(
    db: Session,
    section: dict,
    *,
    agency: Agency,
    host_page_id: Optional[int],
    pages: Optional[Iterable[Page]] = None,
    base: Optional[str] = None,
) -> tuple[list[dict], list[dict]]:
    """Monta os cards da seção por tag. Devolve (cards, roteiros que ficaram de fora com o motivo)."""
    tag_ids = section_tag_ids(section)
    if not tag_ids:
        return [], []
    if pages is None:
        pages = (
            db.query(Page)
            .options(selectinload(Page.tags))
            .filter(Page.agency_id == agency.id, Page.tags.any(PageTag.id.in_(tag_ids)))
            .all()
        )
    if base is None:
        base = agency_page_base(db, agency)
    match_all = section.get("tagMatch") == "all"
    hide_past = section.get("tagHidePast") is not False
    exclude_current = section.get("tagExcludeCurrent") is not False
    today = _today().isoformat()

    included: list[tuple[Page, dict]] = []
    excluded: list[dict] = []
    for page in pages:
        if page.agency_id != agency.id:
            continue
        page_tag_ids = {tag.id for tag in page.tags}
        hit = all(t in page_tag_ids for t in tag_ids) if match_all else any(t in page_tag_ids for t in tag_ids)
        if not hit:
            continue
        data = page_card_data(page)
        reason = ""
        if exclude_current and host_page_id and page.id == host_page_id:
            reason = "current"
        elif page.status != PageStatus.published:
            reason = "draft"
        elif hide_past and data["departureDate"] and data["departureDate"] < today:
            reason = "past"
        if reason:
            excluded.append({"pageId": page.id, "title": page.title, "reason": reason})
        else:
            included.append((page, data))

    sort = section.get("tagSort") if section.get("tagSort") in SORTS else "departure"
    if sort == "title":
        included.sort(key=lambda entry: entry[1]["title"].lower())
    elif sort == "recent":
        included.sort(key=lambda entry: _timestamp(entry[0].published_at or entry[0].created_at), reverse=True)
    else:
        included.sort(key=lambda entry: (entry[1]["departureDate"] or "9999-99-99", entry[1]["title"].lower()))

    try:
        limit = int(section.get("tagLimit", DEFAULT_TAG_LIMIT) or 0)
    except (TypeError, ValueError):
        limit = DEFAULT_TAG_LIMIT
    if section.get("carouselEnabled") is False:
        limit = min(limit or GRID_MAX_ITEMS, GRID_MAX_ITEMS)
    if limit > 0 and len(included) > limit:
        for page, _data in included[limit:]:
            excluded.append({"pageId": page.id, "title": page.title, "reason": "limit"})
        included = included[:limit]

    show_dates = section.get("tagShowDates") is not False
    show_price = section.get("tagShowPrice") is not False
    button = section.get("tagButtonLabel") or {"pt": "Ver roteiro", "es": "Ver itinerario"}
    cards = []
    for page, data in included:
        cards.append(
            {
                "id": f"tag-page-{page.id}",
                "source": "page",
                "pageId": page.id,
                "url": f"{base}{page.slug}",
                "image": data["image"],
                "title": data["title"],
                "description": data["description"],
                "buttonLabel": button,
                "openInNewTab": False,
                "showDates": show_dates and bool(data["departureDate"] or data["returnDate"]),
                "departureDate": data["departureDate"],
                "returnDate": data["returnDate"],
                "showPrice": show_price and bool(data["price"]),
                "pricePrefix": {"pt": "a partir de", "es": "desde"},
                "priceValue": data["price"],
                "priceSuffix": {"pt": "por pessoa", "es": "por persona"},
            }
        )
    return cards, excluded


def inject_tag_links_into_config(db: Session, page: Page, config: Any) -> Any:
    """Preenche os cards das seções Links/Roteiros que estão no modo "Por tag"."""
    tag_sections = [section for section in _sections(config) if is_tag_section(section)]
    if not tag_sections:
        return config
    agency = page.agency or db.query(Agency).filter(Agency.id == page.agency_id).first()
    if not agency:
        return config
    all_ids = {tag_id for section in tag_sections for tag_id in section_tag_ids(section)}
    pages = (
        db.query(Page)
        .options(selectinload(Page.tags))
        .filter(Page.agency_id == agency.id, Page.tags.any(PageTag.id.in_(all_ids)))
        .all()
        if all_ids
        else []
    )
    base = agency_page_base(db, agency)
    for section in tag_sections:
        section["items"], _excluded = resolve_tag_section(
            db, section, agency=agency, host_page_id=page.id, pages=pages, base=base
        )
    return config


def replace_tag_in_sections(db: Session, agency_id: int, old_id: int, new_id: Optional[int]) -> None:
    """Troca (ou tira, com new_id None) uma tag das regras das seções por tag da agência."""
    for page in db.query(Page).filter(Page.agency_id == agency_id).all():
        config = page.config_json
        if not isinstance(config, dict):
            continue
        changed = False
        sections = []
        for section in config.get("sections") or []:
            if is_tag_section(section) and old_id in section_tag_ids(section):
                ids = [new_id if tag_id == old_id else tag_id for tag_id in section_tag_ids(section)]
                section = {**section, "tagIds": list(dict.fromkeys(tag_id for tag_id in ids if tag_id is not None))}
                changed = True
            sections.append(section)
        if changed:
            page.config_json = {**config, "sections": sections}
            db.add(page)


def sections_using_tags(db: Session, agency_id: int) -> dict[int, list[dict]]:
    """Para cada tag, as seções por tag que a usam (página e título da página)."""
    usage: dict[int, list[dict]] = {}
    for page in db.query(Page).filter(Page.agency_id == agency_id).all():
        for section in _sections(page.config_json):
            if not is_tag_section(section):
                continue
            for tag_id in section_tag_ids(section):
                usage.setdefault(tag_id, []).append({"page_id": page.id, "page_title": page.title})
    return usage
