<template>
  <V2Section type="links" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" align="start" />
    <div class="v2-links" :class="{ 'is-scroll': scrolls }">
      <a
        v-for="(item, idx) in items"
        :key="item.key"
        :href="item.url"
        :target="item.newTab ? '_blank' : '_self'"
        rel="noopener noreferrer"
        class="v2-card v2-link-card v2-links-card v2-in"
        :class="`v2-d${Math.min(idx + 3, 7)}`"
      >
        <span class="v2-links-media"><img v-if="item.image" :src="item.image" alt="" loading="lazy" /></span>
        <span class="v2-links-body">
          <b class="v2-links-title">{{ item.title }}</b>
          <span v-if="item.description" class="v2-links-desc">{{ item.description }}</span>
          <span v-if="item.dates" class="v2-links-meta">
            <span class="v2-links-ico" aria-hidden="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="3" /><path d="M16 2v4M8 2v4M3 10h18" /></svg></span>
            <span v-if="item.departure" class="v2-links-dt"><small>{{ copy.departure }}</small><b>{{ item.departure }}</b></span>
            <span v-if="item.return" class="v2-links-dt"><small>{{ copy.return }}</small><b>{{ item.return }}</b></span>
          </span>
          <span v-if="item.price" class="v2-links-price">
            <span class="v2-links-ico" aria-hidden="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.6 2.6A2 2 0 0 0 11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4z" /><circle cx="7.5" cy="7.5" r=".5" fill="currentColor" /></svg></span>
            <small v-if="item.pricePrefix">{{ item.pricePrefix }}</small>
            <b>{{ item.price }}</b>
            <small v-if="item.priceSuffix">{{ item.priceSuffix }}</small>
          </span>
          <span class="v2-btn v2-btn--block v2-links-btn">
            <span>{{ item.buttonLabel }}</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
          </span>
        </span>
      </a>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import type { LinksSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import { localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: LinksSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml } = useHeading(toRef(props, "section"), "links", "");
const copy = {
  departure: localize({ pt: "Ida", es: "Ida" }),
  return: localize({ pt: "Volta", es: "Vuelta" }),
  open: localize({ pt: "Ver roteiro", es: "Ver itinerario" })
};
const formatDate = (value?: string) => {
  if (!value) return "";
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) return `${match[3]}/${match[2]}/${match[1]}`;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString("pt-BR");
};
const items = computed(() =>
  (props.section.items || [])
    .filter(item => item?.url)
    .map((item, idx) => {
      const showDates = item.showDates === true && !!(item.departureDate || item.returnDate);
      const prefix = text(item.pricePrefix);
      const suffix = text(item.priceSuffix);
      const showPrice = item.showPrice === true && !!(prefix || item.priceValue || suffix);
      return {
        key: item.id || `${item.url}-${idx}`,
        url: item.url,
        newTab: item.openInNewTab !== false,
        image: resolveMediaUrl(item.image) || "",
        title: text(item.title),
        description: text(item.description),
        dates: showDates,
        departure: showDates ? formatDate(item.departureDate) : "",
        return: showDates ? formatDate(item.returnDate) : "",
        price: showPrice ? item.priceValue || "" : "",
        pricePrefix: showPrice ? prefix : "",
        priceSuffix: showPrice ? suffix : "",
        buttonLabel: text(item.buttonLabel) || copy.open
      };
    })
);
// Com 4 ou mais roteiros, a lista rola de lado; até 3, vira grade.
const scrolls = computed(() => items.value.length > 3);
</script>

<style scoped>
.v2-links {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr));
  gap: 16px;
}
.v2-links.is-scroll {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  padding-bottom: 8px;
}
.is-scroll .v2-links-card {
  flex: 0 0 min(84%, 340px);
  scroll-snap-align: start;
}
.v2-links-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 24px;
  color: inherit;
  text-decoration: none;
}
.v2-links-media {
  display: block;
  overflow: hidden;
  aspect-ratio: 16 / 11;
  background: var(--v2-soft);
}
.v2-links-media img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.v2-links-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px 22px 22px;
}
.v2-links-title {
  font-size: 20px;
}
.v2-links-desc {
  color: var(--v2-muted);
  line-height: 1.5;
}
.v2-links-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: auto;
  padding: 10px 12px;
  border-radius: 14px;
  background: var(--v2-soft);
}
.v2-links-dt {
  display: flex;
  flex-direction: column;
}
.v2-links-dt small {
  font-size: 12px;
  color: var(--v2-muted);
}
.v2-links-ico {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
}
.v2-links-price {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.v2-links-price small {
  font-size: 14px;
  color: var(--v2-muted);
}
.v2-links-price b {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: 22px;
}
.v2-links-btn {
  margin-top: auto;
  min-height: 48px;
}
.v2-links-meta + .v2-links-btn,
.v2-links-price + .v2-links-btn {
  margin-top: 4px;
}
</style>
