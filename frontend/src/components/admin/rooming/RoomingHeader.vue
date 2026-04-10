<template>
  <header class="rooming-header">
    <div class="rooming-header__info">
      <p class="rooming-header__eyebrow">Rooming List</p>
      <h1>{{ productName }}</h1>
      <p class="rooming-header__subtitle">
        <span v-if="formattedTripDate">Saída {{ formattedTripDate }} • </span>
        {{ totalPassengers }} passageiro(s)
      </p>
      <p class="rooming-header__description">Distribuição real dos passageiros por quarto e tipo de acomodação.</p>
    </div>
    <div class="rooming-header__actions">
      <button type="button" class="rooming-header__button rooming-header__button--ghost" @click="$emit('refresh')">
        Atualizar dados
      </button>
      <button type="button" class="rooming-header__button" @click="$emit('create-room')">Criar quarto</button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  productName: string;
  tripDate?: string | null;
  totalPassengers: number;
}>();

defineEmits<{
  (e: "refresh"): void;
  (e: "create-room"): void;
}>();

const formattedTripDate = computed(() => {
  if (!props.tripDate) {
    return null;
  }
  try {
    return new Date(props.tripDate).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
  } catch {
    return props.tripDate;
  }
});
</script>

<style scoped>
.rooming-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.rooming-header__info h1 {
  margin: 0.15rem 0;
  font-size: 2rem;
  color: #0f172a;
}

.rooming-header__eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.35em;
  font-size: 0.7rem;
  color: #94a3b8;
  margin: 0;
}

.rooming-header__subtitle {
  margin: 0.35rem 0;
  color: #475569;
  font-weight: 600;
}

.rooming-header__description {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

.rooming-header__actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.rooming-header__button {
  border-radius: 0.75rem;
  border: 1px solid transparent;
  background: #1ebd63;
  color: #fff;
  font-weight: 600;
  padding: 0.65rem 1.5rem;
  box-shadow: 0 10px 25px rgba(30, 189, 99, 0.25);
}

.rooming-header__button--ghost {
  background: #f1f5f9;
  color: #0f9d58;
  border-color: #bcebd0;
  box-shadow: none;
}

.rooming-header__button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .rooming-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .rooming-header__actions {
    width: 100%;
  }

  .rooming-header__button {
    flex: 1;
    text-align: center;
  }
}
</style>
