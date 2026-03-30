<template>
  <section
    ref="sectionRef"
    class="w-full"
    :style="{ background: section.backgroundColor || '#e5eef9' }"
    :id="section.anchorId || undefined"
  >
    <div class="mx-auto flex max-w-6xl flex-col" :class="outerClass" :style="borderStyle">
      <!-- Layout com imagem única -->
      <div v-if="isSingle" class="flex w-full flex-col" :class="singleLayoutClass">
        <div :class="textBlockClass" :style="textAnimationStyle">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="ctaColor" />
          <h1 class="text-3xl font-bold leading-tight md:text-4xl" :style="{ color: primaryText }">
            {{ storyTitleText }}
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
              :class="[
                'inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl',
                desktopCtaHoverClass,
                ctaShimmerClass
              ]"
              :style="{ background: ctaColor, color: ctaTextColor }"
            >
              {{ ctaLabelText }}
            </a>
          </div>
        </div>
        <div :class="[mediaContainerClass, isMobilePreview ? 'mt-6' : 'md:mt-0']" :style="mediaAnimationStyle">
          <div :class="mediaInnerClass">
            <template v-if="primaryMedia?.type === 'video'">
              <div class="relative pt-[56.25%]" @pointerdown="handlePrimaryPointerDown">
                <iframe
                  :class="iframeClass"
                  :src="primaryMedia.url"
                  :title="videoTitleText"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              </div>
            </template>
            <img
              v-else-if="primaryMedia"
              :src="primaryMedia.url"
              :alt="imageAltText"
              class="h-full w-full cursor-zoom-in object-cover"
              @click="handlePrimaryImageClick(primaryMedia, 0)"
            />
          </div>
        </div>
      </div>

      <!-- Layout com galeria -->
      <div v-else class="grid w-full" :class="galleryLayoutClass">
        <div :class="[textBlockClass, imagePosition === 'left' ? 'md:order-2' : 'md:order-1']" :style="textAnimationStyle">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="ctaColor" />
          <h1 class="text-3xl font-bold leading-tight md:text-4xl" :style="{ color: primaryText }">
            {{ storyTitleText }}
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
              :class="[
                'inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl',
                desktopCtaHoverClass,
                ctaShimmerClass
              ]"
              :style="{ background: ctaColor, color: ctaTextColor }"
            >
              {{ ctaLabelText }}
            </a>
          </div>
        </div>
        <div
          class="space-y-4"
          :class="[mediaContainerClass, imagePosition === 'left' ? 'md:order-1' : 'md:order-2', isMobilePreview ? 'mt-6' : 'md:mt-0']"
          :style="mediaAnimationStyle"
        >
          <div :class="mediaInnerClass">
            <template v-if="activeMedia?.type === 'video'">
              <div class="relative pt-[56.25%]" @pointerdown="handlePrimaryPointerDown">
                <iframe
                  :class="iframeClass"
                  :src="activeMedia.url"
                  :title="videoTitleText"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              </div>
            </template>
            <img
              v-else-if="activeMedia"
              :src="activeMedia.url"
              :alt="imageAltText"
              :class="[galleryImageClass, 'cursor-zoom-in']"
              @click="handlePrimaryImageClick(activeMedia, activeIndex)"
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
              :class="idx === activeIndex ? 'ring-current' : 'ring-transparent hover:ring-slate-300'"
              :style="idx === activeIndex ? activeThumbnailStyle : undefined"
              @click="handleThumbnailClick(idx)"
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
            :aria-label="lightboxCloseLabel"
          >
            <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M18 6l-12 12" />
            </svg>
          </button>
          <div class="relative max-h-[90vh] w-full max-w-5xl">
            <template v-if="lightboxMedia?.type === 'image'">
              <img
                :src="lightboxMedia.url"
                :alt="lightboxImageAlt"
                class="h-full w-full rounded-3xl object-contain"
              />
            </template>
            <template v-else-if="lightboxMedia?.type === 'video'">
              <div class="relative w-full rounded-3xl bg-black pt-[56.25%]">
                <iframe
                  class="absolute inset-0 h-full w-full rounded-3xl"
                  :src="lightboxMedia.url"
                  :title="lightboxVideoTitle"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                ></iframe>
              </div>
            </template>
            <button
              v-if="canNavigateLightbox"
              class="absolute left-[-48px] top-1/2 -translate-y-1/2 rounded-full bg-white/20 p-3 text-white transition hover:bg-white/35"
              type="button"
              @click.stop="showPrevLightbox"
              :aria-label="lightboxPrevLabel"
            >
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 18l-6-6 6-6" />
              </svg>
            </button>
            <button
              v-if="canNavigateLightbox"
              class="absolute right-[-48px] top-1/2 -translate-y-1/2 rounded-full bg-white/20 p-3 text-white transition hover:bg-white/35"
              type="button"
              @click.stop="showNextLightbox"
              :aria-label="lightboxNextLabel"
            >
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 6l6 6-6 6" />
              </svg>
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { isWhatsappLink } from "../../utils/links";
import { normalizeYoutubeEmbedUrl, extractYoutubeId } from "../../utils/video";
import type { StorySection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { deriveTextPalette, getReadableTextColor } from "../../utils/colorContrast";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: StorySection; previewDevice?: "desktop" | "mobile" }>();
const localize = createLocalizer(getCurrentLanguage());
const headingDefaults = getSectionHeadingDefaults("story");
const storyCopy = {
  title: { pt: "História em destaque", es: "Historia destacada" },
  cta: { pt: "Saiba mais", es: "Saber más" },
  videoTitle: { pt: "Vídeo em destaque", es: "Video destacado" },
  imageAlt: { pt: "Imagem destaque", es: "Imagen destacada" },
  lightboxClose: { pt: "Fechar visualização", es: "Cerrar visualización" },
  lightboxImageAlt: { pt: "Visualização ampliada", es: "Visualización ampliada" },
  lightboxVideoTitle: { pt: "Vídeo ampliado", es: "Video ampliado" },
  lightboxPrev: { pt: "Ver anterior", es: "Ver anterior" },
  lightboxNext: { pt: "Ver próxima", es: "Ver siguiente" }
} as const;

const isSingle = computed(() => props.section.layout !== "gallery");
const imagePosition = computed(() => props.section.imagePosition || "right");
const ctaColor = computed(() => props.section.ctaColor || "#41ce5f");
const ctaTextColor = computed(() => getReadableTextColor(ctaColor.value));
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
const ctaLabelText = computed(() => {
  const text = localize(props.section.ctaLabel).trim();
  return text.length ? text : localize(storyCopy.cta);
});
const animateContent = computed(() => true);
const ctaShimmerClass = computed(() => "hero-cta-shimmer");
const desktopCtaHoverClass = computed(() => "hero-cta-desktop-hover");
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
const headingLabel = computed(() => {
  const label = localize(props.section.headingLabel).trim();
  if (label.length) return label;
  const badge = localize(props.section.badge).trim();
  if (badge.length) return badge;
  const fallback = headingDefaults.label;
  return typeof fallback === "string" ? fallback : localize(fallback);
});
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const storyTitleText = computed(() => {
  const text = localize(props.section.title).trim();
  return text.length ? text : localize(storyCopy.title);
});
const storySubtitleHtml = computed(() => sanitizeHtml(localize(props.section.subtitle)));
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
  props.section.borderEnabled ? "flex-1 w-full overflow-hidden" : "flex-1 w-full overflow-hidden rounded-3xl shadow-2xl"
);
const iframeClass = computed(() =>
  props.section.borderEnabled
    ? "absolute inset-0 h-full w-full object-cover"
    : "absolute inset-0 h-full w-full object-cover"
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
const videoTitleText = computed(() => localize(storyCopy.videoTitle));
const imageAltText = computed(() => localize(storyCopy.imageAlt));
const lightboxCloseLabel = computed(() => localize(storyCopy.lightboxClose));
const lightboxImageAlt = computed(() => localize(storyCopy.lightboxImageAlt));
const lightboxVideoTitle = computed(() => localize(storyCopy.lightboxVideoTitle));
const lightboxPrevLabel = computed(() => localize(storyCopy.lightboxPrev));
const lightboxNextLabel = computed(() => localize(storyCopy.lightboxNext));
const activeThumbnailStyle = computed(() => ({ "--tw-ring-color": ctaColor.value, "--tw-ring-offset-width": "1px", "--tw-ring-width": "2.5px", color: ctaColor.value }));
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
const lightboxIndex = ref<number | null>(null);
const hasWindow = typeof window !== "undefined";
const userInteracted = ref(false);
let autoCycleTimer: number | null = null;
const AUTO_CYCLE_INTERVAL = 5000;
const stopAutoCycle = () => {
  if (autoCycleTimer && hasWindow) {
    window.clearInterval(autoCycleTimer);
    autoCycleTimer = null;
  }
};
const scheduleAutoCycle = () => {
  if (!hasWindow || userInteracted.value || isSingle.value || mediaItems.value.length <= 1) {
    stopAutoCycle();
    return;
  }
  stopAutoCycle();
  autoCycleTimer = window.setInterval(() => {
    activeIndex.value = (activeIndex.value + 1) % mediaItems.value.length;
  }, AUTO_CYCLE_INTERVAL);
};
const registerUserInteraction = () => {
  if (userInteracted.value) return;
  userInteracted.value = true;
  stopAutoCycle();
};
const goToLightboxIndex = (index: number) => {
  const items = mediaItems.value;
  if (!items.length) return;
  const normalized = ((index % items.length) + items.length) % items.length;
  lightboxIndex.value = normalized;
  lightboxMedia.value = items[normalized] || null;
};
const openLightbox = (media?: StoryMediaItem | null, index?: number) => {
  if (!media) return;
  registerUserInteraction();
  if (typeof index === "number") {
    goToLightboxIndex(index);
    return;
  }
  const found = mediaItems.value.findIndex(item => item === media);
  goToLightboxIndex(found >= 0 ? found : 0);
};
const closeLightbox = () => {
  lightboxMedia.value = null;
  lightboxIndex.value = null;
  if (!userInteracted.value) {
    scheduleAutoCycle();
  }
};
const showNextLightbox = () => {
  if (lightboxIndex.value === null) return;
  goToLightboxIndex(lightboxIndex.value + 1);
};
const showPrevLightbox = () => {
  if (lightboxIndex.value === null) return;
  goToLightboxIndex(lightboxIndex.value - 1);
};
const handlePrimaryImageClick = (media?: StoryMediaItem | null, index?: number) => {
  if (!media) return;
  openLightbox(media, index);
};
const handlePrimaryPointerDown = () => {
  registerUserInteraction();
};
const handleThumbnailClick = (index: number) => {
  activeIndex.value = index;
  registerUserInteraction();
};
const sectionRef = ref<HTMLElement | null>(null);
const intersectionProgress = ref(0);
const isDesktopViewport = ref(true);
const viewMode = computed(() => {
  if (props.previewDevice === "mobile") return "mobile";
  if (props.previewDevice === "desktop") return "desktop";
  return isDesktopViewport.value ? "desktop" : "mobile";
});
const animateAsDesktop = computed(() => viewMode.value === "desktop");
const hasRevealedMobile = ref(false);
const clampValue = (value: number, min = 0, max = 1) => Math.min(max, Math.max(min, value));
const desktopAnimationProgress = computed(() => clampValue((intersectionProgress.value - 0.08) / 0.8));
const mobileAnimationProgress = computed(() => clampValue((intersectionProgress.value - 0.08) / 0.8));
const textAnimationStyle = computed(() => {
  if (!animateContent.value) {
    return { opacity: "1", transform: "translate3d(0, 0, 0)" };
  }
  const progress = animateAsDesktop.value ? desktopAnimationProgress.value : mobileAnimationProgress.value;
  const eased = Math.pow(progress, 1.4);
  const offsetY = (1 - eased) * 40;
  if (!animateAsDesktop.value && hasRevealedMobile.value) {
    return { opacity: "1", transform: "translate3d(0, 0, 0)" };
  }
  return {
    opacity: eased.toString(),
    transform: `translate3d(0, ${offsetY}px,0)`
  };
});
const mediaAnimationStyle = computed(() => {
  if (!animateContent.value) {
    return { opacity: "1", transform: "translate3d(0, 0, 0)" };
  }
  const progress = animateAsDesktop.value ? desktopAnimationProgress.value : mobileAnimationProgress.value;
  const eased = Math.pow(progress, 1.4);
  const offsetY = (1 - eased) * 40;
  if (!animateAsDesktop.value && hasRevealedMobile.value) {
    return { opacity: "1", transform: "translate3d(0, 0, 0)" };
  }
  return {
    opacity: eased.toString(),
    transform: `translate3d(0, ${offsetY}px,0)`
  };
});
const canNavigateLightbox = computed(() => mediaItems.value.length > 1);
const scrollThresholds = Array.from({ length: 21 }, (_, index) => index / 20);
let scrollObserver: IntersectionObserver | null = null;
const handleResize = () => {
  if (!hasWindow) return;
  isDesktopViewport.value = window.innerWidth >= 1024;
};
const setupScrollObserver = () => {
  if (!hasWindow || !sectionRef.value) return;
  if (scrollObserver) {
    scrollObserver.disconnect();
    scrollObserver = null;
  }
  scrollObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.target === sectionRef.value) {
          intersectionProgress.value = entry.intersectionRatio;
        }
      });
    },
    { threshold: scrollThresholds }
  );
  scrollObserver.observe(sectionRef.value);
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
    userInteracted.value = false;
    lightboxIndex.value = null;
    lightboxMedia.value = null;
    stopAutoCycle();
    nextTick(() => scheduleAutoCycle());
  },
  { deep: true }
);

watch(
  mediaItems,
  newItems => {
    if (!newItems.length) {
      activeIndex.value = 0;
      lightboxIndex.value = null;
      lightboxMedia.value = null;
      stopAutoCycle();
      return;
    }
    if (activeIndex.value >= newItems.length) {
      activeIndex.value = 0;
    }
    if (lightboxIndex.value !== null) {
      if (lightboxIndex.value >= newItems.length) {
        goToLightboxIndex(newItems.length - 1);
      } else {
        goToLightboxIndex(lightboxIndex.value);
      }
    }
    if (!userInteracted.value) {
      nextTick(() => scheduleAutoCycle());
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

watch(
  () => isSingle.value,
  () => {
    if (userInteracted.value) {
      stopAutoCycle();
      return;
    }
    nextTick(() => scheduleAutoCycle());
  }
);

watch(
  () => userInteracted.value,
  value => {
    if (value) {
      stopAutoCycle();
    } else {
      nextTick(() => scheduleAutoCycle());
    }
  }
);

watch(viewMode, mode => {
  if (mode === "desktop") {
    hasRevealedMobile.value = false;
  }
});

watch(
  () => intersectionProgress.value,
  value => {
    if (!animateAsDesktop.value && !hasRevealedMobile.value && value >= 0.96) {
      hasRevealedMobile.value = true;
    }
  }
);

watch(sectionRef, () => {
  if (!hasWindow) return;
  setupScrollObserver();
});

onMounted(() => {
  if (hasWindow) {
    handleResize();
    window.addEventListener("resize", handleResize);
  }
  setupScrollObserver();
  scheduleAutoCycle();
});

onBeforeUnmount(() => {
  if (!hasWindow) return;
  stopAutoCycle();
  if (scrollObserver) {
    scrollObserver.disconnect();
    scrollObserver = null;
  }
  window.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("resize", handleResize);
  document.body.style.removeProperty("overflow");
});
</script>

