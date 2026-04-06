import { getPlatformOrigin, isCurrentHostPlatform } from "./platform";

const rawApiBase = (import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").trim();

const isAbsoluteUrl = /^https?:\/\//i.test(rawApiBase);

const ensureLeadingSlash = (value: string) => (value.startsWith("/") ? value : `/${value}`);
const stripTrailingSlash = (value: string) => value.replace(/\/+$/, "");

const computeBaseUrl = (): string => {
  if (isAbsoluteUrl) {
    return stripTrailingSlash(rawApiBase);
  }

  const path = ensureLeadingSlash(rawApiBase);
  if (typeof window !== "undefined" && isCurrentHostPlatform()) {
    return `${stripTrailingSlash(window.location.origin)}${path}`;
  }
  return `${getPlatformOrigin()}${path}`;
};

export const API_BASE_URL = computeBaseUrl();
export const API_ROOT_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, "");
