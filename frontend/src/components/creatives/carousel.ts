import type { CreativeData, CreativeFormat } from "./creativeData";

/** Um slide do carrossel; o conteúdo vem do CreativeData (editável na tela). */
export type CarouselStyle = "photo" | "pages" | "sections";
export const CAROUSEL_STYLES: Record<CarouselStyle, { label: string; hint: string }> = {
  photo: { label: "Foto inteira", hint: "Cada slide com uma foto grande e o texto embaixo." },
  pages: { label: "Roteiro em páginas", hint: "Páginas na cor da marca e brancas, linha do tempo e resumo com pacotes." },
  sections: { label: "Seções da página", hint: "Cada slide é uma seção da sua página, igual ao site, adaptada ao post." }
};

export type CarouselSlide =
  | { kind: "cover" }
  | { kind: "intro" }
  | { kind: "details" }
  | { kind: "section"; sectionIndex: number; label: string }
  | { kind: "itinerary"; from: number; to: number; part: number; parts: number }
  | { kind: "included" }
  | { kind: "flights" }
  | { kind: "prices" }
  | { kind: "final" };

export const SLIDE_LABELS: Record<CarouselSlide["kind"], string> = {
  cover: "Capa",
  intro: "Apresentação",
  details: "Detalhes da viagem",
  section: "Seção",
  itinerary: "Roteiro",
  included: "O que está incluso",
  flights: "Voos",
  prices: "Valores",
  final: "Chamada final"
};

/** Quantos dias do roteiro cabem em um slide (com a descrição de cada dia). */
export const daysPerSlide = (format: CreativeFormat) => (format === "story" ? 6 : format === "square" ? 3 : 4);
export const pricesPerSlide = (format: CreativeFormat) => (format === "story" ? 6 : format === "square" ? 3 : 4);

/** Capa → roteiro (em partes) → incluso → voos → valores → chamada final; só entra o que a página tem. */
export const buildCarousel = (data: CreativeData, format: CreativeFormat, style: CarouselStyle = "photo"): CarouselSlide[] => {
  if (style === "pages") return buildPages(data, format);
  const slides: CarouselSlide[] = [{ kind: "cover" }];
  const per = daysPerSlide(format);
  const parts = Math.ceil(data.itinerary.length / per);
  for (let part = 0; part < parts; part += 1) {
    slides.push({ kind: "itinerary", from: part * per, to: Math.min(data.itinerary.length, (part + 1) * per), part: part + 1, parts });
  }
  if (data.benefits.some(Boolean)) slides.push({ kind: "included" });
  if (data.flights.length) slides.push({ kind: "flights" });
  if (data.prices.length) slides.push({ kind: "prices" });
  slides.push({ kind: "final" });
  return slides;
};

/** Roteiro em páginas: capa → apresentação → cronograma (em partes) → detalhes → "vamos nessa?" com os pacotes. */
const buildPages = (data: CreativeData, format: CreativeFormat): CarouselSlide[] => {
  const slides: CarouselSlide[] = [{ kind: "cover" }];
  if (data.subtitle) slides.push({ kind: "intro" });
  const per = format === "story" ? 4 : format === "square" ? 2 : 3;
  const parts = Math.ceil(data.itinerary.length / per);
  for (let part = 0; part < parts; part += 1) {
    slides.push({ kind: "itinerary", from: part * per, to: Math.min(data.itinerary.length, (part + 1) * per), part: part + 1, parts });
  }
  if (data.benefits.some(Boolean) || data.flights.length) slides.push({ kind: "details" });
  slides.push({ kind: "final" });
  return slides;
};
