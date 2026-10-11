<template>
  <section class="am-page">
    <AdminMasterHeader
      title="Empresas"
      subtitle="Situação de cada agência, há quanto tempo está desativada e o espaço que ocupa. O material de quem saiu do ar vai para camadas mais baratas do armazenamento."
    >
      <button type="button" class="am-btn" :disabled="loading" @click="load"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="successMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ successMessage }}</span></div>

    <section class="am-grid-4">
      <AdminMasterKpi icon="check" tone="success" label="No ar" :value="formatInt(onlineCount)" :hint="`${formatInt(count('active'))} ativas · ${formatInt(count('trial'))} em teste · ${formatInt(count('cancelling'))} cancelando${count('internal') ? ` · ${count('internal')} internas` : ''}`" />
      <AdminMasterKpi icon="alert" tone="warning" label="Inadimplentes" :value="formatInt(count('past_due'))" hint="Ainda no ar (menos de 3 falhas de cobrança)" />
      <AdminMasterKpi icon="pause" tone="info" label="Desativadas" :value="formatInt(count('inactive'))" :hint="`${formatInt(summary.inactive_over_30)} há mais de 30 dias`" />
      <AdminMasterKpi
        icon="building"
        tone="violet"
        label="Espaço das desativadas"
        :value="formatBytes(summary.inactive_bytes)"
        :hint="`${formatBytes(summary.archived_bytes)} já em Cool/Archive`"
      />
    </section>

    <section class="am-card">
      <div class="am-card-head">
        <div>
          <div class="am-card-title">Armazenamento</div>
          <div class="am-card-sub">
            Regras: Cool {{ summary.rules.cool_after_days }} dias depois de sair do ar, Archive aos {{ summary.rules.archive_after_days }} dias.
            Arquivos sem uso só podem ser excluídos depois de {{ summary.rules.orphan_grace_days }} dias seguidos sem uso.
          </div>
        </div>
        <button type="button" class="am-btn am-btn-primary shrink-0" :disabled="storage.status === 'running'" @click="analyze">
          <AmIcon name="search" :class="storage.status === 'running' ? 'animate-spin' : ''" />{{ storage.status === "running" ? "Analisando..." : "Analisar agora" }}
        </button>
      </div>
      <div class="am-notice mb-3" :class="summary.automation ? 'am-tone-success' : 'am-tone-neutral'">
        <AmIcon :name="summary.automation ? 'check' : 'info'" />
        <span v-if="summary.automation">Automação ligada: todo dia de madrugada o sistema analisa, move para Cool/Archive quem passou dos prazos e restaura quem voltou a assinar. Exclusão é sempre manual.</span>
        <span v-else>Automação desligada: nada muda sozinho. Use os botões abaixo (ou ligue MEDIA_LIFECYCLE_AUTOMATION no servidor do admin depois de conferir os resultados).</span>
      </div>
      <div v-if="storage.status === 'error'" class="am-notice am-tone-danger mb-3"><AmIcon name="alert" /><span>A análise parou: {{ storage.error }}</span></div>
      <div class="cp-storage">
        <div>
          <span class="am-muted text-xs">Total guardado</span>
          <b>{{ storage.summary.total_bytes !== undefined ? formatBytes(storage.summary.total_bytes) : "—" }}</b>
          <small class="am-muted">{{ storage.summary.total_files !== undefined ? `${formatInt(storage.summary.total_files)} arquivos` : "Rode a análise" }}</small>
        </div>
        <div v-for="tier in tierRows" :key="tier.name">
          <span class="am-muted text-xs">Camada {{ tier.name }}</span>
          <b>{{ formatBytes(tier.bytes) }}</b>
          <small class="am-muted">{{ formatInt(tier.files) }} arquivos</small>
        </div>
        <div>
          <span class="am-muted text-xs">Sem uso</span>
          <b>{{ formatBytes(storage.orphans.bytes) }}</b>
          <small class="am-muted">{{ formatInt(storage.orphans.groups) }} imagens · {{ formatInt(storage.orphans.ready_groups) }} prontas para excluir</small>
        </div>
      </div>
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <button type="button" class="am-btn" :disabled="!storage.orphans.ready_groups || busy" @click="deleteOrphans">
          <AmIcon name="trash" />Excluir sem uso prontas ({{ formatBytes(storage.orphans.ready_bytes) }})
        </button>
        <small class="am-muted">
          {{ storage.finished_at ? `Última análise: ${formatDateTime(storage.finished_at)}` : "Nenhuma análise ainda." }}
          Inclui fotos que estão só na biblioteca, fora de qualquer página.
        </small>
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
      <div class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th>Empresa</th>
              <th>Situação</th>
              <th>Último acesso</th>
              <th class="am-right">Páginas</th>
              <th class="am-right">Visitas 30d</th>
              <th>Arquivos</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !items.length">
              <td colspan="7"><div class="am-empty"><div class="am-spinner"></div>Carregando empresas...</div></td>
            </tr>
            <tr v-for="item in visibleItems" :key="item.id">
              <td>
                <b class="font-semibold">{{ item.name }}</b>
                <small class="am-muted block">{{ item.owner_email || "sem dono" }} · {{ planLabel(item.plan) }}</small>
              </td>
              <td>
                <span class="am-badge am-dot" :class="statusTone(item.status)">{{ item.status_label }}</span>
                <small class="am-muted block text-xs">{{ statusDetail(item) }}</small>
              </td>
              <td class="am-num">{{ item.last_access_at ? relative(item.last_access_at) : "Nunca" }}</td>
              <td class="am-num am-right">{{ item.pages_published }}/{{ item.pages_total }}</td>
              <td class="am-num am-right">{{ formatInt(item.visits_30d) }}</td>
              <td>
                <template v-if="item.media_measured_at || item.media_stage !== 'hot'">
                  <span class="am-badge" :class="stageTone(item.media_stage)">{{ stageLabel(item.media_stage) }}</span>
                  <small class="am-muted block text-xs">
                    {{ formatBytes(item.media_bytes) }} · {{ formatInt(item.media_files) }} arquivos{{ item.media_shared_skipped ? ` · ${item.media_shared_skipped} compartilhados ficam` : "" }}
                  </small>
                </template>
                <small v-else class="am-muted text-xs">{{ item.status === "inactive" ? "Rode a análise" : "—" }}</small>
                <small v-if="item.next_step" class="block text-xs font-semibold">{{ item.next_step }}</small>
                <small v-if="item.media_error" class="block text-xs text-red-600">{{ item.media_error }}</small>
              </td>
              <td class="am-right">
                <div v-if="hasActions(item)" class="relative inline-block" data-company-menu="true">
                  <button type="button" class="am-icon-btn" :aria-label="`Ações de ${item.name}`" @click="menuId = menuId === item.id ? null : item.id">
                    <AmIcon name="dots" />
                  </button>
                  <div v-if="menuId === item.id" class="am-menu right-0 top-full mt-1">
                    <template v-if="item.status === 'inactive' && item.media_stage !== 'deleted'">
                      <button v-if="item.media_stage === 'hot' || item.media_stage === 'restoring'" type="button" @click="act(item, 'cool')"><AmIcon name="pause" />Mover para Cool</button>
                      <button v-if="item.media_stage !== 'archive'" type="button" @click="act(item, 'archive')"><AmIcon name="dl" />Mover para Archive</button>
                    </template>
                    <button v-if="item.media_stage === 'cool' || item.media_stage === 'archive'" type="button" @click="act(item, 'restore')"><AmIcon name="undo" />Restaurar arquivos</button>
                    <button v-if="item.status === 'inactive' && item.media_stage !== 'deleted'" type="button" class="is-danger" @click="removeMedia(item)"><AmIcon name="trash" />Excluir arquivos</button>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !visibleItems.length">
              <td colspan="7"><div class="am-empty">Nenhuma empresa neste filtro.</div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  deleteCompanyMedia,
  deleteReadyOrphans,
  getStorageStatus,
  listCompanies,
  moveCompanyMedia,
  startStorageAnalysis,
  type CompaniesResponse,
  type Company,
  type CompanyStatusKey,
  type MediaStage,
  type StorageStatus
} from "../../services/companies";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";

type Filter = "all" | CompanyStatusKey | "inactive_30" | "archived";
const filters: Array<{ value: Filter; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "active", label: "Ativas" },
  { value: "trial", label: "Em teste" },
  { value: "past_due", label: "Inadimplentes" },
  { value: "cancelling", label: "Cancelando" },
  { value: "inactive", label: "Desativadas" },
  { value: "inactive_30", label: "Desativadas +30 dias" },
  { value: "archived", label: "Com arquivos arquivados" }
];

const loading = ref(false);
const busy = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const items = ref<Company[]>([]);
const filter = ref<Filter>("all");
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

const count = (key: CompanyStatusKey) => summary.counts[key] || 0;
const onlineCount = computed(() => items.value.filter(item => item.online).length);
const matches = (item: Company, value: Filter) => {
  if (value === "all") return true;
  if (value === "inactive_30") return item.status === "inactive" && (item.status_days || 0) >= 30;
  if (value === "archived") return item.media_stage === "cool" || item.media_stage === "archive";
  return item.status === value;
};
const filterCount = (value: Filter) => items.value.filter(item => matches(item, value)).length;
const visibleItems = computed(() => {
  const text = query.value.trim().toLowerCase();
  return items.value.filter(
    item => matches(item, filter.value) && (!text || `${item.name} ${item.slug} ${item.owner_email || ""}`.toLowerCase().includes(text))
  );
});
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
const planLabel = (plan: string | null) => (plan ? plan.charAt(0).toUpperCase() + plan.slice(1) : "sem plano");
const statusTone = (status: CompanyStatusKey) =>
  ({ active: "am-tone-success", internal: "am-tone-violet", trial: "am-tone-info", cancelling: "am-tone-warning", past_due: "am-tone-warning", inactive: "am-tone-danger", no_owner: "am-tone-neutral" })[status] ||
  "am-tone-neutral";
const statusDetail = (item: Company) => {
  if (item.status === "inactive") {
    if (item.status_days === null) return "Desde: sem registro";
    return `Fora do ar há ${item.since_estimated ? "≈ " : ""}${item.status_days} dia${item.status_days === 1 ? "" : "s"}`;
  }
  if (item.status === "cancelling" && item.valid_until) return `No ar até ${new Date(item.valid_until).toLocaleDateString("pt-BR")}`;
  if (item.status === "trial" && item.status_days !== null) return `Teste há ${item.status_days} dia(s)`;
  if (item.status === "active" && item.status_days !== null) return `Cliente há ${item.status_days} dia(s)`;
  return "";
};
const stageLabel = (stage: MediaStage) =>
  ({ hot: "Normal", cool: "Cool", archive: "Archive", restoring: "Restaurando", deleted: "Excluídos" })[stage] || stage;
const stageTone = (stage: MediaStage) =>
  ({ hot: "am-tone-neutral", cool: "am-tone-info", archive: "am-tone-violet", restoring: "am-tone-warning", deleted: "am-tone-danger" })[stage] || "am-tone-neutral";
const hasActions = (item: Company) =>
  (item.status === "inactive" && item.media_stage !== "deleted") || item.media_stage === "cool" || item.media_stage === "archive";
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
    errorMessage.value = errorText(error, "Não foi possível carregar as empresas.");
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

const actionText: Record<"cool" | "archive" | "restore", { ask: string; done: string }> = {
  cool: { ask: "Mover os arquivos desta empresa para Cool? Continuam disponíveis, com armazenamento mais barato.", done: "Arquivos movidos para Cool." },
  archive: {
    ask: "Mover os arquivos para Archive? Ficam indisponíveis e, se a empresa voltar, restaurar leva algumas horas.",
    done: "Arquivos movidos para Archive."
  },
  restore: { ask: "Restaurar os arquivos para a camada normal? Do Archive, o Azure leva algumas horas.", done: "Restauração iniciada." }
};

const act = async (item: Company, action: "cool" | "archive" | "restore") => {
  menuId.value = null;
  if (!window.confirm(`${item.name}: ${actionText[action].ask}`)) return;
  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const result = await moveCompanyMedia(item.id, action);
    successMessage.value = `${item.name}: ${actionText[action].done}${result?.error ? ` Alguns arquivos falharam: ${result.error}` : ""}`;
    await load();
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível concluir a ação.");
  } finally {
    busy.value = false;
  }
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
  if (!event.composedPath().some(el => (el as HTMLElement)?.dataset?.companyMenu === "true")) menuId.value = null;
};

onMounted(() => {
  load();
  document.addEventListener("click", closeMenuOnOutside);
});
onBeforeUnmount(() => {
  document.removeEventListener("click", closeMenuOnOutside);
  if (pollTimer) clearTimeout(pollTimer);
});
</script>

<style scoped>
.cp-storage {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 10px;
}
.cp-storage > div {
  display: grid;
  gap: 2px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
}
.cp-storage b {
  font-size: 18px;
}
</style>
