import type { SectionType } from "../types/page";

export type HeadingStyle = "filled" | "outline";

const HEADING_DEFAULTS: Partial<Record<SectionType, { label: string; style: HeadingStyle }>> = {
  gallery: { label: "Galeria", style: "outline" },
  prices: { label: "Investimento", style: "outline" },
  itinerary: { label: "Itinerário", style: "outline" },
  faq: { label: "FAQ", style: "outline" },
  story: { label: "Sobre nós", style: "outline" },
  reasons: { label: "Por que escolher", style: "outline" },
  testimonials: { label: "Depoimentos", style: "outline" },
  cta: { label: "Convite", style: "outline" },
  countdown: { label: "Contagem regressiva", style: "outline" }
};

export const getSectionHeadingDefaults = (type: SectionType) => {
  return HEADING_DEFAULTS[type] || { label: "", style: "outline" };
};
