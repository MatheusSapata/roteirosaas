<template>
  <section class="w-full" :style="outerStyle" :id="section.anchorId || undefined">
    <!-- Layout simples full width -->
    <div v-if="section.layout === 'simple'" class="relative w-full">
      <div class="absolute inset-0" :style="bgImageStyle"></div>
      <div class="relative mx-auto flex min-h-[300px] w-full max-w-6xl flex-col items-center justify-center px-6 py-12 text-center" :style="{ color: textColor }">
        <p class="text-2xl font-bold md:text-3xl">{{ section.label }}</p>
        <p class="mt-2 text-sm md:text-base" v-if="section.description">{{ section.description }}</p>
        <div class="mt-5 flex justify-center" v-if="ctaHasTarget">
          <a
            :href="ctaHref"
            :data-scroll-target="ctaIsScroll ? 'true' : null"
            target="_blank"
            data-track-event="cta"
            rel="noopener"
            :data-track-type="ctaTrackType"
            class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
            :style="{ background: buttonColor }"
          >
            {{ section.ctaText || "Saiba mais" }}
          </a>
        </div>
      </div>
    </div>

    <!-- Demais layouts dentro de container -->
    <div v-else class="mx-auto max-w-6xl px-6 py-12">
      <div class="rounded-3xl bg-white/90 p-6 shadow-[0_16px_50px_-30px_rgba(15,23,42,0.55)] ring-1 ring-slate-100">
        <!-- Barra -->
        <div
          v-if="section.layout === 'bar' || !section.layout"
          class="flex flex-col gap-4 rounded-2xl border border-slate-100 bg-white/90 px-5 py-4 shadow-lg md:flex-row md:items-center md:justify-between"
          :style="{ borderColor: accentBorder }"
        >
          <div class="space-y-1" :style="{ color: textColor }">
            <p class="text-xs uppercase tracking-[0.2em]" :style="{ color: textColor }">Pronto para viajar?</p>
            <p class="text-lg font-semibold" :style="{ color: textColor }">{{ section.label }}</p>
            <p class="text-sm" :style="{ color: textColor }">{{ section.description }}</p>
          </div>
          <a
            v-if="ctaHasTarget"
            :href="ctaHref"
            :data-scroll-target="ctaIsScroll ? 'true' : null"
            target="_blank"
            data-track-event="cta"
            rel="noopener"
            :data-track-type="ctaTrackType"
            class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
            :style="{ background: buttonColor }"
          >
            Falar com especialista
          </a>
        </div>

        <!-- Split -->
        <div
          v-else-if="section.layout === 'split'"
          class="grid gap-4 rounded-2xl border border-slate-100 bg-white/95 p-6 shadow-xl md:grid-cols-2"
          :style="{ borderColor: accentBorder }"
        >
          <div class="space-y-2" :style="{ color: textColor }">
            <p class="text-xs uppercase tracking-[0.25em]" :style="{ color: textColor }">Convite</p>
            <p class="text-2xl font-bold" :style="{ color: textColor }">{{ section.label }}</p>
            <p class="text-sm" :style="{ color: textColor }">{{ section.description }}</p>
          </div>
          <div class="flex items-center justify-end">
          <a
            v-if="ctaHasTarget"
            :href="ctaHref"
            :data-scroll-target="ctaIsScroll ? 'true' : null"
            target="_blank"
            data-track-event="cta"
            rel="noopener"
            :data-track-type="ctaTrackType"
            class="inline-flex items-center justify-center rounded-lg px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
            :style="{ background: buttonColor }"
          >
            Reservar agora
          </a>
          </div>
        </div>

        <!-- Card -->
        <div
          v-else
          class="relative overflow-hidden rounded-3xl border border-slate-100 bg-white/95 p-6 shadow-2xl"
          :style="{ borderColor: accentBorder }"
        >
          <div class="absolute inset-0 bg-gradient-to-br from-white via-white to-transparent"></div>
          <div class="relative space-y-3" :style="{ color: textColor }">
            <p class="text-xs uppercase tracking-[0.25em]" :style="{ color: textColor }">Vamos comecar</p>
            <p class="text-2xl font-bold" :style="{ color: textColor }">{{ section.label }}</p>
            <p class="text-sm" :style="{ color: textColor }">{{ section.description }}</p>
            <a
              v-if="ctaHasTarget"
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              data-track-event="cta"
              rel="noopener"
              :data-track-type="ctaTrackType"
              class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
              :style="{ background: buttonColor }"
            >
              Agendar contato
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
import type { CtaSection } from "../../types/page";

const props = defineProps<{ section: CtaSection }>();

const accent = computed(() => props.section.backgroundColor || "#0ea5e9");
const buttonColor = computed(() => props.section.ctaColor || accent.value);
const textColor = computed(() => props.section.textColor || (props.section.layout === "simple" ? "#ffffff" : "#0f172a"));
const outerStyle = computed(() => (props.section.layout === "simple" ? {} : { background: accentSoftBg.value }));
const ctaMode = computed(() => props.section.ctaMode || "link");
const ctaHref = computed(() =>
  ctaMode.value === "section" && props.section.ctaSectionId ? `#${props.section.ctaSectionId}` : props.section.link || "#"
);
const ctaHasTarget = computed(() =>
  ctaMode.value === "section" ? !!props.section.ctaSectionId : !!props.section.link
);
const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(14,165,233,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
const accentBorder = computed(() => toRgba(accent.value, 0.25));
const accentSoftBg = computed(() => props.section.backgroundColor || `linear-gradient(135deg, ${toRgba(accent.value, 0.08)}, rgba(255,255,255,0.95))`);
const backgroundImage = computed(() => resolveMediaUrl(props.section.backgroundImage));
const ctaTrackType = computed(() =>
  ctaMode.value === "section" ? "cta" : isWhatsappLink(props.section.link || undefined) ? "whatsapp" : "cta"
);
const bgImageStyle = computed(() =>
  backgroundImage.value
    ? {
        backgroundImage: `linear-gradient(180deg, rgba(0,0,0,0.25), rgba(0,0,0,0.35)), url(${backgroundImage.value})`,
        backgroundSize: "cover",
        backgroundPosition: "center"
      }
    : {
        background: props.section.backgroundColor || accent.value
      }
);
</script>
