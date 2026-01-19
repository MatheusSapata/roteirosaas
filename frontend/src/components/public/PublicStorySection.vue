<template>
  <section class="w-full" :style="{ background: section.backgroundColor || '#e5eef9' }" :id="section.anchorId || undefined">
    <div class="mx-auto flex max-w-6xl flex-col" :class="outerClass" :style="borderStyle">
      <!-- Layout com imagem única -->
      <div v-if="isSingle" class="flex w-full flex-col" :class="singleLayoutClass">
        <div :class="textBlockClass">
          <div v-if="section.badge" :class="badgeClass">
            {{ section.badge }}
          </div>
          <h2 class="text-3xl font-bold leading-tight text-slate-900 md:text-4xl">{{ section.title }}</h2>
          <p class="text-base leading-relaxed text-slate-600 md:text-lg">{{ section.subtitle }}</p>
          <div class="flex flex-wrap items-center gap-4">
            <a
              v-if="ctaEnabled && ctaHasTarget"
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
              :style="{ background: ctaColor }"
            >
              {{ section.ctaLabel || "Saiba mais" }}
            </a>
          </div>
        </div>
        <div :class="mediaContainerClass">
          <div :class="mediaInnerClass">
            <template v-if="section.videoUrl">
              <div class="relative pt-[56.25%]">
                <iframe
                  :class="iframeClass"
                  :src="embeddedVideoUrl"
                  title="Video"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              </div>
            </template>
            <img v-else :src="primaryImage" alt="Destaque" class="h-full w-full object-cover" />
          </div>
        </div>
      </div>

      <!-- Layout com galeria -->
      <div v-else class="grid w-full" :class="galleryLayoutClass">
        <div :class="['text-slate-800', textBlockClass, imagePosition === 'left' ? 'md:order-2' : 'md:order-1']">
          <div v-if="section.badge" :class="badgeClass">
            {{ section.badge }}
          </div>
          <h2 class="text-3xl font-bold leading-tight text-slate-900 md:text-4xl">{{ section.title }}</h2>
          <p class="text-base leading-relaxed text-slate-600 md:text-lg">{{ section.subtitle }}</p>
          <div class="flex flex-wrap items-center gap-4">
            <a
              v-if="ctaEnabled && ctaHasTarget"
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
              :style="{ background: ctaColor }"
            >
              {{ section.ctaLabel || "Saiba mais" }}
            </a>
          </div>
        </div>
        <div class="space-y-4" :class="[mediaContainerClass, imagePosition === 'left' ? 'md:order-1' : 'md:order-2']">
          <div :class="mediaInnerClass">
            <template v-if="section.videoUrl">
              <div class="relative pt-[56.25%]">
                <iframe
                  :class="iframeClass"
                  :src="embeddedVideoUrl"
                  title="Video"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              </div>
            </template>
            <img v-else :src="activeImage" alt="Destaque" :class="galleryImageClass" />
          </div>
          <div v-if="!section.videoUrl" class="flex flex-wrap gap-3">
            <button
              v-for="(img, idx) in resolvedImages"
              :key="idx"
              class="overflow-hidden rounded-xl ring-2 transition"
              :class="idx === activeIndex ? 'ring-slate-900' : 'ring-transparent hover:ring-slate-300'"
              @click="activeIndex = idx"
            >
              <img :src="img" alt="Thumb" class="h-20 w-28 object-cover" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { isWhatsappLink } from "../../utils/links";
import type { StorySection } from "../../types/page";

const props = defineProps<{ section: StorySection; previewDevice?: "desktop" | "mobile" }>();

const isSingle = computed(() => props.section.layout !== "gallery");
const imagePosition = computed(() => props.section.imagePosition || "right");
const ctaColor = computed(() => props.section.ctaColor || "#0ea5e9");
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
const ctaEnabled = computed(() => props.section.ctaEnabled !== false);
const isMobilePreview = computed(() => props.previewDevice === "mobile");
const borderColor = computed(() => props.section.borderColor || props.section.ctaColor || "#0ea5e9");
const borderStyle = computed(() => (props.section.borderEnabled ? { borderColor: borderColor.value } : {}));
const outerClass = computed(() =>
  props.section.borderEnabled
    ? "p-0 gap-0 md:flex-row md:items-stretch overflow-hidden rounded-[30px] bg-white/90 shadow-xl"
    : "gap-8 px-6 py-12 md:flex-row md:items-center md:gap-12"
);
const badgeClass = computed(
  () =>
    "inline-flex self-start items-center rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 w-auto max-w-max whitespace-nowrap"
);
const singleLayoutClass = computed(() => {
  const classes: string[] = [];
  if (props.section.borderEnabled) {
    classes.push("items-stretch", "gap-0");
  } else {
    classes.push("items-center", "gap-4", "md:gap-12");
  }
  if (!isMobilePreview.value) {
    classes.push(imagePosition.value === "left" ? "md:flex-row-reverse" : "md:flex-row");
  }
  return classes;
});
const galleryLayoutClass = computed(() => {
  const base = props.section.borderEnabled
    ? ["gap-0", "grid-cols-1", "md:grid-cols-2", "items-stretch"]
    : ["gap-4", "grid-cols-1", "md:grid-cols-2", "items-center", "md:gap-8"];

  if (isMobilePreview.value) {
    base.push("!grid-cols-1", "!md:grid-cols-1");
  }

  return base;
});
const textBlockClass = computed(() =>
  props.section.borderEnabled
    ? "flex-1 space-y-5 text-slate-800 bg-white px-6 py-8 md:px-10 md:py-12 flex flex-col justify-center"
    : "flex-1 space-y-5 text-slate-800 flex flex-col justify-center"
);
const mediaContainerClass = computed(() => (props.section.borderEnabled ? "flex-1 flex flex-col md:items-stretch" : "flex-1 flex flex-col md:items-stretch"));
const mediaInnerClass = computed(() =>
  props.section.borderEnabled ? "flex-1 overflow-hidden" : "flex-1 overflow-hidden rounded-3xl shadow-2xl ring-1 ring-slate-200"
);
const iframeClass = computed(() =>
  props.section.borderEnabled
    ? "absolute inset-0 h-full w-full object-cover"
    : "absolute inset-0 h-full w-full rounded-3xl object-cover"
);
const galleryImageClass = computed(() =>
  props.section.borderEnabled ? "h-full w-full object-cover" : "h-80 w-full object-cover md:h-96"
);
const embeddedVideoUrl = computed(() => {
  if (!props.section.videoUrl) return "";
  let url = props.section.videoUrl.trim();
  const iframeSrc = url.match(/src=["']([^"']+)["']/i);
  if (iframeSrc?.[1]) {
    url = iframeSrc[1];
  }
  if (!url.startsWith("http")) {
    url = `https://${url}`;
  }
  url = url.replace("watch?v=", "embed/").replace("youtu.be/", "www.youtube.com/embed/");
  return url;
});
const resolvedImages = computed(() =>
  (props.section.images || []).map(img => resolveMediaUrl(img) || img).filter(Boolean)
);
const activeIndex = ref(0);
const activeImage = computed(() => resolvedImages.value[activeIndex.value] || "");
const primaryImage = computed(() => resolvedImages.value[0] || "");

watch(
  () => props.section.images,
  () => {
    activeIndex.value = 0;
  }
);
</script>
