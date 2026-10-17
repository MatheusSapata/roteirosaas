"""Envia os passos da jornada do Roteiro Online para o funil do Viaje On Hub.

Melhor esforço: roda em segundo plano, com prazo curto, e qualquer falha (Hub fora do ar, rede,
configuração ausente) é ignorada para nunca atrasar ou derrubar cadastro, checkout ou pagamento.
O endereço e a chave do produto vêm de HUB_FUNNEL_URL e HUB_FUNNEL_KEY; sem elas, nada é enviado.
"""
from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 5.0


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
    settings = get_settings()
    url = (settings.hub_funnel_url or "").strip()
    key = (settings.hub_funnel_key or "").strip()
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
