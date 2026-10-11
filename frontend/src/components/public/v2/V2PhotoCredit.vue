<template>
  <span
    v-if="credit"
    class="v2-pc"
    :class="{ 'is-open': open }"
    @pointerenter="hover($event, true)"
    @pointerleave="hover($event, false)"
  >
    <button type="button" class="v2-pc-btn" :aria-expanded="open" :aria-label="`Crédito da foto: ${credit.name}, ${credit.provider}`" @click.stop.prevent="open = !open">©</button>
    <span v-show="open" class="v2-pc-text">
      Foto:
      <a v-if="credit.link" :href="credit.link" target="_blank" rel="noopener noreferrer" @click.stop>{{ credit.name }}</a><template v-else>{{ credit.name }}</template>
      ·
      <a v-if="credit.providerLink" :href="credit.providerLink" target="_blank" rel="noopener noreferrer" @click.stop>{{ credit.provider }}</a><template v-else>{{ credit.provider }}</template>
    </span>
  </span>
</template>

<script setup lang="ts">
/**
 * "©" no canto de uma foto de banco gratuito: ao passar o mouse ou tocar, mostra o crédito do
 * fotógrafo e do banco (exigência do Unsplash). Fotos enviadas pela agência não têm crédito.
 */
import { ref } from "vue";
import { usePhotoCredit } from "./photoCredits";

const props = defineProps<{ src?: string | null }>();
const credit = usePhotoCredit(() => props.src);
const open = ref(false);
// Passar o mouse abre; no toque (celular), só o clique abre e fecha.
const hover = (event: PointerEvent, value: boolean) => {
  if (event.pointerType === "mouse") open.value = value;
};
</script>

<style scoped>
.v2-pc {
  position: absolute;
  left: 10px;
  bottom: 10px;
  z-index: 6;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: calc(100% - 20px);
  font-family: Figtree, system-ui, sans-serif;
  pointer-events: auto;
}
.v2-pc-btn {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  flex: none;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(10, 14, 12, 0.45);
  color: rgba(255, 255, 255, 0.92);
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  backdrop-filter: blur(4px);
  transition: background-color 0.15s ease;
}
.v2-pc.is-open .v2-pc-btn,
.v2-pc-btn:hover {
  background: rgba(10, 14, 12, 0.72);
}
.v2-pc-text {
  min-width: 0;
  overflow: hidden;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(10, 14, 12, 0.72);
  color: #fff;
  font-size: 11.5px;
  line-height: 1.3;
  white-space: nowrap;
  text-overflow: ellipsis;
  backdrop-filter: blur(4px);
}
.v2-pc-text a {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
