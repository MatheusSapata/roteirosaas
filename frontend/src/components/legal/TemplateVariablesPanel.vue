<template>
  <aside class="flex h-full flex-col rounded-3xl border border-slate-100 bg-white/80 p-5 shadow-sm">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">{{ copy.header }}</p>
        <p class="text-sm text-slate-500">{{ copy.hint }}</p>
      </div>
      <button type="button" class="btn-secondary" @click="$emit('preview')">
        {{ copy.preview }}
      </button>
    </div>
    <div class="mt-6 flex flex-1 flex-col">
      <div v-if="tabs.length" class="tab-bar custom-scroll-x">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="tab-button"
          :class="tab.value === activeCategoryKey ? 'tab-button--active' : ''"
          @click="activeCategoryKey = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="mt-4 flex-1 space-y-4 overflow-y-auto pr-1 custom-scroll">
        <div v-if="isLoading" class="rounded-2xl border border-dashed border-slate-200 p-4 text-sm text-slate-500">
          {{ copy.loading }}
        </div>
        <div v-else-if="!tabs.length" class="rounded-2xl border border-dashed border-slate-200 p-4 text-sm text-slate-500">
          {{ copy.empty }}
        </div>
        <div
          v-else
          v-for="category in displayedCategories"
          :key="category.key"
          class="space-y-3 rounded-2xl bg-slate-50/80 p-4"
        >
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
            {{ localize(category.label) }}
          </p>
          <div
            v-for="variable in category.variables"
            :key="variable.key"
            class="rounded-2xl border border-slate-100 bg-white/80 p-3 shadow-inner shadow-slate-100 transition hover:shadow-md"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ localize(variable.label) }}</p>
                <p class="text-xs text-slate-500">{{ localize(variable.description) }}</p>
                <p class="mt-1 font-mono text-xs text-emerald-600">{{ variable.placeholder }}</p>
                <p class="text-xs text-slate-400">Ex.: {{ variable.sample_value }}</p>
              </div>
              <div class="flex flex-col items-end gap-2">
                <button type="button" class="btn-tag" @click="$emit('insert', variable.placeholder)">
                  {{ copy.insert }}
                </button>
                <button type="button" class="text-xs font-semibold text-slate-500 hover:text-slate-900" @click="copyPlaceholder(variable.placeholder, variable.key)">
                  {{ copy.copy }}
                </button>
                <span v-if="copiedKey === variable.key" class="text-[11px] font-semibold text-emerald-600">
                  {{ copy.copied }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { LegalVariableCategory, LocalizedText } from "../../types/legal";
import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";

const props = defineProps<{
  categories: LegalVariableCategory[];
  loading?: boolean;
}>();

defineEmits<{
  (e: "preview"): void;
  (e: "insert", placeholder: string): void;
}>();

const t = createAdminLocalizer();
const isLoading = computed(() => props.loading ?? false);
const copiedKey = ref<string | null>(null);
const activeCategoryKey = ref<string | null>(null);

const copy = {
  header: t({ pt: "Variáveis dinâmicas", es: "Variables dinámicas" }),
  hint: t({
    pt: "Clique para inserir diretamente no contrato.",
    es: "Haz clic para insertar directamente en el contrato.",
  }),
  preview: t({ pt: "Visualizar", es: "Previsualizar" }),
  loading: t({ pt: "Carregando variáveis...", es: "Cargando variables..." }),
  empty: t({ pt: "Nenhuma variável definida.", es: "No hay variables definidas." }),
  insert: t({ pt: "Inserir", es: "Insertar" }),
  copy: t({ pt: "Copiar", es: "Copiar" }),
  copied: t({ pt: "Copiado!", es: "¡Copiado!" }),
};

const adminLanguage = getAdminLanguage();

watch(
  () => props.categories,
  value => {
    if (!value.length) {
      activeCategoryKey.value = null;
      return;
    }
    if (!activeCategoryKey.value || !value.some(category => category.key === activeCategoryKey.value)) {
      activeCategoryKey.value = value[0].key;
    }
  },
  { immediate: true }
);

const tabs = computed(() =>
  props.categories.map(category => ({
    label: localize(category.label),
    value: category.key,
  }))
);

const displayedCategories = computed(() => {
  if (!activeCategoryKey.value) return [];
  return props.categories.filter(category => category.key === activeCategoryKey.value);
});

const localize = (value?: LocalizedText | string | null) => {
  if (!value) return "";
  if (typeof value === "string") return value;
  return value[adminLanguage] || value.pt || value.es || "";
};

const copyPlaceholder = async (placeholder: string, key: string) => {
  try {
    await navigator.clipboard.writeText(placeholder);
    copiedKey.value = key;
    setTimeout(() => {
      if (copiedKey.value === key) copiedKey.value = null;
    }, 1500);
  } catch (error) {
    console.error("Erro ao copiar variável", error);
  }
};
</script>

<style scoped>
.btn-secondary {
  @apply rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs font-semibold text-slate-600 shadow-sm transition hover:border-emerald-500 hover:text-emerald-600;
}
.btn-tag {
  @apply rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 transition hover:-translate-y-0.5 hover:border-emerald-300 hover:bg-white;
}
.tab-bar {
  @apply flex gap-2 overflow-x-auto pb-1;
}
.tab-button {
  @apply rounded-full border border-transparent bg-slate-100 px-4 py-1.5 text-xs font-semibold text-slate-500 transition hover:text-slate-900;
}
.tab-button--active {
  @apply border-emerald-200 bg-white text-emerald-600 shadow-sm;
}
.custom-scroll {
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 transparent;
}
.custom-scroll::-webkit-scrollbar {
  width: 6px;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background-color: #cbd5f5;
  border-radius: 9999px;
}
.custom-scroll-x {
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 transparent;
}
.custom-scroll-x::-webkit-scrollbar {
  height: 6px;
}
.custom-scroll-x::-webkit-scrollbar-thumb {
  background-color: #cbd5f5;
  border-radius: 9999px;
}
</style>
