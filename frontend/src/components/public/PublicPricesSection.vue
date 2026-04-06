<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="space-y-6">
        <div class="pb-4 text-center" :style="{ borderBottom: `1px solid ${accentBorder}` }">
          <div class="flex justify-center">
            <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accent" />
          </div>
          <h1 class="mt-1 text-3xl font-bold md:text-4xl" :style="{ color: primaryText }">{{ title }}</h1>
          <p v-if="subtitle" class="text-sm" :style="{ color: mutedText }">{{ subtitle }}</p>
        </div>

        <div class="space-y-8">
          <article
            v-for="(item, index) in section.items || []"
            :key="'column-' + index"
            :class="[
              'relative flex flex-col gap-4 rounded-2xl border p-5 text-center transition md:flex-row md:items-center md:justify-between md:text-left',
              item.highlight
                ? 'border-transparent shadow-xl hover:-translate-y-1 hover:shadow-2xl'
                : 'border-slate-100 bg-white/95 hover:-translate-y-0.5 hover:shadow-lg'
            ]"
            :style="itemCardStyle(item)"
          >
            <div class="space-y-2 text-center md:text-left">
              <p
                v-if="itemTitleLabel(item)"
                class="mt-4 text-xs uppercase tracking-[0.2em] md:mt-0"
                :style="{ color: itemSecondaryTextColor(item) }"
              >
                {{ itemTitleLabel(item).toUpperCase() }}
              </p>

              <p
                class="text-xl font-bold md:text-2xl md:font-bold"
                :style="{ color: itemPrimaryTextColor(item) }"
              >
                {{ itemTitle(item) }}
              </p>
            </div>

            <div class="flex flex-col items-center gap-4 md:flex-row md:items-center md:justify-between">
              <div class="space-y-1 md:text-right">
                <p
                  v-if="itemPriceLabel(item)"
                  class="text-sm font-medium"
                  :style="{ color: itemSecondaryTextColor(item) }"
                >
                  {{ itemPriceLabel(item) }}
                </p>

                <p
                  class="text-3xl font-bold"
                  :style="{ color: itemPriceColor(item) }"
                >
                  {{ formatPrice(item.price, item.currency) }}
                </p>

                <p
                  v-if="itemDescription(item)"
                  class="text-xs"
                  :style="{ color: itemSecondaryTextColor(item) }"
                >
                  {{ itemDescription(item) }}
                </p>
              </div>

              <a
                v-if="itemLink(item)"
                :href="itemLink(item)"
                target="_blank"
                rel="noopener"
                data-track-event="cta"
                :data-track-type="trackType(itemLink(item))"
                :class="[
                  'inline-flex items-center justify-center rounded-full px-5 py-2 text-sm font-semibold shadow-md transition w-full md:w-auto max-w-sm mx-auto md:mx-0 hero-cta-shimmer hero-cta-desktop-hover',
                  item.highlight ? 'hover:-translate-y-0.5 hover:shadow-xl' : 'hover:-translate-y-0.5 hover:shadow-lg'
                ]"
                :style="{ background: buttonBackground(item), color: buttonTextColor(item) }"
              >
                {{ itemCtaLabel(item) }}
              </a>
              <div
                v-else
                class="inline-flex w-full max-w-sm items-center justify-center rounded-full border border-dashed border-slate-200 px-5 py-2 text-sm font-semibold text-slate-400 md:w-auto"
              >
                {{ itemCtaLabel(item) }}
              </div>
            </div>

            <span
              v-if="itemBadge(item)"
              class="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 rounded-full border px-4 py-1 text-xs font-semibold uppercase tracking-wide shadow-sm"
              :style="badgeStyle(item.highlight)"
            >
              <span aria-hidden="true">&bull;</span>
              {{ itemBadge(item) }}
            </span>
          </article>
        </div>

        <p v-if="sectionDescription" class="mt-6 text-sm text-center md:text-left" :style="{ color: mutedText }">
          {{ sectionDescription }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CurrencyCode, PriceItem, PricesSection } from "../../types/page";
import { isWhatsappLink } from "../../utils/links";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../utils/sectionHeadings";
import { deriveTextPalette, getReadableTextColor } from "../../utils/colorContrast";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: PricesSection }>();

const defaultAccent = "#41ce5f";
const headingDefaults = getSectionHeadingDefaults("prices");
const defaultCopy = {
  title: { pt: "Planos e opções", es: "Planes y opciones" },
  subtitle: { pt: "Escolha o formato que combina com você.", es: "Elige el formato que va contigo." },
  cta: { pt: "Reservar", es: "Reservar" }
} as const;

const currentLanguage = getCurrentLanguage();
const localize = createLocalizer(currentLanguage);

const buttonColor = computed(() => props.section.ctaColor || defaultAccent);
const accent = computed(() => buttonColor.value);

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;

  if (full.length !== 6) {
    return `rgba(14,165,233,${alpha})`;
  }

  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);

  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const accentBorder = computed(() => toRgba(accent.value, 0.25));
const headingLabel = computed(() =>
  resolveHeadingLabel(props.section.headingLabel, headingDefaults.label, localize)
);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);

const sanitizeLink = (value?: string | null) => {
  if (!value) return "";

  const trimmed = value.trim();
  if (!trimmed) return "";

  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed) || trimmed.startsWith("#")) {
    return trimmed;
  }

  return `https://${trimmed}`;
};

const baseCtaLink = computed(() => sanitizeLink(props.section.ctaLink));

const title = computed(() => {
  const text = localize(props.section.title);
  return text.trim().length ? text : localize(defaultCopy.title);
});

const subtitle = computed(() => {
  if (props.section.subtitle === null || typeof props.section.subtitle === "undefined") {
    return localize(defaultCopy.subtitle);
  }
  const value = localize(props.section.subtitle);
  return value.trim().length ? value : "";
});

const sectionDescription = computed(() => {
  const value = localize(props.section.description);
  return value.trim();
});

const sectionCtaLabel = computed(() => localize(props.section.ctaLabel));
const highlightShadow = computed(() => toRgba(accent.value, 0.45));

const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);

const normalCardBackground = "#ffffff";

const normalizeColor = (color?: string | null) => (color || "").trim().toLowerCase();

const isReadableColorLight = (background: string) => {
  const readable = normalizeColor(getReadableTextColor(background));
  return (
    readable === "#ffffff" ||
    readable === "#fff" ||
    readable === "white" ||
    readable === "rgb(255,255,255)" ||
    readable === "rgb(255, 255, 255)"
  );
};

const itemBackground = (item: PriceItem) => {
  return item.highlight ? accent.value : normalCardBackground;
};

const itemPrimaryTextColor = (item: PriceItem) => {
  return getReadableTextColor(itemBackground(item));
};

const itemSecondaryTextColor = (item: PriceItem) => {
  const background = itemBackground(item);
  const useLightText = isReadableColorLight(background);

  if (useLightText) {
    return "rgba(255,255,255,0.88)";
  }

  return "rgba(15,23,42,0.72)";
};

const itemPriceColor = (item: PriceItem) => {
  if (item.highlight) {
    return itemPrimaryTextColor(item);
  }

  const accentNeedsLightText = isReadableColorLight(accent.value);
  return accentNeedsLightText ? accent.value : "#0f172a";
};

const itemCardStyle = (item: PriceItem) => {
  if (item.highlight) {
    return {
      background: accent.value,
      color: itemPrimaryTextColor(item),
      boxShadow: `0 25px 60px -30px ${highlightShadow.value}`
    };
  }

  return {
    background: normalCardBackground
  };
};

const badgeStyle = (highlight: boolean) =>
  highlight
    ? { background: "#ffffff", color: accent.value, borderColor: "#ffffff" }
    : {
        background: toRgba(accent.value, 0.12),
        color: accent.value,
        borderColor: toRgba(accent.value, 0.4)
      };

const buttonBackground = (item: PriceItem) => (item.highlight ? "#ffffff" : accent.value);
const buttonTextColor = (item: PriceItem) => getReadableTextColor(buttonBackground(item));

const currencyMap: Record<CurrencyCode, { locale: string; currency: CurrencyCode }> = {
  BRL: { locale: "pt-BR", currency: "BRL" },
  USD: { locale: "en-US", currency: "USD" },
  EUR: { locale: "de-DE", currency: "EUR" },
  ARS: { locale: "es-AR", currency: "ARS" }
};
const defaultCurrency = currencyMap.BRL;

const formatPrice = (price: number, currency?: PriceItem["currency"]) => {
  const config = currencyMap[(currency as CurrencyCode) || "BRL"] || defaultCurrency;

  try {
    return new Intl.NumberFormat(config.locale, {
      style: "currency",
      currency: config.currency
    }).format(price);
  } catch {
    return `R$ ${price.toLocaleString("pt-BR")}`;
  }
};

const itemLink = (item: PriceItem) => {
  const specific = sanitizeLink(item.ctaLink);
  return specific || baseCtaLink.value;
};

const trackType = (link?: string) => (link && isWhatsappLink(link) ? "whatsapp" : "cta");

const itemTitle = (item: PriceItem) => localize(item.title);
const itemDescription = (item: PriceItem) => localize(item.description);
const itemTitleLabel = (item: PriceItem) => localize(item.titleLabel).trim();
const itemPriceLabel = (item: PriceItem) => localize(item.priceLabel).trim();
const itemBadge = (item: PriceItem) => localize(item.badge).trim();
const itemCtaLabel = (item: PriceItem) => {
  const fromItem = localize(item.ctaLabel).trim();
  if (fromItem.length) return fromItem;
  if (sectionCtaLabel.value.trim().length) return sectionCtaLabel.value;
  return localize(defaultCopy.cta);
};
</script>
