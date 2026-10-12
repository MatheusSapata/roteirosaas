<template>
  <section class="am-page">
    <AdminMasterHeader
      title="Receita e MRR"
      subtitle="Quanto a plataforma fatura por mês, o que entrou, o que falta receber e as próximas renovações. Somente leitura: nada aqui gera, altera ou cancela cobrança."
    >
      <input v-model="month" type="month" class="am-input w-[160px]" :max="currentMonth" @change="load" />
      <button type="button" class="am-btn" :disabled="loading" @click="load"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>

    <template v-if="data">
      <section class="am-grid-4">
        <AdminMasterKpi icon="trend" tone="success" label="MRR" :value="money(data.mrr)" :hint="`${data.paying_customers} clientes pagantes · ticket médio ${money(data.arpa)}`" />
        <AdminMasterKpi icon="cal" tone="info" label="ARR" :value="money(data.arr)" hint="MRR × 12" />
        <AdminMasterKpi icon="alert" tone="warning" label="MRR em risco" :value="money(data.mrr_at_risk)" hint="Cancelamento agendado ou falha de cobrança" />
        <AdminMasterKpi icon="wallet" tone="violet" label="Previsto no mês" :value="money(data.month_expected)" :hint="isCurrentMonth ? 'Recebido + a receber, menos estornos' : 'Recebido menos estornos'" />
      </section>

      <section class="am-card">
        <div class="am-card-head">
          <div>
            <div class="am-card-title">{{ monthLabel }}</div>
            <div class="am-card-sub">Pagamentos confirmados pela Asaas e pela Cakto (cada um contado uma vez) e renovações previstas até o fim do mês.</div>
          </div>
        </div>
        <div class="rv-tiles">
          <div>
            <span class="am-muted text-xs">Recebido</span>
            <b>{{ money(data.month_received_gross) }}</b>
            <small class="am-muted">{{ data.month_payments }} pagamentos · líquido {{ money(data.month_received_net) }}</small>
          </div>
          <div v-if="data.month_to_receive !== null">
            <span class="am-muted text-xs">A receber até o fim do mês</span>
            <b>{{ money(data.month_to_receive) }}</b>
            <small class="am-muted">{{ data.month_to_receive_count }} renovações previstas</small>
          </div>
          <div>
            <span class="am-muted text-xs">Em atraso</span>
            <b :class="data.overdue ? 'text-red-600' : ''">{{ money(data.overdue) }}</b>
            <small class="am-muted">{{ data.overdue_items.length }} assinaturas com vencimento passado</small>
          </div>
          <div>
            <span class="am-muted text-xs">Estornos</span>
            <b>{{ money(data.month_refunded) }}</b>
            <small class="am-muted">devolvidos no mês</small>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <button type="button" class="am-btn" :disabled="checkingAsaas" @click="checkAsaas"><AmIcon name="search" />Conferir cobranças em aberto na Asaas</button>
          <small v-if="asaas" class="am-muted">
            Até {{ formatDate(asaas.until) }}: {{ asaas.pending.count }} pendentes ({{ money(asaas.pending.amount) }}) · {{ asaas.overdue.count }} vencidas ({{ money(asaas.overdue.amount) }})
          </small>
          <small v-else class="am-muted">Só consulta: não cria nem altera nada na Asaas.</small>
        </div>
      </section>

      <section class="grid gap-4 lg:grid-cols-3">
        <div v-for="block in breakdowns" :key="block.title" class="am-card">
          <div class="am-card-title mb-2">{{ block.title }}</div>
          <div v-for="(value, key) in block.values" :key="key" class="rv-row">
            <span>{{ key }}</span>
            <div class="am-bar flex-1"><i :style="{ width: `${data.mrr ? Math.round((value / data.mrr) * 100) : 0}%` }"></i></div>
            <b class="am-num">{{ money(value) }}</b>
          </div>
          <div v-if="!Object.keys(block.values).length" class="am-muted text-sm">Sem dados.</div>
        </div>
      </section>

      <section class="am-card am-card-flush">
        <div class="am-toolbar">
          <button v-for="option in [30, 60, 90]" :key="option" type="button" class="am-chip" :class="{ on: horizon === option }" @click="setHorizon(option)">
            Próximos {{ option }} dias
          </button>
          <span class="am-card-sub ml-auto !mt-0">{{ data.upcoming.length }} renovações · {{ money(data.upcoming_total) }}</span>
        </div>
        <div v-if="weeks.length" class="rv-weeks">
          <div v-for="week in weeks" :key="week.start">
            <span class="am-muted text-xs">Semana de {{ formatDate(week.start) }}</span>
            <b class="am-num">{{ money(week.total) }}</b>
          </div>
        </div>
        <div class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Vencimento</th>
                <th>Cliente</th>
                <th>Plano</th>
                <th>Pagamento</th>
                <th class="am-right">Valor da cobrança</th>
                <th>Atenção</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in data.upcoming" :key="`up-${item.subscription_id}`">
                <td class="am-num">{{ formatDate(item.due_on) }}</td>
                <td>
                  <b class="font-semibold">{{ item.name }}</b>
                  <small class="am-muted block">{{ item.email }}</small>
                </td>
                <td>{{ item.plan }} <small class="am-muted block">{{ item.cycle }}</small></td>
                <td>{{ item.method }} <small class="am-muted block">{{ item.provider }}</small></td>
                <td class="am-num am-right"><b>{{ money(item.amount) }}</b></td>
                <td><span v-for="alert in item.alerts" :key="alert" class="am-badge am-tone-warning mr-1">{{ alert }}</span></td>
              </tr>
              <tr v-if="!data.upcoming.length">
                <td colspan="6"><div class="am-empty">Nenhuma renovação neste período.</div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="data.overdue_items.length" class="am-card am-card-flush">
        <div class="am-toolbar"><b>Em atraso</b><span class="am-card-sub ml-auto !mt-0">Vencimento passou e a renovação não foi confirmada</span></div>
        <div class="am-table-wrap">
          <table class="am-table">
            <tbody>
              <tr v-for="item in data.overdue_items" :key="`od-${item.subscription_id}`">
                <td class="am-num">{{ formatDate(item.due_on) }}</td>
                <td><b class="font-semibold">{{ item.name }}</b><small class="am-muted block">{{ item.email }}</small></td>
                <td>{{ item.plan }} · {{ item.method }}</td>
                <td class="am-num am-right"><b>{{ money(item.amount) }}</b></td>
                <td><span v-for="alert in item.alerts" :key="alert" class="am-badge am-tone-warning mr-1">{{ alert }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="am-card am-card-flush">
        <div class="am-toolbar"><b>Pagamentos recebidos em {{ monthLabel.toLowerCase() }}</b></div>
        <div class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr><th>Data</th><th>Origem</th><th>Cliente / descrição</th><th>Forma</th><th class="am-right">Bruto</th><th class="am-right">Líquido</th></tr>
            </thead>
            <tbody>
              <tr v-for="(payment, index) in data.payments" :key="`pay-${index}`">
                <td class="am-num">{{ formatDate(payment.paid_at) }}</td>
                <td>{{ payment.source }}</td>
                <td>{{ payment.email || payment.description || "—" }}</td>
                <td>{{ payment.method }}</td>
                <td class="am-num am-right">{{ money(payment.gross) }}</td>
                <td class="am-num am-right">{{ money(payment.net) }}</td>
              </tr>
              <tr v-if="!data.payments.length"><td colspan="6"><div class="am-empty">Nenhum pagamento neste mês.</div></td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
    <div v-else-if="loading" class="am-empty"><div class="am-spinner"></div>Calculando receita...</div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getAsaasOpenCharges, getRevenue, type AsaasOpenCharges, type RevenueOverview } from "../../services/revenue";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";

const today = new Date();
const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
const month = ref(currentMonth);
const horizon = ref(60);
const loading = ref(false);
const errorMessage = ref("");
const data = ref<RevenueOverview | null>(null);
const asaas = ref<AsaasOpenCharges | null>(null);
const checkingAsaas = ref(false);

const isCurrentMonth = computed(() => month.value === currentMonth);
const monthLabel = computed(() => {
  const [year, monthNumber] = month.value.split("-").map(Number);
  const label = new Date(year, monthNumber - 1, 1).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
  return label.charAt(0).toUpperCase() + label.slice(1);
});
const breakdowns = computed(() =>
  data.value
    ? [
        { title: "MRR por plano", values: data.value.mrr_by_plan },
        { title: "MRR por ciclo", values: data.value.mrr_by_cycle },
        { title: "MRR por forma de pagamento", values: data.value.mrr_by_method }
      ]
    : []
);
const weeks = computed(() => Object.entries(data.value?.upcoming_by_week || {}).map(([start, total]) => ({ start, total })));

const money = (value?: number | null) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value || 0));
const formatDate = (value: string) => {
  const date = new Date(value.length === 10 ? `${value}T12:00:00` : value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("pt-BR");
};

const load = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    data.value = await getRevenue(month.value, horizon.value);
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível calcular a receita.";
  } finally {
    loading.value = false;
  }
};
const setHorizon = (value: number) => {
  horizon.value = value;
  void load();
};
const checkAsaas = async () => {
  checkingAsaas.value = true;
  errorMessage.value = "";
  try {
    asaas.value = await getAsaasOpenCharges();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível consultar a Asaas.";
  } finally {
    checkingAsaas.value = false;
  }
};

onMounted(load);
</script>

<style scoped>
.rv-tiles,
.rv-weeks {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}
.rv-weeks {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.rv-tiles > div,
.rv-weeks > div {
  display: grid;
  gap: 2px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
}
.rv-tiles b {
  font-size: 20px;
}
.rv-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: 13px;
}
.rv-row > span {
  width: 110px;
  flex: none;
}
</style>
