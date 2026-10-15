export const planLabels: Record<string, string> = {
  free: "Começo",
  trial: "Trial",
  essencial: "Profissional",
  growth: "Agência",
  infinity: "Escala",
  teste: "Teste",
  profissional: "Profissional",
  professional: "Profissional",
  agencia: "Agência",
  agency: "Agência",
  escala: "Escala",
  scale: "Escala",
  test: "Teste"
};

export const getPlanLabel = (plan?: string | null): string => {
  if (!plan) return "Indefinido";
  const normalized = String(plan).trim().toLowerCase();
  return planLabels[normalized] || plan;
};

// Para o cliente, o plano à venda (interno: Escala) não tem nome: é a assinatura do Roteiro
// Online. Os planos antigos (Profissional e Agência) continuam com o nome deles.
const UNNAMED_PLANS = new Set(["infinity", "escala", "scale"]);

// Planos antigos com recursos a menos (Profissional e Agência). Quem está neles só vê o próprio
// plano: os avisos de recurso bloqueado não oferecem o plano novo.
const LEGACY_LIMITED_PLANS = new Set(["essencial", "profissional", "professional", "growth", "agencia", "agency"]);

export const isLegacyLimitedPlan = (plan?: string | null): boolean =>
  LEGACY_LIMITED_PLANS.has(String(plan || "").trim().toLowerCase());

export const getCustomerPlanLabel = (plan?: string | null): string => {
  const normalized = String(plan || "").trim().toLowerCase();
  if (UNNAMED_PLANS.has(normalized)) return "Roteiro Online";
  return getPlanLabel(plan);
};
