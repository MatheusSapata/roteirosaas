<template>
  <div class="acc">
    <div v-if="series.length > 1" class="acc-legend">
      <span v-for="(item, index) in series" :key="item.label" class="acc-key">
        <i :class="`acc-swatch is-${item.tone}`"></i>
        {{ item.label }} <b class="am-num">{{ format(totals[index]) }}</b>
      </span>
    </div>

    <div ref="host" class="acc-plot" :style="{ height: `${height}px` }" @mouseleave="active = null">
      <svg v-if="width" :width="width" :height="height" role="img" :aria-label="summary">
        <g>
          <line v-for="tick in ticks" :key="`grid-${tick}`" class="acc-grid" :x1="left" :x2="width" :y1="y(tick)" :y2="y(tick)" />
          <text v-for="tick in ticks" :key="`tick-${tick}`" class="acc-tick" :x="left - 8" :y="y(tick)" text-anchor="end" dominant-baseline="middle">
            {{ formatTick(tick) }}
          </text>
        </g>
        <rect
          v-if="active !== null"
          class="acc-hover"
          :x="left + active * band"
          :y="top"
          :width="band"
          :height="plotHeight"
          rx="6"
        />
        <g v-for="(point, index) in points" :key="point.key">
          <path v-for="segment in segments(index)" :key="segment.key" :d="segment.d" :class="`acc-bar is-${segment.tone}`" />
        </g>
        <text
          v-for="index in labelIndexes"
          :key="`label-${index}`"
          class="acc-tick"
          :x="left + index * band + band / 2"
          :y="height - 6"
          :text-anchor="index === 0 && points.length > 1 ? 'start' : index === points.length - 1 && points.length > 1 ? 'end' : 'middle'"
        >
          {{ points[index].label }}
        </text>
        <rect
          v-for="(point, index) in points"
          :key="`hit-${point.key}`"
          :x="left + index * band"
          :y="top"
          :width="band"
          :height="plotHeight + bottom"
          fill="transparent"
          @mouseenter="active = index"
          @focus="active = index"
        />
      </svg>
      <p v-if="isEmpty" class="acc-empty">{{ emptyText }}</p>
      <div v-if="active !== null && points[active]" class="acc-tip" :style="tipStyle">
        <p class="acc-tip-title">{{ points[active].title || points[active].label }}</p>
        <p v-for="(item, index) in series" :key="item.label" class="acc-tip-row">
          <i :class="`acc-swatch is-${item.tone}`"></i>{{ item.label }} <b class="am-num">{{ format(points[active].values[index] || 0) }}</b>
        </p>
        <p v-for="line in points[active].extra || []" :key="line" class="acc-tip-extra">{{ line }}</p>
      </div>
    </div>

    <table class="sr-only">
      <caption>{{ summary }}</caption>
      <thead>
        <tr>
          <th scope="col">Período</th>
          <th v-for="item in series" :key="item.label" scope="col">{{ item.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="point in points" :key="`row-${point.key}`">
          <th scope="row">{{ point.title || point.label }}</th>
          <td v-for="(item, index) in series" :key="item.label">{{ format(point.values[index] || 0) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

export interface ColumnPoint {
  key: string;
  /** Rótulo curto do eixo (ex.: 12/10). */
  label: string;
  /** Título da dica (ex.: 12/10 a 18/10). */
  title?: string;
  /** Um valor por série, empilhados de baixo para cima. */
  values: number[];
  /** Linhas a mais na dica. */
  extra?: string[];
}

const props = withDefaults(
  defineProps<{
    points: ColumnPoint[];
    series: Array<{ label: string; tone: "accent" | "muted" }>;
    format?: (value: number) => string;
    formatTick?: (value: number) => string;
    summary: string;
    height?: number;
    emptyText?: string;
  }>(),
  {
    format: (value: number) => new Intl.NumberFormat("pt-BR").format(value),
    formatTick: (value: number) => new Intl.NumberFormat("pt-BR", { notation: "compact" }).format(value),
    height: 230,
    emptyText: "Nada no período."
  }
);

const host = ref<HTMLElement | null>(null);
const width = ref(0);
const active = ref<number | null>(null);
let observer: ResizeObserver | null = null;
onMounted(() => {
  if (!host.value) return;
  width.value = host.value.clientWidth;
  observer = new ResizeObserver(entries => {
    width.value = Math.floor(entries[0]?.contentRect.width || 0);
  });
  observer.observe(host.value);
});
onBeforeUnmount(() => observer?.disconnect());

const top = 10;
const bottom = 26;
const plotHeight = computed(() => props.height - top - bottom);
const totals = computed(() => props.series.map((_, index) => props.points.reduce((sum, point) => sum + (point.values[index] || 0), 0)));
const maxTotal = computed(() => Math.max(0, ...props.points.map(point => point.values.reduce((sum, value) => sum + (value || 0), 0))));
const isEmpty = computed(() => maxTotal.value <= 0);

// Eixo com números redondos: passo 1, 2, 2,5 ou 5 vezes uma potência de 10.
const ticks = computed(() => {
  const max = maxTotal.value || 1;
  const raw = max / 4;
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map(factor => factor * power).find(candidate => candidate >= raw) || raw;
  const result: number[] = [];
  for (let value = 0; value <= max + step * 0.001; value += step) result.push(Number(value.toFixed(6)));
  if (result[result.length - 1] < max) result.push(Number((result[result.length - 1] + step).toFixed(6)));
  return result;
});
const scaleMax = computed(() => ticks.value[ticks.value.length - 1] || 1);
const left = computed(() => {
  const longest = Math.max(...ticks.value.map(tick => props.formatTick(tick).length));
  return Math.min(80, Math.max(28, longest * 6.6 + 12));
});
const band = computed(() => (props.points.length ? Math.max(1, (width.value - left.value) / props.points.length) : 0));
const barWidth = computed(() => Math.max(2, Math.min(24, band.value * 0.64)));
const y = (value: number) => top + plotHeight.value - (value / scaleMax.value) * plotHeight.value;

const roundedTop = (x: number, yTop: number, w: number, h: number) => {
  const r = Math.min(4, w / 2, h);
  const base = yTop + h;
  return `M${x},${base} L${x},${yTop + r} Q${x},${yTop} ${x + r},${yTop} L${x + w - r},${yTop} Q${x + w},${yTop} ${x + w},${yTop + r} L${x + w},${base} Z`;
};
const segments = (index: number) => {
  const point = props.points[index];
  const x = left.value + index * band.value + (band.value - barWidth.value) / 2;
  const visible = point.values.map((value, seriesIndex) => ({ value: value || 0, seriesIndex })).filter(item => item.value > 0);
  const result: Array<{ key: string; d: string; tone: string }> = [];
  let cursor = 0;
  visible.forEach((item, position) => {
    const bottomY = y(cursor);
    cursor += item.value;
    const isTop = position === visible.length - 1;
    // 2px de fundo entre as partes empilhadas.
    const topY = y(cursor) + (isTop ? 0 : 2);
    const h = Math.max(1, bottomY - topY);
    const tone = props.series[item.seriesIndex]?.tone || "accent";
    const d = isTop ? roundedTop(x, bottomY - h, barWidth.value, h) : `M${x},${bottomY} L${x},${bottomY - h} L${x + barWidth.value},${bottomY - h} L${x + barWidth.value},${bottomY} Z`;
    result.push({ key: `${point.key}-${item.seriesIndex}`, d, tone });
  });
  return result;
};

// Rótulos do eixo X: no máximo ~7, sempre o primeiro e o último.
const labelIndexes = computed(() => {
  const count = props.points.length;
  if (!count) return [];
  const room = Math.max(2, Math.floor((width.value - left.value) / 64));
  const every = Math.max(1, Math.ceil(count / Math.min(room, 7)));
  const indexes = new Set<number>([0, count - 1]);
  for (let index = every; index < count - 1; index += every) {
    // Pula o rótulo que ficaria colado no último.
    if (count - 1 - index >= every) indexes.add(index);
  }
  return [...indexes].sort((a, b) => a - b);
});

const tipStyle = computed(() => {
  if (active.value === null) return {};
  // Ao lado da coluna (à direita se couber), para não cobrir a coluna destacada.
  const center = left.value + active.value * band.value + band.value / 2;
  const tipWidth = 210;
  const gap = Math.max(10, barWidth.value / 2 + 8);
  const right = center + gap;
  const x = right + tipWidth <= width.value ? right : Math.max(0, center - gap - tipWidth);
  return { left: `${x}px`, top: `${top}px`, width: `${tipWidth}px` };
});
</script>

<style scoped>
.acc {
  --acc-accent: #059669;
  --acc-muted: #8a94a6;
  position: relative;
}
:global(html.dark) .acc {
  --acc-accent: #0fa877;
  --acc-muted: #64748b;
}
.acc-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-bottom: 10px;
  font-size: 12.5px;
  color: var(--muted-foreground);
}
.acc-key {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.acc-key b {
  color: var(--foreground);
  font-weight: 600;
}
.acc-swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  flex-shrink: 0;
  border-radius: 3px;
}
.acc-swatch.is-accent {
  background: var(--acc-accent);
}
.acc-swatch.is-muted {
  background: var(--acc-muted);
}
.acc-plot {
  position: relative;
  width: 100%;
}
.acc-plot svg {
  display: block;
  overflow: visible;
}
.acc-grid {
  stroke: var(--border);
  stroke-width: 1;
  shape-rendering: crispEdges;
}
.acc-tick {
  fill: var(--muted-foreground);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}
.acc-bar.is-accent {
  fill: var(--acc-accent);
}
.acc-bar.is-muted {
  fill: var(--acc-muted);
}
.acc-hover {
  fill: color-mix(in srgb, var(--muted) 70%, transparent);
}
.acc-empty {
  position: absolute;
  inset: 0 0 26px 0;
  display: grid;
  place-items: center;
  font-size: 13px;
  color: var(--muted-foreground);
  pointer-events: none;
}
.acc-tip {
  position: absolute;
  z-index: 5;
  padding: 9px 11px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
  font-size: 12px;
  line-height: 1.45;
  pointer-events: none;
}
.acc-tip-title {
  margin-bottom: 3px;
  font-weight: 600;
}
.acc-tip-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.acc-tip-row b {
  margin-left: auto;
  font-weight: 600;
}
.acc-tip-extra {
  color: var(--muted-foreground);
}
</style>
