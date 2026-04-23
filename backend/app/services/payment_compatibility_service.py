from __future__ import annotations

from typing import Any

from fastapi import HTTPException

DEFAULT_ALLOWED_PAYMENT_METHODS = ["pix", "credit_card", "boleto"]
VALID_ALLOWED_PAYMENT_METHODS = set(DEFAULT_ALLOWED_PAYMENT_METHODS)


def normalize_allowed_payment_methods(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return list(DEFAULT_ALLOWED_PAYMENT_METHODS)
    normalized: list[str] = []
    seen: set[str] = set()
    for entry in raw:
        method = str(entry or "").strip().lower()
        if method not in VALID_ALLOWED_PAYMENT_METHODS:
            continue
        if method in seen:
            continue
        seen.add(method)
        normalized.append(method)
    return normalized or list(DEFAULT_ALLOWED_PAYMENT_METHODS)


def ensure_exact_compatibility(method_groups: list[list[str]]) -> list[str]:
    if not method_groups:
        return list(DEFAULT_ALLOWED_PAYMENT_METHODS)
    baseline = normalize_allowed_payment_methods(method_groups[0])
    baseline_set = set(baseline)
    for group in method_groups[1:]:
        current = normalize_allowed_payment_methods(group)
        if set(current) != baseline_set:
            raise HTTPException(
                status_code=400,
                detail="Os produtos selecionados possuem formas de pagamento incompativeis.",
            )
    return baseline
