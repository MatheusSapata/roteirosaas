<template>
  <RouterLink v-if="visible" to="/admin/administracao/bancos-de-fotos" class="su-chip" :class="{ 'is-done': !uploadState.running }">
    <span v-if="uploadState.running" class="su-spinner" aria-hidden="true"></span>
    <span v-else aria-hidden="true">✓</span>
    <span>{{ text }}</span>
  </RouterLink>
</template>

<script setup lang="ts">
/** Andamento do envio de fotos para o banco próprio, visível em qualquer página do admin. */
import { computed, ref, watch } from "vue";
import { uploadState } from "../../services/stockPhotoUploads";

const showDone = ref(false);
let hideTimer: ReturnType<typeof setTimeout> | null = null;
watch(
  () => uploadState.running,
  running => {
    if (running) return;
    showDone.value = true;
    if (hideTimer) clearTimeout(hideTimer);
    hideTimer = setTimeout(() => (showDone.value = false), 8000);
  }
);
const visible = computed(() => uploadState.running || (showDone.value && uploadState.total > 0));
const text = computed(() =>
  uploadState.running
    ? `Enviando fotos: ${uploadState.done} de ${uploadState.total}`
    : `Fotos enviadas: ${uploadState.added} novas${uploadState.skipped.length ? `, ${uploadState.skipped.length} com erro` : ""}`
);
</script>

<style scoped>
.su-chip {
  position: fixed;
  left: 50%;
  bottom: 20px;
  z-index: 60;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 999px;
  background: var(--foreground, #111);
  color: var(--background, #fff);
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  transform: translateX(-50%);
  text-decoration: none;
}
.su-chip.is-done {
  background: var(--primary, #0f7a4f);
  color: var(--primary-foreground, #fff);
}
.su-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 999px;
  animation: su-spin 0.8s linear infinite;
}
@keyframes su-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
