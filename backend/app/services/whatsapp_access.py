from __future__ import annotations

from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.whatsapp import WhatsAppInboxPermission
from app.services.permissions import normalize_plan
from app.services.team import get_agency_plan


def _resolved_agency_id(user: User, agency_id: int | None) -> int | None:
    resolved = agency_id or getattr(user, "primary_agency_id", None)
    return int(resolved) if resolved else None


def has_whatsapp_connection_access(db: Session, *, user: User, agency_id: int | None) -> bool:
    if bool(getattr(user, "is_superuser", False)):
        return True

    resolved_agency_id = _resolved_agency_id(user, agency_id)
    if not resolved_agency_id:
        return False

    plan = normalize_plan(get_agency_plan(db, resolved_agency_id))
    return plan in {"scale", "test"}


def has_whatsapp_inbox_access(db: Session, *, user: User, agency_id: int | None) -> bool:
    if not has_whatsapp_connection_access(db, user=user, agency_id=agency_id):
        return False

    resolved_agency_id = _resolved_agency_id(user, agency_id)
    filters = [WhatsAppInboxPermission.user_id == user.id]
    if resolved_agency_id:
        filters.append(WhatsAppInboxPermission.agency_id == resolved_agency_id)

    # Regra de prioridade:
    # 1) Qualquer permissao explicita inativa/revogada bloqueia.
    # 2) Senao, permissao explicita ativa libera.
    # 3) Sem permissao explicita, o acesso ao inbox permanece bloqueado.
    explicit_permissions = (
        db.query(WhatsAppInboxPermission)
        .filter(or_(*filters))
        .order_by(
            case((WhatsAppInboxPermission.user_id == user.id, 0), else_=1),
            WhatsAppInboxPermission.updated_at.desc().nullslast(),
            WhatsAppInboxPermission.id.desc(),
        )
        .all()
    )
    if explicit_permissions:
        for permission in explicit_permissions:
            if (not bool(permission.enabled)) or permission.revoked_at is not None:
                return False
        return True

    return False
