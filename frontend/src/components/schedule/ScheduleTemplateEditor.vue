<template>
  <section class="schedule-shell">
    <header class="schedule-header">
      <div>
        <h3 class="schedule-title">Agenda recorrente</h3>
        <p class="schedule-subtitle">Configure quando o produto terá saídas</p>
      </div>
      <div class="schedule-actions">
        <button type="button" class="btn-secondary" :disabled="loading" @click="$emit('generate')">
          Gerar saídas
        </button>
        <button type="button" class="btn-primary" :disabled="loading" @click="$emit('save', modelValue)">
          Salvar template
        </button>
      </div>
    </header>

    <article class="block-card">
      <h4 class="section-title">Tipo de recorrência</h4>
      <div class="segmented">
        <button
          type="button"
          class="segment-item"
          :class="modelValue.template_type === 'weekday' ? 'segment-item--active' : 'segment-item--inactive'"
          @click="modelValue.template_type = 'weekday'"
        >
          <strong>Dias da semana</strong>
          <span>Repete por padrão semanal</span>
        </button>
        <button
          type="button"
          class="segment-item"
          :class="modelValue.template_type === 'calendar' ? 'segment-item--active' : 'segment-item--inactive'"
          @click="modelValue.template_type = 'calendar'"
        >
          <strong>Datas específicas</strong>
          <span>Agenda por seleção no calendário</span>
        </button>
      </div>
    </article>

    <article class="block-card">
      <h4 class="section-title">Agenda</h4>

      <div v-if="modelValue.template_type === 'weekday'" class="space-y-4">
        <section class="sub-card">
          <h5>Dias ativos</h5>
          <WeekdaySelector v-model="modelValue.weekdays" />
        </section>

        <section class="sub-card">
          <h5>Horários</h5>
          <TimeSlotList
            v-model="modelValue.times"
            add-label="Adicionar horário"
            empty-title="Nenhum horário semanal cadastrado"
            empty-description="Adicione horários para começar a gerar as saídas recorrentes."
          />
        </section>
      </div>

      <div v-else class="sub-card">
        <h5>Calendário de datas</h5>
        <CalendarDateSelector v-model="modelValue.calendar_dates" />
      </div>
    </article>

    <article class="block-card">
      <h4 class="section-title">Configurações gerais</h4>
      <div class="config-grid">
        <label v-if="modelValue.template_type === 'weekday'" class="field">
          <span>Data inicial</span>
          <input v-model="modelValue.start_date" type="date" class="input" />
        </label>
        <label v-if="modelValue.template_type === 'weekday'" class="field">
          <span>Data final</span>
          <input v-model="modelValue.end_date" type="date" class="input" />
        </label>
        <label class="field">
          <span>Timezone</span>
          <input v-model="modelValue.timezone" class="input" placeholder="America/Sao_Paulo" />
        </label>
        <label class="field">
          <span>Horizonte de geração (dias)</span>
          <input v-model.number="modelValue.generation_horizon_days" type="number" min="1" max="365" class="input" />
        </label>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { ScheduleTemplatePayload } from "../../types/finance";
import CalendarDateSelector from "./CalendarDateSelector.vue";
import TimeSlotList from "./TimeSlotList.vue";
import WeekdaySelector from "./WeekdaySelector.vue";

defineProps<{
  modelValue: ScheduleTemplatePayload;
  loading?: boolean;
}>();

defineEmits<{
  (e: "save", payload: ScheduleTemplatePayload): void;
  (e: "generate"): void;
}>();
</script>

<style scoped>
.schedule-shell {
  @apply w-full space-y-8 rounded-3xl border border-slate-200 bg-white px-6 py-6 shadow-sm;
}

.schedule-header {
  @apply flex flex-col gap-3 md:flex-row md:items-center md:justify-between;
}

.schedule-title {
  @apply text-2xl font-semibold text-slate-900;
}

.schedule-subtitle {
  @apply mt-1 text-sm text-slate-500;
}

.schedule-actions {
  @apply flex flex-wrap items-center gap-2;
}

.btn-primary {
  @apply rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50;
}

.btn-secondary {
  @apply rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50;
}

.block-card {
  @apply space-y-4 rounded-2xl border border-slate-200 bg-slate-50/35 p-5;
}

.section-title {
  @apply text-sm font-semibold text-slate-700;
}

.segmented {
  @apply grid grid-cols-1 gap-2 md:grid-cols-2;
}

.segment-item {
  @apply flex flex-col items-start gap-1 rounded-xl border px-4 py-3 text-left transition;
}

.segment-item strong {
  @apply text-sm font-semibold;
}

.segment-item span {
  @apply text-xs;
}

.segment-item--active {
  @apply border-emerald-500 bg-emerald-500 text-white shadow-sm shadow-emerald-200;
}

.segment-item--inactive {
  @apply border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50;
}

.sub-card {
  @apply space-y-3 rounded-xl border border-slate-200 bg-white p-4;
}

.sub-card h5 {
  @apply text-sm font-medium text-slate-700;
}

.config-grid {
  @apply grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4;
}

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
