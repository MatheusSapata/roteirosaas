<template>
  <div class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Banner em Card</h3>
    </div>

    <div class="space-y-3">
      <div>
        <label class="text-sm font-semibold text-slate-600">Título</label>
        <input
          v-model="local.title"
          placeholder="Headline principal"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
      </div>
      <div>
        <ImageUploadField
          v-model="local.backgroundImage"
          label="Imagem de fundo"
          hint="Use fotos em alta resolução. A imagem aparece desfocada com um gradiente por cima."
        />
      </div>
    </div>

    <div class="rounded-xl border border-slate-200 p-4">
      <p class="text-sm font-semibold text-slate-700">Cores e contraste</p>
      <div class="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">Cor do fundo da seção</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              v-model="local.backgroundColor"
              class="h-10 w-12 cursor-pointer rounded-lg border border-slate-200 bg-white"
            />
            <input
              v-model="local.backgroundColor"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <p class="text-xs text-slate-500">Define a cor atrás do card.</p>
        </div>
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">Base do gradiente</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              v-model="local.gradientColor"
              class="h-10 w-12 cursor-pointer rounded-lg border border-slate-200 bg-white"
            />
            <input
              v-model="local.gradientColor"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <p class="text-xs text-slate-500">Define o tom que vem da esquerda para a direita.</p>
        </div>
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">Cor do card</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              v-model="local.cardBackground"
              class="h-10 w-12 cursor-pointer rounded-lg border border-slate-200 bg-white"
            />
            <input
              v-model="local.cardBackground"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <p class="text-xs text-slate-500">Fica visível quando não há imagem.</p>
        </div>
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">Cor da borda</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              v-model="local.cardBorderColor"
              class="h-10 w-12 cursor-pointer rounded-lg border border-slate-200 bg-white"
            />
            <input
              v-model="local.cardBorderColor"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <p class="text-xs text-slate-500">Use transparência para um contorno sutil.</p>
        </div>
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">Cor do texto</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              v-model="local.textColor"
              class="h-10 w-12 cursor-pointer rounded-lg border border-slate-200 bg-white"
            />
            <input
              v-model="local.textColor"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <p class="text-xs text-slate-500">Afeta descrições/legendas do banner.</p>
        </div>
      </div>
    </div>

    <div class="rounded-xl border border-slate-200 p-4 space-y-3">
      <p class="text-sm font-semibold text-slate-700">Botão / CTA</p>
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
            placeholder="Quero saber mais"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <div v-if="local.ctaMode !== 'section'">
          <label class="text-sm font-semibold text-slate-600">Link</label>
          <input
            v-model="local.ctaLink"
            placeholder="https://wa.me/"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
      </div>
      <div class="space-y-1" :class="local.ctaMode === 'section' ? 'md:max-w-xs' : ''">
        <label class="text-sm font-semibold text-slate-600">Cor do botão</label>
        <div class="flex items-center gap-2">
          <input
            type="color"
            v-model="local.ctaColor"
            class="h-10 w-12 cursor-pointer rounded-lg border border-slate-200 bg-white"
          />
          <input
            v-model="local.ctaColor"
            class="w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <p class="text-xs text-slate-500">Se preferir, use a cor global definida no topo do editor.</p>
      </div>
    </div>

    <p class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      O banner card ocupa toda a largura disponível no preview e mantém o mesmo layout no desktop e no mobile.
    </p>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import type { BannerCardSection } from "../../types/page";

const props = defineProps<{ modelValue: BannerCardSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BannerCardSection): void }>();

const ensureColor = (value: string | undefined, fallback: string) => value && value.trim() ? value : fallback;

const local = reactive<BannerCardSection>({
  ...props.modelValue,
  enabled: props.modelValue.enabled ?? true,
  backgroundColor: ensureColor(props.modelValue.backgroundColor, "#020617"),
  title: props.modelValue.title || "Conte com especialistas para transformar o seu roteiro.",
  subtitle: props.modelValue.subtitle || "",
  ctaLabel: props.modelValue.ctaLabel || "Quero saber mais",
  ctaLink: props.modelValue.ctaLink || "https://wa.me/",
  ctaColor: ensureColor(props.modelValue.ctaColor, "#41ce5f"),
  gradientColor: ensureColor(props.modelValue.gradientColor, "#05060f"),
  cardBackground: ensureColor(props.modelValue.cardBackground, "rgba(5,6,15,0.88)"),
  cardBorderColor: ensureColor(props.modelValue.cardBorderColor, "rgba(255,255,255,0.25)"),
  textColor: ensureColor(props.modelValue.textColor, "rgba(255,255,255,0.85)"),
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null
});

let syncing = false;
const syncFromProps = (value: BannerCardSection) => {
  syncing = true;
  Object.assign(local, value);
  local.enabled = value.enabled ?? true;
  local.backgroundColor = ensureColor(value.backgroundColor, local.backgroundColor || "#020617");
  local.title = value.title || "Conte com especialistas para transformar o seu roteiro.";
  local.subtitle = value.subtitle || "";
  local.ctaLabel = value.ctaLabel || "Quero saber mais";
  local.ctaLink = value.ctaLink || "https://wa.me/";
  local.ctaColor = ensureColor(value.ctaColor, local.ctaColor || "#41ce5f");
  local.gradientColor = ensureColor(value.gradientColor, local.gradientColor || "#05060f");
  local.cardBackground = ensureColor(value.cardBackground, local.cardBackground || "rgba(5,6,15,0.88)");
  local.cardBorderColor = ensureColor(value.cardBorderColor, local.cardBorderColor || "rgba(255,255,255,0.25)");
  local.textColor = ensureColor(value.textColor, local.textColor || "rgba(255,255,255,0.85)");
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
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
    emit("update:modelValue", value as BannerCardSection);
  },
  { deep: true }
);
</script>
