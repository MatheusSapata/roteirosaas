from __future__ import annotations

from typing import Any, Iterable

import stripe
from fastapi import HTTPException

from app.core.config import get_settings

settings = get_settings()
stripe.api_version = "2023-10-16"


def _require_stripe() -> stripe:  # type: ignore[name-defined]
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=500, detail="Stripe n\u00e3o configurado.")
    if stripe.api_key != settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key
    stripe.max_network_retries = 2
    return stripe


def create_express_account(email: str | None = None) -> stripe.Account:  # type: ignore[name-defined]
    client = _require_stripe()
    try:
        return client.Account.create(
            type="express",
            country="BR",
            email=email,
            capabilities={
                "transfers": {"requested": True},
                "card_payments": {"requested": True},
            },
            business_type="individual",
        )
    except stripe.error.StripeError as exc:  # pragma: no cover - external API
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def create_account_link(account_id: str, refresh_url: str, return_url: str) -> stripe.AccountLink:  # type: ignore[name-defined]
    client = _require_stripe()
    try:
        return client.AccountLink.create(
            account=account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type="account_onboarding",
        )
    except stripe.error.StripeError as exc:  # pragma: no cover - external API
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def retrieve_account(account_id: str) -> stripe.Account:  # type: ignore[name-defined]
    client = _require_stripe()
    try:
        return client.Account.retrieve(account_id)
    except stripe.error.StripeError as exc:  # pragma: no cover - external API
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def create_payment_intent(
    *,
    amount: int,
    currency: str,
    stripe_account_id: str,
    application_fee_amount: int,
    metadata: dict[str, Any],
    customer_email: str | None = None,
    description: str | None = None,
    payment_method_types: Iterable[str] | None = None,
) -> stripe.PaymentIntent:  # type: ignore[name-defined]
    client = _require_stripe()
    payment_method_types = list(payment_method_types or ["card", "boleto", "pix"])
    automatic_methods = {"enabled": True, "allow_redirects": "never"}
    try:
        return client.PaymentIntent.create(
            amount=amount,
            currency=currency,
            application_fee_amount=application_fee_amount,
            transfer_data={"destination": stripe_account_id},
            metadata=metadata,
            description=description,
            receipt_email=customer_email,
            shipping=None,
            payment_method_types=payment_method_types,
            automatic_payment_methods=automatic_methods,
            customer=None,
            payment_method_options={
                "card": {
                    "installments": {"enabled": True},
                    "request_three_d_secure": "automatic",
                }
            },
        )
    except stripe.error.StripeError as exc:  # pragma: no cover - external API
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def retrieve_balance_transaction(
    balance_transaction_id: str,
    *,
    stripe_account: str | None = None,
) -> stripe.BalanceTransaction:  # type: ignore[name-defined]
    client = _require_stripe()
    try:
        return client.BalanceTransaction.retrieve(balance_transaction_id, stripe_account=stripe_account)
    except stripe.error.StripeError as exc:  # pragma: no cover - external API
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def iter_payout_transactions(
    payout_id: str,
    *,
    stripe_account: str,
) -> Iterable[stripe.BalanceTransaction]:  # type: ignore[name-defined]
    client = _require_stripe()
    try:
        transactions = client.BalanceTransaction.list(limit=100, payout=payout_id, stripe_account=stripe_account)
        return transactions.auto_paging_iter()
    except stripe.error.StripeError as exc:  # pragma: no cover - external API
        raise HTTPException(status_code=502, detail=str(exc)) from exc
