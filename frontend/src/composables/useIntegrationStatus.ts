import { reactive } from "vue";
import api from "../services/api";
import { listWhatsAppConnections } from "../services/whatsapp";

// Situação de cada integração, usada nos pontos das abas de Integrações.
// As telas atualizam este estado quando conectam ou desconectam algo.
export const integrationStatus = reactive({
  pixels: null as number | null,
  viajeon: null as boolean | null,
  viajechat: null as boolean | null,
  whatsapp: null as boolean | null
});

export const loadWhatsAppStatus = async (agencyId: number | string) => {
  try {
    const rows = await listWhatsAppConnections(Number(agencyId));
    const first = Array.isArray(rows) && rows.length ? rows[0] : null;
    integrationStatus.whatsapp = String(first?.status || "").toLowerCase() === "connected";
  } catch {
    integrationStatus.whatsapp = false;
  }
};

export const loadIntegrationStatus = async (options: { agencyId?: number | string | null; whatsapp?: boolean } = {}) => {
  const tasks: Promise<unknown>[] = [
    api.get("/pixels/").then(res => {
      integrationStatus.pixels = Array.isArray(res.data) ? res.data.length : 0;
    }),
    api.get("/integrations/viajeon").then(res => {
      integrationStatus.viajeon = !!res.data?.connected;
    }),
    api.get("/integrations/viajechat").then(res => {
      integrationStatus.viajechat = !!res.data?.configured;
    })
  ];
  if (options.whatsapp && options.agencyId) tasks.push(loadWhatsAppStatus(options.agencyId));
  await Promise.allSettled(tasks);
};
