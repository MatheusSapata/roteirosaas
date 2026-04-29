<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_4px_18px_rgba(15,23,42,0.05)]">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <h3 class="text-base font-bold text-slate-900">{{ title }}</h3>
        <p class="text-xs text-slate-500">{{ subtitle }}</p>
      </div>
      <div class="text-right">
        <p class="text-xs uppercase tracking-wide text-slate-500">Total</p>
        <p class="text-lg font-bold text-slate-900">{{ total }}</p>
      </div>
    </div>

    <div v-if="points.length" class="relative h-56 w-full rounded-xl border border-slate-100 bg-slate-50/60 p-3">
      <svg class="h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <linearGradient :id="`line-fill-${id}`" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="#3B82F6" stop-opacity="0.25" />
            <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.02" />
          </linearGradient>
        </defs>
        <polyline
          fill="none"
          stroke="#3B82F6"
          stroke-width="2"
          :points="linePoints"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <polygon :points="areaPoints" :fill="`url(#line-fill-${id})`" />
      </svg>
      <div class="mt-2 flex items-center justify-between text-[11px] font-semibold text-slate-500">
        <span>{{ firstLabel }}</span>
        <span>{{ lastLabel }}</span>
      </div>
    </div>

    <div v-else class="flex h-56 items-center justify-center rounded-xl border border-slate-100 bg-slate-50 text-sm text-slate-500">
      Sem dados no período.
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

type ChartPoint = {
  label: string;
  value: number;
};

const props = defineProps<{
  id: string;
  title: string;
  subtitle: string;
  total: string;
  points: ChartPoint[];
}>();

const safeMax = computed(() => {
  const values = props.points.map(point => point.value);
  const max = Math.max(...values, 0);
  return max > 0 ? max : 1;
});

const linePoints = computed(() => {
  if (!props.points.length) return "";
  const step = props.points.length > 1 ? 100 / (props.points.length - 1) : 100;
  return props.points
    .map((point, index) => {
      const x = props.points.length > 1 ? index * step : 50;
      const y = 100 - (point.value / safeMax.value) * 90;
      return `${x},${y}`;
    })
    .join(" ");
});

const areaPoints = computed(() => {
  if (!props.points.length) return "";
  const firstX = props.points.length > 1 ? 0 : 50;
  const lastX = props.points.length > 1 ? 100 : 50;
  return `${linePoints.value} ${lastX},100 ${firstX},100`;
});

const firstLabel = computed(() => props.points[0]?.label || "");
const lastLabel = computed(() => props.points[props.points.length - 1]?.label || "");
</script>
