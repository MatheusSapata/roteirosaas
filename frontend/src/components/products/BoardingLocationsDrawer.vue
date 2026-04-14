<template>
  <div v-if="visible" class="drawer">
    <div class="drawer__backdrop" @click="$emit('close')"></div>
    <section class="drawer__panel">
      <header class="drawer__header">
        <div>
          <p class="eyebrow">Locais de embarque</p>
          <h3>Defina pontos oficiais</h3>
          <p class="muted">Esses locais aparecem em formulários, contratos e comunicados aos passageiros.</p>
        </div>
        <button type="button" class="icon-btn" @click="$emit('close')">x</button>
      </header>

      <div class="drawer__body">
        <div class="space-y-3">
          <div v-if="loading" class="placeholder">Carregando locais cadastrados...</div>
          <div v-else class="space-y-3">
            <div v-for="(location, index) in form" :key="index" class="location-row">
              <input
                v-model="form[index]"
                type="text"
                class="input"
                placeholder="Terminal Tiete - Plataforma 20"
              />
              <button type="button" class="icon-btn" @click="remove(index)" :disabled="form.length === 1">
                -
              </button>
            </div>
            <button type="button" class="ghost" @click="add">Adicionar local</button>
          </div>
        </div>
      </div>

      <footer class="drawer__footer">
        <button type="button" class="pill" @click="$emit('close')">Cancelar</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="submit">
          {{ saving ? "Salvando..." : "Salvar locais" }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";

const props = defineProps<{
  visible: boolean;
  value: string[];
  saving?: boolean;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", payload: string[]): void;
}>();

const form = reactive<string[]>([""]);

const syncForm = (value: string[] | undefined) => {
  const next = value && value.length ? [...value] : [""];
  form.splice(0, form.length, ...next);
};

watch(
  () => props.value,
  value => syncForm(value),
  { immediate: true, deep: true },
);

const add = () => {
  form.push("");
};

const remove = (index: number) => {
  if (form.length === 1) {
    form[0] = "";
    return;
  }
  form.splice(index, 1);
};

const submit = () => {
  const normalized = form.map(item => item.trim()).filter(Boolean);
  emit("save", normalized);
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
  width: min(460px, 90vw);
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
.location-row {
  display: flex;
  gap: 0.5rem;
}
.input {
  flex: 1;
  border-radius: 1rem;
  border: 1px solid #cbd5f5;
  padding: 0.6rem 0.8rem;
}
.ghost {
  border: 1px dashed #cbd5f5;
  border-radius: 999px;
  padding: 0.45rem 1rem;
  font-weight: 600;
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
.placeholder {
  border: 1px dashed #cbd5f5;
  border-radius: 1rem;
  padding: 1rem;
  text-align: center;
  color: #64748b;
}
</style>
