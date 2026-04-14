<template>
  <div v-if="visible" class="drawer">
    <div class="drawer__backdrop" @click="$emit('close')"></div>
    <section class="drawer__panel">
      <header class="drawer__header">
        <div>
          <p class="eyebrow">Pacote</p>
          <h3>{{ localForm.name || "Novo pacote" }}</h3>
          <p class="muted">Configure valores, estoque e hospedagem.</p>
        </div>
        <button type="button" class="icon-btn" @click="$emit('close')">x</button>
      </header>

      <div class="drawer__body">
        <label class="field">
          <span>Nome</span>
          <input v-model="localForm.name" />
        </label>
        <label class="field">
          <span>Descricao</span>
          <textarea rows="2" v-model="localForm.description"></textarea>
        </label>

        <div class="grid-2">
          <label class="field">
            <span>Preco</span>
            <input type="number" min="0" step="0.01" v-model.number="localForm.price" />
          </label>
          <label class="field">
            <span>Pessoas incluidas</span>
            <input type="number" min="1" v-model.number="localForm.people_included" />
          </label>
        </div>

        <div class="grid-2">
          <label class="field">
            <span>Status</span>
            <select v-model="localForm.status">
              <option value="active">Ativo</option>
              <option value="inactive">Inativo</option>
            </select>
          </label>
          <label class="field">
            <span>Controle de estoque</span>
            <select v-model="localForm.stock_mode">
              <option value="product">Seguir produto</option>
              <option value="variant">Personalizado</option>
            </select>
          </label>
        </div>

        <div v-if="localForm.stock_mode === 'variant'" class="grid-2">
          <label class="field">
            <span>Total</span>
            <input type="number" min="0" v-model.number="localForm.total_slots" />
          </label>
          <label class="field">
            <span>Disponivel</span>
            <input type="number" min="0" v-model.number="localForm.available_slots" />
          </label>
        </div>

        <label class="toggle">
          <input type="checkbox" v-model="localForm.has_accommodation" />
          <span>Inclui hospedagem</span>
        </label>

        <div v-if="localForm.has_accommodation" class="grid-2">
          <label class="field">
            <span>Modo</span>
            <select v-model="localForm.accommodation_mode">
              <option value="private">Privativo</option>
              <option value="shared">Compartilhado</option>
            </select>
          </label>
          <label class="field">
            <span>Capacidade</span>
            <input type="number" min="1" v-model.number="localForm.room_capacity" />
          </label>
          <label class="field" v-if="localForm.accommodation_mode === 'shared'">
            <span>Vagas por unidade</span>
            <input type="number" min="1" v-model.number="localForm.slots_per_unit" />
          </label>
        </div>

        <div class="child-rules">
          <header>
            <h4>Politica de criancas</h4>
            <label class="toggle">
              <input type="checkbox" v-model="localForm.child_policy_enabled" />
              <span>Ativar</span>
            </label>
          </header>
          <div v-if="localForm.child_policy_enabled" class="space-y-3">
            <div v-for="(rule, index) in localForm.child_pricing_rules" :key="rule.key" class="rule-card">
              <div class="rule-header">
                <strong>{{ rule.label }}</strong>
                <label class="toggle">
                  <input type="checkbox" v-model="rule.enabled" />
                  <span>Habilitar</span>
                </label>
              </div>
              <div class="grid-2">
                <label class="field">
                  <span>Idade min.</span>
                  <input type="number" min="0" v-model.number="rule.min_age" />
                </label>
                <label class="field">
                  <span>Idade max.</span>
                  <input type="number" min="0" v-model.number="rule.max_age" />
                </label>
              </div>
              <div class="grid-2">
                <label class="field">
                  <span>Tipo</span>
                  <select v-model="rule.pricing_mode">
                    <option value="free">Gratis</option>
                    <option value="extra">Cobrar adicional</option>
                  </select>
                </label>
                <label class="field" v-if="rule.pricing_mode === 'extra'">
                  <span>Valor extra</span>
                  <input type="number" min="0" step="0.01" v-model.number="rule.extra_amount" />
                </label>
              </div>
              <div class="grid-2">
                <label class="toggle">
                  <input type="checkbox" v-model="rule.counts_towards_capacity" />
                  <span>Consome vaga</span>
                </label>
                <label class="toggle">
                  <input type="checkbox" v-model="rule.counts_as_passenger" />
                  <span>Conta como passageiro</span>
                </label>
              </div>
              <label class="field">
                <span>Maximo por pacote</span>
                <input type="number" min="0" v-model.number="rule.max_quantity" />
              </label>
            </div>
          </div>
        </div>
      </div>

      <footer class="drawer__footer">
        <button type="button" class="pill" @click="$emit('close')">Cancelar</button>
        <button type="button" class="pill danger" @click="$emit('remove')" v-if="!!variation?.public_id">Remover</button>
        <button type="button" class="btn-primary" @click="submit">Salvar</button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";

type ChildRuleForm = {
  key: string;
  label: string;
  min_age: number;
  max_age: number;
  enabled: boolean;
  pricing_mode: "free" | "extra";
  extra_amount: number;
  counts_towards_capacity: boolean;
  counts_as_passenger: boolean;
  max_quantity: number | null;
};

type PackageForm = {
  public_id: string | null;
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
  child_policy_enabled: boolean;
  child_pricing_rules: ChildRuleForm[];
};

const defaultChildRules = (): ChildRuleForm[] => [
  {
    key: "under_5",
    label: "Menores de 5 anos",
    min_age: 0,
    max_age: 4,
    enabled: false,
    pricing_mode: "free",
    extra_amount: 0,
    counts_towards_capacity: false,
    counts_as_passenger: true,
    max_quantity: null,
  },
  {
    key: "age_5_12",
    label: "De 5 a 12 anos",
    min_age: 5,
    max_age: 12,
    enabled: false,
    pricing_mode: "extra",
    extra_amount: 0,
    counts_towards_capacity: true,
    counts_as_passenger: true,
    max_quantity: null,
  },
];

const props = defineProps<{
  visible: boolean;
  variation: PackageForm | null;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", variation: PackageForm): void;
  (e: "remove"): void;
}>();

const localForm = reactive<PackageForm>({
  public_id: null,
  name: "",
  description: null,
  price: 0,
  people_included: 1,
  status: "active",
  stock_mode: "product",
  has_accommodation: false,
  accommodation_mode: "private",
  room_capacity: 1,
  slots_per_unit: 1,
  total_slots: null,
  available_slots: null,
  child_policy_enabled: false,
  child_pricing_rules: [],
});

const fillForm = (variation?: PackageForm | null) => {
  if (!variation) {
    Object.assign(localForm, {
      public_id: null,
      name: "",
      description: null,
      price: 0,
      people_included: 1,
      status: "active",
      stock_mode: "product",
      has_accommodation: false,
      accommodation_mode: "private",
      room_capacity: 1,
      slots_per_unit: 1,
      total_slots: null,
      available_slots: null,
      child_policy_enabled: false,
      child_pricing_rules: defaultChildRules(),
    });
  } else {
    Object.assign(localForm, {
      ...variation,
      child_pricing_rules: (variation.child_pricing_rules && variation.child_pricing_rules.length
        ? variation.child_pricing_rules
        : defaultChildRules()
      ).map(rule => ({ ...rule })),
    });
  }
};

watch(
  () => props.variation,
  newVariation => {
    fillForm(newVariation || null);
  },
  { immediate: true },
);

const submit = () => {
  emit("save", {
    ...localForm,
    child_pricing_rules: localForm.child_pricing_rules.map(rule => ({ ...rule })),
  });
};
</script>

<style scoped>
.drawer {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
}
.drawer__backdrop {
  flex: 1;
  background: rgba(15, 23, 42, 0.4);
}
.drawer__panel {
  width: min(480px, 90vw);
  background: #fff;
  border-radius: 1.5rem 0 0 1.5rem;
  box-shadow: -20px 0 60px rgba(15, 23, 42, 0.2);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}
.drawer__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}
.drawer__body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-right: 0.5rem;
}
.drawer__footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}
.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 0.7rem;
  color: #94a3b8;
}
.muted {
  color: #64748b;
}
.icon-btn {
  border: 1px solid rgba(15, 23, 42, 0.2);
  border-radius: 999px;
  width: 36px;
  height: 36px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: #475569;
}
.field input,
.field select,
.field textarea {
  border: 1px solid #cbd5f5;
  border-radius: 1rem;
  padding: 0.6rem 0.8rem;
}
.toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #475569;
}
.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}
.child-rules {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 1rem;
  background: #f8fafc;
}
.child-rules header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.rule-card {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 0.75rem;
  background: white;
}
.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.pill {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.2);
  padding: 0.4rem 1rem;
}
.pill.danger {
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.5);
}
.btn-primary {
  border-radius: 999px;
  background: #10b981;
  color: white;
  padding: 0.5rem 1.25rem;
  font-weight: 600;
}
</style>
