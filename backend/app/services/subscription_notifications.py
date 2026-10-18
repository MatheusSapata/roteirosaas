"""Avisos das assinaturas no Pushover: um aviso por acontecimento.

Cada pagamento confirmado vira um aviso só, do tipo certo: compra aprovada (assinatura nova),
assinatura renovada ou upgrade (troca de plano ou de ciclo). O cancelamento tem o dele. Texto, som e
quem recebe cada evento ficam em Admin Master › Webhooks e push.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

from app.services.hub_funnel import send_hub_event
from app.services.webhook_notifications import contact_context, notify_safely

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


class SubscriptionPushScenario(StrEnum):
    NEW = "nova_assinatura"
    RENEWED = "assinatura_renovada"
    CANCELLED = "assinatura_cancelada"
    UPGRADED = "upgrade_realizado"


# O evento de cada acontecimento (um só por pagamento) e como ele aparece no texto.
SCENARIO_EVENT_KEYS = {
    SubscriptionPushScenario.NEW: "purchase_approved",
    SubscriptionPushScenario.RENEWED: "subscription_renewed",
    SubscriptionPushScenario.UPGRADED: "upgrade_realizado",
    SubscriptionPushScenario.CANCELLED: "subscription_cancelled",
}
SCENARIO_LABELS = {
    SubscriptionPushScenario.NEW: "Compra aprovada",
    SubscriptionPushScenario.RENEWED: "Assinatura renovada",
    SubscriptionPushScenario.UPGRADED: "Upgrade realizado",
    SubscriptionPushScenario.CANCELLED: "Assinatura cancelada",
}
PURCHASE_KINDS = {
    SubscriptionPushScenario.NEW: "Nova assinatura",
    SubscriptionPushScenario.RENEWED: "Renovação",
    SubscriptionPushScenario.UPGRADED: "Upgrade",
}


def format_brl(value: Decimal | float | int | str | None) -> str:
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


def _send_hub_purchase(
    scenario: SubscriptionPushScenario,
    *,
    email: str | None,
    name: str | None,
    phone: str | None,
    plan: str | None,
    amount: Any,
    payment_method: str | None,
) -> None:
    """Assinatura nova ou troca de plano vira o passo `subscription_paid` no funil do Hub."""
    if scenario not in (SubscriptionPushScenario.NEW, SubscriptionPushScenario.UPGRADED):
        return
    try:
        value = float(amount) if amount is not None else None
    except (TypeError, ValueError):
        value = None
    send_hub_event(
        "subscription_paid",
        email=email,
        name=name,
        phone=phone,
        payload={
            "plan": plan,
            "amount": value,
            "payment_method": payment_method,
            "upgrade": scenario == SubscriptionPushScenario.UPGRADED,
        },
    )


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
    customer_email: str | None = None,
    customer_phone: str | None = None,
) -> None:
    scenario_value = SubscriptionPushScenario(scenario)
    upgraded = scenario_value == SubscriptionPushScenario.UPGRADED
    _send_hub_purchase(
        scenario_value,
        email=customer_email,
        name=user_name,
        phone=customer_phone,
        plan=upgraded_plan_name if upgraded else plan_name,
        amount=amount,
        payment_method=payment_method,
    )
    plan = plan_name or offer_name or "Plano"
    notify_safely(
        event_key=SCENARIO_EVENT_KEYS[scenario_value],
        context={
            "event_label": SCENARIO_LABELS[scenario_value],
            "user_name": user_name,
            "payment_method": payment_method or "Não informado",
            "amount": format_brl(amount),
            # No upgrade, o plano é o novo.
            "plan_name": (upgraded_plan_name or offer_name or plan) if upgraded else plan,
            "offer_name": offer_name or "",
            "previous_plan_name": previous_plan_name or plan_name or "Plano anterior",
            "upgraded_plan_name": upgraded_plan_name or offer_name or "Novo plano",
            "cancelled_item": cancelled_item or "",
            "occurred_at": _format_timestamp(occurred_at),
            "purchase_kind": PURCHASE_KINDS.get(scenario_value, ""),
            **contact_context(customer_email, customer_phone),
        },
    )
