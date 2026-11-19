<template>
  <div class="lcf">
    <ImageUploadField layout="compact" enable-crop edit-label="Cortar" editor-title="Cortar foto" :model-value="item.image || ''" label="Foto" @update:model-value="update({ image: $event || '' })" />
    <EdText :model-value="readText(item.title)" label="Título" @update:model-value="update({ title: writeText(item.title, $event) })" />
    <EdText :model-value="readText(item.description)" label="Texto" multiline @update:model-value="update({ description: writeText(item.description, $event) })" />
    <EdToggle :model-value="!!item.showDates" label="Mostrar datas" @update:model-value="update({ showDates: $event })" />
    <div v-if="item.showDates" class="ved-pair">
      <EdText :model-value="item.departureDate || ''" label="Saída" type="date" @update:model-value="update({ departureDate: $event })" />
      <EdText :model-value="item.returnDate || ''" label="Volta" type="date" @update:model-value="update({ returnDate: $event })" />
    </div>
    <EdToggle :model-value="!!item.showPrice" label="Mostrar preço" @update:model-value="update({ showPrice: $event })" />
    <template v-if="item.showPrice">
      <EdText :model-value="item.priceValue || ''" label="Preço" placeholder="R$ 15.900" @update:model-value="update({ priceValue: $event })" />
      <div class="ved-pair">
        <EdText :model-value="readText(item.pricePrefix)" label="Antes do preço" placeholder="a partir de" @update:model-value="update({ pricePrefix: writeText(item.pricePrefix, $event) })" />
        <EdText :model-value="readText(item.priceSuffix)" label="Depois do preço" placeholder="por pessoa" @update:model-value="update({ priceSuffix: writeText(item.priceSuffix, $event) })" />
      </div>
    </template>
    <EdText :model-value="readText(item.buttonLabel)" label="Texto do botão" placeholder="Ver roteiro" @update:model-value="update({ buttonLabel: writeText(item.buttonLabel, $event) })" />
    <EdToggle v-if="item.source === 'external'" :model-value="item.openInNewTab !== false" label="Abrir em nova aba" @update:model-value="update({ openInNewTab: $event })" />
    <div class="ved-field">
      <span class="ved-label">Destaques</span>
      <span class="ved-hint">Faixas sobre a foto, tipo "LOTADO". Até 3 por card, cada uma com texto e, se quiser, um ícone.</span>
      <EdList
        :items="item.highlights || []"
        :item-title="h => readText(h.text)"
        :new-item="newHighlight"
        add-label="Adicionar destaque"
        item-label="Destaque"
        :max="3"
        @update:items="update({ highlights: $event })"
      >
        <template #default="{ item: highlight, update: updateHighlight }">
          <EdText :model-value="readText(highlight.text)" label="Texto" placeholder="LOTADO" @update:model-value="updateHighlight({ text: writeText(highlight.text, $event) })" />
          <EdColor :model-value="highlight.color" label="Cor de fundo" @update:model-value="updateHighlight({ color: $event })" />
          <div class="ved-field">
            <span class="ved-label">Ícone (opcional)</span>
            <span class="ved-hint">Escolha da lista de turismo, ou cole um emoji (ex: com o atalho de emoji do sistema — Windows "Win + ." ou Mac "Cmd + Ctrl + Espaço").</span>
            <div class="fl-icon-row">
              <TravelIconPicker :model-value="isLibraryIcon(highlight.icon) ? highlight.icon || '' : ''" @update:model-value="updateHighlight({ icon: $event })" />
              <input
                class="ved-input fl-icon-emoji"
                type="text"
                maxlength="8"
                placeholder="ou emoji"
                :value="isLibraryIcon(highlight.icon) ? '' : highlight.icon || ''"
                @input="updateHighlight({ icon: ($event.target as HTMLInputElement).value })"
              />
            </div>
            <EdSeg
              v-if="highlight.icon"
              :model-value="highlight.iconPosition === 'right' ? 'right' : 'left'"
              label="Lado do ícone"
              :options="[
                { value: 'left', label: 'Esquerda' },
                { value: 'right', label: 'Direita' }
              ]"
              @update:model-value="updateHighlight({ iconPosition: $event })"
            />
          </div>
        </template>
      </EdList>
    </div>
  </div>
</template>

<script setup lang="ts">
import { iconValueName } from "../../../../utils/travelIcons";
import type { LinkCardItem, LinkHighlight } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import TravelIconPicker from "../../inputs/TravelIconPicker.vue";
import EdColor from "../EdColor.vue";
import EdList from "../EdList.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import EdToggle from "../EdToggle.vue";
import { readText, writeText } from "../useDraft";

// Campos de um card de Links/Roteiros (foto, textos, datas, preço, botão e destaques): os mesmos
// no modo manual e na edição individual dos cards de uma tag.
defineProps<{ item: LinkCardItem; update: (changes: Record<string, any>) => void }>();

const newHighlight = (): LinkHighlight => ({ id: `hl-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, text: "", color: "#F59E0B", icon: "" });
// Ícone da lista de turismo ("icon:<chave>") ou emoji livre (qualquer outro texto).
const isLibraryIcon = (icon?: string) => !!iconValueName(icon);
</script>

<style scoped>
.lcf { display: contents; }
.fl-icon-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
}
.fl-icon-emoji {
  width: 100px;
  text-align: center;
  font-size: 18px;
}
</style>
