import logging
import hashlib
import json
import time
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.core.request_ip import get_client_ip
from app.models.subscription import Subscription
from app.models.user import User
from app.models.revenue import RevenueTotal
from app.models.asaas import AsaasEventLog
from app.models.checkout import CheckoutSession
from app.services.asaas import AsaasAPIError, AsaasClient, build_default_split_payload
from app.services.cakto import CaktoAPIError, CaktoIntegrationService
from app.services.billing_account import (
    cancel_open_payments,
    covered_by_paid,
    covered_period,
    current_contract_offer,
    is_paid_payment,
    mark_payment_applied,
    parse_date,
    payment_applied,
    pix_automatic_status,
    replaced_payment_ids,
)
from app.services.checkout import find_pix_automatic_authorization_id, handle_asaas_checkout_webhook
from app.services.company_status import ENDED_STATUSES, mark_subscription_overdue
from app.services.subscription_notifications import (
    SubscriptionPushScenario,
    publish_subscription_notification,
    send_hub_refund,
)
from app.services.webhook_notifications import notify_payment_overdue
from app.services.legacy_renewal import (
    LEGACY_RENEWAL_OFFER_KEY,
    create_renewal_checkout_session,
    legacy_renewal_info,
    legacy_upgrade_available,
)
from app.services.plans import effective_plan
from app.services.trial import end_trial
from app.services.trial import republish_all_user_pages
from app.services.viajechat_checkout_flow import mark_cancelled as mark_viajechat_cancelled, mark_signed as mark_viajechat_signed

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

PLAN_PRICING = {
    "essencial": {
        "monthly": {"title": "Plano Essencial", "price": 49.90, "asaas_cycle": "MONTHLY"},
        "annual": {"title": "Plano Essencial Anual", "price": 479.88, "asaas_cycle": "YEARLY"},
    },
    "growth": {
        "monthly": {"title": "Plano Growth", "price": 89.99, "asaas_cycle": "MONTHLY"},
        "annual": {"title": "Plano Growth Anual", "price": 839.88, "asaas_cycle": "YEARLY"},
    },
    "infinity": {
        "monthly": {"title": "Plano Infinity", "price": 129.90, "asaas_cycle": "MONTHLY"},
        "annual": {"title": "Plano Infinity Anual", "price": 1199.88, "asaas_cycle": "YEARLY"},
    },
    "teste": {
        "monthly": {"title": "Plano Teste", "price": 5.00, "asaas_cycle": "MONTHLY"},
        "annual": {"title": "Plano Teste Anual", "price": 6.00, "asaas_cycle": "YEARLY"},
    },
}

DEFAULT_CYCLE = "monthly"


def _normalize_plan_key(value: str | None) -> str:
    raw = (value or "").strip().lower()
    aliases = {
        "professional": "essencial",
        "profissional": "essencial",
        "essencial": "essencial",
        "agency": "growth",
        "agencia": "growth",
        "growth": "growth",
        "scale": "infinity",
        "escala": "infinity",
        "infinity": "infinity",
        "free": "free",
        "trial": "free",
        "teste": "teste",
        "test": "teste",
    }
    return aliases.get(raw, raw or "free")


def _is_comeco_like_plan(value: str | None) -> bool:
    raw = str(value or "").strip().lower()
    return raw in {"comeco", "free"}


def _get_asaas_client() -> AsaasClient:
    if not settings.asaas_api_key:
        raise HTTPException(status_code=500, detail="Chave da API Asaas nÃ£o configurada")
    return AsaasClient(settings.asaas_api_key, settings.asaas_base_url)


def _cancel_asaas_subscription_billing(db: Session, client: AsaasClient, subscription: Subscription) -> None:
    checkout_token = None
    external_reference = str(subscription.external_reference or "").strip()
    if external_reference.startswith("checkout:"):
        checkout_token = external_reference.split("checkout:", 1)[1].strip() or None
    authorization_id = None
    if str(subscription.payment_method_type or "").strip().lower() == "pix":
        authorization_id = find_pix_automatic_authorization_id(
            db,
            user_id=subscription.user_id,
            checkout_token=checkout_token,
        )
    if authorization_id:
        client.cancel_pix_automatic_authorization(
            authorization_id,
            reason="Cancelamento solicitado pelo cliente",
        )
    elif subscription.asaas_subscription_id:
        client.cancel_subscription(subscription.asaas_subscription_id)
    elif subscription.asaas_payment_link_id:
        client.delete_payment_link(subscription.asaas_payment_link_id)


def _extract_asaas_error_detail(exc: AsaasAPIError) -> str:
    payload = exc.args[0] if exc.args else None
    if isinstance(payload, dict):
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                code = str(first.get("code") or "").strip()
                desc = str(first.get("description") or "").strip()
                if code and desc:
                    return f"{code}: {desc}"
                return desc or code or "Erro no Asaas"
            return str(first)
        return str(payload)
    return str(exc)


def _build_external_reference(user_id: int, plan_key: str, cycle: str) -> str:
    return f"{user_id}:{plan_key}:{cycle}"


def _parse_external_reference(ref: Optional[str]) -> tuple[int, str, str] | None:
    if not ref:
        return None
    parts = ref.split(":")
    if len(parts) != 3:
        return None
    raw_user, plan_key, cycle = parts
    try:
        return int(raw_user), plan_key, cycle
    except ValueError:
        return None


# Pagamento sem referência nossa (assinatura criada ou editada no painel do Asaas): só os avisos que
# mudam o acesso, para um "cobrança criada" não mexer no status de quem está em dia.
FALLBACK_PAYMENT_EVENTS = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED", "PAYMENT_OVERDUE"}


def _match_payment_by_asaas_subscription(db: Session, payment: dict[str, Any]) -> tuple[int, str, str] | None:
    """Cobrança paga direto pela fatura, sem a referência do checkout: acha a conta pela assinatura do Asaas
    (ou, sem assinatura, pelo cliente)."""
    sub_id, _ = _extract_resource_info(payment.get("subscription"))
    subscription = None
    if sub_id:
        subscription = db.query(Subscription).filter(Subscription.asaas_subscription_id == sub_id).first()
    if subscription is None:
        # Pix Automático não tem assinatura no Asaas: a cobrança só traz o cliente.
        customer_id, _ = _extract_resource_info(payment.get("customer"))
        owners = (
            db.query(Subscription).filter(Subscription.asaas_customer_id == customer_id).limit(2).all() if customer_id else []
        )
        subscription = owners[0] if len(owners) == 1 else None
    if subscription is None or not subscription.user_id:
        return None
    return subscription.user_id, subscription.plan or "free", subscription.billing_cycle or DEFAULT_CYCLE


def _compute_asaas_event_id(payload: dict[str, Any]) -> str:
    explicit_id = payload.get("id")
    if explicit_id:
        return f"asaas:{explicit_id}"
    event = str(payload.get("event") or "")
    payment = payload.get("payment") or {}
    subscription = payload.get("subscription") or {}
    payment_id = payment.get("id")
    subscription_id = subscription.get("id") if isinstance(subscription, dict) else subscription
    if event and (payment_id or subscription_id):
        return f"asaas:{event}:{payment_id or ''}:{subscription_id or ''}"
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
    return f"asaas:hash:{digest}"


def _register_asaas_event(db: Session, payload: dict[str, Any]) -> tuple[AsaasEventLog, bool]:
    event_id = _compute_asaas_event_id(payload)
    event_type = str(payload.get("event") or "").upper() or None
    existing = db.query(AsaasEventLog).filter(AsaasEventLog.event_id == event_id).first()
    if existing:
        return existing, False
    log = AsaasEventLog(event_id=event_id, event_type=event_type, payload=payload, status="pending")
    db.add(log)
    db.commit()
    db.refresh(log)
    return log, True


class CheckoutRequest(BaseModel):
    plan: str
    cycle: Optional[str] = None


class CheckoutResponse(BaseModel):
    init_point: str
    preapproval_id: Optional[str] = None


class BillingRenewalOffer(BaseModel):
    """Plano, ciclo e valor do contrato do cliente (a renovação nunca usa a vitrine nem a tabela antiga)."""

    plan: str
    billing_cycle: Literal["monthly", "annual"]
    amount: float
    title: str


class BillingInfo(BaseModel):
    plan: str
    status: str
    valid_until: Optional[datetime]
    failed_attempts: int
    preapproval_id: Optional[str] = None
    provider: Optional[str] = None
    billing_cycle: Optional[str] = None
    payment_method_type: Optional[str] = None
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    scheduled_downgrade_plan: Optional[str] = None
    scheduled_downgrade_at: Optional[datetime] = None
    # Plano antigo (antes do plano único): a tela mostra só o plano do cliente, sem o plano novo.
    legacy: bool = False
    # Valor da renovação por ciclo (mensal = do mês, anual = do ano), decidido no servidor.
    legacy_renewal_amount: Optional[Decimal] = None
    # panel: renova pela tela; external: gerida pelo local onde foi contratada; support: fale com o suporte.
    legacy_renewal_mode: Optional[Literal["panel", "external", "support"]] = None
    legacy_managed_externally: bool = False
    # Profissional ou Agência antigo que renova pela tela: também pode fazer upgrade para o plano único.
    legacy_upgrade_available: bool = False
    # Pix Automático: ACTIVE, CANCELLED, EXPIRED ou REFUSED (None para quem não paga assim).
    pix_automatic_status: Optional[str] = None
    renewal_offer: Optional[BillingRenewalOffer] = None


class BillingInvoiceOut(BaseModel):
    id: str
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None
    status: str
    billing_type: Optional[str] = None
    description: Optional[str] = None
    value: float = 0
    due_date: Optional[str] = None
    payment_date: Optional[str] = None
    invoice_url: Optional[str] = None
    bank_slip_url: Optional[str] = None
    receipt_url: Optional[str] = None
    pay_url: Optional[str] = None
    download_url: Optional[str] = None
    is_paid: bool = False
    # replaced: cancelada por troca ou em aberto de um período que outra fatura paga já cobre.
    bucket: Literal["paid", "overdue", "upcoming", "replaced"] = "upcoming"
    # Período que a fatura cobre: do vencimento a um ciclo depois (o dia final não entra).
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class BillingNextCharge(BaseModel):
    due_date: str
    amount: float


class BillingAccountOut(BaseModel):
    # active, past_due, blocked, cancelling ou inactive.
    status: str
    blocked: bool = False
    access_until: Optional[datetime] = None
    # Soma só do que está vencido e não foi substituído ou coberto por outra fatura.
    open_amount: float = 0
    open_count: int = 0
    next_charge: Optional[BillingNextCharge] = None
    # Fatura vencida que, paga, libera o acesso.
    unlocking_invoice_id: Optional[str] = None
    pix_automatic_status: Optional[str] = None
    renewal_offer: Optional[BillingRenewalOffer] = None


class BillingInvoicesResponse(BaseModel):
    items: list[BillingInvoiceOut]
    total: int
    counts: dict[str, int]
    account: Optional[BillingAccountOut] = None


class InvoiceSyncOut(BaseModel):
    paid: bool
    applied: bool
    status: str
    invoice: BillingInvoiceOut


class PlanChangeRequest(BaseModel):
    plan: str


class PaymentMethodUpdateRequest(BaseModel):
    cycle: Optional[str] = None


class PaymentMethodChangeRequest(BaseModel):
    method: Literal["pix", "card"]


class PaymentMethodChangeOut(BillingInfo):
    # Pix: token da sessão de renovação; a tela segue para o QR Code de autorização.
    checkout_token: Optional[str] = None


class CardUpdateRequest(BaseModel):
    holder_name: str
    number: str
    expiry_month: str
    expiry_year: str
    ccv: str
    remote_ip: str | None = None


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    client = _get_asaas_client()
    plan_key = payload.plan
    cycle = (payload.cycle or DEFAULT_CYCLE).lower()
    if plan_key not in PLAN_PRICING:
        raise HTTPException(status_code=400, detail="Plano invÃ¡lido")
    plan_options = PLAN_PRICING[plan_key]
    plan_info = plan_options.get(cycle)
    if not plan_info:
        raise HTTPException(status_code=400, detail="Ciclo de cobranÃ§a invÃ¡lido")

    external_ref = _build_external_reference(current_user.id, plan_key, cycle)
    redirect_url = settings.asaas_success_url or settings.stripe_success_url or settings.mp_success_url

    request_payload: Dict[str, Any] = {
        "name": plan_info["title"],
        "description": f"Assinatura {plan_info['title']}",
        "value": plan_info["price"],
        "billingType": settings.asaas_billing_type,
        "chargeType": "RECURRENT",
        "subscriptionCycle": plan_info["asaas_cycle"],
        "dueDateLimitDays": 5,
        "externalReference": external_ref,
        "notificationEnabled": True,
    }
    if redirect_url:
        request_payload["redirectUrl"] = redirect_url
        request_payload["callback"] = {
            "successUrl": redirect_url,
            "autoRedirect": False
        }

    logger.info("Payload Asaas: %s", request_payload)
    try:
        link = client.create_payment_link(request_payload)
    except AsaasAPIError as exc:  # noqa: BLE001
        logger.exception("Erro ao criar link de pagamento Asaas: %s", exc)
        raise HTTPException(status_code=502, detail="Erro ao criar pagamento no Asaas") from exc

    subscription = current_user.subscription
    if not subscription:
        subscription = Subscription(user_id=current_user.id)
        db.add(subscription)
        db.flush()
        current_user.subscription_id = subscription.id

    subscription.provider = "asaas"
    subscription.status = "pending"
    subscription.failed_attempts = 0
    subscription.asaas_payment_link_id = link.get("id")
    subscription.external_reference = external_ref
    subscription.preapproval_id = link.get("id")
    db.add_all([subscription, current_user])
    db.commit()

    checkout_url = link.get("url") or link.get("shortUrl") or ""
    if not checkout_url:
        raise HTTPException(status_code=502, detail="Asaas nÃ£o retornou URL de pagamento")
    return CheckoutResponse(init_point=checkout_url, preapproval_id=link.get("id"))


def _ensure_subscription(user: User) -> Subscription:
    subscription = user.subscription
    if not subscription:
        subscription = Subscription(user_id=user.id)
    subscription.provider = "asaas"
    return subscription


def _cycle_duration(cycle: str) -> timedelta:
    normalized = (cycle or DEFAULT_CYCLE).lower()
    days_map = {"monthly": 30, "annual": 365}
    return timedelta(days=days_map.get(normalized, 30))


def _parse_decimal_value(raw_value: Any) -> Decimal:
    if raw_value is None:
        return Decimal("0")
    try:
        return Decimal(str(raw_value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _get_or_create_revenue_total(db: Session) -> RevenueTotal:
    entry = db.query(RevenueTotal).order_by(RevenueTotal.id.asc()).first()
    if entry:
        return entry
    entry = RevenueTotal(total_amount=Decimal("0"))
    db.add(entry)
    db.flush()
    return entry


def _increase_total_revenue(db: Session, amount: Decimal) -> None:
    if amount <= 0:
        return
    entry = _get_or_create_revenue_total(db)
    current = _parse_decimal_value(entry.total_amount)
    entry.total_amount = current + amount
    entry.updated_at = datetime.utcnow()
    db.add(entry)


def _renewal_offer_out(db: Session | None, user: User) -> BillingRenewalOffer | None:
    if db is None:
        return None
    offer = current_contract_offer(db, user)
    if offer is None:
        return None
    return BillingRenewalOffer(
        plan=offer.plan_key,
        billing_cycle="annual" if offer.billing_cycle == "annual" else "monthly",
        amount=float(offer.amount),
        title=offer.title,
    )


def _build_billing_info(user: User, db: Session | None = None) -> BillingInfo:
    sub = user.subscription
    legacy = legacy_renewal_info(sub)
    return BillingInfo(
        plan=effective_plan(user),
        status=sub.status if sub else "inactive",
        valid_until=sub.valid_until if sub else None,
        failed_attempts=sub.failed_attempts if sub else 0,
        preapproval_id=(sub.asaas_subscription_id or sub.preapproval_id) if sub else None,
        provider=sub.provider if sub else None,
        billing_cycle=sub.billing_cycle if sub else DEFAULT_CYCLE,
        payment_method_type=sub.payment_method_type if sub else None,
        card_brand=sub.card_brand if sub else None,
        card_last4=sub.card_last4 if sub else None,
        scheduled_downgrade_plan=(sub.external_reference.split("scheduled_downgrade:", 1)[1] if sub and sub.external_reference and sub.external_reference.startswith("scheduled_downgrade:") else None),
        scheduled_downgrade_at=sub.valid_until if sub and sub.external_reference and sub.external_reference.startswith("scheduled_downgrade:") else None,
        legacy=legacy.legacy,
        legacy_renewal_amount=legacy.amount,
        legacy_renewal_mode=legacy.mode,
        legacy_managed_externally=legacy.managed_externally,
        legacy_upgrade_available=legacy_upgrade_available(sub),
        pix_automatic_status=pix_automatic_status(db, user) if db is not None else None,
        renewal_offer=_renewal_offer_out(db, user),
    )


def _parse_asaas_date(value: Any) -> Optional[date]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def _extract_payment_link_url(payment_link: Any) -> Optional[str]:
    if isinstance(payment_link, dict):
        return str(payment_link.get("url") or payment_link.get("shortUrl") or "").strip() or None
    return None


def _normalize_asaas_payment(payment: dict[str, Any]) -> BillingInvoiceOut:
    status = str(payment.get("status") or "").strip().lower()
    due_date = str(payment.get("dueDate") or "").strip() or None
    payment_date = str(payment.get("paymentDate") or "").strip() or None
    invoice_url = str(payment.get("invoiceUrl") or "").strip() or None
    bank_slip_url = str(payment.get("bankSlipUrl") or "").strip() or None
    receipt_url = str(payment.get("transactionReceiptUrl") or payment.get("receiptUrl") or "").strip() or None
    payment_link_url = _extract_payment_link_url(payment.get("paymentLink"))
    current_due_date = _parse_asaas_date(due_date)
    is_paid = status in {"received", "confirmed", "received_in_cash"}
    bucket: Literal["paid", "overdue", "upcoming", "replaced"] = "paid"
    if not is_paid:
        bucket = "overdue" if current_due_date and current_due_date < date.today() else "upcoming"
        # Cancelada no Asaas: o status continua o de antes, só o campo "deleted" muda.
        if payment.get("deleted") is True:
            bucket = "replaced"
    pay_url = invoice_url or payment_link_url or bank_slip_url
    download_url = receipt_url or bank_slip_url or invoice_url or payment_link_url
    return BillingInvoiceOut(
        id=str(payment.get("id") or ""),
        customer_id=str(payment.get("customer") or "").strip() or None,
        subscription_id=str(payment.get("subscription") or "").strip() or None,
        status=status or "pending",
        billing_type=str(payment.get("billingType") or "").strip() or None,
        description=str(payment.get("description") or payment.get("name") or "").strip() or None,
        value=float(_parse_decimal_value(payment.get("value")).quantize(Decimal("0.01"))),
        due_date=due_date,
        payment_date=payment_date,
        invoice_url=invoice_url,
        bank_slip_url=bank_slip_url,
        receipt_url=receipt_url,
        pay_url=pay_url,
        download_url=download_url,
        is_paid=is_paid,
        bucket=bucket,
    )


def _fetch_asaas_payments(client: AsaasClient, params: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    limit = 100
    offset = 0
    while True:
        payload = client.list_payments(limit=limit, offset=offset, **params) or {}
        batch = payload.get("data") or []
        if not isinstance(batch, list) or not batch:
            break
        rows.extend([item for item in batch if isinstance(item, dict)])
        if len(batch) < limit:
            break
        offset += limit
        if offset >= 1000:
            break
    return rows


def _plan_rank(plan: str) -> int:
    mapping = {
        "free": 0,
        "essencial": 1,
        "growth": 2,
        "infinity": 3,
    }
    return mapping.get(_normalize_plan_key(plan), 0)


def _extract_resource_info(resource: Any) -> tuple[Optional[str], Dict[str, Any]]:
    if isinstance(resource, dict):
        return resource.get("id"), resource
    if isinstance(resource, str):
        return resource, {}
    return None, {}


def _set_subscription_active(subscription: Subscription, plan_key: str, due_date: Optional[str], cycle: str) -> None:
    subscription.plan = plan_key
    subscription.billing_cycle = cycle or DEFAULT_CYCLE
    subscription.status = "active"
    subscription.failed_attempts = 0
    period = _cycle_duration(subscription.billing_cycle)
    if due_date:
        try:
            parsed_due = datetime.fromisoformat(due_date)
            if parsed_due <= datetime.utcnow():
                subscription.valid_until = datetime.utcnow() + period
            else:
                subscription.valid_until = parsed_due + timedelta(days=1)
        except ValueError:
            subscription.valid_until = datetime.utcnow() + period
    else:
        subscription.valid_until = datetime.utcnow() + period


def set_subscription_cancelled(subscription: Subscription) -> None:
    subscription.status = "inactive"
    subscription.valid_until = None
    subscription.asaas_subscription_id = None
    subscription.asaas_payment_link_id = None
    subscription.external_reference = None
    subscription.mrr_amount = 0


def set_subscription_cancelled_at_period_end(subscription: Subscription) -> None:
    subscription.status = "inactive"
    subscription.failed_attempts = 0
    if not subscription.valid_until:
        subscription.valid_until = datetime.utcnow() + _cycle_duration(subscription.billing_cycle or DEFAULT_CYCLE)


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


def _notify_subscription_push(
    *,
    scenario: SubscriptionPushScenario,
    user: User,
    subscription: Subscription,
    payment_method: str | None = None,
    amount: Decimal | int | float | str | None = None,
    offer_name: str | None = None,
    cancelled_item: str | None = None,
) -> None:
    try:
        publish_subscription_notification(
            scenario=scenario,
            user_name=user.name or "Não informado",
            payment_method=_humanize_payment_method(payment_method or subscription.payment_method_type),
            amount=amount if amount is not None else subscription.mrr_amount,
            plan_name=subscription.plan or "Assinatura",
            offer_name=offer_name or subscription.external_reference or subscription.asaas_payment_link_id or subscription.asaas_subscription_id,
            cancelled_item=cancelled_item,
            customer_email=user.email,
            customer_phone=user.whatsapp,
        )
    except Exception:  # pragma: no cover - alerta não pode quebrar o webhook
        logger.exception("Falha ao enviar o aviso do webhook Asaas.")


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    payload = await request.json()
    event = payload.get("event")
    if not event:
        return {"received": True}
    event = str(event).upper()

    event_log, should_process = _register_asaas_event(db, payload)
    if not should_process:
        return {"received": True, "duplicate": True}

    try:
        _apply_asaas_event(db, payload)
        event_log.status = "processed"
        event_log.processed_at = datetime.utcnow()
        db.add(event_log)
        db.commit()
        return {"received": True}
    except Exception as exc:  # noqa: BLE001
        event_log.status = "error"
        event_log.error_message = str(exc)[:1000]
        db.add(event_log)
        db.commit()
        raise


def apply_asaas_payment(db: Session, payment: dict[str, Any], event: str = "PAYMENT_RECEIVED") -> bool:
    """Aplica um pagamento do Asaas na conta: o mesmo caminho do webhook, usado também pela
    conferência manual. Idempotente por id do pagamento: não estende o acesso nem soma a receita duas
    vezes. Devolve True quando este pagamento mexeu na conta agora."""
    return _apply_asaas_event(db, {"event": event, "payment": payment})


def _apply_asaas_event(db: Session, payload: dict[str, Any]) -> bool:
    event = str(payload.get("event") or "").upper()
    payment_id = str((payload.get("payment") or {}).get("id") or "").strip() or None
    paid_event = event in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"} and payment_id is not None
    if paid_event and payment_applied(db, payment_id):
        return False
    if event == "PAYMENT_DELETED" and payment_id and replaced_payment_ids(db, [payment_id]):
        # Cobrança que nós mesmos cancelamos ao criar a fatura nova: não encerra a conta.
        return True
    handled = _apply_asaas_event_once(db, payload, event)
    if paid_event and handled:
        mark_payment_applied(db, payment_id, event)
    return handled


def _apply_asaas_event_once(db: Session, payload: dict[str, Any], event: str) -> bool:
    """True quando o evento achou a conta (compra do checkout ou assinatura) e foi aplicado."""
    handled = False
    if handle_asaas_checkout_webhook(db, payload):
        return True

    if event.startswith("PAYMENT_"):
        payment = payload.get("payment") or {}
        parsed = _parse_external_reference(payment.get("externalReference"))
        matched_by_reference = parsed is not None
        if not parsed and event in FALLBACK_PAYMENT_EVENTS:
            parsed = _match_payment_by_asaas_subscription(db, payment)
        if parsed:
            user_id, plan_key, cycle = parsed
            cycle = cycle or DEFAULT_CYCLE
            user = db.query(User).get(user_id)
            if user:
                handled = True
                previous_status = str(user.subscription.status if user.subscription else "").strip().lower()
                subscription = _ensure_subscription(user)
                if matched_by_reference:
                    subscription.external_reference = payment.get("externalReference")
                sub_id, sub_data = _extract_resource_info(payment.get("subscription"))
                customer_id, _ = _extract_resource_info(payment.get("customer"))
                link_id, _ = _extract_resource_info(payment.get("paymentLink"))
                subscription.asaas_subscription_id = sub_id or subscription.asaas_subscription_id
                subscription.asaas_customer_id = customer_id or subscription.asaas_customer_id
                subscription.asaas_payment_link_id = link_id or subscription.asaas_payment_link_id

                if event in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}:
                    next_due = payment.get("nextDueDate") or sub_data.get("nextDueDate") or payment.get("dueDate")
                    _set_subscription_active(subscription, plan_key, next_due, cycle)
                    user.plan = plan_key
                    if not _is_comeco_like_plan(plan_key):
                        republish_all_user_pages(user, db)
                    payment_value = _parse_decimal_value(payment.get("netValue") or payment.get("value"))
                    _increase_total_revenue(db, payment_value)
                    if user.trial_plan:
                        end_trial(user, db, keep_plan=plan_key)
                    mark_viajechat_signed(
                        name=user.name or "",
                        email=user.email or "",
                        phone=user.whatsapp or "",
                        offer_key=plan_key,
                        upgrade_mode=False,
                    )
                    _notify_subscription_push(
                        scenario=SubscriptionPushScenario.RENEWED if previous_status == "active" else SubscriptionPushScenario.NEW,
                        user=user,
                        subscription=subscription,
                        payment_method=payment.get("billingType") or subscription.payment_method_type,
                        amount=payment_value,
                        offer_name=f"{plan_key}/{cycle}",
                    )
                elif event == "PAYMENT_OVERDUE":
                    # Inadimplente: no ar por 3 dias e cobrando por 30 (o job horário encerra depois).
                    mark_subscription_overdue(subscription, payment.get("dueDate"))
                    notify_payment_overdue(
                        user_name=user.name,
                        plan_name=plan_key,
                        amount=payment.get("value"),
                        due_date=payment.get("dueDate"),
                        payment_method=_humanize_payment_method(payment.get("billingType") or subscription.payment_method_type),
                        kind="Renovação" if previous_status in {"active", "past_due"} else "Primeira cobrança",
                        email=user.email,
                        phone=user.whatsapp,
                        dedupe_key=str(payment.get("id") or f"{user.id}:{payment.get('dueDate')}"),
                    )
                elif event in {"PAYMENT_REFUNDED", "PAYMENT_DELETED"}:
                    subscription.status = "inactive"
                    mark_viajechat_cancelled(
                        name=user.name or "",
                        email=user.email or "",
                        phone=user.whatsapp or "",
                    )
                    send_hub_refund(
                        email=user.email,
                        name=user.name,
                        phone=user.whatsapp,
                        reason="Estorno no Asaas" if event == "PAYMENT_REFUNDED" else "Cobrança apagada no Asaas",
                    )
                elif event in {"PAYMENT_REPROVED_BY_RISK_ANALYSIS"}:
                    subscription.status = "failed"
                elif event in {"PAYMENT_CREATED", "PAYMENT_UPDATED"}:
                    # Cobrança criada ou atualizada não muda o acesso de quem está em dia.
                    pass
                else:
                    subscription.status = "pending"

                db.add_all([user, subscription])
                db.commit()

    if event in {"SUBSCRIPTION_DELETED", "SUBSCRIPTION_CANCELLED"}:
        sub_payload = payload.get("subscription") or {}
        sub_id = sub_payload.get("id")
        if sub_id:
            subscription = db.query(Subscription).filter(Subscription.asaas_subscription_id == sub_id).first()
            if subscription:
                user = db.query(User).get(subscription.user_id)
                set_subscription_cancelled_at_period_end(subscription)
                if user:
                    mark_viajechat_cancelled(
                        name=user.name or "",
                        email=user.email or "",
                        phone=user.whatsapp or "",
                    )
                    _notify_subscription_push(
                        scenario=SubscriptionPushScenario.CANCELLED,
                        user=user,
                        subscription=subscription,
                        payment_method=sub_payload.get("billingType") or subscription.payment_method_type,
                        amount=subscription.mrr_amount,
                        offer_name=subscription.external_reference or subscription.asaas_subscription_id,
                        cancelled_item=f"Assinatura {subscription.plan or subscription.asaas_subscription_id or subscription.id}",
                    )
                    db.add(user)
                db.add(subscription)
                db.commit()
    elif event == "SUBSCRIPTION_UPDATED":
        sub_payload = payload.get("subscription") or {}
        sub_id = sub_payload.get("id")
        if sub_id:
            subscription = db.query(Subscription).filter(Subscription.asaas_subscription_id == sub_id).first()
            if subscription:
                cycle = str(sub_payload.get("cycle") or "").upper()
                if cycle in {"MONTHLY", "YEARLY"}:
                    subscription.billing_cycle = "annual" if cycle == "YEARLY" else "monthly"
                if (sub_payload.get("status") or "").upper() in {"ACTIVE"}:
                    subscription.status = "active"
                db.add(subscription)
                db.commit()

    return handled


@router.get("/me", response_model=BillingInfo)
def get_billing_info(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> BillingInfo:
    return _build_billing_info(current_user, db)


_EMPTY_COUNTS = {"paid": 0, "overdue": 0, "upcoming": 0, "replaced": 0}
# Conferência manual: no máximo uma chamada ao Asaas a cada 10 segundos por conta.
SYNC_MIN_INTERVAL_SECONDS = 10
_last_invoice_sync: dict[int, float] = {}


def _account_status(user: User) -> tuple[str, bool]:
    subscription = user.subscription
    if subscription is None:
        return "inactive", False
    blocked = bool(user.subscription_blocked)
    status = str(subscription.status or "").strip().lower()
    if blocked:
        return "blocked", True
    if status == "past_due":
        return "past_due", False
    if status in ENDED_STATUSES:
        valid_until = subscription.valid_until
        if valid_until is not None and valid_until.replace(tzinfo=None) > datetime.utcnow():
            return "cancelling", False
        return "inactive", False
    return "active", False


def _classify_invoices(db: Session, subscription: Subscription, items: list[BillingInvoiceOut]) -> None:
    """Período coberto de cada fatura e quais em aberto não valem mais (cancelada por troca ou de um
    período que outra fatura paga já cobre). Muda os itens no lugar."""
    cycle = subscription.billing_cycle or DEFAULT_CYCLE
    paid_periods: list[tuple[date, date]] = []
    for item in items:
        period = covered_period(parse_date(item.due_date), cycle)
        if period:
            item.period_start, item.period_end = period[0].isoformat(), period[1].isoformat()
            if item.is_paid:
                paid_periods.append(period)
    replaced = replaced_payment_ids(db, [item.id for item in items if not item.is_paid])
    for item in items:
        if item.is_paid:
            continue
        if item.id in replaced or covered_by_paid(parse_date(item.due_date), paid_periods):
            item.bucket = "replaced"


def _build_account(db: Session, user: User, items: list[BillingInvoiceOut]) -> BillingAccountOut:
    status, blocked = _account_status(user)
    overdue = [item for item in items if item.bucket == "overdue"]
    upcoming = sorted((item for item in items if item.bucket == "upcoming"), key=lambda item: item.due_date or "9999-12-31")
    unlocking = max(overdue, key=lambda item: item.due_date or "") if overdue else None
    next_item = upcoming[0] if upcoming else None
    return BillingAccountOut(
        status=status,
        blocked=blocked,
        access_until=user.subscription.valid_until if user.subscription else None,
        open_amount=round(sum(item.value for item in overdue), 2),
        open_count=len(overdue),
        next_charge=BillingNextCharge(due_date=next_item.due_date, amount=next_item.value)
        if next_item and next_item.due_date
        else None,
        unlocking_invoice_id=unlocking.id if unlocking else None,
        pix_automatic_status=pix_automatic_status(db, user),
        renewal_offer=_renewal_offer_out(db, user),
    )


@router.get("/invoices", response_model=BillingInvoicesResponse)
def list_billing_invoices(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> BillingInvoicesResponse:
    subscription = current_user.subscription
    if not subscription or subscription.provider != "asaas":
        return BillingInvoicesResponse(items=[], total=0, counts=dict(_EMPTY_COUNTS))

    client = _get_asaas_client()
    query: dict[str, Any] = {}
    if subscription.asaas_customer_id:
        query["customer"] = subscription.asaas_customer_id
    elif subscription.asaas_subscription_id:
        query["subscription"] = subscription.asaas_subscription_id
    else:
        return BillingInvoicesResponse(items=[], total=0, counts=dict(_EMPTY_COUNTS))

    try:
        payments = _fetch_asaas_payments(client, query)
    except AsaasAPIError as exc:  # noqa: BLE001
        logger.exception("Erro ao listar faturas no Asaas: %s", exc)
        raise HTTPException(status_code=502, detail="Erro ao listar faturas no Asaas") from exc

    items = [_normalize_asaas_payment(payment) for payment in payments if payment.get("id")]
    _classify_invoices(db, subscription, items)
    order = {"overdue": 0, "upcoming": 1, "paid": 2, "replaced": 3}
    items.sort(
        key=lambda item: (
            order.get(item.bucket, 4),
            item.due_date or "9999-12-31",
            item.payment_date or "9999-12-31",
        )
    )
    counts = {key: sum(1 for item in items if item.bucket == key) for key in _EMPTY_COUNTS}
    return BillingInvoicesResponse(
        items=items, total=len(items), counts=counts, account=_build_account(db, current_user, items)
    )


@router.post("/invoices/{payment_id}/sync", response_model=InvoiceSyncOut)
def sync_billing_invoice(
    payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> InvoiceSyncOut:
    """Confere uma fatura no Asaas na hora e, se estiver paga, aplica na conta (quando o aviso do
    Asaas atrasou ou falhou). Só aceita fatura do próprio cliente."""
    subscription = current_user.subscription
    if not subscription or subscription.provider != "asaas":
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")
    now = time.monotonic()
    last = _last_invoice_sync.get(current_user.id)
    if last is not None and now - last < SYNC_MIN_INTERVAL_SECONDS:
        raise HTTPException(status_code=429, detail="Aguarde alguns segundos para conferir de novo.")
    _last_invoice_sync[current_user.id] = now

    client = _get_asaas_client()
    try:
        payment = client.get_payment(payment_id) or {}
    except AsaasAPIError as exc:  # noqa: BLE001
        logger.warning("Fatura %s não encontrada no Asaas: %s", payment_id, exc)
        raise HTTPException(status_code=404, detail="Fatura não encontrada.") from exc

    customer_id, _ = _extract_resource_info(payment.get("customer"))
    payment_subscription_id, _ = _extract_resource_info(payment.get("subscription"))
    owns = bool(customer_id and customer_id == subscription.asaas_customer_id) or bool(
        payment_subscription_id and payment_subscription_id == subscription.asaas_subscription_id
    )
    if not payment.get("id") or not owns:
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")

    paid = is_paid_payment(payment)
    applied = apply_asaas_payment(db, payment) if paid else False
    invoice = _normalize_asaas_payment(payment)
    return InvoiceSyncOut(paid=paid, applied=applied, status=invoice.status, invoice=invoice)


@router.post("/cancel", response_model=BillingInfo)
def cancel_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> BillingInfo:
    sub = current_user.subscription
    if not sub:
        raise HTTPException(status_code=404, detail="Assinatura nÃ£o encontrada")

    if sub.provider == "cakto":
        service = CaktoIntegrationService(db)
        try:
            service.cancel_remote_subscription(
                subscription_code=sub.cakto_subscription_code,
                order_id=sub.cakto_order_id,
            )
        except CaktoAPIError as exc:  # noqa: BLE001
            logger.exception("Erro ao cancelar assinatura Cakto: %s", exc)
            raise HTTPException(status_code=502, detail="Erro ao cancelar assinatura") from exc
    else:
        client = _get_asaas_client()
        try:
            _cancel_asaas_subscription_billing(db, client, sub)
        except AsaasAPIError as exc:  # noqa: BLE001
            logger.exception("Erro ao cancelar assinatura Asaas: %s", exc)
            raise HTTPException(status_code=502, detail="Erro ao cancelar assinatura") from exc

    set_subscription_cancelled_at_period_end(sub)
    mark_viajechat_cancelled(
        name=current_user.name or "",
        email=current_user.email or "",
        phone=current_user.whatsapp or "",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    db.refresh(current_user)

    return _build_billing_info(current_user, db)


@router.post("/change-plan", response_model=BillingInfo)
def change_plan(
    payload: PlanChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    plan_key = payload.plan.lower()
    if plan_key != "free":
        raise HTTPException(status_code=400, detail="Apenas downgrade para o plano gratuito Ã© suportado por aqui.")

    sub = current_user.subscription
    client = _get_asaas_client()
    if sub:
        try:
            _cancel_asaas_subscription_billing(db, client, sub)
        except AsaasAPIError as exc:  # noqa: BLE001
            logger.exception("Erro ao encerrar assinatura Asaas ao mudar para free: %s", exc)
            raise HTTPException(status_code=502, detail="Erro ao cancelar assinatura no Asaas") from exc

        set_subscription_cancelled_at_period_end(sub)
        db.add(sub)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return _build_billing_info(current_user, db)


@router.post("/schedule-downgrade", response_model=BillingInfo)
def schedule_downgrade(
    payload: PlanChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    target_plan = _normalize_plan_key(payload.plan)
    if target_plan not in PLAN_PRICING:
        raise HTTPException(status_code=400, detail="Plano de downgrade invÃ¡lido.")

    current_plan = _normalize_plan_key(effective_plan(current_user) or "free")
    if _plan_rank(target_plan) >= _plan_rank(current_plan):
        raise HTTPException(status_code=400, detail="Apenas downgrade Ã© permitido nesta operaÃ§Ã£o.")

    sub = current_user.subscription
    if not sub:
        raise HTTPException(status_code=404, detail="Assinatura nÃ£o encontrada.")
    if not sub.valid_until:
        raise HTTPException(status_code=400, detail="NÃ£o foi possÃ­vel determinar a validade atual para agendar downgrade.")

    # Mark scheduled downgrade in local system; Asaas change will be applied by background job at D-1.
    sub.external_reference = f"scheduled_downgrade:{target_plan}"

    db.add(sub)
    db.commit()
    db.refresh(current_user)
    return _build_billing_info(current_user, db)


@router.post("/cancel-scheduled-downgrade", response_model=BillingInfo)
def cancel_scheduled_downgrade(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    sub = current_user.subscription
    if not sub or not sub.external_reference or not sub.external_reference.startswith("scheduled_downgrade:"):
        raise HTTPException(status_code=400, detail="NÃ£o existe downgrade agendado para cancelar.")

    current_plan = _normalize_plan_key(effective_plan(current_user) or "free")
    cycle = (sub.billing_cycle or DEFAULT_CYCLE).lower()
    plan_info = PLAN_PRICING.get(current_plan, {}).get(cycle)

    if sub.asaas_subscription_id and sub.provider == "asaas" and plan_info:
        client = _get_asaas_client()
        try:
            client.update_subscription(
                sub.asaas_subscription_id,
                {
                    "value": plan_info["price"],
                    "cycle": plan_info["asaas_cycle"],
                    "externalReference": _build_external_reference(current_user.id, current_plan, cycle),
                    "split": build_default_split_payload(),
                },
            )
        except AsaasAPIError as exc:  # noqa: BLE001
            logger.exception("Erro ao cancelar downgrade agendado no Asaas: %s", exc)
            raise HTTPException(status_code=502, detail="Erro ao cancelar downgrade agendado no Asaas") from exc

    sub.external_reference = None
    db.add(sub)
    db.commit()
    db.refresh(current_user)
    return _build_billing_info(current_user, db)


@router.post("/refresh-payment-method", response_model=CheckoutResponse, deprecated=True)
def refresh_payment_method(
    payload: PaymentMethodUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    """Em desuso: gerava um link com a tabela antiga de planos. Agora devolve a renovação na oferta
    atual do cliente (plano, ciclo e valor do contrato dele); o ciclo enviado é ignorado."""
    session = create_renewal_checkout_session(db, current_user)
    base = (settings.webapp_base_url or "").rstrip("/")
    return CheckoutResponse(
        init_point=f"{base}/checkout/{LEGACY_RENEWAL_OFFER_KEY}?upgrade=1&token={session.token}",
        preapproval_id=None,
    )


def _guess_card_brand(digits: str) -> str | None:
    if digits.startswith("4"):
        return "Visa"
    if (len(digits) >= 2 and 51 <= int(digits[:2]) <= 55) or (len(digits) >= 4 and 2221 <= int(digits[:4]) <= 2720):
        return "Mastercard"
    if digits.startswith(("34", "37")):
        return "Amex"
    if digits.startswith(("6062", "3841")):
        return "Hipercard"
    if digits.startswith(("4011", "4312", "4389")):
        return "Elo"
    return None


def _remember_card(subscription: Subscription, digits: str) -> None:
    subscription.payment_method_type = "card"
    subscription.card_last4 = digits[-4:] if len(digits) >= 4 else None
    subscription.card_brand = _guess_card_brand(digits)


def _installment_card_session(db: Session, user: User) -> CheckoutSession | None:
    """Compra do anual parcelado no cartão: a renovação é cobrada pelo job, no cartão salvo."""
    rows = (
        db.query(CheckoutSession)
        .filter(CheckoutSession.user_id == user.id, CheckoutSession.payment_method == "card", CheckoutSession.status == "paid")
        .order_by(CheckoutSession.id.desc())
        .all()
    )
    return next((row for row in rows if (row.metadata_json or {}).get("card_token")), None)


def _open_invoice_to_pay(client: AsaasClient, customer_id: str) -> dict[str, Any] | None:
    """Fatura vencida mais recente do cliente (a que libera o acesso quando paga)."""
    rows: list[dict[str, Any]] = []
    for status in ("OVERDUE", "PENDING"):
        data = (client.list_payments(customer=customer_id, status=status, limit=100) or {}).get("data") or []
        rows.extend(item for item in data if isinstance(item, dict) and item.get("id"))
    due = [item for item in rows if (parse_date(item.get("dueDate")) or date.max) <= date.today()]
    return max(due, key=lambda item: str(item.get("dueDate") or "")) if due else None


def _pay_open_invoice_with_card(
    db: Session,
    client: AsaasClient,
    subscription: Subscription,
    customer_id: str | None,
    card_payload: dict[str, Any],
    plan_key: str,
    billing_cycle: str,
) -> None:
    """Fatura vencida do cliente é paga na hora no cartão novo (o Asaas confirma na mesma chamada e
    a cobrança passa a CREDIT_CARD). Cartão recusado interrompe antes de qualquer troca."""
    if not customer_id:
        return
    open_invoice = _open_invoice_to_pay(client, customer_id)
    if open_invoice is None:
        return
    paid = client.pay_with_credit_card(str(open_invoice["id"]), card_payload) or {}
    if not is_paid_payment(paid):
        raise HTTPException(status_code=402, detail="O cartão não foi aprovado. Confira os dados ou use outro cartão.")
    full_payment = {**open_invoice, **paid}
    if not apply_asaas_payment(db, full_payment) and not payment_applied(db, str(full_payment.get("id"))):
        _set_subscription_active(subscription, subscription.plan or plan_key, None, billing_cycle)
        _increase_total_revenue(db, _parse_decimal_value(full_payment.get("netValue") or full_payment.get("value")))
        db.add(subscription)
        db.commit()
        mark_payment_applied(db, str(full_payment.get("id")), "PAYMENT_RECEIVED")
    db.refresh(subscription)


def _switch_pix_automatic_to_card(
    db: Session,
    client: AsaasClient,
    user: User,
    subscription: Subscription,
    card_payload: dict[str, Any],
    digits: str,
) -> None:
    """Quem paga por Pix Automático não tem assinatura no Asaas: cria uma no cartão, com o mesmo plano,
    ciclo e valor, e só depois cancela a autorização Pix. Com fatura em aberto, ela é paga na hora no
    cartão novo e a próxima cobrança passa a ser a partir do novo vencimento."""
    contract = current_contract_offer(db, user)
    customer_id = subscription.asaas_customer_id
    if contract is None or not customer_id:
        raise HTTPException(status_code=400, detail="Não encontramos o plano e o valor do seu contrato. Fale com o suporte.")

    _pay_open_invoice_with_card(db, client, subscription, customer_id, card_payload, contract.plan_key, contract.billing_cycle)

    valid_until = subscription.valid_until
    next_due = valid_until.date() if valid_until is not None and valid_until.replace(tzinfo=None) > datetime.utcnow() else date.today()
    cycle_name = "annual" if contract.billing_cycle == "annual" else "monthly"
    created = client.create_subscription(
        {
            "customer": customer_id,
            "billingType": "CREDIT_CARD",
            "nextDueDate": next_due.isoformat(),
            "cycle": "YEARLY" if cycle_name == "annual" else "MONTHLY",
            "value": float(contract.amount),
            "description": contract.title,
            "externalReference": _build_external_reference(user.id, contract.plan_key, cycle_name),
            "split": build_default_split_payload(),
            **card_payload,
        }
    )
    new_subscription_id, _ = _extract_resource_info(created.get("id") if isinstance(created, dict) else None)
    if not new_subscription_id:
        raise HTTPException(status_code=502, detail="O Asaas não confirmou a assinatura no cartão.")

    authorization_id = find_pix_automatic_authorization_id(db, user_id=user.id)
    if authorization_id:
        try:
            client.cancel_pix_automatic_authorization(authorization_id, reason="Troca para cartão pelo cliente")
        except AsaasAPIError:
            logger.exception("Autorização Pix Automático %s não foi cancelada após a troca para cartão.", authorization_id)
        for row in db.query(CheckoutSession).filter(CheckoutSession.user_id == user.id, CheckoutSession.payment_method == "pix").all():
            metadata = dict(row.metadata_json or {})
            if metadata.get("asaas_pix_automatic_authorization_id") == authorization_id:
                metadata["asaas_pix_automatic_authorization_status"] = "CANCELLED"
                row.metadata_json = metadata
                db.add(row)
    cancel_open_payments(db, client, customer_id=customer_id, new_subscription_id=new_subscription_id, replaced_by=new_subscription_id)

    subscription.asaas_subscription_id = new_subscription_id
    subscription.external_reference = _build_external_reference(user.id, contract.plan_key, cycle_name)
    _remember_card(subscription, digits)
    db.add(subscription)


@router.post("/update-card", response_model=BillingInfo)
def update_card(
    payload: CardUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    subscription = current_user.subscription
    installment_session = _installment_card_session(db, current_user) if subscription and not subscription.asaas_subscription_id else None
    pix_customer = bool(
        subscription
        and not subscription.asaas_subscription_id
        and installment_session is None
        and str(subscription.payment_method_type or "").strip().lower() == "pix"
    )
    if not subscription or not (subscription.asaas_subscription_id or installment_session or pix_customer):
        raise HTTPException(status_code=400, detail="Nenhuma assinatura com cartÃ£o ativo encontrada.")

    customer_document = (current_user.cnpj or current_user.cpf or "").strip()
    postal_code = (current_user.address_zipcode or "").replace("-", "").strip()
    if len("".join(ch for ch in customer_document if ch.isdigit())) not in {11, 14}:
        raise HTTPException(status_code=400, detail="Complete CPF/CNPJ no perfil antes de trocar para cartão.")
    if len("".join(ch for ch in postal_code if ch.isdigit())) < 8:
        raise HTTPException(status_code=400, detail="Complete o CEP no perfil antes de trocar para cartão.")
    if not (current_user.name or "").strip() or not (current_user.email or "").strip():
        raise HTTPException(status_code=400, detail="Complete nome e e-mail no perfil antes de trocar para cartão.")

    card_number_digits = "".join(ch for ch in payload.number if ch.isdigit())
    if len(card_number_digits) < 13:
        raise HTTPException(status_code=400, detail="Número do cartão inválido.")
    resolved_ip = get_client_ip(request) or payload.remote_ip or (request.client.host if request.client else None) or "127.0.0.1"
    card_payload = {
        "creditCard": {
            "holderName": payload.holder_name,
            "number": card_number_digits,
            "expiryMonth": payload.expiry_month,
            "expiryYear": payload.expiry_year,
            "ccv": payload.ccv,
        },
        "creditCardHolderInfo": {
            "name": current_user.name,
            "email": current_user.email,
            "cpfCnpj": customer_document,
            "postalCode": postal_code,
            "addressNumber": current_user.address_number or "S/N",
            "addressComplement": current_user.address_complement,
            "phone": current_user.whatsapp,
            "mobilePhone": current_user.whatsapp,
        },
        "remoteIp": resolved_ip,
    }

    client = _get_asaas_client()
    try:
        if installment_session is not None:
            # Anual parcelado: troca o cartão salvo, que o job usa na renovação.
            result = client.tokenize_credit_card({"customer": subscription.asaas_customer_id, **card_payload})
            token = str((result or {}).get("creditCardToken") or "").strip()
            if not token:
                raise HTTPException(status_code=502, detail="O Asaas não salvou o cartão. Tente de novo.")
            metadata = dict(installment_session.metadata_json or {})
            metadata["card_token"] = token
            installment_session.metadata_json = metadata
            db.add(installment_session)
            _remember_card(subscription, card_number_digits)
        elif pix_customer:
            _switch_pix_automatic_to_card(db, client, current_user, subscription, card_payload, card_number_digits)
        else:
            # O Asaas não troca o cartão de cobranças que já estavam pendentes: a vencida é paga já
            # no cartão novo (se recusar, nada muda); as que vencem depois seguem a assinatura.
            _pay_open_invoice_with_card(
                db, client, subscription, subscription.asaas_customer_id, card_payload,
                subscription.plan or "", subscription.billing_cycle or DEFAULT_CYCLE,
            )
            client.update_subscription(subscription.asaas_subscription_id, {"billingType": "CREDIT_CARD"})
            client.update_subscription_card(subscription.asaas_subscription_id, card_payload)
            _remember_card(subscription, card_number_digits)
    except AsaasAPIError as exc:  # noqa: BLE001
        logger.exception("Erro ao atualizar cartÃ£o da assinatura Asaas: %s", exc)
        raise HTTPException(status_code=502, detail=f"Erro ao atualizar cartão no Asaas. {_extract_asaas_error_detail(exc)}") from exc

    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    db.refresh(current_user)
    return _build_billing_info(current_user, db)


@router.post("/update-payment-method", response_model=PaymentMethodChangeOut)
def update_payment_method(
    payload: PaymentMethodChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PaymentMethodChangeOut:
    subscription = current_user.subscription
    if not subscription or str(subscription.plan or "").strip().lower() in {"", "free"}:
        raise HTTPException(status_code=400, detail="Nenhuma assinatura ativa encontrada.")
    info = _build_billing_info(current_user, db).model_dump()

    if payload.method == "pix":
        # Pix é sempre uma nova autorização do Pix Automático, no mesmo plano e valor (a troca para
        # Pix comum saiu). A tela segue para o QR Code com a sessão de renovação.
        session = create_renewal_checkout_session(db, current_user)
        return PaymentMethodChangeOut(**info, checkout_token=session.token)

    # Cartão: os dados do cartão seguem em /billing/update-card, que faz a troca.
    return PaymentMethodChangeOut(**info)
