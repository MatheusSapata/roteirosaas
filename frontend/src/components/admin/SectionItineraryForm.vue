<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Itinerário</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>
    <div class="space-y-3">
      <div v-for="(day, index) in local.days" :key="index" class="grid gap-3 rounded-lg border border-slate-100 p-3 md:grid-cols-3">
        <input v-model="day.day" placeholder="Dia" class="rounded-lg border border-slate-200 px-3 py-2" />
        <input v-model="day.title" placeholder="Título" class="rounded-lg border border-slate-200 px-3 py-2" />
        <textarea v-model="day.description" placeholder="Descrição" class="rounded-lg border border-slate-200 px-3 py-2 md:col-span-3"></textarea>
        <button class="text-left text-sm text-red-500" @click="removeDay(index)">Remover</button>
      </div>
      <button class="text-sm font-semibold text-brand" @click="addDay">+ Adicionar dia</button>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Layout</label>
        <select v-model="local.layout" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="timeline">Timeline</option>
          <option value="cards">Cards</option>
          <option value="minimal">Minimalista</option>
          <option value="steps">Passos (horizontal)</option>
        </select>
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor de fundo</label>
        <select v-model="local.backgroundColor" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option v-for="option in colorOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.fullWidth" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Ocupar largura total</label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import type { ItinerarySection } from "../../types/page";

const props = defineProps<{ modelValue: ItinerarySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ItinerarySection): void }>();

const local = reactive<ItinerarySection>({
  layout: "timeline",
  ...props.modelValue,
  days: Array.isArray(props.modelValue.days) ? [...props.modelValue.days] : []
});
let syncing = false;
const syncFromProps = (value: ItinerarySection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = value.layout || "timeline";
  local.days = Array.isArray(value.days) ? value.days.map(day => ({ ...day })) : [];
  syncing = false;
};

watch(
  () => props.modelValue,
  value => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);
const colorOptions = [
  { label: "Branco", value: "#ffffff" },
  { label: "Cinza suave", value: "#f8fafc" },
  { label: "Azul claro", value: "#e0f2fe" },
  { label: "Marfim", value: "#fef3c7" },
  { label: "Rosa claro", value: "#fdf2f8" },
  { label: "Verde menta", value: "#ecfdf3" },
  { label: "Lilás", value: "#f5f3ff" },
  { label: "Turquesa", value: "#e0f7f7" },
  { label: "Cinza médio", value: "#e2e8f0" },
  { label: "Grafite", value: "#0f172a" }
];

const addDay = () => local.days.push({ day: "Dia", title: "", description: "" });
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
