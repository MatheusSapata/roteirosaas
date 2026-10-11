import api from "./api";
import type { FlightApiKey } from "./flightDetails";

// Chaves dos bancos de fotos (Unsplash e Pexels). Mesmo formato das chaves de voo, mas
// "monthly_limit" é o limite POR HORA e "monthly_usage_estimated" o uso da hora atual.
export type ImageApiKey = FlightApiKey;
export type ImageProvider = "unsplash" | "pexels";

export interface ImageProviderSummary {
  keys: number;
  active_keys: number;
  hour_usage: number;
  hour_limit: number;
  env_key: boolean;
}

export interface ImageApiKeysResponse {
  items: ImageApiKey[];
  summary: {
    searches: number;
    photos: number;
    photo_uses: number;
    search_reuses: number;
    curated_photos: number;
    unsplash: ImageProviderSummary;
    pexels: ImageProviderSummary;
  };
}

const base = "/admin/master/image-api-keys";

export const listImageApiKeys = async () => (await api.get<ImageApiKeysResponse>(base)).data;

export const createImageApiKey = async (payload: {
  provider: ImageProvider;
  label: string;
  api_key: string;
  priority: number;
  hourly_limit: number;
  is_active: boolean;
  notes?: string;
}) => (await api.post<ImageApiKey>(base, payload)).data;

export const updateImageApiKey = async (
  id: number,
  payload: { label?: string; api_key?: string; priority?: number; hourly_limit?: number; is_active?: boolean; notes?: string }
) => (await api.patch<ImageApiKey>(`${base}/${id}`, payload)).data;

export const testImageApiKey = async (id: number) =>
  (await api.post<{ detail: string; remaining_this_hour: number | null }>(`${base}/${id}/test`)).data;

export const pauseImageApiKey = async (id: number) => (await api.post<ImageApiKey>(`${base}/${id}/pause`)).data;
export const activateImageApiKey = async (id: number) => (await api.post<ImageApiKey>(`${base}/${id}/activate`)).data;
export const resetImageApiKeyUsage = async (id: number) => (await api.post<ImageApiKey>(`${base}/${id}/reset-usage`)).data;
export const deleteImageApiKey = async (id: number) => (await api.delete<{ detail: string }>(`${base}/${id}`)).data;

// Fotos cadastradas à mão (qualquer site), com palavras-chave e crédito: a IA usa antes dos bancos.
export interface StockPhoto {
  id: number;
  url: string;
  original_url: string;
  keywords: string[];
  description: string | null;
  author: string | null;
  author_url: string | null;
  source_name: string | null;
  source_url: string | null;
  width: number | null;
  height: number | null;
  uses: number;
  created_at: string | null;
}

export interface StockPhotoPayload {
  url?: string;
  keywords: string;
  description?: string;
  author?: string;
  author_url?: string;
  source_name?: string;
  source_url?: string;
}

const photoBase = "/admin/master/stock-photos";

export const listStockPhotos = async (q?: string) =>
  (await api.get<StockPhoto[]>(photoBase, { params: q ? { q } : undefined })).data;
export const createStockPhoto = async (payload: StockPhotoPayload & { url: string }) =>
  (await api.post<StockPhoto>(photoBase, payload)).data;
export const updateStockPhoto = async (id: number, payload: StockPhotoPayload) =>
  (await api.patch<StockPhoto>(`${photoBase}/${id}`, payload)).data;
export const deleteStockPhoto = async (id: number) => (await api.delete<{ detail: string }>(`${photoBase}/${id}`)).data;

export interface StockPhotoCredits {
  keywords: string;
  author?: string;
  author_url?: string;
  source_name?: string;
  source_url?: string;
}

/** Uma foto do computador; `path` (pastas + nome) vira contexto nas palavras-chave. */
export const uploadStockPhoto = async (file: File, path: string, fields: StockPhotoCredits) => {
  const form = new FormData();
  form.append("file", file);
  form.append("path", path);
  Object.entries(fields).forEach(([key, value]) => form.append(key, value || ""));
  return (await api.post<StockPhoto>(`${photoBase}/upload`, form)).data;
};

export interface StockPhotoImportJob {
  id: string;
  status: "running" | "done" | "error";
  total: number;
  added: number;
  duplicates: number;
  skipped: string[];
  error: string | null;
}

export const importStockPhotosFromLink = async (url: string, fields: StockPhotoCredits) =>
  (await api.post<StockPhotoImportJob>(`${photoBase}/import-link`, { url, ...fields })).data;
export const getStockPhotoImport = async (id: string) =>
  (await api.get<StockPhotoImportJob>(`${photoBase}/import-link/${id}`)).data;
