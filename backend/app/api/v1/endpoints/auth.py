from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.core.rate_limit import InMemoryRateLimiter
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.services import auth as auth_service

router = APIRouter()
settings = get_settings()
login_limiter = InMemoryRateLimiter(attempts=5, window_seconds=300, block_minutes=15)


class TrialAckPayload(BaseModel):
    stage: Literal["start", "end"]


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    existing_cpf = db.query(User).filter(User.cpf == user_in.cpf).first()
    if existing_cpf:
        raise HTTPException(status_code=400, detail="CPF already registered")
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
        hashed_password=hashed,
        plan=user_in.plan or "free"
    )
    db.add(user)
    db.flush()
    sub = Subscription(user_id=user.id, plan=user.plan)
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    client_ip = request.client.host if request.client else "unknown"
    if login_limiter.is_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Tente novamente em alguns minutos.",
        )
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        login_limiter.register_failure(client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    login_limiter.clear(client_ip)
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_service.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_active_user)) -> UserOut:
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> UserOut:
    if user_in.cpf:
        existing_cpf = db.query(User).filter(User.cpf == user_in.cpf, User.id != current_user.id).first()
        if existing_cpf:
            raise HTTPException(status_code=400, detail="CPF already registered")

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
    if user_in.cpf is not None:
        current_user.cpf = user_in.cpf
    if user_in.whatsapp is not None:
        current_user.whatsapp = user_in.whatsapp

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


@router.post("/trial/ack", response_model=UserOut)
def acknowledge_trial(
    payload: TrialAckPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserOut:
    if payload.stage == "start":
        current_user.trial_ack_start = True
    else:
        current_user.trial_ack_end = True
        current_user.trial_original_plan = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
