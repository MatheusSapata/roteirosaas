<template>
  <section class="relative overflow-hidden bg-[#05060f]" :id="section.anchorId || undefined">
    <div :class="mobileWrapperClasses">
      <div class="overflow-hidden bg-[#05060f] shadow-2xl shadow-black/30">
        <div class="relative w-full overflow-hidden" style="aspect-ratio: 3 / 4; max-height: 60vh;">
          <div class="absolute inset-0 bg-cover bg-center" :style="mobileBackgroundStyle"></div>
          <div class="absolute inset-0" :style="mobileGradientStyle"></div>
        </div>
        <div class="relative overflow-hidden px-5 pb-8 text-center text-white" :style="{ background: mobileContentBg }">
          <div class="inline-flex w-full flex-col items-center gap-4" :style="{ paddingTop: `${mobileLogoPadding}px` }">
            <div class="flex justify-center" :style="{ marginTop: `-${mobileLogoLift}px` }">
              <template v-if="logoSrc">
                <div class="drop-shadow-xl" :style="logoBoxStyle">
                  <img :src="logoSrc" alt="Logo" class="h-full w-auto" />
                </div>
              </template>
              <span v-else class="rounded-full bg-white/15 px-4 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-white">
                {{ branding.agency_name || "Sua marca" }}
              </span>
            </div>
            <div class="space-y-1 mt-2">
              <h1 class="text-[26px] font-bold leading-tight">{{ section.title }}</h1>
              <div v-if="subtitleHtml" class="text-sm text-white/85" v-html="subtitleHtml"></div>
            </div>
          </div>
          <div v-if="chipsToShow.length" class="mt-4 flex flex-wrap items-center justify-center gap-2 text-[11px]">
            <span
              v-for="(chip, idx) in chipsToShow"
              :key="idx"
              class="inline-flex items-center gap-2 rounded-full border px-4 py-1 text-xs font-semibold uppercase tracking-wide backdrop-blur"
              :style="{ borderColor: accentBorder, background: accentChipBg, color: '#fff' }"
            >
              <span class="inline-block h-2 w-2 rounded-full" :style="{ background: ctaColor }"></span>
              {{ chip }}
            </span>
          </div>
          <div class="mt-5 space-y-1">
            <a
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              class="inline-flex w-full items-center justify-center rounded-full px-5 py-3 text-sm font-semibold text-white shadow-xl shadow-black/40 transition hover:-translate-y-0.5 hover:shadow-2xl"
              :style="{ background: ctaColor }"
            >
              {{ section.ctaLabel || "Quero falar agora" }}
            </a>
            <p class="text-[11px] text-white/75">Atendimento rápido e personalizado</p>
          </div>
        </div>
      </div>
    </div>

    <div :class="desktopWrapperClasses">
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
        <div class="max-w-3xl space-y-5 text-white md:w-7/12 text-center md:text-left" :class="isMobilePreview ? '!w-full !text-center' : ''">
          <div class="flex items-center gap-3">
            <img
              v-if="logoSrc"
              :src="logoSrc"
              alt="Logo"
              class="w-auto drop-shadow-lg"
              :style="{ height: `${logoSize}px` }"
            />
            <div v-else class="rounded-full bg-white/20 px-4 py-1 text-sm font-semibold uppercase tracking-[0.25em]">
              {{ branding.agency_name || "Sua marca" }}
            </div>
          </div>
          <h1 class="text-3xl font-bold leading-tight md:text-5xl" :class="isMobilePreview ? '!text-3xl' : ''">{{ section.title }}</h1>
          <div
            v-if="subtitleHtml"
            class="text-base text-slate-100 md:text-xl"
            :class="isMobilePreview ? '!text-base' : ''"
            v-html="subtitleHtml"
          ></div>

          <div v-if="chipsToShow.length" class="flex flex-wrap justify-center gap-3 md:justify-start" :class="isMobilePreview ? '!justify-center' : ''">
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

          <div class="flex flex-col items-center gap-3 sm:flex-row sm:items-center sm:justify-start" :class="isMobilePreview ? '!flex-col !items-center !justify-center' : ''">
            <a
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-xl transition hover:-translate-y-0.5 hover:shadow-2xl"
              :style="{ background: ctaColor }"
            >
              {{ section.ctaLabel || "Quero falar agora" }}
            </a>
            <p class="text-sm text-slate-100/90">Atendimento rápido e personalizado</p>
          </div>
        </div>
        <div class="md:w-5/12" v-if="section.videoUrl" :class="isMobilePreview ? '!w-full' : ''">
          <div class="relative overflow-hidden rounded-3xl bg-black/50 shadow-2xl ring-1 ring-white/40">
            <div class="relative pt-[110%] md:pt-[90%]">
              <iframe
                class="absolute inset-0 h-full w-full rounded-3xl object-cover"
                :src="embeddedVideoUrl"
                title="Video"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
              ></iframe>
            </div>
          </div>
        </div>
        <div v-else class="md:w-5/12" :class="isMobilePreview ? '!w-full' : ''"></div>
      </div>

      <!-- Layout clássico -->
      <div
        v-else-if="layout === 'classic'"
        class="flex flex-col gap-6 rounded-3xl bg-white/75 p-6 text-center shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)] ring-1 ring-white/60 backdrop-blur md:p-8 md:text-left"
        :class="isMobilePreview ? '!p-6 !text-center' : ''"
      >
        <div class="flex flex-col gap-6 md:flex-row md:items-center" :class="isMobilePreview ? '!flex-col !items-start' : ''">
          <div class="space-y-4 md:w-7/12" :class="isMobilePreview ? '!w-full' : ''">
            <p
              class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-slate-600"
              :style="{ background: accentSoft, borderColor: accentBorder }"
            >
              <span class="h-2 w-2 rounded-full" :style="{ background: accent }"></span>
              {{ branding.agency_name || "Roteiro exclusivo" }}
            </p>
            <h1 class="text-3xl font-bold leading-tight text-slate-900 md:text-5xl" :class="isMobilePreview ? '!text-3xl' : ''">{{ section.title }}</h1>
            <div
              v-if="subtitleHtml"
              class="text-base text-slate-600 md:text-xl"
              :class="isMobilePreview ? '!text-base' : ''"
              v-html="subtitleHtml"
            ></div>
          <div class="flex flex-wrap items-center justify-center gap-3 md:justify-start" :class="isMobilePreview ? '!justify-center' : ''">
            <a
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              class="rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
              :style="{ background: ctaColor }"
            >
                {{ section.ctaLabel || "Quero reservar" }}
              </a>
              <span class="text-sm text-slate-500">Atendimento rápido e personalizado</span>
            </div>
          </div>
          <div class="md:w-5/12" :class="isMobilePreview ? '!w-full' : ''">
            <div class="rounded-2xl border border-slate-100 bg-white/85 p-5 shadow-xl backdrop-blur">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-full text-slate-900" :style="{ background: accentSoft }">
                  ✈️
                </div>
                <div>
                  <p class="text-sm text-slate-500">Datas sob medida</p>
                  <p class="text-base font-semibold text-slate-900">Fale com um especialista agora</p>
                </div>
              </div>
              <div class="mt-4 rounded-xl border border-slate-100 bg-slate-50/85 p-4 text-sm text-slate-700">
                <p class="font-semibold text-slate-900">Por que reservar aqui?</p>
                <ul class="mt-2 space-y-1">
                  <li class="flex items-center gap-2">
                    <span class="h-2 w-2 rounded-full" :style="{ background: accent }"></span>Equipe local 24/7
                  </li>
                  <li class="flex items-center gap-2">
                    <span class="h-2 w-2 rounded-full" :style="{ background: accent }"></span>Roteiro validado e seguro
                  </li>
                  <li class="flex items-center gap-2">
                    <span class="h-2 w-2 rounded-full" :style="{ background: accent }"></span>Pagamento facilitado
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Layout split -->
      <div
        v-else-if="layout === 'split'"
        class="grid items-center gap-6 rounded-3xl bg-white/75 p-6 text-center shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)] ring-1 ring-white/60 backdrop-blur md:grid-cols-2 md:gap-8 md:p-8 md:text-left"
        :class="isMobilePreview ? '!grid-cols-1 !text-center !p-6' : ''"
      >
        <div class="space-y-4">
          <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Experiencia premium</p>
          <h1 class="text-3xl font-bold leading-tight text-slate-900 md:text-5xl" :class="isMobilePreview ? '!text-3xl' : ''">{{ section.title }}</h1>
          <div
            v-if="subtitleHtml"
            class="text-base text-slate-600 md:text-lg"
            :class="isMobilePreview ? '!text-base' : ''"
            v-html="subtitleHtml"
          ></div>
          <div class="flex flex-wrap items-center justify-center gap-3 md:justify-start" :class="isMobilePreview ? '!justify-center' : ''">
            <a
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              class="rounded-lg px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
              :style="{ background: ctaColor }"
            >
              {{ section.ctaLabel || "Reservar agora" }}
            </a>
            <span class="text-sm text-slate-500">Resposta em poucos minutos</span>
          </div>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white/80 p-6 shadow-2xl backdrop-blur">
          <div class="space-y-3 text-slate-700">
            <p class="text-sm uppercase tracking-wide text-slate-500">Inclui</p>
            <ul class="space-y-2 text-sm">
              <li class="flex items-start gap-2">
                <span class="mt-1 h-2 w-2 rounded-full" :style="{ background: accent }"></span>
                Planejamento completo e suporte 24/7
              </li>
              <li class="flex items-start gap-2">
                <span class="mt-1 h-2 w-2 rounded-full" :style="{ background: accent }"></span>
                Curadoria de experiencias locais autenticas
              </li>
              <li class="flex items-start gap-2">
                <span class="mt-1 h-2 w-2 rounded-full" :style="{ background: accent }"></span>
                Facilidades de pagamento e condicoes especiais
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Layout card -->
      <div v-else class="flex flex-col items-center text-center">
        <div class="max-w-2xl space-y-4 rounded-3xl bg-white/75 p-6 shadow-2xl backdrop-blur ring-1 ring-white/60 md:p-8" :class="isMobilePreview ? '!p-6' : ''">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">{{ branding.agency_name }}</p>
          <h1 class="text-3xl font-bold leading-tight text-slate-900 md:text-5xl" :class="isMobilePreview ? '!text-3xl' : ''">{{ section.title }}</h1>
          <div
            v-if="subtitleHtml"
            class="text-base text-slate-600 md:text-lg"
            :class="isMobilePreview ? '!text-base' : ''"
            v-html="subtitleHtml"
          ></div>
          <a
            :href="ctaHref"
            :data-scroll-target="ctaIsScroll ? 'true' : null"
            target="_blank"
            rel="noopener"
            data-track-event="cta"
            :data-track-type="ctaTrackType"
            class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
            :style="{ background: ctaColor }"
          >
            {{ section.ctaLabel || "Quero reservar" }}
          </a>
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
import type { HeroSection } from "../../types/page";

const props = defineProps<{ section: HeroSection; branding: Record<string, any>; previewDevice?: "desktop" | "mobile" }>();
const subtitleHtml = computed(() => sanitizeHtml(props.section.subtitle));

const layout = computed(() => props.section.layout || "classic");
const heroBackgroundImage = computed(() => resolveMediaUrl(props.section.backgroundImage));
const logoSrc = computed(() => resolveMediaUrl(props.section.logoUrl));
const logoSize = computed(() => props.section.logoSize ?? 64);
const logoBoxStyle = computed(() => ({ height: `${logoSize.value}px` }));
const mobileLogoPadding = -172;
const mobileLogoLift = -150;
const accent = computed(() => props.section.gradientColor || props.section.backgroundColor || "#0ea5e9");
const ctaColor = computed(() => props.section.ctaColor || accent.value);
const ctaMode = computed(() => props.section.ctaMode || "link");
const ctaHref = computed(() =>
  ctaMode.value === "section" && props.section.ctaSectionId ? `#${props.section.ctaSectionId}` : props.section.ctaLink || "#"
);
const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);
const ctaTrackType = computed(() => (ctaMode.value === "section" ? "cta" : trackType(props.section.ctaLink)));
const isMobilePreview = computed(() => props.previewDevice === "mobile");
const mobileWrapperClasses = computed(() => ["relative block md:hidden px-4 pt-12", isMobilePreview.value ? "!block" : ""]);
const desktopWrapperClasses = computed(() => ["relative hidden md:block", isMobilePreview.value ? "!hidden" : ""]);
const mobileBaseColor = computed(() => {
  const candidate = props.section.gradientColor || props.section.backgroundColor;
  if (candidate && candidate.startsWith("#")) return candidate;
  return "#05060f";
});

const normalizeVideoUrl = (raw?: string) => {
  if (!raw) return "";
  let url = raw.trim();
  const iframeSrc = url.match(/src=["']([^"']+)["']/i);
  if (iframeSrc?.[1]) {
    url = iframeSrc[1];
  }
  if (!url.startsWith("http")) {
    url = `https://${url}`;
  }
  url = url.replace("watch?v=", "embed/").replace("youtu.be/", "www.youtube.com/embed/");
  return url;
};

const embeddedVideoUrl = computed(() => normalizeVideoUrl(props.section.videoUrl));

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
      ${toRgba(base, 0)} 16%,
      ${toRgba(base, 0.4)} 30%,
      ${toRgba(base, 0.5)} 50%,
      ${toRgba(base, 0.6)} 58%,
      ${toRgba(base, 0.7)} 66%,
      ${toRgba(base, 0.8)} 74%,
      ${toRgba(base, 0.9)} 82%,
      ${toRgba(base, 1)} 100%
    )`
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

const chipsToShow = computed(() => props.section.chips || []);
const trackType = (link?: string | null) => (isWhatsappLink(link || undefined) ? "whatsapp" : "cta");
</script>
