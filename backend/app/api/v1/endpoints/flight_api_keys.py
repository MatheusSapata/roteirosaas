from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.external_api_key import ExternalApiKey
from app.models.flight_lookup_cache import FlightLookupCache
from app.models.user import User
from app.services.aerodatabox_client import (
    AeroDataBoxClient,
    AeroDataBoxClientError,
    AeroDataBoxQuotaExceededError,
)
from app.services.airlabs_client import AirlabsClient, AirlabsClientError, AirlabsQuotaExceededError
from app.services.api_key_crypto import (
    ApiKeyDecryptionError,
    decrypt_api_key,
    encrypt_api_key,
    extract_api_key_last4,
    mask_api_key,
)
from app.services.flight_provider_key_manager import FlightProviderKeyManager

router = APIRouter(prefix="/master/flight-api-keys")

VALID_PROVIDERS = {"airlabs", "aerodatabox"}
VALID_MARKETPLACES = {"rapidapi", "apimarket", "direct"}
VALID_STATUSES = {"active", "paused", "exhausted", "error"}


def _normalize_provider(value: str | None) -> str:
    provider = (value or "").strip().lower() or "aerodatabox"
    if provider not in VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail="Provider invalido.")
    return provider


def _normalize_marketplace(provider: str, value: str | None) -> str | None:
    if value is None:
        if provider == "aerodatabox":
            return "rapidapi"
        if provider == "airlabs":
            return "direct"
        return None
    marketplace = value.strip().lower()
    if not marketplace:
        return None
    if marketplace not in VALID_MARKETPLACES:
        raise HTTPException(status_code=400, detail="Marketplace invalido.")
    return marketplace


def _default_host(provider: str, marketplace: str | None) -> str | None:
    if provider == "aerodatabox" and marketplace == "rapidapi":
        return "aerodatabox.p.rapidapi.com"
    return None


class FlightApiKeyCreate(BaseModel):
    provider: str = Field(default="aerodatabox")
    marketplace: Optional[str] = None
    api_host: Optional[str] = None
    label: str = Field(..., min_length=2, max_length=255)
    api_key: str = Field(..., min_length=4, max_length=500)
    is_active: bool = True
    status: str = "active"
    priority: int = 1
    monthly_limit: Optional[int] = Field(default=None, ge=1)
    reset_day: Optional[int] = Field(default=None, ge=1, le=31)
    notes: Optional[str] = None


class FlightApiKeyUpdate(BaseModel):
    marketplace: Optional[str] = None
    api_host: Optional[str] = None
    label: Optional[str] = Field(default=None, min_length=2, max_length=255)
    api_key: Optional[str] = Field(default=None, min_length=4, max_length=500)
    is_active: Optional[bool] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    monthly_limit: Optional[int] = Field(default=None, ge=1)
    reset_day: Optional[int] = Field(default=None, ge=1, le=31)
    notes: Optional[str] = None


class FlightApiKeyOut(BaseModel):
    id: int
    provider: str
    marketplace: Optional[str]
    api_host: Optional[str]
    label: str
    key_masked: str
    is_active: bool
    status: str
    priority: int
    monthly_limit: int
    monthly_usage_estimated: int
    total_usage_estimated: int
    last_used_at: Optional[datetime]
    last_error: Optional[str]
    reset_day: Optional[int]
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class FlightApiKeyListResponse(BaseModel):
    items: list[FlightApiKeyOut]
    summary: dict[str, Any]


def serialize_key(record: ExternalApiKey) -> FlightApiKeyOut:
    masked = mask_api_key(record.api_key_last4 or "")
    if record.api_key_last4:
        masked = f"**** **** **** {record.api_key_last4}"
    return FlightApiKeyOut(
        id=record.id,
        provider=record.provider,
        marketplace=record.marketplace,
        api_host=record.api_host,
        label=record.label,
        key_masked=masked,
        is_active=bool(record.is_active),
        status=record.status,
        priority=record.priority,
        monthly_limit=record.monthly_limit,
        monthly_usage_estimated=record.monthly_usage_estimated or 0,
        total_usage_estimated=record.total_usage_estimated or 0,
        last_used_at=record.last_used_at,
        last_error=record.last_error,
        reset_day=record.reset_day,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def get_key_or_404(db: Session, key_id: int) -> ExternalApiKey:
    record = db.query(ExternalApiKey).filter(ExternalApiKey.id == key_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Chave de API nao encontrada.")
    return record


@router.get("", response_model=FlightApiKeyListResponse)
def list_flight_api_keys(
    provider: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyListResponse:
    query = db.query(ExternalApiKey)
    normalized_provider = None
    if provider and provider.lower() != "all":
        normalized_provider = _normalize_provider(provider)
        query = query.filter(ExternalApiKey.provider == normalized_provider)

    records = query.order_by(ExternalApiKey.provider.asc(), ExternalApiKey.priority.asc(), ExternalApiKey.id.asc()).all()
    monthly_usage = sum(int(record.monthly_usage_estimated or 0) for record in records)
    monthly_limit = sum(int(record.monthly_limit or 0) for record in records)
    active_keys = [record for record in records if record.is_active and record.status == "active"]
    active_aerodatabox = [record for record in active_keys if record.provider == "aerodatabox"]
    active_airlabs = [record for record in active_keys if record.provider == "airlabs"]
    last_used = [record.last_used_at for record in records if record.last_used_at]

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    cache_entries_month = (
        db.query(FlightLookupCache)
        .filter(FlightLookupCache.updated_at >= month_start)
        .count()
    )

    summary = {
        "provider": normalized_provider or "all",
        "provider_primary": "aerodatabox",
        "marketplace_primary": "rapidapi",
        "active_keys": len(active_keys),
        "active_keys_aerodatabox": len(active_aerodatabox),
        "active_keys_airlabs": len(active_airlabs),
        "monthly_usage_estimated": monthly_usage,
        "monthly_limit": monthly_limit,
        "real_requests_month": monthly_usage,
        "cache_served_estimated": cache_entries_month,
        "last_used_at": max(last_used).isoformat() if last_used else None,
    }
    return FlightApiKeyListResponse(items=[serialize_key(record) for record in records], summary=summary)


@router.post("", response_model=FlightApiKeyOut)
def create_flight_api_key(
    payload: FlightApiKeyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    provider = _normalize_provider(payload.provider)
    status = (payload.status or "active").strip().lower()
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Status invalido.")
    if not payload.is_active and status == "active":
        status = "paused"

    marketplace = _normalize_marketplace(provider, payload.marketplace)
    api_host = (payload.api_host or "").strip() or _default_host(provider, marketplace)
    default_limit = 6000 if provider == "aerodatabox" else 1000

    record = ExternalApiKey(
        provider=provider,
        marketplace=marketplace,
        api_host=api_host,
        label=payload.label.strip(),
        api_key_encrypted=encrypt_api_key(payload.api_key.strip()),
        api_key_last4=extract_api_key_last4(payload.api_key),
        is_active=payload.is_active,
        status=status,
        priority=max(1, payload.priority or 1),
        monthly_limit=max(1, int(payload.monthly_limit or default_limit)),
        reset_day=payload.reset_day,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_key(record)


@router.patch("/{key_id}", response_model=FlightApiKeyOut)
def update_flight_api_key(
    key_id: int,
    payload: FlightApiKeyUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    record = get_key_or_404(db, key_id)
    updates = payload.model_dump(exclude_unset=True)

    if "marketplace" in updates:
        record.marketplace = _normalize_marketplace(record.provider, updates["marketplace"])
    if "api_host" in updates:
        record.api_host = (updates["api_host"] or "").strip() or _default_host(record.provider, record.marketplace)
    if "label" in updates and updates["label"] is not None:
        record.label = updates["label"].strip()
    if "api_key" in updates and updates["api_key"]:
        record.api_key_encrypted = encrypt_api_key(updates["api_key"].strip())
        record.api_key_last4 = extract_api_key_last4(updates["api_key"])
    if "is_active" in updates and updates["is_active"] is not None:
        record.is_active = bool(updates["is_active"])
        if not record.is_active and record.status == "active":
            record.status = "paused"
    if "status" in updates and updates["status"]:
        status = str(updates["status"]).strip().lower()
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="Status invalido.")
        record.status = status
    if "priority" in updates and updates["priority"] is not None:
        record.priority = max(1, int(updates["priority"]))
    if "monthly_limit" in updates and updates["monthly_limit"] is not None:
        record.monthly_limit = max(1, int(updates["monthly_limit"]))
    if "reset_day" in updates:
        record.reset_day = updates["reset_day"]
    if "notes" in updates:
        record.notes = updates["notes"]
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_key(record)


@router.post("/{key_id}/test")
def test_flight_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict[str, Any]:
    record = get_key_or_404(db, key_id)
    try:
        plain_key = decrypt_api_key(record.api_key_encrypted)
    except ApiKeyDecryptionError as exc:
        record.status = "error"
        record.last_error = str(exc)
        db.add(record)
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if record.provider == "aerodatabox":
        client = AeroDataBoxClient()
        try:
            payload = client.test_connection(plain_key)
        except AeroDataBoxQuotaExceededError as exc:
            record.status = "exhausted"
            record.last_error = str(exc)
            db.add(record)
            db.commit()
            raise HTTPException(status_code=429, detail="A chave atingiu o limite da AeroDataBox.") from exc
        except AeroDataBoxClientError as exc:
            record.status = "error"
            record.last_error = str(exc)
            db.add(record)
            db.commit()
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    else:
        client = AirlabsClient()
        try:
            payload = client.test_connection(plain_key)
        except AirlabsQuotaExceededError as exc:
            record.status = "exhausted"
            record.last_error = str(exc)
            db.add(record)
            db.commit()
            raise HTTPException(status_code=429, detail="A chave atingiu o limite da AirLabs.") from exc
        except AirlabsClientError as exc:
            record.status = "error"
            record.last_error = str(exc)
            db.add(record)
            db.commit()
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    record.status = "active" if record.is_active else "paused"
    record.last_error = None
    record.last_used_at = datetime.now(timezone.utc)
    db.add(record)
    db.commit()
    return {
        "detail": "Conexao testada com sucesso.",
        "provider": record.provider,
        "marketplace": record.marketplace,
        "response_sample": payload,
    }


@router.post("/{key_id}/pause", response_model=FlightApiKeyOut)
def pause_flight_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    record = get_key_or_404(db, key_id)
    record.is_active = False
    record.status = "paused"
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_key(record)


@router.post("/{key_id}/activate", response_model=FlightApiKeyOut)
def activate_flight_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    record = get_key_or_404(db, key_id)
    record.is_active = True
    if record.status in {"paused", "error", "exhausted"}:
        record.status = "active"
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_key(record)


@router.post("/{key_id}/reset-usage", response_model=FlightApiKeyOut)
def reset_flight_api_key_usage(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> FlightApiKeyOut:
    record = get_key_or_404(db, key_id)
    manager = FlightProviderKeyManager(db)
    manager.reset_monthly_usage(record)
    db.refresh(record)
    return serialize_key(record)


@router.delete("/{key_id}")
def delete_flight_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict[str, str]:
    record = get_key_or_404(db, key_id)
    db.delete(record)
    db.commit()
    return {"detail": "Chave removida com sucesso."}
