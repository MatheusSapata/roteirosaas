<template>
  <!-- Duas fitas cruzadas no topo, no estilo de campanha (Black Friday, Oferta...). -->
  <div class="tp" :class="[`tp-${variant || 'dark'}`, `tp-at-${position || 'top'}`]" aria-hidden="true">
    <div v-for="band in 2" :key="band" class="tp-band" :class="`tp-${band}`">
      <span v-for="item in 8" :key="item" class="tp-item">
        <b>{{ first }}</b><em v-if="rest">{{ rest }}</em>
        <svg viewBox="0 0 24 24"><path d="M12 2c1 3.5-1.5 5-1.5 7.5 0 1.4 1 2.5 2.3 2.5 1.6 0 2.4-1.4 2.2-3 2 1.6 3 4 3 6 0 3.9-2.9 7-7 7s-7-3.1-7-7c0-4.6 4.6-7.2 8-13z" /></svg>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ text: string; variant?: "dark" | "yellow"; position?: "top" | "bottom" }>();
// "BLACK FRIDAY" → "BLACK" numa cor e "FRIDAY" na de destaque.
const first = computed(() => props.text.split(" ")[0] || props.text);
const rest = computed(() => props.text.split(" ").slice(1).join(" "));
</script>

<style scoped>
.tp {
  position: absolute;
  inset: 0 0 auto 0;
  z-index: 6;
  height: 260px;
  pointer-events: none;
}
.tp-band {
  position: absolute;
  left: -120px;
  display: flex;
  width: calc(100% + 240px);
  overflow: hidden;
  padding: 14px 0;
  background: #0b0b0b;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  white-space: nowrap;
}
.tp-1 {
  top: 54px;
  transform: rotate(-7deg);
}
.tp-2 {
  top: 96px;
  transform: rotate(6deg);
}
.tp-item {
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  font-family: Sora, Inter, sans-serif;
  font-size: 44px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.tp-item b {
  color: #fff;
  font-weight: 800;
}
.tp-item em {
  color: var(--c2);
  font-style: normal;
}
/* Fita amarela com texto preto (como as fitas de "cuidado"). */
.tp-yellow .tp-band {
  background: var(--c2);
}
.tp-yellow .tp-item b,
.tp-yellow .tp-item em {
  color: #0b0b0b;
}
.tp-yellow .tp-item svg {
  fill: #0b0b0b;
  width: 22px;
  height: 22px;
}
.tp-at-bottom {
  top: auto;
  bottom: 0;
}
.tp-at-bottom .tp-1 {
  top: auto;
  bottom: 40px;
  transform: rotate(6deg);
}
.tp-at-bottom .tp-2 {
  top: auto;
  bottom: 96px;
  transform: rotate(-5deg);
}
.tp-item svg {
  width: 38px;
  height: 38px;
  fill: #f97316;
}
</style>
