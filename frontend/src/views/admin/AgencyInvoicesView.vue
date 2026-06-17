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
  max-width: 1380px;
}

.page-eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #8ea79d;
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
  font-size: 34px;
  line-height: 1.05;
  font-weight: 900;
  letter-spacing: -0.03em;
  color: #0f172a;
}

.page-sub {
  margin-top: 8px;
  color: #64748b;
  max-width: 760px;
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
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.search-field {
  min-width: min(100%, 380px);
  flex: 1;
}

.search-field input,
.page-size-field select {
  height: 46px;
  border: 1px solid #dbe4ef;
  border-radius: 16px;
  background: #fff;
  padding: 0 16px;
  color: #0f172a;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.search-field input:focus,
.page-size-field select:focus {
  border-color: #33c85a;
  box-shadow: 0 0 0 4px rgba(51, 200, 90, 0.12);
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #dbe4ef;
  background: #fff;
  color: #334155;
  border-radius: 999px;
  padding: 10px 14px;
  font-weight: 700;
  transition: all 0.15s ease;
}

.tab-btn.is-active {
  border-color: #33c85a;
  background: #ecfdf3;
  color: #166534;
}

.tab-badge {
  min-width: 30px;
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.15);
  font-size: 12px;
  font-weight: 800;
}

.tab-btn.is-active .tab-badge {
  background: rgba(51, 200, 90, 0.14);
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
  color: #64748b;
  font-size: 12px;
}

.pagination-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pagination-page {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.invoice-card {
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 24px;
  padding: 18px 20px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
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
  font-size: 18px;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.status-pill {
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 800;
}

.status-paid {
  background: #dcfce7;
  color: #166534;
}

.status-overdue {
  background: #fee2e2;
  color: #b91c1c;
}

.status-upcoming {
  background: #dbeafe;
  color: #1d4ed8;
}

.invoice-meta {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  color: #64748b;
  font-size: 13px;
}

.invoice-value {
  font-size: 22px;
  font-weight: 900;
  color: #0f172a;
  white-space: nowrap;
}

.invoice-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eef2f7;
}

.invoice-footnote {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #94a3b8;
}

.empty-state {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 1px dashed #dbe4ef;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.7);
  color: #64748b;
  text-align: center;
}

.empty-state-error {
  border-style: solid;
  background: #fff7f7;
  color: #b91c1c;
}

.spinner {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 4px solid #dbe4ef;
  border-top-color: #33c85a;
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
}
</style>
