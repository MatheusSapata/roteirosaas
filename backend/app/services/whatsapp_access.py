from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.whatsapp import WhatsAppInboxPermission


def has_whatsapp_inbox_access(db: Session, *, user: User, agency_id: int | None) -> bool:
    query = db.query(WhatsAppInboxPermission).filter(
        WhatsAppInboxPermission.enabled.is_(True),
        WhatsAppInboxPermission.revoked_at.is_(None),
    )

    filters = [WhatsAppInboxPermission.user_id == user.id]
    if agency_id:
        filters.append(WhatsAppInboxPermission.agency_id == agency_id)

    permission = query.filter(or_(*filters)).first()
    return permission is not None
