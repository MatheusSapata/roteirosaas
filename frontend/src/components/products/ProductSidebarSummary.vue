<template>
  <div class="sidebar-stack">
    <section class="sidebar-card">
      <div class="card-title">
        <p class="eyebrow">Resumo operacional</p>
        <h3>{{ statusLabel }}</h3>
      </div>
      <div class="summary-items">
        <div>
          <span>Data</span>
          <strong>{{ tripDateLabel }}</strong>
        </div>
        <div>
          <span>Estoque</span>
          <strong>{{ inventoryLabel }}</strong>
        </div>
        <div>
          <span>Overbooking</span>
          <strong>{{ product.allow_oversell ? "Ativo" : "Desativado" }}</strong>
        </div>
        <div>
          <span>Rodoviario</span>
          <strong>{{ product.is_road_trip ? "Sim" : "Nao" }}</strong>
        </div>
        <div>
          <span>Hospedagem</span>
          <strong>{{ product.has_accommodation ? "Sim" : "Nao" }}</strong>
        </div>
      </div>
    </section>

    <section class="sidebar-card metrics-card">
      <p class="eyebrow">Metricas</p>
      <div class="metric-grid">
        <div>
          <p>Totais</p>
          <strong>{{ metrics.total }}</strong>
        </div>
        <div>
          <p>Disponiveis</p>
          <strong>{{ metrics.available }}</strong>
        </div>
        <div>
          <p>Reservadas</p>
          <strong>{{ metrics.reserved }}</strong>
        </div>
        <div>
          <p>Vendidas</p>
          <strong>{{ metrics.sold }}</strong>
        </div>
        <div>
          <p>Ocupacao</p>
          <strong>{{ occupancyLabel }}</strong>
        </div>
      </div>
    </section>

    <section class="sidebar-card actions-card">
      <p class="eyebrow">Acoes rapidas</p>
      <div class="action-grid">
        <button type="button" class="btn btn-primary" @click="$emit('action', 'sale')" :disabled="quickActionsDisabled">
          Nova venda
        </button>
        <button type="button" class="btn ghost" @click="$emit('action', 'payment-link')" :disabled="quickActionsDisabled">
          Link de pagamento
        </button>
        <button type="button" class="btn ghost" @click="$emit('action', 'inventory')" :disabled="quickActionsDisabled">
          Ajustar estoque
        </button>
        <button type="button" class="btn ghost" @click="$emit('action', 'passengers')" :disabled="!passengersEnabled">
          Passageiros
        </button>
        <button type="button" class="btn ghost" @click="$emit('action', 'rooming')" :disabled="!product.has_accommodation">
          Rooming list
        </button>
        <button type="button" class="btn ghost" @click="$emit('action', 'seatmap')" :disabled="!product.is_road_trip">
          Mapa de assentos
        </button>
      </div>
    </section>

    <div class="save-inline">
      <SaveStatusIndicator :state="savingState" :updated-at="lastSavedAt" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SaveStatusIndicator from "./SaveStatusIndicator.vue";

type SaveState = "idle" | "dirty" | "saving" | "saved" | "error";

const props = defineProps<{
  product: {
    status: string;
    trip_date: string | null;
    date_is_flexible: boolean;
    inventory_strategy: "manual" | "unlimited";
    allow_oversell: boolean;
    is_road_trip: boolean;
    has_accommodation: boolean;
  };
  metrics: {
    total: number;
    available: number;
    reserved: number;
    sold: number;
    occupancy: number;
  };
  actionsDisabled?: boolean;
  canPassengers?: boolean;
  savingState: SaveState;
  lastSavedAt: Date | null;
}>();

defineEmits<{
  (
    e: "action",
    action: "sale" | "passengers" | "rooming" | "seatmap" | "payment-link" | "inventory",
  ): void;
}>();

const statusLabel = computed(() => {
  if (props.product.status === "active") return "Ativo";
  if (props.product.status === "archived") return "Arquivado";
  return "Rascunho";
});

const tripDateLabel = computed(() => {
  if (!props.product.trip_date) return "Sem data";
  try {
    const formatted = new Date(props.product.trip_date).toLocaleDateString("pt-BR");
    return props.product.date_is_flexible ? `${formatted} (flexivel)` : formatted;
  } catch {
    return props.product.trip_date;
  }
});

const inventoryLabel = computed(() =>
  props.product.inventory_strategy === "unlimited" ? "Ilimitado" : "Manual",
);

const occupancyLabel = computed(() => `${Math.min(100, Math.max(0, props.metrics.occupancy)).toFixed(0)}%`);

const quickActionsDisabled = computed(() => !!props.actionsDisabled);
const passengersEnabled = computed(() => props.product.is_road_trip && (props.canPassengers ?? true));
</script>

<style scoped>
.sidebar-stack {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.sidebar-card {
  background: white;
  border-radius: 1.25rem;
  border: 1px solid #e2e8f0;
  padding: 1.35rem;
  box-shadow: 0 20px 45px -35px rgba(15, 23, 42, 0.4);
}
.save-inline {
  margin-top: 0.5rem;
}
.card-title h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #0f172a;
}
.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 0.7rem;
  color: #94a3b8;
  margin-bottom: 0.4rem;
}
.summary-items {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem;
  font-size: 0.85rem;
  color: #475569;
}
.summary-items span {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #94a3b8;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}
.metric-grid p {
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #94a3b8;
}
.metric-grid strong {
  font-size: 1.1rem;
  color: #0f172a;
}
.action-grid {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}
.action-grid .btn {
  border-radius: 1rem;
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 0.55rem 0.9rem;
  font-weight: 600;
  text-align: left;
  background: transparent;
  color: #0f172a;
}
.action-grid .btn.btn-primary {
  background: #0f172a;
  color: white;
}
.action-grid .btn.ghost {
  background: transparent;
  color: #0f172a;
}
.action-grid .btn:disabled {
  opacity: 0.4;
}
.save-card {
  background: #fff;
}
</style>
