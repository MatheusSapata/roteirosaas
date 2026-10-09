<template>
  <label class="ved-field">
    <span class="ved-label ved-range-head">
      <span>{{ label }}</span>
      <output class="ved-range-value">{{ display }}</output>
    </span>
    <input
      class="ved-range"
      type="range"
      :min="min"
      :max="max"
      :step="step || 1"
      :value="current"
      :style="{ '--ved-range-fill': `${fill}%` }"
      @input="emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
    />
    <p v-if="hint" class="ved-hint">{{ hint }}</p>
  </label>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ modelValue?: number | null; label: string; min: number; max: number; step?: number; unit?: string; hint?: string }>();
const emit = defineEmits<{ (e: "update:modelValue", value: number): void }>();
const current = computed(() => Math.min(props.max, Math.max(props.min, Number(props.modelValue ?? props.min))));
const fill = computed(() => ((current.value - props.min) / Math.max(1, props.max - props.min)) * 100);
const display = computed(() => `${current.value}${props.unit || ""}`);
</script>
