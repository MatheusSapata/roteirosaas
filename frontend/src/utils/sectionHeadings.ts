import type { SectionType } from "../types/page";
import type { LocalizedString } from "./i18n";

export type HeadingStyle = "filled" | "outline";

const HEADING_DEFAULTS: Partial<Record<SectionType, { label: string; style: HeadingStyle }>> = {
  gallery: { label: "Galeria", style: "outline" },
  prices: { label: "Investimento", style: "outline" },
  itinerary: { label: "Itinerário", style: "outline" },
  faq: { label: "FAQ", style: "outline" },
  story: { label: "Sobre nós", style: "outline" },
  reasons: { label: "Por que escolher", style: "outline" },
  links: { label: "Links", style: "outline" },
  testimonials: { label: "Depoimentos", style: "outline" },
  featured_video: { label: "Video em destaque", style: "outline" },
  video_vsl: { label: "Video VSL", style: "outline" },
  cta: { label: "Convite", style: "outline" },
  countdown: { label: "Contagem regressiva", style: "outline" },
  flight_details: { label: "Detalhes do voo", style: "outline" },
  internal_form: { label: "Fale conosco", style: "outline" }
};

export type HeadingAlign = "left" | "center";

/** Seções do visual novo em que dá para escolher o alinhamento do título e do texto, com o padrão de cada uma. */
const HEADING_ALIGN_DEFAULTS: Partial<Record<SectionType, HeadingAlign>> = {
  faq: "center",
  featured_video: "center",
  gallery: "center",
  itinerary: "center",
  links: "left",
  prices: "center",
  reasons: "center",
  testimonials: "center"
};

export const supportsHeadingAlign = (type?: SectionType) => !!type && type in HEADING_ALIGN_DEFAULTS;

/**
 * Seções em que os itens (ícone, título e texto de cada card) seguem o mesmo
 * alinhamento do cabeçalho. Um controle só por seção, igual no computador e no celular.
 */
const ITEMS_FOLLOW_ALIGN: Partial<Record<SectionType, true>> = { reasons: true };

export const alignAppliesToItems = (type?: SectionType) => !!type && !!ITEMS_FOLLOW_ALIGN[type];

export const resolveHeadingAlign = (type: SectionType, saved?: string | null): HeadingAlign =>
  saved === "left" || saved === "center" ? saved : HEADING_ALIGN_DEFAULTS[type] || "center";

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
