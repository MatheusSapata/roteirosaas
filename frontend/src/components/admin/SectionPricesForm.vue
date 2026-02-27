<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Preços</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>
    <div class="space-y-3">
      <div v-for="(item, index) in local.items" :key="index" class="grid gap-3 rounded-lg border border-slate-100 p-3 md:grid-cols-3">
        <input v-model="item.title" placeholder="Título" class="rounded-lg border border-slate-200 px-3 py-2" />
        <input v-model.number="item.price" type="number" placeholder="Preço" class="rounded-lg border border-slate-200 px-3 py-2" />
        <input v-model="item.description" placeholder="Descrição" class="rounded-lg border border-slate-200 px-3 py-2" />
        <button class="text-left text-sm text-red-500" @click="removeItem(index)">Remover</button>
      </div>
      <button class="text-sm font-semibold text-brand" @click="addItem">+ Adicionar preço</button>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Layout</label>
        <select v-model="local.layout" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="cards">Cards</option>
          <option value="columns">Colunas</option>
          <option value="highlight">Plano destaque</option>
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
    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.fullWidth" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Ocupar largura total</label>
    </div>
    <div>
      <label class="text-sm font-semibold text-slate-600">Cor do botão</label>
      <div class="mt-1 flex items-center gap-2">
        <input type="color" v-model="local.ctaColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
        <input v-model="local.ctaColor" placeholder="#0ea5e9" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import type { PricesSection } from "../../types/page";

const props = defineProps<{ modelValue: PricesSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PricesSection): void }>();

const local = reactive<PricesSection>({
  layout: "cards",
  ...props.modelValue,
  items: Array.isArray(props.modelValue.items) ? [...props.modelValue.items] : []
});
let syncing = false;
const syncFromProps = (value: PricesSection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = value.layout || "cards";
  local.items = Array.isArray(value.items) ? value.items.map(item => ({ ...item })) : [];
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

const addItem = () => local.items.push({ title: "", price: 0, description: "" });
const removeItem = (index: number) => local.items.splice(index, 1);

watch(
  () => ({ ...local, items: local.items.map(item => ({ ...item })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as PricesSection);
  },
  { deep: true }
);
</script>
