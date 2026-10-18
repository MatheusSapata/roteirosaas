/**
 * Origem de quem chega pelo anúncio (UTMs) até virar cliente: a LP, o checkout e o cadastro grátis
 * guardam as UTMs do endereço por 30 dias, e o checkout e o cadastro as enviam ao sistema (Admin
 * Master › Empresas mostra a origem do dono). Um anúncio novo troca a origem guardada (último clique).
 */
export const UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"] as const;
export type Attribution = Partial<Record<(typeof UTM_KEYS)[number] | "referrer", string>>;

const STORAGE_KEY = "ro_attribution";
const MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;

const read = (): (Attribution & { saved_at?: number }) | null => {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (!stored || typeof stored !== "object") return null;
    if (!stored.saved_at || Date.now() - stored.saved_at > MAX_AGE_MS) return null;
    return stored;
  } catch {
    return null;
  }
};

const save = (value: Attribution) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...value, saved_at: Date.now() }));
  } catch {
    // Sem armazenamento: vale só o que está no endereço.
  }
};

const fromUrl = (): Attribution => {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const found: Attribution = {};
  for (const key of UTM_KEYS) {
    const value = params.get(key)?.trim();
    if (value) found[key] = value.slice(0, 255);
  }
  return found;
};

const externalReferrer = () => {
  if (typeof document === "undefined" || !document.referrer) return "";
  try {
    return new URL(document.referrer).origin === window.location.origin ? "" : document.referrer.slice(0, 500);
  } catch {
    return "";
  }
};

/** Guarda as UTMs do endereço atual (ou, sem elas, o site de onde a pessoa veio na primeira visita). */
export const captureAttribution = (): Attribution => {
  const utm = fromUrl();
  const referrer = externalReferrer();
  const stored = read();
  if (Object.keys(utm).length) {
    // Mesmo anúncio (ex.: da LP para o checkout, já sem referrer externo): mantém o site de onde veio.
    const sameAd = Boolean(stored) && UTM_KEYS.every(key => (stored?.[key] || "") === (utm[key] || ""));
    const keptReferrer = referrer || (sameAd ? stored?.referrer : "") || "";
    save({ ...utm, ...(keptReferrer ? { referrer: keptReferrer } : {}) });
  } else if (!stored && referrer) {
    save({ referrer });
  }
  return currentAttribution();
};

/** A origem guardada (UTMs e site de onde veio), sem a data. */
export const currentAttribution = (): Attribution => {
  const stored = read();
  if (!stored) return fromUrl();
  const { saved_at: _savedAt, ...attribution } = stored;
  return attribution;
};

/** Só as UTMs, para levar no endereço do próximo passo (da LP para o checkout). */
export const utmQuery = (): Record<string, string> => {
  const attribution = currentAttribution();
  const query: Record<string, string> = {};
  for (const key of UTM_KEYS) if (attribution[key]) query[key] = attribution[key] as string;
  return query;
};
