<template>
  <div class="w-full space-y-6 px-4 py-6 md:px-8">
    <header class="space-y-1">
      <h1 class="text-3xl font-bold text-slate-900">Atendimento</h1>
      <p class="text-sm text-slate-600">Conecte os canais de atendimento da sua agência.</p>
    </header>

    <section
      v-if="!agencyId"
      class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800"
    >
      Selecione uma agência no topo para gerenciar conexões do WhatsApp.
    </section>

    <section v-else class="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm md:p-6">
      <div class="mb-5 flex items-center justify-between gap-3">
        <h2 class="text-lg font-semibold text-slate-900">Canal de atendimento</h2>
        <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">MVP: 1 conexão</span>
      </div>

      <div v-if="loading" class="space-y-3">
        <div class="h-28 animate-pulse rounded-2xl bg-slate-100"></div>
        <div class="h-28 animate-pulse rounded-2xl bg-slate-100"></div>
      </div>

      <article v-else class="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-4 shadow-sm md:p-5">
        <div class="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-3">
              <span class="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#dcfce7] text-[#16a34a]">
                <img :src="whatsAppLogo" alt="WhatsApp" class="h-5 w-5 object-contain" />
              </span>
              <div class="min-w-0">
                <p class="truncate text-base font-semibold text-slate-900">{{ connectionName }}</p>
                <p class="text-xs text-slate-500">WhatsApp oficial via QR Code</p>
              </div>
              <span class="inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold" :class="statusBadgeClass">
                {{ statusLabel }}
              </span>
            </div>

            <dl class="mt-4 grid grid-cols-1 gap-3 text-sm text-slate-700 md:grid-cols-3">
              <div>
                <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</dt>
                <dd class="mt-1 font-medium text-slate-900">{{ statusLongLabel }}</dd>
              </div>
              <div>
                <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Número</dt>
                <dd class="mt-1 font-medium text-slate-900">{{ formattedPhone }}</dd>
              </div>
              <div>
                <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Última atualização</dt>
                <dd class="mt-1 font-medium text-slate-900">{{ lastUpdateLabel }}</dd>
              </div>
            </dl>
          </div>

          <div class="grid grid-cols-1 gap-2 sm:grid-cols-3 lg:w-[430px]">
            <button
              v-if="statusNormalized !== 'connected'"
              type="button"
              class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="working || loading || refreshing"
              @click="openQrModal"
            >
              <span v-if="working && qrModalOpen">Carregando...</span>
              <span v-else>{{ qrActionLabel }}</span>
            </button>

            <button
              type="button"
              class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="working || loading || refreshing"
              @click="reload"
            >
              <span v-if="refreshing">Atualizando...</span>
              <span v-else>Atualizar</span>
            </button>

            <button
              type="button"
              class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="working || !connection || statusNormalized === 'disconnected'"
              @click="handleDisconnect"
            >
              <span v-if="working && disconnecting">Desconectando...</span>
              <span v-else>Desconectar</span>
            </button>
          </div>
        </div>
      </article>

      <p class="mt-4 text-sm text-slate-500">Nesta versão existe limite de 1 conexão WhatsApp por agência.</p>
    </section>

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
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" />
              </svg>
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

<script setup lang="ts">
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
  if (statusNormalized.value === "connected") return "border-emerald-200 bg-emerald-100 text-emerald-700";
  if (statusNormalized.value === "connecting" || statusNormalized.value === "qr_needed") return "border-amber-200 bg-amber-100 text-amber-700";
  return "border-rose-200 bg-rose-100 text-rose-700";
});

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


