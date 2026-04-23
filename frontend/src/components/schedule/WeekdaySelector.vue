<template>
  <div class="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
    <button
      v-for="item in weekdays"
      :key="item.value"
      type="button"
      class="day-chip"
      :class="isEnabled(item.value) ? 'day-chip--active' : 'day-chip--inactive'"
      @click="toggle(item.value)"
    >
      {{ item.short }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { ScheduleTemplateWeekdayPayload } from "../../types/finance";

const props = defineProps<{
  modelValue: ScheduleTemplateWeekdayPayload[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: ScheduleTemplateWeekdayPayload[]): void;
}>();

const weekdays = [
  { value: 0, short: "Seg" },
  { value: 1, short: "Ter" },
  { value: 2, short: "Qua" },
  { value: 3, short: "Qui" },
  { value: 4, short: "Sex" },
  { value: 5, short: "Sáb" },
  { value: 6, short: "Dom" },
];

const isEnabled = (weekday: number) =>
  props.modelValue.some(entry => entry.weekday === weekday && entry.is_enabled);

const toggle = (weekday: number) => {
  const map = new Map(props.modelValue.map(entry => [entry.weekday, { ...entry }]));
  const current = map.get(weekday);
  map.set(weekday, { weekday, is_enabled: !(current?.is_enabled ?? false) });
  emit("update:modelValue", weekdays.map(day => map.get(day.value) || { weekday: day.value, is_enabled: false }));
};
</script>

<style scoped>
.day-chip {
  @apply flex h-12 items-center justify-center rounded-xl border px-3 text-sm font-semibold transition;
}

.day-chip--active {
  @apply border-emerald-500 bg-emerald-500 text-white shadow-sm shadow-emerald-200;
}

.day-chip--inactive {
  @apply border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50;
}
</style>
