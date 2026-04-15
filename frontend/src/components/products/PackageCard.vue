<template>
  <article class="package-card">
    <div class="package-card__top">
      <div class="package-card__identity">
        <p class="eyebrow">Pacote</p>
        <div class="title-row">
          <h3>{{ variation.name }}</h3>
          <span class="status-pill" :class="statusClass">{{ statusLabel }}</span>
        </div>
        <p v-if="variation.description" class="description">{{ variation.description }}</p>
      </div>

      <div class="package-card__price">
        <span>A partir de</span>
        <strong>{{ formatCurrency(variation.price) }}</strong>
        <small>/ pessoa</small>
      </div>
    </div>

    <div class="package-card__body">
      <article class="highlight">
        <span>Pessoas incluidas</span>
        <strong>{{ variation.people_included }}</strong>
        <small>{{ variation.people_included === 1 ? "por reserva" : "na configuracao base" }}</small>
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

    <div class="package-card__footer">
      <div class="footer-actions">
        <button type="button" class="action-btn action-btn--primary" @click="$emit('edit', variation)">Editar pacote</button>
        <button type="button" class="action-btn action-btn--secondary" @click="$emit('duplicate', variation)">Duplicar</button>
      </div>
      <button type="button" class="action-menu" title="Mais acoes" aria-label="Mais acoes" @click="$emit('remove', variation)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <path d="M5 12h14" />
          <path d="M12 5h.01" />
          <path d="M12 12h.01" />
          <path d="M12 19h.01" />
        </svg>
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  variation: {
    name: string;
    description: string | null;
    price: number;
    people_included: number;
    status: string;
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
  (e: "edit", variation: typeof props.variation): void;
  (e: "duplicate", variation: typeof props.variation): void;
  (e: "remove", variation: typeof props.variation): void;
}>();

const statusLabel = computed(() => (props.variation.status === "active" ? "Ativo" : "Inativo"));
const statusClass = computed(() => (props.variation.status === "active" ? "status-pill--active" : "status-pill--muted"));
const stockLabel = computed(() =>
  props.variation.stock_mode === "variant"
    ? `${props.variation.available_slots ?? 0}/${props.variation.total_slots ?? 0}`
    : "Segue produto",
);
const stockSupportLabel = computed(() =>
  props.variation.stock_mode === "variant" ? "Controle proprio por pacote" : "Compartilha disponibilidade geral",
);
const accommodationPrimary = computed(() => {
  if (!props.variation.has_accommodation) return "Sem hospedagem";
  return props.variation.accommodation_mode === "private" ? "Privativo" : "Compartilhado";
});
const accommodationSecondary = computed(() => {
  if (!props.variation.has_accommodation) return "Produto sem quarto vinculado";
  if (props.variation.accommodation_mode === "private") {
    return `${props.variation.room_capacity} pax por quarto`;
  }
  return `${props.variation.slots_per_unit} vagas por unidade`;
});
const childRulesEnabled = computed(
  () => (props.variation.child_pricing_rules || []).filter(rule => rule.enabled).length,
);
const childPolicyLabel = computed(() => {
  if (!props.variation.child_policy_enabled) return "Segue produto";
  return childRulesEnabled.value ? `${childRulesEnabled.value} ativa(s)` : "Configurada";
});
const childPolicySupportLabel = computed(() =>
  props.variation.child_policy_enabled ? "Faixas customizadas por pacote" : "Usa o comportamento padrao",
);

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
</script>

<style scoped>
.package-card {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
  padding: 1.6rem 1.7rem;
  border-radius: 1.8rem;
  border: 1px solid rgba(203, 213, 225, 0.58);
  background:
    radial-gradient(circle at top right, rgba(191, 219, 254, 0.18), transparent 34%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(249, 251, 255, 0.96));
  box-shadow:
    0 18px 40px -32px rgba(15, 23, 42, 0.22),
    0 32px 70px -58px rgba(15, 23, 42, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.84);
  transition:
    transform 0.18s ease,
    box-shadow 0.22s ease,
    border-color 0.22s ease,
    background-color 0.22s ease;
}

.package-card:hover {
  transform: translateY(-2px);
  border-color: rgba(148, 163, 184, 0.72);
  box-shadow:
    0 22px 45px -34px rgba(15, 23, 42, 0.26),
    0 40px 82px -60px rgba(15, 23, 42, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.package-card__top,
.package-card__footer {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.1rem;
}

.package-card__identity {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 0.55rem;
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.8rem;
}

.title-row h3 {
  margin: 0;
  font-size: 1.68rem;
  font-weight: 700;
  letter-spacing: -0.045em;
  color: #0f172a;
}

.description {
  margin: 0.72rem 0 0;
  max-width: 54ch;
  color: #64748b;
  line-height: 1.65;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 1.95rem;
  padding: 0.26rem 0.76rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
}

.status-pill--active {
  color: #0f766e;
  background: rgba(45, 212, 191, 0.12);
  border: 1px solid rgba(45, 212, 191, 0.2);
}

.status-pill--muted {
  color: #475569;
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.package-card__price {
  min-width: 230px;
  padding-left: 1rem;
  text-align: right;
}

.package-card__price span,
.package-card__price small {
  display: block;
}

.package-card__price span {
  margin-bottom: 0.36rem;
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.package-card__price strong {
  display: block;
  font-size: clamp(2.6rem, 4.2vw, 3.55rem);
  line-height: 0.96;
  letter-spacing: -0.07em;
  color: #0f172a;
}

.package-card__price small {
  margin-top: 0.4rem;
  font-size: 0.78rem;
  color: #94a3b8;
}

.package-card__body {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  border-radius: 1.35rem;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.84), rgba(255, 255, 255, 0.84));
  border: 1px solid rgba(226, 232, 240, 0.68);
  overflow: hidden;
}

.highlight {
  min-width: 0;
  padding: 1.1rem 1.15rem;
}

.highlight + .highlight {
  border-left: 1px solid rgba(226, 232, 240, 0.72);
}

.highlight span,
.highlight small {
  display: block;
}

.highlight span {
  margin-bottom: 0.48rem;
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.highlight strong {
  display: block;
  margin-bottom: 0.3rem;
  font-size: 1.07rem;
  line-height: 1.3;
  color: #0f172a;
}

.highlight small {
  font-size: 0.83rem;
  line-height: 1.5;
  color: #64748b;
}

.package-card__footer {
  align-items: center;
  padding-top: 0.15rem;
}

.footer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.action-btn,
.action-menu {
  transition:
    transform 0.18s ease,
    border-color 0.22s ease,
    background-color 0.22s ease,
    color 0.22s ease,
    box-shadow 0.22s ease;
}

.action-btn:hover,
.action-menu:hover {
  transform: translateY(-1px);
}

.action-btn {
  min-height: 2.8rem;
  padding: 0.72rem 1.05rem;
  border-radius: 1rem;
  font-weight: 700;
}

.action-btn--primary {
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: #0f172a;
  color: #fff;
  box-shadow: 0 18px 28px -24px rgba(15, 23, 42, 0.56);
}

.action-btn--secondary {
  border: 1px solid rgba(203, 213, 225, 0.78);
  background: rgba(255, 255, 255, 0.88);
  color: #334155;
}

.action-btn--secondary:hover {
  border-color: rgba(148, 163, 184, 0.72);
  background: rgba(248, 250, 252, 0.96);
}

.action-menu {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.8rem;
  height: 2.8rem;
  border-radius: 1rem;
  border: 1px solid rgba(203, 213, 225, 0.76);
  background: rgba(255, 255, 255, 0.86);
  color: #64748b;
}

.action-menu svg {
  width: 1rem;
  height: 1rem;
}

@media (max-width: 980px) {
  .package-card__body {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .highlight:nth-child(3),
  .highlight:nth-child(4) {
    border-top: 1px solid rgba(226, 232, 240, 0.72);
  }

  .highlight:nth-child(3) {
    border-left: none;
  }
}

@media (max-width: 720px) {
  .package-card {
    padding: 1.2rem;
    border-radius: 1.45rem;
    gap: 1.25rem;
  }

  .package-card__top,
  .package-card__footer {
    flex-direction: column;
    align-items: stretch;
  }

  .package-card__price {
    min-width: 0;
    padding-left: 0;
    text-align: left;
  }

  .package-card__price strong {
    font-size: 2.55rem;
  }

  .package-card__body {
    grid-template-columns: 1fr;
  }

  .highlight + .highlight,
  .highlight:nth-child(3),
  .highlight:nth-child(4) {
    border-left: none;
    border-top: 1px solid rgba(226, 232, 240, 0.72);
  }

  .package-card__footer {
    gap: 0.85rem;
  }

  .action-menu {
    width: 100%;
  }
}
</style>
