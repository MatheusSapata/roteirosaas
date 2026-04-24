<template>
  <section
    class="w-full py-10 md:py-12"
    :id="section.anchorId || undefined"
    :style="{ background: sectionBackground }"
  >
    <div class="mx-auto w-full max-w-6xl px-4 md:px-6">
      <div class="mb-6 text-center">
        <div class="flex justify-center">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accent" />
        </div>
        <h2 class="mt-1 text-2xl font-bold md:text-3xl" :style="{ color: headingTitleColor }">{{ sectionTitle }}</h2>
        <p v-if="sectionSubtitle" class="mt-2 text-sm md:text-base" :style="{ color: headingSubtitleColor }">{{ sectionSubtitle }}</p>
      </div>

      <div
        v-if="!visibleJourneys.length"
        class="rounded-2xl border border-[#e5e7eb] bg-white p-6 text-center text-sm text-slate-600"
        :style="cardShellStyle"
      >
        Nenhum trecho de voo cadastrado para exibição.
      </div>

      <div v-else class="space-y-4">
        <article
          v-for="(journey, journeyIndex) in visibleJourneys"
          :key="journey.id || `${journey.direction}-${journeyIndex}`"
          class="flight-card overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white"
          :data-dark="!sectionBackgroundIsLight"
          :style="cardShellStyle"
        >
          <header class="border-b border-slate-100 px-4 py-4 md:px-6" :style="darkInnerBorderStyle">
            <div class="flex flex-wrap items-center justify-center gap-3 text-center">
              <div class="inline-flex items-center gap-2 text-[17px] font-bold uppercase tracking-[0.08em] text-slate-800">
                <svg
                  class="h-6 w-6 shrink-0"
                  :class="journey.direction === 'inbound' ? '-scale-x-100' : ''"
                  :style="accentTextStyle"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    fill="currentColor"
                    d="m9.983 20.048l-2.09-3.946l-3.966-2.11l1.083-1.077l3.452.587l3.05-3.05L4.01 7.25l1.388-1.38l9.125 1.565l3.12-3.139q.42-.421 1.03-.421t1.03.421q.422.421.422 1.028t-.421 1.028l-3.145 3.125l1.566 9.12l-1.394 1.394l-3.189-7.502l-3.05 3.05l.573 3.427z"
                  />
                </svg>
                <span>{{ journeyLabel(journey, journeyIndex) }}</span>
              </div>

              <div class="inline-flex items-center gap-1.5 text-base text-slate-500">
                <svg
                  class="h-[18px] w-[18px]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <rect x="3" y="5" width="18" height="16" rx="2" />
                  <path d="M3 10h18M8 3v4M16 3v4" />
                </svg>
                <span>{{ journeyDateLabel(journey) }}</span>
              </div>
            </div>

            <div :class="summaryGridClass" class="mt-3">
              <div :class="firstSummaryColClass">
                <p class="text-[20px] font-bold leading-none md:text-[28px]" :style="accentTextStyle">{{ firstTime(journey) }}</p>
                <p class="mt-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-700">{{ firstIata(journey) }}</p>
                <p class="text-sm text-slate-600">{{ firstCity(journey) }}</p>
              </div>

              <div class="min-w-0">
                <div class="mb-2 flex justify-center">
                  <span
                    class="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold"
                    :class="stopBadgeClass(journey)"
                  >
                    <span
                      class="h-1.5 w-1.5 rounded-full"
                      :class="stopCount(journey) ? 'bg-amber-600' : 'bg-emerald-600'"
                    ></span>
                    {{ stopLabel(journey) }}
                  </span>
                </div>

                <div class="mx-auto h-5 w-full px-5">
                  <div class="relative h-full w-full">
                    <div class="absolute inset-x-0 top-1/2 h-[2px] -translate-y-1/2 rounded-full" :style="accentLineStyle"></div>
                    <div
                      v-for="point in timelinePoints(journey)"
                      :key="point.index"
                      class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
                      :style="{ left: point.left }"
                    >
                      <span
                        class="block rounded-full border-[1.6px]"
                        :class="point.isEdge ? 'h-2.5 w-2.5' : 'h-2 w-2 bg-white'"
                        :style="timelinePointStyle(point.isEdge)"
                      ></span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="min-w-0">
                <p class="text-[20px] font-bold leading-none md:text-[28px]" :style="accentTextStyle">{{ lastTime(journey) }}</p>
                <p class="mt-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-700">{{ lastIata(journey) }}</p>
                <p class="text-sm text-slate-600">{{ lastCity(journey) }}</p>
              </div>

              <div :class="metaSummaryRowClass">
                <div :class="durationSummaryColClass">
                  <p class="inline-flex items-center justify-center gap-1.5 whitespace-nowrap text-sm text-slate-600">
                  <svg
                    class="h-4 w-4 shrink-0 text-slate-500"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="12" r="9" />
                    <path d="M12 7v5l3 2" />
                  </svg>
                  <span class="truncate">Duração: <strong class="font-semibold text-slate-800">{{ journeyDurationLabel(journey) }}</strong></span>
                </p>
                </div>

                <div :class="airlineSummaryColClass">
                  <div class="flex min-w-0 items-center justify-center gap-2">
                    <AirlineLogo
                      :airline-iata="journeyAirlineIata(journey)"
                      :airline-name="journeyAirlineName(journey)"
                      :custom-url="journeyAirlineLogo(journey)"
                      size-class="h-8 w-8"
                    />
                    <span class="truncate text-sm font-semibold text-slate-800">{{ journeyAirlineName(journey) }}</span>
                  </div>
                </div>
              </div>

              <div :class="toggleSummaryColClass">
                <button
                  type="button"
                  class="inline-flex items-center gap-1 whitespace-nowrap text-sm font-semibold"
                  :style="accentTextStyle"
                  @click="toggleJourney(journey, journeyIndex)"
                >
                  {{ isJourneyExpanded(journey, journeyIndex) ? "Ler menos" : "Ler mais" }}
                  <svg
                    class="h-4 w-4 transition-transform duration-200"
                    :class="{ 'rotate-180': isJourneyExpanded(journey, journeyIndex) }"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    aria-hidden="true"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
              </div>
            </div>
          </header>

          <transition name="flight-details-expand">
            <div v-if="isJourneyExpanded(journey, journeyIndex)" :style="expandedAreaStyle">
              <p
                v-if="!segmentsFor(journey).length"
                class="px-4 py-5 text-sm text-slate-600 md:px-6"
              >
                Esta jornada ainda não possui trechos configurados.
              </p>

              <template v-for="(segment, segmentIndex) in segmentsFor(journey)" :key="segment.id || segmentIndex">
                <div
                  class="px-4 py-5 md:px-6 md:py-6"
                  :class="segmentIndex > 0 ? 'border-t border-slate-200/70' : ''"
                  :style="segmentDividerStyle(segmentIndex)"
                >
                  <template v-if="useMobileSummaryLayout">
                    <div class="grid grid-cols-[14px_minmax(0,1fr)] gap-x-3">
                      <div></div>
                      <p class="mb-0.5 text-xs text-slate-500">{{ segmentDateLabel(segment) }}</p>

                      <div class="relative flex items-center justify-center">
                        <span
                          class="absolute left-1/2 top-1/2 bottom-0 w-px -translate-x-1/2 rounded-full"
                          :style="mobileSegmentLineStyle"
                        ></span>
                        <span
                          class="relative z-[1] h-2.5 w-2.5 rounded-full border-[1.8px]"
                          :style="mobileSegmentStartDotStyle"
                        ></span>
                      </div>
                      <p class="mt-0.5 mb-1.5 flex items-baseline gap-2">
                        <span class="text-[34px] font-bold leading-none" :style="accentTextStyle">{{ departureTime(segment) }}</span>
                        <span class="text-sm font-semibold uppercase tracking-[0.06em] text-slate-700">{{ segment.departure_airport_iata || "---" }}</span>
                      </p>

                      <div class="relative">
                        <span
                          class="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 rounded-full"
                          :style="mobileSegmentLineStyle"
                        ></span>
                      </div>
                      <div class="space-y-0.5">
                        <p class="mt-1 text-[24px] font-semibold leading-none text-slate-900">{{ segment.departure_city || "Cidade não informada" }}</p>
                        <p class="mt-0.5 text-sm text-slate-500">{{ departureAirportLabel(segment) }}</p>
                        <p v-if="departureTerminal(segment)" class="text-sm text-slate-500">{{ departureTerminal(segment) }}</p>
                      </div>

                      <div class="relative">
                        <span
                          class="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 rounded-full"
                          :style="mobileSegmentLineStyle"
                        ></span>
                      </div>
                      <p class="my-3 inline-flex items-center gap-1.5 text-sm text-slate-600">
                        <svg
                          class="h-4 w-4"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.8"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <circle cx="12" cy="12" r="9" />
                          <path d="M12 7v5l3 2" />
                        </svg>
                        <span>
                          Duração <strong class="font-semibold text-slate-800">{{ segmentDurationLabel(segment) }}</strong>
                          <span class="text-slate-400"> · </span>
                          {{ segmentAircraftLabel(segment) }}
                        </span>
                      </p>

                      <div class="relative">
                        <span
                          class="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 rounded-full"
                          :style="mobileSegmentLineStyle"
                        ></span>
                      </div>
                      <p class="mt-1 text-xs text-slate-500">{{ segmentDateLabel(segment) }}</p>

                      <div class="relative flex items-center justify-center">
                        <span
                          class="absolute left-1/2 top-0 bottom-1/2 w-px -translate-x-1/2 rounded-full"
                          :style="mobileSegmentLineStyle"
                        ></span>
                        <span
                          class="relative z-[1] h-2.5 w-2.5 rounded-full"
                          :style="accentDotStyle"
                        ></span>
                      </div>
                      <p class="mt-0.5 mb-1.5 flex items-baseline gap-2">
                        <span class="text-[34px] font-bold leading-none" :style="accentTextStyle">{{ arrivalTime(segment) }}</span>
                        <span class="text-sm font-semibold uppercase tracking-[0.06em] text-slate-700">{{ segment.arrival_airport_iata || "---" }}</span>
                      </p>

                      <div></div>
                      <div class="space-y-0.5">
                        <p class="mt-1 text-[24px] font-semibold leading-none text-slate-900">{{ segment.arrival_city || "Cidade não informada" }}</p>
                        <p class="mt-0.5 text-sm text-slate-500">{{ arrivalAirportLabel(segment) }}</p>
                        <p v-if="arrivalTerminal(segment)" class="text-sm text-slate-500">{{ arrivalTerminal(segment) }}</p>
                      </div>
                    </div>
                  </template>

                  <div v-else :class="segmentGridClass">
                    <div :class="segmentDepartureColClass">
                      <p class="text-xs text-slate-500">{{ segmentDateLabel(segment) }}</p>
                      <p class="mt-1 text-[24px] font-bold leading-none md:text-[34px]" :style="accentTextStyle">
                        {{ departureTime(segment) }}
                      </p>
                      <p class="mt-1 text-sm font-semibold uppercase tracking-[0.08em] text-slate-800">
                        {{ segment.departure_airport_iata || "---" }}
                      </p>
                      <p class="mt-1 text-sm text-slate-800 md:text-base">{{ segment.departure_city || "Cidade não informada" }}</p>
                      <p class="text-xs text-slate-500 md:text-sm">{{ departureAirportLabel(segment) }}</p>
                      <p v-if="departureTerminal(segment)" class="text-xs text-slate-500 md:text-sm">{{ departureTerminal(segment) }}</p>
                    </div>

                    <div class="min-w-0">
                      <div :class="segmentMiddleInnerClass">
                        <p class="inline-flex items-center gap-1.5 text-sm text-slate-600">
                          <svg
                            class="h-4 w-4"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.8"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            aria-hidden="true"
                          >
                            <circle cx="12" cy="12" r="9" />
                            <path d="M12 7v5l3 2" />
                          </svg>
                          Duração: <strong class="font-semibold text-slate-800">{{ segmentDurationLabel(segment) }}</strong>
                        </p>

                        <div class="relative h-4 w-full">
                          <div class="absolute left-4 right-4 top-1/2 h-[2px] -translate-y-1/2 rounded-full" :style="accentLineStyle"></div>
                          <span class="absolute left-3 top-1/2 h-2.5 w-2.5 -translate-y-1/2 rounded-full" :style="accentDotStyle"></span>
                          <span class="absolute right-3 top-1/2 h-2.5 w-2.5 -translate-y-1/2 rounded-full" :style="accentDotStyle"></span>
                        </div>

                        <p class="inline-flex items-center gap-1.5 text-xs text-slate-500">
                          <svg
                            class="h-3.5 w-3.5"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.8"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            aria-hidden="true"
                          >
                            <path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.2.6-.6.5-1.1Z" />
                          </svg>
                          {{ segmentAircraftLabel(segment) }}
                        </p>
                        <p class="text-xs text-slate-500">
                          Voo
                          <strong class="ml-1 font-semibold text-slate-700">{{ segmentFlightCode(segment) }}</strong>
                        </p>
                      </div>
                    </div>

                    <div :class="segmentArrivalColClass">
                      <p class="text-xs text-slate-500">{{ segmentDateLabel(segment) }}</p>
                      <p class="mt-1 text-[24px] font-bold leading-none md:text-[34px]" :style="accentTextStyle">
                        {{ arrivalTime(segment) }}
                      </p>
                      <p class="mt-1 text-sm font-semibold uppercase tracking-[0.08em] text-slate-800">
                        {{ segment.arrival_airport_iata || "---" }}
                      </p>
                      <p class="mt-1 text-sm text-slate-800 md:text-base">{{ segment.arrival_city || "Cidade não informada" }}</p>
                      <p class="text-xs text-slate-500 md:text-sm">{{ arrivalAirportLabel(segment) }}</p>
                      <p v-if="arrivalTerminal(segment)" class="text-xs text-slate-500 md:text-sm">{{ arrivalTerminal(segment) }}</p>
                    </div>
                  </div>

                  <div
                    class="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-[#e5e7eb] pt-3 text-xs text-slate-500"
                    :style="darkInnerBorderStyle"
                  >
                    <div class="inline-flex items-center gap-1.5">
                      <span
                        class="inline-flex h-6 w-6 cursor-help items-center justify-center rounded"
                        :class="segment.included_carry_on ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-600'"
                        :title="baggageTooltip('carry_on', segment.included_carry_on)"
                        :aria-label="baggageTooltip('carry_on', segment.included_carry_on)"
                      >
                        <svg viewBox="0 0 24 24" class="h-4 w-4" fill="currentColor" aria-hidden="true">
                          <path d="M7 9a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v9H7V9Zm2-2V6a3 3 0 1 1 6 0v1h-2V6a1 1 0 1 0-2 0v1H9Z" />
                        </svg>
                      </span>
                      <span
                        class="inline-flex h-6 w-6 cursor-help items-center justify-center rounded"
                        :class="segment.included_personal_item ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-600'"
                        :title="baggageTooltip('personal_item', segment.included_personal_item)"
                        :aria-label="baggageTooltip('personal_item', segment.included_personal_item)"
                      >
                        <svg viewBox="0 0 24 24" class="h-4 w-4" fill="currentColor" aria-hidden="true">
                          <path d="M8 8a4 4 0 1 1 8 0v1h1a2 2 0 0 1 2 2v9H5v-9a2 2 0 0 1 2-2h1V8Zm2 1h4V8a2 2 0 1 0-4 0v1Z" />
                        </svg>
                      </span>
                      <span
                        class="inline-flex h-6 w-6 cursor-help items-center justify-center rounded"
                        :class="segment.included_checked_bag ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-600'"
                        :title="baggageTooltip('checked_bag', segment.included_checked_bag)"
                        :aria-label="baggageTooltip('checked_bag', segment.included_checked_bag)"
                      >
                        <svg viewBox="0 0 24 24" class="h-4 w-4" fill="currentColor" aria-hidden="true">
                          <path d="M8 6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1h1a2 2 0 0 1 2 2v10H5V9a2 2 0 0 1 2-2h1V6Zm2 1h4V6h-4v1Z" />
                        </svg>
                      </span>
                    </div>
                    <div><span class="text-slate-400">Mão</span> <strong class="text-slate-700">·</strong> <span class="text-slate-400">Pessoal</span></div>
                    <div>Voo <strong class="font-semibold text-slate-700">{{ segmentFlightCode(segment) }}</strong></div>
                    <div>Classe <strong class="font-semibold text-slate-700">{{ segment.cabin_class || "Não informada" }}</strong></div>
                    <div>Operado por <strong class="font-semibold text-slate-700">{{ segment.airline_name || journeyAirlineName(journey) }}</strong></div>
                  </div>
                </div>

                <div
                  v-if="segmentIndex < segmentsFor(journey).length - 1 && layoverLabel(segmentsFor(journey), segmentIndex)"
                  class="border-y border-slate-200/80 bg-white px-4 py-3 md:px-6"
                  :style="layoverRowStyle"
                >
                  <div class="flex flex-wrap items-center justify-center gap-2 text-xs text-slate-600">
                    <span class="inline-flex items-center gap-1.5">
                      <svg
                        class="h-4 w-4 text-slate-500"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.8"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        aria-hidden="true"
                      >
                        <circle cx="12" cy="12" r="9" />
                        <path d="M12 7v5l3 2" />
                      </svg>
                      {{ layoverLabel(segmentsFor(journey), segmentIndex) }}
                    </span>
                    <span
                      v-if="isLongLayover(segmentsFor(journey), segmentIndex)"
                      :class="longLayoverBadgeClass"
                    >
                      Tempo longo de espera
                    </span>
                  </div>
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
import { computed, inject, isRef, onBeforeUnmount, onMounted, ref } from "vue";
import type { FlightDetailsSection, FlightSectionJourney, FlightSectionSegment } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import AirlineLogo from "../shared/AirlineLogo.vue";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../utils/sectionHeadings";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { deriveTextPalette, getRelativeLuminance, normalizeHexColor } from "../../utils/colorContrast";

const props = defineProps<{ section: FlightDetailsSection; previewDevice?: "desktop" | "mobile" }>();
const localize = createLocalizer(getCurrentLanguage());
const headingDefaults = getSectionHeadingDefaults("flight_details");
const branding = inject(PUBLIC_BRANDING_KEY, null);

const isMobilePreview = computed(() => props.previewDevice === "mobile");
const isNarrowViewport = ref(false);
const syncViewportMode = () => {
  if (typeof window === "undefined") return;
  isNarrowViewport.value = window.innerWidth < 768;
};
onMounted(() => {
  syncViewportMode();
  window.addEventListener("resize", syncViewportMode, { passive: true });
});
onBeforeUnmount(() => {
  if (typeof window === "undefined") return;
  window.removeEventListener("resize", syncViewportMode);
});
const useMobileSummaryLayout = computed(() => isMobilePreview.value || isNarrowViewport.value);
const sectionBackground = computed(() => props.section.backgroundColor || "#ffffff");
const extractFirstHexColor = (value?: string | null) => {
  if (!value) return null;
  const match = String(value).match(/#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b/);
  return match ? `#${match[1]}` : null;
};
const sectionBackgroundHex = computed(() =>
  normalizeHexColor(props.section.backgroundColor) || normalizeHexColor(extractFirstHexColor(props.section.backgroundColor))
);
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const sectionBackgroundIsLight = computed(() => {
  if (!sectionBackgroundHex.value) return !textPalette.value.isLight;
  return getRelativeLuminance(sectionBackgroundHex.value) > 0.7;
});
const sectionTitle = computed(() => {
  const title = localize(props.section.title).trim();
  return title || "Informações do voo";
});
const sectionSubtitle = computed(() => localize(props.section.subtitle).trim());
const brandingPrimary = computed(() => {
  if (!branding) return "";
  const data = isRef(branding) ? branding.value : branding;
  if (typeof data === "object" && data) {
    const color = (data as Record<string, any>).primary_color;
    if (typeof color === "string" && color.trim()) return color.trim();
  }
  return "";
});
const brandingThemeAccent = computed(() => {
  if (!branding) return "";
  const data = isRef(branding) ? branding.value : branding;
  if (typeof data === "object" && data) {
    const theme = (data as Record<string, any>).theme;
    const color = theme && typeof theme.ctaDefaultColor === "string" ? theme.ctaDefaultColor : "";
    if (typeof color === "string" && color.trim()) return color.trim();
  }
  return "";
});
const defaultAccent = "#2563eb";
const sectionAccent = computed(() => {
  const candidate = (props.section as Record<string, any>)?.ctaColor;
  return typeof candidate === "string" ? candidate.trim() : "";
});
const accent = computed(() => sectionAccent.value || brandingThemeAccent.value || brandingPrimary.value || defaultAccent);
const hexToRgba = (hex: string, alpha: number) => {
  const clean = hex.replace("#", "");
  const full = clean.length === 3 ? clean.split("").map(char => `${char}${char}`).join("") : clean;
  const r = Number.parseInt(full.slice(0, 2), 16);
  const g = Number.parseInt(full.slice(2, 4), 16);
  const b = Number.parseInt(full.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
const parseRgb = (value: string) => {
  const match = value
    .trim()
    .match(/^rgba?\((\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*(\d*\.?\d+))?\)$/i);
  if (!match) return null;
  const r = Math.max(0, Math.min(255, Number(match[1])));
  const g = Math.max(0, Math.min(255, Number(match[2])));
  const b = Math.max(0, Math.min(255, Number(match[3])));
  return { r, g, b };
};
const accentColor = computed(() => String(accent.value || defaultAccent).trim());
const accentSoftColor = computed(() => {
  const normalized = normalizeHexColor(accentColor.value);
  if (normalized) return hexToRgba(normalized, 0.28);
  const parsedRgb = parseRgb(accentColor.value);
  if (parsedRgb) return `rgba(${parsedRgb.r}, ${parsedRgb.g}, ${parsedRgb.b}, 0.28)`;
  return "rgba(37, 99, 235, 0.28)";
});
const darkAccentBorderColor = computed(() => {
  const normalized = normalizeHexColor(accentColor.value);
  if (normalized) return hexToRgba(normalized, 0.38);
  const parsedRgb = parseRgb(accentColor.value);
  if (parsedRgb) return `rgba(${parsedRgb.r}, ${parsedRgb.g}, ${parsedRgb.b}, 0.38)`;
  return "rgba(37, 99, 235, 0.38)";
});
const accentTextStyle = computed(() => ({ color: accentColor.value }));
const accentLineStyle = computed(() => ({ backgroundColor: accentSoftColor.value }));
const accentDotStyle = computed(() => ({ backgroundColor: accentColor.value }));
const mobileSegmentLineStyle = computed(() => ({
  backgroundColor: sectionBackgroundIsLight.value ? "#cbd5e1" : darkAccentBorderColor.value
}));
const mobileSegmentStartDotStyle = computed(() => ({
  borderColor: accentColor.value,
  backgroundColor: sectionBackgroundIsLight.value ? "#ffffff" : "rgba(15,23,42,0.82)"
}));
const timelinePointStyle = (isEdge: boolean) => ({
  borderColor: accentColor.value,
  backgroundColor: isEdge ? accentColor.value : "#ffffff"
});
const headingLabel = computed(() =>
  resolveHeadingLabel(props.section.headingLabel, headingDefaults.label, localize)
);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const hasCustomTextColor = computed(() => Boolean(normalizeHexColor(props.section.textColor)));
const headingTitleColor = computed(() => {
  if (hasCustomTextColor.value) return textPalette.value.primary;
  return sectionBackgroundIsLight.value ? "#0f172a" : "#f8fafc";
});
const headingSubtitleColor = computed(() => {
  if (hasCustomTextColor.value) return textPalette.value.muted;
  return sectionBackgroundIsLight.value ? "#475569" : "rgba(241,245,249,0.82)";
});
const cardShellStyle = computed(() => ({
  backgroundColor: sectionBackgroundIsLight.value ? "#ffffff" : "rgba(255,255,255,0.05)",
  borderColor: sectionBackgroundIsLight.value ? "#e5e7eb" : darkAccentBorderColor.value,
  boxShadow: sectionBackgroundIsLight.value ? "0 14px 30px -24px rgba(15,23,42,0.28)" : "none"
}));
const darkInnerBorderStyle = computed(() =>
  sectionBackgroundIsLight.value ? {} : { borderColor: darkAccentBorderColor.value }
);
const segmentDividerStyle = (segmentIndex: number) =>
  !sectionBackgroundIsLight.value && segmentIndex > 0 ? { borderColor: darkAccentBorderColor.value } : {};
const expandedAreaStyle = computed(() => ({
  backgroundColor: sectionBackgroundIsLight.value ? "rgba(0,0,0,0.02)" : "rgba(255,255,255,0.05)"
}));
const layoverRowStyle = computed(() =>
  sectionBackgroundIsLight.value
    ? {}
    : {
        borderColor: darkAccentBorderColor.value,
        backgroundColor: "rgba(255,255,255,0.03)"
      }
);
const longLayoverBadgeClass = computed(() =>
  sectionBackgroundIsLight.value
    ? "rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-700"
    : "rounded-full border border-amber-300/35 bg-amber-500/18 px-2 py-0.5 text-[11px] font-semibold text-amber-100"
);

const visibleJourneys = computed(() => {
  const journeys = (props.section.journeys || []).filter(journey => journey.is_enabled !== false);
  return journeys
    .filter(journey => {
      if (journey.direction === "outbound") return props.section.showOutbound !== false;
      if (journey.direction === "inbound") return props.section.showInbound !== false;
      return true;
    })
    .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
});

const expandedByKey = ref<Record<string, boolean>>({});

const journeyKey = (journey: FlightSectionJourney, index: number) =>
  String(journey.id || `${journey.direction}-${index}`);

const toggleJourney = (journey: FlightSectionJourney, index: number) => {
  const key = journeyKey(journey, index);
  expandedByKey.value[key] = !isJourneyExpanded(journey, index);
};

const isJourneyExpanded = (journey: FlightSectionJourney, index: number) => {
  const key = journeyKey(journey, index);
  const stored = expandedByKey.value[key];
  if (typeof stored === "boolean") return stored;
  return false;
};

const summaryGridClass = computed(() =>
  useMobileSummaryLayout.value
    ? "grid items-center gap-x-3 gap-y-3 grid-cols-[minmax(0,1fr)_minmax(120px,1.2fr)_minmax(0,1fr)]"
    : "grid gap-3 md:items-center md:grid-cols-[140px_minmax(0,1fr)_140px_170px_150px_120px]"
);
const firstSummaryColClass = computed(() =>
  useMobileSummaryLayout.value ? "min-w-0 text-right" : "min-w-0 md:text-right"
);
const metaSummaryRowClass = computed(() =>
  useMobileSummaryLayout.value ? "min-w-0 col-span-3 flex items-center justify-center gap-3" : "contents"
);
const durationSummaryColClass = computed(() =>
  useMobileSummaryLayout.value ? "min-w-0" : "min-w-0 md:justify-self-center"
);
const airlineSummaryColClass = computed(() =>
  useMobileSummaryLayout.value ? "min-w-0" : "min-w-0 md:justify-self-center"
);
const toggleSummaryColClass = computed(() =>
  useMobileSummaryLayout.value ? "min-w-0 col-span-3 justify-self-center" : "min-w-0 md:justify-self-end"
);

const segmentGridClass = computed(() =>
  useMobileSummaryLayout.value
    ? "grid items-start gap-x-3 gap-y-3 grid-cols-[minmax(0,1fr)_minmax(120px,1.15fr)_minmax(0,1fr)]"
    : "grid gap-6 md:grid-cols-[220px_minmax(0,1fr)_220px] md:items-center md:gap-8"
);
const segmentDepartureColClass = computed(() =>
  useMobileSummaryLayout.value ? "min-w-0 text-right" : "min-w-0 text-left md:text-center"
);
const segmentArrivalColClass = computed(() =>
  useMobileSummaryLayout.value ? "min-w-0 text-left" : "min-w-0 text-left md:text-center"
);
const segmentMiddleInnerClass = computed(() =>
  useMobileSummaryLayout.value
    ? "mx-auto flex w-full max-w-[170px] flex-col items-center gap-1.5 text-center"
    : "mx-auto flex max-w-[320px] flex-col items-center gap-2 text-center"
);

const segmentsFor = (journey: FlightSectionJourney): FlightSectionSegment[] =>
  [...(journey.segments || [])].sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));

const firstSegment = (journey: FlightSectionJourney) => segmentsFor(journey)[0] || null;

const lastSegment = (journey: FlightSectionJourney) => {
  const list = segmentsFor(journey);
  return list[list.length - 1] || null;
};

const parseDate = (value?: string | null) => {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
};

const timeFormatter = new Intl.DateTimeFormat("pt-BR", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false
});

const fullDateFormatter = new Intl.DateTimeFormat("pt-BR", {
  weekday: "short",
  day: "numeric",
  month: "short",
  year: "numeric"
});

const shortDateFormatter = new Intl.DateTimeFormat("pt-BR", {
  weekday: "short",
  day: "numeric",
  month: "short"
});

const normalizePtDate = (value: string) => value.replace(/\sde\s(\d{4})$/i, " $1");

const formatTime = (value?: string | null) => {
  const date = parseDate(value);
  if (!date) return "--:--";
  return timeFormatter.format(date);
};

const formatDate = (value?: string | null, full = false) => {
  const date = parseDate(value);
  if (!date) return "--";
  const label = full ? fullDateFormatter.format(date) : shortDateFormatter.format(date);
  return normalizePtDate(label);
};

const formatDurationFromMinutes = (minutes?: number | null) => {
  if (!minutes || minutes <= 0) return "Não informado";
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `${String(hours).padStart(2, "0")}h ${String(rest).padStart(2, "0")}min`;
};

const minutesBetween = (start?: string | null, end?: string | null) => {
  const startDate = parseDate(start);
  const endDate = parseDate(end);
  if (!startDate || !endDate) return 0;
  const diff = Math.round((endDate.getTime() - startDate.getTime()) / 60000);
  return diff > 0 ? diff : 0;
};

const totalDurationMinutes = (journey: FlightSectionJourney) => {
  const first = firstSegment(journey);
  const last = lastSegment(journey);
  const rangeDiff = minutesBetween(first?.departure_datetime, last?.arrival_datetime);
  if (rangeDiff > 0) return rangeDiff;
  return segmentsFor(journey).reduce((sum, segment) => sum + Number(segment.duration_minutes || 0), 0);
};

const stopCount = (journey: FlightSectionJourney) => Math.max(0, segmentsFor(journey).length - 1);

const stopLabel = (journey: FlightSectionJourney) => {
  const stops = stopCount(journey);
  if (!stops) return "Direto";
  return `${stops} ${stops === 1 ? "parada" : "paradas"}`;
};

const stopBadgeClass = (journey: FlightSectionJourney) =>
  stopCount(journey)
    ? "border-amber-200 bg-amber-50 text-amber-700"
    : "border-emerald-200 bg-emerald-50 text-emerald-700";

const timelinePoints = (journey: FlightSectionJourney) => {
  const stops = stopCount(journey);
  const totalPoints = stops + 2;
  return Array.from({ length: totalPoints }, (_, index) => ({
    index,
    left: `${(index / (totalPoints - 1)) * 100}%`,
    isEdge: index === 0 || index === totalPoints - 1
  }));
};

const journeyLabel = (journey: FlightSectionJourney, index: number) => {
  const manual = String(journey.title || "").trim();
  if (manual) return manual;
  const direction = journey.direction === "inbound" ? "VOLTA" : "IDA";
  return `VOO ${index + 1} · ${direction}`;
};

const journeyDateLabel = (journey: FlightSectionJourney) => formatDate(firstSegment(journey)?.departure_datetime, true);
const journeyDurationLabel = (journey: FlightSectionJourney) => formatDurationFromMinutes(totalDurationMinutes(journey));

const firstTime = (journey: FlightSectionJourney) => formatTime(firstSegment(journey)?.departure_datetime);
const lastTime = (journey: FlightSectionJourney) => formatTime(lastSegment(journey)?.arrival_datetime);

const firstIata = (journey: FlightSectionJourney) => firstSegment(journey)?.departure_airport_iata || "---";
const lastIata = (journey: FlightSectionJourney) => lastSegment(journey)?.arrival_airport_iata || "---";

const firstCity = (journey: FlightSectionJourney) => firstSegment(journey)?.departure_city || "Origem";
const lastCity = (journey: FlightSectionJourney) => lastSegment(journey)?.arrival_city || "Destino";

const journeyAirlineName = (journey: FlightSectionJourney) =>
  firstSegment(journey)?.airline_name || "Companhia não informada";

const journeyAirlineIata = (journey: FlightSectionJourney) => firstSegment(journey)?.airline_iata || "";
const journeyAirlineLogo = (journey: FlightSectionJourney) => firstSegment(journey)?.airline_logo_url || "";

const segmentDateLabel = (segment: FlightSectionSegment) => formatDate(segment.departure_datetime);
const departureTime = (segment: FlightSectionSegment) => formatTime(segment.departure_datetime);
const arrivalTime = (segment: FlightSectionSegment) => formatTime(segment.arrival_datetime);

const segmentDurationLabel = (segment: FlightSectionSegment) => {
  const byRange = minutesBetween(segment.departure_datetime, segment.arrival_datetime);
  if (byRange > 0) return formatDurationFromMinutes(byRange);
  return formatDurationFromMinutes(segment.duration_minutes);
};

const departureTerminal = (segment: FlightSectionSegment) => {
  const terminal = String(segment.departure_terminal || "").trim();
  if (!terminal) return "";
  return `Terminal ${terminal}`;
};

const arrivalTerminal = (segment: FlightSectionSegment) => {
  const terminal = String(segment.arrival_terminal || "").trim();
  if (!terminal) return "";
  return `Terminal ${terminal}`;
};

const segmentFlightCode = (segment: FlightSectionSegment) =>
  segment.flight_number || segment.flight_iata || segment.flight_icao || "--";

const normalizeSearchText = (value?: string | null) =>
  String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();

const compactAirportName = (city?: string | null, airportName?: string | null) => {
  const airport = String(airportName || "").trim();
  if (!airport) return "Aeroporto não informado";
  const cityLabel = String(city || "").trim();
  if (!cityLabel) return airport;

  const normalizedAirport = normalizeSearchText(airport);
  const normalizedCity = normalizeSearchText(cityLabel);
  if (!normalizedCity || !normalizedAirport.startsWith(normalizedCity)) return airport;

  const escapedCity = cityLabel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const compact = airport.replace(new RegExp(`^${escapedCity}[\\s\\-,:|]*`, "i"), "").trim();
  return compact || airport;
};

const departureAirportLabel = (segment: FlightSectionSegment) =>
  compactAirportName(segment.departure_city, segment.departure_airport_name);

const arrivalAirportLabel = (segment: FlightSectionSegment) =>
  compactAirportName(segment.arrival_city, segment.arrival_airport_name);

const baggageTooltip = (type: "carry_on" | "personal_item" | "checked_bag", included?: boolean) => {
  const status = included ? "incluida" : "nao incluida";
  if (type === "carry_on") return `Bagagem de mao ${status}`;
  if (type === "personal_item") return `Item pessoal ${status}`;
  return `Bagagem despachada ${status}`;
};

const segmentAircraftLabel = (segment: FlightSectionSegment) => {
  const anySegment = segment as Record<string, any>;
  const direct =
    String(anySegment.aircraft || anySegment.aircraft_name || anySegment.aircraft_model || anySegment.aircraft_type || "").trim();
  if (direct) return direct;
  const raw = anySegment.raw_provider_response as Record<string, any> | null | undefined;
  if (raw && typeof raw === "object") {
    const rawAircraft = raw.aircraft;
    if (typeof rawAircraft === "string" && rawAircraft.trim()) return rawAircraft.trim();
    if (rawAircraft && typeof rawAircraft === "object") {
      const model = String(rawAircraft.model || rawAircraft.name || rawAircraft.code || "").trim();
      if (model) return model;
    }
  }
  return "Aeronave não informada";
};

const layoverMinutes = (segments: FlightSectionSegment[], index: number) => {
  const current = segments[index];
  const next = segments[index + 1];
  if (!current || !next) return 0;
  return minutesBetween(current.arrival_datetime, next.departure_datetime);
};

const layoverDurationLabel = (minutes: number) => {
  if (minutes <= 0) return "";
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `${String(hours).padStart(2, "0")}h ${String(rest).padStart(2, "0")}min`;
};

const layoverLocation = (segments: FlightSectionSegment[], index: number) => {
  const current = segments[index];
  if (!current) return "";
  const city = String(current.arrival_city || "").trim();
  const iata = String(current.arrival_airport_iata || "").trim();
  if (city && iata) return `${city} (${iata})`;
  if (city) return city;
  if (iata) return iata;
  return "aeroporto de conexão";
};

const layoverLabel = (segments: FlightSectionSegment[], index: number) => {
  const minutes = layoverMinutes(segments, index);
  if (!minutes) return "";
  return `Espera de ${layoverDurationLabel(minutes)} em ${layoverLocation(segments, index)}`;
};

const isLongLayover = (segments: FlightSectionSegment[], index: number) => layoverMinutes(segments, index) >= 240;
</script>

<style scoped>
.flight-details-expand-enter-active,
.flight-details-expand-leave-active {
  transition: max-height 0.35s ease, opacity 0.25s ease;
  overflow: hidden;
}

.flight-details-expand-enter-from,
.flight-details-expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.flight-details-expand-enter-to,
.flight-details-expand-leave-from {
  max-height: 3000px;
  opacity: 1;
}

.flight-card[data-dark="true"] .text-slate-900,
.flight-card[data-dark="true"] .text-slate-800,
.flight-card[data-dark="true"] .text-slate-700,
.flight-card[data-dark="true"] .text-slate-600,
.flight-card[data-dark="true"] .text-slate-500,
.flight-card[data-dark="true"] .text-slate-400 {
  color: #f8fafc !important;
}
</style>





