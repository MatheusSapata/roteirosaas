<template>
  <Teleport to="body">
    <Transition name="v2-lb">
      <div
        v-if="start !== null && current"
        class="v2-lb"
        role="dialog"
        aria-modal="true"
        :aria-label="copy.viewer"
        @click.self="emit('close')"
        @touchstart.passive="onTouchStart"
        @touchend="onTouchEnd"
      >
        <span v-if="items.length > 1" class="v2-lb-count">{{ index + 1 }} / {{ items.length }}</span>
        <button ref="closeRef" type="button" class="v2-lb-close" :aria-label="copy.close" @click="emit('close')">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12" /></svg>
        </button>
        <div class="v2-lb-stage" @click.self="emit('close')">
          <iframe
            v-if="current.type === 'video'"
            :key="current.url"
            class="v2-lb-video"
            :src="current.url"
            :title="copy.video"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen
          ></iframe>
          <V2Img v-else :key="current.url" class="v2-lb-img" :src="current.url" :alt="`${copy.photo} ${index + 1}`" loading="eager" />
        </div>
        <template v-if="items.length > 1">
          <button type="button" class="v2-lb-nav is-prev" :aria-label="copy.prev" @click="go(index - 1)">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6" /></svg>
          </button>
          <button type="button" class="v2-lb-nav is-next" :aria-label="copy.next" @click="go(index + 1)">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
          </button>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * Fotos em tela cheia das seções do visual novo: setas, arrastar para os lados no celular,
 * setas do teclado e Esc. Fecha no X, tocando fora da foto ou com Esc.
 */
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { localize } from "./useHeading";
import V2Img from "./V2Img.vue";

export interface V2LightboxItem {
  type: "image" | "video";
  url: string;
}

const props = defineProps<{ items: V2LightboxItem[]; start: number | null }>();
const emit = defineEmits<{ (e: "close"): void; (e: "change", index: number): void }>();

const copy = {
  viewer: localize({ pt: "Fotos em tela cheia", es: "Fotos en pantalla completa" }),
  close: localize({ pt: "Fechar", es: "Cerrar" }),
  prev: localize({ pt: "Foto anterior", es: "Foto anterior" }),
  next: localize({ pt: "Próxima foto", es: "Siguiente foto" }),
  photo: localize({ pt: "Foto", es: "Foto" }),
  video: localize({ pt: "Vídeo", es: "Video" })
};

const index = ref(0);
const current = computed(() => props.items[index.value]);
const closeRef = ref<HTMLButtonElement | null>(null);

const go = (next: number) => {
  const total = props.items.length;
  if (!total) return;
  index.value = ((next % total) + total) % total;
  emit("change", index.value);
};

const onKey = (event: KeyboardEvent) => {
  if (event.key === "Escape") emit("close");
  else if (event.key === "ArrowLeft") go(index.value - 1);
  else if (event.key === "ArrowRight") go(index.value + 1);
};

// Arrastar para os lados troca a foto; o gesto precisa ser mais horizontal que vertical.
let touchX = 0;
let touchY = 0;
const onTouchStart = (event: TouchEvent) => {
  touchX = event.touches[0]?.clientX ?? 0;
  touchY = event.touches[0]?.clientY ?? 0;
};
const onTouchEnd = (event: TouchEvent) => {
  if (props.items.length < 2) return;
  const dx = (event.changedTouches[0]?.clientX ?? 0) - touchX;
  const dy = (event.changedTouches[0]?.clientY ?? 0) - touchY;
  if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.2) go(index.value + (dx < 0 ? 1 : -1));
};

// Aberto, a página atrás não rola e o teclado comanda o visualizador.
let previousOverflow = "";
const lock = (on: boolean) => {
  if (typeof document === "undefined") return;
  if (on) {
    previousOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
  } else {
    document.documentElement.style.overflow = previousOverflow;
    window.removeEventListener("keydown", onKey);
  }
};

watch(
  () => props.start,
  (start, previous) => {
    if (start !== null) {
      index.value = Math.min(Math.max(start, 0), Math.max(props.items.length - 1, 0));
      if (previous === null || previous === undefined) {
        lock(true);
        nextTick(() => closeRef.value?.focus({ preventScroll: true }));
      }
    } else if (previous !== null && previous !== undefined) {
      lock(false);
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  if (props.start !== null) lock(false);
});
</script>

<style scoped>
.v2-lb {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(6, 10, 8, 0.94);
  color: #fff;
  overscroll-behavior: contain;
  touch-action: none;
  -webkit-user-select: none;
  user-select: none;
}
.v2-lb-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 64px 16px;
}
.v2-lb-img {
  display: block;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 12px;
}
.v2-lb-video {
  width: min(100%, 1100px);
  aspect-ratio: 16 / 9;
  border: 0;
  border-radius: 12px;
  background: #000;
}
.v2-lb-count {
  position: absolute;
  top: 18px;
  left: 18px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.v2-lb-close,
.v2-lb-nav {
  position: absolute;
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.v2-lb-close:hover,
.v2-lb-nav:hover {
  background: rgba(255, 255, 255, 0.26);
}
.v2-lb-close {
  top: 12px;
  right: 12px;
}
.v2-lb-nav {
  top: 50%;
  margin-top: -24px;
}
.v2-lb-nav.is-prev {
  left: 16px;
}
.v2-lb-nav.is-next {
  right: 16px;
}
/* Celular: setas embaixo, longe do polegar que arrasta a foto. */
@media (max-width: 640px) {
  .v2-lb-stage {
    padding: 64px 0 96px;
  }
  .v2-lb-img {
    border-radius: 0;
  }
  .v2-lb-nav {
    top: auto;
    bottom: 24px;
    margin-top: 0;
  }
  .v2-lb-nav.is-prev {
    left: calc(50% - 60px);
  }
  .v2-lb-nav.is-next {
    right: calc(50% - 60px);
  }
}
.v2-lb-enter-active,
.v2-lb-leave-active {
  transition: opacity 0.2s ease;
}
.v2-lb-enter-from,
.v2-lb-leave-to {
  opacity: 0;
}
</style>
