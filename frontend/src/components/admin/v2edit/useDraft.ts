import { computed } from "vue";
import { getCurrentLanguage, getLocalizedValue, type LocalizedString } from "../../../utils/i18n";

type Draft = Record<string, any>;
type Emit = (event: "update:modelValue", value: any) => void;

const lang = () => getCurrentLanguage();

/** Lê um texto que pode estar salvo por idioma ({ pt, es }) ou como texto simples. */
export const readText = (value: LocalizedString) => getLocalizedValue(value, lang());

/** Grava o texto mantendo os outros idiomas quando o valor já era por idioma. */
export const writeText = (previous: LocalizedString, next: string): LocalizedString =>
  previous && typeof previous === "object" ? { ...previous, [lang()]: next } : next;

/**
 * Campos do rascunho da seção para os formulários do editor novo.
 * Cada alteração devolve a seção inteira, como os formulários antigos fazem.
 */
export const useDraft = (props: { modelValue: Draft }, emit: Emit) => {
  const patch = (changes: Draft) => emit("update:modelValue", { ...props.modelValue, ...changes });

  /** Valor bruto (booleano, número, lista...). */
  const field = <T = any>(key: string, fallback?: T) =>
    computed<T>({
      get: () => (props.modelValue?.[key] ?? fallback) as T,
      set: value => patch({ [key]: value })
    });

  /** Texto por idioma. */
  const text = (key: string) =>
    computed<string>({
      get: () => readText(props.modelValue?.[key]),
      set: value => patch({ [key]: writeText(props.modelValue?.[key], value) })
    });

  return { patch, field, text };
};
