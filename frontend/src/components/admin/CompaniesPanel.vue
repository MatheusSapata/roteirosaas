<template>
  <section class="am-page">
    <AdminMasterHeader
      title="Empresas"
      subtitle="Situação de cada agência: quem paga, quem está em teste, quem ficou no gratuito ou com o teste encerrado e quem saiu do ar. O espaço dos arquivos fica em Armazenamento."
    >
      <router-link to="/admin/administracao/armazenamento" class="am-btn"><AmIcon name="database" />Armazenamento</router-link>
      <button type="button" class="am-btn" :disabled="loading" @click="load"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="successMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ successMessage }}</span></div>

    <section class="am-grid-4">
      <AdminMasterKpi
        icon="check"
        tone="success"
        label="Clientes pagantes"
        :value="formatInt(paying)"
        :hint="`${formatInt(count('active'))} ativas · ${formatInt(count('past_due'))} inadimplentes · ${formatInt(count('cancelling'))} cancelando`"
      />
      <AdminMasterKpi icon="history" tone="info" label="Em teste" :value="formatInt(count('trial'))" hint="Teste grátis ainda valendo" />
      <AdminMasterKpi
        icon="user"
        tone="neutral"
        label="Sem assinatura paga"
        :value="formatInt(count('free') + count('trial_ended'))"
        :hint="`${formatInt(count('free'))} gratuitas · ${formatInt(count('trial_ended'))} com teste encerrado`"
      />
      <AdminMasterKpi
        icon="pause"
        tone="warning"
        label="Desativadas"
        :value="formatInt(count('inactive'))"
        :hint="`${formatInt(summary.inactive_over_30)} há mais de 30 dias${count('internal') ? ` · ${count('internal')} internas fora da conta` : ''}`"
      />
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

      <div v-if="selection.selected.value.length" class="cp-bulk">
        <b>{{ selection.selected.value.length }} selecionada(s)</b>
        <button type="button" class="am-btn am-btn-sm" @click="copyEmails"><AmIcon name="copy" />Copiar e-mails</button>
        <button type="button" class="am-btn am-btn-sm" @click="exportCsv"><AmIcon name="dl" />Exportar CSV</button>
        <router-link :to="{ path: '/admin/administracao/armazenamento', query: { ids: selection.selected.value.join(',') } }" class="am-btn am-btn-sm">
          <AmIcon name="database" />Ver no armazenamento
        </router-link>
        <button type="button" class="am-btn am-btn-sm ml-auto" @click="selection.clear()"><AmIcon name="x" />Limpar seleção</button>
      </div>

      <div class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th class="cp-check-col">
                <input type="checkbox" class="cp-check" :checked="selection.allVisibleSelected.value" aria-label="Selecionar todas desta lista" @change="selection.toggleAll()" />
              </th>
              <th v-for="column in columns" :key="column.key" :class="column.right ? 'am-right' : ''" :aria-sort="sort.ariaSort(column.key)">
                <button type="button" class="cp-sort" :class="{ on: sort.sortKey.value === column.key }" @click="sort.setSort(column.key)">
                  {{ column.label }} <span aria-hidden="true">{{ sort.arrow(column.key) }}</span>
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !items.length">
              <td :colspan="columns.length + 1"><div class="am-empty"><div class="am-spinner"></div>Carregando empresas...</div></td>
            </tr>
            <tr v-for="item in visibleItems" :key="item.id" :class="{ 'cp-row-on': selection.isSelected(item) }">
              <td class="cp-check-col">
                <input type="checkbox" class="cp-check" :checked="selection.isSelected(item)" :aria-label="`Selecionar ${item.name}`" @change="selection.toggle(item)" />
              </td>
              <td>
                <b class="font-semibold">{{ item.name }}</b>
                <small class="am-muted block">{{ item.owner_email || "sem dono" }} · {{ planLabel(item.plan) }}</small>
              </td>
              <td><span class="am-badge am-dot" :class="statusTone(item.status)">{{ item.status_label }}</span></td>
              <td class="am-num">{{ statusDetail(item) }}</td>
              <td class="am-num">{{ item.last_access_at ? relative(item.last_access_at) : "Nunca" }}</td>
              <td class="am-num am-right">{{ item.pages_published }}/{{ item.pages_total }}</td>
              <td class="am-num am-right">{{ formatInt(item.visits_30d) }}</td>
            </tr>
            <tr v-if="!loading && !visibleItems.length">
              <td :colspan="columns.length + 1"><div class="am-empty">Nenhuma empresa neste filtro.</div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { listCompanies, type CompaniesResponse, type Company, type CompanyStatusKey } from "../../services/companies";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";
import { useSelection, useTableSort } from "./master/useTableSort";

type Filter = "all" | CompanyStatusKey | "paying" | "inactive_30" | "no_use_60";
const filters: Array<{ value: Filter; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "paying", label: "Pagantes" },
  { value: "active", label: "Ativas" },
  { value: "past_due", label: "Inadimplentes" },
  { value: "cancelling", label: "Cancelando" },
  { value: "trial", label: "Em teste" },
  { value: "trial_ended", label: "Teste encerrado" },
  { value: "free", label: "Gratuitas" },
  { value: "inactive", label: "Desativadas" },
  { value: "inactive_30", label: "Desativadas +30 dias" },
  { value: "no_use_60", label: "Sem acesso +60 dias" },
  { value: "internal", label: "Internas" }
];
const PAYING: CompanyStatusKey[] = ["active", "past_due", "cancelling"];
// Ordem de gravidade usada ao ordenar pela coluna Situação.
const STATUS_ORDER: CompanyStatusKey[] = ["inactive", "past_due", "cancelling", "trial_ended", "free", "trial", "active", "internal", "no_owner"];

const columns = [
  { key: "name", label: "Empresa" },
  { key: "status", label: "Situação" },
  { key: "status_days", label: "Há quanto tempo" },
  { key: "last_access", label: "Último acesso" },
  { key: "pages", label: "Páginas", right: true },
  { key: "visits", label: "Visitas 30d", right: true }
];

const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const items = ref<Company[]>([]);
const filter = ref<Filter>("all");
const query = ref("");
const summary = reactive<CompaniesResponse["summary"]>({
  counts: {},
  total: 0,
  inactive_over_30: 0,
  inactive_bytes: 0,
  archived_bytes: 0,
  automation: false,
  rules: { cool_after_days: 7, archive_after_days: 30, orphan_grace_days: 30 }
});

const count = (key: CompanyStatusKey) => summary.counts[key] || 0;
const paying = computed(() => PAYING.reduce((total, key) => total + count(key), 0));
const daysSince = (value: string | null) => (value ? Math.floor((Date.now() - new Date(value).getTime()) / 86400000) : null);
const matches = (item: Company, value: Filter) => {
  if (value === "all") return true;
  if (value === "paying") return PAYING.includes(item.status);
  if (value === "inactive_30") return item.status === "inactive" && (item.status_days || 0) >= 30;
  if (value === "no_use_60") return (daysSince(item.last_access_at) ?? Infinity) >= 60;
  return item.status === value;
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
    status: item => STATUS_ORDER.indexOf(item.status),
    status_days: item => item.status_days,
    // Nunca acessou conta como o acesso mais antigo de todos.
    last_access: item => (item.last_access_at ? new Date(item.last_access_at).getTime() : 0),
    pages: item => item.pages_published,
    visits: item => item.visits_30d
  },
  { key: "status_days", dir: "desc" },
  { status_days: "desc", last_access: "asc", pages: "desc", visits: "desc" }
);
const visibleItems = sort.sorted;
const selection = useSelection(visibleItems);
const selectedItems = computed(() => items.value.filter(item => selection.selected.value.includes(item.id)));

const formatInt = (value?: number | null) => new Intl.NumberFormat("pt-BR").format(Number(value || 0));
const relative = (value: string) => {
  const days = daysSince(value) ?? 0;
  if (days <= 0) return "Hoje";
  if (days === 1) return "Ontem";
  if (days < 60) return `Há ${days} dias`;
  return `Há ${Math.round(days / 30)} meses`;
};
const planLabel = (plan: string | null) => (plan ? plan.charAt(0).toUpperCase() + plan.slice(1) : "sem plano");
const statusTone = (status: CompanyStatusKey) =>
  ({
    active: "am-tone-success",
    internal: "am-tone-violet",
    trial: "am-tone-info",
    free: "am-tone-neutral",
    trial_ended: "am-tone-neutral",
    cancelling: "am-tone-warning",
    past_due: "am-tone-warning",
    inactive: "am-tone-danger",
    no_owner: "am-tone-neutral"
  })[status] || "am-tone-neutral";
const plural = (days: number) => `${days} dia${days === 1 ? "" : "s"}`;
const statusDetail = (item: Company) => {
  const days = item.status_days;
  if (item.status === "inactive") return days === null ? "Sem registro" : `Fora do ar há ${item.since_estimated ? "≈ " : ""}${plural(days)}`;
  if (item.status === "cancelling" && item.valid_until) return `No ar até ${new Date(item.valid_until).toLocaleDateString("pt-BR")}`;
  if (days === null) return "—";
  if (item.status === "trial") return `Teste há ${plural(days)}`;
  if (item.status === "trial_ended") return `Teste acabou há ${plural(days)}`;
  if (item.status === "free") return `Gratuita há ${plural(days)}`;
  if (item.status === "active") return `Cliente há ${plural(days)}`;
  return `${plural(days)}`;
};
const errorText = (error: any, fallback: string) => error?.response?.data?.detail || fallback;

const copyEmails = async () => {
  const emails = [...new Set(selectedItems.value.map(item => item.owner_email).filter(Boolean))].join(", ");
  try {
    await navigator.clipboard.writeText(emails);
    successMessage.value = `${selectedItems.value.length} e-mail(s) copiados.`;
  } catch {
    window.prompt("Copie os e-mails:", emails);
  }
};

const exportCsv = () => {
  const quote = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const header = ["Empresa", "E-mail", "Plano", "Situação", "Há quanto tempo", "Último acesso", "Páginas publicadas", "Páginas", "Visitas 30d"];
  const rows = selectedItems.value.map(item => [
    item.name,
    item.owner_email,
    planLabel(item.plan),
    item.status_label,
    statusDetail(item),
    item.last_access_at ? new Date(item.last_access_at).toLocaleDateString("pt-BR") : "Nunca",
    item.pages_published,
    item.pages_total,
    item.visits_30d
  ]);
  const csv = [header, ...rows].map(row => row.map(quote).join(";")).join("\n");
  const url = URL.createObjectURL(new Blob([`﻿${csv}`], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `empresas-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
};

const load = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    const response = await listCompanies();
    items.value = response.items;
    Object.assign(summary, response.summary);
  } catch (error: any) {
    errorMessage.value = errorText(error, "Não foi possível carregar as empresas.");
  } finally {
    loading.value = false;
  }
};

onMounted(load);
</script>

<style scoped>
.cp-check-col {
  width: 36px;
}
.cp-check {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
  cursor: pointer;
}
.cp-sort {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: inherit;
  color: inherit;
  text-transform: inherit;
  letter-spacing: inherit;
  white-space: nowrap;
}
.cp-sort span {
  opacity: 0.45;
}
.cp-sort.on,
.cp-sort.on span {
  color: var(--foreground);
  opacity: 1;
}
.cp-bulk {
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
.cp-row-on td {
  background: color-mix(in srgb, var(--accent) 60%, transparent);
}
</style>
