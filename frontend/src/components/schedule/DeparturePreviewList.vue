<template>
  <section class="departures-panel">
    <header class="departures-header">
      <div>
        <p class="departures-eyebrow">Gestao de agenda</p>
        <h3>Proximas saidas</h3>
      </div>
      <span class="departures-count">{{ departures.length }} saida(s)</span>
    </header>

    <div v-if="!departures.length" class="empty-state">
      <div class="empty-state__icon"></div>
      <p class="empty-state__title">Nenhuma saida gerada ainda</p>
      <p class="empty-state__desc">Clique em "Gerar saidas" para visualizar o calendario de operacao.</p>
    </div>

    <div v-else class="departures-layout">
      <section class="calendar-card">
        <div class="step-label">Passo 1 - Calendario</div>
        <div class="calendar-head">
          <button type="button" class="month-button" aria-label="Mes anterior" @click="changeMonth(-1)">
            &lt;
          </button>
          <div>
            <p class="calendar-month">{{ monthTitle }}</p>
            <span class="calendar-subtitle">{{ monthDepartureCount }} saida(s) no mes</span>
          </div>
          <button type="button" class="month-button" aria-label="Proximo mes" @click="changeMonth(1)">
            &gt;
          </button>
        </div>

        <div class="weekday-grid">
          <span v-for="day in weekHeader" :key="day">{{ day }}</span>
        </div>

        <div class="calendar-grid">
          <button
            v-for="cell in calendarCells"
            :key="cell.key"
            type="button"
            class="calendar-day"
            :class="dayClass(cell)"
            :disabled="cell.isBlank"
            @click="selectDate(cell.date)"
          >
            <span class="calendar-day__number">{{ cell.dayNumber }}</span>
            <span v-if="cell.departures.length > 1" class="calendar-day__badge">{{ cell.departures.length }}</span>
            <span v-else-if="cell.departures.length" class="calendar-day__dot"></span>
          </button>
        </div>

        <div class="calendar-legend">
          <span><i class="legend-dot legend-dot--active"></i>Com saida</span>
          <span><i class="legend-dot legend-dot--warning"></i>Quase lotado</span>
          <span><i class="legend-dot legend-dot--full"></i>Lotado</span>
        </div>
      </section>

      <section class="details-card">
        <div class="step-label">Passo 2 - Detalhes do dia</div>
        <transition name="details-fade" mode="out-in">
          <div :key="selectedDate || 'empty'">
            <div class="details-head">
              <div>
                <p class="details-date">{{ selectedDateLabel }}</p>
                <span class="details-summary">{{ selectedDepartures.length }} saida(s) no dia</span>
              </div>
              <span class="details-capacity">{{ selectedDaySold }}/{{ selectedDayCapacity }} vendidos</span>
            </div>

            <div v-if="!selectedDepartures.length" class="day-empty">
              <p>Nenhuma saida neste dia.</p>
              <span>Selecione uma data marcada no calendario para ver os horarios.</span>
            </div>

            <div v-else class="slot-list">
              <article v-for="item in selectedDepartures" :key="item.id" class="slot-card">
                <div class="slot-topline">
                  <strong>{{ formatTime(item.time) }}</strong>
                  <span class="status-pill" :class="statusClass(item)">{{ statusLabel(item) }}</span>
                </div>

                <div class="slot-progress">
                  <span :style="{ width: `${occupancyPercent(item)}%` }"></span>
                </div>

                <dl class="slot-metrics">
                  <div>
                    <dt>Vendidos</dt>
                    <dd>{{ item.capacity_sold }}/{{ item.capacity_total }}</dd>
                  </div>
                  <div>
                    <dt>Vagas</dt>
                    <dd>{{ Math.max(item.capacity_available || 0, 0) }}</dd>
                  </div>
                  <div>
                    <dt>Ocupacao</dt>
                    <dd>{{ occupancyPercent(item) }}%</dd>
                  </div>
                  <div>
                    <dt>Receita</dt>
                    <dd>{{ revenueLabel(item) }}</dd>
                  </div>
                </dl>
              </article>
            </div>
          </div>
        </transition>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { DepartureSummary } from "../../types/finance";

type CalendarCell = {
  key: string;
  date: string;
  dayNumber: number;
  isBlank: boolean;
  isCurrentMonth: boolean;
  departures: DepartureSummary[];
};

const props = defineProps<{
  departures: DepartureSummary[];
}>();

const weekHeader = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"];
const selectedDate = ref<string>("");
const monthCursor = ref(firstDayOfMonth(new Date()));

const sortedDepartures = computed(() =>
  [...props.departures].sort((left, right) => {
    const dateCompare = String(left.date).localeCompare(String(right.date));
    if (dateCompare !== 0) return dateCompare;
    return String(left.time).localeCompare(String(right.time));
  }),
);

const departuresByDate = computed(() => {
  const grouped = new Map<string, DepartureSummary[]>();
  for (const departure of sortedDepartures.value) {
    const key = normalizeDate(departure.date);
    if (!key) continue;
    const current = grouped.get(key) || [];
    current.push(departure);
    grouped.set(key, current);
  }
  return grouped;
});

const selectedDepartures = computed(() => departuresByDate.value.get(selectedDate.value) || []);
const selectedDaySold = computed(() => selectedDepartures.value.reduce((sum, item) => sum + Number(item.capacity_sold || 0), 0));
const selectedDayCapacity = computed(() => selectedDepartures.value.reduce((sum, item) => sum + Number(item.capacity_total || 0), 0));

const monthTitle = computed(() =>
  monthCursor.value.toLocaleDateString("pt-BR", { month: "long", year: "numeric" }),
);

const monthDepartureCount = computed(() =>
  sortedDepartures.value.filter(item => {
    const parsed = parseLocalDate(item.date);
    return parsed && parsed.getFullYear() === monthCursor.value.getFullYear() && parsed.getMonth() === monthCursor.value.getMonth();
  }).length,
);

const selectedDateLabel = computed(() => {
  if (!selectedDate.value) return "Selecione uma data";
  const parsed = parseLocalDate(selectedDate.value);
  if (!parsed) return selectedDate.value;
  return parsed.toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
  });
});

const calendarCells = computed<CalendarCell[]>(() => {
  const year = monthCursor.value.getFullYear();
  const month = monthCursor.value.getMonth();
  const first = new Date(year, month, 1);
  const startOffset = first.getDay();
  const start = new Date(first);
  start.setDate(first.getDate() - startOffset);
  const cells: CalendarCell[] = [];

  for (let index = 0; index < 42; index += 1) {
    const current = new Date(start);
    current.setDate(start.getDate() + index);
    const date = toDateString(current);
    const isCurrentMonth = current.getMonth() === month;
    cells.push({
      key: `${date}-${index}`,
      date,
      dayNumber: current.getDate(),
      isBlank: false,
      isCurrentMonth,
      departures: departuresByDate.value.get(date) || [],
    });
  }
  return cells;
});

watch(
  () => props.departures,
  () => {
    const first = sortedDepartures.value[0];
    if (!first) {
      selectedDate.value = "";
      monthCursor.value = firstDayOfMonth(new Date());
      return;
    }
    const currentStillExists = selectedDate.value && departuresByDate.value.has(selectedDate.value);
    const nextDate = currentStillExists ? selectedDate.value : normalizeDate(first.date);
    selectedDate.value = nextDate;
    const parsed = parseLocalDate(nextDate);
    if (parsed) monthCursor.value = firstDayOfMonth(parsed);
  },
  { immediate: true, deep: true },
);

function firstDayOfMonth(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), 1);
}

function parseLocalDate(raw: string) {
  const normalized = normalizeDate(raw);
  if (!normalized) return null;
  const [year, month, day] = normalized.split("-").map(Number);
  const parsed = new Date(year, month - 1, day);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function normalizeDate(raw: string) {
  if (!raw) return "";
  return String(raw).slice(0, 10);
}

function toDateString(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function changeMonth(direction: number) {
  const next = new Date(monthCursor.value);
  next.setMonth(monthCursor.value.getMonth() + direction);
  monthCursor.value = firstDayOfMonth(next);
}

function selectDate(date: string) {
  selectedDate.value = date;
}

function formatTime(raw: string) {
  return String(raw || "").slice(0, 5);
}

function occupancyPercent(item: DepartureSummary) {
  const total = Number(item.capacity_total || 0);
  if (total <= 0) return 0;
  return Math.max(0, Math.min(100, Math.round((Number(item.capacity_sold || 0) / total) * 100)));
}

function dayTone(departures: DepartureSummary[]) {
  if (!departures.length) return "empty";
  if (departures.some(item => item.status === "canceled" || item.status === "closed")) return "closed";
  if (departures.every(item => item.status === "full" || occupancyPercent(item) >= 100 || Number(item.capacity_available || 0) <= 0)) return "full";
  if (departures.some(item => occupancyPercent(item) >= 80 || Number(item.capacity_available || 0) <= 5)) return "warning";
  return "active";
}

function statusTone(item: DepartureSummary) {
  if (item.status === "canceled" || item.status === "closed") return "closed";
  if (item.status === "full" || occupancyPercent(item) >= 100 || Number(item.capacity_available || 0) <= 0) return "full";
  if (occupancyPercent(item) >= 80 || Number(item.capacity_available || 0) <= 5) return "warning";
  if (item.status === "active") return "active";
  return "draft";
}

function statusLabel(item: DepartureSummary) {
  const tone = statusTone(item);
  if (tone === "active") return "Ativa";
  if (tone === "warning") return "Quase lotado";
  if (tone === "full") return "Lotado";
  if (tone === "closed") return item.status === "canceled" ? "Cancelada" : "Fechada";
  return "Rascunho";
}

function statusClass(item: DepartureSummary) {
  return `status-pill--${statusTone(item)}`;
}

function dayClass(cell: CalendarCell) {
  return {
    "calendar-day--muted": !cell.isCurrentMonth,
    "calendar-day--selected": cell.date === selectedDate.value,
    [`calendar-day--${dayTone(cell.departures)}`]: cell.departures.length > 0 && cell.date !== selectedDate.value,
  };
}

function revenueLabel(item: DepartureSummary) {
  const price = item.price_override;
  if (price === null || price === undefined) return "Nao informado";
  const amount = Number(item.capacity_sold || 0) * Number(price || 0);
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(amount / 100);
}
</script>

<style scoped>
.departures-panel {
  border: 1px solid #e2e8f0;
  border-radius: 28px;
  background: #ffffff;
  padding: 1.35rem;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
}

.departures-header,
.calendar-head,
.details-head,
.slot-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.departures-header {
  margin-bottom: 1rem;
}

.departures-eyebrow,
.step-label {
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.departures-header h3 {
  margin-top: 0.2rem;
  color: #0f172a;
  font-size: 1.15rem;
  font-weight: 800;
}

.departures-count {
  border: 1px solid #dbe4ef;
  border-radius: 999px;
  background: #f8fafc;
  padding: 0.55rem 0.85rem;
  color: #334155;
  font-size: 0.78rem;
  font-weight: 800;
}

.departures-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(340px, 0.92fr);
  gap: 1rem;
}

.calendar-card,
.details-card,
.empty-state {
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  padding: 1rem;
}

.calendar-head {
  margin-top: 0.85rem;
  border-radius: 20px;
  background: #f8fafc;
  padding: 0.8rem;
}

.month-button {
  display: inline-flex;
  width: 2.5rem;
  height: 2.5rem;
  align-items: center;
  justify-content: center;
  border: 1px solid #dbe4ef;
  border-radius: 999px;
  background: #ffffff;
  color: #0f172a;
  font-size: 1.45rem;
  line-height: 1;
  transition: all 0.18s ease;
}

.month-button:hover {
  border-color: #0f172a;
  transform: translateY(-1px);
}

.calendar-month {
  color: #0f172a;
  font-size: 1rem;
  font-weight: 800;
  text-align: center;
  text-transform: capitalize;
}

.calendar-subtitle {
  display: block;
  margin-top: 0.15rem;
  color: #64748b;
  font-size: 0.78rem;
  font-weight: 700;
  text-align: center;
}

.weekday-grid,
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.45rem;
}

.weekday-grid {
  margin-top: 0.9rem;
  color: #94a3b8;
  font-size: 0.72rem;
  font-weight: 800;
  text-align: center;
}

.calendar-grid {
  margin-top: 0.45rem;
}

.calendar-day {
  position: relative;
  min-height: 4rem;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #ffffff;
  color: #334155;
  font-weight: 800;
  transition: all 0.18s ease;
}

.calendar-day:hover:not(:disabled) {
  border-color: #94a3b8;
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.calendar-day--muted {
  background: #f8fafc;
  color: #cbd5e1;
}

.calendar-day--active {
  border-color: #bbf7d0;
  background: #ecfdf5;
  color: #047857;
}

.calendar-day--warning {
  border-color: #fde68a;
  background: #fffbeb;
  color: #b45309;
}

.calendar-day--full {
  border-color: #fecaca;
  background: #fff1f2;
  color: #be123c;
}

.calendar-day--closed {
  border-color: #cbd5e1;
  background: #f1f5f9;
  color: #475569;
}

.calendar-day--selected {
  border-color: #0f172a;
  background: #0f172a;
  color: #ffffff;
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.2);
}

.calendar-day__number {
  position: absolute;
  left: 0.65rem;
  top: 0.55rem;
}

.calendar-day__dot {
  position: absolute;
  left: 50%;
  bottom: 0.65rem;
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 999px;
  background: currentColor;
  transform: translateX(-50%);
}

.calendar-day__badge {
  position: absolute;
  right: 0.45rem;
  bottom: 0.45rem;
  min-width: 1.4rem;
  border-radius: 999px;
  background: #0f172a;
  color: #ffffff;
  font-size: 0.72rem;
  line-height: 1.4rem;
}

.calendar-day--selected .calendar-day__badge {
  background: #ffffff;
  color: #0f172a;
}

.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
  color: #64748b;
  font-size: 0.76rem;
  font-weight: 700;
}

.calendar-legend span,
.status-pill {
  display: inline-flex;
  align-items: center;
}

.legend-dot {
  width: 0.55rem;
  height: 0.55rem;
  margin-right: 0.35rem;
  border-radius: 999px;
}

.legend-dot--active {
  background: #10b981;
}

.legend-dot--warning {
  background: #f59e0b;
}

.legend-dot--full {
  background: #ef4444;
}

.details-card {
  min-height: 100%;
}

.details-head {
  margin-top: 0.85rem;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 1rem;
}

.details-date {
  color: #0f172a;
  font-size: 1.2rem;
  font-weight: 900;
  text-transform: capitalize;
}

.details-summary {
  display: block;
  margin-top: 0.25rem;
  color: #64748b;
  font-size: 0.88rem;
  font-weight: 700;
}

.details-capacity {
  border-radius: 999px;
  background: #eef2ff;
  padding: 0.55rem 0.8rem;
  color: #1e3a8a;
  font-size: 0.78rem;
  font-weight: 900;
  white-space: nowrap;
}

.slot-list {
  display: grid;
  gap: 0.85rem;
  margin-top: 1rem;
}

.slot-card {
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  background: #ffffff;
  padding: 1rem;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
  transition: all 0.18s ease;
}

.slot-card:hover {
  border-color: #cbd5e1;
  transform: translateY(-1px);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.08);
}

.slot-topline strong {
  color: #0f172a;
  font-size: 1.35rem;
  font-weight: 900;
}

.status-pill {
  border-radius: 999px;
  padding: 0.45rem 0.7rem;
  font-size: 0.72rem;
  font-weight: 900;
}

.status-pill--active {
  background: #dcfce7;
  color: #047857;
}

.status-pill--warning {
  background: #fef3c7;
  color: #b45309;
}

.status-pill--full {
  background: #ffe4e6;
  color: #be123c;
}

.status-pill--closed {
  background: #e2e8f0;
  color: #334155;
}

.status-pill--draft {
  background: #dbeafe;
  color: #1d4ed8;
}

.slot-progress {
  overflow: hidden;
  height: 0.55rem;
  margin-top: 0.85rem;
  border-radius: 999px;
  background: #e2e8f0;
}

.slot-progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #10b981, #0f766e);
}

.slot-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.slot-metrics div {
  border-radius: 14px;
  background: #f8fafc;
  padding: 0.75rem;
}

.slot-metrics dt {
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
}

.slot-metrics dd {
  margin-top: 0.2rem;
  color: #0f172a;
  font-size: 0.92rem;
  font-weight: 900;
}

.day-empty,
.empty-state {
  text-align: center;
}

.day-empty {
  margin-top: 1rem;
  border: 1px dashed #cbd5e1;
  border-radius: 20px;
  background: #f8fafc;
  padding: 2rem 1rem;
}

.day-empty p,
.empty-state__title {
  color: #0f172a;
  font-weight: 900;
}

.day-empty span,
.empty-state__desc {
  display: block;
  margin-top: 0.35rem;
  color: #64748b;
  font-size: 0.86rem;
}

.empty-state {
  padding: 2.5rem 1rem;
}

.empty-state__icon {
  width: 3rem;
  height: 3rem;
  margin: 0 auto 1rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #e2e8f0, #f8fafc);
}

.details-fade-enter-active,
.details-fade-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.details-fade-enter-from,
.details-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

@media (max-width: 1024px) {
  .departures-layout {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 640px) {
  .departures-panel {
    padding: 0.75rem;
    border-radius: 20px;
  }

  .departures-header,
  .details-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .calendar-card,
  .details-card {
    border-radius: 20px;
    padding: 0.75rem;
  }

  .step-label {
    font-size: 0.66rem;
    letter-spacing: 0.13em;
  }

  .calendar-head {
    margin-top: 0.65rem;
    padding: 0.65rem;
    border-radius: 18px;
  }

  .month-button {
    width: 2.15rem;
    height: 2.15rem;
    font-size: 1.15rem;
    flex: 0 0 auto;
  }

  .calendar-month {
    font-size: 0.95rem;
  }

  .calendar-subtitle {
    font-size: 0.72rem;
  }

  .weekday-grid,
  .calendar-grid {
    gap: 0.35rem;
  }

  .weekday-grid {
    font-size: 0.65rem;
  }

  .calendar-day {
    min-height: 2.95rem;
    border-radius: 12px;
    font-size: 0.78rem;
  }

  .calendar-day__number {
    left: 0.5rem;
    top: 0.45rem;
  }

  .calendar-day__badge {
    right: 0.35rem;
    bottom: 0.35rem;
    min-width: 1.25rem;
    font-size: 0.65rem;
    line-height: 1.25rem;
  }

  .calendar-day__dot {
    bottom: 0.5rem;
  }

  .calendar-legend {
    gap: 0.5rem;
    font-size: 0.68rem;
  }

  .slot-metrics {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 420px) {
  .departures-panel {
    padding: 0.6rem;
  }

  .calendar-card,
  .details-card {
    padding: 0.65rem;
  }

  .weekday-grid,
  .calendar-grid {
    gap: 0.28rem;
  }

  .calendar-day {
    min-height: 2.55rem;
    border-radius: 10px;
    font-size: 0.72rem;
  }

  .calendar-day__number {
    left: 0.42rem;
    top: 0.35rem;
  }

  .calendar-day__badge {
    min-width: 1.1rem;
    font-size: 0.6rem;
    line-height: 1.1rem;
  }
}
</style>
