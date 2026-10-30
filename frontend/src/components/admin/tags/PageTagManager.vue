<template>
  <Teleport to="body">
    <div v-if="open" class="ptm-bg" @click="$emit('close')"></div>
    <aside v-if="open" class="ptm" role="dialog" aria-modal="true" aria-labelledby="ptm-title" @keydown.esc="$emit('close')">
      <header class="ptm-head">
        <div class="ptm-grow">
          <h2 id="ptm-title">Tags</h2>
          <p>Organizam a lista de páginas e alimentam as seções Links/Roteiros por tag. Valem para toda a agência.</p>
        </div>
        <button ref="closeRef" type="button" class="ptm-icon" aria-label="Fechar" @click="$emit('close')"><XIcon aria-hidden="true" /></button>
      </header>
      <div class="ptm-body">
        <div class="ptm-list">
          <label class="ptm-search">
            <SearchIcon aria-hidden="true" />
            <input v-model="search" type="text" placeholder="Buscar tag" autocomplete="off" aria-label="Buscar tag" />
          </label>
          <div class="ptm-rows">
            <button
              v-for="tag in visibleTags"
              :key="tag.id"
              type="button"
              class="ptm-row"
              :class="{ on: selected?.id === tag.id }"
              :style="tagStyle(tag.color)"
              :aria-current="selected?.id === tag.id"
              @click="select(tag.id)"
            >
              <i aria-hidden="true"></i>{{ tag.name }}<span>{{ tag.page_count }}</span>
            </button>
            <p v-if="!visibleTags.length" class="ptm-muted">{{ tags.length ? "Nenhuma tag com esse nome." : "Nenhuma tag ainda." }}</p>
          </div>
          <form v-if="canEdit" class="ptm-new" @submit.prevent="createTag">
            <input v-model="newName" type="text" maxlength="60" placeholder="Nova tag" aria-label="Nome da nova tag" autocomplete="off" />
            <button type="submit" :disabled="!newName.trim() || busy"><PlusIcon aria-hidden="true" />Criar</button>
          </form>
        </div>

        <div v-if="selected" class="ptm-detail">
          <section class="ptm-sec">
            <h3>Nome</h3>
            <input
              v-model="nameDraft"
              class="ptm-name"
              type="text"
              maxlength="60"
              aria-label="Nome da tag"
              :disabled="!canEdit"
              @keydown.enter.prevent="saveName"
              @blur="saveName"
            />
          </section>
          <section class="ptm-sec">
            <h3>Cor</h3>
            <div class="ptm-swatches" role="radiogroup" aria-label="Cor da tag">
              <button
                v-for="color in TAG_COLORS"
                :key="color.value"
                type="button"
                role="radio"
                class="ptm-swatch"
                :class="{ on: selected.color === color.value }"
                :style="tagStyle(color.value)"
                :aria-checked="selected.color === color.value"
                :aria-label="color.label"
                :title="color.label"
                :disabled="!canEdit"
                @click="setColor(color.value)"
              >
                <CheckIcon v-if="selected.color === color.value" aria-hidden="true" />
              </button>
            </div>
            <p class="ptm-muted">Fica assim: <span class="page-tag" :style="tagStyle(selected.color)">{{ selected.name }}</span></p>
          </section>
          <section class="ptm-sec">
            <h3>Páginas com esta tag <span>{{ pagesWithTag.length }}</span></h3>
            <div class="ptm-box">
              <div v-for="page in pagesWithTag" :key="page.id" class="ptm-page">
                <span class="ptm-page-info">
                  <b>{{ page.title }}</b>
                  <small>{{ page.status === "published" ? "Publicada" : "Rascunho" }}</small>
                </span>
                <button
                  v-if="canEdit"
                  type="button"
                  class="ptm-icon"
                  :aria-label="`Tirar ${selected.name} de ${page.title}`"
                  title="Tirar a tag desta página"
                  :disabled="busy"
                  @click="togglePage(page.id, false)"
                >
                  <XIcon aria-hidden="true" />
                </button>
              </div>
              <p v-if="!pagesWithTag.length" class="ptm-muted ptm-pad">Nenhuma página com esta tag.</p>
            </div>
            <select v-if="canEdit && pagesWithoutTag.length" class="ptm-select" :disabled="busy" aria-label="Adicionar página a esta tag" @change="onAddPage">
              <option value="">+ Adicionar página…</option>
              <option v-for="page in pagesWithoutTag" :key="page.id" :value="page.id">{{ page.title }}</option>
            </select>
          </section>
          <section class="ptm-sec">
            <h3>Seções que mostram esta tag <span>{{ selected.sections.length }}</span></h3>
            <div v-if="selected.sections.length" class="ptm-box">
              <div v-for="use in selected.sections" :key="use.page_id" class="ptm-page">
                <span class="ptm-page-info"><b>Links/Roteiros</b><small>em {{ use.page_title }}</small></span>
              </div>
            </div>
            <p v-else class="ptm-muted">Nenhuma seção Links/Roteiros usa esta tag.</p>
          </section>

          <div v-if="confirm === 'delete'" class="ptm-confirm" role="alert">
            <p>
              Apagar a tag <b>{{ selected.name }}</b>? Ela sai de {{ plural(selected.page_count, "página", "páginas") }}; as páginas continuam iguais.
              <template v-if="selected.sections.length">
                <b>{{ plural(selected.sections.length, "seção por tag perde", "seções por tag perdem") }} esses roteiros</b>:
                {{ selected.sections.map(use => use.page_title).join(", ") }}.
              </template>
            </p>
            <div class="ptm-acts">
              <button type="button" class="ptm-btn" @click="confirm = null">Cancelar</button>
              <button type="button" class="ptm-btn is-danger" :disabled="busy" @click="deleteTag">Apagar tag</button>
            </div>
          </div>
          <div v-else-if="confirm === 'merge'" class="ptm-confirm">
            <p>
              Juntar <b>{{ selected.name }}</b> com outra tag. As páginas passam para a tag escolhida e <b>{{ selected.name }}</b> deixa de existir.
              Seções que usavam <b>{{ selected.name }}</b> passam a usar a nova.
            </p>
            <select v-model="mergeTarget" class="ptm-select" aria-label="Juntar com">
              <option :value="null">Escolha a tag que fica…</option>
              <option v-for="tag in otherTags" :key="tag.id" :value="tag.id">{{ tag.name }} ({{ plural(tag.page_count, "página", "páginas") }})</option>
            </select>
            <div class="ptm-acts">
              <button type="button" class="ptm-btn" @click="confirm = null">Cancelar</button>
              <button type="button" class="ptm-btn is-primary" :disabled="!mergeTarget || busy" @click="mergeTag">
                {{ mergeTargetTag ? `Juntar em ${mergeTargetTag.name}` : "Juntar" }}
              </button>
            </div>
          </div>
          <p v-if="error" class="ptm-error" role="alert">{{ error }}</p>
          <div v-if="canEdit" class="ptm-danger">
            <button type="button" class="ptm-btn" :disabled="!otherTags.length" @click="openConfirm('merge')"><MergeIcon aria-hidden="true" />Juntar com outra tag</button>
            <button type="button" class="ptm-btn is-danger-text" @click="openConfirm('delete')"><Trash2Icon aria-hidden="true" />Apagar tag</button>
          </div>
        </div>
        <div v-else class="ptm-detail">
          <p class="ptm-muted">{{ tags.length ? "Escolha uma tag na lista." : "Crie a primeira tag para começar. Ex.: Europa, Nordeste, Lua de mel." }}</p>
        </div>
      </div>
    </aside>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { CheckIcon, MergeIcon, PlusIcon, SearchIcon, Trash2Icon, XIcon } from "lucide-vue-next";
import { errorDetail, usePageTags } from "../../../composables/usePageTags";
import { TAG_COLORS, slugifyTag, tagStyle, type PageTagBrief, type TagColor } from "../../../types/pageTag";

interface TaggedPage {
  id: number;
  title: string;
  status: string;
  tags?: PageTagBrief[];
}

const props = withDefaults(
  defineProps<{ open: boolean; agencyId: number | null | undefined; pages: TaggedPage[]; canEdit?: boolean; initialTagId?: number | null }>(),
  { canEdit: true, initialTagId: null }
);
const emit = defineEmits<{ (e: "close"): void; (e: "pages-changed"): void }>();

const { tags, load, reload, create, update, remove, merge, bulk } = usePageTags();
const search = ref("");
const selectedId = ref<number | null>(null);
const nameDraft = ref("");
const newName = ref("");
const confirm = ref<"delete" | "merge" | null>(null);
const mergeTarget = ref<number | null>(null);
const busy = ref(false);
const error = ref("");
const closeRef = ref<HTMLButtonElement | null>(null);

const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`;
const visibleTags = computed(() => {
  const term = slugifyTag(search.value);
  return tags.value.filter(tag => !term || slugifyTag(tag.name).includes(term));
});
const selected = computed(() => tags.value.find(tag => tag.id === selectedId.value) || null);
const otherTags = computed(() => tags.value.filter(tag => tag.id !== selectedId.value));
const mergeTargetTag = computed(() => tags.value.find(tag => tag.id === mergeTarget.value) || null);
const pagesWithTag = computed(() => props.pages.filter(page => page.tags?.some(tag => tag.id === selectedId.value)));
const pagesWithoutTag = computed(() => props.pages.filter(page => !page.tags?.some(tag => tag.id === selectedId.value)));

const select = (id: number | null) => {
  selectedId.value = id;
  confirm.value = null;
  error.value = "";
};
watch(selected, tag => (nameDraft.value = tag?.name || ""), { immediate: true });
watch(
  () => props.open,
  async isOpen => {
    if (!isOpen) return;
    search.value = "";
    confirm.value = null;
    error.value = "";
    await load(props.agencyId);
    void reload();
    select(props.initialTagId && tags.value.some(tag => tag.id === props.initialTagId) ? props.initialTagId : tags.value[0]?.id ?? null);
    await nextTick();
    closeRef.value?.focus();
  },
  { immediate: true }
);
watch(tags, list => {
  if (selectedId.value && !list.some(tag => tag.id === selectedId.value)) select(list[0]?.id ?? null);
});

const run = async (action: () => Promise<unknown>, fallback: string) => {
  busy.value = true;
  error.value = "";
  try {
    await action();
    return true;
  } catch (err) {
    error.value = errorDetail(err, fallback);
    return false;
  } finally {
    busy.value = false;
  }
};

const createTag = async () => {
  if (!props.agencyId || !newName.value.trim()) return;
  await run(async () => {
    const tag = await create(props.agencyId as number, newName.value.trim());
    newName.value = "";
    search.value = "";
    select(tag.id);
  }, "Não deu para criar a tag.");
};
const saveName = async () => {
  const tag = selected.value;
  const name = nameDraft.value.trim();
  if (!tag || !name || name === tag.name) {
    nameDraft.value = tag?.name || "";
    return;
  }
  const ok = await run(() => update(tag.id, { name }), "Não deu para renomear a tag.");
  if (ok) emit("pages-changed");
  else nameDraft.value = tag.name;
};
const setColor = async (color: TagColor) => {
  const tag = selected.value;
  if (!tag || tag.color === color) return;
  if (await run(() => update(tag.id, { color }), "Não deu para trocar a cor.")) emit("pages-changed");
};
const togglePage = async (pageId: number, add: boolean) => {
  const tag = selected.value;
  if (!tag || !props.agencyId) return;
  const ok = await run(
    () => bulk(props.agencyId as number, [pageId], add ? [tag.id] : [], add ? [] : [tag.id]),
    "Não deu para mudar a tag da página."
  );
  if (ok) emit("pages-changed");
};
const onAddPage = (event: Event) => {
  const select = event.target as HTMLSelectElement;
  const pageId = Number(select.value);
  select.value = "";
  if (pageId) void togglePage(pageId, true);
};
const openConfirm = (kind: "delete" | "merge") => {
  confirm.value = kind;
  mergeTarget.value = null;
  error.value = "";
};
const deleteTag = async () => {
  const tag = selected.value;
  if (!tag) return;
  if (await run(() => remove(tag.id), "Não deu para apagar a tag.")) {
    confirm.value = null;
    emit("pages-changed");
  }
};
const mergeTag = async () => {
  const tag = selected.value;
  if (!tag || !mergeTarget.value) return;
  const target = mergeTarget.value;
  if (await run(() => merge(tag.id, target), "Não deu para juntar as tags.")) {
    confirm.value = null;
    select(target);
    emit("pages-changed");
  }
};
</script>

<style scoped>
.ptm-bg {
  position: fixed;
  inset: 0;
  z-index: 70;
  background: var(--modal-overlay, rgba(0, 0, 0, 0.5));
}
.ptm {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 71;
  display: flex;
  flex-direction: column;
  width: min(780px, 100%);
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: var(--background);
  color: var(--foreground);
  box-shadow: -12px 0 32px rgba(0, 0, 0, 0.18);
}
.ptm-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--card);
}
.ptm-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 600;
}
.ptm-head p {
  margin: 2px 0 0;
  font-size: 12.5px;
  color: var(--muted-foreground);
}
.ptm-grow {
  flex: 1;
  min-width: 0;
}
.ptm-body {
  display: grid;
  flex: 1;
  grid-template-columns: 250px minmax(0, 1fr);
  min-height: 0;
}
.ptm-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  overflow: auto;
  border-right: 1px solid var(--border);
  background: var(--card);
}
.ptm-search {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 12px;
  border-radius: 10px;
  background: var(--muted);
  color: var(--muted-foreground);
}
.ptm-search svg {
  width: 14px;
  height: 14px;
}
.ptm-search input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 13px;
  color: var(--foreground);
}
.ptm-rows {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ptm-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 10px;
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 500;
  text-align: left;
}
.ptm-row:hover {
  background: var(--muted);
}
.ptm-row.on {
  background: var(--tag-bg);
  color: var(--tag-fg);
  font-weight: 600;
}
.ptm-row i {
  width: 10px;
  height: 10px;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--tag-fg);
}
.ptm-row span {
  margin-left: auto;
  font-size: 12px;
  opacity: 0.75;
  font-variant-numeric: tabular-nums;
}
.ptm-new {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}
.ptm-new input {
  flex: 1;
  min-width: 0;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--background);
  font-size: 13px;
}
.ptm-new button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 34px;
  padding: 0 12px;
  border-radius: 9px;
  background: var(--primary);
  color: var(--primary-foreground);
  font-size: 12.5px;
  font-weight: 600;
}
.ptm-new button:disabled {
  opacity: 0.5;
}
.ptm-new svg {
  width: 14px;
  height: 14px;
}
.ptm-detail {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px;
  overflow: auto;
}
.ptm-sec {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ptm-sec h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted-foreground);
}
.ptm-name {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--card);
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
}
.ptm-swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.ptm-swatch {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 2px solid var(--tag-fg);
  border-radius: 999px;
  background: var(--tag-bg);
  color: var(--tag-fg);
}
.ptm-swatch.on {
  box-shadow: 0 0 0 3px var(--background), 0 0 0 5px var(--tag-fg);
}
.ptm-swatch svg {
  width: 15px;
  height: 15px;
}
.ptm-box {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--card);
}
.ptm-page {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px 8px 12px;
  border-top: 1px solid var(--border);
  font-size: 13px;
}
.ptm-page:first-child {
  border-top: 0;
}
.ptm-page-info {
  flex: 1;
  min-width: 0;
}
.ptm-page-info b {
  display: block;
  overflow: hidden;
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.ptm-page-info small {
  font-size: 11.5px;
  color: var(--muted-foreground);
}
.ptm-select {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--card);
  font-size: 13px;
}
.ptm-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 999px;
  color: var(--muted-foreground);
}
.ptm-icon:hover {
  background: var(--muted);
  color: var(--foreground);
}
.ptm-icon svg {
  width: 16px;
  height: 16px;
}
.ptm-muted {
  margin: 0;
  font-size: 12.5px;
  color: var(--muted-foreground);
}
.ptm-pad {
  padding: 14px;
}
.ptm-confirm {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--status-warning, #fff7e6);
  color: var(--status-warning-foreground, #8a4b06);
  font-size: 13px;
}
.ptm-confirm p {
  margin: 0;
}
.ptm-acts {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}
.ptm-danger {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.ptm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--card);
  color: var(--foreground);
  font-size: 12.5px;
  font-weight: 600;
}
.ptm-btn:disabled {
  opacity: 0.5;
}
.ptm-btn svg {
  width: 14px;
  height: 14px;
}
.ptm-btn.is-primary {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-foreground);
}
.ptm-btn.is-danger {
  border-color: #dc2626;
  background: #dc2626;
  color: #fff;
}
.ptm-btn.is-danger-text {
  color: #dc2626;
}
.ptm-error {
  margin: 0;
  font-size: 12.5px;
  color: #dc2626;
}
@media (max-width: 640px) {
  .ptm-body {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto 1fr;
    overflow: auto;
  }
  .ptm-list {
    overflow: visible;
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }
  .ptm-rows {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }
  .ptm-row {
    width: auto;
    padding: 7px 10px;
    background: var(--muted);
  }
  .ptm-detail {
    overflow: visible;
  }
}
</style>
