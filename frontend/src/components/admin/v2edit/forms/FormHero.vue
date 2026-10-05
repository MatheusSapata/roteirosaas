<template>
  <V2EditShell>
    <template #content>
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
          <ImageUploadField :model-value="modelValue.backgroundImage || ''" label="Foto do computador" hint="Ideal 2400 × 1350 px." layout="compact" @update:model-value="patch({ backgroundImage: $event || '' })" />
          <ImageUploadField
            :model-value="modelValue.mobileBackgroundImage || ''"
            label="Foto do celular"
            hint="Opcional. Melhor quase quadrada; sem ela, usa a do computador."
            layout="compact"
            @update:model-value="patch({ mobileBackgroundImage: $event || '' })"
          />
        </template>
        <EdText v-else :model-value="modelValue.videoUrl || ''" label="Link do vídeo" type="url" hint="YouTube. Toca sem som, em repetição." @update:model-value="patch({ videoUrl: $event })" />
      </EdGroup>
      <EdGroup title="Texto">
        <div class="ved-field">
          <span class="ved-label">Destaques</span>
          <EdList :items="chips" :item-title="chip => chip.text" :new-item="() => ({ text: '', icon: '' })" add-label="Adicionar destaque" item-label="Destaque" :max="6" @update:items="setChips">
            <template #default="{ item, update }">
              <div class="ved-field">
                <span class="ved-label">Ícone</span>
                <IconEmojiPicker :model-value="item.icon" mode="icon" @update:model-value="update({ icon: $event })" />
              </div>
              <EdText :model-value="item.text" label="Texto" placeholder="Aéreo incluso" @update:model-value="update({ text: $event })" />
            </template>
          </EdList>
        </div>
        <EdText :model-value="title" label="Título" placeholder="Dolomitas e Lago di Braies em 7 dias" @update:model-value="title = $event" />
        <EdRich :model-value="subtitle" label="Texto" @update:model-value="subtitle = $event" />
      </EdGroup>
      <EdGroup title="Datas">
        <div class="ved-pair">
          <EdText :model-value="modelValue.departureDate || ''" label="Saída" type="date" @update:model-value="patch({ departureDate: $event })" />
          <EdText :model-value="modelValue.returnDate || ''" label="Volta" type="date" :min="modelValue.departureDate || undefined" @update:model-value="patch({ returnDate: $event })" />
        </div>
        <p class="ved-info">A duração é calculada. O roteiro dia a dia usa a mesma data de início.</p>
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
        <p class="ved-info">O logo da agência aparece sozinho quando a página não tem Menu do topo.</p>
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { HeroSection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import IconEmojiPicker from "../../inputs/IconEmojiPicker.vue";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdLayouts from "../EdLayouts.vue";
import EdList from "../EdList.vue";
import EdRich from "../EdRich.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
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

// Destaques ficam em duas listas paralelas: textos (chips) e ícones (chipIcons).
const chips = computed(() => (props.modelValue.chips || []).map((chip, index) => ({ text: readText(chip), icon: props.modelValue.chipIcons?.[index] || "" })));
const setChips = (next: { text: string; icon: string }[]) =>
  patch({
    chips: next.map((chip, index) => writeText(props.modelValue.chips?.[index], chip.text)),
    chipIcons: next.map(chip => chip.icon)
  });
</script>
