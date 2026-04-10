<template>
  <section class="room-group">
    <header class="room-group__header">
      <div>
        <p class="room-group__eyebrow">{{ group.label }}</p>
        <p class="room-group__summary">Capacidade {{ group.capacity }} pessoas</p>
      </div>
      <button type="button" class="room-group__action" @click="$emit('create-room', group.key)">
        Criar quarto
      </button>
    </header>
    <div v-if="group.rooms.length" class="room-group__grid">
      <RoomCard
        v-for="room in group.rooms"
        :key="room.id"
        :room="room"
        @add-passenger="$emit('add-passenger', room)"
        @remove-passenger="$emit('remove-passenger', room, $event)"
        @request-rename="$emit('request-rename', room)"
      />
    </div>
    <p v-else class="room-group__empty">Nenhum quarto cadastrado neste tipo.</p>
  </section>
</template>

<script setup lang="ts">
import type { RoomingAccommodationSection, RoomingPassenger, RoomingRoom } from "../../../types/rooming";
import RoomCard from "./RoomCard.vue";

defineProps<{
  group: RoomingAccommodationSection;
}>();

defineEmits<{
  (e: "create-room", key: string): void;
  (e: "add-passenger", room: RoomingRoom): void;
  (e: "remove-passenger", room: RoomingRoom, passenger: RoomingPassenger): void;
  (e: "request-rename", room: RoomingRoom): void;
}>();
</script>

<style scoped>
.room-group {
  padding: 1.25rem;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-shadow: 0 12px 35px rgba(15, 23, 42, 0.04);
}

.room-group__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.room-group__eyebrow {
  margin: 0;
  font-size: 0.85rem;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.15em;
}

.room-group__summary {
  margin: 0.2rem 0 0;
  color: #94a3b8;
}

.room-group__action {
  border-radius: 0.6rem;
  border: 1px solid #1ebd63;
  padding: 0.4rem 1rem;
  background: #1ebd63;
  color: #fff;
  font-weight: 600;
}

.room-group__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.9rem;
}

.room-group__empty {
  margin: 0;
  color: #94a3b8;
  font-size: 0.9rem;
}

.room-group + .room-group {
  margin-top: 1rem;
}
</style>
