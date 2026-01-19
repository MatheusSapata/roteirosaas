import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

PLAN_PRICING = {
    "free": {"title": "Plano Gratuito", "price": 0.0},
    "essencial": {"title": "Plano Essencial", "price": 39.90},
    "growth": {"title": "Plano Growth", "price": 49.90},
    "infinity": {"title": "Plano Infinity", "price": 89.90},
}

PRICE_MAP = {
    "essencial": settings.stripe_price_essencial,
    "growth": settings.stripe_price_growth,
    "infinity": settings.stripe_price_infinity,
}

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


class CheckoutRequest(BaseModel):
    plan: str


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


class PlanChangeRequest(BaseModel):
    plan: str


def _get_price(plan_key: str) -> str:
    price_id = PRICE_MAP.get(plan_key)
    if not price_id:
        raise HTTPException(status_code=400, detail="Plano sem price configurado no Stripe")
    return price_id


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=500, detail="Stripe secret key não configurada")

    # garante que a chave esteja setada mesmo em reload
    stripe.api_key = settings.stripe_secret_key

    plan_key = payload.plan
    if plan_key not in ("essencial", "growth", "infinity"):
        raise HTTPException(status_code=400, detail="Plano inválido")

    price_id = _get_price(plan_key)

    success_url = settings.stripe_success_url or settings.mp_success_url or "https://example.com/success"
    cancel_url = settings.stripe_cancel_url or settings.mp_failure_url or "https://example.com/cancel"

    try:
        logger.info("Stripe checkout using key prefix=%s...", settings.stripe_secret_key[:10] if settings.stripe_secret_key else "none")
        customer = None
        if current_user.email:
            existing = stripe.Customer.list(email=current_user.email, limit=1).data
            customer = existing[0] if existing else None
        if not customer:
            customer = stripe.Customer.create(email=current_user.email, name=current_user.name)

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer.id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={"metadata": {"user_id": current_user.id, "plan": plan_key}},
            metadata={"plan": plan_key, "user_id": current_user.id},
        )

        subscription = current_user.subscription
        if not subscription:
            subscription = Subscription(user_id=current_user.id, plan=plan_key, provider="stripe")
            db.add(subscription)
            db.flush()
            current_user.subscription_id = subscription.id

        subscription.plan = plan_key
        subscription.provider = "stripe"
        subscription.stripe_customer_id = customer.id
        subscription.failed_attempts = 0
        db.add_all([subscription, current_user])
        db.commit()
        db.refresh(current_user)

        return CheckoutResponse(init_point=session.url, preapproval_id=session.subscription)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao criar checkout do Stripe")
        raise HTTPException(status_code=502, detail="Erro ao criar checkout no Stripe") from exc


def _update_subscription_from_stripe(db: Session, user: User, sub_data: Dict[str, Any], plan_key: Optional[str] = None) -> Subscription:
    subscription = user.subscription
    if not subscription:
        subscription = Subscription(user_id=user.id)
        db.add(subscription)
        db.flush()
        user.subscription_id = subscription.id

    if plan_key:
        subscription.plan = plan_key
    elif sub_data.get("items", {}).get("data"):
        price_id = sub_data["items"]["data"][0]["price"]["id"]
        # map back price -> plan
        for key, val in PRICE_MAP.items():
            if val == price_id:
                subscription.plan = key
                break

    period_end = sub_data.get("current_period_end")
    if period_end:
        subscription.valid_until = datetime.utcfromtimestamp(period_end)
    elif not subscription.valid_until:
        # fallback: 30 dias a partir de agora se Stripe não enviar period_end
        subscription.valid_until = datetime.utcnow() + timedelta(days=30)
    subscription.status = sub_data.get("status") or "active"
    subscription.provider = "stripe"
    subscription.stripe_subscription_id = sub_data.get("id")
    subscription.stripe_price_id = (
        sub_data["items"]["data"][0]["price"]["id"] if sub_data.get("items", {}).get("data") else None
    )
    subscription.failed_attempts = 0 if subscription.status == "active" else subscription.failed_attempts
    return subscription


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not settings.stripe_webhook_secret:
        logger.error("Stripe webhook secret não configurado")
        raise HTTPException(status_code=500, detail="Stripe webhook secret não configurado")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception as exc:  # noqa: BLE001
        logger.error("Falha ao validar webhook Stripe: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    event_type = event["type"]
    data_obj = event["data"]["object"]

    try:
        if event_type == "checkout.session.completed":
            # Retrieve subscription info
            sub_id = data_obj.get("subscription")
            user_id = data_obj.get("metadata", {}).get("user_id")
            plan_key = data_obj.get("metadata", {}).get("plan")
            if not sub_id or not user_id:
                return {"received": True}
            user = db.query(User).get(int(user_id))
            if not user:
                return {"received": True}
            stripe_sub = stripe.Subscription.retrieve(sub_id, expand=["items"])
            subscription = _update_subscription_from_stripe(db, user, stripe_sub, plan_key=plan_key)
            user.plan = subscription.plan
            db.add_all([user, subscription])
            db.commit()
            return {"received": True}

        if event_type == "invoice.payment_succeeded":
            sub_id = data_obj.get("subscription")
            if not sub_id:
                return {"received": True}
            stripe_sub = stripe.Subscription.retrieve(sub_id, expand=["items"])
            user_id = stripe_sub.get("metadata", {}).get("user_id")
            if not user_id and data_obj.get("customer"):
                user = db.query(User).filter(Subscription.stripe_customer_id == data_obj["customer"]).first()
            else:
                user = db.query(User).get(int(user_id)) if user_id else None
            if not user:
                return {"received": True}
            subscription = _update_subscription_from_stripe(db, user, stripe_sub)
            subscription.failed_attempts = 0
            user.plan = subscription.plan
            db.add_all([user, subscription])
            db.commit()
            return {"received": True}

        if event_type == "invoice.payment_failed":
            sub_id = data_obj.get("subscription")
            customer_id = data_obj.get("customer")
            user = None
            if sub_id:
                user = db.query(User).filter(Subscription.stripe_subscription_id == sub_id).first()
            if not user and customer_id:
                user = db.query(User).filter(Subscription.stripe_customer_id == customer_id).first()
            if not user:
                return {"received": True}
            subscription = user.subscription
            if subscription:
                subscription.failed_attempts = (subscription.failed_attempts or 0) + 1
                if subscription.failed_attempts >= 3:
                    subscription.plan = "free"
                    subscription.status = "past_due"
                    subscription.valid_until = None
                    user.plan = "free"
                db.add_all([user, subscription])
                db.commit()
            return {"received": True}

    except Exception:  # noqa: BLE001
        logger.exception("Erro processando webhook Stripe")
        raise HTTPException(status_code=500, detail="Erro interno")

    return {"received": True}


@router.get("/me", response_model=BillingInfo)
def get_billing_info(current_user: User = Depends(get_current_active_user)) -> BillingInfo:
    sub = current_user.subscription
    return BillingInfo(
        plan=sub.plan if sub else current_user.plan,
        status=sub.status if sub else "inactive",
        valid_until=sub.valid_until if sub else None,
        failed_attempts=sub.failed_attempts if sub else 0,
        preapproval_id=sub.stripe_subscription_id if sub else None,
        provider=sub.provider if sub else None,
    )


@router.post("/cancel", response_model=BillingInfo)
def cancel_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> BillingInfo:
    sub = current_user.subscription
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

    try:
        stripe.Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao cancelar assinatura Stripe")
        raise HTTPException(status_code=502, detail="Erro ao cancelar assinatura") from exc

    sub.status = "cancelled"
    db.add(sub)
    db.commit()
    db.refresh(sub)

    return BillingInfo(
        plan=sub.plan,
        status=sub.status,
        valid_until=sub.valid_until,
        failed_attempts=sub.failed_attempts,
        preapproval_id=sub.stripe_subscription_id,
        provider=sub.provider,
    )


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
    if sub and sub.stripe_subscription_id:
        try:
            stripe.Subscription.delete(sub.stripe_subscription_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Erro ao encerrar assinatura Stripe ao mudar para free")
            raise HTTPException(status_code=502, detail="Erro ao cancelar assinatura no Stripe") from exc

    if sub:
        sub.plan = "free"
        sub.status = "cancelled"
        sub.valid_until = None
        sub.stripe_subscription_id = None
        sub.stripe_price_id = None
        sub.provider = "stripe"
        sub.preapproval_id = None
        db.add(sub)

    current_user.plan = "free"
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    status = sub.status if sub else "inactive"
    failed_attempts = sub.failed_attempts if sub else 0
    provider = sub.provider if sub else None
    return BillingInfo(
        plan="free",
        status=status,
        valid_until=None,
        failed_attempts=failed_attempts,
        preapproval_id=None,
        provider=provider,
    )
