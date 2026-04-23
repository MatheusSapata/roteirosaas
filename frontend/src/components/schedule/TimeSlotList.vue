<template>
  <div class="space-y-3">
    <div v-if="!modelValue.length" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-6 text-center">
      <p class="text-sm font-semibold text-slate-700">{{ emptyTitle }}</p>
      <p class="mt-1 text-xs text-slate-500">{{ emptyDescription }}</p>
    </div>

    <div
      v-for="(entry, index) in modelValue"
      :key="`${index}-${entry.time}`"
      class="grid grid-cols-1 gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[minmax(0,1fr),auto] lg:items-end"
    >
      <label class="field">
        <span>Hora</span>
        <input :value="entry.time" type="time" class="input" @input="event => updateField(index, 'time', (event.target as HTMLInputElement).value)" />
      </label>

      <div class="flex items-end">
        <button
          type="button"
          class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 lg:w-auto"
          @click="remove(index)"
        >
          Remover
        </button>
      </div>
    </div>

    <button
      type="button"
      class="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
      @click="add"
    >
      <span class="text-base leading-none">+</span>
      {{ addLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { ScheduleTemplateCalendarDateTimePayload, ScheduleTemplateTimePayload } from "../../types/finance";

type TimeEntry = ScheduleTemplateTimePayload | ScheduleTemplateCalendarDateTimePayload;

const props = withDefaults(
  defineProps<{
    modelValue: TimeEntry[];
    showSortOrder?: boolean;
    addLabel?: string;
    emptyTitle?: string;
    emptyDescription?: string;
  }>(),
  {
    showSortOrder: true,
    addLabel: "Adicionar horario",
    emptyTitle: "Nenhum horario configurado",
    emptyDescription: "Adicione o primeiro horario para comecar.",
  },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: TimeEntry[]): void;
}>();

const add = () => {
  if (props.showSortOrder) {
    emit("update:modelValue", [
      ...props.modelValue,
      {
        time: "09:00",
        capacity_override: null,
        price_override: null,
        is_active: true,
        sort_order: props.modelValue.length,
      } as ScheduleTemplateTimePayload,
    ]);
    return;
  }

  emit("update:modelValue", [
    ...props.modelValue,
    {
      time: "09:00",
      capacity_override: null,
      price_override: null,
      is_active: true,
    } as ScheduleTemplateCalendarDateTimePayload,
  ]);
};

const remove = (index: number) => {
  const next = props.modelValue.slice();
  next.splice(index, 1);
  emit("update:modelValue", next);
};

const updateField = (index: number, field: "time", value: string) => {
  const next = props.modelValue.slice();
  next[index] = { ...next[index], [field]: value };
  emit("update:modelValue", next);
};
</script>

<style scoped>
.field {
  @apply flex flex-col gap-1;
}
.field > span {
  @apply text-xs font-medium text-slate-500;
}
.input {
  @apply w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700;
}
</style>
