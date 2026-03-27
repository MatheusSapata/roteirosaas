<template>
  <div class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Video em destaque</h3>
    </div>

    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />

    <div>
      <label class="text-sm font-semibold text-slate-600">Titulo principal</label>
      <input
        v-model="local.title"
        placeholder="Apresente o video com um titulo forte"
        class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
      />
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">Subtitulo</label>
      <RichTextEditor v-model="local.subtitle" placeholder="Explique o contexto do video em poucas frases" />
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">Video (YouTube ou iframe)</label>
      <input
        v-model="local.videoUrl"
        placeholder="https://www.youtube.com/watch?v=..."
        class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
      />
      <p class="mt-1 text-xs text-slate-500">Aceita links completos ou o código iframe do YouTube/Vimeo.</p>
    </div>

    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.ctaEnabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Mostrar botao de CTA</label>
    </div>

    <div v-if="local.ctaEnabled" class="space-y-3 rounded-xl border border-slate-200 p-4">
      <div class="flex items-center justify-between">
        <p class="text-sm font-semibold text-slate-600">Botão principal</p>
        <span class="text-xs text-slate-500">Defina o destino do CTA</span>
      </div>

      <CtaActionPicker
        v-model:mode="local.ctaMode"
        v-model:sectionId="local.ctaSectionId"
        :current-anchor="local.anchorId"
      />

      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-sm font-semibold text-slate-600">Texto do botão</label>
          <input
            v-model="local.ctaLabel"
            placeholder="Assistir agora"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <div v-if="local.ctaMode !== 'section'">
          <label class="text-sm font-semibold text-slate-600">Link do botão</label>
          <input
            v-model="local.ctaLink"
            placeholder="https://wa.me/"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
      </div>

      <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
        A cor do botão segue a configuração global "Cor de botões e destaques".
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

const props = defineProps<{ modelValue: FeaturedVideoSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FeaturedVideoSection): void }>();
const headingDefaults = getSectionHeadingDefaults("featured_video");

const local = reactive<FeaturedVideoSection>({
  type: "featured_video",
  enabled: true,
  ...props.modelValue,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title || "",
  subtitle: props.modelValue.subtitle || "",
  videoUrl: props.modelValue.videoUrl || "",
  ctaEnabled: props.modelValue.ctaEnabled !== false,
  ctaLabel: props.modelValue.ctaLabel || "Assistir agora",
  ctaLink: props.modelValue.ctaLink || "https://wa.me/",
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId ?? null
});

let syncing = false;
const syncFromProps = (value: FeaturedVideoSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.title = value.title || "";
  local.subtitle = value.subtitle || "";
  local.videoUrl = value.videoUrl || "";
  local.ctaEnabled = value.ctaEnabled !== false;
  local.ctaLabel = value.ctaLabel || "Assistir agora";
  local.ctaLink = value.ctaLink || "https://wa.me/";
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

