<template>
  <section class="w-full" :style="{ background: sectionBackground }" :id="section.anchorId || undefined">
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
            'mx-auto flex w-full max-w-[340px] flex-col rounded-2xl p-4 text-center',
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
              'flex w-full max-w-[260px] flex-col rounded-2xl p-4 text-center',
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
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { deriveTextPalette, getRelativeLuminance, normalizeHexColor } from "../../utils/colorContrast";
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
const headingLabel = computed(() =>
  resolveHeadingLabel(props.section.headingLabel, headingDefaults.label, localize)
);
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
const sectionBackground = computed(() => props.section.backgroundColor || "linear-gradient(180deg,#f8fafc,#fff)");
const sectionBackgroundHex = computed(() => normalizeHexColor(props.section.backgroundColor));
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const sectionBackgroundIsLight = computed(() => {
  if (!sectionBackgroundHex.value) return !textPalette.value.isLight;
  return getRelativeLuminance(sectionBackgroundHex.value) > 0.7;
});
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);
const neutralShadow = "0 18px 38px -28px rgba(15,23,42,0.28)";

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(14,165,233,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const accentShadow = computed(() => toRgba(accentColor.value, 0.35));
const darkCardBorder = computed(() => `1px solid ${toRgba(accentColor.value, 0.42)}`);

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
const mobileStaggerMs = 500;

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
        h("div", {
          class: "mx-auto flex h-16 w-16 items-center justify-center rounded-full",
          style: {
            background: "transparent",
            color: accentColor.value
          }
        }, [
          h("span", {
            style: {
              fontSize: sectionBackgroundIsLight.value ? "2.25rem" : "2.25rem",
              lineHeight: "1"
            }
          }, componentProps.item.icon || "*")
        ]),
        h("h3", {
          class: "mt-1 text-[20px] font-bold leading-tight",
          style: {
            color: sectionBackgroundIsLight.value ? "#0f172a" : "#f8fafc"
          }
        }, componentProps.item.title),
        h("div", {
          class: "mt-2 w-full text-sm leading-relaxed",
          style: {
            color: sectionBackgroundIsLight.value ? "#475569" : "rgba(241,245,249,0.82)"
          },
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
  const baseStyle = {
    background: sectionBackgroundIsLight.value ? "#ffffff" : "rgba(255,255,255,0.10)",
    border: sectionBackgroundIsLight.value ? "none" : darkCardBorder.value,
    boxShadow: sectionBackgroundIsLight.value ? neutralShadow : `0 22px 46px -30px ${accentShadow.value}`
  } as Record<string, string>;

  if (!animationEnabled.value) return baseStyle;
  if (isMobilePreview.value) {
    return {
      ...baseStyle,
      "--reason-duration": `${animationDurationMs.value}ms`,
      "--reason-delay": `${Math.max(0, index) * mobileStaggerMs}ms`
    };
  }
  const delay = cardsInView.value ? Math.max(0, index) * animationStaggerMs.value : 0;
  return {
    ...baseStyle,
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
