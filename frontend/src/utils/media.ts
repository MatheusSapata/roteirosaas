import api from "../services/api";
import placeholderAsset from "../assets/placeholder.png";

interface MediaAsset {
  id: number;
  url: string;
  original_file_name?: string | null;
}

const buildMediaBase = () => {
  const explicit = import.meta.env.VITE_MEDIA_BASE;
  if (explicit) return explicit.endsWith("/") ? explicit.slice(0, -1) : explicit;

  const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
  if (apiBase.endsWith("/api/v1")) {
    return `${apiBase.replace(/\/api\/v1$/, "")}/uploads`;
  }
  return `${apiBase.replace(/\/$/, "")}/uploads`;
};

const MEDIA_BASE = buildMediaBase();
const ABSOLUTE_MEDIA_BASE = /^https?:\/\//i.test(MEDIA_BASE);

const ensureLeadingSlash = (value: string) => (value.startsWith("/") ? value : `/${value}`);

const PUBLIC_ASSET_PREFIXES = ["/assets/", "assets/", "/src/assets/"];
const PLACEHOLDER_PATHS = new Set(["/placeholder.png", "placeholder.png"]);

export const resolveMediaUrl = (value?: string | null): string | undefined => {
  if (!value) return undefined;
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  if (PLACEHOLDER_PATHS.has(trimmed)) {
    return placeholderAsset;
  }
  if (/^(https?:)?\/\//i.test(trimmed) || trimmed.startsWith("data:")) {
    return trimmed;
  }
  const publicPrefix = PUBLIC_ASSET_PREFIXES.find(prefix => trimmed.startsWith(prefix));
  if (publicPrefix) {
    return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  }
  const normalized = ensureLeadingSlash(trimmed);

  if (ABSOLUTE_MEDIA_BASE) {
    try {
      const url = new URL(MEDIA_BASE.endsWith("/") ? MEDIA_BASE : `${MEDIA_BASE}/`);
      const basePath = url.pathname.replace(/\/$/, "") || "/";
      if (normalized.startsWith(basePath)) {
        return `${url.origin}${normalized}`;
      }
      const composed = `${basePath}${normalized}`.replace(/\/{2,}/g, "/");
      return `${url.origin}${composed.startsWith("/") ? composed : `/${composed}`}`;
    } catch {
      const base = MEDIA_BASE.replace(/\/$/, "");
      return `${base}${normalized}`;
    }
  }

  const basePath = ensureLeadingSlash(MEDIA_BASE);
  if (normalized.startsWith(basePath)) {
    return normalized;
  }
  return `${basePath}${normalized}`.replace(/\/{2,}/g, "/");
};

export const uploadImageFile = async (file: File, agencyId: number): Promise<MediaAsset> => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<MediaAsset>("/media/upload", formData, {
    params: { agency_id: agencyId },
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};
