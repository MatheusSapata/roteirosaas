<template>
  <section class="contract-shell">
    <header class="section-head">
      <div>
        <p class="eyebrow">Contrato e documentos</p>
        <h2>Automacao juridica do produto</h2>
        <p class="support-copy">Recurso com acabamento enterprise para garantir contrato certo em cada venda.</p>
      </div>
      <button type="button" class="section-btn" @click="$emit('change')" :disabled="disabled">
        {{ hasTemplate ? "Alterar template" : "Vincular template" }}
      </button>
    </header>

    <div class="contract-card" :class="{ 'contract-card--empty': !hasTemplate }">
      <div class="contract-copy">
        <span class="contract-badge">{{ hasTemplate ? "Envio automatico" : "Sem template ativo" }}</span>
        <h3>{{ hasTemplate ? templateName : "Nenhum template vinculado" }}</h3>
        <p>
          {{
            hasTemplate
              ? templateDescription || "O cliente recebe este documento automaticamente apos a confirmacao do pagamento."
              : "Selecione um modelo para transformar a venda em um fluxo juridico automatizado."
          }}
        </p>
      </div>

      <div class="contract-actions" v-if="hasTemplate">
        <button type="button" class="ghost-btn" @click="$emit('view')">Visualizar</button>
        <button type="button" class="ghost-btn" @click="$emit('manage')">Abrir juridico</button>
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
.contract-shell {
  display: flex;
  flex-direction: column;
  gap: 1.35rem;
  padding: 1.65rem;
  border-radius: 1.75rem;
  border: 1px solid rgba(226, 232, 240, 0.7);
  background: #fff;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.contract-shell:hover {
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

.section-btn,
.ghost-btn {
  min-height: 2.75rem;
  padding: 0.72rem 1rem;
  border-radius: 1rem;
  font-weight: 700;
}

.section-btn {
  border: 1px solid rgba(16, 185, 129, 0.1);
  background: linear-gradient(180deg, #10b981, #059669);
  color: #fff;
}

.contract-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.15rem;
  border-radius: 1.15rem;
  border: 1px solid rgba(226, 232, 240, 0.78);
  background:
    radial-gradient(circle at top left, rgba(191, 219, 254, 0.12), transparent 30%),
    linear-gradient(180deg, rgba(250, 251, 253, 0.9), rgba(255, 255, 255, 0.96));
  box-shadow: 0 14px 26px -24px rgba(15, 23, 42, 0.12);
}

.contract-card--empty {
  background: transparent;
}

.contract-badge {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0.28rem 0.78rem;
  border-radius: 999px;
  margin-bottom: 0.75rem;
  font-size: 0.74rem;
  font-weight: 700;
  color: #0f766e;
  background: rgba(45, 212, 191, 0.14);
  border: 1px solid rgba(45, 212, 191, 0.22);
}

.contract-copy h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
  color: #020617;
}

.contract-copy p {
  margin: 0.45rem 0 0;
  max-width: 42rem;
  line-height: 1.6;
  color: #64748b;
}

.contract-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  justify-content: flex-end;
}

.ghost-btn {
  border: 1px solid rgba(203, 213, 225, 0.88);
  background: rgba(255, 255, 255, 0.9);
  color: #0f172a;
}

@media (max-width: 720px) {
  .contract-shell {
    padding: 1.25rem;
    border-radius: 1.35rem;
  }

  .section-head,
  .contract-card {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
