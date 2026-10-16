from __future__ import annotations

import hashlib
import logging
import secrets
import json
from ipaddress import ip_address
from urllib.request import Request, urlopen
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, object_session, joinedload

from app.core.config import get_settings
from app.models.checkout import CheckoutLead, CheckoutSession, CheckoutSettings, CheckoutTrackingEvent
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.checkout import (
    CheckoutAppearanceOut,
    CheckoutCouponOut,
    CheckoutOfferIn,
    CheckoutOfferOut,
    CheckoutOfferReportItemOut,
    CheckoutPixelOut,
    CheckoutPixelPublicOut,
    CheckoutSettingsUpdate,
)
from app.services import auth as auth_service
from app.services.asaas import AsaasAPIError, AsaasClient, build_default_split_payload
from app.services.card_installments import InstallmentOption, installment_options, option_for
from app.services.company_status import mark_subscription_overdue
from app.services.ntfy import SubscriptionPushScenario, format_brl, publish_subscription_notification
from app.services.trial import end_trial
from app.services.trial import republish_all_user_pages
from app.services.webhook_notifications import contact_context, notify_payment_overdue, notify_safely, send_notification
from app.services.viajechat_checkout_flow import (
    ensure_checkout_contact_at_payment_step,
    mark_signed as mark_viajechat_signed,
)

settings = get_settings()
logger = logging.getLogger(__name__)
TEMP_DISABLE_CHECKOUT_SPLIT = False
ASAAS_CUSTOMER_GROUP_NAME = "Roteiro Online"

DEFAULT_CHECKOUTS = [
    {
        "key": "default",
        "name": "Checkout padrÃ£o",
        "theme_mode": "dark",
        "desktop_image_url": None,
        "mobile_banner_url": None,
        "active": True,
    }
]

DEFAULT_PIXELS: list[dict[str, Any]] = []

DEFAULT_OFFERS = [
    {
        "key": "profissional",
        "title": "Plano profissional",
        "footer_product_label": "Plano profissional",
        "plan_key": "professional",
        "billing_cycle": "monthly",
        "amount": "49.99",
        "active": True,
        "subtitle": "Acesso completo Ã  plataforma",
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


def _next_pix_automatic_due_date(base: date, cycle: str) -> date:
    if str(cycle).strip().lower() == "annual":
        try:
            return base.replace(year=base.year + 1)
        except ValueError:
            return base.replace(year=base.year + 1, day=28)
    next_month = 1 if base.month == 12 else base.month + 1
    next_year = base.year + 1 if base.month == 12 else base.year
    month_after = 1 if next_month == 12 else next_month + 1
    year_after = next_year + 1 if next_month == 12 else next_year
    last_day = (date(year_after, month_after, 1) - timedelta(days=1)).day
    return date(next_year, next_month, min(base.day, last_day))


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


def find_pix_automatic_authorization_id(
    db: Session,
    *,
    user_id: int,
    checkout_token: str | None = None,
) -> str | None:
    """Localiza o mandato Pix Automático ativo associado à assinatura do usuário."""
    query = db.query(CheckoutSession).filter(
        CheckoutSession.user_id == user_id,
        CheckoutSession.payment_method == "pix",
        CheckoutSession.metadata_json.isnot(None),
    )
    if checkout_token:
        query = query.filter(CheckoutSession.token == checkout_token)
    rows = query.order_by(CheckoutSession.created_at.desc()).all()
    for row in rows:
        metadata = dict(row.metadata_json or {})
        if str(metadata.get("pix_mode") or "").strip().lower() != "automatic":
            continue
        authorization_id = str(metadata.get("asaas_pix_automatic_authorization_id") or "").strip()
        if authorization_id:
            return authorization_id
    return None


def _is_upgrade_session(session: CheckoutSession) -> bool:
    metadata = dict(session.metadata_json or {})
    return bool(metadata.get("upgrade_mode"))


def _extract_checkout_session_token(external_reference: str) -> str | None:
    reference = str(external_reference or "").strip()
    if reference.startswith("checkout:"):
        return reference.split("checkout:", 1)[1].strip() or None
    if reference.startswith("checkout_upgrade:"):
        return reference.split("checkout_upgrade:", 1)[1].strip() or None
    if reference.startswith("co:"):
        return reference.split("co:", 1)[1].strip() or None
    if reference.startswith("checkout_renewal:"):
        # checkout_renewal:<token>:<vencimento renovado> (renovação do anual parcelado).
        return reference.split("checkout_renewal:", 1)[1].split(":", 1)[0].strip() or None
    return None


def _extract_pix_automatic_authorization_id(payload: dict[str, Any]) -> str | None:
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
    instruction = payload.get("paymentInstruction") if isinstance(payload.get("paymentInstruction"), dict) else {}
    automatic_instruction = (
        payload.get("pixAutomaticPaymentInstruction")
        if isinstance(payload.get("pixAutomaticPaymentInstruction"), dict)
        else {}
    )
    candidates = (
        payload.get("authorization"),
        payload.get("pixAutomaticAuthorization"),
        payment.get("pixAutomaticAuthorization"),
        payment.get("pixAutomaticAuthorizationId"),
        instruction.get("authorization"),
        automatic_instruction.get("authorization"),
    )
    for candidate in candidates:
        resource_id = _extract_asaas_resource_id(candidate)
        if resource_id:
            return resource_id
    return None


def _extract_pix_automatic_qr_code(authorization: dict[str, Any]) -> dict[str, Any]:
    immediate = authorization.get("immediateQrCode")
    immediate = immediate if isinstance(immediate, dict) else {}
    return {
        "payload": immediate.get("payload") or authorization.get("payload"),
        "encodedImage": immediate.get("encodedImage") or authorization.get("encodedImage"),
        "expirationDate": immediate.get("expirationDate") or authorization.get("expirationDate"),
        "conciliationIdentifier": immediate.get("conciliationIdentifier")
        or authorization.get("conciliationIdentifier"),
    }


def _build_asaas_customer_payload(*, name: str, email: str, document: str, phone: str, session_token: str) -> dict[str, Any]:
    return {
        "name": name,
        "email": email,
        "cpfCnpj": _normalize_digits(document),
        "mobilePhone": _normalize_digits(phone),
        "externalReference": f"checkout:{session_token}",
        "notificationDisabled": False,
        "groupName": ASAAS_CUSTOMER_GROUP_NAME,
    }


def _humanize_payment_method(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"pix", "pix_automatic", "pix-automatic"}:
        return "PIX"
    if normalized in {"card", "credit_card", "credit-card", "creditcard", "c", "cc"}:
        return "Cartão de crédito"
    if normalized in {"boleto", "bank_slip"}:
        return "Boleto"
    if normalized:
        return normalized.replace("_", " ").strip().title()
    return "Não informado"


def _notify_checkout_subscription_push(
    *,
    scenario: SubscriptionPushScenario,
    session: CheckoutSession,
    user: User,
    previous_plan_name: str | None = None,
    upgraded_plan_name: str | None = None,
    cancelled_item: str | None = None,
) -> None:
    payment_method = _humanize_payment_method(session.payment_method)
    plan_name = session.product_name or session.offer_key or session.plan_key or "Assinatura"
    try:
        publish_subscription_notification(
            scenario=scenario,
            user_name=user.name or session.customer_name or "Não informado",
            payment_method=payment_method,
            amount=session.amount,
            plan_name=plan_name,
            offer_name=session.product_name or session.offer_key,
            previous_plan_name=previous_plan_name,
            upgraded_plan_name=upgraded_plan_name,
            cancelled_item=cancelled_item,
            customer_email=session.customer_email or user.email,
            customer_phone=session.customer_phone or user.whatsapp,
        )
    except Exception:  # pragma: no cover - alerta não pode quebrar o checkout
        pass


def _notify_checkout_started(session: CheckoutSession) -> None:
    """Checkout iniciado (dados preenchidos, sem pagar). A mesma pessoa voltando à mesma oferta em
    até 3 horas não gera outro aviso."""
    metadata = dict(session.metadata_json or {})
    first = metadata.get("first_payment_amount")
    notify_safely(
        event_key="checkout_started",
        context={
            "event_label": "Checkout iniciado",
            "user_name": session.customer_name or "Não informado",
            "plan_name": session.product_name or session.offer_key or "Plano",
            "offer_name": session.offer_key or "",
            "amount": format_brl(first or session.amount),
            "payment_method": "",
            "purchase_kind": "Upgrade" if metadata.get("upgrade_mode") else "Nova compra",
            **contact_context(session.customer_email, session.customer_phone),
        },
        dedupe_key=f"{(session.customer_email or session.customer_document or session.token).lower()}:{session.offer_key}",
        dedupe_seconds=3 * 3600,
    )


def _notify_checkout_payment_overdue(session: CheckoutSession, payment: dict[str, Any], kind: str) -> None:
    user = session.user
    notify_payment_overdue(
        user_name=session.customer_name or (user.name if user else None),
        plan_name=session.product_name or session.offer_key,
        amount=payment.get("value") or session.amount,
        due_date=payment.get("dueDate"),
        payment_method=_humanize_payment_method(payment.get("billingType") or session.payment_method),
        kind=kind,
        email=session.customer_email or (user.email if user else None),
        phone=session.customer_phone or (user.whatsapp if user else None),
        dedupe_key=str(payment.get("id") or f"{session.token}:{payment.get('dueDate')}"),
    )


def _notify_gateway_modified_cakto_to_asaas(user: User) -> None:
    try:
        send_notification(
            event_key="gateway_modified_cakto_asaas",
            context={
                "user_name": user.name or "Não informado",
            },
        )
    except Exception:  # pragma: no cover - alerta não pode quebrar o checkout
        logger.exception("Falha ao enviar notificação ntfy de mudança de gateway.")


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


def _can_upgrade_subscription_in_place(subscription: Subscription | None) -> bool:
    if not subscription:
        return False
    provider = str(subscription.provider or "").strip().lower()
    return provider == "asaas" and bool(subscription.asaas_subscription_id)


def _should_upgrade_session_in_place(db: Session, session: CheckoutSession) -> bool:
    if not _is_upgrade_session(session):
        return False
    metadata = dict(session.metadata_json or {})
    if "upgrade_in_place" in metadata:
        return bool(metadata.get("upgrade_in_place"))
    return _can_upgrade_subscription_in_place(_resolve_target_subscription_for_upgrade(db, session))


def _complete_paid_checkout_session(db: Session, session: CheckoutSession) -> User:
    if _should_upgrade_session_in_place(db, session):
        user, _previous_plan = _apply_upgrade_after_payment(db, session)
        return user
    if _is_upgrade_session(session):
        # Plano novo pago: encerra a cobrança do plano anterior (assinatura no cartão ou Pix automático).
        _cancel_replaced_contracts_after_upgrade(db, session)
    return _upsert_paid_user_and_subscription(db, session)


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


def _with_optional_split(payload: dict[str, Any]) -> dict[str, Any]:
    if TEMP_DISABLE_CHECKOUT_SPLIT:
        payload.pop("split", None)
    return payload


def _apply_upgrade_after_payment(db: Session, session: CheckoutSession) -> tuple[User, str | None]:
    subscription = _resolve_target_subscription_for_upgrade(db, session)
    if not subscription or not subscription.asaas_subscription_id:
        raise HTTPException(status_code=400, detail="Assinatura ativa nÃ£o encontrada para upgrade.")

    client = _ensure_asaas_client()
    payload = _with_optional_split({
        "value": float(_parse_decimal(session.amount)),
        "cycle": _resolve_asaas_cycle(session.billing_cycle),
        "status": "ACTIVE",
        "updatePendingPayments": True,
        "externalReference": f"checkout_upgrade:{session.token}",
        "split": build_default_split_payload(),
    })
    client.update_subscription(subscription.asaas_subscription_id, payload)

    user = db.query(User).filter(User.id == subscription.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="UsuÃ¡rio da assinatura nÃ£o encontrado.")
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
    return user, previous_plan


def _cancel_replaced_contracts_after_upgrade(db: Session, session: CheckoutSession) -> None:
    metadata = dict(session.metadata_json or {})
    previous_subscription_id = str(metadata.get("replaced_asaas_subscription_id") or "").strip()
    current_subscription_id = str(metadata.get("asaas_subscription_id") or "").strip()
    current_authorization_id = str(metadata.get("asaas_pix_automatic_authorization_id") or "").strip()
    target_subscription = _resolve_target_subscription_for_upgrade(db, session)
    target_user_id = target_subscription.user_id if target_subscription else session.user_id
    client: AsaasClient | None = None
    changed = False

    # PIX Automatico nao cria um novo /subscriptions/{id}. Portanto, exigir um
    # current_subscription_id aqui fazia a assinatura convencional anterior
    # permanecer ativa depois do upgrade.
    if (
        previous_subscription_id
        and previous_subscription_id != current_subscription_id
        and not metadata.get("replaced_asaas_subscription_cancelled")
    ):
        client = client or _ensure_asaas_client()
        client.cancel_subscription(previous_subscription_id)
        metadata["replaced_asaas_subscription_cancelled"] = True
        if target_subscription and target_subscription.asaas_subscription_id == previous_subscription_id:
            target_subscription.asaas_subscription_id = None
            db.add(target_subscription)
        changed = True

    # Um cliente pode estar migrando de outra autorizacao PIX Automatica. As
    # sessoes antigas precisam ser canceladas no Asaas e localmente; caso
    # contrario o job de renovacao continua criando instrucoes na data antiga.
    if target_user_id:
        previous_pix_sessions = (
            db.query(CheckoutSession)
            .filter(
                CheckoutSession.user_id == target_user_id,
                CheckoutSession.payment_method == "pix",
                CheckoutSession.status == "paid",
            )
            .all()
        )
        cancelled_authorizations: set[str] = set()
        for previous_session in previous_pix_sessions:
            if previous_session.id == session.id or previous_session.token == session.token:
                continue
            previous_metadata = dict(previous_session.metadata_json or {})
            if str(previous_metadata.get("pix_mode") or "").strip().lower() != "automatic":
                continue
            authorization_id = str(
                previous_metadata.get("asaas_pix_automatic_authorization_id") or ""
            ).strip()
            if not authorization_id or authorization_id == current_authorization_id:
                continue
            if authorization_id not in cancelled_authorizations:
                client = client or _ensure_asaas_client()
                client.cancel_pix_automatic_authorization(
                    authorization_id,
                    reason="Substituida por upgrade de plano",
                )
                cancelled_authorizations.add(authorization_id)
            previous_metadata["asaas_pix_automatic_authorization_status"] = "CANCELLED"
            previous_metadata["replaced_by_upgrade_checkout_token"] = session.token
            previous_session.metadata_json = previous_metadata
            previous_session.status = "cancelled"
            previous_session.updated_at = _utcnow()
            db.add(previous_session)
            changed = True

    if not changed:
        return
    session.metadata_json = metadata
    db.add(session)
    db.commit()
    db.refresh(session)


# Nome antigo (o upgrade substituía o contrato anterior só no Pix); hoje vale para qualquer forma de pagamento.
_cancel_replaced_asaas_subscription_after_pix_upgrade = _cancel_replaced_contracts_after_upgrade


def _legacy_checkout_payload(record: CheckoutSettings) -> dict[str, Any]:
    return {
        "key": "default",
        "name": "Checkout padrÃ£o",
        "theme_mode": record.theme_mode or "dark",
        "desktop_image_url": record.desktop_image_url,
        "mobile_banner_url": record.mobile_banner_url,
        "active": True,
    }


def _normalize_offer_keys(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized = []
    for value in values:
        raw = str(value or "").strip().lower()
        if raw:
            normalized.append(raw)
    return normalized


def _serialize_pixels(record: CheckoutSettings) -> list[dict[str, Any]]:
    raw_items = record.pixels_json or DEFAULT_PIXELS
    pixels: list[dict[str, Any]] = []
    for item in raw_items:
        payload = dict(item or {})
        payload["name"] = str(payload.get("name") or "").strip()
        payload["pixel_id"] = str(payload.get("pixel_id") or "").strip()
        payload["access_token"] = str(payload.get("access_token") or "").strip()
        payload["active"] = bool(payload.get("active", True))
        payload["offer_keys"] = _normalize_offer_keys(payload.get("offer_keys"))
        pixels.append(CheckoutPixelOut.model_validate(payload).model_dump(mode="json"))
    return pixels


def _serialize_public_pixels(record: CheckoutSettings, offer_key: str) -> list[dict[str, Any]]:
    normalized_offer_key = str(offer_key or "").strip().lower()
    pixels = []
    for pixel in _serialize_pixels(record):
        offer_keys = set(pixel.get("offer_keys") or [])
        if not pixel.get("active"):
            continue
        if normalized_offer_key not in offer_keys:
            continue
        pixels.append(CheckoutPixelPublicOut.model_validate(pixel).model_dump(mode="json"))
    return pixels


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


def _active_pixels_for_offer(record: CheckoutSettings, offer_key: str) -> list[dict[str, Any]]:
    normalized_offer_key = str(offer_key or "").strip().lower()
    pixels = []
    for pixel in _serialize_pixels(record):
        if not pixel.get("active"):
            continue
        offer_keys = set(pixel.get("offer_keys") or [])
        if normalized_offer_key not in offer_keys:
            continue
        pixels.append(pixel)
    return pixels


def _meta_api_version() -> str:
    raw = getattr(settings, "meta_graph_api_version", None)
    value = str(raw or "").strip()
    return value or "v20.0"


def _build_meta_event_id(
    *,
    session: CheckoutSession,
    event_name: str,
    step: str | None = None,
    status: str | None = None,
    payment_method: str | None = None,
) -> str:
    parts = [
        session.token,
        (event_name or "").strip().lower(),
        (step or "").strip().lower(),
        (status or "").strip().lower(),
        (payment_method or "").strip().lower(),
    ]
    return "|".join(part or "-" for part in parts)


def _hash_meta_value(value: str | None) -> str | None:
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _meta_user_data(session: CheckoutSession, ip_address_value: str | None, user_agent: str | None) -> dict[str, Any]:
    email = _hash_meta_value(session.customer_email)
    phone = _hash_meta_value(_normalize_digits(session.customer_phone))
    user_data: dict[str, Any] = {
        "client_ip_address": ip_address_value,
        "client_user_agent": (user_agent or "").strip()[:2000] or None,
        "external_id": _hash_meta_value(session.token),
    }
    if email:
        user_data["em"] = [email]
    if phone:
        user_data["ph"] = [phone]
    return {key: value for key, value in user_data.items() if value}


def _meta_custom_data(
    session: CheckoutSession,
    *,
    event_name: str,
    step: str | None,
    status: str | None,
    payment_method: str | None,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    custom_data: dict[str, Any] = {
        "currency": "BRL",
        "value": float(session_first_payment_amount(session) or session.amount or 0),
        "content_name": session.product_name,
        "content_ids": [session.offer_key],
        "checkout_event_name": event_name,
        "checkout_step": step,
        "checkout_status": status,
        "checkout_payment_method": payment_method,
    }
    if metadata:
        for key in ("coupon_code", "applied_coupon_code", "pix_mode"):
            if metadata.get(key):
                custom_data[key] = metadata[key]
    return {key: value for key, value in custom_data.items() if value is not None and value != ""}


def _meta_events_for_checkout_event(
    *,
    session: CheckoutSession,
    event_name: str,
    step: str | None,
    status: str | None,
    payment_method: str | None,
) -> list[tuple[str, str]]:
    normalized_event = (event_name or "").strip().lower()
    normalized_status = (status or "").strip().lower()
    normalized_step = (step or "").strip().lower()
    normalized_payment = (payment_method or "").strip().lower()

    events: list[tuple[str, str]] = [("CheckoutStatus", _build_meta_event_id(
        session=session,
        event_name=normalized_event or "checkout_status",
        step=normalized_step,
        status=normalized_status,
        payment_method=normalized_payment,
    ))]

    if normalized_event in {"details_submit_success", "details_completed"}:
        events.append(("Lead", _build_meta_event_id(session=session, event_name="lead", step=normalized_step, status=normalized_status, payment_method=normalized_payment)))
    elif normalized_event in {"step_method_view"}:
        events.append(("Lead", _build_meta_event_id(session=session, event_name="lead", step=normalized_step, status=normalized_status, payment_method=normalized_payment)))
        events.append(("InitiateCheckout", _build_meta_event_id(session=session, event_name="initiate_checkout", step=normalized_step, status=normalized_status, payment_method=normalized_payment)))
    elif normalized_event in {"payment_method_click", "pix_started", "card_processing"}:
        events.append(("AddPaymentInfo", _build_meta_event_id(session=session, event_name="add_payment_info", step=normalized_step, status=normalized_status, payment_method=normalized_payment)))
    elif normalized_event in {"payment_success"} or normalized_status == "paid":
        events.append(("Purchase", _build_meta_event_id(session=session, event_name="purchase", step=normalized_step, status="paid", payment_method=normalized_payment)))

    return events


def _send_meta_pixel_event(
    *,
    pixel: dict[str, Any],
    event_name: str,
    event_id: str,
    session: CheckoutSession,
    step: str | None,
    status: str | None,
    payment_method: str | None,
    metadata: dict[str, Any] | None,
    ip_address_value: str | None,
    user_agent: str | None,
) -> None:
    pixel_id = str(pixel.get("pixel_id") or "").strip()
    access_token = str(pixel.get("access_token") or "").strip()
    if not pixel_id or not access_token:
        return

    payload = {
        "data": [
            {
                "event_name": event_name,
                "event_time": int(datetime.now(timezone.utc).timestamp()),
                "event_id": event_id,
                "action_source": "website",
                "user_data": _meta_user_data(session, ip_address_value, user_agent),
                "custom_data": _meta_custom_data(
                    session,
                    event_name=event_name,
                    step=step,
                    status=status,
                    payment_method=payment_method,
                    metadata=metadata,
                ),
            }
        ]
    }
    url = f"https://graph.facebook.com/{_meta_api_version()}/{pixel_id}/events"
    try:
        response = httpx.post(url, params={"access_token": access_token}, json=payload, timeout=10)
        if response.status_code >= 400:
            logger.error(
                "Meta CAPI retornou erro para pixel_id=%s status=%s body=%s",
                pixel_id,
                response.status_code,
                response.text[:1000],
            )
    except Exception:  # noqa: BLE001
        logger.exception("Erro ao enviar evento Meta CAPI para pixel_id=%s", pixel_id)


def _dispatch_meta_checkout_events(
    db: Session,
    *,
    session: CheckoutSession,
    event_name: str,
    step: str | None,
    status: str | None,
    payment_method: str | None,
    metadata: dict[str, Any] | None,
    ip_address_value: str | None,
    user_agent: str | None,
) -> None:
    settings_record = get_checkout_settings(db)
    pixels = _active_pixels_for_offer(settings_record, session.offer_key)
    if not pixels:
        return

    for meta_event_name, event_id in _meta_events_for_checkout_event(
        session=session,
        event_name=event_name,
        step=step,
        status=status,
        payment_method=payment_method,
    ):
        for pixel in pixels:
            _send_meta_pixel_event(
                pixel=pixel,
                event_name=meta_event_name,
                event_id=event_id,
                session=session,
                step=step,
                status=status,
                payment_method=payment_method,
                metadata=metadata,
                ip_address_value=ip_address_value,
                user_agent=user_agent,
            )


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
        pixels_json=[],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


SALES_SLOT_LABELS = {"monthly": "Mensal", "annual": "Anual"}


def _validate_sales_slots(offers: list[CheckoutOfferIn]) -> None:
    """Plano único: no máximo uma oferta como Mensal e uma como Anual, cada uma com o ciclo
    de cobrança igual ao que representa (senão a página mostraria um preço e cobraria outro)."""
    seen: dict[str, str] = {}
    for offer in offers:
        slot = offer.sales_slot
        if not slot:
            continue
        label = SALES_SLOT_LABELS[slot]
        if slot in seen:
            raise HTTPException(
                status_code=400,
                detail=f"Só uma oferta pode ser a {label} da página de vendas ({seen[slot]} e {offer.key}).",
            )
        if offer.billing_cycle != slot:
            raise HTTPException(
                status_code=400,
                detail=f"A oferta {offer.key} está como {label} na página de vendas, mas cobra no ciclo {SALES_SLOT_LABELS[offer.billing_cycle].lower()}.",
            )
        seen[slot] = offer.key


def _validate_offer_prices(offers: list[CheckoutOfferIn]) -> None:
    """A 1ª mensalidade promocional precisa ficar abaixo do valor cheio da oferta."""
    for offer in offers:
        if offer.first_payment_amount is None:
            continue
        if _quantize_money(_parse_decimal(offer.first_payment_amount)) >= _quantize_money(_parse_decimal(offer.amount)):
            raise HTTPException(
                status_code=400,
                detail=f"A 1ª mensalidade promocional da oferta {offer.key} precisa ser menor que o valor cheio.",
            )


def offer_first_payment_promo(offer: CheckoutOfferIn, now: datetime | None = None) -> Decimal | None:
    """Valor da 1ª mensalidade promocional em vigor (só ofertas mensais); None sem promoção ou depois do fim."""
    if offer.billing_cycle != "monthly" or offer.first_payment_amount is None:
        return None
    promo = _quantize_money(_parse_decimal(offer.first_payment_amount))
    if promo <= 0 or promo >= _quantize_money(_parse_decimal(offer.amount)):
        return None
    ends_at = offer.first_payment_ends_at
    if ends_at is not None:
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
        if (now or _utcnow()) >= ends_at:
            return None
    return promo


def offer_installment_options(offer: CheckoutOfferIn) -> list[InstallmentOption]:
    top = offer.max_installments if offer.billing_cycle == "annual" else 1
    return installment_options(offer.amount, top, offer.installment_fixed_values)


def get_public_sales_plan(db: Session) -> dict[str, Any]:
    """Ofertas do plano único (mensal e anual) para a página de vendas e a tela de planos.
    Vale a oferta ativa marcada no Admin Master; sem marcação, a primeira oferta ativa do plano
    Escala naquele ciclo, para a página não ficar sem preço enquanto a configuração não é feita."""
    record = get_checkout_settings(db)
    result: dict[str, Any] = {"monthly": None, "annual": None}
    if not record.is_active:
        return result
    active = [CheckoutOfferOut.model_validate(raw) for raw in _serialize_offers(record)]
    active = [offer for offer in active if offer.active]
    for slot in ("monthly", "annual"):
        chosen = next((offer for offer in active if offer.sales_slot == slot), None)
        if chosen is None:
            chosen = next(
                (offer for offer in active if offer.billing_cycle == slot and _normalize_plan_key(offer.plan_key) == "scale"),
                None,
            )
        if chosen is not None:
            options = offer_installment_options(chosen)
            top = options[-1] if options else None
            promo = offer_first_payment_promo(chosen)
            result[slot] = {
                "key": chosen.key,
                "title": chosen.title,
                "billing_cycle": chosen.billing_cycle,
                "amount": chosen.amount,
                "max_installments": top.count if top else 1,
                "installment_value": top.value if top and top.count > 1 else None,
                "first_payment_amount": promo,
                "first_payment_ends_at": chosen.first_payment_ends_at if promo is not None else None,
            }
    return result


def update_checkout_settings(db: Session, payload: CheckoutSettingsUpdate) -> CheckoutSettings:
    record = get_checkout_settings(db)
    checkouts = [item.model_dump(mode="json") for item in payload.checkouts]
    active_checkouts = [item for item in checkouts if item.get("active")]
    if not active_checkouts and checkouts:
        checkouts[0]["active"] = True
        active_checkouts = [checkouts[0]]

    fallback_checkout_key = active_checkouts[0]["key"] if active_checkouts else "default"
    _validate_sales_slots(payload.offers)
    _validate_offer_prices(payload.offers)
    offers = []
    for item in payload.offers:
        raw_offer = item.model_dump(mode="json")
        raw_offer["checkout_key"] = raw_offer.get("checkout_key") or fallback_checkout_key
        offers.append(raw_offer)

    record.is_active = payload.is_active
    record.offers_json = offers
    record.coupons_json = [item.model_dump(mode="json") for item in payload.coupons]
    record.checkouts_json = checkouts
    record.pixels_json = [item.model_dump(mode="json") for item in payload.pixels]
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
        "pixels": _serialize_pixels(record),
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
    raise HTTPException(status_code=404, detail="Oferta nÃ£o encontrada.")


def resolve_offer_checkout(record: CheckoutSettings, offer: CheckoutOfferOut) -> CheckoutAppearanceOut:
    active_checkouts = [CheckoutAppearanceOut.model_validate(item) for item in _serialize_checkouts(record) if item.get("active")]
    if not active_checkouts:
        return CheckoutAppearanceOut.model_validate(_legacy_checkout_payload(record))
    if offer.checkout_key:
        for checkout in active_checkouts:
            if checkout.key == offer.checkout_key:
                return checkout
    return active_checkouts[0]


def resolve_offer_pixels(record: CheckoutSettings, offer: CheckoutOfferOut) -> list[dict[str, Any]]:
    return _serialize_public_pixels(record, offer.key)


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
            raise HTTPException(status_code=400, detail="Cupom invÃ¡lido para esta oferta.")
        return coupon
    raise HTTPException(status_code=400, detail="Cupom nÃ£o encontrado ou inativo.")


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


def preview_coupon_amount(
    db: Session,
    *,
    offer: CheckoutOfferOut,
    coupon_code: str,
) -> dict[str, Any]:
    settings_record = get_checkout_settings(db)
    coupon = resolve_coupon(settings_record, coupon_code, offer.key)
    if not coupon:
        raise HTTPException(status_code=400, detail="Cupom nÃ£o encontrado ou inativo.")
    original_amount, final_amount, discount_amount = apply_coupon_to_offer_amount(offer, coupon)
    return {
        "offer_key": offer.key,
        "amount": final_amount,
        "original_amount": original_amount,
        "discount_amount": discount_amount or Decimal("0.00"),
        "applied_coupon_code": coupon.code,
    }


def _ensure_asaas_client() -> AsaasClient:
    if not settings.asaas_api_key:
        raise HTTPException(status_code=500, detail="Asaas nÃ£o configurado.")
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


def _find_existing_checkout_identity(db: Session, email: str, document: str) -> tuple[str, User] | None:
    normalized_email = (email or "").strip().lower()
    digits = _normalize_digits(document)
    sanitized_cpf = func.replace(func.replace(func.replace(func.coalesce(User.cpf, ""), ".", ""), "-", ""), "/", "")
    sanitized_cnpj = func.replace(func.replace(func.replace(func.coalesce(User.cnpj, ""), ".", ""), "-", ""), "/", "")

    if normalized_email:
        user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
        if user:
            return "email", user

    if digits:
        user = db.query(User).filter(or_(sanitized_cpf == digits, sanitized_cnpj == digits)).first()
        if user:
            return "document", user

    return None


def _raise_if_registered_checkout_identity(db: Session, session: CheckoutSession) -> None:
    if _is_upgrade_session(session):
        return
    existing_identity = _find_existing_checkout_identity(db, session.customer_email, session.customer_document)
    if not existing_identity:
        return
    field, _user = existing_identity
    detail = (
        "Este e-mail já está cadastrado. Faça login para acessar sua conta."
        if field == "email"
        else "Este CPF ou CNPJ já está cadastrado. Faça login para acessar sua conta."
    )
    raise HTTPException(status_code=409, detail=detail)


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
        _build_asaas_customer_payload(
            name=name,
            email=email,
            document=digits,
            phone=phone,
            session_token=session_token,
        )
    )
    customer_id = customer.get("id")
    if not customer_id:
        raise HTTPException(status_code=502, detail="Asaas nÃ£o retornou o cliente.")
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
    allow_existing_user: bool = False,
) -> CheckoutSession:
    settings_record = get_checkout_settings(db)
    coupon = resolve_coupon(settings_record, coupon_code, offer.key)
    original_amount, final_amount, discount_amount = apply_coupon_to_offer_amount(offer, coupon)
    existing_user = _find_existing_user(db, customer_email, customer_document) if allow_existing_user else None
    if not allow_existing_user:
        existing_identity = _find_existing_checkout_identity(db, customer_email, customer_document)
        if existing_identity:
            field, _user = existing_identity
            detail = (
                "Este e-mail já está cadastrado. Faça login para acessar sua conta."
                if field == "email"
                else "Este CPF ou CNPJ já está cadastrado. Faça login para acessar sua conta."
            )
            raise HTTPException(status_code=409, detail=detail)
    token = secrets.token_urlsafe(24)
    metadata_payload = dict(metadata or {})
    metadata_payload.update(
        {
            "original_amount": str(original_amount),
            "discount_amount": str(discount_amount or Decimal("0.00")),
            "applied_coupon_code": coupon.code if coupon else None,
        }
    )
    # Parcelas do cartão e promoção da 1ª mensalidade valem pelo que a oferta tinha quando a compra
    # começou. Com cupom, a parcela fixa (ex.: 12x de R$ 97) não vale: as parcelas seguem a tabela.
    metadata_payload["max_installments"] = offer.max_installments if offer.billing_cycle == "annual" else 1
    metadata_payload["installment_fixed_values"] = (
        {} if discount_amount else {count: str(value) for count, value in offer.installment_fixed_values.items()}
    )
    # A promoção é para quem assina pela primeira vez: migração de quem já paga um plano é no valor cheio.
    migrating = bool(metadata_payload.get("upgrade_mode")) and not metadata_payload.get("first_subscription")
    promo = None if migrating else offer_first_payment_promo(offer)
    if promo is not None and promo < final_amount:
        metadata_payload["first_payment_amount"] = str(promo)
        metadata_payload["first_payment_ends_at"] = (
            offer.first_payment_ends_at.isoformat() if offer.first_payment_ends_at else None
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
        user_id=existing_user.id if existing_user else None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    _notify_checkout_started(session)
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
    subscription = user.subscription
    metadata = {
        "upgrade_mode": True,
        "target_user_id": user.id,
        "current_plan": user.plan,
        # Assina pela primeira vez (teste grátis ou conta sem plano pago): vale a promoção da 1ª mensalidade.
        "first_subscription": subscription is None
        or (
            _parse_decimal(subscription.mrr_amount or 0) <= 0
            and not subscription.asaas_subscription_id
            and not subscription.cakto_subscription_code
            and str(subscription.status or "").strip().lower() not in {"active", "past_due", "cancel_at_period_end"}
        ),
        "locked_profile_fields": {
            "customer_name": bool((user.name or "").strip()),
            "customer_email": bool((user.email or "").strip()),
            "customer_document": bool((document or "").strip()),
            "customer_phone": bool((phone or "").strip()),
            "customer_zipcode": bool((zipcode or "").strip()),
        },
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
        allow_existing_user=True,
    )


def update_upgrade_checkout_session_details(
    db: Session,
    *,
    session: CheckoutSession,
    user: User,
    customer_name: str,
    customer_email: str,
    customer_document: str,
    customer_phone: str,
    customer_zipcode: str,
) -> CheckoutSession:
    if not _is_upgrade_session(session):
        raise HTTPException(status_code=400, detail="Sessao nao pertence ao fluxo de upgrade.")

    metadata = dict(session.metadata_json or {})
    target_user_id = metadata.get("target_user_id")
    try:
        parsed_target_user_id = int(target_user_id)
    except (TypeError, ValueError):
        parsed_target_user_id = None
    if parsed_target_user_id is None or parsed_target_user_id != int(user.id):
        raise HTTPException(status_code=403, detail="Sessao de upgrade invalida para este usuario.")

    if session.status == "paid":
        raise HTTPException(status_code=400, detail="Sessao ja concluida.")

    document_digits = _normalize_digits(customer_document)
    phone_digits = _normalize_digits(customer_phone)
    zipcode_digits = _normalize_digits(customer_zipcode)
    if len(document_digits) not in {11, 14}:
        raise HTTPException(status_code=400, detail="Informe um CPF ou CNPJ valido.")
    if len(phone_digits) < 10:
        raise HTTPException(status_code=400, detail="Informe um telefone valido com DDD.")
    if len(zipcode_digits) != 8:
        raise HTTPException(status_code=400, detail="Informe um CEP valido.")

    session.customer_name = customer_name.strip()
    session.customer_email = customer_email.strip().lower()
    session.customer_document = document_digits
    session.customer_phone = phone_digits
    session.customer_zipcode = zipcode_digits
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


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
    _dispatch_meta_checkout_events(
        db,
        session=session,
        event_name=event.event_name,
        step=event.step,
        status=event.status,
        payment_method=event.payment_method,
        metadata=metadata,
        ip_address_value=ip_address_value,
        user_agent=user_agent,
    )


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


def get_checkout_offer_reports(
    db: Session,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    record = get_checkout_settings(db)
    offers_by_key = {item["key"]: item for item in _serialize_offers(record)}
    reports: dict[str, dict[str, Any]] = {}

    for raw_offer in offers_by_key.values():
        normalized_key = str(raw_offer.get("key") or "").strip().lower()
        reports[normalized_key] = {
            "offer_key": normalized_key,
            "offer_title": str(raw_offer.get("title") or normalized_key or "Oferta"),
            "checkout_key": raw_offer.get("checkout_key"),
            "is_active": bool(raw_offer.get("active")),
            "signed_count": 0,
            "upgrade_count": 0,
            "direct_count": 0,
            "total_count": 0,
            "last_signed_at": None,
        }

    leads = (
        db.query(CheckoutLead)
        .options(joinedload(CheckoutLead.session))
        .order_by(CheckoutLead.updated_at.desc())
        .all()
    )
    for lead in leads:
        if lead.signed_at is None:
            continue
        signed_day = lead.signed_at.date()
        if start_date and signed_day < start_date:
            continue
        if end_date and signed_day > end_date:
            continue
        normalized_key = (lead.offer_key or "").strip().lower()
        bucket = reports.get(normalized_key)
        if not bucket:
            bucket = {
                "offer_key": normalized_key,
                "offer_title": normalized_key or "Oferta removida",
                "checkout_key": None,
                "is_active": False,
                "signed_count": 0,
                "upgrade_count": 0,
                "direct_count": 0,
                "total_count": 0,
                "last_signed_at": None,
            }
            reports[normalized_key] = bucket

        session_metadata = getattr(lead.session, "metadata_json", None) or {}
        is_upgrade = bool(session_metadata.get("upgrade_mode"))

        bucket["signed_count"] += 1
        bucket["total_count"] += 1
        if is_upgrade:
            bucket["upgrade_count"] += 1
        else:
            bucket["direct_count"] += 1
        if lead.signed_at and (not bucket["last_signed_at"] or lead.signed_at > bucket["last_signed_at"]):
            bucket["last_signed_at"] = lead.signed_at

    ordered = sorted(
        reports.values(),
        key=lambda item: (item["total_count"], item["signed_count"], item["offer_title"]),
        reverse=True,
    )
    return [CheckoutOfferReportItemOut.model_validate(item).model_dump(mode="json") for item in ordered]


def get_checkout_session_by_token(db: Session, token: str) -> CheckoutSession:
    session = db.query(CheckoutSession).filter(CheckoutSession.token == token).first()
    if not session:
        raise HTTPException(status_code=404, detail="SessÃ£o de checkout nÃ£o encontrada.")
    return session


def session_first_payment_amount(session: CheckoutSession) -> Decimal | None:
    """1ª cobrança promocional desta compra (mensal), ou None quando ela é o valor cheio."""
    raw = (session.metadata_json or {}).get("first_payment_amount")
    if raw in (None, "") or session.billing_cycle != "monthly":
        return None
    value = _quantize_money(_parse_decimal(raw))
    return value if Decimal("0") < value < _quantize_money(_parse_decimal(session.amount)) else None


def session_installment_options(session: CheckoutSession) -> list[InstallmentOption]:
    metadata = session.metadata_json or {}
    top = 1
    if session.billing_cycle == "annual":
        try:
            top = int(metadata.get("max_installments") or 1)
        except (TypeError, ValueError):
            top = 1
    return installment_options(session.amount, top, metadata.get("installment_fixed_values") or {})


def serialize_checkout_session(db: Session, session: CheckoutSession) -> dict[str, Any]:
    user = session.user or _find_existing_user(db, session.customer_email, session.customer_document)
    requires_password_setup = not bool(user and user.hashed_password and session.password_defined_at)
    user_exists = bool(user)
    metadata = session.metadata_json or {}
    pix_mode = metadata.get("pix_mode")
    if session.payment_method == "pix" and pix_mode not in {"automatic", "conventional"}:
        if metadata.get("asaas_pix_automatic_authorization_id"):
            pix_mode = "automatic"
        elif session.asaas_payment_id or metadata.get("asaas_subscription_id"):
            pix_mode = "conventional"
        else:
            pix_mode = None
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
        "pix_mode": pix_mode,
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
        "locked_profile_fields": metadata.get("locked_profile_fields"),
        "first_payment_amount": session_first_payment_amount(session),
        "installment_options": [option.as_dict() for option in session_installment_options(session)],
    }


def start_pix_payment(db: Session, session: CheckoutSession) -> CheckoutSession:
    existing_metadata = dict(session.metadata_json or {})
    has_automatic_authorization = bool(existing_metadata.get("asaas_pix_automatic_authorization_id"))
    if session.payment_method == "pix" and session.status in {"awaiting_payment", "paid"}:
        if has_automatic_authorization:
            return session
        if session.asaas_payment_id:
            return refresh_session_status(db, session) if session.status != "paid" else session
    _raise_if_registered_checkout_identity(db, session)
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
        "description": session.product_name[:35],
        "immediateQrCode": {
            # Com a promoção da 1ª mensalidade, só o pagamento de agora sai mais barato; as
            # renovações (value) seguem no valor cheio.
            "originalValue": float(session_first_payment_amount(session) or session.amount),
            "expirationSeconds": 3600,
            "description": session.product_name[:35],
        },
    }
    authorization = client.create_pix_automatic_authorization(auth_payload)
    authorization_id = _extract_asaas_resource_id(authorization.get("id"))
    if not authorization_id:
        raise HTTPException(status_code=502, detail="Asaas nao retornou autorizacao de Pix Automatico.")
    immediate_qr = _extract_pix_automatic_qr_code(authorization)
    if not immediate_qr.get("payload"):
        raise HTTPException(
            status_code=502,
            detail="Asaas nao retornou o QR Code do Pix Automatico. Nenhuma cobranca PIX convencional foi criada.",
        )
    pix_mode = "automatic"

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
    metadata["pix_mode"] = pix_mode
    metadata["asaas_pix_automatic_authorization_status"] = str(authorization.get("status") or "CREATED").upper()
    metadata["asaas_pix_automatic_start_date"] = start_date
    metadata["asaas_pix_automatic_conciliation_id"] = immediate_qr.get("conciliationIdentifier")
    if _is_upgrade_session(session):
        # O upgrade via PIX precisa substituir a recorrencia anterior somente
        # depois que a nova autorizacao automatica for paga e ativada.
        metadata["upgrade_in_place"] = False
        target_subscription = _resolve_target_subscription_for_upgrade(db, session)
        if target_subscription and target_subscription.asaas_subscription_id:
            metadata["replaced_asaas_subscription_id"] = target_subscription.asaas_subscription_id
    if authorization_id:
        metadata["asaas_pix_automatic_authorization_id"] = authorization_id
    session.metadata_json = metadata
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def _saved_card_token(
    client: AsaasClient,
    payment: dict[str, Any],
    *,
    customer_id: str,
    credit_card: dict[str, Any],
    holder_info: dict[str, Any],
    remote_ip: str,
) -> str | None:
    """Token do cartão no Asaas, para cobrar a renovação do anual parcelado sem pedir o cartão de
    novo. Vem na resposta da cobrança quando a tokenização está ligada; senão, salva à parte."""
    card = payment.get("creditCard") if isinstance(payment.get("creditCard"), dict) else {}
    token = str(card.get("creditCardToken") or "").strip()
    if token:
        return token
    try:
        result = client.tokenize_credit_card(
            {
                "customer": customer_id,
                "creditCard": credit_card,
                "creditCardHolderInfo": holder_info,
                "remoteIp": remote_ip,
            }
        )
    except Exception:  # noqa: BLE001 - a compra já foi feita; sem token, só a renovação fica manual
        logger.exception("Cartão não foi salvo no Asaas para a renovação do anual parcelado (cliente %s).", customer_id)
        return None
    return str((result or {}).get("creditCardToken") or "").strip() or None


def start_card_payment(db: Session, session: CheckoutSession, payload: dict[str, Any]) -> CheckoutSession:
    if session.asaas_payment_id and session.payment_method == "card" and session.status in {"awaiting_payment", "processing", "paid"}:
        return refresh_session_status(db, session) if session.status != "paid" else session
    _raise_if_registered_checkout_identity(db, session)
    try:
        requested_installments = int(payload.get("installment_count") or 1)
    except (TypeError, ValueError):
        requested_installments = 1
    # O valor vem sempre do servidor: o número de parcelas escolhido precisa ser uma das opções.
    option = option_for(session_installment_options(session), requested_installments)
    if option is None:
        raise HTTPException(status_code=400, detail="Escolha uma das parcelas oferecidas.")
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
    remote_ip = payload.get("remote_ip") or "127.0.0.1"
    metadata = dict(session.metadata_json or {})
    if card_last4:
        metadata["card_last4"] = card_last4
    if card_brand:
        metadata["card_brand"] = card_brand
    metadata["remote_ip"] = remote_ip
    is_upgrade = _is_upgrade_session(session)
    if is_upgrade:
        # Migração de plano: o plano novo é um contrato novo (assinatura ou cobrança parcelada) e o
        # anterior é cancelado depois que o pagamento é confirmado. A assinatura antiga não é mais
        # atualizada "no lugar": ela mantinha a data de vencimento antiga e cobrava o plano novo de
        # novo dias depois.
        metadata["upgrade_in_place"] = False
        target_subscription = _resolve_target_subscription_for_upgrade(db, session)
        if target_subscription and target_subscription.asaas_subscription_id:
            metadata["replaced_asaas_subscription_id"] = target_subscription.asaas_subscription_id
    session.metadata_json = metadata
    external_reference = f"checkout_upgrade:{session.token}" if is_upgrade else f"checkout:{session.token}"
    session.asaas_customer_id = customer_id
    session.payment_method = "card"
    session.status = "processing"
    credit_card = {
        "holderName": payload["holder_name"],
        "number": _normalize_digits(payload["card_number"]),
        "expiryMonth": str(payload["expiry_month"]),
        "expiryYear": str(payload["expiry_year"]),
        "ccv": str(payload["ccv"]),
    }
    holder_info = {
        "name": session.customer_name,
        "email": session.customer_email,
        "cpfCnpj": session.customer_document,
        "postalCode": session.customer_zipcode,
        "addressNumber": "S/N",
        "phone": session.customer_phone,
        "mobilePhone": session.customer_phone,
    }
    first_payment: dict[str, Any] = {}
    if option.count > 1:
        # Anual parcelado: uma cobrança parcelada no cartão (não é assinatura do Asaas). A
        # renovação, daqui a 12 meses, é cobrada pelo job horário no cartão salvo, nas mesmas parcelas.
        installment_payload: dict[str, Any] = _with_optional_split({
            "customer": customer_id,
            "billingType": "CREDIT_CARD",
            "installmentCount": option.count,
            "installmentValue": float(option.value),
            "dueDate": _billing_today(),
            "description": f"{session.product_name} ({option.count}x)",
            "externalReference": external_reference,
            "split": build_default_split_payload(),
            "creditCard": credit_card,
            "creditCardHolderInfo": holder_info,
            "remoteIp": remote_ip,
        })
        first_payment = client.create_payment(installment_payload)
        metadata = dict(session.metadata_json or {})
        metadata.update(
            {
                "card_installments": option.count,
                "card_installment_value": str(option.value),
                "card_total": str(option.total),
                "asaas_installment_id": _extract_asaas_resource_id(first_payment.get("installment")),
                "card_token": _saved_card_token(
                    client,
                    first_payment,
                    customer_id=customer_id,
                    credit_card=credit_card,
                    holder_info=holder_info,
                    remote_ip=remote_ip,
                ),
            }
        )
        session.metadata_json = metadata
    else:
        first_value = session_first_payment_amount(session) or amount
        subscription_payload: dict[str, Any] = _with_optional_split({
            "customer": customer_id,
            "billingType": "CREDIT_CARD",
            "nextDueDate": _billing_today(),
            "cycle": _resolve_asaas_cycle(session.billing_cycle),
            "value": float(first_value),
            "description": session.product_name,
            "externalReference": external_reference,
            "split": build_default_split_payload(),
            "creditCard": credit_card,
            "creditCardHolderInfo": holder_info,
            "remoteIp": remote_ip,
        })
        subscription = client.create_subscription(subscription_payload)
        subscription_id = _extract_asaas_resource_id(subscription.get("id"))
        if not subscription_id:
            raise HTTPException(status_code=502, detail="Asaas nao retornou assinatura de cartao.")
        payments = client.list_subscription_payments(subscription_id)
        first_payment = _pick_checkout_subscription_payment(payments)
        metadata = dict(session.metadata_json or {})
        metadata["asaas_subscription_id"] = subscription_id
        if first_value != amount:
            # 1ª mensalidade promocional: a assinatura nasce no valor da promoção (a cobrança de
            # agora) e passa ao valor cheio para as próximas. updatePendingPayments=False não mexe
            # na 1ª cobrança, mesmo que ela ainda esteja em análise. Se falhar, o job horário tenta de novo.
            metadata["pending_subscription_value"] = str(amount)
            session.metadata_json = metadata
            _apply_pending_subscription_value(client, session, update_pending_payments=False)
            metadata = dict(session.metadata_json or {})
        session.metadata_json = metadata

    payment_id = first_payment.get("id")
    if payment_id:
        metadata = dict(session.metadata_json or {})
        metadata.setdefault("first_payment_id", str(payment_id))
        session.metadata_json = metadata
        session.asaas_payment_id = str(payment_id)
        mapped = _map_asaas_payment_status(first_payment.get("status"))
        if mapped:
            session.status = mapped
        if session.status == "paid":
            session.paid_at = _utcnow()
            _complete_paid_checkout_session(db, session)
            _dispatch_meta_checkout_events(
                db,
                session=session,
                event_name="payment_success",
                step="success",
                status="paid",
                payment_method=session.payment_method,
                metadata=dict(session.metadata_json or {}),
                ip_address_value=None,
                user_agent=None,
            )
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _apply_pending_subscription_value(
    client: AsaasClient, session: CheckoutSession, *, update_pending_payments: bool
) -> bool:
    """Passa a assinatura do Asaas para o valor cheio depois da 1ª mensalidade promocional."""
    metadata = dict(session.metadata_json or {})
    pending = str(metadata.get("pending_subscription_value") or "").strip()
    subscription_id = str(metadata.get("asaas_subscription_id") or "").strip()
    if not pending or not subscription_id:
        return False
    try:
        client.update_subscription(
            subscription_id,
            {"value": float(_parse_decimal(pending)), "updatePendingPayments": update_pending_payments},
        )
    except Exception:  # noqa: BLE001 - a compra já foi feita; o job horário tenta de novo
        logger.exception("Assinatura %s não passou para o valor cheio depois da 1ª mensalidade.", subscription_id)
        return False
    metadata.pop("pending_subscription_value", None)
    metadata["subscription_value_updated_at"] = _utcnow().isoformat()
    session.metadata_json = metadata
    return True

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

    previous_provider = (subscription.provider or "").strip().lower()
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
    if previous_provider == "cakto":
        _notify_gateway_modified_cakto_to_asaas(user)
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


def _renew_paid_pix_automatic_subscription(db: Session, session: CheckoutSession) -> User | None:
    user = session.user or _find_existing_user(db, session.customer_email, session.customer_document)
    if not user or not user.subscription:
        return None
    subscription = user.subscription
    now = _utcnow()
    current_valid_until = subscription.valid_until
    if current_valid_until and current_valid_until.tzinfo is None and now.tzinfo is not None:
        now_for_comparison = now.replace(tzinfo=None)
    else:
        now_for_comparison = now
    base = current_valid_until if current_valid_until and current_valid_until > now_for_comparison else now_for_comparison
    subscription.valid_until = base + _duration_from_cycle(session.billing_cycle)
    subscription.status = "active"
    subscription.failed_attempts = 0
    user.plan = session.plan_key
    user.is_active = True
    db.add_all([user, subscription])
    _notify_checkout_subscription_push(
        scenario=SubscriptionPushScenario.RENEWED,
        session=session,
        user=user,
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
    metadata = dict(session.metadata_json or {})
    automatic_authorization_id = str(metadata.get("asaas_pix_automatic_authorization_id") or "").strip()

    if session.payment_method == "pix" and automatic_authorization_id:
        authorization = client.get_pix_automatic_authorization(automatic_authorization_id)
        authorization_status = str(authorization.get("status") or "").upper()
        metadata["asaas_pix_automatic_authorization_status"] = authorization_status or "CREATED"
        immediate_qr = _extract_pix_automatic_qr_code(authorization)
        session.pix_copy_paste = immediate_qr.get("payload") or session.pix_copy_paste
        session.pix_qr_code_base64 = immediate_qr.get("encodedImage") or session.pix_qr_code_base64
        session.metadata_json = metadata
        if authorization_status == "ACTIVE" and session.status != "paid":
            session.status = "paid"
            session.paid_at = session.paid_at or _utcnow()
            if not metadata.get("asaas_pix_automatic_next_due_date"):
                metadata["asaas_pix_automatic_next_due_date"] = _next_pix_automatic_due_date(
                    date.fromisoformat(_billing_today()), session.billing_cycle
                ).isoformat()
                session.metadata_json = metadata
            _complete_paid_checkout_session(db, session)
        elif authorization_status in {"CANCELLED", "REFUSED"} and session.status != "paid":
            session.status = "failed"
        elif authorization_status == "EXPIRED" and session.status != "paid":
            session.status = "expired"
        session.updated_at = _utcnow()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

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
                    _complete_paid_checkout_session(db, session)
                _dispatch_meta_checkout_events(
                    db,
                    session=session,
                    event_name="payment_success",
                    step="success",
                    status="paid",
                    payment_method=session.payment_method,
                    metadata=dict(session.metadata_json or {}),
                    ip_address_value=None,
                    user_agent=None,
                )
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
        _complete_paid_checkout_session(db, session)
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def _mark_checkout_subscription_overdue(session: CheckoutSession, payment: dict[str, Any]) -> None:
    user = session.user
    subscription = user.subscription if user else None
    if subscription is None or (subscription.provider or "").strip().lower() != "asaas":
        return
    remote_id = str(payment.get("subscription") or "").strip()
    same_contract = subscription.external_reference == f"checkout:{session.token}" or (
        remote_id and remote_id == (subscription.asaas_subscription_id or "")
    )
    if not same_contract or (subscription.status or "").strip().lower() not in {"active", "past_due"}:
        return
    mark_subscription_overdue(subscription, payment.get("dueDate"))
    _notify_checkout_payment_overdue(session, payment, "Renovação")


RENEWAL_PAID_EVENTS = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}
RENEWAL_FAILED_EVENTS = {
    "PAYMENT_CREDIT_CARD_CAPTURE_REFUSED",
    "PAYMENT_REPROVED_BY_RISK_ANALYSIS",
    "PAYMENT_DELETED",
    "PAYMENT_REFUNDED",
}


def _payment_due_date(payment: dict[str, Any]) -> date | None:
    raw = str(payment.get("dueDate") or "").strip()[:10]
    try:
        return date.fromisoformat(raw) if raw else None
    except ValueError:
        return None


def _session_contract_subscription_ids(db: Session, session: CheckoutSession) -> set[str]:
    """Assinaturas do Asaas que pertencem a esta compra: a criada nela e, nos upgrades antigos feitos
    "no lugar", a assinatura do cliente que passou a apontar para esta compra."""
    ids = {str((session.metadata_json or {}).get("asaas_subscription_id") or "").strip()}
    user = session.user or _find_existing_user(db, session.customer_email, session.customer_document)
    subscription = user.subscription if user else None
    if subscription is not None and str(subscription.external_reference or "") in {
        f"checkout:{session.token}",
        f"checkout_upgrade:{session.token}",
    }:
        ids.add(str(subscription.asaas_subscription_id or "").strip())
    ids.discard("")
    return ids


def _is_card_subscription_renewal(db: Session, session: CheckoutSession, payment: dict[str, Any]) -> bool:
    """Cobrança de renovação da assinatura no cartão: do mesmo contrato do Asaas e vencendo depois
    da compra. Não conta o pagamento da compra (nem o aviso de "recebido" dele, uns 30 dias depois)."""
    if session.payment_method != "card" or not session.paid_at or payment.get("installment"):
        return False
    metadata = session.metadata_json or {}
    remote = _extract_asaas_resource_id(payment.get("subscription"))
    payment_id = str(payment.get("id") or "").strip()
    if not remote or not payment_id or remote not in _session_contract_subscription_ids(db, session):
        return False
    if payment_id == str(metadata.get("first_payment_id") or ""):
        return False
    due = _payment_due_date(payment)
    paid_at = session.paid_at if session.paid_at.tzinfo else session.paid_at.replace(tzinfo=timezone.utc)
    return due is not None and due > paid_at.astimezone(ZoneInfo("America/Sao_Paulo")).date() + timedelta(days=7)


def _extend_checkout_subscription(db: Session, session: CheckoutSession, *, renewed_from: date | None) -> bool:
    """Renovação paga: estende a assinatura do contrato desta compra por mais um ciclo, contado do
    vencimento renovado (pagar atrasado não encurta o período). Repetir é inofensivo."""
    user = session.user or _find_existing_user(db, session.customer_email, session.customer_document)
    subscription = user.subscription if user else None
    if subscription is None:
        return False
    # O cliente pode ter migrado de plano depois: só mexe se a assinatura ainda é desta compra.
    if str(subscription.external_reference or "") not in {f"checkout:{session.token}", f"checkout_upgrade:{session.token}"}:
        return False
    period = _duration_from_cycle(session.billing_cycle)
    now = _utcnow()
    current = subscription.valid_until
    if current is not None and current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if renewed_from is not None:
        start = datetime(renewed_from.year, renewed_from.month, renewed_from.day, 23, 59, tzinfo=ZoneInfo("America/Sao_Paulo"))
        new_valid_until = start + period
    else:
        new_valid_until = max(current or now, now) + period
    if current is not None and current > new_valid_until:
        new_valid_until = current
    subscription.valid_until = new_valid_until
    subscription.status = "active"
    subscription.failed_attempts = 0
    user.plan = session.plan_key
    user.is_active = True
    db.add_all([user, subscription])
    _notify_checkout_subscription_push(scenario=SubscriptionPushScenario.RENEWED, session=session, user=user)
    return True


def _handle_card_subscription_renewal(db: Session, session: CheckoutSession, payment: dict[str, Any], event: str) -> None:
    metadata = dict(session.metadata_json or {})
    payment_id = str(payment.get("id") or "").strip()
    if event in RENEWAL_PAID_EVENTS:
        renewed = [str(item) for item in (metadata.get("card_renewed_payment_ids") or [])]
        if payment_id not in renewed and _extend_checkout_subscription(db, session, renewed_from=_payment_due_date(payment)):
            renewed.append(payment_id)
            metadata["card_renewed_payment_ids"] = renewed[-36:]
    elif event == "PAYMENT_OVERDUE":
        # Renovação não paga: inadimplente (no ar por 3 dias, cobrança segue por 30).
        _mark_checkout_subscription_overdue(session, payment)
    session.metadata_json = metadata
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()


def _renewal_key_from_reference(reference: str) -> str:
    parts = str(reference or "").split(":")
    return parts[2] if len(parts) >= 3 else ""


def _apply_installment_renewal(db: Session, session: CheckoutSession, key: str) -> None:
    metadata = dict(session.metadata_json or {})
    renewal = dict(metadata.get("installment_renewal") or {})
    paid_keys = [str(item) for item in (metadata.get("installment_renewal_paid_keys") or [])]
    if key and key not in paid_keys:
        try:
            renewed_from = date.fromisoformat(key)
        except ValueError:
            renewed_from = None
        if _extend_checkout_subscription(db, session, renewed_from=renewed_from):
            paid_keys.append(key)
            metadata["installment_renewal_paid_keys"] = paid_keys[-12:]
    if renewal.get("key") == key:
        renewal["state"] = "paid"
        metadata["installment_renewal"] = renewal
    session.metadata_json = metadata


def _handle_installment_renewal_payment(db: Session, session: CheckoutSession, payment: dict[str, Any], event: str) -> None:
    """Avisos da cobrança de renovação do anual parcelado (criada pelo job horário)."""
    key = _renewal_key_from_reference(str(payment.get("externalReference") or ""))
    status = _map_asaas_payment_status(payment.get("status"))
    if event in RENEWAL_PAID_EVENTS or (status == "paid" and not event.startswith("PAYMENT_REFUND")):
        _apply_installment_renewal(db, session, key)
    elif event in RENEWAL_FAILED_EVENTS or status in {"failed", "refunded"}:
        metadata = dict(session.metadata_json or {})
        renewal = dict(metadata.get("installment_renewal") or {})
        if renewal.get("key") == key and renewal.get("state") != "paid":
            renewal["state"] = "failed"
            metadata["installment_renewal"] = renewal
            session.metadata_json = metadata
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()


def _existing_renewal_payment(client: AsaasClient, reference: str) -> dict[str, Any] | None:
    """Cobrança de renovação que já existe no Asaas para esta referência (evita cobrar duas vezes)."""
    rows = (client.list_payments(externalReference=reference, limit=20) or {}).get("data") or []
    alive = [row for row in rows if str(row.get("status") or "").upper() not in {"REFUSED", "CREDIT_CARD_CAPTURE_REFUSED", "REFUNDED", "DELETED"} and not row.get("deleted")]
    if not alive:
        return None
    paid = [row for row in alive if _map_asaas_payment_status(row.get("status")) == "paid"]
    return (paid or alive)[0]


def renew_due_installment_subscriptions(db: Session, client: AsaasClient, now: datetime | None = None) -> int:
    """Renovação do anual parcelado: no vencimento, cobra de novo no cartão salvo, nas mesmas
    parcelas e no mesmo valor da compra. Uma tentativa por dia; recusado, a assinatura segue a
    regra de inadimplência (3 dias no ar, 30 cobrando). Cancelada, não renova (o status deixa de
    ser ativo/inadimplente). Antes de cobrar, trava a compra e confere no Asaas se a cobrança daquele
    vencimento já existe, para nunca cobrar duas vezes (os dois servidores rodam este job)."""
    now = now or _utcnow()
    today = now.astimezone(ZoneInfo("America/Sao_Paulo")).date()
    candidates = (
        db.query(Subscription)
        .filter(
            Subscription.provider == "asaas",
            Subscription.status.in_(("active", "past_due")),
            Subscription.valid_until.isnot(None),
            Subscription.valid_until <= now,
            Subscription.asaas_subscription_id.is_(None),
            or_(Subscription.external_reference.like("checkout:%"), Subscription.external_reference.like("checkout_upgrade:%")),
        )
        .all()
    )
    charged = 0
    for subscription in candidates:
        token = _extract_checkout_session_token(str(subscription.external_reference or ""))
        if not token:
            continue
        session = (
            db.query(CheckoutSession)
            .filter(CheckoutSession.token == token)
            .with_for_update(skip_locked=True)
            .populate_existing()
            .first()
        )
        if session is None:
            db.rollback()
            continue
        metadata = dict(session.metadata_json or {})
        try:
            count = int(metadata.get("card_installments") or 0)
        except (TypeError, ValueError):
            count = 0
        card_token = str(metadata.get("card_token") or "").strip()
        value = str(metadata.get("card_installment_value") or "").strip()
        if count < 2 or not card_token or not value:
            db.rollback()
            continue
        valid_until = subscription.valid_until if subscription.valid_until.tzinfo else subscription.valid_until.replace(tzinfo=timezone.utc)
        key = valid_until.astimezone(ZoneInfo("America/Sao_Paulo")).date().isoformat()
        renewal = dict(metadata.get("installment_renewal") or {})
        if renewal.get("key") == key:
            if renewal.get("state") == "paid" or renewal.get("last_attempt") == today.isoformat():
                db.rollback()
                continue
        else:
            renewal = {"key": key, "attempts": 0}
        renewal.update(state="charging", last_attempt=today.isoformat(), attempts=int(renewal.get("attempts") or 0) + 1)
        metadata["installment_renewal"] = renewal
        session.metadata_json = metadata
        db.add(session)
        db.commit()  # libera a trava já marcando a tentativa de hoje

        reference = f"checkout_renewal:{session.token}:{key}"
        try:
            payment = _existing_renewal_payment(client, reference)
            if payment is None:
                payment = client.create_payment(
                    _with_optional_split({
                        "customer": session.asaas_customer_id,
                        "billingType": "CREDIT_CARD",
                        "installmentCount": count,
                        "installmentValue": float(_parse_decimal(value)),
                        "dueDate": today.isoformat(),
                        "description": f"Renovação {session.product_name} ({count}x)",
                        "externalReference": reference,
                        "split": build_default_split_payload(),
                        "creditCardToken": card_token,
                        "remoteIp": str(metadata.get("remote_ip") or "127.0.0.1"),
                    })
                )
            status = _map_asaas_payment_status(payment.get("status"))
        except Exception:  # noqa: BLE001 - cartão recusado ou Asaas fora: tenta de novo amanhã
            logger.exception("Renovação do anual parcelado não cobrada (checkout %s).", session.token)
            status = "failed"
        metadata = dict(session.metadata_json or {})
        renewal = dict(metadata.get("installment_renewal") or {})
        renewal["state"] = {"paid": "paid", "awaiting_payment": "pending"}.get(status, "failed")
        metadata["installment_renewal"] = renewal
        session.metadata_json = metadata
        if status == "paid":
            _apply_installment_renewal(db, session, key)
            charged += 1
        session.updated_at = _utcnow()
        db.add(session)
        db.commit()
    return charged


def apply_pending_subscription_values(db: Session, client: AsaasClient) -> int:
    """Assinaturas que ficaram no valor da 1ª mensalidade promocional (a troca falhou na compra):
    passa para o valor cheio, inclusive na próxima cobrança se ela já foi gerada."""
    updated = 0
    sessions = (
        db.query(CheckoutSession)
        .filter(CheckoutSession.payment_method == "card", CheckoutSession.status == "paid", CheckoutSession.metadata_json.isnot(None))
        .all()
    )
    for session in sessions:
        if not (session.metadata_json or {}).get("pending_subscription_value"):
            continue
        if _apply_pending_subscription_value(client, session, update_pending_payments=True):
            session.updated_at = _utcnow()
            db.add(session)
            db.commit()
            updated += 1
    return updated


def handle_asaas_checkout_webhook(db: Session, payload: dict[str, Any]) -> bool:
    payment = payload.get("payment") or {}
    authorization = payload.get("pixAutomaticAuthorization") or payload.get("authorization") or {}
    if not isinstance(authorization, dict):
        authorization = {}
    external_reference = str(payment.get("externalReference") or authorization.get("contractId") or "")
    session = None
    token = _extract_checkout_session_token(external_reference)
    if token:
        session = db.query(CheckoutSession).filter(CheckoutSession.token == token).first()
    if not session:
        authorization_id = _extract_pix_automatic_authorization_id(payload)
        if authorization_id:
            rows = db.query(CheckoutSession).filter(CheckoutSession.metadata_json.isnot(None)).all()
            for row in rows:
                metadata = dict(row.metadata_json or {})
                if str(metadata.get("asaas_pix_automatic_authorization_id") or "") == authorization_id:
                    session = row
                    break
    if not session:
        return False
    event_name = str(payload.get("event") or "").upper()
    if external_reference.startswith("checkout_renewal:"):
        _handle_installment_renewal_payment(db, session, payment, event_name)
        return True
    if session.paid_at and payment.get("installment"):
        # Parcelas da compra parcelada (o Asaas avisa cada uma, e de novo quando recebe): a compra
        # já foi confirmada e nenhuma delas muda a assinatura.
        return True
    if _is_card_subscription_renewal(db, session, payment):
        _handle_card_subscription_renewal(db, session, payment, event_name)
        return True
    was_already_paid = session.status == "paid" and bool(session.paid_at)
    session.asaas_payment_id = payment.get("id") or session.asaas_payment_id
    session.asaas_customer_id = payment.get("customer") or authorization.get("customerId") or session.asaas_customer_id
    event = str(payload.get("event") or "").upper()
    metadata = dict(session.metadata_json or {})
    authorization_id = _extract_pix_automatic_authorization_id(payload)
    if authorization_id:
        metadata["asaas_pix_automatic_authorization_id"] = authorization_id
    authorization_status = str(authorization.get("status") or "").upper()
    if authorization_status:
        metadata["asaas_pix_automatic_authorization_status"] = authorization_status
    instruction = payload.get("pixAutomaticPaymentInstruction") or payload.get("paymentInstruction") or {}
    instruction_status = ""
    instruction_id = ""
    if isinstance(instruction, dict) and instruction.get("id"):
        instruction_id = str(instruction["id"])
        metadata["asaas_pix_automatic_last_instruction_id"] = instruction_id
        instruction_status = str(instruction.get("status") or "").upper()
        metadata["asaas_pix_automatic_last_instruction_status"] = instruction_status
    session.metadata_json = metadata
    subscription_id = _extract_asaas_resource_id(payment.get("subscription"))
    if subscription_id:
        metadata = dict(session.metadata_json or {})
        metadata["asaas_subscription_id"] = subscription_id
        session.metadata_json = metadata
    # Consent lifecycle is independent of the already confirmed initial payment.
    # Do not revoke payment, renew access, or replay checkout completion on these events.
    if was_already_paid and event.startswith("PIX_AUTOMATIC_RECURRING_AUTHORIZATION_") and not payment.get("status"):
        if not authorization_status:
            suffix = event.removeprefix("PIX_AUTOMATIC_RECURRING_AUTHORIZATION_")
            metadata["asaas_pix_automatic_authorization_status"] = "ACTIVE" if suffix == "ACTIVATED" else suffix
        if metadata.get("asaas_pix_automatic_authorization_status") == "ACTIVE" and not metadata.get("asaas_pix_automatic_next_due_date"):
            metadata["asaas_pix_automatic_next_due_date"] = _next_pix_automatic_due_date(
                session.paid_at.date(), session.billing_cycle
            ).isoformat()
        session.metadata_json = metadata
        session.updated_at = _utcnow()
        db.add(session)
        db.commit()
        return True
    authorization_activated = event in {
        "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_ACTIVE",
        "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_ACTIVATED",
    } or authorization_status == "ACTIVE"
    if authorization_activated:
        session.status = "paid"
        if not metadata.get("asaas_pix_automatic_next_due_date"):
            metadata["asaas_pix_automatic_next_due_date"] = _next_pix_automatic_due_date(
                date.fromisoformat(_billing_today()), session.billing_cycle
            ).isoformat()
            session.metadata_json = metadata
    elif payment.get("status"):
        session.status = _map_asaas_payment_status(payment.get("status"))
    elif not event.startswith("PIX_AUTOMATIC_RECURRING_PAYMENT_INSTRUCTION_"):
        session.status = _map_asaas_payment_status(event)

    instruction_paid = event.startswith("PIX_AUTOMATIC_RECURRING_PAYMENT_INSTRUCTION_") and (
        instruction_status in {"PAID", "RECEIVED", "CONFIRMED"}
        or event.endswith(("_PAID", "_RECEIVED", "_CONFIRMED"))
    )
    is_pix_automatic = str(metadata.get("pix_mode") or "").strip().lower() == "automatic"
    renewal_key = instruction_id or str(metadata.get("asaas_pix_automatic_last_instruction_id") or "").strip()
    if not renewal_key:
        renewal_key = str(payment.get("id") or "").strip()
    renewal_already_processed = bool(renewal_key) and (
        str(metadata.get("asaas_pix_automatic_last_renewed_instruction_id") or "") == renewal_key
    )
    renewal_confirmed = was_already_paid and is_pix_automatic and (
        instruction_paid or event in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}
    ) and not renewal_already_processed

    if renewal_confirmed:
        session.status = "paid"
        if renewal_key:
            metadata["asaas_pix_automatic_last_renewed_instruction_id"] = renewal_key
            session.metadata_json = metadata
        _renew_paid_pix_automatic_subscription(db, session)
    elif not was_already_paid and (
        event in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"} or authorization_activated or session.status == "paid"
    ):
        if not session.paid_at:
            session.paid_at = _utcnow()
        session.status = "paid"
        if _is_upgrade_session(session):
            if _should_upgrade_session_in_place(db, session):
                user, previous_plan = _apply_upgrade_after_payment(db, session)
            else:
                _cancel_replaced_contracts_after_upgrade(db, session)
                previous_plan = str((dict(session.metadata_json or {}).get("current_plan") or "")).strip().lower() or None
                user = _upsert_paid_user_and_subscription(db, session)
            _notify_checkout_subscription_push(
                scenario=SubscriptionPushScenario.UPGRADED,
                session=session,
                user=user,
                previous_plan_name=previous_plan,
                upgraded_plan_name=session.plan_key,
            )
        else:
            user = _upsert_paid_user_and_subscription(db, session)
            _notify_checkout_subscription_push(
                scenario=SubscriptionPushScenario.NEW,
                session=session,
                user=user,
            )
        _dispatch_meta_checkout_events(
            db,
            session=session,
            event_name="payment_success",
            step="success",
            status="paid",
            payment_method=session.payment_method,
            metadata=dict(session.metadata_json or {}),
            ip_address_value=None,
            user_agent=None,
        )
    elif event in {"PAYMENT_OVERDUE", "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_EXPIRED", "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_REFUSED"}:
        session.status = "expired"
        if event == "PAYMENT_OVERDUE" and session.paid_at:
            # Renovação de quem já pagava: inadimplente (no ar por 3 dias, cobrança segue por 30).
            _mark_checkout_subscription_overdue(session, payment)
        elif event == "PAYMENT_OVERDUE":
            # Pix ou boleto da compra que venceu sem pagamento: a pessoa não concluiu a compra.
            _notify_checkout_payment_overdue(session, payment, "Primeira cobrança (compra não concluída)")
    elif event in {"PAYMENT_REPROVED_BY_RISK_ANALYSIS", "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_CANCELLED"}:
        session.status = "failed"
    session.updated_at = _utcnow()
    db.add(session)
    db.commit()
    return True


def define_password_for_paid_checkout(db: Session, token: str, password: str) -> User:
    session = get_checkout_session_by_token(db, token)
    if session.status != "paid":
        raise HTTPException(status_code=400, detail="O pagamento ainda nÃ£o foi confirmado.")
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







