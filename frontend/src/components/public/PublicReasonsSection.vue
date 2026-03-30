<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="text-center">
        <div class="flex justify-center">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accentColor" />
        </div>
        <h1 class="mt-2 text-3xl font-bold md:text-4xl" :style="{ color: primaryText }">{{ titleText }}</h1>
        <p v-if="subtitleText" class="mt-2 text-base leading-relaxed md:text-lg" :style="{ color: mutedText }">
          {{ subtitleText }}
        </p>
      </div>

      <div v-if="isMobilePreview" ref="cardsWrapperRef" class="mt-8 flex flex-col gap-4">
        <article
          v-for="(item, idx) in limitedItems"
          :key="'mobile-' + idx"
          :class="[
            'mx-auto flex w-full max-w-[340px] flex-col rounded-2xl bg-white/95 p-4 text-center shadow-[0_16px_40px_-28px_rgba(15,23,42,0.6)] ring-1 ring-slate-100',
            ...cardClasses(idx)
          ]"
          :style="cardStyle(idx)"
          :data-card-index="idx"
          :ref="el => registerMobileCardRef(el, idx)"
        >
          <ReasonCard :item="item" :index="idx" />
        </article>
      </div>

      <div v-else ref="cardsWrapperRef" class="mt-8 flex flex-col items-center gap-5">
        <div
          v-for="(row, rowIndex) in desktopRows"
          :key="'row-' + rowIndex"
          class="flex w-full flex-wrap justify-center gap-4"
        >
          <article
            v-for="(item, idx) in row"
            :key="'card-' + rowIndex + '-' + idx"
            :class="[
              'flex w-full max-w-[260px] flex-col rounded-2xl bg-white/95 p-4 text-center shadow-[0_16px_40px_-28px_rgba(15,23,42,0.6)] ring-1 ring-slate-100',
              ...cardClasses(desktopRowOffsets[rowIndex] + idx)
            ]"
            :style="cardStyle(desktopRowOffsets[rowIndex] + idx)"
          >
            <ReasonCard :item="item" :index="desktopRowOffsets[rowIndex] + idx" />
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, inject, isRef, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { ReasonsSection, ReasonItem } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { deriveTextPalette } from "../../utils/colorContrast";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: ReasonsSection; previewDevice?: "desktop" | "mobile" }>();
const localize = createLocalizer(getCurrentLanguage());
const headingDefaults = getSectionHeadingDefaults("reasons");
const reasonsCopy = {
  title: { pt: "Motivos para escolher", es: "Motivos para elegir" },
  subtitle: { pt: "", es: "" },
  itemTitle: { pt: "Motivo", es: "Motivo" },
  itemDescription: { pt: "Atualize este motivo com detalhes.", es: "Actualiza este motivo con detalles." }
} as const;
const isMobilePreview = computed(() => props.previewDevice === "mobile");
const headingLabel = computed(() => {
  const label = localize(props.section.headingLabel).trim();
  if (label.length) return label;
  const fallback = headingDefaults.label;
  return typeof fallback === "string" ? fallback : localize(fallback);
});
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const titleText = computed(() => {
  const text = localize(props.section.title).trim();
  return text.length ? text : localize(reasonsCopy.title);
});
const subtitleText = computed(() => localize(props.section.subtitle).trim());
const branding = inject(PUBLIC_BRANDING_KEY, null);
const brandingPrimary = computed(() => {
  if (!branding) return "";
  const data = isRef(branding) ? branding.value : branding;
  if (typeof data === "object" && data) {
    const color = (data as Record<string, any>).primary_color;
    if (typeof color === "string" && color.trim()) return color.trim();
  }
  return "";
});
const accentColor = computed(() => props.section.ctaColor || brandingPrimary.value || "#41ce5f");
const MAX_ITEMS = 8;
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);

const limitedItems = computed(() => (props.section.items || []).slice(0, MAX_ITEMS));
const cardsInView = ref(false);
const cardsWrapperRef = ref<HTMLElement | null>(null);
const revealedMobileCards = ref<boolean[]>([]);
const mobileCardRefs = ref<(HTMLElement | null)[]>([]);
let cardsObserver: IntersectionObserver | null = null;
let mobileCardsObserver: IntersectionObserver | null = null;
const animationEnabled = computed(() => true);
const clampDuration = (value?: number) => {
  const raw = typeof value === "number" && !Number.isNaN(value) ? value : 550;
  return Math.min(2000, Math.max(200, Math.round(raw)));
};
const clampStagger = (value?: number) => {
  const raw = typeof value === "number" && !Number.isNaN(value) ? value : 150;
  return Math.min(800, Math.max(40, Math.round(raw)));
};
const animationDurationMs = computed(() => clampDuration(props.section.animationDuration));
const animationStaggerMs = computed(() => clampStagger(props.section.cardAnimationStagger));
const mobileStaggerMs = 4000;

const desktopRows = computed(() => {
  const items = limitedItems.value;
  const total = items.length;
  if (!total) return [];
  if (total <= 4) return [items];
  const firstRowCount = Math.min(4, Math.ceil(total / 2));
  const first = items.slice(0, firstRowCount);
  const second = items.slice(firstRowCount);
  return [first, second];
});

const desktopRowOffsets = computed(() => {
  const rows = desktopRows.value;
  const offsets: number[] = [];
  let current = 0;
  rows.forEach(row => {
    offsets.push(current);
    current += row.length;
  });
  return offsets;
});

const descriptionHtml = (text?: any) => {
  const localized = localize(text);
  const sanitized = sanitizeHtml(localized);
  if (sanitized && sanitized.trim().length) {
    return sanitized;
  }
  return sanitizeHtml(localize(reasonsCopy.itemDescription));
};

const ReasonCard = defineComponent({
  props: {
    item: {
      type: Object as () => ReasonItem,
      required: true
    }
  },
  setup(componentProps) {
    return () =>
      h("div", { class: "reason-card-content" }, [
        h("div", { class: "mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-50 text-3xl" }, [
          h("span", componentProps.item.icon || "⭐")
        ]),
        h("h3", { class: "mt-3 text-lg font-semibold text-slate-900" }, componentProps.item.title),
        h("div", {
          class: "mt-2 w-full text-sm leading-relaxed text-slate-600",
          innerHTML: descriptionHtml(componentProps.item.description)
        })
      ]);
  }
});

const cardClasses = (index: number) => {
  if (!animationEnabled.value) return [];
  const isMobile = isMobilePreview.value;
  const isVisible = isMobile ? !!revealedMobileCards.value[index] : cardsInView.value;
  return ["reason-card", isVisible ? "reason-card-visible" : "reason-card-hidden"];
};

const cardStyle = (index: number) => {
  if (!animationEnabled.value) return undefined;
  if (isMobilePreview.value) {
    return {
      "--reason-duration": `${animationDurationMs.value}ms`,
      "--reason-delay": `${Math.max(0, index) * mobileStaggerMs}ms`
    };
  }
  const delay = cardsInView.value ? Math.max(0, index) * animationStaggerMs.value : 0;
  return {
    "--reason-duration": `${animationDurationMs.value}ms`,
    "--reason-delay": `${delay}ms`
  };
};

const setupObserver = () => {
  if (typeof window === "undefined" || cardsInView.value || !animationEnabled.value || isMobilePreview.value) return;
  if (cardsObserver) {
    cardsObserver.disconnect();
    cardsObserver = null;
  }
  if (!cardsWrapperRef.value) return;
  cardsObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          cardsInView.value = true;
          if (cardsObserver) {
            cardsObserver.disconnect();
            cardsObserver = null;
          }
        }
      });
    },
    { threshold: 0.15 }
  );
  cardsObserver.observe(cardsWrapperRef.value);
};

const registerMobileCardRef = (el: HTMLElement | null, index: number) => {
  mobileCardRefs.value[index] = el;
  if (el) {
    el.dataset.cardIndex = String(index);
  }
};

const observeNextMobileCard = (fromIndex = 0) => {
  if (!mobileCardsObserver || !animationEnabled.value || !isMobilePreview.value) return;
  for (let i = fromIndex; i < mobileCardRefs.value.length; i++) {
    if (!revealedMobileCards.value[i] && mobileCardRefs.value[i]) {
      mobileCardsObserver.observe(mobileCardRefs.value[i]!);
      break;
    }
  }
};

const setupMobileCardsObserver = () => {
  if (typeof window === "undefined" || !animationEnabled.value || !isMobilePreview.value) return;
  if (mobileCardsObserver) {
    mobileCardsObserver.disconnect();
    mobileCardsObserver = null;
  }
  mobileCardsObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        const target = entry.target as HTMLElement;
        const dataIndex = target.dataset.cardIndex;
        const index = typeof dataIndex === "string" ? Number(dataIndex) : NaN;
        if (entry.isIntersecting && !Number.isNaN(index)) {
          revealedMobileCards.value[index] = true;
          mobileCardsObserver?.unobserve(target);
          observeNextMobileCard(index + 1);
        }
      });
    },
    { threshold: 0.15 }
  );
  observeNextMobileCard(0);
};

onMounted(() => {
  setupObserver();
  if (isMobilePreview.value && animationEnabled.value) {
    nextTick(() => setupMobileCardsObserver());
  }
});

watch(cardsWrapperRef, () => {
  if (!cardsInView.value && animationEnabled.value && !isMobilePreview.value) {
    setupObserver();
  }
});

watch(animationEnabled, enabled => {
  if (!enabled) {
    cardsInView.value = false;
    revealedMobileCards.value = limitedItems.value.map(() => true);
    if (cardsObserver) {
      cardsObserver.disconnect();
      cardsObserver = null;
    }
    if (mobileCardsObserver) {
      mobileCardsObserver.disconnect();
      mobileCardsObserver = null;
    }
    return;
  }
  cardsInView.value = false;
  revealedMobileCards.value = limitedItems.value.map(() => (isMobilePreview.value ? false : true));
  nextTick(() => {
    setupObserver();
    if (isMobilePreview.value) {
      setupMobileCardsObserver();
    }
  });
});

watch(
  () => [limitedItems.value.length, isMobilePreview.value, animationEnabled.value],
  () => {
    revealedMobileCards.value = limitedItems.value.map(() => (animationEnabled.value && isMobilePreview.value ? false : true));
    mobileCardRefs.value = limitedItems.value.map(() => null);
    nextTick(() => {
      if (animationEnabled.value && isMobilePreview.value) {
        setupMobileCardsObserver();
      }
    });
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  if (cardsObserver) {
    cardsObserver.disconnect();
    cardsObserver = null;
  }
  if (mobileCardsObserver) {
    mobileCardsObserver.disconnect();
    mobileCardsObserver = null;
  }
});
</script>

<style scoped>
.reason-card {
  opacity: 0;
  transform: translateY(20px);
  transition-property: opacity, transform;
  transition-duration: var(--reason-duration, 0.55s);
  transition-delay: var(--reason-delay, 0s);
  will-change: opacity, transform;
}

.reason-card-visible {
  opacity: 1;
  transform: translateY(0);
}

.reason-card-hidden {
  opacity: 0;
  transform: translateY(20px);
}
</style>
