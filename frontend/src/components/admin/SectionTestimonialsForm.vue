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
        class="rounded-lg border border-slate-100 p-4 space-y-3 md:flex md:gap-4 md:space-y-0"
      >
        <div class="md:w-40">
          <label class="mb-1 block text-sm font-semibold text-slate-600">Foto</label>
          <ImageUploadField v-model="item.avatar" label="" hint="" />
        </div>

        <div class="flex-1 space-y-3">
          <div class="grid gap-3 md:grid-cols-[1fr,1fr]">
            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-600">Nome</label>
              <input
                v-model="item.name"
                placeholder="Nome"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-600">Etiqueta</label>
              <input
                v-model="item.role"
                placeholder="(opcional)"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>
          </div>

          <div>
            <label class="mb-1 block text-sm font-semibold text-slate-600">Depoimento</label>
            <textarea
              v-model="item.text"
              placeholder="Depoimento"
              class="w-full min-h-[110px] rounded-lg border border-slate-200 px-3 py-2 md:min-h-[180px]"
            ></textarea>
          </div>

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
import defaultAvatarImage from "../../assets/avatar.jpeg";

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
  items: Array.isArray(props.modelValue.items)
    ? props.modelValue.items.map(i => ({ ...i, avatar: i.avatar || defaultAvatarImage }))
    : []
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
  local.items = Array.isArray(value.items)
    ? value.items.map(i => ({ ...i, avatar: i.avatar || defaultAvatarImage }))
    : [];

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
  local.items.push({ name: "", role: "", text: "", avatar: defaultAvatarImage } as any);
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
