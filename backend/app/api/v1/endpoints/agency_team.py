from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency_user import AgencyUser
from app.models.team_invite import TeamInvite
from app.models.user import User
from app.schemas.team import TeamInviteCreate, TeamInviteOut, TeamMemberOut, TeamSummaryOut, TeamUserPermissionsUpdate
from app.services.email import send_team_invite_email
from app.services.permissions import allowed_permission_keys_for_plan, normalize_plan, plan_extra_user_limit
from app.services.team import (
    create_invite_token,
    enforce_extra_user_limit,
    get_agency_plan,
    get_user_effective_permissions,
    get_user_primary_agency,
    hash_invite_token,
    is_owner_user,
    validate_member_permissions_for_plan,
)

router = APIRouter(prefix="/agency/team")
ALLOWED_TEAM_ROLES = {"admin", "editor", "viewer", "custom", "member"}


def _require_owner(user: User) -> None:
    if not is_owner_user(user) or (user.role and user.role not in {"admin", "owner"}):
        raise HTTPException(status_code=403, detail="Apenas o admin principal pode gerenciar equipe.")


def _member_from_user(db: Session, user: User, agency_id: int) -> TeamMemberOut:
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user.id)
        .first()
    )
    return TeamMemberOut(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        role=(user.role or (membership.role if membership else "member")),
        role_name=None,
        status=(user.status or "active"),
        is_owner=is_owner_user(user),
        permissions=get_user_effective_permissions(db, user, agency_id),
    )


@router.get("", response_model=TeamSummaryOut)
def get_team_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TeamSummaryOut:
    agency = get_user_primary_agency(db, current_user)
    _require_owner(current_user)
    plan = normalize_plan(get_agency_plan(db, agency.id))
    members_raw = (
        db.query(User)
        .join(AgencyUser, AgencyUser.user_id == User.id)
        .filter(AgencyUser.agency_id == agency.id, User.status != "disabled")
        .all()
    )
    members = [_member_from_user(db, member, agency.id) for member in members_raw]
    pending = (
        db.query(TeamInvite)
        .filter(TeamInvite.agency_id == agency.id, TeamInvite.status == "pending")
        .order_by(TeamInvite.created_at.desc())
        .all()
    )
    invites = [
        TeamInviteOut(
            id=invite.id,
            name=invite.name,
            email=invite.email,
            role_name=invite.role_name,
            permissions=list(invite.permissions or []),
            status=invite.status,
            expires_at=invite.expires_at,
            created_at=invite.created_at,
        )
        for invite in pending
    ]
    extra_used = sum(1 for member in members if not member.is_owner and member.status == "active")
    return TeamSummaryOut(
        plan_key=plan,
        extra_users_limit=plan_extra_user_limit(plan),
        extra_users_used=extra_used,
        members=members,
        pending_invites=invites,
        plan_allowed_permissions=sorted(allowed_permission_keys_for_plan(plan)),
    )


@router.post("/invites", response_model=TeamInviteOut, status_code=201)
def create_team_invite(
    payload: TeamInviteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TeamInviteOut:
    agency = get_user_primary_agency(db, current_user)
    _require_owner(current_user)
    plan = get_agency_plan(db, agency.id)
    enforce_extra_user_limit(db, agency.id, plan)
    selected_role = (payload.role or "custom").strip().lower()
    if selected_role not in ALLOWED_TEAM_ROLES:
        raise HTTPException(status_code=400, detail="Role invÃ¡lida.")
    if selected_role == "member":
        selected_role = "custom"
    selected_permissions = [] if selected_role == "admin" else validate_member_permissions_for_plan(payload.permissions, plan)
    normalized_email = payload.email.strip().lower()

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        existing_membership = (
            db.query(AgencyUser)
            .filter(AgencyUser.agency_id == agency.id, AgencyUser.user_id == existing_user.id)
            .first()
        )
        if existing_membership:
            raise HTTPException(status_code=400, detail="UsuÃ¡rio jÃ¡ faz parte desta agÃªncia.")

    token_raw, token_hash = create_invite_token()
    invite = TeamInvite(
        agency_id=agency.id,
        email=normalized_email,
        name=payload.name.strip(),
        role_name=selected_role,
        permissions=selected_permissions,
        token_hash=token_hash,
        status="pending",
        expires_at=datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=7),
        invited_by_user_id=current_user.id,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    from app.core.config import get_settings

    settings = get_settings()
    invite_url = f"{settings.resolved_webapp_base_url}/accept-invite?token={token_raw}"
    send_team_invite_email(
        to_email=invite.email,
        invitee_name=invite.name,
        inviter_name=current_user.name,
        agency_name=agency.name,
        invite_url=invite_url,
    )
    return TeamInviteOut(
        id=invite.id,
        name=invite.name,
        email=invite.email,
        role_name=invite.role_name,
        permissions=list(invite.permissions or []),
        status=invite.status,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
    )


@router.post("/invites/{invite_id}/resend", response_model=TeamInviteOut)
def resend_team_invite(
    invite_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TeamInviteOut:
    agency = get_user_primary_agency(db, current_user)
    _require_owner(current_user)
    invite = db.query(TeamInvite).filter(TeamInvite.id == invite_id, TeamInvite.agency_id == agency.id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Convite nÃ£o encontrado.")
    if invite.status != "pending":
        raise HTTPException(status_code=400, detail="Somente convites pendentes podem ser reenviados.")

    token_raw, token_hash = create_invite_token()
    invite.token_hash = token_hash
    invite.expires_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=7)
    db.add(invite)
    db.commit()
    db.refresh(invite)

    from app.core.config import get_settings

    settings = get_settings()
    invite_url = f"{settings.resolved_webapp_base_url}/accept-invite?token={token_raw}"
    send_team_invite_email(
        to_email=invite.email,
        invitee_name=invite.name,
        inviter_name=current_user.name,
        agency_name=agency.name,
        invite_url=invite_url,
    )
    return TeamInviteOut(
        id=invite.id,
        name=invite.name,
        email=invite.email,
        role_name=invite.role_name,
        permissions=list(invite.permissions or []),
        status=invite.status,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
    )


@router.post("/invites/{invite_id}/cancel")
def cancel_team_invite(
    invite_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    agency = get_user_primary_agency(db, current_user)
    _require_owner(current_user)
    invite = db.query(TeamInvite).filter(TeamInvite.id == invite_id, TeamInvite.agency_id == agency.id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Convite nÃ£o encontrado.")
    invite.status = "cancelled"
    db.add(invite)
    db.commit()
    return {"detail": "Convite cancelado."}


@router.patch("/users/{user_id}/permissions", response_model=TeamMemberOut)
def update_member_permissions(
    user_id: int,
    payload: TeamUserPermissionsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TeamMemberOut:
    agency = get_user_primary_agency(db, current_user)
    _require_owner(current_user)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="UsuÃ¡rio nÃ£o encontrado.")
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == agency.id, AgencyUser.user_id == target.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="UsuÃ¡rio nÃ£o pertence Ã  agÃªncia.")
    if is_owner_user(target):
        raise HTTPException(status_code=400, detail="NÃ£o Ã© possÃ­vel alterar permissÃµes do admin principal.")

    plan = get_agency_plan(db, agency.id)
    target_role = (payload.role or "custom").strip().lower()
    if target_role not in ALLOWED_TEAM_ROLES:
        raise HTTPException(status_code=400, detail="Role invÃ¡lida.")
    if target_role == "member":
        target_role = "custom"
    target.role = target_role
    membership.role = target_role
    target.permissions = [] if target_role == "admin" else validate_member_permissions_for_plan(payload.permissions, plan)
    db.add(membership)
    db.add(target)
    db.commit()
    db.refresh(target)
    return _member_from_user(db, target, agency.id)


@router.patch("/users/{user_id}/disable")
def disable_member(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    agency = get_user_primary_agency(db, current_user)
    _require_owner(current_user)
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="VocÃª nÃ£o pode desativar seu prÃ³prio usuÃ¡rio.")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="UsuÃ¡rio nÃ£o encontrado.")
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == agency.id, AgencyUser.user_id == target.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="UsuÃ¡rio nÃ£o pertence Ã  agÃªncia.")
    if is_owner_user(target):
        raise HTTPException(status_code=400, detail="NÃ£o Ã© possÃ­vel desativar o admin principal.")
    target.status = "disabled"
    target.is_active = False
    db.add(target)
    db.commit()
    return {"detail": "UsuÃ¡rio desativado."}


def find_pending_invite_by_token(db: Session, token: str) -> TeamInvite | None:
    token_hash = hash_invite_token(token)
    return db.query(TeamInvite).filter(TeamInvite.token_hash == token_hash).first()

