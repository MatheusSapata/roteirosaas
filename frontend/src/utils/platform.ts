const defaultPlatformHosts = ["roteiroonline.com", "www.roteiroonline.com", "localhost", "127.0.0.1"];

const envPlatformHosts = (import.meta.env.VITE_PLATFORM_HOSTS || "")
  .split(",")
  .map(host => host.trim().toLowerCase())
  .filter(Boolean);

const sanitizeHost = (value?: string | null) => (value || "").trim().toLowerCase();

export const PLATFORM_HOSTS = Array.from(new Set([...defaultPlatformHosts, ...envPlatformHosts]));

export const isPlatformHostname = (host?: string | null) => {
  const normalized = sanitizeHost(host);
  if (!normalized) return false;
  return PLATFORM_HOSTS.includes(normalized);
};

export const isCurrentHostPlatform = () => {
  if (typeof window === "undefined") return true;
  return isPlatformHostname(window.location.hostname);
};

const stripTrailingSlash = (value: string) => value.replace(/\/+$/, "");

const resolvePreferredPlatformHost = () => {
  const preferred = PLATFORM_HOSTS.find(
    host => host && host !== "localhost" && host !== "127.0.0.1"
  );
  return preferred || PLATFORM_HOSTS[0] || "localhost";
};

const computedPlatformOrigin = (() => {
  const explicitOrigin = (import.meta.env.VITE_PLATFORM_ORIGIN || "").trim();
  if (explicitOrigin) {
    return stripTrailingSlash(explicitOrigin);
  }

  const preferredHost = resolvePreferredPlatformHost();
  if (!preferredHost) {
    return "http://localhost:5173";
  }

  if (preferredHost.startsWith("http://") || preferredHost.startsWith("https://")) {
    return stripTrailingSlash(preferredHost);
  }

  if (preferredHost.startsWith("localhost") || preferredHost.startsWith("127.0.0.1")) {
    return stripTrailingSlash(`http://${preferredHost}`);
  }

  return stripTrailingSlash(`https://${preferredHost}`);
})();

export const getPlatformOrigin = () => computedPlatformOrigin;
