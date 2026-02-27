<template>
  <div v-if="loading" class="flex min-h-screen items-center justify-center text-slate-600">Carregando pagina...</div>
  <div v-else-if="!pageData" class="flex min-h-screen items-center justify-center text-red-500">Pagina nao encontrada.</div>
  <div v-else class="min-h-screen">
    <template v-for="(section, idx) in sections" :key="idx">
      <PublicHeroSection
        v-if="section?.enabled && section.type === 'hero'"
        :section="section"
        :branding="pageData.branding"
      />
      <component
        v-else-if="section?.enabled"
        :is="publicComponents[section.type]"
        :section="section"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import api from "../../services/api";
import PublicHeroSection from "../../components/public/PublicHeroSection.vue";
import PublicPricesSection from "../../components/public/PublicPricesSection.vue";
import PublicItinerarySection from "../../components/public/PublicItinerarySection.vue";
import PublicFaqSection from "../../components/public/PublicFaqSection.vue";
import PublicTestimonialsSection from "../../components/public/PublicTestimonialsSection.vue";
import PublicCtaSection from "../../components/public/PublicCtaSection.vue";
import PublicStorySection from "../../components/public/PublicStorySection.vue";
import PublicReasonsSection from "../../components/public/PublicReasonsSection.vue";
import PublicCountdownSection from "../../components/public/PublicCountdownSection.vue";
import PublicFreeFooterBrandSection from "../../components/public/PublicFreeFooterBrandSection.vue";
import type { PageConfig, PageSection, SectionType, ThemeConfig } from "../../types/page";

interface PublicPageResponse {
  id: number;
  title: string;
  slug: string;
  branding: Record<string, unknown>;
  config: string | PageConfig;
  cover_image_url?: string;
}

const route = useRoute();
const loading = ref(true);
const pageData = ref<PublicPageResponse | null>(null);
const sections = ref<PageSection[]>([]);
const pageId = ref<number | null>(null);
const theme = ref<ThemeConfig>({
  color1: "#f8fafc",
  color2: "#ffffff",
  sidebarTheme: "light"
});

const publicComponents: Record<SectionType, any> = {
  hero: PublicHeroSection,
  prices: PublicPricesSection,
  itinerary: PublicItinerarySection,
  faq: PublicFaqSection,
  testimonials: PublicTestimonialsSection,
  cta: PublicCtaSection,
  story: PublicStorySection,
  reasons: PublicReasonsSection,
  countdown: PublicCountdownSection,
  free_footer_brand: PublicFreeFooterBrandSection
};

let statsClickHandler: ((event: Event) => void) | null = null;
let scrollAnchorHandler: ((event: Event) => void) | null = null;

const cleanupStatsTracking = () => {
  if (statsClickHandler) {
    document.removeEventListener("click", statsClickHandler);
    statsClickHandler = null;
  }
};

const cleanupScrollAnchors = () => {
  if (scrollAnchorHandler) {
    document.removeEventListener("click", scrollAnchorHandler);
    scrollAnchorHandler = null;
  }
};

const handleTrackedClick = (type: "cta" | "whatsapp") => {
  if (!pageId.value) return;
  const endpoint = type === "whatsapp" ? `/stats/${pageId.value}/track-whatsapp-click` : `/stats/${pageId.value}/track-cta`;
  api.post(endpoint).catch(() => undefined);
};

const setupStatsClickTracking = (id: number) => {
  cleanupStatsTracking();
  statsClickHandler = (event: Event) => {
    const target = event.target as HTMLElement | null;
    const el = target && (target.closest?.("[data-track-event='cta']") as HTMLElement | null);
    if (!el) return;
    const type = (el.getAttribute("data-track-type") as "cta" | "whatsapp") || "cta";
    handleTrackedClick(type === "whatsapp" ? "whatsapp" : "cta");
  };
  document.addEventListener("click", statsClickHandler);
};

const setupScrollAnchors = () => {
  cleanupScrollAnchors();
  scrollAnchorHandler = event => {
    const target = event.target as HTMLElement | null;
    const el = target?.closest?.("[data-scroll-target='true']") as HTMLElement | null;
    if (!el) return;
    const href = el.getAttribute("href");
    if (!href || !href.startsWith("#")) return;
    const anchor = document.querySelector(href);
    if (!anchor) return;
    event.preventDefault();
    anchor.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  document.addEventListener("click", scrollAnchorHandler);
};

const trackVisit = () => {
  if (!pageId.value) return;
  api.post(`/stats/${pageId.value}/track-visit`).catch(() => undefined);
};

const resolveParam = (value: string | string[] | undefined) => {
  if (Array.isArray(value)) return value[0];
  return value;
};

const loadPage = async () => {
  loading.value = true;
  const agencySlug = resolveParam(route.params.agencySlug as string | string[] | undefined);
  const pageSlug = resolveParam(route.params.pageSlug as string | string[] | undefined);
  if (!agencySlug) {
    pageData.value = null;
    loading.value = false;
    return;
  }
  try {
    const endpoint = pageSlug
      ? `/public/pages/by-slug/${agencySlug}/${pageSlug}`
      : `/public/pages/default/${agencySlug}`;
    const res = await api.get<PublicPageResponse>(endpoint);
    pageData.value = res.data;
    pageId.value = res.data.id;
    const configJson = typeof res.data.config === "string" ? res.data.config : JSON.stringify(res.data.config);
    const parsed = JSON.parse(configJson) as PageConfig;
    theme.value = { ...theme.value, ...(parsed.theme || {}) };
    sections.value = applyBackgrounds(parsed.sections || []);
    if (pageId.value) {
      trackVisit();
      setupStatsClickTracking(pageId.value);
      setupScrollAnchors();
    }

    // Pixel / GA injection
    const tracking: any = (parsed as any).tracking;
    const pixel = tracking?.pixel;
    const events = tracking?.events || {};
    const sendPageView = events.pageView !== false;
    if (pixel?.type === "meta" && pixel.value) {
      injectMetaPixel(pixel.value, sendPageView);
    }
    if (pixel?.type === "ga" && pixel.value) {
      injectGa(pixel.value, sendPageView);
    }
    if (events.ctaClicks !== false && pixel?.value) {
      setupCtaTracking(pixel);
    }
  } catch (err) {
    console.error(err);
    pageData.value = null;
    pageId.value = null;
    cleanupStatsTracking();
    cleanupScrollAnchors();
  } finally {
    loading.value = false;
  }
};

const getSection = (type: SectionType) => sections.value.find(section => section.type === type);
const sectionEnabled = (type: SectionType) => {
  const section = getSection(type);
  return !!section && (section as PageSection).enabled;
};

onMounted(loadPage);
watch(
  () => [route.params.agencySlug, route.params.pageSlug],
  () => {
    loadPage();
  }
);
onUnmounted(() => {
  cleanupStatsTracking();
  cleanupScrollAnchors();
});

function applyBackgrounds(list: PageSection[]): PageSection[] {
  let altIndex = 0;
  return (list || []).map(section => {
    if (!section) return section;
    if (!section.anchorId) {
      section = { ...section, anchorId: `section-${Math.random().toString(36).slice(2, 9)}` };
    }
    if (section.type === "hero" || section.type === "countdown" || section.type === "free_footer_brand") return section;
    const backgroundColor = section.backgroundColor || (altIndex % 2 === 0 ? theme.value.color1 : theme.value.color2);
    altIndex += 1;
    return { ...section, backgroundColor };
  });
}

function injectMetaPixel(id: string, sendPageView = true) {
  if (document.getElementById("meta-pixel-" + id)) return;
  const script = document.createElement("script");
  script.id = "meta-pixel-" + id;
  script.innerHTML = `
    !function(f,b,e,v,n,t,s)
    {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', '${id}');
    ${sendPageView ? "fbq('track', 'PageView');" : ""}
  `;
  document.head.appendChild(script);
  const noscript = document.createElement("noscript");
  if (sendPageView) {
    noscript.innerHTML = `<img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=${id}&ev=PageView&noscript=1"/>`;
  }
  document.head.appendChild(noscript);
}

function injectGa(measurementId: string, sendPageView = true) {
  if (document.getElementById("ga-measure-" + measurementId)) return;
  const gtagScript = document.createElement("script");
  gtagScript.async = true;
  gtagScript.id = "ga-measure-" + measurementId;
  gtagScript.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`;
  document.head.appendChild(gtagScript);
  const script = document.createElement("script");
  script.innerHTML = `
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', '${measurementId}', { send_page_view: ${sendPageView ? "true" : "false"} });
  `;
  document.head.appendChild(script);
}

function setupCtaTracking(pixel: { type: string; value: string }) {
  const handler = (event: Event) => {
    const target = event.target as HTMLElement | null;
    const el = target && (target.closest?.("[data-track-event='cta']") as HTMLElement | null);
    if (!el) return;
    if (pixel.type === "meta" && (window as any).fbq) {
      (window as any).fbq("trackCustom", "CTA_Click");
    }
    if (pixel.type === "ga" && (window as any).gtag) {
      (window as any).gtag("event", "cta_click");
    }
  };
  document.addEventListener("click", handler);
}
</script>

<style scoped>
.public-page :deep(section) {
  margin-top: 0;
  margin-bottom: 0;
  display: block;
}
</style>
