from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from app.services.payments.blimboo_api import BlimbooAPIClient, BlimbooAPIError

BLIMBOO_CURRENCY_MAP = {"BRL": 1}
PAYMENT_METHOD_TO_BLIMBOO = {
    "credit_card": 2,
    "pix": 3,
    "boleto": 1,
}


@dataclass(slots=True)
class ChargeCardInput:
    holder_name: str
    number: str
    exp_month: int
    exp_year: int
    cvv: str


@dataclass(slots=True)
class ChargeCustomerInput:
    name: str
    email: str
    phone_number: str
    nationality: str
    passport: str


@dataclass(slots=True)
class ChargeBuildInput:
    payment_method: str
    installments: int
    currency: str
    amount_cents: int
    description: str
    customer: ChargeCustomerInput
    order_id: str
    metadata: dict[str, Any]
    card: ChargeCardInput | None = None


def _required(value: str | None, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"Campo obrigatorio ausente: {field}.")
    return text


def _normalize_nationality(value: str) -> int:
    normalized = str(value or "").strip().upper()
    if normalized in {"1", "BR", "BRA", "BRASIL"}:
        return 1
    if normalized in {"2", "OTHER", "OUTROS", "OUTRO"}:
        return 2
    try:
        as_int = int(normalized)
        return 1 if as_int == 1 else 2
    except Exception:
        return 2


def _infer_card_brand(number: str) -> str:
    digits = "".join(ch for ch in str(number or "") if ch.isdigit())
    if digits.startswith("4"):
        return "visa"
    if digits[:2] in {"34", "37"}:
        return "amex"
    if len(digits) >= 2 and 51 <= int(digits[:2]) <= 55:
        return "mastercard"
    if digits.startswith("606282"):
        return "hipercard"
    if digits.startswith("4011") or digits.startswith("4312") or digits.startswith("4389") or digits.startswith("4514"):
        return "elo"
    return "visa"


def validate_customer_input(customer: ChargeCustomerInput) -> None:
    _required(customer.name, "name")
    _required(customer.email, "email")
    _required(customer.phone_number, "phone_number")
    _required(customer.nationality, "nationality")
    _required(customer.passport, "passport")


def validate_method_input(payload: ChargeBuildInput) -> None:
    method = (payload.payment_method or "").strip().lower()
    if method not in PAYMENT_METHOD_TO_BLIMBOO:
        raise HTTPException(status_code=400, detail="Forma de pagamento indisponivel para este produto.")
    if payload.amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Valor da venda invalido.")
    if method == "credit_card":
        if not payload.card:
            raise HTTPException(status_code=400, detail="Dados de cartao obrigatorios para pagamento no cartao.")
        _required(payload.card.holder_name, "card_holder_name")
        _required(payload.card.number, "card_number")
        _required(payload.card.cvv, "card_cvv")
        if payload.card.exp_month < 1 or payload.card.exp_month > 12:
            raise HTTPException(status_code=400, detail="Mes de validade do cartao invalido.")
        if payload.card.exp_year < 2000:
            raise HTTPException(status_code=400, detail="Ano de validade do cartao invalido.")
        if payload.installments < 1:
            raise HTTPException(status_code=400, detail="Parcelamento invalido.")


def build_charge_payload(payload: ChargeBuildInput) -> dict[str, Any]:
    validate_customer_input(payload.customer)
    validate_method_input(payload)

    currency = (payload.currency or "BRL").upper()
    currency_code = BLIMBOO_CURRENCY_MAP.get(currency)
    if currency_code is None:
        raise HTTPException(status_code=400, detail="Moeda nao suportada para cobranca.")

    method = PAYMENT_METHOD_TO_BLIMBOO[payload.payment_method]
    customer_nationality = _normalize_nationality(payload.customer.nationality)
    customer_ssn = payload.customer.passport.strip()
    request_payload: dict[str, Any] = {
        "customer": {
            "name": payload.customer.name.strip(),
            "email": payload.customer.email.strip(),
            "phone_number": payload.customer.phone_number.strip(),
            # Formato oficial da Blimboo: nationality numerico e documento em ssn.
            "nationality": customer_nationality,
            "ssn": customer_ssn,
            # Mantemos passport por compatibilidade retroativa de ambientes antigos.
            "passport": customer_ssn,
        },
        "charge": {
            "method": method,
            "installments": max(1, int(payload.installments or 1)),
            "description": payload.description.strip() or "Cobranca",
            "currency": currency_code,
            "cycle": 0,
            "amount": round(payload.amount_cents / 100, 2),
        },
        "metadata": {
            **payload.metadata,
            "order_id": payload.order_id,
            "payment_method": payload.payment_method,
        },
    }
    if payload.payment_method == "credit_card" and payload.card:
        exp_month_text = str(payload.card.exp_month).zfill(2)
        exp_year_text = str(payload.card.exp_year)[-2:]
        customer_card = {
            "brand": _infer_card_brand(payload.card.number),
            "holder": payload.card.holder_name.strip(),
            "number": payload.card.number.strip(),
            "expiration_month": exp_month_text,
            "expiration_year": exp_year_text,
            "cvv": payload.card.cvv.strip(),
        }
        # Formato esperado pelo exemplo oficial.
        request_payload["customer"]["card"] = customer_card
        # Compatibilidade com payload legado que usa charge.card.
        request_payload["charge"]["card"] = {
            "holder_name": payload.card.holder_name.strip(),
            "number": payload.card.number.strip(),
            "exp_month": payload.card.exp_month,
            "exp_year": payload.card.exp_year,
            "cvv": payload.card.cvv.strip(),
        }
    return request_payload


def create_blimboo_charge(client: BlimbooAPIClient, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = client.create_charge(payload)
    except BlimbooAPIError as exc:
        raw = str(exc)
        if "The given data was invalid" in raw:
            raise HTTPException(status_code=400, detail=f"Revise os dados obrigatorios do pagamento. {raw}") from exc
        raise HTTPException(status_code=502, detail="Nao foi possivel iniciar a cobranca.") from exc
    if isinstance(response, dict):
        # Mantem payload completo para nao perder campos de boleto/pix que
        # podem vir fora de "data" em algumas variacoes da API.
        return response
    return {}
