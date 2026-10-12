<template>
  <Teleport to="body">
    <transition name="amc">
      <div v-if="open" class="amc-root admin-master-surface" role="alertdialog" aria-modal="true" :aria-label="title" @keydown.esc="!busy && $emit('close')">
        <div class="amc-overlay" @click="!busy && $emit('close')"></div>
        <div class="amc-panel">
          <div class="flex items-start gap-3">
            <span class="am-tile !h-9 !w-9 !rounded-xl" :class="`am-tone-${tone}`"><AmIcon :name="icon" /></span>
            <div class="min-w-0 flex-1">
              <h2 class="amc-title">{{ title }}</h2>
              <div class="amc-body"><slot /></div>
            </div>
          </div>
          <div v-if="error" class="am-notice am-tone-danger mt-4"><AmIcon name="alert" /><span>{{ error }}</span></div>
          <div class="mt-5 flex flex-wrap justify-end gap-2">
            <button type="button" class="am-btn" :disabled="busy" @click="$emit('close')">Cancelar</button>
            <button
              type="button"
              class="am-btn"
              :class="tone === 'danger' ? 'am-btn-danger' : 'am-btn-primary'"
              :disabled="busy || disabled"
              @click="$emit('confirm')"
            >
              {{ busy ? busyLabel : confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import AmIcon from "./AmIcon.vue";

withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    confirmLabel?: string;
    busyLabel?: string;
    busy?: boolean;
    disabled?: boolean;
    error?: string;
    icon?: string;
    tone?: "danger" | "warning" | "info" | "success" | "neutral";
  }>(),
  { confirmLabel: "Confirmar", busyLabel: "Salvando...", busy: false, disabled: false, error: "", icon: "alert", tone: "warning" }
);
defineEmits<{ (e: "close"): void; (e: "confirm"): void }>();
</script>

<style scoped>
.amc-root {
  position: fixed;
  inset: 0;
  z-index: 130;
  display: grid;
  place-items: center;
  padding: 16px;
}
.amc-overlay {
  position: absolute;
  inset: 0;
  background: var(--modal-overlay, rgba(0, 0, 0, 0.55));
}
.amc-panel {
  position: relative;
  width: min(480px, 100%);
  max-height: calc(100vh - 32px);
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--card);
  color: var(--card-foreground);
  padding: 20px;
  box-shadow: var(--shadow-elegant);
}
.amc-title {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--foreground);
}
.amc-body {
  margin-top: 6px;
  font-size: 13.5px;
  line-height: 1.5;
  color: var(--muted-foreground);
}
.amc-enter-active,
.amc-leave-active {
  transition: opacity 0.15s ease;
}
.amc-enter-from,
.amc-leave-to {
  opacity: 0;
}
</style>
