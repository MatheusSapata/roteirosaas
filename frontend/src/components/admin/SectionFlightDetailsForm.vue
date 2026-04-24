<template>
  <div class="space-y-4">
    <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Titulo da secao</label>
          <input
            v-model="local.title"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Informacoes do voo"
          />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Subtitulo</label>
          <input
            v-model="local.subtitle"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Confira os detalhes dos voos inclusos no pacote"
          />
        </div>
      </div>
      <div class="mt-3 grid gap-3 md:grid-cols-3">
        <label class="inline-flex items-center gap-2 text-sm text-slate-600">
          <input v-model="local.enabled" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
          Secao ativa
        </label>
        <label class="inline-flex items-center gap-2 text-sm text-slate-600">
          <input v-model="local.showOutbound" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
          Mostrar ida
        </label>
        <label class="inline-flex items-center gap-2 text-sm text-slate-600">
          <input v-model="local.showInbound" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
          Mostrar volta
        </label>
      </div>
      <div class="mt-3">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Layout</label>
        <select v-model="local.visualStyle" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="compact">Compacto</option>
          <option value="decolar">Completo</option>
        </select>
      </div>
      <p v-if="!lookupAvailable" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
        Busca automatica indisponivel. Preencha manualmente.
      </p>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="inline-flex rounded-full border border-slate-200 bg-slate-50 p-1">
          <button
            type="button"
            class="rounded-full px-4 py-1.5 text-sm font-semibold transition"
            :class="activeDirection === 'outbound' ? 'bg-brand text-white' : 'text-slate-600'"
            @click="activeDirection = 'outbound'"
          >
            Ida
          </button>
          <button
            type="button"
            class="rounded-full px-4 py-1.5 text-sm font-semibold transition"
            :class="activeDirection === 'inbound' ? 'bg-brand text-white' : 'text-slate-600'"
            @click="activeDirection = 'inbound'"
          >
            Volta
          </button>
        </div>
        <button
          type="button"
          class="rounded-full border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700"
          @click="addSegment"
        >
          + Adicionar trecho
        </button>
      </div>

      <div v-if="loadingJourneys" class="mt-4 text-sm text-slate-500">Carregando trechos...</div>
      <div v-else class="mt-4 space-y-4">
        <div
          v-for="(segment, index) in activeSegments"
          :key="segment.id || index"
          class="rounded-2xl border border-slate-200 bg-slate-50 p-3"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex min-w-0 items-center gap-2">
              <AirlineLogo
                :airline-iata="segment.airline_iata"
                :airline-name="segment.airline_name"
                :custom-url="segment.airline_logo_url"
                size-class="h-7 w-7"
              />
              <button
                type="button"
                class="min-w-0 text-left text-sm font-semibold text-slate-700"
                @click="selectSegment(segment.id || null)"
              >
                {{ segmentTitle(segment, index) }}
              </button>
            </div>
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="rounded border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600"
                :disabled="index === 0"
                @click="moveSegment(index, -1)"
              >
                Subir
              </button>
              <button
                type="button"
                class="rounded border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600"
                :disabled="index === activeSegments.length - 1"
                @click="moveSegment(index, 1)"
              >
                Descer
              </button>
              <button
                type="button"
                class="rounded border border-rose-200 bg-rose-50 px-2 py-1 text-xs font-semibold text-rose-600"
                @click="removeSegment(segment)"
              >
                Excluir
              </button>
            </div>
          </div>
          <p v-if="index < activeSegments.length - 1 && layoverText(index)" class="mt-2 text-xs text-slate-500">
            {{ layoverText(index) }}
          </p>
        </div>

        <div v-if="!activeSegments.length" class="rounded-xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
          Nenhum trecho cadastrado nesta jornada.
        </div>
      </div>
    </div>

    <div v-if="selectedSegmentDraft" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h4 class="text-sm font-semibold text-slate-800">Trecho selecionado</h4>

      <div class="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Buscar automatico</p>
        <div class="mt-2 grid gap-3 md:grid-cols-3">
          <div>
            <label class="text-xs text-slate-500">Numero do voo</label>
            <input
              v-model="lookupFlightNumber"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              placeholder="AD2769"
            />
          </div>
          <div>
            <label class="text-xs text-slate-500">Data do voo</label>
            <input v-model="lookupFlightDate" type="date" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
          </div>
          <div class="flex items-end">
            <button
              type="button"
              class="w-full rounded-lg bg-brand px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
              :disabled="lookupLoading || !lookupAvailable || !lookupFlightNumber || !lookupFlightDate"
              @click="runLookup(false)"
            >
              {{ lookupLoading ? "Buscando..." : "Buscar voo" }}
            </button>
          </div>
        </div>
        <div class="mt-2 flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 disabled:opacity-60"
            :disabled="lookupLoading || !lookupAvailable || !lookupFlightNumber || !lookupFlightDate"
            @click="runLookup(true)"
          >
            Atualizar dados pela API
          </button>
          <span v-if="lookupState && lookupState !== 'idle'" class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            {{ lookupStateLabel }}
          </span>
        </div>
        <p v-if="lookupMessage" class="mt-2 text-xs text-emerald-700">{{ lookupMessage }}</p>
        <p v-if="lookupProviderInfo" class="mt-1 text-xs text-slate-600">{{ lookupProviderInfo }}</p>
        <p v-if="lookupError" class="mt-2 text-xs text-rose-600">{{ lookupError }}</p>
      </div>

      <div class="mt-4 grid gap-3 md:grid-cols-4">
        <div class="flex items-end">
          <div class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Logo automatica</p>
            <div class="mt-2 flex items-center gap-2">
              <AirlineLogo
                :airline-iata="selectedSegmentDraft.airline_iata"
                :airline-name="selectedSegmentDraft.airline_name"
                :custom-url="selectedSegmentDraft.airline_logo_url"
                size-class="h-10 w-10 sm:h-12 sm:w-12"
              />
              <p class="text-xs text-slate-500">
                {{ (selectedSegmentDraft.airline_iata || "---").toUpperCase() }}
              </p>
            </div>
          </div>
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Companhia aerea</label>
          <input v-model="selectedSegmentDraft.airline_name" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Logo (URL)</label>
          <input v-model="selectedSegmentDraft.airline_logo_url" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Numero do voo</label>
          <input v-model="selectedSegmentDraft.flight_number" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>

      <div class="mt-4 grid gap-3 md:grid-cols-2">
        <div class="rounded-xl border border-slate-200 p-3">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Origem</p>
          <div class="mt-2 grid gap-2 md:grid-cols-2">
            <input v-model="selectedSegmentDraft.departure_airport_iata" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Sigla (IATA)" />
            <input v-model="selectedSegmentDraft.departure_city" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Cidade" />
          </div>
          <input v-model="selectedSegmentDraft.departure_airport_name" class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Aeroporto" />
          <div class="mt-2 grid gap-2 md:grid-cols-2">
            <input v-model="selectedSegmentDraft.departure_country" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Pais" />
            <input v-model="selectedSegmentDraft.departure_datetime" type="datetime-local" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
          </div>
        </div>
        <div class="rounded-xl border border-slate-200 p-3">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Destino</p>
          <div class="mt-2 grid gap-2 md:grid-cols-2">
            <input v-model="selectedSegmentDraft.arrival_airport_iata" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Sigla (IATA)" />
            <input v-model="selectedSegmentDraft.arrival_city" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Cidade" />
          </div>
          <input v-model="selectedSegmentDraft.arrival_airport_name" class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Aeroporto" />
          <div class="mt-2 grid gap-2 md:grid-cols-2">
            <input v-model="selectedSegmentDraft.arrival_country" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Pais" />
            <input v-model="selectedSegmentDraft.arrival_datetime" type="datetime-local" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
          </div>
        </div>
      </div>

      <div class="mt-4 grid gap-3 md:grid-cols-4">
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Duracao (min)</label>
          <input v-model.number="selectedSegmentDraft.duration_minutes" type="number" min="0" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Classe</label>
          <input v-model="selectedSegmentDraft.cabin_class" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" placeholder="Economica" />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</label>
          <input v-model="selectedSegmentDraft.status" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Data do voo</label>
          <input v-model="selectedSegmentDraft.flight_date" type="date" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>

      <div class="mt-4 rounded-xl border border-slate-200 p-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Bagagens incluidas neste trecho</p>
        <div class="mt-2 grid gap-2 md:grid-cols-3">
          <label class="inline-flex items-center gap-2 text-sm text-slate-600">
            <input v-model="selectedSegmentDraft.included_personal_item" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
            Item pessoal
          </label>
          <label class="inline-flex items-center gap-2 text-sm text-slate-600">
            <input v-model="selectedSegmentDraft.included_carry_on" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
            Bagagem de mao
          </label>
          <label class="inline-flex items-center gap-2 text-sm text-slate-600">
            <input v-model="selectedSegmentDraft.included_checked_bag" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
            Bagagem despachada
          </label>
        </div>
      </div>

      <div class="mt-4">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Observacoes</label>
        <textarea
          v-model="selectedSegmentDraft.notes"
          rows="3"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Campo opcional"
        ></textarea>
      </div>

      <div class="mt-4 flex flex-wrap justify-end gap-2">
        <button
          type="button"
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600"
          @click="reloadJourneys"
        >
          Recarregar
        </button>
        <button
          type="button"
          class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          :disabled="savingSegment"
          @click="saveSegment"
        >
          {{ savingSegment ? "Salvando..." : "Salvar trecho" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import type { FlightDetailsSection, FlightSectionJourney, FlightSectionSegment } from "../../types/page";
import AirlineLogo from "../shared/AirlineLogo.vue";
import {
  bootstrapFlightJourneys,
  createFlightSegment,
  deleteFlightSegment,
  getFlightJourneys,
  lookupFlight,
  reorderFlightSegments,
  updateFlightSegment
} from "../../services/flightDetails";

const props = defineProps<{ modelValue: FlightDetailsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FlightDetailsSection): void }>();

const route = useRoute();
const pageId = computed(() => route.params.id as string);

const local = reactive<FlightDetailsSection>({
  ...props.modelValue,
  type: "flight_details",
  enabled: props.modelValue.enabled ?? true,
  title: props.modelValue.title || "Informacoes do voo",
  subtitle: props.modelValue.subtitle || "Confira os detalhes dos voos inclusos no pacote",
  ctaColor: props.modelValue.ctaColor || "",
  visualStyle: props.modelValue.visualStyle || "decolar",
  showOutbound: props.modelValue.showOutbound ?? true,
  showInbound: props.modelValue.showInbound ?? true,
  journeys: props.modelValue.journeys || [],
  sectionId: props.modelValue.sectionId || props.modelValue.anchorId || `flight-${Math.random().toString(36).slice(2, 10)}`
});

const loadingJourneys = ref(false);
const lookupAvailable = ref(Boolean(props.modelValue.lookupAvailable));
const activeDirection = ref<"outbound" | "inbound">("outbound");
const journeys = ref<FlightSectionJourney[]>(props.modelValue.journeys || []);
const selectedSegmentId = ref<number | null>(null);
const selectedSegmentDraft = ref<FlightSectionSegment | null>(null);
const lookupLoading = ref(false);
const lookupMessage = ref("");
const lookupError = ref("");
const lookupProviderInfo = ref("");
const lookupState = ref<"idle" | "loading" | "success" | "cache" | "fallback" | "error">("idle");
const lookupFlightNumber = ref("");
const lookupFlightDate = ref("");
const savingSegment = ref(false);

const lookupStateLabel = computed(() => {
  if (lookupState.value === "loading") return "Carregando";
  if (lookupState.value === "success") return "Sucesso";
  if (lookupState.value === "cache") return "Cache";
  if (lookupState.value === "fallback") return "Fallback";
  if (lookupState.value === "error") return "Erro";
  return "";
});

const emitLocal = () => {
  emit("update:modelValue", {
    ...local,
    sectionId: local.sectionId,
    journeys: journeys.value,
    lookupAvailable: lookupAvailable.value
  });
};

watch(
  () => props.modelValue,
  value => {
    local.enabled = value.enabled ?? true;
    local.title = value.title || "Informacoes do voo";
    local.subtitle = value.subtitle || "Confira os detalhes dos voos inclusos no pacote";
    local.ctaColor = value.ctaColor || "";
    local.visualStyle = value.visualStyle || "decolar";
    local.showOutbound = value.showOutbound ?? true;
    local.showInbound = value.showInbound ?? true;
    local.sectionId = value.sectionId || value.anchorId || local.sectionId || `flight-${Math.random().toString(36).slice(2, 10)}`;
    journeys.value = value.journeys || journeys.value;
    lookupAvailable.value = value.lookupAvailable ?? lookupAvailable.value;
  },
  { deep: true }
);

watch(
  () => [local.enabled, local.title, local.subtitle, local.ctaColor, local.visualStyle, local.showOutbound, local.showInbound, local.sectionId],
  () => emitLocal(),
  { deep: true }
);

const activeJourney = computed(() =>
  journeys.value.find(journey => journey.direction === activeDirection.value) || null
);

const activeSegments = computed(() => {
  const target = activeJourney.value;
  if (!target?.segments) return [];
  return [...target.segments].sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
});

const sectionId = computed(() => local.sectionId || local.anchorId || "");

const setSelectedSegment = (segment: FlightSectionSegment | null) => {
  if (!segment) {
    selectedSegmentId.value = null;
    selectedSegmentDraft.value = null;
    return;
  }
  selectedSegmentId.value = segment.id || null;
  selectedSegmentDraft.value = {
    ...segment,
    flight_date: segment.flight_date ? String(segment.flight_date).slice(0, 10) : "",
    departure_datetime: toDatetimeLocal(segment.departure_datetime),
    arrival_datetime: toDatetimeLocal(segment.arrival_datetime),
    included_personal_item: segment.included_personal_item !== false,
    included_carry_on: segment.included_carry_on !== false,
    included_checked_bag: !!segment.included_checked_bag
  };
  lookupFlightNumber.value = segment.flight_number || segment.flight_iata || "";
  lookupFlightDate.value = segment.flight_date ? String(segment.flight_date).slice(0, 10) : "";
};

const selectSegment = (segmentId: number | null) => {
  if (!segmentId) {
    setSelectedSegment(null);
    return;
  }
  const target = activeSegments.value.find(segment => segment.id === segmentId) || null;
  setSelectedSegment(target);
};

const normalizeJourney = (journey: FlightSectionJourney): FlightSectionJourney => ({
  ...journey,
  segments: (journey.segments || []).map((segment, index) => ({
    ...segment,
    sort_order: segment.sort_order ?? index,
    included_personal_item: segment.included_personal_item !== false,
    included_carry_on: segment.included_carry_on !== false,
    included_checked_bag: !!segment.included_checked_bag
  }))
});

const applyJourneys = (nextJourneys: FlightSectionJourney[]) => {
  journeys.value = nextJourneys.map(normalizeJourney);
  if (selectedSegmentId.value) {
    const selected = journeys.value
      .flatMap(journey => journey.segments || [])
      .find(segment => segment.id === selectedSegmentId.value);
    if (selected) {
      setSelectedSegment(selected);
      emitLocal();
      return;
    }
  }
  const firstSegment = activeSegments.value[0] || null;
  setSelectedSegment(firstSegment);
  emitLocal();
};

const reloadJourneys = async () => {
  if (!pageId.value || !sectionId.value) return;
  loadingJourneys.value = true;
  try {
    let response = await getFlightJourneys(pageId.value, sectionId.value);
    if (!response.journeys?.length) {
      response = await bootstrapFlightJourneys(pageId.value, sectionId.value);
    }
    lookupAvailable.value = !!response.lookup_available;
    applyJourneys(response.journeys || []);
  } catch (error: any) {
    lookupError.value = error?.response?.data?.detail || "Nao foi possivel carregar os trechos.";
  } finally {
    loadingJourneys.value = false;
  }
};

const addSegment = async () => {
  if (!pageId.value || !sectionId.value || !activeJourney.value?.id) return;
  try {
    const response = await createFlightSegment(pageId.value, sectionId.value, {
      journey_id: activeJourney.value.id,
      source_mode: "manual",
      included_personal_item: true,
      included_carry_on: true,
      included_checked_bag: false
    });
    lookupAvailable.value = !!response.lookup_available;
    applyJourneys(response.journeys || []);
  } catch (error: any) {
    lookupError.value = error?.response?.data?.detail || "Nao foi possivel adicionar o trecho.";
  }
};

const removeSegment = async (segment: FlightSectionSegment) => {
  if (!pageId.value || !sectionId.value || !segment.id) return;
  try {
    const response = await deleteFlightSegment(pageId.value, sectionId.value, segment.id);
    lookupAvailable.value = !!response.lookup_available;
    applyJourneys(response.journeys || []);
  } catch (error: any) {
    lookupError.value = error?.response?.data?.detail || "Nao foi possivel excluir o trecho.";
  }
};

const moveSegment = async (index: number, direction: number) => {
  const journey = activeJourney.value;
  if (!journey?.id) return;
  const list = activeSegments.value.slice();
  const targetIndex = index + direction;
  if (targetIndex < 0 || targetIndex >= list.length) return;
  const tmp = list[index];
  list[index] = list[targetIndex];
  list[targetIndex] = tmp;
  const ids = list.map(item => item.id).filter(Boolean) as number[];
  if (!ids.length) return;
  try {
    const response = await reorderFlightSegments(pageId.value, sectionId.value, journey.id, ids);
    applyJourneys(response.journeys || []);
  } catch (error: any) {
    lookupError.value = error?.response?.data?.detail || "Nao foi possivel reordenar os trechos.";
  }
};

const saveSegment = async () => {
  if (!pageId.value || !sectionId.value || !selectedSegmentDraft.value || !selectedSegmentDraft.value.id) return;
  savingSegment.value = true;
  lookupError.value = "";
  try {
    const response = await updateFlightSegment(pageId.value, sectionId.value, selectedSegmentDraft.value.id, {
      ...selectedSegmentDraft.value,
      departure_datetime: fromDatetimeLocal(selectedSegmentDraft.value.departure_datetime),
      arrival_datetime: fromDatetimeLocal(selectedSegmentDraft.value.arrival_datetime)
    });
    lookupAvailable.value = !!response.lookup_available;
    applyJourneys(response.journeys || []);
  } catch (error: any) {
    lookupError.value = error?.response?.data?.detail || "Nao foi possivel salvar o trecho.";
  } finally {
    savingSegment.value = false;
  }
};

const runLookup = async (forceRefresh = false) => {
  if (!pageId.value || !sectionId.value || !lookupFlightNumber.value || !lookupFlightDate.value) return;
  lookupLoading.value = true;
  lookupState.value = "loading";
  lookupError.value = "";
  lookupMessage.value = "";
  lookupProviderInfo.value = "";
  try {
    const response = await lookupFlight(pageId.value, sectionId.value, {
      flight_number: lookupFlightNumber.value.trim().toUpperCase(),
      flight_date: lookupFlightDate.value,
      force_refresh: forceRefresh,
      preferred_provider: "aerodatabox",
      journey_id: activeJourney.value?.id,
      segment_id: selectedSegmentDraft.value?.id
    });
    if (response.from_cache) {
      lookupState.value = "cache";
      lookupMessage.value = "Dados carregados do cache. Nenhuma requisicao externa foi consumida.";
    } else if (response.fallback_used) {
      lookupState.value = "fallback";
      lookupMessage.value = "AeroDataBox falhou. Dados obtidos pelo provider fallback.";
    } else if (response.provider === "aerodatabox") {
      lookupState.value = "success";
      lookupMessage.value = "Dados encontrados via AeroDataBox.";
    } else {
      lookupState.value = "success";
      lookupMessage.value = response.message || "Consulta realizada com sucesso.";
    }
    if (response.provider === "aerodatabox" && (response.marketplace || "").toLowerCase() === "rapidapi") {
      lookupProviderInfo.value = "Provider: AeroDataBox via RapidAPI.";
    } else if (response.provider_message) {
      lookupProviderInfo.value = response.provider_message;
    }
    await reloadJourneys();
  } catch (error: any) {
    const status = Number(error?.response?.status || 0);
    lookupState.value = "error";
    lookupError.value =
      error?.response?.data?.detail ||
      "Nao foi possivel buscar automaticamente. Voce pode preencher manualmente.";
    if (status === 503) {
      await reloadJourneys();
    }
  } finally {
    lookupLoading.value = false;
  }
};

const parseDatetime = (value?: string | null) => {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
};

const layoverText = (index: number) => {
  const current = activeSegments.value[index];
  const next = activeSegments.value[index + 1];
  if (!current || !next) return "";
  const arrival = parseDatetime(current.arrival_datetime || null);
  const departure = parseDatetime(next.departure_datetime || null);
  if (!arrival || !departure) return "";
  const diffMinutes = Math.round((departure.getTime() - arrival.getTime()) / 60000);
  if (diffMinutes <= 0) return "";
  const hours = Math.floor(diffMinutes / 60);
  const minutes = diffMinutes % 60;
  const pieces = [];
  if (hours) pieces.push(`${hours}h`);
  if (minutes) pieces.push(`${minutes}min`);
  return `Espera de ${pieces.join(" ")} entre os voos`;
};

const segmentTitle = (segment: FlightSectionSegment, index: number) => {
  const number = segment.flight_number || segment.flight_iata || `Trecho ${index + 1}`;
  const airline = segment.airline_name || "Companhia nao informada";
  const from = segment.departure_airport_iata || "---";
  const to = segment.arrival_airport_iata || "---";
  return `${number} · ${airline} · ${from} -> ${to}`;
};

const toDatetimeLocal = (value?: string | null) => {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value).slice(0, 16);
  }
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  const hour = String(parsed.getHours()).padStart(2, "0");
  const minute = String(parsed.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:${minute}`;
};

const fromDatetimeLocal = (value?: string | null) => {
  if (!value) return null;
  const clean = String(value).trim();
  if (!clean) return null;
  return clean.length === 16 ? `${clean}:00` : clean;
};

watch(
  () => activeDirection.value,
  () => {
    const first = activeSegments.value[0] || null;
    setSelectedSegment(first);
  }
);

onMounted(async () => {
  await reloadJourneys();
});
</script>
