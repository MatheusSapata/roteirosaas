<template>
  <V2Section type="itinerary" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" />
    <div v-if="!isCards" class="v2-it">
      <div v-if="days.length > 1" class="v2-it-tools">
        <button type="button" class="v2-it-all" @click="toggleAll">{{ allOpen ? copy.closeAll : copy.openAll }}</button>
      </div>
      <ol class="v2-it-list">
        <li v-for="(day, idx) in days" :key="idx" class="v2-it-day v2-in" :class="`v2-d${Math.min(idx + 3, 7)}`">
          <div class="v2-it-rail">
            <span class="v2-it-date" :class="{ 'is-open': open[idx] }">
              <span class="v2-it-date-band">{{ copy.day }}</span>
              <b>{{ day.number }}</b>
            </span>
            <span v-if="idx < days.length - 1" class="v2-it-line" aria-hidden="true"></span>
          </div>
          <article class="v2-it-card" :class="{ 'is-open': open[idx] }">
            <button type="button" class="v2-it-head" :aria-expanded="!!open[idx]" @click="toggle(idx)">
              <span class="v2-it-titles">
                <span class="v2-it-label">{{ day.label }}</span>
                <span class="v2-it-title">{{ day.title }}</span>
              </span>
              <img v-if="day.image && !open[idx]" :src="day.image" alt="" class="v2-it-thumb" loading="lazy" />
              <span class="v2-it-chev" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
              </span>
            </button>
            <div v-show="open[idx]" class="v2-it-body">
              <div v-if="day.descriptionHtml" class="v2-rich" v-html="day.descriptionHtml"></div>
              <img v-if="day.image" :src="day.image" :alt="day.title" class="v2-it-photo" loading="lazy" />
            </div>
          </article>
        </li>
      </ol>
    </div>
    <div v-else class="v2-it-cards">
      <article v-for="(day, idx) in days" :key="idx" class="v2-card v2-it-tile v2-in" :class="`v2-d${Math.min(idx + 3, 7)}`">
        <img v-if="day.image" :src="day.image" :alt="day.title" loading="lazy" />
        <div class="v2-it-tile-body">
          <span class="v2-it-chip">{{ day.label }}</span>
          <h3>{{ day.title }}</h3>
          <div v-if="day.descriptionHtml" class="v2-rich" v-html="day.descriptionHtml"></div>
        </div>
      </article>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, ref, toRef, watch } from "vue";
import type { ItinerarySection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import { html, localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: ItinerarySection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml } = useHeading(toRef(props, "section"), "itinerary", { pt: "Roteiro dia a dia", es: "Itinerario día a día" });
const copy = {
  day: localize({ pt: "DIA", es: "DÍA" }),
  dayPrefix: localize({ pt: "Dia", es: "Día" }),
  openAll: localize({ pt: "Abrir todos os dias", es: "Abrir todos los días" }),
  closeAll: localize({ pt: "Fechar todos os dias", es: "Cerrar todos los días" })
};
// "minimal" e "steps" entram na linha do tempo e nos cartões, respectivamente.
const isCards = computed(() => props.section.layout === "cards" || props.section.layout === "steps");
const days = computed(() =>
  (props.section.days || []).map((day, idx) => {
    const labelText = text(day.day) || `${copy.dayPrefix} ${idx + 1}`;
    const match = labelText.match(/\d+/);
    return {
      label: labelText,
      number: match ? match[0] : String(idx + 1),
      title: text(day.title) || `${copy.dayPrefix} ${idx + 1}`,
      descriptionHtml: text(day.description) ? html(day.description) : "",
      image: resolveMediaUrl(day.image) || ""
    };
  })
);
const open = ref<Record<number, boolean>>({ 0: true });
const allOpen = computed(() => days.value.length > 0 && days.value.every((_, idx) => open.value[idx]));
const toggle = (idx: number) => {
  open.value = { ...open.value, [idx]: !open.value[idx] };
};
const toggleAll = () => {
  const next = !allOpen.value;
  open.value = Object.fromEntries(days.value.map((_, idx) => [idx, next]));
};
watch(
  () => days.value.length,
  () => {
    if (!Object.values(open.value).some(Boolean)) open.value = { 0: true };
  }
);
</script>

<style scoped>
.v2-it {
  max-width: 860px;
  margin: 0 auto;
}
.v2-it-tools {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.v2-it-all {
  min-height: 44px;
  padding: 0 16px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--v2-accent-text);
  font: inherit;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
}
.v2-it-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
}
.v2-it-day {
  display: flex;
  gap: clamp(12px, 2.4cqi, 20px);
}
.v2-it-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 0 0 auto;
  padding-top: 4px;
}
.v2-it-date {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: clamp(58px, 7cqi, 68px);
  overflow: hidden;
  border-radius: 16px;
  box-shadow: 0 8px 18px -14px rgba(6, 12, 9, 0.35), inset 0 0 0 1.5px var(--v2-line);
  background: var(--v2-card);
}
.v2-it-date-band {
  align-self: stretch;
  padding: 5px 0 4px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-align: center;
}
.v2-it-date b {
  padding: 6px 0 9px;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: clamp(24px, 2.6cqi, 28px);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.v2-it-date.is-open {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  box-shadow: 0 14px 28px -16px rgba(6, 12, 9, 0.5);
}
.v2-it-date.is-open .v2-it-date-band {
  background: rgba(0, 0, 0, 0.14);
  color: inherit;
}
.v2-it-line {
  flex: 1;
  width: 2px;
  min-height: 12px;
  margin-top: 6px;
  background: var(--v2-line);
}
.v2-it-card {
  flex: 1;
  min-width: 0;
  margin-bottom: 12px;
  overflow: hidden;
  border-radius: 20px;
  background: var(--v2-card);
  box-shadow: inset 0 0 0 1px var(--v2-line);
}
.v2-it-card.is-open {
  box-shadow: inset 0 0 0 1.5px var(--v2-accent), 0 18px 40px -28px rgba(6, 12, 9, 0.45);
}
.v2-it-head {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  min-height: 76px;
  padding: 12px 16px 12px 20px;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.v2-it-titles {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.v2-it-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--v2-accent-text);
}
.v2-it-title {
  font-size: clamp(17px, 1.9cqi, 20px);
  font-weight: 700;
  line-height: 1.3;
}
.v2-it-thumb {
  flex: 0 0 auto;
  width: 64px;
  height: 64px;
  border-radius: 14px;
  object-fit: cover;
}
.v2-it-chev {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
  transition: transform 0.2s ease;
}
.is-open .v2-it-chev {
  transform: rotate(180deg);
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.v2-it-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0 20px 20px;
  color: var(--v2-muted);
}
.v2-it-photo {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 16px;
}
.v2-it-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr));
  gap: 16px;
}
.v2-it-tile {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.v2-it-tile img {
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
}
.v2-it-tile-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px 22px 24px;
}
.v2-it-chip {
  align-self: flex-start;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
  font-size: 13px;
  font-weight: 700;
}
.v2-it-tile h3 {
  margin: 0;
  font-size: 19px;
  line-height: 1.25;
}
.v2-it-tile .v2-rich {
  color: var(--v2-muted);
}
</style>
