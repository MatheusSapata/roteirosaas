<template>
  <a class="v2-btn" :class="{ 'v2-btn--ghost': ghost, 'v2-btn--block': block }" v-bind="attrs">
    <span><slot /></span>
    <svg v-if="arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
  </a>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ attrs: Record<string, unknown>; ghost?: boolean; block?: boolean; arrow?: boolean }>(), {
  ghost: false,
  block: false,
  arrow: true
});
</script>
