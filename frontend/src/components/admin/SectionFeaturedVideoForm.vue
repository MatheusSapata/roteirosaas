<template>
  <div class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">{{ viewCopy.header.title }}</h3>
    </div>

    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />

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
      <RichTextEditor v-model="local.subtitle" :placeholder="viewCopy.fields.subtitlePlaceholder" />
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.videoLabel }}</label>
      <input
        v-model="local.videoUrl"
        :placeholder="viewCopy.fields.videoPlaceholder"
        class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
      />
      <p class="mt-1 text-xs text-slate-500">{{ viewCopy.fields.videoHelper }}</p>
    </div>

    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.ctaEnabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.toggle }}</label>
    </div>

    <div v-if="local.ctaEnabled" class="space-y-3 rounded-xl border border-slate-200 p-4">
      <div class="flex items-center justify-between">
        <p class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.sectionTitle }}</p>
        <span class="text-xs text-slate-500">{{ viewCopy.cta.sectionHint }}</span>
      </div>

      <CtaActionPicker
        v-model:mode="local.ctaMode"
        v-model:sectionId="local.ctaSectionId"
        :current-anchor="local.anchorId"
      />

      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.textLabel }}</label>
          <input
            v-model="local.ctaLabel"
            :placeholder="viewCopy.cta.textPlaceholder"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <div v-if="local.ctaMode !== 'section'">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.linkLabel }}</label>
          <input
            v-model="local.ctaLink"
            :placeholder="viewCopy.cta.linkPlaceholder"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
      </div>

      <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
        {{ viewCopy.cta.colorInfo }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { FeaturedVideoSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: FeaturedVideoSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FeaturedVideoSection): void }>();
const headingDefaults = getSectionHeadingDefaults("featured_video");
const t = createAdminLocalizer();

const viewCopy = {
  header: {
    title: t({ pt: "Vídeo em destaque", es: "Video destacado" })
  },
  fields: {
    title: t({ pt: "Título principal", es: "Título principal" }),
    titlePlaceholder: t({ pt: "Apresente o vídeo com um título forte", es: "Presenta el video con un título fuerte" }),
    subtitle: t({ pt: "Subtítulo", es: "Subtítulo" }),
    subtitlePlaceholder: t({ pt: "Explique o contexto do vídeo em poucas frases", es: "Explica el contexto del video en pocas frases" }),
    videoLabel: t({ pt: "Vídeo (YouTube ou iframe)", es: "Video (YouTube o iframe)" }),
    videoPlaceholder: "https://www.youtube.com/watch?v=...",
    videoHelper: t({ pt: "Aceita links completos ou o código iframe do YouTube/Vimeo.", es: "Acepta enlaces completos o el código iframe de YouTube/Vimeo." })
  },
  cta: {
    toggle: t({ pt: "Mostrar botão de CTA", es: "Mostrar botón de CTA" }),
    sectionTitle: t({ pt: "Botão principal", es: "Botón principal" }),
    sectionHint: t({ pt: "Defina o destino do CTA", es: "Define el destino del CTA" }),
    textLabel: t({ pt: "Texto do botão", es: "Texto del botón" }),
    textPlaceholder: t({ pt: "Assistir agora", es: "Ver ahora" }),
    linkLabel: t({ pt: "Link do botão", es: "Link del botón" }),
    linkPlaceholder: t({ pt: "https://wa.me/", es: "https://wa.me/" }),
    colorInfo: t({
      pt: 'A cor do botão segue a configuração global "Cor de botões e destaques".',
      es: 'El color del botón sigue la configuración global "Color de botones y destacados".'
    })
  }
};

const local = reactive<FeaturedVideoSection>({
  type: "featured_video",
  enabled: true,
  ...props.modelValue,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title || viewCopy.fields.titlePlaceholder,
  subtitle: props.modelValue.subtitle || "",
  videoUrl: props.modelValue.videoUrl || "",
  ctaEnabled: props.modelValue.ctaEnabled !== false,
  ctaLabel: props.modelValue.ctaLabel || viewCopy.cta.textPlaceholder,
  ctaLink: props.modelValue.ctaLink || viewCopy.cta.linkPlaceholder,
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId ?? null
});

let syncing = false;
const syncFromProps = (value: FeaturedVideoSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.title = value.title || viewCopy.fields.titlePlaceholder;
  local.subtitle = value.subtitle || "";
  local.videoUrl = value.videoUrl || "";
  local.ctaEnabled = value.ctaEnabled !== false;
  local.ctaLabel = value.ctaLabel || viewCopy.cta.textPlaceholder;
  local.ctaLink = value.ctaLink || viewCopy.cta.linkPlaceholder;
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId ?? null;
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
    emit("update:modelValue", value as FeaturedVideoSection);
  },
  { deep: true }
);
</script>
