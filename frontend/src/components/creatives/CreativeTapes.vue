<template>
  <!-- Duas fitas cruzadas de campanha ("BLACK FRIDAY •"), como fita de isolamento. -->
  <div class="tp" :class="[`tp-${variant}`, `tp-at-${position}`]" aria-hidden="true">
    <div v-for="band in 2" :key="band" class="tp-band" :class="`tp-${band}`">
      <span v-for="item in 9" :key="item" class="tp-item">
        <b>{{ first }}</b><em v-if="rest">&nbsp;{{ rest }}</em><i>•</i>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{ text: string; variant?: "dark" | "yellow"; position?: "top" | "bottom" | "corner" }>(), {
  variant: "dark",
  position: "top"
});
// "BLACK FRIDAY" → "BLACK" numa cor e "FRIDAY" na outra (na fita escura).
const first = computed(() => props.text.split(" ")[0] || props.text);
const rest = computed(() => props.text.split(" ").slice(1).join(" "));
</script>

<style scoped>
.tp {
  position: absolute;
  inset: 0;
  z-index: 6;
  overflow: hidden;
  pointer-events: none;
}
.tp-band {
  position: absolute;
  left: -15%;
  display: flex;
  width: 130%;
  padding: 0.32em 0;
  font-family: "Montserrat", sans-serif;
  font-size: 42px;
  font-weight: 900;
  letter-spacing: 0.01em;
  white-space: nowrap;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
}
.tp-item {
  display: inline-flex;
  flex: none;
  align-items: center;
  padding-left: 0.5em;
  text-transform: uppercase;
}
.tp-item i {
  padding-left: 0.5em;
  font-style: normal;
}
.tp-item em {
  font-style: normal;
}

/* Fita escura: "BLACK" branco e "FRIDAY" na cor de destaque. */
.tp-dark .tp-band {
  background: #0b0b0b;
  color: #fff;
}
.tp-dark .tp-item em,
.tp-dark .tp-item i {
  color: var(--c2);
}
/* Fita amarela com texto preto; a segunda, mais clara (como as fitas da referência). */
.tp-yellow .tp-band {
  background: var(--c2);
  color: #0b0b0b;
}
.tp-yellow .tp-2 {
  background: #fff4cf;
}

/* Topo: cruzam um pouco abaixo da borda. */
.tp-at-top .tp-1 {
  top: 3%;
  transform: rotate(-6deg);
}
.tp-at-top .tp-2 {
  top: 6.5%;
  transform: rotate(5deg);
}
/* Base. */
.tp-at-bottom .tp-1 {
  bottom: 3%;
  transform: rotate(5deg);
}
.tp-at-bottom .tp-2 {
  bottom: 7%;
  transform: rotate(-4deg);
}
/* Canto superior esquerdo: fitas em diagonal, uma sobre a outra. */
.tp-at-corner .tp-1 {
  top: 7%;
  left: -40%;
  width: 110%;
  transform: rotate(-28deg);
}
.tp-at-corner .tp-2 {
  top: 2%;
  left: -14%;
  width: 110%;
  transform: rotate(-8deg);
}
</style>
