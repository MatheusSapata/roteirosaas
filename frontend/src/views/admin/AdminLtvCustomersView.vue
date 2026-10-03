<template>
  <div class="am-page w-full">
    <AdminMasterHeader
      title="LTV por cliente"
      subtitle="Quanto cada cliente da Cakto já pagou, pelos eventos de pagamento, renovação e cancelamento."
    >
      <button type="button" class="am-btn" :disabled="!rows.length" @click="exportCsv"><AmIcon name="dl" />Exportar CSV</button>
      <button type="button" class="am-btn" :disabled="loading" @click="loadLtv">
        <AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />
        {{ loading ? "Atualizando..." : "Atualizar" }}
      </button>
    </AdminMasterHeader>

    <section class="am-grid-4">
      <AdminMasterKpi icon="wallet" tone="success" label="LTV médio" :value="formatCurrency(averageLtv)" :hint="`${formatInt(ltv?.total_customers || 0)} clientes`" />
      <AdminMasterKpi icon="users" tone="info" label="Clientes ativos" :value="formatInt(ltv?.active_customers || 0)" :hint="`${activeShare}% da base`" />
      <AdminMasterKpi icon="alert" tone="danger" label="Cancelados" :value="formatInt(ltv?.cancelled_customers || 0)" hint="Com cancelamento registrado" />
      <AdminMasterKpi icon="trend" tone="violet" label="Receita acumulada" :value="formatCurrency(ltv?.total_revenue || 0)" :hint="`Média de ${averageRenewals} renovações`" />
    </section>

    <div v-if="error" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ error }}</span></div>

    <section class="am-card am-card-flush">
      <div class="am-toolbar">
        <label class="am-search">
          <AmIcon name="search" />
          <input v-model="search" type="search" placeholder="Buscar por nome ou e-mail" aria-label="Buscar cliente" />
        </label>
        <button v-for="option in statusOptions" :key="option.id" type="button" class="am-chip" :class="{ on: statusFilter === option.id }" @click="statusFilter = option.id">
          {{ option.label }}
        </button>
        <select v-model="sortBy" class="am-select" aria-label="Ordenar">
          <option value="revenue">Ordenar: maior LTV</option>
          <option value="renewals">Ordenar: mais renovações</option>
          <option value="entered">Ordenar: entrada mais recente</option>
        </select>
      </div>

      <div class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th class="w-10">#</th>
              <th>Cliente</th>
              <th>Situação</th>
              <th>Entrou em</th>
              <th class="am-right">Renovações</th>
              <th class="min-w-[220px]">Total pago</th>
              <th>Próxima renovação</th>
              <th>Último evento</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !rows.length">
              <td colspan="8"><div class="am-empty"><div class="am-spinner"></div>Carregando...</div></td>
            </tr>
            <tr v-else-if="!visibleRows.length">
              <td colspan="8"><div class="am-empty">{{ rows.length ? "Nenhum cliente nesse filtro." : "Sem dados de LTV." }}</div></td>
            </tr>
            <tr v-for="(row, index) in visibleRows" :key="row.email">
              <td class="am-num am-muted">{{ index + 1 }}</td>
              <td>
                <div class="am-who">
                  <span class="am-avatar">{{ initials(row.name || row.email) }}</span>
                  <div class="min-w-0">
                    <b class="truncate">{{ row.name || "Sem nome" }}</b>
                    <small class="truncate">{{ row.email }}</small>
                  </div>
                </div>
              </td>
              <td>
                <span class="am-badge am-dot" :class="row.is_active ? 'am-tone-success' : 'am-tone-danger'">{{ row.is_active ? "Ativo" : "Inativo" }}</span>
                <small v-if="row.cancelled_at" class="am-muted mt-1 block text-xs">Cancelou em {{ formatDate(row.cancelled_at) }}</small>
              </td>
              <td class="am-num">{{ formatDate(row.entered_at) }}</td>
              <td class="am-num am-right">{{ formatInt(row.renewals_count) }}</td>
              <td>
                <div class="flex items-center gap-3">
                  <div class="am-bar flex-1"><i :style="{ width: barWidth(row.total_revenue) }"></i></div>
                  <b class="am-num w-[104px] text-right">{{ formatCurrency(row.total_revenue) }}</b>
                </div>
              </td>
              <td class="am-num">{{ formatDate(row.next_renewal_at) }}</td>
              <td>
                <span>{{ eventLabel(row.last_event_type) }}</span>
                <small class="am-muted block text-xs">{{ formatDateTime(row.last_event_at) }}</small>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="am-foot"><span>{{ formatInt(visibleRows.length) }} de {{ formatInt(rows.length) }} clientes</span></div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import api from "../../services/api";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import AdminMasterKpi from "../../components/admin/master/AdminMasterKpi.vue";

interface LtvRow {
  email: string;
  name?: string | null;
  entered_at?: string | null;
  is_active: boolean;
  renewals_count: number;
  total_revenue: number;
  cancelled_at?: string | null;
  next_renewal_at?: string | null;
  last_event_type?: string | null;
  last_event_at?: string | null;
}

interface LtvResponse {
  total_customers: number;
  active_customers: number;
  cancelled_customers: number;
  total_revenue: number;
  customers: LtvRow[];
}

const ltv = ref<LtvResponse | null>(null);
const rows = ref<LtvRow[]>([]);
const loading = ref(false);
const error = ref("");

const formatDate = (value?: string | null) => {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("pt-BR");
};

const formatDateTime = (value?: string | null) => {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
};

const formatCurrency = (value: number) =>
  Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const search = ref("");
const statusFilter = ref<"all" | "active" | "inactive">("all");
const sortBy = ref<"revenue" | "renewals" | "entered">("revenue");
const statusOptions = [
  { id: "all" as const, label: "Todos" },
  { id: "active" as const, label: "Ativos" },
  { id: "inactive" as const, label: "Inativos" }
];
const formatInt = (value: number) => new Intl.NumberFormat("pt-BR").format(Number(value || 0));
const initials = (name?: string | null) =>
  String(name || "?")
    .trim()
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase() || "")
    .join("") || "?";
const averageLtv = computed(() => (ltv.value?.total_customers ? (ltv.value.total_revenue || 0) / ltv.value.total_customers : 0));
const activeShare = computed(() =>
  ltv.value?.total_customers ? Math.round(((ltv.value.active_customers || 0) / ltv.value.total_customers) * 100) : 0
);
const averageRenewals = computed(() => {
  if (!rows.value.length) return "0";
  const avg = rows.value.reduce((sum, row) => sum + Number(row.renewals_count || 0), 0) / rows.value.length;
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(avg);
});
const maxRevenue = computed(() => Math.max(1, ...rows.value.map(row => Number(row.total_revenue || 0))));
const barWidth = (value: number) => `${Math.max(2, (Number(value || 0) / maxRevenue.value) * 100)}%`;
const visibleRows = computed(() => {
  const term = search.value.trim().toLowerCase();
  const list = rows.value.filter(row => {
    if (statusFilter.value === "active" && !row.is_active) return false;
    if (statusFilter.value === "inactive" && row.is_active) return false;
    if (!term) return true;
    return [row.name, row.email].some(value => String(value || "").toLowerCase().includes(term));
  });
  const time = (value?: string | null) => (value ? new Date(value).getTime() || 0 : 0);
  return [...list].sort((a, b) => {
    if (sortBy.value === "renewals") return (b.renewals_count || 0) - (a.renewals_count || 0);
    if (sortBy.value === "entered") return time(b.entered_at) - time(a.entered_at);
    return (b.total_revenue || 0) - (a.total_revenue || 0);
  });
});
const eventLabels: Record<string, string> = {
  purchase_approved: "Compra aprovada",
  subscription_created: "Assinatura criada",
  subscription_renewed: "Renovação",
  subscription_canceled: "Cancelamento",
  subscription_cancelled: "Cancelamento",
  refund: "Reembolso",
  chargeback: "Chargeback",
  purchase_refused: "Compra recusada",
  subscription_renewal_refused: "Renovação recusada"
};
const eventLabel = (value?: string | null) => (value ? eventLabels[value.toLowerCase()] || value : "—");
const exportCsv = () => {
  const cell = (value: unknown) => {
    let text = String(value ?? "");
    if (/^[\s]*[=+@-]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  };
  const header = ["Cliente", "E-mail", "Situação", "Entrou em", "Renovações", "Total pago", "Cancelou em", "Próxima renovação", "Último evento"];
  const lines = visibleRows.value.map(row => [
    row.name || "",
    row.email,
    row.is_active ? "Ativo" : "Inativo",
    formatDate(row.entered_at),
    row.renewals_count,
    Number(row.total_revenue || 0).toFixed(2).replace(".", ","),
    formatDate(row.cancelled_at),
    formatDate(row.next_renewal_at),
    eventLabel(row.last_event_type)
  ]);
  const blob = new Blob(["\uFEFF" + [header, ...lines].map(line => line.map(cell).join(";")).join("\r\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ltv-por-cliente.csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

const loadLtv = async () => {
  loading.value = true;
  error.value = "";
  try {
    const { data } = await api.get<LtvResponse>("/admin/ltv-customers");
    ltv.value = data;
    rows.value = data.customers || [];
  } catch (err: any) {
    ltv.value = null;
    rows.value = [];
    error.value = err?.response?.data?.detail || "Não foi possível carregar o dashboard de LTV.";
  } finally {
    loading.value = false;
  }
};

onMounted(loadLtv);
</script>
