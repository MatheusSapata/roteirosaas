import re
import unicodedata

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_superuser, get_db
from app.api.v1.endpoints.pages import (
    ensure_agency_member,
    ensure_pages_editor_permission,
    resolve_agency_plan,
)
from app.models.page import Page
from app.models.page_template import PageTemplate
from app.models.user import User
from app.schemas.page_template import (
    AgencyTemplateCreate,
    AgencyTemplateUpdate,
    PageTemplateCreate,
    PageTemplateFromPage,
    PageTemplateOut,
    PageTemplateUpdate,
)
from app.services.page_templates import scrub_template_config

router = APIRouter()


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "modelo"


# Limite de modelos próprios por agência (evita acúmulo sem fim de JSON pesado).
MAX_AGENCY_TEMPLATES = 50

# Partes do config da página que não fazem sentido num modelo: formulário de captura,
# pixels e dados de compartilhamento são escolhidos de novo em cada página.
_TEMPLATE_CONFIG_KEYS = ("version", "design", "theme", "editor", "sections")


def _unique_slug(db: Session, base: str) -> str:
    slug = base
    counter = 1
    while db.query(PageTemplate.id).filter(PageTemplate.slug == slug).first():
        counter += 1
        slug = f"{base}-{counter}"
    return slug


def _get_agency_template(db: Session, template_id: int, user: User) -> PageTemplate:
    template = db.query(PageTemplate).filter(PageTemplate.id == template_id).first()
    if not template or template.agency_id is None:
        raise HTTPException(status_code=404, detail="Modelo não encontrado.")
    ensure_agency_member(db, template.agency_id, user)
    ensure_pages_editor_permission(db, template.agency_id, user)
    return template


@router.get("", response_model=list[PageTemplateOut])
def list_templates(
    agency_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PageTemplateOut]:
    """Sem agency_id: só os modelos da plataforma. Com agency_id: os da plataforma + os da agência."""
    query = db.query(PageTemplate)
    if agency_id:
        ensure_agency_member(db, agency_id, current_user)
        query = query.filter(or_(PageTemplate.agency_id.is_(None), PageTemplate.agency_id == agency_id))
    else:
        query = query.filter(PageTemplate.agency_id.is_(None))
    return query.order_by(PageTemplate.agency_id.is_(None), PageTemplate.id.desc()).all()


@router.get("/{template_id}", response_model=PageTemplateOut)
def get_template(
    template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> PageTemplateOut:
    template = db.query(PageTemplate).filter(PageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Modelo não encontrado.")
    if template.agency_id is not None:
        ensure_agency_member(db, template.agency_id, current_user)
    return template


@router.post("/agency", response_model=PageTemplateOut, status_code=201)
def create_agency_template(
    payload: AgencyTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PageTemplateOut:
    ensure_agency_member(db, payload.agency_id, current_user)
    ensure_pages_editor_permission(db, payload.agency_id, current_user)
    if not getattr(current_user, "is_superuser", False) and resolve_agency_plan(db, payload.agency_id) == "free":
        raise HTTPException(
            status_code=403, detail="Salvar template está disponível apenas a partir do plano Essencial."
        )
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Dê um nome ao modelo.")
    config = scrub_template_config(payload.config_json)
    if not isinstance(config, dict) or not isinstance(config.get("sections"), list) or not config["sections"]:
        raise HTTPException(status_code=400, detail="A página não tem seções para salvar como modelo.")
    config = {key: config[key] for key in _TEMPLATE_CONFIG_KEYS if key in config}
    total = db.query(PageTemplate.id).filter(PageTemplate.agency_id == payload.agency_id).count()
    if total >= MAX_AGENCY_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Limite de {MAX_AGENCY_TEMPLATES} modelos salvos. Exclua algum para salvar outro.",
        )
    template = PageTemplate(
        name=name,
        slug=_unique_slug(db, f"agencia-{payload.agency_id}-{_slugify(name)}"),
        description=(payload.description or "").strip() or None,
        is_default=False,
        config_json=config,
        agency_id=payload.agency_id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.patch("/agency/{template_id}", response_model=PageTemplateOut)
def update_agency_template(
    template_id: int,
    payload: AgencyTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PageTemplateOut:
    template = _get_agency_template(db, template_id, current_user)
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        name = (updates["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Dê um nome ao modelo.")
        template.name = name
    if "description" in updates:
        template.description = (updates["description"] or "").strip() or None
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/agency/{template_id}", status_code=204)
def delete_agency_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    template = _get_agency_template(db, template_id, current_user)
    db.delete(template)
    db.commit()


@router.post("", response_model=PageTemplateOut, dependencies=[Depends(get_current_superuser)])
def create_template(template_in: PageTemplateCreate, db: Session = Depends(get_db)) -> PageTemplateOut:
    slug = _slugify(template_in.slug)
    existing = db.query(PageTemplate).filter(PageTemplate.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug de modelo já existe.")
    payload = template_in.dict()
    payload["slug"] = slug
    template = PageTemplate(**payload)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.post("/from-page", response_model=PageTemplateOut, dependencies=[Depends(get_current_superuser)])
def create_template_from_page(payload: PageTemplateFromPage, db: Session = Depends(get_db)) -> PageTemplateOut:
    slug = _slugify(payload.slug)
    existing = db.query(PageTemplate).filter(PageTemplate.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug de modelo já existe.")
    page = db.query(Page).filter(Page.id == payload.page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    if not page.config_json:
        raise HTTPException(status_code=400, detail="Página não possui conteúdo configurado.")
    sanitized_config = scrub_template_config(page.config_json)
    template = PageTemplate(
        name=payload.name,
        slug=slug,
        description=payload.description,
        is_default=payload.is_default,
        config_json=sanitized_config or {},
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/{template_id}", response_model=PageTemplateOut, dependencies=[Depends(get_current_superuser)])
def update_template(template_id: int, template_in: PageTemplateUpdate, db: Session = Depends(get_db)) -> PageTemplateOut:
    template = db.query(PageTemplate).filter(PageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Modelo não encontrado.")
    updates = template_in.dict(exclude_unset=True)
    if "slug" in updates and updates["slug"]:
        updates["slug"] = _slugify(updates["slug"])
        existing = (
            db.query(PageTemplate)
            .filter(PageTemplate.slug == updates["slug"], PageTemplate.id != template_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Slug de modelo já existe.")
    for key, value in updates.items():
        setattr(template, key, value)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete(
    "/{template_id}",
    status_code=204,
    dependencies=[Depends(get_current_superuser)],
)
def delete_template(template_id: int, db: Session = Depends(get_db)) -> None:
    template = db.query(PageTemplate).filter(PageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Modelo não encontrado.")
    db.delete(template)
    db.commit()
