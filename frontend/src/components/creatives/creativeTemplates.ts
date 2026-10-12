export type CreativeCategory = "simple" | "black" | "complete" | "photos";

export interface CreativeTemplate {
  id: string;
  name: string;
  category: CreativeCategory;
  /** Quantas fotos o modelo usa. */
  photos: number;
  description: string;
}

export const CATEGORY_LABELS: Record<CreativeCategory, string> = {
  simple: "Ofertas",
  black: "Black Friday",
  complete: "Completos",
  photos: "Com mais fotos"
};

/** Modelos em que a foto divide a arte com o conteúdo (aceitam "Tamanho da foto"). */
// (Lista, colagem e mosaico ficam de fora: neles a foto já ocupa tudo o que o conteúdo não usa.)
export const PHOTO_SPLIT_TEMPLATES = new Set(["oferta", "dividido", "destino", "campanha", "price-hero", "black-economia", "black-faixa", "card"]);

/** Modelos com a faixa diagonal da tag no canto (opcional). */
export const RIBBON_TEMPLATES = new Set(["dividido", "benefits", "card", "collage-2", "mosaic-3"]);

/** Modelos da campanha de Black Friday: sempre preto e amarelo. */
export const BLACK_TEMPLATES = new Set(["black-economia", "black-faixa"]);

/** Modelos no estilo das artes de agência: preço parcelado grande, incluso com ícones, selo de oferta. */
export const CREATIVE_TEMPLATES: CreativeTemplate[] = [
  { id: "oferta", name: "Oferta em bloco", category: "simple", photos: 1, description: "Bloco na cor da marca sobre a foto com destino, o que está incluso, preço parcelado e faixa de saída." },
  { id: "dividido", name: "Foto e dois blocos", category: "simple", photos: 1, description: "Foto em cima; embaixo o destino com ícones de um lado e o preço grande do outro." },
  { id: "vidro", name: "Cartão claro", category: "simple", photos: 1, description: "Foto inteira, cartão claro com destino e datas e o preço numa caixa na cor da marca." },
  { id: "destino", name: "Destino em destaque", category: "simple", photos: 1, description: "Nome do destino no alto, foto e base recortada com preço e contato." },
  { id: "manchete", name: "Manchete", category: "simple", photos: 1, description: "Destino enorme sobre a foto, data em tag, preço em caixa e o que inclui ao lado." },
  { id: "campanha", name: "Campanha com ícones", category: "simple", photos: 1, description: "Faixa de campanha com o destino, ícones do que está incluso e preço; foto embaixo." },
  { id: "price-hero", name: "Preço em destaque", category: "simple", photos: 1, description: "O valor bem grande e a foto num círculo, para campanhas de preço." },
  { id: "black-economia", name: "Black Friday economia", category: "black", photos: 1, description: "Preto e amarelo com fitas, destino enorme, De/Por, quanto economiza e selo estourado." },
  { id: "black-faixa", name: "Black Friday faixa", category: "black", photos: 1, description: "Foto com fitas, faixa amarela com o destino, cartão do pacote e caixa de preço preta." },
  { id: "benefits", name: "Lista do que inclui", category: "complete", photos: 1, description: "Foto, tudo o que está incluso com ícones, datas e preço." },
  { id: "card", name: "Cartão com tudo", category: "complete", photos: 1, description: "Um cartão sobre a foto com todas as informações da viagem." },
  { id: "collage-2", name: "Colagem de 2 fotos", category: "photos", photos: 2, description: "Duas fotos da viagem e uma faixa com destino e preço." },
  { id: "mosaic-3", name: "Mosaico de 3 fotos", category: "photos", photos: 3, description: "Três fotos em mosaico, destino, incluso e preço." }
];
