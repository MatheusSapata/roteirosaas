<template>
  <section class="rounded-lg border border-border bg-card p-5 text-card-foreground shadow-card">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <h3 class="font-display text-base font-semibold text-foreground">{{ title }}</h3>
        <p class="text-xs text-muted-foreground">{{ subtitle }}</p>
      </div>
      <div class="text-right">
        <p class="text-xs uppercase tracking-wide text-muted-foreground">Total</p>
        <p class="text-lg font-bold text-foreground">{{ total }}</p>
      </div>
    </div>

    <div v-if="points.length" class="relative h-56 w-full rounded-lg border border-border bg-muted p-3">
      <svg class="h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <linearGradient :id="`line-fill-${id}`" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="var(--chart-3)" stop-opacity="0.25" />
            <stop offset="100%" stop-color="var(--chart-3)" stop-opacity="0.02" />
          </linearGradient>
        </defs>
        <polyline
          fill="none"
          stroke="var(--chart-3)"
          stroke-width="2"
          :points="linePoints"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <polygon :points="areaPoints" :fill="`url(#line-fill-${id})`" />
      </svg>
      <div class="mt-2 flex items-center justify-between text-[11px] font-semibold text-muted-foreground">
        <span>{{ firstLabel }}</span>
        <span>{{ lastLabel }}</span>
      </div>
    </div>

    <div v-else class="flex h-56 items-center justify-center rounded-lg border border-border bg-muted text-sm text-muted-foreground">
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
