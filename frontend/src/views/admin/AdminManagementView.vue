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
          <h2 class="text-lg font-semibold text-slate-900">Usuarios</h2>
          <p class="text-sm text-slate-500">Plano, validade e data de entrada.</p>
        </div>
      </div>
      <div class="mt-4 grid gap-4 md:grid-cols-3">
        <div class="md:col-span-1">
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Buscar</label>
          <input
            v-model="userSearch"
            type="text"
            placeholder="Nome ou email"
            class="mt-1 w-full rounded-full border border-slate-200 px-4 py-2 text-sm focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Plano</label>
          <select
            v-model="userPlanFilter"
            class="mt-1 w-full rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none"
          >
            <option value="all">Todos os planos</option>
            <option v-for="plan in userPlanOptions" :key="plan" :value="plan">{{ planLabel(plan) }}</option>
          </select>
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Agência</label>
          <select
            v-model="userAgencyFilter"
            class="mt-1 w-full rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none"
          >
            <option value="all">Todas</option>
            <option value="__none">Sem agência</option>
            <option v-for="agency in userAgencyOptions" :key="agency" :value="agency">{{ agency }}</option>
          </select>
        </div>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm text-slate-800 divide-y divide-slate-100 interactive-table">
          <thead class="bg-slate-50 text-left text-slate-600">
            <tr>
              <th class="px-3 py-2 text-left">Nome</th>
              <th class="px-3 py-2 text-left">Agência</th>
              <th class="px-3 py-2 text-left">Qtd páginas ativas</th>
              <th class="px-3 py-2 text-left">Plano</th>
              <th class="px-3 py-2 text-left">Validade</th>
              <th class="px-3 py-2 text-left">Entrada</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <template v-for="u in filteredUsers" :key="u.id">
              <tr
                class="transition hover:bg-slate-50/70"
                @click="toggleUserRow(u.id)"
              >
                <td class="px-3 py-3">
                  <div class="flex items-start gap-3">
                    <button
                      type="button"
                      class="mt-1 rounded-full border border-slate-300 p-1 text-xs transition hover:bg-slate-100"
                      @click.stop="toggleUserRow(u.id)"
                    >
                      <span :class="expandedUser === u.id ? 'rotate-90 inline-block transition' : 'inline-block transition'">▶</span>
                    </button>
                    <div>
                      <p class="font-semibold text-slate-900">{{ u.name }}</p>
                      <p class="text-xs text-slate-500">{{ u.email }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-3 py-3">
                  <span class="text-slate-800">{{ u.agency_name || 'Sem agência' }}</span>
                </td>
                <td class="px-3 py-3 font-semibold text-slate-900">
                  {{ u.active_pages ?? 0 }}
                </td>
                <td class="px-3 py-3 capitalize">
                  <span class="text-slate-800">{{ planLabel(u.plan) }}</span>
                  <span
                    v-if="u.trial_plan"
                    class="ml-2 inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-700"
                  >
                    Trial até {{ formatDate(u.trial_ends_at) }}
                  </span>
                </td>
                <td class="px-3 py-3">{{ formatDate(u.valid_until) }}</td>
                <td class="px-3 py-3">{{ formatDate(u.created_at) }}</td>
              </tr>
              <tr v-if="expandedUser === u.id">
                <td colspan="6" class="px-3 pb-4">
                  <div
                    class="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 text-sm text-slate-800 shadow-inner"
                  >
                    <div class="grid gap-4 md:grid-cols-2">
                      <div>
                        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Contato</p>
                        <p class="mt-1 font-semibold no-caret">{{ u.name }}</p>
                        <p class="text-xs text-slate-500 no-caret">{{ u.email }}</p>
                        <p class="text-xs text-slate-500 no-caret">{{ u.whatsapp || 'Sem telefone' }}</p>
                      </div>
                      <div>
                        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Agência</p>
                        <p class="mt-1 font-semibold">{{ u.agency_name || 'Não vinculada' }}</p>
                        <p class="text-xs text-slate-500">
                          {{ u.active_pages ?? 0 }} páginas publicadas · Plano {{ planLabel(u.plan) }}
                        </p>
                      </div>
                    </div>
                    <div class="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        v-if="!u.is_superuser"
                        :class="[
                          'rounded-full border px-4 py-2 text-xs font-semibold text-slate-700 transition disabled:opacity-60',
                          'border-slate-200 hover:bg-emerald-50 hover:text-emerald-700'
                        ]"
                        :disabled="granting === u.id || Boolean(u.trial_plan)"
                        @click.stop="openTrialDialog(u)"
                      >
                        {{ u.trial_plan ? 'Trial ativo' : 'Liberar 7 dias' }}
                      </button>
                      <span v-if="u.is_superuser" class="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-700">Superuser</span>
                    </div>
                    <div class="mt-6">
                      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Páginas publicadas</p>
                      <div v-if="u.published_pages?.length" class="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
                        <table class="min-w-full divide-y divide-slate-100 text-xs text-slate-700 interactive-table">
                          <thead class="bg-slate-50 text-left text-slate-500">
                            <tr>
                              <th class="px-3 py-2">Título</th>
                              <th class="px-3 py-2">Slug</th>
                              <th class="px-3 py-2 text-right">Ações</th>
                            </tr>
                          </thead>
                          <tbody class="divide-y divide-slate-100">
                            <tr v-for="page in u.published_pages" :key="page.id">
                              <td class="px-3 py-2 font-semibold text-slate-900">{{ page.title }}</td>
                              <td class="px-3 py-2 text-[11px] text-slate-500">/{{ page.slug }}</td>
                              <td class="px-3 py-2">
                                <div class="flex justify-end gap-2">
                                  <button
                                    class="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-700 transition hover:bg-slate-100"
                                    @click.stop="viewPublishedPage(page)"
                                  >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.5 4.5h6m0 0v6m0-6L12 12m4.5 7.5h-9a3 3 0 01-3-3v-9"/>
                                    </svg>
                                    Visualizar
                                  </button>
                                  <button
                                    class="inline-flex items-center gap-1 rounded-full border border-slate-900/20 bg-slate-900/90 px-3 py-1 text-[11px] font-semibold text-white transition hover:bg-slate-900 disabled:opacity-60"
                                    :disabled="savingPageId === page.id || !agencyStore.currentAgencyId"
                                    @click.stop="clonePublishedPage(u, page)"
                                  >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 16.5h8M8 12h8m-8-4.5h8M6 19.5h12a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H9l-3 3v10.5A1.5 1.5 0 007.5 19.5z"/>
                                    </svg>
                                    {{ savingPageId === page.id ? 'Salvando...' : 'Salvar' }}
                                  </button>
                                </div>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <p v-else class="mt-3 rounded-xl border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-500">
                        Nenhuma página publicada ainda.
                      </p>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-if="!filteredUsers.length">
              <td colspan="6" class="px-3 py-4 text-center text-slate-500">
                Nenhum usuario encontrado.
              </td>
            </tr>
          </tbody>
        </table>
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
import { useAgencyStore } from "../../store/useAgencyStore";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { getPlanLabel, planLabels } from "../../utils/planLabels";

interface MetricsUserPage {
  id: number;
  title: string;
  slug: string;
  status: string;
  agency_slug?: string | null;
}

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
    agency_id?: number | null;
    agency_name?: string | null;
    agency_slug?: string | null;
    active_pages?: number | null;
    whatsapp?: string | null;
    published_pages?: MetricsUserPage[];
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
const agencyStore = useAgencyStore();
const granting = ref<number | null>(null);
const snackbar = ref<{ open: boolean; text: string } | null>(null);
const trialDialog = ref<{ open: boolean; user: any | null }>({ open: false, user: null });
const premiumMode = computed(() => (auth.user?.plan || "").toLowerCase() === "infinity");
const userSearch = ref("");
const userPlanFilter = ref<string | "all">("all");
const userAgencyFilter = ref<string>("all");
const expandedUser = ref<number | null>(null);
const savingPageId = ref<number | null>(null);

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

const showSnackbar = (text: string) => {
  snackbar.value = { open: true, text };
  setTimeout(() => {
    snackbar.value = null;
  }, 3000);
};

const viewPublishedPage = (page: MetricsUserPage) => {
  if (!page.agency_slug) {
    showSnackbar("Página sem agência vinculada.");
    return;
  }
  const url = `/${page.agency_slug}/${page.slug}`;
  window.open(url, "_blank", "noopener,noreferrer");
};

const clonePublishedPage = async (user: Metrics["users"][number], page: MetricsUserPage) => {
  if (!agencyStore.currentAgencyId) {
    showSnackbar("Selecione uma agência para salvar a página.");
    return;
  }
  savingPageId.value = page.id;
  try {
    await api.post(`/admin/pages/${page.id}/clone`, {
      target_agency_id: agencyStore.currentAgencyId,
      title: `${page.title} - ${user.name}`.trim()
    });
    showSnackbar("Página salva na agência selecionada.");
  } catch (err) {
    console.error(err);
    showSnackbar("Não foi possível salvar esta página.");
  } finally {
    savingPageId.value = null;
  }
};

const userPlanOptions = computed(() => {
  const plans = new Set<string>();
  metrics.value?.users?.forEach(user => {
    if (user.plan) plans.add(user.plan);
  });
  return Array.from(plans).sort();
});

const userAgencyOptions = computed(() => {
  const agencies = new Set<string>();
  metrics.value?.users?.forEach(user => {
    if (user.agency_name) agencies.add(user.agency_name);
  });
  return Array.from(agencies).sort();
});

const filteredUsers = computed(() => {
  const list = metrics.value?.users || [];
  const search = userSearch.value.trim().toLowerCase();
  return list
    .filter(user => {
      const matchesSearch =
        !search ||
        [user.name, user.email, user.agency_name]
          .filter(Boolean)
          .some(field => field!.toLowerCase().includes(search));
      const matchesPlan = userPlanFilter.value === "all" || user.plan === userPlanFilter.value;
      const matchesAgency =
        userAgencyFilter.value === "all" ||
        (userAgencyFilter.value === "__none"
          ? !user.agency_name
          : user.agency_name === userAgencyFilter.value);
      return matchesSearch && matchesPlan && matchesAgency;
    })
    .sort((a, b) => {
      const aDate = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bDate = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bDate - aDate;
    });
});

const toggleUserRow = (userId: number) => {
  expandedUser.value = expandedUser.value === userId ? null : userId;
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
    showSnackbar("Trial premium liberado por 7 dias.");
    closeTrialDialog();
    await loadMetrics();
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível liberar o trial para este usuário.";
    showSnackbar("Não foi possível liberar o trial para este usuário.");
  } finally {
    granting.value = null;
  }
};

const planLabel = (plan: string) => {
  if (!plan) return "Indefinido";
  const lower = plan.toLowerCase();
  if (lower.includes("trial")) return plan;
  return getPlanLabel(plan);
};

watch([userSearch, userPlanFilter, userAgencyFilter], () => {
  expandedUser.value = null;
});

watch(metrics, () => {
  expandedUser.value = null;
});

onMounted(async () => {
  if (!auth.user && auth.token) {
    await auth.fetchProfile();
  }
  if (!agencyStore.agencies.length) {
    try {
      await agencyStore.loadAgencies();
    } catch (err) {
      console.error(err);
    }
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

.no-caret {
  user-select: none;
  caret-color: transparent;
}

.interactive-table,
.interactive-table * {
  user-select: none;
  caret-color: transparent;
}
</style>
