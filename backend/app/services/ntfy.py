from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.core.config import get_settings
from app.services.webhook_notifications import send_notification

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


class NtfyServiceError(Exception):
    """Raised when ntfy rejects a message or cannot be reached."""


class SubscriptionPushScenario(StrEnum):
    NEW = "nova_assinatura"
    RENEWED = "assinatura_renovada"
    CANCELLED = "assinatura_cancelada"
    UPGRADED = "upgrade_realizado"
    TEST = "assinatura_teste"


def _normalize_tags(tags: str | Iterable[str] | None) -> str | None:
    if tags is None:
        return None
    if isinstance(tags, str):
        cleaned = [item.strip() for item in tags.split(",") if item.strip()]
        return ",".join(cleaned) if cleaned else None
    cleaned = [str(item).strip() for item in tags if str(item).strip()]
    return ",".join(cleaned) if cleaned else None


def _format_brl(value: Decimal | float | int | str | None) -> str:
    if value is None:
        return "R$ 0,00"
    if isinstance(value, Decimal):
        amount = value
    else:
        try:
            text = str(value).strip().replace("R$", "").replace(" ", "")
            if "," in text and "." in text:
                if text.rfind(",") > text.rfind("."):
                    text = text.replace(".", "").replace(",", ".")
                else:
                    text = text.replace(",", "")
            elif "," in text:
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
            amount = Decimal(text)
        except (InvalidOperation, ValueError):
            amount = Decimal("0")
    amount = amount.quantize(Decimal("0.01"))
    text = f"{amount:,.2f}"
    return f"R$ {text.replace(',', 'X').replace('.', ',').replace('X', '.')}"


def _format_timestamp(value: datetime | None = None) -> str:
    current = value or datetime.now(tz=BRAZIL_TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=BRAZIL_TZ)
    else:
        current = current.astimezone(BRAZIL_TZ)
    return current.strftime("%d/%m/%Y %H:%M")


def build_subscription_push_message(
    *,
    scenario: SubscriptionPushScenario | str,
    user_name: str,
    payment_method: str,
    amount: Decimal | float | int | str | None,
    plan_name: str | None = None,
    offer_name: str | None = None,
    previous_plan_name: str | None = None,
    upgraded_plan_name: str | None = None,
    cancelled_item: str | None = None,
    occurred_at: datetime | None = None,
) -> tuple[str, str, list[str]]:
    scenario_value = SubscriptionPushScenario(scenario)
    title_label_map = {
        SubscriptionPushScenario.NEW: "Assinatura criada",
        SubscriptionPushScenario.RENEWED: "Assinatura renovada",
        SubscriptionPushScenario.CANCELLED: "Assinatura cancelada",
        SubscriptionPushScenario.UPGRADED: "Upgrade realizado",
        SubscriptionPushScenario.TEST: "Assinatura de teste",
    }
    title_label = title_label_map[scenario_value]
    if scenario_value == SubscriptionPushScenario.UPGRADED:
        source_plan = (previous_plan_name or plan_name or "Plano anterior").strip()
        target_plan = (upgraded_plan_name or offer_name or plan_name or "Novo plano").strip()
        title = f"{title_label} - {source_plan} para {target_plan}"
    else:
        plan_label = (plan_name or offer_name or "Plano").strip()
        title = f"{title_label} - {plan_label}"
    parts = [_format_brl(amount), user_name.strip() or "Não informado"]
    if scenario_value not in (SubscriptionPushScenario.CANCELLED, SubscriptionPushScenario.UPGRADED):
        parts.append(payment_method.strip() or "Não informado")
    message = " | ".join(parts)
    tags = ["rocket", "subscription", scenario_value.value.replace("_", "-")]
    if scenario_value == SubscriptionPushScenario.UPGRADED:
        tags = ["arrow_up", "subscription", "upgrade"]
    return title, message, tags


class NtfyService:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        default_topic: str | None = None,
        timeout_seconds: int | float | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.ntfy_base_url).rstrip("/")
        self.default_topic = (default_topic or settings.ntfy_default_topic).strip("/")
        self.timeout = httpx.Timeout(float(timeout_seconds or settings.ntfy_timeout_seconds))

    def publish(
        self,
        *,
        message: str,
        title: str,
        topic: str | None = None,
        priority: str | int | None = None,
        tags: str | Iterable[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        topic_name = (topic or self.default_topic).strip("/")
        if not topic_name:
            raise NtfyServiceError("Tópico ntfy não configurado.")

        payload = (message or "").strip()
        if not payload:
            raise NtfyServiceError("Mensagem ntfy obrigatória.")

        request_headers = {
            "Title": title.strip(),
        }
        if priority is not None:
            request_headers["Priority"] = str(priority)
        normalized_tags = _normalize_tags(tags)
        if normalized_tags:
            request_headers["Tags"] = normalized_tags
        if headers:
            request_headers.update({key: str(value) for key, value in headers.items() if value is not None})

        url = f"{self.base_url}/{topic_name}"
        try:
            response = httpx.post(url, content=payload.encode("utf-8"), headers=request_headers, timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise NtfyServiceError("Erro ao conectar com ntfy.") from exc

        if response.status_code >= 400:
            detail = response.text.strip()
            if not detail:
                try:
                    detail = str(response.json())
                except Exception:
                    detail = f"ntfy respondeu com status {response.status_code}."
            raise NtfyServiceError(detail)

        if not response.content:
            return None

        try:
            return response.json()
        except Exception:
            return {"status_code": response.status_code, "body": response.text}


def publish_subscription_notification(
    *,
    scenario: SubscriptionPushScenario | str,
    user_name: str,
    payment_method: str | None,
    amount: Decimal | float | int | str | None,
    plan_name: str | None = None,
    offer_name: str | None = None,
    previous_plan_name: str | None = None,
    upgraded_plan_name: str | None = None,
    cancelled_item: str | None = None,
    occurred_at: datetime | None = None,
    topic: str | None = None,
    service: NtfyService | None = None,
) -> None:
    scenario_value = SubscriptionPushScenario(scenario)
    event_key_map = {
        SubscriptionPushScenario.NEW: "subscription_created",
        SubscriptionPushScenario.RENEWED: "subscription_renewed",
        SubscriptionPushScenario.CANCELLED: "subscription_cancelled",
        SubscriptionPushScenario.UPGRADED: "upgrade_realizado",
        SubscriptionPushScenario.TEST: "subscription_test",
    }
    context = {
        "user_name": user_name,
        "payment_method": payment_method or "Não informado",
        "amount": _format_brl(amount),
        "plan_name": plan_name or offer_name or "Plano",
        "offer_name": offer_name or "",
        "previous_plan_name": previous_plan_name or plan_name or "Plano anterior",
        "upgraded_plan_name": upgraded_plan_name or offer_name or "Novo plano",
        "cancelled_item": cancelled_item or "",
        "occurred_at": _format_timestamp(occurred_at),
        "event_label": {
            SubscriptionPushScenario.NEW: "Assinatura criada",
            SubscriptionPushScenario.RENEWED: "Assinatura renovada",
            SubscriptionPushScenario.CANCELLED: "Assinatura cancelada",
            SubscriptionPushScenario.UPGRADED: "Upgrade realizado",
            SubscriptionPushScenario.TEST: "Assinatura de teste",
        }[scenario_value],
    }
    send_notification(event_key=event_key_map[scenario_value], context=context)
