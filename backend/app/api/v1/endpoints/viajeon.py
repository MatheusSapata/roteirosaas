from __future__ import annotations

import json
import base64
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency_integration import AgencyIntegration
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.user import User
from app.api.v1.endpoints.public_pages import _ensure_page_is_publicly_available
from app.services.api_key_crypto import ApiKeyDecryptionError, decrypt_api_key, encrypt_api_key, extract_api_key_last4
from app.services.viajeon import (
    ViajeonAPIError,
    ViajeonClient,
    clear_viajeon_checkout_cache,
    get_cached_viajeon_checkouts,
)


router = APIRouter()
public_router = APIRouter()
PROVIDER = "viajeon"


class ViajeonCredentialsIn(BaseModel):
    token: str = Field(min_length=8, max_length=255)
    secret: str = Field(min_length=8, max_length=255)

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        clean = value.strip()
        if not clean.startswith("rvo_"):
            raise ValueError("Token Viajeon inválido.")
        return clean

    @field_validator("secret")
    @classmethod
    def validate_secret(cls, value: str) -> str:
        clean = value.strip()
        if not clean.startswith("rvs_"):
            raise ValueError("Secret Viajeon inválido.")
        return clean


class ViajeonSessionItemIn(BaseModel):
    package_id: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1, le=999)


class ViajeonCustomerIn(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)


class ViajeonUtmIn(BaseModel):
    utm_source: str | None = Field(default=None, max_length=255)
    utm_medium: str | None = Field(default=None, max_length=255)
    utm_campaign: str | None = Field(default=None, max_length=255)
    utm_term: str | None = Field(default=None, max_length=255)
    utm_content: str | None = Field(default=None, max_length=255)


class ViajeonPublicSessionIn(BaseModel):
    items: list[ViajeonSessionItemIn] = Field(min_length=1, max_length=50)
    utm: ViajeonUtmIn | None = None
    customer: ViajeonCustomerIn | None = None


def _agency_id_for_user(db: Session, user: User) -> int:
    if user.primary_agency_id:
        return int(user.primary_agency_id)
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.user_id == user.id)
        .order_by(AgencyUser.id.asc())
        .first()
    )
    if not membership:
        raise HTTPException(status_code=400, detail="Configure uma agência antes de conectar o Viajeon.")
    return int(membership.agency_id)


def _ensure_write_access(user: User) -> None:
    if user.is_superuser:
        return
    if (user.role or "member").strip().lower() == "viewer":
        raise HTTPException(status_code=403, detail="Seu perfil permite apenas visualizar integrações.")


def _get_integration(db: Session, agency_id: int) -> AgencyIntegration | None:
    return (
        db.query(AgencyIntegration)
        .filter(AgencyIntegration.agency_id == agency_id, AgencyIntegration.provider == PROVIDER)
        .first()
    )


def _status_payload(integration: AgencyIntegration | None) -> dict[str, Any]:
    if not integration:
        return {"provider": PROVIDER, "configured": False, "connected": False, "status": "disconnected"}
    return {
        "provider": PROVIDER,
        "configured": True,
        "connected": integration.enabled and integration.connection_status == "connected",
        "status": integration.connection_status,
        "token_masked": f"rvo_••••••••{integration.token_last4 or ''}",
        "last_error": integration.last_error,
        "last_tested_at": integration.last_tested_at,
    }


def _credentials(integration: AgencyIntegration) -> tuple[str, str]:
    try:
        return decrypt_api_key(integration.token_encrypted), decrypt_api_key(integration.secret_encrypted)
    except ApiKeyDecryptionError as exc:
        raise HTTPException(status_code=503, detail="Não foi possível ler as credenciais do Viajeon. Reconecte a integração.") from exc


def _mark_disconnected(db: Session, integration: AgencyIntegration, error: str) -> None:
    integration.connection_status = "disconnected"
    integration.last_error = error[:500]
    integration.last_tested_at = datetime.now(timezone.utc)
    db.add(integration)
    db.commit()
    clear_viajeon_checkout_cache(integration.id)


def _record_test_error(db: Session, integration: AgencyIntegration, error: str) -> None:
    integration.last_error = error[:500]
    integration.last_tested_at = datetime.now(timezone.utc)
    db.add(integration)
    db.commit()


def _translate_error(exc: ViajeonAPIError) -> HTTPException:
    if exc.status_code == 401:
        return HTTPException(status_code=401, detail="Credenciais Viajeon inválidas ou desativadas.")
    if exc.error == "viajeon-unavailable":
        return HTTPException(status_code=502, detail="O Viajeon está temporariamente indisponível.")
    return HTTPException(status_code=502, detail=f"Erro ao comunicar com o Viajeon: {exc.error}")


@router.get("/viajeon")
def get_viajeon_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    return _status_payload(_get_integration(db, _agency_id_for_user(db, current_user)))


@router.put("/viajeon")
def connect_viajeon(
    payload: ViajeonCredentialsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    _ensure_write_access(current_user)
    agency_id = _agency_id_for_user(db, current_user)
    try:
        checkouts = ViajeonClient(payload.token, payload.secret).list_checkouts()
    except ViajeonAPIError as exc:
        raise _translate_error(exc) from exc

    integration = _get_integration(db, agency_id)
    if not integration:
        integration = AgencyIntegration(agency_id=agency_id, provider=PROVIDER)
    integration.token_encrypted = encrypt_api_key(payload.token)
    integration.secret_encrypted = encrypt_api_key(payload.secret)
    integration.token_last4 = extract_api_key_last4(payload.token)
    integration.enabled = True
    integration.connection_status = "connected"
    integration.last_error = None
    integration.last_tested_at = datetime.now(timezone.utc)
    db.add(integration)
    db.commit()
    db.refresh(integration)
    clear_viajeon_checkout_cache(integration.id)
    return {**_status_payload(integration), "checkout_count": len(checkouts)}


@router.post("/viajeon/test")
def test_viajeon(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    integration = _get_integration(db, _agency_id_for_user(db, current_user))
    if not integration or not integration.enabled:
        raise HTTPException(status_code=404, detail="Integração Viajeon não configurada.")
    token, secret = _credentials(integration)
    try:
        rows = get_cached_viajeon_checkouts(integration.id, token, secret, force_refresh=True)
    except ViajeonAPIError as exc:
        if exc.status_code == 401:
            _mark_disconnected(db, integration, exc.error)
        else:
            _record_test_error(db, integration, exc.error)
        raise _translate_error(exc) from exc
    integration.connection_status = "connected"
    integration.last_error = None
    integration.last_tested_at = datetime.now(timezone.utc)
    db.add(integration)
    db.commit()
    return {"ok": True, "checkout_count": len(rows)}


@router.delete("/viajeon")
def disconnect_viajeon(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, bool]:
    _ensure_write_access(current_user)
    integration = _get_integration(db, _agency_id_for_user(db, current_user))
    if integration:
        clear_viajeon_checkout_cache(integration.id)
        db.delete(integration)
        db.commit()
    return {"ok": True}


@router.get("/viajeon/checkouts")
def list_viajeon_checkouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    integration = _get_integration(db, _agency_id_for_user(db, current_user))
    if not integration or not integration.enabled or integration.connection_status != "connected":
        raise HTTPException(status_code=409, detail="Conecte o Viajeon para consultar os checkouts.")
    token, secret = _credentials(integration)
    try:
        rows = get_cached_viajeon_checkouts(integration.id, token, secret)
    except ViajeonAPIError as exc:
        if exc.status_code == 401:
            _mark_disconnected(db, integration, exc.error)
        raise _translate_error(exc) from exc
    if not rows:
        rows = _recover_agency_checkout_snapshots(db, integration.agency_id, token, secret)
    return {"ok": True, "checkouts": rows}


def _parse_page_config(page: Page) -> dict[str, Any]:
    raw = page.config_json
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = {}
    return raw if isinstance(raw, dict) else {}


def _recover_agency_checkout_snapshots(
    db: Session,
    agency_id: int,
    token: str,
    secret: str,
) -> list[dict[str, Any]]:
    recovered: dict[str, dict[str, Any]] = {}
    client = ViajeonClient(token, secret)
    pages = db.query(Page).filter(Page.agency_id == agency_id).all()
    for page in pages:
        for section in _parse_page_config(page).get("sections") or []:
            if not isinstance(section, dict) or section.get("type") != "viajeon_checkout":
                continue
            snapshot = section.get("checkoutSnapshot")
            if not isinstance(snapshot, dict):
                continue
            checkout_id = str(snapshot.get("checkout_id") or "")
            if not checkout_id or checkout_id in recovered:
                continue
            checkout_url = str(snapshot.get("checkout_url") or "").strip()
            if not checkout_url and snapshot.get("slug"):
                checkout_url = f"https://app.viajeon.com/checkout/{snapshot['slug']}"
            if checkout_url:
                try:
                    recovered[checkout_id] = client.get_public_checkout_by_url(checkout_url)
                    continue
                except ViajeonAPIError:
                    pass
            if isinstance(snapshot.get("packages"), list) and snapshot.get("packages"):
                recovered[checkout_id] = snapshot
    return list(recovered.values())


def _viajeon_section(page: Page, section_id: str) -> dict[str, Any]:
    for section in _parse_page_config(page).get("sections") or []:
        if not isinstance(section, dict):
            continue
        if section.get("type") != "viajeon_checkout" or section.get("enabled") is False:
            continue
        if str(section.get("anchorId") or "") == section_id:
            return section
    raise HTTPException(status_code=404, detail="Seção Viajeon não encontrada nesta página.")


def _public_context(db: Session, page_id: int, section_id: str) -> tuple[Page, dict[str, Any], AgencyIntegration, str, str]:
    page = db.query(Page).filter(Page.id == page_id, Page.status == "published").first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada ou não publicada.")
    _ensure_page_is_publicly_available(page)
    section = _viajeon_section(page, section_id)
    integration = _get_integration(db, page.agency_id)
    if not integration or not integration.enabled or integration.connection_status != "connected":
        raise HTTPException(status_code=503, detail="Integração Viajeon indisponível.")
    token, secret = _credentials(integration)
    return page, section, integration, token, secret


def _selected_checkout(rows: list[dict[str, Any]], checkout_id: str) -> dict[str, Any]:
    checkout = next((row for row in rows if row.get("checkout_id") == checkout_id), None)
    if not checkout:
        raise HTTPException(status_code=404, detail="O checkout Viajeon selecionado não está mais ativo.")
    return checkout


def _selected_checkout_or_snapshot(
    rows: list[dict[str, Any]], section: dict[str, Any]
) -> dict[str, Any]:
    checkout_id = str(section.get("checkoutId") or "")
    checkout = next((row for row in rows if row.get("checkout_id") == checkout_id), None)
    if checkout:
        return checkout
    snapshot = section.get("checkoutSnapshot")
    if (
        isinstance(snapshot, dict)
        and str(snapshot.get("checkout_id") or "") == checkout_id
        and isinstance(snapshot.get("packages"), list)
        and snapshot.get("packages")
    ):
        return snapshot
    raise HTTPException(status_code=404, detail="O checkout Viajeon selecionado não está mais disponível.")


def _checkout_prefill_url(checkout: dict[str, Any], items: list[dict[str, Any]], customer: dict[str, Any] | None) -> str:
    raw_url = str(checkout.get("checkout_url") or "").strip()
    if not raw_url:
        slug = str(checkout.get("slug") or "").strip()
        raw_url = f"https://app.viajeon.com/checkout/{slug}" if slug else ""
    parsed = urlparse(raw_url)
    if parsed.scheme != "https" or parsed.hostname != "app.viajeon.com" or not parsed.path.startswith("/checkout/"):
        raise HTTPException(status_code=502, detail="O link do checkout Viajeon é inválido.")
    prefill: dict[str, Any] = {
        "qty": {item["package_id"]: item["quantity"] for item in items},
    }
    if customer:
        prefill["buyer"] = customer
    encoded = base64.b64encode(json.dumps(prefill, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode("ascii")
    separator = "&" if parsed.query else "?"
    return f"{raw_url}{separator}{urlencode({'prefill': encoded})}"


@public_router.get("/pages/{page_id}/sections/{section_id}")
def get_public_viajeon_section(page_id: int, section_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    _, section, integration, token, secret = _public_context(db, page_id, section_id)
    try:
        rows = get_cached_viajeon_checkouts(integration.id, token, secret)
    except ViajeonAPIError as exc:
        if exc.status_code == 401:
            _mark_disconnected(db, integration, exc.error)
        raise _translate_error(exc) from exc
    checkout = _selected_checkout_or_snapshot(rows, section)
    return {"ok": True, "checkout": checkout}


@public_router.post("/pages/{page_id}/sections/{section_id}/sessions")
def create_public_viajeon_session(
    page_id: int,
    section_id: str,
    payload: ViajeonPublicSessionIn,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _, section, integration, token, secret = _public_context(db, page_id, section_id)
    try:
        rows = get_cached_viajeon_checkouts(integration.id, token, secret)
        checkout = _selected_checkout_or_snapshot(rows, section)
        packages = {str(item.get("id")): item for item in checkout.get("packages") or []}
        normalized_items: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in payload.items:
            if item.package_id in seen:
                raise HTTPException(status_code=400, detail="Um pacote foi enviado mais de uma vez.")
            seen.add(item.package_id)
            package = packages.get(item.package_id)
            if not package:
                raise HTTPException(status_code=400, detail="Um dos pacotes selecionados não está mais disponível.")
            maximum = int(package.get("max_quantity") or 1)
            minimum = int(package.get("min_quantity") or 0)
            if item.quantity > maximum:
                raise HTTPException(status_code=400, detail=f"Quantidade máxima de {package.get('name')} é {maximum}.")
            if minimum > 0 and item.quantity < minimum:
                raise HTTPException(status_code=400, detail=f"Quantidade mínima de {package.get('name')} é {minimum}.")
            normalized_items.append({"package_id": item.package_id, "quantity": item.quantity})

        customer: dict[str, Any] | None = None
        if payload.customer:
            customer = {key: value for key, value in payload.customer.model_dump().items() if value} or None
        url = _checkout_prefill_url(checkout, normalized_items, customer)
    except ViajeonAPIError as exc:
        if exc.status_code == 401:
            _mark_disconnected(db, integration, exc.error)
        raise _translate_error(exc) from exc
    return {"ok": True, "url": url}
