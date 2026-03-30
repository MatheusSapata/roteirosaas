import { resolveCurrentLanguage } from "./i18n";
import type { SupportedLanguage } from "./i18n";

export type AdminLanguage = SupportedLanguage;
export type AdminTranslatable<T = string> = T | Partial<Record<AdminLanguage, T>> | null | undefined;

let adminLanguage: AdminLanguage | null = null;

const detectAdminLanguage = (): AdminLanguage => {
  const host = typeof window !== "undefined" ? window.location.hostname : undefined;
  return resolveCurrentLanguage(host);
};

export const getAdminLanguage = (): AdminLanguage => {
  if (adminLanguage) return adminLanguage;
  adminLanguage = detectAdminLanguage();
  return adminLanguage;
};

export const createAdminLocalizer = (lang: AdminLanguage = getAdminLanguage()) => {
  return <T = string>(value: AdminTranslatable<T>): T | string => {
    if (value === null || typeof value === "undefined") {
      return "";
    }
    if (typeof value !== "object") {
      return value as T;
    }
    const candidate = value[lang];
    if (typeof candidate !== "undefined") {
      return candidate as T;
    }
    const fallback = value.pt;
    if (typeof fallback !== "undefined") {
      return fallback as T;
    }
    const firstAvailable = Object.values(value).find(entry => typeof entry !== "undefined");
    return (firstAvailable ?? "") as T;
  };
};

