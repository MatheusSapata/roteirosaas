import { reactive } from "vue";
import api from "../services/api";

// Contadores do menu do admin master: quem está online e WhatsApp com problema.
export const adminMasterCounts = reactive<{ online: number | null; whatsappIssues: number | null }>({
  online: null,
  whatsappIssues: null
});

let lastLoad = 0;

export const loadAdminMasterCounts = async (force = false) => {
  if (!force && Date.now() - lastLoad < 60_000) return;
  lastLoad = Date.now();
  const [online, whatsapp] = await Promise.allSettled([
    api.get<{ unique_users: number }>("/admin/online-sessions"),
    api.get<{ disconnected_connections: number }>("/admin-master/whatsapp/overview")
  ]);
  if (online.status === "fulfilled") adminMasterCounts.online = online.value.data?.unique_users ?? 0;
  if (whatsapp.status === "fulfilled") adminMasterCounts.whatsappIssues = whatsapp.value.data?.disconnected_connections ?? 0;
};
