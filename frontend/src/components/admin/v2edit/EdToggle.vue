<template>
  <button type="button" class="ved-toggle" role="switch" :aria-checked="!!modelValue" @click="emit('update:modelValue', !modelValue)">
    <span class="ved-toggle-text">
      <span class="ved-label">{{ label }}</span>
      <span v-if="hint" class="ved-hint">{{ hint }}</span>
    </span>
    <span class="ved-switch" :class="{ on: modelValue }" aria-hidden="true"></span>
  </button>
</template>

<script setup lang="ts">
defineProps<{ modelValue?: boolean; label: string; hint?: string }>();
const emit = defineEmits<{ (e: "update:modelValue", value: boolean): void }>();
</script>
