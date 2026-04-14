<template>
<article class="package-card">
  <header class="package-header">
    <div class="package-info">
      <p class="eyebrow">Pacote</p>
      <h3>{{ variation.name }}</h3>
      <p class="muted" v-if="variation.description">{{ variation.description }}</p>
      <div class="package-badges">
        <span class="status" :class="statusClass">{{ statusLabel }}</span>
        <span class="badge" v-if="variation.has_accommodation">{{ accommodationLabel }}</span>
      </div>
    </div>
    <div class="price-block">
      <p>A partir de</p>
      <strong>{{ formatCurrency(variation.price) }}</strong>
      <span>/ pessoa</span>
    </div>
  </header>

  <div class="package-body">
    <dl>
      <dt>Pessoas incluidas</dt>
      <dd>{{ variation.people_included }}</dd>
    </dl>
    <dl>
      <dt>Controle de estoque</dt>
      <dd>{{ stockLabel }}</dd>
    </dl>
    <dl>
      <dt>Status</dt>
      <dd>{{ variation.status === "active" ? "Disponivel" : "Indisponivel" }}</dd>
    </dl>
  </div>

  <footer>
    <div class="actions">
      <button type="button" class="btn" @click="$emit('edit', variation)">Editar pacote</button>
      <button type="button" class="btn ghost" @click="$emit('duplicate', variation)">Duplicar</button>
    </div>
    <button type="button" class="icon-btn" title="Mais acoes" aria-label="Mais acoes" @click="$emit('remove', variation)">⋯</button>
  </footer>
</article>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  variation: {
    name: string;
    description: string | null;
    price: number;
    people_included: number;
    status: string;
    stock_mode: string;
    has_accommodation: boolean;
    accommodation_mode: "private" | "shared";
    room_capacity: number;
    slots_per_unit: number;
    total_slots: number | null;
    available_slots: number | null;
  };
}>();

defineEmits<{
  (e: "edit", variation: typeof props.variation): void;
  (e: "duplicate", variation: typeof props.variation): void;
  (e: "remove", variation: typeof props.variation): void;
}>();

const statusLabel = computed(() => (props.variation.status === "active" ? "Ativo" : "Inativo"));
const statusClass = computed(() => (props.variation.status === "active" ? "status-active" : "status-muted"));
const stockLabel = computed(() =>
  props.variation.stock_mode === "variant"
    ? `${props.variation.available_slots ?? 0}/${props.variation.total_slots ?? 0}`
    : "Segue produto",
);
const accommodationLabel = computed(() => {
  if (props.variation.accommodation_mode === "private") {
    return `Privativo - ${props.variation.room_capacity} pax`;
  }
  return `Compartilhado - ${props.variation.slots_per_unit} vagas`;
});

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
</script>

<style scoped>
.package-card {
  border: 1px solid #e2e8f0;
  border-radius: 1.5rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8fafc, #ffffff);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.package-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.package-info h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.4rem;
}
.package-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.price-block {
  text-align: right;
  min-width: 160px;
}
.price-block p {
  font-size: 0.75rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}
.price-block strong {
  font-size: 1.6rem;
  font-weight: 700;
  color: #0f172a;
}
.price-block span {
  font-size: 0.8rem;
  color: #94a3b8;
}
.badge {
  border-radius: 999px;
  padding: 0.25rem 0.7rem;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid rgba(15, 23, 42, 0.1);
  color: #475569;
}
.status {
  border-radius: 999px;
  padding: 0.25rem 0.85rem;
  font-size: 0.75rem;
  font-weight: 600;
}
.status-active {
  background: rgba(16, 185, 129, 0.15);
  color: #047857;
}
.status-muted {
  background: rgba(148, 163, 184, 0.2);
  color: #475569;
}
.package-body {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
}
.package-body dl {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.package-body dt {
  font-size: 0.7rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #94a3b8;
}
.package-body dd {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
}
footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.btn {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.2);
  padding: 0.45rem 1rem;
  font-weight: 600;
  background: #0f172a;
  color: white;
}
.btn.ghost {
  background: transparent;
  color: #0f172a;
}
.icon-btn {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.15);
  width: 36px;
  height: 36px;
  font-size: 1.2rem;
  color: #475569;
}
</style>
