<template>
  <div v-if="tour" class="hd" :class="{ 'is-full': ampliado }" @keydown="teclas">
    <div v-if="ampliado" class="hd-backdrop" aria-hidden="true" @click="ampliado = false"></div>
    <div class="hd-box">
      <div class="hd-top">
        <div v-if="tour.video" class="hd-tabs" role="tablist" aria-label="Formato da demonstração">
          <button type="button" role="tab" :aria-selected="modo === 'interativo'" :class="{ on: modo === 'interativo' }" @click="modo = 'interativo'">
            <MousePointerClickIcon aria-hidden="true" />
            Interativa
          </button>
          <button type="button" role="tab" :aria-selected="modo === 'video'" :class="{ on: modo === 'video' }" @click="modo = 'video'">
            <PlayIcon aria-hidden="true" />
            Vídeo
          </button>
        </div>
        <p v-else class="hd-kind"><MousePointerClickIcon aria-hidden="true" /> Demonstração interativa</p>
        <button type="button" class="hd-icon" :aria-label="ampliado ? 'Fechar tela ampliada' : 'Ampliar'" :title="ampliado ? 'Fechar' : 'Ampliar'" @click="ampliado = !ampliado">
          <XIcon v-if="ampliado" aria-hidden="true" />
          <Maximize2Icon v-else aria-hidden="true" />
        </button>
      </div>

      <template v-if="modo === 'interativo'">
        <div ref="stage" class="hd-stage" tabindex="0" :aria-label="`Passo ${atual + 1} de ${total}: ${passo.legenda}`">
          <img :key="tela" :src="tela" :alt="passo.legenda" class="hd-img" draggable="false" />
          <button
            v-if="passo.ponto"
            type="button"
            class="hd-spot"
            :style="spotStyle"
            :aria-label="`${passo.legenda} (avançar)`"
            @click="avancar"
          >
            <span class="hd-spot-ring" aria-hidden="true"></span>
          </button>
          <span v-if="passo.ponto" class="hd-tip" :class="tipAbaixo ? 'is-below' : 'is-above'" :style="tipStyle" aria-hidden="true">Clique aqui</span>
          <div v-if="!passo.ponto && atual === total - 1" class="hd-done">
            <CheckIcon aria-hidden="true" />
          </div>
        </div>
        <div class="hd-cap">
          <div class="hd-cap-text">
            <span class="hd-count">Passo {{ atual + 1 }} de {{ total }}</span>
            <b>{{ passo.legenda }}</b>
            <span v-if="passo.detalhe" class="hd-detail">{{ passo.detalhe }}</span>
          </div>
          <div class="hd-nav">
            <button type="button" class="hd-btn" :disabled="atual === 0" @click="voltar">
              <ChevronLeftIcon aria-hidden="true" />
              <span>Voltar</span>
            </button>
            <button v-if="atual < total - 1" type="button" class="hd-btn is-primary" @click="avancar">
              <span>Próximo</span>
              <ChevronRightIcon aria-hidden="true" />
            </button>
            <button v-else type="button" class="hd-btn is-primary" @click="atual = 0">
              <RotateCcwIcon aria-hidden="true" />
              <span>Recomeçar</span>
            </button>
          </div>
        </div>
        <div class="hd-dots" aria-hidden="true">
          <button v-for="(_, i) in tour.passos" :key="i" type="button" tabindex="-1" :class="{ on: i === atual, past: i < atual }" @click="atual = i"></button>
        </div>
      </template>

      <div v-else class="hd-video">
        <video :src="tour.video" :poster="tour.telas[0]?.light" autoplay muted loop playsinline controls preload="metadata"></video>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import {
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Maximize2Icon,
  MousePointerClickIcon,
  PlayIcon,
  RotateCcwIcon,
  XIcon
} from "lucide-vue-next";
import { getTour } from "../../help/media";
import { useThemeStore } from "../../store/useThemeStore";

const props = withDefaults(defineProps<{ tourId: string; inicio?: number }>(), { inicio: 0 });

const theme = useThemeStore();
const tour = computed(() => getTour(props.tourId));
const total = computed(() => tour.value?.passos.length || 0);
const atual = ref(Math.min(props.inicio, Math.max(0, total.value - 1)));
const modo = ref<"interativo" | "video">("interativo");
const ampliado = ref(false);
const stage = ref<HTMLElement | null>(null);

const passo = computed(() => tour.value!.passos[atual.value]);
const tela = computed(() => {
  const t = tour.value!.telas[atual.value];
  return (theme.isDark ? t.dark : t.light) || t.light;
});
const spotStyle = computed(() => {
  const p = passo.value.ponto!;
  return { left: `${p.x}%`, top: `${p.y}%`, width: `${p.w}%`, height: `${p.h}%` };
});
// A dica "Clique aqui" fica acima do ponto; perto do topo da tela, vai para baixo.
const tipAbaixo = computed(() => (passo.value.ponto?.y || 0) < 12);
const tipStyle = computed(() => {
  const p = passo.value.ponto!;
  const left = Math.min(92, Math.max(8, p.x + p.w / 2));
  return tipAbaixo.value ? { left: `${left}%`, top: `${p.y + p.h}%` } : { left: `${left}%`, top: `${p.y}%` };
});

const avancar = () => {
  if (atual.value < total.value - 1) atual.value++;
};
const voltar = () => {
  if (atual.value > 0) atual.value--;
};
const teclas = (event: KeyboardEvent) => {
  if (modo.value !== "interativo") return;
  if (event.key === "ArrowRight") avancar();
  else if (event.key === "ArrowLeft") voltar();
  else if (event.key === "Escape" && ampliado.value) ampliado.value = false;
  else return;
  event.preventDefault();
};

// Carrega a próxima tela antes do clique, para a troca ser imediata.
watch(
  [atual, () => theme.isDark, tour],
  () => {
    const t = tour.value?.telas[atual.value + 1];
    if (t) new Image().src = (theme.isDark ? t.dark : t.light) || t.light;
  },
  { immediate: true }
);
watch(
  () => props.inicio,
  value => {
    if (value < 0) return;
    atual.value = Math.min(value, Math.max(0, total.value - 1));
    modo.value = "interativo";
    nextTick(() => stage.value?.scrollIntoView({ behavior: "smooth", block: "center" }));
  }
);
watch(
  () => props.tourId,
  () => {
    atual.value = 0;
    modo.value = "interativo";
  }
);
watch(ampliado, aberto => {
  document.body.style.overflow = aberto ? "hidden" : "";
  if (aberto) nextTick(() => stage.value?.focus());
});
</script>

<style scoped>
.hd { position: relative; }
.hd-box { overflow: hidden; border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.hd-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 10px 10px 14px; border-bottom: 1px solid var(--border); }
.hd-kind { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: var(--muted-foreground); }
.hd-kind svg, .hd-tabs svg { width: 16px; height: 16px; }
.hd-tabs { display: inline-flex; gap: 4px; padding: 3px; border-radius: 999px; background: var(--muted); }
.hd-tabs button { display: inline-flex; align-items: center; gap: 6px; height: 32px; padding: 0 14px; border-radius: 999px; font-size: 13px; font-weight: 600; color: var(--muted-foreground); transition: background-color 0.2s ease, color 0.2s ease; }
.hd-tabs button.on { background: var(--card); color: var(--foreground); box-shadow: var(--shadow-soft, 0 1px 2px rgba(0, 0, 0, 0.08)); }
.hd-icon { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 999px; color: var(--muted-foreground); }
.hd-icon:hover { background: var(--muted); color: var(--foreground); }
.hd-icon svg { width: 17px; height: 17px; }

.hd-stage { position: relative; overflow: hidden; aspect-ratio: 1440 / 900; background: var(--muted); outline: none; }
.hd-stage:focus-visible { box-shadow: inset 0 0 0 2px var(--ring); }
.hd-img { display: block; width: 100%; height: 100%; object-fit: cover; user-select: none; animation: hd-in 0.25s ease-out; }
@keyframes hd-in { from { opacity: 0.4; } }
.hd-spot { position: absolute; border-radius: 12px; cursor: pointer; background: transparent; box-shadow: 0 0 0 2px #12b981, 0 0 0 9999px rgba(6, 12, 9, 0.28); transition: box-shadow 0.2s ease; }
.hd-spot:hover { box-shadow: 0 0 0 3px #12b981, 0 0 0 9999px rgba(6, 12, 9, 0.18); }
.hd-spot:focus-visible { outline: 3px solid #fff; outline-offset: 2px; }
.hd-spot-ring { position: absolute; inset: -2px; border-radius: inherit; border: 2px solid #12b981; animation: hd-pulse 1.6s ease-out infinite; pointer-events: none; }
@keyframes hd-pulse { 0% { opacity: 0.9; transform: scale(1); } 100% { opacity: 0; transform: scale(1.18); } }
.hd-tip { position: absolute; z-index: 2; padding: 5px 10px; border-radius: 999px; background: #0f1713; color: #fff; font-size: 12px; font-weight: 700; white-space: nowrap; pointer-events: none; box-shadow: 0 6px 16px -6px rgba(0, 0, 0, 0.5); }
.hd-tip.is-above { transform: translate(-50%, calc(-100% - 10px)); }
.hd-tip.is-below { transform: translate(-50%, 10px); }
.hd-done { position: absolute; right: 16px; bottom: 16px; display: grid; place-items: center; width: 44px; height: 44px; border-radius: 999px; background: #12b981; color: #fff; box-shadow: 0 8px 20px -8px rgba(0, 0, 0, 0.45); }
.hd-done svg { width: 22px; height: 22px; }

.hd-cap { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 16px 10px; }
.hd-cap-text { display: flex; min-width: 0; flex-direction: column; gap: 2px; }
.hd-count { font-size: 12px; font-weight: 600; color: var(--muted-foreground); }
.hd-cap-text b { font-size: 16px; font-weight: 700; color: var(--foreground); }
.hd-detail { font-size: 14px; color: var(--muted-foreground); }
.hd-nav { display: flex; flex-shrink: 0; gap: 8px; }
.hd-btn { display: inline-flex; align-items: center; gap: 6px; height: 38px; padding: 0 14px; border-radius: 999px; background: var(--muted); font-size: 13px; font-weight: 700; color: var(--foreground); }
.hd-btn:disabled { opacity: 0.45; }
.hd-btn.is-primary { background: var(--primary); color: var(--primary-foreground); }
.hd-btn svg { width: 16px; height: 16px; }
.hd-dots { display: flex; justify-content: center; gap: 6px; padding: 0 16px 14px; }
.hd-dots button { width: 8px; height: 8px; border-radius: 999px; background: var(--border); transition: width 0.2s ease, background-color 0.2s ease; }
.hd-dots button.past { background: color-mix(in srgb, var(--primary) 45%, var(--border)); }
.hd-dots button.on { width: 22px; background: var(--primary); }

.hd-video video { display: block; width: 100%; aspect-ratio: 1280 / 800; background: #000; }

/* Ampliada: a demonstração ocupa a tela, com o fundo escurecido. */
.hd.is-full .hd-backdrop { position: fixed; inset: 0; z-index: 90; background: rgba(6, 12, 9, 0.72); }
.hd.is-full .hd-box { position: fixed; z-index: 91; top: 50%; left: 50%; width: min(1280px, calc(100vw - 32px), calc((100vh - 170px) * 1.6)); transform: translate(-50%, -50%); }

@media (max-width: 640px) {
  .hd-cap { flex-direction: column; align-items: stretch; }
  .hd-nav { justify-content: space-between; }
  .hd-btn span { display: none; }
  .hd-btn { padding: 0 12px; }
  .hd-tip { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .hd-spot-ring, .hd-img { animation: none; }
}
</style>
