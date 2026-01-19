<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Depoimentos</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>

    <div class="space-y-3">
      <div v-for="(item, index) in local.items" :key="index" class="rounded-lg border border-slate-100 p-3">
        <input v-model="item.name" placeholder="Nome" class="mb-2 w-full rounded-lg border border-slate-200 px-3 py-2" />
        <input v-model="item.role" placeholder="Cargo / Empresa (opcional)" class="mb-2 w-full rounded-lg border border-slate-200 px-3 py-2" />
        <ImageUploadField v-model="item.avatar" label="Foto (opcional)" hint="Mostrada junto ao depoimento." />
        <textarea v-model="item.text" placeholder="Depoimento" class="w-full rounded-lg border border-slate-200 px-3 py-2"></textarea>
        <button class="text-sm text-red-500" @click="removeItem(index)">Remover</button>
      </div>
      <button class="text-sm font-semibold text-brand" @click="addItem">+ Adicionar depoimento</button>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Título (opcional)</label>
        <input v-model="local.title" placeholder="Depoimentos" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Subtítulo (opcional)</label>
        <input v-model="local.subtitle" placeholder="O que dizem nossos clientes" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor de fundo</label>
        <select v-model="local.backgroundColor" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option v-for="option in colorOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor do destaque</label>
        <div class="mt-1 flex items-center gap-2">
          <input type="color" v-model="local.ctaColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
          <input v-model="local.ctaColor" placeholder="#5b49ff" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>
    </div>
    <div>
      <label class="text-sm font-semibold text-slate-600">Cor do card</label>
      <div class="mt-1 flex items-center gap-2">
        <input type="color" v-model="local.cardColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
        <input v-model="local.cardColor" placeholder="#ffffff" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>

    <div class="space-y-3">
      <CtaActionPicker
        v-model:mode="local.ctaMode"
        v-model:sectionId="local.ctaSectionId"
        :current-anchor="local.anchorId"
      />
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-sm font-semibold text-slate-600">Texto do CTA (opcional)</label>
          <input v-model="local.ctaLabel" placeholder="Falar com especialista" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div v-if="local.ctaMode !== 'section'">
          <label class="text-sm font-semibold text-slate-600">Link do CTA (opcional)</label>
          <input v-model="local.ctaLink" placeholder="https://..." class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import type { TestimonialsSection } from "../../types/page";

const props = defineProps<{ modelValue: TestimonialsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: TestimonialsSection): void }>();

const local = reactive<TestimonialsSection>({
  layout: "grid",
  cardColor: props.modelValue.cardColor || "#ffffff",
  ...props.modelValue,
  items: Array.isArray(props.modelValue.items) ? [...props.modelValue.items] : [],
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null
});
let syncing = false;
const syncFromProps = (value: TestimonialsSection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = value.layout || "grid";
  local.cardColor = value.cardColor || "#ffffff";
  local.items = Array.isArray(value.items) ? value.items.map(item => ({ ...item })) : [];
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  syncing = false;
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

const addItem = () => local.items.push({ name: "", text: "", avatar: "" });
const removeItem = (index: number) => local.items.splice(index, 1);

watch(
  () => ({ ...local, items: local.items.map(item => ({ ...item })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as TestimonialsSection);
  },
  { deep: true }
);
</script>
