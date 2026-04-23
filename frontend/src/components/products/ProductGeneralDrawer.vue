<template>
  <div v-if="visible" class="drawer">
    <div class="drawer__backdrop" @click="$emit('close')"></div>
    <section class="drawer__panel">
      <header class="drawer__header">
        <div>
          <p class="eyebrow">Informacoes gerais</p>
          <h3>Editar dados do produto</h3>
          <p class="muted">Atualize status, datas e estrategia de estoque.</p>
        </div>
        <button type="button" class="icon-btn" @click="$emit('close')">x</button>
      </header>

      <div class="drawer__body">
        <label class="field">
          <span>Nome</span>
          <input v-model="form.name" />
        </label>
        <label class="field">
          <span>Descricao</span>
          <textarea rows="2" v-model="form.description"></textarea>
        </label>
        <div class="grid-2">
          <label class="field">
            <span>Status</span>
            <select v-model="form.status">
              <option value="draft">Rascunho</option>
              <option value="active">Ativo</option>
              <option value="archived">Arquivado</option>
            </select>
          </label>
          <label class="field">
            <span>Data da viagem</span>
            <input type="date" v-model="form.trip_date" />
          </label>
        </div>
        <label class="toggle">
          <input type="checkbox" v-model="form.date_is_flexible" />
          <span>Data flexivel</span>
        </label>
        <div class="grid-2">
          <label class="field">
            <span>Modo de agenda</span>
            <select v-model="form.schedule_mode">
              <option value="fixed_date">Fixed date</option>
              <option value="recurring">Recurring</option>
            </select>
          </label>
          <label class="field">
            <span>Timezone</span>
            <input v-model="form.timezone" :disabled="form.schedule_mode !== 'recurring'" placeholder="America/Sao_Paulo" />
          </label>
        </div>
        <div class="grid-2">
          <label class="field">
            <span>Estrategia de estoque</span>
            <select v-model="form.inventory_strategy">
              <option value="manual">Manual</option>
              <option value="unlimited">Ilimitado</option>
            </select>
          </label>
        </div>

        <div v-if="form.inventory_strategy === 'manual'" class="grid-2">
          <label class="field">
            <span>Vagas totais</span>
            <input type="number" min="0" v-model.number="form.total_slots" />
          </label>
          <label class="field">
            <span>Disponiveis</span>
            <input type="number" min="0" v-model.number="form.available_slots" />
          </label>
        </div>

        <label class="toggle">
          <input type="checkbox" v-model="form.allow_oversell" />
          <span>Permitir overbooking</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="form.is_road_trip" />
          <span>Excursao rodoviaria</span>
        </label>

        <section class="payment-methods">
          <p class="payment-methods__title">Formas de pagamento permitidas</p>
          <label class="toggle">
            <input type="checkbox" :checked="hasMethod('pix')" @change="toggleMethod('pix', $event)" />
            <span>PIX</span>
          </label>
          <label class="toggle">
            <input type="checkbox" :checked="hasMethod('credit_card')" @change="toggleMethod('credit_card', $event)" />
            <span>Cartão de crédito</span>
          </label>
          <label class="toggle">
            <input type="checkbox" :checked="hasMethod('boleto')" @change="toggleMethod('boleto', $event)" />
            <span>Boleto</span>
          </label>
          <p class="payment-methods__hint">Essas formas serão exibidas no checkout.</p>
        </section>
      </div>

      <footer class="drawer__footer">
        <button type="button" class="pill" @click="$emit('close')">Cancelar</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="submit">
          {{ saving ? "Salvando..." : "Salvar alteracoes" }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";

type GeneralForm = {
  name: string;
  description: string | null;
  status: string;
  trip_date: string | null;
  date_is_flexible: boolean;
  inventory_strategy: "manual" | "unlimited";
  total_slots: number;
  available_slots: number;
  allow_oversell: boolean;
  is_road_trip: boolean;
  schedule_mode: "fixed_date" | "recurring";
  timezone: string | null;
  allowed_payment_methods: Array<"pix" | "credit_card" | "boleto">;
};

const props = defineProps<{
  visible: boolean;
  value: GeneralForm;
  saving?: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", payload: GeneralForm): void;
}>();

const form = reactive<GeneralForm>({
  name: "",
  description: null,
  status: "draft",
  trip_date: null,
  date_is_flexible: false,
  inventory_strategy: "manual",
  total_slots: 0,
  available_slots: 0,
  allow_oversell: false,
  is_road_trip: false,
  schedule_mode: "fixed_date",
  timezone: "America/Sao_Paulo",
  allowed_payment_methods: ["pix", "credit_card", "boleto"],
});

watch(
  () => props.value,
  value => {
    if (!value) return;
    Object.assign(form, value);
  },
  { immediate: true, deep: true },
);

const submit = () => {
  if (!form.allowed_payment_methods.length) {
    form.allowed_payment_methods = ["pix"];
  }
  emit("save", { ...form });
};

const hasMethod = (method: "pix" | "credit_card" | "boleto") => form.allowed_payment_methods.includes(method);

const toggleMethod = (method: "pix" | "credit_card" | "boleto", event: Event) => {
  const checked = (event.target as HTMLInputElement).checked;
  if (checked && !form.allowed_payment_methods.includes(method)) {
    form.allowed_payment_methods = [...form.allowed_payment_methods, method];
    return;
  }
  if (!checked) {
    const next = form.allowed_payment_methods.filter(item => item !== method);
    form.allowed_payment_methods = next.length ? next : ["pix"];
  }
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
  width: min(440px, 90vw);
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
  margin-bottom: 1.5rem;
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
  margin-top: 1.25rem;
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
.field select,
.field textarea {
  border: 1px solid #cbd5f5;
  border-radius: 1rem;
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
  font-size: 0.85rem;
  color: #475569;
}
.payment-methods {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 0.8rem;
  background: #f8fafc;
}
.payment-methods__title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.35rem;
}
.payment-methods__hint {
  font-size: 0.75rem;
  color: #64748b;
}
.pill {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.2);
  padding: 0.4rem 1rem;
}
.btn-primary {
  border-radius: 999px;
  background: #10b981;
  color: white;
  padding: 0.5rem 1.25rem;
  font-weight: 600;
}
</style>
