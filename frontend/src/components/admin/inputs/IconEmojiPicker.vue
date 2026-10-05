<template>
  <div class="iep-root">
    <button
      ref="trigger"
      type="button"
      class="iep-trigger"
      :aria-label="triggerLabel"
      :title="triggerLabel"
      :aria-expanded="open"
      @click="toggle"
    >
      <TravelIcon v-if="mode === 'icon' && currentIcon" :name="currentIcon" :size="18" />
      <span v-else-if="mode === 'emoji' && modelValue && !currentIcon" class="iep-emoji">{{ modelValue }}</span>
      <span v-else class="iep-empty">+</span>
    </button>
    <Teleport to="body">
      <div v-if="open" ref="pop" class="iep-pop" :style="popStyle" role="dialog" :aria-label="mode === 'icon' ? 'Escolher ícone' : 'Escolher emoji'">
        <label class="iep-search">
          <SearchIcon aria-hidden="true" />
          <input ref="searchInput" v-model="query" type="search" :placeholder="mode === 'icon' ? 'Buscar ícone' : 'Buscar emoji: praia, avião…'" />
        </label>
        <div class="iep-cats" role="tablist">
          <button
            v-for="cat in categories"
            :key="cat.id"
            type="button"
            role="tab"
            :class="{ on: cat.id === activeCat && !query }"
            :aria-selected="cat.id === activeCat && !query"
            @click="activeCat = cat.id; query = ''"
          >
            {{ cat.label }}
          </button>
        </div>
        <div class="iep-grid-wrap">
          <p v-if="loading" class="iep-note">Carregando…</p>
          <p v-else-if="!visible.length" class="iep-note">Nada encontrado para “{{ query }}”.</p>
          <div v-else class="iep-grid" :class="{ 'is-emoji': mode === 'emoji' }">
            <button
              v-for="item in visible"
              :key="item.value"
              type="button"
              class="iep-opt"
              :class="{ on: item.value === modelValue }"
              :title="item.label"
              :aria-label="item.label"
              @click="pick(item.value)"
            >
              <TravelIcon v-if="mode === 'icon'" :name="item.value" :size="20" />
              <span v-else>{{ item.char }}</span>
            </button>
          </div>
          <button v-if="hasMore" type="button" class="iep-more" @click="limit += 240">Mostrar mais</button>
        </div>
        <div class="iep-foot">
          <span>{{ mode === "icon" ? "Ícones na cor de destaque da página" : "Emojis aparecem coloridos" }}</span>
          <button v-if="allowClear && modelValue" type="button" @click="pick('')">Remover</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { SearchIcon } from "lucide-vue-next";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from "vue";
import TravelIcon from "../../shared/TravelIcon.vue";
import { ICON_CATEGORIES, iconLabel, loadIconLibrary } from "../../../utils/iconLibrary";
import { ICON_PREFIX, TRAVEL_ICONS, iconValueName } from "../../../utils/travelIcons";

/**
 * Seletor de ícone OU emoji, conforme o modo da seção.
 * Ícones: "icon:<nome>" (biblioteca completa, com as categorias mais usadas primeiro).
 * Emojis: o próprio caractere (lista completa, com nomes em português).
 */
const props = withDefaults(defineProps<{ modelValue?: string | null; mode: "icon" | "emoji"; allowClear?: boolean }>(), {
  modelValue: "",
  allowClear: true
});
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();

interface Item {
  value: string;
  label: string;
  char?: string;
  search: string;
  cat: string;
}

const open = ref(false);
const query = ref("");
const activeCat = ref("");
const limit = ref(240);
const loading = ref(false);
const trigger = ref<HTMLElement | null>(null);
const pop = ref<HTMLElement | null>(null);
const searchInput = ref<HTMLInputElement | null>(null);
const popStyle = ref<Record<string, string>>({});

const currentIcon = computed(() => iconValueName(props.modelValue));
const triggerLabel = computed(() => {
  if (props.mode === "icon") return currentIcon.value ? `Ícone: ${iconLabel(currentIcon.value)}` : "Escolher ícone";
  return props.modelValue && !currentIcon.value ? `Emoji: ${props.modelValue}` : "Escolher emoji";
});

const normalize = (value: string) =>
  value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");

// Catálogos carregados sob demanda (arquivos separados), uma vez só.
const iconItems = shallowRef<Item[]>([]);
const emojiItems = shallowRef<Item[]>([]);
const emojiGroups = shallowRef<{ id: string; label: string }[]>([]);

const loadIcons = async () => {
  if (iconItems.value.length) return;
  const library = await loadIconLibrary();
  const featured: Item[] = ICON_CATEGORIES.flatMap(cat =>
    cat.icons.map(icon => ({ value: `${ICON_PREFIX}${icon.name}`, label: icon.label, search: normalize(`${icon.label} ${icon.name}`), cat: cat.label }))
  );
  const basics: Item[] = Object.entries(TRAVEL_ICONS).map(([key, icon]) => ({
    value: `${ICON_PREFIX}${key}`,
    label: icon.label,
    search: normalize(`${icon.label} ${key}`),
    cat: "Básicos"
  }));
  const all: Item[] = Object.keys(library).map(name => ({ value: `${ICON_PREFIX}${name}`, label: iconLabel(name), search: normalize(`${iconLabel(name)} ${name}`), cat: "Todos" }));
  iconItems.value = [...basics, ...featured, ...all];
};

const loadEmojis = async () => {
  if (emojiItems.value.length) return;
  const [data, messages] = await Promise.all([import("emojibase-data/pt/compact.json"), import("emojibase-data/pt/messages.json")]);
  const list = ((data as any).default || data) as { unicode: string; label: string; tags?: string[]; group?: number; order?: number }[];
  const groups = (((messages as any).default || messages).groups || []) as { key: string; message: string; order: number }[];
  // Sem "componentes" (tons de pele soltos) e sem as letras de bandeira.
  const groupLabel = new Map(groups.filter(group => group.key !== "component").map(group => [group.order, group.message]));
  emojiGroups.value = groups
    .filter(group => group.key !== "component")
    // A tradução do pacote chama "flags" de "comutadores".
    .map(group => ({ id: String(group.order), label: group.key === "flags" ? "Bandeiras" : group.message.charAt(0).toUpperCase() + group.message.slice(1) }));
  emojiItems.value = list
    .filter(emoji => typeof emoji.group === "number" && groupLabel.has(emoji.group))
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
    .map(emoji => ({
      value: emoji.unicode,
      char: emoji.unicode,
      label: emoji.label,
      search: normalize(`${emoji.label} ${(emoji.tags || []).join(" ")}`),
      cat: String(emoji.group)
    }));
};

const categories = computed(() =>
  props.mode === "icon"
    ? [{ id: "Básicos", label: "Básicos" }, ...ICON_CATEGORIES.map(cat => ({ id: cat.label, label: cat.label })), { id: "Todos", label: "Todos" }]
    : emojiGroups.value
);

const filtered = computed(() => {
  const items = props.mode === "icon" ? iconItems.value : emojiItems.value;
  const q = normalize(query.value.trim());
  if (q) {
    const seen = new Set<string>();
    return items.filter(item => item.search.includes(q) && !seen.has(item.value) && seen.add(item.value));
  }
  return items.filter(item => item.cat === activeCat.value);
});
const visible = computed(() => filtered.value.slice(0, limit.value));
const hasMore = computed(() => filtered.value.length > limit.value);
watch([query, activeCat], () => {
  limit.value = 240;
});

const place = () => {
  const rect = trigger.value?.getBoundingClientRect();
  if (!rect) return;
  const width = 352;
  const height = 420;
  const left = Math.max(8, Math.min(rect.left, window.innerWidth - width - 8));
  const below = rect.bottom + 6 + height < window.innerHeight;
  const top = below ? rect.bottom + 6 : Math.max(8, rect.top - height - 6);
  popStyle.value = { left: `${left}px`, top: `${top}px`, width: `${width}px`, height: `${height}px` };
};

const toggle = async () => {
  if (open.value) {
    open.value = false;
    return;
  }
  place();
  open.value = true;
  query.value = "";
  loading.value = true;
  try {
    if (props.mode === "icon") {
      await loadIcons();
      activeCat.value = "Básicos";
    } else {
      await loadEmojis();
      activeCat.value = emojiGroups.value.find(group => group.label.toLowerCase().startsWith("viage"))?.id || emojiGroups.value[0]?.id || "";
    }
  } finally {
    loading.value = false;
  }
  nextTick(() => searchInput.value?.focus());
};

const pick = (value: string) => {
  emit("update:modelValue", value);
  open.value = false;
};

const onDocDown = (event: MouseEvent) => {
  const target = event.target as Node;
  if (open.value && !pop.value?.contains(target) && !trigger.value?.contains(target)) open.value = false;
};
const onKey = (event: KeyboardEvent) => {
  if (event.key === "Escape") open.value = false;
};
// Se a área que contém o botão rolar, a janela acompanha o botão.
const onScroll = (event: Event) => {
  const target = event.target;
  if (!open.value || !trigger.value) return;
  if (target === document || (target instanceof Node && target.contains(trigger.value))) place();
};
onMounted(() => {
  document.addEventListener("mousedown", onDocDown);
  document.addEventListener("keydown", onKey);
  window.addEventListener("scroll", onScroll, true);
});
onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocDown);
  document.removeEventListener("keydown", onKey);
  window.removeEventListener("scroll", onScroll, true);
});
</script>

<style scoped>
.iep-root {
  display: inline-flex;
}
.iep-trigger {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--muted);
  box-shadow: inset 0 0 0 1px var(--border);
  color: var(--primary);
}
.iep-trigger:hover {
  box-shadow: inset 0 0 0 1.5px var(--ring);
}
.iep-emoji {
  font-size: 22px;
  line-height: 1;
}
.iep-empty {
  font-size: 20px;
  font-weight: 600;
  color: var(--muted-foreground);
}
.iep-pop {
  position: fixed;
  z-index: 200;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 16px;
  background: var(--popover, var(--card));
  color: var(--foreground);
  box-shadow: 0 0 0 1px var(--border), 0 24px 60px -24px rgba(6, 12, 9, 0.55);
  font-family: Figtree, sans-serif;
}
.iep-search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 10px 6px;
  padding: 0 10px;
  border-radius: 10px;
  background: var(--muted);
}
.iep-search svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--muted-foreground);
}
.iep-search input {
  flex: 1;
  min-width: 0;
  height: 38px;
  border: 0;
  background: transparent !important;
  color: var(--foreground);
  font: inherit;
  font-size: 14px;
  outline: none;
}
.iep-cats {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding: 0 10px 8px;
  border-bottom: 1px solid var(--border);
  scrollbar-width: none;
}
.iep-cats button {
  flex-shrink: 0;
  height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--muted);
  font-size: 12px;
  font-weight: 600;
  color: var(--muted-foreground);
}
.iep-cats button.on {
  background: var(--foreground);
  color: var(--background);
}
.iep-grid-wrap {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 10px;
}
.iep-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 2px;
}
.iep-opt {
  display: grid;
  aspect-ratio: 1;
  place-items: center;
  border-radius: 9px;
  color: var(--foreground);
}
.iep-grid.is-emoji .iep-opt {
  font-size: 22px;
  line-height: 1;
}
.iep-opt:hover {
  background: var(--muted);
}
.iep-opt.on {
  background: var(--primary);
  color: var(--primary-foreground);
}
.iep-more {
  width: 100%;
  margin-top: 8px;
  height: 34px;
  border-radius: 10px;
  background: var(--muted);
  font-size: 13px;
  font-weight: 600;
}
.iep-note {
  margin: 24px 0;
  text-align: center;
  font-size: 13px;
  color: var(--muted-foreground);
}
.iep-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: var(--muted-foreground);
}
.iep-foot button {
  font-weight: 700;
  color: #dc2626;
}
</style>
