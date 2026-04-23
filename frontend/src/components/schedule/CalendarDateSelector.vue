<template>
  <div class="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.3fr),minmax(0,1fr)]">
    <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="mb-4 flex items-center justify-between">
        <button type="button" class="month-nav" @click="changeMonth(-1)">‹</button>
        <div class="text-center">
          <p class="text-xs font-medium text-slate-500">Calendário</p>
          <h4 class="text-base font-semibold text-slate-900">{{ monthTitle }}</h4>
        </div>
        <button type="button" class="month-nav" @click="changeMonth(1)">›</button>
      </div>

      <div class="grid grid-cols-7 gap-1.5 text-center text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        <span v-for="day in weekHeader" :key="day">{{ day }}</span>
      </div>

      <div class="mt-2 grid grid-cols-7 gap-1.5">
        <button
          v-for="day in calendarDays"
          :key="day.key"
          type="button"
          :disabled="!day.inCurrentMonth"
          class="calendar-day"
          :class="dayClass(day)"
          @click="selectDay(day.dateString)"
        >
          <span>{{ day.dayNumber }}</span>
          <span v-if="hasDate(day.dateString)" class="calendar-day__dot"></span>
        </button>
      </div>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="mb-3 flex items-start justify-between gap-3">
        <div>
          <p class="text-xs font-medium text-slate-500">Data selecionada</p>
          <h4 class="text-base font-semibold text-slate-900">{{ selectedDateLabel }}</h4>
          <p class="text-xs text-slate-500">{{ selectedEntry ? "Horários configurados para esta data." : "Nenhum horário nesta data." }}</p>
        </div>
        <div class="flex gap-2">
          <button
            v-if="!selectedEntry"
            type="button"
            class="action-btn action-btn--add"
            @click="ensureSelectedDate"
          >
            Adicionar data
          </button>
          <button
            v-else
            type="button"
            class="action-btn action-btn--remove"
            @click="removeSelectedDate"
          >
            Remover data
          </button>
        </div>
      </div>

      <TimeSlotList
        :model-value="selectedEntry?.times || []"
        :show-sort-order="false"
        add-label="Adicionar horário para a data"
        empty-title="Sem horários para esta data"
        empty-description="Inclua horários para liberar saídas neste dia."
        @update:model-value="updateSelectedTimes"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { ScheduleTemplateCalendarDatePayload, ScheduleTemplateCalendarDateTimePayload } from "../../types/finance";
import TimeSlotList from "./TimeSlotList.vue";

type CalendarDay = {
  key: string;
  dateString: string;
  dayNumber: number;
  inCurrentMonth: boolean;
};

const props = defineProps<{
  modelValue: ScheduleTemplateCalendarDatePayload[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: ScheduleTemplateCalendarDatePayload[]): void;
}>();

const weekHeader = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const monthCursor = ref(new Date());
const selectedDate = ref(new Date().toISOString().slice(0, 10));

const toDateString = (value: Date) => {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const monthTitle = computed(() =>
  monthCursor.value.toLocaleDateString("pt-BR", { month: "long", year: "numeric" }),
);

const selectedDateLabel = computed(() => {
  const parsed = new Date(`${selectedDate.value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return selectedDate.value;
  return parsed.toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
});

const normalizedEntries = computed(() =>
  [...props.modelValue].sort((a, b) => a.date.localeCompare(b.date)),
);

const selectedEntry = computed(() =>
  normalizedEntries.value.find(entry => entry.date === selectedDate.value) || null,
);

const calendarDays = computed<CalendarDay[]>(() => {
  const firstDay = new Date(monthCursor.value.getFullYear(), monthCursor.value.getMonth(), 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const startDate = new Date(firstDay);
  startDate.setDate(firstDay.getDate() - startOffset);

  const days: CalendarDay[] = [];
  for (let idx = 0; idx < 42; idx += 1) {
    const current = new Date(startDate);
    current.setDate(startDate.getDate() + idx);
    days.push({
      key: `${toDateString(current)}-${idx}`,
      dateString: toDateString(current),
      dayNumber: current.getDate(),
      inCurrentMonth: current.getMonth() === monthCursor.value.getMonth(),
    });
  }
  return days;
});

const hasDate = (dateValue: string) => props.modelValue.some(entry => entry.date === dateValue);

const dayClass = (day: CalendarDay) => {
  if (!day.inCurrentMonth) return "calendar-day--out";
  if (day.dateString === selectedDate.value) return "calendar-day--selected";
  if (hasDate(day.dateString)) return "calendar-day--configured";
  return "calendar-day--default";
};

const changeMonth = (direction: number) => {
  const next = new Date(monthCursor.value);
  next.setMonth(monthCursor.value.getMonth() + direction);
  monthCursor.value = next;
};

const selectDay = (dateValue: string) => {
  selectedDate.value = dateValue;
};

const ensureSelectedDate = () => {
  if (selectedEntry.value) return;
  emit("update:modelValue", [
    ...props.modelValue,
    {
      date: selectedDate.value,
      is_active: true,
      times: [],
    },
  ]);
};

const removeSelectedDate = () => {
  emit(
    "update:modelValue",
    props.modelValue.filter(entry => entry.date !== selectedDate.value),
  );
};

const updateSelectedTimes = (value: ScheduleTemplateCalendarDateTimePayload[]) => {
  const hasCurrent = props.modelValue.some(entry => entry.date === selectedDate.value);
  if (!hasCurrent) {
    emit("update:modelValue", [
      ...props.modelValue,
      { date: selectedDate.value, is_active: true, times: value },
    ]);
    return;
  }
  emit(
    "update:modelValue",
    props.modelValue.map(entry =>
      entry.date === selectedDate.value
        ? { ...entry, times: value }
        : entry,
    ),
  );
};
</script>

<style scoped>
.month-nav {
  @apply h-9 w-9 rounded-full border border-slate-200 text-lg font-semibold text-slate-600 transition hover:bg-slate-50;
}

.calendar-day {
  @apply relative flex h-10 items-center justify-center rounded-xl border text-sm font-semibold transition;
}

.calendar-day--default {
  @apply border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50;
}

.calendar-day--configured {
  @apply border-emerald-200 bg-emerald-50/60 text-emerald-700 hover:border-emerald-300;
}

.calendar-day--selected {
  @apply border-emerald-500 bg-emerald-500 text-white shadow-sm shadow-emerald-200;
}

.calendar-day--out {
  @apply border-slate-100 bg-slate-50 text-slate-300;
}

.calendar-day__dot {
  @apply absolute bottom-1 h-1.5 w-1.5 rounded-full bg-current;
}

.action-btn {
  @apply rounded-xl px-3 py-2 text-xs font-semibold transition;
}

.action-btn--add {
  @apply border border-slate-300 bg-white text-slate-700 hover:bg-slate-50;
}

.action-btn--remove {
  @apply border border-rose-200 bg-white text-rose-600 hover:bg-rose-50;
}
</style>
