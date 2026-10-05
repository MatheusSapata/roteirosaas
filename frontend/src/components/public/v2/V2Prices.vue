<template>
  <V2Section type="prices" :background="section.backgroundColor" fallback-background="#F2F4F1" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" />
    <ul class="v2-prices">
      <li v-for="(item, idx) in items" :key="idx" class="v2-price v2-in" :class="[`v2-d${Math.min(idx + 3, 7)}`, { 'is-hl': item.highlight }]">
        <div class="v2-price-info">
          <div v-if="item.badge || item.titleLabel" class="v2-price-tags">
            <span v-if="item.badge" class="v2-price-badge">{{ item.badge }}</span>
            <span v-if="item.titleLabel" class="v2-price-kicker">{{ item.titleLabel }}</span>
          </div>
          <h3>{{ item.title }}</h3>
          <p v-if="item.description" class="v2-price-desc">{{ item.description }}</p>
        </div>
        <div class="v2-price-value">
          <b>{{ item.price }}</b>
          <span v-if="item.priceLabel">{{ item.priceLabel }}</span>
        </div>
        <a v-if="item.href" class="v2-btn v2-price-btn" v-bind="item.attrs">
          <span>{{ item.ctaLabel }}</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
        </a>
      </li>
    </ul>
    <p v-if="description" class="v2-prices-note">{{ description }}</p>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import type { CurrencyCode, PriceItem, PricesSection } from "../../../types/page";
import { isWhatsappLink, normalizeExternalLink } from "../../../utils/links";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import { localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: PricesSection; previewDevice?: "desktop" | "mobile" }>();
const heading = useHeading(toRef(props, "section"), "prices", { pt: "Planos e opções", es: "Planes y opciones" });
const label = heading.label;
const title = heading.title;
// Sem subtítulo salvo, mantém o texto padrão das seções antigas.
const subtitleHtml = computed(() =>
  props.section.subtitle === null || props.section.subtitle === undefined
    ? localize({ pt: "Escolha o formato que combina com você.", es: "Elige el formato que va contigo." })
    : heading.subtitleHtml.value
);
const description = computed(() => text(props.section.description));

const locales: Partial<Record<CurrencyCode, string>> = {
  BRL: "pt-BR", USD: "en-US", EUR: "de-DE", GBP: "en-GB", JPY: "ja-JP", CNY: "zh-CN", CAD: "en-CA", AUD: "en-AU",
  CHF: "de-CH", INR: "en-IN", MXN: "es-MX", ARS: "es-AR", CLP: "es-CL", COP: "es-CO", PEN: "es-PE", UYU: "es-UY",
  AED: "ar-AE", NZD: "en-NZ", SGD: "en-SG", HKD: "zh-HK", KRW: "ko-KR", ZAR: "en-ZA"
};
const formatPrice = (price: number, currency: CurrencyCode = "BRL") => {
  const locale = locales[currency] || "pt-BR";
  try {
    return new Intl.NumberFormat(locale, { style: "currency", currency }).format(price);
  } catch {
    return `${currency} ${price.toLocaleString(locale)}`;
  }
};

const sectionLink = computed(() => normalizeExternalLink(props.section.ctaLink));
const linkFor = (item: PriceItem) =>
  item.ctaMode === "section" ? (item.ctaSectionId ? `#${item.ctaSectionId}` : "") : normalizeExternalLink(item.ctaLink) || sectionLink.value || "";

const items = computed(() =>
  (props.section.items || []).map(item => {
    const href = linkFor(item);
    const scroll = item.ctaMode === "section" && !!item.ctaSectionId;
    const newTab = !scroll && (item.ctaOpenInNewTab ?? props.section.ctaOpenInNewTab !== false);
    return {
      title: text(item.title),
      description: text(item.description),
      titleLabel: text(item.titleLabel),
      priceLabel: text(item.priceLabel),
      badge: text(item.badge),
      highlight: !!item.highlight,
      price: formatPrice(Number(item.price) || 0, (item.currency as CurrencyCode) || "BRL"),
      ctaLabel: text(item.ctaLabel) || text(props.section.ctaLabel) || localize({ pt: "Reservar", es: "Reservar" }),
      href,
      attrs: {
        href,
        target: newTab ? "_blank" : undefined,
        rel: newTab ? "noopener" : undefined,
        "data-scroll-target": scroll ? "true" : undefined,
        "data-track-event": "cta",
        "data-track-type": !scroll && isWhatsappLink(href) ? "whatsapp" : "cta"
      }
    };
  })
);
</script>

<style scoped>
.v2-prices {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 960px;
  margin: 0 auto;
  padding: 0;
  list-style: none;
}
.v2-price {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px 28px;
  padding: clamp(18px, 2.6cqi, 26px) clamp(18px, 3cqi, 30px);
  border-radius: 22px;
  background: var(--v2-card);
}
.v2-price.is-hl {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  box-shadow: 0 24px 50px -30px color-mix(in srgb, var(--v2-accent) 70%, transparent);
}
.v2-price-info {
  flex: 1 1 260px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.v2-price-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.v2-price-badge {
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  font-size: 12px;
  font-weight: 700;
}
.is-hl .v2-price-badge {
  background: var(--v2-on-accent);
  color: var(--v2-accent);
}
.v2-price-kicker {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.75;
}
.v2-price h3 {
  margin: 0;
  font-size: clamp(18px, 2cqi, 21px);
  font-weight: 700;
}
.v2-price-desc {
  margin: 0;
  font-size: 15px;
  line-height: 1.5;
  opacity: 0.78;
}
.v2-price-value {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  text-align: right;
}
.v2-price-value b {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: clamp(24px, 3cqi, 32px);
  letter-spacing: -0.02em;
  white-space: nowrap;
}
.v2-price-value span {
  font-size: 13px;
  opacity: 0.75;
}
.is-hl .v2-price-btn {
  background: var(--v2-on-accent);
  color: var(--v2-accent);
}
.v2-prices-note {
  max-width: 960px;
  margin: 20px auto 0;
  font-size: 14px;
  text-align: center;
  color: var(--v2-muted);
}
@container (max-width: 560px) {
  .v2-price-value {
    align-items: flex-start;
    text-align: left;
  }
  .v2-price-btn {
    width: 100%;
  }
}
</style>
