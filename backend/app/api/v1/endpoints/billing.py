import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.models.subscription import Subscription
from app.models.user import User
from app.services.asaas import AsaasAPIError, AsaasClient
from app.services.plans import effective_plan

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


class PlanChangeRequest(BaseModel):
    plan: str


class PaymentMethodUpdateRequest(BaseModel):
    cycle: Optional[str] = None


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
    )


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


def _set_subscription_cancelled(subscription: Subscription) -> None:
    subscription.plan = "free"
    subscription.status = "cancelled"
    subscription.valid_until = None
    subscription.asaas_subscription_id = None
    subscription.asaas_payment_link_id = None
    subscription.external_reference = None
    subscription.billing_cycle = DEFAULT_CYCLE


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    payload = await request.json()
    event = payload.get("event")
    if not event:
        return {"received": True}

    if event.startswith("PAYMENT_"):
        payment = payload.get("payment") or {}
        parsed = _parse_external_reference(payment.get("externalReference"))
        if not parsed:
            return {"received": True}
        user_id, plan_key, cycle = parsed
        cycle = cycle or DEFAULT_CYCLE
        user = db.query(User).get(user_id)
        if not user:
            return {"received": True}
        subscription = _ensure_subscription(user)
        subscription.external_reference = payment.get("externalReference")
        sub_id, sub_data = _extract_resource_info(payment.get("subscription"))
        customer_id, _ = _extract_resource_info(payment.get("customer"))
        link_id, _ = _extract_resource_info(payment.get("paymentLink"))
        subscription.asaas_subscription_id = sub_id or subscription.asaas_subscription_id
        subscription.asaas_customer_id = customer_id or subscription.asaas_customer_id
        subscription.asaas_payment_link_id = link_id or subscription.asaas_payment_link_id

        if event == "PAYMENT_CONFIRMED":
            next_due = payment.get("nextDueDate") or sub_data.get("nextDueDate") or payment.get("dueDate")
            _set_subscription_active(subscription, plan_key, next_due, cycle)
            user.plan = plan_key
        elif event == "PAYMENT_OVERDUE":
            subscription.failed_attempts = (subscription.failed_attempts or 0) + 1
            if subscription.failed_attempts >= 3:
                _set_subscription_cancelled(subscription)
                user.plan = "free"
        else:
            subscription.status = "pending"

        db.add_all([user, subscription])
        db.commit()
        return {"received": True}

    if event in {"SUBSCRIPTION_DELETED", "SUBSCRIPTION_CANCELLED"}:
        sub_payload = payload.get("subscription") or {}
        sub_id = sub_payload.get("id")
        if not sub_id:
            return {"received": True}
        subscription = db.query(Subscription).filter(Subscription.asaas_subscription_id == sub_id).first()
        if subscription:
            user = db.query(User).get(subscription.user_id)
            _set_subscription_cancelled(subscription)
            if user:
                user.plan = "free"
                db.add(user)
            db.add(subscription)
            db.commit()
        return {"received": True}

    return {"received": True}


@router.get("/me", response_model=BillingInfo)
def get_billing_info(current_user: User = Depends(get_current_active_user)) -> BillingInfo:
    return _build_billing_info(current_user)


@router.post("/cancel", response_model=BillingInfo)
def cancel_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> BillingInfo:
    sub = current_user.subscription
    if not sub:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

    client = _get_asaas_client()
    try:
        if sub.asaas_subscription_id:
            client.cancel_subscription(sub.asaas_subscription_id)
        elif sub.asaas_payment_link_id:
            client.delete_payment_link(sub.asaas_payment_link_id)
    except AsaasAPIError as exc:  # noqa: BLE001
        logger.exception("Erro ao cancelar assinatura Asaas: %s", exc)
        raise HTTPException(status_code=502, detail="Erro ao cancelar assinatura") from exc

    _set_subscription_cancelled(sub)
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

        _set_subscription_cancelled(sub)
        db.add(sub)

    current_user.plan = "free"
    db.add(current_user)
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

    db.refresh(subscription)
    db.refresh(current_user)
    return _build_billing_info(current_user)
