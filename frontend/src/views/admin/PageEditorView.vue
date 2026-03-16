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
          :disabled="!hasUnsavedChanges"
          :class="[toolbarPrimaryButtonClass, { 'opacity-60 cursor-not-allowed': !hasUnsavedChanges }]"
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

    <!-- Diálogo de confirmação ao sair sem salvar -->
    <div
      v-if="unsavedNavigationModal.open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4"
    >
      <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">Atenção</p>
        <h3 class="mt-2 text-xl font-bold text-slate-900">Alterações não salvas</h3>
        <p class="mt-2 text-sm text-slate-600">
          Você tem mudanças não salvas nesta página. Deseja salvar antes de sair?
        </p>

        <div class="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            @click="cancelNavigationModal"
          >
            Continuar editando
          </button>
          <button
            type="button"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            @click="discardAndLeave"
          >
            Descartar e sair
          </button>
          <button
            type="button"
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-brand-dark disabled:opacity-60"
            :disabled="unsavedNavigationModal.saving"
            @click="saveAndLeave"
          >
            {{ unsavedNavigationModal.saving ? "Salvando..." : "Salvar e sair" }}
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
                <template v-if="catalog.thumbnail">
                  <img :src="catalog.thumbnail" alt="" class="h-full w-full object-cover" />
                  <div class="absolute inset-0 bg-gradient-to-t from-black/35 to-transparent"></div>
                </template>
                <template v-else>
                  <div class="absolute inset-0 bg-gradient-to-br" :class="catalog.accent"></div>
                  <div class="relative flex h-full w-full items-center justify-center overflow-hidden p-3">
                    <div class="pointer-events-none origin-center scale-[0.55] transform rounded-[30px] border border-white/50 bg-white shadow">
                      <component
                        :is="publicComponents[catalog.type]"
                        :section="catalog.previewSection"
                        :previewDevice="'desktop'"
                        v-bind="sectionRequiresBranding(catalog.type) ? { branding } : {}"
                      />
                    </div>
                  </div>
                </template>
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
      <div class="rounded-2xl bg-white p-4 shadow-md">
        <div class="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-semibold text-slate-600">Título</label>
            <input v-model="pageTitle" @blur="scheduleWhatsAppUpdate" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <label class="text-sm font-semibold text-slate-600">Slug</label>
              <span class="text-xs text-slate-500">Slug é a parte do link depois da barra, sem espaços ou acentos. Ex.: meu-roteiro-incrivel.</span>
            </div>
            <input
              :value="pageSlug"
              @input="handleSlugInput"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
        </div>
        <div class="mt-4 grid gap-4 text-sm text-slate-600 md:grid-cols-2">
          <div>
            <div class="flex items-center gap-2">
              <label class="block text-sm font-semibold text-slate-600">Cores de fundo</label>
              <span class="text-xs text-slate-500">Aplica alternância em todas as seções (exceto hero).</span>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-2">
              <label class="flex items-center gap-2">
                <span>Cor 1</span>
                <input type="color" v-model="colorA" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
              </label>
              <label class="flex items-center gap-2">
                <span>Cor 2</span>
                <input type="color" v-model="colorB" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
              </label>
            </div>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <label class="text-sm font-semibold text-slate-600">Cor de botões e destaques</label>
              <span class="text-xs text-slate-500">Afeta CTAs, chips e elementos em destaque.</span>
            </div>
            <div class="mt-1 flex items-center gap-2">
              <input
                type="color"
                v-model="ctaColor"
                class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white"
              />
              <button
                type="button"
                class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-100"
                @click="refreshCtaColors"
              >
                Atualizar cores
              </button>
            </div>
          </div>
        </div>
        <div class="mt-6 rounded-2xl border border-slate-100 px-4 py-4">
          <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div class="space-y-1">
              <p class="text-sm font-semibold text-slate-700">Pixel de rastreamento</p>
              <p class="text-xs text-slate-500">
                Escolha um pixel cadastrado em Integrações e quais eventos deseja enviar.
              </p>
              <p v-if="!canSelectPixel" class="text-xs text-slate-500">
                Disponível a partir do plano Essencial.
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
                <div class="grid gap-3 md:grid-cols-2">
                  <div>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Pixel Meta</label>
                    <select
                      v-model="selectedPixels.meta"
                      class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800"
                      :disabled="!metaPixelOptions.length"
                    >
                      <option value="">Sem pixel Meta</option>
                      <option v-for="p in metaPixelOptions" :key="p.name" :value="p.name">
                        {{ p.name }} – Meta
                      </option>
                    </select>
                    <p v-if="!metaPixelOptions.length" class="mt-1 text-xs text-slate-500">Cadastre uma conexão Meta em Integrações.</p>
                  </div>
                  <div>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Pixel Google</label>
                    <select
                      v-model="selectedPixels.ga"
                      class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800"
                      :disabled="!gaPixelOptions.length"
                    >
                      <option value="">Sem pixel Google</option>
                      <option v-for="p in gaPixelOptions" :key="p.name" :value="p.name">
                        {{ p.name }} – GA4
                      </option>
                    </select>
                    <p v-if="!gaPixelOptions.length" class="mt-1 text-xs text-slate-500">Cadastre uma conexão GA4 em Integrações.</p>
                  </div>
                </div>

                <div class="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
                  <p class="font-semibold text-slate-800">Eventos a enviar</p>

                  <div class="mt-2 flex flex-wrap gap-4">
                    <label class="flex items-center gap-2">
                      <input type="checkbox" v-model="trackingEvents.pageView" class="h-4 w-4" />
                      Page view (carregamento da página)
                    </label>

                    <label class="flex items-center gap-2">
                      <input type="checkbox" v-model="trackingEvents.ctaClicks" class="h-4 w-4" />
                      Cliques em CTAs
                    </label>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

      <div class="md:sticky md:top-6 rounded-3xl bg-white p-4 shadow-md">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-col gap-1">
          <h2 class="text-lg font-semibold text-slate-900">Preview visual</h2>
          <p class="text-xs text-slate-500">Clique no botão do topo para aplicar as alterações do formulário.</p>
          <p
            v-if="isMobileViewport && previewDevice === 'mobile'"
            class="rounded-2xl bg-amber-100 px-3 py-2 text-center text-sm font-semibold text-amber-700"
          >
            Toque sobre as seções para editar.
          </p>
        </div>
        <div
          v-if="!isMobileViewport"
          class="inline-flex select-none items-center rounded-full border border-slate-200 bg-slate-50 p-1 text-sm font-semibold text-slate-600"
        >
          <button
            v-if="!isMobileViewport"
            type="button"
            class="inline-flex select-none items-center gap-1 rounded-full px-3 py-1 transition"
            :class="previewDevice === 'desktop' ? 'bg-brand text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'"
            @click="previewDevice = 'desktop'"
          >
            <span aria-hidden="true">🖥️</span> Desktop
          </button>
          <button
            type="button"
            class="inline-flex select-none items-center gap-1 rounded-full px-3 py-1 transition"
            :class="previewDevice === 'mobile' ? 'bg-brand text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'"
            @click="previewDevice = 'mobile'"
          >
            <span aria-hidden="true">📱</span> Mobile
          </button>
        </div>
      </div>
      <div class="mt-4">
        <div
          :class="previewDevice === 'mobile'
            ? (isMobileViewport
              ? '-mx-4 w-[calc(100%+2rem)] overflow-hidden rounded-none border-0 bg-transparent shadow-none'
              : 'mx-auto w-full max-w-[420px] overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-xl')
            : ''"
        >
          <div :class="previewDevice === 'mobile' ? 'max-h-none overflow-visible' : ''">
            <div class="space-y-6">
              <template v-if="sections.length === 0">
                <div class="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 px-4 py-12 text-center text-sm text-slate-500">
                  Nenhuma seção adicionada ainda. Use os botões acima para criar o conteúdo.
                </div>
              </template>
              <template v-else>
                <template v-for="(section, idx) in sections" :key="(section as any)?.anchorId || idx">
                    <div v-if="section" class="space-y-3">
                    <div
                      class="group relative overflow-hidden rounded-[32px] border border-transparent shadow transition hover:border-brand/30"
                      @click.capture="handleSectionTap(idx, $event)"
                      :ref="el => registerPreviewSection(el, idx)"
                    >
                      <component
                        v-if="(section as any).enabled"
                        :is="publicComponents[(section as any).type]"
                        :section="previewSections[idx] || section"
                        :previewDevice="previewDevice"
                        v-bind="sectionRequiresBranding((section as any).type) ? { branding } : {}"
                      />
                        <div
                          v-if="(section as any).enabled"
                          :class="[
                            'pointer-events-none absolute inset-0 z-10 flex flex-col bg-transparent opacity-0 transition duration-200 px-4 py-5',
                            !isMobileOverlayMode ? 'group-hover:opacity-100 group-focus-within:opacity-100' : '',
                            isMobileOverlayMode && mobileOverlayVisible[idx] ? '!opacity-100' : ''
                          ]"
                        >
                          <div class="flex items-start justify-between gap-3 pb-3">
                            <span class="pointer-events-auto inline-flex items-center rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate-700 shadow">
                              {{ sectionLabels[(section as any).type] || (section as any).type }}
                              <span v-if="(section as any).enabled === false" class="ml-1 text-red-500">(desativada)</span>
                            </span>
                          </div>
                        <div class="flex flex-1 items-center justify-center px-4 pb-8">
                          <div
                            class="pointer-events-auto relative rounded-[36px] bg-slate-900/85 px-7 py-6 text-center shadow-2xl backdrop-blur-lg"
                            @click.stop
                          >
                            <template v-if="!isLockedFooterSection(section)">
                            <div
                              :class="[
                                isMobileOverlayMode
                                  ? 'grid w-full grid-cols-2 gap-2'
                                  : 'flex flex-wrap items-center justify-center gap-3'
                              ]"
                            >
                              <button
                                type="button"
                                class="inline-flex items-center gap-2 rounded-full border border-white/40 bg-white/20 text-xs font-semibold text-white shadow-md transition hover:bg-white/30"
                                :class="[overlayButtonSizingClass, isMobileOverlayMode ? 'col-span-2' : '']"
                                @click.stop="openSectionEditor(idx)"
                              >
                                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                  <path d="M12 20h9" />
                                  <path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z" />
                                </svg>
                                Editar seção
                              </button>
                              <button
                                type="button"
                                class="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 text-xs font-semibold text-white transition hover:bg-white/20 disabled:opacity-40 disabled:cursor-not-allowed"
                                :class="overlayButtonSizingClass"
                                :disabled="idx === 0"
                                @click.stop="moveSection(idx, -1)"
                              >
                                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                                  <path d="m5 12 7-7 7 7" />
                                  <path d="M12 5v14" />
                                </svg>
                                Subir
                              </button>
                              <button
                                type="button"
                                class="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 text-xs font-semibold text-white transition hover:bg-white/20 disabled:opacity-40 disabled:cursor-not-allowed"
                                :class="overlayButtonSizingClass"
                                :disabled="idx === sections.length - 1"
                                @click.stop="moveSection(idx, 1)"
                              >
                                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                                  <path d="m19 12-7 7-7-7" />
                                  <path d="M12 19V5" />
                                </svg>
                                Descer
                              </button>
                              <button
                                type="button"
                                class="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 text-xs font-semibold text-white shadow-sm transition hover:bg-white/20"
                                :class="overlayButtonSizingClass"
                                @click.stop="duplicateSection(idx)"
                              >
                                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                                  <rect x="9" y="9" width="11" height="11" rx="2" />
                                  <rect x="4" y="4" width="11" height="11" rx="2" />
                                </svg>
                                Duplicar
                              </button>
                              <button
                                type="button"
                                class="inline-flex items-center gap-2 rounded-full border border-red-300/70 bg-red-400/10 text-xs font-semibold text-red-100 transition hover:bg-red-400/20"
                                :class="overlayButtonSizingClass"
                                @click.stop="removeSection(idx)"
                              >
                                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                                  <path d="M3 6h18" />
                                  <path d="M8 6V4h8v2" />
                                  <path d="m9 10 1 8" />
                                  <path d="m15 10-1 8" />
                                  <path d="M5 6l1 14h12l1-14" />
                                </svg>
                                Excluir
                              </button>
                            </div>
                          </template>
                          <template v-else>
                            <div class="rounded-full border border-white/30 bg-white/10 px-4 py-2 text-center text-xs font-semibold text-white">
                              Rodapé obrigatório no plano gratuito. Não é possível editar, mover ou remover esta seção.
                            </div>
                          </template>
                          </div>
                        </div>
                      </div>
                      <div
                        v-else
                        class="bg-white/80 px-6 py-12 text-center text-sm font-semibold text-slate-500"
                      >
                        Seção desativada. Clique em editar para ajustar e ativar novamente.
                      </div>
                    </div>
                    <div v-if="!isLockedFooterSection(section)" class="mt-4 flex justify-center">
                      <button
                        type="button"
                        class="inline-flex items-center gap-2 rounded-full border border-emerald-400 bg-emerald-50 px-5 py-3 text-sm font-semibold text-emerald-700 shadow-sm transition hover:bg-emerald-100"
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

    <Teleport to="body">
      <div
        v-if="isSectionEditorOpen && editingSectionComponent && editingSectionDraft"
        class="fixed inset-0 z-40 flex h-full w-full items-center justify-center bg-slate-900/80 px-4 py-10 md:py-20 backdrop-blur-sm"
        @click.self="closeSectionEditor"
      >
        <div
          class="w-full max-w-4xl overflow-hidden rounded-3xl bg-white shadow-2xl"
          :class="isMobileViewport ? 'max-h-[75vh]' : 'md:max-h-none md:rounded-[32px] md:shadow-2xl'"
        >
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
          <div
            :class="isMobileViewport ? 'max-h-[calc(75vh-11rem)]' : 'max-h-[70vh]'"
            class="overflow-y-auto px-6 py-4"
          >
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
    </Teleport>
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
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, provide, reactive, ref, shallowRef, watch } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { useAgencyStore } from "../../store/useAgencyStore";
import { slugify } from "../../utils/slugify";
import type {
  BannerCardSection,
  CtaSection,
  EditorPreferences,
  FaqSection,
  HeroSection,
  ItinerarySection,
  PageConfig,
  PageSection,
  PhotoSection,
  PricesSection,
  FeaturedVideoSection,
  TestimonialsSection,
  StorySection,
  ReasonsSection,
  CountdownSection,
  AgencyFooterSection,
  SectionType,
  ThemeConfig
} from "../../types/page";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sectionsInjectionKey } from "../../components/admin/sectionsContext";
import { sectionUploadGuardKey } from "../../components/admin/sectionUploadGuard";
import { sectionLabels as defaultSectionLabels } from "../../utils/sectionLabels";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { getReadableTextColor } from "../../utils/colorContrast";
import heroThumb from "../../assets/hero-thumb.jpg";
import bannerCardThumb from "../../assets/banner-card-thumb.jpg";
import photoThumb from "../../assets/photo-thumb.jpg";
import pricesThumb from "../../assets/prices-thumb.jpg";
import itineraryThumb from "../../assets/itinerary-thumb.jpg";
import faqThumb from "../../assets/faq-thumb.jpg";
import testimonialsThumb from "../../assets/testimonials-thumb.jpg";
import ctaThumb from "../../assets/cta-thumb.jpg";
import reasonsThumb from "../../assets/reasons-thumb.jpg";
import footerThumb from "../../assets/footer-thumb.jpg";
import countdownThumb from "../../assets/countdown-thumb.jpg";
import storyThumb from "../../assets/story-thumb.jpg";
import featuredVideoThumb from "../../assets/videoemdestaque.png";

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
  thumbnail?: string;
}

const route = useRoute();
const router = useRouter();
const pageId = Number(route.params.id);
onBeforeRouteLeave((to, _from, next) => {
  if (!hasUnsavedChanges.value) {
    next();
    return;
  }
  pendingNavigationPath.value = to.fullPath || null;
  unsavedNavigationModal.value.open = true;
  unsavedNavigationModal.value.saving = false;
  next(false);
});

const page = ref<Page | null>(null);
const pageTitle = ref("");
const pageSlug = ref("");
const slugAutoSyncEnabled = ref(true);
const PAGE_SLUG_FALLBACK = "pagina";

const normalizeSlugInput = (value: string | undefined | null) => {
  const trimmed = (value || "").trim();
  if (!trimmed) return "";
  return slugify(trimmed, PAGE_SLUG_FALLBACK);
};

const handleSlugInput = (event: Event) => {
  slugAutoSyncEnabled.value = false;
  const target = event.target as HTMLInputElement;
  pageSlug.value = normalizeSlugInput(target.value);
};

watch(
  pageTitle,
  newTitle => {
    if (!slugAutoSyncEnabled.value) return;
    pageSlug.value = normalizeSlugInput(newTitle);
  }
);
watch(pageTitle, () => markUnsavedChanges());
watch(pageSlug, () => markUnsavedChanges());

const auth = useAuthStore();
const agencyStore = useAgencyStore();

const message = ref("");
const errorMessage = ref("");

const ensureValidPageSlug = () => {
  const normalized = normalizeSlugInput(pageSlug.value);
  if (!normalized) {
    const slugError = "Defina um slug válido para a página.";
    errorMessage.value = slugError;
    showSnackbar(slugError);
    return false;
  }
  pageSlug.value = normalized;
  return true;
};

const limitModal = ref({ open: false, message: "" });
const successModal = ref({ open: false });
const snackbar = ref({ open: false, text: "" });
const hasUnsavedChanges = ref(false);
const initialLoadComplete = ref(false);
const unsavedNavigationModal = ref({ open: false, saving: false });
const pendingNavigationPath = ref<string | null>(null);
const savedStateSnapshot = ref("");

const computeStateSnapshot = () => {
  const themeSnapshot = {
    heroTheme: theme.value.heroTheme,
    sidebarTheme: theme.value.sidebarTheme,
    ctaTextColor: theme.value.ctaTextColor,
    ctaDefaultColor: ctaColor.value,
    color1: colorA.value,
    color2: colorB.value
  };
  const editorSnapshot = {
    previewLayout: editorPrefs.value.previewLayout,
    previewDevice: previewDevice.value
  };
  return JSON.stringify({
    title: pageTitle.value,
    slug: pageSlug.value,
    theme: themeSnapshot,
    editor: editorSnapshot,
    sections: sections.value
  });
};

const syncSavedSnapshot = () => {
  savedStateSnapshot.value = computeStateSnapshot();
  hasUnsavedChanges.value = false;
};

const refreshUnsavedState = () => {
  if (!initialLoadComplete.value) return;
  const current = computeStateSnapshot();
  hasUnsavedChanges.value = current !== savedStateSnapshot.value;
};

const markUnsavedChanges = () => {
  refreshUnsavedState();
};

const isPublished = computed(() => page.value?.status === "published");
const isFreePlan = computed(() => (auth.user?.plan || "free") === "free");

const fallbackPrimaryColor = "#41ce5f";
const heroDefaultGradient = "#0b0f19";
const legacyHeroGradient = "#0a4ddf";

const branding = ref({
  agency_name: "Agencia",
  logo_url: "",
  primary_color: fallbackPrimaryColor,
  secondary_color: fallbackPrimaryColor,
  agency_profile: {}
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
const ctaColor = ref(theme.value.ctaDefaultColor || fallbackPrimaryColor);
const previewDevice = ref<"desktop" | "mobile">(editorPrefs.value.previewDevice || "desktop");
const isMobileViewport = ref(false);
const isMobileOverlayMode = computed(() => previewDevice.value === "mobile" || isMobileViewport.value);
const hasWindow = typeof window !== "undefined";
const beforeUnloadHandler = (event: BeforeUnloadEvent) => {
  if (!hasUnsavedChanges.value) return;
  event.preventDefault();
  event.returnValue = "";
};

watch(
  hasUnsavedChanges,
  value => {
    if (!hasWindow) return;
    if (value) {
      window.addEventListener("beforeunload", beforeUnloadHandler);
    } else {
      window.removeEventListener("beforeunload", beforeUnloadHandler);
    }
  },
  { immediate: false }
);
const toolbarSecondaryButtonClass =
  "inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-white";
const toolbarPrimaryButtonClass =
  "inline-flex items-center gap-2 rounded-full border border-brand bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-dark";
const toolbarWarningButtonClass =
  "inline-flex items-center gap-2 rounded-full border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 transition hover:bg-amber-100";
const toolbarStatusPillClass =
  "inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700";
let skipCtaWatcher = false;
let removeViewportWatcher: (() => void) | null = null;

const syncMobileViewport = () => {
  if (!hasWindow) return;
  const matches = window.innerWidth < 768;
  isMobileViewport.value = matches;
  if (matches && previewDevice.value !== "mobile") {
    previewDevice.value = "mobile";
  }
};

const setupViewportWatcher = () => {
  if (!hasWindow) return;
  syncMobileViewport();
  const handler = () => syncMobileViewport();
  window.addEventListener("resize", handler);
  removeViewportWatcher = () => {
    window.removeEventListener("resize", handler);
  };
};

const buildCountdownTargetDate = () => {
  const date = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  return date.toISOString().slice(0, 16);
};

const SectionHeroForm = defineAsyncComponent(() => import("../../components/admin/SectionHeroForm.vue"));
const SectionBannerCardForm = defineAsyncComponent(() => import("../../components/admin/SectionBannerCardForm.vue"));
const SectionPricesForm = defineAsyncComponent(() => import("../../components/admin/SectionPricesForm.vue"));
const SectionPhotoForm = defineAsyncComponent(() => import("../../components/admin/SectionPhotoForm.vue"));
const SectionItineraryForm = defineAsyncComponent(() => import("../../components/admin/SectionItineraryForm.vue"));
const SectionFaqForm = defineAsyncComponent(() => import("../../components/admin/SectionFaqForm.vue"));
const SectionTestimonialsForm = defineAsyncComponent(() => import("../../components/admin/SectionTestimonialsForm.vue"));
const SectionFeaturedVideoForm = defineAsyncComponent(() => import("../../components/admin/SectionFeaturedVideoForm.vue"));
const SectionCtaForm = defineAsyncComponent(() => import("../../components/admin/SectionCtaForm.vue"));
const SectionStoryForm = defineAsyncComponent(() => import("../../components/admin/SectionStoryForm.vue"));
const SectionReasonsForm = defineAsyncComponent(() => import("../../components/admin/SectionReasonsForm.vue"));
const SectionCountdownForm = defineAsyncComponent(() => import("../../components/admin/SectionCountdownForm.vue"));
const SectionAgencyFooterForm = defineAsyncComponent(() => import("../../components/admin/SectionAgencyFooterForm.vue"));
const PublicHeroSection = defineAsyncComponent(() => import("../../components/public/PublicHeroSection.vue"));
const PublicBannerCardSection = defineAsyncComponent(() => import("../../components/public/PublicBannerCardSection.vue"));
const PublicPricesSection = defineAsyncComponent(() => import("../../components/public/PublicPricesSection.vue"));
const PublicPhotoSection = defineAsyncComponent(() => import("../../components/public/PublicPhotoSection.vue"));
const PublicItinerarySection = defineAsyncComponent(() => import("../../components/public/PublicItinerarySection.vue"));
const PublicFaqSection = defineAsyncComponent(() => import("../../components/public/PublicFaqSection.vue"));
const PublicTestimonialsSection = defineAsyncComponent(() => import("../../components/public/PublicTestimonialsSection.vue"));
const PublicFeaturedVideoSection = defineAsyncComponent(() => import("../../components/public/PublicFeaturedVideoSection.vue"));
const PublicCtaSection = defineAsyncComponent(() => import("../../components/public/PublicCtaSection.vue"));
const PublicStorySection = defineAsyncComponent(() => import("../../components/public/PublicStorySection.vue"));
const PublicReasonsSection = defineAsyncComponent(() => import("../../components/public/PublicReasonsSection.vue"));
const PublicCountdownSection = defineAsyncComponent(() => import("../../components/public/PublicCountdownSection.vue"));
const PublicFreeFooterBrandSection = defineAsyncComponent(() => import("../../components/public/PublicFreeFooterBrandSection.vue"));
const PublicAgencyFooterSection = defineAsyncComponent(() => import("../../components/public/PublicAgencyFooterSection.vue"));

const sectionTypes: SectionType[] = [
  "hero",
  "banner_card",
  "photo",
  "prices",
  "itinerary",
  "faq",
  "testimonials",
  "featured_video",
  "cta",
  "story",
  "reasons",
  "countdown",
  "agency_footer"
];
const sectionLabels = defaultSectionLabels;
const sectionDescriptions: Partial<Record<SectionType, string>> = {
  hero: "Bloco inicial com destaque visual, título, subtítulo e CTA principal.",
  banner_card: "Banner em card com imagem de fundo, gradiente e CTA destacado.",
  photo: "Uma única imagem em destaque. Escolha o layout card ou largura total.",
  prices: "Tabela com planos, valores e diferenciais para cada oferta.",
  itinerary: "Sequência de etapas/benefícios para explicar seu serviço ou roteiro.",
  faq: "Perguntas e respostas para antecipar dúvidas frequentes.",
  testimonials: "Carrossel ou lista com depoimentos de clientes.",
  featured_video: "Destaque um video com titulo, subtitulo e CTA centralizado.",
  cta: "Chamada final impulsionando o lead para a ação desejada.",
  story: "Bloco de storytelling: Use para contar sua história,detalhamento do roteiro, e muito mais.",
  reasons: "Liste motivos, benefícios e serviços para reforçar a decisão.",
  countdown: "Cria urgência com contador regressivo para promoções ou eventos.",
  agency_footer: "Cartão institucional com contatos, redes sociais e mapa da agência."
};
const sectionThumbnails: Partial<Record<SectionType, string>> = {
  hero: heroThumb,
  banner_card: bannerCardThumb,
  photo: photoThumb,
  prices: pricesThumb,
  itinerary: itineraryThumb,
  faq: faqThumb,
  testimonials: testimonialsThumb,
  featured_video: featuredVideoThumb,
  cta: ctaThumb,
  story: storyThumb,
  reasons: reasonsThumb,
  countdown: countdownThumb,
  agency_footer: footerThumb
};
const sectionAccents: Partial<Record<SectionType, string>> = {
  hero: "from-sky-100 to-slate-50",
  banner_card: "from-emerald-600/90 to-emerald-400/70",
  photo: "from-slate-100 to-white",
  prices: "from-amber-100 to-white",
  itinerary: "from-emerald-100/70 to-white",
  faq: "from-slate-100 to-white",
  testimonials: "from-purple-100/70 to-white",
  featured_video: "from-indigo-100/70 to-white",
  cta: "from-cyan-100/70 to-white",
  story: "from-rose-100/70 to-white",
  reasons: "from-indigo-100/70 to-white",
  countdown: "from-orange-100/70 to-white",
  agency_footer: "from-slate-900/90 to-slate-800/70"
};
const formComponents: Partial<Record<SectionType, any>> = {
  hero: SectionHeroForm,
  banner_card: SectionBannerCardForm,
  photo: SectionPhotoForm,
  prices: SectionPricesForm,
  itinerary: SectionItineraryForm,
  faq: SectionFaqForm,
  testimonials: SectionTestimonialsForm,
  featured_video: SectionFeaturedVideoForm,
  cta: SectionCtaForm,
  story: SectionStoryForm,
  reasons: SectionReasonsForm,
  countdown: SectionCountdownForm,
  agency_footer: SectionAgencyFooterForm
};

const publicComponents: Partial<Record<SectionType, any>> = {
  hero: PublicHeroSection,
  banner_card: PublicBannerCardSection,
  photo: PublicPhotoSection,
  prices: PublicPricesSection,
  itinerary: PublicItinerarySection,
  faq: PublicFaqSection,
  testimonials: PublicTestimonialsSection,
  featured_video: PublicFeaturedVideoSection,
  cta: PublicCtaSection,
  story: PublicStorySection,
  reasons: PublicReasonsSection,
  countdown: PublicCountdownSection,
  free_footer_brand: PublicFreeFooterBrandSection,
  agency_footer: PublicAgencyFooterSection
};

const sectionRequiresBranding = (type?: SectionType | string | null) => type === "hero" || type === "agency_footer";

const sections = shallowRef<PageSection[]>([]);
const mobileOverlayVisible = reactive<Record<number, boolean>>({});
const mobileOverlayPersistent = reactive<Record<number, boolean>>({});
const mobileOverlayTimers: Record<number, ReturnType<typeof setTimeout> | null> = {};
const MOBILE_OVERLAY_AUTO_HIDE_MS = 5000;
watch(
  () => sections.value,
  () => {
    markUnsavedChanges();
  },
  { deep: true }
);

const clearMobileOverlayTimer = (idx: number) => {
  const timer = mobileOverlayTimers[idx];
  if (timer) {
    clearTimeout(timer);
    mobileOverlayTimers[idx] = null;
  }
};

const scheduleMobileOverlayAutoHide = (idx: number) => {
  clearMobileOverlayTimer(idx);
  if (!hasWindow) return;
  mobileOverlayTimers[idx] = window.setTimeout(() => {
    if (!mobileOverlayPersistent[idx]) {
      mobileOverlayVisible[idx] = false;
    }
    mobileOverlayTimers[idx] = null;
  }, MOBILE_OVERLAY_AUTO_HIDE_MS);
};

const overlayButtonSizingClass = computed(() =>
  isMobileOverlayMode.value ? "w-full justify-center text-[11px] px-3 py-2" : "px-4 py-2"
);

const overlayButtonGridClass = computed(() =>
  isMobileOverlayMode.value
    ? "grid w-full grid-cols-2 gap-2 [button:nth-child(1)]:col-span-2 [button:nth-child(4)]:col-span-2"
    : "flex flex-wrap items-center justify-center gap-3"
);

watch(
  () => isMobileOverlayMode.value,
  value => {
    if (!value) {
      Object.keys(mobileOverlayTimers).forEach(key => clearMobileOverlayTimer(Number(key)));
      Object.keys(mobileOverlayVisible).forEach(key => {
        delete mobileOverlayVisible[Number(key)];
        delete mobileOverlayPersistent[Number(key)];
      });
    }
  }
);

const registerPreviewSection = (el: Element | null, idx: number) => {
  if (!el) {
    clearMobileOverlayTimer(idx);
    delete mobileOverlayVisible[idx];
    delete mobileOverlayPersistent[idx];
  }
};

const handleSectionTap = (idx: number, event?: Event) => {
  if (!isMobileOverlayMode.value) return;
  const target = event?.target as HTMLElement | undefined;
  if (target && target.closest("[data-overlay-control='true']")) return;
  const alreadyVisible = mobileOverlayVisible[idx];
  Object.keys(mobileOverlayVisible).forEach(key => {
    const otherIdx = Number(key);
    if (otherIdx !== idx) {
      mobileOverlayVisible[otherIdx] = false;
      mobileOverlayPersistent[otherIdx] = false;
      clearMobileOverlayTimer(otherIdx);
    }
  });
  mobileOverlayVisible[idx] = true;
  mobileOverlayPersistent[idx] = false;
  scheduleMobileOverlayAutoHide(idx);
  if (!alreadyVisible) {
    event?.stopPropagation();
    event?.preventDefault();
  }
};

const closeMobileOverlay = (idx: number) => {
  if (!isMobileOverlayMode.value) return;
  mobileOverlayVisible[idx] = false;
  clearMobileOverlayTimer(idx);
};
const previewSections = ref<PageSection[]>([]);
const previewReady = ref(false);
const previewLoading = ref(false);
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
const getBrowserStorage = () => {
  if (!hasWindow) return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
};
provide(sectionsInjectionKey, sections);
provide(PUBLIC_BRANDING_KEY, computed(() => branding.value));

const uploadTokens = new Map<symbol, boolean>();
const activeImageUploads = ref(0);
const setSectionUploadState = (id: symbol, uploading: boolean) => {
  if (uploading) {
    uploadTokens.set(id, true);
  } else {
    uploadTokens.delete(id);
  }
  activeImageUploads.value = uploadTokens.size;
};
provide(sectionUploadGuardKey, {
  setUploading: setSectionUploadState
});
const hasPendingImageUploads = computed(() => activeImageUploads.value > 0);

const isFooterSection = (section?: PageSection | null) => !!section && (section as any).type === "free_footer_brand";
const enforceFooterConstraints = (list?: PageSection[] | null) => {
  const normalized = (list || []).filter(Boolean);
  if (!isFreePlan.value) return normalized;
  const footerIndex = normalized.findIndex(isFooterSection);
  if (footerIndex === -1) return normalized;
  const footer = normalized.splice(footerIndex, 1)[0];
  normalized.push(footer);
  return normalized;
};
const isLockedFooterSection = (section?: PageSection | null) => isFreePlan.value && isFooterSection(section);

const setSections = (value: PageSection[] | ((current: PageSection[]) => PageSection[])) => {
  const next = typeof value === "function" ? (value as (current: PageSection[]) => PageSection[])([...sections.value]) : value;
  sections.value = enforceFooterConstraints(next || []);
};

watch(isFreePlan, () => {
  setSections(sections.value.slice());
});

interface PendingSectionUpdate {
  timer: ReturnType<typeof setTimeout>;
  value: PageSection;
}
const pendingSectionUpdates: Record<number, PendingSectionUpdate> = {};
const commitSectionValue = (index: number, value: PageSection) => {
  const next = sections.value.slice();
  next[index] = value;
  setSections(next);
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

const countStoryImages = (images?: string[]) =>
  Array.isArray(images) ? images.filter(img => typeof img === "string" && img.trim().length > 0).length : 0;
const automaticStoryLayout = (images?: string[]) => (countStoryImages(images) > 1 ? "gallery" : "single");
const applyAutomaticStoryLayout = (story: StorySection) => {
  const desired = automaticStoryLayout(story.images);
  if (story.layout !== desired) {
    story.layout = desired;
  }
};

const storyMediaErrorText = "Adicione ao menos uma imagem ou video na secao Story antes de salvar.";
const hasStoryImage = (section: StorySection) => countStoryImages(section.images) > 0;
const hasStoryVideo = (section: StorySection) =>
  typeof section.videoUrl === "string" && section.videoUrl.trim().length > 0;
const validateSection = (section: PageSection | null): string | null => {
  if (!section) return null;
  if ((section as any).type === "story") {
    const story = section as StorySection;
    applyAutomaticStoryLayout(story);
    if (!hasStoryImage(story) && !hasStoryVideo(story)) return storyMediaErrorText;
  }
  return null;
};
const validateAllSections = (): string | null => {
  for (const section of sections.value) {
    const error = validateSection(section);
    if (error) return error;
  }
  return null;
};

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
const whatsappDigits = computed(() => {
  const agency =
    agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId) || agencyStore.agencies[0];
  const agencyDigits = (agency?.cta_whatsapp || "").replace(/\D/g, "");
  if (agencyDigits) return agencyDigits;
  return (auth.user?.whatsapp || "").replace(/\D/g, "");
});
const buildWhatsappLink = (title: string, _planName?: string) => {
  if (!whatsappDigits.value) return "";
  const message = `Oi, tenho interesse no roteiro: ${title || "Roteiro"}`;
  return `https://wa.me/${whatsappDigits.value}?text=${encodeURIComponent(message)}`;
};
const lastAutoWhatsAppLink = ref<string | null>(null);

const pixels = ref<{ id: number; name: string; type: "meta" | "ga"; value: string }[]>([]);
const selectedPixels = reactive<{ meta: string; ga: string }>({ meta: "", ga: "" });
const trackingEvents = ref({ pageView: true, ctaClicks: true });
const metaPixelOptions = computed(() => pixels.value.filter(p => p.type === "meta"));
const gaPixelOptions = computed(() => pixels.value.filter(p => p.type === "ga"));
const resolveSelectedPixel = (type: "meta" | "ga", name: string) =>
  name ? pixels.value.find(p => p.type === type && p.name === name) || null : null;

const canSelectPixel = computed(() => (auth.user?.plan || "free") !== "free" && pixels.value.length > 0);

const currentAgency = computed(() => {
  const selected = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return selected || agencyStore.agencies[0] || null;
});

const sanitizeDigits = (value?: string | null) => (value || "").replace(/\D/g, "");
const buildAddressText = (address: Record<string, string | undefined>) => {
  const line1 = [address.street, address.number, address.complement].filter(Boolean).join(", ");
  const line2 = [address.neighborhood, address.city, address.state, address.zipcode].filter(Boolean).join(", ");
  return [line1, line2].filter(Boolean).join(" - ");
};

const buildAgencyProfile = () => {
  const agency = currentAgency.value;
  const user = auth.user;
  const address = {
    street: user?.address_street || "",
    number: user?.address_number || "",
    complement: user?.address_complement || "",
    neighborhood: user?.address_neighborhood || "",
    city: user?.address_city || "",
    state: user?.address_state || "",
    zipcode: user?.address_zipcode || ""
  };
  const addressText = buildAddressText(address);
  const cnpjDigits = sanitizeDigits(user?.cnpj || "");
  const phone = (agency?.cta_whatsapp || user?.whatsapp || "").trim();

  return {
    name: agency?.name || user?.name || "",
    cnpj: user?.cnpj || "",
    cnpj_digits: cnpjDigits || undefined,
    email: user?.email || "",
    phone,
    social_links: agency?.social_links || [],
    address,
    address_text: addressText || "",
    map_query: addressText || "",
    map_embed_url: addressText
      ? `https://www.google.com/maps?q=${encodeURIComponent(addressText)}&output=embed`
      : "",
    cadastur_url: cnpjDigits
      ? `https://cadastur.turismo.gov.br/cadastur/#!/public/qrcode/${cnpjDigits}`
      : ""
  };
};

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

const applyPrimaryToThemeAndSections = (oldDefault?: string, nextColor?: string, syncPicker = false) => {
  const targetColor = nextColor || ctaColor.value || resolvePrimaryColor();
  const previous = oldDefault || theme.value.ctaDefaultColor || fallbackPrimaryColor;
  theme.value.ctaDefaultColor = targetColor;

  if (syncPicker && ctaColor.value !== targetColor) {
    skipCtaWatcher = true;
    ctaColor.value = targetColor;
  }

  setSections(current =>
    applySectionBackgrounds(
      current.map(section => {
        if (!section) return section;
        const type = (section as any).type as SectionType;
        if (type === "countdown") {
          const countdownBg = (section as any).backgroundColor as string | undefined;
          const shouldReplaceCountdown =
            !countdownBg ||
            countdownBg.toLowerCase?.() === fallbackPrimaryColor.toLowerCase() ||
            (!!previous && countdownBg.toLowerCase?.() === previous.toLowerCase());
          if (shouldReplaceCountdown) (section as any).backgroundColor = targetColor;
        }
        const currentColor = (section as any).ctaColor as string | undefined;
        const shouldReplace =
          !currentColor ||
          currentColor.toLowerCase?.() === fallbackPrimaryColor.toLowerCase() ||
          (!!previous && currentColor.toLowerCase?.() === previous.toLowerCase());
        return shouldReplace ? ({ ...(section as any), ctaColor: targetColor } as any) : section;
      })
    )
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
    secondary_color: agency?.secondary_color || primary,
    agency_profile: buildAgencyProfile()
  };
  applyPrimaryToThemeAndSections(theme.value.ctaDefaultColor, primary, true);
  fillHeroLogoFromAgency();
};

const refreshCtaColors = () => {
  applyPrimaryToThemeAndSections(theme.value.ctaDefaultColor, ctaColor.value);
  refreshPreview(true);
  showSnackbar("Cores aplicadas nas seções");
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
  const baseAuto = buildWhatsappLink(pageTitle.value);
  const isAutoLink = (link?: string, candidate?: string) => {
    if (!link) return true;
    const normalized = link.toLowerCase();
    const candidates = [
      lastAutoWhatsAppLink.value,
      candidate,
      "https://wa.me/559999999",
      "https://wa.me/5599999999"
    ].filter(Boolean) as string[];
    if (candidates.some(c => normalized === c.toLowerCase())) return true;
    return normalized.includes("wa.me") && normalized.includes("interesse");
  };

  const updated = sectionsList.map(section => {
    const type = (section as any).type as SectionType;
    if (!["hero", "story", "cta", "prices", "featured_video"].includes(type)) return section;
    let autoLink = baseAuto;
    if (type === "prices") {
      const firstPlan = ((section as any).items?.[0]?.title as string) || "";
      autoLink = buildWhatsappLink(pageTitle.value, firstPlan);
    }
    if (!autoLink) return section;
    if (type === "story" && (section as any).ctaEnabled === false) return section;

    if (type === "cta") {
      const current = (section as any).link as string | undefined;
      if (!current || isAutoLink(current, autoLink)) {
        (section as any).link = autoLink;
      }
      return section;
    }

    if ((section as any).ctaMode === "section") return section;
    const current = (section as any).ctaLink as string | undefined;
    if (!current || isAutoLink(current, autoLink)) {
      (section as any).ctaLink = autoLink;
    }
    return section;
  });

  if (baseAuto) lastAutoWhatsAppLink.value = baseAuto;
  return updated;
};

const FOOTER_DEFAULT_BG = "#2d2d2d";
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
    const typesWithButton: SectionType[] = ["hero", "prices", "testimonials", "featured_video", "story", "cta", "itinerary"];

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
    const type = (normalized as any).type as SectionType;

    if (
      type === "hero" ||
      type === "countdown" ||
      type === "free_footer_brand" ||
      type === "banner_card"
    ) {
      if ((normalized as any).type === "banner_card" && !(normalized as any).backgroundColor) {
        (normalized as any).backgroundColor = colorA.value;
      }
      return normalized;
    }
    if (type === "agency_footer") {
      const footerBg = ((normalized as any).backgroundColor || "").toLowerCase();
      const primaryLower = (theme.value.ctaDefaultColor || fallbackPrimaryColor || "").toLowerCase();
      const colorALower = colorA.value.toLowerCase();
      const colorBLower = colorB.value.toLowerCase();
      if (!footerBg || footerBg === primaryLower || footerBg === colorALower || footerBg === colorBLower) {
        (normalized as any).backgroundColor = FOOTER_DEFAULT_BG;
      }
      return normalized;
    }
    if (type === "photo") {
      const layout = (normalized as any).layout || "card";
      if (layout === "card") {
        const nextColor = altIndex % 2 === 0 ? colorA.value : colorB.value;
        if (!(normalized as any).backgroundColor) {
          (normalized as any).backgroundColor = nextColor;
        }
        altIndex += 1;
      } else {
        delete (normalized as any).backgroundColor;
      }
      return normalized;
    }
    if (type === "agency_footer") {
      altIndex += 1;
      return normalized;
    }
    const backgroundColor = altIndex % 2 === 0 ? colorA.value : colorB.value;
    altIndex += 1;
    (normalized as any).backgroundColor = backgroundColor;
    const readableText = getReadableTextColor(backgroundColor);
    if (readableText) {
      (normalized as any).textColor = readableText;
    } else {
      delete (normalized as any).textColor;
    }
    return normalized;
  });
};

watch(currentAgency, () => applyAgencyBranding(), { immediate: true });
watch(
  () => ({
    cnpj: auth.user?.cnpj,
    email: auth.user?.email,
    whatsapp: auth.user?.whatsapp,
    street: auth.user?.address_street,
    number: auth.user?.address_number,
    complement: auth.user?.address_complement,
    neighborhood: auth.user?.address_neighborhood,
    city: auth.user?.address_city,
    state: auth.user?.address_state,
    zipcode: auth.user?.address_zipcode
  }),
  () => applyAgencyBranding(),
  { deep: true }
);

const buildConfig = (): PageConfig => ({
  version: 1,
  theme: { ...theme.value, color1: colorA.value, color2: colorB.value },
  editor: { ...editorPrefs.value, previewEnabled: true, previewDevice: previewDevice.value },
  sections: applySectionBackgrounds(sections.value),
  tracking: (() => {
    const metaPixel = resolveSelectedPixel("meta", selectedPixels.meta);
    const gaPixel = resolveSelectedPixel("ga", selectedPixels.ga);
    if (!metaPixel && !gaPixel) return undefined;
    return {
      metaPixel,
      gaPixel,
      events: { ...trackingEvents.value }
    };
  })()
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
  Object.keys(mobileOverlayTimers).forEach(key => clearMobileOverlayTimer(Number(key)));
  if (removeViewportWatcher) {
    removeViewportWatcher();
    removeViewportWatcher = null;
  }
  if (hasWindow) {
    window.removeEventListener("beforeunload", beforeUnloadHandler);
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
      logoBorderRadius: 0,
      chips: ["Leito-cama 180º", "Wi-Fi a bordo", "Tomadas individuais", "Massagem a bordo"],
      ctaLabel: "Quero falar no WhatsApp",
      ctaLink: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
      ctaColor: theme.value.ctaDefaultColor,
      ctaMode: "link",
      ctaSectionId: null
    } as HeroSection);
  }

  if (type === "banner_card") {
    return ensureSectionAnchor({
      type: "banner_card",
      enabled: true,
      backgroundColor: colorA.value,
      title: "Conte com especialistas para transformar o seu roteiro.",
      subtitle:
        "Um banner compacto e elegante para reforçar a principal promessa ou próxima campanha.",
      backgroundImage:
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=80",
      gradientColor: "#05060f",
      cardBackground: "rgba(5,6,15,0.88)",
      cardBorderColor: "rgba(255,255,255,0.25)",
      textColor: "rgba(255,255,255,0.85)",
      bodyColor: "rgba(255,255,255,0.85)",
      ctaLabel: "Quero saber mais",
      ctaLink: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
      ctaColor: theme.value.ctaDefaultColor,
      ctaMode: "link",
      ctaSectionId: null
    } as BannerCardSection);
  }

  if (type === "photo") {
    return ensureSectionAnchor({
      type: "photo",
      enabled: true,
      image:
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80",
      layout: "card",
      altText: "Imagem de destaque"
    } as PhotoSection);
  }

  if (type === "prices") {
    const headingDefaults = getSectionHeadingDefaults("prices");
    return ensureSectionAnchor({
      type: "prices",
      enabled: true,
      layout: "columns",
      ctaLink: buildWhatsappLink(pageTitle.value, "Apartamento duplo") || "",
      title: "Planos e opções",
      subtitle: "Escolha o formato que combina com você.",
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
      ctaColor: theme.value.ctaDefaultColor,
      ctaLabel: "Reservar agora"
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
      ctaColor: theme.value.ctaDefaultColor,
      title: "Dia a dia",
      subtitle: "Visão clara do roteiro completo.",
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
      title: "Perguntas frequentes",
      subtitle: "As dúvidas mais comuns sobre o roteiro.",
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

  if (type === "featured_video") {
    const headingDefaults = getSectionHeadingDefaults("featured_video");
    return ensureSectionAnchor({
      type: "featured_video",
      enabled: true,
      headingLabel: headingDefaults.label,
      headingLabelStyle: headingDefaults.style,
      title: "Assista ao roteiro em 2 minutos",
      subtitle: "Mostre o clima da experiencia com um video curto e objetivo.",
      videoUrl: "https://www.youtube.com/watch?v=ysz5S6PUM-U",
      ctaLabel: "Falar com especialista",
      ctaLink: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
      ctaMode: "link",
      ctaSectionId: null,
      ctaColor: theme.value.ctaDefaultColor
    } as FeaturedVideoSection);
  }

  if (type === "story") {
    const headingDefaults = getSectionHeadingDefaults("story");
    const defaultImages = [
      "https://images.unsplash.com/photo-1502920514313-52581002a659?auto=format&fit=crop&w=1200&q=80",
      "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
      "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"
    ];
    return ensureSectionAnchor({
      type: "story",
      enabled: true,
      layout: automaticStoryLayout(defaultImages),
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
      images: defaultImages
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
      backgroundColor: theme.value.ctaDefaultColor || resolvePrimaryColor(),
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
        { icon: "💰", title: "Economize dinheiro", description: "Aproveite negociações especiais e otimize seu orçamento." },
        { icon: "🧭", title: "Mais liberdade", description: "Planeje quando quiser com apoio de especialistas locais." },
        { icon: "🤝", title: "Apoio dedicado", description: "Suporte próximo antes, durante e depois da viagem." },
        { icon: "✨", title: "Experiência única", description: "Curadoria de passeios e hospedagens memoráveis." }
      ]
    } as ReasonsSection);
  }

  if (type === "agency_footer") {
    return ensureSectionAnchor({
      type: "agency_footer",
      enabled: true,
      showCadastur: true,
      displayVariant: "auto",
      fullWidth: true,
      backgroundColor: "#2d2d2d"
    } as AgencyFooterSection);
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
    ctaText: "Falar com especialista",
    ctaColor: theme.value.ctaDefaultColor,
    textColor: theme.value.ctaTextColor,
    highlight: false,
    highlightColor: theme.value.ctaDefaultColor,
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
      if (parsed.theme.ctaDefaultColor) ctaColor.value = parsed.theme.ctaDefaultColor;
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
    selectedPixels.meta = "";
    selectedPixels.ga = "";
    if (tracking) {
      const legacyPixel = tracking.pixel;
      const metaPixel = tracking.metaPixel || (legacyPixel?.type === "meta" ? legacyPixel : null);
      const gaPixel = tracking.gaPixel || (legacyPixel?.type === "ga" ? legacyPixel : null);
      if (metaPixel?.name) selectedPixels.meta = metaPixel.name;
      if (gaPixel?.name) selectedPixels.ga = gaPixel.name;
    }
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

const defaultPageSlugPattern = /^roteiro-\d+$/i;
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
    const loadedTitle = res.data.title || "";
    const existingSlug = (res.data.slug || "").trim();
    const generatedSlug = normalizeSlugInput(loadedTitle);
    const shouldReplaceWithGenerated = !existingSlug || defaultPageSlugPattern.test(existingSlug);
    slugAutoSyncEnabled.value = shouldReplaceWithGenerated || existingSlug === generatedSlug;
    pageTitle.value = loadedTitle;
    pageSlug.value = shouldReplaceWithGenerated ? generatedSlug : existingSlug || generatedSlug;

    hydrateFromConfig(res.data.config_json);
    await nextTick();
    syncSavedSnapshot();
    initialLoadComplete.value = true;
    message.value = "";
  } catch (err) {
    console.error(err);
    errorMessage.value = "Não foi possível carregar a página.";
  }
};

const saveConfig = async (): Promise<boolean> => {
  if (!auth.token) {
    errorMessage.value = "Sess�o expirada. Fa�a login novamente.";
    return false;
  }

  errorMessage.value = "";
  message.value = "";
  if (!ensureValidPageSlug()) {
    return false;
  }

  try {
    flushPendingSectionUpdates();
    const validationError = validateAllSections();
    if (validationError) {
      errorMessage.value = validationError;
      showSnackbar(validationError);
      return false;
    }
    await api.put(`/pages/${pageId}`, { title: pageTitle.value, slug: pageSlug.value });

    const configPayload = buildConfig();
    await api.put(`/pages/${pageId}/config`, { config: configPayload });

    message.value = "Configuração salva!";
    showSnackbar("Configuração salva");
    syncSavedSnapshot();
    return true;
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    if (detail) {
      limitModal.value = { open: true, message: String(detail) };
    } else {
      errorMessage.value = "Erro ao salvar configuração.";
    }
    return false;
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
    const saved = await saveConfig();
    if (!saved) return;
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

const unpublishPage = async () => {
  if (!auth.token) {
    errorMessage.value = "Sessão expirada. Faça login novamente.";
    return;
  }

  if (!isPublished.value || !page.value) {
    return;
  }

  errorMessage.value = "";
  message.value = "";

  try {
    const res = await api.post(`/pages/${pageId}/publish`, { publish: false });
    page.value = res.data;
    message.value = "Página despublicada.";
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    if (detail) {
      errorMessage.value = String(detail);
    } else {
      errorMessage.value = "Erro ao despublicar. Tente novamente.";
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
  const footerIndex = current.findIndex(isFooterSection);
  const maxInsertIndex = footerIndex >= 0 ? footerIndex : current.length;
  if (typeof insertIndex === "number") {
    const safeIndex = Math.min(Math.max(insertIndex, 0), maxInsertIndex);
    current.splice(safeIndex, 0, next);
  } else {
    current.splice(maxInsertIndex, 0, next);
  }
  setSections(current);
  refreshPreview(true);
};

const scheduleWhatsAppUpdate = () => {
  clearTitleDebounce();
  whatsappTitleDebounce = setTimeout(() => {
    setSections(applyWhatsAppDefaults(sections.value.slice()));
  }, 500);
};

const duplicateSection = (index: number) => {
  if (isLockedFooterSection(sections.value[index])) return;
  const copy = cloneWithNewAnchor(clone(sections.value[index]));
  const next = sections.value.slice();
  next.splice(index + 1, 0, copy);
  setSections(next);
  refreshPreview(true);
};

const removeSection = (index: number) => {
  if (isLockedFooterSection(sections.value[index])) return;
  const next = sections.value.slice();
  next.splice(index, 1);
  setSections(next);
  refreshPreview(true);
};

const moveSection = (index: number, direction: number) => {
  const target = index + direction;
  if (target < 0 || target >= sections.value.length) return;
  if (isLockedFooterSection(sections.value[index]) || isLockedFooterSection(sections.value[target])) return;

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
  if (isLockedFooterSection(target)) return;
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
  markUnsavedChanges();
});

watch(colorB, value => {
  theme.value.color2 = value;
  markUnsavedChanges();
});

watch(ctaColor, (value, previous) => {
  if (!value) return;
  if (skipCtaWatcher) {
    skipCtaWatcher = false;
    return;
  }
  applyPrimaryToThemeAndSections(previous, value);
  markUnsavedChanges();
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
  if (hasPendingImageUploads.value) {
    showSnackbar("A imagem ainda está sendo enviada. Aguarde antes de salvar.");
    return;
  }
  const validationError = validateSection(editingSectionDraft.value);
  if (validationError) {
    errorMessage.value = validationError;
    showSnackbar(validationError);
    return;
  }
  errorMessage.value = "";
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
      if (parsed.theme.ctaDefaultColor) ctaColor.value = parsed.theme.ctaDefaultColor;
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

const cancelNavigationModal = () => {
  pendingNavigationPath.value = null;
  unsavedNavigationModal.value.open = false;
  unsavedNavigationModal.value.saving = false;
};

const proceedToPendingRoute = () => {
  if (!pendingNavigationPath.value) return;
  const target = pendingNavigationPath.value;
  pendingNavigationPath.value = null;
  unsavedNavigationModal.value.open = false;
  unsavedNavigationModal.value.saving = false;
  router.push(target).catch(() => {
    /* ignore navigation failures */
  });
};

const discardAndLeave = () => {
  hasUnsavedChanges.value = false;
  proceedToPendingRoute();
};

const saveAndLeave = async () => {
  if (unsavedNavigationModal.value.saving) return;
  unsavedNavigationModal.value.saving = true;
  const saved = await saveConfig();
  unsavedNavigationModal.value.saving = false;
  if (!saved) return;
  hasUnsavedChanges.value = false;
  proceedToPendingRoute();
};

onMounted(async () => {
  setupViewportWatcher();
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
    previewSection: buildCatalogPreview(type),
    thumbnail: sectionThumbnails[type]
  }));
  previewReady.value = true;
  schedulePreviewHydration(true);
  nextTick(() => setupSectionToolbarObserver());
});
</script>














