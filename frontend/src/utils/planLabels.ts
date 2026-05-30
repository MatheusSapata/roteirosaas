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
