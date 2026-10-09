<template>
  <V2Section type="prices" :background="section.backgroundColor" fallback-background="#F2F4F1" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" :align="heading.align.value" frame="960px" />
    <ul class="v2-prices">
      <li v-for="(item, idx) in items" :key="idx" class="v2-price v2-in" :class="[`v2-d${Math.min(idx + 3, 7)}`, { 'is-hl': item.highlight, 'has-badge': item.badge }]">
        <!-- Mesma ordem de leitura do legado: o que é o pacote → quanto custa → como pagar → botão. -->
        <span v-if="item.badge" class="v2-price-badge">{{ item.badge }}</span>
        <div class="v2-price-info">
          <span v-if="item.titleLabel" class="v2-price-kicker">{{ item.titleLabel }}</span>
          <h3>{{ item.title }}</h3>
        </div>
        <!-- Preço ao lado do botão. As colunas são da lista inteira (subgrid): todos os botões
             ficam com a largura do maior, e os preços alinhados entre si. -->
        <div class="v2-price-side">
          <div class="v2-price-value">
            <span v-if="item.priceLabel" class="v2-price-from">{{ item.priceLabel }}</span>
            <b>{{ item.price }}</b>
            <span v-if="item.description" class="v2-price-terms">{{ item.description }}</span>
          </div>
          <a v-if="item.href" class="v2-btn v2-price-btn" :title="item.ctaLabel" v-bind="item.attrs">
            <span>{{ item.ctaLabel }}</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
          </a>
        </div>
      </li>
    </ul>
    <V2Payments v-if="section.showPayments" :ids="section.paymentMethods" :note="section.paymentNote" />
    <p v-if="description" class="v2-prices-note">{{ description }}</p>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import type { CurrencyCode, PriceItem, PricesSection } from "../../../types/page";
import { isWhatsappLink, normalizeExternalLink } from "../../../utils/links";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import V2Payments from "./V2Payments.vue";
import { localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: PricesSection; previewDevice?: "desktop" | "mobile" }>();
const heading = useHeading(toRef(props, "section"), "prices");
const label = heading.label;
const title = heading.title;
const subtitleHtml = heading.subtitleHtml;
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) max-content max-content;
  gap: 16px clamp(20px, 3.4cqi, 36px);
  max-width: 960px;
  margin: 0 auto;
  padding: 0;
  list-style: none;
}
.v2-price {
  position: relative;
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
  align-items: center;
  gap: 16px clamp(20px, 3.4cqi, 36px);
  padding: clamp(20px, 2.8cqi, 28px) clamp(20px, 3.2cqi, 32px);
  border-radius: 22px;
  background: var(--v2-card);
}
.v2-price.has-badge {
  margin-top: 10px;
}
.v2-price.is-hl {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  box-shadow: 0 24px 50px -30px color-mix(in srgb, var(--v2-accent) 70%, transparent);
}
/* Selo preso à borda de cima, como no legado: chama atenção sem disputar com o título. */
.v2-price-badge {
  position: absolute;
  top: 0;
  left: clamp(20px, 3.2cqi, 32px);
  max-width: calc(100% - 40px);
  padding: 4px 12px;
  border-radius: 999px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transform: translateY(-50%);
  box-shadow: 0 6px 16px -8px rgba(6, 12, 9, 0.45);
}
.is-hl .v2-price-badge {
  background: var(--v2-on-accent);
  color: var(--v2-accent);
}
.v2-price-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.v2-price-kicker {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.7;
}
.v2-price h3 {
  margin: 0;
  font-size: clamp(19px, 2.2cqi, 23px);
  font-weight: 700;
  line-height: 1.25;
}
.v2-price-side {
  display: contents;
}
.v2-price-value {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  text-align: right;
}
.v2-price-from {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  opacity: 0.7;
}
.v2-price-value b {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: clamp(26px, 3.4cqi, 34px);
  line-height: 1.1;
  letter-spacing: -0.02em;
  white-space: nowrap;
}
.v2-price-terms {
  font-size: 14px;
  opacity: 0.75;
  white-space: pre-line;
}
.v2-price-btn {
  width: 100%;
  max-width: 380px;
  min-height: 48px;
  padding: 10px 20px;
  white-space: nowrap;
  font-size: 15px;
  line-height: 1.2;
}
/* Mesma largura em todos os cartões; texto longo quebra em duas linhas em vez de sumir. */
.v2-price-btn span {
  min-width: 0;
  text-align: center;
  overflow-wrap: anywhere;
}
.v2-price-btn svg {
  flex: 0 0 auto;
}
.is-hl .v2-price-btn {
  background: var(--v2-on-accent);
  color: var(--v2-accent);
}
.v2-prices-note {
  white-space: pre-line;
  max-width: 960px;
  margin: 20px auto 0;
  font-size: 14px;
  text-align: center;
  color: var(--v2-muted);
}
/* Telas médias: preço e botão descem para uma linha própria. */
/* Telas menores: cada cartão volta a ter o próprio layout; preço e botão dividem uma linha. */
@container (max-width: 760px) {
  .v2-price-btn {
    white-space: normal;
  }
  .v2-prices {
    display: flex;
    flex-direction: column;
  }
  .v2-price {
    grid-template-columns: minmax(0, 1fr);
  }
  .v2-price-side {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 14px 20px;
  }
  .v2-price-value {
    align-items: flex-start;
    text-align: left;
  }
  .v2-price-btn {
    width: auto;
    max-width: 100%;
  }
}
/* Celular: tudo empilhado e botão na largura do cartão. */
@container (max-width: 480px) {
  .v2-price {
    gap: 14px;
  }
  .v2-price-side {
    flex-direction: column;
    align-items: stretch;
  }
  .v2-price-btn {
    width: 100%;
  }
}
</style>
