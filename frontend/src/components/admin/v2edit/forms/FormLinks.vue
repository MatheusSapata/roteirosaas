<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="links" title-placeholder="Outras viagens que você vai gostar" @patch="patch" />
      <EdGroup title="Origem dos cards" kind="items" :count="tagMode ? 'Por tag' : 'Escolha manual'">
        <EdSeg
          :model-value="tagMode ? 'tag' : 'manual'"
          :options="[
            { value: 'manual', label: 'Escolher roteiros' },
            { value: 'tag', label: 'Por tag' }
          ]"
          @update:model-value="setMode"
        />
        <p class="ved-hint">
          {{ tagMode ? "Os cards vêm das páginas publicadas com as tags escolhidas. Roteiro novo com a tag entra sozinho." : "Cada card é escolhido à mão." }}
        </p>
      </EdGroup>
      <EdGroup v-if="tagMode" title="Roteiros por tag" :count="`${items.length} ${items.length === 1 ? 'roteiro' : 'roteiros'}`">
        <div class="ved-field">
          <span class="ved-label">Tags</span>
          <div v-if="agencyTags.length" class="fl-chips">
            <button
              v-for="tag in agencyTags"
              :key="tag.id"
              type="button"
              class="fl-chip"
              :class="{ on: selectedTagIds.includes(tag.id) }"
              :style="tagStyle(tag.color)"
              :aria-pressed="selectedTagIds.includes(tag.id)"
              @click="toggleTag(tag.id)"
            >
              <i aria-hidden="true"></i>{{ tag.name }}<span>{{ tag.page_count }}</span>
            </button>
          </div>
          <span v-else class="ved-hint">Nenhuma tag criada ainda. Crie na lista de páginas ou na aba Tags do editor, e marque os roteiros.</span>
        </div>
        <EdSeg
          v-if="selectedTagIds.length > 1"
          :model-value="modelValue.tagMatch === 'all' ? 'all' : 'any'"
          label="Mostrar roteiros com"
          :options="[
            { value: 'any', label: 'Qualquer uma' },
            { value: 'all', label: 'Todas as tags' }
          ]"
          @update:model-value="patch({ tagMatch: $event })"
        />
        <label class="ved-field">
          <span class="ved-label">Ordem</span>
          <select class="ved-select" :value="modelValue.tagSort || 'departure'" @change="patch({ tagSort: ($event.target as HTMLSelectElement).value })">
            <option value="departure">Próxima saída primeiro</option>
            <option value="recent">Publicados mais recentemente</option>
            <option value="title">Nome (A–Z)</option>
          </select>
        </label>
        <label class="ved-field">
          <span class="ved-label">Quantidade máxima</span>
          <select class="ved-select" :value="tagLimit" @change="patch({ tagLimit: Number(($event.target as HTMLSelectElement).value) })">
            <option v-for="limit in LIMIT_OPTIONS" :key="limit" :value="limit" :disabled="isGrid && (limit === 0 || limit > 8)">
              {{ limit ? `${limit} roteiros` : "Todos" }}
            </option>
          </select>
          <span v-if="isGrid" class="ved-hint">A grade mostra até 8.</span>
        </label>
        <EdToggle :model-value="modelValue.tagHidePast !== false" label="Esconder viagens que já saíram" hint="Usa a data de saída da Capa de cada roteiro." @update:model-value="patch({ tagHidePast: $event })" />
        <EdToggle :model-value="modelValue.tagExcludeCurrent !== false" label="Não mostrar esta página" hint="Evita que a página apareça nela mesma." @update:model-value="patch({ tagExcludeCurrent: $event })" />
        <EdToggle :model-value="modelValue.tagShowDates !== false" label="Mostrar datas" hint="Vêm da Capa de cada roteiro." @update:model-value="patch({ tagShowDates: $event })" />
        <EdToggle :model-value="modelValue.tagShowPrice !== false" label="Mostrar preço &quot;a partir de&quot;" hint="Menor valor da seção Preços de cada roteiro." @update:model-value="patch({ tagShowPrice: $event })" />
        <EdText
          :model-value="readText(modelValue.tagButtonLabel)"
          label="Texto do botão"
          placeholder="Ver roteiro"
          @update:model-value="patch({ tagButtonLabel: writeText(modelValue.tagButtonLabel, $event) })"
        />
        <div v-if="selectedTagIds.length" class="fl-summary" aria-live="polite">
          <p v-if="resolving">Buscando roteiros…</p>
          <p v-else-if="resolveError">{{ resolveError }}</p>
          <template v-else>
            <p>
              <b>{{ items.length }} {{ items.length === 1 ? "roteiro entra" : "roteiros entram" }} agora.</b>
              Quando outro roteiro receber {{ selectedTagIds.length > 1 ? "essas tags" : "essa tag" }} e for publicado, ele aparece aqui sem editar esta página.
            </p>
            <ul v-if="excluded.length" class="fl-out">
              <li v-for="row in excluded" :key="row.pageId"><span>{{ row.title }}</span><span>{{ REASONS[row.reason] }}</span></li>
            </ul>
          </template>
        </div>
        <button v-if="selectedTagIds.length" type="button" class="ved-inline-btn" :aria-expanded="editingCards" @click="editingCards = !editingCards">
          {{ editingCards ? "Fechar edição individual" : "Editar roteiros da tag individualmente" }}
        </button>
        <template v-if="editingCards && selectedTagIds.length">
          <p class="ved-hint">
            Mude foto, textos, datas, preço, botão e destaques de cada card. A regra da tag continua valendo: roteiros novos entram sozinhos
            e o que você não mexer segue a página.
          </p>
          <EdList
            fixed
            remove-label="Ocultar nesta seção"
            :items="items"
            :item-title="item => readText(item.title)"
            :new-item="newItem"
            add-label=""
            item-label="Roteiro"
            @update:items="onTagItemsChange"
          >
            <template #default="{ item, update }">
              <LinkCardFields :item="item" :update="update" />
              <button v-if="hasOverride(item)" type="button" class="ved-inline-btn" @click="resetCard(item)">Voltar ao original</button>
            </template>
          </EdList>
          <ul v-if="hiddenRows.length" class="fl-out fl-hidden">
            <li v-for="row in hiddenRows" :key="row.pageId">
              <span>{{ row.title }} (oculto nesta seção)</span>
              <button type="button" class="ved-inline-btn" @click="showAgain(row.pageId)">Mostrar de novo</button>
            </li>
          </ul>
        </template>
      </EdGroup>
      <EdGroup v-else title="Links/Roteiros" :count="`${items.length} ${items.length === 1 ? 'item' : 'itens'}`">
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
              <span class="ved-hint">Foto, título, texto, datas e menor preço vêm da página; dá para mudar abaixo.</span>
            </label>
            <template v-else>
              <EdText :model-value="item.url" label="Endereço" type="url" placeholder="https://" @update:model-value="update({ url: $event })" />
              <button type="button" class="ved-inline-btn" :disabled="!item.url || fetchingIndex !== null" @click="fetchMetadata(item, update)">
                {{ fetchingIndex !== null ? "Buscando…" : "Buscar foto e texto do link" }}
              </button>
              <p v-if="fetchError" class="ved-hint">{{ fetchError }}</p>
            </template>
            <LinkCardFields :item="item" :update="update" />
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
        <EdAlign :value="modelValue" type="links" @patch="patch" />
        <p v-if="layoutError" class="ved-hint">{{ layoutError }}</p>
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import api from "../../../../services/api";
import { errorDetail, usePageTags } from "../../../../composables/usePageTags";
import { useAgencyStore } from "../../../../store/useAgencyStore";
import { tagStyle } from "../../../../types/pageTag";
import { pageCardPrefillFields } from "../../../../utils/pageCardPrefill";
import type { LinkCardItem, LinksSection } from "../../../../types/page";
import LinkCardFields from "./LinkCardFields.vue";
import EdAlign from "../EdAlign.vue";
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
  showPrice: false,
  highlights: []
});

const { pages, loading: loadingPages, load: loadPages, pageUrl } = useAgencyPages();
onMounted(loadPages);

// Modo "Por tag": a seção guarda a regra e o servidor monta os cards. Aqui os cards vêm de
// /pages/{id}/tag-cards só para a prévia do editor; a página publicada monta de novo a cada visita.
const route = useRoute();
const agencyStore = useAgencyStore();
const { tags: agencyTags, load: loadTags } = usePageTags();
const LIMIT_OPTIONS = [4, 6, 8, 12, 0];
const REASONS: Record<string, string> = { current: "é esta página", draft: "rascunho", past: "viagem já saiu", limit: "passou do limite", hidden: "oculto nesta seção" };
const tagMode = computed(() => props.modelValue.mode === "tag");
const isGrid = computed(() => props.modelValue.carouselEnabled === false);
const selectedTagIds = computed(() => props.modelValue.tagIds || []);
const tagLimit = computed(() => {
  const limit = props.modelValue.tagLimit ?? 12;
  return isGrid.value && (!limit || limit > 8) ? 8 : limit;
});
// Edição individual dos cards da tag: cada ajuste fica em tagOverrides (por página) e vale por cima do que a tag gera.
const OVERRIDE_FIELDS = ["image", "title", "description", "buttonLabel", "showDates", "departureDate", "returnDate", "showPrice", "priceValue", "pricePrefix", "priceSuffix", "highlights"] as const;
const editingCards = ref(false);
const hiddenRows = computed(() => excluded.value.filter(row => row.reason === "hidden"));
const hasOverride = (item: LinkCardItem) => {
  const entry = item.pageId ? props.modelValue.tagOverrides?.[String(item.pageId)] : undefined;
  return !!entry && Object.keys(entry).some(key => key !== "hidden");
};
const setOverrides = (overrides: NonNullable<LinksSection["tagOverrides"]>, extra: Partial<LinksSection> = {}) => {
  patch({ tagOverrides: Object.keys(overrides).length ? overrides : undefined, ...extra });
};
const onTagItemsChange = (next: LinkCardItem[]) => {
  const overrides = { ...(props.modelValue.tagOverrides || {}) };
  next.forEach(card => {
    const current = items.value.find(item => item.id === card.id);
    if (!current || !card.pageId) return;
    const key = String(card.pageId);
    OVERRIDE_FIELDS.forEach(field => {
      if (JSON.stringify(card[field]) !== JSON.stringify(current[field])) overrides[key] = { ...overrides[key], [field]: card[field] };
    });
  });
  items.value.forEach(current => {
    if (current.pageId && !next.some(card => card.id === current.id)) overrides[String(current.pageId)] = { ...overrides[String(current.pageId)], hidden: true };
  });
  setOverrides(overrides, { items: next });
  // Card ocultado: busca de novo para ele aparecer na lista de ocultos com o botão "Mostrar de novo".
  if (next.length < items.value.length) setTimeout(resolveCards, 0);
};
const resetCard = (item: LinkCardItem) => {
  if (!item.pageId) return;
  const overrides = { ...(props.modelValue.tagOverrides || {}) };
  const key = String(item.pageId);
  const keepHidden = overrides[key]?.hidden;
  if (keepHidden) overrides[key] = { hidden: true };
  else delete overrides[key];
  setOverrides(overrides);
  resolveCards();
};
const showAgain = (pageId: number) => {
  const overrides = { ...(props.modelValue.tagOverrides || {}) };
  const key = String(pageId);
  const { hidden: _hidden, ...rest } = overrides[key] || {};
  if (Object.keys(rest).length) overrides[key] = rest;
  else delete overrides[key];
  setOverrides(overrides);
  resolveCards();
};

const resolving = ref(false);
const resolveError = ref("");
const excluded = ref<{ pageId: number; title: string; reason: string }[]>([]);

onMounted(() => loadTags(agencyStore.currentAgencyId));

const setMode = (mode: string) => {
  if (mode === (tagMode.value ? "tag" : "manual")) return;
  if (mode === "tag") {
    patch({ mode: "tag", manualItems: props.modelValue.items || [], items: [] });
  } else {
    patch({ mode: "manual", items: props.modelValue.manualItems || [], manualItems: undefined });
  }
};
const toggleTag = (tagId: number) => {
  const ids = selectedTagIds.value.includes(tagId) ? selectedTagIds.value.filter(id => id !== tagId) : [...selectedTagIds.value, tagId];
  patch({ tagIds: ids });
};

const ruleKey = computed(() => {
  if (!tagMode.value) return "";
  const { tagIds, tagMatch, tagSort, tagHidePast, tagExcludeCurrent, tagShowDates, tagShowPrice, tagButtonLabel, carouselEnabled } = props.modelValue;
  return JSON.stringify([tagIds, tagMatch, tagSort, tagLimit.value, tagHidePast, tagExcludeCurrent, tagShowDates, tagShowPrice, tagButtonLabel, carouselEnabled]);
});
let resolveTimer: ReturnType<typeof setTimeout> | undefined;
let resolveSeq = 0;
const resolveCards = async () => {
  const pageId = Number(route.params.id);
  if (!tagMode.value || !pageId) return;
  if (!selectedTagIds.value.length) {
    excluded.value = [];
    if (items.value.length) patch({ items: [] });
    return;
  }
  const seq = ++resolveSeq;
  resolving.value = true;
  resolveError.value = "";
  try {
    const { data } = await api.post<{ items: LinkCardItem[]; excluded: typeof excluded.value }>(`/pages/${pageId}/tag-cards`, {
      section: { ...props.modelValue, tagLimit: tagLimit.value, items: [], manualItems: undefined }
    });
    if (seq !== resolveSeq) return;
    excluded.value = data.excluded;
    // Só troca quando muda: abrir a seção não deve marcar "Alterações não salvas".
    if (JSON.stringify(data.items) !== JSON.stringify(items.value)) patch({ items: data.items });
  } catch (error) {
    if (seq === resolveSeq) resolveError.value = errorDetail(error, "Não deu para buscar os roteiros. Tente de novo.");
  } finally {
    if (seq === resolveSeq) resolving.value = false;
  }
};
watch(
  ruleKey,
  key => {
    if (!key) return;
    clearTimeout(resolveTimer);
    resolveTimer = setTimeout(resolveCards, 250);
  },
  { immediate: true }
);
onBeforeUnmount(() => clearTimeout(resolveTimer));

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
    image: hero.backgroundImage || page.cover_image_url || "",
    // Datas do Banner e menor preço (Preços ou Checkout) já vêm preenchidos; dá para mudar abaixo.
    ...pageCardPrefillFields(config)
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
  if (layout === "grid" && tagMode.value) {
    patch({ carouselEnabled: false, tagLimit: Math.min(tagLimit.value || 8, 8) });
    return;
  }
  if (layout === "grid" && items.value.length > 8) {
    layoutError.value = "A grade mostra até 8 links/roteiros. Remova alguns antes de trocar.";
    return;
  }
  patch({ carouselEnabled: layout !== "grid" });
};
</script>

<style scoped>
.fl-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.fl-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: var(--muted);
  color: var(--muted-foreground);
  font-size: 12.5px;
  font-weight: 600;
}
.fl-chip i {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--tag);
}
.fl-chip span {
  font-size: 11px;
  opacity: 0.75;
}
.fl-chip.on i {
  background: var(--tag-fg);
}
.fl-chip.on {
  border-color: var(--tag);
  background: var(--tag-bg);
  color: var(--tag-fg);
}
.fl-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--accent);
  color: var(--accent-foreground);
  font-size: 13px;
}
.fl-summary p {
  margin: 0;
}
.fl-out {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 12px;
}
.fl-out li {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}
.fl-out li span:last-child {
  opacity: 0.8;
  white-space: nowrap;
}
</style>
