"""Chaves dos bancos de fotos (Unsplash, Pexels) cadastradas no Admin Master.

Ficam na mesma tabela das chaves de voo (external_api_keys), com provider "unsplash" ou
"pexels". Para estas, "monthly_limit" é o limite POR HORA e "monthly_usage_estimated" conta
as chamadas da hora atual (zera quando a hora vira). Várias chaves do mesmo banco são usadas
em ordem (priority): quando uma esgota na hora, a próxima assume; a esgotada volta sozinha
na hora seguinte. As chaves de ambiente (UNSPLASH_ACCESS_KEY / PEXELS_API_KEY) entram por
último, como reserva.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.external_api_key import ExternalApiKey
from app.services.api_key_crypto import decrypt_api_key

# Na ordem de uso (depois das fotos cadastradas no Admin Master, que vêm sempre antes).
IMAGE_PROVIDERS = ("pixabay", "unsplash", "pexels")
# Pixabay: 100 por minuto por chave; aqui fica um teto por hora folgado.
DEFAULT_HOURLY_LIMIT = {"pixabay": 1000, "unsplash": 50, "pexels": 200}
# Folga para não bater no limite real do banco (a contagem do banco inclui chamadas de teste).
SAFETY_MARGIN = 3


@dataclass
class ImageKey:
    provider: str
    plain_key: str
    record: ExternalApiKey | None = None

    @property
    def ident(self) -> str:
        return f"{self.provider}:{self.record.id if self.record else 'env'}"


def _hour_start(moment: datetime) -> datetime:
    return moment.replace(minute=0, second=0, microsecond=0)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def roll_hour(record: ExternalApiKey, now: datetime | None = None) -> bool:
    """Zera a contagem quando a hora virou e reativa a chave que tinha esgotado. True se mudou."""
    now = now or datetime.now(timezone.utc)
    last = _aware(record.last_used_at)
    changed = False
    if last is None or _hour_start(last) < _hour_start(now):
        if record.monthly_usage_estimated:
            record.monthly_usage_estimated = 0
            changed = True
        if record.status == "exhausted":
            record.status = "active"
            record.last_error = None
            changed = True
    return changed


# Chaves de ambiente não têm linha no banco: a contagem da hora fica em memória.
_env_calls: dict[str, list[float]] = {}


def _env_has_room(provider: str) -> bool:
    now = time.time()
    calls = [moment for moment in _env_calls.get(provider, []) if moment > now - 3600]
    _env_calls[provider] = calls
    return len(calls) < DEFAULT_HOURLY_LIMIT.get(provider, 50) - SAFETY_MARGIN - 7


def available_image_keys(db: Session, provider: str) -> list[ImageKey]:
    """Chaves com chamadas sobrando nesta hora, na ordem de uso."""
    now = datetime.now(timezone.utc)
    rows = (
        db.query(ExternalApiKey)
        .filter(ExternalApiKey.provider == provider, ExternalApiKey.is_active.is_(True))
        .order_by(ExternalApiKey.priority.asc(), ExternalApiKey.id.asc())
        .all()
    )
    keys: list[ImageKey] = []
    for row in rows:
        if roll_hour(row, now):
            db.add(row)
        if row.status != "active":
            continue
        limit = int(row.monthly_limit or DEFAULT_HOURLY_LIMIT.get(provider, 50))
        if int(row.monthly_usage_estimated or 0) >= max(1, limit - SAFETY_MARGIN):
            continue
        try:
            keys.append(ImageKey(provider=provider, plain_key=decrypt_api_key(row.api_key_encrypted), record=row))
        except Exception as exc:  # noqa: BLE001 - chave ilegível não pode travar a busca
            row.status = "error"
            row.last_error = f"Falha ao ler a chave: {exc}"[:1000]
            db.add(row)
    env_key = env_image_key(provider)
    if env_key.strip() and _env_has_room(provider):
        keys.append(ImageKey(provider=provider, plain_key=env_key.strip()))
    return keys


def env_image_key(provider: str) -> str:
    """Chave de reserva do arquivo de configuração do servidor."""
    settings = get_settings()
    field = {"pixabay": "pixabay_api_key", "unsplash": "unsplash_access_key", "pexels": "pexels_api_key"}.get(provider, "")
    return getattr(settings, field, None) or ""


def has_any_image_key(db: Session) -> bool:
    if any(env_image_key(provider).strip() for provider in IMAGE_PROVIDERS):
        return True
    return (
        db.query(ExternalApiKey.id)
        .filter(ExternalApiKey.provider.in_(IMAGE_PROVIDERS), ExternalApiKey.is_active.is_(True))
        .first()
        is not None
    )


def record_image_call(db: Session, key: ImageKey, response: httpx.Response | None) -> None:
    """Conta a chamada da chave e marca esgotada (até a próxima hora) ou com erro."""
    if key.record is None:
        _env_calls.setdefault(key.provider, []).append(time.time())
        return
    record = key.record
    now = datetime.now(timezone.utc)
    roll_hour(record, now)
    record.monthly_usage_estimated = int(record.monthly_usage_estimated or 0) + 1
    record.total_usage_estimated = int(record.total_usage_estimated or 0) + 1
    record.last_used_at = now
    status = response.status_code if response is not None else 0
    remaining = (response.headers.get("X-Ratelimit-Remaining") if response is not None else None) or ""
    if key.provider == "pixabay":
        remaining = ""  # o limite do Pixabay é por minuto: só o 429 conta como esgotada
    limit = int(record.monthly_limit or DEFAULT_HOURLY_LIMIT.get(key.provider, 50))
    next_hour = (_hour_start(now).hour + 1) % 24
    if status in (401, 403):
        record.status = "error"
        record.last_error = "O banco recusou a chave (inválida ou revogada)."
    elif status == 429 or (remaining.isdigit() and int(remaining) <= SAFETY_MARGIN) or record.monthly_usage_estimated >= limit:
        record.status = "exhausted"
        record.last_error = f"Limite da hora atingido. Volta às {next_hour:02d}h (UTC)."
    elif 200 <= status < 300:
        record.status = "active"
        record.last_error = None
    db.add(record)
    db.flush()
