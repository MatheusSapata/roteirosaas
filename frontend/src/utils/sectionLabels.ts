import type { PageSection, SectionType } from "../types/page";

export const sectionLabels: Partial<Record<SectionType, string>> = {
  hero: "Banner",
  banner_card: "Banner em Card",
  photo: "Foto destacada",
  biography: "Biografia",
  prices: "Preços",
  products: "Produtos",
  itinerary: "Itinerário",
  faq: "Perguntas Frequentes",
  testimonials: "Depoimentos",
  featured_video: "Vídeo em destaque",
  cta: "Chamada para ação",
  story: "Descritivo",
  reasons: "Itens",
  countdown: "Contador",
  agency_footer: "Rodapé da agência",
  free_footer_brand: "Rodapé obrigatório",
  gallery: "Galeria"
};

export const describeSection = (section: PageSection): string => {
  switch (section.type) {
    case "hero":
    case "story":
    case "banner_card":
      return section.title || section.subtitle || "Sem título";
    case "testimonials":
      return section.title || "Depoimentos dos clientes";
    case "cta":
      return section.label || "Chamada principal";
    case "prices":
      return section.items?.[0]?.title || "Planos e valores";
    case "products":
      return section.title || "Produtos e pacotes";
    case "itinerary":
      return section.days?.[0]?.title || "Roteiro personalizado";
    case "reasons":
      return section.title || "Motivos para escolher";
    case "faq":
      return section.items?.[0]?.question || "Perguntas frequentes";
    case "countdown":
      return section.label || "Contagem regressiva";
    case "featured_video":
      return section.title || "Vídeo em destaque";
    case "gallery":
      return "Galeria de imagens";
    case "photo":
      return section.altText || "Imagem destacada";
    case "biography":
      return section.title || "Biografia";
    case "agency_footer":
      return "Rodapé institucional";
    case "free_footer_brand":
      return "Rodapé obrigatório";
    default:
      return "Seção";
  }
};
