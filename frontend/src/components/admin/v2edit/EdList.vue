<template>
  <div class="ved-field">
    <ol class="ved-list">
      <li
        v-for="(item, index) in items"
        :key="keys[index]"
        class="ved-item"
        :class="{ open: openIndex === index, 'drag-over': dragOver === index && dragFrom !== index }"
        @dragover.prevent="dragOver = index"
        @dragleave="dragOver = dragOver === index ? null : dragOver"
        @drop.prevent="drop(index)"
      >
        <div class="ved-item-head">
          <span class="ved-item-grip" draggable="true" title="Arraste para reordenar" @dragstart="dragFrom = index" @dragend="dragFrom = dragOver = null">
            <GripVerticalIcon aria-hidden="true" />
          </span>
          <button type="button" class="ved-item-toggle" :aria-expanded="openIndex === index" @click="openIndex = openIndex === index ? null : index">
            <span>{{ itemTitle(item, index) || `${itemLabel} ${index + 1}` }}</span>
            <span class="ved-item-chev" aria-hidden="true"><ChevronDownIcon /></span>
          </button>
        </div>
        <div v-if="openIndex === index" class="ved-item-body">
          <slot :item="item" :index="index" :update="(changes: Record<string, any>) => update(index, changes)" />
          <div class="ved-item-actions">
            <button type="button" :disabled="!!max && items.length >= max" @click="duplicate(index)"><CopyIcon aria-hidden="true" />Duplicar</button>
            <button type="button" class="danger" :disabled="items.length <= (min || 0)" @click="remove(index)"><Trash2Icon aria-hidden="true" />Excluir</button>
          </div>
        </div>
      </li>
    </ol>
    <button type="button" class="ved-add" :disabled="!!max && items.length >= max" @click="add">
      <PlusIcon aria-hidden="true" />
      {{ addLabel }}
    </button>
  </div>
</template>

<script setup lang="ts" generic="T extends Record<string, any>">
import { ChevronDownIcon, CopyIcon, GripVerticalIcon, PlusIcon, Trash2Icon } from "lucide-vue-next";
import { ref, watch } from "vue";

const props = defineProps<{
  items: T[];
  itemTitle: (item: T, index: number) => string;
  newItem: () => T;
  addLabel: string;
  itemLabel?: string;
  min?: number;
  max?: number;
}>();
const emit = defineEmits<{ (e: "update:items", value: T[]): void }>();

// Chaves estáveis para o Vue não misturar itens ao reordenar.
let seq = 0;
const keys = ref<number[]>(props.items.map(() => seq++));
watch(
  () => props.items.length,
  length => {
    while (keys.value.length < length) keys.value.push(seq++);
    if (keys.value.length > length) keys.value = keys.value.slice(0, length);
  }
);

const openIndex = ref<number | null>(props.items.length ? 0 : null);
const dragFrom = ref<number | null>(null);
const dragOver = ref<number | null>(null);

const clone = <V,>(value: V): V => JSON.parse(JSON.stringify(value));
const commit = (next: T[]) => emit("update:items", next);
const update = (index: number, changes: Record<string, any>) => commit(props.items.map((item, idx) => (idx === index ? ({ ...item, ...changes } as T) : item)));
const add = () => {
  commit([...props.items, props.newItem()]);
  keys.value.push(seq++);
  openIndex.value = props.items.length;
};
const duplicate = (index: number) => {
  const next = [...props.items];
  const copy = clone(next[index]) as Record<string, any>;
  if ("id" in copy) copy.id = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
  next.splice(index + 1, 0, copy as T);
  keys.value.splice(index + 1, 0, seq++);
  commit(next);
  openIndex.value = index + 1;
};
const remove = (index: number) => {
  keys.value.splice(index, 1);
  commit(props.items.filter((_, idx) => idx !== index));
  openIndex.value = null;
};
const drop = (target: number) => {
  const from = dragFrom.value;
  dragFrom.value = dragOver.value = null;
  if (from === null || from === target) return;
  const next = [...props.items];
  const [moved] = next.splice(from, 1);
  next.splice(target, 0, moved);
  const [movedKey] = keys.value.splice(from, 1);
  keys.value.splice(target, 0, movedKey);
  commit(next);
  openIndex.value = target;
};
</script>
