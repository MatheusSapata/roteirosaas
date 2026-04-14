<template>
  <section class="card">
    <header class="card-header">
      <div>
        <p class="eyebrow">Politica infantil</p>
        <h2>Criancas e faixas etarias</h2>
        <p class="muted">Controle quem pode viajar em cada pacote, cobrancas extras e impacto em vagas.</p>
      </div>
    </header>

    <div class="policy-summary" v-if="rules.length">
      <p class="text-sm text-slate-600">
        {{ enabledCount }} faixa(s) ativa(s) distribuida(s) entre os pacotes. Ajuste as regras para refinar sua estrategia
        comercial.
      </p>
    </div>
    <div v-else class="empty-state">
      <p class="font-semibold text-slate-700">Nenhuma faixa configurada.</p>
      <p class="text-sm text-slate-500">Ative politicas infantis nos pacotes para oferecer tarifas diferenciadas.</p>
    </div>

    <div v-if="rules.length" class="rules-grid">
      <article v-for="rule in rules" :key="`${rule.variationIndex}-${rule.key}`" class="rule-card">
        <header>
          <div>
            <p class="variation">{{ rule.variationName }}</p>
            <h3>{{ rule.label || rule.key }}</h3>
            <p class="ages">{{ rule.min_age }} a {{ rule.max_age }} anos</p>
          </div>
          <span class="badge" :class="rule.enabled ? 'badge-success' : 'badge-muted'">
            {{ rule.enabled ? "Ativa" : "Inativa" }}
          </span>
        </header>
        <dl>
          <div>
            <dt>Tipo</dt>
            <dd>{{ rule.pricing_mode === "extra" ? "Adicional" : "Gratuito" }}</dd>
          </div>
          <div>
            <dt>Valor</dt>
            <dd>{{ rule.pricing_mode === "extra" ? formatCurrency(rule.extra_amount) : "R$ 0,00" }}</dd>
          </div>
          <div>
            <dt>Maximo por pacote</dt>
            <dd>{{ rule.max_quantity ?? "Sem limite" }}</dd>
          </div>
        </dl>
        <div class="chips">
          <span class="chip" :class="rule.counts_towards_capacity ? 'chip-emerald' : 'chip-muted'">
            Consome vaga
          </span>
          <span class="chip" :class="rule.counts_as_passenger ? 'chip-emerald' : 'chip-muted'">
            Conta como passageiro
          </span>
        </div>
        <footer>
          <button type="button" class="pill" @click="$emit('edit', rule)">Editar faixa</button>
        </footer>
      </article>
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

const emit = defineEmits<{
  (e: "edit", payload: ChildRuleView): void;
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
.card {
  background: white;
  border-radius: 1.5rem;
  border: 1px solid #e2e8f0;
  padding: 1.5rem;
  box-shadow: 0 15px 40px -25px rgba(15, 23, 42, 0.35);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.card-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
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
.policy-summary {
  background: #f8fafc;
  border-radius: 1.1rem;
  padding: 1rem 1.25rem;
  border: 1px solid #e2e8f0;
}
.rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}
.rule-card {
  border: 1px solid #e2e8f0;
  border-radius: 0.9rem;
  padding: 0.75rem;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.rule-card header {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}
.variation {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: #94a3b8;
}
.rule-card h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
}
.ages {
  font-size: 0.85rem;
  color: #64748b;
}
.badge {
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge-success {
  background: rgba(52, 211, 153, 0.2);
  color: #047857;
}
.badge-muted {
  background: rgba(148, 163, 184, 0.2);
  color: #475569;
}
.rule-card dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}
.rule-card dt {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: #94a3b8;
}
.rule-card dd {
  font-size: 0.95rem;
  font-weight: 600;
  color: #0f172a;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.chip {
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
}
.chip-emerald {
  background: rgba(52, 211, 153, 0.15);
  color: #047857;
}
.chip-muted {
  background: rgba(148, 163, 184, 0.15);
  color: #475569;
}
.pill {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.2);
  padding: 0.4rem 1rem;
  font-weight: 600;
}
.empty-state {
  border: 1px dashed #cbd5f5;
  border-radius: 1.25rem;
  padding: 1.5rem;
  text-align: center;
  background: #f8fafc;
}
</style>
