<template>
  <div class="section-heading-controls">
    <label class="text-sm font-semibold text-slate-600">{{ copy.label }}</label>
    <input
      v-model="headingText"
      :placeholder="copy.placeholder"
      class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
    />
    <p class="text-xs text-slate-500">{{ copy.hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { createAdminLocalizer } from "../../../utils/adminI18n";

const props = defineProps<{ label?: string; style?: "filled" | "outline" }>();
const emit = defineEmits<{
  (e: "update:label", value?: string): void;
  (e: "update:style", value: "filled" | "outline"): void;
}>();

const t = createAdminLocalizer();
const copy = {
  label: t({ pt: "Etiqueta acima do título", es: "Etiqueta encima del título" }),
  placeholder: t({ pt: "Ex.: Investimento", es: "Ej.: Inversión" }),
  hint: t({ pt: "Opcional. Deixe em branco para ocultar.", es: "Opcional. Déjalo en blanco para ocultarlo." })
};

const headingText = computed({
  get: () => props.label || "",
  set: value => {
    emit("update:label", value?.trim() ? value : "");
  }
});

onMounted(() => {
  if (!props.style) {
    emit("update:style", "outline");
  }
});
</script>

<style scoped>
.section-heading-controls { color: var(--foreground); }
.section-heading-controls label { color: var(--muted-foreground); }
.section-heading-controls input {
  border-color: var(--input);
  background: var(--card);
  color: var(--foreground);
}
.section-heading-controls input:focus {
  outline: none;
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 15%, transparent);
}
.section-heading-controls p { color: var(--muted-foreground); }
</style>
