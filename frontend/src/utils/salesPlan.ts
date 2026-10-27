// Contas do plano único usadas na página de vendas, na tela de planos e no Admin Master: quanto o
// trimestral ou o anual economiza frente às mensalidades, o valor por mês e "1 ano por menos de N
// meses do mensal".
export interface SalesPlanMath {
  /** As mensalidades do período (12 no anual, 3 no trimestral). */
  monthlyTotal: number;
  /** Quanto o período economiza frente às mensalidades. */
  savings: number;
  /** Economia em %, arredondada. */
  savingsPercent: number;
  /** Valor do período dividido pelos meses. */
  perMonth: number;
  /** O período custa menos que este número de mensalidades. */
  lessThanMonths: number;
}

export const salesPlanMath = (monthly?: number | string | null, period?: number | string | null, months = 12): SalesPlanMath | null => {
  const m = Number(monthly);
  const a = Number(period);
  if (!Number.isFinite(m) || !Number.isFinite(a) || m <= 0 || a <= 0 || months <= 1) return null;
  const monthlyTotal = m * months;
  const savings = Math.max(0, monthlyTotal - a);
  return {
    monthlyTotal,
    savings,
    savingsPercent: Math.round((savings / monthlyTotal) * 100),
    perMonth: a / months,
    lessThanMonths: Math.ceil(a / m - 1e-9),
  };
};

export const formatBRL = (value: number | string | null | undefined, { cents = "auto" }: { cents?: "auto" | "always" } = {}) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return "";
  const whole = Math.abs(n - Math.round(n)) < 0.005;
  const digits = cents === "always" || !whole ? 2 : 0;
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: digits, maximumFractionDigits: digits });
};
