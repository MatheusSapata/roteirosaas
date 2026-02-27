<template>
  <div>
    <label class="text-sm font-semibold text-slate-600">Etiqueta acima do título</label>
    <input
      v-model="headingText"
      placeholder="Ex.: Investimento"
      class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
    />
    <p class="text-xs text-slate-500">Opcional. Deixe em branco para ocultar.</p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";

const props = defineProps<{ label?: string; style?: "filled" | "outline" }>();
const emit = defineEmits<{
  (e: "update:label", value?: string): void;
  (e: "update:style", value: "filled" | "outline"): void;
}>();

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
