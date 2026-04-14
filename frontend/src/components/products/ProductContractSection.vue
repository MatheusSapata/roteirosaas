<template>
  <section class="contract-card">
    <header class="card-header">
      <div>
        <p class="eyebrow">Contrato vinculado</p>
        <h2>Automacao juridica</h2>
        <p class="muted">Defina qual documento acompanha cada venda.</p>
      </div>
      <button type="button" class="pill" @click="$emit('change')" :disabled="disabled">
        {{ hasTemplate ? "Trocar template" : "Vincular template" }}
      </button>
    </header>

    <div class="contract-body" :class="{ 'contract-body--empty': !hasTemplate }">
      <div>
        <div class="badge" v-if="hasTemplate">Envio automatico</div>
        <h3 v-if="hasTemplate">{{ templateName }}</h3>
        <p v-if="templateDescription" class="muted">{{ templateDescription }}</p>
        <p v-else-if="hasTemplate" class="muted">O cliente recebe o documento apos confirmar o pagamento.</p>
        <p v-else class="muted">Nenhum template selecionado. Vincule um modelo para automatizar contratos.</p>
      </div>
      <div class="actions" v-if="hasTemplate">
        <button type="button" class="btn ghost" @click="$emit('view')">Visualizar</button>
        <button type="button" class="btn ghost" @click="$emit('manage')">Abrir juridico</button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  hasTemplate: boolean;
  templateName?: string | null;
  templateDescription?: string | null;
  disabled?: boolean;
}>();

defineEmits<{
  (e: "change"): void;
  (e: "view"): void;
  (e: "manage"): void;
}>();
</script>

<style scoped>
.contract-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 1.5rem;
  padding: 1.5rem;
  box-shadow: 0 20px 45px -35px rgba(15, 23, 42, 0.4);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 0.7rem;
  color: #94a3b8;
}
.muted {
  font-size: 0.9rem;
  color: #475569;
}
.contract-body {
  border: 1px solid #e2e8f0;
  border-radius: 1.25rem;
  padding: 1.25rem;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.contract-body--empty {
  background: #fff;
}
.label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #94a3b8;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.actions .btn {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.15);
  padding: 0.4rem 1rem;
  font-weight: 600;
  color: #0f172a;
  background: transparent;
}
.contract-body h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #0f172a;
}
.badge {
  padding: 0.25rem 0.85rem;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: #047857;
}
</style>
