<template>
  <div class="ved-field">
    <span v-if="label" class="ved-label">{{ label }}</span>
    <div class="ved-seg" role="radiogroup" :aria-label="label">
      <button
        v-for="option in options"
        :key="String(option.value)"
        type="button"
        role="radio"
        :class="{ on: option.value === modelValue }"
        :aria-checked="option.value === modelValue"
        @click="emit('update:modelValue', option.value)"
      >
        {{ option.label }}
      </button>
    </div>
    <p v-if="hint" class="ved-hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue?: string | number | boolean | null; label?: string; hint?: string; options: { value: any; label: string }[] }>();
const emit = defineEmits<{ (e: "update:modelValue", value: any): void }>();
</script>
