from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.schemas.finance import PaymentInstallmentOption, PaymentPricingResponse
from app.services.payments.blimboo_api import BlimbooAPIClient, BlimbooAPIError

BLIMBOO_CURRENCY_MAP = {
    "BRL": 1,
}

BLIMBOO_CREDIT_CARD_METHOD = 2
BLIMBOO_BOLETO_METHOD = 1
BLIMBOO_PIX_METHOD = 3


def money_to_cents(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return int((decimal_value * 100).quantize(Decimal("1")))


def coerce_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def collect_pricing_options(payload, max_installments: int) -> list[PaymentInstallmentOption]:
    resolved: dict[int, PaymentInstallmentOption] = {}

    if isinstance(payload, dict):
        raw_prices = payload.get("prices")
        if isinstance(raw_prices, list):
            for index, raw_price in enumerate(raw_prices, start=1):
                if index > max(1, max_installments):
                    break
                total_amount = money_to_cents(raw_price)
                if total_amount is None:
                    continue
                resolved[index] = PaymentInstallmentOption(
                    installments=index,
                    installment_amount_cents=int(round(total_amount / index)),
                    total_amount_cents=max(0, total_amount),
                    has_interest=False,
                )

    def register(entry: dict, forced_installments: int | None = None) -> None:
        installments = forced_installments
        if installments is None:
            installments = (
                coerce_int(entry.get("installments"))
                or coerce_int(entry.get("installment"))
                or coerce_int(entry.get("parcel"))
                or coerce_int(entry.get("times"))
                or coerce_int(entry.get("quantity"))
                or coerce_int(entry.get("number"))
            )
        if not installments or installments < 1 or installments > max(1, max_installments):
            return

        total_amount = (
            money_to_cents(entry.get("total_amount"))
            or money_to_cents(entry.get("gross_amount"))
            or money_to_cents(entry.get("amount"))
            or money_to_cents(entry.get("total"))
            or money_to_cents(entry.get("price"))
            or money_to_cents(entry.get("value"))
        )
        installment_amount = (
            money_to_cents(entry.get("installment_amount"))
            or money_to_cents(entry.get("installment_value"))
            or money_to_cents(entry.get("amount_per_installment"))
            or money_to_cents(entry.get("parcel_amount"))
            or money_to_cents(entry.get("value_per_installment"))
        )

        if total_amount is None and installment_amount is None:
            return
        if total_amount is None and installment_amount is not None:
            total_amount = installment_amount * installments
        if installment_amount is None and total_amount is not None:
            installment_amount = int(round(total_amount / max(installments, 1)))
        if total_amount is None or installment_amount is None:
            return

        resolved[installments] = PaymentInstallmentOption(
            installments=installments,
            installment_amount_cents=max(0, installment_amount),
            total_amount_cents=max(0, total_amount),
            has_interest=False,
        )

    def walk(node) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return

        register(node)
        for key, value in node.items():
            forced_installments = coerce_int(key) if isinstance(key, str) and key.isdigit() else None
            if forced_installments and isinstance(value, dict):
                register(value, forced_installments=forced_installments)
            walk(value)

    walk(payload)
    return sorted(resolved.values(), key=lambda option: option.installments)


def resolve_interest_candidates(interest_mode: str | None) -> list[int]:
    normalized = (interest_mode or "").lower()
    preferred = 1 if normalized in {"customer", "client"} else 2
    alternatives = [preferred, 1 if preferred == 2 else 2]
    deduped: list[int] = []
    for candidate in alternatives:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def build_fallback_credit_card_pricing(*, currency: str, base_amount_cents: int, max_installments: int) -> PaymentPricingResponse:
    options = [
        PaymentInstallmentOption(
            installments=installments,
            installment_amount_cents=int(round(base_amount_cents / installments)),
            total_amount_cents=base_amount_cents,
            has_interest=False,
        )
        for installments in range(1, max(1, max_installments) + 1)
    ]
    return PaymentPricingResponse(
        payment_method="credit_card",
        currency=currency,
        base_amount_cents=base_amount_cents,
        options=options,
    )


def fetch_credit_card_pricing(
    *,
    api_base_url: str,
    api_token: str | None,
    currency: str,
    base_amount_cents: int,
    interest_mode: str | None,
    max_installments: int,
) -> PaymentPricingResponse:
    currency_code = BLIMBOO_CURRENCY_MAP.get((currency or "").upper())
    if not api_token or currency_code is None:
        return build_fallback_credit_card_pricing(
            currency=currency,
            base_amount_cents=base_amount_cents,
            max_installments=max_installments,
        )

    client = BlimbooAPIClient(api_base_url or "", api_token)
    amount = round(base_amount_cents / 100, 2)

    for interest_by in resolve_interest_candidates(interest_mode):
        payload = {
            "currency": currency_code,
            "method": BLIMBOO_CREDIT_CARD_METHOD,
            "interest_by": interest_by,
            "advancing_receivables": 1,
            "amount": amount,
        }
        try:
            response = client.get_pricing(payload)
            options = collect_pricing_options(response, max_installments=max_installments)
            if options:
                normalized_options = [
                    PaymentInstallmentOption(
                        installments=option.installments,
                        installment_amount_cents=option.installment_amount_cents,
                        total_amount_cents=option.total_amount_cents,
                        has_interest=option.total_amount_cents > base_amount_cents,
                    )
                    for option in options
                ]
                return PaymentPricingResponse(
                    payment_method="credit_card",
                    currency=currency,
                    base_amount_cents=base_amount_cents,
                    options=normalized_options,
                )
        except (BlimbooAPIError, ValueError):
            continue

    return build_fallback_credit_card_pricing(
        currency=currency,
        base_amount_cents=base_amount_cents,
        max_installments=max_installments,
    )


def merge_credit_card_pricing(
    *,
    currency: str,
    base_amount_cents: int,
    merchant_pricing: PaymentPricingResponse,
    customer_pricing: PaymentPricingResponse,
    max_installments: int,
    max_installments_no_interest: int | None,
) -> PaymentPricingResponse:
    threshold = max(0, min(max_installments, int(max_installments_no_interest or 0)))
    merchant_map = {option.installments: option for option in merchant_pricing.options}
    customer_map = {option.installments: option for option in customer_pricing.options}
    merged: list[PaymentInstallmentOption] = []

    for installments in range(1, max(1, max_installments) + 1):
        preferred = merchant_map if installments <= threshold else customer_map
        fallback = customer_map if installments <= threshold else merchant_map
        option = preferred.get(installments) or fallback.get(installments)
        if option is None:
            total_amount_cents = base_amount_cents
            option = PaymentInstallmentOption(
                installments=installments,
                installment_amount_cents=int(round(total_amount_cents / installments)),
                total_amount_cents=total_amount_cents,
                has_interest=False,
            )
        merged.append(
            PaymentInstallmentOption(
                installments=option.installments,
                installment_amount_cents=option.installment_amount_cents,
                total_amount_cents=option.total_amount_cents,
                has_interest=option.total_amount_cents > base_amount_cents,
            )
        )

    return PaymentPricingResponse(
        payment_method="credit_card",
        currency=currency,
        base_amount_cents=base_amount_cents,
        options=merged,
    )
