<template>
  <div class="package-panel">
    <div class="package-panel__shell">
      <div class="package-panel__header">
        <div>
          <p class="eyebrow">Visao detalhada do pacote</p>
          <p class="description">{{ variation.description || "Detalhes operacionais deste pacote para venda, estoque e configuracao comercial." }}</p>
        </div>
        <div class="package-panel__summary">
          <p class="eyebrow">Configuracao</p>
          <p class="summary-value">{{ configurationLabel }}</p>
          <p class="summary-copy">{{ configurationSupport }}</p>
        </div>
      </div>

      <div class="package-panel__divider"></div>

      <div class="package-panel__highlights">
        <article class="highlight">
          <span>Pessoas incluidas</span>
          <strong>{{ variation.people_included }} {{ variation.people_included === 1 ? "pessoa" : "pessoas" }}</strong>
          <small>{{ variation.people_included === 1 ? "1 passageiro por reserva" : "Capacidade base por reserva" }}</small>
        </article>
        <article class="highlight">
          <span>Estoque</span>
          <strong>{{ stockLabel }}</strong>
          <small>{{ stockSupportLabel }}</small>
        </article>
        <article class="highlight">
          <span>Hospedagem</span>
          <strong>{{ accommodationPrimary }}</strong>
          <small>{{ accommodationSecondary }}</small>
        </article>
        <article class="highlight">
          <span>Regra infantil</span>
          <strong>{{ childPolicyLabel }}</strong>
          <small>{{ childPolicySupportLabel }}</small>
        </article>
      </div>

      <div class="package-panel__footer">
        <button type="button" class="action-btn action-btn--primary" @click="$emit('edit')">Editar pacote</button>
        <button type="button" class="action-btn action-btn--secondary" @click="$emit('duplicate')">Duplicar</button>
        <button type="button" class="action-btn action-btn--ghost" @click="$emit('remove')">Remover</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  variation: {
    description: string | null;
    price: number;
    people_included: number;
    stock_mode: string;
    has_accommodation: boolean;
    accommodation_mode: "private" | "shared";
    room_capacity: number;
    slots_per_unit: number;
    total_slots: number | null;
    available_slots: number | null;
    child_policy_enabled?: boolean;
    child_pricing_rules?: Array<{ enabled: boolean }>;
  };
}>();

defineEmits<{
  (e: "edit"): void;
  (e: "duplicate"): void;
  (e: "remove"): void;
}>();

const stockLabel = computed(() =>
  props.variation.stock_mode === "variant"
    ? `${props.variation.available_slots ?? 0}/${props.variation.total_slots ?? 0}`
    : "Segue produto",
);
const stockSupportLabel = computed(() =>
  props.variation.stock_mode === "variant" ? "Controle proprio por pacote" : "Usa a disponibilidade principal",
);
const accommodationPrimary = computed(() => {
  if (!props.variation.has_accommodation) return "Sem hospedagem";
  return props.variation.accommodation_mode === "private" ? "Privativo" : "Compartilhado";
});
const accommodationSecondary = computed(() => {
  if (!props.variation.has_accommodation) return "Produto sem quarto vinculado";
  if (props.variation.accommodation_mode === "private") return `${props.variation.room_capacity} pax por quarto`;
  return `${props.variation.slots_per_unit} vagas por unidade`;
});
const childRulesEnabled = computed(() => (props.variation.child_pricing_rules || []).filter(rule => rule.enabled).length);
const childPolicyLabel = computed(() => {
  if (!props.variation.child_policy_enabled) return "Segue produto";
  return childRulesEnabled.value ? `${childRulesEnabled.value} faixa(s) ativa(s)` : "Configurada";
});
const childPolicySupportLabel = computed(() =>
  props.variation.child_policy_enabled ? "Faixas customizadas por pacote" : "Comportamento padrao do produto",
);
const configurationLabel = computed(() => {
  if (props.variation.has_accommodation && props.variation.stock_mode === "variant") return "Pacote independente";
  if (props.variation.has_accommodation) return "Hospedagem integrada";
  if (props.variation.stock_mode === "variant") return "Estoque proprio";
  return "Configuracao padrao";
});
const configurationSupport = computed(() => {
  if (props.variation.has_accommodation && props.variation.stock_mode === "variant") {
    return "Com hospedagem e controle separado do produto";
  }
  if (props.variation.has_accommodation) return "Usa a base do produto com componente de hospedagem";
  if (props.variation.stock_mode === "variant") return "Precificacao propria com disponibilidade separada";
  return "Segue a logica principal de estoque e regras";
});
</script>

<style scoped>
.package-panel {
  padding: 0 1.5rem 1.5rem;
}

.package-panel__shell {
  display: flex;
  flex-direction: column;
  gap: 1.35rem;
  padding: 1.2rem 1.35rem 1.35rem;
  border-radius: 1.4rem;
  background: rgba(248, 250, 252, 0.74);
  box-shadow: inset 0 0 0 1px rgba(226, 232, 240, 0.82);
}

.package-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.eyebrow {
  margin: 0 0 0.42rem;
  font-size: 0.69rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.description {
  margin: 0;
  max-width: 52ch;
  color: #64748b;
  line-height: 1.6;
}

.package-panel__summary {
  max-width: 16rem;
  text-align: right;
}

.summary-value,
.summary-copy {
  margin: 0;
}

.summary-value {
  margin-top: 0.5rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-copy {
  margin-top: 0.18rem;
  color: #64748b;
  line-height: 1.5;
}

.package-panel__divider {
  height: 1px;
  background: rgba(226, 232, 240, 0.86);
}

.package-panel__highlights {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1.25rem;
}

.highlight {
  min-width: 0;
}

.highlight span,
.highlight small {
  display: block;
}

.highlight span {
  margin-bottom: 0.45rem;
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.highlight strong {
  display: block;
  margin-bottom: 0.28rem;
  font-size: 1.02rem;
  line-height: 1.35;
  color: #0f172a;
}

.highlight small {
  color: #64748b;
  line-height: 1.5;
}

.package-panel__footer {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.action-btn {
  min-height: 2.7rem;
  padding: 0.7rem 1rem;
  border-radius: 0.95rem;
  font-weight: 700;
  transition:
    transform 0.18s ease,
    border-color 0.2s ease,
    background-color 0.2s ease,
    box-shadow 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.action-btn--primary {
  border: 1px solid rgba(16, 185, 129, 0.08);
  background: linear-gradient(180deg, #10b981, #059669);
  color: #fff;
  box-shadow: 0 16px 28px -24px rgba(16, 185, 129, 0.42);
}

.action-btn--secondary {
  border: 1px solid rgba(203, 213, 225, 0.8);
  background: rgba(255, 255, 255, 0.92);
  color: #334155;
}

.action-btn--ghost {
  border: 1px solid rgba(254, 205, 211, 0.94);
  background: rgba(255, 241, 242, 0.95);
  color: #e11d48;
}

@media (max-width: 980px) {
  .package-panel__highlights {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .package-panel {
    padding: 0 1rem 1rem;
  }

  .package-panel__header {
    flex-direction: column;
  }

  .package-panel__summary {
    max-width: none;
    text-align: left;
  }

  .package-panel__highlights {
    grid-template-columns: 1fr;
    gap: 0.9rem;
  }
}
</style>
