import logging
import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.models.subscription import Subscription
from app.models.user import User
from app.models.revenue import RevenueTotal
from app.models.asaas import AsaasEventLog
from app.services.asaas import AsaasAPIError, AsaasClient, build_default_split_payload
from app.services.cakto import CaktoAPIError, CaktoIntegrationService
from app.services.checkout import handle_asaas_checkout_webhook
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
        raise HTTPException(status_code=500, detail="Chave da API Asaas não configurada")
    return AsaasClient(settings.asaas_api_key, settings.asaas_base_url)


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


class PlanChangeRequest(BaseModel):
    plan: str


class PaymentMethodUpdateRequest(BaseModel):
    cycle: Optional[str] = None


class PaymentMethodChangeRequest(BaseModel):
    method: Literal["pix", "card"]


class CardUpdateRequest(BaseModel):
    holder_name: str
    number: str
    expiry_month: str
    expiry_year: str
    ccv: str


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
        raise HTTPException(status_code=400, detail="Plano inválido")
    plan_options = PLAN_PRICING[plan_key]
    plan_info = plan_options.get(cycle)
    if not plan_info:
        raise HTTPException(status_code=400, detail="Ciclo de cobrança inválido")

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
        raise HTTPException(status_code=502, detail="Asaas não retornou URL de pagamento")
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


def _build_billing_info(user: User) -> BillingInfo:
    sub = user.subscription
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
    )


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
        if handle_asaas_checkout_webhook(db, payload):
            event_log.status = "processed"
            event_log.processed_at = datetime.utcnow()
            db.add(event_log)
            db.commit()
            return {"received": True}

        if event.startswith("PAYMENT_"):
            payment = payload.get("payment") or {}
            parsed = _parse_external_reference(payment.get("externalReference"))
            if parsed:
                user_id, plan_key, cycle = parsed
                cycle = cycle or DEFAULT_CYCLE
                user = db.query(User).get(user_id)
                if user:
                    previous_plan = str(user.plan or "").strip().lower()
                    subscription = _ensure_subscription(user)
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
                    elif event == "PAYMENT_OVERDUE":
                        subscription.failed_attempts = (subscription.failed_attempts or 0) + 1
                        if subscription.failed_attempts >= 3:
                            set_subscription_cancelled(subscription)
                        else:
                            subscription.status = "past_due"
                    elif event in {"PAYMENT_REFUNDED", "PAYMENT_DELETED"}:
                        subscription.status = "inactive"
                        mark_viajechat_cancelled(
                            name=user.name or "",
                            email=user.email or "",
                            phone=user.whatsapp or "",
                        )
                    elif event in {"PAYMENT_REPROVED_BY_RISK_ANALYSIS"}:
                        subscription.status = "failed"
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


@router.get("/me", response_model=BillingInfo)
def get_billing_info(current_user: User = Depends(get_current_active_user)) -> BillingInfo:
    return _build_billing_info(current_user)


@router.post("/cancel", response_model=BillingInfo)
def cancel_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> BillingInfo:
    sub = current_user.subscription
    if not sub:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

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
            if sub.asaas_subscription_id:
                client.cancel_subscription(sub.asaas_subscription_id)
            elif sub.asaas_payment_link_id:
                client.delete_payment_link(sub.asaas_payment_link_id)
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

    return _build_billing_info(current_user)


@router.post("/change-plan", response_model=BillingInfo)
def change_plan(
    payload: PlanChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    plan_key = payload.plan.lower()
    if plan_key != "free":
        raise HTTPException(status_code=400, detail="Apenas downgrade para o plano gratuito é suportado por aqui.")

    sub = current_user.subscription
    client = _get_asaas_client()
    if sub:
        try:
            if sub.asaas_subscription_id:
                client.cancel_subscription(sub.asaas_subscription_id)
            elif sub.asaas_payment_link_id:
                client.delete_payment_link(sub.asaas_payment_link_id)
        except AsaasAPIError as exc:  # noqa: BLE001
            logger.exception("Erro ao encerrar assinatura Asaas ao mudar para free: %s", exc)
            raise HTTPException(status_code=502, detail="Erro ao cancelar assinatura no Asaas") from exc

        set_subscription_cancelled_at_period_end(sub)
        db.add(sub)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return _build_billing_info(current_user)


@router.post("/schedule-downgrade", response_model=BillingInfo)
def schedule_downgrade(
    payload: PlanChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    target_plan = _normalize_plan_key(payload.plan)
    if target_plan not in PLAN_PRICING:
        raise HTTPException(status_code=400, detail="Plano de downgrade inválido.")

    current_plan = _normalize_plan_key(effective_plan(current_user) or "free")
    if _plan_rank(target_plan) >= _plan_rank(current_plan):
        raise HTTPException(status_code=400, detail="Apenas downgrade é permitido nesta operação.")

    sub = current_user.subscription
    if not sub:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")
    if not sub.valid_until:
        raise HTTPException(status_code=400, detail="Não foi possível determinar a validade atual para agendar downgrade.")

    # Mark scheduled downgrade in local system; Asaas change will be applied by background job at D-1.
    sub.external_reference = f"scheduled_downgrade:{target_plan}"

    db.add(sub)
    db.commit()
    db.refresh(current_user)
    return _build_billing_info(current_user)


@router.post("/cancel-scheduled-downgrade", response_model=BillingInfo)
def cancel_scheduled_downgrade(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    sub = current_user.subscription
    if not sub or not sub.external_reference or not sub.external_reference.startswith("scheduled_downgrade:"):
        raise HTTPException(status_code=400, detail="Não existe downgrade agendado para cancelar.")

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
    return _build_billing_info(current_user)


@router.post("/refresh-payment-method", response_model=CheckoutResponse)
def refresh_payment_method(
    payload: PaymentMethodUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    subscription = current_user.subscription
    if not subscription or not subscription.plan or subscription.plan == "free":
        raise HTTPException(status_code=400, detail="Nenhuma assinatura paga ativa para atualizar.")

    plan_key = subscription.plan
    plan_options = PLAN_PRICING.get(plan_key)
    if not plan_options:
        raise HTTPException(status_code=400, detail="Plano atual não suporta cobrança automática.")

    cycle = (payload.cycle or subscription.billing_cycle or DEFAULT_CYCLE).lower()
    plan_info = plan_options.get(cycle)
    if not plan_info:
        raise HTTPException(status_code=400, detail="Ciclo de cobrança inválido para o plano atual.")

    client = _get_asaas_client()
    if subscription.asaas_payment_link_id:
        try:
            client.delete_payment_link(subscription.asaas_payment_link_id)
        except AsaasAPIError as exc:  # noqa: BLE001
            logger.warning("Falha ao remover link de pagamento antigo no Asaas: %s", exc)

    external_ref = _build_external_reference(current_user.id, plan_key, cycle)
    redirect_url = settings.asaas_success_url or settings.stripe_success_url or settings.mp_success_url
    request_payload: Dict[str, Any] = {
        "name": plan_info["title"],
        "description": f"Atualização do {plan_info['title']}",
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

    try:
        link = client.create_payment_link(request_payload)
    except AsaasAPIError as exc:  # noqa: BLE001
        logger.exception("Erro ao recriar link de pagamento Asaas: %s", exc)
        raise HTTPException(status_code=502, detail="Erro ao gerar link de pagamento") from exc

    subscription.asaas_payment_link_id = link.get("id")
    subscription.external_reference = external_ref
    subscription.preapproval_id = link.get("id")
    subscription.billing_cycle = cycle
    db.add(subscription)
    db.commit()

    checkout_url = link.get("url") or link.get("shortUrl") or ""
    if not checkout_url:
        raise HTTPException(status_code=502, detail="Asaas não retornou URL de pagamento")
    return CheckoutResponse(init_point=checkout_url, preapproval_id=link.get("id"))


@router.post("/update-card", response_model=BillingInfo)
def update_card(
    payload: CardUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    subscription = current_user.subscription
    if not subscription or not subscription.asaas_subscription_id:
        raise HTTPException(status_code=400, detail="Nenhuma assinatura com cartão ativo encontrada.")

    card_payload = {
        "holderName": payload.holder_name,
        "number": payload.number,
        "expiryMonth": payload.expiry_month,
        "expiryYear": payload.expiry_year,
        "ccv": payload.ccv,
    }

    client = _get_asaas_client()
    try:
        client.update_subscription_card(subscription.asaas_subscription_id, card_payload)
    except AsaasAPIError as exc:  # noqa: BLE001
        logger.exception("Erro ao atualizar cartão da assinatura Asaas: %s", exc)
        raise HTTPException(status_code=502, detail="Erro ao atualizar cartão no Asaas") from exc

    digits = "".join(ch for ch in payload.number if ch.isdigit())
    subscription.payment_method_type = "card"
    subscription.card_last4 = digits[-4:] if len(digits) >= 4 else None
    if digits.startswith("4"):
        subscription.card_brand = "Visa"
    elif (len(digits) >= 2 and 51 <= int(digits[:2]) <= 55) or (len(digits) >= 4 and 2221 <= int(digits[:4]) <= 2720):
        subscription.card_brand = "Mastercard"
    elif digits.startswith(("34", "37")):
        subscription.card_brand = "Amex"
    elif digits.startswith(("6062", "3841")):
        subscription.card_brand = "Hipercard"
    elif digits.startswith(("4011", "4312", "4389")):
        subscription.card_brand = "Elo"
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    db.refresh(current_user)
    return _build_billing_info(current_user)


@router.post("/update-payment-method", response_model=BillingInfo)
def update_payment_method(
    payload: PaymentMethodChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BillingInfo:
    subscription = current_user.subscription
    if not subscription or not subscription.asaas_subscription_id:
        raise HTTPException(status_code=400, detail="Nenhuma assinatura ativa encontrada.")

    if payload.method == "pix":
        client = _get_asaas_client()
        try:
            client.update_subscription(subscription.asaas_subscription_id, {"billingType": "PIX"})
        except AsaasAPIError as exc:  # noqa: BLE001
            logger.exception("Erro ao alterar forma de pagamento para PIX no Asaas: %s", exc)
            raise HTTPException(status_code=502, detail="Erro ao alterar forma de pagamento no Asaas") from exc

        subscription.payment_method_type = "pix"
        subscription.card_brand = None
        subscription.card_last4 = None
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        db.refresh(current_user)
        return _build_billing_info(current_user)

    # For card we keep the same behavior: user must submit card data in /billing/update-card.
    subscription.payment_method_type = "card"
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    db.refresh(current_user)
    return _build_billing_info(current_user)
