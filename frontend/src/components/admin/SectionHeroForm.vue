<template>
  <div class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Hero</h3>
    </div>

    <div class="space-y-4">
      <div class="rounded-lg border border-slate-200 p-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div class="space-y-4">
            <div>
              <label class="text-sm font-semibold text-slate-600">Titulo</label>
              <input v-model="local.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            </div>
            <div>
              <label class="text-sm font-semibold text-slate-600">Subtitulo</label>
              <RichTextEditor v-model="local.subtitle" placeholder="Conte um pouco sobre o roteiro..." />
            </div>
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Destaques</label>
            <div class="space-y-2">
              <div
                v-for="(chip, index) in local.chips"
                :key="index"
                class="flex items-center gap-2"
              >
                <input
                  v-model="local.chips[index]"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  placeholder="Ex.: Wi-Fi Starlink"
                />
                <button
                  type="button"
                  class="rounded-lg border border-slate-200 px-3 py-1 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                  @click="removeChip(index)"
                >
                  Remover
                </button>
              </div>
              <button
                type="button"
                class="text-sm font-semibold text-brand"
                @click="addChip"
              >
                + Adicionar destaque
              </button>
            </div>
            <p class="mt-1 text-xs text-slate-500">Cada destaque aparece em formato de selo no hero.</p>
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
                label="Logo da agencia"
                hint="Envie a marca que aparecera sobre o fundo."
                :enable-crop="true"
                editor-title="Ajuste da logo"
              />
              <div class="flex items-center gap-2">
                <label class="text-sm font-semibold text-slate-600">Tamanho da logo</label>
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
              <p class="text-xs text-slate-500">Use os botoes ou digite o valor em pixels (min. 48, max. 160).</p>
            </div>
          </div>
          <div class="space-y-4">
            <ImageUploadField
              v-model="local.backgroundImage"
              label="Imagem de fundo"
              hint="Formatos JPG/PNG. Essa imagem aparece no fundo da hero."
            />
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-semibold text-slate-600">Cor/hex do gradiente</label>
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
            <p class="mt-1 text-xs text-slate-500">Use o seletor ou digite um hex (ex.: #0a4ddf). Gradiente usa essa cor como base.</p>
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Video (YouTube)</label>
            <input v-model="local.videoUrl" placeholder="Link do YouTube ou iframe com src" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
            <p class="mt-1 text-xs text-slate-500">Aceita link (watch/short/iframe). No layout imersivo, o video aparece ao lado do texto.</p>
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
            <label class="text-sm font-semibold text-slate-600">Texto do CTA</label>
            <input v-model="local.ctaLabel" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
          </div>
          <div v-if="local.ctaMode !== 'section'">
            <label class="text-sm font-semibold text-slate-600">Link do CTA</label>
            <input v-model="local.ctaLink" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
          </div>
        </div>
        <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
          A cor do botao segue a opcao global "Cor de botoes e destaques" configurada no topo do editor.
        </div>
      </div>

      <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
        Animacoes de fade-in e o brilho do botao estao sempre ativos nesta secao.
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

const props = defineProps<{ modelValue: HeroSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: HeroSection): void }>();

const HERO_LAYOUT: HeroSection["layout"] = "immersive";
const HERO_ANIMATION_DURATION = 1000;

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
