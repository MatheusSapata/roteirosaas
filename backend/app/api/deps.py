from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.user import User
from app.schemas.user import TokenData
from app.services.trial import sync_trial_status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
settings = get_settings()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar suas credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as exc:  # pragma: no cover - segurança
        raise credentials_exception from exc
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    sync_trial_status(user, db)
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo.")
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Permissões insuficientes.")
    return current_user


def require_agency_membership(db: Session, agency_id: int, user_id: int) -> Agency:
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agência não encontrada.")
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Você não faz parte desta agência.")
    return agency
