<template>
  <div class="space-y-4">
    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.sectionTitle }}</label>
        <input v-model="local.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.sectionSubtitle }}</label>
        <input v-model="local.subtitle" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>

    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <p class="text-sm font-semibold text-slate-700">{{ viewCopy.items.heading }}</p>
      </div>
      <div v-for="(item, index) in local.items" :key="index" class="rounded-lg border border-slate-200 p-3">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wide text-slate-500">{{ viewCopy.items.itemLabel }} {{ index + 1 }}</p>
          <button class="text-xs font-semibold text-red-500" @click="removeItem(index)">{{ viewCopy.items.remove }}</button>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div class="relative">
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.items.iconLabel }}</label>
            <div class="mt-1 flex items-center gap-2">
              <input
                v-model="item.icon"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
                :placeholder="viewCopy.items.iconPlaceholder"
                @focus="pendingIconIndex = index"
              />
            </div>
            <button class="mt-2 text-xs font-semibold text-slate-600 underline" @click.prevent="toggleItemPicker(index)">
              {{ viewCopy.items.chooseIcon }}
            </button>
            <div
              v-if="iconOpen[index]"
              class="absolute z-20 mt-2 w-full rounded-lg border border-slate-200 bg-white p-3 shadow-xl"
            >
              <div class="flex max-h-40 flex-wrap gap-2 overflow-auto text-xl">
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
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.items.titleLabel }}</label>
            <input v-model="item.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
          </div>
        </div>
        <div class="mt-2">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.items.descriptionLabel }}</label>
          <RichTextEditor v-model="item.description" :placeholder="viewCopy.items.descriptionPlaceholder" />
        </div>
      </div>
      <div class="flex justify-end">
        <button
          class="text-sm font-semibold text-brand"
          @click="addItem"
          :disabled="local.items.length >= MAX_ITEMS"
        >
          {{ viewCopy.items.addButton }}
        </button>
      </div>
    </div>

    <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      {{ viewCopy.notes.animations }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { ReasonsSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: ReasonsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ReasonsSection): void }>();
const headingDefaults = getSectionHeadingDefaults("reasons");
const t = createAdminLocalizer();

const viewCopy = {
  fields: {
    sectionTitle: t({ pt: "Título", es: "Título" }),
    sectionSubtitle: t({ pt: "Subtítulo", es: "Subtítulo" })
  },
  items: {
    heading: t({ pt: "Itens (benefícios)", es: "Ítems (beneficios)" }),
    itemLabel: t({ pt: "Item", es: "Ítem" }),
    remove: t({ pt: "Remover", es: "Eliminar" }),
    iconLabel: t({ pt: "Ícone", es: "Ícono" }),
    iconPlaceholder: t({ pt: "Ex.: ⭐ ou cole um emoji", es: "Ej.: ⭐ o pega un emoji" }),
    chooseIcon: t({ pt: "Escolher ícone", es: "Elegir ícono" }),
    titleLabel: t({ pt: "Título", es: "Título" }),
    descriptionLabel: t({ pt: "Descrição", es: "Descripción" }),
    descriptionPlaceholder: t({ pt: "Detalhe o benefício", es: "Describe el beneficio" }),
    addButton: t({ pt: "+ Adicionar item", es: "+ Agregar ítem" }),
    defaultTitle: t({ pt: "Benefício", es: "Beneficio" }),
    defaultDescription: t({ pt: "Descreva o ponto forte", es: "Describe el punto fuerte" })
  },
  notes: {
    animations: t({
      pt: "Animações em fade-in dos cards são aplicadas automaticamente nesta seção.",
      es: "Las animaciones en fade-in de los cards se aplican automáticamente en esta sección."
    })
  }
};

const DEFAULT_ANIMATION_DURATION = 1000;
const DEFAULT_ANIMATION_STAGGER = 300;
const clampDuration = (value?: number) => (typeof value === "number" && !Number.isNaN(value) ? value : DEFAULT_ANIMATION_DURATION);
const clampStagger = (value?: number) => (typeof value === "number" && !Number.isNaN(value) ? value : DEFAULT_ANIMATION_STAGGER);

const local = reactive<ReasonsSection>({
  type: "reasons",
  enabled: true,
  layout: "grid",
  items: [],
  ...props.modelValue,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  enableAnimation: true,
  animationDuration: clampDuration(props.modelValue.animationDuration),
  cardAnimationStagger: clampStagger(props.modelValue.cardAnimationStagger)
});
let syncing = false;
const syncFromProps = (value: ReasonsSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.items = Array.isArray(value.items) ? value.items.map(item => ({ ...item })) : [];
  local.enableAnimation = true;
  local.animationDuration = clampDuration(value.animationDuration);
  local.cardAnimationStagger = clampStagger(value.cardAnimationStagger);
  iconOpen.value = local.items.map(() => false);
  nextTick(() => {
    syncing = false;
  });
};

const iconOptions = ["✨", "🚀", "🌍", "❤️", "⭐", "⚡", "🏆", "📍", "🧭", "✅"];
const libraryIcons = ["💡", "🎯", "🌟", "🛡️", "🎒", "☀️", "📞", "📸", "💬", "🧳", "🧡", "🌐", "📌", "🧠", "⛰️", "🏝️", "📍", "🏖️", "💎", "🛫"];
const allIcons = computed(() => Array.from(new Set([...iconOptions, ...libraryIcons])));
const pendingIconIndex = ref<number | null>(null);
const iconOpen = ref<boolean[]>(local.items.map(() => false));

const MAX_ITEMS = 8;

const addItem = () => {
  if (local.items.length >= MAX_ITEMS) return;
  local.items.push({ title: viewCopy.items.defaultTitle, description: viewCopy.items.defaultDescription, icon: "✨" });
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
