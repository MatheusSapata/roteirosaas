<template>
  <div ref="rootRef" class="tag-input" :class="{ 'is-disabled': disabled }" @click="focusInput">
    <span v-for="tag in modelValue" :key="tag.id" class="page-tag" :style="tagStyle(tag.color)">
      {{ tag.name }}
      <button v-if="!disabled" type="button" class="tag-input-x" :aria-label="`Tirar a tag ${tag.name}`" @click.stop="removeTag(tag.id)">
        <XIcon aria-hidden="true" />
      </button>
    </span>
    <input
      :id="inputId"
      ref="inputRef"
      v-model="query"
      class="tag-input-field"
      type="text"
      autocomplete="off"
      role="combobox"
      :aria-expanded="open"
      :aria-controls="`${inputId}-list`"
      aria-label="Tags da página"
      :placeholder="modelValue.length ? 'Adicionar outra…' : 'Escolha ou crie uma tag'"
      :disabled="disabled || busy"
      @focus="open = true"
      @blur="onBlur"
      @keydown.enter.prevent="pickHighlighted"
      @keydown.down.prevent="move(1)"
      @keydown.up.prevent="move(-1)"
      @keydown.esc="open = false"
      @keydown.backspace="onBackspace"
    />
    <div v-if="open && !disabled" :id="`${inputId}-list`" class="tag-input-menu" role="listbox" @mousedown.prevent>
      <button
        v-for="(option, index) in options"
        :key="option.key"
        type="button"
        role="option"
        class="tag-input-option"
        :class="{ 'is-active': index === highlighted, 'is-create': option.create }"
        :style="option.tag ? tagStyle(option.tag.color) : undefined"
        :aria-selected="index === highlighted"
        @click="pick(option)"
      >
        <template v-if="option.tag">
          <i class="tag-input-dot" aria-hidden="true"></i>{{ option.tag.name }}
          <small>{{ option.tag.page_count }} {{ option.tag.page_count === 1 ? "página" : "páginas" }}</small>
        </template>
        <template v-else><PlusIcon aria-hidden="true" />Criar tag "{{ query.trim() }}"</template>
      </button>
      <p v-if="!options.length" class="tag-input-empty">
        {{ query ? "Essa tag já está na página." : allTags.length ? "Todas as tags já estão nesta página. Digite para criar outra." : "Digite o nome da primeira tag." }}
      </p>
    </div>
    <p v-if="error" class="tag-input-error" role="alert">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { PlusIcon, XIcon } from "lucide-vue-next";
import { errorDetail, usePageTags } from "../../../composables/usePageTags";
import { slugifyTag, tagStyle, type PageTag, type PageTagBrief } from "../../../types/pageTag";

const props = withDefaults(
  defineProps<{ modelValue: PageTagBrief[]; agencyId: number | null | undefined; disabled?: boolean; inputId?: string }>(),
  { disabled: false, inputId: "page-tag-input" }
);
const emit = defineEmits<{ (e: "update:modelValue", value: PageTagBrief[]): void }>();

const { tags: allTags, load, create } = usePageTags();
const query = ref("");
const open = ref(false);
const busy = ref(false);
const error = ref("");
const highlighted = ref(0);
const inputRef = ref<HTMLInputElement | null>(null);
const rootRef = ref<HTMLElement | null>(null);

watch(() => props.agencyId, id => load(id), { immediate: true });

type Option = { key: string; tag?: PageTag; create?: boolean };
const options = computed<Option[]>(() => {
  const term = slugifyTag(query.value);
  const chosen = new Set(props.modelValue.map(tag => tag.id));
  const list: Option[] = allTags.value
    .filter(tag => !chosen.has(tag.id) && (!term || slugifyTag(tag.name).includes(term)))
    .map(tag => ({ key: `t${tag.id}`, tag }));
  if (term && !allTags.value.some(tag => slugifyTag(tag.name) === term)) list.push({ key: "create", create: true });
  return list;
});
watch(options, () => (highlighted.value = 0));

const focusInput = () => inputRef.value?.focus();
const move = (step: number) => {
  open.value = true;
  if (!options.value.length) return;
  highlighted.value = (highlighted.value + step + options.value.length) % options.value.length;
};
const onBlur = () => {
  open.value = false;
};

const addTag = (tag: PageTagBrief) => {
  if (props.modelValue.some(item => item.id === tag.id)) return;
  emit("update:modelValue", [...props.modelValue, { id: tag.id, name: tag.name, color: tag.color }]);
};
const removeTag = (tagId: number) => emit("update:modelValue", props.modelValue.filter(tag => tag.id !== tagId));

const pick = async (option?: Option) => {
  if (!option) return;
  error.value = "";
  if (option.tag) {
    addTag(option.tag);
  } else if (option.create && props.agencyId) {
    busy.value = true;
    try {
      addTag(await create(props.agencyId, query.value.trim()));
    } catch (err) {
      error.value = errorDetail(err, "Não deu para criar a tag. Tente de novo.");
    } finally {
      busy.value = false;
    }
  }
  query.value = "";
  open.value = true;
  requestAnimationFrame(focusInput);
};
const pickHighlighted = () => pick(options.value[highlighted.value]);
const onBackspace = () => {
  if (query.value || !props.modelValue.length) return;
  removeTag(props.modelValue[props.modelValue.length - 1].id);
};

defineExpose({ focus: focusInput });
</script>

<style scoped>
.tag-input {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 42px;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--card);
  cursor: text;
}
.tag-input:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 18%, transparent);
}
.tag-input.is-disabled {
  cursor: default;
  opacity: 0.7;
}
.tag-input .page-tag {
  height: 26px;
  font-size: 12px;
}
.tag-input-x {
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  margin-right: -4px;
  border-radius: 999px;
  color: inherit;
  opacity: 0.7;
}
.tag-input-x:hover {
  opacity: 1;
  background: color-mix(in srgb, var(--tag-fg) 15%, transparent);
}
.tag-input-x svg {
  width: 12px;
  height: 12px;
}
.tag-input-field {
  flex: 1;
  min-width: 120px;
  height: 28px;
  padding: 0 4px;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 13px;
  color: var(--foreground);
}
.tag-input-field:focus-visible {
  outline: none;
}
.tag-input-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 40;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 260px;
  overflow: auto;
  padding: 6px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--popover, var(--card));
  box-shadow: 0 12px 32px rgba(24, 32, 40, 0.16);
}
.tag-input-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border-radius: 9px;
  font-size: 13px;
  text-align: left;
  color: var(--foreground);
}
.tag-input-option.is-active,
.tag-input-option:hover {
  background: var(--muted);
}
.tag-input-option small {
  margin-left: auto;
  font-size: 11.5px;
  color: var(--muted-foreground);
}
.tag-input-option.is-create {
  font-weight: 600;
  color: var(--accent-foreground, var(--primary));
}
.tag-input-option svg {
  width: 14px;
  height: 14px;
}
.tag-input-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: var(--tag-fg);
}
.tag-input-empty {
  margin: 0;
  padding: 8px 10px;
  font-size: 12.5px;
  color: var(--muted-foreground);
}
.tag-input-error {
  flex-basis: 100%;
  margin: 2px 2px 0;
  font-size: 12px;
  color: #dc2626;
}
</style>
