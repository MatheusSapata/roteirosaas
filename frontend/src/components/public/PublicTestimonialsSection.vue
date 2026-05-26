<template>
  <section class="w-full" :style="{ background: section.backgroundColor || '#ffffff' }" :id="section.anchorId || undefined">
    <div class="mx-auto flex max-w-6xl flex-col items-center px-6 py-12">
      <div class="flex justify-center mb-1">
        <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accent" />
      </div>
      <h1
        :class="['text-center font-bold leading-tight', isMobilePreview ? 'text-3xl' : 'text-3xl md:text-4xl']"
        :style="{ color: primaryText }"
      >
        {{ titleText }}
      </h1>
      <p
        v-if="subtitleHtml"
        :class="['text-center text-sm', isMobilePreview ? '' : 'md:text-base']"
        v-html="subtitleHtml"
        :style="{ color: mutedText }"
      ></p>
      <p v-else :class="['mt-2 text-center text-sm', isMobilePreview ? '' : 'md:text-base']" :style="{ color: mutedText }">
        {{ defaultSubtitle }}
      </p>

      <div class="mt-8 flex w-full flex-wrap justify-center gap-6">
        <article
          v-for="(item, index) in displayedWithMedia"
          :key="index"
          :ref="setCardRef"
          class="h-full w-full rounded-[20px] p-6 md:p-7"
          :class="cardWidthClass"
          :style="[testimonialCardStyle, uniformCardStyle]"
        >
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full text-sm font-semibold" :style="avatarStyle">
                <img v-if="item.avatarUrl" :src="item.avatarUrl" :alt="avatarAltText" class="h-full w-full object-cover" />
                <span v-else>{{ initials(item.name) }}</span>
              </div>
              <div>
                <p class="text-[18px] font-semibold leading-tight" :style="{ color: testimonialTitleColor }">{{ itemName(item) }}</p>
                <p class="text-[16px] leading-tight" :style="{ color: testimonialMetaColor }">{{ itemRole(item) }}</p>
              </div>
            </div>
          </div>

          <div class="mt-4 flex items-center gap-1 text-lg" :style="{ color: '#f59e0b' }">
            <span v-for="star in 5" :key="star">★</span>
          </div>

          <p class="mt-4 text-base leading-relaxed" :style="{ color: testimonialBodyColor }">
            {{ itemText(item) }}
          </p>
        </article>
      </div>

      <div v-if="ctaHasTarget" class="mt-6">
        <a
          :href="ctaHref"
          :data-scroll-target="ctaIsScroll ? 'true' : null"
          :target="ctaOpenInNewTab ? '_blank' : null"
          :rel="ctaOpenInNewTab ? 'noopener' : null"
          data-track-event="cta"
          :data-track-type="ctaTrackType"
          class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl hero-cta-shimmer hero-cta-desktop-hover"
          :style="{ background: accent, color: ctaTextColor }"
        >
          {{ ctaLabelText }}
        </a>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { isWhatsappLink } from "../../utils/links";
import type { TestimonialsSection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { deriveTextPalette, getReadableTextColor, getRelativeLuminance, normalizeHexColor } from "../../utils/colorContrast";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: TestimonialsSection; previewDevice?: "desktop" | "mobile" }>();
const headingDefaults = getSectionHeadingDefaults("testimonials");
const localize = createLocalizer(getCurrentLanguage());
const testimonialsCopy = {
  title: { pt: "Depoimentos de clientes", es: "Testimonios de clientes" },
  subtitle: { pt: "O que dizem depois de viajar conosco", es: "Lo que dicen después de viajar con nosotros" },
  avatarAlt: { pt: "Avatar", es: "Avatar" },
  ctaLabel: { pt: "Falar com especialista", es: "Hablar con un especialista" }
} as const;

const accent = computed(() => props.section.ctaColor || "#5b49ff");
const isMobilePreview = computed(() => props.previewDevice === "mobile");
const ctaTextColor = computed(() => getReadableTextColor(accent.value));
const accentBackground = computed(() => props.section.backgroundColor || "linear-gradient(135deg,#5b49ff,#3b82f6)");
const sectionBackground = computed(() => props.section.backgroundColor || "#ffffff");
const sectionBackgroundHex = computed(() => normalizeHexColor(props.section.backgroundColor));

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(91,73,255,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const accentSoft = computed(() => toRgba(accent.value, 0.35));
const headingLabel = computed(() =>
  resolveHeadingLabel(props.section.headingLabel, headingDefaults.label, localize)
);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const titleText = computed(() => {
  const text = localize(props.section.title).trim();
  return text.length ? text : localize(testimonialsCopy.title);
});
const subtitleHtml = computed(() => {
  const html = sanitizeHtml(localize(props.section.subtitle));
  return html || "";
});
const defaultSubtitle = computed(() => localize(testimonialsCopy.subtitle));
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const sectionBackgroundIsLight = computed(() => {
  if (!sectionBackgroundHex.value) return !textPalette.value.isLight;
  return getRelativeLuminance(sectionBackgroundHex.value) > 0.7;
});
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);
const neutralShadow = "0 18px 38px -28px rgba(15,23,42,0.28)";
const darkCardBorder = computed(() => `1px solid ${toRgba(accent.value, 0.42)}`);
const testimonialCardStyle = computed(() => ({
  background: sectionBackgroundIsLight.value ? "#ffffff" : "rgba(255,255,255,0.10)",
  border: sectionBackgroundIsLight.value ? "none" : darkCardBorder.value,
  boxShadow: sectionBackgroundIsLight.value ? neutralShadow : `0 22px 46px -30px ${accentSoft.value}`
}));
const avatarStyle = computed(() => ({
  background: sectionBackgroundIsLight.value ? "rgba(241,245,249,0.95)" : toRgba(accent.value, 0.12),
  color: sectionBackgroundIsLight.value ? "#64748b" : "rgba(241,245,249,0.82)"
}));
const testimonialTitleColor = computed(() => (sectionBackgroundIsLight.value ? "#0f172a" : "#f8fafc"));
const testimonialMetaColor = computed(() => (sectionBackgroundIsLight.value ? "#64748b" : "rgba(241,245,249,0.68)"));
const testimonialBodyColor = computed(() => (sectionBackgroundIsLight.value ? "#1e293b" : "rgba(241,245,249,0.82)"));

const avatarAltText = computed(() => localize(testimonialsCopy.avatarAlt));
const initials = (name?: string) => {
  const raw = localize(name).trim();
  if (!raw) return "-";
  const parts = raw.split(" ").filter(Boolean);
  const first = parts[0]?.[0] || "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase() || "-";
};
const itemName = (item: any) => {
  const name = localize(item?.name).trim();
  return name.length ? name : initials(item?.name);
};
const itemRole = (item: any) => localize(item?.role).trim();
const itemText = (item: any) => localize(item?.text).trim();
const displayed = computed(() => props.section.items || []);
const displayedWithMedia = computed(() =>
  displayed.value.map(item => ({
    ...item,
    avatarUrl: resolveMediaUrl(item.avatar) || item.avatar || ""
  }))
);
const cardRefs = ref<HTMLElement[]>([]);
const maxCardHeight = ref(0);
let measureRaf: number | null = null;
const setCardRef = (el: Element | null) => {
  if (!(el instanceof HTMLElement)) return;
  if (!cardRefs.value.includes(el)) cardRefs.value.push(el);
};

const measureCards = () => {
  if (!cardRefs.value.length) {
    maxCardHeight.value = 0;
    return;
  }
  cardRefs.value.forEach(card => {
    card.style.minHeight = "";
  });
  maxCardHeight.value = Math.max(...cardRefs.value.map(card => card.offsetHeight));
};

const scheduleMeasureCards = () => {
  if (measureRaf !== null) cancelAnimationFrame(measureRaf);
  measureRaf = requestAnimationFrame(() => {
    measureCards();
    measureRaf = null;
  });
};

const uniformCardStyle = computed(() =>
  maxCardHeight.value > 0 ? { minHeight: `${maxCardHeight.value}px` } : {}
);
const cardsPerRow = computed(() => {
  const count = displayedWithMedia.value.length;
  if (count <= 1) return 1;
  if (isMobilePreview.value) return 1;
  if (count > 4 && count % 4 === 1) return 3;
  return Math.min(4, count);
});
const cardWidthClass = computed(() => {
  if (cardsPerRow.value === 1) return "";
  if (cardsPerRow.value === 2) return "md:w-[calc((100%-1.5rem)/2)]";
  if (cardsPerRow.value === 3) return "md:w-[calc((100%-3rem)/3)]";
  return "md:w-[calc((100%-4.5rem)/4)]";
});
const ctaMode = computed(() => props.section.ctaMode || "link");
const ctaHref = computed(() =>
  ctaMode.value === "section" && props.section.ctaSectionId ? `#${props.section.ctaSectionId}` : props.section.ctaLink || "#"
);
const ctaHasTarget = computed(() =>
  ctaMode.value === "section" ? !!props.section.ctaSectionId : !!props.section.ctaLink
);
const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);
const ctaOpenInNewTab = computed(() => !ctaIsScroll.value && props.section.ctaOpenInNewTab !== false);
const ctaTrackType = computed(() =>
  ctaMode.value === "section" ? "cta" : isWhatsappLink(props.section.ctaLink || undefined) ? "whatsapp" : "cta"
);
const ctaLabelText = computed(() => {
  const text = localize(props.section.ctaLabel).trim();
  return text.length ? text : localize(testimonialsCopy.ctaLabel);
});

watch(
  () => displayedWithMedia.value.length,
  async () => {
    cardRefs.value = [];
    await nextTick();
    scheduleMeasureCards();
  }
);

watch(
  () => [props.previewDevice, props.section.title, props.section.subtitle],
  () => nextTick(() => scheduleMeasureCards())
);

onMounted(() => {
  window.addEventListener("resize", scheduleMeasureCards);
  nextTick(() => scheduleMeasureCards());
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", scheduleMeasureCards);
  if (measureRaf !== null) cancelAnimationFrame(measureRaf);
});
</script>
