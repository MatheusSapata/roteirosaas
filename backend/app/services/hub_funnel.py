"""Envia os passos da jornada do Roteiro Online para o funil do Viaje On Hub.

Melhor esforço: roda em segundo plano, com prazo curto, e qualquer falha (Hub fora do ar, rede,
configuração ausente) é ignorada para nunca atrasar ou derrubar cadastro, checkout ou pagamento.
O endereço e a chave do produto vêm da tela do Admin Master (Integrações › ViajeHub), guardados
criptografados em external_api_keys; sem eles, valem HUB_FUNNEL_URL e HUB_FUNNEL_KEY do ambiente.
Sem nenhum dos dois, nada é enviado.
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 5.0
PROVIDER = "viajehub"
# A configuração do banco é lida no máximo uma vez por minuto (cada passo do funil passa por aqui).
_CACHE_SECONDS = 60.0
_cache: dict[str, Any] = {"at": 0.0, "value": None}


def _db_config() -> tuple[str, str] | None:
    """Endereço e chave salvos pelo Admin Master; None quando não há ou não dá para ler."""
    from app.db import session as db_session
    from app.models.external_api_key import ExternalApiKey
    from app.services.api_key_crypto import decrypt_api_key

    try:
        db = db_session.SessionLocal()
        try:
            record = (
                db.query(ExternalApiKey)
                .filter(ExternalApiKey.provider == PROVIDER, ExternalApiKey.is_active.is_(True))
                .order_by(ExternalApiKey.id.desc())
                .first()
            )
            if not record or not (record.api_host or "").strip():
                return None
            return record.api_host.strip(), decrypt_api_key(record.api_key_encrypted).strip()
        finally:
            db.close()
    except Exception:  # pragma: no cover - sem banco ou chave ilegível: cai no ambiente
        logger.warning("Não foi possível ler a conexão com o ViajeHub salva no banco.", exc_info=False)
        return None


def clear_config_cache() -> None:
    _cache["at"] = 0.0
    _cache["value"] = None


def hub_config() -> tuple[str, str, str]:
    """(endereço, chave, origem). Origem: "painel", "ambiente" ou "" quando não há configuração."""
    now = time.monotonic()
    if now - _cache["at"] > _CACHE_SECONDS:
        _cache["value"] = _db_config()
        _cache["at"] = now
    saved = _cache["value"]
    if saved and saved[0] and saved[1]:
        return saved[0], saved[1], "painel"
    settings = get_settings()
    url = (settings.hub_funnel_url or "").strip()
    key = (settings.hub_funnel_key or "").strip()
    if url and key:
        return url, key, "ambiente"
    return "", "", ""


def check_connection(url: str, key: str) -> tuple[bool, str]:
    """Confere endereço e chave sem gravar nada no Hub: um corpo vazio é recusado como inválido
    (400) quando a chave é aceita e como não autorizado (401) quando a chave é errada."""
    try:
        response = httpx.post(url, json={}, headers={"x-funnel-key": key}, timeout=_TIMEOUT_SECONDS)
    except Exception:
        return False, "Não foi possível falar com o ViajeHub nesse endereço."
    if response.status_code == 401:
        return False, "O ViajeHub recusou a chave. Confira se copiou a chave do Roteiro Online."
    if response.status_code == 400:
        return True, "Conexão funcionando: o ViajeHub reconheceu a chave."
    if response.status_code == 404:
        return False, "Endereço não encontrado. Ele deve terminar em /api/public/funil/evento."
    return False, f"O ViajeHub respondeu de um jeito inesperado (HTTP {response.status_code})."


def _post(url: str, key: str, body: dict[str, Any]) -> None:
    try:
        response = httpx.post(url, json=body, headers={"x-funnel-key": key}, timeout=_TIMEOUT_SECONDS)
        if response.status_code >= 400:
            logger.warning("Hub recusou o passo %s: HTTP %s", body.get("event_type"), response.status_code)
    except Exception:  # pragma: no cover - o funil nunca pode quebrar o fluxo principal
        logger.warning("Não foi possível enviar o passo %s ao Hub.", body.get("event_type"), exc_info=False)


def send_hub_event(
    event_type: str,
    *,
    email: str | None,
    name: str | None = None,
    phone: str | None = None,
    utm: dict[str, str | None] | None = None,
    payload: dict[str, Any] | None = None,
    external_id: str | None = None,
) -> bool:
    """Dispara o passo em uma thread e volta na hora. Devolve False quando não há o que enviar."""
    url, key, _ = hub_config()
    clean_email = (email or "").strip().lower()
    if not url or not key or not clean_email:
        return False
    body: dict[str, Any] = {
        "event_type": event_type,
        "source": "roteiro_online",
        "email": clean_email,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "external_id": external_id or f"ro-{event_type}-{uuid.uuid4().hex}",
    }
    if name:
        body["name"] = name
    if phone:
        body["phone"] = phone
    clean_utm = {k: v for k, v in (utm or {}).items() if v}
    if clean_utm:
        body["utm"] = clean_utm
    clean_payload = {k: v for k, v in (payload or {}).items() if v is not None}
    if clean_payload:
        body["payload"] = clean_payload
    threading.Thread(target=_post, args=(url, key, body), daemon=True).start()
    return True
