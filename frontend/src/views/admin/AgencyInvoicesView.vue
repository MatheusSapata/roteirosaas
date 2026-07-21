<template>
  <div class="page-wrap agency-invoices">
    <div class="page-eyebrow">Agência</div>
    <div class="page-topbar">
      <div>
        <h1 class="page-title">Faturas</h1>
        <p class="page-sub">Veja as cobranças pagas, vencidas e a vencer. Você pode abrir as pendentes ou baixar as já quitadas.</p>
      </div>
      <button type="button" class="btn btn-p" :disabled="loading" @click="loadInvoices">
        {{ loading ? "Atualizando..." : "Atualizar" }}
      </button>
    </div>

    <div class="invoice-summary-grid">
      <article
        v-for="item in invoiceSummaries"
        :key="item.id"
        class="summary-card"
        :class="`summary-card--${item.id}`"
      >
        <div class="summary-top">
          <span class="summary-label">{{ item.label }}</span>
          <span class="summary-count">{{ item.count }}</span>
        </div>
        <strong class="summary-value">{{ formatCurrency(item.value) }}</strong>
        <span class="summary-helper">{{ item.helper }}</span>
      </article>
    </div>

    <div class="tabs-row">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="tab-btn"
        :class="activeTab === tab.id ? 'is-active' : ''"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
        <span class="tab-badge">{{ counts[tab.id] ?? 0 }}</span>
      </button>
    </div>

    <div class="toolbar-row">
      <label class="search-field">
        <span>Buscar</span>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Buscar por título, ID ou valor"
        />
      </label>

      <div class="page-size-field">
        <span>Por página</span>
        <select v-model.number="pageSize">
          <option :value="5">5</option>
          <option :value="10">10</option>
          <option :value="20">20</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="empty-state">
      <div class="spinner"></div>
      <p>Carregando faturas...</p>
    </div>

    <div v-else-if="errorMessage" class="empty-state empty-state-error">
      <p>{{ errorMessage }}</p>
      <button type="button" class="btn btn-o btn-sm" @click="loadInvoices">Tentar novamente</button>
    </div>

    <div v-else-if="pagedInvoices.length" class="invoice-list">
      <article v-for="invoice in pagedInvoices" :key="invoice.id" class="invoice-card">
        <div class="invoice-main">
          <div class="invoice-text">
            <div class="invoice-title-row">
              <h2 class="invoice-title">{{ invoice.description || "Cobrança sem título" }}</h2>
              <span class="status-pill" :class="statusClass(invoice.bucket)">{{ statusLabel(invoice.bucket) }}</span>
            </div>
            <div class="invoice-meta">
              <span>{{ billingTypeLabel(invoice.billing_type) }}</span>
              <span>•</span>
              <span>Vencimento: {{ formatDate(invoice.due_date) }}</span>
              <span v-if="invoice.payment_date">•</span>
              <span v-if="invoice.payment_date">Pago em: {{ formatDate(invoice.payment_date) }}</span>
            </div>
          </div>
          <div class="invoice-value">
            {{ formatCurrency(invoice.value) }}
          </div>
        </div>

        <div class="invoice-footer">
          <div class="invoice-footnote">
            <span>ID Asaas: {{ invoice.id }}</span>
            <span v-if="invoice.is_paid && invoice.receipt_url">Recibo disponível</span>
          </div>
          <a
            v-if="actionUrl(invoice)"
            :href="actionUrl(invoice)"
            target="_blank"
            rel="noopener"
            class="btn btn-p btn-sm"
          >
            {{ invoice.is_paid ? "Baixar" : "Abrir / pagar" }}
          </a>
          <button v-else type="button" class="btn btn-o btn-sm" disabled>
            Sem link disponível
          </button>
        </div>
      </article>

      <div class="pagination-row">
        <span class="pagination-info">
          Mostrando {{ paginationStart }}-{{ paginationEnd }} de {{ filteredInvoices.length }} faturas
        </span>
        <div class="pagination-actions">
          <button type="button" class="btn btn-o btn-sm" :disabled="currentPage === 1" @click="currentPage -= 1">
            Anterior
          </button>
          <span class="pagination-page">Página {{ currentPage }} de {{ totalPages }}</span>
          <button type="button" class="btn btn-o btn-sm" :disabled="currentPage === totalPages" @click="currentPage += 1">
            Próxima
          </button>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>Nenhuma fatura encontrada nesta categoria.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import api from "../../services/api";
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

const tabs: Array<{ id: InvoiceBucket; label: string }> = [
  { id: "upcoming", label: viewCopy.upcoming },
  { id: "overdue", label: viewCopy.overdue },
  { id: "paid", label: viewCopy.paid }
];

const loading = ref(false);
const errorMessage = ref("");
const invoices = ref<BillingInvoice[]>([]);
const counts = ref<Record<InvoiceBucket, number>>({ paid: 0, overdue: 0, upcoming: 0 });
const activeTab = ref<InvoiceBucket>("upcoming");
const searchQuery = ref("");
const currentPage = ref(1);
const pageSize = ref(10);

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
    if (item.bucket !== activeTab.value) return false;
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
    if (!filteredInvoices.value.length && invoices.value.length) {
      activeTab.value = invoices.value[0].bucket;
    }
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
</style>
