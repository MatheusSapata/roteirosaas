<template>
  <section class="am-page">
    <AdminMasterHeader
      title="Bancos de fotos"
      subtitle="Chaves do Unsplash e do Pexels usadas pelo assistente de IA para buscar fotos. Quando uma chave esgota o limite da hora, a próxima assume sozinha."
    >
      <button type="button" class="am-btn" :disabled="loading" @click="refresh"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
      <button type="button" class="am-btn am-btn-primary" @click="openCreate"><AmIcon name="plus" />Nova chave</button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="successMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ successMessage }}</span></div>

    <section class="am-grid-4">
      <AdminMasterKpi
        icon="image"
        tone="success"
        label="Unsplash nesta hora"
        :value="`${formatInt(summary.unsplash.hour_usage)} / ${formatInt(summary.unsplash.hour_limit)}`"
        :hint="providerHint('unsplash')"
      />
      <AdminMasterKpi
        icon="image"
        tone="info"
        label="Pexels nesta hora"
        :value="`${formatInt(summary.pexels.hour_usage)} / ${formatInt(summary.pexels.hour_limit)}`"
        :hint="providerHint('pexels')"
      />
      <AdminMasterKpi
        icon="search"
        tone="violet"
        label="Buscas guardadas"
        :value="formatInt(summary.searches)"
        :hint="`${formatInt(summary.search_reuses)} reaproveitadas sem gastar chave`"
      />
      <AdminMasterKpi
        icon="eye"
        tone="warning"
        label="Fotos no banco"
        :value="formatInt(summary.photos)"
        :hint="`${formatInt(summary.photo_uses)} usos em páginas`"
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
        <span class="am-card-sub ml-auto !mt-0">Usa o Unsplash primeiro; a ordem de uso define a chave da vez</span>
      </div>
      <div class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th class="w-14">Ordem</th>
              <th>Chave</th>
              <th>Banco</th>
              <th class="min-w-[240px]">Uso nesta hora</th>
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
              <td>{{ providerLabel(item.provider) }}</td>
              <td>
                <div class="flex items-center gap-3">
                  <div class="am-bar flex-1">
                    <i :style="{ width: usagePercent(item) + '%', background: usagePercent(item) >= 85 ? 'var(--status-warning-foreground)' : undefined }"></i>
                  </div>
                  <span class="am-num w-[90px] text-right">{{ formatInt(item.monthly_usage_estimated) }} / {{ formatInt(item.monthly_limit) }}</span>
                </div>
                <small v-if="item.last_error" class="am-muted mt-1 block text-xs">{{ item.last_error }}</small>
              </td>
              <td class="am-num">{{ formatDateTime(item.last_used_at) || "Nunca" }}</td>
              <td><span class="am-badge am-dot" :class="statusTone(item)">{{ statusLabel(item) }}</span></td>
              <td class="am-right">
                <div class="relative inline-block" data-image-key-menu="true">
                  <button type="button" class="am-icon-btn" :aria-label="`Ações de ${item.label}`" @click="rowMenuId = rowMenuId === item.id ? null : item.id">
                    <AmIcon name="dots" />
                  </button>
                  <div v-if="rowMenuId === item.id" class="am-menu right-0 top-full mt-1">
                    <button type="button" @click="runMenu(() => runTest(item.id))"><AmIcon name="play" />Testar chave</button>
                    <button v-if="item.is_active" type="button" @click="runMenu(() => act(pauseImageApiKey, item.id, 'Não foi possível pausar a chave.'))"><AmIcon name="pause" />Pausar</button>
                    <button v-else type="button" @click="runMenu(() => act(activateImageApiKey, item.id, 'Não foi possível ativar a chave.'))"><AmIcon name="check" />Ativar</button>
                    <button type="button" @click="runMenu(() => openEdit(item))"><AmIcon name="edit" />Editar</button>
                    <button type="button" @click="runMenu(() => act(resetImageApiKeyUsage, item.id, 'Não foi possível zerar o uso.'))"><AmIcon name="undo" />Zerar uso da hora</button>
                    <button type="button" class="is-danger" @click="runMenu(() => removeKey(item.id))"><AmIcon name="trash" />Excluir</button>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filteredItems.length">
              <td colspan="7">
                <div class="am-empty">
                  Nenhuma chave cadastrada.
                  <span v-if="summary.unsplash.env_key || summary.pexels.env_key"> O servidor ainda usa a chave do arquivo de configuração.</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <AdminMasterDrawer
      :open="drawerOpen"
      :title="editId ? 'Editar chave' : 'Nova chave de fotos'"
      subtitle="A chave fica guardada criptografada no servidor e aparece mascarada."
      icon="key"
      tone="violet"
      @close="drawerOpen = false"
    >
      <div class="grid gap-3.5 sm:grid-cols-2">
        <div class="am-field">
          <label for="ik-provider">Banco</label>
          <select id="ik-provider" v-model="form.provider" class="am-input" :disabled="Boolean(editId)" @change="onProviderChange">
            <option value="unsplash">Unsplash</option>
            <option value="pexels">Pexels</option>
          </select>
        </div>
        <div class="am-field">
          <label for="ik-label">Nome interno</label>
          <input id="ik-label" v-model="form.label" class="am-input" placeholder="Ex.: Conta 1" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="ik-key">
            {{ form.provider === "unsplash" ? "Access Key" : "API Key" }}
            <span v-if="editId" class="font-normal text-muted-foreground">(deixe em branco para manter)</span>
          </label>
          <input id="ik-key" v-model="form.api_key" class="am-input am-mono" autocomplete="off" />
          <small class="am-muted text-xs">{{ keyHelp }}</small>
        </div>
        <div class="am-field">
          <label for="ik-limit">Limite por hora</label>
          <input id="ik-limit" v-model.number="form.hourly_limit" type="number" min="1" class="am-input" />
        </div>
        <div class="am-field">
          <label for="ik-priority">Ordem de uso</label>
          <input id="ik-priority" v-model.number="form.priority" type="number" min="1" class="am-input" />
        </div>
        <div class="flex items-end sm:col-span-2">
          <button type="button" class="am-btn w-full !justify-between" role="switch" :aria-checked="form.is_active" @click="form.is_active = !form.is_active">
            Chave ligada
            <span class="am-switch" :class="{ on: form.is_active }" aria-hidden="true"></span>
          </button>
        </div>
        <div class="am-field sm:col-span-2">
          <label for="ik-notes">Observações</label>
          <textarea id="ik-notes" v-model="form.notes" rows="2" class="am-input"></textarea>
        </div>
      </div>
      <template #footer>
        <button type="button" class="am-btn" @click="drawerOpen = false">Cancelar</button>
        <button type="button" class="am-btn" :disabled="saving" @click="save(false)">Salvar</button>
        <button type="button" class="am-btn am-btn-primary" :disabled="saving" @click="save(true)">Salvar e testar</button>
      </template>
    </AdminMasterDrawer>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  activateImageApiKey,
  createImageApiKey,
  deleteImageApiKey,
  listImageApiKeys,
  pauseImageApiKey,
  resetImageApiKeyUsage,
  testImageApiKey,
  updateImageApiKey,
  type ImageApiKey,
  type ImageApiKeysResponse,
  type ImageProvider
} from "../../services/imageApiKeys";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";
import AdminMasterDrawer from "./master/AdminMasterDrawer.vue";

const DEFAULT_LIMIT: Record<ImageProvider, number> = { unsplash: 50, pexels: 200 };
const providerFilters: Array<{ value: "all" | ImageProvider; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "unsplash", label: "Unsplash" },
  { value: "pexels", label: "Pexels" }
];

const emptyProvider = () => ({ keys: 0, active_keys: 0, hour_usage: 0, hour_limit: 0, env_key: false });
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const items = ref<ImageApiKey[]>([]);
const providerFilter = ref<"all" | ImageProvider>("all");
const summary = reactive<ImageApiKeysResponse["summary"]>({
  searches: 0,
  photos: 0,
  photo_uses: 0,
  search_reuses: 0,
  unsplash: emptyProvider(),
  pexels: emptyProvider()
});

const drawerOpen = ref(false);
const editId = ref<number | null>(null);
const form = reactive({
  provider: "unsplash" as ImageProvider,
  label: "",
  api_key: "",
  hourly_limit: DEFAULT_LIMIT.unsplash,
  priority: 1,
  is_active: true,
  notes: ""
});

const keyHelp = computed(() =>
  form.provider === "unsplash"
    ? "No Unsplash: Your apps > sua aplicação > Keys > Access Key. Conta de demonstração tem 50 buscas por hora."
    : "No Pexels: pexels.com/api > Your API Key. O limite padrão é 200 buscas por hora."
);

const filteredItems = computed(() =>
  providerFilter.value === "all" ? items.value : items.value.filter(item => item.provider === providerFilter.value)
);
const providerLabel = (provider?: string | null) => (provider === "pexels" ? "Pexels" : provider === "unsplash" ? "Unsplash" : provider || "-");
const providerHint = (provider: ImageProvider) => {
  const data = summary[provider];
  const keys = `${data.active_keys} de ${data.keys} chave${data.keys === 1 ? "" : "s"} ativa${data.active_keys === 1 ? "" : "s"}`;
  return data.env_key ? `${keys} + reserva do servidor` : keys;
};
const formatInt = (value?: number | null) => new Intl.NumberFormat("pt-BR").format(Number(value || 0));
const usagePercent = (item: ImageApiKey) =>
  item.monthly_limit ? Math.min(100, Math.round((Number(item.monthly_usage_estimated || 0) / item.monthly_limit) * 100)) : 0;
const statusLabel = (item: ImageApiKey) => {
  if (!item.is_active || item.status === "paused") return "Pausada";
  if (item.status === "exhausted") return "Esgotada na hora";
  if (item.status === "error") return "Erro";
  return "Ativa";
};
const statusTone = (item: ImageApiKey) => {
  if (!item.is_active || item.status === "paused") return "am-tone-neutral";
  if (item.status === "exhausted") return "am-tone-warning";
  if (item.status === "error") return "am-tone-danger";
  return "am-tone-success";
};
const formatDateTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
};
const errorText = (error: any, fallback: string) => error?.response?.data?.detail || fallback;

const rowMenuId = ref<number | null>(null);
const runMenu = (action: () => unknown) => {
  rowMenuId.value = null;
  void action();
};
const closeMenuOnOutside = (event: MouseEvent) => {
  if (rowMenuId.value === null) return;
  if (!event.composedPath().some(el => (el as HTMLElement)?.dataset?.imageKeyMenu === "true")) rowMenuId.value = null;
};

// Não limpa os avisos: quem chama (teste, salvar) mostra o resultado e só depois recarrega.
const load = async () => {
  loading.value = true;
  try {
    const response = await listImageApiKeys();
    items.value = response.items || [];
    Object.assign(summary, response.summary);
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível carregar as chaves.");
  } finally {
    loading.value = false;
  }
};

const refresh = () => {
  errorMessage.value = "";
  successMessage.value = "";
  return load();
};

const nextPriority = (provider: ImageProvider) =>
  Math.max(0, ...items.value.filter(item => item.provider === provider).map(item => item.priority)) + 1;

const onProviderChange = () => {
  form.hourly_limit = DEFAULT_LIMIT[form.provider];
  form.priority = nextPriority(form.provider);
};

const openCreate = () => {
  editId.value = null;
  Object.assign(form, { provider: "unsplash", label: "", api_key: "", hourly_limit: DEFAULT_LIMIT.unsplash, is_active: true, notes: "" });
  form.priority = nextPriority("unsplash");
  drawerOpen.value = true;
};

const openEdit = (item: ImageApiKey) => {
  editId.value = item.id;
  Object.assign(form, {
    provider: item.provider as ImageProvider,
    label: item.label,
    api_key: "",
    hourly_limit: item.monthly_limit,
    priority: item.priority,
    is_active: item.is_active,
    notes: item.notes || ""
  });
  drawerOpen.value = true;
};

const runTest = async (id: number) => {
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const result = await testImageApiKey(id);
    successMessage.value =
      result.remaining_this_hour !== null ? `Chave funcionando. Restam ${result.remaining_this_hour} buscas nesta hora.` : "Chave funcionando.";
  } catch (error: any) {
    errorMessage.value = errorText(error, "Falha no teste da chave.");
  }
  await load();
};

const save = async (testAfter: boolean) => {
  if (!form.label.trim() || (!editId.value && !form.api_key.trim())) {
    errorMessage.value = "Informe o nome e a chave.";
    return;
  }
  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const payload = {
      label: form.label.trim(),
      priority: form.priority,
      hourly_limit: form.hourly_limit,
      is_active: form.is_active,
      notes: form.notes
    };
    const saved = editId.value
      ? await updateImageApiKey(editId.value, { ...payload, api_key: form.api_key.trim() || undefined })
      : await createImageApiKey({ ...payload, provider: form.provider, api_key: form.api_key.trim() });
    drawerOpen.value = false;
    if (testAfter) await runTest(saved.id);
    else await load();
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível salvar a chave.");
  } finally {
    saving.value = false;
  }
};

const act = async (action: (id: number) => Promise<unknown>, id: number, fallback: string) => {
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await action(id);
    await load();
  } catch (error: any) {
    errorMessage.value = errorText(error, fallback);
  }
};

const removeKey = async (id: number) => {
  if (!window.confirm("Deseja excluir esta chave?")) return;
  await act(deleteImageApiKey, id, "Não foi possível excluir a chave.");
};

onMounted(() => {
  load();
  document.addEventListener("click", closeMenuOnOutside);
});
onBeforeUnmount(() => document.removeEventListener("click", closeMenuOnOutside));
</script>
