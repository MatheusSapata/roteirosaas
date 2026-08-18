from datetime import datetime
from copy import deepcopy
import json
import ipaddress
import re
import socket
import unicodedata
from html.parser import HTMLParser
from typing import Any, Optional, Tuple
from urllib.parse import quote, urljoin, urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page, PageStatus
from app.models.page_template import PageTemplate
from app.models.user import User
from app.schemas.page import PageConfigUpdate, PageCreate, PageOut, PagePublish, PageUpdate, PublicPageOut
from app.services.flight_sections import (
    cleanup_removed_flight_sections,
    ensure_flight_section_ids,
    inject_flight_sections_into_config,
)
from app.services.page_templates import apply_template_branding, build_whatsapp_link
from app.services.plans import effective_plan, plan_limits
from app.services.team import get_user_effective_permissions

router = APIRouter()


class LinkMetadataRequest(BaseModel):
    url: HttpUrl


class _OpenGraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.metadata: dict[str, str] = {}
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        values = {str(key).lower(): value or "" for key, value in attrs}
        if tag.lower() == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            if key and values.get("content"):
                self.metadata.setdefault(key, values["content"].strip())
        elif tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def _ensure_public_http_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Informe uma URL HTTP ou HTTPS válida.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise HTTPException(status_code=422, detail="O endereço informado não pôde ser encontrado.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise HTTPException(status_code=422, detail="Endereços privados ou internos não são permitidos.")
    return raw_url


def _localized_text(value: Any) -> str:
    if isinstance(value, str):
        return re.sub(r"<[^>]+>", "", value).strip()
    if isinstance(value, dict):
        candidate = value.get("pt") or value.get("es") or next(iter(value.values()), "")
        return _localized_text(candidate)
    return ""


def _roteiro_online_metadata(raw_url: str, db: Session) -> Optional[dict[str, str]]:
    parsed = urlparse(raw_url)
    host = (parsed.hostname or "").lower()
    if host not in {"roteiroonline.com", "www.roteiroonline.com", "app.roteiroonline.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if parts and parts[0].lower() == "p":
        parts = parts[1:]
    if len(parts) < 2:
        return None
    agency_slug, page_slug = parts[0], parts[1]
    page = (
        db.query(Page)
        .join(Page.agency)
        .filter(
            Page.slug.ilike(page_slug),
            Page.status == PageStatus.published,
            Page.agency.has(Agency.slug.ilike(agency_slug)),
        )
        .first()
    )
    if not page:
        return None

    config = normalize_config(page.config_json) or {}
    sections = config.get("sections") if isinstance(config, dict) else []
    hero = next(
        (section for section in sections or [] if isinstance(section, dict) and section.get("type") == "hero"),
        {},
    )
    title = (page.seo_title or page.title or "").strip()
    if "roteiro online" not in title.lower():
        title = f"{title} | Roteiro Online"
    description = _localized_text(hero.get("subtitle"))
    if not description:
        general = config.get("general") if isinstance(config, dict) else {}
        description = _localized_text(general.get("shortDescription")) if isinstance(general, dict) else ""
    if not description:
        description = (page.seo_description or "").strip()
    image = str(hero.get("backgroundImage") or page.cover_image_url or page.agency.logo_url or "").strip()
    if image:
        image = urljoin(raw_url, image)
    return {"url": raw_url, "title": title[:300], "description": description[:1000], "image": image}


def _roteiro_online_path(raw_url: str) -> Optional[tuple[str, str, str]]:
    parsed = urlparse(raw_url)
    host = (parsed.hostname or "").lower()
    if host not in {"roteiroonline.com", "www.roteiroonline.com", "app.roteiroonline.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if parts and parts[0].lower() == "p":
        parts = parts[1:]
    if len(parts) < 2:
        return None
    return f"{parsed.scheme}://{parsed.netloc}", parts[0], parts[1]


def _metadata_from_public_page(raw_url: str, payload: dict[str, Any]) -> dict[str, str]:
    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    sections = config.get("sections") if isinstance(config, dict) else []
    hero = next(
        (section for section in sections or [] if isinstance(section, dict) and section.get("type") == "hero"),
        {},
    )
    title = str(payload.get("seo_title") or payload.get("title") or "").strip()
    if title and "roteiro online" not in title.lower():
        title = f"{title} | Roteiro Online"
    description = _localized_text(hero.get("subtitle"))
    if not description:
        general = config.get("general") if isinstance(config, dict) else {}
        description = _localized_text(general.get("shortDescription")) if isinstance(general, dict) else ""
    if not description:
        description = str(payload.get("seo_description") or "").strip()
    branding = payload.get("branding") if isinstance(payload.get("branding"), dict) else {}
    image = str(hero.get("backgroundImage") or payload.get("cover_image_url") or branding.get("logo_url") or "").strip()
    return {
        "url": raw_url,
        "title": title[:300],
        "description": description[:1000],
        "image": urljoin(raw_url, image) if image else "",
    }


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFD", (value or "").strip().lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or f"pagina-{int(datetime.utcnow().timestamp())}"


def _ensure_unique_slug(db: Session, agency_id: int, raw_slug: str, page_id: Optional[int] = None) -> str:
    base_slug = _slugify(raw_slug)
    candidate = base_slug
    counter = 1
    query = db.query(Page.id).filter(Page.agency_id == agency_id, Page.slug == candidate)
    if page_id is not None:
        query = query.filter(Page.id != page_id)
    while (
        query.first()
        is not None
    ):
        suffix = f"-{counter}"
        candidate = f"{base_slug}{suffix}"
        counter += 1
        query = db.query(Page.id).filter(Page.agency_id == agency_id, Page.slug == candidate)
        if page_id is not None:
            query = query.filter(Page.id != page_id)
    return candidate


def _apply_agency_highlight_colors(config: Any, agency: Agency) -> Any:
    parsed = normalize_config(config)
    if not isinstance(parsed, dict):
        return parsed
    primary = (agency.primary_color or "").strip() or "#41ce5f"
    theme = parsed.get("theme")
    if not isinstance(theme, dict):
        theme = {}
        parsed["theme"] = theme
    theme["ctaDefaultColor"] = primary
    sections = parsed.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict):
                section["ctaColor"] = primary
    return parsed


def ensure_agency_member(db: Session, agency_id: int, user: User) -> None:
    if getattr(user, "is_superuser", False):
        return
    membership = db.query(AgencyUser).filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Você não faz parte desta agência.")



def ensure_pages_editor_permission(db: Session, agency_id: int, user: User) -> None:
    if getattr(user, "is_superuser", False):
        return
    effective = set(get_user_effective_permissions(db, user, agency_id))
    if "pages_editor" in effective:
        return
    is_owner = user.is_owner is None or bool(user.is_owner)
    if is_owner or (user.role or "").lower() in {"admin", "owner"}:
        return
    raise HTTPException(status_code=403, detail="Você não tem permissão para alterar páginas.")

def normalize_config(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def resolve_agency_plan(db: Session, agency_id: int) -> str:
    owner = (
        db.query(User)
        .join(AgencyUser, AgencyUser.user_id == User.id)
        .filter(AgencyUser.agency_id == agency_id, AgencyUser.role == "owner")
        .first()
    )
    if owner:
        return effective_plan(owner)

    fallback = (
        db.query(User)
        .join(AgencyUser, AgencyUser.user_id == User.id)
        .filter(AgencyUser.agency_id == agency_id)
        .first()
    )
    if fallback:
        return effective_plan(fallback)
    return "free"


def derive_cover_image_from_config(raw: Any) -> Optional[str]:
    """Extracts a representative cover image from the page config."""
    config = normalize_config(raw)
    if not isinstance(config, dict):
        return None
    sections = config.get("sections")
    if not isinstance(sections, list):
        return None
    for section in sections:
        if not isinstance(section, dict):
            continue
        if section.get("enabled") is False:
            continue
        if section.get("type") != "hero":
            continue
        image = section.get("backgroundImage") or section.get("background_image")
        if isinstance(image, str):
            trimmed = image.strip()
            if trimmed:
                return trimmed
    return None


DEFAULT_FREE_FOOTER_SECTION = {
    "type": "free_footer_brand",
    "text": "Página desenvolvida através do roteiroonline.com",
    "align": "right",
    "enabled": True,
}


def apply_free_footer(cfg: Any, plan: str) -> Any:
    if plan != "free" or not isinstance(cfg, dict):
        return cfg
    sections = cfg.get("sections")
    if not isinstance(sections, list):
        sections = []
    has_footer = False
    for section in sections:
        if isinstance(section, dict) and section.get("type") == "free_footer_brand":
            section.setdefault("text", DEFAULT_FREE_FOOTER_SECTION["text"])
            section.setdefault("align", DEFAULT_FREE_FOOTER_SECTION["align"])
            section["enabled"] = True
            has_footer = True
    if not has_footer:
        sections.append(dict(DEFAULT_FREE_FOOTER_SECTION))
    cfg["sections"] = sections
    return cfg


def sanitize_digits(value: Optional[str]) -> str:
    digits = re.sub(r"\D", "", value or "")
    digits = digits.lstrip("0")
    if not digits:
        return ""
    if digits.startswith("55"):
        return digits
    if len(digits) in (10, 11):
        return f"55{digits}"
    return digits


def resolve_agency_whatsapp(db: Session, agency_id: int) -> str:
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if agency:
        digits = sanitize_digits(agency.cta_whatsapp)
        if digits:
            return digits

    owner = (
        db.query(User)
        .join(AgencyUser, AgencyUser.user_id == User.id)
        .filter(AgencyUser.agency_id == agency_id, AgencyUser.role == "owner")
        .first()
    )
    if owner:
        digits = sanitize_digits(getattr(owner, "whatsapp", ""))
        if digits:
            return digits

    fallback = (
        db.query(User)
        .join(AgencyUser, AgencyUser.user_id == User.id)
        .filter(AgencyUser.agency_id == agency_id)
        .first()
    )
    return sanitize_digits(getattr(fallback, "whatsapp", "")) if fallback else ""


def enforce_page_limits(db: Session, page: Page, publish: bool, config: Any, plan: Optional[str] = None) -> Any:
    plan = plan or resolve_agency_plan(db, page.agency_id)
    max_pages, max_sections = plan_limits(plan)

    # Limite de paginas publicadas (apenas ao publicar e se a pagina estava draft)
    if publish and page.status != "published" and max_pages is not None:
        published_count = db.query(Page).filter(Page.agency_id == page.agency_id, Page.status == "published").count()
        if published_count >= max_pages:
            raise HTTPException(
                status_code=403,
                detail=f"Limite de {max_pages} paginas permitido no plano {plan}. Ajuste suas paginas antes de publicar.",
            )

    # Limite de seções e rodapé obrigatório no free
    cfg = normalize_config(config)
    if isinstance(cfg, dict):
        sections = cfg.get("sections") or []
        if isinstance(sections, list):
            regular_sections = [
                s for s in sections if not (isinstance(s, dict) and s.get("type") == "free_footer_brand")
            ]
            if max_sections is not None and len(regular_sections) > max_sections:
                raise HTTPException(status_code=403, detail=f"Limite de {max_sections} seções por página no plano {plan}.")
            cfg["sections"] = sections
    cfg = apply_free_footer(cfg, plan)
    cfg = ensure_flight_section_ids(cfg)
    return cfg


@router.get("", response_model=list[PageOut])
def list_pages(
    agency_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[PageOut]:
    ensure_agency_member(db, agency_id, current_user)
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    default_id = agency.default_page_id if agency else None
    pages = db.query(Page).filter(Page.agency_id == agency_id).order_by(Page.created_at.desc()).all()
    for page in pages:
        setattr(page, "is_default", bool(default_id and page.id == default_id))
    return pages


@router.post("/link-metadata")
async def fetch_link_metadata(
    payload: LinkMetadataRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    del current_user
    current_url = _ensure_public_http_url(str(payload.url))
    internal_metadata = _roteiro_online_metadata(current_url, db)
    if internal_metadata:
        return internal_metadata
    public_path = _roteiro_online_path(current_url)
    if public_path:
        origin, agency_slug, page_slug = public_path
        public_api_url = (
            f"{origin}/api/v1/public/pages/by-slug/"
            f"{quote(agency_slug, safe='')}/{quote(page_slug, safe='')}"
        )
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as public_client:
                public_response = await public_client.get(public_api_url, headers={"Accept": "application/json"})
            if public_response.is_success:
                public_payload = public_response.json()
                if isinstance(public_payload, dict):
                    return _metadata_from_public_page(current_url, public_payload)
        except (httpx.HTTPError, ValueError):
            pass
    headers = {"User-Agent": "RoteiroOnline-LinkPreview/1.0", "Accept": "text/html,application/xhtml+xml"}
    body = bytearray()
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0), follow_redirects=False) as client:
        for _ in range(6):
            try:
                async with client.stream("GET", current_url, headers=headers) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            raise HTTPException(status_code=422, detail="O link retornou um redirecionamento inválido.")
                        current_url = _ensure_public_http_url(urljoin(current_url, location))
                        continue
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").lower()
                    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                        raise HTTPException(status_code=422, detail="O link não aponta para uma página HTML.")
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) >= 1_000_000:
                            break
                    encoding = response.encoding or "utf-8"
                    html = bytes(body).decode(encoding, errors="replace")
                    break
            except HTTPException:
                raise
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=422, detail="Não foi possível acessar esse link.") from exc
        else:
            raise HTTPException(status_code=422, detail="O link possui redirecionamentos demais.")

    parser = _OpenGraphParser()
    parser.feed(html)
    metadata = parser.metadata
    title = metadata.get("og:title") or metadata.get("twitter:title") or "".join(parser.title_parts).strip()
    description = metadata.get("og:description") or metadata.get("twitter:description") or metadata.get("description") or ""
    image = metadata.get("og:image") or metadata.get("twitter:image") or ""
    return {
        "url": current_url,
        "title": title[:300],
        "description": description[:1000],
        "image": urljoin(current_url, image) if image else "",
    }


@router.get("/{page_id}", response_model=PageOut)
def get_page(
    page_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> PageOut:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    plan = resolve_agency_plan(db, page.agency_id)
    page.config_json = apply_free_footer(normalize_config(page.config_json), plan)
    page.config_json = inject_flight_sections_into_config(db, page.id, page.config_json, include_lookup_status=True)
    default_id = page.agency.default_page_id if page.agency else None
    setattr(page, "is_default", bool(default_id and page.id == default_id))
    return page


@router.post("", response_model=PageOut)
def create_page(
    page_in: PageCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> PageOut:
    ensure_agency_member(db, page_in.agency_id, current_user)
    ensure_pages_editor_permission(db, page_in.agency_id, current_user)
    template = None
    if page_in.template_id:
        template = db.query(PageTemplate).filter(PageTemplate.id == page_in.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Modelo não encontrado.")
    payload = page_in.dict()
    payload["config_json"] = normalize_config(payload.get("config_json"))
    if template and payload["config_json"] is None:
        payload["config_json"] = deepcopy(template.config_json)

    agency = db.query(Agency).filter(Agency.id == page_in.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agência não encontrada.")

    payload["slug"] = _ensure_unique_slug(db, page_in.agency_id, payload.get("slug") or payload.get("title") or "pagina")
    page = Page(**payload)
    if template:
        whatsapp_digits = resolve_agency_whatsapp(db, page.agency_id)
        whatsapp_link = build_whatsapp_link(whatsapp_digits, page.title) if whatsapp_digits else None
        page.config_json = apply_template_branding(
            page.config_json,
            logo_url=getattr(agency, "logo_url", None),
            whatsapp_link=whatsapp_link,
        )
        page.config_json = _apply_agency_highlight_colors(page.config_json, agency)

    plan = resolve_agency_plan(db, page.agency_id)
    max_pages, _ = plan_limits(plan)
    if max_pages is not None:
        total_pages = db.query(Page).filter(Page.agency_id == page.agency_id).count()
        if total_pages >= max_pages:
            limit_headers = {
                "X-Error-Code": "trial_page_limit" if plan == "trial" else "plan_page_limit",
                "X-Plan-Key": plan or "",
                "X-Plan-Max-Pages": str(max_pages),
            }
            if plan == "trial":
                raise HTTPException(
                    status_code=403,
                    detail="Você atingiu o limite de 3 páginas do plano trial. Escolha um plano pago para continuar criando roteiros.",
                    headers=limit_headers,
                )
            raise HTTPException(
                status_code=403,
                detail=f"Limite de {max_pages} paginas permitido no plano {plan}. Exclua uma pagina antes de criar outra.",
                headers=limit_headers,
            )
    page.config_json = enforce_page_limits(db, page, publish=False, config=page.config_json, plan=plan)
    page.cover_image_url = derive_cover_image_from_config(page.config_json)
    db.add(page)
    db.commit()
    db.refresh(page)
    setattr(page, "is_default", False)
    return page


@router.put("/{page_id}", response_model=PageOut)
def update_page(
    page_id: int,
    page_in: PageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PageOut:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)
    plan = resolve_agency_plan(db, page.agency_id)
    updates = page_in.dict(exclude_unset=True)
    if "slug" in updates:
        updates["slug"] = _ensure_unique_slug(db, page.agency_id, updates.get("slug") or page.title or "pagina", page.id)
    if "config_json" in updates:
        normalized = normalize_config(updates.get("config_json"))
        updates["config_json"] = enforce_page_limits(db, page, publish=False, config=normalized, plan=plan)
        cleanup_removed_flight_sections(db, page.id, updates["config_json"])
        if "cover_image_url" not in updates:
            updates["cover_image_url"] = derive_cover_image_from_config(updates["config_json"])
    for key, value in updates.items():
        setattr(page, key, value)
    db.add(page)
    db.commit()
    db.refresh(page)
    default_id = page.agency.default_page_id if page.agency else None
    setattr(page, "is_default", bool(default_id and page.id == default_id))
    return page


@router.put("/{page_id}/config", response_model=PageOut)
def update_page_config(
    page_id: int,
    payload: PageConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PageOut:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)
    plan = resolve_agency_plan(db, page.agency_id)
    normalized = normalize_config(payload.config)
    page.config_json = enforce_page_limits(db, page, publish=False, config=normalized, plan=plan)
    cleanup_removed_flight_sections(db, page.id, page.config_json)
    page.cover_image_url = derive_cover_image_from_config(page.config_json)
    db.add(page)
    db.commit()
    db.refresh(page)
    default_id = page.agency.default_page_id if page.agency else None
    setattr(page, "is_default", bool(default_id and page.id == default_id))
    return page


@router.post("/{page_id}/publish", response_model=PageOut)
def publish_page(
    page_id: int,
    payload: PagePublish,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PageOut:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)
    plan = resolve_agency_plan(db, page.agency_id)
    # aplica limites por plano e enforce de seções/rodapé
    page.config_json = enforce_page_limits(db, page, payload.publish, page.config_json, plan=plan)
    if payload.publish:
        page.status = "published"
        page.published_at = datetime.utcnow()
    else:
        page.status = "draft"
        page.published_at = None
    agency = page.agency
    if not payload.publish and agency and agency.default_page_id == page.id:
        agency.default_page_id = None
        db.add(agency)
    db.add(page)
    db.commit()
    db.refresh(page)
    default_id = page.agency.default_page_id if page.agency else None
    setattr(page, "is_default", bool(default_id and page.id == default_id))
    return page


@router.delete("/{page_id}")
def delete_page(
    page_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)
    if (current_user.role or "").lower() == "editor":
        raise HTTPException(status_code=403, detail="Perfil Editor nao pode excluir paginas.")
    agency = page.agency
    if agency and agency.default_page_id == page.id:
        agency.default_page_id = None
        db.add(agency)
    db.delete(page)
    db.commit()
    return JSONResponse({"detail": "Page deleted"})


@router.post("/{page_id}/set-default", response_model=PageOut)
def set_default_page(
    page_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PageOut:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)
    if page.status != PageStatus.published:
        raise HTTPException(status_code=400, detail="Apenas páginas publicadas podem ser definidas como padrão.")
    agency = page.agency or db.query(Agency).filter(Agency.id == page.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agência não encontrada.")
    agency.default_page_id = page.id
    db.add(agency)
    db.commit()
    db.refresh(page)
    setattr(page, "is_default", True)
    return page


@router.get("/public/by-slug/{agency_slug}/{page_slug}", response_model=PublicPageOut)
def get_public_page(agency_slug: str, page_slug: str, db: Session = Depends(get_db)) -> PublicPageOut:
    page = (
        db.query(Page)
        .join(Page.agency)
        .filter(Page.slug == page_slug, Page.status == "published", Page.agency.has(slug=agency_slug))
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada ou não publicada.")
    plan = resolve_agency_plan(db, page.agency_id)
    branding = {
        "agency_name": page.agency.name,
        "logo_url": page.agency.logo_url,
        "primary_color": page.agency.primary_color,
        "secondary_color": page.agency.secondary_color,
    }
    config = apply_free_footer(normalize_config(page.config_json), plan) or {}
    config = inject_flight_sections_into_config(db, page.id, config, include_lookup_status=False)
    return PublicPageOut(
        id=page.id,
        title=page.title,
        slug=page.slug,
        agency_slug=agency_slug,
        cover_image_url=page.cover_image_url,
        seo_title=page.seo_title,
        seo_description=page.seo_description,
        config=config,
        branding=branding,
    )


