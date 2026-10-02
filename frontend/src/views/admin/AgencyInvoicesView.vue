<template>
  <div class="page-wrap agency-invoices">
    <AgencyHeader>
      <template #actions>
        <button type="button" class="ai-btn-ghost" :disabled="loading" @click="loadInvoices">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7L21 8" /><path d="M21 3v5h-5" /></svg>
          {{ loading ? "Atualizando..." : "Atualizar" }}
        </button>
      </template>
    </AgencyHeader>

    <div class="ai-stats">
      <article v-for="item in invoiceSummaries" :key="item.id" class="ai-stat">
        <span class="ai-stat-icon" :class="`is-${item.id}`" aria-hidden="true">
          <svg v-if="item.id === 'upcoming'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
          <svg v-else-if="item.id === 'overdue'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
        </span>
        <div>
          <p class="ai-stat-k">{{ item.label }} · {{ item.count }}</p>
          <p class="ai-stat-v">{{ formatCurrency(item.value) }}</p>
        </div>
      </article>
    </div>

    <div class="ai-filters">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="ai-filter"
        :class="{ on: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
        <span>{{ tab.id === "all" ? invoices.length : counts[tab.id] ?? 0 }}</span>
      </button>
    </div>

    <div v-if="loading" class="ai-empty">
      <div class="spinner"></div>
      <p>Carregando faturas...</p>
    </div>

    <div v-else-if="errorMessage" class="ai-empty">
      <p>{{ errorMessage }}</p>
      <button type="button" class="ai-btn-ghost" @click="loadInvoices">Tentar novamente</button>
    </div>

    <section v-else-if="pagedInvoices.length" class="ai-table-card">
      <table class="ai-table">
        <thead>
          <tr>
            <th>Fatura</th>
            <th>Forma</th>
            <th>Vencimento</th>
            <th>Pago em</th>
            <th class="text-right">Valor</th>
            <th>Situação</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="invoice in pagedInvoices" :key="invoice.id">
            <td>
              <div class="ai-name">
                <span class="ai-doc" :class="`is-${invoice.bucket}`" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h14v18l-3-2-2 2-2-2-2 2-2-2-3 2z" /><path d="M9 8h6M9 12h6M9 16h4" /></svg>
                </span>
                <span>{{ invoice.description || "Cobrança sem título" }}</span>
              </div>
            </td>
            <td>{{ billingTypeLabel(invoice.billing_type) }}</td>
            <td>{{ formatDate(invoice.due_date) }}</td>
            <td class="ai-muted">{{ invoice.payment_date ? formatDate(invoice.payment_date) : "—" }}</td>
            <td class="ai-value">{{ formatCurrency(invoice.value) }}</td>
            <td><span class="ai-pill" :class="statusClass(invoice.bucket)">{{ statusLabel(invoice.bucket) }}</span></td>
            <td class="text-right">
              <a
                v-if="actionUrl(invoice)"
                :href="actionUrl(invoice)"
                target="_blank"
                rel="noopener"
                :class="invoice.is_paid ? 'ai-btn-ghost ai-btn-sm' : 'ai-btn-primary ai-btn-sm'"
              >
                <svg v-if="invoice.is_paid" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12M6 10l6 6 6-6M5 20h14" /></svg>
                {{ invoice.is_paid ? "Recibo" : "Pagar" }}
              </a>
              <span v-else class="ai-muted">Sem link</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="totalPages > 1" class="ai-pagination">
        <span>Mostrando {{ paginationStart }}-{{ paginationEnd }} de {{ filteredInvoices.length }} faturas</span>
        <div>
          <button type="button" class="ai-btn-ghost ai-btn-sm" :disabled="currentPage === 1" @click="currentPage -= 1">Anterior</button>
          <span>Página {{ currentPage }} de {{ totalPages }}</span>
          <button type="button" class="ai-btn-ghost ai-btn-sm" :disabled="currentPage === totalPages" @click="currentPage += 1">Próxima</button>
        </div>
      </div>
    </section>

    <div v-else class="ai-empty">
      <p>Nenhuma fatura encontrada nesta categoria.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import api from "../../services/api";
import AgencyHeader from "../../components/admin/agency/AgencyHeader.vue";
import { agencyCounts } from "../../composables/useAgencyCounts";
import { createAdminLocalizer } from "../../utils/adminI18n";

type InvoiceBucket = "paid" | "overdue" | "upcoming";

interface BillingInvoice {
  id: string;
  customer_id?: string | null;
  subscription_id?: string | null;
  status: string;
  billing_type?: string | null;
  description?: string | null;
  value: number;
  due_date?: string | null;
  payment_date?: string | null;
  invoice_url?: string | null;
  bank_slip_url?: string | null;
  receipt_url?: string | null;
  pay_url?: string | null;
  download_url?: string | null;
  is_paid: boolean;
  bucket: InvoiceBucket;
}

interface BillingInvoicesResponse {
  items: BillingInvoice[];
  total: number;
  counts: Record<InvoiceBucket, number>;
}

const t = createAdminLocalizer();

const viewCopy = {
  upcoming: t({ pt: "A vencer", es: "Por vencer" }),
  overdue: t({ pt: "Vencidas", es: "Vencidas" }),
  paid: t({ pt: "Pagas", es: "Pagadas" })
};

const tabs: Array<{ id: InvoiceBucket | "all"; label: string }> = [
  { id: "all", label: t({ pt: "Todas", es: "Todas" }) },
  { id: "upcoming", label: viewCopy.upcoming },
  { id: "overdue", label: viewCopy.overdue },
  { id: "paid", label: viewCopy.paid }
];

const loading = ref(false);
const errorMessage = ref("");
const invoices = ref<BillingInvoice[]>([]);
const counts = ref<Record<InvoiceBucket, number>>({ paid: 0, overdue: 0, upcoming: 0 });
const activeTab = ref<InvoiceBucket | "all">("all");
const searchQuery = ref("");
const currentPage = ref(1);
const pageSize = ref(20);

const invoiceSummaries = computed(() =>
  ([
    { id: "upcoming", label: viewCopy.upcoming, helper: "Cobranças programadas" },
    { id: "overdue", label: viewCopy.overdue, helper: "Cobranças que precisam de atenção" },
    { id: "paid", label: viewCopy.paid, helper: "Cobranças já quitadas" }
  ] as const).map(item => ({
    ...item,
    count: counts.value[item.id] ?? 0,
    value: invoices.value
      .filter(invoice => invoice.bucket === item.id)
      .reduce((total, invoice) => total + (Number(invoice.value) || 0), 0)
  }))
);

const normalizeText = (value: unknown) =>
  String(value ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

const filteredInvoices = computed(() => {
  const query = normalizeText(searchQuery.value);
  return invoices.value.filter(item => {
    if (activeTab.value !== "all" && item.bucket !== activeTab.value) return false;
    if (!query) return true;
    const haystack = [
      item.id,
      item.description,
      item.billing_type,
      item.status,
      item.value.toFixed(2),
      item.due_date,
      item.payment_date
    ]
      .map(normalizeText)
      .join(" ");
    return haystack.includes(query);
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredInvoices.value.length / Math.max(1, pageSize.value))));
const pagedInvoices = computed(() => {
  const start = (currentPage.value - 1) * Math.max(1, pageSize.value);
  return filteredInvoices.value.slice(start, start + Math.max(1, pageSize.value));
});
const paginationStart = computed(() => (filteredInvoices.value.length ? (currentPage.value - 1) * Math.max(1, pageSize.value) + 1 : 0));
const paginationEnd = computed(() =>
  filteredInvoices.value.length ? Math.min(currentPage.value * Math.max(1, pageSize.value), filteredInvoices.value.length) : 0
);

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(Number.isFinite(value) ? value : 0);

const formatDate = (value?: string | null) => {
  if (!value) return "--";
  const parsed = value.length === 10 ? new Date(`${value}T00:00:00`) : new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString("pt-BR");
};

const billingTypeLabel = (value?: string | null) => {
  const raw = String(value || "").trim().toUpperCase();
  if (!raw) return "Forma não informada";
  if (raw === "BOLETO") return "Boleto";
  if (raw === "CREDIT_CARD") return "Cartão";
  if (raw === "PIX") return "PIX";
  return raw.replaceAll("_", " ");
};

const statusLabel = (bucket: InvoiceBucket) => {
  if (bucket === "paid") return "Paga";
  if (bucket === "overdue") return "Vencida";
  return "A vencer";
};

const statusClass = (bucket: InvoiceBucket) => {
  if (bucket === "paid") return "status-paid";
  if (bucket === "overdue") return "status-overdue";
  return "status-upcoming";
};

const actionUrl = (invoice: BillingInvoice) => (invoice.is_paid ? invoice.download_url || invoice.invoice_url : invoice.pay_url || invoice.invoice_url);

const loadInvoices = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await api.get<BillingInvoicesResponse>("/billing/invoices");
    invoices.value = Array.isArray(data.items) ? data.items : [];
    counts.value = {
      paid: data.counts?.paid ?? 0,
      overdue: data.counts?.overdue ?? 0,
      upcoming: data.counts?.upcoming ?? 0
    };
    agencyCounts.invoices = (counts.value.upcoming || 0) + (counts.value.overdue || 0);
    currentPage.value = 1;
  } catch (err) {
    console.error("Erro ao carregar faturas", err);
    errorMessage.value = "Não foi possível carregar as faturas do Asaas.";
    invoices.value = [];
    counts.value = { paid: 0, overdue: 0, upcoming: 0 };
  } finally {
    loading.value = false;
  }
};

watch([activeTab, searchQuery, pageSize], () => {
  currentPage.value = 1;
});

watch(filteredInvoices, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value;
  }
});

onMounted(() => {
  void loadInvoices();
});
</script>

<style scoped>
.page-wrap {
  padding: 28px 32px 64px;
  width: 100%;
  max-width: 1440px;
  color: var(--foreground);
}

.page-eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted-foreground);
  margin-bottom: 4px;
}

.page-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 26px;
  line-height: 1.2;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: var(--foreground);
}

.page-sub {
  margin-top: 5px;
  color: var(--muted-foreground);
  max-width: 760px;
  font-size: 13px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 650;
  line-height: 1.2;
  transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.btn-p {
  background: var(--primary);
  color: var(--primary-foreground);
  box-shadow: var(--shadow-soft);
}

.btn-p:hover:not(:disabled) {
  background: var(--brand-dark);
  transform: translateY(-1px);
}

.btn-o {
  border-color: var(--border);
  background: var(--card);
  color: var(--foreground);
}

.btn-o:hover:not(:disabled) {
  background: var(--accent);
}

.btn-sm {
  padding: 7px 12px;
  font-size: 12px;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.invoice-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.summary-card {
  position: relative;
  overflow: hidden;
  display: flex;
  min-height: 132px;
  flex-direction: column;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--card);
  padding: 18px;
  box-shadow: var(--shadow-soft);
}

.summary-card::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--summary-color);
  content: "";
}

.summary-card--upcoming { --summary-color: var(--status-info-foreground); }
.summary-card--overdue { --summary-color: var(--status-danger-foreground); }
.summary-card--paid { --summary-color: var(--status-success-foreground); }

.summary-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.summary-label {
  color: var(--muted-foreground);
  font-size: 11px;
  font-weight: 750;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-count {
  border: 1px solid color-mix(in srgb, var(--summary-color) 24%, var(--border));
  border-radius: 999px;
  background: color-mix(in srgb, var(--summary-color) 9%, var(--card));
  color: var(--summary-color);
  padding: 3px 9px;
  font-size: 11px;
  font-weight: 750;
}

.summary-value {
  margin-top: 12px;
  color: var(--foreground);
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 650;
}

.summary-helper {
  margin-top: 3px;
  color: var(--muted-foreground);
  font-size: 12px;
}

.tabs-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
}

.toolbar-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.search-field,
.page-size-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--muted-foreground);
  font-size: 12px;
  font-weight: 700;
}

.search-field {
  min-width: min(100%, 380px);
  flex: 1;
}

.search-field input,
.page-size-field select {
  height: 42px;
  border: 1px solid var(--input);
  border-radius: var(--radius-lg);
  background: var(--background);
  padding: 0 16px;
  color: var(--foreground);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.search-field input:focus,
.page-size-field select:focus {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 18%, transparent);
}

.search-field input::placeholder {
  color: var(--muted-foreground);
}

.page-size-field option {
  background: var(--popover);
  color: var(--popover-foreground);
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--muted-foreground);
  border-radius: var(--radius-lg);
  padding: 8px 12px;
  font-weight: 700;
  transition: all 0.15s ease;
}

.tab-btn.is-active {
  border-color: color-mix(in srgb, var(--primary) 35%, var(--border));
  background: color-mix(in srgb, var(--primary) 10%, var(--card));
  color: var(--primary);
}

.tab-badge {
  min-width: 30px;
  padding: 3px 9px;
  border-radius: 999px;
  background: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.tab-btn.is-active .tab-badge {
  background: color-mix(in srgb, var(--primary) 15%, var(--card));
}

.invoice-list {
  display: grid;
  gap: 12px;
}

.pagination-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 6px;
}

.pagination-info {
  color: var(--muted-foreground);
  font-size: 12px;
}

.pagination-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pagination-page {
  color: var(--muted-foreground);
  font-size: 12px;
  font-weight: 700;
}

.invoice-card {
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--card-foreground);
  border-radius: var(--radius-xl);
  padding: 18px 20px;
  box-shadow: var(--shadow-soft);
  transition: border-color 0.15s ease, transform 0.15s ease;
}

.invoice-card:hover {
  border-color: color-mix(in srgb, var(--foreground) 14%, var(--border));
  transform: translateY(-1px);
}

.invoice-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.invoice-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.invoice-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: var(--foreground);
}

.status-pill {
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 800;
}

.status-paid {
  background: var(--status-success);
  color: var(--status-success-foreground);
}

.status-overdue {
  background: var(--status-danger);
  color: var(--status-danger-foreground);
}

.status-upcoming {
  background: var(--status-info);
  color: var(--status-info-foreground);
}

.invoice-meta {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--muted-foreground);
  font-size: 13px;
}

.invoice-value {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 650;
  color: var(--foreground);
  white-space: nowrap;
}

.invoice-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid color-mix(in srgb, var(--border) 40%, transparent);
}

.invoice-footnote {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--muted-foreground);
}

.empty-state {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-xl);
  background: color-mix(in srgb, var(--card) 80%, transparent);
  color: var(--muted-foreground);
  text-align: center;
}

.empty-state-error {
  border-style: solid;
  border-color: color-mix(in srgb, var(--destructive) 25%, var(--border));
  background: color-mix(in srgb, var(--destructive) 7%, var(--card));
  color: var(--destructive);
}

.spinner {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 4px solid var(--border);
  border-top-color: var(--primary);
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .page-wrap {
    padding: 20px 16px 40px;
  }

  .page-topbar,
  .invoice-main,
  .invoice-footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar-row,
  .pagination-row {
    align-items: stretch;
  }

  .pagination-actions {
    width: 100%;
    justify-content: space-between;
  }

  .invoice-value {
    white-space: normal;
  }

  .invoice-summary-grid {
    grid-template-columns: 1fr;
  }
}

/* Redesign: faturas */
.agency-invoices { display: flex; flex-direction: column; gap: 16px; }
.ai-btn-ghost, .ai-btn-primary { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 40px; padding: 0 18px; border-radius: 999px; font-size: 13.5px; font-weight: 600; }
.ai-btn-ghost { background: var(--card); color: var(--foreground); box-shadow: var(--shadow-card); }
.ai-btn-ghost:hover:not(:disabled) { background: var(--accent); }
.ai-btn-primary { background: var(--primary); color: var(--primary-foreground); }
.ai-btn-primary:hover { background: color-mix(in srgb, var(--primary) 88%, black); }
.ai-btn-ghost svg, .ai-btn-primary svg { width: 15px; height: 15px; }
.ai-btn-ghost:disabled { opacity: 0.55; }
.ai-btn-sm { height: 32px; padding: 0 14px; font-size: 12.5px; }
.ai-table .ai-btn-ghost { background: var(--muted); box-shadow: none; }
.ai-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.ai-stat { display: flex; align-items: center; gap: 12px; border-radius: 20px; background: var(--card); padding: 14px 16px; box-shadow: var(--shadow-card); }
.ai-stat-icon { display: grid; place-items: center; width: 40px; height: 40px; flex-shrink: 0; border-radius: 999px; }
.ai-stat-icon svg { width: 18px; height: 18px; }
.ai-stat-icon.is-upcoming { background: var(--status-info); color: var(--status-info-foreground); }
.ai-stat-icon.is-overdue { background: var(--muted); color: var(--muted-foreground); }
.ai-stat-icon.is-paid { background: var(--status-success); color: var(--status-success-foreground); }
.ai-stat-k { font-size: 12.5px; color: var(--muted-foreground); }
.ai-stat-v { font-family: var(--font-display); font-size: 20px; line-height: 26px; font-weight: 600; color: var(--foreground); font-variant-numeric: tabular-nums; }
.ai-filters { display: flex; flex-wrap: wrap; gap: 4px; }
.ai-filter { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px; border-radius: 999px; font-size: 13px; font-weight: 600; color: var(--muted-foreground); }
.ai-filter span { border-radius: 999px; background: var(--muted); padding: 0 7px; font-size: 11px; }
.ai-filter.on { background: var(--card); color: var(--foreground); box-shadow: var(--shadow-card); }
.ai-filter.on span { background: var(--accent); color: var(--accent-foreground); }
.ai-table-card { overflow-x: auto; border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.ai-table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.ai-table th { border-bottom: 1px solid var(--border); padding: 12px 16px; text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted-foreground); }
.ai-table th.text-right, .ai-table td.text-right { text-align: right; }
.ai-table td { border-bottom: 1px solid var(--border); padding: 12px 16px; color: var(--foreground); white-space: nowrap; }
.ai-table tbody tr:last-child td { border-bottom: 0; }
.ai-name { display: flex; align-items: center; gap: 12px; font-weight: 600; }
.ai-doc { display: grid; place-items: center; width: 34px; height: 34px; flex-shrink: 0; border-radius: 999px; background: var(--status-success); color: var(--status-success-foreground); }
.ai-doc svg { width: 16px; height: 16px; }
.ai-doc.is-upcoming { background: var(--status-info); color: var(--status-info-foreground); }
.ai-doc.is-overdue { background: var(--status-danger); color: var(--status-danger-foreground); }
.ai-muted { color: var(--muted-foreground) !important; }
.ai-value { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
.ai-pill { border-radius: 999px; padding: 2px 9px; font-size: 11.5px; font-weight: 600; }
.ai-pill.status-paid { background: var(--status-success); color: var(--status-success-foreground); }
.ai-pill.status-upcoming { background: var(--status-info); color: var(--status-info-foreground); }
.ai-pill.status-overdue { background: var(--status-danger); color: var(--status-danger-foreground); }
.ai-pagination { display: flex; align-items: center; justify-content: space-between; gap: 12px; border-top: 1px solid var(--border); padding: 12px 16px; font-size: 12.5px; color: var(--muted-foreground); }
.ai-pagination > div { display: flex; align-items: center; gap: 8px; }
.ai-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; border-radius: 20px; background: var(--card); padding: 40px 16px; text-align: center; font-size: 14px; color: var(--muted-foreground); box-shadow: var(--shadow-card); }
@media (max-width: 900px) { .ai-stats { grid-template-columns: 1fr; } }
</style>
