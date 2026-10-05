import { computed, type Ref } from "vue";
import { usePageDesignContext } from "./designContext";
import { computeSectionTone } from "./useSectionTone";

/**
 * Para seções com muita lógica própria (voos, checkout, formulário), o v2 mantém
 * o componente atual e só troca as cores: destaque da página e texto pelo fundo.
 */
export const useThemedTone = (background: Ref<string | null | undefined>, fallbackBg = "#FFFFFF") => {
  const design = usePageDesignContext();
  return computed(() => computeSectionTone(background.value, design.value.accent, fallbackBg));
};
