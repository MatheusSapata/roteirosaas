<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <header class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm uppercase tracking-[0.25em] text-slate-500">Painel</p>
        <h1 class="text-3xl font-bold text-slate-900">Olá, {{ auth.user?.name || "agente" }}</h1>
        <p class="text-sm text-slate-500">Visão geral das páginas, integrações e performance.</p>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <select v-model="period" class="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
          <option value="7">Últimos 7 dias</option>
          <option value="30">Últimos 30 dias</option>
          <option value="90">Últimos 90 dias</option>
        </select>

        <button
          @click="auth.logout()"
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
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

    <div
      v-if="isFree"
      class="rounded-2xl border border-emerald-100 bg-white p-5 shadow flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
    >
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Plano atual: Começo</p>
        <p class="mt-1 text-base font-semibold text-slate-900">Desbloqueie métricas completas e integrações.</p>
        <p class="text-sm text-slate-600">
          Faça upgrade para organizar mais roteiros, liberar as seções bloqueadas e acompanhar desempenho em tempo real.
        </p>
      </div>
      <button
        class="self-start rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500"
        @click="goPlans"
      >
        Ver planos
      </button>
    </div>

    <!-- Indicadores principais -->
    <section class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100">
        <p class="text-sm text-slate-500">Páginas</p>
        <div class="mt-2 flex items-end justify-between">
          <p class="text-3xl font-bold text-slate-900">{{ pagesCount }}</p>
          <span
            v-if="trend.pages !== null"
            class="text-xs font-semibold"
            :class="trend.pages >= 0 ? 'text-emerald-600' : 'text-rose-600'"
          >
            {{ trend.pages > 0 ? "+" : "" }}{{ trend.pages }}%
          </span>
          <span v-else class="text-xs text-slate-400">--</span>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100">
        <p class="text-sm text-slate-500">Visitas (geral)</p>
        <div class="mt-2 flex items-end justify-between">
          <p class="text-3xl font-bold text-slate-900">{{ totalVisits.toLocaleString("pt-BR") }}</p>
          <span
            v-if="trend.visits !== null"
            class="text-xs font-semibold"
            :class="trend.visits >= 0 ? 'text-emerald-600' : 'text-rose-600'"
          >
            {{ trend.visits > 0 ? "+" : "" }}{{ trend.visits }}%
          </span>
          <span v-else class="text-xs text-slate-400">--</span>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100">
        <p class="text-sm text-slate-500">Cliques (geral)</p>
        <div class="mt-2 flex items-end justify-between">
          <p class="text-3xl font-bold text-slate-900">{{ totalClicks.toLocaleString("pt-BR") }}</p>
          <span
            v-if="trend.clicks !== null"
            class="text-xs font-semibold"
            :class="trend.clicks >= 0 ? 'text-emerald-600' : 'text-rose-600'"
          >
            {{ trend.clicks > 0 ? "+" : "" }}{{ trend.clicks }}%
          </span>
          <span v-else class="text-xs text-slate-400">--</span>
        </div>
      </div>
    </section>

    <section class="space-y-4">
      <!-- Gráfico de performance -->
      <div class="relative">
        <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
          <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Performance geral</h2>
              <p class="text-sm text-slate-500">Visitas e cliques no período.</p>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-xs text-slate-600">
              <label class="font-semibold">Página:</label>
              <select
                v-model="selectedPage"
                class="rounded-lg border border-slate-200 px-3 py-1 text-sm text-slate-700"
              >
                <option value="all">Todas as publicadas</option>
                <option v-for="page in publishedPages" :key="page.id" :value="String(page.id)">
                  {{ page.title }}
                </option>
              </select>
            </div>
          </div>

          <div class="mt-4 space-y-3">
            <div
              v-if="chartPoints.length"
              class="rounded-xl bg-slate-50 p-6"
              :class="{ 'locked-blur': isFree }"
            >
              <div class="-mx-4 overflow-x-auto px-4">
                <div class="space-y-3" :style="chartContainerStyle">
                  <div class="relative" :style="{ height: chartHeight + 'px' }">
                    <svg
                      :viewBox="`0 0 ${chartWidth} ${chartHeight}`"
                      preserveAspectRatio="none"
                      class="h-full w-full"
                    >
                      <template v-for="point in chartPoints" :key="point.label">
                        <rect
                          :x="point.x - barSpacing - barWidth"
                          :y="point.yVisits"
                          :width="barWidth"
                          :height="Math.max(chartHeight - point.yVisits, 1)"
                          rx="6"
                          fill="#0ea5e9"
                          opacity="0.8"
                        />
                        <rect
                          :x="point.x + barSpacing"
                          :y="point.yClicks"
                          :width="barWidth"
                          :height="Math.max(chartHeight - point.yClicks, 1)"
                          rx="6"
                          fill="#8b5cf6"
                          opacity="0.8"
                        />
                      </template>
                    </svg>

                    <div
                      v-if="hoverPoint"
                      class="pointer-events-none absolute inset-y-0 w-px bg-slate-300"
                      :style="{ left: hoverPoint.x + 'px' }"
                    ></div>

                    <div
                      v-if="hoverPoint"
                      class="pointer-events-none absolute -translate-x-1/2 -translate-y-full rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200"
                      :style="tooltipStyle"
                    >
                      <p class="text-[11px] font-semibold text-slate-500">{{ hoverPoint.label }}</p>
                      <p class="text-slate-800">Visitas: {{ hoverPoint.visits }}</p>
                      <p class="text-slate-800">Cliques: {{ hoverPoint.clicks }}</p>
                    </div>

                    <div
                      ref="chartSurfaceRef"
                      class="absolute inset-0 cursor-crosshair"
                      @mousemove="handleChartMove"
                      @mouseleave="clearHover"
                    ></div>
                  </div>

                </div>
              </div>
            </div>

            <div v-else class="flex h-48 items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-500">
      Sem dados de série temporal.
            </div>
          </div>
        </div>

        <div v-if="isFree" class="absolute inset-x-0 bottom-4 flex justify-center">
          <button
            @click="goPlans"
            class="rounded-full bg-white/95 px-4 py-1.5 text-xs font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-white shadow"
          >
            Faça upgrade para ter acesso
          </button>
        </div>
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

type SeriesPoint = {
  label: string;
  visits: number;
  clicks: number;
  conversions: number;
};

interface ChartPoint {
  label: string;
  x: number;
  yVisits: number;
  yClicks: number;
  visits: number;
  clicks: number;
}

interface StatsTrendResponse {
  pages: number | null;
  integrations: number | null;
  visits: number | null;
  whatsapp: number | null;
  clicks: number | null;
}

interface StatsOverviewResponse {
  visits: number;
  whatsapp: number;
  cta: number;
  trend: StatsTrendResponse | null;
  timeseries: SeriesPoint[];
}

const auth = useAuthStore();
const agencyStore = useAgencyStore();
const router = useRouter();

const pages = ref<Page[]>([]);
const pagesCount = ref(0);
const selectedPage = ref<string>("all");
const totalVisits = ref(0);
const totalClicks = ref(0);

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

const period = ref<"7" | "30" | "90">("7");

const trend = reactive<{
  pages: number | null;
  visits: number | null;
  whatsapp: number | null;
  clicks: number | null;
}>({
  pages: null,
  visits: null,
  whatsapp: null,
  clicks: null,
});

const chartDataRaw = ref<SeriesPoint[]>([]);

const chartData = computed(() => {
  if (chartDataRaw.value.length) return chartDataRaw.value;
  return [];
});

const chartHeight = 280;
const pointGap = 70;
const horizontalPadding = 30;
const barWidth = 18;
const barSpacing = 10;

const chartWidth = computed(() => {
  const count = chartData.value.length;
  if (!count) return 360;
  const baseWidth = Math.max((count - 1) * pointGap, 0) + horizontalPadding * 2;
  const minWidth = count === 1 ? 200 : 360;
  return Math.max(baseWidth, minWidth);
});

const chartContainerStyle = computed(() => ({
  minWidth: `${chartWidth.value}px`,
}));

const maxMetric = computed(() => {
  if (!chartData.value.length) return 1;
  const maxValue = Math.max(
    ...chartData.value.map(point => Math.max(point.visits ?? 0, point.clicks ?? 0, 0))
  );
  return maxValue > 0 ? maxValue : 1;
});

const chartPoints = computed<ChartPoint[]>(() => {
  const maxValue = maxMetric.value || 1;
  return chartData.value.map((point, index) => {
    const x = index * pointGap + horizontalPadding;
    const visitRatio = (point.visits ?? 0) / maxValue;
    const clickRatio = (point.clicks ?? 0) / maxValue;
    return {
      label: point.label,
      x,
      yVisits: chartHeight - visitRatio * chartHeight,
      yClicks: chartHeight - clickRatio * chartHeight,
      visits: point.visits ?? 0,
      clicks: point.clicks ?? 0,
    };
  });
});

const chartSurfaceRef = ref<HTMLDivElement | null>(null);
const hoverPoint = ref<ChartPoint | null>(null);
const tooltipStyle = computed(() => {
  if (!hoverPoint.value) return {};
  const padding = 60;
  const left = Math.min(Math.max(hoverPoint.value.x, padding), chartWidth.value - padding);
  const minY = Math.min(hoverPoint.value.yVisits, hoverPoint.value.yClicks);
  const top = Math.max(minY - 40, 24);
  return { left: `${left}px`, top: `${top}px` };
});

const handleChartMove = (event: MouseEvent) => {
  if (!chartSurfaceRef.value || !chartPoints.value.length) return;
  const rect = chartSurfaceRef.value.getBoundingClientRect();
  const offsetX = event.clientX - rect.left;
  let nearest = chartPoints.value[0];
  let minDistance = Math.abs(nearest.x - offsetX);
  for (const point of chartPoints.value) {
    const distance = Math.abs(point.x - offsetX);
    if (distance < minDistance) {
      nearest = point;
      minDistance = distance;
    }
  }
  hoverPoint.value = nearest;
};

const clearHover = () => {
  hoverPoint.value = null;
};

const publishedPages = computed(() =>
  pages.value.filter(page => page.status?.toLowerCase() === "published")
);

const fetchData = async () => {
  await agencyStore.loadAgencies();
  if (!agencyStore.currentAgencyId) return;

  const agencyId = agencyStore.currentAgencyId;

  const res = await api.get<Page[]>("/pages", { params: { agency_id: agencyId } });
  pages.value = res.data;
  pagesCount.value = res.data.length;

  try {
    const params: Record<string, string | number> = { days: period.value, agency_id: agencyId };
    if (selectedPage.value !== "all") {
      params.page_id = Number(selectedPage.value);
    }
    const s = await api.get<StatsOverviewResponse>("/stats/overview", { params });
    trend.pages = s.data?.trend?.pages ?? null;
    trend.visits = s.data?.trend?.visits ?? null;
    trend.whatsapp = s.data?.trend?.whatsapp ?? null;
    trend.clicks = s.data?.trend?.clicks ?? null;
    totalVisits.value = s.data?.visits ?? 0;
    totalClicks.value = (s.data?.whatsapp ?? 0) + (s.data?.cta ?? 0);
    if (Array.isArray(s.data?.timeseries)) {
      chartDataRaw.value = s.data.timeseries as SeriesPoint[];
    } else {
      chartDataRaw.value = [];
    }
    hoverPoint.value = null;
  } catch {
    trend.pages = null;
    trend.visits = null;
    trend.whatsapp = null;
    trend.clicks = null;
    totalVisits.value = 0;
    totalClicks.value = 0;
    chartDataRaw.value = [];
    hoverPoint.value = null;
  }
};

watch(
  () => publishedPages.value,
  pagesList => {
    if (selectedPage.value !== "all" && !pagesList.some(p => String(p.id) === selectedPage.value)) {
      selectedPage.value = "all";
    }
  }
);

onMounted(fetchData);
watch([period, selectedPage], fetchData);

const goPlans = () => {
  router.push("/admin/planos");
};
</script>

<style scoped>
.locked-blur {
  filter: blur(8px);
  opacity: 0.15;
  pointer-events: none;
  transition: opacity 0.2s ease, filter 0.2s ease;
}
</style>
