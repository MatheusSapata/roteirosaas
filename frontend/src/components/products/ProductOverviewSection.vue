<template>
  <section class="overview-shell">
    <header class="section-head">
      <div>
        <p class="eyebrow">Visao geral</p>
        <h2>Contexto comercial do produto</h2>
      </div>
      <button type="button" class="section-link" @click="$emit('edit')">Editar dados</button>
    </header>

    <div class="overview-copy">
      <p>{{ summary }}</p>
    </div>

    <div class="attribute-strip">
      <span class="attribute-chip" :class="`attribute-chip--${statusTone}`">{{ statusLabel }}</span>
      <span class="attribute-chip">{{ inventoryLabel }}</span>
      <span class="attribute-chip">{{ oversellLabel }}</span>
      <span class="attribute-chip">{{ roadTripLabel }}</span>
      <span class="attribute-chip">{{ accommodationLabel }}</span>
    </div>

    <div class="section-divider"></div>

    <dl class="meta-list">
      <div class="meta-row">
        <dt>Data</dt>
        <dd>{{ tripDate }}</dd>
      </div>
      <div class="meta-row">
        <dt>Operacao</dt>
        <dd>{{ operationLabel }}</dd>
      </div>
      <div class="meta-row">
        <dt>Infantil</dt>
        <dd>{{ childPolicySummary }}</dd>
      </div>
    </dl>
  </section>
 </template>

<script setup lang="ts">
defineProps<{
  summary: string;
  statusLabel: string;
  statusTone: "success" | "muted" | "warning";
  inventoryLabel: string;
  oversellLabel: string;
  roadTripLabel: string;
  accommodationLabel: string;
  tripDate: string;
  operationLabel: string;
  childPolicySummary: string;
}>();

defineEmits<{
  (e: "edit"): void;
}>();
</script>

<style scoped>
.overview-shell {
  display: flex;
  flex-direction: column;
  gap: 1.45rem;
  padding: 1.65rem;
  border-radius: 1.75rem;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.7);
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.overview-shell:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.74rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.section-head h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: #0f172a;
}

.section-link {
  border: none;
  background: transparent;
  padding: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: #0f172a;
}

.overview-copy {
  max-width: 60ch;
}

.overview-copy p {
  margin: 0;
  font-size: 0.96rem;
  line-height: 1.9;
  color: #475569;
}

.attribute-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.attribute-chip {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0.34rem 0.82rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #334155;
  background: rgba(248, 250, 252, 0.88);
  border: 1px solid rgba(226, 232, 240, 0.88);
}

.attribute-chip--success {
  color: #0f766e;
  border-color: rgba(45, 212, 191, 0.25);
  background: rgba(240, 253, 250, 0.96);
}

.attribute-chip--muted {
  color: #475569;
}

.attribute-chip--warning {
  color: #9a3412;
  border-color: rgba(251, 146, 60, 0.24);
  background: rgba(255, 247, 237, 0.96);
}

.section-divider {
  height: 1px;
  background: rgba(226, 232, 240, 0.72);
}

.meta-list {
  margin: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.meta-row {
  display: flex;
  flex-direction: column;
  gap: 0.42rem;
  padding: 0.1rem 0;
}

.meta-row dt,
.meta-row dd {
  margin: 0;
}

.meta-row dt {
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.meta-row dd {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #020617;
  font-weight: 600;
}

@media (max-width: 960px) {
  .meta-list {
    grid-template-columns: 1fr;
  }

  .meta-row {
    gap: 0.3rem;
  }
}

@media (max-width: 720px) {
  .overview-shell {
    padding: 1.25rem;
    border-radius: 1.35rem;
  }

  .section-head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
