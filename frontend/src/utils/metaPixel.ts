/**
 * Pixel da Meta do Roteiro Online: LP de vendas e checkout próprio.
 *
 * As duas páginas mandam para o pixel da página de vendas (o que a página no WordPress usava) e
 * para os pixels das ofertas em Admin Master › Ofertas e checkout. Cada evento padrão do checkout
 * sai uma vez por compra, com o mesmo event_id que o servidor usa na API de Conversões
 * ("<token da sessão>|<evento em minúsculas>"): o Meta junta os dois e conta um só.
 */
export const SALES_META_PIXEL_ID = "1584327072834789";

type Fbq = ((...args: unknown[]) => void) & {
  callMethod?: (...args: unknown[]) => void;
  queue: unknown[][];
  loaded: boolean;
  version: string;
  push: unknown;
  disablePushState?: boolean;
};
type MetaWindow = Window & { fbq?: Fbq; _fbq?: Fbq; __roMetaPixels?: Set<string> };

const metaWindow = () => window as unknown as MetaWindow;

const loadMetaPixel = (): Fbq => {
  const w = metaWindow();
  if (!w.fbq) {
    const fbq = function (...args: unknown[]) {
      if (fbq.callMethod) fbq.callMethod(...args);
      else fbq.queue.push(args);
    } as Fbq;
    fbq.push = fbq;
    fbq.loaded = true;
    fbq.version = "2.0";
    fbq.queue = [];
    w.fbq = fbq;
    if (!w._fbq) w._fbq = fbq;
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://connect.facebook.net/en_US/fbevents.js";
    document.head.appendChild(script);
  }
  // A visita de cada página sai aqui (PageView): sem isto o pixel contaria outra a cada troca de
  // endereço do app, como a da LP para o checkout.
  w.fbq.disablePushState = true;
  return w.fbq;
};

// Clique do anúncio (fbclid) guardado desde a LP: o checkout, que não recebe o fbclid no endereço,
// ainda manda o _fbc ao servidor mesmo sem o cookie do pixel.
const CLICK_KEY = "ro_fbc";
const rememberAdClick = () => {
  const fbclid = new URLSearchParams(window.location.search).get("fbclid");
  if (!fbclid) return;
  try {
    localStorage.setItem(CLICK_KEY, `fb.1.${Date.now()}.${fbclid}`);
  } catch {
    // Sem armazenamento: fica o cookie _fbc do pixel.
  }
};
const storedAdClick = () => {
  try {
    return localStorage.getItem(CLICK_KEY) || "";
  } catch {
    return "";
  }
};

/** Liga os pixels (cada um uma vez por aba) e conta a visita da página. Devolve os pixels ligados. */
export const startMetaPixels = (ids: string[]): string[] => {
  if (typeof window === "undefined") return [];
  rememberAdClick();
  const unique = [...new Set(ids.map(id => String(id || "").trim()).filter(Boolean))];
  if (!unique.length) return [];
  const fbq = loadMetaPixel();
  const w = metaWindow();
  const started = (w.__roMetaPixels ||= new Set<string>());
  for (const id of unique) {
    if (started.has(id)) continue;
    fbq("init", id);
    started.add(id);
  }
  for (const id of unique) fbq("trackSingle", id, "PageView");
  return unique;
};

/** Evento só para estes pixels (não vaza para outro pixel que esteja ligado na aba). */
export const trackMetaEvent = (ids: string[], event: string, data: Record<string, unknown>, options: { eventId?: string; custom?: boolean } = {}) => {
  const fbq = typeof window === "undefined" ? undefined : metaWindow().fbq;
  if (!fbq) return;
  for (const id of ids) {
    fbq(options.custom ? "trackSingleCustom" : "trackSingle", id, event, data, options.eventId ? { eventID: options.eventId } : undefined);
  }
};

/** O mesmo event_id do servidor (app/services/checkout.py, meta_standard_event_id). */
export const metaStandardEventId = (token: string, event: string) => `${token}|${event.toLowerCase()}`;

const SENT_KEY = "ro_meta_sent";
/** True na primeira vez deste evento: recarregar a página de sucesso não manda outro Purchase. */
export const firstMetaSend = (eventId: string): boolean => {
  try {
    const sent = JSON.parse(localStorage.getItem(SENT_KEY) || "[]") as string[];
    if (sent.includes(eventId)) return false;
    localStorage.setItem(SENT_KEY, JSON.stringify([...sent, eventId].slice(-100)));
  } catch {
    // Sem armazenamento: o event_id igual ainda faz o Meta contar uma vez só.
  }
  return true;
};

const readCookie = (name: string) => {
  if (typeof document === "undefined") return "";
  const row = document.cookie.split("; ").find(item => item.startsWith(`${name}=`));
  return row ? decodeURIComponent(row.slice(name.length + 1)) : "";
};

/** Cookies do Meta (_fbp e _fbc) e a página, para o servidor reconhecer a pessoa na API de Conversões. */
export const metaBrowserContext = () => {
  if (typeof window === "undefined") return {};
  const fbclid = new URLSearchParams(window.location.search).get("fbclid");
  const fbc = readCookie("_fbc") || (fbclid ? `fb.1.${Date.now()}.${fbclid}` : storedAdClick());
  // Sem a query: o endereço do checkout leva o token da sessão.
  const context: Record<string, string> = { page_url: `${window.location.origin}${window.location.pathname}` };
  const fbp = readCookie("_fbp");
  if (fbp) context.fbp = fbp;
  if (fbc) context.fbc = fbc;
  return context;
};
