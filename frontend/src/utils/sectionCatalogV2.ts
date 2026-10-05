import type { SectionType } from "../types/page";
import { createLocalizer, getCurrentLanguage } from "./i18n";

const t = createLocalizer(getCurrentLanguage());

/** Categorias do seletor de seções do editor novo, na ordem em que aparecem. */
export const SECTION_CATEGORIES_V2 = [
  { id: "topo", label: t({ pt: "Topo", es: "Inicio" }), hint: t({ pt: "Abertura da página: capa ou vídeo", es: "Apertura de la página: portada o video" }) },
  { id: "apresentacao", label: t({ pt: "Apresentação", es: "Presentación" }), hint: t({ pt: "Conte o que é a viagem", es: "Cuenta de qué se trata el viaje" }) },
  { id: "roteiro", label: t({ pt: "Roteiro e mídia", es: "Itinerario y medios" }), hint: t({ pt: "Dias, fotos e voos", es: "Días, fotos y vuelos" }) },
  { id: "oferta", label: t({ pt: "Oferta", es: "Oferta" }), hint: t({ pt: "Preço, compra e urgência", es: "Precio, compra y urgencia" }) },
  { id: "confianca", label: t({ pt: "Confiança", es: "Confianza" }), hint: t({ pt: "Quem garante a viagem", es: "Quién respalda el viaje" }) },
  { id: "contato", label: t({ pt: "Contato", es: "Contacto" }), hint: t({ pt: "Captar e tirar dúvidas", es: "Captar y resolver dudas" }) },
  { id: "fechamento", label: t({ pt: "Fechamento", es: "Cierre" }), hint: t({ pt: "Fim da página", es: "Final de la página" }) }
] as const;

export type SectionCategoryV2 = (typeof SECTION_CATEGORIES_V2)[number]["id"];

/** Bloco da miniatura, em % da área: retângulo de cor ou "foto" (degradê). */
export interface ThumbBlock {
  x: number;
  y: number;
  w: number;
  h: number;
  c?: string;
  photo?: PhotoKey;
  r?: number;
}

type PhotoKey = "lago" | "serra" | "vale" | "estrada" | "mar" | "praia";

/** Degradês no lugar de fotos reais, para a miniatura sugerir uma imagem sem carregar nada. */
export const THUMB_PHOTOS: Record<PhotoKey, string> = {
  lago: "linear-gradient(170deg, #9fd3e6 0%, #6aa7c0 38%, #2f6f78 62%, #1d4a43 100%)",
  serra: "linear-gradient(165deg, #f4c48d 0%, #c98a6a 35%, #6d6a7c 62%, #33404a 100%)",
  vale: "linear-gradient(175deg, #c9e3f0 0%, #8fbf9a 45%, #4f8a5a 70%, #2e5a3a 100%)",
  estrada: "linear-gradient(170deg, #f6d8a8 0%, #e3a86a 40%, #8a6a52 70%, #3f3a36 100%)",
  mar: "linear-gradient(180deg, #bfe6f5 0%, #6cc4dd 45%, #1f8aa6 70%, #0f5a74 100%)",
  praia: "linear-gradient(180deg, #a9dcef 0%, #7cc6df 45%, #f1dcae 72%, #e2c48c 100%)"
};

export interface SectionCatalogItemV2 {
  type: SectionType;
  cat: SectionCategoryV2;
  label: string;
  /** Palavras extras para a busca (nomes antigos, sinônimos). */
  keywords: string;
  desc: string;
  page: string;
  blocks: ThumbBlock[];
}

const A = "var(--thumb-accent, #12B981)";
const D = "#0F1713";
const L = "#DCE1DA";
const W = "#FFFFFF";
const S = "#F1F4F0";
const G = "rgba(255,255,255,0.55)";
const DIM = "rgba(255,255,255,0.35)";

const R = (x: number, y: number, w: number, h: number, c: string, r = 3): ThumbBlock => ({ x, y, w, h, c, r });
const P = (x: number, y: number, w: number, h: number, photo: PhotoKey, r = 0): ThumbBlock => ({ x, y, w, h, photo, r });
const head = (y: number) => [R(40, y, 20, 5, A, 8), R(25, y + 8, 50, 7, D), R(32, y + 18, 36, 4, L)];

export const SECTION_CATALOG_V2: SectionCatalogItemV2[] = [
  {
    type: "header", cat: "topo", label: t({ pt: "Menu do topo", es: "Menú superior" }), keywords: "cabeçalho cabecalho header menu",
    desc: t({ pt: "Logo, links para as seções e botão de contato.", es: "Logo, enlaces a las secciones y botón de contacto." }), page: W,
    blocks: [P(0, 22, 100, 78, "lago"), R(0, 0, 100, 22, W, 0), R(5, 8, 16, 6, D), R(36, 9, 9, 4, L), R(49, 9, 9, 4, L), R(62, 9, 9, 4, L), R(78, 6, 17, 10, A, 9)]
  },
  {
    type: "hero", cat: "topo", label: t({ pt: "Capa da viagem", es: "Portada del viaje" }), keywords: "banner hero capa",
    desc: t({ pt: "Foto grande, título, datas e o botão principal.", es: "Foto grande, título, fechas y el botón principal." }), page: W,
    blocks: [P(0, 0, 100, 100, "lago"), R(0, 50, 100, 50, "rgba(11,20,16,0.78)", 0), R(6, 46, 13, 6, G, 8), R(21, 46, 13, 6, G, 8), R(36, 46, 13, 6, G, 8), R(6, 57, 62, 8, W), R(6, 67, 42, 8, W), R(6, 81, 26, 11, W, 5), R(35, 81, 18, 11, A, 9)]
  },
  {
    type: "banner_card", cat: "topo", label: t({ pt: "Capa com card", es: "Portada con tarjeta" }), keywords: "banner em card",
    desc: t({ pt: "Foto de fundo com um card de texto por cima.", es: "Foto de fondo con una tarjeta de texto encima." }), page: W,
    blocks: [P(0, 0, 100, 100, "serra"), R(8, 18, 48, 66, W, 7), R(13, 26, 20, 5, A, 8), R(13, 36, 38, 7, D), R(13, 46, 30, 4, L), R(13, 53, 34, 4, L), R(13, 66, 20, 10, A, 9)]
  },
  {
    type: "video_vsl", cat: "topo", label: t({ pt: "Vídeo de vendas", es: "Video de ventas" }), keywords: "vsl video",
    desc: t({ pt: "Vídeo com chamada e botão logo abaixo.", es: "Video con llamada y botón debajo." }), page: "#0E1A15",
    blocks: [R(20, 8, 60, 7, W), R(30, 18, 40, 4, "rgba(255,255,255,0.4)"), P(16, 28, 68, 48, "praia", 6), R(44, 45, 12, 16, W, 30), R(34, 82, 32, 10, A, 9)]
  },
  {
    type: "story", cat: "apresentacao", label: t({ pt: "Sobre a viagem", es: "Sobre el viaje" }), keywords: "descritivo historia texto",
    desc: t({ pt: "Texto com carrossel de até 10 fotos.", es: "Texto con carrusel de hasta 10 fotos." }), page: W,
    blocks: [R(6, 18, 16, 5, A, 8), R(6, 28, 38, 7, D), R(6, 39, 40, 4, L), R(6, 46, 36, 4, L), R(6, 53, 38, 4, L), R(6, 64, 18, 10, A, 9), P(52, 10, 42, 58, "vale", 6), P(52, 73, 9, 12, "lago", 3), P(63, 73, 9, 12, "serra", 3), P(74, 73, 9, 12, "mar", 3), P(85, 73, 9, 12, "estrada", 3)]
  },
  {
    type: "reasons", cat: "apresentacao", label: t({ pt: "Diferenciais", es: "Diferenciales" }), keywords: "itens motivos vantagens",
    desc: t({ pt: "Cards com ícone, título e texto curto.", es: "Tarjetas con ícono, título y texto corto." }), page: "#F2F4F1",
    blocks: head(10).concat([R(6, 42, 20, 48, W, 6), R(29, 42, 20, 48, W, 6), R(52, 42, 20, 48, W, 6), R(75, 42, 19, 48, W, 6), R(9, 47, 7, 11, A, 3), R(32, 47, 7, 11, A, 3), R(55, 47, 7, 11, A, 3), R(78, 47, 7, 11, A, 3), R(9, 64, 13, 4, D), R(32, 64, 13, 4, D), R(55, 64, 13, 4, D), R(78, 64, 13, 4, D)])
  },
  {
    type: "photo", cat: "apresentacao", label: t({ pt: "Foto em destaque", es: "Foto destacada" }), keywords: "foto destacada imagem",
    desc: t({ pt: "Uma imagem grande com legenda.", es: "Una imagen grande con leyenda." }), page: W,
    blocks: [P(6, 10, 88, 70, "mar", 6), R(30, 86, 40, 4, L)]
  },
  {
    type: "biography", cat: "apresentacao", label: t({ pt: "Artigo", es: "Artículo" }), keywords: "biografia blog texto post",
    desc: t({ pt: "Imagem de capa com título e texto formatado, como um post.", es: "Imagen de portada con título y texto con formato, como un post." }), page: W,
    blocks: [P(0, 0, 100, 44, "serra"), R(0, 0, 100, 44, "rgba(6,12,9,0.45)", 0), R(22, 16, 56, 7, W), R(32, 26, 36, 7, W), R(24, 54, 52, 5, D), R(24, 63, 48, 4, L), R(24, 70, 52, 4, L), R(24, 77, 44, 4, L), R(24, 87, 30, 5, D)]
  },
  {
    type: "featured_video", cat: "apresentacao", label: t({ pt: "Vídeo", es: "Video" }), keywords: "video em destaque youtube vimeo",
    desc: t({ pt: "Vídeo do YouTube ou Vimeo com título.", es: "Video de YouTube o Vimeo con título." }), page: W,
    blocks: head(6).concat([P(14, 34, 72, 60, "estrada", 6), R(44, 52, 12, 20, W, 30), R(48, 58, 5, 8, A, 2)])
  },
  {
    type: "itinerary", cat: "roteiro", label: t({ pt: "Roteiro dia a dia", es: "Itinerario día a día" }), keywords: "roteiro itinerario dias",
    desc: t({ pt: "Linha do tempo com data e foto de cada dia.", es: "Línea de tiempo con fecha y foto de cada día." }), page: W,
    blocks: [R(30, 8, 40, 7, D), R(12, 24, 9, 16, A, 4), R(25, 24, 63, 16, S, 5), R(28, 29, 38, 5, D), P(76, 26, 10, 12, "vale", 3), R(16, 41, 1, 7, L, 0), R(12, 48, 9, 16, W, 4), R(25, 48, 63, 16, S, 5), R(28, 54, 34, 5, D), R(16, 65, 1, 7, L, 0), R(12, 72, 9, 16, W, 4), R(25, 72, 63, 16, S, 5), R(28, 78, 30, 5, D)]
  },
  {
    type: "gallery", cat: "roteiro", label: t({ pt: "Galeria de fotos", es: "Galería de fotos" }), keywords: "galeria fotos carrossel mosaico",
    desc: t({ pt: "Carrossel, mosaico ou grade de fotos.", es: "Carrusel, mosaico o cuadrícula de fotos." }), page: W,
    blocks: head(6).concat([P(5, 36, 29, 46, "lago", 5), P(36, 36, 29, 46, "vale", 5), P(67, 36, 29, 46, "serra", 5), R(40, 88, 7, 3, A, 4), R(49, 88, 3, 3, L, 4), R(54, 88, 3, 3, L, 4)])
  },
  {
    type: "flight_details", cat: "roteiro", label: t({ pt: "Voos", es: "Vuelos" }), keywords: "detalhes do voo aereo passagem",
    desc: t({ pt: "Horários, conexões e bagagem de ida e volta.", es: "Horarios, conexiones y equipaje de ida y vuelta." }), page: "#0E1A15",
    blocks: [R(36, 10, 28, 6, W), R(8, 26, 84, 28, "rgba(255,255,255,0.08)", 6), R(13, 34, 14, 8, A), R(73, 34, 14, 8, A), R(31, 38, 38, 1, "rgba(255,255,255,0.4)", 0), R(8, 60, 84, 28, "rgba(255,255,255,0.08)", 6), R(13, 68, 14, 8, A), R(73, 68, 14, 8, A), R(31, 72, 38, 1, "rgba(255,255,255,0.4)", 0)]
  },
  {
    type: "prices", cat: "oferta", label: t({ pt: "Preços e pacotes", es: "Precios y paquetes" }), keywords: "precos valores pacotes",
    desc: t({ pt: "Lista de ofertas, de uma até várias.", es: "Lista de ofertas, de una a varias." }), page: "#F2F4F1",
    blocks: [R(30, 8, 40, 7, D), R(8, 22, 84, 16, W, 5), R(12, 28, 24, 5, D), R(60, 27, 14, 6, D), R(78, 26, 11, 8, A, 6), R(8, 42, 84, 16, A, 5), R(12, 48, 24, 5, W), R(60, 47, 14, 6, W), R(78, 46, 11, 8, D, 6), R(8, 62, 84, 16, W, 5), R(12, 68, 24, 5, D), R(60, 67, 14, 6, D), R(78, 66, 11, 8, A, 6)]
  },
  {
    type: "viajeon_checkout", cat: "oferta", label: t({ pt: "Compra online", es: "Compra en línea" }), keywords: "checkout viajeon pagamento",
    desc: t({ pt: "Pacotes da sua operação com compra direta.", es: "Paquetes de tu operación con compra directa." }), page: W,
    blocks: [R(30, 8, 40, 7, D), R(8, 22, 56, 18, S, 5), R(8, 44, 56, 18, S, 5), R(12, 28, 24, 5, D), R(12, 50, 24, 5, D), R(46, 28, 14, 7, W, 6), R(46, 50, 14, 7, W, 6), R(68, 22, 24, 62, S, 5), R(71, 70, 18, 9, A, 8)]
  },
  {
    type: "countdown", cat: "oferta", label: t({ pt: "Contagem regressiva", es: "Cuenta regresiva" }), keywords: "contador prazo timer",
    desc: t({ pt: "Prazo da oferta com dias, horas e minutos.", es: "Plazo de la oferta con días, horas y minutos." }), page: A,
    blocks: [R(6, 30, 36, 6, "rgba(15,23,19,0.2)", 8), R(6, 42, 38, 8, W), R(6, 54, 28, 8, W), R(50, 30, 10, 30, D, 5), R(62, 30, 10, 30, D, 5), R(74, 30, 10, 30, D, 5), R(86, 30, 10, 30, D, 5)]
  },
  {
    type: "cta", cat: "oferta", label: t({ pt: "Faixa de chamada", es: "Franja de llamada" }), keywords: "chamada para acao cta botao",
    desc: t({ pt: "Frase curta com um botão de destaque.", es: "Frase corta con un botón destacado." }), page: W,
    blocks: [R(0, 28, 100, 44, A, 0), R(8, 40, 46, 8, W), R(8, 52, 32, 5, "rgba(255,255,255,0.6)"), R(66, 42, 26, 14, D, 10)]
  },
  {
    type: "testimonials", cat: "confianca", label: t({ pt: "Depoimentos", es: "Testimonios" }), keywords: "depoimentos avaliacoes clientes",
    desc: t({ pt: "Relatos de quem já viajou com você.", es: "Relatos de quienes ya viajaron contigo." }), page: "#F2F4F1",
    blocks: head(6).concat([R(6, 36, 28, 54, W, 6), R(36, 36, 28, 54, W, 6), R(66, 36, 28, 54, W, 6), R(10, 42, 14, 4, "#E0A526"), R(40, 42, 14, 4, "#E0A526"), R(70, 42, 14, 4, "#E0A526"), R(10, 52, 20, 4, L), R(40, 52, 20, 4, L), R(70, 52, 20, 4, L), R(10, 76, 7, 10, A, 20), R(40, 76, 7, 10, A, 20), R(70, 76, 7, 10, A, 20)])
  },
  {
    type: "faq", cat: "confianca", label: t({ pt: "Dúvidas frequentes", es: "Preguntas frecuentes" }), keywords: "perguntas frequentes faq duvidas",
    desc: t({ pt: "Perguntas e respostas que abrem com um toque.", es: "Preguntas y respuestas que se abren con un toque." }), page: W,
    blocks: [R(30, 8, 40, 7, D), R(10, 22, 80, 24, S, 5), R(14, 27, 44, 5, D), R(14, 36, 60, 4, L), R(82, 26, 5, 8, A, 10), R(10, 50, 80, 12, S, 5), R(14, 54, 40, 5, D), R(82, 52, 5, 8, L, 10), R(10, 66, 80, 12, S, 5), R(14, 70, 36, 5, D), R(82, 68, 5, 8, L, 10)]
  },
  {
    type: "internal_form", cat: "contato", label: t({ pt: "Formulário de contato", es: "Formulario de contacto" }), keywords: "formulario interno lead captacao",
    desc: t({ pt: "Capta nome, WhatsApp e e-mail do interessado.", es: "Capta nombre, WhatsApp y correo del interesado." }), page: "#F2F4F1",
    blocks: [R(6, 20, 36, 8, D), R(6, 32, 30, 4, L), R(50, 10, 44, 80, W, 7), R(54, 18, 36, 9, S, 4), R(54, 32, 36, 9, S, 4), R(54, 46, 36, 9, S, 4), R(54, 64, 36, 11, A, 9)]
  },
  {
    type: "links", cat: "contato", label: t({ pt: "Outros roteiros", es: "Otros itinerarios" }), keywords: "links paginas",
    desc: t({ pt: "Cards que levam para suas outras páginas.", es: "Tarjetas que llevan a tus otras páginas." }), page: W,
    blocks: [R(6, 8, 18, 5, A, 8), R(6, 16, 44, 7, D), R(6, 26, 30, 4, L), P(6, 36, 28, 26, "mar", 5), P(36, 36, 28, 26, "serra", 5), P(66, 36, 28, 26, "praia", 5), R(6, 66, 18, 4, D), R(36, 66, 18, 4, D), R(66, 66, 18, 4, D), R(6, 80, 28, 8, A, 8), R(36, 80, 28, 8, A, 8), R(66, 80, 28, 8, A, 8)]
  },
  {
    type: "agency_footer", cat: "fechamento", label: t({ pt: "Rodapé da agência", es: "Pie de la agencia" }), keywords: "rodape contatos cadastur",
    desc: t({ pt: "Contatos, Cadastur e redes da agência.", es: "Contactos, Cadastur y redes de la agencia." }), page: "#0E1A15",
    blocks: [R(6, 20, 18, 7, W), R(6, 32, 30, 4, DIM), R(6, 39, 26, 4, DIM), R(52, 20, 14, 4, W), R(52, 28, 18, 4, DIM), R(52, 35, 16, 4, DIM), R(76, 20, 14, 4, W), R(76, 28, 18, 4, DIM), R(0, 74, 100, 1, "rgba(255,255,255,0.15)", 0), R(6, 82, 40, 4, DIM)]
  }
];

const BY_TYPE = new Map(SECTION_CATALOG_V2.map(item => [item.type, item]));

/** Nome da seção no editor novo (camadas, prévia e seletor). */
export const sectionNameV2 = (type: string): string | undefined => BY_TYPE.get(type as SectionType)?.label;
