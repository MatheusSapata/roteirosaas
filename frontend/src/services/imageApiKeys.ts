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
