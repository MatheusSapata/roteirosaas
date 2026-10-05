<template>
  <div class="connections-view w-full space-y-6 px-4 py-6 md:px-8">
    <IntegrationsHeader />

    <section
      v-if="!agencyId"
      class="cv-alert"
    >
      Selecione uma agência no topo para gerenciar conexões do WhatsApp.
    </section>

    <div v-else class="cv-split">
      <section class="cv-panel">
        <div v-if="loading" class="space-y-3">
          <div class="h-16 animate-pulse rounded-2xl bg-muted"></div>
          <div class="h-20 animate-pulse rounded-2xl bg-muted"></div>
        </div>

        <template v-else>
          <header class="cv-head">
            <span class="cv-logo">
              <img :src="whatsAppLogo" alt="WhatsApp" class="h-5 w-5 object-contain" />
            </span>
            <div class="min-w-0 flex-1">
              <h2>WhatsApp da agência</h2>
              <p>{{ connectionName }} · conectado por QR Code. Usado no atendimento e nas mensagens automáticas.</p>
            </div>
            <span class="cv-pill" :class="statusBadgeClass">{{ statusLabel }}</span>
          </header>

          <dl class="cv-facts">
            <div>
              <dt>Situação</dt>
              <dd>{{ statusLongLabel }}</dd>
            </div>
            <div>
              <dt>Número</dt>
              <dd>{{ formattedPhone }}</dd>
            </div>
            <div>
              <dt>Última atualização</dt>
              <dd>{{ lastUpdateLabel }}</dd>
            </div>
          </dl>

          <div v-if="statusNormalized !== 'connected'" class="cv-line">
            <div>
              <p class="cv-line-title">Conectar</p>
              <p class="cv-line-text">Leia o QR Code com o WhatsApp do celular da agência.</p>
            </div>
            <button
              type="button"
              class="cv-btn cv-btn-primary"
              :disabled="working || loading || refreshing"
              @click="openQrModal"
            >
              <span v-if="working && qrModalOpen">Carregando...</span>
              <span v-else>{{ qrActionLabel }}</span>
            </button>
          </div>

          <div class="cv-line">
            <div>
              <p class="cv-line-title">Status</p>
              <p class="cv-line-text">Confira se a conexão continua ativa no celular.</p>
            </div>
            <button
              type="button"
              class="cv-btn"
              :disabled="working || loading || refreshing"
              @click="reload"
            >
              <span v-if="refreshing">Atualizando...</span>
              <span v-else>Atualizar status</span>
            </button>
          </div>

          <div class="cv-line">
            <div>
              <p class="cv-line-title">Desconectar</p>
              <p class="cv-line-text">As mensagens automáticas param até conectar de novo.</p>
            </div>
            <button
              type="button"
              class="cv-btn cv-btn-danger"
              :disabled="working || !connection || statusNormalized === 'disconnected'"
              @click="handleDisconnect"
            >
              <span v-if="working && disconnecting">Desconectando...</span>
              <span v-else>Desconectar</span>
            </button>
          </div>

          <p class="cv-note">Cada agência pode ter 1 conexão de WhatsApp.</p>
        </template>
      </section>

      <aside class="cv-info">
        <span class="cv-info-icon" aria-hidden="true">
          <InfoIcon aria-hidden="true" />
        </span>
        <div>
          <p class="cv-info-title">Onde o WhatsApp é usado</p>
          <p class="cv-info-text">Nas mensagens automáticas dos formulários (Captação de leads › Formulários) e na caixa de entrada de atendimento.</p>
        </div>
      </aside>
    </div>

    <Teleport to="body">
      <div v-if="qrModalOpen" class="app-modal-overlay fixed inset-0 z-[180] flex items-center justify-center px-3 md:px-4">
        <div class="w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-4 shadow-2xl md:p-6">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div class="flex items-center gap-3">
              <span class="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#dcfce7] text-[#16a34a]">
                <img :src="whatsAppLogo" alt="WhatsApp" class="h-5 w-5 object-contain" />
              </span>
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">WhatsApp</p>
                <h3 class="mt-1 text-xl font-bold text-slate-900 md:text-2xl">Conectar dispositivo</h3>
              </div>
            </div>
            <button
              type="button"
              class="rounded-full border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50"
              @click="closeQrModal"
            >
              <XIcon class="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div v-if="qrLoading" class="space-y-3">
              <div class="mx-auto h-64 w-64 animate-pulse rounded-xl border border-slate-200 bg-white"></div>
              <div class="mx-auto h-3 w-44 animate-pulse rounded bg-slate-200"></div>
            </div>

            <div v-else-if="qrImage" class="space-y-3">
              <div class="flex items-center justify-center">
                <img :src="qrImage" alt="QR Code WhatsApp" class="h-64 w-64 rounded-xl border border-slate-200 bg-white p-2" />
              </div>
              <p class="text-center text-xs text-slate-500">Escaneie o QR para concluir o pareamento</p>
            </div>

            <div v-else class="space-y-3 py-8 text-center">
              <p class="text-sm font-semibold text-rose-700">Não foi possível carregar o QR Code.</p>
              <p v-if="pairingCode" class="text-sm text-slate-700">Pairing code: <strong>{{ pairingCode }}</strong></p>
              <button
                type="button"
                class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
                @click="fetchQr"
              >
                Tentar novamente
              </button>
            </div>
          </div>

          <div class="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p class="text-sm text-slate-700">Abra o WhatsApp no celular e vá em Aparelhos conectados.</p>
            <p class="mt-2 text-sm font-semibold" :class="statusTextClass">{{ statusHint }}</p>
          </div>
        </div>
      </div>

      <div
        v-if="toastMessage"
        class="app-snackbar-layer z-[200] rounded-full border px-4 py-2 text-sm font-semibold shadow-lg"
        :class="toastError ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'"
      >
        {{ toastMessage }}
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.connections-view { color: var(--foreground); }
.connections-view :deep(.bg-white),
.connections-view :deep(.from-white) { background: var(--card) !important; }
.connections-view :deep(.bg-slate-50),
.connections-view :deep(.bg-slate-100),
.connections-view :deep(.to-slate-50) { background: var(--muted) !important; }
.connections-view :deep(.border-slate-200),
.connections-view :deep(.border-slate-300) { border-color: var(--border) !important; }
.connections-view :deep(.text-slate-900),
.connections-view :deep(.text-slate-800),
.connections-view :deep(.text-slate-700) { color: var(--foreground) !important; }
.connections-view :deep(.text-slate-600),
.connections-view :deep(.text-slate-500) { color: var(--muted-foreground) !important; }
.connections-view :deep(input),
.connections-view :deep(select),
.connections-view :deep(textarea) {
  border-color: var(--input) !important;
  background: var(--background) !important;
  color: var(--foreground) !important;
}

/* Redesign: notificações (WhatsApp) */
.cv-alert { border-radius: 16px; background: var(--status-warning); padding: 14px 16px; font-size: 14px; color: var(--status-warning-foreground); }
.cv-split { display: grid; grid-template-columns: minmax(0, 1fr) 360px; align-items: start; gap: 16px; }
.cv-panel { border-radius: 20px; background: var(--card); padding: 20px; box-shadow: var(--shadow-card); }
.cv-head { display: flex; align-items: flex-start; gap: 12px; }
.cv-head h2 { font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--foreground); }
.cv-head p { margin-top: 2px; font-size: 13px; color: var(--muted-foreground); }
.cv-logo { display: grid; place-items: center; width: 44px; height: 44px; flex-shrink: 0; border-radius: 14px; background: var(--status-success); }
.cv-pill { flex-shrink: 0; border: 0 !important; border-radius: 999px; padding: 2px 10px; font-size: 12px; font-weight: 600; }
.cv-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 16px 0 4px; }
.cv-facts > div { border-radius: 14px; background: var(--muted); padding: 10px 14px; }
.cv-facts dt { font-size: 12px; color: var(--muted-foreground); }
.cv-facts dd { margin-top: 2px; font-size: 14.5px; font-weight: 600; color: var(--foreground); }
.cv-line { display: flex; align-items: center; justify-content: space-between; gap: 16px; border-top: 1px solid var(--border); padding: 14px 0; }
.cv-line-title { font-size: 14px; font-weight: 600; color: var(--foreground); }
.cv-line-text { margin-top: 2px; font-size: 12.5px; color: var(--muted-foreground); }
.cv-btn { flex-shrink: 0; height: 36px; padding: 0 16px; border-radius: 999px; background: var(--muted); font-size: 13px; font-weight: 600; color: var(--foreground); }
.cv-btn:hover:not(:disabled) { background: var(--accent); color: var(--accent-foreground); }
.cv-btn:disabled { cursor: not-allowed; opacity: 0.55; }
.cv-btn-primary { background: var(--primary); color: var(--primary-foreground); }
.cv-btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 88%, black); color: var(--primary-foreground); }
.cv-btn-danger { background: var(--status-danger); color: var(--status-danger-foreground); }
.cv-note { border-radius: 14px; background: var(--status-info); padding: 10px 14px; font-size: 12.5px; color: var(--status-info-foreground); }
.cv-info { display: flex; gap: 12px; border-radius: 20px; background: var(--card); padding: 18px; box-shadow: var(--shadow-card); }
.cv-info-icon { display: grid; place-items: center; width: 36px; height: 36px; flex-shrink: 0; border-radius: 999px; background: var(--status-success); color: var(--status-success-foreground); }
.cv-info-icon svg { width: 18px; height: 18px; }
.cv-info-title { font-size: 14px; font-weight: 600; color: var(--foreground); }
.cv-info-text { margin-top: 4px; font-size: 12.5px; line-height: 1.55; color: var(--muted-foreground); }
@media (max-width: 1024px) { .cv-split { grid-template-columns: 1fr; } }
@media (max-width: 640px) {
  .cv-facts { grid-template-columns: 1fr; }
  .cv-line { flex-direction: column; align-items: flex-start; }
}
</style>

<script setup lang="ts">
import { InfoIcon, XIcon } from "lucide-vue-next";
import IntegrationsHeader from "../../components/admin/integrations/IntegrationsHeader.vue";
import { integrationStatus } from "../../composables/useIntegrationStatus";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useAgencyStore } from "../../store/useAgencyStore";
import {
  createWhatsAppConnection,
  disconnectWhatsAppConnection,
  getWhatsAppConnectionQr,
  getWhatsAppConnectionStatus,
  listWhatsAppConnections
} from "../../services/whatsapp";
import type { WhatsAppConnection, WhatsAppConnectionStatus } from "../../types/whatsapp";
import whatsAppLogo from "../../assets/whatsapp-logo.svg";

const agencyStore = useAgencyStore();

const loading = ref(false);
const refreshing = ref(false);
const working = ref(false);
const disconnecting = ref(false);
const connection = ref<WhatsAppConnection | null>(null);
const statusValue = ref<WhatsAppConnectionStatus>("disconnected");
const lastStatusUpdateAt = ref<Date | null>(null);

const qrModalOpen = ref(false);
const qrLoading = ref(false);
const qrImage = ref("");
const pairingCode = ref("");
const statusHint = ref("Aguardando leitura...");
const closingAfterSuccess = ref(false);

const toastMessage = ref("");
const toastError = ref(false);

let toastTimer: ReturnType<typeof setTimeout> | null = null;
let statusInterval: ReturnType<typeof setInterval> | null = null;
let qrCloseTimer: ReturnType<typeof setTimeout> | null = null;

const agencyId = computed(() => agencyStore.currentAgencyId);

const statusNormalized = computed<WhatsAppConnectionStatus>(() => {
  const raw = String(statusValue.value || "").toLowerCase();
  if (raw === "connected") return "connected";
  if (raw === "connecting" || raw === "open") return "connecting";
  if (raw === "qr_needed") return "qr_needed";
  if (raw === "error") return "error";
  return "disconnected";
});

const selectedAgencyName = computed(() => {
  const id = agencyId.value;
  if (!id) return "";
  return agencyStore.agencies.find(item => item.id === id)?.name?.trim() || "";
});

const connectionName = computed(() => {
  if (selectedAgencyName.value) return `Conexão Agência ${selectedAgencyName.value}`;
  return connection.value?.name || "Conexão WhatsApp";
});

const statusLabel = computed(() => {
  if (statusNormalized.value === "connected") return "Conectado";
  if (statusNormalized.value === "connecting" || statusNormalized.value === "qr_needed") return "Conectando";
  if (statusNormalized.value === "error") return "Erro";
  return "Desconectado";
});

const statusLongLabel = computed(() => {
  if (statusNormalized.value === "connected") return "Conexão ativa e pronta para uso";
  if (statusNormalized.value === "connecting" || statusNormalized.value === "qr_needed") return "Aguardando pareamento por QR Code";
  if (statusNormalized.value === "error") return "Falha de conexão com o canal";
  return "Canal desconectado";
});

const statusBadgeClass = computed(() => {
  if (statusNormalized.value === "connected") return "bg-status-success text-status-success-foreground";
  if (statusNormalized.value === "connecting" || statusNormalized.value === "qr_needed") return "bg-status-warning text-status-warning-foreground";
  return "bg-status-danger text-status-danger-foreground";
});

watch(statusNormalized, value => { integrationStatus.whatsapp = value === "connected"; }, { immediate: true });

const statusTextClass = computed(() => {
  if (statusNormalized.value === "connected") return "text-emerald-700";
  if (statusNormalized.value === "connecting" || statusNormalized.value === "qr_needed") return "text-amber-700";
  return "text-rose-700";
});

const qrActionLabel = computed(() => (connection.value ? "Ver QR Code" : "Conectar WhatsApp"));

const formattedPhone = computed(() => formatPhone(connection.value?.phoneNumber || ""));

const lastUpdateLabel = computed(() => {
  if (!lastStatusUpdateAt.value) return "â€”";
  const diff = Date.now() - lastStatusUpdateAt.value.getTime();
  if (diff < 60000) return "agora";
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins} min atrás`;
  return lastStatusUpdateAt.value.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
});

const showToast = (message: string, isError = false) => {
  toastMessage.value = message;
  toastError.value = isError;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMessage.value = "";
    toastError.value = false;
  }, 3200);
};

const clearStatusPolling = () => {
  if (statusInterval) {
    clearInterval(statusInterval);
    statusInterval = null;
  }
};

const clearCloseTimer = () => {
  if (qrCloseTimer) {
    clearTimeout(qrCloseTimer);
    qrCloseTimer = null;
  }
};

const markUpdated = () => {
  lastStatusUpdateAt.value = new Date();
};

const formatPhone = (raw: string) => {
  const digits = String(raw || "").replace(/\D+/g, "");
  if (!digits) return "Não conectado";
  const country = digits.startsWith("55") ? "55" : "";
  const local = country ? digits.slice(2) : digits;
  if (local.length < 10) return `+${digits}`;
  const ddd = local.slice(0, 2);
  const prefix = local.length >= 9 ? local.slice(2, 7) : local.slice(2, 6);
  const suffix = local.length >= 9 ? local.slice(7, 11) : local.slice(6, 10);
  const cc = country || "55";
  return `+${cc} ${ddd} ${prefix}-${suffix}`;
};

const normalizePhoneCandidate = (input: unknown): string | null => {
  if (!input) return null;
  const raw = String(input);
  const clean = raw.replace(/@s\.whatsapp\.net$/i, "").replace(/\D+/g, "");
  if (clean.length < 10) return null;
  return clean;
};

const extractPhoneFromStatusPayload = (payload: unknown): string | null => {
  if (!payload || typeof payload !== "object") return null;
  const queue: unknown[] = [payload];
  const keys = ["phone", "phoneNumber", "number", "ownerJid", "wid", "user"];
  while (queue.length) {
    const current = queue.shift();
    if (!current || typeof current !== "object") continue;
    const record = current as Record<string, unknown>;
    for (const key of keys) {
      const phone = normalizePhoneCandidate(record[key]);
      if (phone) return phone;
    }
    for (const value of Object.values(record)) {
      if (value && typeof value === "object") queue.push(value);
    }
  }
  return null;
};

const updateStatus = async () => {
  if (!agencyId.value || !connection.value) return;
  try {
    const response = await getWhatsAppConnectionStatus(connection.value.id, agencyId.value);
    statusValue.value = (response.status as WhatsAppConnectionStatus) || "disconnected";
    const extractedPhone = extractPhoneFromStatusPayload(response.raw);
    if (extractedPhone && connection.value) {
      connection.value = { ...connection.value, phoneNumber: extractedPhone };
    }
    markUpdated();
    if (statusNormalized.value === "connected") {
      statusHint.value = "Conectado com sucesso.";
      if (!closingAfterSuccess.value) {
        closingAfterSuccess.value = true;
        showToast("WhatsApp conectado com sucesso.");
        clearStatusPolling();
        clearCloseTimer();
        qrCloseTimer = setTimeout(async () => {
          qrModalOpen.value = false;
          closingAfterSuccess.value = false;
          await loadConnections(true);
        }, 1200);
      }
    } else if (statusNormalized.value === "connecting" || statusNormalized.value === "qr_needed") {
      statusHint.value = "Aguardando leitura...";
    } else if (statusNormalized.value === "error") {
      statusHint.value = "Erro ao conectar. Tente gerar um novo QR.";
    } else {
      statusHint.value = "Desconectado.";
    }
  } catch {
    statusHint.value = "Erro ao consultar status da conexão.";
  }
};

const startStatusPolling = () => {
  clearStatusPolling();
  statusInterval = setInterval(() => {
    void updateStatus();
  }, 3000);
};

const loadConnections = async (silent = false) => {
  if (!agencyId.value) {
    connection.value = null;
    statusValue.value = "disconnected";
    return;
  }
  if (silent) refreshing.value = true;
  else loading.value = true;

  try {
    const rows = await listWhatsAppConnections(agencyId.value);
    const first = Array.isArray(rows) && rows.length > 0 ? rows[0] : null;
    connection.value = first;
    statusValue.value = (first?.status as WhatsAppConnectionStatus) || "disconnected";
    markUpdated();
  } catch {
    showToast("Não foi possível carregar conexões.", true);
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
};

const ensureConnection = async () => {
  if (!agencyId.value) return null;
  if (connection.value) return connection.value;
  const created = await createWhatsAppConnection({
    agencyId: agencyId.value,
    name: "Conexão WhatsApp"
  });
  connection.value = created;
  statusValue.value = (created.status as WhatsAppConnectionStatus) || "connecting";
  markUpdated();
  showToast("Conexão criada com sucesso.");
  return created;
};

const fetchQr = async () => {
  if (!agencyId.value || !connection.value) return;
  qrLoading.value = true;
  qrImage.value = "";
  pairingCode.value = "";
  try {
    const response = await getWhatsAppConnectionQr(connection.value.id, agencyId.value);
    const base64 = String(response.qr_code_base64 || "").trim();
    const pair = String(response.pairing_code || response.code || "").trim();
    if (base64) {
      qrImage.value = base64.startsWith("data:image") ? base64 : `data:image/png;base64,${base64}`;
      showToast("QR Code carregado.");
    }
    if (pair) pairingCode.value = pair;
    statusHint.value = base64 || pair ? "Aguardando leitura..." : "QR indisponível no momento. Tente novamente.";
    if (!base64 && !pair) {
      showToast("QR Code vazio no momento. Tente novamente.", true);
    }
  } catch {
    statusHint.value = "Erro ao buscar QR Code.";
    showToast("Erro ao carregar QR Code.", true);
  } finally {
    qrLoading.value = false;
  }
};

const openQrModal = async () => {
  if (!agencyId.value) {
    showToast("Selecione uma agência para conectar o WhatsApp.", true);
    return;
  }
  try {
    working.value = true;
    disconnecting.value = false;
    closingAfterSuccess.value = false;
    clearCloseTimer();
    qrModalOpen.value = true;
    const ensured = await ensureConnection();
    if (!ensured) {
      showToast("Não foi possível iniciar a conexão.", true);
      return;
    }
    await fetchQr();
    await updateStatus();
    startStatusPolling();
  } catch (error: any) {
    const detail = error?.response?.data?.detail || "Falha ao iniciar conexão do WhatsApp.";
    showToast(detail, true);
  } finally {
    working.value = false;
  }
};

const closeQrModal = () => {
  qrModalOpen.value = false;
  clearStatusPolling();
  clearCloseTimer();
  closingAfterSuccess.value = false;
};

const handleDisconnect = async () => {
  if (!agencyId.value || !connection.value) return;
  try {
    working.value = true;
    disconnecting.value = true;
    await disconnectWhatsAppConnection(connection.value.id, agencyId.value);
    statusValue.value = "disconnected";
    markUpdated();
    showToast("Conexão desconectada.");
    await loadConnections(true);
  } catch {
    showToast("Erro ao desconectar o WhatsApp.", true);
  } finally {
    working.value = false;
    disconnecting.value = false;
  }
};

const reload = async () => {
  await loadConnections(true);
  await updateStatus();
  showToast("Status atualizado.");
};

watch(
  () => agencyId.value,
  () => {
    closeQrModal();
    qrImage.value = "";
    pairingCode.value = "";
    statusHint.value = "Aguardando leitura...";
    lastStatusUpdateAt.value = null;
    void loadConnections();
  },
  { immediate: true }
);

onMounted(() => {
  if (!agencyStore.agencies.length) {
    void agencyStore.loadAgencies().catch(() => undefined);
  }
});

onBeforeUnmount(() => {
  closeQrModal();
  if (toastTimer) clearTimeout(toastTimer);
});
</script>


