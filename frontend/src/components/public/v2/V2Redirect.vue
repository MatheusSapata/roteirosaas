<template>
  <V2Section type="redirect" :background="section.backgroundColor" :anchor-id="section.anchorId" flush>
    <div class="v2-rd v2-in" :class="{ 'v2-rd--live': live }">
      <img v-if="logo" :src="logo" alt="" class="v2-rd-logo" />
      <V2Img v-if="image" :src="image" alt="" class="v2-rd-img" />
      <h1 v-if="title" class="v2-title v2-rd-title" :style="titleScaleStyle(title)">{{ title }}</h1>
      <p v-if="subtitle" class="v2-lead v2-rd-sub">{{ subtitle }}</p>

      <template v-if="destination">
        <!-- Contagem: anel que esvazia a cada segundo e o número no meio. -->
        <div class="v2-rd-count" role="timer" aria-live="polite">
          <span class="v2-rd-ring" :class="{ 'v2-rd-ring--done': phase !== 'counting' }">
            <svg viewBox="0 0 100 100" aria-hidden="true">
              <circle class="v2-rd-track" cx="50" cy="50" r="44" />
              <circle class="v2-rd-bar" cx="50" cy="50" r="44" :style="{ strokeDashoffset: `${ringOffset}` }" />
            </svg>
            <b v-if="phase === 'counting'">{{ remaining }}</b>
            <svg v-else class="v2-rd-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
          </span>
          <span class="v2-rd-status">{{ statusText }}</span>
        </div>

        <V2Button class="v2-rd-btn" :attrs="buttonAttrs" block>{{ buttonLabel }}</V2Button>
        <p v-if="phase === 'failed' || !live" class="v2-rd-fallback" :class="{ 'v2-rd-fallback--on': phase === 'failed' }">{{ fallbackLabel }}</p>
      </template>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
/**
 * Redirecionamento: marca, contagem e botão. Só a página publicada (LIVE_PAGE_KEY) conta e leva
 * ao destino; na prévia do editor, nas miniaturas e nos criativos a contagem fica parada.
 * O destino é aberto no navegador, depois da página carregar (sem redirecionamento do servidor),
 * e o botão funciona como plano B se o navegador não abrir sozinho.
 */
import { computed, inject, onBeforeUnmount, onMounted, ref } from "vue";
import type { RedirectSection } from "../../../types/page";
import { PUBLIC_BRANDING_KEY } from "../../../utils/brandingKeys";
import { resolveMediaUrl } from "../../../utils/media";
import { safeRedirectUrl } from "../../../utils/redirectUrl";
import V2Button from "./V2Button.vue";
import V2Img from "./V2Img.vue";
import V2Section from "./V2Section.vue";
import { LIVE_PAGE_KEY } from "./livePage";
import { localize, text } from "./useHeading";
import { titleScaleStyle } from "./useCopyFit";

const props = defineProps<{ section: RedirectSection; previewDevice?: "desktop" | "mobile" }>();

const live = inject(LIVE_PAGE_KEY, false);
const provided = inject(PUBLIC_BRANDING_KEY, null) as any;
const branding = computed<Record<string, any>>(() => (provided && "value" in provided ? provided.value : provided) || {});

const copy = {
  button: { pt: "Entrar agora", es: "Entrar ahora" },
  fallback: { pt: "Não abriu sozinho? Toque no botão acima.", es: "¿No se abrió solo? Toca el botón de arriba." },
  redirecting: { pt: "Abrindo...", es: "Abriendo..." }
} as const;

const destination = computed(() => safeRedirectUrl(props.section.url));
const seconds = computed(() => Math.min(30, Math.max(1, Math.round(Number(props.section.seconds) || 5))));
const logo = computed(() => (props.section.showLogo === false ? "" : resolveMediaUrl(props.section.logoUrl) || resolveMediaUrl(branding.value?.logo_url) || ""));
const image = computed(() => resolveMediaUrl(props.section.image) || "");
const title = computed(() => text(props.section.title || ""));
const subtitle = computed(() => text(props.section.subtitle || ""));
const buttonLabel = computed(() => text(props.section.buttonText || "") || localize(copy.button));
const fallbackLabel = computed(() => text(props.section.fallbackText || "") || localize(copy.fallback));

const remaining = ref(seconds.value);
const phase = ref<"counting" | "redirecting" | "failed">("counting");
const statusText = computed(() => {
  if (phase.value !== "counting") return localize(copy.redirecting);
  const n = live ? remaining.value : seconds.value;
  return localize({
    pt: `Você será direcionado em ${n} segundo${n === 1 ? "" : "s"}`,
    es: `Serás redirigido en ${n} segundo${n === 1 ? "" : "s"}`
  });
});
// Anel cheio no começo e vazio no fim (circunferência de r=44 ≈ 276,5).
const CIRCLE = 2 * Math.PI * 44;
const ringOffset = computed(() => (phase.value === "counting" ? CIRCLE * (1 - (live ? remaining.value : seconds.value) / seconds.value) : CIRCLE));

let tick: ReturnType<typeof setInterval> | null = null;
let failTimer: ReturnType<typeof setTimeout> | null = null;

const go = () => {
  if (!destination.value || typeof window === "undefined") return;
  phase.value = "redirecting";
  // replace: o "voltar" do celular não cai de novo na contagem.
  window.location.replace(destination.value);
  // Se a página continuar aberta (app que não abriu, bloqueio do navegador), mostra o plano B.
  failTimer = setTimeout(() => {
    phase.value = "failed";
  }, 2500);
};

const buttonAttrs = computed(() => ({
  href: destination.value,
  rel: "noopener",
  // Fora da página publicada o botão não navega (a prévia do editor continua aberta).
  onClick: (event: MouseEvent) => {
    if (!live) event.preventDefault();
  }
}));

onMounted(() => {
  if (!live || !destination.value) return;
  remaining.value = seconds.value;
  tick = setInterval(() => {
    remaining.value -= 1;
    if (remaining.value <= 0) {
      if (tick) clearInterval(tick);
      tick = null;
      go();
    }
  }, 1000);
});

onBeforeUnmount(() => {
  if (tick) clearInterval(tick);
  if (failTimer) clearTimeout(failTimer);
});
</script>

<style scoped>
.v2-rd {
  display: flex;
  width: 100%;
  max-width: 560px;
  min-height: 560px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  margin: 0 auto;
  padding: clamp(36px, 7cqi, 72px) 0;
  text-align: center;
}
/* Na página publicada ocupa a tela toda (é, em geral, a única seção). */
.v2-rd--live {
  min-height: min(100svh, 920px);
}
.v2-rd-logo {
  display: block;
  max-width: 200px;
  max-height: 72px;
  object-fit: contain;
}
.v2-rd-img {
  width: 100%;
  aspect-ratio: 16 / 10;
  border-radius: 24px;
  object-fit: cover;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.16);
}
.v2-rd-title {
  font-size: max(26px, calc(clamp(28px, 5cqi, 44px) * var(--v2-title-scale, 1)));
}
.v2-rd-sub {
  margin: -6px 0 0;
  color: var(--v2-muted);
}
.v2-rd-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}
.v2-rd-ring {
  position: relative;
  display: grid;
  width: 92px;
  height: 92px;
  place-items: center;
  color: var(--v2-ink);
}
.v2-rd-ring svg:first-child {
  position: absolute;
  inset: 0;
  transform: rotate(-90deg);
}
.v2-rd-track,
.v2-rd-bar {
  fill: none;
  stroke-width: 7;
}
.v2-rd-track {
  stroke: var(--v2-accent-soft);
}
.v2-rd-bar {
  stroke: var(--v2-accent);
  stroke-dasharray: 276.46;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s linear;
}
/* Número e seta ocupam a mesma célula, no centro do anel. */
.v2-rd-ring > b,
.v2-rd-arrow {
  grid-area: 1 / 1;
}
.v2-rd-ring b {
  position: relative;
  line-height: 1;
  font-family: var(--v2-display, inherit);
  font-size: 34px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.v2-rd-arrow {
  position: relative;
  display: block;
  width: 34px;
  height: 34px;
  color: var(--v2-accent);
}
.v2-rd-status {
  color: var(--v2-muted);
  font-size: 15px;
  font-weight: 600;
}
.v2-rd-btn {
  width: 100%;
  max-width: 420px;
  --v2-btn-h: 58px;
  font-size: 17px;
}
.v2-rd-fallback {
  margin: 0;
  color: var(--v2-muted);
  font-size: 14px;
}
.v2-rd-fallback--on {
  color: var(--v2-ink);
  font-weight: 600;
}
@media (prefers-reduced-motion: reduce) {
  .v2-rd-bar {
    transition: none;
  }
}
</style>
