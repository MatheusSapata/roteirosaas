<template>
  <div ref="root" class="vsl-player" :class="`is-${state}`" :style="playerStyle">
    <video
      ref="videoRef"
      class="vsl-player-video"
      :class="{ 'is-contain': fit === 'contain' }"
      :src="src"
      :poster="poster || undefined"
      :preload="autoPreview ? 'auto' : 'metadata'"
      :loop="state === 'preview'"
      muted
      playsinline
      webkit-playsinline
      disablepictureinpicture
      @loadedmetadata="syncTime"
      @durationchange="syncTime"
      @timeupdate="syncTime"
      @pause="onPause"
      @ended="onEnded"
      @error="emit('error')"
    ></video>

    <!-- Prévia muda em laço; clicar recomeça do início, com som. -->
    <button v-if="state === 'preview'" type="button" class="vsl-player-cover" :aria-label="`Ativar o som e assistir: ${title}`" @click="startWithSound">
      <span class="vsl-player-unmute">
        <span>Clique aqui</span>
        <!-- Alto-falante cheio com ondas, cortado por um traço com borda na cor da caixa. -->
        <svg class="vsl-player-unmute-ico" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 9.2h3.6L11.4 5v14l-4.8-4.2H3z" fill="currentColor" />
          <path d="M14.9 9.3a3.8 3.8 0 0 1 0 5.4M17.6 6.6a7.6 7.6 0 0 1 0 10.8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          <path d="M3.5 3.5l17 17" stroke="var(--vsl-color)" stroke-width="5" stroke-linecap="round" />
          <path d="M3.5 3.5l17 17" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" />
        </svg>
        <span>para ativar o som</span>
      </span>
    </button>

    <!-- Tocando: clicar em qualquer parte pausa. -->
    <button v-else-if="state === 'playing'" type="button" class="vsl-player-cover" aria-label="Pausar vídeo" @click="pause"></button>

    <!-- Sem prévia (menos movimento ou bloqueio do navegador), pausado ou no fim: o botão central. -->
    <button v-else type="button" class="vsl-player-cover is-dim" :aria-label="state === 'paused' ? 'Continuar vídeo' : `Assistir: ${title}`" @click="resume">
      <span class="vsl-player-play">
        <RotateCcw v-if="state === 'ended'" aria-hidden="true" />
        <svg v-else viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 5.2v13.6L19.3 12z" fill="currentColor" /></svg>
      </span>
    </button>

    <div v-if="state === 'playing' || state === 'paused' || state === 'ended'" class="vsl-player-progress" aria-hidden="true">
      <div class="vsl-player-progress-fill" :style="{ width: `${progress}%` }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RotateCcw } from "lucide-vue-next";
import { vslProgressPercent } from "../../utils/video";

/**
 * Player próprio no estilo do Panda: prévia muda em laço com o aviso "Clique aqui para ativar o
 * som"; ao clicar, o vídeo recomeça do início com som e a barra de progresso "fictícia" (rápida no
 * começo, devagar depois). Sem barra de tempo nem controles do navegador.
 */
const props = withDefaults(
  defineProps<{
    src: string;
    poster?: string | null;
    /** Cor do aviso de som, do botão e da barra (#RRGGBB). */
    color?: string | null;
    title?: string;
    fit?: "cover" | "contain";
  }>(),
  { poster: null, color: null, title: "Vídeo", fit: "cover" }
);
const emit = defineEmits<{ (event: "start"): void; (event: "error"): void }>();

const DEFAULT_COLOR = "#12B981";
type PlayerState = "idle" | "preview" | "playing" | "paused" | "ended";

const root = ref<HTMLElement | null>(null);
const videoRef = ref<HTMLVideoElement | null>(null);
const state = ref<PlayerState>("idle");
const currentTime = ref(0);
const duration = ref(0);
// Quem pede menos movimento no sistema não vê a prévia andando: fica a capa com o botão.
const autoPreview = ref(true);
let observer: IntersectionObserver | null = null;

const hexToRgba = (hex: string, alpha: number) => {
  const match = /^#([0-9a-f]{6})$/i.exec(hex);
  const value = parseInt(match ? match[1] : DEFAULT_COLOR.slice(1), 16);
  return `rgba(${(value >> 16) & 255}, ${(value >> 8) & 255}, ${value & 255}, ${alpha})`;
};
const playerStyle = computed(() => {
  const color = props.color || DEFAULT_COLOR;
  return { "--vsl-color": color, "--vsl-color-soft": hexToRgba(color, 0.86) };
});
const progress = computed(() => vslProgressPercent(currentTime.value, duration.value, state.value === "ended"));

const syncTime = () => {
  const video = videoRef.value;
  if (!video) return;
  currentTime.value = video.currentTime || 0;
  if (Number.isFinite(video.duration) && video.duration > 0) duration.value = video.duration;
};

const startPreview = async () => {
  const video = videoRef.value;
  if (!video || !autoPreview.value) return;
  video.muted = true;
  try {
    await video.play();
    if (state.value === "idle") state.value = "preview";
  } catch {
    // Navegador barrou a reprodução automática (ex.: economia de bateria): fica a capa.
    state.value = "idle";
  }
};

const startWithSound = async () => {
  const video = videoRef.value;
  if (!video) return;
  state.value = "playing";
  video.currentTime = 0;
  currentTime.value = 0;
  video.muted = false;
  try {
    await video.play();
  } catch {
    // Sem som não toca (raro, depois de um clique): toca mudo para não travar.
    video.muted = true;
    try {
      await video.play();
    } catch {
      state.value = "paused";
      return;
    }
  }
  emit("start");
};

const pause = () => {
  state.value = "paused";
  videoRef.value?.pause();
};

const resume = async () => {
  if (state.value !== "paused") {
    await startWithSound();
    return;
  }
  state.value = "playing";
  try {
    await videoRef.value?.play();
  } catch {
    state.value = "paused";
  }
};

// O sistema pausou (ligação, fone desconectado...): mostra o botão para continuar.
const onPause = () => {
  if (state.value === "playing" && !videoRef.value?.ended) state.value = "paused";
};
const onEnded = () => {
  if (state.value === "playing") state.value = "ended";
};

// A prévia só anda enquanto o vídeo aparece na tela (poupa bateria e dados).
const watchVisibility = () => {
  if (!root.value || typeof IntersectionObserver === "undefined") return;
  observer = new IntersectionObserver(entries => {
    const video = videoRef.value;
    if (!video || state.value !== "preview") return;
    if (entries.some(entry => entry.isIntersecting)) void video.play().catch(() => undefined);
    else video.pause();
  });
  observer.observe(root.value);
};

watch(
  () => props.src,
  async () => {
    state.value = "idle";
    currentTime.value = 0;
    duration.value = 0;
    await nextTick();
    void startPreview();
  }
);

onMounted(() => {
  autoPreview.value = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  void startPreview();
  watchVisibility();
});
onBeforeUnmount(() => observer?.disconnect());
</script>

<style scoped>
.vsl-player {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: #000;
  container-type: size;
}
.vsl-player-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.vsl-player-video.is-contain {
  object-fit: contain;
}
.vsl-player-cover {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}
.vsl-player-cover.is-dim {
  background: rgba(0, 0, 0, 0.28);
}
.vsl-player-cover:focus-visible {
  outline: 3px solid #fff;
  outline-offset: -6px;
}

/* Aviso de som: caixa na cor do player, borda branca e o alto-falante mudo no meio. */
.vsl-player-unmute {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35em;
  width: min(68%, 360px);
  padding: 0.9em 0.75em;
  border: 3px solid #fff;
  border-radius: 14px;
  background: var(--vsl-color-soft);
  color: #fff;
  font-size: 16px;
  font-size: clamp(13px, 4.6cqw, 21px);
  font-weight: 800;
  line-height: 1.15;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
  animation: vsl-player-pulse 1.8s ease-in-out infinite;
}
.vsl-player-unmute-ico {
  width: 3.4em;
  height: 3.4em;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.3));
}
@keyframes vsl-player-pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.035);
  }
}

.vsl-player-play {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 76px;
  height: 76px;
  border: 3px solid #fff;
  border-radius: 999px;
  background: var(--vsl-color);
  color: #fff;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
  transition: transform 0.2s ease;
}
.vsl-player-play svg {
  width: 32px;
  height: 32px;
}
.vsl-player-cover:hover .vsl-player-play {
  transform: scale(1.06);
}

/* Barra de progresso: na base do vídeo, sem marcar o tempo real. */
.vsl-player-progress {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 2;
  height: 8px;
  background: rgba(255, 255, 255, 0.25);
  pointer-events: none;
}
.vsl-player-progress-fill {
  height: 100%;
  width: 0;
  border-radius: 0 999px 999px 0;
  background: var(--vsl-color);
  transition: width 0.3s linear;
}

@media (prefers-reduced-motion: reduce) {
  .vsl-player-unmute {
    animation: none;
  }
  .vsl-player-play,
  .vsl-player-progress-fill {
    transition: none;
  }
}
</style>
