<template>
<section class="px-4 py-12" :id="section.anchorId || undefined" :style="{ background: section.backgroundColor || '#020617' }">
    <div class="mx-auto max-w-5xl">
      <div class="relative flex items-center overflow-hidden rounded-[32px] border shadow-2xl min-h-[250px] md:min-h-[350px]" :style="cardSurfaceStyle">
        <div class="absolute inset-0">
          <div class="absolute inset-0 bg-cover bg-center" :style="backgroundImageStyle"></div>
          <div class="absolute inset-0" :style="gradientOverlayStyle"></div>
        </div>
        <div class="banner-text relative z-10 flex min-h-full flex-col justify-center gap-4 p-8 text-left md:p-12" :style="{ color: textColor }">
          <p
            v-if="section.headingLabel"
            class="text-xs font-semibold uppercase tracking-[0.35em] text-white/80"
          >
            {{ section.headingLabel }}
          </p>
          <h2 class="banner-title text-3xl font-bold leading-tight md:text-4xl" :style="{ color: titleColor }">{{ section.title }}</h2>
          <div class="mt-2">
            <a
              v-if="ctaHasTarget"
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              class="inline-flex min-w-[180px] items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-xl transition hover:-translate-y-0.5 hover:shadow-2xl"
              :style="{ background: ctaColor, color: buttonTextColor }"
            >
              {{ section.ctaLabel || "Falar agora" }}
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
import { getReadableTextColor } from "../../utils/colorContrast";
import type { BannerCardSection } from "../../types/page";

const props = defineProps<{ section: BannerCardSection; previewDevice?: "desktop" | "mobile" }>();

const fallbackChannels = { r: 5, g: 6, b: 15 };

const parseChannels = (value?: string) => {
  if (!value) return fallbackChannels;
  const trimmed = value.trim();
  const hexMatch = trimmed.match(/^#?([0-9a-f]{6})$/i);
  if (hexMatch) {
    const hex = hexMatch[1];
    return {
      r: parseInt(hex.slice(0, 2), 16),
      g: parseInt(hex.slice(2, 4), 16),
      b: parseInt(hex.slice(4, 6), 16)
    };
  }
  const rgbMatch = trimmed.match(/rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)(?:\s*,\s*([0-9.]+))?\s*\)/i);
  if (rgbMatch) {
    return {
      r: Number(rgbMatch[1]),
      g: Number(rgbMatch[2]),
      b: Number(rgbMatch[3])
    };
  }
  return fallbackChannels;
};

const toRgba = (channels: { r: number; g: number; b: number }, alpha: number) =>
  `rgba(${Math.round(channels.r)}, ${Math.round(channels.g)}, ${Math.round(channels.b)}, ${alpha})`;

const gradientChannels = computed(() => parseChannels(props.section.gradientColor));
const gradientLuminance = computed(() => {
  const { r, g, b } = gradientChannels.value;
  const toLinear = (channel: number) => {
    const c = channel / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  };
  const rLin = toLinear(r);
  const gLin = toLinear(g);
  const bLin = toLinear(b);
  return 0.2126 * rLin + 0.7152 * gLin + 0.0722 * bLin;
});

const backgroundImage = computed(
  () => resolveMediaUrl(props.section.backgroundImage || "") || props.section.backgroundImage || ""
);

const backgroundImageStyle = computed(() =>
  backgroundImage.value
    ? {
        backgroundImage: `url('${backgroundImage.value}')`,
        backgroundSize: "cover",
        backgroundPosition: "center"
      }
    : { backgroundColor: "#05060f" }
);

const gradientOverlayStyle = computed(() => {
  const base = toRgba(gradientChannels.value, 0.9);
  const mid = toRgba(gradientChannels.value, 0.55);
  const tail = toRgba(gradientChannels.value, 0.05);
  return {
    background: `linear-gradient(120deg, ${base} 0%, ${mid} 45%, ${tail} 100%)`
  };
});

const cardSurfaceStyle = computed(() => ({
  borderColor: props.section.cardBorderColor || "rgba(255,255,255,0.25)",
  background: props.section.cardBackground || "rgba(5,6,15,0.85)"
}));

const titleColor = computed(() => (gradientLuminance.value > 0.5 ? "#0f172a" : "#ffffff"));
const textColor = computed(() => props.section.textColor || "rgba(255,255,255,0.85)");

const ctaMode = computed(() => props.section.ctaMode || "link");
const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);
const ctaHasTarget = computed(() =>
  ctaMode.value === "section" ? !!props.section.ctaSectionId : !!props.section.ctaLink
);
const ctaHref = computed(() =>
  ctaIsScroll.value ? `#${props.section.ctaSectionId}` : props.section.ctaLink || "#"
);
const ctaColor = computed(() => props.section.ctaColor || "#41ce5f");
const buttonTextColor = computed(() => getReadableTextColor(ctaColor.value));
const ctaTrackType = computed(() =>
  ctaIsScroll.value ? "cta" : isWhatsappLink(props.section.ctaLink || undefined) ? "whatsapp" : "cta"
);
</script>

<style scoped>
.banner-text {
  max-width: 70%;
}

@media (min-width: 768px) {
  .banner-text {
    max-width: 55%;
  }
}

@media (max-width: 767px) {
  .banner-title {
    font-size: 1.5rem;
    line-height: 1.25;
  }
}

.subtitle-rich :deep(*) {
  color: var(--banner-card-body-color) !important;
}
</style>
