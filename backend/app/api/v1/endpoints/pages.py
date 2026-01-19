from datetime import datetime
import json
from typing import Any, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page, PageStatus
from app.models.page_template import PageTemplate
from app.models.user import User
from app.schemas.page import PageConfigUpdate, PageCreate, PageOut, PagePublish, PageUpdate, PublicPageOut
from app.services.plans import effective_plan, plan_limits

router = APIRouter()


def ensure_agency_member(db: Session, agency_id: int, user_id: int) -> None:
    membership = db.query(AgencyUser).filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user_id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this agency")


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


def enforce_page_limits(db: Session, page: Page, publish: bool, config: Any, plan: Optional[str] = None) -> Any:
    plan = plan or resolve_agency_plan(db, page.agency_id)
    max_published, max_sections = plan_limits(plan)

    # Limite de páginas publicadas (apenas ao publicar e se a página estava draft)
    if publish and page.status != "published" and max_published is not None:
        published_count = db.query(Page).filter(Page.agency_id == page.agency_id, Page.status == "published").count()
        if published_count >= max_published:
            raise HTTPException(status_code=403, detail=f"Limite de {max_published} páginas publicadas para o plano {plan}.")

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
    return cfg


@router.get("", response_model=list[PageOut])
def list_pages(
    agency_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[PageOut]:
    ensure_agency_member(db, agency_id, current_user.id)
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    default_id = agency.default_page_id if agency else None
    pages = db.query(Page).filter(Page.agency_id == agency_id).order_by(Page.created_at.desc()).all()
    for page in pages:
        setattr(page, "is_default", bool(default_id and page.id == default_id))
    return pages


@router.get("/{page_id}", response_model=PageOut)
def get_page(
    page_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> PageOut:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    ensure_agency_member(db, page.agency_id, current_user.id)
    plan = resolve_agency_plan(db, page.agency_id)
    page.config_json = apply_free_footer(normalize_config(page.config_json), plan)
    default_id = page.agency.default_page_id if page.agency else None
    setattr(page, "is_default", bool(default_id and page.id == default_id))
    return page


@router.post("", response_model=PageOut)
def create_page(
    page_in: PageCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> PageOut:
    ensure_agency_member(db, page_in.agency_id, current_user.id)
    if page_in.template_id:
        template = db.query(PageTemplate).filter(PageTemplate.id == page_in.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
    payload = page_in.dict()
    payload["config_json"] = normalize_config(payload.get("config_json"))
    page = Page(**payload)
    plan = resolve_agency_plan(db, page.agency_id)
    page.config_json = enforce_page_limits(db, page, publish=False, config=page.config_json, plan=plan)
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
        raise HTTPException(status_code=404, detail="Page not found")
    ensure_agency_member(db, page.agency_id, current_user.id)
    plan = resolve_agency_plan(db, page.agency_id)
    updates = page_in.dict(exclude_unset=True)
    if "config_json" in updates:
        normalized = normalize_config(updates.get("config_json"))
        updates["config_json"] = enforce_page_limits(db, page, publish=False, config=normalized, plan=plan)
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
        raise HTTPException(status_code=404, detail="Page not found")
    ensure_agency_member(db, page.agency_id, current_user.id)
    plan = resolve_agency_plan(db, page.agency_id)
    normalized = normalize_config(payload.config)
    page.config_json = enforce_page_limits(db, page, publish=False, config=normalized, plan=plan)
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
        raise HTTPException(status_code=404, detail="Page not found")
    ensure_agency_member(db, page.agency_id, current_user.id)
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
        raise HTTPException(status_code=404, detail="Page not found")
    ensure_agency_member(db, page.agency_id, current_user.id)
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
        raise HTTPException(status_code=404, detail="Page not found")
    ensure_agency_member(db, page.agency_id, current_user.id)
    if page.status != PageStatus.published:
        raise HTTPException(status_code=400, detail="Only published pages can be set as default")
    agency = page.agency or db.query(Agency).filter(Agency.id == page.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
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
        raise HTTPException(status_code=404, detail="Page not found or not published")
    plan = resolve_agency_plan(db, page.agency_id)
    branding = {
        "agency_name": page.agency.name,
        "logo_url": page.agency.logo_url,
        "primary_color": page.agency.primary_color,
        "secondary_color": page.agency.secondary_color,
    }
    config = apply_free_footer(normalize_config(page.config_json), plan) or {}
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
