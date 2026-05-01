<template>
  <div class="dashboard-reference" :class="{ 'is-loading': isBootstrappingDashboard }">
    <div v-if="isBootstrappingDashboard" class="dashboard-loading">
      <div class="spinner"></div>
    </div>

    <template v-else>
      <header class="topbar">
        <div>
          <h1 class="page-title">Olá, {{ userName }} 👋</h1>
          <p class="page-sub">Visão geral das suas páginas e performance.</p>
        </div>
        <div class="topbar-actions">
          <button type="button" class="btn btn-ghost" @click="goToLessons">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <polygon points="23 7 16 12 23 17 23 7"/>
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
            </svg>
            Aulas
          </button>
          <button type="button" class="btn btn-primary" @click="goToPages">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Nova Página
          </button>
        </div>
      </header>

      <SystemBanner
        v-if="eligibleBanner && showBanner"
        :title="eligibleBanner.title"
        :subtitle="eligibleBanner.subtitle || ''"
        :has-icon="eligibleBanner.has_icon"
        :icon-name="eligibleBanner.icon_name"
        :background-variant="eligibleBanner.background_variant"
        :has-cta="eligibleBanner.has_cta"
        :cta-label="eligibleBanner.cta_label"
        :dismissible="eligibleBanner.dismissible"
        @cta="handleBannerCta"
        @close="dismissEligibleBanner"
      />

      <section class="metrics-grid">
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Páginas</span>
            <span class="metric-icon green" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </span>
          </div>
          <p class="metric-value">{{ pagesCount }}</p>
          <p class="metric-footer-text">publicadas</p>
        </article>

        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Visitas</span>
            <span class="metric-icon green" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </span>
          </div>
          <p class="metric-value">{{ totalVisits.toLocaleString(numberLocale) }}</p>
          <div class="metric-footer">
            <span class="metric-badge" :class="visitsTrend >= 0 ? 'up' : 'down'">{{ visitsTrendText }}</span>
            <span class="metric-footer-text">vs. período anterior</span>
          </div>
        </article>

        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Cliques</span>
            <span class="metric-icon amber" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m4 3 7.5 17 2.4-7.1L21 10.5 4 3z" />
                <path d="m13.9 12.9 3.6 3.6" />
              </svg>
            </span>
          </div>
          <p class="metric-value">{{ clicksMetric.toLocaleString(numberLocale) }}</p>
          <p class="metric-footer-text">nos botões</p>
        </article>

        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Leads</span>
            <span class="metric-icon purple" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </span>
          </div>
          <p class="metric-value">{{ leadsMetric }}</p>
          <div class="metric-footer">
            <span class="metric-badge up">{{ leadsMonthText }}</span>
            <span class="metric-footer-text">este mês</span>
          </div>
        </article>
      </section>

      <section class="chart-card-wrap">
        <article class="chart-card">
          <header class="chart-header">
            <div>
              <h2 class="chart-title">Resumo das páginas</h2>
              <p class="chart-sub">Visitas, cliques e leads por período</p>
            </div>
            <div class="chart-controls">
              <select v-model="selectedPage" class="filter-select">
                <option value="all">Todas as páginas</option>
                <option v-for="page in pages" :key="page.id" :value="String(page.id)">{{ page.title }}</option>
              </select>

              <div class="chart-legend">
                <button type="button" class="legend-item legend-toggle" :class="{ off: !visibleSeries.visits }" @click="toggleSeries('visits')"><i class="legend-dot visits"></i>Visitas</button>
                <button type="button" class="legend-item legend-toggle" :class="{ off: !visibleSeries.clicks }" @click="toggleSeries('clicks')"><i class="legend-dot clicks"></i>Cliques</button>
                <button type="button" class="legend-item legend-toggle" :class="{ off: !visibleSeries.leads }" @click="toggleSeries('leads')"><i class="legend-dot leads"></i>Leads</button>
              </div>

              <div class="period-switch">
                <button
                  v-for="period in periods"
                  :key="period"
                  type="button"
                  class="period-btn"
                  :class="{ active: selectedPeriod === period }"
                  @click="selectedPeriod = period"
                >
                  {{ period }}d
                </button>
              </div>
            </div>
          </header>

          <div ref="chartStageRef" class="chart-stage">
            <svg id="areaChart" width="100%" :height="chartHeight" preserveAspectRatio="none">
              <defs>
                <linearGradient id="g-visits" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#2EAD4C" stop-opacity="0.20" />
                  <stop offset="100%" stop-color="#2EAD4C" stop-opacity="0.01" />
                </linearGradient>
                <linearGradient id="g-clicks" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#F97316" stop-opacity="0.20" />
                  <stop offset="100%" stop-color="#F97316" stop-opacity="0.01" />
                </linearGradient>
                <linearGradient id="g-leads" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#7C5CFC" stop-opacity="0.20" />
                  <stop offset="100%" stop-color="#7C5CFC" stop-opacity="0.01" />
                </linearGradient>
              </defs>

              <path v-if="visibleSeries.visits && chartSeries.visits.area" :d="chartSeries.visits.area" fill="url(#g-visits)" />
              <path v-if="visibleSeries.clicks && chartSeries.clicks.area" :d="chartSeries.clicks.area" fill="url(#g-clicks)" />
              <path v-if="visibleSeries.leads && chartSeries.leads.area" :d="chartSeries.leads.area" fill="url(#g-leads)" />

              <path v-if="visibleSeries.visits && chartSeries.visits.path" :d="chartSeries.visits.path" fill="none" stroke="#2EAD4C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
              <path v-if="visibleSeries.clicks && chartSeries.clicks.path" :d="chartSeries.clicks.path" fill="none" stroke="#F97316" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
              <path v-if="visibleSeries.leads && chartSeries.leads.path" :d="chartSeries.leads.path" fill="none" stroke="#7C5CFC" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />

              <circle
                v-for="dot in visibleSeries.visits ? chartSeries.visits.dots : []"
                :key="`visits-${dot.index}`"
                :cx="dot.x"
                :cy="dot.y"
                r="3.5"
                fill="#2EAD4C"
                stroke="#fff"
                stroke-width="1.5"
              />
              <circle
                v-for="dot in visibleSeries.clicks ? chartSeries.clicks.dots : []"
                :key="`clicks-${dot.index}`"
                :cx="dot.x"
                :cy="dot.y"
                r="3.5"
                fill="#F97316"
                stroke="#fff"
                stroke-width="1.5"
              />
              <circle
                v-for="dot in visibleSeries.leads ? chartSeries.leads.dots : []"
                :key="`leads-${dot.index}`"
                :cx="dot.x"
                :cy="dot.y"
                r="3.5"
                fill="#7C5CFC"
                stroke="#fff"
                stroke-width="1.5"
              />

              <rect
                v-for="hit in chartHitAreas"
                :key="`hit-${hit.index}`"
                :x="hit.x"
                y="0"
                :width="hit.width"
                :height="chartHeight"
                fill="transparent"
                @mouseenter="showChartTooltip(hit.index, $event)"
                @mousemove="moveChartTooltip(hit.index, $event)"
                @mouseleave="hideChartTooltip"
              />
            </svg>
            <div v-if="chartTooltip.visible" class="chart-tooltip" :style="chartTooltipStyle">
              <p class="chart-tooltip-date">{{ chartTooltip.label }}</p>
              <p>Visitas: {{ chartTooltip.visits }}</p>
              <p>Cliques: {{ chartTooltip.clicks }}</p>
              <p>Leads: {{ chartTooltip.leads }}</p>
            </div>
          </div>

          <div class="chart-dates">
            <span>{{ chartStartLabel }}</span>
            <span>{{ chartEndLabel }}</span>
          </div>
        </article>
      </section>

      <section class="bottom-grid">
        <article class="list-card">
          <header class="list-header">
            <h3 class="list-title">Top páginas</h3>
            <button type="button" class="list-link" @click="goToPages">Ver todas →</button>
          </header>
          <div class="list-body">
            <div v-for="item in topPages" :key="item.id" class="page-item">
              <div class="page-thumb">📄</div>
              <div class="page-info">
                <p class="page-name">{{ truncateText(item.title, 30) }}</p>
                <p class="page-dest">{{ truncateText(item.origin, 30) }}</p>
                <div class="page-bar"><div class="page-bar-fill" :style="{ width: `${item.progress}%` }"></div></div>
              </div>
              <div class="page-side">
                <span class="page-visits">{{ item.visits }}</span>
                <div class="page-actions">
                  <button type="button" class="page-action-btn view" title="Ver" @click="viewPage(item)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  </button>
                  <button type="button" class="page-action-btn edit" title="Editar" @click="editPage(item)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z" />
                      <path d="M14 3v6h6" />
                      <path d="m9 15 5.5-5.5a1.5 1.5 0 0 1 2.1 2.1L11.1 17H9v-2z" />
                    </svg>
                  </button>
                  <button type="button" class="page-action-btn share" title="Copiar" @click="sharePage(item)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                      <rect x="9" y="9" width="11" height="11" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <p v-if="!topPages.length" class="empty-text">Sem páginas com dados ainda.</p>
          </div>
        </article>

        <article class="list-card">
          <header class="list-header">
            <h3 class="list-title">Leads recentes</h3>
            <button type="button" class="list-link" @click="goToOpportunities">Ver todos →</button>
          </header>
          <div class="list-body">
            <div v-for="lead in recentLeads" :key="String(lead.id)" class="lead-item">
              <div class="lead-avatar">{{ (lead.name || '?').charAt(0).toUpperCase() }}</div>
              <div class="lead-info">
                <div class="lead-copy">
                  <p class="lead-name">{{ truncateText(lead.name || 'Lead sem nome', 40) }}</p>
                  <p class="lead-meta">{{ truncateText(`${lead.page_title || lead.page_slug || lead.form_name || '-'} · ${relativeTime(lead.created_at)}`, 30) }}</p>
                </div>
                <div class="lead-actions">
                  <a
                    v-if="leadWhatsappUrl(lead)"
                    class="lead-btn lead-btn-contact"
                    :href="leadWhatsappUrl(lead)"
                    target="_blank"
                    rel="noopener"
                  >
                    Contato
                  </a>
                  <button type="button" class="lead-btn lead-btn-details" @click="openLeadDetails(lead.id)">Detalhes</button>
                </div>
              </div>
            </div>
            <p v-if="!recentLeads.length" class="empty-text">Sem leads recentes.</p>
          </div>
        </article>
      </section>

      <OpportunityDrawer
        v-model="drawerOpen"
        :contact-id="selectedLeadId"
        :statuses="statuses"
        mode="modal"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";
import { useLeadCaptureStore } from "../../store/useLeadCaptureStore";
import type { LeadContact } from "../../types/leads";
import OpportunityDrawer from "../../components/admin/leads/OpportunityDrawer.vue";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";
import SystemBanner from "../../components/admin/SystemBanner.vue";

interface Page {
  id: number;
  title: string;
  slug?: string;
  status: string;
}

interface PageStatsSummary {
  page_id: number;
  visits: number;
  clicks_cta: number;
  clicks_whatsapp: number;
  leads: number;
}

interface OverviewTimeseriesPoint {
  label?: string;
  date?: string;
  visits?: number;
  whatsapp?: number;
  cta?: number;
  clicks?: number;
  leads?: number;
  conversions?: number;
}

interface OverviewResponse {
  visits: number;
  whatsapp: number;
  cta: number;
  trend?: {
    visits?: number | null;
  } | null;
  timeseries?: OverviewTimeseriesPoint[];
}

interface SystemBannerPayload {
  id: number;
  title: string;
  subtitle?: string | null;
  has_icon: boolean;
  icon_name?: string | null;
  background_variant: string;
  dismissible: boolean;
  dismiss_behavior?: string | null;
  dismiss_duration_days?: number | null;
  has_cta: boolean;
  cta_label?: string | null;
  cta_type?: "internal_route" | "external_url" | "none" | null;
  cta_target?: string | null;
}

const router = useRouter();
const auth = useAuthStore();
const agencyStore = useAgencyStore();
const leadStore = useLeadCaptureStore();
const { contacts, statuses } = storeToRefs(leadStore);

const numberLocale = "pt-BR";
const periods = [7, 14, 30];
const selectedPeriod = ref<number>(7);
const selectedPage = ref<string>("all");
const pages = ref<Page[]>([]);
const pageStatsMap = ref<Record<number, PageStatsSummary>>({});
const overview = ref<OverviewResponse | null>(null);
const isBootstrappingDashboard = ref(true);
const showBanner = ref(true);
const eligibleBanner = ref<SystemBannerPayload | null>(null);
const hasTrackedBannerImpression = ref(false);
const chartStageRef = ref<HTMLElement | null>(null);
const chartWidth = ref(800);
const chartHeight = 160;
const chartPad = 12;
let chartResizeObserver: ResizeObserver | null = null;
const chartTooltip = reactive({
  visible: false,
  index: -1,
  x: 0,
  y: 0,
  label: "--",
  visits: 0,
  clicks: 0,
  leads: 0
});
const visibleSeries = reactive({
  visits: true,
  clicks: true,
  leads: true
});

const drawerOpen = ref(false);
const selectedLeadId = ref<string | number | null>(null);

const userName = computed(() => auth.user?.name || "Agente");
const pagesCount = computed(() => pages.value.filter(page => String(page.status || "").toLowerCase() === "published").length);
const totalVisits = computed(() => overview.value?.visits || 0);
const visitsTrend = computed(() => Number(overview.value?.trend?.visits ?? 0));
const visitsTrendText = computed(() => `${visitsTrend.value >= 0 ? "+" : ""}${visitsTrend.value}%`);
const clicksMetric = computed(() => {
  if (selectedPage.value !== "all") {
    const pageId = Number(selectedPage.value);
    if (!Number.isNaN(pageId)) {
      const stats = pageStatsMap.value[pageId];
      if (stats) return (stats.clicks_cta || 0) + (stats.clicks_whatsapp || 0);
    }
  }
  if (overview.value) return Number(overview.value.cta || 0) + Number(overview.value.whatsapp || 0);
  return Object.values(pageStatsMap.value).reduce((sum, item) => sum + (item.clicks_cta || 0) + (item.clicks_whatsapp || 0), 0);
});

const leadsMetric = computed(() => {
  if (selectedPage.value !== "all") {
    const pageId = Number(selectedPage.value);
    if (!Number.isNaN(pageId)) return pageStatsMap.value[pageId]?.leads || 0;
  }
  if (contacts.value.length) return contacts.value.length;
  return Object.values(pageStatsMap.value).reduce((sum, item) => sum + (item.leads || 0), 0);
});

const leadsThisMonth = computed(() => {
  const now = new Date();
  return contacts.value.filter(contact => {
    if (!contact.created_at) return false;
    const date = new Date(contact.created_at);
    return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
  }).length;
});

const leadsMonthText = computed(() => `+${leadsThisMonth.value}`);

const fetchEligibleBanner = async (agencyId: number) => {
  try {
    const { data } = await api.get<{ banner: SystemBannerPayload | null }>("/system-banners/eligible", {
      params: { placement: "dashboard", agency_id: agencyId }
    });
    eligibleBanner.value = data?.banner || null;
    showBanner.value = true;
    hasTrackedBannerImpression.value = false;
  } catch {
    eligibleBanner.value = null;
  }
};

const trackBannerEvent = async (event: "impression" | "click" | "dismiss") => {
  if (!eligibleBanner.value) return;
  const agencyId = agencyStore.currentAgencyId;
  if (!agencyId) return;
  await api.post(`/system-banners/${eligibleBanner.value.id}/${event}`, { agency_id: agencyId });
};

const ensureBannerImpression = async () => {
  if (!eligibleBanner.value || hasTrackedBannerImpression.value) return;
  try {
    await trackBannerEvent("impression");
    hasTrackedBannerImpression.value = true;
  } catch {
    // noop
  }
};

const handleBannerCta = async () => {
  const banner = eligibleBanner.value;
  if (!banner) return;
  try {
    await trackBannerEvent("click");
  } catch {
    // noop
  }
  if (!banner.has_cta || !banner.cta_type || banner.cta_type === "none" || !banner.cta_target) return;
  if (banner.cta_type === "internal_route") {
    router.push(banner.cta_target);
    return;
  }
  if (banner.cta_type === "external_url") {
    window.open(banner.cta_target, "_blank", "noopener");
  }
};

const dismissEligibleBanner = async () => {
  if (!eligibleBanner.value) return;
  try {
    const agencyId = agencyStore.currentAgencyId;
    await api.post(`/system-banners/${eligibleBanner.value.id}/dismiss`, {
      agency_id: agencyId,
      mode: eligibleBanner.value.dismiss_behavior || "hide_forever",
      dismiss_duration_days: eligibleBanner.value.dismiss_duration_days || null
    });
  } catch {
    // noop
  } finally {
    showBanner.value = false;
  }
};

const chartBase = computed(() => {
  const series = (overview.value?.timeseries || []).map((point, index) => {
    const rawLabel = String(point.label || point.date || index + 1);
    const label = formatDateLabel(rawLabel);
    const visits = Number(point.visits || 0);
    const clicks = Number(point.clicks || ((point.whatsapp || 0) + (point.cta || 0)));
    const leads = Number(point.leads || point.conversions || 0);
    return { label, visits, clicks, leads };
  });

  const max = Math.max(1, ...series.flatMap(item => [item.visits, item.clicks, item.leads]));
  return { series, max };
});

const measureChartWidth = () => {
  const width = chartStageRef.value?.clientWidth || 0;
  chartWidth.value = width > 0 ? width : 800;
};

type ChartPoint = [number, number];
type DotPoint = { index: number; x: number; y: number };
type RenderedSeries = { path: string; area: string; dots: DotPoint[] };
const baselineY = chartHeight - chartPad;
const clampY = (value: number) => Math.min(Math.max(value, chartPad), baselineY);

const makePath = (data: number[], max: number, W: number, H: number, pad: number): { path: string; pts: ChartPoint[] } => {
  if (!data.length) return { path: "", pts: [] };
  const n = data.length;
  const pts: ChartPoint[] = data.map((value, index) => [
    pad + (index / Math.max(1, n - 1)) * (W - pad * 2),
    clampY(H - pad - (value / max) * (H - pad * 2))
  ]);

  let path = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i += 1) {
    const x0 = i > 0 ? pts[i - 1][0] : pts[0][0];
    const y0 = i > 0 ? pts[i - 1][1] : pts[0][1];
    const x1 = pts[i][0];
    const y1 = pts[i][1];
    const x2 = pts[i + 1][0];
    const y2 = pts[i + 1][1];
    const x3 = i < pts.length - 2 ? pts[i + 2][0] : x2;
    const y3 = i < pts.length - 2 ? pts[i + 2][1] : y2;
    const t = 0.25;
    const cy1 = clampY(y1 + (y2 - y0) * t);
    const cy2 = clampY(y2 - (y3 - y1) * t);
    path += ` C ${x1 + (x2 - x0) * t} ${cy1}, ${x2 - (x3 - x1) * t} ${cy2}, ${x2} ${clampY(y2)}`;
  }

  return { path, pts };
};

const buildSeries = (data: number[], max: number): RenderedSeries => {
  const { path, pts } = makePath(data, max, chartWidth.value, chartHeight, chartPad);
  if (!path || !pts.length) return { path: "", area: "", dots: [] };
  const area = `${path} L ${pts[pts.length - 1][0]} ${baselineY} L ${pts[0][0]} ${baselineY} Z`;
  const dots = pts
    .map((point, index) => ({ index, x: point[0], y: point[1], value: data[index] || 0 }))
    .filter(point => point.value > 0)
    .map(({ index, x, y }) => ({ index, x, y }));
  return { path, area, dots };
};

const chartSeries = computed(() => {
  const visitsValues = chartBase.value.series.map(item => item.visits);
  const clicksValues = chartBase.value.series.map(item => item.clicks);
  const leadsValues = chartBase.value.series.map(item => item.leads);
  const max = Math.max(1, ...visitsValues, ...clicksValues, ...leadsValues);

  return {
    visits: buildSeries(visitsValues, max),
    clicks: buildSeries(clicksValues, max),
    leads: buildSeries(leadsValues, max)
  };
});

const chartStartLabel = computed(() => chartBase.value.series[0]?.label || "--");
const chartEndLabel = computed(() => chartBase.value.series[chartBase.value.series.length - 1]?.label || "--");

const chartHitAreas = computed(() => {
  const count = chartBase.value.series.length;
  if (!count) return [] as Array<{ index: number; x: number; width: number }>;
  if (count === 1) return [{ index: 0, x: 0, width: chartWidth.value }];
  const step = (chartWidth.value - chartPad * 2) / (count - 1);
  return Array.from({ length: count }, (_, index) => {
    const centerX = chartPad + index * step;
    const left = index === 0 ? 0 : centerX - step / 2;
    const right = index === count - 1 ? chartWidth.value : centerX + step / 2;
    return { index, x: left, width: right - left };
  });
});

const updateTooltipFromEvent = (event: MouseEvent) => {
  const host = chartStageRef.value;
  if (!host) return;
  const rect = host.getBoundingClientRect();
  const tooltipWidth = 144;
  const tooltipHeight = 82;
  const rawX = event.clientX - rect.left + 10;
  const rawY = event.clientY - rect.top - tooltipHeight - 8;
  const maxX = Math.max(0, rect.width - tooltipWidth);
  const maxY = Math.max(0, rect.height - tooltipHeight);
  chartTooltip.x = Math.min(Math.max(0, rawX), maxX);
  chartTooltip.y = Math.min(Math.max(0, rawY), maxY);
};

const showChartTooltip = (index: number, event: MouseEvent) => {
  const point = chartBase.value.series[index];
  if (!point) return;
  chartTooltip.visible = true;
  chartTooltip.index = index;
  chartTooltip.label = point.label;
  chartTooltip.visits = point.visits;
  chartTooltip.clicks = point.clicks;
  chartTooltip.leads = point.leads;
  updateTooltipFromEvent(event);
};

const moveChartTooltip = (index: number, event: MouseEvent) => {
  if (!chartTooltip.visible || chartTooltip.index !== index) {
    showChartTooltip(index, event);
    return;
  }
  updateTooltipFromEvent(event);
};

const hideChartTooltip = () => {
  chartTooltip.visible = false;
};

type SeriesKey = keyof typeof visibleSeries;
const toggleSeries = (key: SeriesKey) => {
  const currentlyVisible = Object.values(visibleSeries).filter(Boolean).length;
  if (visibleSeries[key] && currentlyVisible === 1) return;
  visibleSeries[key] = !visibleSeries[key];
};

const chartTooltipStyle = computed(() => ({
  left: `${chartTooltip.x}px`,
  top: `${chartTooltip.y}px`
}));

const topPages = computed(() => {
  const maxVisits = Math.max(1, ...Object.values(pageStatsMap.value).map(item => item.visits || 0));
  return pages.value
    .map(page => {
      const stats = pageStatsMap.value[page.id] || { page_id: page.id, visits: 0, clicks_cta: 0, clicks_whatsapp: 0, leads: 0 };
      return {
        id: page.id,
        title: page.title,
        slug: page.slug || "",
        origin: page.slug ? `/${page.slug}` : "Origem não informada",
        visits: stats.visits || 0,
        progress: Math.round(((stats.visits || 0) / maxVisits) * 100)
      };
    })
    .sort((a, b) => b.visits - a.visits)
    .slice(0, 5);
});

const recentLeads = computed(() =>
  [...contacts.value]
    .sort((a, b) => {
      const left = a.created_at ? new Date(a.created_at).getTime() : 0;
      const right = b.created_at ? new Date(b.created_at).getTime() : 0;
      return right - left;
    })
    .slice(0, 5)
);

const fetchPages = async (agencyId: number) => {
  const { data } = await api.get<Page[]>("/pages", { params: { agency_id: agencyId } });
  pages.value = data;
};

const fetchPageStats = async (agencyId: number) => {
  const { data } = await api.get<PageStatsSummary[]>("/stats/pages", { params: { agency_id: agencyId } });
  const map: Record<number, PageStatsSummary> = {};
  data.forEach(item => {
    map[item.page_id] = item;
  });
  pageStatsMap.value = map;
};

const fetchOverview = async (agencyId: number) => {
  const params: Record<string, string | number> = { agency_id: agencyId, days: selectedPeriod.value };
  if (selectedPage.value !== "all") {
    const pageId = Number(selectedPage.value);
    if (!Number.isNaN(pageId)) params.page_id = pageId;
  }
  const { data } = await api.get<OverviewResponse>("/stats/overview", { params });
  overview.value = data;
};

const fetchLeads = async () => {
  try {
    await Promise.all([
      leadStore.fetchContacts(undefined, true),
      leadStore.fetchStatuses(true)
    ]);
  } catch {
    // sem bloqueio do dashboard
  }
};

const loadDashboard = async () => {
  isBootstrappingDashboard.value = true;
  try {
    await agencyStore.loadAgencies();
    const agencyId = agencyStore.currentAgencyId || agencyStore.agencies[0]?.id;
    if (!agencyId) return;
    await agencyStore.loadPrimaryDomain(agencyId);

    await Promise.all([fetchPages(agencyId), fetchPageStats(agencyId), fetchOverview(agencyId), fetchLeads(), fetchEligibleBanner(agencyId)]);
    await ensureBannerImpression();
  } finally {
    isBootstrappingDashboard.value = false;
  }
};

const goToLessons = () => router.push("/admin/aulas");
const goToPages = () => router.push("/admin/pages");
const goToOpportunities = () => router.push("/admin/leads/opportunities");
const goToIntegrations = () => router.push("/admin/integracoes");

const currentAgencySlug = computed(() => {
  const agency = agencyStore.currentAgency || agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return agency?.slug || "";
});

const buildPublicPageUrl = (slug: string) => {
  if (!slug) return "";
  const domain = agencyStore.currentPrimaryDomain;
  const protocol = typeof window !== "undefined" ? window.location.protocol : "https:";
  if (domain) return `${protocol}//${domain}/${slug}`;
  const agencySlug = currentAgencySlug.value;
  if (!agencySlug) return "";
  return `${window.location.origin}/${agencySlug}/${slug}`;
};

const viewPage = (item: { slug: string }) => {
  if (!item.slug) return;
  const url = buildPublicPageUrl(item.slug);
  if (!url) return;
  window.open(url, "_blank", "noopener");
};

const editPage = (item: { id: number }) => {
  router.push(`/admin/pages/${item.id}/edit`);
};

const sharePage = async (item: { slug: string }) => {
  if (!item.slug) return;
  const url = buildPublicPageUrl(item.slug);
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
  } catch {
    window.prompt("Copie o link:", url);
  }
};

const leadWhatsappUrl = (lead: LeadContact) => {
  const digits = normalizeWhatsappDigits(lead.phone || "");
  if (!digits) return "";
  return `https://wa.me/${digits}`;
};

const openLeadDetails = (leadId: string | number) => {
  selectedLeadId.value = leadId;
  drawerOpen.value = true;
};

const relativeTime = (value?: string) => {
  if (!value) return "agora";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "agora";
  const diffMs = Date.now() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "agora";
  if (diffHours < 24) return `há ${diffHours}h`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return "ontem";
  return `há ${diffDays} dias`;
};

const truncateText = (value: string, limit = 50) => {
  const text = String(value || "").trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, Math.max(0, limit - 3))}...`;
};

const formatDateLabel = (raw: string) => {
  const value = String(raw || "").trim();
  const brLike = value.match(/^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/);
  if (brLike) {
    const day = brLike[1].padStart(2, "0");
    const month = brLike[2].padStart(2, "0");
    return `${day}/${month}`;
  }
  const date = new Date(raw);
  if (!Number.isNaN(date.getTime())) {
    return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
  }
  return value;
};

watch([selectedPeriod, selectedPage], async () => {
  const agencyId = agencyStore.currentAgencyId || agencyStore.agencies[0]?.id;
  if (!agencyId) return;
  hideChartTooltip();
  await fetchOverview(agencyId);
});

watch(
  () => [agencyStore.currentAgencyId, eligibleBanner.value?.id],
  async () => {
    await ensureBannerImpression();
  }
);

onMounted(async () => {
  await loadDashboard();
  await nextTick();
  measureChartWidth();
  if (typeof ResizeObserver !== "undefined") {
    chartResizeObserver = new ResizeObserver(() => measureChartWidth());
    if (chartStageRef.value) chartResizeObserver.observe(chartStageRef.value);
  }
  window.addEventListener("resize", measureChartWidth);
});

onBeforeUnmount(() => {
  chartResizeObserver?.disconnect();
  chartResizeObserver = null;
  window.removeEventListener("resize", measureChartWidth);
});
</script>

<style scoped>
.dashboard-reference {
  --verde: #3dcc5f;
  --verde-light: #5be07a;
  --verde-dim: rgba(61, 204, 95, 0.12);
  --verde-border: rgba(61, 204, 95, 0.25);
  --sidebar: #1a3d25;
  --sidebar-active: #2a5c38;
  --bg: #f5f7f5;
  --surface: #ffffff;
  --surface2: #f0f5f1;
  --text: #0f1f14;
  --text-2: #4a6455;
  --text-3: #8aa693;
  --border: #dde8df;
  --shadow: 0 1px 3px rgba(15, 31, 20, 0.06), 0 4px 12px rgba(15, 31, 20, 0.04);
  --shadow-md: 0 4px 16px rgba(15, 31, 20, 0.08), 0 1px 4px rgba(15, 31, 20, 0.04);
  --purple: #7c5cfc;

  width: 100%;
  min-height: 100%;
  background: transparent;
  padding: 28px 32px;
  color: var(--text);
  font-family: "Plus Jakarta Sans", "Inter", sans-serif;
}

.dashboard-loading {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 4px solid #d6e4da;
  border-top-color: var(--verde);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.4px;
}

.page-sub {
  font-size: 13px;
  color: var(--text-3);
  margin-top: 2px;
}

.topbar-actions {
  display: flex;
  gap: 10px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: none;
  border-radius: 10px;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
}

.btn svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.btn-primary {
  background: var(--verde);
  color: #0f1f14;
}

.btn-ghost {
  background: var(--surface);
  color: var(--text-2);
  border: 1px solid var(--border);
}

.banner {
  background: linear-gradient(135deg, #1a3d25 0%, #2a5c38 50%, #1f4a2d 100%);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.banner-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(61, 204, 95, 0.2);
  color: var(--verde);
  font-weight: 800;
}

.banner-title {
  color: #fff;
  font-size: 15px;
  font-weight: 700;
}

.banner-desc {
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
  margin-top: 2px;
}

.banner-cta {
  border: none;
  border-radius: 10px;
  background: var(--verde);
  color: #0f1f14;
  font-weight: 700;
  font-size: 13px;
  padding: 9px 18px;
  cursor: pointer;
}

.banner-close {
  position: absolute;
  top: 10px;
  right: 10px;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.1);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
}

.metric-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.metric-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-3);
}

.metric-icon {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.metric-icon svg {
  width: 16px;
  height: 16px;
}

.metric-icon.green {
  background: var(--verde-dim);
  color: var(--verde);
}

.metric-icon.amber {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.metric-icon.purple {
  background: rgba(124, 92, 252, 0.1);
  color: var(--purple);
}

.metric-value {
  font-size: 32px;
  line-height: 1;
  letter-spacing: -1px;
  margin: 12px 0 8px;
  font-weight: 800;
}

.metric-footer {
  display: flex;
  align-items: center;
  gap: 6px;
}

.metric-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 7px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
}

.metric-badge.up {
  background: var(--verde-dim);
  color: #2a8a3e;
}

.metric-badge.down {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.metric-footer-text {
  font-size: 11px;
  color: var(--text-3);
}

.chart-card-wrap {
  margin-bottom: 24px;
}

.chart-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
}

.chart-title {
  font-size: 15px;
  font-weight: 700;
}

.chart-sub {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.filter-select {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-2);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 6px 10px;
  background: var(--surface);
}

.chart-legend {
  display: flex;
  gap: 12px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-2);
}

.legend-toggle {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.legend-toggle.off {
  opacity: 0.45;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 3px;
}

.legend-dot.visits { background: #2ead4c; }
.legend-dot.clicks { background: #f97316; }
.legend-dot.leads { background: #7c5cfc; }

.period-switch {
  display: inline-flex;
  gap: 4px;
}

.period-btn {
  border: none;
  border-radius: 7px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-3);
  background: transparent;
  cursor: pointer;
}

.period-btn.active {
  background: var(--verde);
  color: #0f1f14;
}

.chart-stage {
  position: relative;
  height: 160px;
}

.chart-stage svg {
  width: 100%;
  height: 100%;
  display: block;
}

.chart-tooltip {
  position: absolute;
  z-index: 2;
  pointer-events: none;
  min-width: 144px;
  border-radius: 10px;
  padding: 8px 10px;
  background: #0f172a;
  color: #fff;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.28);
  font-size: 11px;
  line-height: 1.35;
}

.chart-tooltip p {
  margin: 0;
}

.chart-tooltip p + p {
  margin-top: 2px;
}

.chart-tooltip-date {
  margin-bottom: 4px !important;
  font-size: 12px;
  font-weight: 700;
}

.chart-dates {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-3);
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.list-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.list-title {
  font-size: 15px;
  font-weight: 700;
}

.list-link {
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--verde);
  font-weight: 700;
  cursor: pointer;
}

.page-item,
.lead-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}

.page-item:last-child,
.lead-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.page-thumb,
.lead-avatar {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 800;
}

.page-thumb {
  background: var(--verde-dim);
  color: var(--verde);
}

.lead-avatar {
  background: rgba(124, 92, 252, 0.12);
  color: var(--purple);
}

.page-info,
.lead-info {
  flex: 1;
  min-width: 0;
}

.lead-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.lead-copy {
  min-width: 0;
}

.page-name,
.lead-name {
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}

.page-dest,
.lead-meta {
  font-size: 11px;
  color: var(--text-3);
  margin: 0;
}

.lead-meta {
  margin-top: 2px;
}

.page-bar {
  width: 100%;
  height: 3px;
  border-radius: 999px;
  background: var(--surface2);
  overflow: hidden;
  margin-top: 4px;
}

.page-bar-fill {
  height: 100%;
  background: var(--verde);
}

.page-side {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-visits {
  font-size: 13px;
  font-weight: 800;
}

.page-actions,
.lead-actions {
  display: flex;
  gap: 5px;
}

.page-action-btn,
.lead-btn {
  border: none;
  border-radius: 7px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
}

.page-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
  width: 38px;
  height: 38px;
  font-size: 19px;
}

.page-action-btn svg {
  width: 18px;
  height: 18px;
}

.page-action-btn.view { background: var(--verde-dim); color: var(--verde); }
.page-action-btn.edit { background: var(--surface2); color: var(--text-2); border: 1px solid var(--border); }
.page-action-btn.share { background: rgba(124, 92, 252, 0.12); color: var(--purple); }

.lead-btn {
  padding: 4px 9px;
}

.lead-btn-contact {
  background: var(--verde);
  color: #0f1f14;
  text-decoration: none;
}

.lead-btn-details {
  background: var(--surface2);
  color: var(--text-2);
  border: 1px solid var(--border);
}

.empty-text {
  font-size: 12px;
  color: var(--text-3);
  padding-top: 4px;
}

@media (max-width: 1100px) {
  .dashboard-reference {
    padding: 22px 16px;
  }

  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .chart-header {
    flex-direction: column;
  }

  .chart-controls {
    width: 100%;
    justify-content: flex-start;
  }

  .banner {
    padding-right: 56px;
  }

  .list-card {
    padding: 14px;
  }

  .list-body {
    overflow-x: hidden;
  }

  .page-item,
  .lead-item {
    gap: 8px;
  }

  .page-thumb,
  .lead-avatar {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    font-size: 10px;
  }

  .page-name,
  .lead-name {
    font-size: 12px;
    white-space: normal;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .page-dest,
  .lead-meta,
  .page-visits {
    font-size: 10px;
  }

  .page-side,
  .lead-actions {
    gap: 6px;
    flex-shrink: 0;
  }

  .page-action-btn {
    width: 32px;
    height: 32px;
  }

  .page-action-btn svg {
    width: 15px;
    height: 15px;
  }

  .lead-btn {
    padding: 3px 8px;
    font-size: 10px;
    white-space: nowrap;
  }
}
</style>
