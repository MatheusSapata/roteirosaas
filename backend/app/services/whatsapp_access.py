from __future__ import annotations

from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.whatsapp import WhatsAppInboxPermission


def has_whatsapp_inbox_access(db: Session, *, user: User, agency_id: int | None) -> bool:
    filters = [WhatsAppInboxPermission.user_id == user.id]
    if agency_id:
        filters.append(WhatsAppInboxPermission.agency_id == agency_id)

    # Regra de prioridade:
    # 1) Qualquer permissao explicita inativa/revogada bloqueia.
    # 2) Senao, permissao explicita ativa libera.
    # 3) Sem permissao explicita, apenas superuser libera.
    #    Demais usuarios ficam bloqueados por padrao ate liberacao no admin master.
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

    if bool(getattr(user, "is_superuser", False)):
        return True

    return False
