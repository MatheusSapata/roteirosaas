<template>
  <div class="dashboard-reference" :class="{ 'is-loading': isBootstrappingDashboard }">
    <transition name="fade">
      <div v-if="copyToast" class="copy-toast app-snackbar-layer">
        {{ copyToast }}
      </div>
    </transition>
    <div v-if="isBootstrappingDashboard" class="dashboard-loading">
      <div class="spinner"></div>
    </div>

    <template v-else>
      <header class="topbar">
        <div class="min-w-0">
          <p class="page-date">{{ todayLabel }}</p>
          <h1 class="page-title">{{ greeting }}, <span class="page-title-name">{{ firstName }}</span></h1>
        </div>
        <div class="topbar-actions">
          <div class="period-switch" role="group" aria-label="Período">
            <button
              v-for="period in periods"
              :key="period"
              type="button"
              class="period-btn"
              :class="{ active: selectedPeriod === period }"
              @click="selectedPeriod = period"
            >
              {{ period }} dias
            </button>
          </div>
          <button type="button" class="btn btn-primary" @click="openNewPage">
            <PlusIcon aria-hidden="true" />
            Nova página
          </button>
        </div>
      </header>

      <SystemBanner
        v-if="eligibleBanner && showBanner"
        :title="eligibleBanner.title"
        :subtitle="eligibleBanner.subtitle || ''"
        :has-icon="eligibleBanner.has_icon"
        :icon-name="eligibleBanner.icon_name"
        :icon-svg="eligibleBannerIconSvg"
        :show-icon-background="eligibleBannerShowIconBackground"
        :background-variant="eligibleBanner.background_variant"
        :custom-background="eligibleBannerBackground"
        :cta-background="eligibleBannerCtaBackground"
        :cta-text-color="eligibleBannerCtaTextColor"
        :has-cta="eligibleBanner.has_cta"
        :cta-label="eligibleBanner.cta_label"
        :dismissible="eligibleBanner.dismissible"
        @cta="handleBannerCta"
        @close="dismissEligibleBanner"
      />

      <section class="metrics-grid">
        <article class="metric-card metric-hero">
          <div class="metric-header">
            <span class="metric-icon" aria-hidden="true">
              <EyeIcon aria-hidden="true" />
            </span>
            <span class="metric-label">Visitas no período</span>
          </div>
          <p class="metric-value">{{ totalVisits.toLocaleString(numberLocale) }}</p>
          <div class="metric-footer">
            <span class="metric-badge" :class="visitsTrend >= 0 ? 'up' : 'down'">{{ visitsTrendText }}</span>
            <span class="metric-footer-text">vs. {{ selectedPeriod }} dias anteriores</span>
          </div>
        </article>

        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-icon tone-warning" aria-hidden="true">
              <MousePointerClickIcon aria-hidden="true" />
            </span>
            <span class="metric-label">Cliques nos botões</span>
          </div>
          <p class="metric-value">{{ clicksMetric.toLocaleString(numberLocale) }}</p>
          <div class="metric-footer">
            <span class="metric-badge up">{{ formatPercent(clickRate) }}</span>
            <span class="metric-footer-text">das visitas clicaram</span>
          </div>
        </article>

        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-icon tone-violet" aria-hidden="true">
              <UserPlusIcon aria-hidden="true" />
            </span>
            <span class="metric-label">Leads</span>
          </div>
          <p class="metric-value">{{ leadsMetric.toLocaleString(numberLocale) }}</p>
          <div class="metric-footer">
            <span class="metric-badge up">{{ leadsMonthText }}</span>
            <span class="metric-footer-text">este mês</span>
          </div>
        </article>

        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-icon tone-info" aria-hidden="true">
              <FileTextIcon aria-hidden="true" />
            </span>
            <span class="metric-label">Páginas no ar</span>
          </div>
          <p class="metric-value">{{ pagesCount }} <small>de {{ pages.length }}</small></p>
          <div class="metric-footer">
            <span class="metric-badge neutral">{{ draftsCount }} {{ draftsCount === 1 ? "rascunho" : "rascunhos" }}</span>
          </div>
        </article>
      </section>

      <section class="mid-grid">
        <article class="chart-card">
          <header class="chart-header">
            <div>
              <p class="card-eyebrow">Desempenho</p>
              <h2 class="chart-title">Resumo das páginas</h2>
            </div>
            <div class="chart-controls">
              <div class="chart-legend">
                <button type="button" class="legend-item legend-toggle" :class="{ off: !visibleSeries.visits }" @click="toggleSeries('visits')"><i class="legend-dot visits"></i>Visitas</button>
                <button type="button" class="legend-item legend-toggle" :class="{ off: !visibleSeries.clicks }" @click="toggleSeries('clicks')"><i class="legend-dot clicks"></i>Cliques</button>
                <button type="button" class="legend-item legend-toggle" :class="{ off: !visibleSeries.leads }" @click="toggleSeries('leads')"><i class="legend-dot leads"></i>Leads</button>
              </div>
              <select v-model="selectedPage" class="filter-select" aria-label="Página">
                <option value="all">Todas as páginas</option>
                <option v-for="page in pages" :key="page.id" :value="String(page.id)">{{ page.title }}</option>
              </select>
            </div>
          </header>

          <div ref="chartStageRef" class="chart-stage">
            <svg id="areaChart" width="100%" :height="chartHeight" preserveAspectRatio="none">
              <defs>
                <linearGradient id="g-visits" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="var(--chart-1)" stop-opacity="0.22" />
                  <stop offset="100%" stop-color="var(--chart-1)" stop-opacity="0.01" />
                </linearGradient>
              </defs>

              <path v-if="visibleSeries.visits && chartSeries.visits.area" :d="chartSeries.visits.area" fill="url(#g-visits)" />

              <path v-if="visibleSeries.visits && chartSeries.visits.path" :d="chartSeries.visits.path" fill="none" stroke="var(--chart-1)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
              <path v-if="visibleSeries.clicks && chartSeries.clicks.path" :d="chartSeries.clicks.path" fill="none" stroke="var(--chart-4)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
              <path v-if="visibleSeries.leads && chartSeries.leads.path" :d="chartSeries.leads.path" fill="none" stroke="var(--chart-6)" stroke-width="2.5" stroke-dasharray="5 5" stroke-linecap="round" stroke-linejoin="round" />

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
            <span class="chart-note">Leads em linha tracejada, na própria escala</span>
            <span>{{ chartEndLabel }}</span>
          </div>
        </article>

        <article class="chart-card funnel-card">
          <header class="chart-header">
            <div>
              <p class="card-eyebrow">Conversão</p>
              <h2 class="chart-title">Do clique ao lead</h2>
            </div>
          </header>
          <div class="funnel">
            <div v-for="step in funnelSteps" :key="step.key" class="funnel-step">
              <div class="funnel-row"><span>{{ step.label }}</span><b>{{ step.value.toLocaleString(numberLocale) }}</b></div>
              <div class="funnel-bar"><span :class="`fill-${step.key}`" :style="{ width: `${step.width}%` }"></span></div>
            </div>
          </div>
          <div class="funnel-total">
            <span class="metric-icon tone-success" aria-hidden="true">
              <TrendingUpIcon aria-hidden="true" />
            </span>
            <div>
              <b>{{ formatPercent(leadRate) }}</b>
              <span>das visitas viraram lead</span>
            </div>
          </div>
        </article>
      </section>

      <section class="bottom-grid">
        <article class="list-card">
          <header class="list-header">
            <div>
              <p class="card-eyebrow">Páginas</p>
              <h3 class="list-title">Mais visitadas</h3>
            </div>
            <button type="button" class="list-link" @click="goToPages">Ver todas →</button>
          </header>
          <div class="list-body">
            <div v-for="item in topPages" :key="item.id" class="page-item">
              <div class="page-thumb" aria-hidden="true">
                <FileTextIcon aria-hidden="true" />
              </div>
              <div class="page-info">
                <p class="page-name">{{ truncateText(item.title, 30) }}</p>
                <p class="page-dest">{{ truncateText(item.origin, 30) }}</p>
                <div class="page-bar"><div class="page-bar-fill" :style="{ width: `${item.progress}%` }"></div></div>
              </div>
              <div class="page-side">
                <span class="page-visits">{{ item.visits.toLocaleString(numberLocale) }}<small>visitas</small></span>
                <div class="page-actions">
                  <button type="button" class="page-action-btn" title="Ver" aria-label="Ver página publicada" @click="viewPage(item)">
                    <EyeIcon aria-hidden="true" />
                  </button>
                  <button type="button" class="page-action-btn" title="Editar" aria-label="Editar página" @click="editPage(item)">
                    <PencilIcon aria-hidden="true" />
                  </button>
                  <button type="button" class="page-action-btn" title="Copiar link" aria-label="Copiar link da página" @click="sharePage(item)">
                    <LinkIcon aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
            <p v-if="!topPages.length" class="empty-text">Sem páginas com dados ainda.</p>
          </div>
        </article>

        <article class="list-card">
          <header class="list-header">
            <div>
              <p class="card-eyebrow">Leads</p>
              <h3 class="list-title">Chegaram agora</h3>
            </div>
            <button type="button" class="list-link" @click="goToOpportunities">Ver todos →</button>
          </header>
          <div class="list-body">
            <div v-for="(lead, index) in recentLeads" :key="String(lead.id)" class="lead-item">
              <div class="lead-avatar" :class="`tone-${avatarTones[index % avatarTones.length]}`">{{ initials(lead.name) }}</div>
              <div class="lead-info">
                <div class="lead-copy">
                  <p class="lead-name">{{ truncateText(lead.name || 'Lead sem nome', 40) }}</p>
                  <p class="lead-meta">{{ truncateText(`${leadPageLabel(lead)} · ${relativeTime(lead.created_at)}`, 34) }}</p>
                </div>
                <div class="lead-actions">
                  <span v-if="lead.status_name" class="lead-stage" :style="stageStyle(lead.status_color)">{{ lead.status_name }}</span>
                  <a
                    v-if="leadWhatsappUrl(lead)"
                    class="lead-btn lead-btn-contact"
                    :href="leadWhatsappUrl(lead)"
                    target="_blank"
                    rel="noopener"
                  >
                    <MessageCircleIcon aria-hidden="true" />
                    WhatsApp
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
import {
  EyeIcon,
  FileTextIcon,
  LinkIcon,
  MessageCircleIcon,
  MousePointerClickIcon,
  PencilIcon,
  PlusIcon,
  TrendingUpIcon,
  UserPlusIcon
} from "lucide-vue-next";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";
import { useLeadCaptureStore } from "../../store/useLeadCaptureStore";
import type { LeadContact } from "../../types/leads";
import OpportunityDrawer from "../../components/admin/leads/OpportunityDrawer.vue";
import { normalizeExternalLink } from "../../utils/links";
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
  cta_type?: "internal_route" | "external_url" | "open_modal" | "system_action" | "none" | null;
  cta_target?: string | null;
  rule_config?: Record<string, any> | null;
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
const chartHeight = 230;
const chartPad = 12;
let chartResizeObserver: ResizeObserver | null = null;

const normalizeBannerHex = (value?: string | null, fallback = "#1a3d25") => {
  const raw = String(value || "").trim();
  return /^#[0-9a-f]{6}$/i.test(raw) ? raw : fallback;
};

const normalizeBannerGradientIntensity = (value?: number | null) => {
  const parsed = Number(value || 100);
  if (Number.isNaN(parsed)) return 100;
  return Math.min(100, Math.max(35, parsed));
};

const eligibleBannerVisual = computed(() => {
  const config = (eligibleBanner.value?.rule_config || {}) as { visual?: Record<string, any> };
  return config.visual || {};
});

const eligibleBannerBackground = computed(() => {
  const visual = eligibleBannerVisual.value;
  if (visual.background_type === "solid") {
    return normalizeBannerHex(visual.solid_color);
  }
  if (visual.background_type === "gradient") {
    const start = normalizeBannerHex(visual.gradient_start);
    const end = normalizeBannerHex(visual.gradient_end, "#3dcc5f");
    const intensity = normalizeBannerGradientIntensity(visual.gradient_intensity);
    return `linear-gradient(135deg, ${start} 0%, ${end} ${intensity}%)`;
  }
  return null;
});

const eligibleBannerIconSvg = computed(() => {
  const visual = eligibleBannerVisual.value;
  return visual.icon_mode === "svg" ? String(visual.icon_svg || "") : "";
});

const eligibleBannerShowIconBackground = computed(() => {
  const visual = eligibleBannerVisual.value;
  return visual.icon_mode === "svg" ? Boolean(visual.show_icon_background) : true;
});

const eligibleBannerCtaBackground = computed(() =>
  normalizeBannerHex(String(eligibleBannerVisual.value.cta_background_color || ""), "#3dcc5f")
);

const eligibleBannerCtaTextColor = computed(() =>
  normalizeBannerHex(String(eligibleBannerVisual.value.cta_text_color || ""), "#0f1f14")
);
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

const firstName = computed(() => (userName.value || "").trim().split(/\s+/)[0] || userName.value);
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
});
const todayLabel = computed(() => {
  const label = new Date().toLocaleDateString(numberLocale, { weekday: "long", day: "numeric", month: "long" });
  return label.charAt(0).toUpperCase() + label.slice(1);
});
const draftsCount = computed(() => Math.max(pages.value.length - pagesCount.value, 0));
const clickRate = computed(() => (totalVisits.value > 0 ? clicksMetric.value / totalVisits.value : 0));
const leadRate = computed(() => (totalVisits.value > 0 ? leadsMetric.value / totalVisits.value : 0));
const formatPercent = (value: number) =>
  `${(value * 100).toLocaleString(numberLocale, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;

const funnelSteps = computed(() => {
  const visits = totalVisits.value;
  const whatsapp = Number(overview.value?.whatsapp || 0);
  const cta = Number(overview.value?.cta || 0);
  const leads = leadsMetric.value;
  const base = Math.max(1, visits, whatsapp, cta, leads);
  return [
    { key: "visits", label: "Visitas", value: visits },
    { key: "whatsapp", label: "Cliques no WhatsApp", value: whatsapp },
    { key: "cta", label: "Cliques no botão", value: cta },
    { key: "leads", label: "Leads", value: leads }
  ].map(step => ({ ...step, width: Math.max(step.value > 0 ? 2 : 0, Math.round((step.value / base) * 100)) }));
});

const avatarTones = ["violet", "info", "warning", "success"];
const initials = (name?: string | null) => {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  return `${parts[0][0] || ""}${parts.length > 1 ? parts[parts.length - 1][0] : ""}`.toUpperCase();
};
// Cor da etapa vem da agência (Configurações do funil).
const stageStyle = (color?: string | null) => {
  const value = color || "var(--muted-foreground)";
  return {
    color: value,
    background: `color-mix(in srgb, ${value} 14%, transparent)`
  };
};

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
    const href = normalizeExternalLink(banner.cta_target);
    if (!href) return;
    window.open(href, "_blank", "noopener");
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
  const max = Math.max(1, ...visitsValues, ...clicksValues);
  // Leads usam a própria escala (linha tracejada): na escala das visitas
  // ficariam achatados no chão.
  const leadsMax = Math.max(1, ...leadsValues) * 1.6;

  return {
    visits: buildSeries(visitsValues, max),
    clicks: buildSeries(clicksValues, max),
    leads: buildSeries(leadsValues, leadsMax)
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

const pagesById = computed(() => {
  const map: Record<number, Page> = {};
  pages.value.forEach(page => {
    map[page.id] = page;
  });
  return map;
});

const leadPageLabel = (lead: LeadContact) => {
  const numericPageId = Number(lead.page_id);
  if (!Number.isNaN(numericPageId) && pagesById.value[numericPageId]?.title) {
    return pagesById.value[numericPageId].title;
  }
  if (lead.page_title && lead.page_title.trim()) return lead.page_title.trim();
  if (lead.page_slug && lead.page_slug.trim()) return lead.page_slug.trim();
  return "Sem página";
};

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

const goToPages = () => router.push("/admin/pages");
const openNewPage = () => router.push({ path: "/admin/pages", query: { nova: "1" } });
const goToOpportunities = () => router.push("/admin/leads/opportunities");
const goToIntegrations = () => router.push("/admin/integracoes");

const currentAgencySlug = computed(() => {
  const agency = agencyStore.currentAgency || agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return agency?.slug || "";
});

const copyToast = ref("");
let copyToastTimer: ReturnType<typeof setTimeout> | null = null;

const showCopyToast = (message: string) => {
  copyToast.value = message;
  if (copyToastTimer) clearTimeout(copyToastTimer);
  copyToastTimer = setTimeout(() => {
    copyToast.value = "";
    copyToastTimer = null;
  }, 2200);
};

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
    showCopyToast("Link copiado para a área de transferência.");
  } catch {
    window.prompt("Copie o link:", url);
    showCopyToast("Não foi possível copiar o link.");
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
  if (copyToastTimer) clearTimeout(copyToastTimer);
});
</script>

<style scoped>
.dashboard-reference {
  width: 100%;
  min-height: 100%;
  background: transparent;
  padding: 0;
  color: var(--foreground);
  font-family: var(--font-sans);
}

.copy-toast {
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  padding: 10px 14px;
  border-radius: 999px;
  box-shadow: var(--shadow-elegant);
  font-size: 12px;
  font-weight: 600;
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
  border: 4px solid var(--border);
  border-top-color: var(--primary);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Topo */
.topbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-end;
  margin-bottom: 20px;
}

.page-date {
  font-size: 13px;
  color: var(--muted-foreground);
}

.page-title {
  margin-top: 2px;
  font-family: var(--font-display);
  font-size: 34px;
  line-height: 42px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.page-title-name {
  color: var(--primary);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 18px;
  border-radius: 999px;
  font-size: 13.5px;
  font-weight: 600;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.btn svg {
  width: 16px;
  height: 16px;
}

.btn-primary {
  background: var(--primary);
  color: var(--primary-foreground);
}

.btn-primary:hover {
  background: color-mix(in srgb, var(--primary) 88%, black);
}

.btn-ghost {
  background: var(--card);
  color: var(--foreground);
  box-shadow: var(--shadow-card);
}

.btn-ghost:hover {
  background: var(--muted);
}

.period-switch {
  display: inline-flex;
  padding: 4px;
  border-radius: 999px;
  background: var(--card);
  box-shadow: var(--shadow-card);
}

.period-btn {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--muted-foreground);
}

.period-btn.active {
  background: var(--accent);
  color: var(--accent-foreground);
}

/* Cartões e números */
.metrics-grid {
  display: grid;
  grid-template-columns: 1.25fr 1fr 1fr 1fr;
  gap: 16px;
  margin: 20px 0;
}

.metric-card,
.chart-card,
.list-card {
  position: relative;
  min-width: 0;
  border-radius: 20px;
  background: var(--card);
  box-shadow: var(--shadow-card);
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 22px;
  overflow: hidden;
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-label {
  font-size: 12.5px;
  color: var(--muted-foreground);
}

.metric-icon {
  display: inline-grid;
  place-items: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 999px;
}

.metric-icon svg {
  width: 18px;
  height: 18px;
}

.tone-success { background: var(--status-success); color: var(--status-success-foreground); }
.tone-warning { background: var(--status-warning); color: var(--status-warning-foreground); }
.tone-info { background: var(--status-info); color: var(--status-info-foreground); }
.tone-violet { background: var(--status-violet); color: var(--status-violet-foreground); }

.metric-value {
  font-family: var(--font-display);
  font-size: 28px;
  line-height: 34px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.metric-value small {
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 500;
  color: var(--muted-foreground);
}

.metric-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted-foreground);
}

.metric-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 11.5px;
  font-weight: 600;
}

.metric-badge.up { background: var(--status-success); color: var(--status-success-foreground); }
.metric-badge.down { background: var(--status-danger); color: var(--status-danger-foreground); }
.metric-badge.neutral { background: var(--status-neutral); color: var(--status-neutral-foreground); }

.metric-footer-text {
  font-size: 12px;
  color: var(--muted-foreground);
}

/* Destaque: visitas em verde claro, como os cards de destaque do Viaje On */
.metric-hero {
  border-color: color-mix(in srgb, var(--primary) 22%, var(--border));
  background: linear-gradient(135deg, var(--accent) 0%, var(--card) 100%);
  box-shadow: inset 4px 0 0 var(--primary), var(--shadow-card);
}

.metric-hero .metric-icon {
  background: var(--card);
  color: var(--accent-foreground);
}

/* Gráfico e conversão */
.mid-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  padding: 22px;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.card-eyebrow {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: color-mix(in srgb, var(--muted-foreground) 80%, transparent);
}

.chart-title,
.list-title {
  margin-top: 2px;
  font-family: var(--font-sans);
  font-size: 17px;
  line-height: 24px;
  font-weight: 600;
  letter-spacing: 0;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-select {
  height: 34px;
  border-radius: 999px;
  border: 0;
  background: var(--muted);
  color: var(--foreground);
  padding: 0 32px 0 14px;
  font-size: 12.5px;
  font-weight: 600;
}

.chart-legend {
  display: flex;
  gap: 12px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: var(--muted-foreground);
}

.legend-toggle {
  transition: opacity 0.15s ease;
}

.legend-toggle.off {
  opacity: 0.4;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}

.legend-dot.visits { background: var(--chart-1); }
.legend-dot.clicks { background: var(--chart-4); }
.legend-dot.leads { background: var(--chart-6); }

.chart-stage {
  position: relative;
}

.chart-stage svg {
  display: block;
  overflow: visible;
}

.chart-tooltip {
  position: absolute;
  z-index: 2;
  pointer-events: none;
  min-width: 144px;
  border-radius: 12px;
  padding: 8px 10px;
  background: var(--popover);
  color: var(--popover-foreground);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-elegant);
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
  font-weight: 600;
}

.chart-dates {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
  font-size: 11.5px;
  color: var(--muted-foreground);
}

.chart-note {
  font-size: 11px;
  opacity: 0.8;
}

.funnel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.funnel-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}

.funnel-row b {
  font-variant-numeric: tabular-nums;
}

.funnel-bar {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--muted);
}

.funnel-bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
}

.fill-visits { background: var(--chart-1); }
.fill-whatsapp { background: var(--status-success-foreground); }
.fill-cta { background: var(--chart-4); }
.fill-leads { background: var(--chart-6); }

.funnel-total {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
  padding: 14px;
  border-radius: 16px;
  background: var(--muted);
}

.funnel-total b {
  display: block;
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
}

.funnel-total span {
  font-size: 12px;
  color: var(--muted-foreground);
}

/* Listas */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.list-card {
  padding: 22px;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.list-link {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-foreground);
}

.page-item,
.lead-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid var(--border);
}

.page-item:first-child,
.lead-item:first-child {
  border-top: 0;
}

.page-thumb,
.lead-avatar {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
}

.page-thumb {
  background: var(--status-success);
  color: var(--status-success-foreground);
}

.page-thumb svg {
  width: 18px;
  height: 18px;
}

.page-info,
.lead-info {
  flex: 1;
  min-width: 0;
}

.lead-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.lead-copy {
  flex: 1;
  min-width: 0;
}

.page-name,
.lead-name {
  overflow: hidden;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.page-dest,
.lead-meta {
  overflow: hidden;
  font-size: 12px;
  color: var(--muted-foreground);
  white-space: nowrap;
  text-overflow: ellipsis;
}

.page-bar {
  height: 4px;
  max-width: 240px;
  margin-top: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--muted);
}

.page-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: var(--chart-1);
}

.page-side {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-visits {
  min-width: 64px;
  font-family: var(--font-display);
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.page-visits small {
  display: block;
  font-family: var(--font-sans);
  font-size: 11.5px;
  font-weight: 400;
  color: var(--muted-foreground);
}

.page-actions,
.lead-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-action-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: var(--muted);
  color: var(--muted-foreground);
  transition: background 0.15s ease, color 0.15s ease;
}

.page-action-btn:hover {
  background: var(--accent);
  color: var(--accent-foreground);
}

.page-action-btn svg {
  width: 16px;
  height: 16px;
}

.lead-stage {
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 11.5px;
  font-weight: 600;
  white-space: nowrap;
}

.lead-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  white-space: nowrap;
}

.lead-btn svg {
  width: 14px;
  height: 14px;
}

.lead-btn-contact {
  background: var(--status-success);
  color: var(--status-success-foreground);
}

.lead-btn-details {
  background: var(--muted);
  color: var(--foreground);
}

.empty-text {
  padding: 16px 0;
  font-size: 13px;
  color: var(--muted-foreground);
}

@media (max-width: 1100px) {
  .metrics-grid {
    grid-template-columns: 1fr 1fr;
  }

  .mid-grid,
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-title {
    font-size: 26px;
    line-height: 32px;
  }

  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .lead-info {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-note {
    display: none;
  }
}

@media (max-width: 420px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .page-actions {
    display: none;
  }
}
</style>
