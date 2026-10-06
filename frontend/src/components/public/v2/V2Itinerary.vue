<template>
  <V2Section type="itinerary" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" />
    <!-- Jornada: cada dia é um cartão inteiro que abre e fecha, com o calendário à esquerda,
         a linha passando por trás dos cartões e o texto antes da foto. -->
    <div v-if="isJourney" class="v2-jr">
      <div v-if="days.length > 1" class="v2-it-tools">
        <button type="button" class="v2-it-all" @click="toggleAll">{{ allOpen ? copy.closeAll : copy.openAll }}</button>
      </div>
      <ol class="v2-jr-list">
        <li v-if="days.length > 1" class="v2-jr-line" aria-hidden="true"></li>
        <li v-for="(day, idx) in days" :key="idx" class="v2-jr-day v2-in" :class="[`v2-d${Math.min(idx + 3, 7)}`, { 'is-open': open[idx] }]">
          <article class="v2-jr-card">
            <button type="button" class="v2-jr-head" :aria-expanded="!!open[idx]" @click="toggle(idx)">
              <span class="v2-jr-cal" :style="{ animationDelay: `${0.3 + idx * 0.08}s` }">
                <span class="v2-jr-cal-band">{{ copy.day }} {{ day.number }}</span>
                <b>{{ day.date ? day.date.day : day.number }}</b>
                <span v-if="day.date" class="v2-jr-cal-month">{{ day.date.month }}</span>
              </span>
              <span class="v2-jr-titles">
                <span class="v2-jr-label">{{ day.date ? day.date.weekday : day.label }}</span>
                <span class="v2-jr-title">{{ day.title }}</span>
              </span>
              <img v-if="day.image" :src="day.image" alt="" class="v2-jr-thumb" loading="lazy" />
              <span class="v2-jr-chev" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
              </span>
            </button>
            <div class="v2-jr-body" :aria-hidden="!open[idx]">
              <div>
                <div class="v2-jr-inner">
                  <div v-if="day.descriptionHtml" class="v2-rich v2-jr-desc" v-html="day.descriptionHtml"></div>
                  <img v-if="day.image" :src="day.image" :alt="day.title" class="v2-jr-photo" loading="lazy" />
                </div>
              </div>
            </div>
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
  closeAll: localize({ pt: "Fechar todos os dias", es: "Cerrar todos los días" })
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
      date: date
        ? { day: String(date.getDate()), month: formatMonthShort(date), weekday: formatWeekday(date), short: formatDayMonth(date) }
        : null
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
.v2-jr-list {
  --jr-pad: clamp(14px, 2cqi, 18px);
  --jr-cal: clamp(54px, 6.5cqi, 64px);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}
/* A linha passa por trás dos cartões, alinhada ao centro dos calendários; aparece nos espaços entre eles. */
.v2-jr-line {
  position: absolute;
  top: 40px;
  bottom: 40px;
  left: calc(var(--jr-pad) + var(--jr-cal) / 2 - 1px);
  width: 2px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--v2-accent), color-mix(in srgb, var(--v2-accent) 25%, transparent));
  transform-origin: top;
}
.v2-armed.v2-on .v2-jr-line {
  animation: v2-jr-line 1.4s cubic-bezier(0.22, 0.8, 0.24, 1) 0.2s both;
}
.v2-armed .v2-jr-line {
  transform: scaleY(0);
}
.v2-jr-day {
  position: relative;
  z-index: 1;
}
.v2-jr-card {
  overflow: hidden;
  border-radius: 22px;
  /* Fundo opaco: a linha só aparece nos espaços entre os cartões. */
  background: color-mix(in srgb, var(--v2-ink) 4%, var(--v2-bg));
  box-shadow: 0 1px 2px rgba(6, 12, 9, 0.04);
  transition: box-shadow 0.35s ease;
}
.v2-jr-day.is-open .v2-jr-card {
  box-shadow: 0 20px 44px -26px rgba(6, 12, 9, 0.38), 0 4px 14px -8px rgba(6, 12, 9, 0.12);
}
@media (hover: hover) {
  .v2-jr-card:hover {
    box-shadow: 0 20px 44px -26px rgba(6, 12, 9, 0.38), 0 4px 14px -8px rgba(6, 12, 9, 0.14);
  }
}
.v2-jr-head {
  display: flex;
  align-items: center;
  gap: clamp(12px, 2cqi, 18px);
  width: 100%;
  padding: clamp(12px, 1.6cqi, 14px) var(--jr-pad);
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
/* Calendário sem contorno: fechado, só a faixa de cima na cor de destaque; aberto, o calendário inteiro. */
.v2-jr-cal {
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  align-items: center;
  width: var(--jr-cal);
  overflow: hidden;
  border-radius: 14px;
  background: var(--v2-bg);
  color: var(--v2-ink);
  transition: background-color 0.35s ease, color 0.35s ease;
}
.v2-armed.v2-on .v2-jr-cal {
  animation: v2-jr-pop 0.6s cubic-bezier(0.22, 0.8, 0.24, 1) both;
}
.v2-jr-cal-band {
  align-self: stretch;
  padding: 4px 0 3px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-align: center;
  text-transform: uppercase;
  transition: background-color 0.35s ease;
}
.v2-jr-cal b {
  padding: 5px 0 7px;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: clamp(22px, 2.4cqi, 26px);
  line-height: 1;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}
.v2-jr-cal-month {
  margin-top: -5px;
  padding: 0 0 7px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  opacity: 0.75;
}
.is-open .v2-jr-cal {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.is-open .v2-jr-cal-band {
  background: rgba(0, 0, 0, 0.16);
}
.v2-jr-titles {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}
.v2-jr-label {
  color: var(--v2-accent-text);
  font-size: 13px;
  font-weight: 700;
}
.v2-jr-label::first-letter {
  text-transform: uppercase;
}
.v2-jr-title {
  font-size: clamp(17px, 1.9cqi, 20px);
  font-weight: 700;
  line-height: 1.3;
}
.v2-jr-thumb {
  flex: 0 0 auto;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  object-fit: cover;
  transition: opacity 0.25s ease, width 0.35s cubic-bezier(0.22, 0.8, 0.24, 1), margin 0.35s ease;
}
.is-open .v2-jr-thumb {
  width: 0;
  margin-right: -12px;
  opacity: 0;
}
.v2-jr-chev {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
  transition: transform 0.35s cubic-bezier(0.22, 0.8, 0.24, 1), background-color 0.35s ease, color 0.35s ease;
}
.is-open .v2-jr-chev {
  transform: rotate(180deg);
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
/* Abrir e fechar sem salto: a altura vai de 0 ao conteúdo, com o texto deslizando de leve. */
.v2-jr-body {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.45s cubic-bezier(0.22, 0.8, 0.24, 1);
}
.is-open .v2-jr-body {
  grid-template-rows: 1fr;
}
.v2-jr-body > div {
  min-height: 0;
  overflow: hidden;
}
.v2-jr-inner {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0 var(--jr-pad) clamp(16px, 2cqi, 20px);
  opacity: 0;
  transform: translateY(-8px);
  transition: opacity 0.35s ease, transform 0.45s cubic-bezier(0.22, 0.8, 0.24, 1);
}
.is-open .v2-jr-inner {
  opacity: 1;
  transform: none;
}
.v2-jr-desc {
  padding: 0 4px;
  color: var(--v2-muted);
}
.v2-jr-photo {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 16px;
}
@keyframes v2-jr-line {
  from { transform: scaleY(0); }
  to { transform: scaleY(1); }
}
@keyframes v2-jr-pop {
  0% { opacity: 0; transform: scale(0.6); }
  70% { transform: scale(1.06); }
  100% { opacity: 1; transform: none; }
}
@container (max-width: 480px) {
  .v2-jr-thumb {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .v2-jr-line,
  .v2-jr-cal {
    animation: none !important;
    transform: none !important;
  }
  .v2-jr-body,
  .v2-jr-inner,
  .v2-jr-thumb,
  .v2-jr-cal,
  .v2-jr-chev {
    transition: none;
  }
}
</style>
