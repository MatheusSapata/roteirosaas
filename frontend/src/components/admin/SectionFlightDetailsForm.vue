<template>
  <div class="flight-shell">
    <aside class="flight-nav">
      <button type="button" class="flight-nav-item" :class="{ active: activeTab === 'text' }" @click="activeTab = 'text'">
        <span class="flight-nav-icon" v-html="adminTabIcons.text"></span>
        <span><strong>Textos</strong><small>Informações gerais</small></span>
      </button>
      <button type="button" class="flight-nav-item" :class="{ active: activeTab === 'outbound' }" @click="activeTab = 'outbound'">
        <span class="flight-nav-icon" v-html="adminTabIcons.flightOutbound"></span>
        <span><strong>Ida</strong><small>Trechos de ida</small></span>
      </button>
      <button type="button" class="flight-nav-item" :class="{ active: activeTab === 'inbound' }" @click="activeTab = 'inbound'">
        <span class="flight-nav-icon" :style="mirroredIconStyle" v-html="adminTabIcons.flightOutbound"></span>
        <span><strong>Volta</strong><small>Trechos de volta</small></span>
      </button>
    </aside>

    <section class="flight-content">
      <div v-if="activeTab === 'text'" class="p-0">
      <h4 class="flight-title">Textos da seção</h4>
      <p class="flight-subtitle">Configure os textos exibidos acima dos detalhes dos voos.</p>
      <div class="grid gap-3">
        <div>
          <label class="flight-field-title">
            Etiqueta acima do título
            <span class="flight-optional">opcional</span>
            <span class="flight-help">?</span>
          </label>
          <input
            v-model="local.headingLabel"
            class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Detalhes do voo"
          />
        </div>
        <div>
          <label class="flight-field-title">Título da seção <span class="flight-help">?</span></label>
          <input
            v-model="local.title"
            class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Informações do voo"
          />
        </div>
        <div>
          <label class="flight-field-title">Subtítulo <span class="flight-help">?</span></label>
          <input
            v-model="local.subtitle"
            class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            placeholder="Confira os detalhes dos voos inclusos no pacote"
          />
        </div>
      </div>
      <div class="mt-3">
        <label class="flight-field-title">Informações adicionais <span class="flight-help">?</span></label>
        <RichTextEditor
          v-model="local.generalInfo"
          class="mt-1 flight-rich"
          placeholder="Ex: regras de alteração, documentos obrigatórios, check-in."
        />
      </div>
      <p v-if="!lookupAvailable" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
        Busca automatica indisponivel. Preencha manualmente.
      </p>
    </div>

      <div v-if="activeTab !== 'text'" class="p-0">
      <div class="flight-head-row">
        <div>
          <h4 class="flight-title">{{ activeTab === "outbound" ? "Trechos de ida" : "Trechos de volta" }}</h4>
          <p class="flight-subtitle">
            {{ activeTab === "outbound" ? "Adicione, selecione e reordene os trechos de ida do pacote." : "Adicione, selecione e reordene os trechos de retorno da viagem." }}
          </p>
        </div>
        <button
          type="button"
          class="flight-add-segment"
          @click="addSegment"
        >
          + Adicionar trecho
        </button>
      </div>
      <div v-if="loadingJourneys" class="mt-4 text-sm text-slate-500">Carregando trechos...</div>
      <div v-else class="mt-4">
        <div class="segment-top-row">
          <div ref="segmentTabsRef" class="segment-tabs-wrap">
            <button
              v-for="(segment, index) in activeSegments"
              :key="segment.id || index"
              type="button"
              data-flight-segment-chip
              class="segment-pill"
              :class="{ active: selectedSegmentIndex === index }"
              @click="selectSegmentByIndex(index)"
            >
              <span class="segment-pill-handle">⋮⋮</span>
              <span>Trecho {{ index + 1 }}</span>
              <span class="segment-pill-remove" @click.stop="removeSegment(segment)">×</span>
            </button>
          </div>
        </div>
        <p v-if="!activeSegments.length" class="mt-3 rounded-xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
          Nenhum trecho cadastrado nesta jornada.
        </p>
      </div>
    </div>

      <div v-if="selectedSegmentDraft && activeTab !== 'text'" class="flight-selected-card p-0">
      <div class="flight-lookup-box mt-3 p-0">
        <div class="flight-lookup-head">
          <p class="flight-field-title">Buscar voo automaticamente</p>
          <button
            type="button"
            class="rounded border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 disabled:opacity-60"
            :disabled="lookupLoading || !lookupAvailable || !lookupFlightNumber || !lookupFlightDate"
            @click="runLookup(true)"
          >
            Atualizar dados pela API
          </button>
        </div>
        <div class="mt-2 grid gap-3 md:grid-cols-2">
          <div>
            <input
              v-model="lookupFlightNumber"
              class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              placeholder="Numero do voo"
            />
          </div>
          <div>
            <input v-model="lookupFlightDate" type="date" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Data do voo" />
          </div>
        </div>
        <button
          type="button"
          class="flight-search-btn mt-2 w-full rounded-lg bg-brand px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
          :disabled="lookupLoading || !lookupAvailable || !lookupFlightNumber || !lookupFlightDate"
          @click="runLookup(false)"
        >
          {{ lookupLoading ? "Buscando..." : "Buscar voo" }}
        </button>
      </div>

      <div class="flight-grid-2 mt-4 grid gap-3 md:grid-cols-2">
        <div>
          <label class="flight-field-title">Companhia aerea</label>
          <input v-model="selectedSegmentDraft.airline_name" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="flight-field-title">Numero do voo</label>
          <input v-model="selectedSegmentDraft.flight_number" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="flight-field-title">Origem</label>
          <input v-model="selectedSegmentDraft.departure_city" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="flight-field-title">Destino</label>
          <input v-model="selectedSegmentDraft.arrival_city" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="flight-field-title">Data e horário de saída</label>
          <input v-model="selectedSegmentDraft.departure_datetime" type="datetime-local" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="flight-field-title">Data e horário de chegada</label>
          <input v-model="selectedSegmentDraft.arrival_datetime" type="datetime-local" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="flight-field-title">Duracao</label>
          <input v-model.number="selectedSegmentDraft.duration_minutes" type="number" min="0" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="flight-field-title">Classe</label>
          <select v-model="selectedSegmentDraft.cabin_class" class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
            <option value="">Selecione</option>
            <option value="Econômica">Econômica</option>
            <option value="Premium Economy">Premium Economy</option>
            <option value="Executiva">Executiva</option>
            <option value="Primeira Classe">Primeira Classe</option>
          </select>
        </div>
      </div>

      <div class="mt-4">
        <p class="flight-field-title">Bagagens inclusas <span class="flight-help">?</span></p>
        <div class="flight-pill-row mt-2">
          <button type="button" class="flight-pill" :class="{ active: selectedSegmentDraft.included_personal_item }" @click="selectedSegmentDraft.included_personal_item = !selectedSegmentDraft.included_personal_item">
            Item pessoal
          </button>
          <button type="button" class="flight-pill" :class="{ active: selectedSegmentDraft.included_carry_on }" @click="selectedSegmentDraft.included_carry_on = !selectedSegmentDraft.included_carry_on">
            Bagagem de mão
          </button>
          <button type="button" class="flight-pill" :class="{ active: selectedSegmentDraft.included_checked_bag }" @click="selectedSegmentDraft.included_checked_bag = !selectedSegmentDraft.included_checked_bag">
            Bagagem despachada
          </button>
        </div>
      </div>

      <div class="mt-4">
        <label class="flight-field-title">Observacoes</label>
        <textarea
          v-model="selectedSegmentDraft.notes"
          rows="3"
          class="flight-input mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          placeholder="Campo opcional"
        ></textarea>
      </div>

      <div v-if="lookupToast.visible" class="flight-snackbar" :class="lookupToast.type === 'error' ? 'error' : 'success'">
        {{ lookupToast.message }}
      </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, defineExpose, onMounted, onBeforeUnmount, reactive, ref, watch, nextTick } from "vue";
import { useRoute } from "vue-router";
import Sortable, { type SortableEvent } from "sortablejs";
import type { FlightDetailsSection, FlightSectionJourney, FlightSectionSegment } from "../../types/page";
import AirlineLogo from "../shared/AirlineLogo.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import {
  bootstrapFlightJourneys,
  createFlightSegment,
  deleteFlightSegment,
  getFlightJourneys,
  lookupFlight,
  reorderFlightSegments,
  updateFlightSegment
} from "../../services/flightDetails";
import { adminTabIcons, mirroredIconStyle } from "../../utils/adminTabIcons";

const props = defineProps<{ modelValue: FlightDetailsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FlightDetailsSection): void }>();

const route = useRoute();
const pageId = computed(() => route.params.id as string);
const DEFAULT_VISUAL_STYLE: FlightDetailsSection["visualStyle"] = "decolar";
const normalizeLegacyLocalizedText = (value: unknown, fallback = "") => {
  if (typeof value === "string") return value;
  if (!value || typeof value !== "object") return fallback;
  const record = value as Record<string, unknown>;
  const preferredKeys = ["pt", "es"];
  for (const key of preferredKeys) {
    const candidate = record[key];
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate;
    }
  }
  for (const candidate of Object.values(record)) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate;
    }
  }
  return fallback;
};

const local = reactive<FlightDetailsSection>({
  ...props.modelValue,
  type: "flight_details",
  enabled: props.modelValue.enabled ?? true,
  title: props.modelValue.title || "Informações do voo",
  subtitle: props.modelValue.subtitle || "Confira os detalhes dos voos inclusos no pacote",
  generalInfo: normalizeLegacyLocalizedText(props.modelValue.generalInfo),
  ctaColor: props.modelValue.ctaColor || "",
  visualStyle: DEFAULT_VISUAL_STYLE,
  showOutbound: props.modelValue.showOutbound ?? true,
  showInbound: props.modelValue.showInbound ?? true,
  journeys: props.modelValue.journeys || [],
  sectionId: props.modelValue.sectionId || props.modelValue.anchorId || `flight-${Math.random().toString(36).slice(2, 10)}`
});

const loadingJourneys = ref(false);
const lookupAvailable = ref(Boolean(props.modelValue.lookupAvailable));
const activeDirection = ref<"outbound" | "inbound">("outbound");
const activeTab = ref<"text" | "outbound" | "inbound">("text");
const journeys = ref<FlightSectionJourney[]>(props.modelValue.journeys || []);
const selectedSegmentId = ref<number | null>(null);
const selectedSegmentIndex = ref<number | null>(null);
const selectedSegmentDraft = ref<FlightSectionSegment | null>(null);
const selectedSegmentBaseSnapshot = ref<string | null>(null);
const segmentTabsRef = ref<HTMLElement | null>(null);
let segmentsSortable: Sortable | null = null;
const lookupLoading = ref(false);
const lookupMessage = ref("");
const lookupError = ref("");
const lookupProviderInfo = ref("");
const lookupState = ref<"idle" | "loading" | "success" | "cache" | "fallback" | "error">("idle");
const lookupToast = ref<{ visible: boolean; message: string; type: "success" | "error" }>({
  visible: false,
  message: "",
  type: "success"
});
let lookupToastTimer: number | undefined;
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

const showLookupToast = (message: string, type: "success" | "error" = "success") => {
  if (!message) return;
  if (lookupToastTimer) window.clearTimeout(lookupToastTimer);
  lookupToast.value = { visible: true, message, type };
  lookupToastTimer = window.setTimeout(() => {
    lookupToast.value.visible = false;
  }, 3200);
};

const emitLocal = () => {
  emit("update:modelValue", {
    ...local,
    visualStyle: DEFAULT_VISUAL_STYLE,
    sectionId: local.sectionId,
    journeys: journeys.value,
    lookupAvailable: lookupAvailable.value
  });
};

const reorderActiveSegments = (from: number, to: number) => {
  const journey = activeJourney.value;
  if (!journey?.segments || from === to) return;
  const sorted = [...journey.segments].sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
  const moved = sorted.splice(from, 1)[0];
  if (!moved) return;
  sorted.splice(to, 0, moved);
  sorted.forEach((segment, index) => {
    segment.sort_order = index;
  });
  journey.segments = sorted;
  if (selectedSegmentIndex.value === from) selectedSegmentIndex.value = to;
  else if ((selectedSegmentIndex.value ?? -1) > from && (selectedSegmentIndex.value ?? -1) <= to) selectedSegmentIndex.value = (selectedSegmentIndex.value || 0) - 1;
  else if ((selectedSegmentIndex.value ?? -1) < from && (selectedSegmentIndex.value ?? -1) >= to) selectedSegmentIndex.value = (selectedSegmentIndex.value || 0) + 1;
  emitLocal();
};

const handleSegmentsDragEnd = (event: SortableEvent) => {
  const from = event.oldIndex;
  const to = event.newIndex;
  if (from === undefined || to === undefined) return;
  reorderActiveSegments(from, to);
};

const destroySortable = () => {
  if (!segmentsSortable) return;
  segmentsSortable.destroy();
  segmentsSortable = null;
};

const initSortable = () => {
  if (!segmentTabsRef.value || activeSegments.value.length <= 1 || activeTab.value === "text") {
    destroySortable();
    return;
  }
  destroySortable();
  segmentsSortable = Sortable.create(segmentTabsRef.value, {
    animation: 160,
    draggable: "button[data-flight-segment-chip]",
    handle: ".segment-pill-handle",
    onEnd: handleSegmentsDragEnd
  });
};

const scheduleSortableRefresh = () => nextTick(initSortable);

watch(
  () => props.modelValue,
  value => {
    local.enabled = value.enabled ?? true;
    local.title = value.title || "Informações do voo";
    local.subtitle = value.subtitle || "Confira os detalhes dos voos inclusos no pacote";
    local.generalInfo = normalizeLegacyLocalizedText(value.generalInfo);
    local.ctaColor = value.ctaColor || "";
    local.visualStyle = DEFAULT_VISUAL_STYLE;
    local.showOutbound = value.showOutbound ?? true;
    local.showInbound = value.showInbound ?? true;
    local.sectionId = value.sectionId || value.anchorId || local.sectionId || `flight-${Math.random().toString(36).slice(2, 10)}`;
    journeys.value = value.journeys || journeys.value;
    lookupAvailable.value = value.lookupAvailable ?? lookupAvailable.value;
  },
  { deep: true }
);

watch(
  () => [local.enabled, local.title, local.subtitle, local.generalInfo, local.ctaColor, local.showOutbound, local.showInbound, local.sectionId],
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
    selectedSegmentIndex.value = null;
    selectedSegmentDraft.value = null;
    selectedSegmentBaseSnapshot.value = null;
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
  selectedSegmentBaseSnapshot.value = serializeSegmentSnapshot(selectedSegmentDraft.value);
};

const selectSegment = (segmentId: number | null) => {
  if (!segmentId) {
    setSelectedSegment(null);
    return;
  }
  const target = activeSegments.value.find(segment => segment.id === segmentId) || null;
  selectedSegmentIndex.value = target ? activeSegments.value.findIndex(segment => segment.id === target.id) : null;
  setSelectedSegment(target);
};

const selectSegmentByIndex = (index: number) => {
  const target = activeSegments.value[index] || null;
  selectedSegmentIndex.value = target ? index : null;
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
      selectedSegmentIndex.value = activeSegments.value.findIndex(segment => segment.id === selected.id);
      setSelectedSegment(selected);
      emitLocal();
      return;
    }
  }
  const firstSegment = activeSegments.value[0] || null;
  selectedSegmentIndex.value = firstSegment ? 0 : null;
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
  if (!pageId.value || !sectionId.value || !selectedSegmentDraft.value || !selectedSegmentDraft.value.id) return false;
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
    return true;
  } catch (error: any) {
    lookupError.value = error?.response?.data?.detail || "Nao foi possivel salvar o trecho.";
    return false;
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
    showLookupToast([lookupMessage.value, lookupProviderInfo.value].filter(Boolean).join(" "), "success");
    await reloadJourneys();
  } catch (error: any) {
    const status = Number(error?.response?.status || 0);
    lookupState.value = "error";
    lookupError.value =
      error?.response?.data?.detail ||
      "Nao foi possivel buscar automaticamente. Voce pode preencher manualmente.";
    showLookupToast(lookupError.value, "error");
    if (status === 503) {
      await reloadJourneys();
    }
  } finally {
    lookupLoading.value = false;
  }
};

const parseFlightCivilDate = (value?: string | null) => {
  if (!value) return null;
  const raw = String(value).trim();
  if (!raw) return null;
  if (/[zZ]|[+-]\d{2}:\d{2}$/.test(raw)) {
    const parsed = new Date(raw);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }
  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})(?::(\d{2}))?/);
  if (!match) return null;
  const [, year, month, day, hour, minute, second] = match;
  const parsed = new Date(
    Number(year),
    Number(month) - 1,
    Number(day),
    Number(hour),
    Number(minute),
    Number(second || "0")
  );
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
};

const parseDatetime = (value?: string | null) => parseFlightCivilDate(value);

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
  return `${number} Â· ${airline} Â· ${from} -> ${to}`;
};

const toDatetimeLocal = (value?: string | null) => {
  if (!value) return "";
  const parsed = parseFlightCivilDate(value);
  if (!parsed || Number.isNaN(parsed.getTime())) {
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

const serializeSegmentSnapshot = (segment: FlightSectionSegment | null) => {
  if (!segment) return null;
  return JSON.stringify({
    flight_number: segment.flight_number || "",
    flight_iata: segment.flight_iata || "",
    flight_icao: segment.flight_icao || "",
    flight_date: segment.flight_date || "",
    airline_name: segment.airline_name || "",
    airline_iata: segment.airline_iata || "",
    airline_icao: segment.airline_icao || "",
    airline_logo_url: segment.airline_logo_url || "",
    departure_airport_iata: segment.departure_airport_iata || "",
    departure_airport_name: segment.departure_airport_name || "",
    departure_city: segment.departure_city || "",
    departure_country: segment.departure_country || "",
    departure_terminal: segment.departure_terminal || "",
    departure_gate: segment.departure_gate || "",
    departure_datetime: segment.departure_datetime || "",
    arrival_airport_iata: segment.arrival_airport_iata || "",
    arrival_airport_name: segment.arrival_airport_name || "",
    arrival_city: segment.arrival_city || "",
    arrival_country: segment.arrival_country || "",
    arrival_terminal: segment.arrival_terminal || "",
    arrival_gate: segment.arrival_gate || "",
    arrival_datetime: segment.arrival_datetime || "",
    duration_minutes: Number(segment.duration_minutes || 0),
    cabin_class: segment.cabin_class || "",
    status: segment.status || "",
    included_personal_item: segment.included_personal_item !== false,
    included_carry_on: segment.included_carry_on !== false,
    included_checked_bag: !!segment.included_checked_bag,
    notes: segment.notes || ""
  });
};

const hasUnsavedSegmentDraftChanges = () => {
  if (!selectedSegmentDraft.value || !selectedSegmentBaseSnapshot.value) return false;
  const currentSnapshot = serializeSegmentSnapshot(selectedSegmentDraft.value);
  return !!currentSnapshot && currentSnapshot !== selectedSegmentBaseSnapshot.value;
};

const savePendingSegmentDraft = async () => {
  if (!hasUnsavedSegmentDraftChanges()) return true;
  return await saveSegment();
};

defineExpose({
  hasUnsavedSegmentDraftChanges,
  savePendingSegmentDraft
});

watch(
  () => activeTab.value,
  value => {
    if (value === "outbound" || value === "inbound") {
      activeDirection.value = value;
    }
  }
);

watch(
  () => activeDirection.value,
  () => {
    if (activeDirection.value === "outbound" || activeDirection.value === "inbound") {
      activeTab.value = activeDirection.value;
    }
    const first = activeSegments.value[0] || null;
    setSelectedSegment(first);
    scheduleSortableRefresh();
  }
);

watch(
  () => [activeTab.value, activeSegments.value.length],
  () => scheduleSortableRefresh()
);

onMounted(async () => {
  await reloadJourneys();
  scheduleSortableRefresh();
});

onBeforeUnmount(() => {
  if (lookupToastTimer) window.clearTimeout(lookupToastTimer);
  destroySortable();
});
</script>

<style scoped>
.flight-shell {
  display: grid;
  grid-template-columns: 178px 1fr;
  height: 100%;
  min-height: 56vh;
}

.flight-nav {
  border-right: 1px solid #e6eee8;
  padding: 16px 12px 16px 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.flight-nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #d8dfda;
  border-radius: 14px;
  padding: 7px 9px;
  background: #eef2ef;
  color: #0f172a;
  text-align: left;
}

.flight-nav-item.active {
  border-color: #34c759;
  background: #34c759;
}

.flight-nav-icon {
  width: 22px;
  height: 22px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.flight-nav-icon svg {
  width: 13px;
  height: 13px;
}

.flight-nav-item strong {
  display: block;
  font-size: 16px;
  line-height: 0.95;
  font-weight: 700;
}

.flight-nav-item small {
  display: block;
  font-size: 10px;
  color: rgba(15, 23, 42, 0.55);
  font-weight: 600;
}

.flight-nav-item.active small {
  color: rgba(7, 82, 36, 0.78);
}

.flight-content {
  background: #f4f7f5;
  padding: 10px 14px;
  overflow-y: auto;
  display: grid;
  gap: 10px;
}

.flight-title {
  margin: 0 0 2px;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.flight-subtitle {
  margin: 0;
  color: #607284;
  font-size: 12px;
}

.flight-head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.flight-add-segment {
  border: 1px solid #cad7d1;
  border-radius: 999px;
  background: #fff;
  color: #475569;
  font-size: 11px;
  font-weight: 700;
  padding: 7px 11px;
}

.flight-lookup-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.flight-selected-card {
  background: #f8faf9;
}

.flight-selected-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.15;
}

.flight-field-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #748379;
  font-weight: 950;
}

.flight-optional {
  margin-left: auto;
  text-transform: none;
  letter-spacing: 0;
  font-size: 12px;
  color: #93a29a;
  font-weight: 700;
}

.flight-help {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 1px solid #d8e3dc;
  color: #9aaaa0;
  font-size: 9px;
  font-weight: 900;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.flight-rich :deep(.ql-toolbar.ql-snow) {
  border: 1px solid #dfe8e2 !important;
  border-bottom: 0 !important;
  border-radius: 10px 10px 0 0;
  background: #fbfdfc;
}

.flight-rich :deep(.ql-container.ql-snow) {
  border: 1px solid #dfe8e2 !important;
  border-radius: 0 0 10px 10px;
}

.flight-pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.flight-pill {
  border: 1px solid #dfe8e2;
  background: #fff;
  border-radius: 999px;
  padding: 8px 12px;
  color: #516358;
  font-size: 12px;
  font-weight: 850;
}

.flight-pill.active {
  background: #07111f;
  color: #fff;
  border-color: #07111f;
}

.flight-mini-label {
  font-size: 12px;
  color: #607284;
}

.flight-input {
  border-radius: 10px !important;
  border-color: #dfe8e2 !important;
}

.flight-search-btn {
  background: #35d467 !important;
  border-color: #35d467 !important;
  color: #073417 !important;
  font-size: 16px;
  line-height: 1;
  font-weight: 800;
  min-height: 40px;
}

.flight-grid-4 {
  align-items: end;
}

.flight-snackbar {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 60;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 10px 24px rgba(7, 17, 31, 0.2);
}

.flight-snackbar.success {
  background: #ecfdf3;
  color: #166534;
  border: 1px solid #86efac;
}

.flight-snackbar.error {
  background: #fff1f1;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.segment-tabs-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.segment-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.segment-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 1px solid #dfe8e2;
  background: #fff;
  border-radius: 999px;
  padding: 8px 10px;
  color: #516358;
  font-size: 12px;
  font-weight: 850;
}

.segment-pill.active {
  background: #f0fff5;
  color: #173b25;
  border-color: #35d467;
}

.segment-pill-handle {
  color: #9aaaa0;
  font-weight: 950;
  line-height: 1;
}

.segment-pill-remove {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #ffe8e8;
  color: #d93a3a;
  font-size: 12px;
  font-weight: 900;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

@media (max-width: 900px) {
  .flight-shell {
    grid-template-columns: 1fr;
    min-height: 100%;
    height: 100%;
    align-content: start;
    grid-auto-rows: min-content;
  }

  .flight-nav {
    border-right: 0;
    border-bottom: 0;
    padding: 8px 8px 8px 16px;
    margin-bottom: 8px;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 8px;
  }

  .flight-nav-item {
    min-width: 0;
    flex: 0 0 calc((100% - 16px) / 3);
    width: calc((100% - 16px) / 3);
    height: 40px;
    min-height: 40px;
    padding: 0 10px;
    gap: 8px;
    border-radius: 13px;
  }

  .flight-nav-icon {
    width: 20px;
    height: 20px;
    border-radius: 7px;
    font-size: 11px;
  }

  .flight-nav-item strong {
    font-size: 14px;
    line-height: 1;
  }

  .flight-nav-item small {
    display: none;
  }

  .flight-content {
    padding: 10px;
  }
}
</style>





