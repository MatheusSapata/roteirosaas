from __future__ import annotations

import uuid
from dataclasses import asdict, replace
from decimal import Decimal, ROUND_HALF_UP

from app.models.sale import SalePaymentStatus

from .base import PaymentCharge, PaymentChargeRequest, PaymentProvider, PaymentQuote, PaymentQuoteRequest


class SimulatedBlimbooProvider(PaymentProvider):
    """
    Provider simulado que aplica a l�gica descrita na diretriz principal.
    Todos os valores utilizam centavos para evitar erros de ponto flutuante.
    """

    name = "blimboo"
    platform_margin_pct = Decimal("0.03")  # 3%
    gateway_fee_pct = Decimal("0.13")  # 13%
    installment_factor_step = Decimal("0.02")
    max_installments_supported = 12

    def _installment_factor(self, installments: int) -> Decimal:
        count = max(1, min(installments, self.max_installments_supported))
        if count == 1:
            return Decimal("1")
        # Aplica um fator incremental de 2% a cada parcela adicional
        return Decimal("1") + (Decimal(count - 1) * self.installment_factor_step)

    @staticmethod
    def _quantize(value: Decimal) -> Decimal:
        return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    def quote(self, request: PaymentQuoteRequest) -> PaymentQuote:
        if request.base_amount <= 0:
            raise ValueError("Valor base deve ser positivo.")
        base = Decimal(request.base_amount)
        platform_fee = self._quantize(base * self.platform_margin_pct)
        total_after_margin = base + platform_fee
        gateway_divisor = Decimal("1") - self.gateway_fee_pct
        total_base = total_after_margin / gateway_divisor
        gateway_fee = self._quantize(total_base - total_after_margin)
        factor = self._installment_factor(request.installments)
        gross = self._quantize(total_base * factor)
        installment_amount = self._quantize(gross / Decimal(max(1, request.installments)))
        agency_net = gross - platform_fee - gateway_fee
        spread_ratio = Decimal("0")
        if base > 0:
            spread_ratio = (gross - base) / base
        spread_percentage_bps = int(self._quantize(spread_ratio * Decimal("10000")))
        return PaymentQuote(
            base_amount=int(base),
            gross_amount=int(gross),
            platform_fee_amount=int(platform_fee),
            gateway_fee_estimated=int(gateway_fee),
            agency_net_amount=int(agency_net),
            spread_percentage_bps=max(spread_percentage_bps, 0),
            installment_amount=int(installment_amount),
            installments=max(1, request.installments),
            payment_method=request.payment_method,
            currency=request.currency.lower(),
        )

    def initialize_charge(self, request: PaymentChargeRequest) -> PaymentCharge:
        quote = self.quote(request)
        return PaymentCharge(
            **asdict(quote),
            provider=self.name,
            provider_charge_id=uuid.uuid4().hex,
            provider_status=SalePaymentStatus.pending,
            metadata=request.metadata or {},
        )

    def update_status(self, charge: PaymentCharge, status: SalePaymentStatus) -> PaymentCharge:
        return replace(charge, provider_status=status)


provider = SimulatedBlimbooProvider()
