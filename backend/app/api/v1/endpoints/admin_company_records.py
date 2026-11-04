"""Admin Master › página da empresa: faturas e pagamentos, avisos de cobrança, mensagens enviadas e
logs. Só leitura (menos a conferência de uma fatura no Asaas, a mesma que o cliente pode fazer).

De onde vem cada coisa:
- Faturas do Asaas: lidas na hora no Asaas (as mesmas da tela de faturas do cliente).
- Pagamentos pela Cakto: dos webhooks da Cakto guardados (cakto_event_logs), pelo e-mail do dono.
- Checkout próprio: as sessões de compra (checkout_sessions) do e-mail do dono.
- Avisos de cobrança: billing_notice_sends da conta do dono.
- Mensagens: avisos de cobrança (WhatsApp e e-mail) e e-mails do sistema (email_logs) da equipe.
- Logs: ações do Admin Master (admin_action_logs), webhooks do Asaas e da Cakto, compras no checkout
  e entradas no painel (user_sessions).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.api.v1.endpoints.admin_billing_notices import _send_out
from app.models.activity_log import AdminActionLog, EmailLog
from app.models.agency import Agency
from app.models.asaas import AsaasEventLog
from app.models.billing_notice import BillingNoticeSend
from app.models.cakto import CaktoEventLog
from app.models.checkout import CheckoutSession
from app.models.user import User
from app.models.user_session import UserSession
from app.services import billing_notices as notices
from app.services.asaas import AsaasAPIError
from app.services.company_status import agency_owner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/master/companies")

LOG_LIMIT = 150
CAKTO_PAYMENT_EVENTS = {"purchase_approved", "subscription_created", "subscription_renewed"}
CAKTO_EVENT_LABELS = {
    "purchase_approved": "Compra aprovada",
    "subscription_created": "Assinatura criada",
    "subscription_renewed": "Assinatura renovada",
    "subscription_canceled": "Assinatura cancelada",
    "subscription_cancelled": "Assinatura cancelada",
    "subscription_renewal_refused": "Renovação recusada",
    "refund": "Reembolso",
    "chargeback": "Chargeback",
}
ASAAS_EVENT_LABELS = {
    "PAYMENT_CREATED": "Cobrança criada",
    "PAYMENT_UPDATED": "Cobrança atualizada",
    "PAYMENT_CONFIRMED": "Pagamento confirmado",
    "PAYMENT_RECEIVED": "Pagamento recebido",
    "PAYMENT_OVERDUE": "Cobrança vencida",
    "PAYMENT_DELETED": "Cobrança apagada",
    "PAYMENT_RESTORED": "Cobrança restaurada",
    "PAYMENT_REFUNDED": "Pagamento estornado",
    "PAYMENT_REPROVED_BY_RISK_ANALYSIS": "Pagamento reprovado na análise de risco",
    "PAYMENT_CREDIT_CARD_CAPTURE_REFUSED": "Cartão recusado",
    "SUBSCRIPTION_CREATED": "Assinatura criada",
    "SUBSCRIPTION_UPDATED": "Assinatura atualizada",
    "SUBSCRIPTION_DELETED": "Assinatura removida",
    "SUBSCRIPTION_CANCELLED": "Assinatura cancelada",
    "SUBSCRIPTION_INACTIVATED": "Assinatura inativada",
}
CHECKOUT_STATUS_LABELS = {
    "draft": "Começou a compra",
    "pending": "Aguardando pagamento",
    "awaiting_payment": "Aguardando pagamento",
    "paid": "Pago",
    "failed": "Falhou",
    "expired": "Expirou",
    "cancelled": "Cancelada",
    "abandoned": "Abandonada",
}


def _load(db: Session, agency_id: int) -> tuple[Agency, User | None]:
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if agency is None:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return agency, agency_owner(agency)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _team(agency: Agency) -> list[User]:
    return [rel.user for rel in agency.users or [] if rel.user and not rel.hidden_from_team]


def _emails(users: list[User]) -> list[str]:
    return sorted({(user.email or "").strip().lower() for user in users if user and user.email})


def _json_contains(column, terms: list[str]):
    """Busca no JSON guardado como texto (os webhooks não têm coluna própria de cliente)."""
    text = func.lower(cast(column, String))
    return or_(*[text.like(f"%{term.lower()}%") for term in terms])


def _asaas_ids(db: Session, owner: User | None) -> list[str]:
    if owner is None:
        return []
    ids: set[str] = set()
    sub = owner.subscription
    if sub:
        for value in (sub.asaas_customer_id, sub.asaas_subscription_id):
            if value:
                ids.add(value)
    for (customer_id,) in (
        db.query(CheckoutSession.asaas_customer_id)
        .filter(func.lower(CheckoutSession.customer_email) == (owner.email or "").lower())
        .filter(CheckoutSession.asaas_customer_id.isnot(None))
        .distinct()
    ):
        ids.add(customer_id)
    return sorted(ids)


def _cakto_events(db: Session, owner: User | None, limit: int = LOG_LIMIT) -> list[CaktoEventLog]:
    if owner is None:
        return []
    terms = [term for term in (owner.email, owner.subscription.cakto_order_id if owner.subscription else None) if term]
    if not terms:
        return []
    return (
        db.query(CaktoEventLog)
        .filter(_json_contains(CaktoEventLog.payload, terms))
        .order_by(CaktoEventLog.created_at.desc(), CaktoEventLog.id.desc())
        .limit(limit)
        .all()
    )


def _asaas_events(db: Session, owner: User | None, limit: int = LOG_LIMIT) -> list[AsaasEventLog]:
    ids = _asaas_ids(db, owner)
    if not ids:
        return []
    return (
        db.query(AsaasEventLog)
        .filter(_json_contains(AsaasEventLog.payload, ids))
        .order_by(AsaasEventLog.created_at.desc(), AsaasEventLog.id.desc())
        .limit(limit)
        .all()
    )


def _checkouts(db: Session, owner: User | None) -> list[CheckoutSession]:
    if owner is None or not owner.email:
        return []
    return (
        db.query(CheckoutSession)
        .filter(or_(func.lower(CheckoutSession.customer_email) == owner.email.lower(), CheckoutSession.user_id == owner.id))
        .order_by(CheckoutSession.created_at.desc(), CheckoutSession.id.desc())
        .limit(50)
        .all()
    )


def _cakto_payment(service, row: CaktoEventLog) -> dict[str, Any]:
    payload = row.payload if isinstance(row.payload, dict) else {}
    order = service._extract_order(payload)  # noqa: SLF001 - mesmas regras de leitura do webhook
    amount = service._extract_order_amount(order, payload)  # noqa: SLF001
    return {
        "id": row.id,
        "event_type": (row.event_type or "").lower(),
        "label": CAKTO_EVENT_LABELS.get((row.event_type or "").lower(), row.event_type or "Evento"),
        "amount": float(amount) if amount is not None else None,
        "offer": service._extract_offer_name(order, payload),  # noqa: SLF001
        "payment_method": service._extract_payment_method(payload, order),  # noqa: SLF001
        "order_id": service._extract_order_id(payload),  # noqa: SLF001
        "status": row.status,
        "created_at": _iso(row.created_at),
    }


def _checkout_out(row: CheckoutSession) -> dict[str, Any]:
    return {
        "id": row.id,
        "token": row.token,
        "product_name": row.product_name,
        "plan_key": row.plan_key,
        "billing_cycle": row.billing_cycle,
        "amount": float(row.amount or 0),
        "status": row.status,
        "status_label": CHECKOUT_STATUS_LABELS.get((row.status or "").lower(), row.status),
        "payment_method": row.payment_method,
        "coupon_code": row.coupon_code,
        "asaas_payment_id": row.asaas_payment_id,
        "created_at": _iso(row.created_at),
        "paid_at": _iso(row.paid_at),
    }


@router.get("/{agency_id}/billing")
def company_billing(agency_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> dict[str, Any]:
    """Faturas do Asaas (lidas na hora), pagamentos pela Cakto e compras no checkout próprio."""
    from app.api.v1.endpoints.billing import collect_asaas_invoices
    from app.services.cakto import CaktoIntegrationService

    _agency, owner = _load(db, agency_id)
    invoices: dict[str, Any] | None = None
    asaas_error: str | None = None
    sub = owner.subscription if owner else None
    if sub and (sub.asaas_customer_id or sub.asaas_subscription_id):
        try:
            invoices = collect_asaas_invoices(db, owner).model_dump(mode="json")
        except (AsaasAPIError, HTTPException) as exc:
            asaas_error = getattr(exc, "detail", None) or str(exc) or "Erro ao consultar o Asaas."
            logger.warning("Faturas do Asaas da empresa %s não carregaram: %s", agency_id, exc)
        except Exception as exc:  # noqa: BLE001 - a página não pode cair por causa do Asaas
            asaas_error = "Não foi possível consultar o Asaas agora."
            logger.exception("Erro ao listar faturas da empresa %s: %s", agency_id, exc)

    service = CaktoIntegrationService(db)
    cakto = [
        _cakto_payment(service, row)
        for row in _cakto_events(db, owner)
        if (row.event_type or "").lower() in CAKTO_PAYMENT_EVENTS
    ]
    return {
        "provider": (sub.provider if sub else None),
        "asaas_customer_id": sub.asaas_customer_id if sub else None,
        "asaas": invoices,
        "asaas_error": asaas_error,
        "cakto_payments": cakto,
        "checkouts": [_checkout_out(row) for row in _checkouts(db, owner)],
    }


@router.post("/{agency_id}/invoices/{payment_id}/sync")
def company_invoice_sync(
    agency_id: int, payment_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)
) -> dict[str, Any]:
    """Confere a fatura no Asaas e, se estiver paga, aplica na conta (quando o webhook não chegou)."""
    from app.api.v1.endpoints.billing import (
        _extract_resource_info,
        _get_asaas_client,
        _normalize_asaas_payment,
        apply_asaas_payment,
    )
    from app.services.billing_account import is_paid_payment

    _agency, owner = _load(db, agency_id)
    sub = owner.subscription if owner else None
    if not sub:
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")
    try:
        payment = _get_asaas_client().get_payment(payment_id) or {}
    except AsaasAPIError as exc:
        raise HTTPException(status_code=404, detail="Fatura não encontrada no Asaas.") from exc
    customer_id, _ = _extract_resource_info(payment.get("customer"))
    subscription_id, _ = _extract_resource_info(payment.get("subscription"))
    owns = bool(customer_id and customer_id == sub.asaas_customer_id) or bool(
        subscription_id and subscription_id == sub.asaas_subscription_id
    )
    if not payment.get("id") or not owns:
        raise HTTPException(status_code=404, detail="Esta fatura não é desta empresa.")
    paid = is_paid_payment(payment)
    applied = apply_asaas_payment(db, payment) if paid else False
    return {"paid": paid, "applied": applied, "invoice": _normalize_asaas_payment(payment).model_dump(mode="json")}


@router.get("/{agency_id}/notices")
def company_notices(agency_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> dict[str, Any]:
    """Avisos de cobrança da conta do dono: o que saiu, o que falhou e o que foi cancelado."""
    _agency, owner = _load(db, agency_id)
    settings_row = notices.get_settings_row(db)
    rows = (
        db.query(BillingNoticeSend)
        .filter(BillingNoticeSend.user_id == owner.id)
        .order_by(BillingNoticeSend.created_at.desc(), BillingNoticeSend.id.desc())
        .limit(300)
        .all()
        if owner
        else []
    )
    items = [_send_out(row, owner) for row in rows]
    counts: dict[str, int] = {}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {
        "enabled": bool(settings_row.enabled),
        "asaas_notifications_enabled": bool(settings_row.asaas_notifications_enabled),
        "steps": [{"key": step.key, "label": step.label} for step in notices.STEPS],
        "counts": counts,
        "items": items,
    }


@router.get("/{agency_id}/messages")
def company_messages(agency_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> dict[str, Any]:
    """Tudo o que o sistema mandou para a empresa: avisos de cobrança e e-mails do sistema."""
    from app.services.platform_branding import EMAIL_BY_KEY

    agency, owner = _load(db, agency_id)
    items: list[dict[str, Any]] = []
    if owner:
        for row in (
            db.query(BillingNoticeSend)
            .filter(BillingNoticeSend.user_id == owner.id, BillingNoticeSend.status != "cancelled")
            .order_by(BillingNoticeSend.created_at.desc())
            .limit(300)
        ):
            step = notices.STEP_BY_KEY.get(row.step)
            items.append({
                "id": f"notice-{row.id}",
                "source": "billing_notice",
                "channel": row.channel,
                "title": f"Aviso de cobrança · {step.label if step else row.step}",
                "recipient": row.recipient,
                "status": row.status,
                "error": row.error,
                "at": _iso(row.sent_at or row.updated_at or row.created_at),
                "notice_id": row.id,
                "payment_id": row.payment_id,
            })
    emails = _emails(_team(agency))
    if emails:
        for row in (
            db.query(EmailLog)
            .filter(func.lower(EmailLog.to_email).in_(emails))
            .order_by(EmailLog.created_at.desc())
            .limit(300)
        ):
            spec = EMAIL_BY_KEY.get(row.kind or "")
            items.append({
                "id": f"email-{row.id}",
                "source": "system_email",
                "channel": "email",
                "title": row.subject or (spec.label if spec else "E-mail do sistema"),
                "kind_label": spec.label if spec else None,
                "recipient": row.to_email,
                "status": row.status,
                "error": row.error,
                "at": _iso(row.created_at),
            })
    items.sort(key=lambda item: item["at"] or "", reverse=True)
    return {"items": items}


def _asaas_summary(payload: dict[str, Any]) -> str:
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else None
    subscription = payload.get("subscription") if isinstance(payload.get("subscription"), dict) else None
    if payment:
        parts = [payment.get("id")]
        if payment.get("value") is not None:
            parts.append(f"R$ {float(payment.get('value') or 0):.2f}".replace(".", ","))
        if payment.get("dueDate"):
            parts.append(f"vence {payment.get('dueDate')}")
        if payment.get("billingType"):
            parts.append(str(payment.get("billingType")))
        return " · ".join(str(part) for part in parts if part)
    if subscription:
        parts = [subscription.get("id"), subscription.get("status"), subscription.get("cycle")]
        return " · ".join(str(part) for part in parts if part)
    return ""


@router.get("/{agency_id}/logs")
def company_logs(agency_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> dict[str, Any]:
    """Linha do tempo da empresa: ações do Admin Master, webhooks do Asaas e da Cakto, compras no
    checkout e entradas no painel."""
    from app.services.cakto import CaktoIntegrationService

    agency, owner = _load(db, agency_id)
    team = _team(agency)
    names = {user.id: user.name or user.email for user in team}
    items: list[dict[str, Any]] = []

    if owner:
        for row in (
            db.query(AdminActionLog)
            .filter(AdminActionLog.target_user_id == owner.id)
            .order_by(AdminActionLog.created_at.desc())
            .limit(LOG_LIMIT)
        ):
            items.append({
                "id": f"admin-{row.id}",
                "source": "admin",
                "title": row.summary,
                "detail": f"Por {row.actor_name or 'admin'}",
                "status": "ok",
                "at": _iso(row.created_at),
                "data": row.details,
            })

    for row in _asaas_events(db, owner):
        event = (row.event_type or "").upper()
        payload = row.payload if isinstance(row.payload, dict) else {}
        items.append({
            "id": f"asaas-{row.id}",
            "source": "asaas",
            "title": ASAAS_EVENT_LABELS.get(event, event or "Evento do Asaas"),
            "detail": _asaas_summary(payload),
            "event": event,
            "status": "error" if row.status == "error" else "ok",
            "error": row.error_message,
            "at": _iso(row.created_at),
            "data": payload,
        })

    service = CaktoIntegrationService(db)
    for row in _cakto_events(db, owner):
        info = _cakto_payment(service, row)
        detail = " · ".join(
            str(part)
            for part in (
                info["order_id"],
                f"R$ {info['amount']:.2f}".replace(".", ",") if info["amount"] is not None else None,
                info["offer"],
            )
            if part
        )
        items.append({
            "id": f"cakto-{row.id}",
            "source": "cakto",
            "title": info["label"],
            "detail": detail,
            "event": info["event_type"],
            "status": "error" if row.status == "error" else "ok",
            "error": row.error_message,
            "at": info["created_at"],
            "data": row.payload,
        })

    for row in _checkouts(db, owner):
        out = _checkout_out(row)
        items.append({
            "id": f"checkout-{row.id}",
            "source": "checkout",
            "title": f"Checkout: {out['status_label']}",
            "detail": " · ".join(
                str(part)
                for part in (
                    row.product_name,
                    f"R$ {out['amount']:.2f}".replace(".", ","),
                    row.payment_method,
                    f"cupom {row.coupon_code}" if row.coupon_code else None,
                )
                if part
            ),
            "status": "ok",
            "at": out["paid_at"] or out["created_at"],
        })

    if team:
        for row in (
            db.query(UserSession)
            .filter(UserSession.user_id.in_([user.id for user in team]))
            .order_by(UserSession.created_at.desc())
            .limit(LOG_LIMIT)
        ):
            device = " · ".join(part for part in (row.device_label, row.client_name, row.ip_address) if part)
            items.append({
                "id": f"login-{row.id}",
                "source": "login",
                "title": f"Entrou no painel: {names.get(row.user_id, 'usuário')}",
                "detail": device + (f" · visto por último em {row.last_path}" if row.last_path else ""),
                "status": "revoked" if row.revoked_at else "ok",
                "at": _iso(row.created_at),
                "last_seen_at": _iso(row.last_seen_at),
            })

    items.sort(key=lambda item: item["at"] or "", reverse=True)
    counts: dict[str, int] = {}
    for item in items:
        counts[item["source"]] = counts.get(item["source"], 0) + 1
    return {"items": items, "counts": counts}
