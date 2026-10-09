import type { SectionType } from "../types/page";
import { createLocalizer, getCurrentLanguage } from "./i18n";

const t = createLocalizer(getCurrentLanguage());

/** Categorias do seletor de seções do editor novo, na ordem em que aparecem. */
export const SECTION_CATEGORIES_V2 = [
  { id: "navegacao", label: t({ pt: "Menu e rodapé", es: "Menú y pie" }), hint: t({ pt: "Navegação e dados da agência", es: "Navegación y datos de la agencia" }) },
  { id: "capa", label: t({ pt: "Capa", es: "Portada" }), hint: t({ pt: "A primeira coisa que o cliente vê", es: "Lo primero que ve el cliente" }) },
  { id: "viagem", label: t({ pt: "Detalhamento", es: "Detalles" }), hint: t({ pt: "Destino, dias, voos, o que está incluso e outros roteiros", es: "Destino, días, vuelos, lo que está incluido y otros itinerarios" }) },
  { id: "midia", label: t({ pt: "Fotos e vídeos", es: "Fotos y videos" }), hint: t({ pt: "Mostre o destino", es: "Muestra el destino" }) },
  { id: "venda", label: t({ pt: "Venda", es: "Venta" }), hint: t({ pt: "Preço, compra e prazo da oferta", es: "Precio, compra y plazo de la oferta" }) },
  { id: "confianca", label: t({ pt: "Confiança", es: "Confianza" }), hint: t({ pt: "Depoimentos e respostas", es: "Testimonios y respuestas" }) },
  { id: "contato", label: t({ pt: "Contato", es: "Contacto" }), hint: t({ pt: "Capte quem tem interesse", es: "Capta a quien tiene interés" }) }
] as const;

export type SectionCategoryV2 = (typeof SECTION_CATEGORIES_V2)[number]["id"];

export interface SectionCatalogItemV2 {
  type: SectionType;
  cat: SectionCategoryV2;
  label: string;
  /** Palavras extras para a busca (nomes antigos, sinônimos). */
  keywords: string;
  desc: string;
}

export const SECTION_CATALOG_V2: SectionCatalogItemV2[] = [
  {
    type: "header", cat: "navegacao", label: t({ pt: "Menu do topo", es: "Menú superior" }), keywords: "cabeçalho cabecalho header menu",
    desc: t({ pt: "Logo, links para as seções e botão de contato.", es: "Logo, enlaces a las secciones y botón de contacto." })
  },
  {
    type: "hero", cat: "capa", label: t({ pt: "Banner Inicial", es: "Banner inicial" }), keywords: "banner hero capa da viagem",
    desc: t({ pt: "Foto grande, título, datas e o botão principal.", es: "Foto grande, título, fechas y el botón principal." })
  },
  {
    type: "banner_card", cat: "capa", label: t({ pt: "Banner em Card", es: "Banner en tarjeta" }), keywords: "banner em card capa com card",
    desc: t({ pt: "Foto de fundo com texto e botão por cima, com ou sem card.", es: "Foto de fondo con texto y botón encima, con o sin tarjeta." })
  },
  {
    type: "video_vsl", cat: "capa", label: t({ pt: "Vídeo de Vendas (VSL)", es: "Video de Ventas (VSL)" }), keywords: "vsl video de vendas liberar",
    desc: t({
      pt: "Vídeo com botão abaixo. Pode esconder o resto da página e o botão até um momento do vídeo que você escolhe.",
      es: "Video con botón debajo. Puede ocultar el resto de la página y el botón hasta un momento del video que tú eliges."
    })
  },
  {
    type: "story", cat: "viagem", label: t({ pt: "Texto e Imagens", es: "Texto e Imágenes" }), keywords: "sobre a viagem descritivo historia texto imagens",
    desc: t({ pt: "Texto com carrossel de até 10 fotos.", es: "Texto con carrusel de hasta 10 fotos." })
  },
  {
    type: "reasons", cat: "viagem", label: t({ pt: "Diferenciais", es: "Diferenciales" }), keywords: "itens motivos vantagens",
    desc: t({ pt: "Cards com ícone, título e texto curto.", es: "Tarjetas con ícono, título y texto corto." })
  },
  {
    type: "photo", cat: "midia", label: t({ pt: "Foto em destaque", es: "Foto destacada" }), keywords: "foto destacada imagem",
    desc: t({ pt: "Uma imagem grande com legenda.", es: "Una imagen grande con leyenda." })
  },
  {
    type: "biography", cat: "viagem", label: t({ pt: "Artigo", es: "Artículo" }), keywords: "biografia blog texto post",
    desc: t({ pt: "Imagem de capa com título e texto formatado, como um post.", es: "Imagen de portada con título y texto con formato, como un post." })
  },
  {
    type: "featured_video", cat: "midia", label: t({ pt: "Vídeo", es: "Video" }), keywords: "video em destaque youtube vimeo",
    desc: t({ pt: "Vídeo do YouTube ou Vimeo com título.", es: "Video de YouTube o Vimeo con título." })
  },
  {
    type: "itinerary", cat: "viagem", label: t({ pt: "Roteiro dia a dia", es: "Itinerario día a día" }), keywords: "roteiro itinerario dias",
    desc: t({ pt: "Linha do tempo com data e foto de cada dia.", es: "Línea de tiempo con fecha y foto de cada día." })
  },
  {
    type: "gallery", cat: "midia", label: t({ pt: "Galeria de fotos", es: "Galería de fotos" }), keywords: "galeria fotos carrossel mosaico",
    desc: t({ pt: "Carrossel, mosaico ou grade de fotos.", es: "Carrusel, mosaico o cuadrícula de fotos." })
  },
  {
    type: "flight_details", cat: "viagem", label: t({ pt: "Voos", es: "Vuelos" }), keywords: "detalhes do voo aereo passagem",
    desc: t({ pt: "Horários, conexões e bagagem de ida e volta.", es: "Horarios, conexiones y equipaje de ida y vuelta." })
  },
  {
    type: "prices", cat: "venda", label: t({ pt: "Preços e pacotes", es: "Precios y paquetes" }), keywords: "precos valores pacotes",
    desc: t({ pt: "Lista de ofertas, de uma até várias.", es: "Lista de ofertas, de una a varias." })
  },
  {
    type: "viajeon_checkout", cat: "venda", label: t({ pt: "Compra Online (Viaje On)", es: "Compra en Línea (Viaje On)" }), keywords: "compra online checkout viajeon viaje on pagamento",
    desc: t({
      pt: "Pacotes da sua operação no Viaje On com compra direta. Precisa da integração com o Viaje On ativa.",
      es: "Paquetes de tu operación en Viaje On con compra directa. Requiere la integración con Viaje On activa."
    })
  },
  {
    type: "countdown", cat: "venda", label: t({ pt: "Contagem regressiva", es: "Cuenta regresiva" }), keywords: "contador prazo timer",
    desc: t({ pt: "Prazo da oferta com dias, horas e minutos.", es: "Plazo de la oferta con días, horas y minutos." })
  },
  {
    type: "cta", cat: "venda", label: t({ pt: "Faixa de chamada", es: "Franja de llamada" }), keywords: "chamada para acao cta botao",
    desc: t({ pt: "Frase curta com um botão de destaque.", es: "Frase corta con un botón destacado." })
  },
  {
    type: "testimonials", cat: "confianca", label: t({ pt: "Depoimentos", es: "Testimonios" }), keywords: "depoimentos avaliacoes clientes",
    desc: t({ pt: "Relatos de quem já viajou com você.", es: "Relatos de quienes ya viajaron contigo." })
  },
  {
    type: "faq", cat: "confianca", label: t({ pt: "Dúvidas frequentes", es: "Preguntas frecuentes" }), keywords: "perguntas frequentes faq duvidas",
    desc: t({ pt: "Perguntas e respostas que abrem com um toque.", es: "Preguntas y respuestas que se abren con un toque." })
  },
  {
    type: "internal_form", cat: "contato", label: t({ pt: "Formulário de contato", es: "Formulario de contacto" }), keywords: "formulario interno lead captacao",
    desc: t({ pt: "Capta nome, WhatsApp e e-mail do interessado.", es: "Capta nombre, WhatsApp y correo del interesado." })
  },
  {
    type: "links", cat: "viagem", label: t({ pt: "Links/Roteiros", es: "Links/Itinerarios" }), keywords: "links roteiros outros roteiros paginas",
    desc: t({ pt: "Cards que levam para suas outras páginas.", es: "Tarjetas que llevan a tus otras páginas." })
  },
  {
    type: "agency_footer", cat: "navegacao", label: t({ pt: "Rodapé da agência", es: "Pie de la agencia" }), keywords: "rodape contatos cadastur",
    desc: t({ pt: "Contatos, Cadastur e redes da agência.", es: "Contactos, Cadastur y redes de la agencia." })
  }
];

const BY_TYPE = new Map(SECTION_CATALOG_V2.map(item => [item.type, item]));

/** Nome da seção no editor novo (camadas, prévia e seletor). */
export const sectionNameV2 = (type: string): string | undefined => BY_TYPE.get(type as SectionType)?.label;
