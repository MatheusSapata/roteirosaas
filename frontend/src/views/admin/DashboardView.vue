<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <header class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm uppercase tracking-[0.25em] text-slate-500">Painel</p>
        <h1 class="text-3xl font-bold text-slate-900">Olá, {{ auth.user?.name || "agente" }}</h1>
        <p class="text-sm text-slate-500">Visão geral das páginas, integrações e performance.</p>
      </div>

      <div class="flex flex-wrap items-center gap-3">
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
      class="flex flex-col gap-4 rounded-2xl border border-emerald-100 bg-white p-5 shadow md:flex-row md:items-center md:justify-between"
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
          <p class="text-3xl font-bold text-slate-900" :class="{ 'blurred-value': isFree }">
            {{ totalVisits.toLocaleString("pt-BR") }}
          </p>
          <span
            v-if="trend.visits !== null"
            class="text-xs font-semibold"
            :class="trend.visits >= 0 ? 'text-emerald-600' : 'text-rose-600'"
          >
            {{ trend.visits > 0 ? "+" : "" }}{{ trend.visits }}%
          </span>
          <span v-else class="text-xs text-slate-400">--</span>
        </div>
        <div v-if="isFree" class="mt-3 text-right">
          <button class="upgrade-chip" @click="goPlans">Desbloquear</button>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100">
        <p class="text-sm text-slate-500">Cliques (geral)</p>
        <div class="mt-2 flex items-end justify-between">
          <p class="text-3xl font-bold text-slate-900" :class="{ 'blurred-value': isFree }">
            {{ totalClicks.toLocaleString("pt-BR") }}
          </p>
          <span
            v-if="trend.clicks !== null"
            class="text-xs font-semibold"
            :class="trend.clicks >= 0 ? 'text-emerald-600' : 'text-rose-600'"
          >
            {{ trend.clicks > 0 ? "+" : "" }}{{ trend.clicks }}%
          </span>
          <span v-else class="text-xs text-slate-400">--</span>
        </div>
        <div v-if="isFree" class="mt-3 text-right">
          <button class="upgrade-chip" @click="goPlans">Desbloquear</button>
        </div>
      </div>
    </section>

    <div class="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-600">
      <label class="font-semibold">Página:</label>
      <select v-model="selectedPage" class="rounded-lg border border-slate-200 px-3 py-1 text-sm text-slate-700">
        <option value="all">Todas as publicadas</option>
        <option v-for="page in publishedPages" :key="page.id" :value="String(page.id)">
          {{ page.title }}
        </option>
      </select>
    </div>

    <section class="grid gap-4 lg:grid-cols-2">
      <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Visitas (últimos 7 dias)</h2>
            <p class="text-sm text-slate-500">Volume diário de acessos.</p>
          </div>
          <div class="text-3xl font-bold text-slate-900" :class="{ 'blurred-value': isFree }">
            {{ totalVisits.toLocaleString("pt-BR") }}
          </div>
        </div>
        <div v-if="isFree" class="mt-2 flex justify-end">
          <button class="upgrade-chip" @click="goPlans">Ver planos</button>
        </div>

        <div class="mt-4 space-y-3">
          <div v-if="visitsPoints.length" class="rounded-xl bg-slate-50 p-6" :class="{ 'locked-blur': isFree }">
            <div class="-mx-4 overflow-x-auto px-4">
              <div class="flex min-w-full justify-center">
                <div class="space-y-3" :style="chartContainerStyle">
                  <div class="relative" :style="{ height: chartHeight + 'px' }">
                    <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none" class="h-full w-full">
                      <template v-for="point in visitsPoints" :key="point.label + '-visits'">
                        <rect
                          :x="point.x"
                          :y="point.y"
                          :width="barWidth"
                          :height="Math.max(chartHeight - point.y, 1)"
                          rx="6"
                          fill="#0ea5e9"
                          opacity="0.85"
                        />
                      </template>
                    </svg>

                    <div
                      v-if="visitsHoverPoint"
                      class="pointer-events-none absolute inset-y-0 w-px bg-slate-300"
                      :style="{ left: visitsHoverPoint.centerX + 'px' }"
                    ></div>

                    <div
                      v-if="visitsHoverPoint"
                      class="pointer-events-none absolute -translate-x-1/2 rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200"
                      :style="visitsTooltipStyle"
                    >
                      <p class="text-[11px] font-semibold text-slate-500">{{ visitsHoverPoint.label }}</p>
                      <p class="text-slate-800">Visitas: {{ visitsHoverPoint.value.toLocaleString("pt-BR") }}</p>
                    </div>

                    <div
                      ref="visitsSurfaceRef"
                      class="absolute inset-0 cursor-crosshair"
                      @mousemove="visitsHandleMove"
                      @mouseleave="visitsClearHover"
                    ></div>
                  </div>

                  <div class="relative h-6 text-xs text-slate-500" :style="{ width: chartWidth + 'px' }">
                    <span
                      v-for="point in visitsPoints"
                      :key="point.label + '-label-visits'"
                      class="absolute -translate-x-1/2 whitespace-nowrap"
                      :style="{ left: point.centerX + 'px' }"
                    >
                      {{ point.label }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="flex h-48 items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-500">
            Sem dados de série temporal.
          </div>
        </div>
      </div>

      <div class="relative rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Cliques (últimos 7 dias)</h2>
            <p class="text-sm text-slate-500">Total somado de cliques.</p>
          </div>
          <div class="text-3xl font-bold text-slate-900" :class="{ 'blurred-value': isFree }">
            {{ totalClicks.toLocaleString("pt-BR") }}
          </div>
        </div>
        <div v-if="isFree" class="mt-2 flex justify-end">
          <button class="upgrade-chip" @click="goPlans">Ver planos</button>
        </div>

        <div class="mt-4 space-y-3">
          <div v-if="clicksPoints.length" class="rounded-xl bg-slate-50 p-6" :class="{ 'locked-blur': isFree }">
            <div class="-mx-4 overflow-x-auto px-4">
              <div class="flex min-w-full justify-center">
                <div class="space-y-3" :style="chartContainerStyle">
                  <div class="relative" :style="{ height: chartHeight + 'px' }">
                    <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none" class="h-full w-full">
                      <template v-for="point in clicksPoints" :key="point.label + '-clicks'">
                        <rect
                          :x="point.x"
                          :y="point.y"
                          :width="barWidth"
                          :height="Math.max(chartHeight - point.y, 1)"
                          rx="6"
                          fill="#8b5cf6"
                          opacity="0.85"
                        />
                      </template>
                    </svg>

                    <div
                      v-if="clicksHoverPoint"
                      class="pointer-events-none absolute inset-y-0 w-px bg-slate-300"
                      :style="{ left: clicksHoverPoint.centerX + 'px' }"
                    ></div>

                    <div
                      v-if="clicksHoverPoint"
                      class="pointer-events-none absolute -translate-x-1/2 rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200"
                      :style="clicksTooltipStyle"
                    >
                      <p class="text-[11px] font-semibold text-slate-500">{{ clicksHoverPoint.label }}</p>
                      <p class="text-slate-800">Cliques: {{ clicksHoverPoint.value.toLocaleString("pt-BR") }}</p>
                    </div>

                    <div
                      ref="clicksSurfaceRef"
                      class="absolute inset-0 cursor-crosshair"
                      @mousemove="clicksHandleMove"
                      @mouseleave="clicksClearHover"
                    ></div>
                  </div>

                  <div class="relative h-6 text-xs text-slate-500" :style="{ width: chartWidth + 'px' }">
                    <span
                      v-for="point in clicksPoints"
                      :key="point.label + '-label-clicks'"
                      class="absolute -translate-x-1/2 whitespace-nowrap"
                      :style="{ left: point.centerX + 'px' }"
                    >
                      {{ point.label }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="flex h-48 items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-500">
            Sem dados de série temporal.
          </div>
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

type MetricPoint = {
  label: string;
  x: number;
  centerX: number;
  y: number;
  value: number;
};

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

const trend = reactive<{
  pages: number | null;
  visits: number | null;
  whatsapp: number | null;
  clicks: number | null;
}>({
  pages: null,
  visits: null,
  whatsapp: null,
  clicks: null
});

const chartDataRaw = ref<SeriesPoint[]>([]);

const chartData = computed(() => {
  if (chartDataRaw.value.length) return chartDataRaw.value;
  return [];
});

const STATS_PERIOD_DAYS = 7;

const chartHeight = 280;
const barWidth = 28;
const barGap = 24;
const horizontalPadding = 32;

const chartWidth = computed(() => {
  const count = chartData.value.length;
  if (!count) return 360;
  const baseWidth = horizontalPadding * 2 + count * (barWidth + barGap);
  return Math.max(baseWidth, 360);
});

const chartContainerStyle = computed(() => ({
  width: `${chartWidth.value}px`,
  minWidth: `${chartWidth.value}px`
}));

const maxVisits = computed(() => {
  if (!chartData.value.length) return 1;
  const maxValue = Math.max(...chartData.value.map((point) => point.visits ?? 0));
  return maxValue > 0 ? maxValue : 1;
});

const maxClicks = computed(() => {
  if (!chartData.value.length) return 1;
  const maxValue = Math.max(...chartData.value.map((point) => point.clicks ?? 0));
  return maxValue > 0 ? maxValue : 1;
});

const buildMetricPoints = (metric: "visits" | "clicks", maxValue: number): MetricPoint[] => {
  const safeMax = maxValue > 0 ? maxValue : 1;

  return chartData.value.map((point, index) => {
    const x = horizontalPadding + index * (barWidth + barGap);
    const ratio = (point[metric] ?? 0) / safeMax;

    return {
      label: point.label,
      x,
      centerX: x + barWidth / 2,
      y: chartHeight - ratio * chartHeight,
      value: point[metric] ?? 0
    };
  });
};

const visitsPoints = computed(() => buildMetricPoints("visits", maxVisits.value));
const clicksPoints = computed(() => buildMetricPoints("clicks", maxClicks.value));

const createMetricHover = (pointsGetter: () => MetricPoint[]) => {
  const surfaceRef = ref<HTMLDivElement | null>(null);
  const hoverPoint = ref<MetricPoint | null>(null);

  const tooltipStyle = computed(() => {
    if (!hoverPoint.value) return {};
    const padding = 40;
    const left = Math.min(Math.max(hoverPoint.value.centerX, padding), chartWidth.value - padding);
    const top = Math.max(hoverPoint.value.y - 40, 24);
    return { left: `${left}px`, top: `${top}px` };
  });

  const handleMove = (event: MouseEvent) => {
    const points = pointsGetter();
    if (!surfaceRef.value || !points.length) return;

    const rect = surfaceRef.value.getBoundingClientRect();
    const offsetX = event.clientX - rect.left;

    let nearest = points[0];
    let minDistance = Math.abs(nearest.centerX - offsetX);

    for (const point of points) {
      const distance = Math.abs(point.centerX - offsetX);
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

  return { surfaceRef, hoverPoint, tooltipStyle, handleMove, clearHover };
};

const visitsChart = createMetricHover(() => visitsPoints.value);
const clicksChart = createMetricHover(() => clicksPoints.value);

const visitsSurfaceRef = visitsChart.surfaceRef;
const visitsHoverPoint = visitsChart.hoverPoint;
const visitsTooltipStyle = visitsChart.tooltipStyle;
const visitsHandleMove = visitsChart.handleMove;
const visitsClearHover = visitsChart.clearHover;

const clicksSurfaceRef = clicksChart.surfaceRef;
const clicksHoverPoint = clicksChart.hoverPoint;
const clicksTooltipStyle = clicksChart.tooltipStyle;
const clicksHandleMove = clicksChart.handleMove;
const clicksClearHover = clicksChart.clearHover;

const publishedPages = computed(() => pages.value.filter((page) => page.status?.toLowerCase() === "published"));

const fetchData = async () => {
  await agencyStore.loadAgencies();
  if (!agencyStore.currentAgencyId) return;

  const agencyId = agencyStore.currentAgencyId;

  const res = await api.get<Page[]>("/pages", { params: { agency_id: agencyId } });
  pages.value = res.data;
  pagesCount.value = res.data.length;

  try {
    const params: Record<string, string | number> = {
      days: STATS_PERIOD_DAYS,
      agency_id: agencyId
    };

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

    visitsChart.clearHover();
    clicksChart.clearHover();
  } catch {
    trend.pages = null;
    trend.visits = null;
    trend.whatsapp = null;
    trend.clicks = null;

    totalVisits.value = 0;
    totalClicks.value = 0;

    chartDataRaw.value = [];

    visitsChart.clearHover();
    clicksChart.clearHover();
  }
};

watch(
  () => publishedPages.value,
  (pagesList) => {
    if (selectedPage.value !== "all" && !pagesList.some((p) => String(p.id) === selectedPage.value)) {
      selectedPage.value = "all";
    }
  }
);

onMounted(fetchData);
watch(selectedPage, fetchData);

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
.blurred-value {
  filter: blur(8px);
  opacity: 0.1;
  pointer-events: none;
  user-select: none;
  position: relative;
}
.upgrade-chip {
  border-radius: 9999px;
  border: 1px solid rgb(226 232 240);
  background-color: white;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgb(51 65 85);
  transition: background-color 0.2s;
}
.upgrade-chip:hover {
  background-color: rgb(248 250 252);
}
</style>
