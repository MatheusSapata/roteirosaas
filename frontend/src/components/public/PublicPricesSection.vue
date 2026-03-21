<template>
  <section
    class="w-full"
    :style="{ background: sectionBackground }"
    :id="section.anchorId || undefined"
  >
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="space-y-6">
        <div class="pb-4 text-center" :style="{ borderBottom: `1px solid ${accentBorder}` }">
          <div class="flex justify-center">
            <SectionHeadingChip
              :text="headingLabel"
              :styleType="headingStyle"
              :accent="headingChipAccent"
            />
          </div>

          <h1 class="mt-3 text-2xl font-bold" :style="{ color: primaryText }">
            {{ title }}
          </h1>

          <p v-if="subtitle" class="text-sm" :style="{ color: mutedText }">
            {{ subtitle }}
          </p>
        </div>

        <div class="space-y-8">
          <article
            v-for="(item, index) in section.items"
            :key="'column-' + index"
            class="relative flex flex-col gap-4 rounded-2xl border p-5 text-center transition hover:-translate-y-0.5 md:flex-row md:items-center md:justify-between md:text-left"
            :style="cardStyle(item)"
          >
            <div class="space-y-2 text-center md:text-left">
              <p
                v-if="item.titleLabel"
                class="mt-4 text-xs uppercase tracking-[0.2em] md:mt-0"
                :style="{ color: paletteFor(item).secondary }"
              >
                {{ item.titleLabel.toUpperCase() }}
              </p>

              <p class="text-xl font-semibold" :style="{ color: paletteFor(item).primary }">
                {{ item.title }}
              </p>
            </div>

            <div class="flex flex-col items-center gap-4 md:flex-row md:items-center md:justify-between">
              <div class="space-y-1 md:text-right">
                <p
                  v-if="item.priceLabel"
                  class="text-sm font-medium"
                  :style="{ color: paletteFor(item).secondary }"
                >
                  {{ item.priceLabel }}
                </p>

                <p class="text-3xl font-bold" :style="{ color: paletteFor(item).primary }">
                  {{ formatPrice(item.price, item.currency) }}
                </p>

                <p
                  v-if="item.description"
                  class="text-xs"
                  :style="{ color: paletteFor(item).muted }"
                >
                  {{ item.description }}
                </p>
              </div>

              <a
                v-if="ctaLink"
                :href="ctaLink"
                target="_blank"
                rel="noopener"
                data-track-event="cta"
                :data-track-type="ctaTrackType"
                class="inline-flex w-full max-w-sm items-center justify-center rounded-full px-5 py-2 text-sm font-semibold shadow-md transition md:mx-0 md:w-auto"
                :style="ctaStyle(item)"
              >
                {{ section.ctaLabel || "Reservar" }}
              </a>
            </div>

            <span
              v-if="item.badge"
              class="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 rounded-full border px-4 py-1 text-xs font-semibold uppercase tracking-wide shadow-sm"
              :style="badgeStyle(item)"
            >
              <span aria-hidden="true">★</span>
              {{ item.badge }}
            </span>
          </article>
        </div>

        <p
          v-if="section.description"
          class="mt-6 text-center text-sm md:text-left"
          :style="{ color: mutedText }"
        >
          {{ section.description }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, inject, isRef } from "vue";
import type { CurrencyCode, PriceItem, PricesSection } from "../../types/page";
import { isWhatsappLink } from "../../utils/links";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { getReadableTextColor } from "../../utils/colorContrast";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";

const props = defineProps<{ section: PricesSection }>();

const defaultAccent = "#41ce5f";
const headingDefaults = getSectionHeadingDefaults("prices");
const defaultTitle = "Planos e opções";
const defaultSubtitle = "Escolha o formato que combina com você.";

const branding = inject(PUBLIC_BRANDING_KEY, null);

const normalizeColor = (value?: string | null) => (typeof value === "string" ? value.trim() : "");

const brandingPrimary = computed(() => {
  if (!branding) return "";
  const data = isRef(branding) ? branding.value : branding;

  if (typeof data === "object" && data) {
    const color = (data as Record<string, any>).primary_color;
    if (typeof color === "string" && color.trim()) {
      return color.trim();
    }
  }

  return "";
});

const accent = computed(() => normalizeColor(props.section.ctaColor) || brandingPrimary.value || defaultAccent);
const cardColor = computed(() => normalizeColor(props.section.cardColor) || accent.value);

const sectionBackground = computed(
  () => normalizeColor(props.section.backgroundColor) || "linear-gradient(180deg,#f8fafc,#fff)"
);

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map((c) => c + c).join("") : cleaned;

  if (full.length !== 6) return `rgba(14,165,233,${alpha})`;

  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);

  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const getContrastTextColor = (color?: string) => {
  if (!color) return "#ffffff";

  const normalized = color.trim();

  if (!normalized.startsWith("#")) {
    return "#ffffff";
  }

  const hex = normalized.replace("#", "");
  const full = hex.length === 3 ? hex.split("").map((c) => c + c).join("") : hex;

  if (full.length !== 6) return "#ffffff";

  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);

  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  return luminance > 0.6 ? "#111827" : "#ffffff";
};

const accentBorder = computed(() => {
  const bg = normalizeColor(props.section.backgroundColor);
  if (bg.startsWith("#")) {
    const contrast = getContrastTextColor(bg);
    return contrast === "#ffffff" ? "rgba(255,255,255,0.16)" : "rgba(15,23,42,0.14)";
  }
  return toRgba(accent.value, 0.25);
});

const headingLabel = computed(() => props.section.headingLabel ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);

const sanitizeLink = (value?: string | null) => {
  if (!value) return "";
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed) || trimmed.startsWith("#")) return trimmed;
  return `https://${trimmed}`;
};

const ctaLink = computed(() => sanitizeLink(props.section.ctaLink));

const title = computed(() =>
  props.section.title && props.section.title.trim().length ? props.section.title : defaultTitle
);

const subtitle = computed(() => {
  const raw = props.section.subtitle ?? null;
  if (raw === null) return defaultSubtitle;
  return raw.trim().length ? raw : "";
});

const effectiveSectionTextColor = computed(() => {
  const custom = normalizeColor(props.section.textColor);
  if (custom) return custom;

  const bg = normalizeColor(props.section.backgroundColor);
  if (bg.startsWith("#")) {
    return getContrastTextColor(bg);
  }

  return "#ffffff";
});

const primaryText = computed(() => effectiveSectionTextColor.value);

const mutedText = computed(() =>
  primaryText.value === "#ffffff"
    ? "rgba(255,255,255,0.82)"
    : "rgba(15,23,42,0.72)"
);

const headingChipAccent = computed(() => {
  const bg = normalizeColor(props.section.backgroundColor);

  if (bg.startsWith("#")) {
    return getContrastTextColor(bg) === "#ffffff"
      ? "rgba(255,255,255,0.92)"
      : "#0f172a";
  }

  return "rgba(255,255,255,0.92)";
});

const cardTextPalette = computed(() => {
  const primary = getReadableTextColor(cardColor.value);
  const secondary = primary === "#ffffff" ? "rgba(255,255,255,0.88)" : "rgba(15,23,42,0.72)";
  const muted = primary === "#ffffff" ? "rgba(255,255,255,0.75)" : "rgba(15,23,42,0.6)";
  return { primary, secondary, muted };
});

const baseCardStyle = computed(() => ({
  background: cardColor.value,
  borderColor: toRgba(cardColor.value, 0.35),
  boxShadow: `0 25px 60px -30px ${toRgba(cardColor.value, 0.45)}`
}));

const highlightCardStyle = computed(() => ({
  background: cardColor.value,
  borderColor: "transparent",
  boxShadow: `0 40px 80px -35px ${toRgba(cardColor.value, 0.6)}`
}));

const paletteFor = (_item: PriceItem) => cardTextPalette.value;
const cardStyle = (item: PriceItem) => (item.highlight ? highlightCardStyle.value : baseCardStyle.value);

const ctaStyle = (_item: PriceItem) => {
  const buttonBg = "#ffffff";

  return {
    background: buttonBg,
    color: getContrastTextColor(buttonBg),
    border: `1px solid ${toRgba(cardColor.value, 0.14)}`
  };
};

const badgeStyle = (item: PriceItem) => {
  if (item.highlight) {
    const bg = "#ffffff";
    return {
      background: bg,
      color: getContrastTextColor(bg),
      borderColor: "#ffffff"
    };
  }

  const bg = cardColor.value;

  return {
    background: bg,
    color: getContrastTextColor(bg),
    borderColor: toRgba(cardColor.value, 0.4)
  };
};

const currencyMap: Record<CurrencyCode, { locale: string; currency: CurrencyCode }> = {
  BRL: { locale: "pt-BR", currency: "BRL" },
  USD: { locale: "en-US", currency: "USD" },
  EUR: { locale: "de-DE", currency: "EUR" },
  ARS: { locale: "es-AR", currency: "ARS" }
};

const defaultCurrency = currencyMap.BRL;

const normalizePrice = (price: number | string | undefined | null): number => {
  if (typeof price === "number" && !Number.isNaN(price)) return price;

  if (typeof price === "string") {
    const cleaned = price.replace(/\./g, "").replace(",", ".").trim();
    const parsed = Number.parseFloat(cleaned);
    if (!Number.isNaN(parsed)) return parsed;
  }

  return 0;
};

const formatPrice = (price: number | string | undefined, currency?: PriceItem["currency"]) => {
  const config = currencyMap[(currency as CurrencyCode) || "BRL"] || defaultCurrency;
  const value = normalizePrice(price);

  try {
    return new Intl.NumberFormat(config.locale, {
      style: "currency",
      currency: config.currency
    }).format(value);
  } catch {
    return `R$ ${value.toLocaleString("pt-BR")}`;
  }
};

const ctaTrackType = computed(() => (ctaLink.value && isWhatsappLink(ctaLink.value) ? "whatsapp" : "cta"));
</script>