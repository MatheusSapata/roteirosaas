from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_superuser, get_db
from app.core.request_ip import get_client_ip
from app.models.user import User
from app.schemas.checkout import (
    CheckoutCardStartRequest,
    CheckoutPasswordRequest,
    CheckoutPasswordResponse,
    CheckoutPublicConfigOut,
    CheckoutSessionCreate,
    CheckoutSessionOut,
    CheckoutSettingsOut,
    CheckoutSettingsUpdate,
    CheckoutTrackEventIn,
    CheckoutTrackEventOut,
    CheckoutTrackingDocumentDetailOut,
    CheckoutTrackingItemOut,
)
from app.services.checkout import (
    coerce_checkout_http_error,
    create_checkout_session,
    create_upgrade_checkout_session,
    define_password_for_paid_checkout,
    get_checkout_session_by_token,
    get_checkout_settings,
    list_checkout_tracking,
    get_checkout_tracking_document_detail,
    refresh_session_status,
    resolve_offer,
    resolve_offer_checkout,
    serialize_checkout_session,
    serialize_checkout_settings,
    start_card_payment,
    start_pix_payment,
    track_checkout_event,
    update_checkout_settings,
)

router = APIRouter()
admin_router = APIRouter(prefix="/admin/checkout-settings")


class CheckoutConfigResponse(CheckoutPublicConfigOut):
    pass


class CheckoutSessionTokenIn(BaseModel):
    token: str


class CheckoutUpgradeSessionCreateIn(BaseModel):
    offer_key: str
    coupon_code: str | None = None


@admin_router.get("", response_model=CheckoutSettingsOut)
def get_admin_checkout_settings(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> CheckoutSettingsOut:
    return CheckoutSettingsOut.model_validate(serialize_checkout_settings(get_checkout_settings(db)))


@admin_router.put("", response_model=CheckoutSettingsOut)
def save_admin_checkout_settings(
    payload: CheckoutSettingsUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> CheckoutSettingsOut:
    record = update_checkout_settings(db, payload)
    return CheckoutSettingsOut.model_validate(serialize_checkout_settings(record))


@admin_router.get("/tracking", response_model=list[CheckoutTrackingItemOut])
def list_admin_checkout_tracking(
    offer_key: str | None = None,
    limit: int = 200,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> list[CheckoutTrackingItemOut]:
    rows = list_checkout_tracking(db, offer_key=offer_key, limit=limit)
    return [CheckoutTrackingItemOut.model_validate(item) for item in rows]


@admin_router.get("/tracking/document/{customer_document}", response_model=CheckoutTrackingDocumentDetailOut)
def get_admin_checkout_tracking_document(
    customer_document: str,
    offer_key: str | None = None,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> CheckoutTrackingDocumentDetailOut:
    payload = get_checkout_tracking_document_detail(db, customer_document=customer_document, offer_key=offer_key)
    return CheckoutTrackingDocumentDetailOut.model_validate(payload)


@router.get("/public/config/{offer_key}", response_model=CheckoutConfigResponse)
def get_public_checkout_config(offer_key: str, db: Session = Depends(get_db)) -> CheckoutConfigResponse:
    settings = get_checkout_settings(db)
    offer = resolve_offer(db, offer_key)
    checkout = resolve_offer_checkout(settings, offer)
    return CheckoutConfigResponse(
        theme_mode=checkout.theme_mode,
        desktop_image_url=checkout.desktop_image_url,
        mobile_banner_url=checkout.mobile_banner_url,
        offer=offer,
    )


@router.post("/public/session", response_model=CheckoutSessionOut, status_code=status.HTTP_201_CREATED)
def create_public_checkout_session(payload: CheckoutSessionCreate, db: Session = Depends(get_db)) -> CheckoutSessionOut:
    offer = resolve_offer(db, payload.offer_key)
    session = create_checkout_session(
        db,
        offer=offer,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        customer_document=payload.customer_document,
        customer_phone=payload.customer_phone,
        customer_zipcode=payload.customer_zipcode,
        coupon_code=payload.coupon_code,
        metadata=payload.metadata,
    )
    return CheckoutSessionOut.model_validate(serialize_checkout_session(db, session))


@router.post("/public/session/upgrade", response_model=CheckoutSessionOut, status_code=status.HTTP_201_CREATED)
def create_public_upgrade_checkout_session(
    payload: CheckoutUpgradeSessionCreateIn,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CheckoutSessionOut:
    offer = resolve_offer(db, payload.offer_key)
    session = create_upgrade_checkout_session(
        db,
        offer=offer,
        user=current_user,
        coupon_code=payload.coupon_code,
    )
    return CheckoutSessionOut.model_validate(serialize_checkout_session(db, session))


@router.get("/public/session/{token}", response_model=CheckoutSessionOut)
def get_public_checkout_session(token: str, db: Session = Depends(get_db)) -> CheckoutSessionOut:
    session = get_checkout_session_by_token(db, token)
    return CheckoutSessionOut.model_validate(serialize_checkout_session(db, session))


@router.post("/public/session/{token}/refresh", response_model=CheckoutSessionOut)
def refresh_public_checkout_session(token: str, db: Session = Depends(get_db)) -> CheckoutSessionOut:
    session = get_checkout_session_by_token(db, token)
    session = refresh_session_status(db, session)
    return CheckoutSessionOut.model_validate(serialize_checkout_session(db, session))


@router.post("/public/session/{token}/pix", response_model=CheckoutSessionOut)
def begin_pix_checkout(token: str, db: Session = Depends(get_db)) -> CheckoutSessionOut:
    session = get_checkout_session_by_token(db, token)
    try:
        session = start_pix_payment(db, session)
    except Exception as exc:  # noqa: BLE001
        raise coerce_checkout_http_error(exc) from exc
    return CheckoutSessionOut.model_validate(serialize_checkout_session(db, session))


@router.post("/public/session/{token}/card", response_model=CheckoutSessionOut)
def begin_card_checkout(
    token: str,
    payload: CheckoutCardStartRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> CheckoutSessionOut:
    session = get_checkout_session_by_token(db, token)
    if payload.token != token:
        raise HTTPException(status_code=400, detail="Token de sessao invalido.")
    body = payload.model_dump()
    body["remote_ip"] = payload.remote_ip or get_client_ip(request) or "127.0.0.1"
    try:
        session = start_card_payment(db, session, body)
    except Exception as exc:  # noqa: BLE001
        raise coerce_checkout_http_error(exc) from exc
    return CheckoutSessionOut.model_validate(serialize_checkout_session(db, session))


@router.post("/public/session/{token}/track", response_model=CheckoutTrackEventOut)
def track_public_checkout_event(
    token: str,
    payload: CheckoutTrackEventIn,
    request: Request,
    db: Session = Depends(get_db),
) -> CheckoutTrackEventOut:
    session = get_checkout_session_by_token(db, token)
    track_checkout_event(
        db,
        session=session,
        event_name=payload.event_name,
        step=payload.step,
        status=payload.status,
        payment_method=payload.payment_method,
        duration_ms=payload.duration_ms,
        error_message=payload.error_message,
        metadata=payload.metadata,
        ip_address_value=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return CheckoutTrackEventOut(ok=True)


@router.post("/public/session/{token}/password", response_model=CheckoutPasswordResponse)
def finish_checkout_password(
    token: str,
    payload: CheckoutPasswordRequest,
    db: Session = Depends(get_db),
) -> CheckoutPasswordResponse:
    if payload.token != token:
        raise HTTPException(status_code=400, detail="Token de sessao invalido.")
    user = define_password_for_paid_checkout(db, token, payload.password)
    return CheckoutPasswordResponse(detail="Senha definida com sucesso.", email=user.email)
