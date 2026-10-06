<template>
  <V2Section type="itinerary" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" />
    <!-- Jornada: linha do tempo destacada com os dias sempre abertos, em cartões completos,
         e um mapa opcional que acompanha o lugar de cada dia. -->
    <div v-if="isJourney" class="v2-jr" :class="{ 'has-map': !!mapSrc }">
      <div v-if="mapSrc" class="v2-jr-map v2-in v2-d3">
        <iframe :key="mapSrc" :src="mapSrc" :title="copy.mapTitle" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        <span v-if="mapPlace" class="v2-jr-map-chip">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" /><circle cx="12" cy="10" r="3" /></svg>
          {{ mapPlace }}
        </span>
      </div>
      <ol class="v2-jr-list">
        <li v-for="(day, idx) in days" :key="idx" class="v2-jr-day v2-in" :class="[`v2-d${Math.min(idx + 3, 7)}`, { 'is-active': mapSrc && activeDay === idx }]">
          <span class="v2-jr-node" aria-hidden="true">{{ idx + 1 }}</span>
          <article class="v2-jr-card">
            <div class="v2-jr-text">
              <span class="v2-jr-label">{{ day.date ? `${day.label} · ${day.date.weekday}, ${day.date.short}` : day.label }}</span>
              <h3 class="v2-jr-title">{{ day.title }}</h3>
              <div v-if="day.descriptionHtml" class="v2-rich v2-jr-desc" v-html="day.descriptionHtml"></div>
              <button v-if="mapSrc && day.location" type="button" class="v2-jr-place" :aria-pressed="activeDay === idx" @click="activeDay = idx">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" /><circle cx="12" cy="10" r="3" /></svg>
                {{ day.location }}
              </button>
            </div>
            <img v-if="day.image" :src="day.image" :alt="day.title" class="v2-jr-photo" loading="lazy" />
          </article>
        </li>
      </ol>
    </div>
    <div v-else-if="!isCards" class="v2-it">
      <div v-if="days.length > 1" class="v2-it-tools">
        <button type="button" class="v2-it-all" @click="toggleAll">{{ allOpen ? copy.closeAll : copy.openAll }}</button>
      </div>
      <ol class="v2-it-list">
        <li v-for="(day, idx) in days" :key="idx" class="v2-it-day v2-in" :class="`v2-d${Math.min(idx + 3, 7)}`">
          <div class="v2-it-rail">
            <span class="v2-it-date" :class="{ 'is-open': open[idx], 'has-date': !!day.date }">
              <span class="v2-it-date-band">{{ copy.day }} {{ day.date ? day.number : "" }}</span>
              <b>{{ day.date ? day.date.day : day.number }}</b>
              <span v-if="day.date" class="v2-it-date-month">{{ day.date.month }}</span>
            </span>
            <span v-if="idx < days.length - 1" class="v2-it-line" aria-hidden="true"></span>
          </div>
          <article class="v2-it-card" :class="{ 'is-open': open[idx] }">
            <button type="button" class="v2-it-head" :aria-expanded="!!open[idx]" @click="toggle(idx)">
              <span class="v2-it-titles">
                <span class="v2-it-label">{{ day.date ? `${day.label} · ${day.date.weekday}` : day.label }}</span>
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
          <span class="v2-it-chip">{{ day.date ? `${day.label} · ${day.date.short}` : day.label }}</span>
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
import { addDays, formatDayMonth, formatMonthShort, formatWeekday, parseTripDate } from "../../../utils/tripDates";

const props = defineProps<{ section: ItinerarySection; previewDevice?: "desktop" | "mobile"; tripStartDate?: string }>();
const { label, title, subtitleHtml } = useHeading(toRef(props, "section"), "itinerary", { pt: "Roteiro dia a dia", es: "Itinerario día a día" });
const copy = {
  day: localize({ pt: "DIA", es: "DÍA" }),
  dayPrefix: localize({ pt: "Dia", es: "Día" }),
  openAll: localize({ pt: "Abrir todos os dias", es: "Abrir todos los días" }),
  closeAll: localize({ pt: "Fechar todos os dias", es: "Cerrar todos los días" }),
  mapTitle: localize({ pt: "Mapa do roteiro", es: "Mapa del itinerario" })
};
// "minimal" e "steps" entram na linha do tempo e nos cartões, respectivamente.
const isCards = computed(() => props.section.layout === "cards" || props.section.layout === "steps");
const isJourney = computed(() => props.section.layout === "journey");
// Data de cada dia: início do roteiro, ou a saída da Capa quando ele fica vazio.
const start = computed(() => parseTripDate(props.section.startDate) || parseTripDate(props.tripStartDate));
// Um dia com data própria muda a sequência: os seguintes continuam a partir dela.
const dayDates = computed(() => {
  let previous: Date | null = null;
  return (props.section.days || []).map((day, idx) => {
    const own = parseTripDate(day.date);
    const date = own || (previous ? addDays(previous, 1) : start.value ? addDays(start.value, idx) : null);
    previous = date;
    return date;
  });
});
const days = computed(() =>
  (props.section.days || []).map((day, idx) => {
    const date = dayDates.value[idx];
    const labelText = text(day.day) || `${copy.dayPrefix} ${idx + 1}`;
    const match = labelText.match(/\d+/);
    return {
      label: labelText,
      number: match ? match[0] : String(idx + 1),
      title: text(day.title) || `${copy.dayPrefix} ${idx + 1}`,
      descriptionHtml: text(day.description) ? html(day.description) : "",
      image: resolveMediaUrl(day.image) || "",
      location: (day.location || "").trim(),
      date: date
        ? { day: String(date.getDate()), month: formatMonthShort(date), weekday: formatWeekday(date), short: formatDayMonth(date) }
        : null
    };
  })
);
// Mapa: o lugar do dia escolhido; sem ele, o lugar geral do roteiro.
const activeDay = ref<number | null>(null);
const mapPlace = computed(() => {
  if (!props.section.mapEnabled) return "";
  const chosen = activeDay.value !== null ? days.value[activeDay.value]?.location : "";
  return chosen || (props.section.mapQuery || "").trim() || days.value.find(day => day.location)?.location || "";
});
const mapSrc = computed(() =>
  mapPlace.value ? `https://maps.google.com/maps?q=${encodeURIComponent(mapPlace.value)}&z=${activeDay.value !== null ? 12 : 9}&output=embed` : ""
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
  box-shadow: 0 8px 18px -14px rgba(6, 12, 9, 0.35);
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
.v2-it-date.has-date b {
  padding: 5px 0 0;
}
.v2-it-date-month {
  padding: 1px 0 7px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.75;
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
  border-radius: 22px;
  background: var(--v2-card);
  transition: box-shadow 0.28s ease;
}
/* Mesmo cartão das outras seções: sem contorno; o dia aberto ganha só profundidade. */
.v2-it-card.is-open {
  box-shadow: 0 18px 40px -28px rgba(6, 12, 9, 0.4);
}
@media (hover: hover) {
  .v2-it-card:hover {
    box-shadow: 0 20px 44px -26px rgba(6, 12, 9, 0.38), 0 4px 14px -8px rgba(6, 12, 9, 0.14);
  }
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
/* Jornada */
.v2-jr {
  max-width: 860px;
  margin: 0 auto;
}
.v2-jr.has-map {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 0.8fr);
  align-items: start;
  gap: clamp(24px, 4cqi, 48px);
  max-width: 1180px;
}
.v2-jr-map {
  position: sticky;
  top: 96px;
  grid-column: 2;
  grid-row: 1;
  height: min(72vh, 560px);
  overflow: hidden;
  border-radius: 24px;
  background: var(--v2-card);
  box-shadow: 0 24px 50px -32px rgba(6, 12, 9, 0.45);
}
.v2-jr-map iframe {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}
.v2-jr-map-chip {
  position: absolute;
  top: 14px;
  left: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: calc(100% - 28px);
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.95);
  color: #0f1713;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 6px 18px -8px rgba(6, 12, 9, 0.4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none;
}
.v2-jr-list {
  position: relative;
  grid-column: 1;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}
/* A linha destacada passa pelo centro dos marcadores, do primeiro ao último dia. */
.v2-jr-list::before {
  content: "";
  position: absolute;
  top: 28px;
  bottom: 28px;
  left: 19px;
  width: 2px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--v2-accent), color-mix(in srgb, var(--v2-accent) 35%, transparent));
}
.v2-jr-day {
  position: relative;
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  gap: clamp(12px, 2cqi, 20px);
}
.v2-jr-node {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  margin-top: 18px;
  border-radius: 999px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  font-size: 15px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  box-shadow: 0 0 0 6px var(--v2-bg);
}
.v2-jr-card {
  display: flex;
  align-items: flex-start;
  gap: clamp(16px, 2.4cqi, 24px);
  padding: clamp(18px, 2.4cqi, 24px);
  border-radius: 22px;
  background: var(--v2-card);
  box-shadow: 0 1px 2px rgba(6, 12, 9, 0.04), 0 14px 32px -26px rgba(6, 12, 9, 0.35);
  transition: box-shadow 0.28s ease;
}
@media (hover: hover) {
  .v2-jr-card:hover {
    box-shadow: 0 20px 44px -26px rgba(6, 12, 9, 0.38), 0 4px 14px -8px rgba(6, 12, 9, 0.14);
  }
}
.v2-jr-day.is-active .v2-jr-card {
  box-shadow: inset 0 0 0 1.5px color-mix(in srgb, var(--v2-accent) 60%, transparent), 0 14px 32px -26px rgba(6, 12, 9, 0.35);
}
.v2-jr-text {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}
.v2-jr-label {
  color: var(--v2-accent-text);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.v2-jr-title {
  margin: 0;
  font-size: clamp(18px, 2cqi, 21px);
  font-weight: 700;
  line-height: 1.3;
}
.v2-jr-desc {
  margin-top: 2px;
  color: var(--v2-muted);
}
.v2-jr-place {
  display: inline-flex;
  align-self: flex-start;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  margin-top: 6px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}
.v2-jr-place[aria-pressed="true"] {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.v2-jr-photo {
  flex: 0 0 auto;
  width: clamp(140px, 30%, 220px);
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: 16px;
}
/* Com mapa em telas médias, ou em qualquer celular: uma coluna, mapa no topo. */
@container (max-width: 900px) {
  .v2-jr.has-map {
    grid-template-columns: minmax(0, 1fr);
  }
  .v2-jr-map {
    position: relative;
    top: 0;
    grid-column: 1;
    height: auto;
    aspect-ratio: 16 / 10;
  }
  .v2-jr.has-map .v2-jr-list {
    grid-row: 2;
  }
}
@container (max-width: 640px) {
  .v2-jr-list::before {
    left: 15px;
  }
  .v2-jr-day {
    grid-template-columns: 32px minmax(0, 1fr);
    gap: 10px;
  }
  .v2-jr-node {
    width: 32px;
    height: 32px;
    margin-top: 16px;
    font-size: 13px;
    box-shadow: 0 0 0 4px var(--v2-bg);
  }
  .v2-jr-card {
    flex-direction: column-reverse;
    padding: 16px;
    border-radius: 18px;
  }
  .v2-jr-photo {
    width: 100%;
    aspect-ratio: 16 / 9;
  }
  .v2-jr-map {
    aspect-ratio: 4 / 3;
    border-radius: 18px;
  }
}
</style>
