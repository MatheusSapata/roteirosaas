<template>
  <section class="relative overflow-hidden bg-[#05060f]" :id="section.anchorId || undefined" :style="animationVars">
    <!-- MOBILE -->
    <div :class="mobileWrapperClasses">
      <div class="overflow-hidden bg-[#05060f] shadow-2xl shadow-black/30">
        <!-- capa -->
        <div class="relative w-full overflow-hidden" style="aspect-ratio: 3 / 4; max-height: 50vh;">
          <div class="absolute inset-0 bg-cover bg-center" :style="mobileBackgroundStyle"></div>
          <div class="absolute inset-0" :style="mobileGradientStyle"></div>
          <div v-if="embeddedVideoUrl" class="absolute inset-0" :style="mobileVideoOverlayStyle"></div>

          <div class="absolute inset-0 flex flex-col items-center gap-4 px-4 py-6">
            <div class="flex justify-center w-full mt-auto mb-2" :class="animationClasses(1)">
              <template v-if="logoSrc">
                <div class="drop-shadow-xl overflow-hidden" :style="logoBoxStyle">
                  <img :src="logoSrc" alt="Logo" class="h-full w-auto object-contain" :style="logoImageStyle" />
                </div>
              </template>
              <span
                v-else
                class="rounded-full bg-white/15 px-4 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-white"
              >
                {{ branding.agency_name || fallbackBrandName }}
              </span>
            </div>

            <div v-if="embeddedVideoUrl" class="w-full max-w-[320px] mb-2">
              <div class="overflow-hidden rounded-2xl border border-white/10 bg-black/30 shadow-xl ring-1 ring-white/10">
                <div class="relative pt-[56.25%]">
                  <iframe
                    class="absolute inset-0 h-full w-full rounded-2xl object-cover"
                    :src="embeddedVideoUrl"
                    title="Vídeo de apresentação"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                  ></iframe>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- conteúdo -->
        <div
          class="relative -mt-6 overflow-hidden px-5 pb-12 pt-1 text-center text-white md:mt-0 md:pb-8"
          :style="{ background: mobileContentBg }"
        >
          <div class="space-y-0.5 md:mt-0">
            <h1 class="text-[32px] font-bold leading-tight" :class="animationClasses(2)">{{ heroTitle }}</h1>
            <div
              v-if="subtitleHtml"
              class="text-sm text-white/85 leading-tight"
              :class="animationClasses(3)"
              v-html="subtitleHtml"
            ></div>
          </div>

          <div
            v-if="chipsToShow.length"
            class="mt-4 flex flex-wrap items-center justify-center gap-1.5 text-[11px]"
            :class="animationClasses(4)"
          >
            <span
              v-for="(chip, idx) in chipsToShow"
              :key="idx"
              class="inline-flex items-center gap-2 rounded-full border px-4 py-1 text-xs font-semibold uppercase tracking-wide backdrop-blur"
              :style="{ borderColor: accentChipBorder, background: accentChipBg, color: '#fff' }"
            >
              <span class="inline-block h-2 w-2 rounded-full" :style="{ background: ctaColor }"></span>
              {{ chip }}
            </span>
          </div>

          <div class="mt-5 space-y-0.5" :class="animationClasses(5)">
            <a
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              :class="['inline-flex w-full items-center justify-center rounded-full px-5 py-3 text-sm font-semibold shadow-xl shadow-black/40 transition hover:-translate-y-0.5 hover:shadow-2xl', ctaShimmerClass]"
              :style="{ background: ctaColor, color: ctaTextColor }"
            >
              {{ ctaLabel }}
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- DESKTOP -->
    <div :class="desktopWrapperClasses">
      <div class="relative w-full">
        <!-- Fundo -->
        <div
          class="absolute inset-0 bg-cover bg-center"
          :style="layout === 'immersive' ? immersiveBackground : { background: softBackground }"
        ></div>

        <div v-if="layout === 'immersive'" class="pointer-events-none absolute inset-0" :style="immersiveGradient"></div>

        <div v-else class="pointer-events-none absolute inset-0">
          <div class="absolute inset-0 bg-gradient-to-br from-slate-900/12 via-white/0 to-white/0"></div>
          <div class="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(148,163,184,0.12),transparent_32%)]"></div>
        </div>

        <div :class="containerClasses" :style="accentVars">
          <!-- Layout imersivo -->
          <div
            v-if="layout === 'immersive'"
            class="relative z-10 flex flex-col gap-6 py-6 md:min-h-[540px] md:flex-row md:items-center md:gap-12 md:py-10"
            :class="isMobilePreview ? '!flex-col !gap-6 !py-6' : ''"
          >
            <div
              class="max-w-3xl space-y-5 text-white md:w-7/12 text-center md:text-left"
              :class="isMobilePreview ? '!w-full !text-center' : ''"
            >
              <div class="flex items-center gap-3" :class="animationClasses(1)">
                <img
                  v-if="logoSrc"
                  :src="logoSrc"
                  alt="Logo"
                  class="w-auto drop-shadow-lg object-contain"
                  :style="logoImageStyle"
                />
                <div v-else class="rounded-full bg-white/20 px-4 py-1 text-sm font-semibold uppercase tracking-[0.25em]">
                  {{ branding.agency_name || fallbackBrandName }}
                </div>
              </div>

              <h1
                class="text-3xl font-bold leading-tight md:text-5xl"
                :class="[isMobilePreview ? '!text-3xl' : '', ...animationClasses(2)]"
              >
                {{ heroTitle }}
              </h1>

              <div
                v-if="subtitleHtml"
                class="text-base text-slate-100 md:text-xl"
                :class="[isMobilePreview ? '!text-base' : '', ...animationClasses(3)]"
                v-html="subtitleHtml"
              ></div>

              <div
                v-if="chipsToShow.length"
                class="flex flex-wrap justify-center gap-3 md:justify-start"
                :class="[isMobilePreview ? '!justify-center' : '', ...animationClasses(4)]"
              >
                <span
                  v-for="(chip, idx) in chipsToShow"
                  :key="idx"
                  class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold backdrop-blur"
                  :style="{ borderColor: accentBorder, background: accentChipBg }"
                >
                  <span class="inline-block h-2 w-2 rounded-full" :style="{ background: ctaColor }"></span>
                  {{ chip }}
                </span>
              </div>

              <div
                class="flex flex-col items-center gap-3 sm:flex-row sm:items-center sm:justify-start"
                :class="[isMobilePreview ? '!flex-col !items-center !justify-center' : '', ...animationClasses(5)]"
              >
                <a
                  :href="ctaHref"
                  :data-scroll-target="ctaIsScroll ? 'true' : null"
                  target="_blank"
                  rel="noopener"
                  data-track-event="cta"
                  :data-track-type="ctaTrackType"
                  :class="['inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-xl transition hover:-translate-y-0.5 hover:shadow-2xl', ctaShimmerClass, desktopCtaHoverClass]"
                  :style="{ background: ctaColor, color: ctaTextColor }"
                >
                  {{ ctaLabel }}
                </a>
              </div>
            </div>

            <div class="md:w-6/12 lg:w-5/12" v-if="section.videoUrl" :class="isMobilePreview ? '!w-full !mt-6' : ''">
              <div
                class="relative overflow-hidden rounded-3xl bg-transparent shadow-2xl ring-1 ring-white/40"
                :class="!isMobilePreview ? 'md:scale-[1.05] md:origin-center' : ''"
              >
                <div class="relative pt-[56.25%]">
                  <iframe
                    class="absolute inset-0 h-full w-full rounded-3xl object-cover"
                    :src="embeddedVideoUrl"
                    title="Vídeo"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                  ></iframe>
                </div>
              </div>
            </div>
            <div v-else class="md:w-6/12 lg:w-5/12" :class="isMobilePreview ? '!w-full' : ''"></div>
          </div>

          <!-- Layout clássico -->
          <div
            v-else-if="layout === 'classic'"
            class="relative z-10 flex flex-col gap-6 rounded-3xl bg-white/75 p-6 text-center shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)] ring-1 ring-white/60 backdrop-blur md:p-8 md:text-left"
            :class="isMobilePreview ? '!p-6 !text-center' : ''"
          >
            <!-- (o resto do teu classic/split/card pode ficar igual, só cuida os fechamentos) -->
            <!-- ... -->
          </div>

          <!-- Layout split -->
          <div
            v-else-if="layout === 'split'"
            class="relative z-10 grid items-center gap-6 rounded-3xl bg-white/75 p-6 text-center shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)] ring-1 ring-white/60 backdrop-blur md:grid-cols-2 md:gap-8 md:p-8 md:text-left"
            :class="isMobilePreview ? '!grid-cols-1 !text-center !p-6' : ''"
          >
            <!-- ... -->
          </div>

          <!-- Layout card -->
          <div v-else class="relative z-10 flex flex-col items-center text-center">
            <!-- ... -->
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
<script setup lang="ts">
import { computed } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { isWhatsappLink } from "../../utils/links";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { normalizeYoutubeEmbedUrl } from "../../utils/video";
import { getReadableTextColor } from "../../utils/colorContrast";
import type { HeroSection } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: HeroSection; branding: Record<string, any>; previewDevice?: "desktop" | "mobile" }>();
const heroCopy = {
  defaultCta: { pt: "Quero falar agora", es: "Quiero hablar ahora" },
  fallbackBrand: { pt: "Sua marca", es: "Tu marca" }
} as const;
const currentLanguage = getCurrentLanguage();
const localize = createLocalizer(currentLanguage);

const heroTitle = computed(() => localize(props.section.title));
const subtitleHtml = computed(() => sanitizeHtml(localize(props.section.subtitle)));

const layout = computed(() => "immersive");
const heroBackgroundImage = computed(() => resolveMediaUrl(props.section.backgroundImage));
const logoSrc = computed(() => resolveMediaUrl(props.section.logoUrl));
const logoSize = computed(() => props.section.logoSize ?? 64);
const logoBorderRadius = computed(() => props.section.logoBorderRadius ?? 0);
const logoBoxStyle = computed(() => ({
  height: `${logoSize.value}px`,
  borderRadius: `${logoBorderRadius.value}px`
}));
const logoImageStyle = computed(() => ({
  height: `${logoSize.value}px`,
  borderRadius: `${logoBorderRadius.value}px`
}));
const accent = computed(() => props.section.gradientColor || props.section.backgroundColor || "#41ce5f");
const ctaColor = computed(() => props.section.ctaColor || accent.value);
const ctaTextColor = computed(() => getReadableTextColor(ctaColor.value));
const ctaMode = computed(() => props.section.ctaMode || "link");
const ctaHref = computed(() =>
  ctaMode.value === "section" && props.section.ctaSectionId ? `#${props.section.ctaSectionId}` : props.section.ctaLink || "#"
);
const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);
const ctaTrackType = computed(() => (ctaMode.value === "section" ? "cta" : trackType(props.section.ctaLink)));
const ctaLabel = computed(() => localize(props.section.ctaLabel) || localize(heroCopy.defaultCta));
const isMobilePreview = computed(() => props.previewDevice === "mobile");
const mobileWrapperClasses = computed(() => ["relative block md:hidden px-0 pt-0 -mt-8", isMobilePreview.value ? "!block" : ""]);
const desktopWrapperClasses = computed(() => ["relative hidden md:block", isMobilePreview.value ? "!hidden" : ""]);
const mobileBaseColor = computed(() => {
  const candidate = props.section.gradientColor || props.section.backgroundColor;
  if (candidate && candidate.startsWith("#")) return candidate;
  return "#05060f";
});

const embeddedVideoUrl = computed(() => normalizeYoutubeEmbedUrl(props.section.videoUrl));

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(14,165,233,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const accentSoft = computed(() => toRgba(accent.value, 0.12));
const accentBorder = computed(() => toRgba(accent.value, 0.25));
const accentChipBg = computed(() => toRgba(accent.value, 0.18));
const accentChipBorder = computed(() => {
  const source = ctaColor.value || accent.value;
  if (source.startsWith("#")) {
    return toRgba(source, 0.5);
  }
  return toRgba(accent.value, 0.5);
});
const mobileContentBg = computed(() => mobileBaseColor.value);
const mobileBackgroundStyle = computed(() => {
  if (heroBackgroundImage.value) {
    return {
      backgroundImage: `url(${heroBackgroundImage.value})`,
      backgroundSize: "cover",
      backgroundPosition: "center"
    };
  }
  return { background: `linear-gradient(135deg, ${toRgba(accent.value, 0.2)}, rgba(5,6,15,0.8))` };
});
const mobileGradientStyle = computed(() => {
  const base = mobileBaseColor.value;
  return {
    background: `linear-gradient(
      180deg,
      ${toRgba(base, 0)} 0%,
      ${toRgba(base, 0)} 50%,
      ${toRgba(base, 0.1)} 53%,
      ${toRgba(base, 0.2)} 56%,
      ${toRgba(base, 0.3)} 59%,
      ${toRgba(base, 0.4)} 62%,
      ${toRgba(base, 0.5)} 65%,
      ${toRgba(base, 0.6)} 68%,
      ${toRgba(base, 0.7)} 71%,
      ${toRgba(base, 0.78)} 74%,
      ${toRgba(base, 0.85)} 77%,
      ${toRgba(base, 0.9)} 80%,
      ${toRgba(base, 0.94)} 83%,
      ${toRgba(base, 0.97)} 86%,
      ${toRgba(base, 0.985)} 89%,
      ${toRgba(base, 0.993)} 92%,
      ${toRgba(base, 0.998)} 95%,
      ${toRgba(base, 1)} 100%
    )`
  };
});

const mobileVideoOverlayStyle = computed(() => {
  if (!embeddedVideoUrl.value) return null;
  const strong = toRgba(accent.value, 0.65);
  const soft = toRgba(accent.value, 0.25);
  return {
    background: `linear-gradient(180deg, ${strong} 0%, ${soft} 100%)`
  };
});
const accentVars = computed(() => ({
  "--accent": accent.value,
  "--accent-soft": accentSoft.value,
  "--accent-border": accentBorder.value
}));

const containerClasses = computed(() => [
  "relative flex flex-col gap-8 px-5 py-8 md:px-10 md:py-16",
  isMobilePreview.value ? "!px-5 !py-8" : "",
  layout.value === "immersive" ? "mx-auto max-w-6xl" : props.section.fullWidth ? "w-full" : "mx-auto max-w-6xl"
]);

const softBackground = computed(() => {
  if (heroBackgroundImage.value) {
    return `linear-gradient(120deg, rgba(15,23,42,0.12), rgba(8,47,73,0.15)), url(${heroBackgroundImage.value})`;
  }
  return `linear-gradient(135deg, ${toRgba(accent.value, 0.08)}, rgba(255,255,255,0.95))`;
});

const immersiveBackground = computed(() => {
  if (heroBackgroundImage.value) {
    return { backgroundImage: `url(${heroBackgroundImage.value})` };
  }
  return { background: `linear-gradient(135deg, ${accentSoft.value}, rgba(255,255,255,0.85))` };
});

const immersiveGradient = computed(() => {
  const main = toRgba(accent.value, 0.9);
  const soft = toRgba(accent.value, 0.65);
  return {
    background: `linear-gradient(90deg, ${main} 0%, ${soft} 40%, rgba(0,0,0,0.38) 65%, rgba(0,0,0,0) 100%)`
  };
});

const chipsToShow = computed(() =>
  (props.section.chips || [])
    .map(chip => localize(chip))
    .filter(chip => typeof chip === "string" && chip.trim().length)
);
const fallbackBrandName = computed(() => localize(heroCopy.fallbackBrand));
const trackType = (link?: string | null) => (isWhatsappLink(link || undefined) ? "whatsapp" : "cta");
const animateContent = computed(() => true);
const HERO_ANIMATION_MS = 1000;
const animationDuration = computed(() => HERO_ANIMATION_MS);
const animationVars = computed(() => ({ "--hero-anim-duration": `${animationDuration.value}ms` }));
const animationClasses = (step: number) => ["hero-fade", `hero-delay-${Math.min(Math.max(step, 1), 6)}`];
const ctaShimmerClass = computed(() => "hero-cta-shimmer");
const desktopCtaHoverClass = computed(() => "hero-cta-desktop-hover");
</script>

<style scoped>
@keyframes hero-fade-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-fade {
  opacity: 0;
  transform: translateY(16px);
  animation: hero-fade-in var(--hero-anim-duration, 0.6s) ease forwards;
}

.hero-delay-1 {
  animation-delay: 0.05s;
}

.hero-delay-2 {
  animation-delay: 0.15s;
}

.hero-delay-3 {
  animation-delay: 0.25s;
}

.hero-delay-4 {
  animation-delay: 0.35s;
}

.hero-delay-5 {
  animation-delay: 0.45s;
}

.hero-delay-6 {
  animation-delay: 0.55s;
}
</style>
