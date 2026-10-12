<template>
  <section class="am-page">
    <AdminMasterHeader
      title="Armazenamento"
      subtitle="Espaço dos arquivos das agências. O material de quem saiu do ar vai para camadas mais baratas (Cool e Archive); arquivos sem uso podem ser excluídos com margem de segurança."
    >
      <router-link to="/admin/administracao/empresas" class="am-btn"><AmIcon name="building" />Empresas</router-link>
      <button type="button" class="am-btn" :disabled="loading" @click="load"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="successMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ successMessage }}</span></div>

    <section class="am-grid-4">
      <AdminMasterKpi
        icon="database"
        tone="info"
        label="Total guardado"
        :value="storage.summary.total_bytes !== undefined ? formatBytes(storage.summary.total_bytes) : '—'"
        :hint="storage.summary.total_files !== undefined ? `${formatInt(storage.summary.total_files)} arquivos` : 'Rode a análise'"
      />
      <AdminMasterKpi
        icon="pause"
        tone="warning"
        label="Espaço das desativadas"
        :value="formatBytes(summary.inactive_bytes)"
        :hint="`${formatInt(offlineCount)} empresas fora do ar · ainda na camada normal`"
      />
      <AdminMasterKpi icon="dl" tone="violet" label="Já em Cool/Archive" :value="formatBytes(summary.archived_bytes)" :hint="`${formatInt(archivedCount)} empresas`" />
      <AdminMasterKpi
        icon="trash"
        tone="danger"
        label="Sem uso"
        :value="formatBytes(storage.orphans.bytes)"
        :hint="`${formatInt(storage.orphans.groups)} imagens · ${formatInt(storage.orphans.ready_groups)} prontas para excluir`"
      />
    </section>

    <section class="am-card">
      <div class="am-card-head">
        <div>
          <div class="am-card-title">Análise e regras</div>
          <div class="am-card-sub">
            Cool {{ summary.rules.cool_after_days }} dias depois de sair do ar, Archive aos {{ summary.rules.archive_after_days }} dias. Arquivos sem uso só podem ser
            excluídos depois de {{ summary.rules.orphan_grace_days }} dias seguidos sem uso.
          </div>
        </div>
        <button type="button" class="am-btn am-btn-primary shrink-0" :disabled="storage.status === 'running'" @click="analyze">
          <AmIcon name="search" :class="storage.status === 'running' ? 'animate-spin' : ''" />{{ storage.status === "running" ? "Analisando..." : "Analisar agora" }}
        </button>
      </div>
      <div class="am-notice mb-3" :class="summary.automation ? 'am-tone-success' : 'am-tone-neutral'">
        <AmIcon :name="summary.automation ? 'check' : 'info'" />
        <span v-if="summary.automation">Automação ligada: todo dia de madrugada o sistema analisa, move para Cool/Archive quem passou dos prazos e restaura quem voltou a assinar. Exclusão é sempre manual.</span>
        <span v-else>Automação desligada: nada muda sozinho. Use as ações abaixo (ou ligue MEDIA_LIFECYCLE_AUTOMATION no servidor do admin depois de conferir os resultados).</span>
      </div>
      <div v-if="storage.status === 'error'" class="am-notice am-tone-danger mb-3"><AmIcon name="alert" /><span>A análise parou: {{ storage.error }}</span></div>
      <div class="sp-tiers">
        <div v-for="tier in tierRows" :key="tier.name">
          <span class="am-muted text-xs">Camada {{ tier.name }}</span>
          <b>{{ formatBytes(tier.bytes) }}</b>
          <small class="am-muted">{{ formatInt(tier.files) }} arquivos</small>
        </div>
        <div>
          <span class="am-muted text-xs">Sem uso</span>
          <b>{{ formatBytes(storage.orphans.bytes) }}</b>
          <small class="am-muted">inclui fotos só na biblioteca, fora de qualquer página</small>
        </div>
      </div>
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <button type="button" class="am-btn" :disabled="!storage.orphans.ready_groups || busy" @click="deleteOrphans">
          <AmIcon name="trash" />Excluir sem uso prontas ({{ formatBytes(storage.orphans.ready_bytes) }})
        </button>
        <small class="am-muted">{{ storage.finished_at ? `Última análise: ${formatDateTime(storage.finished_at)}` : "Nenhuma análise ainda." }}</small>
      </div>
    </section>

    <section class="am-card am-card-flush">
      <div class="am-toolbar flex-wrap">
        <button
          v-for="option in filters"
          :key="option.value"
          type="button"
          class="am-chip"
          :class="{ on: filter === option.value }"
          @click="filter = option.value"
        >
          {{ option.label }} <span class="am-muted">{{ filterCount(option.value) }}</span>
        </button>
        <input v-model="query" class="am-input ml-auto max-w-[260px]" placeholder="Buscar empresa ou e-mail" />
      </div>

      <div v-if="selection.selected.value.length" class="sp-bulk">
        <b>{{ selection.selected.value.length }} selecionada(s)</b>
        <button type="button" class="am-btn am-btn-sm" :disabled="busy" @click="bulk('cool')"><AmIcon name="pause" />Mover para Cool</button>
        <button type="button" class="am-btn am-btn-sm" :disabled="busy" @click="bulk('archive')"><AmIcon name="dl" />Mover para Archive</button>
        <button type="button" class="am-btn am-btn-sm" :disabled="busy" @click="bulk('restore')"><AmIcon name="undo" />Restaurar</button>
        <button type="button" class="am-btn am-btn-sm am-btn-danger" :disabled="busy" @click="bulkDelete"><AmIcon name="trash" />Excluir arquivos</button>
        <span v-if="progress" class="am-muted">{{ progress }}</span>
        <button type="button" class="am-btn am-btn-sm ml-auto" :disabled="busy" @click="selection.clear()"><AmIcon name="x" />Limpar seleção</button>
      </div>

      <div class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th class="sp-check-col">
                <input type="checkbox" class="sp-check" :checked="selection.allVisibleSelected.value" aria-label="Selecionar todas desta lista" @change="selection.toggleAll()" />
              </th>
              <th v-for="column in columns" :key="column.key" :class="column.right ? 'am-right' : ''" :aria-sort="sort.ariaSort(column.key)">
                <button type="button" class="sp-sort" :class="{ on: sort.sortKey.value === column.key }" @click="sort.setSort(column.key)">
                  {{ column.label }} <span aria-hidden="true">{{ sort.arrow(column.key) }}</span>
                </button>
              </th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !items.length">
              <td :colspan="columns.length + 2"><div class="am-empty"><div class="am-spinner"></div>Carregando...</div></td>
            </tr>
            <tr v-for="item in visibleItems" :key="item.id" :class="{ 'sp-row-on': selection.isSelected(item) }">
              <td class="sp-check-col">
                <input type="checkbox" class="sp-check" :checked="selection.isSelected(item)" :aria-label="`Selecionar ${item.name}`" @change="selection.toggle(item)" />
              </td>
              <td>
                <b class="font-semibold">{{ item.name }}</b>
                <small class="am-muted block">{{ item.owner_email || "sem dono" }}</small>
              </td>
              <td>
                <span class="am-badge am-dot" :class="item.online ? 'am-tone-success' : 'am-tone-danger'">{{ item.status_label }}</span>
                <small class="am-muted block text-xs">{{ offlineText(item) }}</small>
              </td>
              <td class="am-num">{{ item.last_access_at ? relative(item.last_access_at) : "Nunca" }}</td>
              <td class="am-num am-right">
                <template v-if="item.media_measured_at || item.media_stage !== 'hot'">
                  {{ formatBytes(item.media_bytes) }}
                  <small class="am-muted block text-xs">{{ formatInt(item.media_files) }} arquivos{{ item.media_shared_skipped ? ` · ${item.media_shared_skipped} compartilhados` : "" }}</small>
                </template>
                <small v-else class="am-muted text-xs">{{ item.online ? "—" : "Rode a análise" }}</small>
              </td>
              <td>
                <span class="am-badge" :class="stageTone(item.media_stage)">{{ stageLabel(item.media_stage) }}</span>
                <small v-if="item.next_step" class="block text-xs font-semibold">{{ item.next_step }}</small>
                <small v-if="item.media_error" class="block text-xs text-red-600">{{ item.media_error }}</small>
              </td>
              <td class="am-right">
                <div v-if="hasActions(item)" class="relative inline-block" data-storage-menu="true">
                  <button type="button" class="am-icon-btn" :aria-label="`Ações de ${item.name}`" @click="menuId = menuId === item.id ? null : item.id">
                    <AmIcon name="dots" />
                  </button>
                  <div v-if="menuId === item.id" class="am-menu right-0 top-full mt-1">
                    <template v-if="!item.online && item.media_stage !== 'deleted'">
                      <button v-if="item.media_stage === 'hot' || item.media_stage === 'restoring'" type="button" @click="act(item, 'cool')"><AmIcon name="pause" />Mover para Cool</button>
                      <button v-if="item.media_stage !== 'archive'" type="button" @click="act(item, 'archive')"><AmIcon name="dl" />Mover para Archive</button>
                    </template>
                    <button v-if="item.media_stage === 'cool' || item.media_stage === 'archive'" type="button" @click="act(item, 'restore')"><AmIcon name="undo" />Restaurar arquivos</button>
                    <button v-if="!item.online && item.media_stage !== 'deleted'" type="button" class="is-danger" @click="removeMedia(item)"><AmIcon name="trash" />Excluir arquivos</button>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !visibleItems.length">
              <td :colspan="columns.length + 2"><div class="am-empty">Nenhuma empresa neste filtro.</div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import {
  deleteCompanyMedia,
  deleteReadyOrphans,
  getStorageStatus,
  listCompanies,
  moveCompanyMedia,
  startStorageAnalysis,
  type CompaniesResponse,
  type Company,
  type MediaStage,
  type StorageStatus
} from "../../services/companies";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";
import { useSelection, useTableSort } from "./master/useTableSort";

type Filter = "offline" | "offline_30" | "ready" | "archived" | "with_files" | "picked" | "all";
type Action = "cool" | "archive" | "restore";

const route = useRoute();
const pickedIds = String(route.query.ids || "")
  .split(",")
  .map(Number)
  .filter(Boolean);

const filters: Array<{ value: Filter; label: string }> = [
  ...(pickedIds.length ? [{ value: "picked" as Filter, label: "Vindas de Empresas" }] : []),
  { value: "offline", label: "Fora do ar" },
  { value: "offline_30", label: "Fora do ar +30 dias" },
  { value: "ready", label: "Prontas para mover" },
  { value: "archived", label: "Em Cool/Archive" },
  { value: "with_files", label: "Com arquivos medidos" },
  { value: "all", label: "Todas" }
];
const columns = [
  { key: "name", label: "Empresa" },
  { key: "offline_days", label: "Fora do ar há" },
  { key: "last_access", label: "Último acesso" },
  { key: "bytes", label: "Espaço", right: true },
  { key: "stage", label: "Camada" }
];
const STAGE_ORDER: MediaStage[] = ["hot", "restoring", "cool", "archive", "deleted"];

const loading = ref(false);
const busy = ref(false);
const progress = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const items = ref<Company[]>([]);
const filter = ref<Filter>(pickedIds.length ? "picked" : "offline");
const query = ref("");
const menuId = ref<number | null>(null);
const summary = reactive<CompaniesResponse["summary"]>({
  counts: {},
  total: 0,
  inactive_over_30: 0,
  inactive_bytes: 0,
  archived_bytes: 0,
  automation: false,
  rules: { cool_after_days: 7, archive_after_days: 30, orphan_grace_days: 30 }
});
const storage = reactive<StorageStatus>({
  status: "idle",
  started_at: null,
  finished_at: null,
  error: null,
  summary: {},
  orphans: { groups: 0, bytes: 0, ready_groups: 0, ready_bytes: 0, oldest_seen_at: null }
});
let pollTimer: ReturnType<typeof setTimeout> | null = null;

const offlineCount = computed(() => items.value.filter(item => !item.online).length);
const archivedCount = computed(() => items.value.filter(item => item.media_stage === "cool" || item.media_stage === "archive").length);
const matches = (item: Company, value: Filter) => {
  if (value === "all") return true;
  if (value === "picked") return pickedIds.includes(item.id);
  if (value === "offline") return !item.online;
  if (value === "offline_30") return !item.online && (item.status_days || 0) >= 30;
  if (value === "ready") return Boolean(item.next_step && /^Pronta/.test(item.next_step));
  if (value === "archived") return item.media_stage === "cool" || item.media_stage === "archive";
  return Boolean(item.media_measured_at);
};
const filterCount = (value: Filter) => items.value.filter(item => matches(item, value)).length;
const filtered = computed(() => {
  const text = query.value.trim().toLowerCase();
  return items.value.filter(
    item => matches(item, filter.value) && (!text || `${item.name} ${item.slug} ${item.owner_email || ""}`.toLowerCase().includes(text))
  );
});
const sort = useTableSort(
  filtered,
  {
    name: item => item.name,
    offline_days: item => (item.online ? null : item.status_days),
    last_access: item => (item.last_access_at ? new Date(item.last_access_at).getTime() : 0),
    bytes: item => item.media_bytes,
    stage: item => STAGE_ORDER.indexOf(item.media_stage)
  },
  { key: "offline_days", dir: "desc" },
  { offline_days: "desc", last_access: "asc", bytes: "desc" }
);
const visibleItems = sort.sorted;
const selection = useSelection(visibleItems);
const selectedItems = computed(() => items.value.filter(item => selection.selected.value.includes(item.id)));
const tierRows = computed(() =>
  Object.entries(storage.summary.tiers || {})
    .map(([name, data]) => ({ name, ...data }))
    .sort((a, b) => b.bytes - a.bytes)
);

const formatInt = (value?: number | null) => new Intl.NumberFormat("pt-BR").format(Number(value || 0));
const formatBytes = (value?: number | null) => {
  const bytes = Number(value || 0);
  if (bytes < 1024 * 1024) return `${formatInt(Math.round(bytes / 1024))} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MB`;
  return `${(bytes / 1024 ** 3).toLocaleString("pt-BR", { maximumFractionDigits: 2 })} GB`;
};
const formatDateTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
};
const relative = (value: string) => {
  const days = Math.floor((Date.now() - new Date(value).getTime()) / 86400000);
  if (days <= 0) return "Hoje";
  if (days === 1) return "Ontem";
  if (days < 60) return `Há ${days} dias`;
  return `Há ${Math.round(days / 30)} meses`;
};
const offlineText = (item: Company) => {
  if (item.online) return "No ar";
  if (item.status_days === null) return "Desde: sem registro";
  return `${item.since_estimated ? "≈ " : ""}${item.status_days} dia${item.status_days === 1 ? "" : "s"}`;
};
const stageLabel = (stage: MediaStage) =>
  ({ hot: "Normal", cool: "Cool", archive: "Archive", restoring: "Restaurando", deleted: "Excluídos" })[stage] || stage;
const stageTone = (stage: MediaStage) =>
  ({ hot: "am-tone-neutral", cool: "am-tone-info", archive: "am-tone-violet", restoring: "am-tone-warning", deleted: "am-tone-danger" })[stage] || "am-tone-neutral";
const hasActions = (item: Company) => (!item.online && item.media_stage !== "deleted") || item.media_stage === "cool" || item.media_stage === "archive";
const errorText = (error: any, fallback: string) => error?.response?.data?.detail || fallback;

const load = async () => {
  loading.value = true;
  try {
    const [response, storageResponse] = await Promise.all([listCompanies(), getStorageStatus()]);
    items.value = response.items;
    Object.assign(summary, response.summary);
    Object.assign(storage, storageResponse);
    if (storage.status === "running") schedulePoll();
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível carregar o armazenamento.");
  } finally {
    loading.value = false;
  }
};

const schedulePoll = () => {
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = setTimeout(async () => {
    try {
      Object.assign(storage, await getStorageStatus());
    } catch {
      /* tenta de novo no próximo ciclo */
    }
    if (storage.status === "running") schedulePoll();
    else await load();
  }, 3000);
};

const analyze = async () => {
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await startStorageAnalysis();
    storage.status = "running";
    schedulePoll();
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível começar a análise.");
  }
};

const actionText: Record<Action, { ask: string; done: string }> = {
  cool: { ask: "Mover os arquivos para Cool? Continuam disponíveis, com armazenamento mais barato.", done: "movidos para Cool" },
  archive: { ask: "Mover os arquivos para Archive? Ficam indisponíveis e, se a empresa voltar, restaurar leva algumas horas.", done: "movidos para Archive" },
  restore: { ask: "Restaurar os arquivos para a camada normal? Do Archive, o Azure leva algumas horas.", done: "em restauração" }
};

const act = async (item: Company, action: Action) => {
  menuId.value = null;
  if (!window.confirm(`${item.name}: ${actionText[action].ask}`)) return;
  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const result = await moveCompanyMedia(item.id, action);
    successMessage.value = `${item.name}: arquivos ${actionText[action].done}.${result?.error ? ` Alguns arquivos falharam: ${result.error}` : ""}`;
    await load();
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível concluir a ação.");
  } finally {
    busy.value = false;
  }
};

/** Ações em massa: uma empresa por vez; o servidor confere as regras de cada uma (prazos, se está no ar). */
const runBulk = async (list: Company[], run: (item: Company) => Promise<unknown>, doneText: string) => {
  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  const failed: string[] = [];
  let done = 0;
  for (const [index, item] of list.entries()) {
    progress.value = `${index + 1} de ${list.length}: ${item.name}...`;
    try {
      await run(item);
      done += 1;
    } catch (error: any) {
      failed.push(`${item.name} (${errorText(error, "erro")})`);
    }
  }
  progress.value = "";
  busy.value = false;
  if (done) successMessage.value = `${done} empresa(s): arquivos ${doneText}.`;
  if (failed.length) errorMessage.value = `Não foi possível em ${failed.length}: ${failed.join("; ")}`;
  selection.clear();
  await load();
};

const bulk = async (action: Action) => {
  const list = selectedItems.value;
  if (!list.length || !window.confirm(`${list.length} empresa(s) selecionada(s). ${actionText[action].ask}`)) return;
  await runBulk(list, item => moveCompanyMedia(item.id, action), actionText[action].done);
};

const removeMedia = async (item: Company) => {
  menuId.value = null;
  const typed = window.prompt(
    `Excluir de vez os arquivos de ${item.name}? Não dá para desfazer (a não ser pela exclusão reversível do Azure, se estiver ligada).\n\nPara confirmar, digite: ${item.slug}`
  );
  if (typed === null) return;
  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await deleteCompanyMedia(item.id, typed);
    successMessage.value = `${item.name}: arquivos excluídos.`;
    await load();
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível excluir.");
  } finally {
    busy.value = false;
  }
};

const bulkDelete = async () => {
  const list = selectedItems.value;
  if (!list.length) return;
  const phrase = `EXCLUIR ${list.length}`;
  const typed = window.prompt(
    `Excluir de vez os arquivos de ${list.length} empresa(s)? Não dá para desfazer (a não ser pela exclusão reversível do Azure, se estiver ligada). Só empresas fora do ar há mais de 30 dias são excluídas; as outras são recusadas pelo servidor.\n\n${list
      .slice(0, 12)
      .map(item => `• ${item.name}`)
      .join("\n")}${list.length > 12 ? `\n… e mais ${list.length - 12}` : ""}\n\nPara confirmar, digite: ${phrase}`
  );
  if (typed === null) return;
  if (typed.trim().toUpperCase() !== phrase) {
    errorMessage.value = `Confirmação diferente de "${phrase}". Nada foi excluído.`;
    return;
  }
  await runBulk(list, item => deleteCompanyMedia(item.id, item.slug), "excluídos");
};

const deleteOrphans = async () => {
  const typed = window.prompt(
    `Excluir ${storage.orphans.ready_groups} imagens sem uso há mais de ${summary.rules.orphan_grace_days} dias (${formatBytes(storage.orphans.ready_bytes)})? Antes de excluir, o sistema confere de novo se continuam sem uso.\n\nPara confirmar, digite: EXCLUIR`
  );
  if (typed === null) return;
  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const result = await deleteReadyOrphans(typed);
    successMessage.value = `${formatInt(result.deleted_files)} arquivos excluídos (${formatBytes(result.deleted_bytes)}).${result.kept ? ` ${result.kept} voltaram a ser usados e ficaram.` : ""}`;
    await load();
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível excluir.");
  } finally {
    busy.value = false;
  }
};

const closeMenuOnOutside = (event: MouseEvent) => {
  if (menuId.value === null) return;
  if (!event.composedPath().some(el => (el as HTMLElement)?.dataset?.storageMenu === "true")) menuId.value = null;
};

onMounted(() => {
  load();
  if (pickedIds.length) selection.selected.value = [...pickedIds];
  document.addEventListener("click", closeMenuOnOutside);
});
onBeforeUnmount(() => {
  document.removeEventListener("click", closeMenuOnOutside);
  if (pollTimer) clearTimeout(pollTimer);
});
</script>

<style scoped>
.sp-tiers {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 10px;
}
.sp-tiers > div {
  display: grid;
  gap: 2px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
}
.sp-tiers b {
  font-size: 18px;
}
.sp-check-col {
  width: 36px;
}
.sp-check {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
  cursor: pointer;
}
.sp-sort {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: inherit;
  color: inherit;
  text-transform: inherit;
  letter-spacing: inherit;
  white-space: nowrap;
}
.sp-sort span {
  opacity: 0.45;
}
.sp-sort.on,
.sp-sort.on span {
  color: var(--foreground);
  opacity: 1;
}
.sp-bulk {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--accent);
  color: var(--accent-foreground);
  font-size: 13px;
}
.sp-row-on td {
  background: color-mix(in srgb, var(--accent) 60%, transparent);
}
</style>
