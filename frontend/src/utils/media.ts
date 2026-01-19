import api from "../services/api";

interface MediaAsset {
  id: number;
  url: string;
  original_file_name?: string | null;
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const MEDIA_BASE =
  import.meta.env.VITE_MEDIA_BASE || (API_BASE.endsWith("/api/v1") ? API_BASE.replace("/api/v1", "") : API_BASE);

export const resolveMediaUrl = (value?: string | null): string | undefined => {
  if (!value) return undefined;
  if (/^(https?:)?\/\//i.test(value) || value.startsWith("data:")) {
    return value;
  }
  if (value.startsWith("/")) {
    return `${MEDIA_BASE}${value}`;
  }
  return `${MEDIA_BASE}/${value}`;
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
