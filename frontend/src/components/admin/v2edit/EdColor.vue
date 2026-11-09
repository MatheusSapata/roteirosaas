<template>
  <label class="ved-field">
    <span class="ved-label">{{ label }}</span>
    <span class="edc-row">
      <span class="edc-swatch" :style="{ background: normalized }">
        <input type="color" :value="normalized" :aria-label="label" @input="onPick($event)" />
      </span>
      <input class="ved-input edc-hex" type="text" :value="modelValue || ''" :placeholder="fallback" maxlength="7" @input="onHex($event)" />
    </span>
    <p v-if="hint" class="ved-hint">{{ hint }}</p>
  </label>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{ modelValue?: string; label: string; hint?: string; fallback?: string }>(), { fallback: "#F59E0B" });
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();

const normalized = computed(() => (/^#([0-9a-f]{6})$/i.test(props.modelValue || "") ? (props.modelValue as string) : props.fallback));
const onPick = (event: Event) => emit("update:modelValue", (event.target as HTMLInputElement).value);
const onHex = (event: Event) => emit("update:modelValue", (event.target as HTMLInputElement).value);
</script>

<style scoped>
.edc-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.edc-swatch {
  position: relative;
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  overflow: hidden;
  border-radius: 10px;
  box-shadow: inset 0 0 0 1px var(--border, rgba(0, 0, 0, 0.12));
}
.edc-swatch input[type="color"] {
  position: absolute;
  inset: -4px;
  width: calc(100% + 8px);
  height: calc(100% + 8px);
  padding: 0;
  border: 0;
  cursor: pointer;
}
.edc-hex {
  flex: 1 1 auto;
  text-transform: uppercase;
}
</style>
