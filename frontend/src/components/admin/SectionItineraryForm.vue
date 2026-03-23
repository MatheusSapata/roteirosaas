<template>
  <div class="space-y-3 -mt-6">
    <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Título</label>
          <input v-model="local.title" placeholder="Dia a dia" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Subtítulo</label>
          <input
            v-model="local.subtitle"
            placeholder="Visão clara do roteiro completo"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
      </div>
    </div>
    <div class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="flex flex-wrap items-center gap-2">
        <template v-if="local.days.length">
          <button
            v-for="(day, index) in local.days"
            :key="index"
            class="rounded-full border px-4 py-2 text-sm font-semibold transition"
            :class="selectedDayIndex === index ? 'border-brand bg-brand/10 text-brand' : 'border-slate-200 text-slate-500 hover:border-brand/60 hover:text-brand'"
            @click="selectedDayIndex = index"
          >
            {{ day.day || `Dia ${index + 1}` }}
          </button>
        </template>
        <span v-else class="text-sm text-slate-500">Nenhum dia cadastrado.</span>
        <button class="text-sm font-semibold text-brand" @click="addDay">+ Adicionar dia</button>
      </div>
      <div v-if="currentDay" class="grid gap-3 rounded-lg border border-slate-100 p-3 md:grid-cols-2">
        <div class="space-y-3">
          <div class="grid gap-3 md:grid-cols-2">
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Dia</label>
              <input v-model="currentDay.day" placeholder="Dia" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Título do dia</label>
              <input v-model="currentDay.title" placeholder="Título" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
          </div>
          <div>
            <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Descrição</label>
            <div class="mt-1">
              <RichTextEditor :key="selectedDayIndex" v-model="currentDay.description" placeholder="Descrição detalhada do dia" />
            </div>
          </div>
        </div>
        <div>
          <div class="flex h-full flex-col justify-between space-y-2 rounded-lg border border-dashed border-slate-200 p-3">
            <div class="flex items-center justify-between text-sm font-semibold text-slate-600">
              <span>Imagem opcional</span>
              <button
                v-if="currentDay.image"
                type="button"
                class="text-xs font-semibold uppercase tracking-wide text-rose-500 hover:text-rose-600"
                @click="removeDayImage(currentDay)"
              >
                remover
              </button>
            </div>
            <ImageUploadField
              v-model="currentDay.image"
              label=""
              hint="Esta imagem aparece quando o visitante expande o dia."
            />
          </div>
        </div>
        <button class="text-left text-sm text-red-500 md:col-span-2" @click="removeDay(selectedDayIndex)">Remover este dia</button>
      </div>
      <div v-else class="rounded-lg border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
        Clique em "+ Adicionar dia" para come�ar a montar o cronograma.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { ItinerarySection } from "../../types/page";

const props = defineProps<{ modelValue: ItinerarySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ItinerarySection): void }>();
const headingDefaults = getSectionHeadingDefaults("itinerary");
const selectedDayIndex = ref(0);

const local = reactive<ItinerarySection>({
  ...props.modelValue,
  layout: "timeline",
  enabled: true,
  fullWidth: false,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  days: Array.isArray(props.modelValue.days) ? [...props.modelValue.days] : [],
  title: props.modelValue.title ?? "Dia a dia",
  subtitle: props.modelValue.subtitle ?? "Visão clara do roteiro completo."
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
  local.days = Array.isArray(value.days) ? value.days.map(day => ({ ...day })) : [];
  local.title = value.title ?? "Dia a dia";
  local.subtitle = value.subtitle ?? "Visão clara do roteiro completo.";
  ensureSelectedDay();
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
  local.days.push({ day: "", title: "", description: "", image: "" });
  selectedDayIndex.value = local.days.length - 1;
  ensureSelectedDay();
};
const removeDay = (index: number) => {
  local.days.splice(index, 1);
  ensureSelectedDay();
};
const removeDayImage = (day: ItinerarySection["days"][number]) => {
  day.image = "";
};

watch(
  () => ({ ...local, days: local.days.map(day => ({ ...day })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as ItinerarySection);
  },
  { deep: true }
);
</script>
