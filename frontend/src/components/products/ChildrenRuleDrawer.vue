<template>
  <div v-if="visible" class="drawer">
    <div class="drawer__backdrop" @click="$emit('close')"></div>
    <section class="drawer__panel">
      <header class="drawer__header">
        <div>
          <p class="eyebrow">Faixa etaria</p>
          <h3>{{ variationName }}</h3>
          <p class="muted">Ajuste regras de cobranca para a faixa selecionada.</p>
        </div>
        <button type="button" class="icon-btn" @click="$emit('close')">x</button>
      </header>

      <div class="drawer__body">
        <label class="field">
          <span>Nome</span>
          <input v-model="form.label" type="text" />
        </label>
        <div class="grid-2">
          <label class="field">
            <span>Idade minima</span>
            <input type="number" min="0" v-model.number="form.min_age" />
          </label>
          <label class="field">
            <span>Idade maxima</span>
            <input type="number" min="0" v-model.number="form.max_age" />
          </label>
        </div>
        <label class="field">
          <span>Tipo de cobranca</span>
          <select v-model="form.pricing_mode">
            <option value="free">Gratuito</option>
            <option value="extra">Adicional</option>
          </select>
        </label>
        <label class="field" v-if="form.pricing_mode === 'extra'">
          <span>Valor adicional</span>
          <input type="number" min="0" step="0.01" v-model.number="form.extra_amount" />
        </label>
        <label class="field">
          <span>Maximo por pacote</span>
          <input type="number" min="0" v-model.number="form.max_quantity" />
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="form.enabled" />
          <span>Habilitar faixa</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="form.counts_towards_capacity" />
          <span>Consome vaga</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="form.counts_as_passenger" />
          <span>Conta como passageiro</span>
        </label>
      </div>

      <footer class="drawer__footer">
        <button type="button" class="pill" @click="$emit('close')">Cancelar</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="submit">
          {{ saving ? "Salvando..." : "Salvar faixa" }}
        </button>
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
  pricing_mode: "free" | "extra";
  extra_amount: number;
  max_quantity: number | null;
  counts_towards_capacity: boolean;
  counts_as_passenger: boolean;
  enabled: boolean;
};

const props = defineProps<{
  visible: boolean;
  variationName: string;
  rule: ChildRuleForm | null;
  saving?: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", payload: ChildRuleForm): void;
}>();

const form = reactive<ChildRuleForm>({
  key: "",
  label: "",
  min_age: 0,
  max_age: 0,
  pricing_mode: "free",
  extra_amount: 0,
  max_quantity: null,
  counts_towards_capacity: false,
  counts_as_passenger: true,
  enabled: false,
});

watch(
  () => props.rule,
  value => {
    if (!value) return;
    Object.assign(form, value);
  },
  { immediate: true, deep: true },
);

const submit = () => {
  emit("save", { ...form });
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
  width: min(420px, 90vw);
  background: white;
  border-radius: 1.5rem 0 0 1.5rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  box-shadow: -25px 0 60px rgba(15, 23, 42, 0.25);
}
.drawer__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.2);
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
.field select {
  border-radius: 1rem;
  border: 1px solid #cbd5f5;
  padding: 0.6rem 0.8rem;
}
.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}
.toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #475569;
}
.pill {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.2);
  padding: 0.4rem 1rem;
  font-weight: 600;
}
.btn-primary {
  border-radius: 999px;
  background: #10b981;
  color: white;
  padding: 0.5rem 1.25rem;
  font-weight: 600;
}
</style>
