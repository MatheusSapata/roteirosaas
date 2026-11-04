<template>
  <div class="space-y-4">
    <div v-if="loading" class="am-card"><div class="am-empty"><div class="am-spinner"></div>Consultando faturas e pagamentos...</div></div>
    <div v-else-if="loadError" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ loadError }}</span></div>

    <template v-else-if="data">
      <div v-if="notice" class="am-notice" :class="`am-tone-${notice.tone}`">
        <AmIcon :name="notice.tone === 'success' ? 'check' : 'alert'" /><span>{{ notice.text }}</span>
      </div>

      <section class="am-grid-4">
        <AdminMasterKpi icon="check" tone="success" label="Pago" :value="formatMoney(paidTotal)" :hint="`${formatInt(paidCount)} pagamentos registrados`" />
        <AdminMasterKpi
          icon="alert"
          tone="danger"
          label="Vencido em aberto"
          :value="formatMoney(account?.open_amount || 0)"
          :hint="account?.open_count ? `${plural(account.open_count, 'fatura vencida', 'faturas vencidas')}` : 'Nada vencido'"
        />
        <AdminMasterKpi
          icon="cal"
          tone="info"
          label="Próxima cobrança"
          :value="account?.next_charge ? formatMoney(account.next_charge.amount) : '—'"
          :hint="account?.next_charge ? `vence ${formatPlainDate(account.next_charge.due_date)}` : 'Nenhuma fatura a vencer'"
        />
        <AdminMasterKpi
          icon="card"
          tone="neutral"
          label="Cobrança"
          :value="gatewayLabel(data.provider)"
          :hint="data.asaas_customer_id ? `Cliente Asaas ${data.asaas_customer_id}` : 'Sem cliente no Asaas'"
        />
      </section>

      <!-- FATURAS DO ASAAS -->
      <section class="am-card am-card-flush">
        <div class="am-card-head cb-head">
          <div>
            <div class="am-card-title">Faturas no Asaas</div>
            <div class="am-card-sub">Lidas agora no Asaas. As mesmas que o cliente vê em Faturas.</div>
          </div>
          <button type="button" class="am-btn am-btn-sm" :disabled="loading" @click="load"><AmIcon name="refresh" />Atualizar</button>
        </div>
        <div v-if="data.asaas_error" class="am-notice am-tone-warning mx-4 mb-3"><AmIcon name="alert" /><span>{{ data.asaas_error }}</span></div>
        <template v-if="invoices.length">
          <div class="am-toolbar">
            <button
              v-for="option in bucketFilters"
              :key="option.value"
              type="button"
              class="am-chip"
              :class="{ on: bucket === option.value }"
              @click="bucket = option.value"
            >
              {{ option.label }} <span class="am-count am-num">{{ formatInt(bucketCount(option.value)) }}</span>
            </button>
          </div>
          <div class="am-table-wrap">
            <table class="am-table">
              <thead>
                <tr>
                  <th>Vencimento</th>
                  <th>Situação</th>
                  <th>Forma</th>
                  <th>Período</th>
                  <th class="am-right">Valor</th>
                  <th>Pago em</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="invoice in filteredInvoices" :key="invoice.id">
                  <td class="am-num">
                    {{ formatPlainDate(invoice.due_date) }}
                    <small class="am-muted am-mono block">{{ invoice.id }}</small>
                  </td>
                  <td>
                    <span class="am-badge am-dot" :class="(invoiceBucketMeta[invoice.bucket] || invoiceBucketMeta.upcoming).tone">
                      {{ (invoiceBucketMeta[invoice.bucket] || invoiceBucketMeta.upcoming).label }}
                    </span>
                    <small v-if="invoice.id === account?.unlocking_invoice_id" class="am-muted block">Paga, libera o acesso</small>
                    <small v-else-if="invoice.bucket === 'replaced'" class="am-muted block">{{ invoice.status }}</small>
                  </td>
                  <td>{{ billingTypeLabel(invoice.billing_type) }}</td>
                  <td class="am-num whitespace-nowrap">
                    <template v-if="invoice.period_start">{{ formatPlainDate(invoice.period_start) }} a {{ formatPlainDate(invoice.period_end) }}</template>
                    <template v-else>—</template>
                  </td>
                  <td class="am-right am-num">{{ formatMoney(invoice.value) }}</td>
                  <td class="am-num">{{ invoice.payment_date ? formatPlainDate(invoice.payment_date) : "—" }}</td>
                  <td class="am-right whitespace-nowrap">
                    <a v-if="invoice.invoice_url || invoice.pay_url" :href="invoice.invoice_url || invoice.pay_url || ''" target="_blank" rel="noopener noreferrer" class="am-btn am-btn-sm">
                      Abrir
                    </a>
                    <button
                      v-if="!invoice.is_paid && invoice.bucket !== 'replaced'"
                      type="button"
                      class="am-btn am-btn-sm ml-1"
                      :disabled="syncingId === invoice.id"
                      title="Confere no Asaas e, se estiver paga, aplica na conta"
                      @click="sync(invoice)"
                    >
                      {{ syncingId === invoice.id ? "Conferindo..." : "Conferir no Asaas" }}
                    </button>
                  </td>
                </tr>
                <tr v-if="!filteredInvoices.length">
                  <td colspan="7"><div class="am-empty">Nenhuma fatura nesta situação.</div></td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <div v-else-if="!data.asaas_error" class="am-empty">Nenhuma fatura no Asaas para esta empresa.</div>
      </section>

      <!-- CAKTO -->
      <section v-if="data.cakto_payments.length || data.provider === 'cakto'" class="am-card am-card-flush">
        <div class="am-card-head cb-head">
          <div>
            <div class="am-card-title">Pagamentos pela Cakto</div>
            <div class="am-card-sub">Compras e renovações que a Cakto avisou (pelo e-mail do dono).</div>
          </div>
        </div>
        <div v-if="data.cakto_payments.length" class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Evento</th>
                <th>Oferta</th>
                <th>Forma</th>
                <th class="am-right">Valor</th>
                <th>Pedido</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="payment in data.cakto_payments" :key="payment.id">
                <td class="am-num">{{ formatDateTime(payment.created_at) }}</td>
                <td>
                  <span class="am-badge am-dot" :class="payment.status === 'error' ? 'am-tone-danger' : 'am-tone-success'">{{ payment.label }}</span>
                </td>
                <td>{{ payment.offer || "—" }}</td>
                <td>{{ billingTypeLabel(payment.payment_method) }}</td>
                <td class="am-right am-num">{{ payment.amount !== null ? formatMoney(payment.amount) : "—" }}</td>
                <td class="am-mono">{{ payment.order_id || "—" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="am-empty">Nenhum pagamento da Cakto registrado para este e-mail.</div>
      </section>

      <!-- CHECKOUT -->
      <section class="am-card am-card-flush">
        <div class="am-card-head cb-head">
          <div>
            <div class="am-card-title">Compras no checkout</div>
            <div class="am-card-sub">Cada vez que o dono abriu o checkout próprio: o que escolheu e como terminou.</div>
          </div>
        </div>
        <div v-if="data.checkouts.length" class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Início</th>
                <th>Situação</th>
                <th>Produto</th>
                <th>Forma</th>
                <th class="am-right">Valor</th>
                <th>Pago em</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="checkout in data.checkouts" :key="checkout.id">
                <td class="am-num">{{ formatDateTime(checkout.created_at) }}</td>
                <td>
                  <span class="am-badge am-dot" :class="checkout.status === 'paid' ? 'am-tone-success' : 'am-tone-neutral'">{{ checkout.status_label }}</span>
                </td>
                <td>
                  {{ checkout.product_name }}
                  <small class="am-muted block">{{ planLabel(checkout.plan_key) }} · {{ cycleLabel(checkout.billing_cycle) }}<template v-if="checkout.coupon_code"> · cupom {{ checkout.coupon_code }}</template></small>
                </td>
                <td>{{ billingTypeLabel(checkout.payment_method) }}</td>
                <td class="am-right am-num">{{ formatMoney(checkout.amount) }}</td>
                <td class="am-num">{{ checkout.paid_at ? formatDateTime(checkout.paid_at) : "—" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="am-empty">Nenhuma compra pelo checkout próprio.</div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { getCompanyBilling, syncCompanyInvoice, type CompanyBilling, type CompanyInvoice } from "../../../services/companies";
import AmIcon from "../master/AmIcon.vue";
import AdminMasterKpi from "../master/AdminMasterKpi.vue";
import { formatDateTime, formatInt, formatMoney, gatewayLabel, planLabel, plural } from "../master/format";
import { billingTypeLabel, formatPlainDate, invoiceBucketMeta } from "./companyLabels";
import { cycleLabel } from "../../../utils/billingCycle";

const props = defineProps<{ companyId: number }>();
const emit = defineEmits<{ (e: "changed", message: string): void }>();

const data = ref<CompanyBilling | null>(null);
const loading = ref(false);
const loadError = ref("");
const notice = ref<{ tone: "success" | "danger" | "info"; text: string } | null>(null);

const load = async () => {
  loading.value = true;
  loadError.value = "";
  try {
    data.value = await getCompanyBilling(props.companyId);
  } catch (error: any) {
    loadError.value = error?.response?.data?.detail || "Não foi possível carregar as faturas.";
  } finally {
    loading.value = false;
  }
};
onMounted(load);
watch(() => props.companyId, load);

const invoices = computed(() => data.value?.asaas?.items || []);
const account = computed(() => data.value?.asaas?.account || null);

type Bucket = "all" | "pending" | "paid" | "overdue" | "upcoming" | "replaced";
const bucket = ref<Bucket>("all");
const bucketFilters: Array<{ value: Bucket; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "pending", label: "Pendentes" },
  { value: "overdue", label: "Vencidas" },
  { value: "upcoming", label: "A vencer" },
  { value: "paid", label: "Pagas" },
  { value: "replaced", label: "Substituídas" }
];
const matches = (invoice: CompanyInvoice, value: Bucket) =>
  value === "all" || (value === "pending" ? ["overdue", "upcoming"].includes(invoice.bucket) : invoice.bucket === value);
const bucketCount = (value: Bucket) => invoices.value.filter(invoice => matches(invoice, value)).length;
const filteredInvoices = computed(() => invoices.value.filter(invoice => matches(invoice, bucket.value)));

const paidInvoices = computed(() => invoices.value.filter(invoice => invoice.is_paid));
const paidTotal = computed(
  () =>
    paidInvoices.value.reduce((sum, invoice) => sum + invoice.value, 0) +
    (data.value?.cakto_payments || []).reduce((sum, payment) => sum + (payment.amount || 0), 0)
);
const paidCount = computed(() => paidInvoices.value.length + (data.value?.cakto_payments.length || 0));

const syncingId = ref<string | null>(null);
const sync = async (invoice: CompanyInvoice) => {
  syncingId.value = invoice.id;
  notice.value = null;
  try {
    const result = await syncCompanyInvoice(props.companyId, invoice.id);
    if (result.paid && result.applied) {
      notice.value = { tone: "success", text: `Fatura ${invoice.id} está paga no Asaas e foi aplicada na conta.` };
      emit("changed", "");
    } else if (result.paid) {
      notice.value = { tone: "info", text: `Fatura ${invoice.id} está paga no Asaas; a conta já estava em dia.` };
    } else {
      notice.value = { tone: "info", text: `Fatura ${invoice.id} continua em aberto no Asaas (${result.invoice.status}).` };
    }
    await load();
  } catch (error: any) {
    notice.value = { tone: "danger", text: error?.response?.data?.detail || "Não foi possível conferir a fatura." };
  } finally {
    syncingId.value = null;
  }
};
</script>

<style scoped>
.cb-head {
  padding: 16px 16px 10px;
  margin: 0;
}
</style>
