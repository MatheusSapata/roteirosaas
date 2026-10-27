<template>
  <div class="page-wrap agency-invoices">
    <AgencyHeader>
      <template #actions>
        <button type="button" class="ai-btn-ghost" :disabled="loading" @click="loadInvoices">
          <RotateCwIcon aria-hidden="true" />
          {{ loading ? "Atualizando..." : "Atualizar" }}
        </button>
      </template>
    </AgencyHeader>

    <div v-if="watcher.phase.value === 'checking'" class="ai-notice is-info" role="status">
      <span class="ai-notice-icon" aria-hidden="true"><span class="ai-spinner"></span></span>
      <div class="ai-notice-text">
        <p class="ai-notice-title">Conferindo o pagamento da fatura{{ watchedMonthLabel }}</p>
        <p>
          Pix costuma levar menos de 1 minuto; boleto, até 3 dias úteis. A tela confere sozinha a cada 15 segundos.
          <span v-if="watcher.hint.value">{{ watcher.hint.value }}</span>
        </p>
      </div>
      <button type="button" class="ai-btn-ghost ai-btn-sm" :disabled="watcher.checking.value" @click="watcher.checkNow()">
        {{ watcher.checking.value ? "Conferindo..." : "Verificar agora" }}
      </button>
    </div>
    <div v-else-if="watcher.phase.value === 'paid'" class="ai-notice is-ok" role="status">
      <span class="ai-notice-icon" aria-hidden="true"><CheckIcon aria-hidden="true" /></span>
      <div class="ai-notice-text">
        <p class="ai-notice-title">Pagamento recebido.{{ accessUntilSentence }}</p>
        <p>Suas páginas voltaram ao ar. O recibo já está na lista abaixo.</p>
      </div>
    </div>
    <div v-else-if="watcher.phase.value === 'gave-up'" class="ai-notice is-warn" role="status">
      <div class="ai-notice-text">
        <p class="ai-notice-title">Ainda não recebemos o pagamento</p>
        <p>Se você já pagou, aguarde alguns minutos e confira de novo. Boleto pode levar até 3 dias úteis.</p>
      </div>
      <button type="button" class="ai-btn-ghost ai-btn-sm" @click="verifyPayment">Verificar pagamento</button>
    </div>

    <section v-if="account" class="pf-card" aria-label="Situação da assinatura">
      <div class="pf-plan">
        <span class="pf-plan-icon" aria-hidden="true"><StarIcon aria-hidden="true" /></span>
        <div class="pf-plan-main">
          <p class="pf-plan-k">Seu plano</p>
          <p class="pf-plan-v">{{ planName }}</p>
        </div>
        <span class="pf-status" :class="statusTone">{{ statusLabel }}</span>
        <button v-if="unlockingInvoice" type="button" class="pf-plan-btn" @click="payInvoice(unlockingInvoice)">
          Pagar {{ formatBRL(unlockingInvoice.value) }}
        </button>
        <button v-else-if="account.status === 'inactive' || account.status === 'cancelling'" type="button" class="pf-plan-btn" @click="openRenewal()">
          Renovar assinatura
        </button>
      </div>

      <div class="pf-facts">
        <div v-if="unlockingInvoice">
          <p>Fatura em aberto</p>
          <b>{{ capitalize(monthName(unlockingInvoice.due_date)) }} · venceu em {{ formatDayMonth(unlockingInvoice.due_date) }}</b>
        </div>
        <div v-else>
          <p>Próxima renovação</p>
          <b>{{ account.next_charge ? formatDate(account.next_charge.due_date) : "—" }}</b>
        </div>
        <div>
          <p>{{ account.status === "active" ? "Edição liberada até" : "Acesso até" }}</p>
          <b>{{ account.access_until ? formatDate(account.access_until) : "—" }}</b>
        </div>
        <div class="pf-fact-pay">
          <div class="min-w-0">
            <p>Forma de pagamento</p>
            <b>
              {{ paymentLabel }}
              <span v-if="pixDisabled" class="tag danger">Desativado</span>
            </b>
          </div>
          <button v-if="pixDisabled" type="button" class="pf-link" @click="openRenewal('pix')">Reativar</button>
        </div>
      </div>

      <p v-if="unlockingInvoice" class="pf-note">
        Pague a fatura em aberto e o acesso volta sozinho, sem passar pelo checkout. Já pagou?
        <button type="button" class="pf-link" :disabled="watcher.checking.value" @click="verifyPayment">Verificar pagamento</button>
      </p>
      <div v-if="pixDisabled && !unlockingInvoice" class="ai-notice is-warn ai-notice-inline">
        <div class="ai-notice-text">
          <p class="ai-notice-title">Ative o Pix Automático para a próxima cobrança</p>
          <p>
            A autorização anterior foi encerrada. Sem ela, a próxima fatura chega por e-mail e precisa ser paga na mão.
            Reativar mantém o mesmo plano e o mesmo valor.
          </p>
        </div>
        <button type="button" class="ai-btn-primary ai-btn-sm" @click="openRenewal('pix')">Reativar Pix Automático</button>
      </div>
    </section>

    <div class="ai-stats">
      <article v-for="item in invoiceSummaries" :key="item.id" class="ai-stat">
        <span class="ai-stat-icon" :class="`is-${item.id}`" aria-hidden="true">
          <ClockIcon v-if="item.id === 'upcoming'" aria-hidden="true" />
          <TriangleAlertIcon v-else-if="item.id === 'overdue'" aria-hidden="true" />
          <CheckIcon v-else aria-hidden="true" />
        </span>
        <div>
          <p class="ai-stat-k">{{ item.label }}</p>
          <p class="ai-stat-v">{{ item.value }}</p>
          <p class="ai-stat-h">{{ item.helper }}</p>
        </div>
      </article>
    </div>

    <div class="ai-filters" role="tablist" aria-label="Filtrar faturas">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        role="tab"
        :aria-selected="activeTab === tab.id"
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

    <section v-else-if="pagedInvoices.length" class="ai-table-card" aria-label="Faturas">
      <table class="ai-table">
        <thead>
          <tr>
            <th scope="col">Fatura</th>
            <th scope="col">Forma</th>
            <th scope="col">Período</th>
            <th scope="col">Vencimento</th>
            <th scope="col">Pago em</th>
            <th scope="col" class="text-right">Valor</th>
            <th scope="col">Situação</th>
            <th scope="col"><span class="sr-only">Ação</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="invoice in pagedInvoices" :key="invoice.id">
            <td>
              <div class="ai-name">
                <span class="ai-doc" :class="`is-${invoice.bucket}`" aria-hidden="true">
                  <ReceiptIcon aria-hidden="true" />
                </span>
                <span>
                  {{ invoice.description || "Cobrança sem título" }}
                  <small>{{ invoice.id }}</small>
                </span>
              </div>
            </td>
            <td>{{ billingTypeLabel(invoice.billing_type) }}</td>
            <td :class="{ 'ai-muted': invoice.bucket === 'replaced' }">{{ periodLabel(invoice) }}</td>
            <td>{{ formatDate(invoice.due_date) }}</td>
            <td class="ai-muted">{{ invoice.payment_date ? formatDate(invoice.payment_date) : "—" }}</td>
            <td class="ai-value"><span :class="{ 'ai-strike': invoice.bucket === 'replaced' }">{{ formatBRL(invoice.value) }}</span></td>
            <td><span class="ai-pill" :class="statusClass(invoice.bucket)">{{ bucketLabel(invoice.bucket) }}</span></td>
            <td class="text-right">
              <span v-if="invoice.bucket === 'replaced'" class="ai-muted ai-small">Cancelada no Asaas</span>
              <template v-else>
                <button
                  v-if="!invoice.is_paid && actionUrl(invoice)"
                  type="button"
                  class="ai-btn-primary ai-btn-sm"
                  @click="payInvoice(invoice)"
                >
                  Pagar
                </button>
                <a
                  v-else-if="invoice.is_paid && actionUrl(invoice)"
                  :href="actionUrl(invoice)"
                  target="_blank"
                  rel="noopener"
                  class="ai-btn-ghost ai-btn-sm"
                >
                  <DownloadIcon aria-hidden="true" />
                  Recibo
                </a>
                <span v-else class="ai-muted">Sem link</span>
              </template>
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
      <p v-if="counts.replaced" class="ai-foot">
        Substituída: a cobrança deste período foi trocada por outra (paga ou mais nova) e cancelada no Asaas. Não é dívida e não bloqueia a conta.
      </p>
    </section>

    <div v-else class="ai-empty">
      <p>Nenhuma fatura encontrada nesta categoria.</p>
    </div>

    <RenewalModal
      :open="renewalOpen"
      :invoice="unlockingInvoice"
      :initial-method="renewalMethod"
      @close="renewalOpen = false"
      @paid="onRenewed"
    />
  </div>
</template>

<script setup lang="ts">
import {
  CheckIcon,
  ClockIcon,
  DownloadIcon,
  ReceiptIcon,
  RotateCwIcon,
  StarIcon,
  TriangleAlertIcon
} from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AgencyHeader from "../../components/admin/agency/AgencyHeader.vue";
import RenewalModal from "../../components/admin/billing/RenewalModal.vue";
import { agencyCounts } from "../../composables/useAgencyCounts";
import { useInvoicePaymentWatch } from "../../composables/useInvoicePaymentWatch";
import {
  formatBRL,
  formatInvoiceDate as formatDate,
  formatInvoiceDayMonth as formatDayMonth,
  getBillingInvoices,
  invoiceMonthName as monthName,
  type BillingAccount,
  type BillingInvoice,
  type InvoiceBucket
} from "../../services/billing";
import { useAuthStore } from "../../store/useAuthStore";
import { getCustomerPlanLabel } from "../../utils/planLabels";
import { cycleLabel } from "../../utils/billingCycle";

const route = useRoute();
const auth = useAuthStore();

const tabs: Array<{ id: InvoiceBucket | "all"; label: string }> = [
  { id: "all", label: "Todas" },
  { id: "overdue", label: "Em aberto" },
  { id: "upcoming", label: "A vencer" },
  { id: "paid", label: "Pagas" },
  { id: "replaced", label: "Substituídas" }
];

const loading = ref(false);
const errorMessage = ref("");
const invoices = ref<BillingInvoice[]>([]);
const account = ref<BillingAccount | null>(null);
const counts = ref<Record<InvoiceBucket, number>>({ paid: 0, overdue: 0, upcoming: 0, replaced: 0 });
const activeTab = ref<InvoiceBucket | "all">("all");
const currentPage = ref(1);
const pageSize = ref(20);
const renewalOpen = ref(false);
const renewalMethod = ref<"pix" | "card">("pix");

const capitalize = (value: string) => (value ? value.charAt(0).toUpperCase() + value.slice(1) : value);

const unlockingInvoice = computed(
  () => invoices.value.find(invoice => invoice.id === account.value?.unlocking_invoice_id) ?? null
);

// A fatura que a pessoa mandou conferir (ela sai da lista de abertas quando o pagamento é reconhecido).
const watcher = useInvoicePaymentWatch(async () => {
  await loadInvoices(false);
});
const watchedMonthLabel = computed(() => {
  const invoice = invoices.value.find(item => item.id === watcher.invoiceId.value);
  const month = monthName(invoice?.due_date);
  return month ? ` de ${month}` : "";
});
const accessUntilSentence = computed(() =>
  auth.user?.subscription_valid_until ? ` Edição liberada até ${formatDate(auth.user.subscription_valid_until)}` : ""
);

const planName = computed(() => {
  const offer = account.value?.renewal_offer;
  const label = getCustomerPlanLabel(offer?.plan || auth.user?.plan);
  const cycle = offer ? cycleLabel(offer.billing_cycle) : "";
  return cycle ? `${label} · ${cycle}` : label;
});
const statusLabel = computed(() => {
  switch (account.value?.status) {
    case "active":
      return "Ativo";
    case "past_due":
      return "Pagamento pendente";
    case "blocked":
      return "Bloqueado";
    case "cancelling":
      return "Cancelando";
    default:
      return "Encerrado";
  }
});
const statusTone = computed(() => {
  if (account.value?.status === "active") return "ok";
  if (account.value?.status === "past_due" || account.value?.status === "cancelling") return "warn";
  return "off";
});
const pixDisabled = computed(() => {
  const status = account.value?.pix_automatic_status;
  return Boolean(status && status !== "ACTIVE");
});
const paymentLabel = computed(() => {
  if (account.value?.pix_automatic_status) return "Pix Automático";
  const latestPaid = invoices.value.find(invoice => invoice.is_paid);
  return billingTypeLabel(latestPaid?.billing_type);
});

const invoiceSummaries = computed(() => {
  const paid = invoices.value.filter(invoice => invoice.bucket === "paid");
  const next = account.value?.next_charge;
  return [
    {
      id: "overdue",
      label: `Em aberto · ${account.value?.open_count ?? counts.value.overdue ?? 0}`,
      value: formatBRL(account.value?.open_amount ?? 0),
      helper: unlockingInvoice.value ? "O que libera o acesso" : "Nada vencido"
    },
    {
      id: "upcoming",
      label: "Próxima cobrança",
      value: next ? formatDate(next.due_date) : "—",
      helper: next ? `${formatBRL(next.amount)} · mesmo valor de hoje` : "Nenhuma cobrança programada"
    },
    {
      id: "paid",
      label: `Pagas · ${counts.value.paid ?? 0}`,
      value: formatBRL(paid.reduce((total, invoice) => total + (Number(invoice.value) || 0), 0)),
      helper: "Cobranças já quitadas"
    }
  ] as const;
});

const filteredInvoices = computed(() =>
  invoices.value.filter(item => activeTab.value === "all" || item.bucket === activeTab.value)
);

const totalPages = computed(() => Math.max(1, Math.ceil(filteredInvoices.value.length / Math.max(1, pageSize.value))));
const pagedInvoices = computed(() => {
  const start = (currentPage.value - 1) * Math.max(1, pageSize.value);
  return filteredInvoices.value.slice(start, start + Math.max(1, pageSize.value));
});
const paginationStart = computed(() => (filteredInvoices.value.length ? (currentPage.value - 1) * Math.max(1, pageSize.value) + 1 : 0));
const paginationEnd = computed(() =>
  filteredInvoices.value.length ? Math.min(currentPage.value * Math.max(1, pageSize.value), filteredInvoices.value.length) : 0
);

const billingTypeLabel = (value?: string | null) => {
  const raw = String(value || "").trim().toUpperCase();
  if (!raw) return "Forma não informada";
  if (raw === "BOLETO") return "Boleto";
  if (raw === "CREDIT_CARD") return "Cartão";
  if (raw === "PIX") return "PIX";
  return raw.replaceAll("_", " ");
};

const bucketLabel = (bucket: InvoiceBucket) => {
  if (bucket === "paid") return "Paga";
  if (bucket === "overdue") return "Vencida";
  if (bucket === "replaced") return "Substituída";
  return "A vencer";
};

const statusClass = (bucket: InvoiceBucket) => `status-${bucket}`;

const periodLabel = (invoice: BillingInvoice) => {
  if (invoice.bucket === "replaced") return "Já coberto";
  if (!invoice.period_start || !invoice.period_end) return "—";
  return `${formatDayMonth(invoice.period_start)} a ${formatDayMonth(invoice.period_end)}`;
};

const actionUrl = (invoice: BillingInvoice) => (invoice.is_paid ? invoice.download_url || invoice.invoice_url : invoice.pay_url || invoice.invoice_url);

// Abre a fatura do Asaas em outra aba e passa a conferir o pagamento sozinho.
const payInvoice = (invoice: BillingInvoice) => {
  const url = actionUrl(invoice);
  if (!url) return;
  window.open(url, "_blank", "noopener");
  watcher.start(invoice.id);
};

const verifyPayment = () => {
  const target = watcher.invoiceId.value || unlockingInvoice.value?.id;
  if (!target) return;
  if (watcher.invoiceId.value !== target || watcher.phase.value !== "checking") watcher.start(target);
  void watcher.checkNow();
};

const openRenewal = (method: "pix" | "card" = "pix") => {
  renewalMethod.value = method;
  renewalOpen.value = true;
};

const onRenewed = async () => {
  await loadInvoices(false);
};

const loadInvoices = async (showSpinner = true) => {
  if (showSpinner) loading.value = true;
  errorMessage.value = "";
  try {
    const data = await getBillingInvoices();
    invoices.value = Array.isArray(data.items) ? data.items : [];
    account.value = data.account ?? null;
    counts.value = {
      paid: data.counts?.paid ?? 0,
      overdue: data.counts?.overdue ?? 0,
      upcoming: data.counts?.upcoming ?? 0,
      replaced: data.counts?.replaced ?? 0
    };
    agencyCounts.invoices = (counts.value.upcoming || 0) + (counts.value.overdue || 0);
    if (showSpinner) currentPage.value = 1;
  } catch (err) {
    console.error("Erro ao carregar faturas", err);
    errorMessage.value = "Não foi possível carregar as faturas do Asaas.";
    invoices.value = [];
    account.value = null;
    counts.value = { paid: 0, overdue: 0, upcoming: 0, replaced: 0 };
  } finally {
    loading.value = false;
  }
};

watch([activeTab, pageSize], () => {
  currentPage.value = 1;
});

watch(filteredInvoices, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value;
  }
});

onMounted(async () => {
  await loadInvoices();
  // Voltou do pagamento (link de retorno com ?paid=1): confere a fatura que libera o acesso.
  if (String(route.query.paid || "") === "1" && unlockingInvoice.value) {
    watcher.start(unlockingInvoice.value.id);
    void watcher.checkNow();
  }
});
</script>

<style scoped>
.page-wrap {
  padding: 0 0 48px;
  width: 100%;
  color: var(--foreground);
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

@media (prefers-reduced-motion: reduce) {
  .spinner,
  .ai-spinner {
    animation-duration: 3s;
  }
}

/* Cartão de situação da assinatura (mesmo desenho de "Seu plano" no Perfil) */
.pf-card { border-radius: 20px; background: var(--card); padding: 20px 22px; box-shadow: var(--shadow-card); }
.pf-plan { display: flex; flex-wrap: wrap; align-items: center; gap: 14px; border-radius: 16px; background: linear-gradient(120deg, #0d1f19, #0b1512 60%, #10291f); padding: 18px 20px; color: #fff; }
.pf-plan-icon { display: grid; place-items: center; width: 40px; height: 40px; flex-shrink: 0; border-radius: 999px; background: rgba(31, 227, 160, 0.14); color: #34d399; }
.pf-plan-icon svg { width: 18px; height: 18px; }
.pf-plan-main { flex: 1 1 220px; min-width: 0; }
.pf-plan-k { font-size: 12.5px; color: rgba(255, 255, 255, 0.72); }
.pf-plan-v { font-family: var(--font-display); font-size: 24px; line-height: 30px; font-weight: 600; }
.pf-status { border-radius: 999px; padding: 2px 10px; font-size: 11.5px; font-weight: 600; }
.pf-status.ok { background: rgba(52, 211, 153, 0.16); color: #34d399; }
.pf-status.warn { background: rgba(251, 191, 36, 0.16); color: #fbbf24; }
.pf-status.off { background: rgba(255, 255, 255, 0.12); color: rgba(255, 255, 255, 0.8); }
.pf-plan-btn { min-height: 44px; padding: 0 18px; border-radius: 999px; background: #1fe3a0; font-size: 13.5px; font-weight: 600; color: #062016; }
.pf-plan-btn:hover { background: #3eeab0; }
.pf-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 12px; }
.pf-facts > div { border-radius: 14px; background: var(--muted); padding: 10px 14px; }
.pf-facts p { font-size: 12px; color: var(--muted-foreground); }
.pf-facts b { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 2px; font-size: 14.5px; font-weight: 600; color: var(--foreground); }
.pf-fact-pay { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.pf-link { font-size: 13px; font-weight: 600; color: var(--primary); }
.pf-link:disabled { opacity: 0.6; }
.pf-note { margin-top: 12px; font-size: 12.5px; color: var(--muted-foreground); }
.tag { border-radius: 999px; padding: 1px 8px; font-size: 11px; font-weight: 600; }
.tag.danger { background: var(--status-danger); color: var(--status-danger-foreground); }

/* Avisos de conferência do pagamento */
.ai-notice { display: flex; flex-wrap: wrap; align-items: center; gap: 14px; border-radius: 20px; padding: 16px 18px; box-shadow: var(--shadow-card); }
.ai-notice.is-info { background: var(--status-info); color: var(--status-info-foreground); }
.ai-notice.is-ok { background: var(--status-success); color: var(--status-success-foreground); }
.ai-notice.is-warn { background: var(--status-warning); color: var(--status-warning-foreground); }
.ai-notice-inline { margin-top: 12px; box-shadow: none; }
.ai-notice-icon { display: grid; place-items: center; width: 40px; height: 40px; flex-shrink: 0; border-radius: 999px; background: var(--card); }
.ai-notice-icon svg { width: 18px; height: 18px; }
.ai-notice-text { flex: 1 1 320px; min-width: 0; font-size: 13px; opacity: 0.95; }
.ai-notice-title { font-family: var(--font-display); font-size: 16px; line-height: 22px; font-weight: 600; }
.ai-spinner { width: 18px; height: 18px; border-radius: 999px; border: 3px solid #cfe0f7; border-top-color: #2563eb; animation: spin 0.9s linear infinite; }

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

.ai-stat-icon.is-overdue { background: var(--status-danger); color: var(--status-danger-foreground); }
.ai-stat-h { font-size: 12px; color: var(--muted-foreground); }
.ai-doc.is-replaced { background: var(--muted); color: var(--muted-foreground); }
.ai-name small { display: block; font-size: 12px; font-weight: 400; color: var(--muted-foreground); }
.ai-strike { text-decoration: line-through; color: var(--muted-foreground); }
.ai-small { font-size: 12px; }
.ai-pill.status-replaced { background: var(--muted); color: var(--muted-foreground); }
.ai-foot { border-top: 1px solid var(--border); padding: 12px 16px; font-size: 12.5px; color: var(--muted-foreground); }
.ai-btn-ghost, .ai-btn-primary { min-height: 44px; }
.ai-table td, .ai-table th { padding-left: 12px; padding-right: 12px; }
.ai-table td:first-child { white-space: normal; min-width: 220px; }
.ai-table td:last-child, .ai-table th:last-child { padding-right: 16px; }
.ai-small { white-space: normal; display: inline-block; max-width: 110px; }
.ai-btn-sm { min-height: 36px; }
@media (max-width: 900px) { .pf-facts { grid-template-columns: 1fr; } }
</style>
