// Ciclos de cobrança da assinatura (mensal, trimestral e anual): nomes, períodos e meses usados na
// página de vendas, na tela de planos, no checkout e no Admin Master. As regras de cobrança ficam no
// servidor (app/services/billing_cycles.py); ciclo desconhecido conta como mensal, como lá.
export type BillingCycle = "monthly" | "quarterly" | "annual";

export const BILLING_CYCLES: BillingCycle[] = ["monthly", "quarterly", "annual"];

export const normalizeCycle = (value?: string | null): BillingCycle =>
  value === "quarterly" || value === "annual" ? value : "monthly";

const MONTHS: Record<BillingCycle, number> = { monthly: 1, quarterly: 3, annual: 12 };
const DAYS: Record<BillingCycle, number> = { monthly: 30, quarterly: 90, annual: 365 };

export const cycleMonths = (cycle?: string | null) => MONTHS[normalizeCycle(cycle)];
export const cycleDays = (cycle?: string | null) => DAYS[normalizeCycle(cycle)];

type Localized = { pt: string; es: string };

/** "Mensal", "Trimestral", "Anual". */
export const CYCLE_LABELS: Record<BillingCycle, Localized> = {
  monthly: { pt: "Mensal", es: "Mensual" },
  quarterly: { pt: "Trimestral", es: "Trimestral" },
  annual: { pt: "Anual", es: "Anual" }
};
/** Período de cada cobrança: "mês", "trimestre", "ano" (para "/mês" e "o ano inteiro"). */
export const CYCLE_PERIODS: Record<BillingCycle, Localized> = {
  monthly: { pt: "mês", es: "mes" },
  quarterly: { pt: "trimestre", es: "trimestre" },
  annual: { pt: "ano", es: "año" }
};
/** Duração de um ciclo: "1 mês", "3 meses", "1 ano" (para "1 ano por menos de 8 meses do mensal"). */
export const CYCLE_SPANS: Record<BillingCycle, Localized> = {
  monthly: { pt: "1 mês", es: "1 mes" },
  quarterly: { pt: "3 meses", es: "3 meses" },
  annual: { pt: "1 ano", es: "1 año" }
};

export const cycleLabel = (cycle?: string | null) => CYCLE_LABELS[normalizeCycle(cycle)].pt;
export const cyclePeriod = (cycle?: string | null) => CYCLE_PERIODS[normalizeCycle(cycle)].pt;
export const cycleSpan = (cycle?: string | null) => CYCLE_SPANS[normalizeCycle(cycle)].pt;

/** "Mensal ou trimestral", "Mensal, trimestral ou anual". */
export const joinCycleLabels = (cycles: BillingCycle[], language: "pt" | "es" = "pt") => {
  const names = cycles.map((cycle, index) => {
    const name = CYCLE_LABELS[cycle][language];
    return index === 0 ? name : name.toLowerCase();
  });
  const or = language === "es" ? " o " : " ou ";
  return names.length > 1 ? `${names.slice(0, -1).join(", ")}${or}${names[names.length - 1]}` : names[0] || "";
};
