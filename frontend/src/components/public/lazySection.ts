import { defineAsyncComponent, defineComponent, h, inject, type Component, type InjectionKey } from "vue";

/**
 * Página pública de verdade: enquanto o arquivo de uma seção baixa, ela já ocupa espaço.
 * Sem isso a página fica com a altura só do Banner e, no iPhone, o scroll "bate" no fim
 * (efeito elástico) até as seções chegarem. Prévias e miniaturas não fornecem a chave.
 */
export const SECTION_PLACEHOLDER_KEY: InjectionKey<boolean> = Symbol("section-placeholder");

const SectionPlaceholder = defineComponent({
  name: "SectionPlaceholder",
  setup() {
    const reserve = inject(SECTION_PLACEHOLDER_KEY, false);
    return () => h("div", { "aria-hidden": "true", style: reserve ? { minHeight: "70vh" } : undefined });
  }
});

/** Seção baixada à parte, com o espaço reservado desde o primeiro instante (sem os 200ms padrão). */
export const lazySection = (loader: () => Promise<{ default: Component } | Component>) =>
  defineAsyncComponent({ loader: loader as () => Promise<Component>, loadingComponent: SectionPlaceholder, delay: 0 });
