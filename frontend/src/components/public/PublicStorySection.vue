<template>
  <section class="w-full" :style="{ background: section.backgroundColor || '#e5eef9' }" :id="section.anchorId || undefined">
    <div class="mx-auto flex max-w-6xl flex-col" :class="outerClass" :style="borderStyle">
      <!-- Layout com imagem única -->
      <div v-if="isSingle" class="flex w-full flex-col" :class="singleLayoutClass">
        <div :class="textBlockClass">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="ctaColor" />
          <h1 class="text-3xl font-bold leading-tight md:text-4xl" :style="{ color: primaryText }">
            {{ section.title }}
          </h1>
          <div
            v-if="storySubtitleHtml"
            class="text-base leading-relaxed md:text-lg"
            :style="{ color: mutedText }"
            v-html="storySubtitleHtml"
          ></div>
          <div :class="ctaContainerClass">
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
        <div :class="[mediaContainerClass, isMobilePreview ? 'mt-6' : 'md:mt-0']">
          <div :class="mediaInnerClass">
            <template v-if="primaryMedia?.type === 'video'">
              <div class="relative pt-[56.25%]">
                <iframe
                  :class="iframeClass"
                  :src="primaryMedia.url"
                  title="Video"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              </div>
            </template>
            <img
              v-else-if="primaryMedia"
              :src="primaryMedia.url"
              alt="Destaque"
              class="h-full w-full cursor-zoom-in object-cover"
              @click="openLightbox(primaryMedia)"
            />
          </div>
        </div>
      </div>

      <!-- Layout com galeria -->
      <div v-else class="grid w-full" :class="galleryLayoutClass">
        <div :class="[textBlockClass, imagePosition === 'left' ? 'md:order-2' : 'md:order-1']">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="ctaColor" />
          <h1 class="text-3xl font-bold leading-tight md:text-4xl" :style="{ color: primaryText }">
            {{ section.title }}
          </h1>
          <div
            v-if="storySubtitleHtml"
            class="text-base leading-relaxed md:text-lg"
            :style="{ color: mutedText }"
            v-html="storySubtitleHtml"
          ></div>
          <div :class="ctaContainerClass">
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
        <div
          class="space-y-4"
          :class="[mediaContainerClass, imagePosition === 'left' ? 'md:order-1' : 'md:order-2', isMobilePreview ? 'mt-6' : 'md:mt-0']"
        >
          <div :class="mediaInnerClass">
            <template v-if="activeMedia?.type === 'video'">
              <div class="relative pt-[56.25%]">
                <iframe
                  :class="iframeClass"
                  :src="activeMedia.url"
                  title="Video"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              </div>
            </template>
            <img
              v-else-if="activeMedia"
              :src="activeMedia.url"
              alt="Destaque"
              :class="[galleryImageClass, 'cursor-zoom-in']"
              @click="openLightbox(activeMedia)"
            />
          </div>
          <div
            v-if="mediaItems.length > 1"
            :class="thumbnailContainerClass"
            :style="thumbnailGridStyle"
          >
            <button
              v-for="(media, idx) in mediaItems"
              :key="`media-thumb-${idx}`"
              class="overflow-hidden rounded-xl ring-2 transition"
              :class="idx === activeIndex ? 'ring-slate-900' : 'ring-transparent hover:ring-slate-300'"
              @click="activeIndex = idx"
            >
              <template v-if="media.type === 'image'">
                <img :src="media.url" alt="Thumb" :class="thumbnailImageClass" />
              </template>
              <template v-else>
                <div :class="thumbnailVideoWrapperClass">
                  <img
                    v-if="media.thumb"
                    :src="media.thumb"
                    alt="Thumb vídeo"
                    class="h-full w-full object-cover opacity-80"
                  />
                  <div class="absolute inset-0 flex items-center justify-center">
                    <svg class="h-6 w-6 text-white" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M8 5v14l11-7z"></path>
                    </svg>
                  </div>
                </div>
              </template>
            </button>
          </div>
        </div>
      </div>
    </div>
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="lightboxMedia"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4 py-6 backdrop-blur-sm"
          @click.self="closeLightbox"
        >
          <button
            class="absolute right-4 top-4 rounded-full bg-white/10 p-2 text-white transition hover:bg-white/20"
            type="button"
            @click="closeLightbox"
            aria-label="Fechar visualização"
          >
            <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M18 6l-12 12" />
            </svg>
          </button>
          <div class="max-h-[90vh] w-full max-w-5xl">
            <img
              v-if="lightboxMedia?.type === 'image'"
              :src="lightboxMedia.url"
              alt="Visualização ampliada"
              class="h-full w-full rounded-3xl object-contain"
            />
          </div>
        </div>
      </Transition>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { isWhatsappLink } from "../../utils/links";
import { normalizeYoutubeEmbedUrl, extractYoutubeId } from "../../utils/video";
import type { StorySection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { deriveTextPalette } from "../../utils/colorContrast";

const props = defineProps<{ section: StorySection; previewDevice?: "desktop" | "mobile" }>();
const headingDefaults = getSectionHeadingDefaults("story");

const isSingle = computed(() => props.section.layout !== "gallery");
const imagePosition = computed(() => props.section.imagePosition || "right");
const ctaColor = computed(() => props.section.ctaColor || "#41ce5f");
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
const borderColor = computed(() => props.section.borderColor || props.section.ctaColor || "#41ce5f");
const borderStyle = computed(() =>
  props.section.borderEnabled ? { borderColor: borderColor.value, borderWidth: "2px", borderStyle: "solid" } : {}
);
const outerClass = computed(() =>
  props.section.borderEnabled
    ? "my-6 border-2 border-transparent p-0 gap-0 md:flex-row md:items-stretch overflow-hidden rounded-[30px] bg-white/90 shadow-xl"
    : "gap-8 px-6 py-12 md:flex-row md:items-center md:gap-12"
);
const headingLabel = computed(() => props.section.headingLabel ?? props.section.badge ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const storySubtitleHtml = computed(() => sanitizeHtml(props.section.subtitle));
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);
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
const textBlockClass = computed(() => {
  const baseClasses = props.section.borderEnabled
    ? ["flex-1 space-y-5 bg-white px-6 py-8 md:px-10 md:py-12 flex flex-col justify-center"]
    : ["flex-1 space-y-5 flex flex-col justify-center"];
  baseClasses.push("text-center md:text-left", "items-center md:items-start");
  return baseClasses.join(" ");
});
const ctaContainerClass = computed(() => "flex flex-wrap items-center gap-4 justify-center md:justify-start");
const mediaContainerClass = computed(() =>
  props.section.borderEnabled ? "flex-1 flex flex-col w-full md:items-stretch" : "flex-1 flex flex-col w-full md:items-stretch"
);
const mediaInnerClass = computed(() =>
  props.section.borderEnabled ? "flex-1 w-full overflow-hidden" : "flex-1 w-full overflow-hidden rounded-3xl shadow-2xl ring-1 ring-slate-200"
);
const iframeClass = computed(() =>
  props.section.borderEnabled
    ? "absolute inset-0 h-full w-full object-cover"
    : "absolute inset-0 h-full w-full rounded-3xl object-cover"
);
const galleryImageClass = computed(() =>
  props.section.borderEnabled ? "h-full w-full object-cover" : "h-80 w-full object-cover md:h-96"
);
const thumbnailContainerClass = computed(() =>
  isMobilePreview.value ? "w-full grid grid-cols-2 gap-2" : "w-full grid gap-3 justify-items-stretch"
);
const thumbnailGridStyle = computed(() => {
  if (isMobilePreview.value) return undefined;
  const columns = Math.min(mediaItems.value.length, 5);
  return {
    gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`
  };
});
const thumbnailImageClass = computed(() => "w-full aspect-[4/3] object-cover");
const thumbnailVideoWrapperClass = computed(() => "relative overflow-hidden rounded-xl bg-slate-900/70 text-white w-full aspect-[4/3]");
const youtubeThumbnail = (url: string) => {
  const id = extractYoutubeId(url);
  return id ? `https://img.youtube.com/vi/${id}/hqdefault.jpg` : "";
};
type StoryMediaItem =
  | { type: "video"; url: string; thumb?: string }
  | { type: "image"; url: string };
const videoInputs = computed(() => {
  const list = Array.isArray(props.section.videoUrls)
    ? props.section.videoUrls.map(video => (typeof video === "string" ? video.trim() : "")).filter(Boolean)
    : [];
  if (typeof props.section.videoUrl === "string") {
    const legacy = props.section.videoUrl.trim();
    if (legacy && !list.includes(legacy)) {
      list.unshift(legacy);
    }
  }
  return list;
});
const resolvedVideos = computed<StoryMediaItem[]>(() =>
  videoInputs.value
    .map(url => {
      const normalized = normalizeYoutubeEmbedUrl(url);
      if (!normalized) return null;
      return { type: "video" as const, url: normalized, thumb: youtubeThumbnail(url) };
    })
    .filter((item): item is StoryMediaItem => !!item)
);
const resolvedImages = computed(() =>
  (props.section.images || []).map(img => resolveMediaUrl(img) || img).filter(Boolean)
);
const mediaItems = computed<StoryMediaItem[]>(() => [
  ...resolvedVideos.value,
  ...resolvedImages.value.map(url => ({ type: "image" as const, url }))
]);
const primaryMedia = computed(() => mediaItems.value[0] || null);
const activeIndex = ref(0);
const activeMedia = computed(() => mediaItems.value[activeIndex.value] || null);
const lightboxMedia = ref<StoryMediaItem | null>(null);
const hasWindow = typeof window !== "undefined";
const openLightbox = (media?: StoryMediaItem | null) => {
  if (!media || media.type !== "image") return;
  lightboxMedia.value = media;
};
const closeLightbox = () => {
  lightboxMedia.value = null;
};
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    closeLightbox();
  }
};
watch(
  () => [props.section.images, props.section.videoUrls, props.section.videoUrl],
  () => {
    activeIndex.value = 0;
  },
  { deep: true }
);

watch(
  mediaItems,
  newItems => {
    if (activeIndex.value > 0 && activeIndex.value >= newItems.length) {
      activeIndex.value = 0;
    }
  },
  { deep: true }
);

watch(
  () => lightboxMedia.value,
  value => {
    if (!hasWindow) return;
    if (value) {
      window.addEventListener("keydown", handleKeydown);
      document.body.style.setProperty("overflow", "hidden");
    } else {
      window.removeEventListener("keydown", handleKeydown);
      document.body.style.removeProperty("overflow");
    }
  }
);

onBeforeUnmount(() => {
  if (!hasWindow) return;
  window.removeEventListener("keydown", handleKeydown);
  document.body.style.removeProperty("overflow");
});
</script>

