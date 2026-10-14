"""Parcelas do cartão no checkout.

Mesma conta do Sistema Viajeon (src/lib/payments/asaas-fees.ts, assinatura da plataforma): o
acréscimo de cada parcela repassa ao cliente a taxa do cartão do Asaas ("Cobranças online") mais a
antecipação automática e os R$ 0,49 por cobrança, para o valor líquido ficar igual ao da venda.
À vista (1x) não tem acréscimo. Um valor fixo de parcela configurado na oferta (ex.: 12x de
R$ 97,00) vale no lugar da conta, mesmo que fique abaixo dela.

O valor de cada parcela é arredondado para centavos e o total é sempre parcela × quantidade:
o que aparece na tela é exatamente o que vai para o Asaas.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Mapping

MAX_INSTALLMENTS = 12

ASAAS_FIXED_FEE = Decimal("0.49")

# Antecipação automática do Asaas por número de parcelas (fração do valor), tabela oficial.
ANTICIPATION_FEE: dict[int, Decimal] = {
    1: Decimal("0.00847"),
    2: Decimal("0.02677"),
    3: Decimal("0.03552"),
    4: Decimal("0.0443"),
    5: Decimal("0.05309"),
    6: Decimal("0.06213"),
    7: Decimal("0.07051"),
    8: Decimal("0.07934"),
    9: Decimal("0.08811"),
    10: Decimal("0.09684"),
    11: Decimal("0.10569"),
    12: Decimal("0.11446"),
}

CENT = Decimal("0.01")


def card_fee(installments: int) -> Decimal:
    """Taxa do cartão do Asaas por faixa: à vista 2,99%, 2 a 6x 3,49%, 7 a 12x 3,99%."""
    if installments <= 1:
        return Decimal("0.0299")
    if installments <= 6:
        return Decimal("0.0349")
    return Decimal("0.0399")


def asaas_total_rate(installments: int) -> Decimal:
    n = min(max(int(installments), 1), MAX_INSTALLMENTS)
    return card_fee(n) + ANTICIPATION_FEE[n]


@dataclass(frozen=True)
class InstallmentOption:
    count: int
    value: Decimal
    total: Decimal
    no_interest: bool

    def as_dict(self) -> dict[str, Any]:
        return {"count": self.count, "value": self.value, "total": self.total, "no_interest": self.no_interest}


def normalize_fixed_values(raw: Mapping[Any, Any] | None) -> dict[int, Decimal]:
    """{"12": "97.00"} → {12: Decimal("97.00")}, só de 2 a 12 parcelas e valores positivos."""
    fixed: dict[int, Decimal] = {}
    for key, value in (raw or {}).items():
        try:
            count = int(str(key).strip())
            amount = Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
        except (ArithmeticError, ValueError):
            continue
        if 2 <= count <= MAX_INSTALLMENTS and amount > 0:
            fixed[count] = amount
    return fixed


def _computed_value(amount: Decimal, count: int) -> Decimal:
    rate = asaas_total_rate(count)
    gross = amount / (Decimal("1") - rate) + ASAAS_FIXED_FEE / (Decimal("1") - rate)
    return (gross / Decimal(count)).quantize(CENT, rounding=ROUND_HALF_UP)


def installment_options(
    amount: Decimal | str | float,
    max_installments: int,
    fixed_values: Mapping[Any, Any] | None = None,
) -> list[InstallmentOption]:
    """Parcelas de 1x até max_installments para o valor à vista `amount`."""
    base = Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)
    if base <= 0:
        return []
    top = min(max(int(max_installments or 1), 1), MAX_INSTALLMENTS)
    fixed = normalize_fixed_values(fixed_values)
    options = [InstallmentOption(count=1, value=base, total=base, no_interest=True)]
    for count in range(2, top + 1):
        value = fixed.get(count) or _computed_value(base, count)
        total = (value * count).quantize(CENT)
        options.append(InstallmentOption(count=count, value=value, total=total, no_interest=total <= base))
    return options


def option_for(options: list[InstallmentOption], count: int) -> InstallmentOption | None:
    return next((option for option in options if option.count == int(count)), None)
