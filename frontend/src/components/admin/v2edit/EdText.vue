<template>
  <label class="ved-field">
    <span class="ved-label">{{ label }}</span>
    <textarea
      v-if="multiline"
      class="ved-input"
      :value="modelValue ?? ''"
      :placeholder="placeholder"
      :maxlength="maxlength"
      rows="3"
      @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>
    <input
      v-else
      class="ved-input"
      :type="type || 'text'"
      :value="modelValue ?? ''"
      :placeholder="placeholder"
      :maxlength="maxlength"
      :min="min"
      :inputmode="type === 'number' ? 'decimal' : undefined"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="hint" class="ved-hint">{{ hint }}</p>
  </label>
</template>

<script setup lang="ts">
defineProps<{
  modelValue?: string | number | null;
  label: string;
  hint?: string;
  placeholder?: string;
  multiline?: boolean;
  type?: "text" | "url" | "date" | "datetime-local" | "number" | "tel";
  maxlength?: number;
  min?: string;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();
</script>
