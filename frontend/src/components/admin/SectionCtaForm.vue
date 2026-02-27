<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">CTA / Contato</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Texto</label>
        <input v-model="local.label" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div v-if="local.ctaMode !== 'section'">
        <label class="text-sm font-semibold text-slate-600">Link</label>
        <input v-model="local.link" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>
    <CtaActionPicker
      v-model:mode="local.ctaMode"
      v-model:sectionId="local.ctaSectionId"
      :current-anchor="local.anchorId"
    />
    <div>
      <label class="text-sm font-semibold text-slate-600">Descrição (opcional)</label>
      <textarea v-model="local.description" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"></textarea>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Layout</label>
        <select v-model="local.layout" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="bar">Barra</option>
          <option value="split">Split</option>
          <option value="card">Card</option>
          <option value="simple">Simples (full width)</option>
        </select>
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor de fundo</label>
        <select v-model="local.backgroundColor" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option v-for="option in colorOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <ImageUploadField
        v-model="local.backgroundImage"
        label="Imagem de fundo (opcional)"
        hint="Se enviar uma imagem, ela será usada como fundo e aplicaremos um overlay para garantir legibilidade."
      />
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor do texto</label>
        <div class="mt-1 flex items-center gap-2">
          <input type="color" v-model="local.textColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
          <input v-model="local.textColor" placeholder="#ffffff" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>
    </div>
    <div>
      <label class="text-sm font-semibold text-slate-600">Cor do botão</label>
      <div class="mt-1 flex items-center gap-2">
        <input type="color" v-model="local.ctaColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
        <input v-model="local.ctaColor" placeholder="#0ea5e9" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>
    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.fullWidth" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Ocupar largura total</label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import type { CtaSection } from "../../types/page";

const props = defineProps<{ modelValue: CtaSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: CtaSection): void }>();

const local = reactive<CtaSection>({
  layout: "bar",
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null,
  ...props.modelValue
});
let syncing = false;
const syncFromProps = (value: CtaSection) => {
  syncing = true;
  Object.assign(local, value);
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  nextTick(() => {
    syncing = false;
  });
};

watch(
  () => props.modelValue,
  value => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);
const colorOptions = [
  { label: "Branco", value: "#ffffff" },
  { label: "Cinza suave", value: "#f8fafc" },
  { label: "Azul claro", value: "#e0f2fe" },
  { label: "Marfim", value: "#fef3c7" },
  { label: "Rosa claro", value: "#fdf2f8" },
  { label: "Verde menta", value: "#ecfdf3" },
  { label: "Lilás", value: "#f5f3ff" },
  { label: "Turquesa", value: "#e0f7f7" },
  { label: "Cinza médio", value: "#e2e8f0" },
  { label: "Grafite", value: "#0f172a" }
];

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as CtaSection);
  },
  { deep: true }
);
</script>
