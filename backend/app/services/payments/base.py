from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.models.sale import SalePaymentStatus


@dataclass(slots=True)
class PaymentQuoteRequest:
    base_amount: int
    currency: str = "BRL"
    installments: int = 1
    payment_method: str = "credit_card"


@dataclass(slots=True)
class PaymentQuote:
    base_amount: int
    gross_amount: int
    platform_fee_amount: int
    gateway_fee_estimated: int
    agency_net_amount: int
    spread_percentage_bps: int
    installment_amount: int
    installments: int
    payment_method: str
    currency: str


@dataclass(slots=True)
class PaymentChargeRequest(PaymentQuoteRequest):
    metadata: dict[str, str | int | None] | None = None


@dataclass(slots=True)
class PaymentCharge(PaymentQuote):
    provider: str
    provider_charge_id: str
    provider_status: SalePaymentStatus
    metadata: dict[str, str | int | None] | None = None


class PaymentProvider(Protocol):
    name: str

    def quote(self, request: PaymentQuoteRequest) -> PaymentQuote:
        ...

    def initialize_charge(self, request: PaymentChargeRequest) -> PaymentCharge:
        ...

    def update_status(self, charge: PaymentCharge, status: SalePaymentStatus) -> PaymentCharge:
        ...
