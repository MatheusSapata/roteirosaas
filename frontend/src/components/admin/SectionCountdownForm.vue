<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Contagem regressiva</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Texto</label>
        <input v-model="local.label" placeholder="Garanta sua vaga agora mesmo!" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Data/hora alvo</label>
        <input v-model="local.targetDate" type="datetime-local" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">Layout</label>
      <select v-model="local.layout" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
        <option value="bar">Barra larga (cheia)</option>
        <option value="flip">Cartões (dias/horas/min/seg)</option>
      </select>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor de fundo</label>
        <div class="mt-1 flex items-center gap-2">
          <input type="color" v-model="local.backgroundColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
          <input v-model="local.backgroundColor" placeholder="#ef4444" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor do texto</label>
        <div class="mt-1 flex items-center gap-2">
          <input type="color" v-model="local.textColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
          <input v-model="local.textColor" placeholder="#ffffff" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import type { CountdownSection } from "../../types/page";

const props = defineProps<{ modelValue: CountdownSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: CountdownSection): void }>();

const buildDefaultTargetDate = () => {
  const date = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  return date.toISOString().slice(0, 16);
};

const local = reactive<CountdownSection>({
  enabled: true,
  label: "Garanta sua vaga agora mesmo!",
  targetDate: props.modelValue.targetDate || buildDefaultTargetDate(),
  backgroundColor: "#ef4444",
  textColor: "#ffffff",
  layout: "bar",
  ...props.modelValue
});
let syncing = false;
const syncFromProps = (value: CountdownSection) => {
  syncing = true;
  Object.assign(local, value);
  local.targetDate = value.targetDate || buildDefaultTargetDate();
  local.layout = value.layout || "bar";
  nextTick(() => {
    syncing = false;
  });
};

watch(
  () => props.modelValue,
  value => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as CountdownSection);
  },
  { deep: true }
);
</script>
