<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="links" title-placeholder="Outras viagens que você vai gostar" @patch="patch" />
      <EdGroup title="Links/Roteiros" :count="`${items.length} ${items.length === 1 ? 'item' : 'itens'}`">
        <EdList
          :items="items"
          :item-title="item => readText(item.title)"
          :new-item="newItem"
          add-label="Adicionar link/roteiro"
          item-label="Link/roteiro"
          :max="maxItems"
          @update:items="patch({ items: $event })"
        >
          <template #default="{ item, update }">
            <EdSeg
              :model-value="item.source"
              label="Origem"
              :options="[
                { value: 'page', label: 'Minha página' },
                { value: 'external', label: 'Link' }
              ]"
              @update:model-value="update({ source: $event, pageId: undefined, url: '' })"
            />
            <label v-if="item.source === 'page'" class="ved-field">
              <span class="ved-label">Página</span>
              <select class="ved-select" :value="item.pageId || ''" @change="pickPage(Number(($event.target as HTMLSelectElement).value), update)">
                <option value="">{{ loadingPages ? "Carregando…" : "Escolher página…" }}</option>
                <option v-for="page in pages" :key="page.id" :value="page.id">{{ page.title }}</option>
              </select>
              <span class="ved-hint">Foto, título e texto vêm da página; dá para mudar abaixo.</span>
            </label>
            <template v-else>
              <EdText :model-value="item.url" label="Endereço" type="url" placeholder="https://" @update:model-value="update({ url: $event })" />
              <button type="button" class="ved-inline-btn" :disabled="!item.url || fetchingIndex !== null" @click="fetchMetadata(item, update)">
                {{ fetchingIndex !== null ? "Buscando…" : "Buscar foto e texto do link" }}
              </button>
              <p v-if="fetchError" class="ved-hint">{{ fetchError }}</p>
            </template>
            <ImageUploadField layout="compact" :model-value="item.image || ''" label="Foto" @update:model-value="update({ image: $event || '' })" />
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
          </template>
        </EdList>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.carouselEnabled === false ? 'grid' : 'carousel'"
          :options="[
            { value: 'carousel', label: 'Carrossel', desc: 'Cards que deslizam' },
            { value: 'grid', label: 'Grade', desc: 'Até 8 cards fixos' }
          ]"
          @update:model-value="setLayout"
        />
        <p v-if="layoutError" class="ved-hint">{{ layoutError }}</p>
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import api from "../../../../services/api";
import type { LinkCardItem, LinksSection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdLayouts from "../EdLayouts.vue";
import EdList from "../EdList.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import EdToggle from "../EdToggle.vue";
import V2EditShell from "../V2EditShell.vue";
import { useAgencyPages, type AgencyPage } from "../useAgencyPages";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: LinksSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: LinksSection): void }>();
const { patch } = useDraft(props, emit);

const items = computed(() => props.modelValue.items || []);
const maxItems = computed(() => (props.modelValue.carouselEnabled === false ? 8 : undefined));
const newItem = (): LinkCardItem => ({
  id: `link-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
  source: "page",
  url: "",
  image: "",
  title: "",
  description: "",
  buttonLabel: "Ver roteiro",
  openInNewTab: false,
  showDates: false,
  showPrice: false
});

const { pages, loading: loadingPages, load: loadPages, pageUrl } = useAgencyPages();
onMounted(loadPages);

const plainText = (value: any): string => {
  if (typeof value === "string") return value.replace(/<[^>]+>/g, "").trim();
  if (value && typeof value === "object") return plainText(value.pt || value.es || Object.values(value)[0] || "");
  return "";
};
// Mesmos dados que o formulário antigo usava: capa, título e texto da própria página.
const pageCard = (page: AgencyPage) => {
  let config: Record<string, any> = {};
  try {
    config = typeof page.config_json === "string" ? JSON.parse(page.config_json) : page.config_json || {};
  } catch {
    config = {};
  }
  const hero = Array.isArray(config.sections) ? config.sections.find((section: any) => section?.type === "hero") || {} : {};
  return {
    title: (page.seo_title || page.title || "").trim(),
    description: plainText(hero.subtitle) || plainText(config.general?.shortDescription) || page.seo_description || "",
    image: hero.backgroundImage || page.cover_image_url || ""
  };
};
const pickPage = (pageId: number, update: (changes: Record<string, any>) => void) => {
  const page = pages.value.find(candidate => candidate.id === pageId);
  if (!page) {
    update({ pageId: undefined, url: "" });
    return;
  }
  update({ pageId: page.id, url: pageUrl(page), ...pageCard(page) });
};

const fetchingIndex = ref<number | null>(null);
const fetchError = ref("");
const fetchMetadata = async (item: LinkCardItem, update: (changes: Record<string, any>) => void) => {
  if (!item.url) return;
  fetchingIndex.value = 0;
  fetchError.value = "";
  const url = /^https?:\/\//i.test(item.url) ? item.url : `https://${item.url}`;
  try {
    const { data } = await api.post<{ url: string; title: string; description: string; image: string }>("/pages/link-metadata", { url });
    update({ url: data.url || url, title: data.title || item.title, description: data.description || item.description, image: data.image || item.image });
  } catch (error: any) {
    fetchError.value = error?.response?.data?.detail || "Não deu para ler o link. Preencha a foto e o texto à mão.";
  } finally {
    fetchingIndex.value = null;
  }
};

const layoutError = ref("");
const setLayout = (layout: string) => {
  layoutError.value = "";
  if (layout === "grid" && items.value.length > 8) {
    layoutError.value = "A grade mostra até 8 links/roteiros. Remova alguns antes de trocar.";
    return;
  }
  patch({ carouselEnabled: layout !== "grid" });
};
</script>
