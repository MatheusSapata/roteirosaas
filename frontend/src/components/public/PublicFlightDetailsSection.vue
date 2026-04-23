<template>
  <section
    class="relative overflow-hidden py-14"
    :id="section.anchorId || undefined"
    :style="{ background: section.backgroundColor || 'linear-gradient(180deg, #eff6ff 0%, #f8fafc 52%, #ffffff 100%)' }"
  >
    <div class="pointer-events-none absolute inset-0">
      <div class="absolute -left-16 top-0 h-44 w-44 rounded-full bg-sky-200/40 blur-2xl"></div>
      <div class="absolute -right-10 bottom-0 h-56 w-56 rounded-full bg-cyan-200/35 blur-2xl"></div>
    </div>

    <div class="relative mx-auto w-full max-w-6xl px-4 md:px-6">
      <div class="mb-8 text-center">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-sky-600">Informacoes aereas</p>
        <h2 class="mt-2 text-3xl font-bold text-slate-900 md:text-4xl">{{ sectionTitle }}</h2>
        <p v-if="sectionSubtitle" class="mt-2 text-sm text-slate-600 md:text-base">{{ sectionSubtitle }}</p>
      </div>

      <div v-if="!visibleJourneys.length" class="rounded-3xl border border-slate-200 bg-white/90 p-6 text-center text-sm text-slate-600">
        Nenhum trecho de voo cadastrado para exibicao.
      </div>

      <div v-else class="space-y-4">
        <article
          v-for="(journey, journeyIndex) in visibleJourneys"
          :key="journey.id || `${journey.direction}-${journeyIndex}`"
          class="overflow-hidden rounded-3xl border border-slate-200 bg-white/95 shadow-[0_22px_45px_-30px_rgba(15,23,42,0.35)] backdrop-blur"
        >
          <header class="border-b border-slate-100 px-4 py-4 md:px-6">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="space-y-1">
                <p class="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
                  {{ journey.direction === "outbound" ? "IDA" : "VOLTA" }}
                </p>
                <h3 class="text-lg font-bold text-slate-900 md:text-xl">{{ routeSummary(journey) }}</h3>
                <p class="text-sm text-slate-600">{{ topSummary(journey) }}</p>
                <p v-if="journeyDate(journey)" class="text-xs font-medium text-slate-500">{{ journeyDate(journey) }}</p>
              </div>
              <button
                type="button"
                class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-700 transition hover:bg-slate-100"
                @click="toggleJourney(journey, journeyIndex)"
              >
                {{ isJourneyExpanded(journey, journeyIndex) ? "Ver menos" : "Ver detalhes" }}
                <svg
                  class="h-4 w-4 transition"
                  :class="{ 'rotate-180': isJourneyExpanded(journey, journeyIndex) }"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="m6 9 6 6 6-6" />
                </svg>
              </button>
            </div>
            <div class="mt-3 grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-2xl bg-slate-50 px-3 py-2 md:px-4">
              <div class="min-w-0 text-center">
                <p class="text-2xl font-bold leading-none text-slate-900">{{ firstTime(journey) }}</p>
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ firstIata(journey) }}</p>
              </div>
              <div class="flex min-w-0 items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <div class="h-[2px] min-w-5 flex-1 bg-slate-200"></div>
                <span class="whitespace-nowrap">{{ stopSummary(journey) }}</span>
                <div class="h-[2px] min-w-5 flex-1 bg-slate-200"></div>
              </div>
              <div class="min-w-0 text-center">
                <p class="text-2xl font-bold leading-none text-slate-900">{{ lastTime(journey) }}</p>
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ lastIata(journey) }}</p>
              </div>
            </div>
          </header>

          <transition name="flight-expand">
            <div v-if="isJourneyExpanded(journey, journeyIndex)" class="space-y-4 px-4 py-4 md:px-6 md:py-5">
              <p v-if="!segmentsFor(journey).length" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                Esta jornada ainda nao possui trechos configurados.
              </p>

              <template v-for="(segment, index) in segmentsFor(journey)" :key="segment.id || index">
                <div class="grid gap-4 rounded-2xl border border-slate-100 bg-slate-50/65 p-3 md:grid-cols-[1.4fr_0.8fr] md:p-4">
                  <div class="space-y-3">
                    <div>
                      <p class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Trecho {{ index + 1 }}</p>
                      <p v-if="segmentDate(segment)" class="text-xs text-slate-500">{{ segmentDate(segment) }}</p>
                    </div>
                    <div class="grid gap-3 sm:grid-cols-2">
                      <div>
                        <p class="text-3xl font-bold leading-none text-slate-900">{{ departureTime(segment) }}</p>
                        <p class="text-sm font-semibold uppercase tracking-wide text-sky-700">{{ segment.departure_airport_iata || "---" }}</p>
                        <p class="mt-1 text-sm text-slate-700">{{ segment.departure_city || "Cidade nao informada" }}</p>
                        <p class="text-xs text-slate-500">{{ segment.departure_airport_name || "Aeroporto nao informado" }}</p>
                        <p v-if="segment.departure_country" class="text-xs text-slate-500">{{ segment.departure_country }}</p>
                        <p v-if="terminalGateText(segment.departure_terminal, segment.departure_gate)" class="text-xs text-slate-500">
                          {{ terminalGateText(segment.departure_terminal, segment.departure_gate) }}
                        </p>
                      </div>
                      <div>
                        <p class="text-3xl font-bold leading-none text-slate-900">{{ arrivalTime(segment) }}</p>
                        <p class="text-sm font-semibold uppercase tracking-wide text-sky-700">{{ segment.arrival_airport_iata || "---" }}</p>
                        <p class="mt-1 text-sm text-slate-700">{{ segment.arrival_city || "Cidade nao informada" }}</p>
                        <p class="text-xs text-slate-500">{{ segment.arrival_airport_name || "Aeroporto nao informado" }}</p>
                        <p v-if="segment.arrival_country" class="text-xs text-slate-500">{{ segment.arrival_country }}</p>
                        <p v-if="terminalGateText(segment.arrival_terminal, segment.arrival_gate)" class="text-xs text-slate-500">
                          {{ terminalGateText(segment.arrival_terminal, segment.arrival_gate) }}
                        </p>
                      </div>
                    </div>
                    <p class="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-600">Duracao: {{ segmentDuration(segment) }}</p>
                  </div>
                  <aside class="space-y-2 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-700">
                    <div class="flex items-center gap-2">
                      <img
                        v-if="segment.airline_logo_url"
                        :src="segment.airline_logo_url"
                        alt=""
                        class="h-8 w-8 rounded-md object-contain"
                      />
                      <p class="font-semibold">{{ segment.airline_name || "Companhia nao informada" }}</p>
                    </div>
                    <p class="text-xs text-slate-500">Voo: {{ segment.flight_number || segment.flight_iata || "--" }}</p>
                    <p class="text-xs text-slate-500">Classe: {{ segment.cabin_class || "Nao informada" }}</p>
                    <p v-if="segment.status" class="text-xs text-slate-500">Status: {{ segment.status }}</p>
                    <div class="pt-1">
                      <p class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Bagagens</p>
                      <ul v-if="segmentBaggageItems(segment).length" class="mt-1 space-y-1">
                        <li v-if="segment.included_personal_item" class="flex items-center gap-1 text-xs">
                          <svg class="h-4 w-4 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                            <rect x="7" y="7" width="10" height="11" rx="2"></rect>
                            <path d="M10 7V5a2 2 0 0 1 4 0v2"></path>
                          </svg>
                          1x Item pessoal
                        </li>
                        <li v-if="segment.included_carry_on" class="flex items-center gap-1 text-xs">
                          <svg class="h-4 w-4 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                            <rect x="5" y="8" width="14" height="11" rx="2"></rect>
                            <path d="M9 8V6a3 3 0 0 1 6 0v2"></path>
                            <path d="M9 14h6"></path>
                          </svg>
                          1x Bagagem de mao
                        </li>
                        <li v-if="segment.included_checked_bag" class="flex items-center gap-1 text-xs">
                          <svg class="h-4 w-4 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                            <rect x="6" y="6" width="12" height="14" rx="2"></rect>
                            <path d="M9 6V5a3 3 0 0 1 6 0v1"></path>
                            <path d="M10 11h4"></path>
                          </svg>
                          1x Bagagem despachada
                        </li>
                      </ul>
                      <p v-else class="mt-1 text-xs text-slate-500">Franquia nao informada</p>
                    </div>
                    <p v-if="segment.notes" class="rounded-lg bg-slate-50 px-2 py-1 text-xs text-slate-600">Obs: {{ segment.notes }}</p>
                  </aside>
                </div>
                <div
                  v-if="index < segmentsFor(journey).length - 1 && layoverText(segmentsFor(journey), index)"
                  class="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600"
                >
                  <svg class="h-4 w-4 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <circle cx="12" cy="12" r="9"></circle>
                    <path d="M12 7v5l3 2"></path>
                  </svg>
                  <span>{{ layoverText(segmentsFor(journey), index) }}</span>
                </div>
              </template>
            </div>
          </transition>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { FlightDetailsSection, FlightSectionJourney, FlightSectionSegment } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: FlightDetailsSection; previewDevice?: "desktop" | "mobile" }>();
const localize = createLocalizer(getCurrentLanguage());

const sectionTitle = computed(() => localize(props.section.title || "Informacoes do voo"));
const sectionSubtitle = computed(() => localize(props.section.subtitle || ""));

const visibleJourneys = computed(() => {
  const list = (props.section.journeys || []).filter(journey => journey.is_enabled !== false);
  return list
    .filter(journey => {
      if (journey.direction === "outbound") return props.section.showOutbound !== false;
      if (journey.direction === "inbound") return props.section.showInbound !== false;
      return true;
    })
    .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
});

const expandedIds = ref<Record<string, boolean>>({});

const journeyKey = (journey: FlightSectionJourney, index: number) => String(journey.id || `${journey.direction}-${index}`);

const toggleJourney = (journey: FlightSectionJourney, index: number) => {
  const key = journeyKey(journey, index);
  expandedIds.value[key] = !expandedIds.value[key];
};

const isJourneyExpanded = (journey: FlightSectionJourney, index: number) => {
  const key = journeyKey(journey, index);
  if (Object.prototype.hasOwnProperty.call(expandedIds.value, key)) return !!expandedIds.value[key];
  return index === 0;
};

const parseDate = (value?: string | null) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date;
};

const formatTime = (value?: string | null) => {
  const date = parseDate(value);
  if (!date) return "--:--";
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
};

const formatDate = (value?: string | null) => {
  const date = parseDate(value);
  if (!date) return "";
  return date.toLocaleDateString("pt-BR", {
    weekday: "short",
    day: "numeric",
    month: "short"
  });
};

const formatDuration = (minutes?: number | null) => {
  if (!minutes || minutes <= 0) return "Nao informado";
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `${String(hours).padStart(2, "0")}h${String(rest).padStart(2, "0")}`;
};

const segmentsFor = (journey: FlightSectionJourney): FlightSectionSegment[] =>
  [...(journey.segments || [])].sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));

const firstSegment = (journey: FlightSectionJourney) => segmentsFor(journey)[0] || null;

const lastSegment = (journey: FlightSectionJourney) => {
  const list = segmentsFor(journey);
  return list[list.length - 1] || null;
};

const pointLabel = (city?: string, iata?: string, fallback = "---") => {
  const cityValue = (city || "").trim();
  const iataValue = (iata || "").trim();
  if (cityValue && iataValue) return `${cityValue} (${iataValue})`;
  if (cityValue) return cityValue;
  if (iataValue) return iataValue;
  return fallback;
};

const routeSummary = (journey: FlightSectionJourney) => {
  const first = firstSegment(journey);
  const last = lastSegment(journey);
  const from = pointLabel(first?.departure_city, first?.departure_airport_iata, "Origem");
  const to = pointLabel(last?.arrival_city, last?.arrival_airport_iata, "Destino");
  return `${from} -> ${to}`;
};

const totalDuration = (journey: FlightSectionJourney) => {
  const first = firstSegment(journey);
  const last = lastSegment(journey);
  const firstDeparture = parseDate(first?.departure_datetime || null);
  const lastArrival = parseDate(last?.arrival_datetime || null);
  if (firstDeparture && lastArrival) {
    const diffMinutes = Math.round((lastArrival.getTime() - firstDeparture.getTime()) / 60000);
    if (diffMinutes > 0) return diffMinutes;
  }
  return segmentsFor(journey).reduce((total, segment) => total + Number(segment.duration_minutes || 0), 0);
};

const stopSummary = (journey: FlightSectionJourney) => {
  const stops = Math.max(0, segmentsFor(journey).length - 1);
  return stops ? `${stops} parada${stops > 1 ? "s" : ""}` : "Direto";
};

const topSummary = (journey: FlightSectionJourney) => {
  const airline = firstSegment(journey)?.airline_name || "Companhia nao informada";
  const duration = formatDuration(totalDuration(journey));
  return `${airline} · ${stopSummary(journey)} · Duracao total: ${duration}`;
};

const journeyDate = (journey: FlightSectionJourney) => formatDate(firstSegment(journey)?.departure_datetime);
const firstTime = (journey: FlightSectionJourney) => formatTime(firstSegment(journey)?.departure_datetime);
const lastTime = (journey: FlightSectionJourney) => formatTime(lastSegment(journey)?.arrival_datetime);
const firstIata = (journey: FlightSectionJourney) => firstSegment(journey)?.departure_airport_iata || "---";
const lastIata = (journey: FlightSectionJourney) => lastSegment(journey)?.arrival_airport_iata || "---";
const departureTime = (segment: FlightSectionSegment) => formatTime(segment.departure_datetime);
const arrivalTime = (segment: FlightSectionSegment) => formatTime(segment.arrival_datetime);
const segmentDate = (segment: FlightSectionSegment) => formatDate(segment.departure_datetime);
const segmentDuration = (segment: FlightSectionSegment) => formatDuration(segment.duration_minutes);

const segmentBaggageItems = (segment: FlightSectionSegment) =>
  [segment.included_personal_item, segment.included_carry_on, segment.included_checked_bag].filter(Boolean);

const terminalGateText = (terminal?: string | null, gate?: string | null) => {
  const terminalValue = (terminal || "").trim();
  const gateValue = (gate || "").trim();
  if (!terminalValue && !gateValue) return "";
  if (terminalValue && gateValue) return `Terminal ${terminalValue} · Portao ${gateValue}`;
  if (terminalValue) return `Terminal ${terminalValue}`;
  return `Portao ${gateValue}`;
};

const layoverText = (segments: FlightSectionSegment[], index: number) => {
  const current = segments[index];
  const next = segments[index + 1];
  if (!current || !next) return "";
  const currentArrival = parseDate(current.arrival_datetime || null);
  const nextDeparture = parseDate(next.departure_datetime || null);
  if (!currentArrival || !nextDeparture) return "";
  const diff = Math.round((nextDeparture.getTime() - currentArrival.getTime()) / 60000);
  if (diff <= 0) return "";
  const hours = Math.floor(diff / 60);
  const minutes = diff % 60;
  const tokens: string[] = [];
  if (hours) tokens.push(`${hours}h`);
  if (minutes) tokens.push(`${minutes}min`);
  return `Espera de ${tokens.join(" ")} entre os voos`;
};
</script>

<style scoped>
.flight-expand-enter-active,
.flight-expand-leave-active {
  transition: max-height 0.4s ease, opacity 0.25s ease;
  overflow: hidden;
}

.flight-expand-enter-from,
.flight-expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.flight-expand-enter-to,
.flight-expand-leave-from {
  max-height: 3000px;
  opacity: 1;
}
</style>
