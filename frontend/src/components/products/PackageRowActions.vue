<template>
  <details class="package-row-actions__menu">
    <summary class="package-row-actions__trigger" aria-label="Mais acoes">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
        <path d="M12 5h.01" />
        <path d="M12 12h.01" />
        <path d="M12 19h.01" />
      </svg>
    </summary>

    <div class="package-row-actions__dropdown">
      <button type="button" @click="$emit('duplicate')">Duplicar</button>
      <button type="button" class="danger" @click="$emit('remove')">Remover</button>
    </div>
  </details>
</template>

<script setup lang="ts">
defineEmits<{
  (e: "duplicate"): void;
  (e: "remove"): void;
}>();
</script>

<style scoped>
.package-row-actions__menu {
  position: relative;
  z-index: 20;
}

.package-row-actions__trigger {
  display: inline-flex;
  list-style: none;
  align-items: center;
  justify-content: center;
  width: 2.65rem;
  height: 2.65rem;
  border-radius: 1rem;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.96);
  color: #64748b;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.18s ease,
    box-shadow 0.2s ease;
}

.package-row-actions__trigger::-webkit-details-marker {
  display: none;
}

.package-row-actions__menu[open] .package-row-actions__trigger,
.package-row-actions__trigger:hover {
  transform: translateY(-1px);
  border-color: rgba(203, 213, 225, 0.98);
  background: #f8fafc;
  color: #334155;
  box-shadow: 0 14px 24px -22px rgba(15, 23, 42, 0.22);
}

.package-row-actions__trigger svg {
  width: 1rem;
  height: 1rem;
}

.package-row-actions__dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  z-index: 30;
  display: grid;
  min-width: 10rem;
  padding: 0.4rem;
  border-radius: 1rem;
  border: 1px solid rgba(226, 232, 240, 0.92);
  background: rgba(255, 255, 255, 0.99);
  box-shadow:
    0 20px 40px -28px rgba(15, 23, 42, 0.22),
    0 14px 24px -20px rgba(15, 23, 42, 0.18);
}

.package-row-actions__dropdown button {
  min-height: 2.35rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 0.8rem;
  background: transparent;
  color: #0f172a;
  text-align: left;
  font-weight: 600;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.package-row-actions__dropdown button:hover {
  background: #f8fafc;
}

.package-row-actions__dropdown .danger {
  color: #e11d48;
}
</style>
