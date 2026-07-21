import api from "../services/api";
import { API_BASE_URL, API_ROOT_URL } from "./apiBase";

interface MediaAsset {
  id: number;
  url: string;
  original_file_name?: string | null;
}

const buildMediaBase = () => {
  const explicit = import.meta.env.VITE_MEDIA_BASE;
  if (explicit) return explicit.endsWith("/") ? explicit.slice(0, -1) : explicit;

  if (API_BASE_URL.endsWith("/api/v1")) {
    return `${API_ROOT_URL}/uploads`;
  }
  return `${API_BASE_URL.replace(/\/$/, "")}/uploads`;
};

const MEDIA_BASE = buildMediaBase();
const ABSOLUTE_MEDIA_BASE = /^https?:\/\//i.test(MEDIA_BASE);

const ensureLeadingSlash = (value: string) => (value.startsWith("/") ? value : `/${value}`);

export const resolveMediaUrl = (value?: string | null): string | undefined => {
  if (!value) return undefined;
  if (/^(https?:)?\/\//i.test(value) || value.startsWith("data:")) {
    return value;
  }
  if (value.startsWith("/assets/") || value.startsWith("assets/") || value.startsWith("/src/assets/")) {
    return value.startsWith("/") ? value : `/${value}`;
  }
  const normalized = ensureLeadingSlash(value);

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

const blobToDataUrl = (blob: Blob): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("Não foi possível ler a imagem processada."));
    reader.readAsDataURL(blob);
  });

export const removeImageBackground = async (source: string, agencyId: number): Promise<string> => {
  const sourceResponse = await fetch(source);
  if (!sourceResponse.ok) {
    throw new Error("Não foi possível carregar a imagem selecionada.");
  }
  const sourceBlob = await sourceResponse.blob();
  if (!sourceBlob.type.startsWith("image/")) {
    throw new Error("O arquivo selecionado não é uma imagem válida.");
  }

  const extension = sourceBlob.type.split("/")[1]?.replace("jpeg", "jpg") || "png";
  const formData = new FormData();
  formData.append("file", new File([sourceBlob], `background-source.${extension}`, { type: sourceBlob.type }));
  const response = await api.post<Blob>("/media/remove-background", formData, {
    params: { agency_id: agencyId },
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob"
  });
  return blobToDataUrl(response.data);
};
