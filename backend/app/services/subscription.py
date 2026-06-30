import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.subscription import Subscription
from app.models.user import User
from app.services.asaas import AsaasAPIError, AsaasClient, build_default_split_payload
from app.services.viajechat_checkout_flow import tag_abandoned_checkout_sessions

logger = logging.getLogger(__name__)
settings = get_settings()

PLAN_PRICING = {
    "essencial": {"monthly": {"price": 49.90, "asaas_cycle": "MONTHLY"}, "annual": {"price": 479.88, "asaas_cycle": "YEARLY"}},
    "growth": {"monthly": {"price": 89.99, "asaas_cycle": "MONTHLY"}, "annual": {"price": 839.88, "asaas_cycle": "YEARLY"}},
    "infinity": {"monthly": {"price": 129.90, "asaas_cycle": "MONTHLY"}, "annual": {"price": 1199.88, "asaas_cycle": "YEARLY"}},
}


def _parse_scheduled_downgrade(ref: str | None) -> str | None:
    raw = str(ref or "")
    if not raw.startswith("scheduled_downgrade:"):
        return None
    target = raw.split("scheduled_downgrade:", 1)[1].strip().lower()
    return target or None


def _build_external_reference(user_id: int, plan_key: str, cycle: str) -> str:
    return f"{user_id}:{plan_key}:{cycle}"


def _apply_scheduled_downgrades(now: datetime) -> int:
    if not settings.asaas_api_key:
        return 0
    db = SessionLocal()
    updated = 0
    try:
        client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url)
        subs = (
            db.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.valid_until.isnot(None),
                Subscription.external_reference.isnot(None),
            )
            .all()
        )
        for sub in subs:
            target_plan = _parse_scheduled_downgrade(sub.external_reference)
            if not target_plan:
                continue
            if not sub.asaas_subscription_id or sub.provider != "asaas":
                continue
            if not sub.valid_until:
                continue
            # Apply at D-1 (or later if the job was unavailable), before expiration.
            if sub.valid_until > (now + timedelta(days=1)):
                continue

            cycle = (sub.billing_cycle or "monthly").lower()
            plan_info = PLAN_PRICING.get(target_plan, {}).get(cycle)
            if not plan_info:
                continue

            try:
                client.update_subscription(
                    sub.asaas_subscription_id,
                    {
                        "value": plan_info["price"],
                        "cycle": plan_info["asaas_cycle"],
                        "externalReference": _build_external_reference(sub.user_id, target_plan, cycle),
                        "split": build_default_split_payload(),
                    },
                )
                updated += 1
            except AsaasAPIError:
                logger.exception("Erro ao aplicar downgrade agendado para subscription_id=%s", sub.id)

        if updated:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Erro ao aplicar downgrades agendados")
    finally:
        db.close()
    return updated


def _apply_scheduled_cancellations(now: datetime) -> int:
    if not settings.asaas_api_key:
        return 0
    db = SessionLocal()
    processed = 0
    try:
        client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url)
        subs = (
            db.query(Subscription)
            .filter(
                Subscription.provider == "asaas",
                Subscription.status == "cancel_at_period_end",
                Subscription.asaas_subscription_id.isnot(None),
                Subscription.valid_until.isnot(None),
            )
            .all()
        )
        for sub in subs:
            if not sub.valid_until:
                continue
            # Execute at D-1 (or later if delayed) before next charge window.
            if sub.valid_until > (now + timedelta(days=1)):
                continue
            try:
                client.cancel_subscription(sub.asaas_subscription_id)
                sub.status = "cancelled"
                db.add(sub)
                processed += 1
            except AsaasAPIError:
                logger.exception("Erro ao aplicar cancelamento agendado para subscription_id=%s", sub.id)
        if processed:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Erro ao aplicar cancelamentos agendados")
    finally:
        db.close()
    return processed


def expire_subscriptions(now: Optional[datetime] = None) -> int:
    """
    Marca assinaturas vencidas como inativas sem despublicar páginas.
    Retorna quantidade processada.
    """
    now = now or datetime.utcnow()
    db = SessionLocal()
    processed = 0
    try:
        expired = (
            db.query(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .filter(
                Subscription.valid_until.isnot(None),
                Subscription.valid_until < now,
                Subscription.status.in_(("active", "cancelled", "cancel_at_period_end")),
            )
            .all()
        )
        for sub, user in expired:
            sub.status = "inactive"
            sub.valid_until = None
            sub.failed_attempts = 3
            db.add(user)
            processed += 1
        if processed:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Erro ao expirar assinaturas")
    finally:
        db.close()
    return processed


def schedule_expiration_job(interval_minutes: int = 60) -> None:
    """
    Inicia uma tarefa assincrona que roda a cada interval_minutes.
    """

    async def _loop() -> None:
        while True:
            try:
                _apply_scheduled_downgrades(datetime.utcnow())
                _apply_scheduled_cancellations(datetime.utcnow())
                tag_abandoned_checkout_sessions(cutoff_minutes=30)
                expire_subscriptions()
            except Exception:
                logger.exception("Erro no job de expiracao de assinaturas")
            await asyncio.sleep(interval_minutes * 60)

    try:
        asyncio.get_event_loop().create_task(_loop())
    except RuntimeError:
        # fallback para caso nao haja loop configurado
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(_loop())
