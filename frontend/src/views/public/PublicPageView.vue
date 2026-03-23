<template>
  <div v-if="loading" class="flex min-h-screen items-center justify-center text-slate-600">Carregando pagina...</div>
  <div
    v-else-if="!pageData"
    class="flex min-h-screen flex-col items-center justify-center bg-[#05060f] px-4 text-center text-white"
  >
    <img :src="brandLogo" alt="Roteiro Online" class="w-56 max-w-full" />
    <p class="mt-6 text-2xl font-semibold">Página não encontrada.</p>
    <p class="mt-2 max-w-md text-base text-white/90">
      O link que você acessou não existe mais ou foi removido. Peça um novo roteiro para a agência responsável.
    </p>
  </div>
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
        v-bind="sectionRequiresBranding(section.type) ? { branding: pageData.branding } : {}"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, provide, ref, watch } from "vue";
import { useRoute } from "vue-router";
import api from "../../services/api";
import PublicHeroSection from "../../components/public/PublicHeroSection.vue";
import PublicBannerCardSection from "../../components/public/PublicBannerCardSection.vue";
import PublicPricesSection from "../../components/public/PublicPricesSection.vue";
import PublicItinerarySection from "../../components/public/PublicItinerarySection.vue";
import PublicFaqSection from "../../components/public/PublicFaqSection.vue";
import PublicTestimonialsSection from "../../components/public/PublicTestimonialsSection.vue";
import PublicFeaturedVideoSection from "../../components/public/PublicFeaturedVideoSection.vue";
import PublicCtaSection from "../../components/public/PublicCtaSection.vue";
import PublicStorySection from "../../components/public/PublicStorySection.vue";
import PublicReasonsSection from "../../components/public/PublicReasonsSection.vue";
import PublicCountdownSection from "../../components/public/PublicCountdownSection.vue";
import PublicFreeFooterBrandSection from "../../components/public/PublicFreeFooterBrandSection.vue";
import PublicAgencyFooterSection from "../../components/public/PublicAgencyFooterSection.vue";
import PublicPhotoSection from "../../components/public/PublicPhotoSection.vue";
import PublicBiographySection from "../../components/public/PublicBiographySection.vue";
import type { HeroSection, PageConfig, PageSection, SectionType, ThemeConfig } from "../../types/page";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import BrandLogo from "../../assets/Logo Branco - Roteiro Online.png";
import { resolveMediaUrl } from "../../utils/media";

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
const brandLogo = BrandLogo;
const defaultDescription =
  "Link inválido ou página indisponível. Solicite um novo roteiro profissional no Roteiro Online.";

const defaultPlatformHosts = ["roteiroonline.com", "www.roteiroonline.com", "localhost", "127.0.0.1"];
const envPlatformHosts = (import.meta.env.VITE_PLATFORM_HOSTS || "")
  .split(",")
  .map(host => host.trim().toLowerCase())
  .filter(Boolean);
const platformHosts = Array.from(new Set([...defaultPlatformHosts, ...envPlatformHosts]));

const isPlatformHost = computed(() => {
  if (typeof window === "undefined") return true;
  const currentHost = window.location.hostname.toLowerCase();
  return platformHosts.includes(currentHost);
});

const brandingInfo = computed(() => pageData.value?.branding || {});
provide(PUBLIC_BRANDING_KEY, brandingInfo);

const publicComponents: Record<SectionType, any> = {
  hero: PublicHeroSection,
  banner_card: PublicBannerCardSection,
  photo: PublicPhotoSection,
  biography: PublicBiographySection,
  prices: PublicPricesSection,
  itinerary: PublicItinerarySection,
  faq: PublicFaqSection,
  testimonials: PublicTestimonialsSection,
  featured_video: PublicFeaturedVideoSection,
  cta: PublicCtaSection,
  story: PublicStorySection,
  reasons: PublicReasonsSection,
  countdown: PublicCountdownSection,
  free_footer_brand: PublicFreeFooterBrandSection,
  agency_footer: PublicAgencyFooterSection
};

const sectionRequiresBranding = (type?: SectionType) => type === "hero" || type === "agency_footer";

let statsClickHandler: ((event: Event) => void) | null = null;
let scrollAnchorHandler: ((event: Event) => void) | null = null;
const heroSection = computed(() => sections.value.find(section => section.type === "hero") as HeroSection | undefined);
const heroBackgroundImage = computed(() => {
  const hero = heroSection.value;
  if (hero?.backgroundImage) {
    return resolveMediaUrl(hero.backgroundImage);
  }
  if (pageData.value?.cover_image_url) {
    return resolveMediaUrl(pageData.value.cover_image_url);
  }
  return brandLogo;
});
const heroSubtitleText = computed(() => {
  const hero = heroSection.value;
  const raw = hero?.subtitle || "";
  return raw.replace(/<[^>]+>/g, "").trim();
});

const findClosestElement = (target: EventTarget | null, selector: string): HTMLElement | null => {
  if (!target) return null;
  if (target instanceof Element) {
    return target.closest(selector) as HTMLElement | null;
  }
  if (target instanceof Node && target.parentElement) {
    return target.parentElement.closest(selector) as HTMLElement | null;
  }
  return null;
};

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
    const el = findClosestElement(event.target, "[data-track-event='cta']");
    if (!el) return;
    const type = (el.getAttribute("data-track-type") as "cta" | "whatsapp") || "cta";
    handleTrackedClick(type === "whatsapp" ? "whatsapp" : "cta");
  };
  document.addEventListener("click", statsClickHandler);
};

const setupScrollAnchors = () => {
  cleanupScrollAnchors();
  scrollAnchorHandler = event => {
    const el = findClosestElement(event.target, "[data-scroll-target='true']");
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

const ensureMetaTag = (selector: string, attr: "property" | "name", value: string) => {
  if (typeof document === "undefined") return;
  let tag = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${selector}"]`);
  if (!tag) {
    tag = document.createElement("meta");
    tag.setAttribute(attr, selector);
    document.head.appendChild(tag);
  }
  tag.setAttribute("content", value);
};

const applySeoMeta = (title?: string | null, description?: string | null, imageUrl?: string | null) => {
  if (typeof document === "undefined") return;
  const finalTitle = title ? `${title} | Roteiro Online` : "Roteiro Online";
  const finalDescription = (description && description.trim()) || defaultDescription;
  const finalImage = imageUrl || brandLogo;
  document.title = finalTitle;
  ensureMetaTag("og:title", "property", finalTitle);
  ensureMetaTag("og:description", "property", finalDescription);
  ensureMetaTag("og:image", "property", finalImage);
  ensureMetaTag("og:type", "property", "website");
  ensureMetaTag("twitter:card", "name", "summary_large_image");
  ensureMetaTag("twitter:title", "name", finalTitle);
  ensureMetaTag("twitter:description", "name", finalDescription);
  ensureMetaTag("twitter:image", "name", finalImage);
  ensureMetaTag("description", "name", finalDescription);
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
  const rawAgencyParam = resolveParam(route.params.agencySlug as string | string[] | undefined);
  const rawPageParam = resolveParam(route.params.pageSlug as string | string[] | undefined);
  const platformHost = isPlatformHost.value;

  if (platformHost && !rawAgencyParam) {
    pageData.value = null;
    loading.value = false;
    return;
  }

  const endpoint = (() => {
    if (platformHost) {
      return rawPageParam
        ? `/public/pages/by-slug/${rawAgencyParam}/${rawPageParam}`
        : `/public/pages/default/${rawAgencyParam}`;
    }
    const customPageSlug = rawPageParam || rawAgencyParam;
    return customPageSlug ? `/public/pages/by-host/${customPageSlug}` : `/public/pages/by-host`;
  })();

  try {
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
    const tracking: any = (parsed as any).tracking || {};
    const events = tracking.events || {};
    const sendPageView = events.pageView !== false;
    const legacyPixel = tracking.pixel;
    const metaPixel = tracking.metaPixel || (legacyPixel?.type === "meta" ? legacyPixel : null);
    const gaPixel = tracking.gaPixel || (legacyPixel?.type === "ga" ? legacyPixel : null);
    const activePixels = [metaPixel, gaPixel].filter(p => p && p.value);
    if (metaPixel?.value) {
      injectMetaPixel(metaPixel.value, sendPageView);
    }
    if (gaPixel?.value) {
      injectGa(gaPixel.value, sendPageView);
    }
    if (events.ctaClicks !== false && activePixels.length) {
      setupCtaTracking(activePixels as { type: string; value: string }[]);
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
watch(
  () => [pageData.value, heroBackgroundImage.value, heroSubtitleText.value],
  () => {
    applySeoMeta(pageData.value?.title, heroSubtitleText.value, heroBackgroundImage.value);
  },
  { immediate: true }
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

function setupCtaTracking(pixels: { type: string; value: string }[]) {
  if (!pixels.length) return;
  const handler = (event: Event) => {
    const el = findClosestElement(event.target, "[data-track-event='cta']");
    if (!el) return;
    pixels.forEach(pixel => {
      if (pixel.type === "meta" && (window as any).fbq) {
        (window as any).fbq("trackCustom", "CTA_Click");
      }
      if (pixel.type === "ga" && (window as any).gtag) {
        (window as any).gtag("event", "cta_click");
      }
    });
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
