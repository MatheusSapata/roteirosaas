<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p class="text-sm font-semibold text-slate-800">Rodapé com dados da agência</p>
      <p class="mt-2 text-sm text-slate-600">
        Os campos são preenchidos automaticamente usando as informações cadastradas em
        <span class="font-semibold">Configurações &gt; Agência</span>. Nome, CNPJ, endereço, contatos e redes sociais são
        exibidos somente se estiverem completos.
      </p>
      <ul class="mt-3 list-disc space-y-1 pl-5 text-xs text-slate-500">
        <li>Preencha o CEP, endereço e contatos no painel para ativar o mapa e os textos.</li>
        <li>Os ícones das redes aparecem apenas quando a agência possui links cadastrados.</li>
      </ul>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <label class="space-y-1 text-sm font-semibold text-slate-600">
        Layout preferido
        <select v-model="local.displayVariant" class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm">
          <option value="auto">Automático (mobile em card, desktop amplo)</option>
          <option value="stacked">Sempre empilhado</option>
          <option value="wide">Sempre em bloco horizontal</option>
        </select>
      </label>

      <label class="space-y-2 text-sm font-semibold text-slate-600">
        Cor de fundo
        <div class="flex items-center gap-2">
          <input type="color" v-model="local.backgroundColor" class="h-10 w-12 cursor-pointer rounded border border-slate-200 bg-white" />
          <input
            v-model="local.backgroundColor"
            placeholder="#0b0f19"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
          />
        </div>
        <p class="text-xs font-normal text-slate-500">
          Por padrão usamos a cor definida em “Cor de botões e destaques” no Page Editor. Ajuste aqui se quiser um fundo diferente.
        </p>
      </label>
    </div>

    <div class="rounded-xl border border-slate-200 px-4 py-3">
      <label class="flex items-center gap-3 text-sm font-semibold text-slate-700">
        <input type="checkbox" v-model="local.showCadastur" class="h-4 w-4" />
        Exibir selo Cadastur
      </label>
      <p class="mt-1 text-xs text-slate-500">
        Será mostrado apenas se houver um CNPJ válido. O link usa automaticamente o documento informado.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import type { AgencyFooterSection } from "../../types/page";

const props = defineProps<{ modelValue: AgencyFooterSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: AgencyFooterSection): void }>();

const local = reactive<AgencyFooterSection>({
  ...props.modelValue,
  type: "agency_footer",
  enabled: props.modelValue.enabled ?? true,
  fullWidth: props.modelValue.fullWidth ?? true,
  displayVariant: props.modelValue.displayVariant || "auto",
  showCadastur: props.modelValue.showCadastur !== false,
  backgroundColor: props.modelValue.backgroundColor || "#0b0f19"
});

let syncing = false;
const syncFromProps = (value: AgencyFooterSection) => {
  syncing = true;
  Object.assign(local, value);
  local.displayVariant = value.displayVariant || "auto";
  local.fullWidth = value.fullWidth ?? true;
  local.showCadastur = value.showCadastur !== false;
  local.enabled = value.enabled ?? true;
  local.backgroundColor = value.backgroundColor || local.backgroundColor || "#0b0f19";
  syncing = false;
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
    emit("update:modelValue", value as AgencyFooterSection);
  },
  { deep: true }
);
</script>
