<template>
  <section class="w-full" :style="{ background: section.backgroundColor || '#f5f7fb' }" :id="section.anchorId || undefined">
    <div class="mx-auto w-full max-w-5xl px-6 py-16 text-center">
      <div class="flex justify-center mb-1">
        <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="ctaColor" />
      </div>
      <h2 class="text-3xl font-bold leading-tight md:text-4xl" :style="{ color: primaryText }">
        {{ section.title || "Video em destaque" }}
      </h2>
      <div
        v-if="subtitleHtml"
        class="mt-1 text-base leading-relaxed md:text-lg"
        :style="{ color: mutedText }"
        v-html="subtitleHtml"
      ></div>

      <div v-if="embeddedVideoUrl" class="mt-8 w-full overflow-hidden rounded-[28px] shadow-2xl ring-1 ring-slate-200" :class="videoWrapperClass">
        <div class="relative pt-[56.25%]">
          <iframe
            class="absolute inset-0 h-full w-full rounded-[28px]"
            :src="embeddedVideoUrl"
            title="Video em destaque"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen
          ></iframe>
        </div>
      </div>
      <div v-else class="mt-8 rounded-3xl border border-dashed border-slate-200 bg-white/60 px-6 py-16 text-sm text-slate-500">
        Adicione um link de video para aparecer aqui.
      </div>

      <div v-if="ctaEnabled && ctaHasTarget" class="mt-8">
        <a
          :href="ctaHref"
          :data-scroll-target="ctaIsScroll ? 'true' : null"
          target="_blank"
          rel="noopener"
          data-track-event="cta"
          :data-track-type="ctaTrackType"
          class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl hero-cta-shimmer hero-cta-desktop-hover"
          :style="{ background: ctaColor, color: ctaTextColor }"
        >
          {{ section.ctaLabel || "Assistir agora" }}
        </a>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { FeaturedVideoSection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { deriveTextPalette, getReadableTextColor } from "../../utils/colorContrast";
import { isWhatsappLink } from "../../utils/links";
import { normalizeYoutubeEmbedUrl } from "../../utils/video";

const props = defineProps<{ section: FeaturedVideoSection; previewDevice?: "desktop" | "mobile" }>();
const headingDefaults = getSectionHeadingDefaults("featured_video");

const headingLabel = computed(() => props.section.headingLabel ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const subtitleHtml = computed(() => sanitizeHtml(props.section.subtitle));
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);
const ctaColor = computed(() => props.section.ctaColor || "#41ce5f");
const ctaTextColor = computed(() => getReadableTextColor(ctaColor.value));
const isMobilePreview = computed(() => props.previewDevice === "mobile");
const videoWrapperClass = computed(() => (isMobilePreview.value ? "rounded-[18px]" : "rounded-[28px]"));

const embeddedVideoUrl = computed(() => normalizeYoutubeEmbedUrl(props.section.videoUrl));

const ctaEnabled = computed(() => props.section.ctaEnabled !== false);
const ctaMode = computed(() => props.section.ctaMode || "link");
const ctaHasTarget = computed(() =>
  ctaMode.value === "section" ? !!props.section.ctaSectionId : !!props.section.ctaLink
);
const ctaHref = computed(() =>
  ctaMode.value === "section" && props.section.ctaSectionId ? `#${props.section.ctaSectionId}` : props.section.ctaLink || "#"
);
const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);
const ctaTrackType = computed(() =>
  ctaMode.value === "section" ? "cta" : isWhatsappLink(props.section.ctaLink || undefined) ? "whatsapp" : "cta"
);
</script>

