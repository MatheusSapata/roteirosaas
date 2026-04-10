import api from "./api";

export interface MediaProxyResponse {
  data_url: string;
}

export const fetchMediaDataUrl = async (url: string): Promise<string | null> => {
  if (!url) return null;
  try {
    const { data } = await api.get<MediaProxyResponse>("/media/proxy/logo", {
      params: { url }
    });
    return data.data_url;
  } catch (err) {
    console.error("Erro ao buscar logo via proxy", err);
    return null;
  }
};
