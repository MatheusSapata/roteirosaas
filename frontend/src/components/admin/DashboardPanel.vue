<template>
  <section class="am-page">
    <AdminMasterHeader title="Painel da plataforma" subtitle="Receita, clientes e cadastros. Os números seguem as mesmas regras das telas Receita e MRR e Empresas.">
      <div class="am-seg" role="group" aria-label="Período">
        <button v-for="option in periodOptions" :key="option.value" type="button" :class="{ on: period === option.value }" @click="period = option.value">
          {{ option.label }}
        </button>
      </div>
      <button type="button" class="am-btn" :disabled="!data" @click="exportPdf"><AmIcon name="dl" />Exportar PDF</button>
    </AdminMasterHeader>

    <div v-if="period === 'custom'" class="am-card flex flex-wrap items-center gap-3 !py-3">
      <label class="am-label !mb-0" for="dp-from">De</label>
      <input id="dp-from" v-model="customStart" type="date" class="am-input !w-auto" />
      <label class="am-label !mb-0" for="dp-to">até</label>
      <input id="dp-to" v-model="customEnd" type="date" class="am-input !w-auto" />
    </div>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="loading && !data" class="am-card am-empty"><div class="am-spinner"></div>Calculando os números...</div>

    <template v-if="data">
      <section class="am-grid-4" :class="{ 'opacity-60': loading }">
        <AdminMasterKpi icon="wallet" tone="success" label="Receita recorrente (MRR)" :value="formatMoney(data.mrr)">
          <template #hint>{{ plural(data.paying_customers, "cliente pagante", "clientes pagantes") }} · ticket médio {{ formatMoney(data.arpa) }}</template>
        </AdminMasterKpi>
        <AdminMasterKpi icon="card" tone="info" :label="`Recebido ${periodShort}`" :value="formatMoney(data.received)">
          <template #hint>
            <DeltaText :now="data.received" :before="data.received_previous" :label="previousLabel" />
            · {{ plural(data.payments, "pagamento", "pagamentos") }}<template v-if="data.refunded"> · {{ formatMoney(data.refunded) }} estornado</template>
          </template>
        </AdminMasterKpi>
        <AdminMasterKpi icon="trend" tone="violet" label="Novos clientes pagantes" :value="formatInt(data.new_paying)">
          <template #hint>
            <DeltaText :now="data.new_paying" :before="data.new_paying_previous" :label="previousLabel" /> · primeiro pagamento no período
          </template>
        </AdminMasterKpi>
        <AdminMasterKpi icon="pause" tone="warning" label="Clientes que saíram" :value="formatInt(data.left)">
          <template #hint>Saíram do ar no período · {{ formatMoney(data.mrr_at_risk) }} de MRR em risco hoje</template>
        </AdminMasterKpi>
      </section>

      <section class="dp-row" :class="{ 'opacity-60': loading }">
        <div class="am-card">
          <div class="am-card-head">
            <div>
              <h2 class="am-card-title">Receita recebida</h2>
              <p class="am-card-sub">{{ data.period.weekly ? "Por semana" : "Por dia" }} · {{ periodLabel }} · pagamentos confirmados na Asaas e na Cakto</p>
            </div>
            <p class="dp-figure am-num">{{ formatMoney(data.received) }}</p>
          </div>
          <AdminColumnChart
            :points="revenuePoints"
            :series="[{ label: 'Recebido', tone: 'accent' }]"
            :format="formatMoney"
            :format-tick="formatMoneyShort"
            :height="280"
            summary="Receita recebida no período"
            empty-text="Nenhum pagamento confirmado no período."
          />
        </div>

        <div class="am-card">
          <div class="am-card-head">
            <div>
              <h2 class="am-card-title">Empresas por situação</h2>
              <p class="am-card-sub">Hoje · {{ plural(companiesTotal, "empresa cliente", "empresas clientes") }} (fora as internas)</p>
            </div>
          </div>
          <div class="space-y-1">
            <RouterLink v-for="row in statusRows" :key="row.key" :to="row.to" class="dp-status">
              <div class="flex items-center justify-between gap-3 text-[13px]">
                <span>{{ row.label }}</span>
                <span class="am-num"><b>{{ formatInt(row.count) }}</b> <span class="am-muted">· {{ row.percent }}%</span></span>
              </div>
              <div class="dp-track"><i :style="{ width: `${row.bar}%` }"></i></div>
            </RouterLink>
          </div>
          <p class="am-card-sub mt-3">
            {{ plural(data.users, "pessoa com acesso", "pessoas com acesso") }} · {{ plural(data.pages, "página", "páginas") }} ({{ formatInt(data.pages_published) }} publicadas)
          </p>
        </div>
      </section>

      <section class="dp-row" :class="{ 'opacity-60': loading }">
        <div class="am-card">
          <div class="am-card-head">
            <div>
              <h2 class="am-card-title">Empresas cadastradas</h2>
              <p class="am-card-sub">{{ data.period.weekly ? "Por semana" : "Por dia" }} · {{ periodLabel }} · quantas dessas já pagam hoje</p>
            </div>
            <p class="dp-figure am-num">{{ formatInt(data.signups) }}</p>
          </div>
          <AdminColumnChart
            :points="signupPoints"
            :height="250"
            :series="[
              { label: 'Já pagam', tone: 'accent' },
              { label: 'Ainda não pagam', tone: 'muted' }
            ]"
            summary="Empresas cadastradas no período"
            empty-text="Nenhuma empresa cadastrada no período."
          />
          <p class="am-card-sub mt-2">
            Conversão do período: <b class="text-foreground">{{ conversion }}</b>
            · <DeltaText :now="data.signups" :before="data.signups_previous" :label="`cadastros ${previousLabel}`" />
          </p>
        </div>

        <div class="am-card">
          <div class="am-card-head">
            <div>
              <h2 class="am-card-title">Clientes pagantes por plano</h2>
              <p class="am-card-sub">Hoje · quem renova (sem quem já cancelou)</p>
            </div>
          </div>
          <div v-if="data.mrr_by_plan.length" class="space-y-3">
            <div v-for="row in planRows" :key="row.plan">
              <div class="mb-1.5 flex items-center justify-between gap-3 text-[13px]">
                <span>{{ row.label }} <span class="am-muted">· {{ plural(row.customers, "cliente", "clientes") }}</span></span>
                <b class="am-num">{{ formatMoney(row.mrr) }}</b>
              </div>
              <div class="dp-track"><i :style="{ width: `${row.bar}%` }"></i></div>
            </div>
          </div>
          <p v-else class="am-empty">Nenhum cliente pagante ainda.</p>
          <RouterLink to="/admin/administracao/receita-previsao" class="mt-4 inline-block text-xs font-semibold text-primary">Abrir Receita e MRR →</RouterLink>
        </div>
      </section>

      <section class="am-card">
        <div class="am-card-head">
          <div>
            <h2 class="am-card-title">Precisa de atenção</h2>
            <p class="am-card-sub">O que pede ação hoje</p>
          </div>
        </div>
        <div class="dp-attention">
          <RouterLink v-for="item in attentionItems" :key="item.id" :to="item.to" class="dp-attention-item">
            <span class="am-tile !h-8 !w-8" :class="`am-tone-${item.count ? item.tone : 'neutral'}`"><AmIcon :name="item.icon" /></span>
            <div class="min-w-0">
              <b class="text-[13.5px]">{{ item.title }}</b>
              <p class="am-card-sub !mt-0">{{ item.description }}</p>
              <p class="mt-1.5 text-xs font-semibold text-primary">Abrir {{ item.target }} →</p>
            </div>
          </RouterLink>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref, watch } from "vue";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { getDashboard, type DashboardData } from "../../services/adminMaster";
import type { CompanyStatusKey } from "../../services/companies";
import { adminMasterCounts } from "../../composables/useAdminMasterCounts";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";
import AdminColumnChart, { type ColumnPoint } from "./master/AdminColumnChart.vue";
import { formatInt, formatMoney, formatMoneyShort, planLabel, plural } from "./master/format";

type Period = "7" | "30" | "90" | "custom";
const periodOptions: Array<{ value: Period; label: string }> = [
  { value: "7", label: "7 dias" },
  { value: "30", label: "30 dias" },
  { value: "90", label: "90 dias" },
  { value: "custom", label: "Personalizado" }
];

/** "▲ 12% vs 30 dias anteriores": variação contra o período anterior de mesmo tamanho. */
const DeltaText = defineComponent({
  props: { now: { type: Number, required: true }, before: { type: Number, required: true }, label: { type: String, required: true } },
  setup(props) {
    return () => {
      if (!props.before) return h("span", props.now ? `sem base ${props.label}` : `igual ${props.label}`);
      const change = Math.round(((props.now - props.before) / props.before) * 100);
      if (!change) return h("span", `igual ${props.label}`);
      return h("span", [h("span", { class: change > 0 ? "am-up" : "am-down" }, `${change > 0 ? "▲" : "▼"} ${Math.abs(change)}%`), ` ${props.label}`]);
    };
  }
});

const period = ref<Period>("30");
const customStart = ref("");
const customEnd = ref("");
const data = ref<DashboardData | null>(null);
const loading = ref(false);
const errorMessage = ref("");
let requestId = 0;

const load = async () => {
  if (period.value === "custom" && (!customStart.value || !customEnd.value)) return;
  const id = ++requestId;
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = period.value === "custom" ? { start_date: customStart.value, end_date: customEnd.value } : { days: Number(period.value) };
    const result = await getDashboard(params);
    if (id === requestId) data.value = result;
  } catch (error: any) {
    if (id === requestId) errorMessage.value = error?.response?.data?.detail || "Não foi possível carregar o painel.";
  } finally {
    if (id === requestId) loading.value = false;
  }
};
watch([period, customStart, customEnd], () => void load());
onMounted(load);

const parseDay = (iso: string) => new Date(`${iso}T12:00:00`);
const shortDay = (iso: string) => parseDay(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
const longDay = (iso: string) => parseDay(iso).toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" });
const bucketTitle = (start: string, end: string) => (start === end ? longDay(start) : `${shortDay(start)} a ${shortDay(end)}`);

const periodLabel = computed(() => (data.value ? `${shortDay(data.value.period.start)} a ${shortDay(data.value.period.end)}` : ""));
const periodShort = computed(() => (period.value === "custom" ? "no período" : `em ${period.value} dias`));
const previousLabel = computed(() => `vs ${data.value?.period.days ?? ""} dias anteriores`);
const conversion = computed(() => {
  if (!data.value?.signups) return "—";
  return `${Math.round((data.value.signups_paying / data.value.signups) * 100)}% (${formatInt(data.value.signups_paying)} de ${formatInt(data.value.signups)})`;
});

const revenuePoints = computed<ColumnPoint[]>(() =>
  (data.value?.series || []).map(bucket => ({
    key: bucket.start,
    label: shortDay(bucket.start),
    title: bucketTitle(bucket.start, bucket.end),
    values: [bucket.received],
    extra: [plural(bucket.payments, "pagamento", "pagamentos"), plural(bucket.new_paying, "cliente novo", "clientes novos")]
  }))
);
const signupPoints = computed<ColumnPoint[]>(() =>
  (data.value?.series || []).map(bucket => ({
    key: bucket.start,
    label: shortDay(bucket.start),
    title: bucketTitle(bucket.start, bucket.end),
    values: [bucket.signups_paying, bucket.signups - bucket.signups_paying],
    extra: [plural(bucket.signups, "cadastro", "cadastros")]
  }))
);

const STATUS_ROWS: Array<{ key: CompanyStatusKey; label: string; filtro: string }> = [
  { key: "active", label: "Ativas com pagamento em dia", filtro: "ativas" },
  { key: "past_due", label: "Inadimplentes", filtro: "inadimplentes" },
  { key: "cancelling", label: "Cancelando no fim do período", filtro: "cancelando" },
  { key: "trial", label: "Em teste", filtro: "teste" },
  { key: "free", label: "Gratuitas no prazo", filtro: "gratuitas" },
  { key: "free_expired", label: "Gratuitas vencidas", filtro: "vencidas" },
  { key: "trial_ended", label: "Teste encerrado", filtro: "teste-encerrado" },
  { key: "combo", label: "Combo Viaje On (fora do MRR)", filtro: "combo" },
  { key: "inactive", label: "Desativadas", filtro: "desativadas" }
];
const companiesTotal = computed(() => STATUS_ROWS.reduce((sum, row) => sum + (data.value?.companies[row.key] || 0), 0));
const statusRows = computed(() => {
  const total = companiesTotal.value || 1;
  const max = Math.max(1, ...STATUS_ROWS.map(row => data.value?.companies[row.key] || 0));
  return STATUS_ROWS.map(row => {
    const count = data.value?.companies[row.key] || 0;
    return {
      ...row,
      count,
      percent: Math.round((count / total) * 100),
      bar: count ? Math.max(1.5, (count / max) * 100) : 0,
      to: { path: "/admin/administracao/empresas", query: { filtro: row.filtro } }
    };
  });
});
const planRows = computed(() => {
  const rows = data.value?.mrr_by_plan || [];
  const max = Math.max(1, ...rows.map(row => row.mrr));
  return rows.map(row => ({ ...row, label: planLabel(row.plan), bar: (row.mrr / max) * 100 }));
});

const attentionItems = computed(() => {
  const counts = data.value?.companies || {};
  const pastDue = counts.past_due || 0;
  const cancelling = counts.cancelling || 0;
  const trials = data.value?.trials_ending || 0;
  const expired = counts.free_expired || 0;
  const whatsapp = adminMasterCounts.whatsappIssues ?? 0;
  const companies = (filtro: string) => ({ path: "/admin/administracao/empresas", query: { filtro } });
  return [
    { id: "past_due", count: pastDue, icon: "alert", tone: "danger", title: plural(pastDue, "empresa inadimplente", "empresas inadimplentes"), description: "Cobrança com falha ou atrasada", target: "Empresas", to: companies("inadimplentes") },
    { id: "cancelling", count: cancelling, icon: "cal", tone: "warning", title: plural(cancelling, "empresa cancelando", "empresas cancelando"), description: "Saem no fim do período pago", target: "Empresas", to: companies("cancelando") },
    { id: "trials", count: trials, icon: "history", tone: "info", title: plural(trials, "teste termina", "testes terminam"), description: "Em até 3 dias", target: "Empresas", to: companies("teste-acabando") },
    { id: "free_expired", count: expired, icon: "user", tone: "warning", title: plural(expired, "gratuita vencida", "gratuitas vencidas"), description: "Prazo do acesso gratuito já passou", target: "Empresas", to: companies("vencidas") },
    { id: "whatsapp", count: whatsapp, icon: "wa", tone: "warning", title: `${formatInt(whatsapp)} WhatsApp ${whatsapp === 1 ? "desconectado" : "desconectados"}`, description: "Conexões das agências fora do ar", target: "WhatsApp", to: "/admin/administracao/whatsapp" }
  ];
});

const exportPdf = () => {
  const report = data.value;
  if (!report) return;
  const doc = new jsPDF("p", "mm", "a4");
  const margin = 14;
  doc.setFontSize(16);
  doc.text("Painel da plataforma · Roteiro Online", margin, 18);
  doc.setFontSize(10);
  doc.text(`Período: ${periodLabel.value} · emitido em ${new Date().toLocaleString("pt-BR")}`, margin, 25);
  autoTable(doc, {
    startY: 32,
    head: [["Indicador", "Valor"]],
    body: [
      ["MRR (hoje)", formatMoney(report.mrr)],
      ["ARR (MRR × 12)", formatMoney(report.arr)],
      ["Clientes pagantes (hoje)", formatInt(report.paying_customers)],
      ["Ticket médio", formatMoney(report.arpa)],
      ["MRR em risco (hoje)", formatMoney(report.mrr_at_risk)],
      ["Recebido no período", formatMoney(report.received)],
      ["Estornado no período", formatMoney(report.refunded)],
      ["Novos clientes pagantes", formatInt(report.new_paying)],
      ["Clientes que saíram", formatInt(report.left)],
      ["Empresas cadastradas", formatInt(report.signups)],
      ["Cadastros que já pagam", formatInt(report.signups_paying)]
    ],
    theme: "striped",
    styles: { fontSize: 10, cellPadding: 3 },
    headStyles: { fillColor: [5, 150, 105], textColor: 255 }
  });
  autoTable(doc, {
    startY: (doc as any).lastAutoTable.finalY + 8,
    head: [["Situação das empresas (hoje)", "Empresas"]],
    body: statusRows.value.map(row => [row.label, formatInt(row.count)]),
    theme: "grid",
    styles: { fontSize: 10, cellPadding: 3 },
    headStyles: { fillColor: [71, 85, 105], textColor: 255 }
  });
  autoTable(doc, {
    startY: (doc as any).lastAutoTable.finalY + 8,
    head: [[report.period.weekly ? "Semana" : "Dia", "Recebido", "Pagamentos", "Clientes novos", "Cadastros"]],
    body: report.series.map(bucket => [
      bucketTitle(bucket.start, bucket.end),
      formatMoney(bucket.received),
      formatInt(bucket.payments),
      formatInt(bucket.new_paying),
      formatInt(bucket.signups)
    ]),
    theme: "grid",
    styles: { fontSize: 9, cellPadding: 2 },
    headStyles: { fillColor: [71, 85, 105], textColor: 255 }
  });
  doc.save(`painel-admin-${new Date().toISOString().slice(0, 10)}.pdf`);
};
</script>

<style scoped>
.dp-row {
  display: grid;
  align-items: start;
  gap: 14px;
  grid-template-columns: minmax(0, 1fr);
}
@media (min-width: 1180px) {
  .dp-row {
    grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  }
}
.dp-figure {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  white-space: nowrap;
  color: var(--foreground);
}
.dp-status {
  display: block;
  margin: 0 -8px;
  padding: 6px 8px;
  border-radius: 10px;
  transition: background-color 0.15s ease;
}
.dp-status:hover {
  background: var(--muted);
}
.dp-track {
  height: 6px;
  margin-top: 5px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--muted);
}
.dp-track > i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: #059669;
}
:global(html.dark) .dp-track > i {
  background: #0fa877;
}
.dp-attention {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
}
.dp-attention-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border-radius: 14px;
  background: var(--muted);
  padding: 12px;
  transition: box-shadow 0.15s ease;
}
.dp-attention-item:hover {
  box-shadow: inset 0 0 0 1px var(--border);
}
</style>
