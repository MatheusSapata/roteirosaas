<template>
  <div class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">{{ viewCopy.header.title }}</h3>
    </div>

    <div class="space-y-4">
      <div class="rounded-lg border border-slate-200 p-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div class="space-y-4">
            <div>
              <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.titleLabel }}</label>
              <input v-model="local.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-sm font-semibold text-slate-600">{{ viewCopy.fields.subtitleLabel }}</label>
              <RichTextEditor v-model="local.subtitle" :placeholder="viewCopy.fields.subtitlePlaceholder" />
            </div>
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.chips.label }}</label>
            <div class="space-y-2">
              <div
                v-for="(chip, index) in local.chips"
                :key="index"
                class="flex items-center gap-2"
              >
                <input
                  v-model="local.chips[index]"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  :placeholder="viewCopy.chips.placeholder"
                />
                <button
                  type="button"
                  class="rounded-lg border border-slate-200 px-3 py-1 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                  @click="removeChip(index)"
                >
                  {{ viewCopy.chips.remove }}
                </button>
              </div>
              <button
                type="button"
                class="text-sm font-semibold text-brand"
                @click="addChip"
              >
                {{ viewCopy.chips.add }}
              </button>
            </div>
            <p class="mt-1 text-xs text-slate-500">{{ viewCopy.chips.helper }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 p-4 space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div class="space-y-4">
            <div class="space-y-2">
              <ImageUploadField
                v-model="local.logoUrl"
                v-model:roundedValue="local.logoBorderRadius"
                :rounded-max="logoRadiusMax"
                :label="viewCopy.logoField.label"
                :hint="viewCopy.logoField.hint"
                :enable-crop="true"
                :editor-title="viewCopy.logoField.editorTitle"
              />
              <div class="flex items-center gap-2">
                <label class="text-sm font-semibold text-slate-600">{{ viewCopy.logoSize.label }}</label>
                <input
                  v-model.number="local.logoSize"
                  type="number"
                  min="48"
                  max="160"
                  step="4"
                  class="w-24 rounded-lg border border-slate-200 px-2 py-1 text-sm"
                />
                <div class="flex gap-1">
                  <button
                    type="button"
                    class="rounded-full border border-slate-200 px-3 py-1 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                    @click="updateLogoSize(-4)"
                  >
                    &minus;
                  </button>
                  <button
                    type="button"
                    class="rounded-full border border-slate-200 px-3 py-1 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                    @click="updateLogoSize(4)"
                  >
                    +
                  </button>
                </div>
              </div>
              <p class="text-xs text-slate-500">{{ viewCopy.logoSize.helper }}</p>
            </div>
          </div>
          <div class="space-y-4">
            <ImageUploadField
              v-model="local.backgroundImage"
              :label="viewCopy.backgroundField.label"
              :hint="viewCopy.backgroundField.hint"
            />
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.gradient.label }}</label>
            <div class="mt-1 flex items-center gap-3">
              <input
                type="color"
                class="h-10 w-14 rounded-lg border border-slate-200 bg-white"
                :value="colorOnly(local.gradientColor)"
                @input="onColorPick"
              />
              <input
                v-model="local.gradientColor"
                placeholder="#41ce5f"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>
            <p class="mt-1 text-xs text-slate-500">{{ viewCopy.gradient.helper }}</p>
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.video.label }}</label>
            <input v-model="local.videoUrl" :placeholder="viewCopy.video.placeholder" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            <p class="mt-1 text-xs text-slate-500">{{ viewCopy.video.helper }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 p-4 space-y-4">
        <CtaActionPicker
          v-model:mode="local.ctaMode"
          v-model:sectionId="local.ctaSectionId"
          :current-anchor="local.anchorId"
        />
        <div class="grid gap-2 md:grid-cols-2">
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
          {{ viewCopy.cta.colorHelper }}
        </div>
      </div>

      <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
        {{ viewCopy.notes.animations }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import type { HeroSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: HeroSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: HeroSection): void }>();

const HERO_LAYOUT: HeroSection["layout"] = "immersive";
const HERO_ANIMATION_DURATION = 1000;
const t = createAdminLocalizer();

const viewCopy = {
  header: {
    title: t({ pt: "Hero", es: "Hero" })
  },
  fields: {
    titleLabel: t({ pt: "Título", es: "Título" }),
    subtitleLabel: t({ pt: "Subtítulo", es: "Subtítulo" }),
    subtitlePlaceholder: t({ pt: "Conte um pouco sobre o roteiro...", es: "Cuenta un poco sobre el itinerario..." })
  },
  chips: {
    label: t({ pt: "Destaques", es: "Destacados" }),
    placeholder: t({ pt: "Ex.: Wi-Fi Starlink", es: "Ej.: Wi-Fi Starlink" }),
    remove: t({ pt: "Remover", es: "Eliminar" }),
    add: t({ pt: "+ Adicionar destaque", es: "+ Agregar destacado" }),
    helper: t({ pt: "Cada destaque aparece em formato de selo no hero.", es: "Cada destacado aparece en formato de etiqueta en el hero." })
  },
  logoField: {
    label: t({ pt: "Logo da agência", es: "Logo de la agencia" }),
    hint: t({ pt: "Envie a marca que aparecerá sobre o fundo.", es: "Sube la marca que aparecerá sobre el fondo." }),
    editorTitle: t({ pt: "Ajuste da logo", es: "Ajuste del logo" })
  },
  logoSize: {
    label: t({ pt: "Tamanho da logo", es: "Tamaño del logo" }),
    helper: t({ pt: "Use os botões ou digite o valor em pixels (min. 48, máx. 160).", es: "Usa los botones o ingresa el valor en píxeles (min. 48, máx. 160)." })
  },
  backgroundField: {
    label: t({ pt: "Imagem de fundo", es: "Imagen de fondo" }),
    hint: t({ pt: "Formatos JPG/PNG. Essa imagem aparece no fundo da hero.", es: "Formatos JPG/PNG. Esta imagen aparece en el fondo del hero." })
  },
  gradient: {
    label: t({ pt: "Cor/hex do gradiente", es: "Color/hex del degradado" }),
    helper: t({ pt: "Use o seletor ou digite um hex (ex.: #0a4ddf). O gradiente usa essa cor como base.", es: "Usa el selector o ingresa un hex (ej.: #0a4ddf). El degradado usa ese color como base." })
  },
  video: {
    label: t({ pt: "Vídeo (YouTube)", es: "Video (YouTube)" }),
    placeholder: t({ pt: "Link do YouTube ou iframe com src", es: "Link de YouTube o iframe con src" }),
    helper: t({ pt: "Aceita link (watch/short/iframe). No layout imersivo, o vídeo aparece ao lado do texto.", es: "Acepta link (watch/short/iframe). En el layout inmersivo, el video aparece al lado del texto." })
  },
  cta: {
    textLabel: t({ pt: "Texto do CTA", es: "Texto del CTA" }),
    linkLabel: t({ pt: "Link do CTA", es: "Link del CTA" }),
    colorHelper: t({
      pt: "A cor do botão segue a opção global “Cor de botões e destaques” configurada no topo do editor.",
      es: "El color del botón sigue la opción global “Color de botones y destacados” configurada en la parte superior del editor."
    })
  },
  notes: {
    animations: t({ pt: "Animações de fade-in e o brilho do botão estão sempre ativos nesta seção.", es: "Las animaciones de fade-in y el brillo del botón están siempre activos en esta sección." })
  }
};

const local = reactive<HeroSection>({
  ...props.modelValue,
  layout: HERO_LAYOUT,
  logoSize: props.modelValue.logoSize ?? 64,
  logoBorderRadius: props.modelValue.logoBorderRadius ?? 0,
  chips: props.modelValue.chips ? [...props.modelValue.chips] : [],
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null,
  enableAnimation: true,
  animationDuration: HERO_ANIMATION_DURATION,
  ctaShimmer: true
});
if (!local.chips || !local.chips.length) {
  local.chips = [""];
}
let syncing = false;
const syncFromProps = (value: HeroSection) => {
  syncing = true;
  Object.assign(local, value);
  local.logoSize = value.logoSize ?? 64;
  local.logoBorderRadius = value.logoBorderRadius ?? 0;
  local.chips = value.chips ? [...value.chips] : [];
  local.layout = HERO_LAYOUT;
  if (!local.chips.length) local.chips = [""];
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  local.enableAnimation = true;
  local.animationDuration = HERO_ANIMATION_DURATION;
  local.ctaShimmer = true;
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

const addChip = () => {
  if (!Array.isArray(local.chips)) local.chips = [];
  local.chips.push("");
};

const removeChip = (index: number) => {
  if (!Array.isArray(local.chips)) return;
  local.chips.splice(index, 1);
};

const colorOnly = (value?: string) => {
  if (!value) return "#41ce5f";
  const match = value.match(/#([0-9a-fA-F]{6})/);
  return match ? `#${match[1]}` : "#41ce5f";
};

const onColorPick = (event: Event) => {
  const target = event.target as HTMLInputElement;
  local.gradientColor = target.value;
};

const updateLogoSize = (delta: number) => {
  const current = local.logoSize || 64;
  const next = Math.min(160, Math.max(48, current + delta));
  local.logoSize = next;
};

const logoRadiusMax = computed(() => Math.round((local.logoSize || 64) / 2));
const ensureLogoRadiusBounds = () => {
  const current = local.logoBorderRadius ?? 0;
  const max = logoRadiusMax.value;
  if (current > max) {
    local.logoBorderRadius = max;
  } else if (current < 0) {
    local.logoBorderRadius = 0;
  }
};

watch(
  () => local.logoSize,
  () => ensureLogoRadiusBounds()
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as HeroSection);
  },
  { deep: true }
);
</script>
