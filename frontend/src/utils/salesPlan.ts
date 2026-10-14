// Contas do plano único (assinatura mensal e anual) usadas na página de vendas, na tela de
// planos e no Admin Master: economia do anual, valor por mês e "1 ano por menos de N meses".
export interface SalesPlanMath {
  /** 12 mensalidades. */
  twelveMonths: number;
  /** Quanto o anual economiza frente a 12 mensalidades. */
  savings: number;
  /** Economia em %, arredondada. */
  savingsPercent: number;
  /** Valor do anual dividido por 12. */
  perMonth: number;
  /** O anual custa menos que este número de mensalidades. */
  lessThanMonths: number;
}

export const salesPlanMath = (monthly?: number | string | null, annual?: number | string | null): SalesPlanMath | null => {
  const m = Number(monthly);
  const a = Number(annual);
  if (!Number.isFinite(m) || !Number.isFinite(a) || m <= 0 || a <= 0) return null;
  const twelveMonths = m * 12;
  const savings = Math.max(0, twelveMonths - a);
  return {
    twelveMonths,
    savings,
    savingsPercent: Math.round((savings / twelveMonths) * 100),
    perMonth: a / 12,
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
