<template>
  <div v-if="visible" class="drawer">
    <div class="drawer__backdrop" @click="$emit('close')"></div>
    <section class="drawer__panel">
      <header class="drawer__header">
        <div>
          <p class="eyebrow">Transporte rodoviario</p>
          <h3>Configurar operacao</h3>
          <p class="muted">Habilite transporte, controle overbooking e acesse o mapa de assentos.</p>
        </div>
        <button type="button" class="icon-btn" @click="$emit('close')">x</button>
      </header>

      <div class="drawer__body">
        <label class="toggle">
          <input type="checkbox" v-model="form.is_road_trip" />
          <span>Habilitar rodoviario</span>
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="form.allow_oversell" />
          <span>Permitir overbooking</span>
        </label>
        <label class="field">
          <span>Estrategia de estoque</span>
          <select v-model="form.inventory_strategy">
            <option value="manual">Manual</option>
            <option value="unlimited">Ilimitado</option>
          </select>
        </label>
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
        <div class="info-card">
          <p class="text-sm text-slate-600">
            Ajuste os layouts e configuracoes avancadas diretamente no mapa de assentos.
          </p>
          <button type="button" class="pill" @click="$emit('open-seatmap')" :disabled="!canOpenSeatmap">
            Abrir mapa de assentos
          </button>
        </div>
      </div>

      <footer class="drawer__footer">
        <button type="button" class="pill" @click="$emit('close')">Cancelar</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="submit">
          {{ saving ? "Salvando..." : "Salvar" }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";

type TransportForm = {
  is_road_trip: boolean;
  allow_oversell: boolean;
  inventory_strategy: "manual" | "unlimited";
  total_slots: number;
  available_slots: number;
};

const props = defineProps<{
  visible: boolean;
  value: TransportForm;
  saving?: boolean;
  canOpenSeatmap?: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", payload: TransportForm): void;
  (e: "open-seatmap"): void;
}>();

const form = reactive<TransportForm>({
  is_road_trip: false,
  allow_oversell: false,
  inventory_strategy: "manual",
  total_slots: 0,
  available_slots: 0,
});

watch(
  () => props.value,
  value => {
    if (!value) return;
    Object.assign(form, value);
  },
  { immediate: true, deep: true },
);

const canOpenSeatmap = computed(() => props.canOpenSeatmap && form.is_road_trip);

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
.field select,
.field input {
  border-radius: 1rem;
  border: 1px solid #cbd5f5;
  padding: 0.6rem 0.8rem;
}
.toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #475569;
}
.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}
.info-card {
  border-radius: 1rem;
  border: 1px dashed #cbd5f5;
  padding: 1rem;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.pill {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.2);
  padding: 0.4rem 1rem;
  font-weight: 600;
  align-self: flex-start;
}
.btn-primary {
  border-radius: 999px;
  background: #10b981;
  color: white;
  padding: 0.5rem 1.25rem;
  font-weight: 600;
}
</style>
