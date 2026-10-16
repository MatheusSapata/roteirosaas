"""Envio de avisos pelo Pushover (https://pushover.net/api).

Cada conta cadastrada no Admin Master é uma pessoa (chave do usuário). O token do aplicativo é de
um aplicativo criado em pushover.net/apps: um só serve para mandar a todas as contas.
"""
from __future__ import annotations

import httpx

MESSAGES_URL = "https://api.pushover.net/1/messages.json"
VALIDATE_URL = "https://api.pushover.net/1/users/validate.json"
TIMEOUT_SECONDS = 8.0
MAX_TITLE = 250
MAX_MESSAGE = 1024

# Prioridade das regras (1 a 5, a do ntfy) → Pushover (-2 a 2). A 2 do Pushover (emergência) fica
# de fora: ela repete o alarme até alguém confirmar no celular.
PRIORITY_MAP = {1: -2, 2: -1, 3: 0, 4: 1, 5: 1}


class PushoverError(Exception):
    """O Pushover recusou o aviso (chave ou token inválido, limite do mês) ou não respondeu."""


def _errors(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Pushover respondeu com status {response.status_code}."
    errors = payload.get("errors") if isinstance(payload, dict) else None
    if isinstance(errors, list) and errors:
        return "; ".join(str(item) for item in errors)
    return f"Pushover respondeu com status {response.status_code}."


def send_message(
    *,
    app_token: str,
    user_key: str,
    title: str,
    message: str,
    priority: int = 3,
    device: str | None = None,
    url: str | None = None,
    url_title: str | None = None,
    sound: str | None = None,
) -> None:
    data = {
        "token": app_token,
        "user": user_key,
        "title": (title or "").strip()[:MAX_TITLE],
        "message": ((message or "").strip() or (title or "").strip() or "Aviso")[:MAX_MESSAGE],
        "priority": str(PRIORITY_MAP.get(int(priority or 3), 0)),
    }
    if device:
        data["device"] = device
    if sound:
        data["sound"] = sound  # ex.: "cashregister" (cha-ching); sem: o som padrão do aparelho
    if url:
        data["url"] = url[:512]
        if url_title:
            data["url_title"] = url_title[:100]
    try:
        response = httpx.post(MESSAGES_URL, data=data, timeout=TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise PushoverError("Não foi possível falar com o Pushover.") from exc
    if response.status_code >= 400:
        raise PushoverError(_errors(response))


def validate_user(*, app_token: str, user_key: str, device: str | None = None) -> None:
    """Confere a chave do usuário (e o aparelho) com o token do aplicativo, sem mandar aviso."""
    data = {"token": app_token, "user": user_key}
    if device:
        data["device"] = device
    try:
        response = httpx.post(VALIDATE_URL, data=data, timeout=TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise PushoverError("Não foi possível falar com o Pushover.") from exc
    if response.status_code >= 400:
        raise PushoverError(_errors(response))
