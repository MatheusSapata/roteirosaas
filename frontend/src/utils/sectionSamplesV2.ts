import type { PageSection, SectionType } from "../types/page";
import { createLocalizer, getCurrentLanguage } from "./i18n";

const t = createLocalizer(getCurrentLanguage());

/** Fotos de exemplo (Unsplash, uso livre) para as miniaturas e para as seções novas. */
const unsplash = (id: string, width = 1600) => `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=${width}&q=70`;
export const SAMPLE_PHOTOS = {
  lago: unsplash("1501785888041-af3ef285b470"),
  barco: unsplash("1476514525535-07fb3b4ae5f1"),
  vale: unsplash("1470071459604-3b5ec3a7fe05"),
  estrada: unsplash("1500530855697-b586d89ba3ee"),
  praia: unsplash("1507525428034-b723cf961d3e"),
  baloes: unsplash("1530789253388-582c481c54b0"),
  serra: unsplash("1506905925346-21bda4d32df4"),
  trilha: unsplash("1469474968028-56623f02e42e")
};
const AVATARS = [
  unsplash("1494790108377-be9c29b29330", 200),
  unsplash("1500648767791-00dcc994a43e", 200),
  unsplash("1438761681033-6461ffad8d80", 200)
];

/** Data no formato da página (AAAA-MM-DD), a N dias de hoje. */
const daysFromNow = (days: number) => {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
};

/** Marca de exemplo para Menu do topo, Capa e Rodapé nas miniaturas. */
export const SAMPLE_BRANDING = {
  agency_name: t({ pt: "Sua Agência", es: "Tu Agencia" }),
  logo_url: "",
  agency_profile: {
    name: t({ pt: "Sua Agência de Viagens", es: "Tu Agencia de Viajes" }),
    description: t({ pt: "Roteiros pensados com cuidado, do embarque à volta para casa.", es: "Itinerarios pensados con cuidado, del embarque al regreso a casa." }),
    phone: "(11) 99999-9999",
    email: "contato@suaagencia.com.br",
    city: t({ pt: "São Paulo · SP", es: "São Paulo · SP" }),
    social_links: [
      { platform: "instagram", url: "https://instagram.com" },
      { platform: "facebook", url: "https://facebook.com" }
    ]
  }
};

const chips = [
  t({ pt: "Hospedagem inclusa", es: "Alojamiento incluido" }),
  t({ pt: "Guia local", es: "Guía local" }),
  t({ pt: "Café da manhã", es: "Desayuno" }),
  t({ pt: "Grupos pequenos", es: "Grupos pequeños" })
];

/**
 * Conteúdo genérico de cada seção, usado nas miniaturas do seletor:
 * a miniatura é a própria seção, em escala, com textos e fotos de exemplo.
 */
const SAMPLES: Partial<Record<SectionType, () => Record<string, any>>> = {
  header: () => ({
    mode: "solid",
    backgroundColor: "#ffffff",
    links: [
      { id: "l1", label: t({ pt: "Roteiro", es: "Itinerario" }), targetType: "section", target: "" },
      { id: "l2", label: t({ pt: "Preços", es: "Precios" }), targetType: "section", target: "" },
      { id: "l3", label: t({ pt: "Dúvidas", es: "Dudas" }), targetType: "section", target: "" }
    ],
    actionType: "contact",
    contactLabel: t({ pt: "Falar no WhatsApp", es: "Hablar por WhatsApp" }),
    contactType: "whatsapp",
    stickyEnabled: false
  }),
  hero: () => ({
    layout: "immersive",
    title: t({ pt: "Nome do destino: uma viagem para lembrar", es: "Nombre del destino: un viaje para recordar" }),
    subtitle: t({ pt: "Uma frase curta sobre o que torna esta viagem especial.", es: "Una frase corta sobre lo que hace especial este viaje." }),
    backgroundImage: SAMPLE_PHOTOS.lago,
    chips,
    departureDate: daysFromNow(40),
    returnDate: daysFromNow(46),
    ctaLabel: t({ pt: "Quero reservar", es: "Quiero reservar" }),
    ctaLink: "#"
  }),
  banner_card: () => ({
    title: t({ pt: "Uma chamada forte para a sua viagem", es: "Un llamado fuerte para tu viaje" }),
    subtitle: t({ pt: "Destaque a principal promessa ou a próxima saída.", es: "Destaca la promesa principal o la próxima salida." }),
    backgroundImage: SAMPLE_PHOTOS.trilha,
    ctaEnabled: true,
    ctaLabel: t({ pt: "Quero saber mais", es: "Quiero saber más" }),
    ctaLink: "#"
  }),
  video_vsl: () => ({
    title: t({ pt: "Assista antes de continuar", es: "Mira antes de continuar" }),
    subtitle: t({ pt: "Em poucos minutos, tudo o que você precisa saber.", es: "En pocos minutos, todo lo que necesitas saber." }),
    videoUrl: "",
    thumbnailUrl: SAMPLE_PHOTOS.praia,
    videoAspectRatio: "horizontal",
    ctaLabel: t({ pt: "Quero aproveitar", es: "Quiero aprovechar" }),
    ctaLink: "#"
  }),
  story: () => ({
    layout: "gallery",
    imagePosition: "right",
    badge: t({ pt: "Sobre a viagem", es: "Sobre el viaje" }),
    title: t({ pt: "Uma experiência do começo ao fim", es: "Una experiencia de principio a fin" }),
    subtitle: t({
      pt: "Conte aqui como é a viagem: o clima do destino, o ritmo dos dias e o que ninguém pode deixar de viver.",
      es: "Cuenta aquí cómo es el viaje: el clima del destino, el ritmo de los días y lo que nadie puede dejar de vivir."
    }),
    images: [SAMPLE_PHOTOS.barco, SAMPLE_PHOTOS.vale, SAMPLE_PHOTOS.praia],
    ctaEnabled: true,
    ctaLabel: t({ pt: "Quero saber mais", es: "Quiero saber más" }),
    ctaLink: "#"
  }),
  reasons: () => ({
    title: t({ pt: "Por que viajar com a gente", es: "Por qué viajar con nosotros" }),
    subtitle: t({ pt: "O que está incluso e faz diferença.", es: "Lo que está incluido y marca la diferencia." }),
    iconMode: "icon",
    items: [
      { icon: "icon:bed", title: t({ pt: "Hospedagem", es: "Alojamiento" }), description: t({ pt: "Hotéis bem localizados e confortáveis.", es: "Hoteles bien ubicados y cómodos." }) },
      { icon: "icon:guide", title: t({ pt: "Guia local", es: "Guía local" }), description: t({ pt: "Quem conhece o destino de verdade.", es: "Quien conoce de verdad el destino." }) },
      { icon: "icon:bus", title: t({ pt: "Transporte", es: "Transporte" }), description: t({ pt: "Traslados e passeios sem preocupação.", es: "Traslados y paseos sin preocupaciones." }) },
      { icon: "icon:shield", title: t({ pt: "Suporte", es: "Soporte" }), description: t({ pt: "Atendimento antes e durante a viagem.", es: "Atención antes y durante el viaje." }) }
    ]
  }),
  biography: () => ({
    title: t({ pt: "Título do artigo", es: "Título del artículo" }),
    text: t({
      pt: "<p>Use esta seção para um texto mais longo: dicas do destino, a história da agência ou um relato de viagem.</p>",
      es: "<p>Usa esta sección para un texto más largo: consejos del destino, la historia de la agencia o un relato de viaje.</p>"
    }),
    image: SAMPLE_PHOTOS.serra,
    overlayOpacity: 0.45
  }),
  photo: () => ({ image: SAMPLE_PHOTOS.barco, layout: "card", altText: t({ pt: "Legenda da foto", es: "Leyenda de la foto" }) }),
  featured_video: () => ({
    title: t({ pt: "Veja como é a viagem", es: "Mira cómo es el viaje" }),
    subtitle: t({ pt: "Um vídeo curto mostrando o clima da experiência.", es: "Un video corto mostrando el ambiente de la experiencia." }),
    videoUrl: "",
    ctaEnabled: false
  }),
  gallery: () => ({
    layout: "mosaic",
    images: [SAMPLE_PHOTOS.lago, SAMPLE_PHOTOS.baloes, SAMPLE_PHOTOS.vale, SAMPLE_PHOTOS.praia, SAMPLE_PHOTOS.estrada]
  }),
  itinerary: () => ({
    layout: "journey",
    title: t({ pt: "Roteiro dia a dia", es: "Itinerario día a día" }),
    subtitle: t({ pt: "Tudo o que acontece em cada dia.", es: "Todo lo que pasa cada día." }),
    startDate: daysFromNow(40),
    days: [
      { day: "Dia 1", title: t({ pt: "Chegada e boas-vindas", es: "Llegada y bienvenida" }), description: t({ pt: "Recepção no aeroporto, traslado ao hotel e jantar de boas-vindas.", es: "Recepción en el aeropuerto, traslado al hotel y cena de bienvenida." }), image: SAMPLE_PHOTOS.barco.replace("w=1600", "w=600") },
      { day: "Dia 2", title: t({ pt: "Passeio principal", es: "Paseo principal" }), description: t({ pt: "Dia inteiro conhecendo o destino com guia local.", es: "Día entero conociendo el destino con guía local." }) },
      { day: "Dia 3", title: t({ pt: "Dia livre e retorno", es: "Día libre y regreso" }), description: "" }
    ]
  }),
  flight_details: () => ({
    title: t({ pt: "Voos", es: "Vuelos" }),
    subtitle: t({ pt: "Horários e bagagem de ida e volta.", es: "Horarios y equipaje de ida y vuelta." }),
    visualStyle: "decolar",
    showOutbound: true,
    showInbound: true,
    journeys: [
      {
        direction: "outbound",
        segments: [
          {
            airline_name: "Companhia Aérea",
            flight_number: "AB 1234",
            departure_airport_iata: "GRU",
            departure_city: "São Paulo",
            departure_datetime: `${daysFromNow(40)}T08:30:00`,
            arrival_airport_iata: "SSA",
            arrival_city: "Salvador",
            arrival_datetime: `${daysFromNow(40)}T11:00:00`,
            duration_minutes: 150,
            included_personal_item: true,
            included_carry_on: true
          }
        ]
      }
    ]
  }),
  prices: () => ({
    layout: "columns",
    title: t({ pt: "Escolha seu pacote", es: "Elige tu paquete" }),
    subtitle: t({ pt: "Valores por pessoa, com tudo o que está incluso.", es: "Valores por persona, con todo lo incluido." }),
    ctaLabel: t({ pt: "Reservar", es: "Reservar" }),
    items: [
      { title: t({ pt: "Quarto duplo", es: "Habitación doble" }), price: 3490, priceLabel: t({ pt: "por pessoa", es: "por persona" }), currency: "BRL", highlight: false, ctaLink: "#" },
      { title: t({ pt: "Quarto triplo", es: "Habitación triple" }), price: 3190, priceLabel: t({ pt: "por pessoa", es: "por persona" }), currency: "BRL", highlight: true, badge: t({ pt: "Mais vendido", es: "Más vendido" }), ctaLink: "#" }
    ]
  }),
  viajeon_checkout: () => ({
    title: t({ pt: "Escolha seu pacote", es: "Elige tu paquete" }),
    subtitle: t({ pt: "Selecione as quantidades e siga para o pagamento.", es: "Selecciona las cantidades y continúa al pago." }),
    buttonLabel: t({ pt: "Continuar para o pagamento", es: "Continuar al pago" }),
    checkoutSnapshot: {
      checkout_id: "exemplo",
      slug: "exemplo",
      name: t({ pt: "Nome da viagem", es: "Nombre del viaje" }),
      packages: [
        { id: "p1", name: t({ pt: "Adulto", es: "Adulto" }), price: 3490, min_quantity: 0, max_quantity: 10, active: true },
        { id: "p2", name: t({ pt: "Criança", es: "Niño" }), price: 1990, min_quantity: 0, max_quantity: 10, active: true }
      ]
    }
  }),
  countdown: () => ({
    label: t({ pt: "A oferta termina em breve", es: "La oferta termina pronto" }),
    countdownMode: "fixed",
    targetDate: `${daysFromNow(3)}T23:59:00`,
    layout: "cards"
  }),
  cta: () => ({
    label: t({ pt: "Pronto para a próxima viagem?", es: "¿Listo para el próximo viaje?" }),
    description: t({ pt: "Fale com a gente e garanta sua vaga.", es: "Habla con nosotros y asegura tu lugar." }),
    ctaEnabled: true,
    ctaText: t({ pt: "Falar no WhatsApp", es: "Hablar por WhatsApp" }),
    link: "#"
  }),
  testimonials: () => ({
    layout: "grid",
    title: t({ pt: "Quem já viajou com a gente", es: "Quien ya viajó con nosotros" }),
    subtitle: t({ pt: "Relatos de clientes.", es: "Relatos de clientes." }),
    items: [
      { name: "Ana", text: t({ pt: "Tudo muito bem organizado, voltaria amanhã.", es: "Todo muy bien organizado, volvería mañana." }), avatar: AVATARS[0], rating: 5 },
      { name: "Carlos", text: t({ pt: "Guia excelente e passeios incríveis.", es: "Guía excelente y paseos increíbles." }), avatar: AVATARS[1], rating: 5 },
      { name: "Júlia", text: t({ pt: "Atendimento atencioso do começo ao fim.", es: "Atención cuidadosa de principio a fin." }), avatar: AVATARS[2], rating: 5 }
    ]
  }),
  faq: () => ({
    layout: "accordion",
    title: t({ pt: "Dúvidas frequentes", es: "Preguntas frecuentes" }),
    items: [
      { question: t({ pt: "O que está incluso?", es: "¿Qué está incluido?" }), answer: t({ pt: "Hospedagem, transporte e passeios do roteiro.", es: "Alojamiento, transporte y paseos del itinerario." }) },
      { question: t({ pt: "Como faço a reserva?", es: "¿Cómo reservo?" }), answer: "" },
      { question: t({ pt: "Posso parcelar?", es: "¿Puedo pagar en cuotas?" }), answer: "" }
    ]
  }),
  internal_form: () => ({
    title: t({ pt: "Fale com um especialista", es: "Habla con un especialista" }),
    subtitle: t({ pt: "Deixe seus dados e retornamos em seguida.", es: "Deja tus datos y te respondemos enseguida." }),
    formId: "",
    backgroundType: "solid",
    alignment: "center"
  }),
  links: () => ({
    title: t({ pt: "Links/roteiros", es: "Links/itinerarios" }),
    subtitle: t({ pt: "Mais viagens que você vai gostar.", es: "Más viajes que te van a gustar." }),
    carouselEnabled: false,
    items: [
      { id: "a", source: "external", url: "#", image: SAMPLE_PHOTOS.praia, title: t({ pt: "Destino de praia", es: "Destino de playa" }), description: "", buttonLabel: t({ pt: "Ver roteiro", es: "Ver itinerario" }) },
      { id: "b", source: "external", url: "#", image: SAMPLE_PHOTOS.serra, title: t({ pt: "Destino de serra", es: "Destino de montaña" }), description: "", buttonLabel: t({ pt: "Ver roteiro", es: "Ver itinerario" }) },
      { id: "c", source: "external", url: "#", image: SAMPLE_PHOTOS.baloes, title: t({ pt: "Destino internacional", es: "Destino internacional" }), description: "", buttonLabel: t({ pt: "Ver roteiro", es: "Ver itinerario" }) }
    ]
  }),
  agency_footer: () => ({ showCadastur: true })
};

export const hasSectionSampleV2 = (type: SectionType) => !!SAMPLES[type];

export const buildSectionSampleV2 = (type: SectionType): PageSection | null => {
  const build = SAMPLES[type];
  return build ? ({ type, enabled: true, anchorId: `amostra-${type}`, ...build() } as unknown as PageSection) : null;
};
