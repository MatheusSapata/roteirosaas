<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center">
      <h3 class="text-lg font-semibold text-slate-900">{{ viewCopy.header.title }}</h3>
    </div>
    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.title }}</label>
        <input
          v-model="local.title"
          :placeholder="viewCopy.fields.titlePlaceholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.subtitle }}</label>
        <textarea
          v-model="local.subtitle"
          :placeholder="viewCopy.fields.subtitlePlaceholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        ></textarea>
      </div>
    </div>
    <div class="space-y-3">
      <div v-for="(item, index) in local.items" :key="index" class="rounded-lg border border-slate-100 p-3">
        <label class="text-sm font-semibold text-slate-600 mb-1 block">{{ viewCopy.items.question }}</label>
        <input
          v-model="item.question"
          :placeholder="viewCopy.items.questionPlaceholder"
          class="mb-3 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
        <label class="text-sm font-semibold text-slate-600 mb-1 block">{{ viewCopy.items.answer }}</label>
        <RichTextEditor v-model="item.answer" :placeholder="viewCopy.items.answerPlaceholder" />
        <button class="text-sm text-red-500" @click="removeItem(index)">{{ viewCopy.items.remove }}</button>
      </div>
      <button class="text-sm font-semibold text-brand" @click="addItem">{{ viewCopy.items.add }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { FaqSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: FaqSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FaqSection): void }>();
const headingDefaults = getSectionHeadingDefaults("faq");
const t = createAdminLocalizer();

const viewCopy = {
  header: {
    title: t({ pt: "FAQ", es: "FAQ" })
  },
  fields: {
    title: t({ pt: "Título", es: "Título" }),
    titlePlaceholder: t({ pt: "Perguntas frequentes", es: "Preguntas frecuentes" }),
    subtitle: t({ pt: "Subtítulo", es: "Subtítulo" }),
    subtitlePlaceholder: t({ pt: "As dúvidas mais comuns sobre o roteiro.", es: "Las dudas más comunes sobre el itinerario." })
  },
  items: {
    question: t({ pt: "Pergunta", es: "Pregunta" }),
    questionPlaceholder: t({ pt: "Pergunta", es: "Pregunta" }),
    answer: t({ pt: "Resposta", es: "Respuesta" }),
    answerPlaceholder: t({ pt: "Adicione uma resposta formatada", es: "Agrega una respuesta formateada" }),
    remove: t({ pt: "Remover", es: "Eliminar" }),
    add: t({ pt: "+ Adicionar pergunta", es: "+ Agregar pregunta" })
  }
};

const defaultTitle = viewCopy.fields.titlePlaceholder;
const defaultSubtitle = viewCopy.fields.subtitlePlaceholder;

const local = reactive<FaqSection>({
  ...props.modelValue,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title ?? defaultTitle,
  subtitle: props.modelValue.subtitle ?? defaultSubtitle,
  layout: "accordion",
  items: Array.isArray(props.modelValue.items) ? [...props.modelValue.items] : []
});
let syncing = false;
const syncFromProps = (value: FaqSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.title = value.title ?? defaultTitle;
  local.subtitle = value.subtitle ?? defaultSubtitle;
  local.layout = "accordion";
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

const addItem = () => local.items.push({ question: "", answer: "" });
const removeItem = (index: number) => local.items.splice(index, 1);

watch(
  () => ({ ...local, items: local.items.map(item => ({ ...item })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as FaqSection);
  },
  { deep: true }
);
</script>
