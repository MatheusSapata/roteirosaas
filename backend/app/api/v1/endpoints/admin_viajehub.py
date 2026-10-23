"""Admin Master: conexão com o funil do ViajeHub (endereço e chave do Roteiro Online).

Fica no banco, criptografada em external_api_keys (provedor "viajehub"), para não depender do
.env da VPS. Sem nada salvo aqui, o envio usa HUB_FUNNEL_URL e HUB_FUNNEL_KEY do ambiente.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.external_api_key import ExternalApiKey
from app.models.user import User
from app.services import hub_funnel
from app.services.api_key_crypto import encrypt_api_key, extract_api_key_last4, mask_api_key

router = APIRouter(prefix="/admin-master/viajehub")


class ViajeHubConnectionOut(BaseModel):
    url: str = ""
    key_masked: str = ""
    has_key: bool = False
    source: str = ""


class ViajeHubConnectionIn(BaseModel):
    url: str = Field(..., min_length=8, max_length=255)
    # Vazio mantém a chave já salva.
    key: Optional[str] = Field(default=None, max_length=500)


class ViajeHubTestOut(BaseModel):
    ok: bool
    message: str


def _record(db: Session) -> ExternalApiKey | None:
    return (
        db.query(ExternalApiKey)
        .filter(ExternalApiKey.provider == hub_funnel.PROVIDER)
        .order_by(ExternalApiKey.id.desc())
        .first()
    )


def _clean_url(value: str) -> str:
    url = value.strip()
    if url.upper().startswith("POST "):
        url = url[5:].strip()
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="O endereço deve começar com https://.")
    return url


def _out(db: Session) -> ViajeHubConnectionOut:
    record = _record(db)
    _, _, source = hub_funnel.hub_config()
    if record:
        return ViajeHubConnectionOut(
            url=record.api_host or "",
            key_masked=mask_api_key(record.api_key_last4),
            has_key=True,
            source=source,
        )
    return ViajeHubConnectionOut(source=source)


@router.get("", response_model=ViajeHubConnectionOut)
def get_connection(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> ViajeHubConnectionOut:
    return _out(db)


@router.put("", response_model=ViajeHubConnectionOut)
def save_connection(
    payload: ViajeHubConnectionIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> ViajeHubConnectionOut:
    url = _clean_url(payload.url)
    key = "".join((payload.key or "").split())
    record = _record(db)
    if not record and not key:
        raise HTTPException(status_code=400, detail="Informe a chave do Roteiro Online.")
    if not record:
        record = ExternalApiKey(provider=hub_funnel.PROVIDER, label="ViajeHub · funil", monthly_limit=0)
    record.api_host = url
    if key:
        record.api_key_encrypted = encrypt_api_key(key)
        record.api_key_last4 = extract_api_key_last4(key)
    record.is_active = True
    record.status = "active"
    db.add(record)
    db.commit()
    hub_funnel.clear_config_cache()
    return _out(db)


@router.delete("", response_model=ViajeHubConnectionOut)
def delete_connection(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> ViajeHubConnectionOut:
    record = _record(db)
    if record:
        db.delete(record)
        db.commit()
    hub_funnel.clear_config_cache()
    return _out(db)


@router.post("/test", response_model=ViajeHubTestOut)
def test_connection(
    _: User = Depends(get_current_superuser),
) -> ViajeHubTestOut:
    hub_funnel.clear_config_cache()
    url, key, _source = hub_funnel.hub_config()
    if not url or not key:
        return ViajeHubTestOut(ok=False, message="Salve o endereço e a chave antes de testar.")
    ok, message = hub_funnel.check_connection(url, key)
    return ViajeHubTestOut(ok=ok, message=message)
