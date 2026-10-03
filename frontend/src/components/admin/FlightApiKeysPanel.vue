<template>
  <section class="am-page">
    <AdminMasterHeader title="APIs de voo" subtitle="Chaves usadas pelo editor para buscar voos. A página publicada só lê o que já foi salvo.">
      <button type="button" class="am-btn" :disabled="loading" @click="load"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
      <button type="button" class="am-btn am-btn-primary" @click="openCreateModal"><AmIcon name="plus" />Nova chave</button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>

    <section class="am-grid-4">
      <AdminMasterKpi
        icon="plane"
        tone="success"
        label="Uso no mês"
        :value="formatInt(summary.monthly_usage_estimated)"
        :hint="`de ${formatInt(summary.monthly_limit)} disponíveis · ${formatInt(summary.real_requests_month)} consultas reais`"
      />
      <AdminMasterKpi icon="refresh" tone="info" label="Respondidas pelo cache" :value="formatInt(summary.cache_served_estimated)" hint="Sem gastar chave" />
      <AdminMasterKpi
        icon="key"
        tone="violet"
        label="Chaves ativas"
        :value="formatInt(summary.active_keys)"
        :hint="`AeroDataBox ${summary.active_keys_aerodatabox} · AirLabs ${summary.active_keys_airlabs}`"
      />
      <AdminMasterKpi
        icon="alert"
        tone="warning"
        label="Perto do limite"
        :value="formatInt(nearLimitKeys.length)"
        :hint="nearLimitKeys.length ? nearLimitKeys.map(key => key.label).join(', ') : 'Nenhuma chave acima de 85%'"
      />
    </section>

    <section class="am-card am-card-flush">
      <div class="am-toolbar">
        <button
          v-for="option in providerFilters"
          :key="option.value"
          type="button"
          class="am-chip"
          :class="{ on: providerFilter === option.value }"
          @click="providerFilter = option.value"
        >
          {{ option.label }}
        </button>
        <span class="am-card-sub ml-auto !mt-0">A ordem de uso define qual chave é usada primeiro</span>
      </div>
      <div class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th class="w-14">Ordem</th>
              <th>Chave</th>
              <th>Provedor</th>
              <th class="min-w-[240px]">Uso no mês</th>
              <th>Último uso</th>
              <th>Situação</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !items.length">
              <td colspan="7"><div class="am-empty"><div class="am-spinner"></div>Carregando chaves...</div></td>
            </tr>
            <tr v-for="item in filteredItems" :key="item.id">
              <td class="am-num am-muted">{{ item.priority }}</td>
              <td>
                <b class="font-semibold">{{ item.label }}</b>
                <small class="am-mono am-muted block">{{ item.key_masked }}</small>
              </td>
              <td>
                {{ providerLabel(item.provider) }}
                <small class="am-muted block text-xs">{{ marketplaceLabel(item.marketplace) }}</small>
              </td>
              <td>
                <div class="flex items-center gap-3">
                  <div class="am-bar flex-1">
                    <i :style="{ width: usagePercent(item) + '%', background: usagePercent(item) >= 85 ? 'var(--status-warning-foreground)' : undefined }"></i>
                  </div>
                  <span class="am-num w-[118px] text-right">{{ formatInt(item.monthly_usage_estimated) }} / {{ formatInt(item.monthly_limit) }}</span>
                </div>
              </td>
              <td class="am-num">{{ formatDateTime(item.last_used_at) || "Nunca" }}</td>
              <td><span class="am-badge am-dot" :class="statusTone(item.status, item.is_active)">{{ statusLabel(item.status, item.is_active) }}</span></td>
              <td class="am-right">
                <div class="relative inline-block" data-flight-menu="true">
                  <button type="button" class="am-icon-btn" :aria-label="`Ações de ${item.label}`" @click="rowMenuId = rowMenuId === item.id ? null : item.id">
                    <AmIcon name="dots" />
                  </button>
                  <div v-if="rowMenuId === item.id" class="am-menu right-0 top-full mt-1">
                    <button type="button" @click="runMenu(() => runTest(item.id))"><AmIcon name="play" />Testar conexão</button>
                    <button v-if="item.is_active" type="button" @click="runMenu(() => pauseKey(item.id))"><AmIcon name="pause" />Pausar</button>
                    <button v-else type="button" @click="runMenu(() => activateKey(item.id))"><AmIcon name="check" />Ativar</button>
                    <button type="button" @click="runMenu(() => openEditModal(item))"><AmIcon name="edit" />Editar</button>
                    <button type="button" @click="runMenu(() => resetUsage(item.id))"><AmIcon name="undo" />Zerar uso do mês</button>
                    <button type="button" class="is-danger" @click="runMenu(() => removeKey(item.id))"><AmIcon name="trash" />Excluir</button>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filteredItems.length">
              <td colspan="7"><div class="am-empty">Nenhuma chave cadastrada.</div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <AdminMasterDrawer :open="createModalOpen" title="Nova chave de voo" subtitle="A chave fica guardada no servidor e aparece mascarada." icon="key" tone="violet" @close="createModalOpen = false">
      <div class="grid gap-3.5 sm:grid-cols-2">
        <div class="am-field">
          <label for="fk-provider">Provedor</label>
          <select id="fk-provider" v-model="createForm.provider" class="am-input">
            <option value="aerodatabox">AeroDataBox</option>
            <option value="airlabs">AirLabs</option>
          </select>
        </div>
        <div class="am-field">
          <label for="fk-market">Marketplace</label>
          <input id="fk-market" v-model="createForm.marketplace" class="am-input" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="fk-host">Host</label>
          <input id="fk-host" v-model="createForm.api_host" class="am-input am-mono" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="fk-label">Nome interno</label>
          <input id="fk-label" v-model="createForm.label" class="am-input" placeholder="Ex.: Chave principal" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="fk-key">Chave da API</label>
          <input id="fk-key" v-model="createForm.api_key" class="am-input am-mono" autocomplete="off" />
        </div>
        <div class="am-field">
          <label for="fk-limit">Limite por mês</label>
          <input id="fk-limit" v-model.number="createForm.monthly_limit" type="number" min="1" class="am-input" />
        </div>
        <div class="am-field">
          <label for="fk-priority">Ordem de uso</label>
          <input id="fk-priority" v-model.number="createForm.priority" type="number" min="1" class="am-input" />
        </div>
        <div class="am-field">
          <label for="fk-status">Situação</label>
          <select id="fk-status" v-model="createForm.status" class="am-input">
            <option value="active">Ativa</option>
            <option value="paused">Pausada</option>
          </select>
        </div>
        <div class="flex items-end">
          <button type="button" class="am-btn w-full !justify-between" role="switch" :aria-checked="createForm.is_active" @click="createForm.is_active = !createForm.is_active">
            Chave ligada
            <span class="am-switch" :class="{ on: createForm.is_active }" aria-hidden="true"></span>
          </button>
        </div>
        <div class="am-field sm:col-span-2">
          <label for="fk-notes">Observações</label>
          <textarea id="fk-notes" v-model="createForm.notes" rows="2" class="am-input"></textarea>
        </div>
      </div>
      <template #footer>
        <button type="button" class="am-btn" @click="createModalOpen = false">Cancelar</button>
        <button type="button" class="am-btn" :disabled="saving" @click="createKey(false)">Salvar</button>
        <button type="button" class="am-btn am-btn-primary" :disabled="saving" @click="createKey(true)">Salvar e testar</button>
      </template>
    </AdminMasterDrawer>

    <AdminMasterDrawer :open="editModalOpen" title="Editar chave" icon="key" tone="violet" @close="editModalOpen = false">
      <div class="grid gap-3.5 sm:grid-cols-2">
        <div class="am-field">
          <label for="fke-provider">Provedor</label>
          <input id="fke-provider" :value="providerLabel(editForm.provider)" disabled class="am-input opacity-70" />
        </div>
        <div class="am-field">
          <label for="fke-market">Marketplace</label>
          <input id="fke-market" v-model="editForm.marketplace" class="am-input" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="fke-host">Host</label>
          <input id="fke-host" v-model="editForm.api_host" class="am-input am-mono" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="fke-label">Nome interno</label>
          <input id="fke-label" v-model="editForm.label" class="am-input" placeholder="Ex.: Chave principal" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="fke-key">Nova chave da API <span class="font-normal text-muted-foreground">(opcional)</span></label>
          <input id="fke-key" v-model="editForm.api_key" class="am-input am-mono" autocomplete="off" />
        </div>
        <div class="am-field">
          <label for="fke-limit">Limite por mês</label>
          <input id="fke-limit" v-model.number="editForm.monthly_limit" type="number" min="1" class="am-input" />
        </div>
        <div class="am-field">
          <label for="fke-priority">Ordem de uso</label>
          <input id="fke-priority" v-model.number="editForm.priority" type="number" min="1" class="am-input" />
        </div>
        <div class="am-field">
          <label for="fke-status">Situação</label>
          <select id="fke-status" v-model="editForm.status" class="am-input">
            <option value="active">Ativa</option>
            <option value="paused">Pausada</option>
            <option value="exhausted">Esgotada</option>
            <option value="error">Com erro</option>
          </select>
        </div>
        <div class="flex items-end">
          <button type="button" class="am-btn w-full !justify-between" role="switch" :aria-checked="editForm.is_active" @click="editForm.is_active = !editForm.is_active">
            Chave ligada
            <span class="am-switch" :class="{ on: editForm.is_active }" aria-hidden="true"></span>
          </button>
        </div>
        <div class="am-field sm:col-span-2">
          <label for="fke-notes">Observações</label>
          <textarea id="fke-notes" v-model="editForm.notes" rows="2" class="am-input"></textarea>
        </div>
      </div>
      <template #footer>
        <button type="button" class="am-btn" @click="editModalOpen = false">Cancelar</button>
        <button type="button" class="am-btn am-btn-primary" :disabled="saving" @click="saveEdit">Salvar alterações</button>
      </template>
    </AdminMasterDrawer>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
  activateFlightApiKey,
  createFlightApiKey,
  deleteFlightApiKey,
  listFlightApiKeys,
  pauseFlightApiKey,
  resetFlightApiKeyUsage,
  testFlightApiKey,
  updateFlightApiKey,
  type FlightApiKey
} from "../../services/flightDetails";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";
import AdminMasterDrawer from "./master/AdminMasterDrawer.vue";

const providerFilters: Array<{ value: "all" | "aerodatabox" | "airlabs"; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "aerodatabox", label: "AeroDataBox" },
  { value: "airlabs", label: "AirLabs" }
];

const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const items = ref<FlightApiKey[]>([]);
const providerFilter = ref<"all" | "aerodatabox" | "airlabs">("all");

const summary = reactive({
  provider: "all",
  provider_primary: "aerodatabox",
  marketplace_primary: "rapidapi",
  active_keys: 0,
  active_keys_aerodatabox: 0,
  active_keys_airlabs: 0,
  monthly_usage_estimated: 0,
  monthly_limit: 0,
  real_requests_month: 0,
  cache_served_estimated: 0,
  last_used_at: null as string | null
});

const createModalOpen = ref(false);
const createForm = reactive({
  provider: "aerodatabox",
  marketplace: "rapidapi",
  api_host: "aerodatabox.p.rapidapi.com",
  label: "",
  api_key: "",
  monthly_limit: 6000,
  priority: 1,
  status: "active",
  reset_day: null as number | null,
  is_active: true,
  notes: ""
});

const editModalOpen = ref(false);
const editTargetId = ref<number | null>(null);
const editForm = reactive({
  provider: "aerodatabox",
  marketplace: "rapidapi",
  api_host: "aerodatabox.p.rapidapi.com",
  label: "",
  api_key: "",
  monthly_limit: 6000,
  priority: 1,
  status: "active",
  is_active: true,
  notes: ""
});

const filteredItems = computed(() => {
  if (providerFilter.value === "all") return items.value;
  return items.value.filter(item => item.provider === providerFilter.value);
});

const providerLabel = (provider?: string | null) => {
  if (provider === "aerodatabox") return "AeroDataBox";
  if (provider === "airlabs") return "AirLabs";
  return provider || "-";
};

const statusTone = (status: string, isActive: boolean) => {
  if (!isActive || status === "paused") return "am-tone-neutral";
  if (status === "active") return "am-tone-success";
  if (status === "exhausted" || status === "error") return "am-tone-danger";
  return "am-tone-warning";
};
const formatInt = (value?: number | null) => new Intl.NumberFormat("pt-BR").format(Number(value || 0));
const marketplaceLabel = (value?: string | null) => {
  if (!value) return "—";
  if (value === "rapidapi") return "RapidAPI";
  if (value === "direct") return "Direto";
  return value;
};
const usagePercent = (item: FlightApiKey) =>
  item.monthly_limit ? Math.min(100, Math.round((Number(item.monthly_usage_estimated || 0) / item.monthly_limit) * 100)) : 0;
const nearLimitKeys = computed(() => items.value.filter(item => item.is_active && usagePercent(item) >= 85));
const rowMenuId = ref<number | null>(null);
const runMenu = (action: () => unknown) => {
  rowMenuId.value = null;
  void action();
};
const closeMenuOnOutside = (event: MouseEvent) => {
  if (rowMenuId.value === null) return;
  const path = event.composedPath();
  if (!path.some(el => (el as HTMLElement)?.dataset?.flightMenu === "true")) rowMenuId.value = null;
};

const statusLabel = (status: string, isActive: boolean) => {
  if (!isActive) return "Pausada";
  if (status === "active") return "Ativa";
  if (status === "paused") return "Pausada";
  if (status === "exhausted") return "Esgotada";
  if (status === "error") return "Erro";
  return status;
};

const formatDateTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
};

const applyProviderDefaults = (target: { provider: string; marketplace: string; api_host: string; monthly_limit: number }) => {
  if (target.provider === "aerodatabox") {
    target.marketplace = "rapidapi";
    target.api_host = "aerodatabox.p.rapidapi.com";
    target.monthly_limit = 6000;
    return;
  }
  target.marketplace = "direct";
  target.api_host = "";
  target.monthly_limit = 1000;
};

watch(
  () => createForm.provider,
  () => applyProviderDefaults(createForm)
);

const load = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    const response = await listFlightApiKeys();
    items.value = response.items || [];
    summary.provider = response.summary?.provider || "all";
    summary.provider_primary = response.summary?.provider_primary || "aerodatabox";
    summary.marketplace_primary = response.summary?.marketplace_primary || "rapidapi";
    summary.active_keys = response.summary?.active_keys || 0;
    summary.active_keys_aerodatabox = response.summary?.active_keys_aerodatabox || 0;
    summary.active_keys_airlabs = response.summary?.active_keys_airlabs || 0;
    summary.monthly_usage_estimated = response.summary?.monthly_usage_estimated || 0;
    summary.monthly_limit = response.summary?.monthly_limit || 0;
    summary.real_requests_month = response.summary?.real_requests_month || 0;
    summary.cache_served_estimated = response.summary?.cache_served_estimated || 0;
    summary.last_used_at = response.summary?.last_used_at || null;
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível carregar as chaves.";
  } finally {
    loading.value = false;
  }
};

const openCreateModal = () => {
  createForm.provider = "aerodatabox";
  createForm.marketplace = "rapidapi";
  createForm.api_host = "aerodatabox.p.rapidapi.com";
  createForm.label = "";
  createForm.api_key = "";
  createForm.monthly_limit = 6000;
  createForm.priority = 1;
  createForm.status = "active";
  createForm.reset_day = null;
  createForm.is_active = true;
  createForm.notes = "";
  createModalOpen.value = true;
};

const createKey = async (testAfterCreate: boolean) => {
  if (!createForm.label.trim() || !createForm.api_key.trim()) {
    errorMessage.value = "Informe o nome e a chave da API.";
    return;
  }
  saving.value = true;
  errorMessage.value = "";
  try {
    const created = await createFlightApiKey({
      provider: createForm.provider,
      marketplace: createForm.marketplace || null,
      api_host: createForm.api_host || null,
      label: createForm.label.trim(),
      api_key: createForm.api_key.trim(),
      monthly_limit: createForm.monthly_limit,
      priority: createForm.priority,
      status: createForm.status,
      reset_day: createForm.reset_day,
      is_active: createForm.is_active,
      notes: createForm.notes
    });
    if (testAfterCreate) {
      await testFlightApiKey(created.id);
    }
    createModalOpen.value = false;
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível salvar a chave.";
  } finally {
    saving.value = false;
  }
};

const openEditModal = (item: FlightApiKey) => {
  editTargetId.value = item.id;
  editForm.provider = item.provider;
  editForm.marketplace = item.marketplace || (item.provider === "aerodatabox" ? "rapidapi" : "direct");
  editForm.api_host = item.api_host || (item.provider === "aerodatabox" ? "aerodatabox.p.rapidapi.com" : "");
  editForm.label = item.label;
  editForm.api_key = "";
  editForm.monthly_limit = item.monthly_limit;
  editForm.priority = item.priority;
  editForm.status = item.status;
  editForm.is_active = item.is_active;
  editForm.notes = item.notes || "";
  editModalOpen.value = true;
};

const saveEdit = async () => {
  if (!editTargetId.value) return;
  saving.value = true;
  errorMessage.value = "";
  try {
    await updateFlightApiKey(editTargetId.value, {
      marketplace: editForm.marketplace || null,
      api_host: editForm.api_host || null,
      label: editForm.label,
      api_key: editForm.api_key || undefined,
      monthly_limit: editForm.monthly_limit,
      priority: editForm.priority,
      status: editForm.status,
      is_active: editForm.is_active,
      notes: editForm.notes
    });
    editModalOpen.value = false;
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível salvar as alterações.";
  } finally {
    saving.value = false;
  }
};

const runTest = async (id: number) => {
  try {
    await testFlightApiKey(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Falha no teste de conexão.";
  }
};

const pauseKey = async (id: number) => {
  try {
    await pauseFlightApiKey(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível pausar a chave.";
  }
};

const activateKey = async (id: number) => {
  try {
    await activateFlightApiKey(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível ativar a chave.";
  }
};

const resetUsage = async (id: number) => {
  try {
    await resetFlightApiKeyUsage(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível zerar o uso.";
  }
};

const removeKey = async (id: number) => {
  if (!window.confirm("Deseja excluir esta chave?")) return;
  try {
    await deleteFlightApiKey(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível excluir a chave.";
  }
};

onMounted(() => {
  load();
  document.addEventListener("click", closeMenuOnOutside);
});
onBeforeUnmount(() => document.removeEventListener("click", closeMenuOnOutside));
</script>
