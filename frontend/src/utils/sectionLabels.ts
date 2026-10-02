import type { PageSection, SectionType } from "../types/page";

export const sectionLabels: Partial<Record<SectionType, string>> = {
  header: "Cabeçalho",
  hero: "Banner",
  banner_card: "Banner em Card",
  photo: "Foto destacada",
  biography: "Biografia",
  prices: "Preços",
  itinerary: "Roteiro",
  faq: "Perguntas frequentes",
  testimonials: "Depoimentos",
  featured_video: "Vídeo em destaque",
  video_vsl: "Vídeo VSL",
  cta: "Chamada para ação",
  story: "Descritivo",
  reasons: "Itens",
  links: "Links",
  countdown: "Contador",
  agency_footer: "Rodapé da agência",
  flight_details: "Detalhes do voo",
  viajeon_checkout: "Checkout ViajeOn",
  internal_form: "Formulário interno",
  free_footer_brand: "Rodapé obrigatório",
  gallery: "Galeria"
};

export const describeSection = (section: PageSection): string => {
  switch (section.type) {
    case "header":
      return "Navegação principal";
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
    case "itinerary":
      return section.days?.[0]?.title || "Roteiro personalizado";
    case "reasons":
      return section.title || "Motivos para escolher";
    case "links":
      return section.title || "Links recomendados";
    case "faq":
      return section.items?.[0]?.question || "Perguntas frequentes";
    case "countdown":
      return section.label || "Contagem regressiva";
    case "featured_video":
      return section.title || "Vídeo em destaque";
    case "video_vsl":
      return section.title || "Vídeo VSL";
    case "gallery":
      return "Galeria de imagens";
    case "photo":
      return section.altText || "Imagem destacada";
    case "biography":
      return section.title || "Biografia";
    case "agency_footer":
      return "Rodapé institucional";
    case "flight_details":
      return section.title || "Informações de voo";
    case "viajeon_checkout":
      return section.title || section.checkoutName || "Checkout ViajeOn";
    case "internal_form":
      return section.title || "Formulário interno";
    case "free_footer_brand":
      return "Rodapé obrigatório";
    default:
      return "Seção";
  }
};
