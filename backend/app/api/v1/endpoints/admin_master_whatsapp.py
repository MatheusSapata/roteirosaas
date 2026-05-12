from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, aliased

from app.api.deps import get_current_superuser, get_db
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.user import User
from app.models.whatsapp import WhatsAppConnection, WhatsAppInboxPermission
from app.schemas.whatsapp import (
    AdminMasterWhatsAppConnectionOut,
    AdminMasterWhatsAppInboxPermissionOut,
    AdminMasterWhatsAppInboxPermissionUpsertIn,
    AdminMasterWhatsAppOverviewOut,
)

router = APIRouter()


def _permission_to_out(
    row: WhatsAppInboxPermission,
    user: User | None,
    agency: Agency | None,
    granted_by: User | None,
) -> AdminMasterWhatsAppInboxPermissionOut:
    return AdminMasterWhatsAppInboxPermissionOut(
        id=row.id,
        user_id=row.user_id,
        user_name=user.name if user else None,
        user_email=user.email if user else None,
        agency_id=row.agency_id,
        agency_name=agency.name if agency else None,
        enabled=bool(row.enabled),
        granted_at=row.granted_at,
        revoked_at=row.revoked_at,
        granted_by_user_id=row.granted_by_user_id,
        granted_by_name=granted_by.name if granted_by else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/overview", response_model=AdminMasterWhatsAppOverviewOut)
def get_whatsapp_overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminMasterWhatsAppOverviewOut:
    status_norm = func.lower(func.coalesce(WhatsAppConnection.status, "disconnected"))

    totals = (
        db.query(
            func.count(WhatsAppConnection.id).label("total"),
            func.sum(case((status_norm == "connected", 1), else_=0)).label("connected"),
            func.sum(case((status_norm == "disconnected", 1), else_=0)).label("disconnected"),
            func.sum(case((status_norm.in_(["connecting", "open", "qrcode", "pairing"]), 1), else_=0)).label("connecting"),
            func.count(func.distinct(case((status_norm == "connected", WhatsAppConnection.agency_id), else_=None))).label("agencies_connected"),
        )
        .one()
    )

    inbox_enabled_users = (
        db.query(func.count(func.distinct(WhatsAppInboxPermission.user_id)))
        .filter(
            WhatsAppInboxPermission.enabled.is_(True),
            WhatsAppInboxPermission.revoked_at.is_(None),
            WhatsAppInboxPermission.user_id.isnot(None),
        )
        .scalar()
        or 0
    )
    inbox_enabled_agencies = (
        db.query(func.count(func.distinct(WhatsAppInboxPermission.agency_id)))
        .filter(
            WhatsAppInboxPermission.enabled.is_(True),
            WhatsAppInboxPermission.revoked_at.is_(None),
            WhatsAppInboxPermission.agency_id.isnot(None),
        )
        .scalar()
        or 0
    )

    return AdminMasterWhatsAppOverviewOut(
        total_connections=int(totals.total or 0),
        connected_connections=int(totals.connected or 0),
        disconnected_connections=int(totals.disconnected or 0),
        connecting_connections=int(totals.connecting or 0),
        agencies_with_whatsapp=int(totals.agencies_connected or 0),
        inbox_enabled_users=int(inbox_enabled_users),
        inbox_enabled_agencies=int(inbox_enabled_agencies),
    )


@router.get("/users-search")
def search_users_for_inbox_permission(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[dict[str, object]]:
    sanitized = (q or "").strip()
    needle = f"%{sanitized}%"
    digits = "".join(ch for ch in sanitized if ch.isdigit())
    digits_needle = f"%{digits}%" if digits else None
    membership = aliased(AgencyUser)
    linked_agency = aliased(Agency)
    filters = [
        User.name.ilike(needle),
        User.email.ilike(needle),
        func.coalesce(linked_agency.name, "").ilike(needle),
    ]
    if digits_needle:
        filters.extend(
            [
                func.coalesce(User.whatsapp, "").ilike(digits_needle),
                func.coalesce(User.cpf, "").ilike(digits_needle),
                func.coalesce(User.cnpj, "").ilike(digits_needle),
            ]
        )
    rows = (
        db.query(User, linked_agency)
        .outerjoin(membership, membership.user_id == User.id)
        .outerjoin(linked_agency, linked_agency.id == membership.agency_id)
        .filter(
            User.is_active.is_(True),
            or_(*filters),
        )
        .order_by(User.name.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "whatsapp": user.whatsapp,
            "cpf": user.cpf,
            "cnpj": user.cnpj,
            "agency_id": agency.id if agency else None,
            "agency_name": agency.name if agency else None,
        }
        for user, agency in rows
    ]


@router.get("/connections", response_model=list[AdminMasterWhatsAppConnectionOut])
def list_whatsapp_connections(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[AdminMasterWhatsAppConnectionOut]:
    owner_membership = aliased(AgencyUser)
    owner_user = aliased(User)

    query = (
        db.query(WhatsAppConnection, Agency, owner_user)
        .join(Agency, Agency.id == WhatsAppConnection.agency_id)
        .outerjoin(
            owner_membership,
            (owner_membership.agency_id == Agency.id) & (func.lower(owner_membership.role) == "owner"),
        )
        .outerjoin(owner_user, owner_user.id == owner_membership.user_id)
    )

    if q:
        needle = f"%{q.strip()}%"
        query = query.filter(
            Agency.name.ilike(needle)
            | WhatsAppConnection.name.ilike(needle)
            | WhatsAppConnection.instance_name.ilike(needle)
            | func.coalesce(WhatsAppConnection.phone_number, "").ilike(needle)
            | func.coalesce(owner_user.name, "").ilike(needle)
            | func.coalesce(owner_user.email, "").ilike(needle)
        )

    rows = query.order_by(WhatsAppConnection.updated_at.desc().nullslast(), WhatsAppConnection.id.desc()).all()

    return [
        AdminMasterWhatsAppConnectionOut(
            id=conn.id,
            agency_id=agency.id,
            agency_name=agency.name,
            owner_user_id=owner.id if owner else None,
            owner_name=owner.name if owner else None,
            owner_email=owner.email if owner else None,
            name=conn.name,
            phone_number=conn.phone_number,
            status=conn.status,
            instance_name=conn.instance_name,
            created_at=conn.created_at,
            connected_at=conn.connected_at,
            updated_at=conn.updated_at,
        )
        for conn, agency, owner in rows
    ]


@router.get("/inbox-permissions", response_model=list[AdminMasterWhatsAppInboxPermissionOut])
def list_inbox_permissions(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[AdminMasterWhatsAppInboxPermissionOut]:
    target_user = aliased(User)
    granted_by = aliased(User)

    query = (
        db.query(WhatsAppInboxPermission, target_user, Agency, granted_by)
        .outerjoin(target_user, target_user.id == WhatsAppInboxPermission.user_id)
        .outerjoin(Agency, Agency.id == WhatsAppInboxPermission.agency_id)
        .outerjoin(granted_by, granted_by.id == WhatsAppInboxPermission.granted_by_user_id)
    )

    if q:
        needle = f"%{q.strip()}%"
        query = query.filter(
            func.coalesce(target_user.name, "").ilike(needle)
            | func.coalesce(target_user.email, "").ilike(needle)
            | func.coalesce(Agency.name, "").ilike(needle)
        )

    rows = query.order_by(WhatsAppInboxPermission.updated_at.desc().nullslast(), WhatsAppInboxPermission.id.desc()).all()
    return [_permission_to_out(permission, user, agency, granted) for permission, user, agency, granted in rows]


@router.post("/inbox-permissions", response_model=AdminMasterWhatsAppInboxPermissionOut, status_code=status.HTTP_201_CREATED)
def upsert_inbox_permission(
    payload: AdminMasterWhatsAppInboxPermissionUpsertIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> AdminMasterWhatsAppInboxPermissionOut:
    if not payload.user_id and not payload.agency_id:
        raise HTTPException(status_code=400, detail="Informe userId ou agencyId.")

    if payload.user_id:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if payload.agency_id:
        agency = db.query(Agency).filter(Agency.id == payload.agency_id).first()
        if not agency:
            raise HTTPException(status_code=404, detail="Agência não encontrada.")

    row = None
    if payload.user_id:
        row = db.query(WhatsAppInboxPermission).filter(WhatsAppInboxPermission.user_id == payload.user_id).first()
    if not row and payload.agency_id:
        row = db.query(WhatsAppInboxPermission).filter(WhatsAppInboxPermission.agency_id == payload.agency_id).first()

    now = datetime.now(timezone.utc)
    if not row:
        row = WhatsAppInboxPermission(
            user_id=payload.user_id,
            agency_id=payload.agency_id,
            enabled=bool(payload.enabled),
            granted_by_user_id=current_user.id,
            granted_at=now if payload.enabled else None,
            revoked_at=None if payload.enabled else now,
        )
        db.add(row)
    else:
        row.user_id = payload.user_id if payload.user_id else row.user_id
        row.agency_id = payload.agency_id if payload.agency_id else row.agency_id
        row.enabled = bool(payload.enabled)
        row.granted_by_user_id = current_user.id
        if payload.enabled:
            row.granted_at = now
            row.revoked_at = None
        else:
            row.granted_at = None
            row.revoked_at = now

    db.commit()
    db.refresh(row)

    target_user = db.query(User).filter(User.id == row.user_id).first() if row.user_id else None
    target_agency = db.query(Agency).filter(Agency.id == row.agency_id).first() if row.agency_id else None
    granted_by_user = db.query(User).filter(User.id == row.granted_by_user_id).first() if row.granted_by_user_id else None
    return _permission_to_out(row, target_user, target_agency, granted_by_user)


@router.patch("/inbox-permissions/{permission_id}", response_model=AdminMasterWhatsAppInboxPermissionOut)
def update_inbox_permission(
    permission_id: int,
    payload: AdminMasterWhatsAppInboxPermissionUpsertIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> AdminMasterWhatsAppInboxPermissionOut:
    row = db.query(WhatsAppInboxPermission).filter(WhatsAppInboxPermission.id == permission_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Permissão não encontrada.")

    now = datetime.now(timezone.utc)
    row.enabled = bool(payload.enabled)
    row.granted_by_user_id = current_user.id
    if payload.enabled:
        row.granted_at = now
        row.revoked_at = None
    else:
        row.granted_at = None
        row.revoked_at = now

    db.commit()
    db.refresh(row)

    target_user = db.query(User).filter(User.id == row.user_id).first() if row.user_id else None
    target_agency = db.query(Agency).filter(Agency.id == row.agency_id).first() if row.agency_id else None
    granted_by_user = db.query(User).filter(User.id == row.granted_by_user_id).first() if row.granted_by_user_id else None
    return _permission_to_out(row, target_user, target_agency, granted_by_user)


@router.delete("/inbox-permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_inbox_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> None:
    row = db.query(WhatsAppInboxPermission).filter(WhatsAppInboxPermission.id == permission_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Permissão não encontrada.")
    now = datetime.now(timezone.utc)
    row.enabled = False
    row.granted_by_user_id = current_user.id
    row.granted_at = None
    row.revoked_at = now
    db.commit()
