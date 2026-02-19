<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <header class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm uppercase tracking-[0.25em] text-slate-500">Painel</p>
        <h1 class="text-3xl font-bold text-slate-900">Ola, {{ auth.user?.name || "agente" }}</h1>
        <p class="text-sm text-slate-500">Visao geral das paginas, integracoes e performance.</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <select v-model="period" class="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
          <option value="7">Últimos 7 dias</option>
          <option value="30">Últimos 30 dias</option>
          <option value="90">Últimos 90 dias</option>
        </select>
        <button @click="auth.logout()" class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100">
          Sair
        </button>
      </div>
    </header>
    <div
      v-if="trialInfo"
      class="flex flex-col gap-3 rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-5 text-slate-800 shadow-sm md:flex-row md:items-center md:justify-between"
    >
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-600">Trial ativo</p>
        <p class="text-base font-semibold">
          Você está aproveitando o plano {{ trialInfo.plan }} até {{ trialInfo.endsAt }}.
        </p>
        <p class="text-sm text-slate-600">Contrate agora para manter os recursos premium sem interrupção.</p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-full bg-amber-600 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-amber-500"
        @click="goPlans"
      >
        Ativar plano
      </button>
    </div>

    <!-- KPIs -->
    <section class="grid gap-4 md:grid-cols-4">
      <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100">
        <p class="text-sm text-slate-500">Paginas</p>
        <div class="mt-2 flex items-end justify-between">
          <p class="text-3xl font-bold text-slate-900">{{ pagesCount }}</p>
          <span class="text-xs font-semibold text-emerald-600" v-if="trend?.pages !== null">+{{ trend.pages }}%</span>
          <span class="text-xs text-slate-400" v-else>--</span>
        </div>
      </div>
      <div class="relative">
        <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100" :class="{ 'blur-sm pointer-events-none': isFree }">
          <p class="text-sm text-slate-500">Integracoes (pixels)</p>
          <div class="mt-2 flex items-end justify-between">
            <p class="text-3xl font-bold text-slate-900">{{ integrationsCount }}</p>
            <span class="text-xs font-semibold text-emerald-600" v-if="trend?.integrations !== null">+{{ trend.integrations }}%</span>
            <span class="text-xs text-slate-400" v-else>--</span>
          </div>
        </div>
        <div v-if="isFree" class="absolute inset-0 flex items-center justify-center">
          <button
            @click="goPlans"
            class="rounded-full bg-white/95 px-4 py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-white"
          >
            Faca upgrade para ter acesso
          </button>
        </div>
      </div>
      <div class="relative">
        <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100" :class="{ 'blur-sm pointer-events-none': isFree }">
          <p class="text-sm text-slate-500">Visitas ({{ period }}d)</p>
          <div class="mt-2 flex items-end justify-between">
            <p class="text-3xl font-bold text-slate-900">{{ stats.visits ?? "--" }}</p>
            <span class="text-xs font-semibold text-emerald-600" v-if="trend?.visits !== null">+{{ trend.visits }}%</span>
            <span class="text-xs text-slate-400" v-else>--</span>
          </div>
        </div>
        <div v-if="isFree" class="absolute inset-0 flex items-center justify-center">
          <button
            @click="goPlans"
            class="rounded-full bg-white/95 px-4 py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-white"
          >
            Faca upgrade para ter acesso
          </button>
        </div>
      </div>
      <div class="relative">
        <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100" :class="{ 'blur-sm pointer-events-none': isFree }">
          <p class="text-sm text-slate-500">Cliques WhatsApp ({{ period }}d)</p>
          <div class="mt-2 flex items-end justify-between">
            <p class="text-3xl font-bold text-slate-900">{{ stats.whatsapp ?? "--" }}</p>
            <span class="text-xs font-semibold text-emerald-600" v-if="trend?.whatsapp !== null">+{{ trend.whatsapp }}%</span>
            <span class="text-xs text-slate-400" v-else>--</span>
          </div>
        </div>
        <div v-if="isFree" class="absolute inset-0 flex items-center justify-center">
          <button
            @click="goPlans"
            class="rounded-full bg-white/95 px-4 py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-white"
          >
            Faca upgrade para ter acesso
          </button>
        </div>
      </div>
    </section>

    <section class="grid gap-4 lg:grid-cols-3">
      <!-- Grǭfico de performance -->
      <div class="relative lg:col-span-2">
        <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100" :class="{ 'blur-sm pointer-events-none': isFree }">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Performance geral</h2>
              <p class="text-sm text-slate-500">Visitas, cliques e conversoes no periodo.</p>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <span class="inline-flex items-center gap-1 text-slate-700"><span class="h-2 w-2 rounded-full bg-sky-500"></span>Visitas</span>
              <span class="inline-flex items-center gap-1 text-slate-700"><span class="h-2 w-2 rounded-full bg-emerald-500"></span>Cliques</span>
              <span class="inline-flex items-center gap-1 text-slate-700"><span class="h-2 w-2 rounded-full bg-indigo-500"></span>Conversoes</span>
            </div>
          </div>
          <div class="mt-4 h-64 rounded-xl bg-slate-50 p-4">
            <div v-if="chartData.length" class="flex h-full items-end gap-2">
              <div
                v-for="point in chartData"
                :key="point.label"
                class="flex-1 space-y-1 rounded-lg bg-white p-2 shadow-sm"
              >
                <div class="w-full rounded-md bg-gradient-to-t from-sky-200 to-sky-500" :style="{ height: Math.min(point.visits, 120) + 'px' }"></div>
                <div class="w-full rounded-md bg-gradient-to-t from-emerald-200 to-emerald-500" :style="{ height: Math.min(point.clicks, 120) + 'px' }"></div>
                <div class="w-full rounded-md bg-gradient-to-t from-indigo-200 to-indigo-500" :style="{ height: Math.min(point.conversions, 120) + 'px' }"></div>
                <p class="text-center text-xs text-slate-500">{{ point.label }}</p>
              </div>
            </div>
            <div v-else class="flex h-full items-center justify-center text-sm text-slate-500">Sem dados de serie temporal.</div>
          </div>
        </div>
        <div v-if="isFree" class="absolute inset-0 flex items-center justify-center">
          <button
            @click="goPlans"
            class="rounded-full bg-white/95 px-4 py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-white"
          >
            Faca upgrade para ter acesso
          </button>
        </div>
      </div>

      <!-- DistribuiÇðo e metas -->
      <div class="space-y-4">
        <div class="relative">
          <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100" :class="{ 'blur-sm pointer-events-none': isFree }">
            <h3 class="text-sm font-semibold text-slate-900">Conversao por canal</h3>
            <div v-if="breakdown" class="mt-3 space-y-3 text-sm text-slate-700">
              <div class="flex items-center justify-between" v-for="item in breakdownList" :key="item.name">
                <span>{{ item.name }}</span>
                <span class="font-semibold">{{ item.value }}%</span>
              </div>
            </div>
            <div v-else class="mt-3 text-sm text-slate-500">Sem dados de canais.</div>
          </div>
          <div v-if="isFree" class="absolute inset-0 flex items-center justify-center">
            <button
              @click="goPlans"
              class="rounded-full bg-white/95 px-4 py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-white"
            >
              Faca upgrade para ter acesso
            </button>
          </div>
        </div>

        <div class="relative">
          <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100" :class="{ 'blur-sm pointer-events-none': isFree }">
            <h3 class="text-sm font-semibold text-slate-900">Metas rapidas</h3>
            <ul class="mt-3 space-y-2 text-sm text-slate-700">
              <li>· Publicar +{{ Math.max(1, Math.ceil(pagesCount * 0.3)) }} paginas este mes</li>
              <li>· Configurar pixels em 100% das paginas</li>
              <li>· Aumentar conversoes em +15%</li>
            </ul>
          </div>
          <div v-if="isFree" class="absolute inset-0 flex items-center justify-center">
            <button
              @click="goPlans"
              class="rounded-full bg-white/95 px-4 py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-white"
            >
              Faca upgrade para ter acesso
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-slate-900">Roteiros recentes</h2>
          <p class="text-sm text-slate-500">Gerencie suas paginas e acompanhe o status.</p>
        </div>
        <router-link to="/admin/pages" class="text-brand hover:text-brand-dark">Ver todos</router-link>
      </div>
      <div class="mt-4 divide-y divide-slate-100">
        <div v-for="page in pages.slice(0, 6)" :key="page.id" class="flex items-center justify-between py-3">
          <div>
            <p class="text-base font-semibold text-slate-900">{{ page.title }}</p>
            <p class="text-sm text-slate-500">{{ page.status === "published" ? "Publicada" : "Rascunho" }}</p>
          </div>
          <router-link :to="`/admin/pages/${page.id}/edit`" class="text-sm font-semibold text-brand hover:text-brand-dark">Editar</router-link>
        </div>
        <p v-if="pages.length === 0" class="py-4 text-sm text-slate-500">Nenhum roteiro criado ainda.</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";

interface Page {
  id: number;
  title: string;
  status: string;
}

const auth = useAuthStore();
const agencyStore = useAgencyStore();
const router = useRouter();
const pages = ref<Page[]>([]);
const pagesCount = ref(0);
const integrationsCount = ref(0);
const isFree = computed(() => (auth.user?.plan || "free") === "free");
const trialInfo = computed(() => {
  const tPlan = auth.user?.trial_plan;
  const endsAt = auth.user?.trial_ends_at;
  if (!tPlan || !endsAt) return null;
  const planLabel = tPlan.charAt(0).toUpperCase() + tPlan.slice(1);
  const date = new Date(endsAt);
  return {
    plan: planLabel,
    endsAt: date.toLocaleDateString("pt-BR")
  };
});
const stats = reactive<{ visits: number | null; whatsapp: number | null }>({ visits: null, whatsapp: null });
const period = ref<"7" | "30" | "90">("7");
const trend = reactive<{ pages: number | null; integrations: number | null; visits: number | null; whatsapp: number | null }>({
  pages: null,
  integrations: null,
  visits: null,
  whatsapp: null
});

const chartData = computed(() => {
  if (chartDataRaw.value.length) return chartDataRaw.value;
  return [];
});

const breakdownData = ref<{ organic?: number; meta?: number; google?: number; referral?: number } | null>(null);
const breakdown = computed(() => breakdownData.value);
const breakdownList = computed(() => {
  if (!breakdownData.value) return [];
  return [
    { name: "Organico", value: breakdownData.value.organic ?? 0 },
    { name: "Meta Ads", value: breakdownData.value.meta ?? 0 },
    { name: "Google Ads", value: breakdownData.value.google ?? 0 },
    { name: "Referral", value: breakdownData.value.referral ?? 0 }
  ];
});

const fetchData = async () => {
  await agencyStore.loadAgencies();
  if (!agencyStore.currentAgencyId) return;
  const agencyId = agencyStore.currentAgencyId;
  const res = await api.get<Page[]>("/pages", { params: { agency_id: agencyId } });
  pages.value = res.data;
  pagesCount.value = res.data.length;
  // Pixels cadastrados como integraÇõÇæes
  try {
    const pix = await api.get("/pixels/");
    integrationsCount.value = Array.isArray(pix.data) ? pix.data.length : 0;
  } catch {
    integrationsCount.value = 0;
  }
  // Tenta buscar dados reais de stats, senão deixa como null
  try {
    const s = await api.get("/stats/overview", { params: { days: period.value, agency_id: agencyId } });
    stats.visits = s.data?.visits ?? null;
    stats.whatsapp = s.data?.whatsapp ?? null;
    trend.pages = s.data?.trend?.pages ?? null;
    trend.integrations = s.data?.trend?.integrations ?? null;
    trend.visits = s.data?.trend?.visits ?? null;
    trend.whatsapp = s.data?.trend?.whatsapp ?? null;
    if (s.data?.breakdown) breakdownData.value = s.data.breakdown;
    if (Array.isArray(s.data?.timeseries)) {
      chartDataRaw.value = s.data.timeseries;
    }
  } catch {
    stats.visits = null;
    stats.whatsapp = null;
    trend.pages = trend.integrations = trend.visits = trend.whatsapp = null;
    breakdownData.value = null;
    chartDataRaw.value = [];
  }
};

onMounted(fetchData);

const chartDataRaw = ref<{ label: string; visits: number; clicks: number; conversions: number }[]>([]);
watch(period, fetchData);

const goPlans = () => {
  router.push("/admin/planos");
};
</script>
