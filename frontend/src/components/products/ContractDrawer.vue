<template>
  <div v-if="visible" class="drawer">
    <div class="drawer__backdrop" @click="$emit('close')"></div>
    <section class="drawer__panel">
      <header class="drawer__header">
        <div>
          <p class="eyebrow">Template de contrato</p>
          <h3>Selecionar modelo</h3>
          <p class="muted">Escolha qual documento sera enviado automaticamente apos cada venda.</p>
        </div>
        <button type="button" class="icon-btn" @click="$emit('close')">x</button>
      </header>

      <div class="drawer__body">
        <div v-if="loading" class="placeholder">Carregando templates disponiveis...</div>
        <div v-else class="space-y-3">
          <label class="template-option">
            <input type="radio" :value="null" v-model="selected" />
            <div>
              <p class="title">Sem contrato</p>
              <p class="muted">Nenhum documento sera enviado automaticamente para este produto.</p>
            </div>
          </label>

          <div v-if="!templates.length" class="placeholder">
            Nenhum template cadastrado. Configure em Juridico &gt; Contratos.
          </div>

          <label v-for="template in templates" :key="template.id" class="template-option">
            <input type="radio" :value="template.id" v-model="selected" />
            <div>
              <p class="title">{{ template.name }}</p>
              <p class="muted">{{ template.description || "Envio padrao apos confirmacao" }}</p>
            </div>
          </label>
        </div>
        <button type="button" class="ghost" @click="$emit('manage')">Ir para gestao de contratos</button>
      </div>

      <footer class="drawer__footer">
        <button type="button" class="pill" @click="$emit('close')">Cancelar</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="submit">
          {{ saving ? "Salvando..." : "Salvar template" }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type { LegalTemplateSummary } from "../../types/legal";

const props = defineProps<{
  visible: boolean;
  templates: LegalTemplateSummary[];
  selectedId: number | null;
  loading?: boolean;
  saving?: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", templateId: number | null): void;
  (e: "manage"): void;
}>();

const selected = ref<number | null>(null);

watch(
  () => props.selectedId,
  id => {
    selected.value = id ?? null;
  },
  { immediate: true },
);

const submit = () => {
  emit("save", selected.value ?? null);
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
  margin-bottom: 1rem;
}
.drawer__body {
  flex: 1;
  overflow-y: auto;
  padding-right: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
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
.template-option {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 0.9rem;
  display: flex;
  gap: 0.75rem;
  background: #f8fafc;
}
.template-option input {
  margin-top: 0.3rem;
}
.title {
  font-weight: 600;
  color: #0f172a;
}
.ghost {
  border: 1px dashed #cbd5f5;
  border-radius: 999px;
  padding: 0.4rem 1rem;
  font-weight: 600;
  align-self: flex-start;
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
