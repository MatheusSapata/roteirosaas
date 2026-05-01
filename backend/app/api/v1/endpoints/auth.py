from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.core.rate_limit import InMemoryRateLimiter
from app.core.request_ip import get_client_ip
from app.models.user import User
from app.models.subscription import Subscription
from app.models.user_session import UserSession
from app.models.user_tracking import UserTracking
from app.schemas.user import (
    PasswordResetByProfile,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordChange,
    Token,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.schemas.team import AcceptInviteIn, InviteInfoOut
from app.models.team_invite import TeamInvite
from app.models.agency_user import AgencyUser
from app.models.agency import Agency
from app.services import auth as auth_service
from app.services.permissions import final_permissions_for_member
from app.services.team import ensure_legacy_owner_context, find_pending_invite_by_token, get_agency_plan, is_owner_user
from app.services.session_monitor import summarize_user_agent
from app.services.trial import start_trial
from app.services.media_storage import media_storage

router = APIRouter()
settings = get_settings()
login_limiter = InMemoryRateLimiter(attempts=5, window_seconds=300, block_minutes=15)


class TrialAckPayload(BaseModel):
    stage: Literal["start", "end", "warn3", "warn1"]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já registrado.")
    existing_cpf = db.query(User).filter(User.cpf == user_in.cpf).first()
    if existing_cpf:
        raise HTTPException(status_code=400, detail="CPF já registrado.")
    if user_in.cnpj:
        existing_cnpj = db.query(User).filter(User.cnpj == user_in.cnpj).first()
        if existing_cnpj:
            raise HTTPException(status_code=400, detail="CNPJ já registrado.")
    try:
        auth_service.validate_password_strength(user_in.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    hashed = auth_service.get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        name=user_in.name,
        cpf=user_in.cpf,
        whatsapp=user_in.whatsapp,
        cnpj=user_in.cnpj,
        address_street=user_in.address_street,
        address_number=user_in.address_number,
        address_complement=user_in.address_complement,
        address_neighborhood=user_in.address_neighborhood,
        address_city=user_in.address_city,
        address_state=user_in.address_state,
        address_zipcode=user_in.address_zipcode,
        hashed_password=hashed,
        plan=user_in.plan or "free",
        is_owner=True,
        role="admin",
        status="active",
        permissions=[],
    )
    db.add(user)
    db.flush()
    sub = Subscription(user_id=user.id, plan=user.plan)
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    if user_in.utm:
        tracking = UserTracking(
            user_id=user.id,
            utm_source=user_in.utm.source,
            utm_medium=user_in.utm.medium,
            utm_campaign=user_in.utm.campaign,
            utm_term=user_in.utm.term,
            utm_content=user_in.utm.content,
            referrer=user_in.utm.referrer,
        )
        db.add(tracking)
    start_trial(user, "trial", duration_days=7)
    db.commit()
    db.refresh(user)
    ensure_legacy_owner_context(db, user)
    return user



@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    client_ip = get_client_ip(request)
    login_key = f"{client_ip}:{form_data.username.lower().strip()}"
    if login_limiter.is_blocked(login_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Tente novamente em alguns minutos.",
        )
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        login_limiter.register_failure(login_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos.")
    login_limiter.clear(login_key)
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    agent_header = (request.headers.get("user-agent") or "").strip()
    device_label, client_name = summarize_user_agent(agent_header)
    issued_at = datetime.now(timezone.utc)
    current_path = (request.headers.get("X-Client-Path") or "").strip()
    session = UserSession(
        user_id=user.id,
        ip_address=client_ip,
        user_agent=agent_header[:500] or None,
        device_label=device_label,
        client_name=client_name,
        created_at=issued_at,
        last_seen_at=issued_at,
        expires_at=issued_at + timedelta(minutes=settings.refresh_token_expire_minutes),
        last_path=current_path[:255] or None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    access_token = auth_service.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
        session_id=session.id,
    )
    refresh_token = auth_service.create_refresh_token(user.email, session.id)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> Token:
    data = auth_service.decode_token(payload.refresh_token)
    if not data or data.get("scope") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")
    email = data.get("sub")
    session_id = data.get("sid")
    if not email or not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
    session = (
        db.query(UserSession)
        .filter(UserSession.id == session_id, UserSession.user_id == user.id)
        .first()
    )
    if not session or session.revoked_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada.")
    now = datetime.now(timezone.utc)
    if session.expires_at and session.expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada.")
    session.last_seen_at = now
    session.expires_at = now + timedelta(minutes=settings.refresh_token_expire_minutes)
    session.ip_address = get_client_ip(request)
    agent_header = (request.headers.get("user-agent") or "").strip()
    if agent_header:
        session.user_agent = agent_header[:500]
        device_label, client_name = summarize_user_agent(agent_header)
        session.device_label = device_label
        session.client_name = client_name
    current_path = (request.headers.get("X-Client-Path") or "").strip()
    if current_path:
        session.last_path = current_path[:255]
    db.add(session)
    db.commit()
    access_token = auth_service.create_access_token(data={"sub": email}, session_id=session.id)
    refresh_token = auth_service.create_refresh_token(email, session.id)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.get("/me", response_model=UserOut)
def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserOut:
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    ensure_legacy_owner_context(db, user)
    plan = get_agency_plan(db, user.primary_agency_id or 0)
    user.effective_permissions = final_permissions_for_member(
        user_is_owner=is_owner_user(user),
        user_role=user.role,
        selected_permissions=user.permissions if isinstance(user.permissions, list) else [],
        plan=plan,
    )
    return user


@router.put("/me", response_model=UserOut)
def update_me(user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> UserOut:
    provided_fields = user_in.model_fields_set

    if user_in.email:
        normalized_email = user_in.email.strip().lower()
        existing_email = db.query(User).filter(User.email == normalized_email, User.id != current_user.id).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email jǭ registrado.")
        current_user.email = normalized_email

    if user_in.cpf:
        existing_cpf = db.query(User).filter(User.cpf == user_in.cpf, User.id != current_user.id).first()
        if existing_cpf:
            raise HTTPException(status_code=400, detail="CPF já registrado.")

    if user_in.cnpj:
        existing_cnpj = db.query(User).filter(User.cnpj == user_in.cnpj, User.id != current_user.id).first()
        if existing_cnpj:
            raise HTTPException(status_code=400, detail="CNPJ já registrado.")

    if user_in.password:
        try:
            auth_service.validate_password_strength(user_in.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        current_user.hashed_password = auth_service.get_password_hash(user_in.password)
    if user_in.name:
        current_user.name = user_in.name
    if user_in.plan:
        current_user.plan = user_in.plan
    if user_in.subscription_id is not None:
        current_user.subscription_id = user_in.subscription_id
    if "cpf" in provided_fields:
        current_user.cpf = user_in.cpf
    if "cnpj" in provided_fields:
        current_user.cnpj = user_in.cnpj
    if "whatsapp" in provided_fields:
        current_user.whatsapp = user_in.whatsapp
    if "address_street" in provided_fields:
        current_user.address_street = (user_in.address_street or "").strip() or None
    if "address_number" in provided_fields:
        current_user.address_number = (user_in.address_number or "").strip() or None
    if "address_complement" in provided_fields:
        current_user.address_complement = (user_in.address_complement or "").strip() or None
    if "address_neighborhood" in provided_fields:
        current_user.address_neighborhood = (user_in.address_neighborhood or "").strip() or None
    if "address_city" in provided_fields:
        current_user.address_city = (user_in.address_city or "").strip() or None
    if "address_state" in provided_fields:
        current_user.address_state = user_in.address_state
    if "address_zipcode" in provided_fields:
        current_user.address_zipcode = user_in.address_zipcode

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password")
def change_my_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    if not auth_service.verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    try:
        auth_service.validate_password_strength(payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    current_user.hashed_password = auth_service.get_password_hash(payload.new_password)
    db.add(current_user)
    db.commit()
    return {"detail": "Senha atualizada com sucesso."}


@router.post("/me/avatar", response_model=UserOut)
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    content_type = (getattr(file, "content_type", "") or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Envie uma imagem válida.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="A imagem deve ter no máximo 5MB.")

    avatar_url = media_storage.save(file_bytes, file.filename or "avatar", content_type)
    current_user.avatar_url = avatar_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/avatar", response_model=UserOut)
def delete_my_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    current_user.avatar_url = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/password/forgot")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == payload.email).first()
    # Mesmo que o email não exista, retornamos resposta genérica para evitar enumeração
    if not user:
        return {"detail": "Se o email estiver cadastrado, enviaremos instruções para redefinir a senha."}

    token = auth_service.create_password_reset_token(user.email)
    response: dict[str, str] = {
        "detail": "Se o email estiver cadastrado, enviaremos instruções para redefinir a senha."
    }
    # Ambiente dev/test: retornamos o token para facilitar QA. Em produção, será enviado por e-mail.
    if settings.env != "prod":
        response["reset_token"] = token
    return response


@router.post("/password/reset")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> dict:
    email = auth_service.verify_password_reset_token(payload.token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    try:
        auth_service.validate_password_strength(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user.hashed_password = auth_service.get_password_hash(payload.password)
    db.add(user)
    db.commit()
    return {"detail": "Senha atualizada com sucesso."}


@router.post("/password/reset/by-profile")
def reset_password_by_profile(payload: PasswordResetByProfile, db: Session = Depends(get_db)) -> dict:
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Dados nao conferem.")

    stored_cpf = "".join(filter(str.isdigit, user.cpf or ""))
    if not stored_cpf or stored_cpf != payload.cpf:
        raise HTTPException(status_code=400, detail="Dados nao conferem.")

    try:
        auth_service.validate_password_strength(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user.hashed_password = auth_service.get_password_hash(payload.password)
    db.add(user)
    db.commit()
    return {"detail": "Senha atualizada com sucesso."}


@router.post("/trial/ack", response_model=UserOut)
def acknowledge_trial(
    payload: TrialAckPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserOut:
    if payload.stage == "start":
        current_user.trial_ack_start = True
    elif payload.stage == "warn3":
        current_user.trial_warn_3days_ack = True
    elif payload.stage == "warn1":
        current_user.trial_warn_1day_ack = True
    else:
        current_user.trial_ack_end = True
        current_user.trial_original_plan = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/invite-info", response_model=InviteInfoOut)
def get_invite_info(token: str, db: Session = Depends(get_db)) -> InviteInfoOut:
    invite = find_pending_invite_by_token(db, token)
    if not invite:
        return InviteInfoOut(valid=False, reason="invalid")
    now = datetime.now(timezone.utc)
    if invite.status != "pending":
        return InviteInfoOut(valid=False, reason=invite.status)
    if invite.expires_at < now:
        invite.status = "expired"
        db.add(invite)
        db.commit()
        return InviteInfoOut(valid=False, reason="expired")
    agency = db.query(Agency).filter(Agency.id == invite.agency_id).first()
    return InviteInfoOut(
        valid=True,
        agency_name=agency.name if agency else "Agência",
        email=invite.email,
        name=invite.name,
    )


@router.post("/accept-invite")
def accept_invite(payload: AcceptInviteIn, db: Session = Depends(get_db)) -> dict:
    invite = find_pending_invite_by_token(db, payload.token)
    if not invite:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado.")
    if invite.status != "pending":
        raise HTTPException(status_code=400, detail="Convite não está pendente.")
    now = datetime.now(timezone.utc)
    if invite.expires_at < now:
        invite.status = "expired"
        db.add(invite)
        db.commit()
        raise HTTPException(status_code=400, detail="Token expirado.")

    try:
        auth_service.validate_password_strength(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = db.query(User).filter(User.email == invite.email).first()
    if not user:
        invited_role = (invite.role_name or "member").strip().lower()
        if invited_role not in {"admin", "member"}:
            invited_role = "member"
        user = User(
            email=invite.email,
            name=invite.name,
            hashed_password=auth_service.get_password_hash(payload.password),
            plan="free",
            is_active=True,
            is_owner=False,
            role=invited_role,
            status="active",
            permissions=[] if invited_role == "admin" else list(invite.permissions or []),
            invited_by_user_id=invite.invited_by_user_id,
        )
        db.add(user)
        db.flush()
        sub = Subscription(user_id=user.id, plan=user.plan or "free")
        db.add(sub)
        db.flush()
        user.subscription_id = sub.id
    else:
        invited_role = (invite.role_name or "member").strip().lower()
        if invited_role not in {"admin", "member"}:
            invited_role = "member"
        user.hashed_password = auth_service.get_password_hash(payload.password)
        user.is_active = True
        user.is_owner = False if user.is_owner is None else user.is_owner
        user.role = invited_role
        user.status = "active"
        user.permissions = [] if invited_role == "admin" else list(invite.permissions or [])
        if invite.invited_by_user_id and not user.invited_by_user_id:
            user.invited_by_user_id = invite.invited_by_user_id

    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == invite.agency_id, AgencyUser.user_id == user.id)
        .first()
    )
    if not membership:
        membership = AgencyUser(agency_id=invite.agency_id, user_id=user.id, role=(invite.role_name or "member"))
        db.add(membership)
    if not user.primary_agency_id:
        user.primary_agency_id = invite.agency_id

    invite.status = "accepted"
    invite.accepted_at = now
    db.add(invite)
    db.add(user)
    db.commit()
    return {"detail": "Convite aceito com sucesso."}

