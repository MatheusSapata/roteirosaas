from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.subscription import Subscription
from app.models.team_invite import TeamInvite
from app.models.user import User
from app.services.permissions import final_permissions_for_member, plan_extra_user_limit, sanitize_requested_permissions
from app.services.plans import effective_plan


def _slugify(value: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in base:
        base = base.replace("--", "-")
    return base or "agencia"


def _ensure_subscription(db: Session, user: User) -> None:
    if user.subscription_id:
        return
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not sub:
        sub = Subscription(user_id=user.id, plan=user.plan or "free")
        db.add(sub)
        db.flush()
    user.subscription_id = sub.id


def ensure_legacy_owner_context(db: Session, user: User) -> Agency:
    membership = db.query(AgencyUser).filter(AgencyUser.user_id == user.id).order_by(AgencyUser.id.asc()).first()
    if membership:
        agency = db.query(Agency).filter(Agency.id == membership.agency_id).first()
        if not agency:
            raise HTTPException(status_code=500, detail="Dados de agência inconsistentes.")
    else:
        base_slug = _slugify(user.name or user.email.split("@")[0])
        slug = base_slug
        idx = 1
        while db.query(Agency).filter(Agency.slug == slug).first():
            idx += 1
            slug = f"{base_slug}-{idx}"
        agency = Agency(name=(user.name or "Minha Agência").strip(), slug=slug)
        db.add(agency)
        db.flush()
        membership = AgencyUser(agency_id=agency.id, user_id=user.id, role="owner")
        db.add(membership)

    if user.is_owner is None:
        user.is_owner = True
    if not user.role:
        user.role = "admin"
    if not user.status:
        user.status = "active"
    if not user.primary_agency_id:
        user.primary_agency_id = membership.agency_id
    if user.permissions is None and bool(user.is_owner):
        user.permissions = []
    _ensure_subscription(db, user)
    db.add(user)
    db.commit()
    db.refresh(user)
    return agency


def get_user_primary_agency(db: Session, user: User) -> Agency:
    ensure_legacy_owner_context(db, user)
    agency_id = user.primary_agency_id
    if not agency_id:
        raise HTTPException(status_code=500, detail="Usuário sem agência principal.")
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agência não encontrada.")
    return agency


def get_agency_plan(db: Session, agency_id: int) -> str:
    owner_membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == agency_id, AgencyUser.role == "owner")
        .order_by(AgencyUser.id.asc())
        .first()
    )
    user = None
    if owner_membership:
        user = db.query(User).filter(User.id == owner_membership.user_id).first()
    if not user:
        fallback = db.query(AgencyUser).filter(AgencyUser.agency_id == agency_id).order_by(AgencyUser.id.asc()).first()
        if fallback:
            user = db.query(User).filter(User.id == fallback.user_id).first()
    return effective_plan(user) if user else "free"


def is_owner_user(user: User) -> bool:
    return user.is_owner is None or bool(user.is_owner)


def get_user_effective_permissions(db: Session, user: User, agency_id: int | None = None) -> list[str]:
    owner = is_owner_user(user)
    plan = get_agency_plan(db, agency_id or user.primary_agency_id or 0)
    selected = user.permissions if isinstance(user.permissions, list) else []
    return final_permissions_for_member(user_is_owner=owner, user_role=user.role, selected_permissions=selected, plan=plan)


def enforce_extra_user_limit(db: Session, agency_id: int, plan: str) -> None:
    limit = plan_extra_user_limit(plan)
    if limit is None:
        return
    extra_count = (
        db.query(User)
        .join(AgencyUser, AgencyUser.user_id == User.id)
        .filter(AgencyUser.agency_id == agency_id, User.is_owner.is_(False), User.status == "active")
        .count()
    )
    pending_count = (
        db.query(TeamInvite)
        .filter(TeamInvite.agency_id == agency_id, TeamInvite.status == "pending", TeamInvite.expires_at > datetime.now(timezone.utc))
        .count()
    )
    if extra_count + pending_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Seu plano permite até {limit} usuários extras. Faça upgrade para adicionar mais membros.",
        )


def create_invite_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return token, token_hash


def hash_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def find_pending_invite_by_token(db: Session, token: str) -> TeamInvite | None:
    token_hash = hash_invite_token(token)
    return db.query(TeamInvite).filter(TeamInvite.token_hash == token_hash).first()


def validate_member_permissions_for_plan(selected_permissions: list[str], plan: str) -> list[str]:
    return sanitize_requested_permissions(selected_permissions, plan)


def invite_expiration(days: int = 7) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)

