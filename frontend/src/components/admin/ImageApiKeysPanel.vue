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

    <section class="am-card">
      <div class="am-card-head">
        <div>
          <div class="am-card-title">Fotos cadastradas</div>
          <div class="am-card-sub">
            Fotos de qualquer site, com palavras-chave e crédito. Quando a busca da IA tem as palavras-chave, a foto entra antes do Unsplash e do Pexels.
          </div>
        </div>
        <button type="button" class="am-btn am-btn-primary shrink-0" @click="openPhotoCreate"><AmIcon name="plus" />Adicionar foto</button>
      </div>
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <input v-model="photoQuery" class="am-input max-w-xs" placeholder="Buscar por palavra-chave ou autor" @keyup.enter="loadPhotos" />
        <button type="button" class="am-btn" @click="loadPhotos"><AmIcon name="search" />Buscar</button>
        <span class="am-card-sub ml-auto !mt-0">{{ formatInt(photos.length) }} foto{{ photos.length === 1 ? "" : "s" }}</span>
      </div>
      <div v-if="photos.length" class="ik-photos">
        <article v-for="photo in photos" :key="photo.id" class="ik-photo">
          <img :src="mediaUrl(photo.url)" :alt="photo.description || photo.keywords.join(', ')" loading="lazy" />
          <div class="ik-photo-body">
            <div class="flex flex-wrap gap-1">
              <span v-for="keyword in photo.keywords" :key="keyword" class="am-badge am-tone-neutral">{{ keyword }}</span>
            </div>
            <small class="am-muted block text-xs">
              {{ photoCredit(photo) || "Sem crédito (foto própria ou sem exigência)" }}
            </small>
            <small class="am-muted block text-xs">
              {{ photo.width && photo.height ? `${photo.width}×${photo.height}` : "" }}{{ photo.width && photo.height && photo.height > photo.width ? " · em pé, fica cortada nas seções" : "" }}
              · usada {{ photo.uses }}×
            </small>
            <div class="mt-1 flex gap-1">
              <button type="button" class="am-icon-btn" :aria-label="`Editar foto ${photo.id}`" @click="openPhotoEdit(photo)"><AmIcon name="edit" /></button>
              <button type="button" class="am-icon-btn" :aria-label="`Excluir foto ${photo.id}`" @click="removePhoto(photo)"><AmIcon name="trash" /></button>
            </div>
          </div>
        </article>
      </div>
      <div v-else class="am-empty">{{ photosLoading ? "Carregando fotos..." : "Nenhuma foto cadastrada ainda." }}</div>
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
    <AdminMasterDrawer
      :open="photoDrawerOpen"
      :title="photoEditId ? 'Editar foto' : 'Adicionar foto'"
      subtitle="A foto é baixada e guardada no nosso servidor, para a página não depender do site de origem."
      icon="image"
      tone="violet"
      @close="photoDrawerOpen = false"
    >
      <div class="grid gap-3.5">
        <div v-if="photoError" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ photoError }}</span></div>
        <div class="am-field">
          <label for="ph-url">Endereço da imagem</label>
          <input id="ph-url" v-model="photoForm.url" class="am-input am-mono" :disabled="Boolean(photoEditId)" placeholder="https://.../foto.jpg" />
          <small class="am-muted text-xs">Abra a foto no site, clique nela com o botão direito e escolha "Copiar endereço da imagem".</small>
        </div>
        <img v-if="photoPreview" :src="photoPreview" alt="" class="ik-preview" @error="photoPreviewFailed = true" @load="photoPreviewFailed = false" />
        <small v-if="photoPreview && photoPreviewFailed" class="am-muted text-xs">Não deu para mostrar a prévia. Confira se o endereço é da imagem.</small>
        <div class="am-field">
          <label for="ph-keywords">Palavras-chave</label>
          <input id="ph-keywords" v-model="photoForm.keywords" class="am-input" placeholder="Ex.: Beto Carrero, Penha, theme park, family amusement park" />
          <small class="am-muted text-xs">Separe por vírgula. Inclua o lugar e termos em inglês, porque a IA busca em inglês (ex.: "Gramado, Gramado Brazil, wine, couple").</small>
        </div>
        <div class="am-field">
          <label for="ph-desc">Descrição <span class="font-normal text-muted-foreground">(opcional)</span></label>
          <input id="ph-desc" v-model="photoForm.description" class="am-input" placeholder="Ex.: Montanha-russa do parque ao entardecer" />
        </div>
        <div class="grid gap-3.5 sm:grid-cols-2">
          <div class="am-field">
            <label for="ph-author">Autor / fotógrafo</label>
            <input id="ph-author" v-model="photoForm.author" class="am-input" />
          </div>
          <div class="am-field">
            <label for="ph-author-url">Link do autor</label>
            <input id="ph-author-url" v-model="photoForm.author_url" class="am-input" placeholder="https://" />
          </div>
          <div class="am-field">
            <label for="ph-source">Fonte</label>
            <input id="ph-source" v-model="photoForm.source_name" class="am-input" placeholder="Ex.: Wikimedia Commons, Santur" />
          </div>
          <div class="am-field">
            <label for="ph-source-url">Link da fonte ou da licença</label>
            <input id="ph-source-url" v-model="photoForm.source_url" class="am-input" placeholder="https://" />
          </div>
        </div>
        <small class="am-muted text-xs">O crédito aparece no "©" da foto na página: "Foto: autor · fonte". Sem autor e sem fonte, a foto entra sem "©".</small>
        <label v-if="!photoEditId" class="flex items-start gap-2 text-sm">
          <input v-model="photoRights" type="checkbox" class="mt-1" />
          <span>Tenho direito de usar esta foto em sites de clientes (licença livre, autorização do autor ou foto própria).</span>
        </label>
      </div>
      <template #footer>
        <button type="button" class="am-btn" @click="photoDrawerOpen = false">Cancelar</button>
        <button type="button" class="am-btn am-btn-primary" :disabled="photoSaving || (!photoEditId && !photoRights)" @click="savePhoto">
          {{ photoSaving ? "Baixando a foto..." : "Salvar foto" }}
        </button>
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
  type ImageProvider,
  createStockPhoto,
  deleteStockPhoto,
  listStockPhotos,
  updateStockPhoto,
  type StockPhoto
} from "../../services/imageApiKeys";
import { resolveMediaUrl } from "../../utils/media";
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
  curated_photos: 0,
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

// Fotos cadastradas à mão
const photos = ref<StockPhoto[]>([]);
const photosLoading = ref(false);
const photoQuery = ref("");
const photoDrawerOpen = ref(false);
const photoEditId = ref<number | null>(null);
const photoSaving = ref(false);
const photoRights = ref(false);
const photoPreviewFailed = ref(false);
const photoError = ref("");
const emptyPhotoForm = () => ({ url: "", keywords: "", description: "", author: "", author_url: "", source_name: "", source_url: "" });
const photoForm = reactive(emptyPhotoForm());
const mediaUrl = (url: string) => resolveMediaUrl(url) || url;
const photoPreview = computed(() => (/^https?:\/\/\S+$/.test(photoForm.url.trim()) ? photoForm.url.trim() : ""));
const photoCredit = (photo: StockPhoto) => {
  if (!photo.author && !photo.source_name) return "";
  return `Foto: ${[photo.author, photo.source_name].filter(Boolean).join(" · ")}`;
};

const loadPhotos = async () => {
  photosLoading.value = true;
  try {
    photos.value = await listStockPhotos(photoQuery.value.trim() || undefined);
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível carregar as fotos.");
  } finally {
    photosLoading.value = false;
  }
};

const openPhotoCreate = () => {
  photoEditId.value = null;
  photoError.value = "";
  successMessage.value = "";
  Object.assign(photoForm, emptyPhotoForm());
  photoRights.value = false;
  photoDrawerOpen.value = true;
};

const openPhotoEdit = (photo: StockPhoto) => {
  photoEditId.value = photo.id;
  photoError.value = "";
  successMessage.value = "";
  Object.assign(photoForm, {
    url: photo.original_url,
    keywords: photo.keywords.join(", "),
    description: photo.description || "",
    author: photo.author || "",
    author_url: photo.author_url || "",
    source_name: photo.source_name || "",
    source_url: photo.source_url || ""
  });
  photoDrawerOpen.value = true;
};

const savePhoto = async () => {
  if (!photoForm.keywords.trim() || (!photoEditId.value && !photoForm.url.trim())) {
    photoError.value = "Informe o endereço da imagem e ao menos uma palavra-chave.";
    return;
  }
  photoSaving.value = true;
  photoError.value = "";
  successMessage.value = "";
  const { url, ...details } = photoForm;
  try {
    if (photoEditId.value) await updateStockPhoto(photoEditId.value, details);
    else await createStockPhoto({ ...details, url: url.trim() });
    photoDrawerOpen.value = false;
    successMessage.value = photoEditId.value ? "Foto atualizada." : "Foto adicionada ao banco.";
    await Promise.all([loadPhotos(), load()]);
  } catch (error: any) {
    photoError.value = errorText(error, "Não foi possível salvar a foto.");
  } finally {
    photoSaving.value = false;
  }
};

const removePhoto = async (photo: StockPhoto) => {
  if (!window.confirm("Tirar esta foto do banco? Páginas que já usam a foto continuam com ela.")) return;
  try {
    await deleteStockPhoto(photo.id);
    await loadPhotos();
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível excluir a foto.");
  }
};

onMounted(() => {
  load();
  loadPhotos();
  document.addEventListener("click", closeMenuOnOutside);
});
onBeforeUnmount(() => document.removeEventListener("click", closeMenuOnOutside));
</script>

<style scoped>
.ik-photos {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.ik-photo {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--card);
}
.ik-photo img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  background: var(--muted);
}
.ik-photo-body {
  display: grid;
  gap: 6px;
  padding: 10px 12px 12px;
}
.ik-preview {
  width: 100%;
  max-height: 220px;
  object-fit: contain;
  border-radius: 12px;
  background: var(--muted);
}
</style>
