<template>
  <V2Section type="countdown" :background="background" :anchor-id="section.anchorId" flush>
    <div v-if="isBar" role="timer" :aria-label="ariaLabel" class="v2-cd-bar">
      <span v-if="label" class="v2-cd-text"><span class="v2-cd-dot" aria-hidden="true"></span>{{ label }}</span>
      <span class="v2-cd-mini">
        <span v-for="part in parts" :key="part.short"><b>{{ part.value }}</b>{{ part.short }}</span>
      </span>
    </div>
    <div v-else class="v2-cd">
      <div class="v2-cd-copy v2-in">
        <span v-if="eyebrow" class="v2-cd-pill"><span class="v2-cd-dot" aria-hidden="true"></span>{{ eyebrow }}</span>
        <h2 v-if="label" class="v2-title" :style="titleScaleStyle(label)">{{ label }}</h2>
      </div>
      <div role="timer" :aria-label="ariaLabel" class="v2-cd-tiles v2-in v2-d2">
        <template v-for="(part, idx) in parts" :key="part.short">
          <span v-if="idx" class="v2-cd-sep" aria-hidden="true">:</span>
          <span class="v2-cd-unit">
            <span class="v2-cd-tile"><b :key="part.value" :class="{ 'v2-cd-tick': idx === 3 }">{{ part.value }}</b></span>
            <span class="v2-cd-label">{{ part.label }}</span>
          </span>
        </template>
      </div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { CountdownSection } from "../../../types/page";
import V2Section from "./V2Section.vue";
import { usePageDesignContext } from "./designContext";
import { localize, text } from "./useHeading";
import { titleScaleStyle } from "./useCopyFit";
import { resolveHeadingLabel } from "../../../utils/sectionHeadings";

const props = defineProps<{ section: CountdownSection; previewDevice?: "desktop" | "mobile" }>();
const design = usePageDesignContext();
const copy = {
  aria: { pt: "Tempo restante", es: "Tiempo restante" },
  days: { pt: "DIAS", es: "DÍAS" },
  hours: { pt: "HORAS", es: "HORAS" },
  minutes: { pt: "MIN", es: "MIN" },
  seconds: { pt: "SEG", es: "SEG" }
} as const;

const isBar = computed(() => props.section.layout === "bar");
const background = computed(() => props.section.backgroundColor || design.value.accent);
// Só o que está salvo: selo e texto vazios ficam vazios, como na seção antiga.
const eyebrow = computed(() => resolveHeadingLabel(props.section.headingLabel, "", localize));
const label = computed(() => text(props.section.label));
const ariaLabel = localize(copy.aria);

// Mesma regra das seções antigas: data fixa, ou um prazo por visita; prazo vencido vira 3 dias.
const unitToMs = (unit: CountdownSection["sessionUnit"], amount: number) =>
  unit === "days" ? amount * 86400000 : unit === "hours" ? amount * 3600000 : amount * 60000;
const sessionTarget = ref<number | null>(null);
const resetSession = () => {
  sessionTarget.value =
    props.section.countdownMode === "session"
      ? Date.now() + unitToMs(props.section.sessionUnit || "minutes", Math.max(1, Math.round(props.section.sessionDuration || 15)))
      : null;
};
const fixedTarget = computed(() => {
  const raw = props.section.targetDate;
  if (!raw) return null;
  const parsed = Date.parse(raw.includes("T") ? raw : raw.replace(" ", "T"));
  return Number.isNaN(parsed) ? null : parsed;
});
const now = ref(Date.now());
const target = computed(() => {
  if (sessionTarget.value) return sessionTarget.value;
  const fixed = fixedTarget.value;
  return fixed && fixed > now.value ? fixed : now.value + 3 * 86400000;
});
const pad = (n: number) => String(n).padStart(2, "0");
const parts = computed(() => {
  const total = Math.max(0, Math.floor((target.value - now.value) / 1000));
  return [
    { label: localize(copy.days), short: "d", value: pad(Math.floor(total / 86400)) },
    { label: localize(copy.hours), short: "h", value: pad(Math.floor((total % 86400) / 3600)) },
    { label: localize(copy.minutes), short: "m", value: pad(Math.floor((total % 3600) / 60)) },
    { label: localize(copy.seconds), short: "s", value: pad(total % 60) }
  ];
});

let timer: number | undefined;
onMounted(() => {
  resetSession();
  timer = window.setInterval(() => (now.value = Date.now()), 1000);
});
watch(() => [props.section.countdownMode, props.section.sessionDuration, props.section.sessionUnit], resetSession);
onBeforeUnmount(() => timer && window.clearInterval(timer));
</script>

<style scoped>
.v2-cd {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 28px 48px;
}
.v2-cd-copy {
  flex: 1 1 340px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.v2-cd-copy .v2-title {
  font-size: max(22px, calc(clamp(26px, 3.6cqi, 44px) * var(--v2-title-scale, 1)));
}
.v2-cd-pill {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 7px 14px 7px 12px;
  border-radius: 999px;
  background: var(--v2-card);
  font-size: 14px;
  font-weight: 700;
}
.v2-cd-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
  animation: v2-cd-pulse 1.8s ease-out infinite;
}
.v2-cd-tiles {
  display: flex;
  align-items: flex-start;
  gap: clamp(6px, 1.2cqi, 14px);
}
.v2-cd-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.v2-cd-tile {
  position: relative;
  display: grid;
  place-items: center;
  width: clamp(64px, 8.6cqi, 108px);
  aspect-ratio: 1 / 1.1;
  overflow: hidden;
  border-radius: clamp(14px, 1.6cqi, 22px);
  background: color-mix(in srgb, #0b1410 86%, var(--v2-accent));
  color: #fff;
  box-shadow: 0 18px 30px -18px rgba(0, 0, 0, 0.55);
}
.v2-cd-tile::before {
  content: "";
  position: absolute;
  inset: 0 0 50% 0;
  background: rgba(255, 255, 255, 0.05);
}
.v2-cd-tile::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 2px;
  margin-top: -1px;
  background: rgba(0, 0, 0, 0.5);
}
.v2-cd-tile b {
  position: relative;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: clamp(30px, 4.6cqi, 58px);
  line-height: 1;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}
.v2-cd-tick {
  animation: v2-cd-drop 0.42s cubic-bezier(0.22, 0.8, 0.24, 1);
}
.v2-cd-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--v2-muted);
}
.v2-cd-sep {
  display: flex;
  align-items: center;
  height: calc(clamp(64px, 8.6cqi, 108px) * 1.1);
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-weight: 700;
  font-size: clamp(22px, 3cqi, 38px);
  color: var(--v2-muted);
}
.v2-cd-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px 22px;
  margin: -12px 0;
}
.v2-cd-text {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
}
.v2-cd-mini {
  display: inline-flex;
  gap: 8px;
}
.v2-cd-mini span {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  font-size: 13px;
  font-weight: 700;
  color: var(--v2-muted);
}
.v2-cd-mini b {
  display: inline-grid;
  place-items: center;
  min-width: 40px;
  height: 40px;
  border-radius: 10px;
  background: color-mix(in srgb, #0b1410 86%, var(--v2-accent));
  color: #fff;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: 20px;
  font-variant-numeric: tabular-nums;
}
/* Celular: o contador ocupa toda a largura, com os quatro blocos dividindo o espaço. */
@container (max-width: 560px) {
  .v2-cd-tiles {
    width: 100%;
  }
  .v2-cd-unit {
    flex: 1 1 0;
    min-width: 0;
  }
  .v2-cd-tile {
    width: 100%;
  }
  .v2-cd-tile b {
    font-size: clamp(30px, 9cqi, 46px);
  }
  /* Os dois-pontos acompanham a altura do bloco, descontando o rótulo embaixo. */
  .v2-cd-sep {
    align-self: stretch;
    height: auto;
    padding-bottom: 25px;
  }
  .v2-cd-mini {
    width: 100%;
  }
  .v2-cd-mini span {
    flex: 1 1 0;
    min-width: 0;
  }
  .v2-cd-mini b {
    flex: 1;
  }
}
@keyframes v2-cd-pulse {
  0% { box-shadow: 0 0 0 0 currentColor; }
  70%, 100% { box-shadow: 0 0 0 9px transparent; }
}
@keyframes v2-cd-drop {
  from { opacity: 0.35; transform: translateY(-8px); }
  to { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .v2-cd-dot,
  .v2-cd-tick {
    animation: none;
  }
}
</style>
