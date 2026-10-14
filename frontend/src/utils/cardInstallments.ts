/**
 * Parcelas do cartão: mesma conta do servidor (backend/app/services/card_installments.py), usada só
 * para a prévia no Admin Master. O checkout e a página de vendas mostram o que o servidor calcula.
 *
 * O acréscimo repassa ao cliente a taxa do cartão do Asaas + a antecipação automática + R$ 0,49
 * (tabela do Sistema Viajeon). À vista não tem acréscimo; um valor fixo de parcela vale no lugar da conta.
 */
export const MAX_INSTALLMENTS = 12;

const ASAAS_FIXED_FEE = 0.49;

const ANTICIPATION_FEE: Record<number, number> = {
  1: 0.00847,
  2: 0.02677,
  3: 0.03552,
  4: 0.0443,
  5: 0.05309,
  6: 0.06213,
  7: 0.07051,
  8: 0.07934,
  9: 0.08811,
  10: 0.09684,
  11: 0.10569,
  12: 0.11446
};

const cardFee = (count: number) => (count <= 1 ? 0.0299 : count <= 6 ? 0.0349 : 0.0399);

const roundCents = (value: number) => Math.round((value + Number.EPSILON) * 100) / 100;

/** Valor da parcela pela tabela de repasse, sem valor fixo. */
export const computedInstallmentValue = (amount: number, count: number) => {
  if (count <= 1) return roundCents(amount);
  const rate = cardFee(count) + (ANTICIPATION_FEE[count] ?? ANTICIPATION_FEE[12]);
  return roundCents((amount / (1 - rate) + ASAAS_FIXED_FEE / (1 - rate)) / count);
};

export interface InstallmentPreview {
  count: number;
  value: number;
  total: number;
  fixed: boolean;
}

export const installmentPreview = (
  amount: number,
  maxInstallments: number,
  fixedValues: Record<string, string | number> = {}
): InstallmentPreview[] => {
  const top = Math.min(Math.max(Math.floor(maxInstallments || 1), 1), MAX_INSTALLMENTS);
  const rows: InstallmentPreview[] = [];
  for (let count = 1; count <= top; count++) {
    const fixedRaw = count > 1 ? Number(String(fixedValues[String(count)] ?? "").replace(",", ".")) : NaN;
    const fixed = Number.isFinite(fixedRaw) && fixedRaw > 0;
    const value = fixed ? roundCents(fixedRaw) : computedInstallmentValue(amount, count);
    rows.push({ count, value, total: roundCents(value * count), fixed });
  }
  return rows;
};
