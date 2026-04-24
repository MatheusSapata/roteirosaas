import type { PageSection, SectionType } from "../types/page";

export const sectionLabels: Partial<Record<SectionType, string>> = {
  hero: "Banner",
  banner_card: "Banner em Card",
  photo: "Foto destacada",
  biography: "Biografia",
  prices: "Precos",
  itinerary: "Itinerario",
  faq: "Perguntas Frequentes",
  testimonials: "Depoimentos",
  featured_video: "Video em destaque",
  cta: "Chamada para acao",
  story: "Descritivo",
  reasons: "Itens",
  countdown: "Contador",
  agency_footer: "Rodape da agencia",
  flight_details: "Detalhes do voo",
  free_footer_brand: "Rodape obrigatorio",
  gallery: "Galeria"
};

export const describeSection = (section: PageSection): string => {
  switch (section.type) {
    case "hero":
    case "story":
    case "banner_card":
      return section.title || section.subtitle || "Sem titulo";
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
    case "featured_video":
      return section.title || "Video em destaque";
    case "gallery":
      return "Galeria de imagens";
    case "photo":
      return section.altText || "Imagem destacada";
    case "biography":
      return section.title || "Biografia";
    case "agency_footer":
      return "Rodape institucional";
    case "flight_details":
      return section.title || "Informacões de voo";
    case "free_footer_brand":
      return "Rodape obrigatorio";
    default:
      return "Secao";
  }
};
