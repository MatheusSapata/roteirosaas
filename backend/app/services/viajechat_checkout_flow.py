from __future__ import annotations

import logging
import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import exists

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.checkout import CheckoutSession, CheckoutTrackingEvent
from app.services.viajechat import ViajeChatClient, ViajeChatClientError
from app.services.viajechat_tags import get_viajechat_tag_id

logger = logging.getLogger(__name__)

OFFER_TO_TAG_KEY = {
    "profissional": "professional",
    "professional": "professional",
    "agencia": "agency",
    "agency": "agency",
    "escala": "scale",
    "scale": "scale",
}

SIGNED_TAG_KEYS = [
    "signed_professional",
    "signed_agency",
    "signed_scale",
]


def _client() -> ViajeChatClient | None:
    settings = get_settings()
    if not settings.viajechat_api_key:
        return None
    return ViajeChatClient(settings.viajechat_api_key, settings.viajechat_api_base_url)


def _normalize_phone_for_viajechat(phone: str | None) -> str:
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("55"):
        return digits
    return f"55{digits}"


def _correlation_id(*, token: str | None = None, email: str | None = None, phone: str | None = None) -> str:
    if token:
        return f"chk:{token}"
    base = f"{(email or '').strip().lower()}|{''.join(ch for ch in str(phone or '') if ch.isdigit())}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
    return f"ct:{digest}"


def _mask_email(email: str | None) -> str:
    raw = str(email or "").strip()
    if "@" not in raw:
        return "***"
    name, domain = raw.split("@", 1)
    if len(name) <= 2:
        return f"{name[:1]}***@{domain}"
    return f"{name[:2]}***@{domain}"


def _mask_phone(phone: str | None) -> str:
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if len(digits) <= 4:
        return "***"
    return f"***{digits[-4:]}"


def _normalize_offer(offer_key: str | None) -> str:
    return OFFER_TO_TAG_KEY.get(str(offer_key or "").strip().lower(), "")


def _abandoned_tag_key_for_offer(offer_key: str | None) -> str | None:
    offer = _normalize_offer(offer_key)
    if offer == "professional":
        return "checkout_abandoned_professional"
    if offer == "agency":
        return "checkout_abandoned_agency"
    if offer == "scale":
        return "checkout_abandoned_scale"
    return None


def _signed_tag_key_for_offer(offer_key: str | None) -> str | None:
    offer = _normalize_offer(offer_key)
    if offer == "professional":
        return "signed_professional"
    if offer == "agency":
        return "signed_agency"
    if offer == "scale":
        return "signed_scale"
    return None


def _tag_ids(keys: list[str]) -> list[str]:
    return [tag_id for key in keys if (tag_id := get_viajechat_tag_id(key))]


def ensure_checkout_contact_at_payment_step(
    *,
    name: str,
    email: str,
    phone: str,
    offer_key: str | None = None,
    token: str | None = None,
) -> str | None:
    correlation_id = _correlation_id(email=email, phone=phone)
    client = _client()
    if not client:
        return None
    online_tag_id = get_viajechat_tag_id("online_itinerary")
    if not online_tag_id:
        return None
    settings = get_settings()
    normalized_phone = _normalize_phone_for_viajechat(phone)
    if not normalized_phone:
        logger.warning("VIAJECHAT_SYNC_SKIP correlation_id=%s reason=missing_phone email=%s", correlation_id, _mask_email(email))
        return None
    if not ((settings.viajechat_checkout_sector_id or settings.viajechat_checkout_sector_name) and (settings.viajechat_checkout_column_id or settings.viajechat_checkout_column_name)):
        logger.warning("VIAJECHAT_SYNC_SKIP correlation_id=%s reason=missing_kanban_config", correlation_id)
        return None
    logger.info(
        "VIAJECHAT_SYNC_ATTEMPT correlation_id=%s event=checkout_step_method_view email=%s phone=%s offer_key=%s token=%s tag_key=online_itinerary tag_id=%s",
        correlation_id,
        _mask_email(email),
        _mask_phone(phone),
        offer_key,
        token,
        online_tag_id,
    )
    try:
        try:
            created = client.create_deal_card(
                phone=normalized_phone,
                name=name,
                email=email or None,
                sector_id=settings.viajechat_checkout_sector_id,
                sector_name=settings.viajechat_checkout_sector_name,
                column_id=settings.viajechat_checkout_column_id,
                column_name=settings.viajechat_checkout_column_name,
                lead_source=settings.viajechat_checkout_lead_source or "Checkout Roteiro Online",
                notes=[f"Checkout iniciado - oferta {offer_key or '-'}", f"Token: {token or '-'}"],
            )
        except ViajeChatClientError:
            # Fallback: some tenants fail with IDs but work with names.
            if settings.viajechat_checkout_sector_name and settings.viajechat_checkout_column_name:
                logger.warning(
                    "VIAJECHAT_SYNC_FALLBACK correlation_id=%s event=checkout_step_method_view strategy=names_only",
                    correlation_id,
                )
                created = client.create_deal_card(
                    phone=normalized_phone,
                    name=name,
                    email=email or None,
                    sector_id=None,
                    sector_name=settings.viajechat_checkout_sector_name,
                    column_id=None,
                    column_name=settings.viajechat_checkout_column_name,
                    lead_source=settings.viajechat_checkout_lead_source or "Checkout Roteiro Online",
                    notes=[f"Checkout iniciado - oferta {offer_key or '-'}", f"Token: {token or '-'}"],
                )
            else:
                raise

        contact_id = str((((created or {}).get("deal") or {}).get("contact") or {}).get("id") or "")
        if not contact_id:
            logger.warning(
                "VIAJECHAT_SYNC_RESULT correlation_id=%s event=checkout_step_method_view ok=false reason=missing_contact_id",
                correlation_id,
            )
            return None
        client.add_tags_to_contact(contact_id, [online_tag_id])
        logger.info(
            "VIAJECHAT_SYNC_RESULT correlation_id=%s event=checkout_step_method_view ok=true email=%s contact_id=%s tag_key=online_itinerary",
            correlation_id,
            _mask_email(email),
            contact_id,
        )
        return contact_id
    except ViajeChatClientError:
        logger.exception("Falha ao sincronizar contato/etiqueta de etapa pagamento no ViajeChat.")
        return None


def mark_signed(
    *,
    name: str,
    email: str,
    phone: str,
    offer_key: str,
    upgrade_mode: bool = False,
    contact_id: str | None = None,
) -> None:
    correlation_id = _correlation_id(email=email, phone=phone)
    client = _client()
    if not client:
        return
    signed_key = _signed_tag_key_for_offer(offer_key)
    signed_id = get_viajechat_tag_id(signed_key) if signed_key else None
    active_id = get_viajechat_tag_id("plan_active")
    if not signed_id and not active_id:
        return
    logger.info(
        "VIAJECHAT_SYNC_ATTEMPT correlation_id=%s event=payment_signed email=%s phone=%s offer_key=%s upgrade_mode=%s signed_tag=%s active_tag=%s",
        correlation_id,
        _mask_email(email),
        _mask_phone(phone),
        offer_key,
        upgrade_mode,
        signed_id,
        active_id,
    )
    try:
        if upgrade_mode:
            remove_ids = _tag_ids(SIGNED_TAG_KEYS)
            if remove_ids:
                if contact_id:
                    client.remove_tags_from_contact_by_id(contact_id, remove_ids)
                else:
                    client.remove_tags_from_contact_by_email(email, remove_ids)
                logger.info(
                    "VIAJECHAT_SYNC_DETAIL correlation_id=%s event=payment_signed action=remove_old_signed_tags email=%s removed_tag_ids=%s",
                    correlation_id,
                    _mask_email(email),
                    ",".join(remove_ids),
                )
        add_ids = [tag_id for tag_id in [signed_id, active_id] if tag_id]
        if add_ids:
            if contact_id:
                ok = client.add_tags_to_contact_by_id(contact_id, add_ids)
            else:
                ok = client.add_tags_to_contact_by_email_or_phone(
                    name=name,
                    email=email,
                    phone=phone,
                    tag_ids=add_ids,
                )
            logger.info(
                "VIAJECHAT_SYNC_RESULT correlation_id=%s event=payment_signed ok=%s email=%s added_tag_ids=%s",
                correlation_id,
                bool(ok),
                _mask_email(email),
                ",".join(add_ids),
            )
    except ViajeChatClientError:
        logger.exception("Falha ao sincronizar etiqueta de assinatura no ViajeChat.")


def mark_cancelled(*, name: str, email: str, phone: str, contact_id: str | None = None) -> None:
    correlation_id = _correlation_id(email=email, phone=phone)
    client = _client()
    if not client:
        return
    active_id = get_viajechat_tag_id("plan_active")
    cancelled_id = get_viajechat_tag_id("plan_cancelled")
    logger.info(
        "VIAJECHAT_SYNC_ATTEMPT correlation_id=%s event=subscription_cancelled email=%s phone=%s active_tag=%s cancelled_tag=%s",
        correlation_id,
        _mask_email(email),
        _mask_phone(phone),
        active_id,
        cancelled_id,
    )
    try:
        if active_id:
            if contact_id:
                client.remove_tags_from_contact_by_id(contact_id, [active_id])
            else:
                client.remove_tags_from_contact_by_email(email, [active_id])
            logger.info(
                "VIAJECHAT_SYNC_DETAIL correlation_id=%s event=subscription_cancelled action=remove_active_tag email=%s tag_id=%s",
                correlation_id,
                _mask_email(email),
                active_id,
            )
        if cancelled_id:
            if contact_id:
                ok = client.add_tags_to_contact_by_id(contact_id, [cancelled_id])
            else:
                ok = client.add_tags_to_contact_by_email_or_phone(
                    name=name,
                    email=email,
                    phone=phone,
                    tag_ids=[cancelled_id],
                )
            logger.info(
                "VIAJECHAT_SYNC_RESULT correlation_id=%s event=subscription_cancelled ok=%s email=%s added_tag_id=%s",
                correlation_id,
                bool(ok),
                _mask_email(email),
                cancelled_id,
            )
    except ViajeChatClientError:
        logger.exception("Falha ao sincronizar etiqueta de cancelamento no ViajeChat.")


def tag_abandoned_checkout_sessions(cutoff_minutes: int = 30) -> int:
    """
    Marca sessões abandonadas (já chegaram na etapa de pagamento e não pagaram após cutoff).
    """
    client = _client()
    if not client:
        return 0
    db = SessionLocal()
    tagged = 0
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max(5, cutoff_minutes))
        method_view_exists = exists().where(
            (CheckoutTrackingEvent.session_id == CheckoutSession.id)
            & (CheckoutTrackingEvent.event_name == "step_method_view")
        )
        rows = (
            db.query(CheckoutSession)
            .filter(
                CheckoutSession.created_at <= cutoff,
                CheckoutSession.status != "paid",
                method_view_exists,
            )
            .all()
        )
        for session in rows:
            correlation_id = _correlation_id(token=session.token, email=session.customer_email, phone=session.customer_phone)
            metadata = dict(session.metadata_json or {})
            if metadata.get("viajechat_abandonment_tagged"):
                continue
            tag_key = _abandoned_tag_key_for_offer(session.offer_key)
            tag_id = get_viajechat_tag_id(tag_key) if tag_key else None
            if not tag_id:
                continue
            try:
                logger.info(
                    "VIAJECHAT_SYNC_ATTEMPT correlation_id=%s event=checkout_abandoned session_id=%s token=%s email=%s offer_key=%s tag_key=%s tag_id=%s",
                    correlation_id,
                    session.id,
                    session.token,
                    _mask_email(session.customer_email),
                    session.offer_key,
                    tag_key,
                    tag_id,
                )
                contact_id = str((metadata.get("viajechat_contact_id") or "")).strip()
                if contact_id:
                    ok = client.add_tags_to_contact_by_id(contact_id, [tag_id])
                else:
                    ok = client.add_tags_to_contact_by_email_or_phone(
                        name=session.customer_name,
                        email=session.customer_email,
                        phone=session.customer_phone,
                        tag_ids=[tag_id],
                    )
                if ok:
                    metadata["viajechat_abandonment_tagged"] = True
                    metadata["viajechat_abandonment_tagged_at"] = datetime.now(timezone.utc).isoformat()
                    session.metadata_json = metadata
                    db.add(session)
                    tagged += 1
                    logger.info(
                        "VIAJECHAT_SYNC_RESULT correlation_id=%s event=checkout_abandoned ok=true session_id=%s email=%s",
                        correlation_id,
                        session.id,
                        _mask_email(session.customer_email),
                    )
                else:
                    logger.info(
                        "VIAJECHAT_SYNC_RESULT correlation_id=%s event=checkout_abandoned ok=false session_id=%s email=%s",
                        correlation_id,
                        session.id,
                        _mask_email(session.customer_email),
                    )
            except ViajeChatClientError:
                logger.exception("Falha ao aplicar tag de abandono no ViajeChat para sessão %s", session.id)
        if tagged:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Erro ao processar abandono de checkout para ViajeChat.")
    finally:
        db.close()
    return tagged
