<template>
  <div class="cta-action-picker space-y-2">
    <div class="flex items-center justify-between">
      <label class="text-sm font-semibold text-slate-600">{{ label }}</label>
      <span class="text-xs text-slate-500">{{ copy.destinationHint }}</span>
    </div>
    <div class="flex flex-wrap gap-2">
      <button
        type="button"
        class="rounded-lg border px-3 py-1.5 text-sm font-semibold transition"
        :class="mode === 'link' ? 'cta-mode-active' : 'cta-mode-idle'"
        @click="setMode('link')"
      >
        {{ copy.options.link }}
      </button>
      <button
        type="button"
        class="rounded-lg border px-3 py-1.5 text-sm font-semibold transition"
        :class="mode === 'section' ? 'cta-mode-active' : 'cta-mode-idle'"
        :disabled="!availableSections.length"
        @click="setMode('section')"
      >
        {{ copy.options.section }}
      </button>
    </div>

    <div v-if="mode === 'section'" class="rounded-lg border border-emerald-100 bg-emerald-50/70 px-3 py-3 text-sm text-emerald-900">
      <div v-if="selectedSection">
        <p class="text-xs uppercase tracking-[0.2em] text-emerald-700">{{ selectedSection.typeLabel }}</p>
        <p class="text-base font-semibold">{{ selectedSection.title }}</p>
        <p class="text-xs text-emerald-800">{{ selectedSection.description }}</p>
      </div>
      <p v-else class="text-xs text-emerald-800">{{ copy.sectionSelect.helper }}</p>
      <div class="mt-3 flex flex-wrap gap-2">
        <button type="button" class="rounded-full border border-emerald-600 px-3 py-1 text-xs font-semibold text-emerald-700" @click="dialogOpen = true">
          {{ copy.sectionSelect.choose }}
        </button>
        <button
          v-if="selectedSection"
          type="button"
          class="rounded-full border border-transparent px-3 py-1 text-xs font-semibold text-emerald-800 hover:border-emerald-600"
          @click="emit('update:sectionId', null)"
        >
          {{ copy.sectionSelect.clear }}
        </button>
      </div>
      <p v-if="!availableSections.length" class="mt-2 text-xs text-emerald-800">
        {{ copy.sectionSelect.empty }}
      </p>
    </div>

    <transition name="fade">
      <div v-if="dialogOpen" class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4 py-6">
        <div class="cta-picker-dialog flex w-full max-w-3xl max-h-[calc(100vh-3rem)] flex-col overflow-hidden rounded-2xl p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500">{{ copy.dialog.subtitle }}</p>
              <h3 class="text-lg font-semibold text-slate-900">{{ copy.dialog.title }}</h3>
            </div>
            <button type="button" class="text-sm font-semibold text-slate-500 hover:text-slate-900" @click="dialogOpen = false">
              {{ copy.dialog.close }}
            </button>
          </div>
          <div class="mt-5 min-h-0 flex-1 overflow-y-auto pr-1">
            <div class="grid gap-3 md:grid-cols-2">
            <button
              v-for="section in availableSections"
              :key="section.anchorId"
              type="button"
              class="rounded-2xl border border-slate-200 p-4 text-left transition hover:-translate-y-0.5 hover:border-emerald-400 hover:shadow-lg"
              @click="selectSection(section.anchorId)"
            >
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">{{ section.typeLabel }}</p>
              <p class="mt-1 text-base font-semibold text-slate-900">{{ section.title }}</p>
              <p class="text-xs text-slate-500">{{ section.description }}</p>
            </button>
            </div>
          </div>
          <p v-if="!availableSections.length" class="mt-4 text-sm text-slate-500">
            {{ copy.dialog.noSections }}
          </p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref } from "vue";
import type { PageSection } from "../../../types/page";
import { sectionsInjectionKey } from "../sectionsContext";
import { describeSection, sectionLabels } from "../../../utils/sectionLabels";
import { createAdminLocalizer } from "../../../utils/adminI18n";

const props = defineProps<{
  mode?: "link" | "section";
  sectionId?: string | null;
  currentAnchor?: string | null;
  label?: string;
}>();
const emit = defineEmits<{
  (e: "update:mode", value: "link" | "section"): void;
  (e: "update:sectionId", value: string | null): void;
}>();

const dialogOpen = ref(false);
const sections = inject(sectionsInjectionKey, ref<PageSection[]>([]));
const t = createAdminLocalizer();

const copy = {
  destinationHint: t({ pt: "Escolha o destino do botão", es: "Elige el destino del botón" }),
  options: {
    link: t({ pt: "Whatsapp / Link externo", es: "Whatsapp / Link externo" }),
    section: t({ pt: "Ir para seção", es: "Ir a la sección" })
  },
  sectionSelect: {
    helper: t({ pt: "Selecione abaixo para onde o botão deve rolar.", es: "Selecciona abajo a dónde debe hacer scroll el botón." }),
    choose: t({ pt: "Escolher seção", es: "Elegir sección" }),
    clear: t({ pt: "Limpar", es: "Limpiar" }),
    empty: t({ pt: "Adicione e ative outras seções para usá-las como destino.", es: "Agrega y activa otras secciones para usarlas como destino." })
  },
  dialog: {
    subtitle: t({ pt: "Selecionar seção", es: "Seleccionar sección" }),
    title: t({ pt: "Escolha o destino do botão", es: "Elige el destino del botón" }),
    close: t({ pt: "Fechar", es: "Cerrar" }),
    noSections: t({
      pt: "Ainda não há outras seções ativas para rolar. Adicione novas seções no editor.",
      es: "Aún no hay otras secciones activas para hacer scroll. Agrega nuevas secciones en el editor."
    })
  }
};

const normalizedMode = computed(() => props.mode || "link");
const label = computed(() => props.label || t({ pt: "Ação do botão", es: "Acción del botón" }));

const availableSections = computed(() => {
  const list = sections?.value || [];
  return list
    .filter(section => section.anchorId && section.anchorId !== props.currentAnchor && section.enabled !== false)
    .map(section => ({
      anchorId: section.anchorId as string,
      type: section.type,
      typeLabel: sectionLabels[section.type] || t({ pt: "Seção", es: "Sección" }),
      title: describeSection(section),
      description: section.type === "hero" ? section.subtitle || "" : section.type === "story" ? section.subtitle || "" : ""
    }));
});

const selectedSection = computed(() => availableSections.value.find(item => item.anchorId === props.sectionId));

const setMode = (value: "link" | "section") => {
  emit("update:mode", value);
  if (value === "link") {
    emit("update:sectionId", null);
  } else if (!props.sectionId && availableSections.value[0]) {
    emit("update:sectionId", availableSections.value[0].anchorId);
  }
};

const selectSection = (anchorId: string) => {
  emit("update:sectionId", anchorId);
  emit("update:mode", "section");
  dialogOpen.value = false;
};
</script>

<style scoped>
.cta-action-picker { color: var(--foreground); }
.cta-action-picker :deep(.text-slate-900),
.cta-action-picker :deep(.text-slate-700),
.cta-action-picker :deep(.text-slate-600) { color: var(--foreground) !important; }
.cta-action-picker :deep(.text-slate-500) { color: var(--muted-foreground) !important; }
.cta-mode-active {
  border-color: var(--primary) !important;
  background: var(--primary) !important;
  color: var(--primary-foreground) !important;
}
.cta-mode-idle {
  border-color: var(--border) !important;
  background: var(--muted) !important;
  color: var(--foreground) !important;
}
.cta-mode-idle:hover { background: var(--accent) !important; }
.cta-picker-dialog {
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}
.cta-picker-dialog :deep(.border-slate-200) { border-color: var(--border) !important; }
.cta-picker-dialog :deep(button:hover) { background: var(--accent); }
</style>
