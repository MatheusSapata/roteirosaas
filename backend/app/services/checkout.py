from __future__ import annotations

import secrets
import json
from ipaddress import ip_address
from urllib.request import Request, urlopen
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, object_session

from app.core.config import get_settings
from app.models.checkout import CheckoutLead, CheckoutSession, CheckoutSettings, CheckoutTrackingEvent
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.checkout import (
    CheckoutAppearanceOut,
    CheckoutCouponOut,
    CheckoutOfferOut,
    CheckoutSettingsUpdate,
)
from app.services import auth as auth_service
from app.services.asaas import AsaasAPIError, AsaasClient, build_default_split_payload
from app.services.trial import end_trial
from app.services.trial import republish_all_user_pages
from app.services.viajechat_checkout_flow import (
    ensure_checkout_contact_at_payment_step,
    mark_signed as mark_viajechat_signed,
)

settings = get_settings()

DEFAULT_CHECKOUTS = [
    {
        "key": "default",
        "name": "Checkout padrão",
        "theme_mode": "dark",
        "desktop_image_url": None,
        "mobile_banner_url": None,
        "active": True,
    }
]

DEFAULT_OFFERS = [
    {
        "key": "profissional",
        "title": "Plano profissional",
        "footer_product_label": "Plano profissional",
        "plan_key": "professional",
        "billing_cycle": "monthly",
        "amount": "49.99",
        "active": True,
        "subtitle": "Acesso completo à plataforma",
        "checkout_key": "default",
    }
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _billing_today() -> str:
    tz_name = settings.trial_tag_job_timezone or "America/Sao_Paulo"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:  # noqa: BLE001
        tz = ZoneInfo("America/Sao_Paulo")
    return datetime.now(tz).date().isoformat()


def _normalize_digits(value: str | None) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _normalize_plan_key(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    aliases = {
        "essencial": "professional",
        "profissional": "professional",
        "professional": "professional",
        "growth": "agency",
        "agencia": "agency",
        "agency": "agency",
        "infinity": "scale",
        "escala": "scale",
        "scale": "scale",
        "teste": "test",
        "test": "test",
    }
    return aliases.get(normalized, normalized or "professional")


def _is_comeco_like_plan(value: str | None) -> bool:
    raw = str(value or "").strip().lower()
    return raw in {"comeco", "free"}


def _duration_from_cycle(cycle: str) -> timedelta:
    return timedelta(days=365 if cycle == "annual" else 30)


def _parse_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _resolve_asaas_cycle(cycle: str) -> str:
    return "YEARLY" if str(cycle).strip().lower() == "annual" else "MONTHLY"


def _extract_asaas_resource_id(resource: Any) -> str | None:
    if isinstance(resource, str):
        value = resource.strip()
        return value or None
    if isinstance(resource, dict):
        value = str(resource.get("id") or "").strip()
        return value or None
    return None


def _resolve_session_subscription_id(session: CheckoutSession) -> str | None:
    metadata = dict(session.metadata_json or {})
    raw = metadata.get("asaas_subscription_id")
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None


def _is_upgrade_session(session: CheckoutSession) -> bool:
    metadata = dict(session.metadata_json or {})
    return bool(metadata.get("upgrade_mode"))


def _resolve_target_subscription_for_upgrade(db: Session, session: CheckoutSession) -> Subscription | None:
    metadata = dict(session.metadata_json or {})
    raw_user_id = metadata.get("target_user_id")
    user: User | None = None
    if raw_user_id is not None:
        try:
            user = db.query(User).filter(User.id == int(raw_user_id)).first()
        except (TypeError, ValueError):
            user = None
    if not user:
        user = session.user or _find_existing_user(db, session.customer_email, session.customer_document)
    if not user:
        return None
    return user.subscription


def _extract_card_last4(number: str | None) -> str | None:
    digits = "".join(ch for ch in str(number or "") if ch.isdigit())
    if len(digits) < 4:
        return None
    return digits[-4:]


def _infer_card_brand(number: str | None) -> str | None:
    digits = "".join(ch for ch in str(number or "") if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("4"):
        return "Visa"
    if len(digits) >= 2 and 51 <= int(digits[:2]) <= 55:
        return "Mastercard"
    if len(digits) >= 4 and 2221 <= int(digits[:4]) <= 2720:
        return "Mastercard"
    if digits.startswith(("34", "37")):
        return "Amex"
    if digits.startswith("6011") or digits.startswith("65") or (
        len(digits) >= 3 and 644 <= int(digits[:3]) <= 649
    ):
        return "Discover"
    if digits.startswith(("6062", "3841")):
        return "Hipercard"
    if digits.startswith(("4011", "4312", "4389")):
        return "Elo"
    return None


def _apply_upgrade_after_payment(db: Session, session: CheckoutSession) -> User:
    subscription = _resolve_target_subscription_for_upgrade(db, session)
    if not subscription or not subscription.asaas_subscription_id:
        raise HTTPException(status_code=400, detail="Assinatura ativa não encontrada para upgrade.")

    client = _ensure_asaas_client()
    payload = {
        "value": float(_parse_decimal(session.amount)),
        "cycle": _resolve_asaas_cycle(session.billing_cycle),
        "status": "ACTIVE",
        "updatePendingPayments": True,
        "externalReference": f"checkout_upgrade:{session.token}",
        "split": build_default_split_payload(),
    }
    client.update_subscription(subscription.asaas_subscription_id, payload)

    user = db.query(User).filter(User.id == subscription.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário da assinatura não encontrado.")
    previous_plan = str(user.plan or "").strip().lower()
    user.plan = session.plan_key
    user.name = session.customer_name or user.name
    user.whatsapp = session.customer_phone or user.whatsapp
    user.address_zipcode = session.customer_zipcode or user.address_zipcode

    subscription.plan = session.plan_key
    subscription.status = "active"
    subscription.billing_cycle = session.billing_cycle
    subscription.payment_method_type = "card"
    metadata = dict(session.metadata_json or {})
    subscription.card_brand = metadata.get("card_brand") or subscription.card_brand
    subscription.card_last4 = metadata.get("card_last4") or subscription.card_last4
    subscription.failed_attempts = 0
    subscription.valid_until = _utcnow() + _duration_from_cycle(session.billing_cycle)
    subscription.asaas_customer_id = session.asaas_customer_id or subscription.asaas_customer_id
    subscription.external_reference = f"checkout_upgrade:{session.token}"
    subscription.mrr_amount = (
        _parse_decimal(session.amount) / Decimal("12")
        if session.billing_cycle == "annual"
        else _parse_decimal(session.amount)
    )
    end_trial(user, db, keep_plan=session.plan_key)
    if not _is_comeco_like_plan(session.plan_key):
        republish_all_user_pages(user, db)
    db.add_all([user, subscription])
    db.commit()
    db.refresh(user)
    # Keep agency creation explicit; do not auto-create here.
    mark_viajechat_signed(
        name=session.customer_name,
        email=session.customer_email,
        phone=session.customer_phone,
        offer_key=session.offer_key,
        upgrade_mode=True,
        contact_id=str((dict(session.metadata_json or {}).get("viajechat_contact_id") or "")).strip() or None,
    )
    return user


def _legacy_checkout_payload(record: CheckoutSettings) -> dict[str, Any]:
    return {
        "key": "default",
        "name": "Checkout padrão",
        "theme_mode": record.theme_mode or "dark",
        "desktop_image_url": record.desktop_image_url,
        "mobile_banner_url": record.mobile_banner_url,
        "active": True,
    }


def _serialize_checkouts(record: CheckoutSettings) -> list[dict[str, Any]]:
    raw_items = record.checkouts_json or []
    if not raw_items:
        raw_items = [_legacy_checkout_payload(record)]
    return [CheckoutAppearanceOut.model_validate(item).model_dump(mode="json") for item in raw_items]


def _serialize_offers(record: CheckoutSettings) -> list[dict[str, Any]]:
    raw_items = record.offers_json or DEFAULT_OFFERS
    checkouts = _serialize_checkouts(record)
    available_checkout_keys = {item["key"] for item in checkouts if item.get("active")}
    fallback_checkout_key = next((item["key"] for item in checkouts if item.get("active")), None)
    offers: list[dict[str, Any]] = []
    for item in raw_items:
        payload = dict(item or {})
        if not payload.get("checkout_key"):
            payload["checkout_key"] = fallback_checkout_key
        if payload.get("checkout_key") not in available_checkout_keys and fallback_checkout_key:
            payload["checkout_key"] = fallback_checkout_key
        offers.append(CheckoutOfferOut.model_validate(payload).model_dump(mode="json"))
    return offers


def _serialize_coupons(record: CheckoutSettings) -> list[dict[str, Any]]:
    raw_items = record.coupons_json or []
    db = object_session(record)
    usage_rows = (
        db.query(CheckoutSession.coupon_code, func.count(CheckoutSession.id))
        .filter(CheckoutSession.coupon_code.isnot(None))
        .group_by(CheckoutSession.coupon_code)
        .all()
        if db is not None
        else []
    )
    usage_map = {str(code).upper(): int(total) for code, total in usage_rows if code}
    coupons: list[dict[str, Any]] = []
    for item in raw_items:
        payload = dict(item or {})
        payload["usage_count"] = usage_map.get(str(payload.get("code") or "").upper(), 0)
        coupons.append(CheckoutCouponOut.model_validate(payload).model_dump(mode="json"))
    return coupons


def get_checkout_settings(db: Session) -> CheckoutSettings:
    record = db.query(CheckoutSettings).order_by(CheckoutSettings.id.asc()).first()
    if record:
        return record
    record = CheckoutSettings(
        theme_mode="dark",
        is_active=True,
        offers_json=DEFAULT_OFFERS,
        coupons_json=[],
        checkouts_json=DEFAULT_CHECKOUTS,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_checkout_settings(db: Session, payload: CheckoutSettingsUpdate) -> CheckoutSettings:
    record = get_checkout_settings(db)
    checkouts = [item.model_dump(mode="json") for item in payload.checkouts]
    active_checkouts = [item for item in checkouts if item.get("active")]
    if not active_checkouts and checkouts:
        checkouts[0]["active"] = True
        active_checkouts = [checkouts[0]]

    fallback_checkout_key = active_checkouts[0]["key"] if active_checkouts else "default"
    offers = []
    for item in payload.offers:
        raw_offer = item.model_dump(mode="json")
        raw_offer["checkout_key"] = raw_offer.get("checkout_key") or fallback_checkout_key
        offers.append(raw_offer)

    record.is_active = payload.is_active
    record.offers_json = offers
    record.coupons_json = [item.model_dump(mode="json") for item in payload.coupons]
    record.checkouts_json = checkouts
    if active_checkouts:
        primary = active_checkouts[0]
        record.theme_mode = primary["theme_mode"]
        record.desktop_image_url = primary.get("desktop_image_url")
        record.mobile_banner_url = primary.get("mobile_banner_url")
    record.updated_at = _utcnow()
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def serialize_checkout_settings(record: CheckoutSettings) -> dict[str, Any]:
    return {
        "id": record.id,
        "is_active": bool(record.is_active),
        "offers": _serialize_offers(record),
        "coupons": _serialize_coupons(record),
        "checkouts": _serialize_checkouts(record),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def resolve_offer(db: Session, offer_key: str) -> CheckoutOfferOut:
    record = get_checkout_settings(db)
    if not record.is_active:
        raise HTTPException(status_code=404, detail="Checkout desativado.")
    normalized_key = offer_key.strip().lower()
    for raw in _serialize_offers(record):
        offer = CheckoutOfferOut.model_validate(raw)
        if offer.active and offer.key == normalized_key:
            return offer
    raise HTTPException(status_code=404, detail="Oferta não encontrada.")


def resolve_offer_checkout(record: CheckoutSettings, offer: CheckoutOfferOut) -> CheckoutAppearanceOut:
    active_checkouts = [CheckoutAppearanceOut.model_validate(item) for item in _serialize_checkouts(record) if item.get("active")]
    if not active_checkouts:
        return CheckoutAppearanceOut.model_validate(_legacy_checkout_payload(record))
    if offer.checkout_key:
        for checkout in active_checkouts:
            if checkout.key == offer.checkout_key:
                return checkout
    return active_checkouts[0]


def resolve_coupon(record: CheckoutSettings, coupon_code: str | None, offer_key: str) -> CheckoutCouponOut | None:
    normalized_code = str(coupon_code or "").strip().upper()
    if not normalized_code:
        return None
    normalized_offer_key = offer_key.strip().lower()
    for raw in _serialize_coupons(record):
        coupon = CheckoutCouponOut.model_validate(raw)
        if not coupon.active or coupon.code != normalized_code:
            continue
        if coupon.offer_keys and normalized_offer_key not in coupon.offer_keys:
            raise HTTPException(status_code=400, detail="Cupom inválido para esta oferta.")
        return coupon
    raise HTTPException(status_code=400, detail="Cupom não encontrado ou inativo.")


def apply_coupon_to_offer_amount(offer: CheckoutOfferOut, coupon: CheckoutCouponOut | None) -> tuple[Decimal, Decimal, Decimal | None]:
    original_amount = _quantize_money(_parse_decimal(offer.amount))
    if not coupon:
        return original_amount, original_amount, None
    if coupon.discount_type == "percent":
        discount_amount = _quantize_money((original_amount * _parse_decimal(coupon.value)) / Decimal("100"))
    else:
        discount_amount = _quantize_money(_parse_decimal(coupon.value))
    final_amount = _quantize_money(max(Decimal("0.01"), original_amount - discount_amount))
    applied_discount = _quantize_money(original_amount - final_amount)
    return original_amount, final_amount, applied_discount


def _ensure_asaas_client() -> AsaasClient:
    if not settings.asaas_api_key:
        raise HTTPException(status_code=500, detail="Asaas não configurado.")
    return AsaasClient(settings.asaas_api_key, settings.asaas_base_url)


def _find_existing_user(db: Session, email: str, document: str) -> User | None:
    digits = _normalize_digits(document)
    sanitized_cpf = func.replace(func.replace(func.replace(func.coalesce(User.cpf, ""), ".", ""), "-", ""), "/", "")
    sanitized_cnpj = func.replace(func.replace(func.replace(func.coalesce(User.cnpj, ""), ".", ""), "-", ""), "/", "")
    return (
        db.query(User)
        .filter(
            or_(
                func.lower(User.email) == email.strip().lower(),
                sanitized_cpf == digits,
                sanitized_cnpj == digits,
            )
        )
        .first()
    )


def _find_or_create_asaas_customer(
    client: AsaasClient,
    *,
    session_token: str,
    name: str,
    email: str,
    document: str,
    phone: str,
) -> str:
    digits = _normalize_digits(document)
    customer_list = client.list_customers(cpfCnpj=digits)
    for item in customer_list.get("data", []) or []:
        if _normalize_digits(item.get("cpfCnpj")) == digits:
            return str(item.get("id"))
    customer = client.create_customer(
        {
            "name": name,
            "email": email,
            "cpfCnpj": digits,
            "mobilePhone": _normalize_digits(phone),
            "externalReference": f"checkout:{session_token}",
            "notificationDisabled": False,
        }
    )
    customer_id = customer.get("id")
    if not customer_id:
        raise HTTPException(status_code=502, detail="Asaas não retornou o cliente.")
    return str(customer_id)


def create_checkout_session(
    db: Session,
    *,
    offer: CheckoutOfferOut,
    customer_name: str,
    customer_email: str,
    customer_document: str,
    customer_phone: str,
    customer_zipcode: str,
    coupon_code: str | None,
    metadata: dict[str, Any] | None,
) -> CheckoutSession:
    settings_record = get_checkout_settings(db)
    coupon = resolve_coupon(settings_record, coupon_code, offer.key)
    original_amount, final_amount, discount_amount = apply_coupon_to_offer_amount(offer, coupon)
    existing = _find_existing_user(db, customer_email, customer_document)
    token = secrets.token_urlsafe(24)
    metadata_payload = dict(metadata or {})
    metadata_payload.update(
        {
            "original_amount": str(original_amount),
            "discount_amount": str(discount_amount or Decimal("0.00")),
            "applied_coupon_code": coupon.code if coupon else None,
        }
    )
    session = CheckoutSession(
        token=token,
        offer_key=offer.key,
        product_name=offer.title,
        plan_key=_normalize_plan_key(offer.plan_key),
        billing_cycle=offer.billing_cycle,
        amount=final_amount,
        status="details_completed",
        customer_name=customer_name.strip(),
        customer_email=customer_email.strip().lower(),
        customer_document=_normalize_digits(customer_document),
        customer_phone=_normalize_digits(customer_phone),
        customer_zipcode=_normalize_digits(customer_zipcode),
        coupon_code=coupon.code if coupon else None,
        metadata_json=metadata_payload,
        expires_at=_utcnow() + timedelta(hours=24),
        user_id=existing.id if existing else None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_upgrade_checkout_session(
    db: Session,
    *,
    offer: CheckoutOfferOut,
    user: User,
    coupon_code: str | None = None,
) -> CheckoutSession:
    document = user.cnpj or user.cpf or ""
    phone = user.whatsapp or ""
    zipcode = user.address_zipcode or ""
    if not (document and phone and zipcode):
        raise HTTPException(
            status_code=400,
            detail="Complete CPF/CNPJ, celular e CEP no perfil para continuar com o upgrade.",
        )
    metadata = {
        "upgrade_mode": True,
        "target_user_id": user.id,
        "current_plan": user.plan,
    }
    return create_checkout_session(
        db,
        offer=offer,
        customer_name=user.name,
        customer_email=user.email,
        customer_document=document,
        customer_phone=phone,
        customer_zipcode=zipcode,
        coupon_code=coupon_code,
        metadata=metadata,
    )


def _extract_public_ip(raw_ip: str | None) -> str | None:
    if not raw_ip:
        return None
    try:
        parsed = ip_address(raw_ip.strip())
    except ValueError:
        return None
    if parsed.is_private or parsed.is_loopback or parsed.is_link_local:
        return None
    return str(parsed)


def _resolve_geoip(ip: str | None) -> dict[str, str | None]:
    public_ip = _extract_public_ip(ip)
    if not public_ip:
        return {
            "ip_country": None,
            "ip_region": None,
            "ip_city": None,
            "ip_timezone": None,
            "ip_lat": None,
            "ip_lon": None,
        }
    try:
        req = Request(
            f"http://ip-api.com/json/{public_ip}?fields=status,country,regionName,city,timezone,lat,lon",
            headers={"User-Agent": "agencia-checkout-tracking/1.0"},
        )
        with urlopen(req, timeout=2.0) as res:  # noqa: S310
            payload = json.loads(res.read().decode("utf-8"))
        if str(payload.get("status")).lower() != "success":
            raise ValueError("geoip_failed")
        return {
            "ip_country": str(payload.get("country") or "") or None,
            "ip_region": str(payload.get("regionName") or "") or None,
            "ip_city": str(payload.get("city") or "") or None,
            "ip_timezone": str(payload.get("timezone") or "") or None,
            "ip_lat": str(payload.get("lat") or "") or None,
            "ip_lon": str(payload.get("lon") or "") or None,
        }
    except Exception:
        return {
            "ip_country": None,
            "ip_region": None,
            "ip_city": None,
            "ip_timezone": None,
            "ip_lat": None,
            "ip_lon": None,
        }


def _find_or_create_checkout_lead(db: Session, session: CheckoutSession) -> CheckoutLead:
    lead = db.query(CheckoutLead).filter(CheckoutLead.session_id == session.id).first()
    if lead:
        return lead
    lead = CheckoutLead(
        session_id=session.id,
        token=session.token,
        offer_key=session.offer_key,
        customer_name=session.customer_name,
        customer_email=session.customer_email,
        customer_document=session.customer_document,
        customer_phone=session.customer_phone,
        customer_zipcode=session.customer_zipcode,
        metadata_json={},
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(lead)
    db.flush()
    return lead


def track_checkout_event(
    db: Session,
    *,
    session: CheckoutSession,
    event_name: str,
    step: str | None,
    status: str | None,
    payment_method: str | None,
    duration_ms: int | None,
    error_message: str | None,
    metadata: dict[str, Any] | None,
    ip_address_value: str | None,
    user_agent: str | None,
) -> None:
    geo = _resolve_geoip(ip_address_value)
    event = CheckoutTrackingEvent(
        session_id=session.id,
        token=session.token,
        offer_key=session.offer_key,
        event_name=(event_name or "").strip().lower()[:80],
        step=(step or "").strip().lower()[:40] or None,
        status=(status or "").strip().lower()[:40] or None,
        payment_method=(payment_method or "").strip().lower()[:30] or None,
        duration_ms=duration_ms,
        error_message=error_message,
        ip_address=ip_address_value,
        ip_country=geo["ip_country"],
        ip_region=geo["ip_region"],
        ip_city=geo["ip_city"],
        ip_timezone=geo["ip_timezone"],
        ip_lat=geo["ip_lat"],
        ip_lon=geo["ip_lon"],
        user_agent=(user_agent or "")[:2000] or None,
        metadata_json=metadata or {},
        created_at=_utcnow(),
    )
    db.add(event)

    lead = _find_or_create_checkout_lead(db, session)
    if event.event_name == "step_method_view":
        lead.customer_name = session.customer_name
        lead.customer_email = session.customer_email
        lead.customer_document = session.customer_document
        lead.customer_phone = session.customer_phone
        lead.customer_zipcode = session.customer_zipcode
        existing_metadata = dict(session.metadata_json or {})
        if not existing_metadata.get("viajechat_contact_id"):
            contact_id = ensure_checkout_contact_at_payment_step(
                name=session.customer_name,
                email=session.customer_email,
                phone=session.customer_phone,
                offer_key=session.offer_key,
                token=session.token,
            )
            if contact_id:
                existing_metadata["viajechat_contact_id"] = str(contact_id)
                existing_metadata["viajechat_contact_created_at"] = _utcnow().isoformat()
                session.metadata_json = existing_metadata
                db.add(session)
    if payment_method:
        lead.payment_method_selected = payment_method
    if session.status == "paid":
        lead.signed_at = lead.signed_at or session.paid_at or _utcnow()
    if session.password_defined_at:
        lead.password_defined_at = session.password_defined_at
    lead.updated_at = _utcnow()
    db.add(lead)
    db.commit()


def list_checkout_tracking(db: Session, offer_key: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    rows = (
        db.query(CheckoutLead)
        .order_by(CheckoutLead.updated_at.desc())
        .limit(max(1, min(limit, 500)))
        .all()
    )
    if offer_key:
        normalized = offer_key.strip().lower()
        rows = [row for row in rows if (row.offer_key or "").strip().lower() == normalized]
    grouped: dict[str, dict[str, Any]] = {}
    for lead in rows:
        document_key = (lead.customer_document or "").strip() or f"session:{lead.session_id}"
        events = (
            db.query(CheckoutTrackingEvent)
            .filter(CheckoutTrackingEvent.session_id == lead.session_id)
            .order_by(CheckoutTrackingEvent.created_at.asc())
            .all()
        )
        total_time_seconds = None
        if events:
            first = events[0].created_at
            last = events[-1].created_at
            if first and last:
                total_time_seconds = max(0, int((last - first).total_seconds()))
        success_count = sum(1 for ev in events if (ev.status or "") == "paid" or ev.event_name == "payment_success")
        error_count = sum(1 for ev in events if (ev.status or "") == "error" or bool(ev.error_message))
        last = events[-1] if events else None
        bucket = grouped.get(document_key)
        if not bucket:
            bucket = {
                "id": lead.id,
                "token": lead.token,
                "offer_key": lead.offer_key,
                "customer_name": lead.customer_name,
                "customer_email": lead.customer_email,
                "customer_document": lead.customer_document,
                "customer_phone": lead.customer_phone,
                "customer_zipcode": lead.customer_zipcode,
                "payment_method_selected": lead.payment_method_selected,
                "signed_at": lead.signed_at,
                "password_defined_at": lead.password_defined_at,
                "created_at": lead.created_at,
                "updated_at": lead.updated_at,
                "events_count": 0,
                "success_events_count": 0,
                "error_events_count": 0,
                "last_event_name": None,
                "last_event_at": None,
                "last_ip_address": None,
                "last_ip_city": None,
                "last_ip_region": None,
                "last_ip_country": None,
                "total_time_seconds": 0,
                "sessions_count": 0,
            }
            grouped[document_key] = bucket
        bucket["sessions_count"] += 1
        bucket["events_count"] += len(events)
        bucket["success_events_count"] += success_count
        bucket["error_events_count"] += error_count
        if total_time_seconds:
            bucket["total_time_seconds"] += total_time_seconds
        if lead.signed_at and (not bucket["signed_at"] or lead.signed_at > bucket["signed_at"]):
            bucket["signed_at"] = lead.signed_at
        if lead.password_defined_at and (not bucket["password_defined_at"] or lead.password_defined_at > bucket["password_defined_at"]):
            bucket["password_defined_at"] = lead.password_defined_at
        if lead.updated_at and (not bucket["updated_at"] or lead.updated_at > bucket["updated_at"]):
            bucket["updated_at"] = lead.updated_at
        if last and (not bucket["last_event_at"] or (last.created_at and last.created_at > bucket["last_event_at"])):
            bucket["last_event_name"] = last.event_name
            bucket["last_event_at"] = last.created_at
            bucket["last_ip_address"] = last.ip_address
            bucket["last_ip_city"] = last.ip_city
            bucket["last_ip_region"] = last.ip_region
            bucket["last_ip_country"] = last.ip_country
    result = sorted(grouped.values(), key=lambda item: item.get("updated_at") or _utcnow(), reverse=True)
    return result[: max(1, min(limit, 500))]


def get_checkout_tracking_document_detail(db: Session, customer_document: str, offer_key: str | None = None) -> dict[str, Any]:
    normalized_document = _normalize_digits(customer_document)
    leads = (
        db.query(CheckoutLead)
        .filter(CheckoutLead.customer_document == normalized_document)
        .order_by(CheckoutLead.updated_at.desc())
        .all()
    )
    if offer_key:
        normalized_offer = offer_key.strip().lower()
        leads = [lead for lead in leads if (lead.offer_key or "").strip().lower() == normalized_offer]
    if not leads:
        raise HTTPException(status_code=404, detail="Lead nao encontrado para este documento.")
    session_ids = [lead.session_id for lead in leads]
    events = (
        db.query(CheckoutTrackingEvent)
        .filter(CheckoutTrackingEvent.session_id.in_(session_ids))
        .order_by(CheckoutTrackingEvent.created_at.asc())
        .all()
    )
    latest = leads[0]
    return {
        "customer_document": normalized_document,
        "customer_name": latest.customer_name,
        "customer_email": latest.customer_email,
        "customer_phone": latest.customer_phone,
        "sessions_count": len(leads),
        "events_count": len(events),
        "error_events_count": sum(1 for ev in events if (ev.status or "") == "error" or bool(ev.error_message)),
        "signed_count": sum(1 for lead in leads if lead.signed_at is not None),
        "password_defined_count": sum(1 for lead in leads if lead.password_defined_at is not None),
        "first_seen_at": leads[-1].created_at if leads else None,
        "last_seen_at": leads[0].updated_at if leads else None,
        "events": [
            {
                "id": ev.id,
                "token": ev.token,
                "offer_key": ev.offer_key,
                "event_name": ev.event_name,
                "step": ev.step,
                "status": ev.status,
                "payment_method": ev.payment_method,
                "duration_ms": ev.duration_ms,
                "error_message": ev.error_message,
                "ip_address": ev.ip_address,
                "ip_country": ev.ip_country,
                "ip_region": ev.ip_region,
                "ip_city": ev.ip_city,
                "created_at": ev.created_at,
            }
            for ev in events
        ],
    }


def get_checkout_session_by_token(db: Session, token: str) -> CheckoutSession:
    session = db.query(CheckoutSession).filter(CheckoutSession.token == token).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão de checkout não encontrada.")
    return session


def serialize_checkout_session(db: Session, session: CheckoutSession) -> dict[str, Any]:
    user = session.user or _find_existing_user(db, session.customer_email, session.customer_document)
    requires_password_setup = not bool(user and user.hashed_password and session.password_defined_at)
    user_exists = bool(user)
    metadata = session.metadata_json or {}
    return {
        "token": session.token,
        "offer_key": session.offer_key,
        "product_name": session.product_name,
        "billing_cycle": session.billing_cycle,
        "amount": session.amount,
        "original_amount": metadata.get("original_amount"),
        "discount_amount": metadata.get("discount_amount"),
        "applied_coupon_code": metadata.get("applied_coupon_code"),
        "status": session.status,
        "payment_method": session.payment_method,
        "customer_name": session.customer_name,
        "customer_email": session.customer_email,
        "customer_document": session.customer_document,
        "customer_phone": session.customer_phone,
        "customer_zipcode": session.customer_zipcode,
        "pix_copy_paste": session.pix_copy_paste,
        "pix_qr_code_base64": session.pix_qr_code_base64,
        "pix_expiration_date": session.pix_expiration_date,
        "paid_at": session.paid_at,
        "password_defined_at": session.password_defined_at,
        "user_exists": user_exists,
        "requires_password_setup": False if _is_upgrade_session(session) else requires_password_setup,
        "is_upgrade": _is_upgrade_session(session),
    }


def start_pix_payment(db: Session, session: CheckoutSession) -> CheckoutSession:
    if session.asaas_payment_id and session.payment_method == "pix" and session.status in {"awaiting_payment", "paid"}:
        return refresh_session_status(db, session) if session.status != "paid" else session
    client = _ensure_asaas_client()
    customer_id = session.asaas_customer_id or _find_or_create_asaas_customer(
        client,
        session_token=session.token,
        name=session.customer_name,
        email=session.customer_email,
        document=session.customer_document,
        phone=session.customer_phone,
    )
    immediate_qr: dict[str, Any] = {}
    authorization_id: str | None = None
    subscription_id: str | None = None
    if _is_upgrade_session(session):
        payment = client.create_payment(
            {
                "customer": customer_id,
                "billingType": "PIX",
                "value": float(session.amount),
                "dueDate": _utcnow().date().isoformat(),
                "description": f"Upgrade {session.product_name}",
                "externalReference": f"checkout_upgrade:{session.token}",
            }
        )
        payment_id = _extract_asaas_resource_id(payment.get("id"))
        if not payment_id:
            raise HTTPException(status_code=502, detail="Asaas não retornou cobrança PIX.")
        session.asaas_payment_id = payment_id
        try:
            immediate_qr = client.get_pix_qr_code(payment_id) or {}
        except AsaasAPIError:
            immediate_qr = {}
    else:
        frequency = "ANNUALLY" if session.billing_cycle == "annual" else "MONTHLY"
        start_date = _billing_today()
        # Asaas limita contractId a 35 chars.
        contract_id = f"co:{session.token}"[:35]
        auth_payload = {
            "customerId": customer_id,
            "frequency": frequency,
            "contractId": contract_id,
            "startDate": start_date,
            "value": float(session.amount),
            "originalValue": float(session.amount),
            "description": session.product_name[:35],
            "expirationSeconds": 3600,
            "immediateQrCode": {
                "paymentCreationMode": "SUBSCRIPTION",
                "expirationSeconds": 3600,
                "originalValue": float(session.amount),
            },
        }
        authorization = client.create_pix_automatic_authorization(auth_payload)
        authorization_id = _extract_asaas_resource_id(authorization.get("id"))
        if not authorization_id:
            raise HTTPException(status_code=502, detail="Asaas nao retornou autorizacao de Pix Automatico.")
        immediate_qr = authorization.get("immediateQrCode") or {}
        # Fallback: alguns ambientes retornam autorização sem immediateQrCode.
        # Nesse caso criamos assinatura PIX padrão e buscamos o QR no primeiro pagamento.
        if not immediate_qr.get("payload"):
            subscription_payload: dict[str, Any] = {
                "customer": customer_id,
                "billingType": "PIX",
                "nextDueDate": _billing_today(),
                "cycle": _resolve_asaas_cycle(session.billing_cycle),
                "value": float(session.amount),
                "description": session.product_name,
                "externalReference": f"checkout:{session.token}",
                "split": build_default_split_payload(),
            }
            subscription = client.create_subscription(subscription_payload)
            subscription_id = _extract_asaas_resource_id(subscription.get("id"))
            if subscription_id:
                payments = client.list_subscription_payments(subscription_id)
                first_payment = _pick_checkout_subscription_payment(payments)
                payment_id = _extract_asaas_resource_id(first_payment.get("id"))
                if payment_id:
                    session.asaas_payment_id = payment_id
                    try:
                        immediate_qr = client.get_pix_qr_code(payment_id) or {}
                    except AsaasAPIError:
                        immediate_qr = {}

    session.asaas_customer_id = customer_id
    session.payment_method = "pix"
    session.status = "awaiting_payment"
    session.pix_copy_paste = immediate_qr.get("payload")
    session.pix_qr_code_base64 = immediate_qr.get("encodedImage")
    expiration = immediate_qr.get("expirationDate")
    if expiration:
        try:
            session.pix_expiration_date = datetime.fromisoformat(str(expiration).replace("Z", "+00:00"))
        except ValueError:
            session.pix_expiration_date = None
    session.updated_at = _utcnow()
    metadata = dict(session.metadata_json or {})
    if authorization_id:
        metadata["asaas_pix_automatic_authorization_id"] = authorization_id
    if subscription_id:
        metadata["asaas_subscription_id"] = subscription_id
    session.metadata_json = metadata
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def start_card_payment(db: Session, session: CheckoutSession, payload: dict[str, Any]) -> CheckoutSession:
    if session.asaas_payment_id and session.payment_method == "card" and session.status in {"awaiting_payment", "processing", "paid"}:
        return refresh_session_status(db, session) if session.status != "paid" else session
    client = _ensure_asaas_client()
    customer_id = session.asaas_customer_id or _find_or_create_asaas_customer(
        client,
        session_token=session.token,
        name=session.customer_name,
        email=session.customer_email,
        document=session.customer_document,
        phone=session.customer_phone,
    )
    amount = Decimal(str(session.amount))
    card_last4 = _extract_card_last4(payload.get("card_number"))
    card_brand = _infer_card_brand(payload.get("card_number"))
    metadata = dict(session.metadata_json or {})
    if card_last4:
        metadata["card_last4"] = card_last4
    if card_brand:
        metadata["card_brand"] = card_brand
    session.metadata_json = metadata
    is_upgrade = _is_upgrade_session(session)
    upgrade_target_subscription = _resolve_target_subscription_for_upgrade(db, session) if is_upgrade else None
    can_upgrade_in_place = bool(upgrade_target_subscription and upgrade_target_subscription.asaas_subscription_id)
    external_reference = f"checkout_upgrade:{session.token}" if is_upgrade else f"checkout:{session.token}"
    session.asaas_customer_id = customer_id
    session.payment_method = "card"
    session.status = "processing"
    payment_id = None
    first_payment: dict[str, Any] = {}
    if is_upgrade and can_upgrade_in_place:
        payment_payload: dict[str, Any] = {
            "customer": customer_id,
            "billingType": "CREDIT_CARD",
            "value": float(amount),
            "dueDate": _billing_today(),
            "description": f"Upgrade {session.product_name}",
            "externalReference": external_reference,
            "split": build_default_split_payload(),
            "creditCard": {
                "holderName": payload["holder_name"],
                "number": _normalize_digits(payload["card_number"]),
                "expiryMonth": str(payload["expiry_month"]),
                "expiryYear": str(payload["expiry_year"]),
                "ccv": str(payload["ccv"]),
            },
            "creditCardHolderInfo": {
                "name": session.customer_name,
                "email": session.customer_email,
                "cpfCnpj": session.customer_document,
                "postalCode": session.customer_zipcode,
                "addressNumber": "S/N",
                "phone": session.customer_phone,
                "mobilePhone": session.customer_phone,
            },
            "remoteIp": payload.get("remote_ip") or "127.0.0.1",
        }
        created_payment = client.create_payment(payment_payload)
        payment_id = created_payment.get("id")
        first_payment = created_payment
    else:
        subscription_payload: dict[str, Any] = {
            "customer": customer_id,
            "billingType": "CREDIT_CARD",
            "nextDueDate": _billing_today(),
            "cycle": _resolve_asaas_cycle(session.billing_cycle),
            "value": float(amount),
            "description": session.product_name,
            "externalReference": external_reference,
            "split": build_default_split_payload(),
            "creditCard": {
                "holderName": payload["holder_name"],
                "number": _normalize_digits(payload["card_number"]),
                "expiryMonth": str(payload["expiry_month"]),
                "expiryYear": str(payload["expiry_year"]),
                "ccv": str(payload["ccv"]),
            },
            "creditCardHolderInfo": {
                "name": session.customer_name,
                "email": session.customer_email,
                "cpfCnpj": session.customer_document,
                "postalCode": session.customer_zipcode,
                "addressNumber": "S/N",
                "phone": session.customer_phone,
                "mobilePhone": session.customer_phone,
            },
            "remoteIp": payload.get("remote_ip") or "127.0.0.1",
        }
        subscription = client.create_subscription(subscription_payload)
        subscription_id = _extract_asaas_resource_id(subscription.get("id"))
        if not subscription_id:
            raise HTTPException(status_code=502, detail="Asaas nao retornou assinatura de cartao.")
        payments = client.list_subscription_payments(subscription_id)
        first_payment = _pick_checkout_subscription_payment(payments)
        payment_id = first_payment.get("id")
        metadata = dict(session.metadata_json or {})
        metadata["asaas_subscription_id"] = subscription_id
        session.metadata_json = metadata

    if payment_id:
        session.asaas_payment_id = str(payment_id)
        mapped = _map_asaas_payment_status(first_payment.get("status"))
        if mapped:
            session.status = mapped
        if session.status == "paid":
            session.paid_at = _utcnow()
            if _is_upgrade_session(session) and can_upgrade_in_place:
                _apply_upgrade_after_payment(db, session)
            else:
                _upsert_paid_user_and_subscription(db, session)
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def _upsert_paid_user_and_subscription(db: Session, session: CheckoutSession) -> User:
    user = session.user or _find_existing_user(db, session.customer_email, session.customer_document)
    previous_plan = str(user.plan or "").strip().lower() if user else ""
    if not user:
        user = User(
            email=session.customer_email,
            name=session.customer_name,
            hashed_password=auth_service.get_password_hash(secrets.token_urlsafe(32)),
            cpf=session.customer_document if len(session.customer_document) <= 11 else None,
            cnpj=session.customer_document if len(session.customer_document) > 11 else None,
            whatsapp=session.customer_phone,
            address_zipcode=session.customer_zipcode,
            plan=session.plan_key,
            is_active=True,
            is_owner=True,
            role="admin",
            status="pending_agency_setup",
            permissions=[],
        )
        db.add(user)
        db.flush()
    else:
        user.name = session.customer_name or user.name
        user.whatsapp = session.customer_phone or user.whatsapp
        user.address_zipcode = session.customer_zipcode or user.address_zipcode
        if len(session.customer_document) > 11:
            user.cnpj = session.customer_document
        else:
            user.cpf = session.customer_document
        user.plan = session.plan_key

    subscription = user.subscription
    if not subscription:
        subscription = Subscription(user_id=user.id)
        db.add(subscription)
        db.flush()
        user.subscription_id = subscription.id

    subscription.provider = "asaas"
    subscription.plan = session.plan_key
    subscription.status = "active"
    subscription.billing_cycle = session.billing_cycle
    subscription.payment_method_type = "pix" if session.payment_method == "pix" else "card"
    metadata = dict(session.metadata_json or {})
    if session.payment_method == "card":
        subscription.card_brand = metadata.get("card_brand")
        subscription.card_last4 = metadata.get("card_last4")
    else:
        subscription.card_brand = None
        subscription.card_last4 = None
    subscription.failed_attempts = 0
    subscription.valid_until = _utcnow() + _duration_from_cycle(session.billing_cycle)
    subscription.asaas_customer_id = session.asaas_customer_id
    metadata = dict(session.metadata_json or {})
    if metadata.get("asaas_subscription_id"):
        subscription.asaas_subscription_id = str(metadata["asaas_subscription_id"])
    subscription.external_reference = f"checkout:{session.token}"
    subscription.mrr_amount = (
        _parse_decimal(session.amount) / Decimal("12")
        if session.billing_cycle == "annual"
        else _parse_decimal(session.amount)
    )

    session.user_id = user.id
    session.updated_at = _utcnow()
    end_trial(user, db, keep_plan=session.plan_key)
    if not _is_comeco_like_plan(session.plan_key):
        republish_all_user_pages(user, db)
    db.add_all([user, subscription, session])
    db.commit()
    db.refresh(user)
    # Do not auto-create agency for checkout-first users.
    # Agency setup should happen explicitly later in product flow.
    mark_viajechat_signed(
        name=session.customer_name,
        email=session.customer_email,
        phone=session.customer_phone,
        offer_key=session.offer_key,
        upgrade_mode=False,
        contact_id=str((dict(session.metadata_json or {}).get("viajechat_contact_id") or "")).strip() or None,
    )
    return user


def _map_asaas_payment_status(status: Any) -> str:
    raw = str(status or "").upper()
    if raw in {"RECEIVED", "CONFIRMED", "AUTHORIZED"}:
        return "paid"
    if raw in {"PENDING", "AWAITING_RISK_ANALYSIS"}:
        return "awaiting_payment"
    if raw in {"OVERDUE"}:
        return "expired"
    if raw in {"REFUNDED", "RECEIVED_IN_CASH_UNDONE", "CHARGEBACK_REQUESTED", "CHARGEBACK_DISPUTE"}:
        return "refunded"
    if raw in {"REFUSED", "REPROVED_BY_RISK_ANALYSIS"}:
        return "failed"
    return raw.lower() or "draft"


def _pick_latest_payment(payments_payload: dict[str, Any] | None) -> dict[str, Any]:
    rows = ((payments_payload or {}).get("data") or [])
    if not rows:
        return {}

    def _to_dt(value: Any) -> datetime:
        raw = str(value or "").strip()
        if not raw:
            return datetime.min.replace(tzinfo=timezone.utc)
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)

    return max(
        rows,
        key=lambda item: (
            _to_dt(item.get("dateCreated")),
            _to_dt(item.get("dueDate")),
            str(item.get("id") or ""),
        ),
    )


def _pick_checkout_subscription_payment(
    payments_payload: dict[str, Any] | None,
    preferred_payment_id: str | None = None,
) -> dict[str, Any]:
    rows = ((payments_payload or {}).get("data") or [])
    if not rows:
        return {}

    def _to_dt(value: Any) -> datetime:
        raw = str(value or "").strip()
        if not raw:
            return datetime.max.replace(tzinfo=timezone.utc)
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return datetime.max.replace(tzinfo=timezone.utc)

    if preferred_payment_id:
        for item in rows:
            if str(item.get("id") or "") == str(preferred_payment_id):
                return item

    paid_like = {"RECEIVED", "CONFIRMED", "AUTHORIZED"}
    paid_rows = [item for item in rows if str(item.get("status") or "").upper() in paid_like]
    if paid_rows:
        return max(
            paid_rows,
            key=lambda item: (
                _to_dt(item.get("dateCreated")),
                _to_dt(item.get("dueDate")),
                str(item.get("id") or ""),
            ),
        )

    return min(
        rows,
        key=lambda item: (
            _to_dt(item.get("dueDate")),
            _to_dt(item.get("dateCreated")),
            str(item.get("id") or ""),
        ),
    )


def refresh_session_status(db: Session, session: CheckoutSession) -> CheckoutSession:
    client = _ensure_asaas_client()
    payment_id = session.asaas_payment_id
    subscription_id = _resolve_session_subscription_id(session)

    if session.payment_method == "card" and subscription_id:
        payments = client.list_subscription_payments(subscription_id)
        selected = _pick_checkout_subscription_payment(payments, preferred_payment_id=payment_id)
        selected_id = selected.get("id")
        if selected_id:
            payment_id = str(selected_id)
            session.asaas_payment_id = payment_id
            mapped_from_list = _map_asaas_payment_status(selected.get("status"))
            if mapped_from_list == "paid":
                session.status = "paid"
                if not session.paid_at:
                    session.paid_at = _utcnow()
                    if _is_upgrade_session(session):
                        _apply_upgrade_after_payment(db, session)
                    else:
                        _upsert_paid_user_and_subscription(db, session)
                session.updated_at = _utcnow()
                db.add(session)
                db.commit()
                db.refresh(session)
                return session

    if not payment_id:
        if session.payment_method == "pix":
            return session
        if not subscription_id:
            return session
        payments = client.list_subscription_payments(subscription_id)
        first_payment = _pick_checkout_subscription_payment(payments)
        payment_id = first_payment.get("id")
        if payment_id:
            session.asaas_payment_id = str(payment_id)
            if session.payment_method == "pix":
                try:
                    pix = client.get_pix_qr_code(str(payment_id))
                    session.pix_copy_paste = pix.get("payload")
                    session.pix_qr_code_base64 = pix.get("encodedImage")
                    expiration = pix.get("expirationDate")
                    if expiration:
                        try:
                            session.pix_expiration_date = datetime.fromisoformat(str(expiration).replace("Z", "+00:00"))
                        except ValueError:
                            session.pix_expiration_date = None
                except AsaasAPIError:
                    pass
        else:
            session.updated_at = _utcnow()
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
    payment = client.get_payment(str(payment_id))
    mapped = _map_asaas_payment_status(payment.get("status"))
    if mapped:
        session.status = mapped
    if mapped == "paid" and not session.paid_at:
        session.paid_at = _utcnow()
        if _is_upgrade_session(session):
            _apply_upgrade_after_payment(db, session)
        else:
            _upsert_paid_user_and_subscription(db, session)
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def handle_asaas_checkout_webhook(db: Session, payload: dict[str, Any]) -> bool:
    payment = payload.get("payment") or {}
    authorization = payload.get("authorization") or {}
    external_reference = str(payment.get("externalReference") or authorization.get("contractId") or "")
    session = None
    token = None
    if external_reference.startswith("checkout:"):
        token = external_reference.split("checkout:", 1)[1].strip()
    elif external_reference.startswith("checkout_upgrade:"):
        token = external_reference.split("checkout_upgrade:", 1)[1].strip()
    if token:
        session = db.query(CheckoutSession).filter(CheckoutSession.token == token).first()
    if not session:
        authorization_id = _extract_asaas_resource_id(authorization.get("id"))
        if authorization_id:
            rows = db.query(CheckoutSession).filter(CheckoutSession.metadata_json.isnot(None)).all()
            for row in rows:
                metadata = dict(row.metadata_json or {})
                if str(metadata.get("asaas_pix_automatic_authorization_id") or "") == authorization_id:
                    session = row
                    break
    if not session:
        return False
    session.asaas_payment_id = payment.get("id") or session.asaas_payment_id
    session.asaas_customer_id = payment.get("customer") or session.asaas_customer_id
    subscription_id = _extract_asaas_resource_id(payment.get("subscription"))
    if subscription_id:
        metadata = dict(session.metadata_json or {})
        metadata["asaas_subscription_id"] = subscription_id
        session.metadata_json = metadata
    session.status = _map_asaas_payment_status(payment.get("status") or payload.get("event"))
    event = str(payload.get("event") or "").upper()
    if event in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"} or session.status == "paid":
        if not session.paid_at:
            session.paid_at = _utcnow()
        session.status = "paid"
        if _is_upgrade_session(session):
            _apply_upgrade_after_payment(db, session)
        else:
            _upsert_paid_user_and_subscription(db, session)
    elif event in {"PAYMENT_OVERDUE", "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_EXPIRED", "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_REFUSED"}:
        session.status = "expired"
    elif event in {"PAYMENT_REPROVED_BY_RISK_ANALYSIS", "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_CANCELLED"}:
        session.status = "failed"
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()
    return True


def define_password_for_paid_checkout(db: Session, token: str, password: str) -> User:
    session = get_checkout_session_by_token(db, token)
    if session.status != "paid":
        raise HTTPException(status_code=400, detail="O pagamento ainda não foi confirmado.")
    try:
        auth_service.validate_password_strength(password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = _upsert_paid_user_and_subscription(db, session)
    user.hashed_password = auth_service.get_password_hash(password)
    session.password_defined_at = _utcnow()
    session.updated_at = _utcnow()
    db.add_all([user, session])
    db.commit()
    db.refresh(user)
    return user


def coerce_checkout_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, AsaasAPIError):
        detail = "Erro ao processar cobrança no Asaas."
        try:
            raw = str(exc)
            if raw:
                detail = f"{detail} {raw[:700]}"
        except Exception:
            pass
        return HTTPException(status_code=502, detail=detail)
    return HTTPException(status_code=500, detail="Erro interno no checkout.")






