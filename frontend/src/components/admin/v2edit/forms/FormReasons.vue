<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="reasons" title-placeholder="Por que viajar com a gente" @patch="patch" />
      <EdGroup title="Itens" :count="`${items.length} ${items.length === 1 ? 'item' : 'itens'}`">
        <EdSeg
          :model-value="mode"
          label="Os itens usam"
          :options="[
            { value: 'icon', label: 'Ícones' },
            { value: 'emoji', label: 'Emojis' }
          ]"
          hint="Um tipo só para a seção inteira. Ícones seguem a cor de destaque; emojis aparecem coloridos."
          @update:model-value="setMode"
        />
        <EdList
          :items="items"
          :item-title="item => readText(item.title)"
          :new-item="() => ({ icon: mode === 'icon' ? 'icon:check' : '✅', title: '', description: '' })"
          add-label="Adicionar item"
          item-label="Item"
          @update:items="patch({ items: $event })"
        >
          <template #default="{ item, update }">
            <div class="ved-field">
              <span class="ved-label">{{ mode === "icon" ? "Ícone" : "Emoji" }}</span>
              <IconEmojiPicker :model-value="item.icon || ''" :mode="mode" :allow-clear="false" @update:model-value="update({ icon: $event })" />
            </div>
            <EdText :model-value="readText(item.title)" label="Título" @update:model-value="update({ title: writeText(item.title, $event) })" />
            <EdRich :model-value="readText(item.description)" label="Texto" @update:model-value="update({ description: writeText(item.description, $event) })" />
          </template>
        </EdList>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdAlign :value="modelValue" type="reasons" @patch="patch" />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" fallback="#F2F4F1" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ReasonsSection } from "../../../../types/page";
import IconEmojiPicker from "../../inputs/IconEmojiPicker.vue";
import EdSeg from "../EdSeg.vue";
import EdAlign from "../EdAlign.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdList from "../EdList.vue";
import EdRich from "../EdRich.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";
import { iconValueName } from "../../../../utils/travelIcons";

const props = defineProps<{ modelValue: ReasonsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ReasonsSection): void }>();
const { patch } = useDraft(props, emit);
const items = computed(() => props.modelValue.items || []);

// Seções antigas não guardam o tipo: com algum ícone salvo, são de ícones; senão, de emojis.
const mode = computed<"icon" | "emoji">(
  () => props.modelValue.iconMode || (items.value.some(item => iconValueName(item.icon)) ? "icon" : "emoji")
);
const ICON_SUGGESTIONS = ["icon:check", "icon:plane", "icon:bed", "icon:users", "icon:map", "icon:shield", "icon:utensils", "icon:camera"];
const EMOJI_SUGGESTIONS = ["✅", "✈️", "🏨", "👥", "🗺️", "🛡️", "🍽️", "📸"];
// Trocar o tipo troca todos os itens, para a seção nunca misturar ícone e emoji.
const setMode = (next: "icon" | "emoji") => {
  if (next === mode.value && props.modelValue.iconMode === next) return;
  const isIcon = (value?: string) => !!iconValueName(value);
  patch({
    iconMode: next,
    items: items.value.map((item, index) => {
      const keep = next === "icon" ? isIcon(item.icon) : !!item.icon && !isIcon(item.icon);
      if (keep) return item;
      const list = next === "icon" ? ICON_SUGGESTIONS : EMOJI_SUGGESTIONS;
      return { ...item, icon: list[index % list.length] };
    })
  });
};
</script>
