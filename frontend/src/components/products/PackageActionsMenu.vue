<template>
  <details class="package-actions" @click.stop>
    <summary class="package-actions__trigger" aria-label="Mais acoes" @click.stop>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
        <path d="M12 5h.01" />
        <path d="M12 12h.01" />
        <path d="M12 19h.01" />
      </svg>
    </summary>

    <div class="package-actions__menu">
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
.package-actions {
  position: relative;
}

.package-actions__trigger {
  display: inline-flex;
  list-style: none;
  align-items: center;
  justify-content: center;
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 0.95rem;
  border: 1px solid rgba(203, 213, 225, 0.72);
  background: rgba(255, 255, 255, 0.92);
  color: #64748b;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.18s ease;
}

.package-actions__trigger::-webkit-details-marker {
  display: none;
}

.package-actions[open] .package-actions__trigger,
.package-actions__trigger:hover {
  transform: translateY(-1px);
  border-color: rgba(148, 163, 184, 0.74);
  background: rgba(248, 250, 252, 0.98);
  color: #334155;
  box-shadow: 0 14px 24px -22px rgba(15, 23, 42, 0.34);
}

.package-actions__trigger svg {
  width: 1rem;
  height: 1rem;
}

.package-actions__menu {
  position: absolute;
  top: calc(100% + 0.55rem);
  right: 0;
  z-index: 5;
  display: grid;
  min-width: 10.5rem;
  padding: 0.45rem;
  border-radius: 1rem;
  border: 1px solid rgba(226, 232, 240, 0.88);
  background: rgba(255, 255, 255, 0.98);
  box-shadow:
    0 20px 40px -28px rgba(15, 23, 42, 0.28),
    0 12px 20px -18px rgba(15, 23, 42, 0.22);
}

.package-actions__menu button {
  min-height: 2.35rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 0.8rem;
  background: transparent;
  color: #0f172a;
  font-weight: 600;
  text-align: left;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.package-actions__menu button:hover {
  background: #f8fafc;
}

.package-actions__menu .danger {
  color: #b91c1c;
}
</style>
