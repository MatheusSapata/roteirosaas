<template>
  <section class="children-shell">
    <header class="section-head">
      <div>
        <p class="eyebrow">Politica infantil</p>
        <h2>Resumo executivo das faixas</h2>
        <p class="support-copy">Leitura rapida de regras ativas, impacto em ocupacao e estrategia comercial.</p>
      </div>
      <button type="button" class="section-link" @click="$emit('edit-summary')">Gerenciar faixas</button>
    </header>

    <div v-if="rules.length" class="summary-banner">
      <strong>{{ enabledCount }} faixa(s) ativa(s)</strong>
      <p>{{ enabledCount ? "Regras distribuidas entre os pacotes para controlar capacidade e cobranca." : "A politica existe, mas ainda nao ha faixa ativa." }}</p>
    </div>

    <div v-if="rules.length" class="rules-grid">
      <article v-for="rule in rules" :key="`${rule.variationIndex}-${rule.key}`" class="rule-card">
        <div class="rule-head">
          <div>
            <span class="variation">{{ rule.variationName }}</span>
            <h3>{{ rule.label || rule.key }}</h3>
            <p>{{ rule.min_age }} a {{ rule.max_age }} anos</p>
          </div>
          <span class="badge" :class="rule.enabled ? 'badge--active' : 'badge--muted'">
            {{ rule.enabled ? "Ativa" : "Inativa" }}
          </span>
        </div>

        <dl class="rule-facts">
          <div>
            <dt>Tipo</dt>
            <dd>{{ rule.pricing_mode === "extra" ? "Adicional" : "Gratuito" }}</dd>
          </div>
          <div>
            <dt>Valor</dt>
            <dd>{{ rule.pricing_mode === "extra" ? formatCurrency(rule.extra_amount) : "R$ 0,00" }}</dd>
          </div>
          <div>
            <dt>Limite</dt>
            <dd>{{ rule.max_quantity ?? "Sem limite" }}</dd>
          </div>
        </dl>

        <div class="chips">
          <span class="chip" :class="rule.counts_towards_capacity ? 'chip--active' : 'chip--muted'">Consome vaga</span>
          <span class="chip" :class="rule.counts_as_passenger ? 'chip--active' : 'chip--muted'">Conta passageiro</span>
        </div>

        <button type="button" class="rule-link" @click="$emit('edit', rule)">Editar faixa</button>
      </article>
    </div>

    <div v-else class="empty-state">
      <strong>Nenhuma faixa configurada</strong>
      <p>Ative politicas infantis nos pacotes para oferecer regras comerciais mais sofisticadas.</p>
      <button type="button" class="empty-cta" @click="$emit('edit-summary')">Gerenciar faixas</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

type ChildRuleBase = {
  key: string;
  label: string;
  min_age: number;
  max_age: number;
  pricing_mode: "free" | "extra";
  extra_amount: number;
  max_quantity: number | null;
  counts_towards_capacity: boolean;
  counts_as_passenger: boolean;
  enabled: boolean;
};

type ChildRuleView = ChildRuleBase & {
  variationIndex: number;
  variationName: string;
};

const props = defineProps<{
  variations: Array<{
    name: string;
    child_policy_enabled: boolean;
    child_pricing_rules: ChildRuleBase[];
  }>;
}>();

defineEmits<{
  (e: "edit", payload: ChildRuleView): void;
  (e: "edit-summary"): void;
}>();

const rules = computed<ChildRuleView[]>(() =>
  props.variations.flatMap((variation, variationIndex) => {
    if (!variation.child_policy_enabled) return [];
    return (variation.child_pricing_rules || []).map(rule => ({
      variationIndex,
      variationName: variation.name,
      ...rule,
    }));
  }),
);

const enabledCount = computed(() => rules.value.filter(rule => rule.enabled).length);

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
</script>

<style scoped>
.children-shell {
  display: flex;
  flex-direction: column;
  gap: 1.4rem;
  padding: 1.65rem;
  border-radius: 1.75rem;
  border: 1px solid rgba(226, 232, 240, 0.7);
  background: #fff;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.children-shell:hover {
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

.section-link,
.rule-link,
.empty-cta {
  border: none;
  background: transparent;
  padding: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-banner,
.empty-state {
  padding: 1.2rem 1.25rem;
  border-radius: 1.1rem;
  border: 1px solid rgba(226, 232, 240, 0.78);
  background: linear-gradient(180deg, rgba(250, 251, 253, 0.92), rgba(248, 250, 252, 0.78));
}

.summary-banner strong,
.empty-state strong {
  display: block;
  margin-bottom: 0.35rem;
  color: #0f172a;
}

.summary-banner p,
.empty-state p {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(245px, 1fr));
  gap: 0.85rem;
}

.rule-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.15rem;
  border-radius: 1.3rem;
  border: 1px solid rgba(226, 232, 240, 0.8);
  background: rgba(255, 255, 255, 0.76);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.rule-card:hover {
  transform: translateY(-1px);
  border-color: rgba(203, 213, 225, 0.92);
  box-shadow: 0 16px 30px -24px rgba(15, 23, 42, 0.1);
}

.rule-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.variation {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.68rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.rule-head h3 {
  margin: 0;
  font-size: 1rem;
  color: #0f172a;
}

.rule-head p {
  margin: 0.22rem 0 0;
  color: #64748b;
}

.badge {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
}

.badge--active {
  color: #0f766e;
  background: rgba(45, 212, 191, 0.14);
  border: 1px solid rgba(45, 212, 191, 0.24);
}

.badge--muted {
  color: #475569;
  background: rgba(148, 163, 184, 0.16);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.rule-facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0;
}

.rule-facts dt {
  margin-bottom: 0.22rem;
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.rule-facts dd {
  margin: 0;
  color: #0f172a;
  font-weight: 600;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chip {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0.28rem 0.78rem;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
}

.chip--active {
  color: #0f766e;
  background: rgba(240, 253, 250, 0.95);
  border: 1px solid rgba(45, 212, 191, 0.2);
}

.chip--muted {
  color: #475569;
  background: rgba(248, 250, 252, 0.95);
  border: 1px solid rgba(203, 213, 225, 0.85);
}

.empty-state {
  text-align: left;
}

.empty-cta {
  margin-top: 0.9rem;
}

@media (max-width: 720px) {
  .children-shell {
    padding: 1.25rem;
    border-radius: 1.35rem;
  }

  .section-head {
    flex-direction: column;
    align-items: stretch;
  }

  .rule-facts {
    grid-template-columns: 1fr;
  }
}
</style>
