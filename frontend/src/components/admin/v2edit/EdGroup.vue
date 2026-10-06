<template>
  <section class="ved-group" :class="[`is-${kindName}`, { 'is-collapsed': collapsed }]">
    <button v-if="title" type="button" class="ved-group-head" :aria-expanded="!collapsed" @click="collapsed = !collapsed">
      <span class="ved-group-icon" aria-hidden="true"><component :is="KIND_ICONS[kindName]" /></span>
      <h3>{{ title }}</h3>
      <span v-if="count" class="ved-group-count">{{ count }}</span>
      <span v-if="extra" class="ved-group-extra">Extra</span>
      <ChevronDownIcon class="ved-group-chev" aria-hidden="true" />
    </button>
    <div v-show="!collapsed || !title" class="ved-group-body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
import {
  CalendarDaysIcon,
  ChevronDownIcon,
  ImageIcon,
  LayoutTemplateIcon,
  ListIcon,
  MousePointerClickIcon,
  PaletteIcon,
  StoreIcon,
  TypeIcon
} from "lucide-vue-next";
import { computed, ref } from "vue";
import type { Component } from "vue";

/** Tipo de parte da seção: define o ícone e a cor do grupo no painel. */
export type EdGroupKind = "text" | "media" | "items" | "dates" | "action" | "layout" | "background" | "info";

const props = defineProps<{ title?: string; count?: string; extra?: boolean; kind?: EdGroupKind; startCollapsed?: boolean }>();

const KIND_ICONS: Record<EdGroupKind, Component> = {
  text: TypeIcon,
  media: ImageIcon,
  items: ListIcon,
  dates: CalendarDaysIcon,
  action: MousePointerClickIcon,
  layout: LayoutTemplateIcon,
  background: PaletteIcon,
  info: StoreIcon
};

// Sem "kind", o tipo vem do título, para todos os formulários seguirem o mesmo padrão.
const BY_TITLE: Array<[RegExp, EdGroupKind]> = [
  [/^fundo/i, "background"],
  [/layout|formato|estilo|comportamento/i, "layout"],
  [/data|prazo/i, "dates"],
  [/m[ií]dia|foto|capa|v[ií]deo|logo|imagem/i, "media"],
  [/bot[aã]o|checkout|formul[aá]rio|lado direito|libera/i, "action"],
  [/itens|ofertas|perguntas|depoimentos|dias|roteiros|links|trechos|voos/i, "items"],
  [/dados|ag[eê]ncia/i, "info"]
];
const kindName = computed<EdGroupKind>(() => props.kind || BY_TITLE.find(([pattern]) => pattern.test(props.title || ""))?.[1] || "text");

const collapsed = ref(!!props.startCollapsed);
</script>
