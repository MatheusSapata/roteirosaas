<template>
  <aside class="rooming-sidebar">
    <section>
      <header class="rooming-sidebar__header">
        <h3>Passageiros sem quarto</h3>
        <div class="rooming-sidebar__header-actions">
          <span class="rooming-sidebar__badge">{{ pendingPassengers.length }}</span>
          <button
            type="button"
            class="rooming-sidebar__auto-match"
            :disabled="autoMatchLoading"
            @click="$emit('auto-match')"
          >
            Organizar automaticamente
          </button>
        </div>
      </header>
      <div class="rooming-sidebar__list">
        <PendingPassengerCard
          v-for="passenger in pendingPassengers"
          :key="passenger.id"
          :passenger="passenger"
          @assign="$emit('assign-passenger', $event)"
        />
        <p v-if="!pendingPassengers.length" class="rooming-sidebar__empty">Nenhum passageiro aguardando.</p>
      </div>
    </section>

    <section>
      <header class="rooming-sidebar__header">
        <h3>Alertas</h3>
      </header>
      <ul class="rooming-sidebar__alerts">
        <li v-for="alert in alerts" :key="alert.id" :class="`rooming-sidebar__alert--${alert.tone}`">
          {{ alert.message }}
        </li>
      </ul>
    </section>
  </aside>
</template>

<script setup lang="ts">
import type { RoomingAlert, RoomingPassenger } from "../../../types/rooming";
import PendingPassengerCard from "./PendingPassengerCard.vue";

defineProps<{
  pendingPassengers: RoomingPassenger[];
  alerts: RoomingAlert[];
  autoMatchLoading?: boolean;
}>();

defineEmits<{
  (e: "assign-passenger", passenger: RoomingPassenger): void;
  (e: "auto-match"): void;
}>();
</script>

<style scoped>
.rooming-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.rooming-sidebar__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.rooming-sidebar__header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rooming-sidebar__header h3 {
  margin: 0;
  color: #0f172a;
  font-size: 0.95rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.rooming-sidebar__badge {
  background: #e0f2fe;
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  font-size: 0.75rem;
  color: #075985;
  border: 1px solid #7dd3fc;
}

.rooming-sidebar__auto-match {
  border-radius: 0.6rem;
  border: 1px solid #12a14f;
  background: #1ebd63;
  color: #fff;
  font-weight: 600;
  font-size: 0.85rem;
  padding: 0.3rem 0.8rem;
}

.rooming-sidebar__auto-match:disabled {
  opacity: 0.6;
}

.rooming-sidebar__list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.rooming-sidebar__empty {
  margin: 0;
  font-size: 0.85rem;
  color: #64748b;
}

.rooming-sidebar__alerts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rooming-sidebar__alerts li {
  border-radius: 0.75rem;
  padding: 0.65rem 0.9rem;
  font-size: 0.85rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #0f172a;
  box-shadow: none;
}

.rooming-sidebar__alert--warning {
  border-color: #fcd34d;
  background: #fef9c3;
  color: #854d0e;
}

.rooming-sidebar__alert--danger {
  border-color: #fca5a5;
  background: #fee2e2;
  color: #b91c1c;
}

.rooming-sidebar__alert--neutral {
  border-color: #cbd5f5;
  background: #f8fafc;
  color: #475569;
}
</style>
