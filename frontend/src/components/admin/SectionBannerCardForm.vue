<template>
  <div class="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">{{ viewCopy.header.title }}</h3>
    </div>

    <div class="space-y-3">
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.title.label }}</label>
        <input
          v-model="local.title"
          :placeholder="viewCopy.title.placeholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
      </div>
      <div>
        <ImageUploadField
          v-model="local.backgroundImage"
          :label="viewCopy.backgroundImage.label"
          :hint="viewCopy.backgroundImage.hint"
        />
      </div>
    </div>

    <div class="rounded-xl border border-slate-200 p-4">
      <p class="text-sm font-semibold text-slate-700">{{ viewCopy.colors.heading }}</p>
      <div class="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.sectionBackground }}</label>
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
          <p class="text-xs text-slate-500">{{ viewCopy.colors.sectionBackgroundHint }}</p>
        </div>
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.gradientBase }}</label>
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
          <p class="text-xs text-slate-500">{{ viewCopy.colors.gradientBaseHint }}</p>
        </div>
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.cardBackground }}</label>
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
          <p class="text-xs text-slate-500">{{ viewCopy.colors.cardBackgroundHint }}</p>
        </div>
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.cardBorder }}</label>
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
          <p class="text-xs text-slate-500">{{ viewCopy.colors.cardBorderHint }}</p>
        </div>
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        <div class="space-y-1">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.textColor }}</label>
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
          <p class="text-xs text-slate-500">{{ viewCopy.colors.textColorHint }}</p>
        </div>
      </div>
    </div>

    <div class="rounded-xl border border-slate-200 p-4 space-y-3">
      <p class="text-sm font-semibold text-slate-700">{{ viewCopy.cta.heading }}</p>
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
      <div class="space-y-1" :class="local.ctaMode === 'section' ? 'md:max-w-xs' : ''">
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.colorLabel }}</label>
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
        <p class="text-xs text-slate-500">{{ viewCopy.cta.colorHint }}</p>
      </div>
    </div>

    <p class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      {{ viewCopy.notes.fullWidth }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import type { BannerCardSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: BannerCardSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BannerCardSection): void }>();
const t = createAdminLocalizer();

const viewCopy = {
  header: {
    title: t({ pt: "Banner em Card", es: "Banner en Card" })
  },
  title: {
    label: t({ pt: "Título", es: "Título" }),
    placeholder: t({ pt: "Headline principal", es: "Titular principal" })
  },
  backgroundImage: {
    label: t({ pt: "Imagem de fundo", es: "Imagen de fondo" }),
    hint: t({
      pt: "Use fotos em alta resolução. A imagem aparece desfocada com um gradiente por cima.",
      es: "Usa fotos en alta resolución. La imagen aparece difuminada con un degradado encima."
    })
  },
  colors: {
    heading: t({ pt: "Cores e contraste", es: "Colores y contraste" }),
    sectionBackground: t({ pt: "Cor do fundo da seção", es: "Color del fondo de la sección" }),
    sectionBackgroundHint: t({ pt: "Define a cor atrás do card.", es: "Define el color detrás del card." }),
    gradientBase: t({ pt: "Base do gradiente", es: "Base del degradado" }),
    gradientBaseHint: t({ pt: "Define o tom que vem da esquerda para a direita.", es: "Define el tono que va de izquierda a derecha." }),
    cardBackground: t({ pt: "Cor do card", es: "Color del card" }),
    cardBackgroundHint: t({ pt: "Fica visível quando não há imagem.", es: "Se nota cuando no hay imagen." }),
    cardBorder: t({ pt: "Cor da borda", es: "Color del borde" }),
    cardBorderHint: t({ pt: "Use transparência para um contorno sutil.", es: "Usa transparencia para un contorno sutil." }),
    textColor: t({ pt: "Cor do texto", es: "Color del texto" }),
    textColorHint: t({ pt: "Afeta descrições/legendas do banner.", es: "Afecta descripciones/leyendas del banner." })
  },
  cta: {
    heading: t({ pt: "Botão / CTA", es: "Botón / CTA" }),
    textLabel: t({ pt: "Texto do botão", es: "Texto del botón" }),
    textPlaceholder: t({ pt: "Quero saber mais", es: "Quiero saber más" }),
    linkLabel: t({ pt: "Link", es: "Link" }),
    linkPlaceholder: t({ pt: "https://wa.me/", es: "https://wa.me/" }),
    colorLabel: t({ pt: "Cor do botão", es: "Color del botón" }),
    colorHint: t({ pt: "Se preferir, use a cor global definida no topo do editor.", es: "Si prefieres, usa el color global definido arriba del editor." })
  },
  notes: {
    fullWidth: t({
      pt: "O banner card ocupa toda a largura disponível no preview e mantém o mesmo layout no desktop e no mobile.",
      es: "El banner card ocupa todo el ancho disponible en el preview y mantiene el mismo layout en desktop y mobile."
    })
  }
};

const ensureColor = (value: string | undefined, fallback: string) => value && value.trim() ? value : fallback;

const defaultTitle = t({ pt: "Conte com especialistas para transformar o seu roteiro.", es: "Cuenta con especialistas para transformar tu itinerario." });
const defaultSubtitle = t({ pt: "", es: "" });
const defaultCtaLabel = t({ pt: "Quero saber mais", es: "Quiero saber más" });
const defaultCtaLink = t({ pt: "https://wa.me/", es: "https://wa.me/" });

const local = reactive<BannerCardSection>({
  ...props.modelValue,
  enabled: props.modelValue.enabled ?? true,
  backgroundColor: ensureColor(props.modelValue.backgroundColor, "#020617"),
  title: props.modelValue.title || defaultTitle,
  subtitle: props.modelValue.subtitle || defaultSubtitle,
  ctaLabel: props.modelValue.ctaLabel || defaultCtaLabel,
  ctaLink: props.modelValue.ctaLink || defaultCtaLink,
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
  local.title = value.title || defaultTitle;
  local.subtitle = value.subtitle || defaultSubtitle;
  local.ctaLabel = value.ctaLabel || defaultCtaLabel;
  local.ctaLink = value.ctaLink || defaultCtaLink;
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
