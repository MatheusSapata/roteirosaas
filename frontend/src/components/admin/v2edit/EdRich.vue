<template>
  <div class="ved-field ved-rich">
    <span class="ved-label">{{ label }}</span>
    <RichTextEditor :model-value="modelValue || ''" :placeholder="placeholder" :variant="variant" :no-align="variant !== 'article'" @update:model-value="emit('update:modelValue', $event)" />
    <p v-if="hint" class="ved-hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
// Textos curtos das seções não têm alinhamento próprio: segue o "Alinhamento" da seção
// (Aparência › Layout). O artigo (Biografia) mantém o botão.
import RichTextEditor from "../inputs/RichTextEditor.vue";

defineProps<{ modelValue?: string | null; label: string; hint?: string; placeholder?: string; variant?: "basic" | "article" }>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();
</script>
