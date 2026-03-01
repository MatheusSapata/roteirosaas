<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <header class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p :class="['text-xs uppercase tracking-[0.25em]', premiumMode ? 'text-white/50' : 'text-slate-500']">Administracao</p>
        <h1 :class="['text-3xl font-bold', premiumMode ? 'text-white' : 'text-slate-900']">Visao gerencial</h1>
        <p :class="['text-sm', premiumMode ? 'text-white/60' : 'text-slate-500']">Resumo de usuarios, planos, validade e MRR.</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <select v-model="days" class="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
          <option value="7">Ultimos 7 dias</option>
          <option value="30">Ultimos 30 dias</option>
          <option value="90">Ultimos 90 dias</option>
        </select>
        <button
          @click="exportPdf"
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
          Exportar PDF
        </button>
      </div>
    </header>

    <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ error }}
    </div>

    <section class="grid gap-4 md:grid-cols-4">
      <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Usuarios</p>
        <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.total_users ?? "--" }}</p>
        <p class="text-xs text-slate-400">Contas ativas no SaaS.</p>
      </div>
      <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Agencias</p>
        <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.total_agencies ?? "--" }}</p>
        <p class="text-xs text-slate-400">Times cadastrados.</p>
      </div>
      <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Paginas totais</p>
        <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.total_pages ?? "--" }}</p>
        <p class="text-xs text-slate-400">Inclui rascunhos e publicadas.</p>
      </div>
      <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Paginas publicadas</p>
        <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.published_pages ?? "--" }}</p>
        <p class="text-xs text-slate-400">Visiveis ao publico.</p>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">MRR estimado</p>
        <p class="mt-2 text-3xl font-bold text-slate-900">R$ {{ metrics?.mrr?.toFixed(2) ?? "--" }}</p>
        <p class="text-xs text-slate-400">Somatório dos planos ativos.</p>
      </div>
      <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Novos usuarios ({{ days }}d)</p>
        <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.new_users_last_days ?? "--" }}</p>
        <p class="text-xs text-slate-400">Entradas recentes.</p>
      </div>
      <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Distribuicao de planos</p>
        <ul class="mt-3 space-y-1 text-sm text-slate-600">
          <li v-for="p in metrics?.plans || []" :key="p.plan" class="flex justify-between">
            <span class="capitalize">{{ planLabel(p.plan) }}</span>
            <span class="font-semibold">{{ p.count }}</span>
          </li>
          <li v-if="!(metrics?.plans?.length)" class="text-xs text-slate-400">Sem dados ainda.</li>
        </ul>
      </div>
    </section>

    <section class="grid gap-4 lg:grid-cols-3">
      <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100 lg:col-span-2">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Novos usuarios ({{ days }}d)</h2>
            <p class="text-sm text-slate-500">Entradas diárias.</p>
          </div>
        </div>
        <div class="mt-4 h-64 rounded-xl bg-slate-50 p-4">
          <div v-if="metrics?.new_users_timeseries?.length" class="flex h-full items-end gap-3">
            <div
              v-for="point in metrics.new_users_timeseries"
              :key="point.label"
              class="flex-1 rounded-2xl bg-white p-2 text-center shadow-sm"
            >
              <div class="mx-auto w-8 rounded-xl bg-gradient-to-t from-emerald-200 to-emerald-500" :style="{ height: Math.min(point.value * 10 + 10, 140) + 'px' }"></div>
              <p class="mt-2 text-xs text-slate-500">{{ point.label }}</p>
              <p class="text-sm font-semibold text-slate-900">{{ point.value }}</p>
            </div>
          </div>
          <div class="flex h-full items-center justify-center text-sm text-slate-500" v-else>Sem dados no periodo.</div>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
        <h3 class="text-sm font-semibold text-slate-900">Resumo geral</h3>
        <ul class="mt-3 space-y-3 text-sm text-slate-700">
          <li class="flex items-center justify-between">
            <span>Usuarios ativos</span>
            <span class="font-semibold">{{ metrics?.total_users ?? "--" }}</span>
          </li>
          <li class="flex items-center justify-between">
            <span>Agencias</span>
            <span class="font-semibold">{{ metrics?.total_agencies ?? "--" }}</span>
          </li>
          <li class="flex items-center justify-between">
            <span>Paginas publicadas</span>
            <span class="font-semibold">{{ metrics?.published_pages ?? "--" }}</span>
          </li>
        </ul>
      </div>
    </section>

    <section class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
      <div class="flex items-center justify-between">
        <div>
          <h2 :class="['text-lg font-semibold', premiumMode ? 'text-white' : 'text-slate-900']">Usuarios</h2>
          <p :class="['text-sm', premiumMode ? 'text-white/60' : 'text-slate-500']">Plano, validade e data de entrada.</p>
        </div>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm" :class="tableRowDivider">
          <thead :class="tableHeaderClass">
            <tr>
              <th class="px-3 py-2">Nome</th>
              <th class="px-3 py-2">Email</th>
              <th class="px-3 py-2">Plano</th>
              <th class="px-3 py-2">Validade</th>
              <th class="px-3 py-2">Entrada</th>
              <th class="px-3 py-2">Superuser</th>
              <th class="px-3 py-2 text-right">Trial 7 dias</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="u in metrics?.users || []" :key="u.id" class="text-slate-800">
              <td class="px-3 py-2" :class="premiumMode ? 'text-white' : 'text-slate-800'">{{ u.name }}</td>
              <td class="px-3 py-2" :class="premiumMode ? 'text-white/80' : 'text-slate-800'">{{ u.email }}</td>
              <td class="px-3 py-2 capitalize" :class="premiumMode ? 'text-white' : 'text-slate-800'">
                {{ planLabel(u.plan) }}
                <span
                  v-if="u.trial_plan"
                  class="ml-2 inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-700"
                >
                  Trial até {{ formatDate(u.trial_ends_at) }}
                </span>
              </td>
              <td class="px-3 py-2">{{ formatDate(u.valid_until) }}</td>
              <td class="px-3 py-2">{{ formatDate(u.created_at) }}</td>
              <td class="px-3 py-2">{{ u.is_superuser ? "Sim" : "Nao" }}</td>
              <td class="px-3 py-2 text-right">
              <button
                v-if="!u.is_superuser"
                :class="[
                  'rounded-full border px-3 py-1 text-xs font-semibold transition disabled:opacity-60',
                  premiumMode ? 'border-white/30 text-white hover:bg-white/10' : 'border-slate-200 text-slate-700 hover:bg-emerald-50 hover:text-emerald-700'
                ]"
                :disabled="granting === u.id || Boolean(u.trial_plan)"
                @click="openTrialDialog(u)"
              >
                {{ u.trial_plan ? "Trial ativo" : "Liberar 7 dias" }}
              </button>
            </td>
          </tr>
            <tr v-if="!metrics?.users?.length">
              <td colspan="7" :class="['px-3 py-4 text-center', premiumMode ? 'text-white/60' : 'text-slate-500']">Nenhum usuario encontrado.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid gap-4 lg:grid-cols-2">
      <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
        <div class="flex items-center justify-between">
          <div>
            <h2 :class="['text-lg font-semibold', premiumMode ? 'text-white' : 'text-slate-900']">Agencias recentes</h2>
            <p :class="['text-sm', premiumMode ? 'text-white/60' : 'text-slate-500']">Últimos cadastros com volume de páginas.</p>
          </div>
        </div>
        <div class="mt-4 overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-slate-600">
              <tr>
                <th class="px-3 py-2">Agencia</th>
                <th class="px-3 py-2">Slug</th>
                <th class="px-3 py-2">Paginas</th>
                <th class="px-3 py-2">Criada em</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="agency in metrics?.agencies || []" :key="agency.id" :class="premiumMode ? 'text-white' : 'text-slate-800'">
                <td class="px-3 py-2 font-semibold">{{ agency.name }}</td>
                <td class="px-3 py-2 text-xs" :class="premiumMode ? 'text-white/70' : 'text-slate-500'">{{ agency.slug }}</td>
                <td class="px-3 py-2">{{ agency.pages_count }}</td>
                <td class="px-3 py-2">{{ formatDate(agency.created_at) }}</td>
              </tr>
              <tr v-if="!metrics?.agencies?.length">
                <td colspan="4" :class="['px-3 py-4 text-center', premiumMode ? 'text-white/60' : 'text-slate-500']">Nenhuma agencia cadastrada.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
        <div class="flex items-center justify-between">
          <div>
            <h2 :class="['text-lg font-semibold', premiumMode ? 'text-white' : 'text-slate-900']">Paginas recentes</h2>
            <p :class="['text-sm', premiumMode ? 'text-white/60' : 'text-slate-500']">Últimas criações/publicações.</p>
          </div>
        </div>
        <div class="mt-4 overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-slate-600">
              <tr>
                <th class="px-3 py-2">Titulo</th>
                <th class="px-3 py-2">Agencia</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2">Criada</th>
                <th class="px-3 py-2">Publicada</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="page in metrics?.pages || []" :key="page.id" :class="premiumMode ? 'text-white' : 'text-slate-800'">
                <td class="px-3 py-2 font-semibold">{{ page.title }}</td>
                <td class="px-3 py-2">{{ page.agency_name }}</td>
                <td
                  class="px-3 py-2 capitalize"
                  :class="page.status === 'published' ? (premiumMode ? 'text-emerald-300' : 'text-emerald-600') : premiumMode ? 'text-white/60' : 'text-slate-500'"
                >
                  {{ page.status }}
                </td>
                <td class="px-3 py-2">{{ formatDate(page.created_at) }}</td>
                <td class="px-3 py-2">{{ formatDate(page.published_at) }}</td>
              </tr>
              <tr v-if="!metrics?.pages?.length">
                <td colspan="5" :class="['px-3 py-4 text-center', premiumMode ? 'text-white/60' : 'text-slate-500']">Nenhuma página recente.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
  <transition name="fade">
    <div
      v-if="snackbar?.open"
      class="fixed bottom-6 right-6 z-50 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-2xl"
    >
      {{ snackbar.text }}
    </div>
  </transition>

  <transition name="fade">
    <div
      v-if="trialDialog.open && trialDialog.user"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
    >
      <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Upgrade exclusivo</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">Liberar 7 dias do plano {{ planLabels.infinity }}</h2>
        <div class="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
          <p class="font-semibold text-slate-900">{{ trialDialog.user.name }}</p>
          <p class="text-xs text-slate-500">{{ trialDialog.user.email }}</p>
          <div class="mt-3 grid grid-cols-2 gap-3 text-xs">
            <div class="rounded-xl bg-white p-3 shadow-sm">
              <p class="text-slate-500">Plano atual</p>
              <p class="text-base font-semibold capitalize">{{ planLabel(trialDialog.user.plan) }}</p>
            </div>
            <div class="rounded-xl bg-white p-3 shadow-sm">
              <p class="text-slate-500">Validade atual</p>
              <p class="text-base font-semibold">{{ formatDate(trialDialog.user.valid_until) }}</p>
            </div>
          </div>
        </div>
        <p class="mt-5 text-sm text-slate-600">
          O usuário receberá acesso total ao plano {{ planLabels.infinity }} por 7 dias. Enviaremos alertas no painel dele para aproveitar o período promocional.
        </p>
        <div class="mt-6 flex justify-end gap-3">
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            @click="closeTrialDialog"
          >
            Cancelar
          </button>
          <button
            class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            :disabled="granting === trialDialog.user.id"
            @click="grantTrial"
          >
            {{ granting === trialDialog.user.id ? "Processando..." : "Liberar agora" }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, computed } from "vue";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { getPlanLabel, planLabels } from "../../utils/planLabels";

interface Metrics {
  total_users: number;
  total_agencies: number;
  total_pages: number;
  published_pages: number;
  mrr: number;
  new_users_last_days: number;
  plans: { plan: string; count: number }[];
  new_users_timeseries: { label: string; value: number }[];
  users: {
    id: number;
    name: string;
    email: string;
    plan: string;
    is_superuser: boolean;
    created_at?: string;
    valid_until?: string;
    trial_plan?: string | null;
    trial_ends_at?: string | null;
  }[];
  agencies: {
    id: number;
    name: string;
    slug: string;
    created_at?: string;
    pages_count: number;
  }[];
  pages: {
    id: number;
    title: string;
    agency_name: string;
    status: string;
    created_at?: string;
    published_at?: string;
  }[];
}

const days = ref<"7" | "30" | "90">("30");
const metrics = ref<Metrics | null>(null);
const error = ref("");
const auth = useAuthStore();
const granting = ref<number | null>(null);
const snackbar = ref<{ open: boolean; text: string } | null>(null);
const trialDialog = ref<{ open: boolean; user: any | null }>({ open: false, user: null });

const loadMetrics = async () => {
  error.value = "";
  try {
    const res = await api.get("/admin/metrics", { params: { days: days.value } });
    metrics.value = res.data;
  } catch (err: any) {
    metrics.value = null;
    if (err?.response?.status === 403) {
      error.value = "Acesso restrito a administradores.";
    } else {
      error.value = "Nao foi possivel carregar os dados.";
    }
  }
};

const formatDate = (val?: string) => {
  if (!val) return "--";
  const d = new Date(val);
  if (isNaN(d.getTime())) return "--";
  return d.toLocaleDateString();
};

const exportPdf = () => {
  if (!metrics.value) return;
  const doc = new jsPDF("p", "mm", "a4");
  const margin = 14;
  const lineHeight = 8;
  let cursor = margin;

  doc.setFillColor(22, 27, 34);
  doc.rect(0, 0, 210, 40, "F");
  doc.setTextColor("#ffffff");
  doc.setFontSize(18);
  doc.text("Visão Gerencial · Relatório Premium", margin, cursor);
  cursor += lineHeight;
  doc.setFontSize(11);
  doc.text(`Período: últimos ${days.value} dias`, margin, cursor);
  cursor += lineHeight;
  doc.text(`Emitido em ${new Date().toLocaleString()}`, margin, cursor);
  cursor = 50;

  doc.setTextColor("#111111");
  doc.setFontSize(14);
  doc.text("KPIs principais", margin, cursor);
  cursor += lineHeight;

  const KPI_ROWS = [
    ["Usuários ativos", metrics.value.total_users ?? "--"],
    ["Agências", metrics.value.total_agencies ?? "--"],
    ["Páginas totais", metrics.value.total_pages ?? "--"],
    ["Páginas publicadas", metrics.value.published_pages ?? "--"],
    ["MRR estimado", `R$ ${(metrics.value.mrr ?? 0).toFixed(2)}`],
    ["Novos usuários (período)", metrics.value.new_users_last_days ?? "--"]
  ];
  autoTable(doc, {
    startY: cursor,
    head: [["Indicador", "Valor"]],
    body: KPI_ROWS,
    theme: "striped",
    styles: { fontSize: 10, cellPadding: 3 },
    headStyles: { fillColor: [67, 56, 202], textColor: 255 }
  });
  cursor = (doc as any).lastAutoTable.finalY + 10;

  doc.setFontSize(14);
  doc.text("Distribuição de planos", margin, cursor);
  cursor += lineHeight;
  const planRows = (metrics.value.plans || []).map(plan => [planLabel(plan.plan), String(plan.count)]);
  autoTable(doc, {
    startY: cursor,
    head: [["Plano", "Total"]],
    body: planRows,
    theme: "grid",
    styles: { fontSize: 10, cellPadding: 3 },
    headStyles: { fillColor: [14, 116, 144], textColor: 255 }
  });
  cursor = (doc as any).lastAutoTable.finalY + 10;

  doc.setFontSize(14);
  doc.text("Usuários · Trial e planos", margin, cursor);
  cursor += lineHeight;
  const userRows = (metrics.value.users || []).slice(0, 12).map(u => [
    u.name,
    u.email,
    planLabel(u.plan),
    u.trial_plan ? `Trial até ${formatDate(u.trial_ends_at)}` : "-",
    formatDate(u.created_at)
  ]);
  autoTable(doc, {
    startY: cursor,
    head: [["Nome", "Email", "Plano", "Trial", "Entrada"]],
    body: userRows,
    theme: "grid",
    styles: { fontSize: 9, cellPadding: 2 },
    headStyles: { fillColor: [15, 118, 110], textColor: 255 }
  });

  doc.save(`relatorio-admin-${new Date().toISOString().slice(0, 10)}.pdf`);
};

const openTrialDialog = (user: Metrics["users"][number]) => {
  trialDialog.value = { open: true, user };
};

const closeTrialDialog = () => {
  trialDialog.value = { open: false, user: null };
};

const grantTrial = async () => {
  if (!auth.user?.is_superuser || !trialDialog.value.user) return;
  granting.value = trialDialog.value.user.id;
  error.value = "";
  try {
    await api.post(`/admin/users/${trialDialog.value.user.id}/grant-trial`, { plan: "infinity", days: 7 });
    snackbar.value = { open: true, text: "Trial premium liberado por 7 dias." };
    closeTrialDialog();
    await loadMetrics();
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível liberar o trial para este usuário.";
  } finally {
    granting.value = null;
    setTimeout(() => {
      snackbar.value = null;
    }, 3000);
  }
};

const planLabel = (plan: string) => {
  if (!plan) return "Indefinido";
  const lower = plan.toLowerCase();
  if (lower.includes("trial")) return plan;
  return getPlanLabel(plan);
};

onMounted(async () => {
  if (!auth.user && auth.token) {
    await auth.fetchProfile();
  }
  await loadMetrics();
});

watch(days, loadMetrics);
</script>

<style scoped>
.premium-panel {
  background: radial-gradient(circle at top, #101828 0%, #05060f 60%);
  min-height: 100vh;
  color: #f8fafc;
  border-radius: 0;
  margin: 0;
  padding: 0;
}

.premium-panel .premium-card {
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.03);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(14px);
}
</style>
