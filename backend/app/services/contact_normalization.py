from __future__ import annotations

import re


def normalize_cpf(value: str | None) -> str | None:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 11:
        return None
    return digits


def normalize_phone(value: str | None) -> str | None:
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return None
    return digits


def normalize_email(value: str | None) -> str | None:
    cleaned = (value or "").strip().lower()
    return cleaned or None
