<template>
  <section class="operations-shell">
    <header class="section-head">
      <div>
        <p class="eyebrow">Operacao em tempo real</p>
        <h2>Painel de controle operacional</h2>
        <p class="support-copy">Leitura rapida da saude do produto, transporte e capacidade ativa.</p>
      </div>
      <button type="button" class="section-link" :disabled="!canConfigure" @click="$emit('open-transport')">
        Ajustar transporte
      </button>
    </header>

    <div class="status-rail">
      <article class="rail-item" :class="transportReady ? 'rail-item--ok' : 'rail-item--warn'">
        <span class="rail-dot"></span>
        <div>
          <strong>{{ transportReady ? "Transporte pronto" : "Transporte pendente" }}</strong>
          <p>{{ transportReady ? "Fluxo preparado para alocar passageiros." : "Defina estrutura de embarque e capacidade." }}</p>
        </div>
      </article>

      <article class="rail-item" :class="boardingCount ? 'rail-item--ok' : 'rail-item--warn'">
        <span class="rail-dot"></span>
        <div>
          <strong>{{ boardingLabel }}</strong>
          <p>{{ boardingCount ? "Locais publicados para venda e operacao." : "Nenhum local de embarque informado." }}</p>
        </div>
      </article>

      <article class="rail-item" :class="product.hasRooms ? 'rail-item--ok' : 'rail-item--muted'">
        <span class="rail-dot"></span>
        <div>
          <strong>{{ product.hasRooms ? "Hospedagem integrada" : "Sem hospedagem" }}</strong>
          <p>{{ product.hasRooms ? "Pacotes conectados ao fluxo de rooming." : "Produto opera sem configuracao de quartos." }}</p>
        </div>
      </article>
    </div>

    <div class="operation-facts">
      <article>
        <span>Estrategia</span>
        <strong>{{ inventoryLabel }}</strong>
      </article>
      <article>
        <span>Overbooking</span>
        <strong>{{ product.allow_oversell ? "Habilitado" : "Desativado" }}</strong>
      </article>
      <article>
        <span>Rodoviario</span>
        <strong>{{ product.is_road_trip ? "Ativo" : "Inativo" }}</strong>
      </article>
    </div>

    <div class="action-row">
      <button type="button" class="action-btn" :disabled="boardingDisabled" @click="$emit('open-boarding')">
        Gerenciar embarques
      </button>
      <button type="button" class="action-btn" :disabled="!product.is_road_trip || seatmapDisabled" @click="$emit('open-seatmap')">
        Abrir mapa de assentos
      </button>
      <button type="button" class="action-btn" :disabled="!product.hasRooms" @click="$emit('open-rooming')">
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
  props.product.inventory_strategy === "unlimited" ? "Estoque ilimitado" : "Estoque manual",
);

const boardingLabel = computed(() => {
  if (!props.boardingCount) return "Embarques pendentes";
  return props.boardingCount === 1 ? "1 embarque publicado" : `${props.boardingCount} embarques publicados`;
});

const boardingDisabled = computed(() => false);
</script>

<style scoped>
.operations-shell {
  display: flex;
  flex-direction: column;
  gap: 1.45rem;
  padding: 1.65rem;
  border-radius: 1.75rem;
  border: 1px solid rgba(226, 232, 240, 0.7);
  background: #fff;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.operations-shell:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.eyebrow {
  margin: 0 0 0.32rem;
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.section-head h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: #0f172a;
}

.support-copy {
  margin: 0.5rem 0 0;
  color: #64748b;
  line-height: 1.6;
}

.section-link {
  border: none;
  background: transparent;
  padding: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #0f172a;
}

.status-rail {
  display: grid;
  gap: 0.75rem;
}

.rail-item {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  padding: 1rem 1.05rem;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 1rem;
  background: linear-gradient(180deg, rgba(250, 251, 253, 0.92), rgba(248, 250, 252, 0.72));
  box-shadow: 0 12px 26px -24px rgba(15, 23, 42, 0.14);
}

.rail-dot {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 999px;
  margin-top: 0.28rem;
  flex-shrink: 0;
}

.rail-item strong {
  display: block;
  margin-bottom: 0.28rem;
  font-size: 0.92rem;
  color: #0f172a;
}

.rail-item p {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.6;
  color: #64748b;
}

.rail-item--ok .rail-dot {
  background: #14b8a6;
  box-shadow: 0 0 0 6px rgba(45, 212, 191, 0.12);
}

.rail-item--warn .rail-dot {
  background: #f97316;
  box-shadow: 0 0 0 6px rgba(251, 146, 60, 0.14);
}

.rail-item--muted .rail-dot {
  background: #94a3b8;
  box-shadow: 0 0 0 6px rgba(148, 163, 184, 0.12);
}

.operation-facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}

.operation-facts article {
  border-radius: 1rem;
  border: 1px solid rgba(226, 232, 240, 0.75);
  background: rgba(248, 250, 252, 0.7);
  padding: 0.9rem 1rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.operation-facts span {
  display: block;
  margin-bottom: 0.32rem;
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.operation-facts strong {
  color: #0f172a;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.action-btn {
  min-height: 2.75rem;
  padding: 0.72rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(203, 213, 225, 0.88);
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  font-weight: 700;
  transition: transform 0.18s ease, box-shadow 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 16px 30px -24px rgba(15, 23, 42, 0.35);
}

.action-btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

@media (max-width: 840px) {
  .operation-facts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .operations-shell {
    padding: 1.25rem;
    border-radius: 1.35rem;
  }

  .section-head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
