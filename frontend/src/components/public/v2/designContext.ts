import { computed, inject, type ComputedRef, type InjectionKey } from "vue";

export interface PageDesignContext {
  /** Cor de destaque da página (Configurações → Cores). */
  accent: string;
}

export const PAGE_DESIGN_KEY: InjectionKey<ComputedRef<PageDesignContext>> = Symbol("page-design");

export const DEFAULT_ACCENT = "#12B981";

export const usePageDesignContext = () => {
  const ctx = inject(PAGE_DESIGN_KEY, null);
  return computed<PageDesignContext>(() => ctx?.value ?? { accent: DEFAULT_ACCENT });
};
