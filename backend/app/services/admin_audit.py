"""Registro do que o Admin Master fez numa conta (aparece na aba Logs da página da empresa)."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.activity_log import AdminActionLog
from app.models.user import User

logger = logging.getLogger(__name__)


def record_admin_action(
    db: Session,
    *,
    actor: User | None,
    target_user_id: int | None,
    action: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Entra na mesma transação da ação: só fica gravado se a ação for salva."""
    try:
        db.add(AdminActionLog(
            target_user_id=target_user_id,
            actor_user_id=actor.id if actor else None,
            actor_name=((actor.name or actor.email) if actor else None),
            action=action,
            summary=summary[:2000],
            details=details or None,
        ))
    except Exception:  # pragma: no cover - o registro não pode impedir a ação
        logger.exception("Não foi possível registrar a ação do admin (%s)", action)


def _plain(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    try:
        return float(value) if not isinstance(value, (str, int, bool)) else value
    except (TypeError, ValueError):
        return str(value)


def subscription_snapshot(user: User) -> dict[str, Any]:
    sub = user.subscription
    return {
        "plan": user.plan,
        "status": _plain(sub.status) if sub else None,
        "valid_until": _plain(sub.valid_until) if sub else None,
        "mrr_amount": _plain(sub.mrr_amount) if sub else None,
        "trial_plan": user.trial_plan,
        "trial_ends_at": _plain(user.trial_ends_at),
    }
