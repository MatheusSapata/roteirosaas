import type { PageConfig, PageSection } from "../../types/page";
import { getLocalizedValue } from "../../utils/i18n";
import { resolveMediaUrl } from "../../utils/media";

/** Dados da viagem usados nos criativos (tudo editável na tela antes de baixar). */
export interface CreativeData {
  title: string;
  subtitle: string;
  dates: string;
  pricePrefix: string;
  priceValue: string;
  priceSuffix: string;
  installments: string;
  benefits: string[];
  /** Único elemento com cara de botão na arte: aparece só se ativado. */
  ctaEnabled: boolean;
  cta: string;
  contact: string;
  agencyName: string;
  logoUrl: string;
  images: string[];
  primary: string;
  secondary: string;
  itinerary: { day: string; title: string; description: string }[];
  prices: { title: string; prefix: string; value: string; note: string }[];
  flights: { label: string; date: string; route: string; times: string; details: string }[];
}

/** A arte não é clicável: o botão é opcional e serve de chamada de anúncio. */
export const CTA_SUGGESTIONS = ["Saiba mais", "Garanta agora", "Reserve já", "Quero ir"];

export type CreativeFormat = "feed" | "square" | "story";
export const FORMAT_SIZES: Record<CreativeFormat, { width: number; height: number; label: string }> = {
  feed: { width: 1080, height: 1350, label: "Feed 4:5" },
  square: { width: 1080, height: 1080, label: "Quadrado" },
  story: { width: 1080, height: 1920, label: "Stories" }
};

const text = (value: unknown) => (value ? getLocalizedValue(value as never).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim() : "");

const isPlaceholder = (url: string) => !url || /placeholder|via\.placeholder|unsplash\.com\/photo-1500/i.test(url);

const formatDate = (iso?: string) => {
  if (!iso) return "";
  const [year, month, day] = iso.slice(0, 10).split("-");
  return day && month ? `${day}/${month}${year ? `/${year}` : ""}` : "";
};

export const formatMoney = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: value % 1 ? 2 : 0 }).format(value);

/** Todas as fotos da página, a capa primeiro e sem repetir. */
export const collectImages = (sections: PageSection[]): string[] => {
  const found: string[] = [];
  const push = (value: unknown) => {
    const url = typeof value === "string" ? resolveMediaUrl(value) || value : "";
    if (url && !isPlaceholder(url) && !found.includes(url)) found.push(url);
  };
  const hero = sections.find(section => section.type === "hero") as any;
  push(hero?.backgroundImage);
  for (const section of sections as any[]) {
    if (section.enabled === false) continue;
    push(section.backgroundImage);
    push(section.image);
    (section.images || []).forEach(push);
    (section.days || []).forEach((day: any) => push(day?.image));
    (section.items || []).forEach((item: any) => push(item?.image));
  }
  return found;
};

export const extractCreativeData = (
  config: PageConfig | null,
  page: { title?: string } | null,
  agency: { name?: string; logo_url?: string | null; cta_whatsapp?: string | null; primary_color?: string | null } | null
): CreativeData => {
  const sections = (config?.sections || []).filter(section => (section as any).enabled !== false) as PageSection[];
  const hero = sections.find(section => section.type === "hero") as any;
  const reasons = sections.find(section => section.type === "reasons") as any;
  const prices = sections.find(section => section.type === "prices") as any;
  const itinerary = sections.find(section => section.type === "itinerary") as any;

  const priceItems = (prices?.items || []).filter((item: any) => Number(item?.price) > 0);
  const sortedPrices = [...priceItems].sort((a: any, b: any) => Number(a.price) - Number(b.price));
  const cheapest = sortedPrices[0];
  const priceDescription = text(cheapest?.description);
  // "por pessoa" às vezes vem no rótulo do preço; ele vai depois do valor, não antes.
  const priceLabel = text(cheapest?.priceLabel);
  const perPerson = /por pessoa|p\/ pessoa|por pax/i;
  const installments = priceDescription.match(/(em at[ée] \d+x[^\n.]*)/i)?.[1] || "";

  const chips = (hero?.chips || []).map(text).filter(Boolean);
  const reasonTitles = (reasons?.items || []).map((item: any) => text(item?.title)).filter(Boolean);
  const benefits = [...chips, ...reasonTitles].filter((item, index, all) => all.indexOf(item) === index).slice(0, 8);

  const departure = formatDate(hero?.departureDate);
  const back = formatDate(hero?.returnDate);
  const days = itinerary?.days?.length ? `${itinerary.days.length} dias` : "";
  const dates = departure ? (back ? `${departure} a ${back}` : `Saída ${departure}`) : days;

  const phone = (agency?.cta_whatsapp || "").replace(/\D/g, "");
  const contact = phone.length >= 10 ? `(${phone.slice(-11, -9) || phone.slice(-10, -8)}) ${phone.slice(-9, -4)}-${phone.slice(-4)}` : "";

  return {
    title: text(hero?.title) || page?.title || "Sua próxima viagem",
    subtitle: text(hero?.subtitle).slice(0, 140),
    dates,
    pricePrefix: cheapest ? (priceLabel && !perPerson.test(priceLabel) ? priceLabel : "A partir de") : "",
    priceValue: cheapest ? formatMoney(Number(cheapest.price)) : "",
    priceSuffix: cheapest && perPerson.test(`${priceLabel} ${priceDescription}`) ? "por pessoa" : "",
    installments,
    benefits,
    ctaEnabled: false,
    cta: "Saiba mais",
    contact,
    agencyName: agency?.name || "",
    logoUrl: resolveMediaUrl(hero?.logoUrl || agency?.logo_url || "") || "",
    images: collectImages(sections),
    ...brandColors(config, agency?.primary_color),
    itinerary: (itinerary?.days || [])
      .map((day: any, index: number) => ({
        day: text(day?.day) || `Dia ${index + 1}`,
        title: text(day?.title),
        description: shorten(text(day?.description), 110)
      }))
      .filter((day: { title: string; description: string }) => day.title || day.description),
    prices: priceItems.slice(0, 6).map((item: any) => {
      const label = text(item.priceLabel);
      return {
        title: text(item.title),
        prefix: label && !perPerson.test(label) ? label : "",
        value: formatMoney(Number(item.price)),
        note: shorten(text(item.description), 90)
      };
    }),
    flights: extractFlights(sections)
  };
};

const shorten = (value: string, max: number) => (value.length > max ? `${value.slice(0, max - 1).replace(/\s+\S*$/, "")}…` : value);

const hour = (iso?: string) => (iso && iso.length >= 16 ? iso.slice(11, 16) : "");

/** Ida e volta da seção Voos, em uma linha cada (origem → destino, horários, companhia). */
const extractFlights = (sections: PageSection[]) => {
  const flight = sections.find(section => section.type === "flight_details") as any;
  return ((flight?.journeys || []) as any[])
    .filter(journey => journey?.is_enabled !== false && journey?.segments?.length)
    .map(journey => {
      const segments = journey.segments as any[];
      const first = segments[0];
      const last = segments[segments.length - 1];
      const place = (city?: string, iata?: string) => [city, iata ? `(${iata})` : ""].filter(Boolean).join(" ");
      const airlines = [...new Set(segments.map(segment => segment.airline_name).filter(Boolean))].join(" + ");
      const stops = segments.length > 1 ? `${segments.length - 1} conexão${segments.length > 2 ? "ões" : ""}` : "Voo direto";
      const times = [hour(first.departure_datetime), hour(last.arrival_datetime)].filter(Boolean).join(" → ");
      return {
        label: journey.title || (journey.direction === "inbound" ? "Volta" : "Ida"),
        date: formatDate(first.flight_date || first.departure_datetime),
        route: `${place(first.departure_city, first.departure_airport_iata)} → ${place(last.arrival_city, last.arrival_airport_iata)}`,
        times,
        details: [airlines, stops].filter(Boolean).join(" · ")
      };
    });
};

const HEX = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i;
const toRgb = (hex: string) => {
  const clean = hex.replace("#", "");
  const full = clean.length === 3 ? clean.split("").map(c => c + c).join("") : clean;
  return [0, 2, 4].map(i => parseInt(full.slice(i, i + 2), 16) || 0);
};
/** Mistura a cor com preto (amount 0–1), para um fundo escuro na mesma família da cor. */
export const darken = (hex: string, amount: number) =>
  `#${toRgb(hex).map(value => Math.round(value * (1 - amount)).toString(16).padStart(2, "0")).join("")}`;

/**
 * Cores da arte. color1/color2 do tema são os fundos da página (quase sempre claros); a cor de
 * marca é a dos botões (ctaDefaultColor). Destaque = cor de marca; principal = fundo escuro do
 * tema, ou a cor de marca escurecida quando o fundo é claro (texto branco sempre legível).
 */
const brandColors = (config: PageConfig | null, agencyColor?: string | null) => {
  const theme = config?.theme;
  const accent = [theme?.ctaDefaultColor, agencyColor, "#12B981"].find(color => color && HEX.test(color)) as string;
  const background = theme?.color1 && HEX.test(theme.color1) ? theme.color1 : "";
  const primary = background && readableOn(background) === "#ffffff" ? background : darken(accent, 0.62);
  return { primary, secondary: accent };
};

/** Texto escuro ou claro para ler bem sobre uma cor. */
export const readableOn = (hex: string) => {
  const clean = hex.replace("#", "");
  const full = clean.length === 3 ? clean.split("").map(c => c + c).join("") : clean;
  const [r, g, b] = [0, 2, 4].map(i => parseInt(full.slice(i, i + 2), 16) || 0);
  return (r * 299 + g * 587 + b * 114) / 1000 > 150 ? "#111827" : "#ffffff";
};
