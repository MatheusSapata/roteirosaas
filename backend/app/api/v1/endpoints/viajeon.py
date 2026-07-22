from __future__ import annotations

import json
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from datetime import timedelta
from typing import Any
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency_integration import AgencyIntegration
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.user import User
from app.models.user_session import UserSession
from app.models.viajeon_sso_ticket import ViajeonSsoTicket
from app.api.v1.endpoints.public_pages import _ensure_page_is_publicly_available
from app.services.api_key_crypto import ApiKeyDecryptionError, decrypt_api_key, encrypt_api_key, extract_api_key_last4
from app.services.viajeon import (
    ViajeonAPIError,
    ViajeonClient,
    clear_viajeon_checkout_cache,
    get_cached_viajeon_checkouts,
)
from app.services import auth as auth_service
from app.core.config import get_settings
from app.core.request_ip import get_client_ip
from app.services.session_monitor import summarize_user_agent


router = APIRouter()
public_router = APIRouter()
PROVIDER = "viajeon"
settings = get_settings()


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


class ViajeonSsoEmailIn(BaseModel):
    email: EmailStr


class ViajeonReverseSsoIn(BaseModel):
    email: EmailStr


class ViajeonSsoExchangeIn(BaseModel):
    ticket: str = Field(min_length=32, max_length=255)


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


def _status_payload(integration: AgencyIntegration | None, default_email: str | None = None) -> dict[str, Any]:
    if not integration:
        return {
            "provider": PROVIDER,
            "configured": False,
            "connected": False,
            "status": "disconnected",
            "sso_email": (default_email or "").strip(),
        }
    return {
        "provider": PROVIDER,
        "configured": True,
        "connected": integration.enabled and integration.connection_status == "connected",
        "status": integration.connection_status,
        "token_masked": f"rvo_••••••••{integration.token_last4 or ''}",
        "last_error": integration.last_error,
        "last_tested_at": integration.last_tested_at,
        "sso_email": (integration.sso_email or default_email or "").strip(),
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


def _translate_sso_error(exc: ViajeonAPIError) -> HTTPException:
    messages = {
        "invalid-email": "Informe um email válido.",
        "missing-credentials": "As credenciais Viajeon não foram enviadas. Reconecte a integração.",
        "invalid-credentials": "Reconecte a integração Viajeon.",
        "sso-disabled": "Habilite 'Permitir login via token' no Viajeon.",
        "user-not-in-agency": "Esse email não faz parte da equipe da agência conectada.",
        "user-not-found": "Esse email não tem cadastro no Viajeon.",
    }
    return HTTPException(
        status_code=exc.status_code if 400 <= exc.status_code < 500 else 502,
        detail=messages.get(exc.error, "Não foi possível gerar o login agora. Tente novamente."),
    )


@router.get("/viajeon")
def get_viajeon_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    return _status_payload(_get_integration(db, _agency_id_for_user(db, current_user)), current_user.email)


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
    if not integration.sso_email:
        integration.sso_email = (current_user.email or "").strip() or None
    integration.sso_user_id = current_user.id
    integration.last_error = None
    integration.last_tested_at = datetime.now(timezone.utc)
    db.add(integration)
    db.commit()
    db.refresh(integration)
    clear_viajeon_checkout_cache(integration.id)
    return {**_status_payload(integration, current_user.email), "checkout_count": len(checkouts)}


@router.patch("/viajeon/sso-email")
def update_viajeon_sso_email(
    payload: ViajeonSsoEmailIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    _ensure_write_access(current_user)
    integration = _get_integration(db, _agency_id_for_user(db, current_user))
    if not integration or not integration.enabled:
        raise HTTPException(status_code=409, detail="Conecte a integração Viajeon antes de configurar o email.")
    integration.sso_email = str(payload.email).strip().lower()
    integration.sso_user_id = current_user.id
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return _status_payload(integration, current_user.email)


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


@router.post("/viajeon/sso")
def create_viajeon_sso(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    integration = _get_integration(db, _agency_id_for_user(db, current_user))
    if not integration or not integration.enabled or integration.connection_status != "connected":
        raise HTTPException(status_code=409, detail="Conecte a integração Viajeon para abrir o painel.")
    email = (integration.sso_email or current_user.email or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Informe um email válido.")
    token, secret = _credentials(integration)
    try:
        url = ViajeonClient(token, secret).create_sso_url(email)
    except ViajeonAPIError as exc:
        if exc.error == "invalid-credentials":
            _mark_disconnected(db, integration, exc.error)
        raise _translate_sso_error(exc) from exc
    return {"ok": True, "url": url}


def _reverse_sso_integration(
    db: Session,
    email: str,
    api_token: str,
    api_secret: str,
) -> AgencyIntegration | None:
    candidates = (
        db.query(AgencyIntegration)
        .filter(
            AgencyIntegration.provider == PROVIDER,
            AgencyIntegration.enabled.is_(True),
            AgencyIntegration.connection_status == "connected",
            func.lower(AgencyIntegration.sso_email) == email,
        )
        .all()
    )
    for integration in candidates:
        try:
            stored_token, stored_secret = _credentials(integration)
        except HTTPException:
            continue
        token_ok = hmac.compare_digest(stored_token.encode(), api_token.encode())
        secret_ok = hmac.compare_digest(stored_secret.encode(), api_secret.encode())
        if token_ok and secret_ok:
            return integration
    return None


@public_router.post("/sso", response_model=None)
def create_reverse_viajeon_sso(
    payload: ViajeonReverseSsoIn,
    x_api_token: str | None = Header(default=None, alias="X-Api-Token"),
    x_api_secret: str | None = Header(default=None, alias="X-Api-Secret"),
    db: Session = Depends(get_db),
) -> Any:
    if not x_api_token or not x_api_secret:
        return JSONResponse(status_code=401, content={"ok": False, "error": "missing-credentials"})
    email = str(payload.email).strip().lower()
    integration = _reverse_sso_integration(db, email, x_api_token, x_api_secret)
    if not integration:
        return JSONResponse(status_code=401, content={"ok": False, "error": "invalid-credentials-or-email"})
    if not integration.sso_user_id:
        return JSONResponse(status_code=403, content={"ok": False, "error": "sso-user-not-configured"})
    user = db.query(User).filter(User.id == integration.sso_user_id).first()
    if not user or not user.is_active or (user.status or "active").lower() not in {"active", "pending_agency_setup"}:
        return JSONResponse(status_code=403, content={"ok": False, "error": "user-inactive"})
    membership = db.query(AgencyUser).filter(
        AgencyUser.agency_id == integration.agency_id,
        AgencyUser.user_id == user.id,
    ).first()
    if not membership and user.primary_agency_id != integration.agency_id:
        return JSONResponse(status_code=403, content={"ok": False, "error": "user-not-in-agency"})
    raw_ticket = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(ViajeonSsoTicket(
        token_hash=hashlib.sha256(raw_ticket.encode()).hexdigest(),
        integration_id=integration.id,
        user_id=user.id,
        requested_email=email,
        expires_at=expires_at,
    ))
    db.commit()
    base_url = (settings.webapp_base_url or "https://app.roteiroonline.com").rstrip("/")
    return {
        "ok": True,
        "url": f"{base_url}/sso/viajeon?ticket={raw_ticket}",
        "expires_in": 600,
        "mode": "full",
    }


@public_router.post("/sso/exchange")
def exchange_reverse_viajeon_sso(
    payload: ViajeonSsoExchangeIn,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ticket_hash = hashlib.sha256(payload.ticket.encode()).hexdigest()
    ticket = db.query(ViajeonSsoTicket).filter(ViajeonSsoTicket.token_hash == ticket_hash).with_for_update().first()
    now = datetime.now(timezone.utc)
    if not ticket or ticket.used_at or ticket.expires_at < now:
        raise HTTPException(status_code=401, detail={"error": "invalid-or-expired-ticket"})
    user = db.query(User).filter(User.id == ticket.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=403, detail={"error": "user-inactive"})
    agent_header = (request.headers.get("user-agent") or "").strip()
    device_label, client_name = summarize_user_agent(agent_header)
    session = UserSession(
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=agent_header[:500] or None,
        device_label=device_label,
        client_name=client_name,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(minutes=settings.refresh_token_expire_minutes),
        last_path="/sso/viajeon",
    )
    ticket.used_at = now
    db.add_all([ticket, session])
    db.commit()
    db.refresh(session)
    return {
        "access_token": auth_service.create_access_token(
            {"sub": user.email},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
            session_id=session.id,
        ),
        "refresh_token": auth_service.create_refresh_token(user.email, session.id),
        "token_type": "bearer",
    }


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
