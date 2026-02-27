<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Motivos / Por que escolher</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>

    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Título</label>
        <input v-model="local.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Subtítulo</label>
        <input v-model="local.subtitle" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">Cor de fundo</label>
      <input v-model="local.backgroundColor" placeholder="#f8fafc" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
    </div>

    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <p class="text-sm font-semibold text-slate-700">Itens (benefícios)</p>
      </div>
      <div v-for="(item, index) in local.items" :key="index" class="rounded-lg border border-slate-200 p-3">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wide text-slate-500">Item {{ index + 1 }}</p>
          <button class="text-xs font-semibold text-red-500" @click="removeItem(index)">Remover</button>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div class="relative">
            <label class="text-sm font-semibold text-slate-600">Ícone</label>
            <div class="mt-1 flex items-center gap-2">
              <input
                v-model="item.icon"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
                placeholder="Ex.: ✈️ ou cole um emoji"
                @focus="pendingIconIndex = index"
              />
            </div>
            <button class="mt-2 text-xs font-semibold text-slate-600 underline" @click.prevent="toggleItemPicker(index)">
              Escolher ícone
            </button>
            <div
              v-if="iconOpen[index]"
              class="absolute z-20 mt-2 w-full rounded-lg border border-slate-200 bg-white p-3 shadow-xl"
            >
              <div class="flex flex-wrap gap-2 text-xl max-h-40 overflow-auto">
                <button
                  v-for="icon in allIcons"
                  :key="icon"
                  class="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100"
                  @click.prevent="applyIcon(index, icon)"
                >
                  {{ icon }}
                </button>
              </div>
            </div>
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Título</label>
            <input v-model="item.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
          </div>
        </div>
        <div class="mt-2">
          <label class="text-sm font-semibold text-slate-600">Descrição</label>
          <textarea v-model="item.description" rows="3" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"></textarea>
        </div>
      </div>
      <div class="flex justify-end">
        <button
          class="text-sm font-semibold text-brand"
          @click="addItem"
          :disabled="local.items.length >= MAX_ITEMS"
        >
          + Adicionar item
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { ReasonsSection } from "../../types/page";

const props = defineProps<{ modelValue: ReasonsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ReasonsSection): void }>();
const headingDefaults = getSectionHeadingDefaults("reasons");

const local = reactive<ReasonsSection>({
  type: "reasons",
  enabled: true,
  layout: "grid",
  items: [],
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  ...props.modelValue
});
let syncing = false;
const syncFromProps = (value: ReasonsSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.items = Array.isArray(value.items) ? value.items.map(item => ({ ...item })) : [];
  iconOpen.value = local.items.map(() => false);
  nextTick(() => {
    syncing = false;
  });
};

const iconOptions = ["✈️", "💰", "🧭", "🏨", "🧳", "🎯", "🤝", "⭐", "🚐", "🌎"];
const libraryIcons = [
  "✈️",
  "🚐",
  "🚌",
  "🚢",
  "🚲",
  "🏝️",
  "🏔️",
  "🏨",
  "🛎️",
  "🧳",
  "💰",
  "💳",
  "🎯",
  "🤝",
  "⭐",
  "❤️",
  "🛟",
  "🗺️",
  "🧭",
  "📸",
  "🏆",
  "🚀",
  "🍽️",
  "🌅",
  "🧑‍✈️",
  "🧳",
  "🗼",
  "🏛️",
  "🏖️",
  "🏞️",
  "🌋",
  "⛱️",
  "🏕️",
  "🚁",
  "🚄",
  "⛴️",
  "🛥️",
  "🚗",
  "🚙",
  "🚐",
  "🚌",
  "🧨",
  "🎉",
  "🎟️",
  "🎁",
  "🪙",
  "🏅",
  "📌",
  "🧰",
  "🧠",
  "🫶",
  "🤗",
  "😎"
];
const allIcons = computed(() => Array.from(new Set([...iconOptions, ...libraryIcons])));
const pendingIconIndex = ref<number | null>(null);
const iconOpen = ref<boolean[]>([]);

const MAX_ITEMS = 8;

const addItem = () => {
  if (local.items.length >= MAX_ITEMS) return;
  local.items.push({ title: "Benefício", description: "Descreva o ponto forte", icon: "⭐" });
  iconOpen.value.push(false);
};

const removeItem = (index: number) => {
  local.items.splice(index, 1);
  iconOpen.value.splice(index, 1);
};

const toggleItemPicker = (index: number) => {
  iconOpen.value[index] = !iconOpen.value[index];
  pendingIconIndex.value = index;
};

const applyIcon = (index: number, icon: string) => {
  if (!local.items[index]) return;
  local.items[index].icon = icon;
  iconOpen.value[index] = false;
  pendingIconIndex.value = index;
};

// garantir tamanho inicial do estado de abertura
iconOpen.value = local.items.map(() => false);

watch(
  () => props.modelValue,
  value => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as ReasonsSection);
  },
  { deep: true }
);
</script>
