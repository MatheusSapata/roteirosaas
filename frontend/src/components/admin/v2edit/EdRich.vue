<template>
  <div class="ved-field ved-rich">
    <span class="ved-label">{{ label }}</span>
    <RichTextEditor :model-value="modelValue || ''" :placeholder="placeholder" :variant="variant" @update:model-value="emit('update:modelValue', $event)" />
    <p v-if="hint" class="ved-hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import RichTextEditor from "../inputs/RichTextEditor.vue";

defineProps<{ modelValue?: string | null; label: string; hint?: string; placeholder?: string; variant?: "basic" | "article" }>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();
</script>
