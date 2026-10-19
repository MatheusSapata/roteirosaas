<template>
  <!-- No body e acima de tudo: dentro do painel da seção a janela ficaria presa atrás dele. -->
  <Teleport to="body">
    <transition name="fade">
      <div v-if="open" class="ifd-overlay" role="dialog" aria-modal="true" :aria-label="title" @click.self="emit('close')">
        <div class="ifd-modal">
          <header class="ifd-head">
            <div class="min-w-0">
              <p class="ifd-eyebrow">Encaixe da foto</p>
              <h3 class="ifd-title">{{ title }}</h3>
              <p class="ifd-sub">Clique ou arraste na foto para marcar o que não pode ficar de fora. As molduras mostram como ela fica em cada tela.</p>
            </div>
            <button type="button" class="ifd-close" aria-label="Fechar" @click="emit('close')">×</button>
          </header>

          <div class="ifd-body">
            <div class="ifd-stage">
              <div ref="pickArea" class="ifd-pick" @pointerdown="startDrag" @pointermove="drag" @pointerup="endDrag" @pointercancel="endDrag">
                <img :src="src" alt="" draggable="false" />
                <span
                  class="ifd-marker"
                  :style="{ left: `${point.x}%`, top: `${point.y}%` }"
                  tabindex="0"
                  role="slider"
                  aria-label="Ponto de encaixe (use as setas para mover)"
                  :aria-valuetext="`${point.x}% da esquerda, ${point.y}% do topo`"
                  @keydown="nudge"
                ></span>
              </div>
            </div>
            <aside class="ifd-previews">
              <figure v-for="screen in screens" :key="screen" class="ifd-frame" :class="`is-${screen}`">
                <div class="ifd-shot" :style="{ aspectRatio: screen === 'desktop' ? desktopRatio : mobileRatio }">
                  <img :src="src" alt="" :style="{ objectPosition: position }" />
                </div>
                <figcaption>{{ screen === "desktop" ? "Computador" : "Celular" }}</figcaption>
              </figure>
            </aside>
          </div>

          <footer class="ifd-foot">
            <button type="button" class="ifd-btn is-ghost" :disabled="!chosen" @click="reset">Voltar ao padrão</button>
            <span class="ifd-spacer"></span>
            <button type="button" class="ifd-btn" @click="emit('close')">Cancelar</button>
            <button type="button" class="ifd-btn is-primary" @click="apply">Aplicar encaixe</button>
          </footer>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * Encaixe de uma foto que a tela corta (capa cheia no computador, quase quadrada no celular):
 * a pessoa marca o ponto que precisa aparecer e vê na hora as molduras de cada tela. Não corta
 * nem envia o arquivo de novo: guarda o ponto ("x% y%"), que a página usa como object-position.
 */
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { formatFocus, parseFocus, type FocusPoint } from "../../../utils/heroPhoto";

const props = withDefaults(
  defineProps<{
    open: boolean;
    src: string;
    /** Encaixe salvo ("x% y%"); vazio é o padrão do layout. */
    modelValue?: string;
    /** Telas em que esta foto aparece (uma moldura para cada). */
    screens?: ("desktop" | "mobile")[];
    /** Encaixe padrão do layout, para a prévia sem escolha. */
    defaultFocus?: string;
    desktopRatio?: string;
    mobileRatio?: string;
    title?: string;
  }>(),
  {
    modelValue: "",
    screens: () => ["desktop", "mobile"],
    defaultFocus: "50% 0%",
    desktopRatio: "16 / 9",
    mobileRatio: "1 / 1.12",
    title: "Ajuste o encaixe"
  }
);
const emit = defineEmits<{ (e: "apply", value: string): void; (e: "close"): void }>();

const fallbackPoint = (): FocusPoint => parseFocus(props.defaultFocus) || { x: 50, y: 0 };
const point = ref<FocusPoint>(fallbackPoint());
// Sem tocar na foto, "Aplicar" mantém o padrão do layout (nada é salvo).
const chosen = ref(false);
const position = computed(() => `${point.value.x}% ${point.value.y}%`);

watch(
  () => props.open,
  open => {
    if (!open) return;
    const saved = parseFocus(props.modelValue);
    point.value = saved || fallbackPoint();
    chosen.value = Boolean(saved);
  },
  { immediate: true }
);

const pickArea = ref<HTMLElement | null>(null);
const dragging = ref(false);
const placeAt = (event: PointerEvent) => {
  const rect = pickArea.value?.getBoundingClientRect();
  if (!rect || !rect.width || !rect.height) return;
  point.value = {
    x: Math.round(Math.min(100, Math.max(0, ((event.clientX - rect.left) / rect.width) * 100))),
    y: Math.round(Math.min(100, Math.max(0, ((event.clientY - rect.top) / rect.height) * 100)))
  };
  chosen.value = true;
};
const startDrag = (event: PointerEvent) => {
  dragging.value = true;
  pickArea.value?.setPointerCapture?.(event.pointerId);
  placeAt(event);
};
const drag = (event: PointerEvent) => {
  if (dragging.value) placeAt(event);
};
const endDrag = () => {
  dragging.value = false;
};
const nudge = (event: KeyboardEvent) => {
  const step = event.shiftKey ? 10 : 2;
  const moves: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
  const move = moves[event.key];
  if (!move) return;
  event.preventDefault();
  point.value = {
    x: Math.min(100, Math.max(0, point.value.x + move[0])),
    y: Math.min(100, Math.max(0, point.value.y + move[1]))
  };
  chosen.value = true;
};

const reset = () => {
  point.value = fallbackPoint();
  chosen.value = false;
};
const apply = () => emit("apply", chosen.value ? formatFocus(point.value) : "");

const onKeydown = (event: KeyboardEvent) => {
  if (event.key === "Escape" && props.open) emit("close");
};
watch(
  () => props.open,
  open => (open ? document.addEventListener("keydown", onKeydown) : document.removeEventListener("keydown", onKeydown)),
  { immediate: true }
);
onBeforeUnmount(() => document.removeEventListener("keydown", onKeydown));
</script>

<style scoped>
.ifd-overlay {
  position: fixed;
  inset: 0;
  z-index: 130;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background: rgba(8, 15, 12, 0.55);
}
.ifd-modal {
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 100%;
  max-width: 920px;
  max-height: calc(100dvh - 48px);
  overflow: auto;
  padding: 22px;
  border: 1px solid var(--border);
  border-radius: var(--radius-2xl, 20px);
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-elegant, 0 24px 60px rgba(0, 0, 0, 0.25));
}
.ifd-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.ifd-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted-foreground);
}
.ifd-title {
  margin-top: 2px;
  font-size: 20px;
  font-weight: 800;
  color: var(--foreground);
}
.ifd-sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--muted-foreground);
}
.ifd-close {
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: var(--muted);
  font-size: 20px;
  line-height: 1;
  color: var(--foreground);
}
.ifd-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  gap: 18px;
  align-items: start;
}
.ifd-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  padding: 12px;
  border-radius: 16px;
  background: var(--muted);
}
.ifd-pick {
  position: relative;
  display: inline-block;
  max-width: 100%;
  cursor: crosshair;
  touch-action: none;
  user-select: none;
}
.ifd-pick img {
  display: block;
  max-width: 100%;
  max-height: min(56vh, 460px);
  border-radius: 10px;
  pointer-events: none;
}
.ifd-marker {
  position: absolute;
  width: 30px;
  height: 30px;
  border: 3px solid #fff;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary, #12b981) 55%, transparent);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.35), 0 4px 14px rgba(0, 0, 0, 0.35);
  transform: translate(-50%, -50%);
  outline: none;
}
.ifd-marker:focus-visible {
  box-shadow: 0 0 0 3px var(--ring, #12b981), 0 4px 14px rgba(0, 0, 0, 0.35);
}
.ifd-previews {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.ifd-frame {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ifd-frame.is-mobile .ifd-shot {
  width: 62%;
  border-radius: 18px;
}
.ifd-shot {
  width: 100%;
  overflow: hidden;
  border-radius: 10px;
  background: var(--muted);
  box-shadow: inset 0 0 0 1px var(--border);
}
.ifd-shot img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.ifd-frame figcaption {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted-foreground);
}
.ifd-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.ifd-spacer {
  flex: 1;
}
.ifd-btn {
  height: 38px;
  padding: 0 18px;
  border-radius: 999px;
  background: var(--muted);
  box-shadow: inset 0 0 0 1px var(--border);
  font-size: 13.5px;
  font-weight: 700;
  color: var(--foreground);
}
.ifd-btn:disabled {
  opacity: 0.5;
}
.ifd-btn.is-ghost {
  background: transparent;
  box-shadow: none;
  padding: 0 6px;
  color: var(--muted-foreground);
}
.ifd-btn.is-primary {
  background: var(--primary, #12b981);
  box-shadow: none;
  color: var(--primary-foreground, #fff);
}
/* Celular: a foto em cima e as molduras lado a lado embaixo. */
@media (max-width: 720px) {
  .ifd-modal {
    padding: 16px;
  }
  .ifd-body {
    grid-template-columns: minmax(0, 1fr);
  }
  .ifd-previews {
    flex-direction: row;
    align-items: flex-start;
  }
  .ifd-frame {
    flex: 1 1 0;
    min-width: 0;
  }
  .ifd-frame.is-mobile .ifd-shot {
    width: 70%;
  }
  .ifd-pick img {
    max-height: 34vh;
  }
  /* Cancelar e Aplicar lado a lado; "Voltar ao padrão" embaixo. */
  .ifd-foot {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
  .ifd-spacer {
    display: none;
  }
  .ifd-btn.is-ghost {
    grid-column: 1 / -1;
    order: 3;
  }
}
</style>
