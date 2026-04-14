<template>
  <section class="card">
    <header class="card-header">
      <div>
        <p class="eyebrow">Operacao da viagem</p>
        <h2>Fluxos operacionais</h2>
        <p class="muted">Gerencie transporte, embarques e integracoes com passageiros.</p>
      </div>
      <button type="button" class="pill" @click="$emit('open-transport')" :disabled="!canConfigure">
        Configurar rodoviario
      </button>
    </header>

    <div class="status-tiles">
      <article class="tile">
        <p>Estrategia</p>
        <strong>{{ inventoryLabel }}</strong>
        <span :class="['badge-pill', product.inventory_strategy === 'manual' ? 'badge-pill-warm' : 'badge-pill-cool']">
          {{ product.inventory_strategy === "manual" ? "Controle manual" : "Estoque ilimitado" }}
        </span>
      </article>
      <article class="tile">
        <p>Overbooking</p>
        <strong>{{ product.allow_oversell ? "Habilitado" : "Desativado" }}</strong>
        <span :class="['badge-pill', product.allow_oversell ? 'badge-pill-on' : 'badge-pill-muted']">
          {{ product.allow_oversell ? "Flexivel" : "Conservador" }}
        </span>
      </article>
      <article class="tile">
        <p>Rodoviario</p>
        <strong>{{ product.is_road_trip ? "Ativo" : "Inativo" }}</strong>
        <span :class="['badge-pill', product.is_road_trip ? 'badge-pill-on' : 'badge-pill-muted']">
          {{ product.is_road_trip ? "Transportes habilitados" : "Sem transporte" }}
        </span>
      </article>
      <article class="tile">
        <p>Transporte</p>
        <strong>{{ transportReady ? "Configurado" : "Pendente" }}</strong>
        <span :class="['badge-pill', transportReady ? 'badge-pill-on' : 'badge-pill-warn']">
          {{ transportReady ? "Pronto para passageiros" : "Defina layouts" }}
        </span>
      </article>
      <article class="tile">
        <p>Embarques</p>
        <strong>{{ boardingLabel }}</strong>
        <span class="badge-pill badge-pill-muted">Fluxo operacional</span>
      </article>
      <article class="tile">
        <p>Hospedagem</p>
        <strong>{{ product.hasRooms ? "Com quartos" : "Sem hospedagem" }}</strong>
        <span class="badge-pill badge-pill-muted">{{ product.hasRooms ? "Integra rooming" : "Opcional" }}</span>
      </article>
    </div>

    <div class="action-row">
      <button type="button" class="action" @click="$emit('open-boarding')" :disabled="boardingDisabled">
        Gerenciar embarques
      </button>
      <button type="button" class="action" @click="$emit('open-seatmap')" :disabled="!product.is_road_trip || seatmapDisabled">
        Abrir mapa de assentos
      </button>
      <button type="button" class="action" @click="$emit('open-rooming')" :disabled="!product.hasRooms">
        Rooming list
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  product: {
    inventory_strategy: "manual" | "unlimited";
    allow_oversell: boolean;
    is_road_trip: boolean;
    hasRooms: boolean;
  };
  boardingCount: number;
  transportReady: boolean;
  canConfigure: boolean;
  seatmapDisabled?: boolean;
}>();

defineEmits<{
  (e: "open-transport"): void;
  (e: "open-boarding"): void;
  (e: "open-seatmap"): void;
  (e: "open-rooming"): void;
}>();

const inventoryLabel = computed(() =>
  props.product.inventory_strategy === "unlimited" ? "Ilimitado" : "Manual",
);

const boardingLabel = computed(() => {
  if (!props.boardingCount) return "Nao definidos";
  return props.boardingCount === 1 ? "1 local" : `${props.boardingCount} locais`;
});

const boardingDisabled = computed(() => false);
</script>

<style scoped>
.card {
  background: white;
  border-radius: 1.5rem;
  border: 1px solid #e2e8f0;
  padding: 1.5rem;
  box-shadow: 0 20px 45px -20px rgba(15, 23, 42, 0.25);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 0.7rem;
  color: #94a3b8;
}
.muted {
  font-size: 0.9rem;
  color: #64748b;
}
.pill {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.2);
  padding: 0.4rem 1.1rem;
  font-weight: 600;
}
.status-tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}
.tile {
  border: 1px solid #e2e8f0;
  border-radius: 1.25rem;
  padding: 1rem;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.tile p {
  font-size: 0.7rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #94a3b8;
}
.tile strong {
  font-size: 1.15rem;
  color: #0f172a;
}
.badge-pill {
  align-self: flex-start;
  border-radius: 999px;
  padding: 0.25rem 0.9rem;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid rgba(15, 23, 42, 0.1);
  color: #475569;
}
.badge-pill-on {
  background: rgba(16, 185, 129, 0.18);
  border-color: rgba(16, 185, 129, 0.45);
  color: #047857;
}
.badge-pill-warm {
  background: rgba(249, 115, 22, 0.15);
  border-color: rgba(251, 146, 60, 0.4);
  color: #9a3412;
}
.badge-pill-cool {
  background: rgba(14, 165, 233, 0.14);
  border-color: rgba(56, 189, 248, 0.35);
  color: #0369a1;
}
.badge-pill-muted {
  background: rgba(148, 163, 184, 0.15);
}
.badge-pill-warn {
  background: rgba(251, 191, 36, 0.18);
  border-color: rgba(251, 191, 36, 0.5);
  color: #92400e;
}
.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.action {
  flex: 1;
  min-width: 160px;
  border-radius: 1rem;
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 0.65rem 1rem;
  font-weight: 600;
  text-align: center;
  background: white;
  color: #0f172a;
}
.action:disabled {
  opacity: 0.4;
}
</style>
