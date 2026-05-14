from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.whatsapp import WhatsAppInboxPermission
from app.services.permissions import normalize_plan


ALLOWED_WHATSAPP_PLANS = {"scale", "test"}


def _effective_plan(user: User) -> str:
    trial_plan = getattr(user, "trial_plan", None)
    if trial_plan:
        return normalize_plan(trial_plan)

    subscription = getattr(user, "subscription", None)
    subscription_plan = getattr(subscription, "plan", None) if subscription else None
    if subscription_plan:
        return normalize_plan(subscription_plan)

    return normalize_plan(getattr(user, "plan", None))


def has_whatsapp_inbox_access(db: Session, *, user: User, agency_id: int | None) -> bool:
    if bool(getattr(user, "is_superuser", False)):
        return True

    # Plano elegivel ja concede acesso ao Atendimento WhatsApp.
    # Mantemos a leitura de permissoes explicitas como compatibilidade legada.
    if _effective_plan(user) in ALLOWED_WHATSAPP_PLANS:
        return True

    query = db.query(WhatsAppInboxPermission).filter(
        WhatsAppInboxPermission.enabled.is_(True),
        WhatsAppInboxPermission.revoked_at.is_(None),
    )

    filters = [WhatsAppInboxPermission.user_id == user.id]
    if agency_id:
        filters.append(WhatsAppInboxPermission.agency_id == agency_id)

    permission = query.filter(or_(*filters)).first()
    return permission is not None
