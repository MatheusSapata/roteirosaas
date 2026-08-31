from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_agency_membership
from app.models.agency_integration import AgencyIntegration
from app.models.agency_user import AgencyUser
from app.models.user import User
from app.services.api_key_crypto import ApiKeyDecryptionError, decrypt_api_key, encrypt_api_key, extract_api_key_last4
from app.services.viajechat import ViajeChatClient, ViajeChatClientError

router = APIRouter()
PROVIDER = "viajechat"


class ViajeChatCredentialsIn(BaseModel):
    api_key: str = Field(min_length=8, max_length=500)

    @field_validator("api_key")
    @classmethod
    def clean_key(cls, value: str) -> str:
        return value.strip()


def _agency_id(db: Session, user: User, requested_agency_id: int | None = None) -> int:
    if requested_agency_id:
        require_agency_membership(db=db, agency_id=requested_agency_id, user_id=user.id)
        return int(requested_agency_id)
    if user.primary_agency_id:
        return int(user.primary_agency_id)
    membership = db.query(AgencyUser).filter(AgencyUser.user_id == user.id).order_by(AgencyUser.id.asc()).first()
    if not membership:
        raise HTTPException(status_code=400, detail="Configure uma agência antes de conectar o ViajeChat.")
    return int(membership.agency_id)


def _ensure_write(user: User) -> None:
    if not user.is_superuser and (user.role or "member").strip().lower() == "viewer":
        raise HTTPException(status_code=403, detail="Seu perfil permite apenas visualizar integrações.")


def _integration(db: Session, agency_id: int) -> AgencyIntegration | None:
    return db.query(AgencyIntegration).filter(AgencyIntegration.agency_id == agency_id, AgencyIntegration.provider == PROVIDER).first()


def _status(row: AgencyIntegration | None) -> dict[str, Any]:
    return {
        "provider": PROVIDER,
        "configured": bool(row),
        "connected": bool(row and row.enabled and row.connection_status == "connected"),
        "status": row.connection_status if row else "disconnected",
        "api_key_masked": f"••••••••{row.token_last4 or ''}" if row else None,
        "last_error": row.last_error if row else None,
        "last_tested_at": row.last_tested_at if row else None,
    }


def _columns(pipeline: dict[str, Any]) -> list[dict[str, str]]:
    raw = pipeline.get("columns") or pipeline.get("stages") or pipeline.get("statuses") or []
    if isinstance(raw, dict):
        raw = raw.get("data") or raw.get("items") or []
    if not isinstance(raw, list):
        return []
    return [{"id": str(item.get("id") or item.get("uuid") or ""), "name": str(item.get("name") or item.get("title") or item.get("label") or "Coluna")} for item in raw if isinstance(item, dict)]


def _kanbans(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"id": str(item.get("id") or item.get("uuid") or ""), "name": str(item.get("name") or item.get("title") or item.get("label") or "Kanban"), "columns": _columns(item)} for item in rows]


def _load_key(row: AgencyIntegration) -> str:
    try:
        return decrypt_api_key(row.token_encrypted)
    except ApiKeyDecryptionError as exc:
        raise HTTPException(status_code=503, detail="Não foi possível ler a API key. Reconecte o ViajeChat.") from exc


@router.get("/viajechat")
def status(agency_id: int | None = Query(None, alias="agencyId"), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    return _status(_integration(db, _agency_id(db, current_user, agency_id)))


@router.put("/viajechat")
def connect(payload: ViajeChatCredentialsIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    _ensure_write(current_user)
    try:
        pipelines = ViajeChatClient(payload.api_key).list_pipelines()
    except ViajeChatClientError as exc:
        raise HTTPException(status_code=401, detail="API key do ViajeChat inválida ou sem permissão para acessar os kanbans.") from exc
    row = _integration(db, _agency_id(db, current_user)) or AgencyIntegration(agency_id=_agency_id(db, current_user), provider=PROVIDER)
    row.token_encrypted = encrypt_api_key(payload.api_key)
    row.secret_encrypted = encrypt_api_key("viajechat-api-key")
    row.token_last4 = extract_api_key_last4(payload.api_key)
    row.enabled = True; row.connection_status = "connected"; row.last_error = None; row.last_tested_at = datetime.now(timezone.utc)
    db.add(row); db.commit(); db.refresh(row)
    return {**_status(row), "kanbans": _kanbans(pipelines)}


@router.get("/viajechat/kanbans")
def kanbans(agency_id: int | None = Query(None, alias="agencyId"), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    row = _integration(db, _agency_id(db, current_user, agency_id))
    if not row or not row.enabled:
        raise HTTPException(status_code=404, detail="Integração ViajeChat não configurada.")
    try:
        pipelines = ViajeChatClient(_load_key(row)).list_pipelines()
    except ViajeChatClientError as exc:
        row.connection_status = "disconnected"; row.last_error = "Falha ao consultar kanbans"; row.last_tested_at = datetime.now(timezone.utc); db.add(row); db.commit()
        raise HTTPException(status_code=502, detail="Não foi possível consultar os kanbans do ViajeChat.") from exc
    row.connection_status = "connected"; row.last_error = None; row.last_tested_at = datetime.now(timezone.utc); db.add(row); db.commit()
    return {"kanbans": _kanbans(pipelines)}


@router.delete("/viajechat", status_code=204)
def disconnect(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> None:
    _ensure_write(current_user)
    row = _integration(db, _agency_id(db, current_user))
    if row:
        db.delete(row); db.commit()
