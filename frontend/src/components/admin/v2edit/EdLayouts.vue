<template>
  <div class="ved-layouts" role="radiogroup" aria-label="Layout">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      role="radio"
      :class="{ on: option.value === modelValue }"
      :aria-checked="option.value === modelValue"
      @click="emit('update:modelValue', option.value)"
    >
      <b>{{ option.label }}</b>
      <span v-if="option.desc">{{ option.desc }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue?: string | null; options: { value: string; label: string; desc?: string }[] }>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();
</script>
