<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p class="text-sm font-semibold text-slate-800">{{ viewCopy.info.title }}</p>
      <p class="mt-2 text-sm text-slate-600">
        {{ viewCopy.info.description }}
        <span class="font-semibold">{{ viewCopy.info.configs }}</span>
        {{ viewCopy.info.details }}
      </p>
      <ul class="mt-3 list-disc space-y-1 pl-5 text-xs text-slate-500">
        <li>{{ viewCopy.info.listAddress }}</li>
        <li>{{ viewCopy.info.listSocial }}</li>
      </ul>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <label class="space-y-1 text-sm font-semibold text-slate-600">
        {{ viewCopy.layout.label }}
        <select v-model="local.displayVariant" class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm">
          <option value="auto">{{ viewCopy.layout.auto }}</option>
          <option value="stacked">{{ viewCopy.layout.stacked }}</option>
          <option value="wide">{{ viewCopy.layout.wide }}</option>
        </select>
      </label>
      <label class="space-y-2 text-sm font-semibold text-slate-600">
        {{ viewCopy.colors.backgroundLabel }}
        <div class="flex items-center gap-2">
          <input type="color" v-model="local.backgroundColor" class="h-10 w-12 cursor-pointer rounded border border-slate-200 bg-white" />
          <input
            v-model="local.backgroundColor"
            placeholder="#2d2d2d"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
          />
        </div>
        <p class="text-xs font-normal text-slate-500">
          {{ viewCopy.colors.helper }}
          <span class="font-mono text-slate-700">#2d2d2d</span>
          {{ viewCopy.colors.helperHighlight }}
        </p>
      </label>
    </div>

    <div class="rounded-xl border border-slate-200 px-4 py-3">
      <label class="flex items-center gap-3 text-sm font-semibold text-slate-700">
        <input type="checkbox" v-model="local.showCadastur" class="h-4 w-4" />
        {{ viewCopy.cadastur.label }}
      </label>
      <p class="mt-1 text-xs text-slate-500">
        {{ viewCopy.cadastur.helper }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import type { AgencyFooterSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: AgencyFooterSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: AgencyFooterSection): void }>();
const t = createAdminLocalizer();

const viewCopy = {
  info: {
    title: t({ pt: "Rodapé com dados da agência", es: "Pie con datos de la agencia" }),
    description: t({
      pt: "Os campos são preenchidos automaticamente usando as informações cadastradas em",
      es: "Los campos se completan automáticamente usando la información registrada en"
    }),
    configs: t({ pt: "Configurações > Agência", es: "Configuraciones > Agencia" }),
    details: t({
      pt: ". Nome, CNPJ, endereço, contatos e redes sociais são exibidos somente se estiverem completos.",
      es: ". Nombre, CNPJ, dirección, contactos y redes sociales se muestran solo si están completos."
    }),
    listAddress: t({ pt: "Preencha o CEP, endereço e contatos no painel para ativar o mapa e os textos.", es: "Completa el CEP, dirección y contactos para habilitar el mapa y los textos." }),
    listSocial: t({ pt: "Os ícones das redes aparecem apenas quando a agência possui links cadastrados.", es: "Los íconos de redes solo aparecen cuando la agencia tiene enlaces registrados." })
  },
  layout: {
    label: t({ pt: "Layout preferido", es: "Layout preferido" }),
    auto: t({ pt: "Automático (mobile em card, desktop amplo)", es: "Automático (mobile en card, desktop amplio)" }),
    stacked: t({ pt: "Sempre empilhado", es: "Siempre apilado" }),
    wide: t({ pt: "Sempre em bloco horizontal", es: "Siempre en bloque horizontal" })
  },
  colors: {
    backgroundLabel: t({ pt: "Cor de fundo", es: "Color de fondo" }),
    helper: t({ pt: "Por padrão usamos a cor fixa", es: "Por defecto usamos el color fijo" }),
    helperHighlight: t({ pt: ", independente da cor de botões. Ajuste aqui se quiser outro fundo.", es: ", independientemente del color de botones. Ajusta aquí si quieres otro fondo." })
  },
  cadastur: {
    label: t({ pt: "Exibir selo Cadastur", es: "Mostrar sello Cadastur" }),
    helper: t({
      pt: "Habilite para mostrar o selo usando automaticamente o CPF/CNPJ salvo em Configurações da Agência.",
      es: "Activa para mostrar el sello usando automáticamente el CPF/CNPJ guardado en Configuraciones de la Agencia."
    })
  }
};

const DEFAULT_FOOTER_BG = "#2d2d2d";

const local = reactive<AgencyFooterSection>({
  ...props.modelValue,
  type: "agency_footer",
  enabled: props.modelValue.enabled ?? true,
  fullWidth: props.modelValue.fullWidth ?? true,
  displayVariant: props.modelValue.displayVariant || "auto",
  showCadastur: props.modelValue.showCadastur !== false,
  backgroundColor: props.modelValue.backgroundColor || DEFAULT_FOOTER_BG
});

let syncing = false;
const syncFromProps = (value: AgencyFooterSection) => {
  syncing = true;
  Object.assign(local, value);
  local.displayVariant = value.displayVariant || "auto";
  local.fullWidth = value.fullWidth ?? true;
  local.showCadastur = value.showCadastur !== false;
  local.enabled = value.enabled ?? true;
  local.backgroundColor = value.backgroundColor || DEFAULT_FOOTER_BG;
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
