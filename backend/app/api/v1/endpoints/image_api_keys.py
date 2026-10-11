"""Admin Master: chaves dos bancos de fotos gratuitos (Unsplash e Pexels) usadas pelo
assistente de IA. Várias chaves por banco; quando uma esgota o limite da hora, a próxima
assume (ver app.services.image_api_keys)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.api.v1.endpoints.flight_api_keys import FlightApiKeyOut, get_key_or_404, serialize_key
from app.core.config import get_settings
from app.models.external_api_key import ExternalApiKey
from app.models.stock_image import StockImage, StockImageSearch
from app.models.user import User
from app.services.api_key_crypto import ApiKeyDecryptionError, decrypt_api_key, encrypt_api_key, extract_api_key_last4
from app.services.image_api_keys import DEFAULT_HOURLY_LIMIT, IMAGE_PROVIDERS, ImageKey, record_image_call, roll_hour

router = APIRouter(prefix="/master/image-api-keys")

PROVIDERS = set(IMAGE_PROVIDERS)
VALID_STATUSES = {"active", "paused", "exhausted", "error"}
TEST_URLS = {
    "unsplash": ("https://api.unsplash.com/search/photos", {"query": "beach", "per_page": 1}),
    "pexels": ("https://api.pexels.com/v1/search", {"query": "beach", "per_page": 1}),
}


class ImageApiKeyCreate(BaseModel):
    provider: str = "unsplash"
    label: str = Field(..., min_length=2, max_length=255)
    api_key: str = Field(..., min_length=4, max_length=500)
    is_active: bool = True
    priority: int = 1
    hourly_limit: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = None


class ImageApiKeyUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=2, max_length=255)
    api_key: Optional[str] = Field(default=None, min_length=4, max_length=500)
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    hourly_limit: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = None


class ImageApiKeyListResponse(BaseModel):
    items: list[FlightApiKeyOut]
    summary: dict[str, Any]


def _provider(value: str | None) -> str:
    provider = (value or "").strip().lower()
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail="Banco de fotos inválido. Use Unsplash ou Pexels.")
    return provider


def _get(db: Session, key_id: int) -> ExternalApiKey:
    return get_key_or_404(db, key_id, PROVIDERS)


def _save(db: Session, record: ExternalApiKey) -> FlightApiKeyOut:
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_key(record)


@router.get("", response_model=ImageApiKeyListResponse)
def list_image_api_keys(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> ImageApiKeyListResponse:
    records = (
        db.query(ExternalApiKey)
        .filter(ExternalApiKey.provider.in_(IMAGE_PROVIDERS))
        .order_by(ExternalApiKey.provider.desc(), ExternalApiKey.priority.asc(), ExternalApiKey.id.asc())
        .all()
    )
    # Mostra a hora atual: chave esgotada na hora anterior já aparece ativa e zerada.
    if any(roll_hour(record) for record in records):
        db.commit()
    settings = get_settings()
    summary: dict[str, Any] = {
        "searches": db.query(func.count(StockImageSearch.id)).scalar() or 0,
        "photos": db.query(func.count(StockImage.id)).scalar() or 0,
        "photo_uses": int(db.query(func.coalesce(func.sum(StockImage.uses), 0)).scalar() or 0),
        "search_reuses": int(db.query(func.coalesce(func.sum(StockImageSearch.uses), 0)).scalar() or 0),
    }
    for provider in IMAGE_PROVIDERS:
        rows = [record for record in records if record.provider == provider]
        active = [record for record in rows if record.is_active and record.status == "active"]
        summary[provider] = {
            "keys": len(rows),
            "active_keys": len(active),
            "hour_usage": sum(int(record.monthly_usage_estimated or 0) for record in rows),
            "hour_limit": sum(int(record.monthly_limit or 0) for record in active),
            "env_key": bool((settings.unsplash_access_key if provider == "unsplash" else settings.pexels_api_key) or ""),
        }
    return ImageApiKeyListResponse(items=[serialize_key(record) for record in records], summary=summary)


@router.post("", response_model=FlightApiKeyOut)
def create_image_api_key(
    payload: ImageApiKeyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    provider = _provider(payload.provider)
    record = ExternalApiKey(
        provider=provider,
        label=payload.label.strip(),
        api_key_encrypted=encrypt_api_key(payload.api_key.strip()),
        api_key_last4=extract_api_key_last4(payload.api_key),
        is_active=payload.is_active,
        status="active" if payload.is_active else "paused",
        priority=max(1, payload.priority or 1),
        monthly_limit=max(1, int(payload.hourly_limit or DEFAULT_HOURLY_LIMIT[provider])),
        monthly_usage_estimated=0,
        notes=payload.notes,
    )
    return _save(db, record)


@router.patch("/{key_id}", response_model=FlightApiKeyOut)
def update_image_api_key(
    key_id: int,
    payload: ImageApiKeyUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    record = _get(db, key_id)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("label"):
        record.label = updates["label"].strip()
    if updates.get("api_key"):
        record.api_key_encrypted = encrypt_api_key(updates["api_key"].strip())
        record.api_key_last4 = extract_api_key_last4(updates["api_key"])
        if record.status == "error":
            record.status = "active" if record.is_active else "paused"
            record.last_error = None
    if updates.get("is_active") is not None:
        record.is_active = bool(updates["is_active"])
        if not record.is_active:
            record.status = "paused"
        elif record.status == "paused":
            record.status = "active"
    if updates.get("priority") is not None:
        record.priority = max(1, int(updates["priority"]))
    if updates.get("hourly_limit") is not None:
        record.monthly_limit = max(1, int(updates["hourly_limit"]))
    if "notes" in updates:
        record.notes = updates["notes"]
    return _save(db, record)


@router.post("/{key_id}/test")
def test_image_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict[str, Any]:
    record = _get(db, key_id)
    try:
        plain_key = decrypt_api_key(record.api_key_encrypted)
    except ApiKeyDecryptionError as exc:
        record.status = "error"
        record.last_error = str(exc)
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    url, params = TEST_URLS[record.provider]
    headers = (
        {"Authorization": f"Client-ID {plain_key}", "Accept-Version": "v1"}
        if record.provider == "unsplash"
        else {"Authorization": plain_key}
    )
    paused = not record.is_active
    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(url, params=params, headers=headers)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Não foi possível falar com o banco de fotos: {exc}") from exc
    record_image_call(db, ImageKey(provider=record.provider, plain_key=plain_key, record=record), response)
    if paused:
        record.status = "paused" if record.status == "active" else record.status
    db.commit()
    if response.status_code in (401, 403):
        raise HTTPException(status_code=400, detail="O banco recusou a chave. Confira se copiou a chave certa.")
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="A chave atingiu o limite desta hora.")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"O banco respondeu com erro {response.status_code}.")
    remaining = response.headers.get("X-Ratelimit-Remaining")
    return {
        "detail": "Chave funcionando.",
        "provider": record.provider,
        "remaining_this_hour": int(remaining) if remaining and remaining.isdigit() else None,
    }


@router.post("/{key_id}/pause", response_model=FlightApiKeyOut)
def pause_image_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    record = _get(db, key_id)
    record.is_active = False
    record.status = "paused"
    return _save(db, record)


@router.post("/{key_id}/activate", response_model=FlightApiKeyOut)
def activate_image_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    record = _get(db, key_id)
    record.is_active = True
    record.status = "active"
    record.last_error = None
    return _save(db, record)


@router.post("/{key_id}/reset-usage", response_model=FlightApiKeyOut)
def reset_image_api_key_usage(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    record = _get(db, key_id)
    record.monthly_usage_estimated = 0
    if record.status in {"exhausted", "error"}:
        record.status = "active" if record.is_active else "paused"
        record.last_error = None
    record.last_used_at = datetime.now(timezone.utc)
    return _save(db, record)


@router.delete("/{key_id}")
def delete_image_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict[str, str]:
    record = _get(db, key_id)
    db.delete(record)
    db.commit()
    return {"detail": "Chave removida."}
