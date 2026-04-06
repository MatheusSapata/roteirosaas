import type { SectionType } from "../types/page";
import type { LocalizedString } from "./i18n";

export type HeadingStyle = "filled" | "outline";

const HEADING_DEFAULTS: Partial<Record<SectionType, { label: string; style: HeadingStyle }>> = {
  gallery: { label: "Galeria", style: "outline" },
  prices: { label: "Investimento", style: "outline" },
  products: { label: "Pacotes", style: "outline" },
  itinerary: { label: "Itinerário", style: "outline" },
  faq: { label: "FAQ", style: "outline" },
  story: { label: "Sobre nós", style: "outline" },
  reasons: { label: "Por que escolher", style: "outline" },
  testimonials: { label: "Depoimentos", style: "outline" },
  featured_video: { label: "Video em destaque", style: "outline" },
  cta: { label: "Convite", style: "outline" },
  countdown: { label: "Contagem regressiva", style: "outline" }
};

export const getSectionHeadingDefaults = (type: SectionType) => {
  return HEADING_DEFAULTS[type] || { label: "", style: "outline" };
};

export const resolveHeadingLabel = (
  label: LocalizedString,
  fallback: LocalizedString = "",
  localize: (value: LocalizedString) => string
): string => {
  if (label !== null && typeof label !== "undefined") {
    return localize(label).trim();
  }

  if (fallback === null || typeof fallback === "undefined") {
    return "";
  }

  if (typeof fallback === "string") {
    return fallback.trim();
  }

  return localize(fallback).trim();
};
