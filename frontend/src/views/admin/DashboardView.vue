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

    <section
      v-if="!allOnboardingStepsCompleted"
      class="rounded-2xl bg-white p-5 shadow ring-1 ring-slate-100"
    >
      <p class="text-xs font-semibold uppercase tracking-[0.4em] text-slate-500">Comece por aqui</p>
      <h2 class="mt-1 text-xl font-bold text-slate-900">Monte seu ambiente em 3 passos</h2>
      <div class="relative mt-6">
        <div class="absolute left-10 right-10 top-6 h-0.5 bg-slate-200"></div>
        <div class="relative flex flex-col gap-6 md:flex-row md:justify-between">
          <div
            v-for="step in onboardingSteps"
            :key="step.id"
            class="flex flex-col items-center gap-3 text-center transition md:w-1/3"
          >
            <div class="relative flex flex-col items-center gap-2">
              <div
                class="flex h-12 w-12 items-center justify-center rounded-full border-4 text-sm font-semibold shadow-sm"
                :class="step.completed ? 'border-emerald-200 bg-emerald-500 text-white' : 'border-slate-200 bg-white text-slate-700'"
              >
                <svg
                  v-if="step.completed"
                  viewBox="0 0 24 24"
                  class="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M5 13l4 4L19 7" />
                </svg>
                <span v-else>{{ step.order }}</span>
              </div>
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ step.title }}</p>
                <p class="text-xs text-slate-500 max-w-[180px] mx-auto">{{ step.subtitle }}</p>
              </div>
            </div>
            <div v-if="!step.completed">
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-full px-6 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                :style="{ backgroundColor: brandGreen }"
                :disabled="step.disabled"
                @click="!step.disabled && step.action?.()"
              >
                {{ step.cta }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div
      v-if="isFree"
      class="flex flex-col gap-4 rounded-2xl border bg-white p-5 shadow md:flex-row md:items-center md:justify-between"
      :style="{ borderColor: brandBorderSoft }"
    >
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.3em]" :style="{ color: brandGreen }">Plano atual: Começo</p>
        <p class="mt-1 text-base font-semibold text-slate-900">Desbloqueie métricas completas e integrações.</p>
        <p class="text-sm text-slate-600">
          Faça upgrade para organizar mais roteiros, liberar as seções bloqueadas e acompanhar desempenho em tempo real.
        </p>
      </div>

      <button
        class="self-start rounded-full px-5 py-2 text-sm font-semibold text-white shadow transition hover:opacity-90"
        :style="{ backgroundColor: brandGreen }"
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
            :class="trend.pages >= 0 ? 'text-brand' : 'text-rose-600'"
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
            {{ cardsTotalVisits.toLocaleString("pt-BR") }}
          </p>
          <span
            v-if="trend.visits !== null"
            class="text-xs font-semibold"
            :class="trend.visits >= 0 ? 'text-brand' : 'text-rose-600'"
          >
            {{ trend.visits > 0 ? "+" : "" }}{{ trend.visits }}%
          </span>
          <span v-else class="text-xs text-slate-400">--</span>
        </div>
        <div v-if="isFree" class="mt-3 text-right">
          <button
            class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            @click="goPlans"
          >
            Desbloquear
          </button>
        </div>
      </div>

      <div class="rounded-2xl bg-white p-5 shadow-md ring-1 ring-slate-100">
        <p class="text-sm text-slate-500">Cliques (geral)</p>
        <div class="mt-2 flex items-end justify-between">
          <p class="text-3xl font-bold text-slate-900" :class="{ 'blurred-value': isFree }">
            {{ cardsTotalClicks.toLocaleString("pt-BR") }}
          </p>
          <span
            v-if="trend.clicks !== null"
            class="text-xs font-semibold"
            :class="trend.clicks >= 0 ? 'text-brand' : 'text-rose-600'"
          >
            {{ trend.clicks > 0 ? "+" : "" }}{{ trend.clicks }}%
          </span>
          <span v-else class="text-xs text-slate-400">--</span>
        </div>
        <div v-if="isFree" class="mt-3 text-right">
          <button
            class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            @click="goPlans"
          >
            Desbloquear
          </button>
        </div>
      </div>
    </section>

    <div class="mb-2 flex flex-wrap items-center gap-4 text-xs text-slate-600">
      <div class="flex items-center gap-2">
        <label class="font-semibold">Página:</label>
        <select v-model="selectedPage" class="rounded-lg border border-slate-200 px-3 py-1 text-sm text-slate-700">
          <option value="all">Todas as publicadas</option>
          <option v-for="page in publishedPages" :key="page.id" :value="String(page.id)">
            {{ page.title }}
          </option>
        </select>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <label class="font-semibold">Período:</label>
        <select v-model="selectedPeriod" class="rounded-lg border border-slate-200 px-3 py-1 text-sm text-slate-700">
          <option v-for="period in statsPeriodOptions" :key="period" :value="period">
            Últimos {{ period }} dias
          </option>
          <option value="custom">Personalizado</option>
        </select>
        <div v-if="selectedPeriod === 'custom'" class="flex flex-wrap items-center gap-2 text-xs text-slate-600">
          <label class="font-semibold">De</label>
          <input
            type="date"
            v-model="customStartDate"
            class="rounded-lg border border-slate-200 px-3 py-1 text-sm text-slate-700"
          />
          <span class="font-semibold">até</span>
          <input
            type="date"
            v-model="customEndDate"
            class="rounded-lg border border-slate-200 px-3 py-1 text-sm text-slate-700"
          />
        </div>
      </div>
    </div>


    <section class="grid gap-4 lg:grid-cols-2">
      <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Visitas ({{ chartPeriodLabel }})</h2>
            <p class="text-sm text-slate-500">Volume diário de acessos.</p>
          </div>
          <div class="text-3xl font-bold text-slate-900" :class="{ 'blurred-value': isFree }">
            {{ totalVisits.toLocaleString("pt-BR") }}
          </div>
        </div>
        <div v-if="isFree" class="mt-2 flex justify-end">
          <button
            class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            @click="goPlans"
          >
            Ver planos
          </button>
        </div>

        <div class="mt-4 space-y-3">
          <div v-if="visitsPoints.length" class="rounded-xl bg-slate-50 p-6" :class="{ 'locked-blur': isFree }">
            <div class="relative rounded-2xl border border-slate-100 bg-white/80 p-4">
              <div class="pointer-events-none absolute inset-4">
                <div
                  v-for="line in chartGridLines"
                  :key="'grid-visits-' + line"
                  class="absolute left-0 right-0 border-t border-dashed border-emerald-100"
                  :style="{ top: line + 'px' }"
                ></div>
              </div>
              <div class="relative" :style="{ height: chartHeight + 'px' }">
                <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none" class="h-full w-full text-emerald-500">
                  <defs>
                    <linearGradient id="visits-line-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stop-color="#16a34a" stop-opacity="0.95"></stop>
                      <stop offset="100%" stop-color="#22c55e" stop-opacity="0.65"></stop>
                    </linearGradient>
                    <linearGradient id="visits-area-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stop-color="#86efac" stop-opacity="0.35"></stop>
                      <stop offset="100%" stop-color="#f0fdf4" stop-opacity="0"></stop>
                    </linearGradient>
                  </defs>
                  <path v-if="visitsAreaPath" :d="visitsAreaPath" fill="url(#visits-area-gradient)" stroke="none" />
                  <path
                    v-if="visitsLinePath"
                    :d="visitsLinePath"
                    stroke="url(#visits-line-gradient)"
                    stroke-width="3"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <template v-for="point in visitsPoints" :key="point.label + '-dot'">
                    <circle :cx="point.centerX" :cy="point.y" r="4.5" fill="#f8fffe" stroke="#16a34a" stroke-width="2" />
                  </template>
                </svg>

                <div
                  ref="visitsSurfaceRef"
                  class="absolute inset-0 cursor-crosshair"
                  @mousemove="visitsHandleMove"
                  @mouseleave="visitsClearHover"
                ></div>

                <div
                  v-if="visitsHoverPoint"
                  class="pointer-events-none absolute -translate-x-1/2 rounded-xl border border-white bg-slate-900/90 px-4 py-2 text-xs text-white shadow-lg"
                  :style="visitsTooltipStyle"
                >
                  <p class="font-semibold">{{ visitsHoverPoint.label }}</p>
                  <p>Visitas: {{ visitsHoverPoint.value.toLocaleString("pt-BR") }}</p>
                </div>
              </div>
            </div>

            <div class="mt-2 text-xs text-slate-500">
              <template v-if="compactChartLabels && chartLabelRange">
                <div class="flex items-center justify-between font-semibold text-slate-700">
                  <span>{{ chartLabelRange.start }}</span>
                  <span>{{ chartLabelRange.end }}</span>
                </div>
              </template>
              <template v-else>
                <div class="flex flex-wrap justify-between gap-2 font-semibold text-slate-700">
                  <span v-for="point in visitsPoints" :key="point.label + '-label-visits'">{{ point.label }}</span>
                </div>
              </template>
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
            <h2 class="text-lg font-semibold text-slate-900">Cliques ({{ chartPeriodLabel }})</h2>
            <p class="text-sm text-slate-500">Total somado de cliques.</p>
          </div>
          <div class="text-3xl font-bold text-slate-900" :class="{ 'blurred-value': isFree }">
            {{ totalClicks.toLocaleString("pt-BR") }}
          </div>
        </div>
        <div v-if="isFree" class="mt-2 flex justify-end">
          <button
            class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            @click="goPlans"
          >
            Ver planos
          </button>
        </div>

        <div class="mt-4 space-y-3">
          <div v-if="clicksPoints.length" class="rounded-xl bg-slate-50 p-6" :class="{ 'locked-blur': isFree }">
            <div class="relative rounded-2xl border border-slate-100 bg-white/80 p-4">
              <div class="pointer-events-none absolute inset-4">
                <div
                  v-for="line in chartGridLines"
                  :key="'grid-clicks-' + line"
                  class="absolute left-0 right-0 border-t border-dashed border-indigo-200"
                  :style="{ top: line + 'px' }"
                ></div>
              </div>
              <div class="relative" :style="{ height: chartHeight + 'px' }">
                <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none" class="h-full w-full text-indigo-500">
                  <defs>
                    <linearGradient id="clicks-line-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stop-color="#7c3aed" stop-opacity="0.95"></stop>
                      <stop offset="100%" stop-color="#a855f7" stop-opacity="0.65"></stop>
                    </linearGradient>
                    <linearGradient id="clicks-area-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stop-color="#ddd6fe" stop-opacity="0.35"></stop>
                      <stop offset="100%" stop-color="#faf5ff" stop-opacity="0"></stop>
                    </linearGradient>
                  </defs>
                  <path v-if="clicksAreaPath" :d="clicksAreaPath" fill="url(#clicks-area-gradient)" stroke="none" />
                  <path
                    v-if="clicksLinePath"
                    :d="clicksLinePath"
                    stroke="url(#clicks-line-gradient)"
                    stroke-width="3"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <template v-for="point in clicksPoints" :key="point.label + '-dot'">
                    <circle :cx="point.centerX" :cy="point.y" r="4.5" fill="#f8f5ff" stroke="#7c3aed" stroke-width="2" />
                  </template>
                </svg>

                <div
                  ref="clicksSurfaceRef"
                  class="absolute inset-0 cursor-crosshair"
                  @mousemove="clicksHandleMove"
                  @mouseleave="clicksClearHover"
                ></div>

                <div
                  v-if="clicksHoverPoint"
                  class="pointer-events-none absolute -translate-x-1/2 rounded-xl border border-white bg-slate-900/90 px-4 py-2 text-xs text-white shadow-lg"
                  :style="clicksTooltipStyle"
                >
                  <p class="font-semibold">{{ clicksHoverPoint.label }}</p>
                  <p>Cliques: {{ clicksHoverPoint.value.toLocaleString("pt-BR") }}</p>
                </div>
              </div>
            </div>

            <div class="mt-2 text-xs text-slate-500">
              <template v-if="compactChartLabels && chartLabelRange">
                <div class="flex items-center justify-between font-semibold text-slate-700">
                  <span>{{ chartLabelRange.start }}</span>
                  <span>{{ chartLabelRange.end }}</span>
                </div>
              </template>
              <template v-else>
                <div class="flex flex-wrap justify-between gap-2 font-semibold text-slate-700">
                  <span v-for="point in clicksPoints" :key="point.label + '-label-clicks'">{{ point.label }}</span>
                </div>
              </template>
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
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
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

interface OnboardingStep {
  id: string;
  order: number;
  title: string;
  subtitle: string;
  completed: boolean;
  cta?: string;
  action?: (() => void) | null;
  disabled?: boolean;
}

const auth = useAuthStore();
const agencyStore = useAgencyStore();
const router = useRouter();

const pages = ref<Page[]>([]);
const pagesCount = ref(0);

const selectedPage = ref<string>("all");
const totalVisits = ref(0);
const totalClicks = ref(0);
const cardsTotalVisits = ref(0);
const cardsTotalClicks = ref(0);
const statsPeriodOptions = [7, 14, 30];
const selectedPeriod = ref<number | "custom">(statsPeriodOptions[0]);
const customStartDate = ref("");
const customEndDate = ref("");
const isMobile = ref(false);

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

const brandGreen = "#41ce5f";
const brandBorderSoft = "#cdeed9";

const lineChartHeight = 240;
const lineChartWidth = 640;
const lineChartPaddingX = 28;
const lineChartPaddingY = 28;
const lineChartInnerHeight = lineChartHeight - lineChartPaddingY * 2;
const lineChartInnerWidth = lineChartWidth - lineChartPaddingX * 2;
const chartGridLineRatios = [0.2, 0.4, 0.6, 0.8];

const chartHeight = lineChartHeight;
const chartWidth = computed(() => lineChartWidth);
const chartGridLines = computed(() =>
  chartGridLineRatios.map((ratio) => lineChartPaddingY + ratio * lineChartInnerHeight)
);
const isCustomPeriod = computed(() => selectedPeriod.value === "custom");
const customRangeReady = computed(
  () => isCustomPeriod.value && Boolean(customStartDate.value) && Boolean(customEndDate.value)
);
const orderedCustomRange = computed(() => {
  if (!customRangeReady.value) return null;
  const start = new Date(customStartDate.value);
  const end = new Date(customEndDate.value);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  if (start.getTime() <= end.getTime()) {
    return { startISO: customStartDate.value, endISO: customEndDate.value, startDate: start, endDate: end };
  }
  return { startISO: customEndDate.value, endISO: customStartDate.value, startDate: end, endDate: start };
});
const hasValidCustomRange = computed(() => Boolean(orderedCustomRange.value));
const formatShortDate = (iso: string) => {
  if (!iso) return "--";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "--";
  return d.toLocaleDateString("pt-BR");
};
const selectedPeriodDays = computed(() => {
  if (orderedCustomRange.value) {
    const diff =
      Math.floor(
        (orderedCustomRange.value.endDate.getTime() - orderedCustomRange.value.startDate.getTime()) /
          (1000 * 60 * 60 * 24)
      ) + 1;
    return Math.max(diff, 1);
  }
  return typeof selectedPeriod.value === "number" ? selectedPeriod.value : statsPeriodOptions[0];
});
const chartPeriodLabel = computed(() => {
  if (orderedCustomRange.value) {
    return `${formatShortDate(orderedCustomRange.value.startISO)} a ${formatShortDate(orderedCustomRange.value.endISO)}`;
  }
  if (isCustomPeriod.value) {
    return "período personalizado";
  }
  return `últimos ${selectedPeriodDays.value} dias`;
});

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
  if (!chartData.value.length) return [];
  const count = chartData.value.length;
  const step = count > 1 ? lineChartInnerWidth / (count - 1) : 0;

  return chartData.value.map((point, index) => {
    const value = point[metric] ?? 0;
    const ratio = value / safeMax;
    const centerX = count === 1 ? lineChartWidth / 2 : lineChartPaddingX + index * step;
    const y = lineChartPaddingY + (lineChartInnerHeight - ratio * lineChartInnerHeight);

    return {
      label: point.label,
      centerX,
      y,
      value
    };
  });
};

const buildLinePath = (points: MetricPoint[]) => {
  if (!points.length) return "";
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.centerX} ${point.y}`).join(" ");
};

const buildAreaPath = (points: MetricPoint[]) => {
  if (!points.length) return "";
  const baselineY = lineChartPaddingY + lineChartInnerHeight;
  if (points.length === 1) {
    const point = points[0];
    return `M ${point.centerX} ${baselineY} L ${point.centerX} ${point.y} L ${point.centerX} ${baselineY} Z`;
  }
  const segments = points.map((point) => `L ${point.centerX} ${point.y}`).join(" ");
  const first = points[0];
  const last = points[points.length - 1];
  return `M ${first.centerX} ${baselineY} ${segments} L ${last.centerX} ${baselineY} Z`;
};

const visitsPoints = computed(() => buildMetricPoints("visits", maxVisits.value));
const clicksPoints = computed(() => buildMetricPoints("clicks", maxClicks.value));
const visitsLinePath = computed(() => buildLinePath(visitsPoints.value));
const visitsAreaPath = computed(() => buildAreaPath(visitsPoints.value));
const clicksLinePath = computed(() => buildLinePath(clicksPoints.value));
const clicksAreaPath = computed(() => buildAreaPath(clicksPoints.value));
const compactChartLabels = computed(() => isMobile.value || selectedPeriodDays.value >= 14);
const chartLabelRange = computed(() => {
  if (!compactChartLabels.value || chartData.value.length < 2) return null;
  const first = chartData.value[0]?.label || "";
  const last = chartData.value[chartData.value.length - 1]?.label || "";
  if (!first || !last) return null;
  return { start: first, end: last };
});

const createMetricHover = (pointsGetter: () => MetricPoint[]) => {
  const surfaceRef = ref<HTMLDivElement | null>(null);
  const hoverPoint = ref<MetricPoint | null>(null);

  const tooltipStyle = computed(() => {
    if (!hoverPoint.value) return {};
    const padding = 40;
    const surfaceWidth = surfaceRef.value?.clientWidth || chartWidth.value;
    const scaledX = (hoverPoint.value.centerX / chartWidth.value) * surfaceWidth;
    const left = Math.min(Math.max(scaledX, padding), surfaceWidth - padding);
    const top = Math.max(hoverPoint.value.y - 40, 24);
    return { left: `${left}px`, top: `${top}px` };
  });

  const handleMove = (event: MouseEvent) => {
    const points = pointsGetter();
    if (!surfaceRef.value || !points.length) return;

    const rect = surfaceRef.value.getBoundingClientRect();
    const offsetX = event.clientX - rect.left;
    const surfaceWidth = surfaceRef.value.clientWidth || chartWidth.value;
    const normalizedX = (offsetX / surfaceWidth) * chartWidth.value;

    let nearest = points[0];
    let minDistance = Math.abs(nearest.centerX - normalizedX);

    for (const point of points) {
      const distance = Math.abs(point.centerX - normalizedX);
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
const hasAgency = computed(() => agencyStore.agencies.length > 0);
const hasPublishedPage = computed(() => publishedPages.value.length > 0);

const goToAgencySettings = () => {
  router.push("/admin/agency");
};

const goToPagesList = () => {
  router.push("/admin/pages");
};

const onboardingSteps = computed<OnboardingStep[]>(() => [
  {
    id: "finish-signup",
    order: 1,
    title: "Finalizar cadastro",
    subtitle: "Seus dados estão completos.",
    completed: true
  },
  {
    id: "create-agency",
    order: 2,
    title: "Criar agência",
    subtitle: hasAgency.value ? "Agência criada com sucesso." : "Cadastre sua primeira agência.",
    completed: hasAgency.value,
    cta: "Ir para Agências",
    action: hasAgency.value ? null : goToAgencySettings
  },
  {
    id: "publish-page",
    order: 3,
    title: "Publicar primeira página",
    subtitle: hasPublishedPage.value ? "Sua primeira página já está no ar." : "Publique um roteiro para compartilhar.",
    completed: hasPublishedPage.value,
    cta: "Publicar agora",
    action: hasPublishedPage.value ? null : goToPagesList,
    disabled: !hasAgency.value
  }
]);

const allOnboardingStepsCompleted = computed(() => onboardingSteps.value.every(step => step.completed));

const applyCardsStats = (stats: StatsOverviewResponse | null) => {
  trend.pages = stats?.trend?.pages ?? null;
  trend.visits = stats?.trend?.visits ?? null;
  trend.whatsapp = stats?.trend?.whatsapp ?? null;
  trend.clicks = stats?.trend?.clicks ?? null;
  cardsTotalVisits.value = stats?.visits ?? 0;
  cardsTotalClicks.value = (stats?.whatsapp ?? 0) + (stats?.cta ?? 0);
};

const applyChartStats = (stats: StatsOverviewResponse | null) => {
  totalVisits.value = stats?.visits ?? 0;
  totalClicks.value = (stats?.whatsapp ?? 0) + (stats?.cta ?? 0);
  if (stats && Array.isArray(stats.timeseries)) {
    chartDataRaw.value = stats.timeseries as SeriesPoint[];
  } else {
    chartDataRaw.value = [];
  }
  visitsChart.clearHover();
  clicksChart.clearHover();
};

const appendRangeParams = (params: Record<string, string | number>) => {
  if (orderedCustomRange.value) {
    params.start_date = orderedCustomRange.value.startISO;
    params.end_date = orderedCustomRange.value.endISO;
  } else {
    params.days = selectedPeriodDays.value;
  }
};

const fetchOverviewStats = async (agencyId: number) => {
  try {
    const params: Record<string, string | number> = { agency_id: agencyId };
    appendRangeParams(params);
    const { data } = await api.get<StatsOverviewResponse>("/stats/overview", { params });
    applyCardsStats(data);
    if (selectedPage.value === "all") {
      applyChartStats(data);
    }
  } catch {
    applyCardsStats(null);
    if (selectedPage.value === "all") {
      applyChartStats(null);
    }
  }
};

const fetchSelectedPageStats = async (agencyId: number) => {
  if (selectedPage.value === "all") return;

  const pageId = Number(selectedPage.value);
  if (Number.isNaN(pageId)) {
    applyChartStats(null);
    return;
  }

  try {
    const params: Record<string, string | number> = {
      agency_id: agencyId,
      page_id: pageId
    };
    appendRangeParams(params);
    const { data } = await api.get<StatsOverviewResponse>("/stats/overview", { params });
    applyChartStats(data);
  } catch {
    applyChartStats(null);
  }
};

const fetchData = async () => {
  await agencyStore.loadAgencies();
  if (!agencyStore.currentAgencyId) return;
  if (selectedPeriod.value === "custom" && !hasValidCustomRange.value) return;

  const agencyId = agencyStore.currentAgencyId;

  const res = await api.get<Page[]>("/pages", { params: { agency_id: agencyId } });
  pages.value = res.data;
  pagesCount.value = res.data.length;

  await fetchOverviewStats(agencyId);
  await fetchSelectedPageStats(agencyId);
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
const updateIsMobile = () => {
  if (typeof window === "undefined") return;
  isMobile.value = window.matchMedia("(max-width: 768px)").matches;
};
onMounted(() => {
  updateIsMobile();
  window.addEventListener("resize", updateIsMobile);
});
onUnmounted(() => {
  window.removeEventListener("resize", updateIsMobile);
});
watch(
  selectedPage,
  async () => {
    if (!agencyStore.currentAgencyId) return;
    await fetchSelectedPageStats(agencyStore.currentAgencyId);
  }
);

watch(
  selectedPeriod,
  async (value) => {
    if (!agencyStore.currentAgencyId) return;
    if (value === "custom" && !hasValidCustomRange.value) return;
    const agencyId = agencyStore.currentAgencyId;
    await fetchOverviewStats(agencyId);
    await fetchSelectedPageStats(agencyId);
  }
);

watch(
  [customStartDate, customEndDate],
  async () => {
    if (selectedPeriod.value !== "custom" || !hasValidCustomRange.value) return;
    if (!agencyStore.currentAgencyId) return;
    const agencyId = agencyStore.currentAgencyId;
    await fetchOverviewStats(agencyId);
    await fetchSelectedPageStats(agencyId);
  }
);

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
</style>
