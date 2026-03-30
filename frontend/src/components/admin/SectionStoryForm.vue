<template>
  <div class="space-y-3">
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.imagePosition.label }}</label>
        <select v-model="local.imagePosition" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="right">{{ viewCopy.imagePosition.right }}</option>
          <option value="left">{{ viewCopy.imagePosition.left }}</option>
        </select>
      </div>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.titleLabel }}</label>
        <input v-model="local.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.subtitleLabel }}</label>
        <RichTextEditor v-model="local.subtitle" :placeholder="viewCopy.fields.subtitlePlaceholder" />
      </div>
    </div>

    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.ctaEnabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.toggleLabel }}</label>
    </div>
    <div v-if="local.ctaEnabled" class="space-y-3">
      <CtaActionPicker
        v-model:mode="local.ctaMode"
        v-model:sectionId="local.ctaSectionId"
        :current-anchor="local.anchorId"
      />
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.textLabel }}</label>
          <input v-model="local.ctaLabel" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div v-if="local.ctaMode !== 'section'">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.linkLabel }}</label>
          <input v-model="local.ctaLink" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>
      <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
        {{ viewCopy.cta.helper }}
      </div>
    </div>

    <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      {{ viewCopy.notes.animations }}
    </div>

    <MultiImageUploadField
      v-model="local.images"
      :label="viewCopy.gallery.label"
      :hint="viewCopy.gallery.hint"
    />
    <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      {{ viewCopy.gallery.layoutHint }}
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.videos.label }}</label>
        <button type="button" class="text-sm font-semibold text-brand" @click="addVideoField">
          {{ viewCopy.videos.addButton }}
        </button>
      </div>
      <p class="text-xs text-slate-500">{{ viewCopy.videos.helper }}</p>
      <div v-if="local.videoUrls?.length" class="space-y-2">
        <div v-for="(video, index) in local.videoUrls" :key="`video-${index}`" class="flex items-center gap-2">
          <input
            v-model="local.videoUrls[index]"
            :placeholder="viewCopy.videos.placeholder"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
          <button type="button" class="text-sm font-semibold text-rose-500" @click="removeVideoField(index)">
            {{ viewCopy.videos.removeButton }}
          </button>
        </div>
      </div>
      <div v-else class="rounded-lg border border-dashed border-slate-200 px-3 py-2 text-xs text-slate-500">
        {{ viewCopy.videos.emptyState }}
      </div>
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.styles.backgroundLabel }}</label>
      <input v-model="local.backgroundColor" placeholder="#e5eef9" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
    </div>
    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.borderEnabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.styles.borderLabel }}</label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import MultiImageUploadField from "./inputs/MultiImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { StorySection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: StorySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: StorySection): void }>();
const headingDefaults = getSectionHeadingDefaults("story");
const t = createAdminLocalizer();

const viewCopy = {
  imagePosition: {
    label: t({ pt: "Posicao da imagem", es: "Posicion de la imagen" }),
    right: t({ pt: "Direita", es: "Derecha" }),
    left: t({ pt: "Esquerda", es: "Izquierda" })
  },
  fields: {
    titleLabel: t({ pt: "Titulo", es: "Titulo" }),
    subtitleLabel: t({ pt: "Subtitulo", es: "Subtitulo" }),
    subtitlePlaceholder: t({ pt: "Conte a historia da agencia...", es: "Cuenta la historia de la agencia..." })
  },
  cta: {
    toggleLabel: t({ pt: "Inserir botao de CTA", es: "Insertar boton de CTA" }),
    textLabel: t({ pt: "Texto do CTA", es: "Texto del CTA" }),
    linkLabel: t({ pt: "Link do CTA", es: "Link del CTA" }),
    helper: t({
      pt: "A cor do botao segue a opcao global 'Cor de botoes e destaques' configurada no topo do editor.",
      es: "El color del boton sigue la opcion global 'Color de botones y destacados' configurada en la parte superior del editor."
    })
  },
  notes: {
    animations: t({
      pt: "Animacoes de fade-in e o brilho do botao de CTA sao aplicados automaticamente nesta secao.",
      es: "Las animaciones de fade-in y el brillo del boton CTA se aplican automaticamente en esta seccion."
    })
  },
  gallery: {
    label: t({ pt: "Imagens", es: "Imagenes" }),
    hint: t({
      pt: "A primeira imagem e destacada; nas thumbs, o clique alterna a principal.",
      es: "La primera imagen se destaca; en las miniaturas, el clic alterna la principal."
    }),
    layoutHint: t({
      pt: "Layout definido automaticamente: 1 imagem exibe destaque unico; 2 ou mais ativam galeria.",
      es: "Layout definido automaticamente: 1 imagen muestra destaque unico; 2 o mas activan galeria."
    })
  },
  videos: {
    label: t({ pt: "Videos do YouTube", es: "Videos de YouTube" }),
    addButton: t({ pt: "+ Adicionar video", es: "+ Agregar video" }),
    helper: t({
      pt: "Cole links do YouTube ou iframes; exibimos sempre antes das imagens.",
      es: "Pega enlaces de YouTube o iframes; los mostramos antes de las imagenes."
    }),
    placeholder: t({ pt: "https://www.youtube.com/watch?v=...", es: "https://www.youtube.com/watch?v=..." }),
    removeButton: t({ pt: "Remover", es: "Eliminar" }),
    emptyState: t({ pt: "Nenhum video adicionado ainda.", es: "Ningun video agregado todavia." })
  },
  styles: {
    backgroundLabel: t({ pt: "Cor de fundo", es: "Color de fondo" }),
    borderLabel: t({ pt: "Ativar borda destacada (texto em card)", es: "Activar borde destacado (texto en tarjeta)" })
  }
};

const normalizeVideoList = (section: StorySection) => {
  const list = Array.isArray(section.videoUrls) ? [...section.videoUrls] : [];
  if (!list.length && typeof section.videoUrl === "string" && section.videoUrl.trim().length > 0) {
    list.push(section.videoUrl);
  }
  return list;
};

const local = reactive<StorySection>({
  type: "story",
  layout: "single",
  enabled: true,
  images: [],
  videoUrls: normalizeVideoList(props.modelValue),
  ctaEnabled: true,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  ...props.modelValue,
  enableAnimation: true,
  ctaShimmer: true,
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null
});
const countValidImages = (images?: string[]) =>
  Array.isArray(images) ? images.filter(img => typeof img === "string" && img.trim().length > 0).length : 0;
const countValidVideos = (videos?: string[]) =>
  Array.isArray(videos) ? videos.filter(video => typeof video === "string" && video.trim().length > 0).length : 0;
const determineLayoutFromMedia = () => (countValidImages(local.images) + countValidVideos(local.videoUrls) > 1 ? "gallery" : "single");
const applyAutomaticLayout = () => {
  const desired = determineLayoutFromMedia();
  if (local.layout !== desired) {
    local.layout = desired;
  }
};

let syncing = false;
const syncFromProps = (value: StorySection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.images = Array.isArray(value.images) ? [...value.images] : [];
  local.videoUrls = normalizeVideoList(value);
  local.videoUrl = local.videoUrls[0] || "";
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  local.enableAnimation = true;
  local.ctaShimmer = true;
  applyAutomaticLayout();
  nextTick(() => {
    syncing = false;
  });
};

const addVideoField = () => {
  if (!Array.isArray(local.videoUrls)) {
    local.videoUrls = [];
  }
  local.videoUrls.push("");
};

const removeVideoField = (index: number) => {
  if (!Array.isArray(local.videoUrls)) return;
  local.videoUrls = local.videoUrls.filter((_, i) => i !== index);
  local.videoUrl = local.videoUrls[0] || "";
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
  () => local.videoUrls,
  () => {
    if (syncing) return;
    local.videoUrl = Array.isArray(local.videoUrls) && local.videoUrls.length ? local.videoUrls[0] : "";
    applyAutomaticLayout();
  },
  { deep: true }
);

watch(
  () => local.images,
  () => {
    if (syncing) return;
    applyAutomaticLayout();
  },
  { deep: true }
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as StorySection);
  },
  { deep: true }
);
</script>
