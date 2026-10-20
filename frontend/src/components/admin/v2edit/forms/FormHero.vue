<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Texto">
        <EdText :model-value="title" label="Título" placeholder="Dolomitas e Lago di Braies em 7 dias" @update:model-value="title = $event" />
        <EdRich :model-value="subtitle" label="Texto" @update:model-value="subtitle = $event" />
      </EdGroup>
      <EdGroup title="Destaques" kind="items" :count="`${chips.length} de 6`">
        <EdList :items="chips" :item-title="chip => chip.text" :new-item="() => ({ text: '', icon: '' })" add-label="Adicionar destaque" item-label="Destaque" :max="6" @update:items="setChips">
          <template #default="{ item, update }">
            <div class="ved-field">
              <span class="ved-label">Ícone</span>
              <IconEmojiPicker :model-value="item.icon" mode="icon" @update:model-value="update({ icon: $event })" />
            </div>
            <EdText :model-value="item.text" label="Texto" placeholder="Aéreo incluso" @update:model-value="update({ text: $event })" />
          </template>
        </EdList>
      </EdGroup>
      <EdGroup title="Mídia">
        <EdSeg
          :model-value="mediaMode"
          label="Fundo"
          :options="[
            { value: 'photo', label: 'Foto' },
            { value: 'video', label: 'Vídeo' }
          ]"
          @update:model-value="setMediaMode"
        />
        <template v-if="mediaMode === 'photo'">
          <ImageUploadField
            :model-value="modelValue.backgroundImage || ''"
            label="Foto do computador"
            :hint="desktopHint"
            layout="compact"
            enable-crop
            edit-label="Cortar"
            editor-title="Cortar foto do computador"
            :crop-aspect="frameAspect(frames.desktop)"
            :fallback-url="modelValue.backgroundImage ? '' : modelValue.mobileBackgroundImage || ''"
            @update:model-value="setPhoto('desktop', $event)"
          />
          <button v-if="modelValue.backgroundImage" type="button" class="ved-inline-btn" @click="openFocus('desktop')">Ajustar encaixe</button>
          <ImageUploadField
            :model-value="modelValue.mobileBackgroundImage || ''"
            label="Foto do celular"
            :hint="mobileHint"
            layout="compact"
            enable-crop
            edit-label="Cortar"
            editor-title="Cortar foto do celular"
            :crop-aspect="frameAspect(frames.mobile)"
            :fallback-url="modelValue.mobileBackgroundImage ? '' : modelValue.backgroundImage || ''"
            @update:model-value="setPhoto('mobile', $event)"
          />
          <button v-if="modelValue.mobileBackgroundImage" type="button" class="ved-inline-btn" @click="openFocus('mobile')">Ajustar encaixe</button>
          <ImageFocusDialog
            :open="focusDialog.open"
            :src="focusDialog.src"
            :model-value="focusDialog.value"
            :screens="focusDialog.screens"
            :default-focus="frames.focus"
            :desktop-ratio="frames.desktop"
            :mobile-ratio="frames.mobile"
            :title="focusDialog.title"
            @apply="applyFocus"
            @close="focusDialog.open = false"
          />
        </template>
        <EdText v-else :model-value="modelValue.videoUrl || ''" label="Link do vídeo" type="url" hint="YouTube. Toca sem som, em repetição." @update:model-value="patch({ videoUrl: $event })" />
      </EdGroup>
      <EdGroup title="Logo">
        <ImageUploadField
          layout="compact"
          label="Imagem"
          contain
          enable-crop
          editor-title="Logo desta página"
          edit-label="Editar"
          remove-label="Usar o da agência"
          :model-value="customLogo"
          :fallback-url="agencyLogo"
          :hint="logoHint"
          @update:model-value="patch({ logoUrl: $event || '' })"
        />
        <EdSeg
          v-if="!hasHeader"
          :model-value="logoPosition"
          label="Posição"
          :options="[
            { value: 'top', label: 'No topo' },
            { value: 'content', label: 'Junto ao conteúdo' }
          ]"
          hint="Padrão: no topo quando há destaques; junto ao conteúdo quando não há."
          @update:model-value="patch({ logoPosition: $event })"
        />
        <EdRange v-if="!hasHeader" :model-value="modelValue.logoSize ?? 64" label="Tamanho" :min="32" :max="160" :step="4" unit="px" @update:model-value="patch({ logoSize: $event })" />
        <EdSeg
          :model-value="logoCorners"
          label="Cantos"
          :options="[
            { value: 0, label: 'Retos' },
            { value: 12, label: 'Arredondados' },
            { value: 999, label: 'Redondo' }
          ]"
          hint="Faz diferença em logos com fundo."
          @update:model-value="patch({ logoBorderRadius: $event })"
        />
        <p v-if="hasHeader" class="ved-info">Esta página tem Menu do topo: o logo aparece nele, com esta imagem e estes cantos. O tamanho fica em Menu do topo › Logo.</p>
      </EdGroup>
      <EdGroup title="Datas">
        <div class="ved-pair">
          <EdText :model-value="modelValue.departureDate || ''" label="Saída" type="date" @update:model-value="patch({ departureDate: $event })" />
          <EdText :model-value="modelValue.returnDate || ''" label="Volta" type="date" :min="modelValue.departureDate || undefined" @update:model-value="patch({ returnDate: $event })" />
        </div>
        <p class="ved-info">O roteiro dia a dia usa a mesma data de início.</p>
      </EdGroup>
      <EdButton :value="modelValue" placeholder="Quero reservar" @patch="patch" />
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.layout || 'immersive'"
          :options="[
            { value: 'immersive', label: 'Imersivo', desc: 'Foto inteira atrás do texto' },
            { value: 'classic', label: 'Clássico', desc: 'Texto centralizado' },
            { value: 'split', label: 'Dividido', desc: 'Texto ao lado da foto' },
            { value: 'card', label: 'Cartão', desc: 'Texto num card sobre a foto' }
          ]"
          @update:model-value="patch({ layout: $event })"
        />
      </EdGroup>
      <EdGroup title="Fundo do texto no celular">
        <EdBackground :value="modelValue" field="gradientColor" @change="patch" fallback="#0B1410" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, inject, ref } from "vue";
import type { Ref } from "vue";
import type { HeroSection, PageSection } from "../../../../types/page";
import { PUBLIC_BRANDING_KEY } from "../../../../utils/brandingKeys";
import { resolveMediaUrl } from "../../../../utils/media";
import { sectionsInjectionKey } from "../../sectionsContext";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import IconEmojiPicker from "../../inputs/IconEmojiPicker.vue";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdLayouts from "../EdLayouts.vue";
import EdList from "../EdList.vue";
import EdRange from "../EdRange.vue";
import EdRich from "../EdRich.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import ImageFocusDialog from "../ImageFocusDialog.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: HeroSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: HeroSection): void }>();
const { patch, text } = useDraft(props, emit);
const title = text("title");
const subtitle = text("subtitle");

const mediaMode = ref<"photo" | "video">(props.modelValue.videoUrl ? "video" : "photo");
// Voltar para foto tira o vídeo, senão ele continuaria por cima da foto.
const setMediaMode = (mode: "photo" | "video") => {
  mediaMode.value = mode;
  if (mode === "photo" && props.modelValue.videoUrl) patch({ videoUrl: "" });
};

// Logo: por padrão o da agência (Minha Agência); trocar aqui vale só para esta página.
// O editor copia o logo da agência para o Banner quando ele está vazio, então "é o da agência"
// é comparar as duas imagens.
const brandingRef = inject<Ref<Record<string, any>> | null>(PUBLIC_BRANDING_KEY, null);
const agencyLogo = computed(() => String(brandingRef?.value?.logo_url || ""));
const customLogo = computed(() => {
  const own = props.modelValue.logoUrl || "";
  return own && resolveMediaUrl(own) !== resolveMediaUrl(agencyLogo.value) ? own : "";
});
const logoHint = computed(() => {
  if (customLogo.value) return "Só nesta página. Editar corta a imagem e remove o fundo.";
  if (agencyLogo.value) return "Logo da agência (Minha Agência). Trocar vale só para esta página; Editar corta e remove o fundo.";
  return "A agência ainda não tem logo em Minha Agência. Envie um para esta página.";
});
const logoCorners = computed(() => {
  const radius = Number(props.modelValue.logoBorderRadius ?? 0);
  return radius <= 0 ? 0 : radius >= 100 ? 999 : 12;
});
// Com Menu do topo, o logo aparece nele (o Banner esconde o dele) e o tamanho é o do menu.
const sections = inject(sectionsInjectionKey, ref<PageSection[]>([]));
const hasHeader = computed(() => sections.value.some(section => section.type === "header" && section.enabled !== false));

// Destaques ficam em duas listas paralelas: textos (chips) e ícones (chipIcons).
const chips = computed(() => (props.modelValue.chips || []).map((chip, index) => ({ text: readText(chip), icon: props.modelValue.chipIcons?.[index] || "" })));
const setChips = (next: { text: string; icon: string }[]) =>
  patch({
    chips: next.map((chip, index) => writeText(props.modelValue.chips?.[index], chip.text)),
    chipIcons: next.map(chip => chip.icon)
  });
// Fotos: sem a do computador, a do celular vale nas duas telas (e vice-versa). O encaixe é de
// cada foto; foto nova volta ao encaixe padrão. Enviar só a do celular abre o encaixe na hora,
// porque ela vai aparecer também na capa larga do computador.
type PhotoSlot = "desktop" | "mobile";
const layout = computed(() => props.modelValue.layout || "immersive");
const desktopHint = computed(() =>
  !props.modelValue.backgroundImage && props.modelValue.mobileBackgroundImage
    ? "Usando a foto do celular. Envie outra se quiser uma só para o computador."
    : "Ideal 2400 × 1350 px."
);
const mobileHint = computed(() =>
  props.modelValue.mobileBackgroundImage || !props.modelValue.backgroundImage
    ? "Opcional. Melhor quase quadrada; sem ela, usa a do computador."
    : "Usando a do computador. Envie uma quase quadrada se quiser outra no celular."
);
// Proporção numérica de uma moldura ("16 / 9" vira 1,77), para o recorte seguir o quadro.
const frameAspect = (frame: string) => {
  const [w, h] = frame.split("/").map(n => parseFloat(n));
  return w && h ? w / h : undefined;
};
// Molduras da prévia do encaixe, na proporção que a capa tem em cada tela.
const frames = computed(() => {
  if (layout.value === "split") return { desktop: "4 / 5", mobile: "4 / 5", focus: "50% 50%" };
  if (layout.value === "immersive") return { desktop: "16 / 9", mobile: "1 / 1.12", focus: "50% 0%" };
  return { desktop: "16 / 9", mobile: "7 / 10", focus: "50% 0%" };
});
// Telas em que a foto aparece: a do computador vai também ao celular sem foto própria (e nos
// layouts que usam uma foto só); a do celular vai também ao computador sem foto própria.
const screensFor = (slot: PhotoSlot, hasDesktop: boolean, hasMobile: boolean): PhotoSlot[] => {
  if (slot === "desktop") return hasMobile && layout.value === "immersive" ? ["desktop"] : ["desktop", "mobile"];
  return hasDesktop ? ["mobile"] : ["desktop", "mobile"];
};
const focusDialog = ref({ open: false, slot: "desktop" as PhotoSlot, src: "", value: "", screens: [] as PhotoSlot[], title: "" });
const openFocus = (slot: PhotoSlot, uploaded?: string) => {
  const section = props.modelValue;
  const url = uploaded || (slot === "desktop" ? section.backgroundImage : section.mobileBackgroundImage) || "";
  if (!url) return;
  const hasDesktop = Boolean(slot === "desktop" ? url : section.backgroundImage);
  const hasMobile = Boolean(slot === "mobile" ? url : section.mobileBackgroundImage);
  const screens = screensFor(slot, hasDesktop, hasMobile);
  focusDialog.value = {
    open: true,
    slot,
    src: resolveMediaUrl(url) || url,
    value: uploaded ? "" : (slot === "desktop" ? section.backgroundFocus : section.mobileBackgroundFocus) || "",
    screens,
    title: screens.length > 1 ? "Ajuste a foto para o computador e o celular" : slot === "desktop" ? "Ajuste a foto do computador" : "Ajuste a foto do celular"
  };
};
const setPhoto = (slot: PhotoSlot, url: string | null) => {
  const value = url || "";
  if (slot === "desktop") patch({ backgroundImage: value, backgroundFocus: "" });
  else patch({ mobileBackgroundImage: value, mobileBackgroundFocus: "" });
  if (value && slot === "mobile" && !props.modelValue.backgroundImage) openFocus("mobile", value);
};
const applyFocus = (value: string) => {
  patch(focusDialog.value.slot === "desktop" ? { backgroundFocus: value } : { mobileBackgroundFocus: value });
  focusDialog.value.open = false;
};

// Sem escolha salva, mostra o padrão da capa: no topo com destaques, junto ao conteúdo sem eles.
const logoPosition = computed(() => props.modelValue.logoPosition || (chips.value.some(chip => chip.text.trim()) ? "top" : "content"));
</script>
