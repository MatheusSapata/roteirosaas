from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User

# Usa pbkdf2_sha256 para evitar limitações/bugs do backend bcrypt.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def validate_password_strength(password: str) -> None:
    if not password or len(password) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    if not any(c.islower() for c in password):
        raise ValueError("A senha deve ter pelo menos uma letra minúscula.")
    if not any(c.isupper() for c in password):
        raise ValueError("A senha deve ter pelo menos uma letra maiúscula.")
    if not any(c.isdigit() for c in password):
        raise ValueError("A senha deve ter pelo menos um número.")


def create_password_reset_token(email: str, expires_minutes: Optional[int] = None) -> str:
    duration = expires_minutes or settings.password_reset_token_minutes
    expire = datetime.utcnow() + timedelta(minutes=duration)
    payload = {"sub": email, "scope": "password-reset", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_password_reset_token(token: str) -> Optional[str]:
    payload = decode_token(token)
    if not payload:
        return None
    if payload.get("scope") != "password-reset":
        return None
    return payload.get("sub")
