export type SupportedLanguage = "pt" | "es";

export type LocalizedObject = Partial<Record<SupportedLanguage, string>> & Record<string, string | undefined>;

export type LocalizedString = string | LocalizedObject | null | undefined;

const PT_HOSTS = new Set(["roteiroonline.com", "www.roteiroonline.com"]);
const ES_HINTS = ["latam", "es", "intl"];

let currentLanguage: SupportedLanguage = "pt";

const normalizeHost = (host?: string | null) => (host || "").trim().toLowerCase();

export const resolveCurrentLanguage = (host?: string | null): SupportedLanguage => {
  // 👇 DEBUG LOCAL (override manual)
  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    const forcedLang = params.get("lang");
    if (forcedLang === "es") return "es";
    if (forcedLang === "pt") return "pt";
  }

  const normalized = normalizeHost(host);

  if (PT_HOSTS.has(normalized)) {
    return "pt";
  }

  if (normalized && ES_HINTS.some(token => normalized.includes(token))) {
    return "es";
  }

  return "pt";
};

const setDocumentLanguage = (lang: SupportedLanguage) => {
  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("lang", lang);
  }
};

export const setCurrentLanguage = (lang: SupportedLanguage) => {
  currentLanguage = lang;
  setDocumentLanguage(lang);
};

export const getCurrentLanguage = (): SupportedLanguage => currentLanguage;

const fallbackToFirstAvailable = (value: LocalizedObject): string | undefined => {
  const entries = Object.values(value);
  for (const entry of entries) {
    if (typeof entry === "string" && entry.trim().length) {
      return entry;
    }
  }
  return undefined;
};

export const getLocalizedValue = (field: LocalizedString, lang: SupportedLanguage = getCurrentLanguage()): string => {
  if (field === null || typeof field === "undefined") return "";
  if (typeof field === "string") return field;
  if (typeof field === "object") {
    const candidate = field[lang];
    if (typeof candidate === "string" && candidate.trim().length) {
      return candidate;
    }
    const ptValue = field.pt;
    if (typeof ptValue === "string" && ptValue.trim().length) {
      return ptValue;
    }
    const fallback = fallbackToFirstAvailable(field);
    if (typeof fallback === "string") {
      return fallback;
    }
  }
  return "";
};

export const createTranslatable = <T extends Record<string, LocalizedString>>(values: T) => values;

export const createLocalizer = (lang: SupportedLanguage = getCurrentLanguage()) => {
  return (value: LocalizedString) => getLocalizedValue(value, lang);
};
