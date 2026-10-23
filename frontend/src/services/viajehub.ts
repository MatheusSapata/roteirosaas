import api from "./api";

// Conexão com o funil do ViajeHub (Admin Master › Integrações › ViajeHub). A chave fica
// criptografada no servidor; aqui só chegam os quatro últimos caracteres.
export interface ViajeHubConnection {
  url: string;
  key_masked: string;
  has_key: boolean;
  // "painel" (salvo nesta tela), "ambiente" (.env da VPS) ou "" (sem conexão).
  source: "painel" | "ambiente" | "";
}

const base = "/admin/admin-master/viajehub";

export const getViajeHubConnection = async () => (await api.get<ViajeHubConnection>(base)).data;

export const saveViajeHubConnection = async (payload: { url: string; key?: string }) =>
  (await api.put<ViajeHubConnection>(base, payload)).data;

export const deleteViajeHubConnection = async () => (await api.delete<ViajeHubConnection>(base)).data;

export const testViajeHubConnection = async () =>
  (await api.post<{ ok: boolean; message: string }>(`${base}/test`)).data;
