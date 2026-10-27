"""Ciclos de cobrança da assinatura: mensal, trimestral e anual.

Um lugar só para o que muda com o ciclo (meses cobertos, dias de acesso por pagamento, códigos do
Asaas e próximo vencimento). Ciclo desconhecido ou vazio conta como mensal, como sempre foi.
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

BILLING_CYCLES = ("monthly", "quarterly", "annual")
CYCLE_LABELS = {"monthly": "Mensal", "quarterly": "Trimestral", "annual": "Anual"}

_MONTHS = {"monthly": 1, "quarterly": 3, "annual": 12}
# Acesso liberado por pagamento (o mensal sempre foi 30 dias e o anual, 365).
_DAYS = {"monthly": 30, "quarterly": 90, "annual": 365}
# Assinatura no cartão (campo "cycle") e autorização do Pix Automático (campo "frequency").
_ASAAS_CYCLE = {"monthly": "MONTHLY", "quarterly": "QUARTERLY", "annual": "YEARLY"}
_PIX_AUTOMATIC_FREQUENCY = {"monthly": "MONTHLY", "quarterly": "QUARTERLY", "annual": "ANNUALLY"}
_FROM_ASAAS_CYCLE = {value: key for key, value in _ASAAS_CYCLE.items()}


def normalize_cycle(cycle: Any) -> str:
    value = str(cycle or "").strip().lower()
    return value if value in _MONTHS else "monthly"


def cycle_months(cycle: Any) -> int:
    return _MONTHS[normalize_cycle(cycle)]


def cycle_duration(cycle: Any) -> timedelta:
    return timedelta(days=_DAYS[normalize_cycle(cycle)])


def asaas_cycle(cycle: Any) -> str:
    return _ASAAS_CYCLE[normalize_cycle(cycle)]


def pix_automatic_frequency(cycle: Any) -> str:
    return _PIX_AUTOMATIC_FREQUENCY[normalize_cycle(cycle)]


def cycle_from_asaas(value: Any) -> str | None:
    """Ciclo nosso a partir do "cycle" de uma assinatura do Asaas; None para os que não vendemos."""
    return _FROM_ASAAS_CYCLE.get(str(value or "").strip().upper())


def add_months(base: date, months: int) -> date:
    """Mesmo dia, N meses depois; sem esse dia no mês (31, 29/2), o último dia do mês."""
    index = base.month - 1 + months
    year = base.year + index // 12
    month = index % 12 + 1
    return date(year, month, min(base.day, calendar.monthrange(year, month)[1]))


def next_due_date(base: date, cycle: Any) -> date:
    return add_months(base, cycle_months(cycle))


def monthly_amount(amount: Decimal, cycle: Any) -> Decimal:
    """Valor por mês (MRR) de uma cobrança do ciclo."""
    return amount / Decimal(cycle_months(cycle))
