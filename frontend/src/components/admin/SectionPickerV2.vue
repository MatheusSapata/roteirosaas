<template>
  <Teleport to="body">
    <div class="spk-overlay" @click.self="emit('close')">
      <div class="spk" role="dialog" aria-modal="true" aria-labelledby="spk-title" :style="{ '--thumb-accent': accent }" @keydown.esc="emit('close')">
        <header class="spk-head">
          <div class="spk-head-row">
            <div class="spk-titles">
              <h2 id="spk-title">Adicionar seção</h2>
              <p>
                <template v-if="afterLabel">Entra logo abaixo de <b>{{ afterLabel }}</b></template>
                <template v-else>Entra no fim da página</template>
              </p>
            </div>
            <button type="button" class="spk-close" aria-label="Fechar" @click="emit('close')">
              <XIcon aria-hidden="true" />
            </button>
          </div>
          <label class="spk-search" :class="{ 'has-q': query }">
            <SearchIcon aria-hidden="true" />
            <span class="sr-only">Buscar seção</span>
            <input ref="searchRef" v-model="query" type="search" placeholder="Buscar seção: preço, vídeo, contato…" autocomplete="off" />
            <button v-if="query" type="button" class="spk-search-clear" aria-label="Limpar busca" @click="query = ''">
              <XIcon aria-hidden="true" />
            </button>
          </label>
          <div class="spk-chips" role="tablist" aria-label="Categorias">
            <button
              v-for="chip in chips"
              :key="chip.id"
              type="button"
              role="tab"
              class="spk-chip"
              :class="{ on: category === chip.id }"
              :aria-selected="category === chip.id"
              @click="category = chip.id"
            >
              {{ chip.label }}
              <span>{{ chip.count }}</span>
            </button>
          </div>
        </header>

        <div class="spk-body">
          <div v-if="!groups.length" class="spk-empty">
            <b>Nenhuma seção para “{{ query }}”</b>
            <span>Tente “preço”, “vídeo” ou “contato”.</span>
          </div>
          <section v-for="group in groups" :key="group.id" class="spk-group">
            <div class="spk-group-head">
              <h3>{{ group.label }}</h3>
              <span>{{ group.hint }}</span>
            </div>
            <div class="spk-grid">
              <button
                v-for="item in group.items"
                :key="item.type"
                type="button"
                class="spk-card"
                :class="{ 'is-locked': item.locked, 'is-off': item.unavailable }"
                :disabled="item.unavailable"
                :title="item.unavailable ? 'A página já tem esta seção' : undefined"
                @click="pick(item)"
              >
                <span class="spk-thumb" aria-hidden="true">
                  <SectionThumbV2 :type="item.type" />
                  <span v-if="item.locked" class="spk-lock"><span>Conecte o Viaje On</span></span>
                  <span class="spk-go">{{ item.unavailable ? "Já na página" : item.locked ? "Integrar" : "Inserir" }}</span>
                </span>
                <span class="spk-card-text">
                  <b>{{ item.label }}</b>
                  <span>{{ item.desc }}</span>
                  <em v-if="item.unavailable || item.locked" class="spk-note">{{ item.unavailable ? "Já está na página" : "Conecte o Viaje On para usar" }}</em>
                </span>
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { SearchIcon, XIcon } from "lucide-vue-next";
import { computed, nextTick, onMounted, ref } from "vue";
import type { SectionType } from "../../types/page";
import { SECTION_CATALOG_V2, SECTION_CATEGORIES_V2, type SectionCatalogItemV2 } from "../../utils/sectionCatalogV2";
import SectionThumbV2 from "./SectionThumbV2.vue";

const props = defineProps<{
  afterLabel?: string;
  /** Tipos que o editor sabe criar; os demais ficam fora da lista. */
  types?: SectionType[];
  /** Tipos que não podem entrar de novo (ex.: o Menu do topo já existe). */
  unavailable?: SectionType[];
  viajeonConnected?: boolean;
  accent?: string;
}>();
const emit = defineEmits<{ (e: "select", type: SectionType): void; (e: "close"): void; (e: "integrate"): void }>();

const query = ref("");
const category = ref<string>("todas");
const searchRef = ref<HTMLInputElement | null>(null);

const normalize = (value: string) =>
  value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");

type PickerItem = SectionCatalogItemV2 & { locked: boolean; unavailable: boolean };

const matched = computed<PickerItem[]>(() => {
  const q = normalize(query.value.trim());
  return SECTION_CATALOG_V2.filter(item => !props.types || props.types.includes(item.type))
    .filter(item => !q || normalize(`${item.label} ${item.keywords} ${item.desc}`).includes(q)).map(item => ({
    ...item,
    locked: item.type === "viajeon_checkout" && !props.viajeonConnected,
    unavailable: !!props.unavailable?.includes(item.type)
  }));
});

const chips = computed(() =>
  [{ id: "todas", label: "Todas" }, ...SECTION_CATEGORIES_V2].map(chip => ({
    id: chip.id,
    label: chip.label,
    count: matched.value.filter(item => chip.id === "todas" || item.cat === chip.id).length
  }))
);

const groups = computed(() =>
  SECTION_CATEGORIES_V2.map(cat => ({
    id: cat.id,
    label: cat.label,
    hint: cat.hint,
    items: matched.value.filter(item => item.cat === cat.id && (category.value === "todas" || category.value === cat.id))
  })).filter(group => group.items.length)
);

const pick = (item: PickerItem) => {
  if (item.unavailable) return;
  if (item.locked) {
    emit("integrate");
    return;
  }
  emit("select", item.type);
};

// Só no computador a busca já abre com o cursor: no celular o teclado subiria por cima da lista.
onMounted(() => {
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
  nextTick(() => searchRef.value?.focus());
});
</script>

<style scoped>
.spk-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background: rgba(9, 14, 12, 0.55);
}
.spk {
  display: flex;
  width: 100%;
  max-width: 1080px;
  height: min(860px, 100%);
  flex-direction: column;
  overflow: hidden;
  border-radius: 24px;
  background: #fff;
  color: #0f1713;
  font-family: Figtree, sans-serif;
  box-shadow: 0 40px 100px -30px rgba(6, 12, 9, 0.6);
}
.spk-head {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 22px 24px 14px;
  border-bottom: 1px solid #e3e8e2;
}
.spk-head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.spk-titles h2 {
  margin: 0;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.spk-titles p {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 4px 0 0;
  font-size: 14px;
  color: #5b6761;
}
.spk-titles b {
  display: inline-flex;
  padding: 2px 10px;
  border-radius: 999px;
  background: #f1f4f0;
  color: #0f1713;
  font-weight: 700;
}
.spk-close {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 999px;
  background: #f1f4f0;
  color: #0f1713;
}
.spk-close:hover {
  background: #e3e8e2;
}
.spk-close svg {
  width: 20px;
  height: 20px;
}
.spk-search {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px 0 16px;
  border-radius: 14px;
  background: #f4f6f2;
  box-shadow: inset 0 0 0 1.5px transparent;
  transition: box-shadow 0.15s ease;
}
.spk-search:focus-within,
.spk-search.has-q {
  box-shadow: inset 0 0 0 1.5px var(--thumb-accent, #12b981);
}
.spk-search > svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #7a857f;
}
.spk-search input {
  flex: 1;
  min-width: 0;
  height: 46px;
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 15px;
  color: #0f1713;
  outline: none;
}
.spk-search input::-webkit-search-cancel-button {
  display: none;
}
.spk-search-clear {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: #e3e8e2;
}
.spk-search-clear svg {
  width: 14px;
  height: 14px;
}
.spk-chips {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}
.spk-chip {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 8px 0 14px;
  border-radius: 999px;
  background: #f1f4f0;
  color: #0f1713;
  font-size: 14px;
  font-weight: 600;
  transition: background-color 0.15s ease;
}
.spk-chip span {
  min-width: 22px;
  padding: 1px 7px;
  border-radius: 999px;
  background: #e3e8e2;
  font-size: 12px;
  font-weight: 700;
}
.spk-chip.on {
  background: #0f1713;
  color: #fff;
}
.spk-chip.on span {
  background: rgba(255, 255, 255, 0.18);
}
.spk-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 24px 28px;
  background: #fafbf9;
}
.spk-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 64px 16px;
  text-align: center;
  color: #5b6761;
}
.spk-empty b {
  font-size: 16px;
  color: #0f1713;
}
.spk-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 20px;
}
.spk-group-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.spk-group-head h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}
.spk-group-head span {
  font-size: 13px;
  color: #7a857f;
}
.spk-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 228px), 1fr));
  gap: 14px;
}
.spk-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
  border-radius: 16px;
  background: #fff;
  text-align: left;
  box-shadow: 0 0 0 1px #e3e8e2;
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}
.spk-card:hover:not(:disabled),
.spk-card:focus-visible {
  box-shadow: 0 0 0 2px var(--thumb-accent, #12b981), 0 18px 36px -20px rgba(6, 12, 9, 0.45);
  transform: translateY(-2px);
  outline: none;
}
.spk-card.is-off {
  cursor: not-allowed;
  opacity: 0.55;
}
.spk-thumb {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  border-bottom: 1px solid #eef1ec;
}
.spk-lock {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(9, 14, 12, 0.55);
}
.spk-lock span {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: #fff;
  font-size: 12px;
  font-weight: 700;
}
.spk-go {
  position: absolute;
  right: 10px;
  bottom: 10px;
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: #0f1713;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  opacity: 0;
  transform: translateY(4px);
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.spk-card:hover .spk-go,
.spk-card:focus-visible .spk-go,
.spk-card.is-locked .spk-go {
  opacity: 1;
  transform: none;
}
.spk-card-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 12px 14px 14px;
}
.spk-card-text b {
  font-size: 15px;
  font-weight: 700;
}
.spk-card-text span {
  font-size: 13px;
  line-height: 1.4;
  color: #5b6761;
}
.spk-note {
  display: none;
}
/* Celular: lista de uma coluna, com a miniatura à esquerda e título e descrição à direita.
   A miniatura é a própria seção reduzida, então fica pequena e inteira ao lado do texto. */
@media (max-width: 640px) {
  .spk-overlay {
    padding: 0;
  }
  .spk {
    height: 100%;
    border-radius: 0;
  }
  .spk-head {
    padding: 16px 16px 12px;
  }
  .spk-body {
    padding: 4px 16px 24px;
  }
  .spk-group {
    gap: 8px;
    padding-top: 18px;
  }
  .spk-group-head {
    flex-direction: column;
    gap: 0;
  }
  .spk-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }
  .spk-card {
    flex-direction: row;
    align-items: center;
    gap: 12px;
    min-height: 92px;
    padding: 8px 12px 8px 8px;
    border-radius: 16px;
  }
  .spk-card:hover:not(:disabled),
  .spk-card:focus-visible {
    transform: none;
  }
  .spk-card:active:not(:disabled) {
    box-shadow: 0 0 0 2px var(--thumb-accent, #12b981);
  }
  .spk-thumb {
    flex: none;
    width: 120px;
    aspect-ratio: 4 / 3;
    border-bottom: 0;
    border-radius: 10px;
    box-shadow: inset 0 0 0 1px #e9ede8;
  }
  .spk-go,
  .spk-lock span {
    display: none;
  }
  .spk-card-text {
    min-width: 0;
    flex: 1;
    gap: 2px;
    padding: 0;
  }
  .spk-card-text b {
    font-size: 15px;
    line-height: 1.25;
  }
  .spk-card-text span {
    display: -webkit-box;
    overflow: hidden;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    font-size: 13px;
    line-height: 1.35;
  }
  .spk-note {
    display: inline-flex;
    align-self: flex-start;
    margin-top: 4px;
    padding: 2px 8px;
    border-radius: 999px;
    background: #f1f4f0;
    font-size: 11.5px;
    font-style: normal;
    font-weight: 700;
    color: #3d4842;
  }
  .spk-card.is-locked .spk-note {
    background: #fff4e5;
    color: #8a4b08;
  }
}
@media (prefers-reduced-motion: reduce) {
  .spk-card,
  .spk-go {
    transition: none;
  }
}
</style>
