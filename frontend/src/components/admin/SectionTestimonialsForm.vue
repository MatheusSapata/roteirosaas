<template>
  <div class="space-y-3 rounded-xl border border-slate-200 p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">{{ viewCopy.header.title }}</h3>
    </div>

    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.sectionTitle }}</label>
        <input
          v-model="local.title"
          :placeholder="viewCopy.fields.sectionTitlePlaceholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
      </div>

      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.sectionSubtitle }}</label>
        <RichTextEditor v-model="local.subtitle" :placeholder="viewCopy.fields.sectionSubtitlePlaceholder" />
      </div>
    </div>

    <div class="space-y-3">
      <div
        v-for="(item, index) in local.items"
        :key="index"
        class="rounded-lg border border-slate-100 p-4 space-y-3 md:flex md:gap-4 md:space-y-0"
      >
        <div class="md:w-40">
          <label class="mb-1 block text-sm font-semibold text-slate-600">{{ viewCopy.items.photo }}</label>
          <ImageUploadField v-model="item.avatar" label="" hint="" />
        </div>

        <div class="flex-1 space-y-3">
          <div class="grid gap-3 md:grid-cols-[1fr,1fr]">
            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-600">{{ viewCopy.items.name }}</label>
              <input
                v-model="item.name"
                :placeholder="viewCopy.items.namePlaceholder"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-600">{{ viewCopy.items.role }}</label>
              <input
                v-model="item.role"
                :placeholder="viewCopy.items.rolePlaceholder"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>
          </div>

          <div>
            <label class="mb-1 block text-sm font-semibold text-slate-600">{{ viewCopy.items.text }}</label>
            <textarea
              v-model="item.text"
              :placeholder="viewCopy.items.textPlaceholder"
              class="w-full min-h-[110px] rounded-lg border border-slate-200 px-3 py-2 md:min-h-[180px]"
            ></textarea>
          </div>

          <div class="flex justify-end">
            <button
              type="button"
              class="text-sm text-red-500 hover:text-red-600"
              @click="removeItem(index)"
            >
              {{ viewCopy.items.removeButton }}
            </button>
          </div>
        </div>
      </div>

      <button type="button" class="text-sm font-semibold text-brand" @click="addItem">
        {{ viewCopy.items.addButton }}
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
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: TestimonialsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: TestimonialsSection): void }>();

const headingDefaults = getSectionHeadingDefaults("testimonials");
const t = createAdminLocalizer();

const viewCopy = {
  header: {
    title: t({ pt: "Depoimentos", es: "Testimonios" })
  },
  fields: {
    sectionTitle: t({ pt: "Título da seção", es: "Título de la sección" }),
    sectionTitlePlaceholder: t({ pt: "Quem já viajou com a gente", es: "Quién ya viajó con nosotros" }),
    sectionSubtitle: t({ pt: "Subtítulo", es: "Subtítulo" }),
    sectionSubtitlePlaceholder: t({ pt: "Feedbacks reais de clientes", es: "Comentarios reales de clientes" })
  },
  items: {
    photo: t({ pt: "Foto", es: "Foto" }),
    name: t({ pt: "Nome", es: "Nombre" }),
    namePlaceholder: t({ pt: "Nome", es: "Nombre" }),
    role: t({ pt: "Etiqueta", es: "Etiqueta" }),
    rolePlaceholder: t({ pt: "(opcional)", es: "(opcional)" }),
    text: t({ pt: "Depoimento", es: "Testimonio" }),
    textPlaceholder: t({ pt: "Depoimento", es: "Testimonio" }),
    removeButton: t({ pt: "Remover", es: "Eliminar" }),
    addButton: t({ pt: "+ Adicionar depoimento", es: "+ Agregar testimonio" })
  }
};

const local = reactive<TestimonialsSection>({
  layout: "grid",
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title || "",
  subtitle: props.modelValue.subtitle || "",
  ...props.modelValue,
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
