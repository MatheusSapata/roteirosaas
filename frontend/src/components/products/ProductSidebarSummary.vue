<template>
  <div class="sidebar-stack">
    <section class="sidebar-card sidebar-card--status">
      <div class="status-head">
        <div>
          <p class="eyebrow">Situacao</p>
          <h3>{{ statusLabel }}</h3>
        </div>
        <span class="status-dot" :class="`status-dot--${statusTone}`"></span>
      </div>

      <p class="status-summary">
        {{ metrics.sold }} venda(s) confirmada(s), {{ metrics.available }} vaga(s) livres e ocupacao atual de
        {{ occupancyLabel }}.
      </p>

      <div class="mini-metrics">
        <article>
          <span>Disponiveis</span>
          <strong>{{ metrics.available }}</strong>
        </article>
        <article>
          <span>Vendidas</span>
          <strong>{{ metrics.sold }}</strong>
        </article>
        <article>
          <span>Sincronia</span>
          <strong>{{ savingCopy }}</strong>
        </article>
      </div>
    </section>

    <section class="sidebar-card">
      <div class="card-head">
        <p class="eyebrow">Acoes rapidas</p>
        <p class="support-copy">Fluxos principais para venda, operacao e atendimento.</p>
      </div>

      <div class="action-list">
        <button type="button" class="action-btn action-btn--primary" :disabled="quickActionsDisabled" @click="$emit('action', 'sale')">
          Nova venda
        </button>
        <button type="button" class="action-btn" :disabled="quickActionsDisabled" @click="$emit('action', 'payment-link')">
          Link de pagamento
        </button>
        <button type="button" class="action-btn" :disabled="quickActionsDisabled" @click="$emit('action', 'inventory')">
          Ajustar operacao
        </button>
        <button type="button" class="action-btn action-btn--soft" :disabled="!passengersEnabled" @click="$emit('action', 'passengers')">
          Passageiros
        </button>
        <button type="button" class="action-btn action-btn--soft" :disabled="!product.has_accommodation" @click="$emit('action', 'rooming')">
          Rooming list
        </button>
        <button type="button" class="action-btn action-btn--soft" :disabled="!product.is_road_trip" @click="$emit('action', 'seatmap')">
          Mapa de assentos
        </button>
      </div>
    </section>

    <section class="sidebar-card sidebar-card--system">
      <div class="card-head">
        <p class="eyebrow">Estado do sistema</p>
        <p class="support-copy">Resumo executivo do produto e salvamento automatico.</p>
      </div>

      <div class="system-list">
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
          <strong>{{ product.allow_oversell ? "Habilitado" : "Desativado" }}</strong>
        </div>
        <div>
          <span>Rodoviario</span>
          <strong>{{ product.is_road_trip ? "Ativo" : "Inativo" }}</strong>
        </div>
      </div>

      <div class="save-inline">
        <SaveStatusIndicator :state="savingState" :updated-at="lastSavedAt" />
      </div>
    </section>
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

const statusTone = computed(() => {
  if (props.product.status === "active") return "success";
  if (props.product.status === "archived") return "muted";
  return "warning";
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
  props.product.inventory_strategy === "unlimited" ? "Estoque ilimitado" : "Estoque manual",
);

const occupancyLabel = computed(() => `${Math.min(100, Math.max(0, props.metrics.occupancy)).toFixed(0)}%`);
const quickActionsDisabled = computed(() => !!props.actionsDisabled);
const passengersEnabled = computed(() => props.product.is_road_trip && (props.canPassengers ?? true));
const savingCopy = computed(() => {
  if (props.savingState === "saving") return "Salvando";
  if (props.savingState === "saved") return "Sincronizado";
  if (props.savingState === "error") return "Revisar";
  if (props.savingState === "dirty") return "Pendente";
  return "Estavel";
});
</script>

<style scoped>
.sidebar-stack {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.sidebar-card {
  padding: 1.25rem;
  border-radius: 1.45rem;
  border: 1px solid rgba(226, 232, 240, 0.7);
  background: #fff;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.sidebar-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.sidebar-card--status {
  padding-bottom: 1.2rem;
}

.status-head,
.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.8rem;
}

.eyebrow {
  margin: 0 0 0.28rem;
  font-size: 0.69rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.status-head h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: #0f172a;
}

.status-dot {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 999px;
  margin-top: 0.4rem;
  box-shadow: 0 0 0 6px rgba(148, 163, 184, 0.08);
}

.status-dot--success { background: #14b8a6; }
.status-dot--muted { background: #94a3b8; }
.status-dot--warning { background: #f97316; }

.status-summary,
.support-copy {
  margin: 0.7rem 0 0;
  font-size: 0.88rem;
  line-height: 1.6;
  color: #64748b;
}

.mini-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.mini-metrics article,
.system-list div {
  padding: 0.8rem 0.85rem;
  border-radius: 0.95rem;
  background: rgba(248, 250, 252, 0.7);
  border: 1px solid rgba(226, 232, 240, 0.72);
}

.mini-metrics span,
.system-list span {
  display: block;
  margin-bottom: 0.28rem;
  font-size: 0.68rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.mini-metrics strong,
.system-list strong {
  font-size: 0.95rem;
  color: #0f172a;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  margin-top: 0.95rem;
}

.action-btn {
  width: 100%;
  min-height: 2.85rem;
  padding: 0.75rem 0.95rem;
  border-radius: 1rem;
  border: 1px solid rgba(203, 213, 225, 0.88);
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  font-weight: 700;
  text-align: left;
  transition: transform 0.18s ease, box-shadow 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 18px 28px -24px rgba(15, 23, 42, 0.35);
}

.action-btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.action-btn--primary {
  color: #fff;
  border-color: rgba(16, 185, 129, 0.1);
  background: linear-gradient(180deg, #10b981, #059669);
  box-shadow: 0 18px 30px -24px rgba(16, 185, 129, 0.42);
}

.action-btn--soft {
  background: rgba(248, 250, 252, 0.94);
}

.system-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.7rem;
  margin-top: 0.95rem;
}

.save-inline {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(226, 232, 240, 0.9);
}

@media (max-width: 720px) {
  .mini-metrics,
  .system-list {
    grid-template-columns: 1fr;
  }
}
</style>
