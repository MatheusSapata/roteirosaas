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
  cta: string;
  contact: string;
  agencyName: string;
  logoUrl: string;
  images: string[];
  primary: string;
  secondary: string;
}

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
  agency: { name?: string; logo_url?: string | null; cta_whatsapp?: string | null } | null
): CreativeData => {
  const sections = (config?.sections || []).filter(section => (section as any).enabled !== false) as PageSection[];
  const hero = sections.find(section => section.type === "hero") as any;
  const reasons = sections.find(section => section.type === "reasons") as any;
  const prices = sections.find(section => section.type === "prices") as any;
  const itinerary = sections.find(section => section.type === "itinerary") as any;

  const priceItems = (prices?.items || []).filter((item: any) => Number(item?.price) > 0);
  const cheapest = priceItems.sort((a: any, b: any) => Number(a.price) - Number(b.price))[0];
  const priceDescription = text(cheapest?.description);
  // "por pessoa" às vezes vem no rótulo do preço; ele vai depois do valor, não antes.
  const priceLabel = text(cheapest?.priceLabel);
  const perPerson = /por pessoa|p\/ pessoa|por pax/i;
  const installments = priceDescription.match(/(em at[ée] \d+x[^\n.]*)/i)?.[1] || "";

  const chips = (hero?.chips || []).map(text).filter(Boolean);
  const reasonTitles = (reasons?.items || []).map((item: any) => text(item?.title)).filter(Boolean);
  const benefits = [...chips, ...reasonTitles].filter((item, index, all) => all.indexOf(item) === index).slice(0, 6);

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
    cta: phone ? "Chame no WhatsApp" : "Fale com a gente",
    contact,
    agencyName: agency?.name || "",
    logoUrl: resolveMediaUrl(hero?.logoUrl || agency?.logo_url || "") || "",
    images: collectImages(sections),
    primary: config?.theme?.color1 || "#0f7a4f",
    secondary: config?.theme?.color2 || "#f59e0b"
  };
};

/** Texto escuro ou claro para ler bem sobre uma cor. */
export const readableOn = (hex: string) => {
  const clean = hex.replace("#", "");
  const full = clean.length === 3 ? clean.split("").map(c => c + c).join("") : clean;
  const [r, g, b] = [0, 2, 4].map(i => parseInt(full.slice(i, i + 2), 16) || 0);
  return (r * 299 + g * 587 + b * 114) / 1000 > 150 ? "#111827" : "#ffffff";
};
