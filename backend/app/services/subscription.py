import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.db.session import SessionLocal
from app.models.subscription import Subscription

logger = logging.getLogger(__name__)


def expire_subscriptions(now: Optional[datetime] = None) -> int:
    """
    Marca assinaturas vencidas como free/past_due e sincroniza user.plan.
    Retorna quantidade processada.
    """
    now = now or datetime.utcnow()
    db = SessionLocal()
    processed = 0
    try:
        expired = (
            db.query(Subscription)
            .filter(
                Subscription.valid_until.isnot(None),
                Subscription.valid_until < now,
                Subscription.status.in_(("active", "cancelled")),
            )
            .all()
        )
        for sub in expired:
            sub.status = "past_due"
            sub.plan = "free"
            sub.valid_until = None
            sub.failed_attempts = 3
            if sub.user:
                sub.user.plan = "free"
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
    Inicia uma tarefa assíncrona que roda a cada interval_minutes.
    """
    async def _loop() -> None:
        while True:
            try:
                expire_subscriptions()
            except Exception:
                logger.exception("Erro no job de expiração de assinaturas")
            await asyncio.sleep(interval_minutes * 60)

    try:
        asyncio.get_event_loop().create_task(_loop())
    except RuntimeError:
        # fallback para caso não haja loop configurado
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(_loop())
