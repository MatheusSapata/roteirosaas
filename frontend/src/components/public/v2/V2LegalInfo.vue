<template>
  <p ref="root" class="v2-legal" :class="`is-${align}`">
    <span>{{ copyrightLine }}</span>
    <span class="v2-legal-anchor">
      <button
        type="button"
        class="v2-legal-btn"
        :class="{ 'is-open': open }"
        :aria-expanded="open"
        :aria-controls="noteId"
        :aria-label="copy.toggle"
        :title="copy.toggle"
        @click="toggle"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M12 11v6M12 7.5v.01" /></svg>
      </button>
      <!-- Balão por cima do rodapé (não aumenta a seção), apontando para o (i). -->
      <Transition name="v2-legal-pop">
        <span v-if="open" ref="noteEl" :id="noteId" class="v2-legal-note" role="note" :style="{ '--v2-legal-shift': `${shift}px` }">{{ note }}</span>
      </Transition>
    </span>
  </p>
</template>

<script setup lang="ts">
/**
 * "© ano Empresa · CNPJ (i)" do rodapé. O (i) abre, num balão por cima, o aviso de que o
 * conteúdo e as imagens são responsabilidade da agência (a plataforma só fornece a ferramenta).
 * Fecha ao clicar fora, no (i) de novo ou com Esc.
 */
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { getCurrentLanguage } from "../../../utils/i18n";
import { localize } from "./useHeading";

const props = withDefaults(
  defineProps<{ companyName?: string; cnpj?: string; hasContacts?: boolean; align?: "start" | "end" | "center"; id?: string }>(),
  { companyName: "", cnpj: "", hasContacts: false, align: "end", id: "rodape" }
);

const copy = { toggle: localize({ pt: "Sobre o conteúdo desta página", es: "Sobre el contenido de esta página" }) };
const root = ref<HTMLElement | null>(null);
const open = ref(false);
const noteEl = ref<HTMLElement | null>(null);
// Deslocamento do balão para a direita, para caber na tela (no celular o (i) pode estar perto
// da borda esquerda); a ponta continua apontando para o (i).
const shift = ref(0);
const fitNote = () => {
  const el = noteEl.value;
  if (!el || typeof window === "undefined") return;
  const rect = el.getBoundingClientRect();
  // A página pública é exibida em escala (zoom 0,9): converte pixels da tela em pixels do CSS.
  const scale = el.offsetWidth ? rect.width / el.offsetWidth : 1;
  const margin = 12;
  let delta = 0;
  if (rect.left < margin) delta = margin - rect.left;
  if (rect.right + delta > window.innerWidth - margin) delta = window.innerWidth - margin - rect.right;
  shift.value = Math.round(delta / scale);
};
const toggle = () => {
  open.value = !open.value;
  shift.value = 0;
  if (open.value) nextTick(fitNote);
};
const noteId = computed(() => `v2-legal-${props.id}`);
const year = new Date().getFullYear();

const copyrightLine = computed(() => {
  const doc = props.cnpj ? ` · CNPJ ${props.cnpj}` : "";
  const fallback = getCurrentLanguage() === "es" ? "Agencia" : "Agência";
  return `© ${year} ${props.companyName || fallback}${doc}`;
});

const note = computed(() => {
  const name = props.companyName;
  if (getCurrentLanguage() === "es") {
    const who = name ? name : "la agencia";
    return [
      `Los textos, imágenes, precios y ofertas de esta página son publicados por ${who}, que responde por ellos con exclusividad, incluso por el derecho de uso de las imágenes.`,
      `Las dudas o reclamos deben enviarse a la agencia${props.hasContacts ? " por los contactos indicados" : ""}.`,
      "Roteiro Online solo ofrece la herramienta de creación de la página y no responde por el contenido publicado."
    ].join(" ");
  }
  const by = name ? `por ${name}` : "pela agência";
  return [
    `Textos, imagens, preços e ofertas desta página são publicados ${by}, que responde por eles com exclusividade, inclusive pelo direito de uso das imagens.`,
    `Dúvidas ou contestações devem ser enviadas à agência${props.hasContacts ? " pelos contatos acima" : ""}.`,
    "O Roteiro Online apenas fornece a ferramenta de criação da página e não responde pelo conteúdo publicado."
  ].join(" ");
});

const onDocumentClick = (event: MouseEvent) => {
  if (root.value && !root.value.contains(event.target as Node)) open.value = false;
};
const onKey = (event: KeyboardEvent) => {
  if (event.key === "Escape") open.value = false;
};
watch(open, value => {
  if (typeof document === "undefined") return;
  if (value) {
    document.addEventListener("click", onDocumentClick, true);
    document.addEventListener("keydown", onKey);
  } else {
    document.removeEventListener("click", onDocumentClick, true);
    document.removeEventListener("keydown", onKey);
  }
});
onBeforeUnmount(() => {
  if (typeof document === "undefined") return;
  document.removeEventListener("click", onDocumentClick, true);
  document.removeEventListener("keydown", onKey);
});
</script>

<style scoped>
.v2-legal {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}
.v2-legal.is-end {
  justify-content: flex-end;
}
.v2-legal.is-center {
  justify-content: center;
  text-align: center;
}
.v2-legal-anchor {
  position: relative;
  display: inline-flex;
}
.v2-legal-btn {
  display: inline-grid;
  place-items: center;
  width: 22px;
  height: 22px;
  flex: none;
  padding: 0;
  border: 1px solid currentColor;
  border-radius: 999px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  opacity: 0.85;
  transition: background-color 0.15s ease, color 0.15s ease, opacity 0.15s ease;
}
/* Área de toque maior que o desenho, para o dedo acertar no celular. */
.v2-legal-btn::before {
  content: "";
  position: absolute;
  inset: -11px;
}
/* Fundo na própria cor do texto, para funcionar no rodapé claro e no escuro. */
.v2-legal-btn:hover,
.v2-legal-btn.is-open {
  opacity: 1;
  background: color-mix(in srgb, currentColor 16%, transparent);
}
/* Balão: abre para cima, por cima do que estiver ali, com a ponta no (i). */
.v2-legal-note {
  position: absolute;
  z-index: 50;
  bottom: calc(100% + 12px);
  right: calc(-12px - var(--v2-legal-shift, 0px));
  width: min(340px, calc(100vw - 32px));
  padding: 14px 16px;
  border-radius: 14px;
  background: #fff;
  color: #2b3530;
  box-shadow: 0 18px 40px -16px rgba(6, 12, 9, 0.45), 0 2px 6px rgba(6, 12, 9, 0.12);
  font-size: 12.5px;
  line-height: 1.6;
  text-align: left;
  white-space: normal;
}
.v2-legal-note::after {
  content: "";
  position: absolute;
  top: 100%;
  right: calc(18px + var(--v2-legal-shift, 0px));
  border: 7px solid transparent;
  border-top-color: #fff;
}
.v2-legal-pop-enter-active,
.v2-legal-pop-leave-active {
  transition: opacity 0.16s ease-out, translate 0.16s ease-out;
}
.v2-legal-pop-enter-from,
.v2-legal-pop-leave-to {
  opacity: 0;
  translate: 0 6px;
}
@media (prefers-reduced-motion: reduce) {
  .v2-legal-pop-enter-active,
  .v2-legal-pop-leave-active {
    transition: none;
  }
}
</style>
