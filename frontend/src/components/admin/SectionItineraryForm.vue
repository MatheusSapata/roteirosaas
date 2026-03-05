<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <h3 class="text-lg font-semibold text-slate-900">Itinerário</h3>
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
    <div class="space-y-3">
      <div v-for="(day, index) in local.days" :key="index" class="grid gap-3 rounded-lg border border-slate-100 p-3 md:grid-cols-3">
        <input v-model="day.day" placeholder="Dia" class="rounded-lg border border-slate-200 px-3 py-2" />
        <input v-model="day.title" placeholder="Título" class="rounded-lg border border-slate-200 px-3 py-2" />
        <div class="md:col-span-3">
          <RichTextEditor v-model="day.description" placeholder="Descrição detalhada do dia" />
        </div>
        <div class="md:col-span-3">
          <ImageUploadField
            v-model="day.image"
            label="Imagem opcional"
            hint="Esta imagem aparece quando o visitante expande o dia."
          />
        </div>
        <button class="text-left text-sm text-red-500" @click="removeDay(index)">Remover</button>
      </div>
      <button class="text-sm font-semibold text-brand" @click="addDay">+ Adicionar dia</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { ItinerarySection } from "../../types/page";

const props = defineProps<{ modelValue: ItinerarySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ItinerarySection): void }>();
const headingDefaults = getSectionHeadingDefaults("itinerary");

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
const addDay = () => local.days.push({ day: "Dia", title: "", description: "", image: "" });
const removeDay = (index: number) => local.days.splice(index, 1);

watch(
  () => ({ ...local, days: local.days.map(day => ({ ...day })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as ItinerarySection);
  },
  { deep: true }
);
</script>
