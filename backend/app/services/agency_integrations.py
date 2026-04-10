from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.agency_payment_settings import AgencyPaymentSettings
from app.models.agency_user import AgencyUser
from app.models.user import User


def _default_agency_membership(user: User, db: Session) -> AgencyUser | None:
    return (
        db.query(AgencyUser)
        .filter(AgencyUser.user_id == user.id)
        .order_by(AgencyUser.role.asc())
        .first()
    )


def get_user_default_agency_id(user: User, db: Session) -> int:
    membership = _default_agency_membership(user, db)
    if not membership:
        raise HTTPException(status_code=400, detail="Usuario nao esta vinculado a nenhuma agencia.")
    return membership.agency_id


def get_agency_payment_settings(db: Session, agency_id: int) -> AgencyPaymentSettings | None:
    return (
        db.query(AgencyPaymentSettings)
        .filter(AgencyPaymentSettings.agency_id == agency_id)
        .first()
    )


def get_agency_blimboo_token(db: Session, agency_id: int | None) -> str | None:
    if not agency_id:
        return None
    record = get_agency_payment_settings(db, agency_id)
    return record.blimboo_api_token if record else None


def save_agency_blimboo_token(db: Session, agency_id: int, token: str | None) -> AgencyPaymentSettings:
    normalized = token.strip() if token else ""
    record = get_agency_payment_settings(db, agency_id)
    if record is None:
        record = AgencyPaymentSettings(agency_id=agency_id)
    record.blimboo_api_token = normalized or None
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
