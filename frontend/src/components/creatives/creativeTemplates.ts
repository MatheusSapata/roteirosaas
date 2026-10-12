export type CreativeCategory = "simple" | "complete" | "photos";

export interface CreativeTemplate {
  id: string;
  name: string;
  category: CreativeCategory;
  /** Quantas fotos o modelo usa. */
  photos: number;
  description: string;
}

export const CATEGORY_LABELS: Record<CreativeCategory, string> = {
  simple: "Simples",
  complete: "Completos",
  photos: "Com mais fotos"
};

export const CREATIVE_TEMPLATES: CreativeTemplate[] = [
  { id: "full-photo", name: "Foto cheia", category: "simple", photos: 1, description: "A foto de capa ocupa tudo, com título e preço por cima." },
  { id: "color-band", name: "Faixa colorida", category: "simple", photos: 1, description: "Foto em cima e uma faixa na cor de destaque com título, datas e preço." },
  { id: "frame", name: "Moldura", category: "simple", photos: 1, description: "Fundo na cor de destaque e a foto emoldurada no centro." },
  { id: "price-hero", name: "Preço em destaque", category: "simple", photos: 1, description: "O valor bem grande, para campanhas de oferta." },
  { id: "benefits", name: "Lista de benefícios", category: "complete", photos: 1, description: "Foto, o que está incluso, datas, preço e chamada para o WhatsApp." },
  { id: "card", name: "Cartão com tudo", category: "complete", photos: 1, description: "Um cartão sobre a foto com todas as informações da viagem." },
  { id: "collage-2", name: "Colagem de 2 fotos", category: "photos", photos: 2, description: "Duas fotos da viagem e uma faixa com título e preço." },
  { id: "mosaic-3", name: "Mosaico de 3 fotos", category: "photos", photos: 3, description: "Três fotos em mosaico, título, benefícios e preço." }
];
