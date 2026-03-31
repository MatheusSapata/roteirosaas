import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_superuser, get_db
from app.models.page import Page
from app.models.page_template import PageTemplate
from app.models.user import User
from app.schemas.page_template import (
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


@router.get("", response_model=list[PageTemplateOut])
def list_templates(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> list[PageTemplateOut]:
    return db.query(PageTemplate).all()


@router.get("/{template_id}", response_model=PageTemplateOut)
def get_template(
    template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> PageTemplateOut:
    template = db.query(PageTemplate).filter(PageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Modelo não encontrado.")
    return template


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
