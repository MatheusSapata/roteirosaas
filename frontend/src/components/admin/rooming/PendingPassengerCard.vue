<template>
  <article class="pending-card">
    <div>
      <p class="pending-card__name">{{ passenger.name }}</p>
      <p class="pending-card__info" v-if="passenger.variation_name">{{ passenger.variation_name }}</p>
      <p class="pending-card__info">Pedido #{{ passenger.order_code }}</p>
    </div>
    <button type="button" class="pending-card__action" @click="$emit('assign', passenger)">
      Alocar em quarto
    </button>
  </article>
</template>

<script setup lang="ts">
import type { RoomingPassenger } from "../../../types/rooming";

defineProps<{
  passenger: RoomingPassenger;
}>();

defineEmits<{
  (e: "assign", passenger: RoomingPassenger): void;
}>();
</script>

<style scoped>
.pending-card {
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  padding: 0.9rem;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
}

.pending-card__name {
  margin: 0;
  color: #0f172a;
  font-weight: 600;
}

.pending-card__info {
  margin: 0;
  color: #475569;
  font-size: 0.85rem;
}

.pending-card__action {
  margin-top: 0.35rem;
  border-radius: 0.6rem;
  border: 1px solid #1ebd63;
  background: #1ebd63;
  color: #fff;
  font-weight: 600;
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  align-self: flex-start;
}

.pending-card__action:hover {
  background: #169c52;
  border-color: #169c52;
}
</style>
