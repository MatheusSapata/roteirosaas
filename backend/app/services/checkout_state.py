from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException

from app.models.sale import Sale


@dataclass(slots=True)
class CheckoutState:
    sale: Sale
    payment_method: str
    installments: int
    fee_mode: str
    allowed_payment_methods: list[str]

    @property
    def currency(self) -> str:
        return (self.sale.currency or "BRL").upper()

    @property
    def base_amount_cents(self) -> int:
        return int(self.sale.base_amount or self.sale.amount or 0)


def build_checkout_state(
    *,
    sale: Sale,
    payment_method: str,
    installments: int,
    fee_mode: str,
    allowed_payment_methods: list[str],
) -> CheckoutState:
    normalized_method = (payment_method or "").strip().lower() or "pix"
    if normalized_method not in {"pix", "credit_card", "boleto"}:
        raise HTTPException(status_code=400, detail="Forma de pagamento indisponivel para este produto.")
    if normalized_method not in set(allowed_payment_methods):
        raise HTTPException(status_code=400, detail="Forma de pagamento indisponivel para este produto.")
    normalized_installments = max(1, int(installments or 1))
    if normalized_method != "credit_card":
        normalized_installments = 1
    if normalized_installments > 12:
        raise HTTPException(status_code=400, detail="Parcelamento invalido.")
    if fee_mode not in {"absorb", "pass_through"}:
        fee_mode = "absorb"
    state = CheckoutState(
        sale=sale,
        payment_method=normalized_method,
        installments=normalized_installments,
        fee_mode=fee_mode,
        allowed_payment_methods=allowed_payment_methods,
    )
    if state.base_amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Valor da venda invalido.")
    return state
