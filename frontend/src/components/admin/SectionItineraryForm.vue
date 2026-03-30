<template>
  <div class="space-y-3 -mt-6">
    <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.fields.titleLabel }}</label>
          <input
            v-model="local.title"
            :placeholder="viewCopy.fields.titlePlaceholder"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.fields.subtitleLabel }}</label>
          <input
            v-model="local.subtitle"
            :placeholder="viewCopy.fields.subtitlePlaceholder"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
      </div>
    </div>
    <div class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="flex flex-wrap items-center gap-2">
        <div v-if="local.days.length" ref="dayChipsRef" class="flex flex-wrap items-center gap-2">
          <button
            v-for="(day, index) in local.days"
            :key="day.id || index"
            type="button"
            data-day-chip
            class="rounded-full border px-4 py-2 text-sm font-semibold transition cursor-grab active:cursor-grabbing"
            :class="selectedDayIndex === index ? 'border-brand bg-brand/10 text-brand' : 'border-slate-200 text-slate-500 hover:border-brand/60 hover:text-brand'"
            @click="selectedDayIndex = index"
          >
            {{ day.day || formatDayChipLabel(index + 1) }}
          </button>
        </div>
        <span v-else class="text-sm text-slate-500">{{ viewCopy.days.emptyMessage }}</span>
        <button class="text-sm font-semibold text-brand" type="button" @click="addDay">{{ viewCopy.days.addButton }}</button>
      </div>
      <p v-if="local.days.length" class="flex items-center gap-1 text-xs text-slate-400">
        <svg aria-hidden="true" class="h-4 w-4 text-slate-300" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v5" stroke-linecap="round" />
          <path d="M12 8h.01" stroke-linecap="round" />
        </svg>
        {{ viewCopy.days.reorderHint }}
      </p>
      <div v-if="currentDay" class="grid gap-3 rounded-lg border border-slate-100 p-3 md:grid-cols-2">
        <div class="space-y-3">
          <div class="grid gap-3 md:grid-cols-2">
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.days.dayLabel }}</label>
              <input
                v-model="currentDay.day"
                :placeholder="viewCopy.days.dayPlaceholder"
                class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.days.dayTitleLabel }}</label>
              <input
                v-model="currentDay.title"
                :placeholder="viewCopy.days.dayTitlePlaceholder"
                class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>
          </div>
          <div>
            <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.days.descriptionLabel }}</label>
            <div class="mt-1">
              <RichTextEditor
                :key="currentDay?.id || selectedDayIndex"
                v-model="currentDay.description"
                :placeholder="viewCopy.days.descriptionPlaceholder"
              />
            </div>
          </div>
        </div>
        <div>
          <div class="flex h-full flex-col justify-between space-y-2 rounded-lg border border-dashed border-slate-200 p-3">
            <div class="flex items-center justify-between text-sm font-semibold text-slate-600">
              <span>{{ viewCopy.days.imageLabel }}</span>
              <button
                v-if="currentDay.image"
                type="button"
                class="text-xs font-semibold uppercase tracking-wide text-rose-500 hover:text-rose-600"
                @click="removeDayImage(currentDay)"
              >
                {{ viewCopy.days.removeImage }}
              </button>
            </div>
            <ImageUploadField
              v-model="currentDay.image"
              label=""
              :hint="viewCopy.days.imageHint"
            />
          </div>
        </div>
        <button class="text-left text-sm text-red-500 md:col-span-2" type="button" @click="removeDay(selectedDayIndex)">
          {{ viewCopy.days.removeDayButton }}
        </button>
      </div>
      <div v-else class="rounded-lg border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
        {{ viewCopy.days.emptyStateHint }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import Sortable, { type SortableEvent } from "sortablejs";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { ItinerarySection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: ItinerarySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ItinerarySection): void }>();
const headingDefaults = getSectionHeadingDefaults("itinerary");
const t = createAdminLocalizer();

const viewCopy = {
  fields: {
    titleLabel: t({ pt: "Titulo", es: "Titulo" }),
    titlePlaceholder: t({ pt: "Dia a dia", es: "Dia a dia" }),
    subtitleLabel: t({ pt: "Subtitulo", es: "Subtitulo" }),
    subtitlePlaceholder: t({ pt: "Visao clara do roteiro completo", es: "Vision clara del itinerario completo" })
  },
  days: {
    emptyMessage: t({ pt: "Nenhum dia cadastrado.", es: "Ningun dia registrado." }),
    addButton: t({ pt: "+ Adicionar dia", es: "+ Agregar dia" }),
    reorderHint: t({ pt: "Arraste e solte os dias para reordenar.", es: "Arrastra y suelta los dias para reordenar." }),
    chipPrefix: t({ pt: "Dia", es: "Dia" }),
    dayLabel: t({ pt: "Dia", es: "Dia" }),
    dayPlaceholder: t({ pt: "Dia", es: "Dia" }),
    dayTitleLabel: t({ pt: "Titulo do dia", es: "Titulo del dia" }),
    dayTitlePlaceholder: t({ pt: "Titulo", es: "Titulo" }),
    descriptionLabel: t({ pt: "Descricao", es: "Descripcion" }),
    descriptionPlaceholder: t({ pt: "Descricao detalhada do dia", es: "Descripcion detallada del dia" }),
    imageLabel: t({ pt: "Imagem opcional", es: "Imagen opcional" }),
    removeImage: t({ pt: "Remover", es: "Eliminar" }),
    imageHint: t({
      pt: "Esta imagem aparece quando o visitante expande o dia.",
      es: "Esta imagen aparece cuando el visitante expande el dia."
    }),
    removeDayButton: t({ pt: "Remover este dia", es: "Eliminar este dia" }),
    emptyStateHint: t({
      pt: "Clique em \"+ Adicionar dia\" para comecar a montar o cronograma.",
      es: "Haz clic en \"+ Agregar dia\" para empezar a armar el cronograma."
    })
  }
};

const formatDayChipLabel = (index: number) => `${viewCopy.days.chipPrefix} ${index}`;

const selectedDayIndex = ref(0);
const dayChipsRef = ref<HTMLElement | null>(null);
let chipsSortable: Sortable | null = null;

const createDayId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
const normalizeDays = (days?: ItinerarySection["days"]): ItinerarySection["days"] => {
  if (!Array.isArray(days)) return [];
  return days.map(day => ({
    ...day,
    id: day.id || createDayId()
  }));
};
const createEmptyDay = () => ({
  id: createDayId(),
  day: "",
  title: "",
  description: "",
  image: ""
});

const local = reactive<ItinerarySection>({
  ...props.modelValue,
  layout: "timeline",
  enabled: true,
  fullWidth: false,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  days: normalizeDays(props.modelValue.days),
  title: props.modelValue.title ?? viewCopy.fields.titlePlaceholder,
  subtitle: props.modelValue.subtitle ?? viewCopy.fields.subtitlePlaceholder
});
const currentDay = computed(() => local.days[selectedDayIndex.value] || null);

function ensureSelectedDay() {
  if (!local.days.length) {
    selectedDayIndex.value = 0;
    return;
  }
  if (selectedDayIndex.value >= local.days.length) {
    selectedDayIndex.value = local.days.length - 1;
  }
  if (selectedDayIndex.value < 0) {
    selectedDayIndex.value = 0;
  }
}

let syncing = false;
const syncFromProps = (value: ItinerarySection) => {
  syncing = true;
  Object.assign(local, value);
  local.enabled = true;
  local.layout = "timeline";
  local.fullWidth = false;
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.days = normalizeDays(value.days);
  local.title = value.title ?? viewCopy.fields.titlePlaceholder;
  local.subtitle = value.subtitle ?? viewCopy.fields.subtitlePlaceholder;
  ensureSelectedDay();
  scheduleSortableRefresh();
  nextTick(() => {
    syncing = false;
  });
};

watch(
  () => props.modelValue,
  value => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);

const addDay = () => {
  local.days.push(createEmptyDay());
  selectedDayIndex.value = local.days.length - 1;
  ensureSelectedDay();
};

const removeDay = (index: number) => {
  if (index < 0 || index >= local.days.length) return;
  local.days.splice(index, 1);
  ensureSelectedDay();
};

const removeDayImage = (day: ItinerarySection["days"][number] | undefined) => {
  if (!day) return;
  day.image = "";
};

const updateSelectionAfterMove = (oldIndex: number, newIndex: number) => {
  if (selectedDayIndex.value === oldIndex) {
    selectedDayIndex.value = newIndex;
  } else if (selectedDayIndex.value > oldIndex && selectedDayIndex.value <= newIndex) {
    selectedDayIndex.value -= 1;
  } else if (selectedDayIndex.value < oldIndex && selectedDayIndex.value >= newIndex) {
    selectedDayIndex.value += 1;
  }
  ensureSelectedDay();
};

const reorderDays = (oldIndex: number, newIndex: number) => {
  if (oldIndex === newIndex) return;
  if (oldIndex < 0 || oldIndex >= local.days.length) return;
  const [movedDay] = local.days.splice(oldIndex, 1);
  if (!movedDay) return;
  const targetIndex = Math.min(Math.max(newIndex, 0), local.days.length);
  local.days.splice(targetIndex, 0, movedDay);
  updateSelectionAfterMove(oldIndex, targetIndex);
};

const handleDragEnd = (event: SortableEvent) => {
  if (typeof event.oldIndex !== "number" || typeof event.newIndex !== "number") return;
  reorderDays(event.oldIndex, event.newIndex);
};

const destroySortable = () => {
  if (chipsSortable) {
    chipsSortable.destroy();
    chipsSortable = null;
  }
};

function initSortable() {
  if (!dayChipsRef.value || local.days.length <= 1) {
    destroySortable();
    return;
  }
  destroySortable();
  chipsSortable = Sortable.create(dayChipsRef.value, {
    animation: 180,
    draggable: "button[data-day-chip]",
    ghostClass: "itinerary-chip-ghost",
    dragClass: "itinerary-chip-dragging",
    forceFallback: true,
    fallbackTolerance: 5,
    delayOnTouchOnly: true,
    delay: 120,
    swapThreshold: 0.45,
    onEnd: handleDragEnd
  });
}

function scheduleSortableRefresh() {
  nextTick(() => {
    initSortable();
  });
}

onMounted(() => {
  scheduleSortableRefresh();
});

onBeforeUnmount(() => {
  destroySortable();
});

watch(
  () => local.days.length,
  () => {
    scheduleSortableRefresh();
  }
);

watch(
  () => ({ ...local, days: local.days.map(day => ({ ...day })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as ItinerarySection);
  },
  { deep: true }
);
</script>

<style scoped>
.itinerary-chip-ghost {
  opacity: 0.5;
}

.itinerary-chip-dragging {
  cursor: grabbing !important;
}
</style>
