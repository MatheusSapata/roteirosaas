<template>
  <section class="rooming-stats">
    <article v-for="stat in statCards" :key="stat.label" class="rooming-stats__card">
      <p class="rooming-stats__label">{{ stat.label }}</p>
      <p class="rooming-stats__value">{{ stat.value }}</p>
      <p class="rooming-stats__hint">{{ stat.hint }}</p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { RoomingStats } from "../../../types/rooming";

const props = defineProps<{
  stats: RoomingStats;
}>();

const statCards = computed(() => [
  {
    label: "Passageiros",
    value: props.stats.total_passengers,
    hint: `${props.stats.passengers_with_room} alocados`,
  },
  {
    label: "Sem quarto",
    value: props.stats.passengers_without_room,
    hint: "Precisa de atenção",
  },
  {
    label: "Quartos completos",
    value: props.stats.rooms_complete,
    hint: `${props.stats.total_rooms} no total`,
  },
  {
    label: "Quartos incompletos",
    value: props.stats.rooms_incomplete,
    hint: `${props.stats.rooms_empty} vazios`,
  },
]);
</script>

<style scoped>
.rooming-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.rooming-stats__card {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 1rem;
  background: #fff;
  box-shadow: none;
}

.rooming-stats__label {
  margin: 0;
  font-size: 0.9rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.rooming-stats__value {
  margin: 0.2rem 0;
  font-size: 1.85rem;
  color: #0f172a;
  font-weight: 700;
}

.rooming-stats__hint {
  margin: 0;
  color: #475569;
  font-size: 0.85rem;
}
</style>
