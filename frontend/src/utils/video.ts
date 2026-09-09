const ensureHttps = (value: string) => {
  if (!value) return "";
  if (!/^https?:\/\//i.test(value)) {
    return `https://${value.replace(/^\/+/, "")}`;
  }
  return value.replace(/^http:\/\//i, "https://");
};

const stripIframeWrapper = (raw: string) => {
  const iframeSrc = raw.match(/src=["']([^"']+)["']/i);
  return iframeSrc?.[1] ? iframeSrc[1] : raw;
};

export const extractYoutubeId = (raw?: string | null): string => {
  if (!raw) return "";
  const normalized = ensureHttps(stripIframeWrapper(raw.trim()));
  const patterns = [
    /youtube\.com\/embed\/([a-zA-Z0-9_-]+)/i,
    /youtu\.be\/([a-zA-Z0-9_-]+)/i,
    /youtube\.com\/shorts\/([a-zA-Z0-9_-]+)/i,
    /[?&]v=([a-zA-Z0-9_-]+)/i
  ];
  for (const pattern of patterns) {
    const match = normalized.match(pattern);
    if (match?.[1]) return match[1];
  }
  return "";
};

export const normalizeYoutubeEmbedUrl = (raw?: string | null): string => {
  if (!raw) return "";
  const id = extractYoutubeId(raw);
  if (id) {
    return `https://www.youtube.com/embed/${id}`;
  }
  return ensureHttps(stripIframeWrapper(raw.trim()));
};

export const normalizeYoutubePlayerUrl = (raw?: string | null): string => {
  const id = extractYoutubeId(raw);
  if (!id) return "";
  const origin = typeof window !== "undefined" ? `&origin=${encodeURIComponent(window.location.origin)}` : "";
  return `https://www.youtube.com/embed/${id}?enablejsapi=1&playsinline=1&controls=0&disablekb=1&fs=0&iv_load_policy=3&cc_load_policy=0&rel=0${origin}`;
};
