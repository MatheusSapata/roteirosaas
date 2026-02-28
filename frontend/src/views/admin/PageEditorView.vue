<template>
<div class="w-full space-y-6 px-4 py-10 md:px-8">
    <div class="sticky top-0 z-30 flex flex-col gap-3 border-b border-white/40 bg-slate-50/90 py-4 backdrop-blur md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm uppercase tracking-wide text-slate-500">Editor de página</p>
        <h1 class="text-3xl font-bold text-slate-900">{{ page?.title || "Roteiro" }}</h1>
        <p class="text-sm text-slate-500">Monte a página por seções, salve e visualize ao lado.</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            @click="refreshPreview(true)"
            :class="toolbarSecondaryButtonClass"
          >
            <svg
              class="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <polyline points="23 4 23 10 17 10" />
              <polyline points="1 20 1 14 7 14" />
              <path d="M3.51 9A9 9 0 0 1 21 10M20.49 15A9 9 0 0 1 3 14" />
            </svg>
            Atualizar preview
          </button>
        </div>

        <button
          @click="saveTemplate"
          :class="toolbarSecondaryButtonClass"
        >
          Salvar como template padrão
        </button>

        <button
          @click="goBack"
          :class="toolbarSecondaryButtonClass"
        >
          Voltar
        </button>

        <button
          v-if="isPublished"
          :disabled="!publicUrl"
          @click="viewPublicPage"
          :class="[toolbarSecondaryButtonClass, 'disabled:opacity-60']"
        >
          <svg
            class="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          Visualizar página
        </button>

        <button
          @click="saveConfig"
          :class="toolbarPrimaryButtonClass"
        >
          Salvar
        </button>

        <button
          v-if="!isPublished"
          @click="publishPage"
          :class="toolbarPrimaryButtonClass"
        >
          Publicar
        </button>

        <div v-else class="flex flex-wrap items-center gap-2">
          <span :class="toolbarStatusPillClass">
            Publicada
          </span>
          <button
            type="button"
            @click="unpublishPage"
            :class="toolbarWarningButtonClass"
          >
            Despublicar
          </button>
        </div>
      </div>
    </div>

    
    <!-- Dialog de limite de plano (reutilizado também para "template no free") -->
    <div v-if="limitModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">Limite do plano</p>
        <h3 class="mt-2 text-xl font-bold text-slate-900">Ação indisponível</h3>
        <p class="mt-2 text-sm text-slate-600">
          {{ limitModal.message || "Seu plano atual atingiu o limite. Atualize para continuar." }}
        </p>

        <div class="mt-4 flex flex-wrap gap-2">
          <button
            @click="limitModal.open = false"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Fechar
          </button>

          <button
            @click="goPlans"
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark"
          >
            Ver planos
          </button>
        </div>
      </div>
    </div>

    <!-- Dialog de sucesso ao publicar -->
    <div v-if="successModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">Publicação</p>
        <h3 class="mt-2 text-xl font-bold text-slate-900">Página publicada com sucesso</h3>
        <p class="mt-2 text-sm text-slate-600">Escolha o que deseja fazer em seguida.</p>

        <div class="mt-4 flex flex-wrap gap-2">
          <button
            @click="successModal.open = false"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Fechar
          </button>

          <button
            @click="goPages"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Voltar para páginas
          </button>

          <button
            :disabled="!publicUrl"
            @click="viewPublicPage"
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:opacity-50"
          >
            Ver página
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="sectionPicker.open"
      class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/60 px-4 py-8"
      @click.self="closeSectionPicker"
    >
      <div class="w-full max-w-5xl rounded-3xl bg-white shadow-2xl">
        <div class="flex flex-col gap-2 border-b border-slate-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">Adicionar nova seção</p>
            <h3 class="text-lg font-semibold text-slate-900">Escolha um layout</h3>
            <p class="text-sm text-slate-500">A nova seção será inserida logo abaixo do bloco selecionado.</p>
          </div>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            @click="closeSectionPicker"
          >
            Fechar
          </button>
        </div>
        <div class="max-h-[70vh] overflow-y-auto px-6 py-6">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            <button
              v-for="catalog in sectionCatalog"
              :key="catalog.type"
              type="button"
              class="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition hover:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand/40"
              @click="handleSectionPickerSelect(catalog.type)"
            >
              <div class="relative h-44 w-full overflow-hidden rounded-t-2xl border-b border-slate-100 bg-slate-50">
                <div class="absolute inset-0 bg-gradient-to-br" :class="catalog.accent"></div>
                <div class="relative flex h-full w-full items-center justify-center overflow-hidden p-3">
                  <div class="pointer-events-none origin-center scale-[0.55] transform rounded-[30px] border border-white/50 bg-white shadow">
                    <component
                      :is="publicComponents[catalog.type]"
                      :section="catalog.previewSection"
                      :previewDevice="'desktop'"
                      v-bind="catalog.type === 'hero' ? { branding } : {}"
                    />
                  </div>
                </div>
              </div>
              <div class="p-4">
                <p class="text-sm font-semibold text-slate-800">{{ catalog.label }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ catalog.description }}</p>
              </div>
              <div class="pointer-events-none absolute inset-0 flex items-center justify-center bg-slate-900/70 opacity-0 transition group-hover:opacity-100">
                <span class="rounded-full bg-white/20 px-4 py-1 text-xs font-semibold text-white backdrop-blur">Clique para inserir</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="space-y-4">
      <div class="rounded-2xl bg-white p-4 shadow-md" ref="sectionToolbarRef">
        <label class="text-sm font-semibold text-slate-600">Título</label>
        <input v-model.lazy="pageTitle" @blur="scheduleWhatsAppUpdate" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <label class="block text-sm font-semibold text-slate-600">Slug</label>
          <span class="text-xs text-slate-500">
            Slug é a parte do link depois da barra, sem espaços ou acentos. Ex.: meu-roteiro-incrivel.
          </span>
        </div>
        <input v-model.lazy="pageSlug" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        <div class="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-600">
          <label class="block text-sm font-semibold text-slate-600">Cores de fundo</label>
          <label class="flex items-center gap-2">
            <span>Cor 1</span>
            <input type="color" v-model="colorA" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
          </label>
          <label class="flex items-center gap-2">
            <span>Cor 2</span>
            <input type="color" v-model="colorB" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
          </label>
          <span class="text-xs text-slate-500">Aplica alternância em todas as seções (exceto hero).</span>
        </div>
        <div class="mt-6 rounded-2xl border border-slate-100 px-4 py-4">
          <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div class="space-y-1">
              <p class="text-sm font-semibold text-slate-700">Pixel de rastreamento</p>
              <p class="text-xs text-slate-500">
                Escolha um pixel cadastrado em Integrações e quais eventos deseja enviar. Disponível a partir do plano Essencial.
              </p>
            </div>

            <div class="w-full max-w-xl space-y-3">
              <div
                v-if="!canSelectPixel"
                class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
              >
                Adicione pixels na página Integrações (plano Essencial ou superior).
              </div>

              <template v-else>
                <select v-model="selectedPixel" class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800">
                  <option value="">Selecione</option>
                  <option v-for="p in pixels" :key="p.name" :value="p.name">
                    {{ p.name }} · {{ p.type === "meta" ? "Meta" : "GA4" }}
                  </option>
                </select>

                <div class="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
                  <p class="font-semibold text-slate-800">Eventos a enviar</p>

                  <label class="mt-2 flex items-center gap-2">
                    <input type="checkbox" v-model="trackingEvents.pageView" class="h-4 w-4" />
                    Page view (carregamento da página)
                  </label>

                  <label class="mt-1 flex items-center gap-2">
                    <input type="checkbox" v-model="trackingEvents.ctaClicks" class="h-4 w-4" />
                    Cliques em CTAs
                  </label>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

      <div class="rounded-3xl bg-white p-4 shadow-md" ref="previewPanelRef">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-col gap-1">
          <h2 class="text-lg font-semibold text-slate-900">Preview visual</h2>
          <p class="text-xs text-slate-500">Clique no botão do topo para aplicar as alterações do formulário.</p>
        </div>
        <div class="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-semibold text-slate-600">
          <button
            type="button"
            class="rounded-full px-3 py-1 transition"
            :class="previewDevice === 'desktop' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
            @click="previewDevice = 'desktop'"
          >
            Desktop
          </button>
          <button
            type="button"
            class="rounded-full px-3 py-1 transition"
            :class="previewDevice === 'mobile' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
            @click="previewDevice = 'mobile'"
          >
            Mobile
          </button>
        </div>
      </div>
      <div class="mt-4">
        <div
          :class="previewDevice === 'mobile'
            ? 'mx-auto w-full max-w-[420px] overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-xl'
            : ''"
        >
          <div :class="previewDevice === 'mobile' ? 'max-h-[80vh] overflow-y-auto' : ''">
            <div class="space-y-6">
              <template v-if="sections.length === 0">
                <div class="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 px-4 py-12 text-center text-sm text-slate-500">
                  Nenhuma seção adicionada ainda. Use os botões acima para criar o conteúdo.
                </div>
              </template>
              <template v-else>
                <template v-for="(section, idx) in sections" :key="(section as any)?.anchorId || idx">
                  <div v-if="section" class="space-y-3">
                    <div class="group relative overflow-hidden rounded-[32px] border border-transparent shadow transition hover:border-brand/30">
                      <component
                        v-if="(section as any).enabled"
                        :is="publicComponents[(section as any).type]"
                        :section="previewSections[idx] || section"
                        :previewDevice="previewDevice"
                        v-bind="(section as any).type === 'hero' ? { branding } : {}"
                      />
                      <div
                        v-if="(section as any).enabled"
                        class="pointer-events-none absolute inset-0 z-10 flex flex-col justify-between bg-slate-900/35 opacity-0 backdrop-blur-sm transition duration-200 group-hover:opacity-100 group-focus-within:opacity-100"
                      >
                        <div class="flex items-start justify-between gap-3 p-4">
                          <span class="pointer-events-auto inline-flex items-center rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate-700">
                            {{ sectionLabels[(section as any).type] || (section as any).type }}
                            <span v-if="(section as any).enabled === false" class="ml-1 text-red-500">(desativada)</span>
                          </span>
                          <div class="pointer-events-auto flex flex-wrap gap-2">
                            <button
                              type="button"
                              class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/50 bg-white/20 text-white transition hover:bg-white/30"
                              title="Duplicar seção"
                              @click.stop="duplicateSection(idx)"
                            >
                              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                                <rect x="9" y="9" width="11" height="11" rx="2" />
                                <rect x="4" y="4" width="11" height="11" rx="2" />
                              </svg>
                            </button>
                            <button
                              type="button"
                              class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/50 bg-white/20 text-white transition hover:bg-white/30 disabled:opacity-40 disabled:cursor-not-allowed"
                              title="Mover para cima"
                              :disabled="idx === 0"
                              @click.stop="moveSection(idx, -1)"
                            >
                              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                                <path d="m5 12 7-7 7 7" />
                                <path d="M12 5v14" />
                              </svg>
                            </button>
                            <button
                              type="button"
                              class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/50 bg-white/20 text-white transition hover:bg-white/30 disabled:opacity-40 disabled:cursor-not-allowed"
                              title="Mover para baixo"
                              :disabled="idx === sections.length - 1"
                              @click.stop="moveSection(idx, 1)"
                            >
                              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                                <path d="m19 12-7 7-7-7" />
                                <path d="M12 19V5" />
                              </svg>
                            </button>
                            <button
                              type="button"
                              class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-red-200 bg-white/10 text-red-200 transition hover:bg-white/20"
                              title="Excluir seção"
                              @click.stop="removeSection(idx)"
                            >
                              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                                <path d="M3 6h18" />
                                <path d="M8 6V4h8v2" />
                                <path d="m9 10 1 8" />
                                <path d="m15 10-1 8" />
                                <path d="M5 6l1 14h12l1-14" />
                              </svg>
                            </button>
                          </div>
                        </div>
                        <div class="pointer-events-auto pb-6 text-center">
                          <button
                            type="button"
                            class="mx-auto flex items-center gap-2 rounded-full border border-white/50 bg-white/20 px-5 py-2 text-sm font-semibold text-white shadow-lg hover:bg-white/30"
                            @click.stop="openSectionEditor(idx)"
                          >
                            <span class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/40 bg-white/10">
                              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 20h9" />
                                <path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z" />
                              </svg>
                            </span>
                            Editar seção
                          </button>
                        </div>
                      </div>
                      <div
                        v-else
                        class="bg-white/80 px-6 py-12 text-center text-sm font-semibold text-slate-500"
                      >
                        Seção desativada. Clique em editar para ajustar e ativar novamente.
                      </div>
                    </div>
                    <div class="mt-2 flex justify-center">
                      <button
                        type="button"
                        class="inline-flex items-center gap-2 rounded-full border border-dashed border-slate-300 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:border-brand/60 hover:text-brand"
                        @click="openSectionPicker(idx)"
                      >
                        <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M12 5v14" />
                          <path d="M5 12h14" />
                        </svg>
                        Adicionar seção abaixo
                      </button>
                    </div>
                  </div>
                </template>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <transition name="fade">
      <div
        v-if="showFloatingAddBar"
        class="pointer-events-none fixed bottom-4 z-30"
        :style="floatingToolbarStyle"
      >
        <div class="flex justify-center px-4">
          <div
            class="pointer-events-auto flex flex-wrap items-center gap-2 rounded-full border border-slate-200 bg-white/95 px-4 py-2 shadow-lg backdrop-blur"
          >
            <span class="text-sm font-semibold text-slate-700">Adicionar seção:</span>
            <div
              v-for="type in sectionTypes"
              :key="'floating-' + type"
              class="group relative"
            >
              <button
                class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-100"
                @click="addSection(type)"
              >
                {{ sectionLabels[type] || type }}
              </button>
              <div
                class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 w-48 -translate-x-1/2 rounded-2xl bg-slate-900/95 px-3 py-2 text-center text-[11px] font-medium text-white opacity-0 shadow-lg transition duration-200 group-hover:-translate-y-1 group-hover:opacity-100"
              >
                <p class="text-[11px] font-semibold text-white/90">{{ sectionLabels[type] || type }}</p>
                <p class="mt-1 text-[10px] text-white/70">
                  {{ sectionDescriptions[type] || "Bloco personalizável para compor sua página." }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <div
      v-if="isSectionEditorOpen && editingSectionComponent && editingSectionDraft"
      class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/70 px-4 py-10"
      @click.self="closeSectionEditor"
    >
      <div class="w-full max-w-4xl overflow-hidden rounded-3xl bg-white shadow-2xl">
        <div class="flex flex-col gap-1 border-b border-slate-100 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">Editar seção</p>
            <h3 class="text-lg font-semibold text-slate-900">{{ editingSectionLabel }}</h3>
          </div>
          <button
            class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            @click="closeSectionEditor"
          >
            Fechar
          </button>
        </div>
        <div class="max-h-[70vh] overflow-y-auto px-6 py-4">
          <component
            :is="editingSectionComponent"
            :modelValue="editingSectionDraft"
            @update:modelValue="updateEditingDraft"
          />
        </div>
        <div class="flex flex-wrap items-center justify-end gap-2 border-t border-slate-100 px-6 py-4">
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
            @click="closeSectionEditor"
          >
            Cancelar
          </button>
          <button
            class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark"
            @click="saveEditingSection"
          >
            Salvar seção
          </button>
        </div>
      </div>
    </div>
    <transition name="fade">
      <div
        v-if="snackbar.open"
        class="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-2xl"
      >
        {{ snackbar.text }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, provide, ref, shallowRef, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { useAgencyStore } from "../../store/useAgencyStore";
import type {
  CtaSection,
  EditorPreferences,
  FaqSection,
  HeroSection,
  ItinerarySection,
  PageConfig,
  PageSection,
  PricesSection,
  TestimonialsSection,
  StorySection,
  ReasonsSection,
  CountdownSection,
  SectionType,
  ThemeConfig
} from "../../types/page";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sectionsInjectionKey } from "../../components/admin/sectionsContext";
import { sectionLabels as defaultSectionLabels } from "../../utils/sectionLabels";

interface Page {
  id: number;
  title: string;
  slug: string;
  status: string;
  config_json?: PageConfig | string | null;
  cover_image_url?: string;
}

interface SectionCatalogItem {
  type: SectionType;
  label: string;
  description: string;
  accent: string;
  previewSection: PageSection;
}

const route = useRoute();
const router = useRouter();
const pageId = Number(route.params.id);

const page = ref<Page | null>(null);
const pageTitle = ref("");
const pageSlug = ref("");

const auth = useAuthStore();
const agencyStore = useAgencyStore();

const message = ref("");
const errorMessage = ref("");

const limitModal = ref({ open: false, message: "" });
const successModal = ref({ open: false });
const snackbar = ref({ open: false, text: "" });

const isPublished = computed(() => page.value?.status === "published");

const fallbackPrimaryColor = "#0ea5e9";
const heroDefaultGradient = "#0b0f19";
const legacyHeroGradient = "#0a4ddf";

const branding = ref({
  agency_name: "Agencia",
  logo_url: "",
  primary_color: fallbackPrimaryColor,
  secondary_color: fallbackPrimaryColor
});

const theme = ref<ThemeConfig>({
  color1: "#ffffff",
  color2: "#f8fafc",
  heroTheme: "immersive",
  ctaDefaultColor: fallbackPrimaryColor,
  ctaTextColor: "#0f172a",
  sidebarTheme: "light"
});

const editorPrefs = ref<EditorPreferences>({
  previewEnabled: true,
  previewLayout: "split",
  previewDevice: "desktop"
});

const colorA = ref(theme.value.color1);
const colorB = ref(theme.value.color2);
const previewDevice = ref<"desktop" | "mobile">(editorPrefs.value.previewDevice || "desktop");
const toolbarSecondaryButtonClass =
  "inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-white";
const toolbarPrimaryButtonClass =
  "inline-flex items-center gap-2 rounded-full border border-brand bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-dark";
const toolbarWarningButtonClass =
  "inline-flex items-center gap-2 rounded-full border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 transition hover:bg-amber-100";
const toolbarStatusPillClass =
  "inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700";

const buildCountdownTargetDate = () => {
  const date = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  return date.toISOString().slice(0, 16);
};

const SectionHeroForm = defineAsyncComponent(() => import("../../components/admin/SectionHeroForm.vue"));
const SectionPricesForm = defineAsyncComponent(() => import("../../components/admin/SectionPricesForm.vue"));
const SectionItineraryForm = defineAsyncComponent(() => import("../../components/admin/SectionItineraryForm.vue"));
const SectionFaqForm = defineAsyncComponent(() => import("../../components/admin/SectionFaqForm.vue"));
const SectionTestimonialsForm = defineAsyncComponent(() => import("../../components/admin/SectionTestimonialsForm.vue"));
const SectionCtaForm = defineAsyncComponent(() => import("../../components/admin/SectionCtaForm.vue"));
const SectionStoryForm = defineAsyncComponent(() => import("../../components/admin/SectionStoryForm.vue"));
const SectionReasonsForm = defineAsyncComponent(() => import("../../components/admin/SectionReasonsForm.vue"));
const SectionCountdownForm = defineAsyncComponent(() => import("../../components/admin/SectionCountdownForm.vue"));
const PublicHeroSection = defineAsyncComponent(() => import("../../components/public/PublicHeroSection.vue"));
const PublicPricesSection = defineAsyncComponent(() => import("../../components/public/PublicPricesSection.vue"));
const PublicItinerarySection = defineAsyncComponent(() => import("../../components/public/PublicItinerarySection.vue"));
const PublicFaqSection = defineAsyncComponent(() => import("../../components/public/PublicFaqSection.vue"));
const PublicTestimonialsSection = defineAsyncComponent(() => import("../../components/public/PublicTestimonialsSection.vue"));
const PublicCtaSection = defineAsyncComponent(() => import("../../components/public/PublicCtaSection.vue"));
const PublicStorySection = defineAsyncComponent(() => import("../../components/public/PublicStorySection.vue"));
const PublicReasonsSection = defineAsyncComponent(() => import("../../components/public/PublicReasonsSection.vue"));
const PublicCountdownSection = defineAsyncComponent(() => import("../../components/public/PublicCountdownSection.vue"));
const PublicFreeFooterBrandSection = defineAsyncComponent(() => import("../../components/public/PublicFreeFooterBrandSection.vue"));

const sectionTypes: SectionType[] = ["hero", "prices", "itinerary", "faq", "testimonials", "cta", "story", "reasons", "countdown"];
const sectionLabels = defaultSectionLabels;
const sectionDescriptions: Partial<Record<SectionType, string>> = {
  hero: "Bloco inicial com destaque visual, título, subtítulo e CTA principal.",
  prices: "Tabela com planos, valores e diferenciais para cada oferta.",
  itinerary: "Sequência de etapas/benefícios para explicar seu serviço ou roteiro.",
  faq: "Perguntas e respostas para antecipar dúvidas frequentes.",
  testimonials: "Carrossel ou lista com depoimentos de clientes.",
  cta: "Chamada final impulsionando o lead para a ação desejada.",
  story: "Bloco de storytelling para apresentar autoridade e conexão.",
  reasons: "Lista de motivos/benefícios para reforçar a decisão.",
  countdown: "Cria urgência com contador regressivo para promoções ou eventos."
};
const sectionAccents: Partial<Record<SectionType, string>> = {
  hero: "from-sky-100 to-slate-50",
  prices: "from-amber-100 to-white",
  itinerary: "from-emerald-100/70 to-white",
  faq: "from-slate-100 to-white",
  testimonials: "from-purple-100/70 to-white",
  cta: "from-cyan-100/70 to-white",
  story: "from-rose-100/70 to-white",
  reasons: "from-indigo-100/70 to-white",
  countdown: "from-orange-100/70 to-white"
};
const formComponents: Partial<Record<SectionType, any>> = {
  hero: SectionHeroForm,
  prices: SectionPricesForm,
  itinerary: SectionItineraryForm,
  faq: SectionFaqForm,
  testimonials: SectionTestimonialsForm,
  cta: SectionCtaForm,
  story: SectionStoryForm,
  reasons: SectionReasonsForm,
  countdown: SectionCountdownForm
};

const publicComponents: Partial<Record<SectionType, any>> = {
  hero: PublicHeroSection,
  prices: PublicPricesSection,
  itinerary: PublicItinerarySection,
  faq: PublicFaqSection,
  testimonials: PublicTestimonialsSection,
  cta: PublicCtaSection,
  story: PublicStorySection,
  reasons: PublicReasonsSection,
  countdown: PublicCountdownSection,
  free_footer_brand: PublicFreeFooterBrandSection
};

const sections = shallowRef<PageSection[]>([]);
const previewSections = ref<PageSection[]>([]);
const previewReady = ref(false);
const previewLoading = ref(false);
const sectionToolbarRef = ref<HTMLElement | null>(null);
const previewPanelRef = ref<HTMLElement | null>(null);
const showFloatingAddBar = ref(false);
const floatingToolbarStyle = ref<Record<string, string>>({ left: "0px", width: "auto" });
let toolbarObserver: IntersectionObserver | null = null;
const editingSectionIndex = ref<number | null>(null);
const editingSectionDraft = ref<PageSection | null>(null);
const sectionCatalog = ref<SectionCatalogItem[]>([]);
const sectionPicker = ref<{ open: boolean; index: number | null }>({ open: false, index: null });
const editingSectionType = computed<SectionType | null>(() => {
  if (editingSectionIndex.value === null) return null;
  const section = sections.value[editingSectionIndex.value];
  if (!section) return null;
  return ((section as any).type || null) as SectionType | null;
});
const editingSectionLabel = computed(() => {
  const type = editingSectionType.value;
  if (!type) return "";
  return sectionLabels[type] || type;
});
const editingSectionComponent = computed(() => {
  const type = editingSectionType.value;
  if (!type) return null;
  return formComponents[type];
});
const isSectionEditorOpen = computed(() => editingSectionIndex.value !== null && !!editingSectionDraft.value);
const hasWindow = typeof window !== "undefined";
const getBrowserStorage = () => {
  if (!hasWindow) return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
};
provide(sectionsInjectionKey, sections);

const updateFloatingToolbarStyle = () => {
  if (!hasWindow) return;
  const anchor = previewPanelRef.value || sectionToolbarRef.value;
  if (!anchor) return;
  const rect = anchor.getBoundingClientRect();
  floatingToolbarStyle.value = {
    left: `${Math.max(rect.left, 0)}px`,
    width: `${rect.width}px`
  };
};

const setupSectionToolbarObserver = () => {
  if (!hasWindow) return;
  if (toolbarObserver) {
    toolbarObserver.disconnect();
    toolbarObserver = null;
  }
  const el = sectionToolbarRef.value;
  if (!el) return;
  toolbarObserver = new IntersectionObserver(entries => {
    const entry = entries[0];
    const hidden = !!entry && !entry.isIntersecting;
    showFloatingAddBar.value = hidden;
    if (hidden) updateFloatingToolbarStyle();
  }, { threshold: 0.1 });
  toolbarObserver.observe(el);
};

watch(sectionToolbarRef, () => {
  if (!hasWindow) return;
  nextTick(() => setupSectionToolbarObserver());
});

watch(previewPanelRef, () => {
  if (!hasWindow) return;
  nextTick(() => updateFloatingToolbarStyle());
});

if (hasWindow) {
  window.addEventListener("resize", updateFloatingToolbarStyle);
}

const setSections = (value: PageSection[] | ((current: PageSection[]) => PageSection[])) => {
  const next = typeof value === "function" ? (value as (current: PageSection[]) => PageSection[])([...sections.value]) : value;
  sections.value = (next || []).filter(Boolean);
};

interface PendingSectionUpdate {
  timer: ReturnType<typeof setTimeout>;
  value: PageSection;
}
const pendingSectionUpdates: Record<number, PendingSectionUpdate> = {};
const commitSectionValue = (index: number, value: PageSection) => {
  const next = sections.value.slice();
  next[index] = value;
  sections.value = next;
};
const flushPendingSectionUpdates = () => {
  Object.keys(pendingSectionUpdates).forEach(key => {
    const index = Number(key);
    const pending = pendingSectionUpdates[index];
    if (!pending) return;
    clearTimeout(pending.timer);
    commitSectionValue(index, pending.value);
    delete pendingSectionUpdates[index];
  });
};
const updateSectionAt = (index: number, value: PageSection, immediate = false) => {
  if (pendingSectionUpdates[index]) {
    clearTimeout(pendingSectionUpdates[index].timer);
    delete pendingSectionUpdates[index];
  }

  if (immediate) {
    commitSectionValue(index, value);
    return;
  }

  const timer = setTimeout(() => {
    commitSectionValue(index, value);
    delete pendingSectionUpdates[index];
  }, 150);
  pendingSectionUpdates[index] = { timer, value };
};

const createAnchorId = () => `section-${Math.random().toString(36).slice(2, 9)}`;
const ensureSectionAnchor = <T extends PageSection>(section: T): T => {
  if (!section.anchorId) section.anchorId = createAnchorId();
  return section;
};
const cloneWithNewAnchor = <T extends PageSection>(section: T): T => ({ ...section, anchorId: createAnchorId() } as T);

const buildCatalogPreview = (type: SectionType): PageSection => {
  const base = clone(defaultSection(type));
  if (type === "hero") {
    (base as any).title = "Título impactante";
    (base as any).subtitle = "Explique rapidamente o benefício oferecido.";
  }
  if (Array.isArray((base as any).items)) {
    (base as any).items = (base as any).items.slice(0, 2);
  }
  if (Array.isArray((base as any).days)) {
    (base as any).days = (base as any).days.slice(0, 2);
  }
  return ensureSectionAnchor(base);
};

const templateKey = computed(() => (auth.user ? `page_template_${auth.user.id}` : null));
const whatsappDigits = computed(() => (auth.user?.whatsapp || "").replace(/\D/g, ""));
const buildWhatsappLink = (title: string) => {
  if (!whatsappDigits.value) return "";
  const text = encodeURIComponent(`Oi, tenho interesse no roteiro: ${title || "Roteiro"}`);
  return `https://wa.me/${whatsappDigits.value}?text=${text}`;
};
const lastAutoWhatsAppLink = ref<string | null>(null);

const pixels = ref<{ id: number; name: string; type: "meta" | "ga"; value: string }[]>([]);
const selectedPixel = ref<string | null>(null);
const trackingEvents = ref({ pageView: true, ctaClicks: true });

const canSelectPixel = computed(() => (auth.user?.plan || "free") !== "free" && pixels.value.length > 0);

const currentAgency = computed(() => {
  const selected = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return selected || agencyStore.agencies[0] || null;
});

const resolvePrimaryColor = () => currentAgency.value?.primary_color || fallbackPrimaryColor;

const fillHeroLogoFromAgency = () => {
  const logo = currentAgency.value?.logo_url;
  if (!logo) return;
  setSections(current =>
    current.map(section => {
      if ((section as any).type === "hero" && !(section as any).logoUrl) {
        return { ...(section as any), logoUrl: logo } as PageSection;
      }
      return section;
    })
  );
};

const applyAgencyBranding = () => {
  const primary = resolvePrimaryColor();
  const agency = currentAgency.value;
  branding.value = {
    ...branding.value,
    agency_name: agency?.name || branding.value.agency_name,
    logo_url: agency?.logo_url || branding.value.logo_url,
    primary_color: primary,
    secondary_color: agency?.secondary_color || primary
  };
  theme.value.ctaDefaultColor = primary;
  fillHeroLogoFromAgency();
};

const applyPrimaryToThemeAndSections = (oldDefault?: string) => {
  const primary = resolvePrimaryColor();
  const previous = oldDefault || theme.value.ctaDefaultColor;
  theme.value.ctaDefaultColor = primary;

  setSections(current =>
    applySectionBackgrounds(
      current.map(section => {
        if (!section) return section;
        if ((section as any).type === "countdown") {
          const countdownBg = (section as any).backgroundColor as string | undefined;
          const shouldReplaceCountdown =
            !countdownBg ||
            countdownBg.toLowerCase?.() === fallbackPrimaryColor.toLowerCase() ||
            (!!previous && countdownBg.toLowerCase?.() === previous.toLowerCase());
          if (shouldReplaceCountdown) (section as any).backgroundColor = primary;
        }
        const currentColor = (section as any).ctaColor as string | undefined;
        const shouldReplace =
          !currentColor ||
          currentColor.toLowerCase?.() === fallbackPrimaryColor.toLowerCase() ||
          (!!previous && currentColor.toLowerCase?.() === previous.toLowerCase());
        return shouldReplace ? ({ ...(section as any), ctaColor: primary } as any) : section;
      })
    )
  );
};

const loadPixels = async () => {
  try {
    const res = await api.get("/pixels/");
    pixels.value = res.data;
  } catch (err) {
    console.error("Erro ao carregar pixels", err);
  }
};

const clone = <T>(val: T): T => {
  try {
    // structuredClone pode nÃ£o existir em browsers antigos; fallback seguro
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    return typeof structuredClone === "function" ? structuredClone(val) : JSON.parse(JSON.stringify(val));
  } catch {
    return JSON.parse(JSON.stringify(val));
  }
};

const applyWhatsAppDefaults = (sectionsList: PageSection[]): PageSection[] => {
  const newAuto = buildWhatsappLink(pageTitle.value);
  const isAutoLink = (link?: string) => {
    if (!link) return true;
    const normalized = link.toLowerCase();
    const candidates = [lastAutoWhatsAppLink.value, "https://wa.me/559999999", "https://wa.me/5599999999"].filter(Boolean) as string[];
    if (candidates.some(c => normalized === c.toLowerCase())) return true;
    return normalized.includes("wa.me") && normalized.includes("interesse");
  };

  const updated = sectionsList.map(section => {
    const type = (section as any).type as SectionType;
    if (!["hero", "story", "cta"].includes(type) || !newAuto) return section;
    if ((section as any).ctaMode === "section") return section;
    if (type === "story" && (section as any).ctaEnabled === false) return section;
    const key = type === "cta" ? "link" : "ctaLink";
    const current = (section as any)[key] as string | undefined;
    if (!current || isAutoLink(current)) {
      (section as any)[key] = newAuto;
    }
    return section;
  });

  if (newAuto) lastAutoWhatsAppLink.value = newAuto;
  return updated;
};

const applySectionBackgrounds = (list: PageSection[]): PageSection[] => {
  const normalizeHeroGradient = (section: PageSection) => {
    if ((section as any).type !== "hero") return section;
    const current = (section as any).gradientColor as string | undefined;
    const isMissing = !current;
    const isLegacy = current?.toLowerCase?.() === legacyHeroGradient.toLowerCase();
    if (isMissing || isLegacy) {
      (section as any).gradientColor = heroDefaultGradient;
    }
    return section;
  };

  const ensureButtonColor = (section: PageSection) => {
    const type = (section as any).type as SectionType;
    const typesWithButton: SectionType[] = ["hero", "prices", "testimonials", "story", "cta"];
    if (typesWithButton.includes(type)) {
      const currentColor = (section as any).ctaColor;
      const needsDefault =
        !currentColor || currentColor.toLowerCase() === fallbackPrimaryColor.toLowerCase();
      if (needsDefault) {
        (section as any).ctaColor = theme.value.ctaDefaultColor;
      }
    }
    return section;
  };

  let altIndex = 0;
  const withWhatsApp = applyWhatsAppDefaults(list || []);
  return withWhatsApp.map(section => {
    if (!section) return section;
    const normalized = ensureButtonColor(normalizeHeroGradient(ensureSectionAnchor(section)));
    if (
      (normalized as any).type === "hero" ||
      (normalized as any).type === "countdown" ||
      (normalized as any).type === "free_footer_brand"
    ) {
      return normalized;
    }
    const backgroundColor = altIndex % 2 === 0 ? colorA.value : colorB.value;
    altIndex += 1;
    (normalized as any).backgroundColor = backgroundColor;
    return normalized;
  });
};

const buildConfig = (): PageConfig => ({
  version: 1,
  theme: { ...theme.value, color1: colorA.value, color2: colorB.value },
  editor: { ...editorPrefs.value, previewEnabled: true, previewDevice: previewDevice.value },
  sections: applySectionBackgrounds(sections.value),
  tracking: selectedPixel.value
    ? {
        pixel: pixels.value.find(p => p.name === selectedPixel.value) || null,
        events: { ...trackingEvents.value }
      }
    : undefined
});

const hydratePreviewSections = (source?: PageSection[]) => {
  const snapshot = source ? source : clone(sections.value);
  previewSections.value = applySectionBackgrounds(snapshot);
};

let previewFrame: number | null = null;
let previewTimeout: ReturnType<typeof setTimeout> | null = null;
let previewIdle: number | null = null;
let whatsappTitleDebounce: ReturnType<typeof setTimeout> | null = null;
const clearPreviewScheduler = () => {
  if (previewFrame !== null) {
    if (hasWindow && typeof window.cancelAnimationFrame === "function") {
      window.cancelAnimationFrame(previewFrame);
    }
    previewFrame = null;
  }
  if (previewIdle !== null) {
    if (hasWindow && typeof (window as any).cancelIdleCallback === "function") {
      (window as any).cancelIdleCallback(previewIdle);
    }
    previewIdle = null;
  }
  if (previewTimeout) {
    clearTimeout(previewTimeout);
    previewTimeout = null;
  }
  previewLoading.value = false;
};

const clearTitleDebounce = () => {
  if (whatsappTitleDebounce) {
    clearTimeout(whatsappTitleDebounce);
    whatsappTitleDebounce = null;
  }
};

const schedulePreviewHydration = (immediate = false) => {
  if (!previewReady.value) {
    clearPreviewScheduler();
    return;
  }

  const snapshot = clone(sections.value);
  const execute = () => {
    hydratePreviewSections(snapshot);
    previewLoading.value = false;
  };

  if (immediate) {
    previewLoading.value = true;
    execute();
    return;
  }

  clearPreviewScheduler();
  previewLoading.value = true;

  if (hasWindow) {
    const idle = (window as any).requestIdleCallback;
    if (typeof idle === "function") {
      previewIdle = idle(() => {
        previewIdle = null;
        execute();
      }, { timeout: 400 });
      return;
    }
    if (typeof window.requestAnimationFrame === "function") {
      previewFrame = window.requestAnimationFrame(() => {
        previewFrame = null;
        execute();
      });
      return;
    }
  }

  previewTimeout = setTimeout(() => {
    previewTimeout = null;
    execute();
  }, 100);
};

onBeforeUnmount(() => {
  clearPreviewScheduler();
  clearTitleDebounce();
  Object.values(pendingSectionUpdates).forEach(timeout => clearTimeout(timeout));
  if (toolbarObserver) {
    toolbarObserver.disconnect();
    toolbarObserver = null;
  }
  if (hasWindow) {
    window.removeEventListener("resize", updateFloatingToolbarStyle);
  }
});

function defaultSection(type: SectionType): PageSection {
  if (type === "hero") {
    return ensureSectionAnchor({
      type: "hero",
      enabled: true,
      layout: "immersive",
      title: "Viajar com conforto e segurança nunca foi tão fácil.",
      subtitle: "Conectamos você aos melhores destinos do Brasil com frota premium e atendimento próximo.",
      backgroundImage: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80",
      gradientColor: heroDefaultGradient,
      logoUrl: currentAgency.value?.logo_url || "",
      chips: ["Leito-cama 180º", "Wi-Fi a bordo", "Tomadas individuais", "Massagem a bordo"],
      ctaLabel: "Quero falar no WhatsApp",
      ctaLink: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
      ctaColor: theme.value.ctaDefaultColor,
      ctaMode: "link",
      ctaSectionId: null
    } as HeroSection);
  }

  if (type === "prices") {
    const headingDefaults = getSectionHeadingDefaults("prices");
    return ensureSectionAnchor({
      type: "prices",
      enabled: true,
      layout: "columns",
      headingLabel: headingDefaults.label,
      headingLabelStyle: headingDefaults.style,
      description: "Escolha o formato que combina com você.",
      items: [
        {
          title: "Apartamento duplo",
          price: 3490,
          description: "Por pessoa",
          titleLabel: "Pacote",
          priceLabel: "Por pessoa",
          currency: "BRL",
          badge: "",
          highlight: false
        }
      ],
      ctaColor: theme.value.ctaDefaultColor
    } as PricesSection);
  }

  if (type === "itinerary") {
    const headingDefaults = getSectionHeadingDefaults("itinerary");
    return ensureSectionAnchor({
      type: "itinerary",
      enabled: true,
      layout: "timeline",
      headingLabel: headingDefaults.label,
      headingLabelStyle: headingDefaults.style,
      days: [
        { day: "Dia 1", title: "Chegada", description: "Recepção no aeroporto e traslado." },
        { day: "Dia 2", title: "Trilhas", description: "Passeio pelas dunas e cachoeiras." }
      ]
    } as ItinerarySection);
  }

  if (type === "faq") {
    const headingDefaults = getSectionHeadingDefaults("faq");
    return ensureSectionAnchor({
      type: "faq",
      enabled: true,
      layout: "accordion",
      headingLabel: headingDefaults.label,
      headingLabelStyle: headingDefaults.style,
      items: [
        { question: "O que está incluído?", answer: "Hospedagem, transporte interno e passeios." },
        { question: "Como reservar?", answer: "Clique no botão de WhatsApp e fale com a equipe." }
      ]
    } as FaqSection);
  }

  if (type === "testimonials") {
    const headingDefaults = getSectionHeadingDefaults("testimonials");
    return ensureSectionAnchor({
      type: "testimonials",
      enabled: true,
      layout: "grid",
      headingLabel: headingDefaults.label,
      headingLabelStyle: headingDefaults.style,
      title: "Quem já viajou com a gente",
      subtitle: "Feedbacks reais de clientes",
      items: [{ name: "Mariana", text: "Viagem incrí­vel, super bem organizada!", avatar: "" }],
      cardColor: "#ffffff",
      ctaColor: theme.value.ctaDefaultColor,
      ctaMode: "link",
      ctaSectionId: null
    } as TestimonialsSection);
  }

  if (type === "story") {
    const headingDefaults = getSectionHeadingDefaults("story");
    return ensureSectionAnchor({
      type: "story",
      enabled: true,
      layout: "single",
      headingLabel: headingDefaults.label,
      headingLabelStyle: headingDefaults.style,
      imagePosition: "right",
      badge: "Sobre nós",
      title: "Conheça nossa história",
      subtitle: "Somos uma equipe apaixonada por criar experiências memoráveis de viagem, com atendimento próximo e cuidadoso.",
      ctaLabel: "Quero saber mais",
      ctaLink: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
      ctaColor: theme.value.ctaDefaultColor,
      ctaEnabled: true,
      ctaMode: "link",
      ctaSectionId: null,
      borderEnabled: false,
      borderColor: "#cbd5e1",
      images: [
        "https://images.unsplash.com/photo-1502920514313-52581002a659?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"
      ]
    } as StorySection);
  }

  if (type === "countdown") {
    const headingDefaults = getSectionHeadingDefaults("countdown");
    return ensureSectionAnchor({
      type: "countdown",
      enabled: true,
      headingLabel: headingDefaults.label,
      headingLabelStyle: headingDefaults.style,
      label: "Garanta sua vaga agora mesmo!",
      targetDate: buildCountdownTargetDate(),
      backgroundColor: resolvePrimaryColor(),
      textColor: "#ffffff",
      layout: "cards"
    } as CountdownSection);
  }

  if (type === "reasons") {
    const headingDefaults = getSectionHeadingDefaults("reasons");
    return ensureSectionAnchor({
      type: "reasons",
      enabled: true,
      headingLabel: headingDefaults.label,
      headingLabelStyle: headingDefaults.style,
      title: "Por que escolher a nossa agência?",
      subtitle: "Benefí­cios claros para ajudar na conversão",
      items: [
        { icon: "coin", title: "Economize dinheiro", description: "Aproveite negociações especiais e otimize seu orçamento." },
        { icon: "compass", title: "Mais liberdade", description: "Planeje quando quiser com apoio de especialistas locais." },
        { icon: "support", title: "Apoio dedicado", description: "Suporte próximo antes, durante e depois da viagem." },
        { icon: "spark", title: "Experiência única", description: "Curadoria de passeios e hospedagens memoráveis." }
      ]
    } as ReasonsSection);
  }

  const headingDefaults = getSectionHeadingDefaults("cta");
  return ensureSectionAnchor({
    type: "cta",
    enabled: true,
    layout: "simple",
    headingLabel: headingDefaults.label,
    headingLabelStyle: headingDefaults.style,
    label: "Quero reservar pelo WhatsApp",
    link: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
    description: "Fale com um especialista agora mesmo.",
    ctaColor: theme.value.ctaDefaultColor,
    textColor: theme.value.ctaTextColor,
    fullWidth: true,
    ctaMode: "link",
    ctaSectionId: null
  } as CtaSection);
}

const hydrateFromConfig = (config?: PageConfig | string | null) => {
  if (!config) return;

  try {
    const parsed = (typeof config === "string" ? JSON.parse(config) : config) as PageConfig;
    const oldDefaultCta = parsed.theme?.ctaDefaultColor;

    if (parsed.theme) {
      theme.value = { ...theme.value, ...parsed.theme };
      colorA.value = parsed.theme.color1 || colorA.value;
      colorB.value = parsed.theme.color2 || colorB.value;
    }

    if (parsed.editor) {
      editorPrefs.value = { ...editorPrefs.value, ...parsed.editor, previewEnabled: true };
      if (parsed.editor.previewDevice === "mobile" || parsed.editor.previewDevice === "desktop") {
        previewDevice.value = parsed.editor.previewDevice;
      }
    }

    if (parsed.sections && Array.isArray(parsed.sections) && parsed.sections.length) {
      setSections(applySectionBackgrounds(parsed.sections as PageSection[]));
      fillHeroLogoFromAgency();
    }

    // pixel selecionado e eventos
    const tracking: any = (parsed as any).tracking;
    if (tracking?.pixel?.name) selectedPixel.value = tracking.pixel.name;
    if (tracking?.events) {
      trackingEvents.value = {
        pageView: tracking.events.pageView !== false,
        ctaClicks: tracking.events.ctaClicks !== false
      };
    }

    applyPrimaryToThemeAndSections(oldDefaultCta);
  } catch (err) {
    console.error("Erro ao ler config_json", err);
  }
};

const fetchPage = async () => {
  if (!auth.token) {
    errorMessage.value = "Faça login novamente para editar.";
    return;
  }

  if (!auth.user) {
    try {
      await auth.fetchProfile();
    } catch (err) {
      errorMessage.value = "Sessão expirada. Faça login novamente.";
      return;
    }
  }

  try {
    const res = await api.get<Page>(`/pages/${pageId}`);
    page.value = res.data;
    pageTitle.value = res.data.title;
    pageSlug.value = res.data.slug;

    hydrateFromConfig(res.data.config_json);

    message.value = "";
  } catch (err) {
    console.error(err);
    errorMessage.value = "Não foi possível carregar a página.";
  }
};

const saveConfig = async () => {
  if (!auth.token) {
    errorMessage.value = "Sessão expirada. Faça login novamente.";
    return;
  }

  errorMessage.value = "";
  message.value = "";

  try {
    flushPendingSectionUpdates();
    await api.put(`/pages/${pageId}`, { title: pageTitle.value, slug: pageSlug.value });

    const configPayload = buildConfig();
    await api.put(`/pages/${pageId}/config`, { config: configPayload });

    message.value = "Configuração salva!";
    showSnackbar("Configuração salva");
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    if (detail) {
      limitModal.value = { open: true, message: String(detail) };
    } else {
      errorMessage.value = "Erro ao salvar configuração.";
    }
  }
};

const publishPage = async () => {
  if (!auth.token) {
    errorMessage.value = "Sessão expirada. Faça login novamente.";
    return;
  }

  errorMessage.value = "";
  message.value = "";

  try {
    await saveConfig();
    const res = await api.post(`/pages/${pageId}/publish`, { publish: true });
    page.value = res.data;

    message.value = "Página publicada!";
    successModal.value.open = true;
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;

    if (detail) {
      limitModal.value = { open: true, message: String(detail) };
    } else {
      errorMessage.value = "Erro ao publicar. Verifique se esta¡ logado e tem acesso a agência.";
    }
  }
};

const goBack = () => {
  router.back();
};

const goPlans = () => {
  router.push({ name: "plans" });
};

const openSectionPicker = (index: number | null = null) => {
  sectionPicker.value = { open: true, index };
};

const closeSectionPicker = () => {
  sectionPicker.value = { open: false, index: null };
};

const handleSectionPickerSelect = (type: SectionType) => {
  const afterIndex = sectionPicker.value.index;
  const insertAt = typeof afterIndex === "number" ? afterIndex + 1 : sections.value.length;
  addSection(type, insertAt);
  closeSectionPicker();
};

const addSection = (type: SectionType, insertIndex?: number) => {
  const next = clone(defaultSection(type));
  const current = sections.value.slice();
  if (typeof insertIndex === "number") {
    const safeIndex = Math.min(Math.max(insertIndex, 0), current.length);
    current.splice(safeIndex, 0, next);
  } else {
    current.push(next);
  }
  sections.value = current;
  refreshPreview(true);
};

const scheduleWhatsAppUpdate = () => {
  clearTitleDebounce();
  whatsappTitleDebounce = setTimeout(() => {
    sections.value = applyWhatsAppDefaults(sections.value.slice());
  }, 500);
};

const duplicateSection = (index: number) => {
  const copy = cloneWithNewAnchor(clone(sections.value[index]));
  const next = sections.value.slice();
  next.splice(index + 1, 0, copy);
  sections.value = next;
  refreshPreview(true);
};

const removeSection = (index: number) => {
  // Permite remover hero apenas se houver mais de um
  if ((sections.value[index] as any)?.type === "hero") {
    const heroCount = sections.value.filter(s => (s as any).type === "hero").length;
    if (heroCount <= 1) return;
  }
  const next = sections.value.slice();
  next.splice(index, 1);
  sections.value = next;
  refreshPreview(true);
};

const moveSection = (index: number, direction: number) => {
  const target = index + direction;
  if (target < 0 || target >= sections.value.length) return;

  setSections(current => {
    const next = [...current];
    const temp = next[index];
    next[index] = next[target];
    next[target] = temp;
    return next;
  });
  refreshPreview(true);
};

const openSectionEditor = (index: number) => {
  const target = sections.value[index];
  if (!target) return;
  editingSectionIndex.value = index;
  editingSectionDraft.value = clone(target);
};

const closeSectionEditor = () => {
  editingSectionIndex.value = null;
  editingSectionDraft.value = null;
};

const updateEditingDraft = (value: PageSection) => {
  if (!editingSectionDraft.value) {
    editingSectionDraft.value = value;
    return;
  }
  Object.assign(editingSectionDraft.value, value);
};

watch([colorA, colorB], ([a, b], [_prevA, prevB]) => {
  if (a.toLowerCase() === b.toLowerCase()) {
    colorB.value = prevB || "#ffffff";
  }
});

watch(colorA, value => {
  theme.value.color1 = value;
});

watch(colorB, value => {
  theme.value.color2 = value;
});

watch(previewDevice, value => {
  editorPrefs.value.previewDevice = value;
});

const refreshPreview = (immediate = false) => {
  flushPendingSectionUpdates();
  schedulePreviewHydration(immediate);
};

const saveEditingSection = () => {
  if (editingSectionIndex.value === null || !editingSectionDraft.value) return;
  updateSectionAt(editingSectionIndex.value, editingSectionDraft.value, true);
  closeSectionEditor();
  refreshPreview(true);
};

const setDefaultSectionsByPlan = () => {
  const plan = auth.user?.plan || "free";

  if (plan === "free") {
    setSections([defaultSection("hero"), defaultSection("story"), defaultSection("itinerary"), defaultSection("cta")]);
  } else {
    const storyRight = defaultSection("story") as any;
    storyRight.imagePosition = "right";

    const storyLeft = defaultSection("story") as any;
    storyLeft.imagePosition = "left";

    setSections([
      defaultSection("hero"),
      defaultSection("reasons"),
      storyRight,
      storyLeft,
      defaultSection("itinerary"),
      defaultSection("countdown"),
      defaultSection("cta")
    ]);
  }
};

const ensureProfile = async () => {
  if (!auth.user) {
    try {
      await auth.fetchProfile();
    } catch {
      /* ignore */
    }
  }
};

const applySavedTemplate = (): boolean => {
  const key = templateKey.value;
  if (!key) return false;

  const storage = getBrowserStorage();
  if (!storage) return false;

  try {
    const saved = storage.getItem(key);
    if (!saved) return false;

    const parsed = JSON.parse(saved);
    const oldDefaultCta = parsed.theme?.ctaDefaultColor;

    if (parsed.theme) {
      theme.value = { ...theme.value, ...parsed.theme };
      if (parsed.theme.color1) colorA.value = parsed.theme.color1;
      if (parsed.theme.color2) colorB.value = parsed.theme.color2;
    }

    if (parsed.sections && Array.isArray(parsed.sections) && parsed.sections.length) {
      setSections(applySectionBackgrounds(parsed.sections as PageSection[]));
      applyPrimaryToThemeAndSections(oldDefaultCta);
      return true;
    }
  } catch (err) {
    console.error("Erro ao aplicar template salvo", err);
  }

  return false;
};

const showSnackbar = (text: string) => {
  snackbar.value = { open: true, text };
  setTimeout(() => (snackbar.value.open = false), 3000);
};

/**
 * âœ… BLOQUEIO: plano free NÃƒO pode salvar template.
 * Deve abrir dialog com Fechar / Ver planos.
 */
const saveTemplate = () => {
  // se nÃ£o logou
  if (!auth.user) {
    errorMessage.value = "Faça login para salvar um template.";
    return;
  }

  // bloqueio do plano free
  const plan = auth.user?.plan || "free";
  if (plan === "free") {
    limitModal.value = {
      open: true,
      message: "Salvar template esta¡ disponí­vel apenas a partir do plano Essencial. Atualize seu plano para liberar."
    };
    return;
  }

  const key = templateKey.value;
  if (!key) {
    errorMessage.value = "Faça login para salvar um template.";
    return;
  }

  try {
    flushPendingSectionUpdates();
    const payload = {
      sections: sections.value,
      theme: { ...theme.value, color1: colorA.value, color2: colorB.value }
    };

    const storage = getBrowserStorage();
    if (!storage) {
      errorMessage.value = "Recurso indisponivel no momento.";
      return;
    }

    storage.setItem(key, JSON.stringify(payload));
    message.value = "Template salvo! Novas páginas iniciarão com essa estrutura.";
    showSnackbar("Template salvo com sucesso");
  } catch (err) {
    console.error(err);
    errorMessage.value = "Não foi possí­vel salvar o template.";
  }
};

const ensureAgencies = async () => {
  if (!agencyStore.agencies.length) {
    try {
      await agencyStore.loadAgencies();
    } catch {
      /* ignore */
    }
  }
  applyPrimaryToThemeAndSections();
};

const publicUrl = computed(() => {
  const agencySlug = agencyStore.agencies[0]?.slug;
  const slug = pageSlug.value || page.value?.slug;
  if (!agencySlug || !slug) return null;
  return `/${agencySlug}/${slug}`;
});

const goPages = () => {
  router.push({ name: "pages" });
};

const viewPublicPage = () => {
  if (!publicUrl.value || !hasWindow) return;
  window.open(publicUrl.value, "_blank");
};

onMounted(async () => {
  await ensureProfile();
  await ensureAgencies();
  applyAgencyBranding();
  loadPixels();

  const applied = applySavedTemplate();
  if (!applied) setDefaultSectionsByPlan();

  await fetchPage();
  sectionCatalog.value = sectionTypes.map(type => ({
    type,
    label: sectionLabels[type] || type,
    description: sectionDescriptions[type] || "Bloco personalizável para compor sua página.",
    accent: sectionAccents[type] || "from-slate-100 to-white",
    previewSection: buildCatalogPreview(type)
  }));
  previewReady.value = true;
  schedulePreviewHydration(true);
  nextTick(() => setupSectionToolbarObserver());
});
</script>






