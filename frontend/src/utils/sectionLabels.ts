import type { PageSection, SectionType } from "../types/page";

export const sectionLabels: Partial<Record<SectionType, string>> = {
  hero: "Banner",
  prices: "Preços",
  itinerary: "Itinerário",
  faq: "Perguntas Frequentes",
  testimonials: "Depoimentos",
  cta: "Chamada para ação",
  story: "Descritivo",
  reasons: "Itens",
  countdown: "Contador",
  free_footer_brand: "Rodapé obrigatório",
  gallery: "Galeria"
};

export const describeSection = (section: PageSection): string => {
  switch (section.type) {
    case "hero":
    case "story":
      return section.title || section.subtitle || "Sem título";
    case "testimonials":
      return section.title || "Depoimentos dos clientes";
    case "cta":
      return section.label || "Chamada principal";
    case "prices":
      return section.items?.[0]?.title || "Planos e valores";
    case "itinerary":
      return section.days?.[0]?.title || "Roteiro personalizado";
    case "reasons":
      return section.title || "Motivos para escolher";
    case "faq":
      return section.items?.[0]?.question || "Perguntas frequentes";
    case "countdown":
      return section.label || "Contagem regressiva";
    case "gallery":
      return "Galeria de imagens";
    case "free_footer_brand":
      return "Rodapé obrigatório";
    default:
      return "Seção";
  }
};
