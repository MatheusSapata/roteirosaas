<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">CTA / Contato</h3>
    </div>
    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
    <div>
      <label class="text-sm font-semibold text-slate-600">Texto</label>
      <input v-model="local.label" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
    </div>
    <div>
      <label class="text-sm font-semibold text-slate-600">Descrição (opcional)</label>
      <RichTextEditor v-model="local.description" placeholder="Use este espaço para reforçar sua oferta" />
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Texto do botão</label>
        <input
          v-model="local.ctaText"
          placeholder="Ex.: Falar com especialista"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Link</label>
        <input v-model="local.link" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>
    <div class="rounded-lg border border-slate-200 p-3">
      <label class="flex items-center gap-2 text-sm font-semibold text-slate-600">
        <input type="checkbox" v-model="local.highlight" class="h-4 w-4" />
        Destacar card
      </label>
      <div v-if="local.highlight" class="mt-3">
        <label class="text-xs font-semibold text-slate-500">Cor do destaque</label>
        <div class="mt-1 flex items-center gap-2">
          <input type="color" v-model="local.highlightColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
          <input v-model="local.highlightColor" placeholder="#0f172a" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>
    </div>
    <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      A cor do botão segue a opção global "Cor de botões e destaques" configurada no topo do editor.
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { CtaSection } from "../../types/page";

const props = defineProps<{ modelValue: CtaSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: CtaSection): void }>();
const headingDefaults = getSectionHeadingDefaults("cta");

const local = reactive<CtaSection>({
  ...props.modelValue,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  link: props.modelValue.link || "https://wa.me/",
  ctaMode: "link",
  ctaSectionId: null,
  ctaText: props.modelValue.ctaText || "Falar com especialista",
  highlight: props.modelValue.highlight ?? false,
  highlightColor: props.modelValue.highlightColor || props.modelValue.ctaColor || "#0f172a"
});

let syncing = false;
const syncFromProps = (value: CtaSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.ctaMode = "link";
  local.ctaSectionId = null;
  local.link = value.link || "https://wa.me/";
  local.highlight = value.highlight ?? false;
  local.highlightColor = value.highlightColor || local.highlightColor || "#0f172a";
  local.ctaText = value.ctaText || "Falar com especialista";
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

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as CtaSection);
  },
  { deep: true }
);

watch(
  () => local.highlight,
  value => {
    if (value && !local.highlightColor) {
      local.highlightColor = "#0f172a";
    }
  }
);
</script>
