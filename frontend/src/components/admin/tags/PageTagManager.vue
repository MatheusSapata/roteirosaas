<template>
  <Teleport to="body">
    <div v-if="open" class="app-modal-overlay fixed inset-0 z-[170] flex items-center justify-center px-4" @click.self="close">
      <div class="tag-modal-shell w-full max-w-lg p-6" role="dialog" aria-modal="true" aria-labelledby="tag-modal-title" @keydown.esc="close">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="tag-modal-eyebrow">Tags</p>
            <h3 id="tag-modal-title" class="mt-2 text-2xl font-bold">{{ editing ? (editing.id ? "Editar tag" : "Nova tag") : "Gerenciar tags" }}</h3>
            <p v-if="!editing" class="tag-modal-hint">Organizam a lista de páginas e as seções Links/Roteiros por tag.</p>
          </div>
          <button ref="closeRef" type="button" class="tag-modal-close" aria-label="Fechar" @click="close">
            <XIcon class="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <!-- Formulário: criar ou editar -->
        <form v-if="editing" class="mt-5 grid gap-4" @submit.prevent="save">
          <label class="block">
            <span class="tag-modal-label">Nome da tag</span>
            <input
              ref="nameRef"
              v-model="editing.name"
              type="text"
              maxlength="60"
              placeholder="Ex: Europa"
              class="tag-modal-input mt-2 w-full px-4 py-2.5 text-sm outline-none transition"
            />
          </label>
          <div>
            <span class="tag-modal-label">Cor</span>
            <div class="mt-2 flex flex-wrap gap-2" role="radiogroup" aria-label="Cor da tag">
              <button
                v-for="color in TAG_COLORS"
                :key="color.value"
                type="button"
                role="radio"
                class="tag-swatch"
                :class="{ 'is-on': editing.color === color.value }"
                :style="tagStyle(color.value)"
                :aria-checked="editing.color === color.value"
                :aria-label="color.label"
                :title="color.label"
                @click="editing.color = color.value"
              ></button>
            </div>
          </div>
          <div v-if="clash" class="tag-modal-notice">
            Já existe a tag <b>{{ clash.name }}</b>. Quer juntar as duas? As páginas passam para <b>{{ clash.name }}</b>.
            <button type="button" class="tag-modal-action mt-2" :disabled="saving" @click="mergeInto(clash)">Juntar com {{ clash.name }}</button>
          </div>
          <p v-else-if="error" class="tag-modal-error" role="alert">{{ error }}</p>
          <div class="flex justify-end gap-2">
            <button type="button" class="tag-modal-cancel" @click="editing = null">Cancelar</button>
            <button type="submit" class="btn-brand rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-60" :disabled="saving || !editing.name.trim()">
              {{ saving ? "Salvando..." : editing.id ? "Salvar alterações" : "Criar tag" }}
            </button>
          </div>
        </form>

        <!-- Lista de tags -->
        <template v-else>
          <div v-if="loading && !tags.length" class="tag-modal-empty mt-5">Carregando tags...</div>
          <div v-else-if="!tags.length" class="tag-modal-empty mt-5">Nenhuma tag criada ainda.</div>
          <ul v-else class="tag-list mt-5">
            <li v-for="tag in tags" :key="tag.id" class="tag-row" :style="tagStyle(tag.color)">
              <template v-if="deleting?.id === tag.id">
                <p class="tag-row-confirm">
                  Excluir <b>{{ tag.name }}</b>? Sai de {{ plural(tag.page_count, "página", "páginas") }}.
                  <template v-if="tag.sections.length">
                    {{ plural(tag.sections.length, "seção Links/Roteiros deixa", "seções Links/Roteiros deixam") }} de mostrar esses roteiros.
                  </template>
                </p>
                <div class="flex gap-2">
                  <button type="button" class="tag-modal-action" @click="deleting = null">Cancelar</button>
                  <button type="button" class="tag-modal-action is-danger" :disabled="saving" @click="confirmDelete(tag.id)">Excluir</button>
                </div>
              </template>
              <template v-else>
                <span class="tag-dot" aria-hidden="true"></span>
                <span class="tag-row-text">
                  <span class="tag-row-name">{{ tag.name }}</span>
                  <span class="tag-row-count">{{ plural(tag.page_count, "página", "páginas") }}</span>
                </span>
                <div v-if="canEdit" class="flex gap-2">
                  <button type="button" class="tag-modal-action" @click="startEdit(tag)">Editar</button>
                  <button type="button" class="tag-modal-action is-danger" @click="deleting = tag">Excluir</button>
                </div>
              </template>
            </li>
          </ul>
          <p v-if="error" class="tag-modal-error mt-3" role="alert">{{ error }}</p>
          <button v-if="canEdit" type="button" class="tag-add" @click="startEdit(null)">+ Adicionar tag</button>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { XIcon } from "lucide-vue-next";
import { errorDetail, usePageTags } from "../../../composables/usePageTags";
import { TAG_COLORS, slugifyTag, tagStyle, type PageTag, type TagColor } from "../../../types/pageTag";

const props = withDefaults(defineProps<{ open: boolean; agencyId: number | null | undefined; canEdit?: boolean }>(), { canEdit: true });
const emit = defineEmits<{ (e: "close"): void; (e: "pages-changed"): void }>();

const { tags, loading, load, reload, create, update, remove, merge } = usePageTags();
const editing = ref<{ id: number | null; name: string; color: TagColor } | null>(null);
const deleting = ref<PageTag | null>(null);
const clash = ref<PageTag | null>(null);
const saving = ref(false);
const error = ref("");
const closeRef = ref<HTMLButtonElement | null>(null);
const nameRef = ref<HTMLInputElement | null>(null);

const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`;

watch(
  () => props.open,
  async isOpen => {
    if (!isOpen) return;
    editing.value = null;
    deleting.value = null;
    error.value = "";
    await load(props.agencyId);
    void reload();
    await nextTick();
    closeRef.value?.focus();
  },
  { immediate: true }
);
watch(
  () => editing.value?.name,
  () => {
    clash.value = null;
    error.value = "";
  }
);

const close = () => {
  if (saving.value) return;
  emit("close");
};

const nextColor = (): TagColor => {
  const used = new Set(tags.value.map(tag => tag.color));
  return TAG_COLORS.find(color => !used.has(color.value))?.value || TAG_COLORS[tags.value.length % TAG_COLORS.length].value;
};
const startEdit = async (tag: PageTag | null) => {
  error.value = "";
  deleting.value = null;
  editing.value = tag ? { id: tag.id, name: tag.name, color: tag.color } : { id: null, name: "", color: nextColor() };
  await nextTick();
  nameRef.value?.focus();
};

const save = async () => {
  const draft = editing.value;
  if (!draft || !props.agencyId) return;
  const name = draft.name.trim();
  if (!name) return;
  // Nome igual ao de outra tag: oferece juntar em vez de criar duas parecidas.
  const same = tags.value.find(tag => tag.id !== draft.id && slugifyTag(tag.name) === slugifyTag(name));
  if (same && draft.id) {
    clash.value = same;
    return;
  }
  saving.value = true;
  error.value = "";
  try {
    if (draft.id) await update(draft.id, { name, color: draft.color });
    else await create(props.agencyId, name, draft.color);
    editing.value = null;
    emit("pages-changed");
  } catch (err) {
    error.value = errorDetail(err, "Não deu para salvar a tag. Tente de novo.");
  } finally {
    saving.value = false;
  }
};

const mergeInto = async (target: PageTag) => {
  const draft = editing.value;
  if (!draft?.id) return;
  saving.value = true;
  try {
    await merge(draft.id, target.id);
    editing.value = null;
    emit("pages-changed");
  } catch (err) {
    error.value = errorDetail(err, "Não deu para juntar as tags.");
    clash.value = null;
  } finally {
    saving.value = false;
  }
};

const confirmDelete = async (tagId: number) => {
  saving.value = true;
  error.value = "";
  try {
    await remove(tagId);
    deleting.value = null;
    emit("pages-changed");
  } catch (err) {
    error.value = errorDetail(err, "Não deu para excluir a tag.");
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
/* Mesmo padrão do modal de etapas do funil (LeadStatusManagerPanel). */
.tag-modal-shell {
  max-height: calc(100vh - 32px);
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: 1.5rem;
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-xl);
}
.tag-modal-shell h3 {
  color: var(--foreground);
  font-family: var(--font-display);
}
.tag-modal-eyebrow,
.tag-modal-label {
  color: var(--muted-foreground);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.tag-modal-label {
  display: inline-block;
}
.tag-modal-hint {
  margin-top: 4px;
  color: var(--muted-foreground);
  font-size: 0.8125rem;
}
.tag-modal-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  background: var(--muted);
  color: var(--muted-foreground);
  padding: 0.5rem;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.tag-modal-close:hover {
  background: var(--accent);
  color: var(--foreground);
}
.tag-modal-input {
  border: 1px solid var(--input);
  border-radius: 0.75rem;
  background: var(--background);
  color: var(--foreground);
}
.tag-modal-input:focus {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 18%, transparent);
}
.tag-swatch {
  width: 2.25rem;
  height: 2.25rem;
  border: 2px solid var(--tag-fg);
  border-radius: 999px;
  background: var(--tag-bg);
  transition: transform 0.15s ease;
}
.tag-swatch.is-on {
  box-shadow: 0 0 0 3px var(--card), 0 0 0 5px var(--tag-fg);
}
.tag-list {
  display: grid;
}
.tag-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--border);
}
.tag-row:hover {
  background: color-mix(in srgb, var(--muted) 55%, transparent);
}
.tag-dot {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--tag-fg);
  box-shadow: 0 0 0 4px var(--tag-bg);
}
.tag-row-text {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}
.tag-row-name {
  overflow: hidden;
  color: var(--foreground);
  font-size: 0.9375rem;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tag-row-count {
  color: var(--muted-foreground);
  font-size: 0.75rem;
}
.tag-row-confirm {
  flex: 1;
  min-width: 200px;
  margin: 0;
  color: var(--foreground);
  font-size: 0.8125rem;
}
.tag-modal-action,
.tag-modal-cancel {
  border-radius: 999px;
  background: var(--muted);
  color: var(--foreground);
  padding: 0.4rem 0.8rem;
  font-size: 0.75rem;
  font-weight: 650;
  transition: background-color 0.15s ease;
}
.tag-modal-action:hover,
.tag-modal-cancel:hover {
  background: var(--accent);
  color: var(--accent-foreground);
}
.tag-modal-action.is-danger {
  background: var(--status-danger);
  color: var(--status-danger-foreground);
}
.tag-modal-action:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.tag-modal-cancel {
  border: 1px solid var(--border);
  background: var(--background);
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}
.tag-add {
  display: block;
  width: 100%;
  margin-top: 12px;
  border: 1px dashed var(--border);
  border-radius: 14px;
  padding: 10px;
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
}
.tag-add:hover {
  background: var(--accent);
}
.tag-modal-empty {
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  background: var(--muted);
  color: var(--muted-foreground);
  padding: 2rem 1rem;
  text-align: center;
  font-size: 0.875rem;
}
.tag-modal-notice {
  border-radius: 12px;
  background: var(--status-warning);
  color: var(--status-warning-foreground);
  padding: 10px 12px;
  font-size: 0.8125rem;
}
.tag-modal-error {
  color: var(--destructive, #dc2626);
  font-size: 0.8125rem;
}
.btn-brand {
  background: var(--primary);
  color: var(--primary-foreground);
  box-shadow: var(--shadow-soft);
}
</style>
