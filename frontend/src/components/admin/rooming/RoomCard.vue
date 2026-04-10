<template>
  <article class="room-card" :class="roomCardClass" @click="handleCardClick">
    <header class="room-card__header">
      <div>
        <p class="room-card__title">{{ room.name }}</p>
        <p class="room-card__capacity">{{ room.occupancy }} / {{ room.capacity }} ocupantes</p>
      </div>
      <div class="room-card__chips">
        <span class="room-card__chip room-card__chip--status" :class="`room-card__chip--${room.status}`">
          {{ statusLabel }}
        </span>
        <span v-if="room.is_private" class="room-card__chip room-card__chip--private">Privativo</span>
      </div>
    </header>
    <p v-if="room.locked" class="room-card__lock-note">Alocação automática para venda privativa.</p>
    <ul class="room-card__passengers">
      <li
        v-for="passenger in room.passengers"
        :key="passenger.id"
        class="room-card__passenger"
        :class="{ 'room-card__passenger--locked': room.locked }"
      >
        <div class="room-card__avatar">{{ passenger.name.slice(0, 1).toUpperCase() }}</div>
        <div class="room-card__details">
          <p class="room-card__passenger-name">{{ passenger.name }}</p>
          <p class="room-card__meta">Pedido #{{ passenger.order_code }}</p>
        </div>
        <button
          v-if="!room.locked"
          type="button"
          class="room-card__remove"
          @click.stop="$emit('remove-passenger', passenger)"
        >
          Remover
        </button>
      </li>
      <li v-if="!room.passengers.length" class="room-card__empty">Nenhum passageiro neste quarto.</li>
    </ul>
    <button v-if="!room.locked" type="button" class="room-card__action" @click.stop="$emit('add-passenger')">
      Alocar passageiro
    </button>
    <p v-else class="room-card__locked-note">Quarto bloqueado para ajustes manuais.</p>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { RoomingPassenger, RoomingRoom, RoomingStatus } from "../../../types/rooming";

const props = defineProps<{
  room: RoomingRoom;
}>();

const emit = defineEmits<{
  (e: "add-passenger"): void;
  (e: "remove-passenger", passenger: RoomingPassenger): void;
  (e: "request-rename", room: RoomingRoom): void;
}>();

const statusLabels: Record<RoomingStatus, string> = {
  empty: "Vazio",
  incomplete: "Incompleto",
  complete: "Completo",
  conflict: "Conflito",
  pending: "Pendente",
  shared: "Compartilhado",
};

const statusLabel = computed(() => statusLabels[props.room.status] ?? "Status");

const handleCardClick = () => {
  if (!props.room.is_private) {
    return;
  }
  emit("request-rename", props.room);
};

const roomCardClass = computed(() => [
  `room-card--${props.room.status}`,
  { "room-card--interactive": props.room.is_private },
]);
</script>

<style scoped>
.room-card {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background: #ffffff;
  cursor: default;
}

.room-card--interactive {
  cursor: pointer;
}
.room-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.room-card__title {
  margin: 0;
  color: #0f172a;
  font-weight: 600;
}

.room-card__capacity {
  margin: 0.2rem 0 0;
  color: #475569;
  font-size: 0.85rem;
}

.room-card__chips {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.room-card__chip {
  border-radius: 999px;
  padding: 0.2rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.room-card__chip--status {
  background: #e2e8f0;
  color: #0f172a;
}

.room-card__chip--private {
  background: #dcfce7;
  color: #15803d;
}

.room-card__lock-note,
.room-card__locked-note {
  margin: 0;
  font-size: 0.85rem;
  color: #0f9d58;
}

.room-card__passengers {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.room-card__passengers li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.room-card__avatar {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.room-card__details {
  flex: 1;
}

.room-card__passenger-name {
  margin: 0;
  font-weight: 600;
  color: #0f172a;
}

.room-card__meta {
  margin: 0;
  color: #94a3b8;
  font-size: 0.8rem;
}

.room-card__remove {
  border: none;
  background: transparent;
  color: #b91c1c;
  font-weight: 600;
  font-size: 0.85rem;
}

.room-card__empty {
  margin: 0;
  color: #94a3b8;
  font-size: 0.9rem;
}

.room-card__action {
  border: 1px solid #1ebd63;
  border-radius: 0.8rem;
  background: #1ebd63;
  color: #fff;
  font-weight: 600;
  padding: 0.6rem;
  display: inline-flex;
  justify-content: center;
}

.room-card__action:hover {
  background: #17a553;
}

.room-card--complete {
  border-color: #34d399;
}

.room-card--incomplete {
  border-color: #fbbf24;
}

.room-card--conflict {
  border-color: #f87171;
}

.room-card--empty {
  border-color: #cbd5f5;
}
</style>
