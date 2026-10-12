<template>
  <component :is="tag" ref="el" class="fit" :class="{ 'fit-fill': fill, 'fit-line': line }" :style="style">
    <slot />
  </component>
</template>

<script setup lang="ts">
/**
 * Texto (ou bloco) que se ajusta à área onde está: encontra o maior tamanho de fonte entre
 * `min` e `max` que cabe sem estourar. Tudo dentro do bloco deve ser medido em `em`, assim
 * preço, rótulos e listas crescem e encolhem juntos.
 *
 * - `fill`: o bloco ocupa a altura que o layout der (região com altura definida) e precisa caber nela.
 * - `line`: uma linha só (cabe na largura).
 * - `lines`: no máximo N linhas.
 * Palavras nunca são quebradas no meio: se uma palavra não cabe na largura, a fonte diminui.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";

const props = withDefaults(
  defineProps<{ max: number; min?: number; tag?: string; fill?: boolean; line?: boolean; lines?: number; lineHeight?: number }>(),
  { min: 10, tag: "div", fill: false, line: false, lines: 0, lineHeight: 1.05 }
);

const el = ref<HTMLElement | null>(null);
const size = ref(props.max);
// Com limite de linhas, a altura da linha vem daqui para a medição bater com o que aparece.
const style = computed(() => ({ fontSize: `${size.value}px`, ...(props.lines ? { lineHeight: String(props.lineHeight) } : {}) }));
let resizeObserver: ResizeObserver | null = null;
let mutationObserver: MutationObserver | null = null;
let frame = 0;

/**
 * Caixa ocupada pelo conteúdo: a caixa de cada elemento filho e, para texto solto, a do texto.
 * Usar a caixa dos filhos (e não o contorno das letras) evita contar como "estouro" a sobra
 * natural das letras grandes de um título com entrelinha apertada dentro do bloco.
 */
const contentBox = (element: HTMLElement) => {
  let top = Infinity;
  let left = Infinity;
  let right = -Infinity;
  let bottom = -Infinity;
  const add = (rect: DOMRect) => {
    if (!rect.width && !rect.height) return;
    top = Math.min(top, rect.top);
    left = Math.min(left, rect.left);
    right = Math.max(right, rect.right);
    bottom = Math.max(bottom, rect.bottom);
  };
  element.childNodes.forEach(node => {
    if (node.nodeType === Node.ELEMENT_NODE) add((node as Element).getBoundingClientRect());
    else if (node.nodeType === Node.TEXT_NODE && node.textContent?.trim()) {
      const range = document.createRange();
      range.selectNodeContents(node);
      add(range.getBoundingClientRect());
    }
  });
  return top === Infinity ? null : { top, left, right, bottom };
};

const fits = (element: HTMLElement, px: number) => {
  element.style.fontSize = `${px}px`;
  if (element.scrollWidth > element.clientWidth + 1) return false;
  if (props.lines) {
    // A parte de baixo das letras passa um pouco da última linha e entra na medida; a folga
    // cobre isso (uma linha a mais ocupa bem mais que 0,25em).
    if (element.scrollHeight > px * props.lineHeight * props.lines + px * 0.25 + 1) return false;
  }
  if (props.fill) {
    // Pega também o que estoura para cima ou para os lados quando o bloco está centralizado (o
    // que scrollHeight não mede). As medidas da tela vêm com a escala da prévia.
    const box = element.getBoundingClientRect();
    if (!box.height || !element.offsetHeight) return true;
    const content = contentBox(element);
    if (!content) return true;
    const scale = box.height / element.offsetHeight;
    const slackY = (px * 0.2 + 1) * scale;
    const slackX = 2 * scale;
    if (content.top < box.top - slackY || content.bottom > box.bottom + slackY) return false;
    if (content.left < box.left - slackX || content.right > box.right + slackX) return false;
  }
  return true;
};

const fit = () => {
  const element = el.value;
  if (!element || !element.isConnected) return;
  let low = props.min;
  let high = props.max;
  if (fits(element, high)) {
    size.value = high;
    return;
  }
  // Busca binária: ~10 medições até 0,5 px de precisão.
  while (high - low > 0.5) {
    const middle = (low + high) / 2;
    if (fits(element, middle)) low = middle;
    else high = middle;
  }
  size.value = Math.floor(low * 2) / 2;
  element.style.fontSize = `${size.value}px`;
};

const schedule = () => {
  cancelAnimationFrame(frame);
  frame = requestAnimationFrame(fit);
};

onMounted(async () => {
  await nextTick();
  fit();
  const element = el.value;
  if (!element) return;
  if ("ResizeObserver" in window) {
    resizeObserver = new ResizeObserver(schedule);
    resizeObserver.observe(element);
    if (element.parentElement) resizeObserver.observe(element.parentElement);
  }
  mutationObserver = new MutationObserver(schedule);
  mutationObserver.observe(element, { childList: true, subtree: true, characterData: true });
  // Fontes carregadas depois mudam a largura do texto.
  document.fonts?.ready.then(schedule);
  document.fonts?.addEventListener?.("loadingdone", schedule);
});

onBeforeUnmount(() => {
  cancelAnimationFrame(frame);
  resizeObserver?.disconnect();
  mutationObserver?.disconnect();
  document.fonts?.removeEventListener?.("loadingdone", schedule);
});

defineExpose({ fit });
</script>

<style scoped>
/*
 * :where() deixa estas regras com prioridade mínima: o modelo que usa o FitText pode mudar
 * largura, flex e display à vontade. Sem "fill", o bloco não encolhe dentro de uma coluna flex
 * (encolher cortaria o texto em vez de diminuir a fonte); com "fill", ocupa o espaço que sobrar.
 */
:where(.fit) {
  min-width: 0;
  max-width: 100%;
  flex: none;
  overflow-wrap: normal;
  word-break: normal;
  hyphens: none;
}
:where(.fit-fill) {
  width: 100%;
  height: 100%;
  min-height: 0;
  flex: 1 1 0;
}
:where(.fit-line) {
  white-space: nowrap;
}
</style>
