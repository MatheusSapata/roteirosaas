from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(slots=True)
class CheckoutPricing:
    base_amount_cents: int
    final_amount_cents: int

    @property
    def fee_amount_cents(self) -> int:
        return max(0, self.final_amount_cents - self.base_amount_cents)


def money_to_cents(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return int((decimal_value * 100).quantize(Decimal("1")))


def resolve_quote_total_cents(payload: dict[str, Any]) -> int | None:
    quote_payload = payload.get("quote") if isinstance(payload.get("quote"), dict) else payload
    if not isinstance(quote_payload, dict):
        return None
    return (
        money_to_cents(quote_payload.get("gross_amount"))
        or money_to_cents(quote_payload.get("total_amount"))
        or money_to_cents(quote_payload.get("amount"))
        or money_to_cents(quote_payload.get("value"))
    )


def pricing_from_sale(base_amount_cents: int, quoted_total_cents: int | None, fee_mode: str) -> CheckoutPricing:
    if fee_mode == "pass_through" and quoted_total_cents and quoted_total_cents > 0:
        return CheckoutPricing(base_amount_cents=base_amount_cents, final_amount_cents=quoted_total_cents)
    return CheckoutPricing(base_amount_cents=base_amount_cents, final_amount_cents=base_amount_cents)
