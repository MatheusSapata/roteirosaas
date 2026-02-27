<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Hero</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Título</label>
        <input v-model="local.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Subtítulo</label>
        <input v-model="local.subtitle" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <ImageUploadField
        v-model="local.backgroundImage"
        label="Imagem de fundo"
        hint="Formatos JPG/PNG. Essa imagem aparece ocupando todo o fundo do hero."
      />
      <div class="space-y-2">
        <ImageUploadField
          v-model="local.logoUrl"
          label="Logo da agência"
          hint="Envie a marca que aparecerá sobre o fundo."
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
        <p class="text-xs text-slate-500">Use os botões ou digite o valor em pixels (mín. 48, máx. 160).</p>
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Vídeo (YouTube)</label>
        <input v-model="local.videoUrl" placeholder="Link do YouTube ou iframe com src" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        <p class="mt-1 text-xs text-slate-500">Aceita link (watch/short/iframe). No layout imersivo, o vídeo aparece ao lado do texto.</p>
      </div>
      <CtaActionPicker
        class="md:col-span-2"
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
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Layout do Hero</label>
        <select v-model="local.layout" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="classic">Clássico (texto + CTA)</option>
          <option value="split">Split (texto + card de destaque)</option>
          <option value="card">Card central com overlay</option>
          <option value="immersive">Imersivo (background + gradiente + destaques)</option>
        </select>
      </div>
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
            placeholder="#0ea5e9"
            class="w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <p class="mt-1 text-xs text-slate-500">Use o seletor ou digite um hex (ex.: #0a4ddf). Gradiente usa essa cor como base.</p>
      </div>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor do botão CTA</label>
        <div class="mt-1 flex items-center gap-3">
          <input
            type="color"
            class="h-10 w-14 rounded-lg border border-slate-200 bg-white"
            :value="colorOnly(local.ctaColor)"
            @input="onCtaColorPick"
          />
          <input
            v-model="local.ctaColor"
            placeholder="#0ea5e9"
            class="w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
      </div>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
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
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor de fundo (demais layouts)</label>
        <select v-model="local.backgroundColor" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option v-for="option in colorOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.fullWidth" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Ocupar largura total</label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import type { HeroSection } from "../../types/page";

const props = defineProps<{ modelValue: HeroSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: HeroSection): void }>();

const local = reactive<HeroSection>({
  layout: "classic",
  logoSize: props.modelValue.logoSize ?? 64,
  ...props.modelValue,
  chips: props.modelValue.chips ? [...props.modelValue.chips] : [],
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null
});
if (!local.chips || !local.chips.length) {
  local.chips = [""];
}

let syncing = false;
const syncFromProps = (value: HeroSection) => {
  syncing = true;
  Object.assign(local, value);
  local.logoSize = value.logoSize ?? 64;
  local.chips = value.chips ? [...value.chips] : [];
  if (!local.chips.length) local.chips = [""];
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

const colorOptions = [
  { label: "Azul oceano", value: "linear-gradient(135deg,#0ea5e9,#1d4ed8)" },
  { label: "Roxo neon", value: "linear-gradient(135deg,#7c3aed,#4338ca)" },
  { label: "Laranja pôr do sol", value: "linear-gradient(135deg,#f97316,#ea580c)" },
  { label: "Verde floresta", value: "linear-gradient(135deg,#16a34a,#15803d)" },
  { label: "Rosa vibrante", value: "linear-gradient(135deg,#ec4899,#db2777)" },
  { label: "Turquesa", value: "linear-gradient(135deg,#14b8a6,#0ea5e9)" },
  { label: "Dourado", value: "linear-gradient(135deg,#f59e0b,#d97706)" },
  { label: "Cinza elegante", value: "linear-gradient(135deg,#475569,#1f2937)" },
  { label: "Marinho", value: "linear-gradient(135deg,#0f172a,#1e3a8a)" },
  { label: "Preto premium", value: "linear-gradient(135deg,#0b0f19,#111827)" }
];

const addChip = () => {
  if (!Array.isArray(local.chips)) local.chips = [];
  local.chips.push("");
};

const removeChip = (index: number) => {
  if (!Array.isArray(local.chips)) return;
  local.chips.splice(index, 1);
};

const colorOnly = (value?: string) => {
  if (!value) return "#0ea5e9";
  const match = value.match(/#([0-9a-fA-F]{6})/);
  return match ? `#${match[1]}` : "#0ea5e9";
};

const onColorPick = (event: Event) => {
  const target = event.target as HTMLInputElement;
  local.gradientColor = target.value;
};

const onCtaColorPick = (event: Event) => {
  const target = event.target as HTMLInputElement;
  local.ctaColor = target.value;
};

const updateLogoSize = (delta: number) => {
  const current = local.logoSize || 64;
  const next = Math.min(160, Math.max(48, current + delta));
  local.logoSize = next;
};

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as HeroSection);
  },
  { deep: true }
);
</script>
