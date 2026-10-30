// Datas e menor preço de uma página para pré-preencher o card de Links/Roteiros.
// Mesma regra do servidor (backend/app/services/page_tags.py, page_card_data).

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const CURRENCY_PREFIX: Record<string, string> = { BRL: "R$", USD: "US$", EUR: "€", GBP: "£" };

const validDate = (value: unknown) => (typeof value === "string" && DATE_RE.test(value) ? value : "");

export const formatCardPrice = (value: number, currency = "BRL") => {
  const whole = Math.abs(value - Math.round(value)) < 0.005;
  const text = value.toLocaleString("pt-BR", { minimumFractionDigits: whole ? 0 : 2, maximumFractionDigits: whole ? 0 : 2 });
  return `${CURRENCY_PREFIX[currency] || currency} ${text}`;
};

export const pageCardPrefill = (config: any) => {
  const sections: any[] = Array.isArray(config?.sections) ? config.sections.filter((section: any) => section && typeof section === "object") : [];
  const hero = sections.find(section => section.type === "hero") || {};
  const candidates: [unknown, string][] = [];
  let excursion: any = null;
  for (const section of sections) {
    if (section.enabled === false) continue;
    if (section.type === "prices") {
      for (const item of section.items || []) candidates.push([item?.price, String(item?.currency || "BRL")]);
    } else if (section.type === "viajeon_checkout") {
      const snapshot = section.checkoutSnapshot || {};
      for (const item of snapshot.packages || []) if (item?.active !== false) candidates.push([item?.price, "BRL"]);
      excursion = excursion || snapshot.excursion || null;
    }
  }
  let lowest: { price: number; currency: string } | null = null;
  for (const [raw, currency] of candidates) {
    const price = Number(raw) || 0;
    if (price <= 0 || (lowest && currency !== lowest.currency)) continue;
    if (!lowest || price < lowest.price) lowest = { price, currency };
  }
  let departureDate = validDate(hero.departureDate);
  let returnDate = validDate(hero.returnDate);
  if (!departureDate && !returnDate && excursion) {
    departureDate = validDate(String(excursion.departure_date || "").slice(0, 10));
    returnDate = validDate(String(excursion.return_date || "").slice(0, 10));
  }
  return { departureDate, returnDate, price: lowest ? formatCardPrice(lowest.price, lowest.currency) : "" };
};

/** Campos do card já preenchidos (e editáveis) a partir da página escolhida. */
export const pageCardPrefillFields = (config: any) => {
  const { departureDate, returnDate, price } = pageCardPrefill(config);
  return {
    showDates: !!(departureDate || returnDate),
    departureDate,
    returnDate,
    showPrice: !!price,
    priceValue: price,
    pricePrefix: price ? "a partir de" : "",
    priceSuffix: price ? "por pessoa" : ""
  };
};
