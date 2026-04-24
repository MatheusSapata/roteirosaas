from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class ApiKeyDecryptionError(Exception):
    """Raised when an encrypted API key cannot be decrypted."""


def mask_api_key(raw_key: str | None) -> str:
    clean = "".join((raw_key or "").split())
    if not clean:
        return "****"
    tail = clean[-4:]
    return f"**** **** **** {tail}"


def extract_api_key_last4(raw_key: str | None) -> str:
    clean = "".join((raw_key or "").split())
    if not clean:
        return ""
    return clean[-4:]


def _build_fernet_key(seed: str) -> bytes:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache
def _resolve_fernet() -> Fernet:
    settings = get_settings()
    configured = (getattr(settings, "flight_api_keys_encryption_key", None) or "").strip()
    if configured:
        if len(configured) == 44:
            key = configured.encode("utf-8")
        else:
            key = _build_fernet_key(configured)
    else:
        key = _build_fernet_key(settings.jwt_secret_key)
    return Fernet(key)


def encrypt_api_key(raw_key: str) -> str:
    fernet = _resolve_fernet()
    token = fernet.encrypt(raw_key.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_api_key(value: str) -> str:
    try:
        decrypted = _resolve_fernet().decrypt(value.encode("utf-8"))
        return decrypted.decode("utf-8")
    except (InvalidToken, ValueError, TypeError) as exc:
        raise ApiKeyDecryptionError("A chave de API não pôde ser descriptografada.") from exc
