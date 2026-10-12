<template>
  <section class="am-page">
    <AdminMasterHeader
      title="Empresas"
      subtitle="Cada agência cliente: dono, plano, cobrança, prazo e uso. Clique numa empresa para ver tudo e mudar plano, validade ou assinatura."
    >
      <router-link to="/admin/administracao/armazenamento" class="am-btn"><AmIcon name="database" />Armazenamento</router-link>
      <button type="button" class="am-btn" :disabled="loading" @click="load()"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
      <button type="button" class="am-btn am-btn-primary" @click="createOpen = true"><AmIcon name="plus" />Nova empresa</button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="successMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ successMessage }}</span></div>

    <section class="am-grid-4">
      <AdminMasterKpi
        icon="check"
        tone="success"
        label="Ativas com pagamento"
        :value="formatInt(filterCount('paying'))"
        :hint="`${formatInt(count('active'))} em dia · ${formatInt(count('cancelling'))} cancelando no fim do período · fora ${plural(count('past_due'), 'inadimplente', 'inadimplentes')}`"
      />
      <AdminMasterKpi
        icon="history"
        tone="info"
        label="Em teste"
        :value="formatInt(count('trial'))"
        :hint="`${formatInt(filterCount('trial_ending'))} terminam em até 3 dias`"
      />
      <AdminMasterKpi
        icon="alert"
        tone="warning"
        label="Acesso grátis vencido"
        :value="formatInt(count('free_expired') + count('trial_ended'))"
        :hint="`${formatInt(count('free_expired'))} gratuitas vencidas · ${formatInt(count('trial_ended'))} testes encerrados · ${formatInt(count('free'))} gratuitas no prazo`"
      />
      <AdminMasterKpi
        icon="pause"
        tone="danger"
        label="Desativadas"
        :value="formatInt(count('inactive'))"
        :hint="`${formatInt(summary.inactive_over_30)} há mais de 30 dias${count('internal') ? ` · ${count('internal')} internas fora da conta` : ''}`"
      />
    </section>

    <section class="am-card am-card-flush">
      <div class="am-toolbar">
        <button
          v-for="option in visibleFilters"
          :key="option.value"
          type="button"
          class="am-chip"
          :class="{ on: filter === option.value }"
          :title="option.hint"
          @click="filter = option.value"
        >
          {{ option.label }} <span class="am-count am-num">{{ formatInt(filterCount(option.value)) }}</span>
        </button>
      </div>
      <div class="am-toolbar">
        <label class="am-search">
          <AmIcon name="search" />
          <input v-model="query" type="search" placeholder="Buscar por empresa, dono, e-mail ou WhatsApp" aria-label="Buscar empresa" />
        </label>
        <select v-model="planFilter" class="am-select" aria-label="Filtrar por plano">
          <option value="">Plano: todos</option>
          <option v-for="plan in planChoices" :key="plan" :value="plan">{{ planLabel(plan) }}</option>
        </select>
        <select v-model="gatewayFilter" class="am-select" aria-label="Filtrar por cobrança">
          <option value="">Cobrança: todas</option>
          <option v-for="gateway in gatewayChoices" :key="gateway" :value="gateway">{{ gatewayLabel(gateway === "__none" ? "" : gateway) }}</option>
        </select>
        <select v-model.number="createdWithin" class="am-select" aria-label="Filtrar por data de cadastro">
          <option :value="0">Cadastro: qualquer data</option>
          <option :value="1">Cadastradas hoje</option>
          <option :value="7">Nos últimos 7 dias</option>
          <option :value="30">Nos últimos 30 dias</option>
          <option :value="90">Nos últimos 90 dias</option>
        </select>
        <button v-if="hasExtraFilters" type="button" class="am-chip" @click="clearFilters"><AmIcon name="x" class="h-3.5 w-3.5" />Limpar</button>
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
                <input type="checkbox" class="cp-check" :checked="selection.allVisibleSelected.value" aria-label="Selecionar todas desta página" @change="selection.toggleAll()" />
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
            <tr
              v-for="item in pageItems"
              :key="item.id"
              class="cursor-pointer"
              :class="{ 'cp-row-on': selection.isSelected(item) || selectedId === item.id }"
              @click="openCompany(item)"
            >
              <td class="cp-check-col" @click.stop>
                <input type="checkbox" class="cp-check" :checked="selection.isSelected(item)" :aria-label="`Selecionar ${item.name}`" @change="selection.toggle(item)" />
              </td>
              <td>
                <button type="button" class="cp-name" @click.stop="openCompany(item)">{{ item.name }}</button>
                <small class="am-muted block max-w-[280px] truncate">{{ item.owner_name || "Sem dono" }}<template v-if="item.owner_email"> · {{ item.owner_email }}</template></small>
              </td>
              <td>
                <span class="am-badge am-dot" :class="statusTone(item.status)">{{ item.status_label }}</span>
                <small class="am-muted mt-1 block whitespace-nowrap">{{ statusDetail(item) }}</small>
              </td>
              <td>
                <span class="block whitespace-nowrap">{{ planLabel(item.plan) }}</span>
                <small class="am-muted block whitespace-nowrap">{{ gatewayLabel(billingProvider(item)) }}<template v-if="item.mrr_amount"> · {{ formatMoney(item.mrr_amount) }}/mês</template></small>
              </td>
              <td class="am-num">
                {{ formatDate(item.created_at) }}
                <small class="am-muted block">{{ relativeDay(item.created_at) }}</small>
              </td>
              <td class="am-num">{{ item.last_access_at ? relativeDay(item.last_access_at) : "Nunca" }}</td>
              <td class="am-num am-right">
                {{ item.pages_published }}/{{ item.pages_total }} {{ item.pages_total === 1 ? "página" : "páginas" }}
                <small class="am-muted block">{{ formatInt(item.visits_30d) }} visitas em 30 dias</small>
              </td>
            </tr>
            <tr v-if="!loading && !pageItems.length">
              <td :colspan="columns.length + 1"><div class="am-empty">Nenhuma empresa com esses filtros.</div></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="am-foot">
        <span>Mostrando {{ formatInt(range.start) }}–{{ formatInt(range.end) }} de {{ formatInt(sorted.length) }}</span>
        <div class="flex flex-wrap items-center gap-2">
          <label class="flex items-center gap-2">
            Linhas
            <select v-model.number="pageSize" class="am-select">
              <option v-for="size in [25, 50, 100]" :key="size" :value="size">{{ size }}</option>
            </select>
          </label>
          <button type="button" class="am-chip" :disabled="page <= 1" @click="page -= 1">Anterior</button>
          <span>Página {{ page }} de {{ totalPages }}</span>
          <button type="button" class="am-chip" :disabled="page >= totalPages" @click="page += 1">Próxima</button>
        </div>
      </div>
    </section>

    <CompanyDrawer :company="selectedCompany" :free-days="summary.rules.free_access_days || 7" @close="closeCompany" @changed="handleChanged" />
    <CreateCompanyDrawer :open="createOpen" @close="createOpen = false" @created="handleChanged" />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { listCompanies, type CompaniesResponse, type Company, type CompanyStatusKey } from "../../services/companies";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";
import { useSelection, useTableSort } from "./master/useTableSort";
import { daysSince, daysUntil, formatDate, formatInt, formatMoney, gatewayLabel, planLabel, plural, relativeDay, statusTone } from "./master/format";
import CompanyDrawer from "./companies/CompanyDrawer.vue";
import CreateCompanyDrawer from "./companies/CreateCompanyDrawer.vue";
import { billingProvider, statusDetail } from "./companies/companyStatus";

type Filter = "all" | CompanyStatusKey | "paying" | "trial_ending" | "no_use_60";
// "extra": só aparece quando chega selecionado por um link (ex.: do Painel).
const filters: Array<{ value: Filter; label: string; hint?: string; extra?: boolean }> = [
  { value: "all", label: "Todas" },
  { value: "paying", label: "Ativas com pagamento", hint: "Pagamento em dia, incluindo quem cancelou e fica até o fim do período pago" },
  { value: "active", label: "Em dia", extra: true },
  { value: "trial_ending", label: "Teste termina em 3 dias", extra: true },
  { value: "past_due", label: "Inadimplentes", hint: "Cobrança com falha ou atrasada" },
  { value: "cancelling", label: "Cancelando" },
  { value: "trial", label: "Em teste" },
  { value: "free", label: "Gratuitas no prazo" },
  { value: "free_expired", label: "Gratuitas vencidas" },
  { value: "trial_ended", label: "Teste encerrado" },
  { value: "inactive", label: "Desativadas" },
  { value: "no_use_60", label: "Sem acesso +60 dias" },
  { value: "internal", label: "Internas" }
];
const visibleFilters = computed(() => filters.filter(option => !option.extra || filter.value === option.value));
const queryFilters: Record<string, Filter> = {
  pagantes: "paying",
  ativas: "active",
  inadimplentes: "past_due",
  cancelando: "cancelling",
  teste: "trial",
  "teste-acabando": "trial_ending",
  gratuitas: "free",
  vencidas: "free_expired",
  "teste-encerrado": "trial_ended",
  desativadas: "inactive"
};
// Ordem de gravidade usada ao ordenar pela coluna Situação.
const STATUS_ORDER: CompanyStatusKey[] = ["inactive", "past_due", "cancelling", "free_expired", "trial_ended", "free", "trial", "active", "internal", "no_owner"];

const columns = [
  { key: "name", label: "Empresa" },
  { key: "status", label: "Situação" },
  { key: "plan", label: "Plano" },
  { key: "created", label: "Cadastro" },
  { key: "last_access", label: "Último acesso" },
  { key: "visits", label: "Uso", right: true }
];

const route = useRoute();
const router = useRouter();
const firstQuery = (value: unknown) => String(Array.isArray(value) ? value[0] ?? "" : value ?? "");

const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const items = ref<Company[]>([]);
const filter = ref<Filter>(queryFilters[firstQuery(route.query.filtro)] || "all");
const query = ref(firstQuery(route.query.busca));
const planFilter = ref("");
const gatewayFilter = ref("");
const createdWithin = ref(0);
const createOpen = ref(false);
const summary = reactive<CompaniesResponse["summary"]>({
  counts: {},
  total: 0,
  inactive_over_30: 0,
  inactive_bytes: 0,
  archived_bytes: 0,
  automation: false,
  rules: { cool_after_days: 7, archive_after_days: 30, orphan_grace_days: 30, free_access_days: 7 }
});

const count = (key: CompanyStatusKey) => summary.counts[key] || 0;
const normalized = (value?: string | null) => String(value || "").trim().toLowerCase();
const matches = (item: Company, value: Filter) => {
  if (value === "all") return true;
  if (value === "paying") return item.status === "active" || item.status === "cancelling";
  if (value === "trial_ending") return item.status === "trial" && (daysUntil(item.access_until) ?? Infinity) <= 3;
  if (value === "no_use_60") return item.status !== "internal" && (daysSince(item.last_access_at) ?? Infinity) >= 60;
  return item.status === value;
};
const filterCount = (value: Filter) => items.value.filter(item => matches(item, value)).length;

const planChoices = computed(() => [...new Set(items.value.map(item => normalized(item.plan)).filter(Boolean))].sort());
const gatewayChoices = computed(() => {
  const set = new Set(items.value.map(item => billingProvider(item) || "__none"));
  return [...set].sort();
});
const hasExtraFilters = computed(() => Boolean(query.value.trim() || planFilter.value || gatewayFilter.value || createdWithin.value));
const clearFilters = () => {
  query.value = "";
  planFilter.value = "";
  gatewayFilter.value = "";
  createdWithin.value = 0;
};

const filtered = computed(() => {
  const text = normalized(query.value);
  const digits = text.replace(/\D/g, "");
  return items.value.filter(item => {
    if (!matches(item, filter.value)) return false;
    if (planFilter.value && normalized(item.plan) !== planFilter.value) return false;
    if (gatewayFilter.value && (billingProvider(item) || "__none") !== gatewayFilter.value) return false;
    if (createdWithin.value) {
      const age = daysSince(item.created_at);
      if (age === null || age >= createdWithin.value) return false;
    }
    if (!text) return true;
    const haystack = `${item.name} ${item.slug} ${item.owner_name || ""} ${item.owner_email || ""}`.toLowerCase();
    if (haystack.includes(text)) return true;
    return digits.length >= 4 && String(item.owner_whatsapp || "").replace(/\D/g, "").includes(digits);
  });
});

const time = (value?: string | null) => (value ? new Date(value).getTime() : null);
const sort = useTableSort(
  filtered,
  {
    name: item => item.name,
    status: item => STATUS_ORDER.indexOf(item.status),
    plan: item => planLabel(item.plan),
    created: item => time(item.created_at),
    // Nunca acessou conta como o acesso mais antigo de todos.
    last_access: item => time(item.last_access_at) ?? 0,
    visits: item => item.visits_30d
  },
  { key: "created", dir: "desc" },
  { created: "desc", last_access: "desc", visits: "desc" }
);
const sorted = sort.sorted;

const page = ref(1);
const pageSize = ref(25);
const totalPages = computed(() => Math.max(1, Math.ceil(sorted.value.length / pageSize.value)));
const pageItems = computed(() => sorted.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value));
const range = computed(() => {
  if (!sorted.value.length) return { start: 0, end: 0 };
  const start = (page.value - 1) * pageSize.value + 1;
  return { start, end: Math.min(sorted.value.length, start + pageSize.value - 1) };
});
watch([filter, query, planFilter, gatewayFilter, createdWithin, pageSize, () => sort.sortKey.value, () => sort.sortDir.value], () => {
  page.value = 1;
});
watch(totalPages, total => {
  if (page.value > total) page.value = total;
});

const selection = useSelection(pageItems);
const selectedItems = computed(() => items.value.filter(item => selection.selected.value.includes(item.id)));

// ---------- Empresa aberta (fica no endereço para dar para compartilhar) ----------
const selectedId = ref<number | null>(Number(firstQuery(route.query.empresa)) || null);
const selectedCompany = computed(() => items.value.find(item => item.id === selectedId.value) || null);
const openCompany = (item: Company) => {
  selectedId.value = item.id;
  void router.replace({ query: { ...route.query, empresa: String(item.id) } });
};
const closeCompany = () => {
  selectedId.value = null;
  const next = { ...route.query };
  delete next.empresa;
  void router.replace({ query: next });
};
watch(
  () => route.query.filtro,
  value => {
    if (value !== undefined) filter.value = queryFilters[firstQuery(value)] || "all";
  }
);

const handleChanged = async (message: string) => {
  if (message) {
    successMessage.value = message;
    errorMessage.value = "";
  }
  await load(true);
};

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
  const header = ["Empresa", "Dono", "E-mail", "WhatsApp", "Plano", "Cobrança", "Valor mensal", "Situação", "Detalhe", "Cadastro", "Último acesso", "Páginas publicadas", "Páginas", "Visitas 30d"];
  const rows = selectedItems.value.map(item => [
    item.name,
    item.owner_name,
    item.owner_email,
    item.owner_whatsapp,
    planLabel(item.plan),
    gatewayLabel(billingProvider(item)),
    item.mrr_amount ? item.mrr_amount.toFixed(2).replace(".", ",") : "",
    item.status_label,
    statusDetail(item),
    formatDate(item.created_at),
    item.last_access_at ? formatDate(item.last_access_at) : "Nunca",
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

const load = async (keepMessage = false) => {
  loading.value = true;
  errorMessage.value = "";
  if (!keepMessage) successMessage.value = "";
  try {
    const response = await listCompanies();
    items.value = response.items;
    Object.assign(summary, response.summary);
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível carregar as empresas.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => load());
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
.cp-name {
  display: block;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
  font-weight: 600;
  color: var(--foreground);
}
.cp-name:hover {
  text-decoration: underline;
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
