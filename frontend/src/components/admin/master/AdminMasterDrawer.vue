<template>
  <Teleport to="body">
    <transition name="amd">
      <div v-if="open" class="amd-root" role="dialog" aria-modal="true" :aria-label="title" @keydown.esc="$emit('close')">
        <div class="amd-overlay" @click="$emit('close')"></div>
        <aside class="amd-panel" :style="{ width: `min(${width}px, calc(100vw - 24px))` }">
          <header class="amd-head">
            <span v-if="icon" class="am-tile !h-[38px] !w-[38px] !rounded-xl" :class="`am-tone-${tone}`"><AmIcon :name="icon" /></span>
            <div class="min-w-0 flex-1">
              <h2 class="amd-title">{{ title }}</h2>
              <p v-if="subtitle" class="amd-sub">{{ subtitle }}</p>
            </div>
            <button type="button" class="am-icon-btn" aria-label="Fechar" @click="$emit('close')"><AmIcon name="x" /></button>
          </header>
          <div class="amd-body"><slot /></div>
          <footer v-if="$slots.footer" class="amd-foot"><slot name="footer" /></footer>
        </aside>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import AmIcon from "./AmIcon.vue";

withDefaults(
  defineProps<{ open: boolean; title: string; subtitle?: string; icon?: string; tone?: string; width?: number }>(),
  { subtitle: "", icon: "", tone: "success", width: 520 }
);
defineEmits<{ (e: "close"): void }>();
</script>

<style scoped>
.amd-root {
  position: fixed;
  inset: 0;
  z-index: 120;
}
.amd-overlay {
  position: absolute;
  inset: 0;
  background: var(--modal-overlay, rgba(0, 0, 0, 0.55));
}
.amd-panel {
  position: absolute;
  top: 12px;
  right: 12px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  border-radius: 22px;
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-elegant);
}
.amd-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 22px 22px 14px;
}
.amd-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--foreground);
}
.amd-sub {
  margin-top: 2px;
  font-size: 13px;
  color: var(--muted-foreground);
}
.amd-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 22px 18px;
}
.amd-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 22px;
  border-top: 1px solid var(--border);
}
.amd-enter-active,
.amd-leave-active {
  transition: opacity 0.18s ease;
}
.amd-enter-active .amd-panel,
.amd-leave-active .amd-panel {
  transition: transform 0.2s ease;
}
.amd-enter-from,
.amd-leave-to {
  opacity: 0;
}
.amd-enter-from .amd-panel,
.amd-leave-to .amd-panel {
  transform: translateX(24px);
}
</style>
