import { getPlatformOrigin } from "./platform";

const rawApiBase = (import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").trim();

const isAbsoluteUrl = /^https?:\/\//i.test(rawApiBase);

const ensureLeadingSlash = (value: string) => (value.startsWith("/") ? value : `/${value}`);
const stripTrailingSlash = (value: string) => value.replace(/\/+$/, "");

const resolvePath = () => ensureLeadingSlash(rawApiBase);

const computeBaseUrl = (): string => {
  if (isAbsoluteUrl) {
    return stripTrailingSlash(rawApiBase);
  }
  const path = resolvePath();
  if (typeof window !== "undefined" && window.location?.origin) {
    return `${stripTrailingSlash(window.location.origin)}${path}`;
  }
  return `${getPlatformOrigin()}${path}`;
};

const computePlatformBaseUrl = (): string => {
  if (isAbsoluteUrl) {
    return stripTrailingSlash(rawApiBase);
  }
  const path = resolvePath();
  return `${getPlatformOrigin()}${path}`;
};

export const API_BASE_URL = computeBaseUrl();
export const PLATFORM_API_BASE_URL = computePlatformBaseUrl();
export const API_ROOT_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, "");
export const PLATFORM_API_ROOT_URL = PLATFORM_API_BASE_URL.replace(/\/api\/v1\/?$/, "");
