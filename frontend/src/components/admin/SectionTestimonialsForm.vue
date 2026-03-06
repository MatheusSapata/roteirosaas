<template>
  <div class="space-y-3 rounded-xl border border-slate-200 p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Depoimentos</h3>
    </div>

    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Título da seção</label>
        <input
          v-model="local.title"
          placeholder="Quem já viajou com a gente"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
      </div>

      <div>
        <label class="text-sm font-semibold text-slate-600">Subtítulo</label>
        <RichTextEditor v-model="local.subtitle" placeholder="Feedbacks reais de clientes" />
      </div>
    </div>

    <div class="space-y-3">
      <div
  v-for="(item, index) in local.items"
  :key="index"
  class="rounded-lg border border-slate-100 p-3 space-y-3"
>
  <!-- Linha superior -->
  <div class="grid gap-3 md:grid-cols-[180px_1fr_1fr] items-end">
    
    <!-- FOTO -->
    <div>
      <label class="text-sm font-semibold text-slate-600 block mb-1">
        Foto
      </label>

      <ImageUploadField
        v-model="item.avatar"
        label=""
        hint=""
      />
    </div>

    <!-- NOME -->
    <div>
      <label class="text-sm font-semibold text-slate-600 block mb-1">
        Nome
      </label>

      <input
        v-model="item.name"
        placeholder="Nome"
        class="w-full rounded-lg border border-slate-200 px-3 py-2"
      />
    </div>

    <!-- CARGO -->
    <div>
      <label class="text-sm font-semibold text-slate-600 block mb-1">
        Cargo / Empresa
      </label>

      <input
        v-model="item.role"
        placeholder="Cargo / Empresa (opcional)"
        class="w-full rounded-lg border border-slate-200 px-3 py-2"
      />
    </div>

  </div>

  <!-- DEPOIMENTO -->
  <div>
    <label class="text-sm font-semibold text-slate-600 block mb-1">
      Depoimento
    </label>

    <textarea
      v-model="item.text"
      placeholder="Depoimento"
      class="w-full min-h-[110px] rounded-lg border border-slate-200 px-3 py-2"
    ></textarea>
  </div>

  <!-- AÇÕES -->
  <div class="flex justify-end">
    <button
      type="button"
      class="text-sm text-red-500 hover:text-red-600"
      @click="removeItem(index)"
    >
      Remover
    </button>
  </div>

</div>

      <button type="button" class="text-sm font-semibold text-brand" @click="addItem">
        + Adicionar depoimento
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { TestimonialsSection } from "../../types/page";

const props = defineProps<{ modelValue: TestimonialsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: TestimonialsSection): void }>();

const headingDefaults = getSectionHeadingDefaults("testimonials");

const local = reactive<TestimonialsSection>({
  layout: "grid",
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title || "",
  subtitle: props.modelValue.subtitle || "",
  ...props.modelValue,
  // sempre clonar itens pra não mutar props direto
  items: Array.isArray(props.modelValue.items) ? props.modelValue.items.map(i => ({ ...i })) : []
});

let syncing = false;

const syncFromProps = (value: TestimonialsSection) => {
  syncing = true;

  Object.assign(local, value);

  local.layout = value.layout || "grid";
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle ?? headingDefaults.style;
  local.title = value.title || "";
  local.subtitle = value.subtitle || "";
  local.items = Array.isArray(value.items) ? value.items.map(i => ({ ...i })) : [];

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

const addItem = () => {
  local.items.push({ name: "", role: "", text: "", avatar: "" } as any);
};

const removeItem = (index: number) => {
  local.items.splice(index, 1);
};

watch(
  () => ({ ...local, items: local.items.map(i => ({ ...i })) }),
  value => {
    if (syncing) return;

    // remove lixo de versões antigas (cta/background/cardColor etc) caso existam no objeto
    const cleaned = { ...(value as any) };
    delete cleaned.backgroundColor;
    delete cleaned.cardColor;
    delete cleaned.ctaMode;
    delete cleaned.ctaSectionId;
    delete cleaned.ctaLink;
    delete cleaned.ctaLabel;

    emit("update:modelValue", cleaned as TestimonialsSection);
  },
  { deep: true }
);
</script>