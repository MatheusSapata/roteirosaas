<template>
  <section class="space-y-5 rounded-3xl bg-white p-6 shadow-md ring-1 ring-slate-100">
    <header class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Integracoes Master</p>
        <h2 class="mt-2 text-2xl font-bold text-slate-900">APIs de Voo</h2>
        <p class="mt-1 text-sm text-slate-500">
          Gerencie as chaves usadas no editor. A pagina publica usa apenas dados salvos no banco.
        </p>
      </div>
      <button
        type="button"
        class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark"
        @click="openCreateModal"
      >
        + Nova chave
      </button>
    </header>

    <div v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}
    </div>

    <div class="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
      <article class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p class="text-xs uppercase tracking-wide text-slate-500">Provider principal</p>
        <p class="mt-1 text-base font-bold text-slate-900">AeroDataBox</p>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p class="text-xs uppercase tracking-wide text-slate-500">Marketplace</p>
        <p class="mt-1 text-base font-bold text-slate-900">RapidAPI</p>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p class="text-xs uppercase tracking-wide text-slate-500">Chaves AeroDataBox ativas</p>
        <p class="mt-1 text-2xl font-bold text-slate-900">{{ summary.active_keys_aerodatabox ?? 0 }}</p>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p class="text-xs uppercase tracking-wide text-slate-500">Uso mensal estimado</p>
        <p class="mt-1 text-2xl font-bold text-slate-900">
          {{ summary.monthly_usage_estimated ?? 0 }} / {{ summary.monthly_limit ?? 0 }}
        </p>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p class="text-xs uppercase tracking-wide text-slate-500">Consultas servidas por cache</p>
        <p class="mt-1 text-2xl font-bold text-slate-900">{{ summary.cache_served_estimated ?? 0 }}</p>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p class="text-xs uppercase tracking-wide text-slate-500">Requests reais do mes</p>
        <p class="mt-1 text-2xl font-bold text-slate-900">{{ summary.real_requests_month ?? 0 }}</p>
      </article>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="option in providerFilters"
        :key="option.value"
        type="button"
        class="rounded-full border px-3 py-1 text-xs font-semibold"
        :class="providerFilter === option.value ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 text-slate-600'"
        @click="providerFilter = option.value"
      >
        {{ option.label }}
      </button>
    </div>

    <div class="overflow-x-auto rounded-2xl border border-slate-200">
      <table class="min-w-full text-sm">
        <thead class="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-3 py-2">Status</th>
            <th class="px-3 py-2">Provider</th>
            <th class="px-3 py-2">Marketplace</th>
            <th class="px-3 py-2">Nome</th>
            <th class="px-3 py-2">Uso mensal</th>
            <th class="px-3 py-2">Limite</th>
            <th class="px-3 py-2">Prioridade</th>
            <th class="px-3 py-2">Ultimo uso</th>
            <th class="px-3 py-2">Acoes</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading" class="border-t border-slate-100">
            <td colspan="9" class="px-3 py-4 text-center text-slate-500">Carregando chaves...</td>
          </tr>
          <tr v-for="item in filteredItems" :key="item.id" class="border-t border-slate-100">
            <td class="px-3 py-2">
              <span class="inline-flex rounded-full px-2 py-1 text-xs font-semibold" :class="statusClass(item.status)">
                {{ statusLabel(item.status, item.is_active) }}
              </span>
            </td>
            <td class="px-3 py-2 text-slate-700">{{ providerLabel(item.provider) }}</td>
            <td class="px-3 py-2 text-slate-700">{{ item.marketplace || "-" }}</td>
            <td class="px-3 py-2">
              <p class="font-semibold text-slate-800">{{ item.label }}</p>
              <p class="text-xs text-slate-500">{{ item.key_masked }}</p>
            </td>
            <td class="px-3 py-2 text-slate-700">{{ item.monthly_usage_estimated }}</td>
            <td class="px-3 py-2 text-slate-700">{{ item.monthly_limit }}</td>
            <td class="px-3 py-2 text-slate-700">{{ item.priority }}</td>
            <td class="px-3 py-2 text-xs text-slate-500">{{ formatDateTime(item.last_used_at) || "Nunca" }}</td>
            <td class="px-3 py-2">
              <div class="flex flex-wrap gap-1">
                <button class="rounded border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600" @click="runTest(item.id)">Testar conexao</button>
                <button
                  v-if="item.is_active"
                  class="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700"
                  @click="pauseKey(item.id)"
                >
                  Pausar
                </button>
                <button
                  v-else
                  class="rounded border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700"
                  @click="activateKey(item.id)"
                >
                  Ativar
                </button>
                <button class="rounded border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600" @click="openEditModal(item)">Editar</button>
                <button class="rounded border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600" @click="resetUsage(item.id)">Resetar uso</button>
                <button class="rounded border border-rose-200 bg-rose-50 px-2 py-1 text-xs font-semibold text-rose-600" @click="removeKey(item.id)">Excluir</button>
              </div>
            </td>
          </tr>
          <tr v-if="!loading && !filteredItems.length" class="border-t border-slate-100">
            <td colspan="9" class="px-3 py-4 text-center text-slate-500">Nenhuma chave cadastrada.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <div v-if="createModalOpen" class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4">
        <div class="w-full max-w-2xl rounded-2xl bg-white p-5 shadow-2xl">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-slate-900">Nova chave de voo</h3>
            <button class="text-sm text-slate-500" @click="createModalOpen = false">Fechar</button>
          </div>
          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Provider</label>
              <select v-model="createForm.provider" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
                <option value="aerodatabox">AeroDataBox</option>
                <option value="airlabs">AirLabs</option>
              </select>
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Marketplace</label>
              <input v-model="createForm.marketplace" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div class="md:col-span-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Host</label>
              <input v-model="createForm.api_host" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div class="md:col-span-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Nome interno</label>
              <input v-model="createForm.label" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div class="md:col-span-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">API key</label>
              <input v-model="createForm.api_key" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Limite mensal</label>
              <input v-model.number="createForm.monthly_limit" type="number" min="1" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Prioridade</label>
              <input v-model.number="createForm.priority" type="number" min="1" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</label>
              <select v-model="createForm.status" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
                <option value="active">active</option>
                <option value="paused">paused</option>
              </select>
            </div>
            <div class="flex items-end">
              <label class="inline-flex items-center gap-2 text-sm text-slate-600">
                <input v-model="createForm.is_active" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
                Chave ativa
              </label>
            </div>
            <div class="md:col-span-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Observacoes</label>
              <textarea v-model="createForm.notes" rows="2" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"></textarea>
            </div>
          </div>
          <div class="mt-4 flex flex-wrap justify-end gap-2">
            <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600" @click="createModalOpen = false">Cancelar</button>
            <button class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" :disabled="saving" @click="createKey(false)">Salvar</button>
            <button class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" :disabled="saving" @click="createKey(true)">Salvar e testar conexao</button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="editModalOpen" class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4">
        <div class="w-full max-w-2xl rounded-2xl bg-white p-5 shadow-2xl">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-slate-900">Editar chave</h3>
            <button class="text-sm text-slate-500" @click="editModalOpen = false">Fechar</button>
          </div>
          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Provider</label>
              <input :value="providerLabel(editForm.provider)" disabled class="mt-1 w-full rounded-lg border border-slate-200 bg-slate-100 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Marketplace</label>
              <input v-model="editForm.marketplace" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div class="md:col-span-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Host</label>
              <input v-model="editForm.api_host" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div class="md:col-span-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Nome interno</label>
              <input v-model="editForm.label" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div class="md:col-span-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Nova API key (opcional)</label>
              <input v-model="editForm.api_key" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Limite mensal</label>
              <input v-model.number="editForm.monthly_limit" type="number" min="1" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Prioridade</label>
              <input v-model.number="editForm.priority" type="number" min="1" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</label>
              <select v-model="editForm.status" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
                <option value="active">active</option>
                <option value="paused">paused</option>
                <option value="exhausted">exhausted</option>
                <option value="error">error</option>
              </select>
            </div>
            <div class="flex items-end">
              <label class="inline-flex items-center gap-2 text-sm text-slate-600">
                <input v-model="editForm.is_active" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
                Chave ativa
              </label>
            </div>
            <div class="md:col-span-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Observacoes</label>
              <textarea v-model="editForm.notes" rows="2" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"></textarea>
            </div>
          </div>
          <div class="mt-4 flex flex-wrap justify-end gap-2">
            <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600" @click="editModalOpen = false">Cancelar</button>
            <button class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" :disabled="saving" @click="saveEdit">Salvar alteracoes</button>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
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

const providerFilters = [
  { value: "all", label: "Todos" },
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

const statusClass = (status: string) => {
  if (status === "active") return "bg-emerald-100 text-emerald-700";
  if (status === "paused") return "bg-amber-100 text-amber-700";
  if (status === "exhausted") return "bg-rose-100 text-rose-700";
  return "bg-slate-100 text-slate-700";
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
  return date.toLocaleString("pt-BR");
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
    errorMessage.value = error?.response?.data?.detail || "Nao foi possivel carregar as chaves.";
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
    errorMessage.value = "Informe nome e API key.";
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
    errorMessage.value = error?.response?.data?.detail || "Nao foi possivel salvar a chave.";
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
    errorMessage.value = error?.response?.data?.detail || "Nao foi possivel salvar alteracoes.";
  } finally {
    saving.value = false;
  }
};

const runTest = async (id: number) => {
  try {
    await testFlightApiKey(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Falha no teste de conexao.";
  }
};

const pauseKey = async (id: number) => {
  try {
    await pauseFlightApiKey(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Nao foi possivel pausar a chave.";
  }
};

const activateKey = async (id: number) => {
  try {
    await activateFlightApiKey(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Nao foi possivel ativar a chave.";
  }
};

const resetUsage = async (id: number) => {
  try {
    await resetFlightApiKeyUsage(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Nao foi possivel resetar o uso.";
  }
};

const removeKey = async (id: number) => {
  if (!window.confirm("Deseja excluir esta chave?")) return;
  try {
    await deleteFlightApiKey(id);
    await load();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Nao foi possivel excluir a chave.";
  }
};

onMounted(() => {
  load();
});
</script>
