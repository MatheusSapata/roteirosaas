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


@lru_cache
def _resolve_decryption_fernets() -> tuple[Fernet, ...]:
    settings = get_settings()
    candidates: list[str] = []

    configured = (getattr(settings, "flight_api_keys_encryption_key", None) or "").strip()
    if configured:
        candidates.append(configured)

    for legacy in getattr(settings, "flight_api_keys_decryption_keys", []) or []:
        seed = (legacy or "").strip()
        if seed:
            candidates.append(seed)

    jwt_seed = (settings.jwt_secret_key or "").strip()
    if jwt_seed:
        candidates.append(jwt_seed)

    unique_candidates = list(dict.fromkeys(candidates))
    if not unique_candidates:
        return (_resolve_fernet(),)

    fernets: list[Fernet] = []
    for seed in unique_candidates:
        if len(seed) == 44:
            key = seed.encode("utf-8")
        else:
            key = _build_fernet_key(seed)
        fernets.append(Fernet(key))
    return tuple(fernets)


def encrypt_api_key(raw_key: str) -> str:
    fernet = _resolve_fernet()
    token = fernet.encrypt(raw_key.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_api_key_with_migration_hint(value: str) -> tuple[str, bool]:
    raw_value = str(value or "").strip()
    if not raw_value:
        raise ApiKeyDecryptionError("A chave de API nao pode ser descriptografada.")

    last_exc: Exception | None = None
    for fernet in _resolve_decryption_fernets():
        try:
            decrypted = fernet.decrypt(raw_value.encode("utf-8"))
            return decrypted.decode("utf-8"), False
        except (InvalidToken, ValueError, TypeError) as exc:
            last_exc = exc
            continue

    # Legacy support: some old rows were persisted in plain text.
    if not raw_value.startswith("gAAAA"):
        return raw_value, True

    raise ApiKeyDecryptionError("A chave de API nao pode ser descriptografada.") from last_exc


def decrypt_api_key(value: str) -> str:
    plain_key, _ = decrypt_api_key_with_migration_hint(value)
    return plain_key
