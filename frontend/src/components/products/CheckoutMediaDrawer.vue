<template>
  <div v-if="visible" class="drawer">
    <div class="drawer__backdrop" @click="$emit('close')"></div>
    <section class="drawer__panel">
      <header class="drawer__header">
        <div>
          <p class="eyebrow">Midia do checkout</p>
          <h3>Atualizar imagens</h3>
          <p class="muted">Carregue arquivos em alta resolucao para reforcar a confianca no checkout.</p>
        </div>
        <button type="button" class="icon-btn" @click="$emit('close')">x</button>
      </header>

      <div class="drawer__body">
        <ImageUploadField
          v-model="form.banner"
          label="Banner principal"
          :hint="'Recomendado 1600x600px. Formatos: JPG ou PNG.'"
          :enable-crop="true"
          :crop-aspect="16 / 6"
        />
        <ImageUploadField
          v-model="form.product"
          label="Imagem do produto"
          :hint="'Recomendado 900x900px. Formatos: JPG ou PNG.'"
          :enable-crop="true"
          :crop-aspect="1"
        />
        <button type="button" class="ghost" @click="clearImages">Remover imagens</button>
      </div>

      <footer class="drawer__footer">
        <button type="button" class="pill" @click="$emit('close')">Cancelar</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="submit">
          {{ saving ? "Salvando..." : "Salvar midia" }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import ImageUploadField from "../admin/inputs/ImageUploadField.vue";

const props = defineProps<{
  visible: boolean;
  value: { banner: string | null; product: string | null };
  saving?: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", payload: { banner: string | null; product: string | null }): void;
}>();

const form = reactive<{ banner: string | null; product: string | null }>({
  banner: null,
  product: null,
});

watch(
  () => props.value,
  value => {
    if (!value) return;
    form.banner = value.banner || null;
    form.product = value.product || null;
  },
  { immediate: true, deep: true },
);

const clearImages = () => {
  form.banner = null;
  form.product = null;
};

const submit = () => {
  emit("save", { banner: form.banner, product: form.product });
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
  width: min(520px, 92vw);
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
.ghost {
  border: 1px dashed #cbd5f5;
  border-radius: 999px;
  padding: 0.4rem 1rem;
  font-weight: 600;
  color: #475569;
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
</style>
