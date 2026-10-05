<template>
  <div class="ved-field">
    <div class="ved-bg" role="radiogroup" aria-label="Fundo da seção">
      <button
        v-for="option in options"
        :key="option.id"
        type="button"
        role="radio"
        class="ved-bg-opt"
        :class="{ on: selected === option.id }"
        :aria-checked="selected === option.id"
        @click="pick(option.id, option.color)"
      >
        <span class="ved-bg-swatch" :style="{ background: option.swatch || option.color }"></span>
        {{ option.label }}
      </button>
      <label class="ved-bg-opt" :class="{ on: selected === 'custom' }">
        <span
          class="ved-bg-swatch"
          :style="{ background: selected === 'custom' ? current : 'conic-gradient(#f87171, #fbbf24, #34d399, #60a5fa, #a78bfa, #f87171)' }"
        >
          <input type="color" :value="current || '#ffffff'" aria-label="Outra cor de fundo" @input="pick('custom', ($event.target as HTMLInputElement).value)" />
        </span>
        Outra
      </label>
    </div>
    <p class="ved-hint">
      {{ auto ? "Página segue as cores de fundo de Configurações → Cores. " : "" }}Texto, cards e botões se ajustam sozinhos ao fundo.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { usePageDesignContext } from "../../public/v2/designContext";

const props = withDefaults(
  defineProps<{
    /** Seção inteira (ou o item) de onde vem a cor. */
    value: Record<string, any>;
    /** Campo da cor. */
    field?: string;
    /**
     * Seções que alternam as cores da página: "Página" volta para a alternância
     * e as demais opções marcam o fundo como escolhido (customBackground).
     */
    auto?: boolean;
    /** Cor usada quando a seção não tem cor salva. */
    fallback?: string;
  }>(),
  { field: "backgroundColor", auto: false, fallback: "#FFFFFF" }
);
const emit = defineEmits<{ (e: "change", value: Record<string, any>): void }>();
const design = usePageDesignContext();

const options = computed(() => [
  { id: "page", label: "Página", color: "#FFFFFF", swatch: props.auto ? "linear-gradient(135deg, #ffffff 50%, #f2f4f1 50%)" : "" },
  { id: "soft", label: "Suave", color: "#F2F4F1", swatch: "" },
  { id: "accent", label: "Destaque", color: design.value.accent, swatch: "" },
  { id: "dark", label: "Escuro", color: "#0E1A15", swatch: "" }
]);
const current = computed(() => String(props.value?.[props.field] || props.fallback || "").trim());
const selected = computed(() => {
  if (props.auto && !props.value?.customBackground) return "page";
  const value = current.value.toLowerCase();
  const match = options.value.find(option => option.color.toLowerCase() === value);
  if (match && !(props.auto && match.id === "page")) return match.id;
  return value ? "custom" : "page";
});
const pick = (id: string, color: string) => {
  if (props.auto) {
    emit("change", id === "page" ? { customBackground: false } : { [props.field]: color, customBackground: true });
    return;
  }
  emit("change", { [props.field]: color });
};
</script>
