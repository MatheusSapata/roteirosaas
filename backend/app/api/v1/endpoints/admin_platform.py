"""Admin master › Marca e SEO e › E-mails do sistema."""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.user import User
from app.services import platform_branding as branding

router = APIRouter()
public_router = APIRouter()

MAX_IMAGE_BYTES = 5 * 1024 * 1024
# SVG fica de fora: pode carregar script e é servido no mesmo endereço do painel.
IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


class BrandingIn(BaseModel):
    site_title: str | None = Field(None, max_length=120)
    site_description: str | None = Field(None, max_length=300)
    theme_color: str | None = Field(None, max_length=20)
    logo_url: str | None = Field(None, max_length=1000)
    logo_dark_url: str | None = Field(None, max_length=1000)
    favicon_url: str | None = Field(None, max_length=1000)
    email_logo_url: str | None = Field(None, max_length=1000)
    share_image_url: str | None = Field(None, max_length=1000)


class EmailTextsIn(BaseModel):
    subject: str = ""
    eyebrow: str = ""
    title: str = ""
    body: str = ""
    button_label: str = ""
    note: str = ""


class EmailsIn(BaseModel):
    templates: dict[str, EmailTextsIn] = Field(default_factory=dict)


class EmailPreviewIn(BaseModel):
    key: str
    texts: EmailTextsIn | None = None


class EmailTestIn(BaseModel):
    key: str
    to: str = Field(..., min_length=3, max_length=255)


def _branding_out(db: Session) -> dict[str, Any]:
    row = branding.get_row(db)
    return {
        **{name: getattr(row, name) for name in branding.BRAND_FIELDS},
        "defaults": {
            "site_title": branding.DEFAULT_SITE_TITLE,
            "site_description": branding.DEFAULT_SITE_DESCRIPTION,
            "theme_color": branding.DEFAULT_THEME_COLOR,
        },
    }


def _clean(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


@public_router.get("/public/platform-branding")
def get_public_branding():
    return branding.public_branding()


@router.get("/platform/branding")
def get_branding(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    return _branding_out(db)


@router.put("/platform/branding")
def update_branding(payload: BrandingIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    color = _clean(payload.theme_color)
    if color and not HEX_COLOR.match(color):
        raise HTTPException(422, "Use a cor no formato #RRGGBB.")
    for name in branding.IMAGE_FIELDS:
        url = _clean(getattr(payload, name))
        if url and not url.startswith(("https://", "http://", "/uploads/")):
            raise HTTPException(422, "Endereço de imagem inválido.")
    row = branding.get_row(db)
    for name in branding.BRAND_FIELDS:
        setattr(row, name, _clean(getattr(payload, name)))
    db.add(row)
    db.commit()
    branding.clear_cache()
    return _branding_out(db)


@router.post("/platform/branding/upload")
async def upload_brand_image(
    field: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    if field not in branding.IMAGE_FIELDS:
        raise HTTPException(422, "Campo de imagem inválido.")
    content_type = (file.content_type or "").lower()
    extension = IMAGE_TYPES.get(content_type)
    if not extension:
        raise HTTPException(422, "Envie PNG, JPG, WebP ou ICO.")
    data = await file.read()
    if not data:
        raise HTTPException(422, "Arquivo vazio.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(422, "A imagem pode ter até 5 MB.")
    from app.services.media_storage import MediaStorage

    url = await run_in_threadpool(MediaStorage().save, data, f"marca{extension}", content_type)
    row = branding.get_row(db)
    setattr(row, field, url)
    db.add(row)
    db.commit()
    branding.clear_cache()
    return _branding_out(db)


def _emails_out(db: Session) -> dict[str, Any]:
    row = branding.get_row(db)
    saved = row.email_templates_json if isinstance(row.email_templates_json, dict) else {}
    items = []
    for spec in branding.SYSTEM_EMAILS:
        current = saved.get(spec.key) if isinstance(saved.get(spec.key), dict) else {}
        texts = {name: (str(current.get(name) or "").strip() or spec.defaults[name]) for name in branding.EMAIL_FIELDS}
        items.append(
            {
                "key": spec.key,
                "label": spec.label,
                "description": spec.description,
                "variables": [{"key": key, "label": label} for key, label in spec.variables],
                "texts": texts,
                "defaults": spec.defaults,
                "custom_fields": [name for name in branding.EMAIL_FIELDS if texts[name] != spec.defaults[name]],
            }
        )
    from app.services.email import EmailClient

    return {"items": items, "email_configured": EmailClient()._is_configured()}


@router.get("/platform/emails")
def get_emails(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    return _emails_out(db)


@router.put("/platform/emails")
def update_emails(payload: EmailsIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    row = branding.get_row(db)
    saved = dict(row.email_templates_json) if isinstance(row.email_templates_json, dict) else {}
    saved.update({key: value.model_dump() for key, value in payload.templates.items()})
    row.email_templates_json = branding.clean_email_templates(saved)
    db.add(row)
    db.commit()
    branding.clear_cache()
    return _emails_out(db)


def _spec(key: str) -> branding.SystemEmail:
    spec = branding.EMAIL_BY_KEY.get(key)
    if spec is None:
        raise HTTPException(422, "E-mail inválido.")
    return spec


def _sample_highlight(spec: branding.SystemEmail) -> str | None:
    if spec.key.startswith("boas_vindas"):
        return f"<b>{spec.sample['plano'].capitalize()}</b> · {spec.sample['ciclo']}"
    return None


@router.post("/platform/emails/preview")
def preview_email(payload: EmailPreviewIn, _: User = Depends(get_current_superuser)):
    """Prévia com dados de exemplo e os textos da tela (mesmo os ainda não salvos). Não envia."""
    spec = _spec(payload.key)
    texts = None
    if payload.texts is not None:
        raw = payload.texts.model_dump()
        texts = {name: (raw.get(name) or "").strip() or spec.defaults[name] for name in branding.EMAIL_FIELDS}
    subject, html_body, _text = branding.build_system_email(
        spec.key, spec.sample, button_url=spec.sample["link"], highlight=_sample_highlight(spec), texts=texts
    )
    return {"subject": subject, "html": html_body}


@router.post("/platform/emails/test")
def test_email(payload: EmailTestIn, _: User = Depends(get_current_superuser)):
    """Envia o e-mail com os textos salvos e dados de exemplo."""
    spec = _spec(payload.key)
    to = payload.to.strip()
    if "@" not in to:
        raise HTTPException(422, "Informe um e-mail válido.")
    from app.services.email import EmailClient

    subject, html_body, text_body = branding.build_system_email(
        spec.key, spec.sample, button_url=spec.sample["link"], highlight=_sample_highlight(spec)
    )
    try:
        EmailClient().send_email(
            to_email=to, subject=f"[Teste] {subject}", html_body=html_body, text_body=text_body, raise_errors=True,
            kind=spec.key,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"O teste não saiu: {exc}") from exc
    return {"sent": True}
