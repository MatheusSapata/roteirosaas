export const planLabels: Record<string, string> = {
  free: "Começo",
  essencial: "Profissional",
  growth: "Agência",
  infinity: "Escala",
  teste: "Teste"
};

export const getPlanLabel = (plan?: string | null): string => {
  if (!plan) return "Indefinido";
  return planLabels[plan] || plan;
};
