<template>
  <div v-if="images.length" class="ppp">
    <span class="ppp-label">{{ label || "Ou escolha uma foto da página" }}</span>
    <div class="ppp-grid">
      <button
        v-for="url in images"
        :key="url"
        type="button"
        class="ppp-item"
        :class="{ 'is-active': url === modelValue }"
        :aria-pressed="url === modelValue"
        :aria-label="url === modelValue ? 'Foto escolhida' : 'Usar esta foto'"
        @click="emit('update:modelValue', url === modelValue ? '' : url)"
      >
        <img :src="url" alt="" loading="lazy" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
// Miniaturas das fotos que a página já tem; clicar de novo na escolhida desfaz a escolha.
defineProps<{ images: string[]; modelValue?: string | null; label?: string }>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();
</script>

<style scoped>
.ppp { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.ppp-label { font-size: 12px; font-weight: 600; color: #64748b; }
.ppp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(64px, 1fr)); gap: 6px; max-height: 220px; overflow-y: auto; }
.ppp-item {
  position: relative;
  aspect-ratio: 1;
  padding: 0;
  overflow: hidden;
  border: 2px solid transparent;
  border-radius: 8px;
  background: #f1f5f9;
  cursor: pointer;
}
.ppp-item img { width: 100%; height: 100%; object-fit: cover; display: block; }
.ppp-item:hover { border-color: #cbd5e1; }
.ppp-item.is-active { border-color: var(--primary, #12b981); box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary, #12b981) 30%, transparent); }
</style>
