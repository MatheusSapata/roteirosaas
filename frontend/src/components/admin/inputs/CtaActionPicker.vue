<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <label class="text-sm font-semibold text-slate-600">{{ label }}</label>
      <span class="text-xs text-slate-500">Escolha o destino do botão</span>
    </div>
    <div class="flex flex-wrap gap-2">
      <button
        type="button"
        class="rounded-lg border px-3 py-1.5 text-sm font-semibold transition"
        :class="mode === 'link' ? 'border-slate-800 bg-slate-900 text-white' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
        @click="setMode('link')"
      >
        CTA / Link externo
      </button>
      <button
        type="button"
        class="rounded-lg border px-3 py-1.5 text-sm font-semibold transition"
        :class="mode === 'section' ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
        :disabled="!availableSections.length"
        @click="setMode('section')"
      >
        Chamada para seção
      </button>
    </div>

    <div v-if="mode === 'section'" class="rounded-lg border border-emerald-100 bg-emerald-50/70 px-3 py-3 text-sm text-emerald-900">
      <div v-if="selectedSection">
        <p class="text-xs uppercase tracking-[0.2em] text-emerald-700">{{ selectedSection.typeLabel }}</p>
        <p class="text-base font-semibold">{{ selectedSection.title }}</p>
        <p class="text-xs text-emerald-800">{{ selectedSection.description }}</p>
      </div>
      <p v-else class="text-xs text-emerald-800">Selecione abaixo para onde o botão deve rolar.</p>
      <div class="mt-3 flex flex-wrap gap-2">
        <button type="button" class="rounded-full border border-emerald-600 px-3 py-1 text-xs font-semibold text-emerald-700" @click="dialogOpen = true">
          Escolher seção
        </button>
        <button
          v-if="selectedSection"
          type="button"
          class="rounded-full border border-transparent px-3 py-1 text-xs font-semibold text-emerald-800 hover:border-emerald-600"
          @click="emit('update:sectionId', null)"
        >
          Limpar
        </button>
      </div>
      <p v-if="!availableSections.length" class="mt-2 text-xs text-emerald-800">
        Adicione e ative outras seções para usá-las como destino.
      </p>
    </div>

    <transition name="fade">
      <div v-if="dialogOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4">
        <div class="w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Selecionar seção</p>
              <h3 class="text-lg font-semibold text-slate-900">Escolha o destino do botão</h3>
            </div>
            <button type="button" class="text-sm font-semibold text-slate-500 hover:text-slate-900" @click="dialogOpen = false">
              Fechar
            </button>
          </div>
          <div class="mt-5 grid gap-3 md:grid-cols-2">
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
          <p v-if="!availableSections.length" class="mt-4 text-sm text-slate-500">
            Ainda não há outras seções ativas para rolar. Adicione novas seções no editor.
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

const normalizedMode = computed(() => props.mode || "link");
const label = computed(() => props.label || "Ação do botão");

const availableSections = computed(() => {
  const list = sections?.value || [];
  return list
    .filter(section => section.anchorId && section.anchorId !== props.currentAnchor && section.enabled !== false)
    .map(section => ({
      anchorId: section.anchorId as string,
      type: section.type,
      typeLabel: sectionLabels[section.type] || "Seção",
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
