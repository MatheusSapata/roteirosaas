<template>
<div class="page-editor-view w-full" :class="newEditor ? 'is-v2 space-y-2 px-1 py-1' : 'space-y-6 px-4 py-6 md:px-8 md:py-4'">
    <div class="ed-topbar">
      <button type="button" class="ed-back" @click="goBack" :aria-label="viewCopy.actions.goBack">
        <ChevronLeftIcon aria-hidden="true" />
      </button>
      <div class="ed-title-block">
        <p class="ed-crumb">Páginas</p>
        <div class="ed-title-row">
          <h1 class="ed-title">{{ page?.title || viewCopy.header.defaultTitle }}</h1>
          <span class="ed-pill" :class="isPublished ? 'is-on' : 'is-off'"><i></i>{{ isPublished ? "Publicada" : "Rascunho" }}</span>
          <span class="ed-saved" :class="{ 'is-dirty': hasUnsavedChanges }">
            <CheckIcon v-if="!hasUnsavedChanges" aria-hidden="true" />
            <i v-else></i>
            {{ hasUnsavedChanges ? "Alterações não salvas" : "Tudo salvo" }}
          </span>
        </div>
      </div>
      <div class="ed-actions">
        <button v-if="canUseAiAssistant && !isMobileViewport" type="button" class="ed-btn ed-btn-ai" @click="toggleAiAssistant">
          <SparkleIcon aria-hidden="true" />
          Assistente IA
        </button>
        <button v-if="isPublished" type="button" class="ed-btn ed-btn-ghost" :disabled="!publicUrl" @click="viewPublicPage">
          <ExternalLinkIcon aria-hidden="true" />
          {{ viewCopy.actions.viewPage }}
        </button>
        <div class="ed-menu-wrap">
          <button type="button" class="ed-icon-btn" aria-label="Mais ações" title="Mais ações" @click.stop="topbarMenuOpen = !topbarMenuOpen">
            <EllipsisVerticalIcon aria-hidden="true" />
          </button>
          <div v-if="topbarMenuOpen" class="ed-menu" @click="topbarMenuOpen = false">
            <button type="button" @click="saveTemplate">{{ viewCopy.toolbar.saveTemplate }}</button>
            <button v-if="isPublished" type="button" class="danger" @click="unpublishPage">{{ viewCopy.toolbar.unpublish }}</button>
          </div>
        </div>
        <button v-if="!isPublished" type="button" class="ed-btn ed-btn-ghost" @click="publishPage">{{ viewCopy.toolbar.publish }}</button>
        <button type="button" class="ed-btn ed-btn-primary" :disabled="!hasUnsavedChanges" @click="saveConfig">{{ viewCopy.toolbar.save }}</button>
      </div>
    </div>

    <!-- Dialog de limite de plano (reutilizado tamb?m para "template no free") -->
    <div :class="['editor-workspace', showAiAssistant ? 'ai-assistant-open' : '', { 'is-v2': newEditor }]">

      <Transition name="ai-sidebar-slide">
        <aside
          v-if="showAiAssistant"
          class="editor-ai-sidebar hidden md:flex"
          :style="aiAssistantSidebarStyle"
          aria-label="Painel do assistente"
        >
          <button
            type="button"
            class="editor-ai-sidebar-resize-handle"
            @pointerdown="startAiAssistantSidebarResize"
            aria-label="Redimensionar painel"
            title="Arraste para ajustar a largura"
          >
            <span class="editor-ai-sidebar-resize-grip" aria-hidden="true"></span>
          </button>
          <div class="editor-ai-sidebar-header">
            <span v-if="newEditor" class="ai-v2-mark" aria-hidden="true"><SparkleIcon /></span>
            <div class="editor-ai-sidebar-header-copy">
              <div class="editor-ai-sidebar-title-row">
                <h2 class="editor-ai-sidebar-title">Assistente IA</h2>
                <span v-if="!newEditor" class="editor-ai-sidebar-usage-pill">{{ aiAssistantUsageLabel }}</span>
              </div>
              <span v-if="newEditor && aiAssistantUsageText" class="ai-v2-usage">{{ aiAssistantUsageText }}</span>
            </div>
            <button type="button" class="editor-ai-sidebar-close" @click="toggleAiAssistant" aria-label="Fechar ajuda de IA">
              <XIcon class="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
            <div class="editor-ai-sidebar-chat">
              <div
                class="editor-ai-sidebar-chat-log"
                ref="aiAssistantChatLogRef"
              >
                <template v-if="aiAssistantVisibleMessages.length">
                  <div
                    v-for="(message, index) in aiAssistantVisibleMessages"
                    :key="`${message.role}-${index}-${message.content.slice(0, 12)}`"
                    class="editor-ai-sidebar-bubble"
                    :class="message.role === 'user' ? 'is-user' : 'is-assistant'"
                  >
                    <template v-if="newEditor && message.role === 'assistant' && hasAiStructure(message.content)">
                      <div v-if="aiIntroText(message.content)" class="editor-ai-sidebar-response-text">{{ aiIntroText(message.content) }}</div>
                      <div class="ai-v2-structure">
                        <p class="ai-v2-structure-title">Sugiro esta estrutura, com {{ aiStructureNames(message.content).length }} {{ aiStructureNames(message.content).length === 1 ? "seção" : "seções" }}:</p>
                        <ol>
                          <li v-for="(name, nameIndex) in aiStructureNames(message.content).slice(0, aiExpanded.has(index) ? undefined : 5)" :key="nameIndex">
                            <b>{{ nameIndex + 1 }}</b><span>{{ name }}</span>
                          </li>
                          <li v-if="!aiExpanded.has(index) && aiStructureNames(message.content).length > 5" class="is-more">
                            <button type="button" @click="toggleAiExpanded(index)">+{{ aiStructureNames(message.content).length - 5 }} seções</button>
                          </li>
                        </ol>
                        <div class="ai-v2-actions">
                          <button type="button" class="is-primary" :disabled="aiStructureApplying || aiAssistantLoading || isSectionEditorOpen" @click="applyAiStructure(message.content, 'insert')">Inserir no fim</button>
                          <button type="button" :disabled="aiStructureApplying || aiAssistantLoading || isSectionEditorOpen" @click="applyAiStructure(message.content, 'replace')">Substituir tudo</button>
                        </div>
                        <span class="ai-v2-hint">{{ isSectionEditorOpen ? "Feche a edição da seção para aplicar." : "Dá para desfazer depois de aplicar." }}</span>
                        <button type="button" class="ai-v2-details" @click="toggleAiDetails(index)">{{ aiDetails.has(index) ? "Esconder resposta completa" : "Ver resposta completa" }}</button>
                        <div v-if="aiDetails.has(index)" class="editor-ai-sidebar-response-text ai-v2-full">{{ message.content }}</div>
                      </div>
                    </template>
                    <div v-else class="editor-ai-sidebar-response-text">{{ message.content }}</div>
                    <div v-if="!newEditor && message.role === 'assistant' && hasAiStructure(message.content)" class="mt-3 flex items-center gap-1">
                        <button type="button" class="min-h-11 min-w-0 flex-1 rounded-lg border border-indigo-200 bg-white px-3 py-2.5 text-sm font-semibold text-indigo-700 hover:bg-indigo-50 focus-visible:outline-indigo-600 disabled:opacity-50"
                          title="Adiciona todas as seções da sugestão ao final do conteúdo já existente."
                          aria-label="Inserir estrutura: adiciona todas as seções da sugestão ao final do conteúdo já existente."
                          :disabled="aiStructureApplying || aiAssistantLoading || isSectionEditorOpen"
                          @click="applyAiStructure(message.content, 'insert')">
                          Inserir estrutura
                        </button>
                        <button type="button" class="min-h-11 min-w-0 flex-1 rounded-lg border border-indigo-200 bg-white px-3 py-2.5 text-sm font-semibold text-indigo-700 hover:bg-indigo-50 focus-visible:outline-indigo-600 disabled:opacity-50"
                          title="Substitui todas as seções da página pelas seções da sugestão."
                          aria-label="Substituir estrutura: substitui todas as seções da página pelas seções da sugestão."
                          :disabled="aiStructureApplying || aiAssistantLoading || isSectionEditorOpen"
                          @click="applyAiStructure(message.content, 'replace')">
                          Substituir estrutura
                        </button>
                    </div>
                    <p v-if="aiStructureApplying && message.role === 'assistant' && hasAiStructure(message.content)" role="status" class="mt-1 text-xs text-slate-500">Aplicando estrutura...</p>
                  </div>
                </template>

                <div v-if="newEditor && !aiAssistantLoading && !aiAssistantMessages.some(message => message.role === 'user')" class="ai-v2-chips">
                  <button v-for="suggestion in aiSuggestions" :key="suggestion.label" type="button" @click="useAiSuggestion(suggestion)">{{ suggestion.label }}</button>
                </div>
                <button v-if="aiStructurePreviousSections" type="button"
                  class="my-2 text-sm font-semibold text-indigo-600 underline"
                  :disabled="aiStructureApplying || isSectionEditorOpen" @click="undoAiStructure">
                  Desfazer estrutura aplicada
                </button>
                <p v-if="aiStructureError" role="alert" class="my-2 text-sm text-red-600">{{ aiStructureError }}</p>
                <div v-if="aiAssistantLoading" class="editor-ai-sidebar-typing" aria-label="Carregando resposta">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>

            <div class="editor-ai-sidebar-composer">
              <input
                ref="aiAssistantFileInputRef"
                class="hidden"
                type="file"
                multiple
                @change="handleAiAssistantFileChange"
              />

              <div class="editor-ai-sidebar-composer-row">
                <button
                  type="button"
                  class="editor-ai-sidebar-icon-button editor-ai-sidebar-attach"
                  @click="openAiAssistantFilePicker"
                  :disabled="aiAssistantLoading || aiAssistantLimitReached"
                  aria-label="Anexar arquivos"
                >
                  <PaperclipIcon class="h-4 w-4" aria-hidden="true" />
                </button>

                <span class="editor-ai-sidebar-attach-count" v-if="aiAssistantAttachments.length">
                  {{ aiAssistantAttachments.length }}
                </span>

                <textarea
                  v-model="aiAssistantDraft"
                  class="editor-ai-sidebar-input"
                  rows="1"
                  placeholder="Digite sua mensagem..."
                  :disabled="aiAssistantLoading || aiAssistantLimitReached"
                ></textarea>

                <button
                  type="button"
                  class="editor-ai-sidebar-icon-button editor-ai-sidebar-send"
                  :disabled="aiAssistantLoading || aiAssistantLimitReached || (!aiAssistantDraft.trim() && aiAssistantAttachments.length === 0)"
                  @click="sendAiAssistantMessage"
                  :aria-label="aiAssistantSendButtonLabel"
                >
                  <SendIcon class="h-4 w-4" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        </aside>
      </Transition>

    <Teleport to="body" v-if="limitModal.open">
      <div class="fixed inset-0 z-50 flex items-center justify-center px-4 page-editor-overlay">
        <div class="editor-dialog-shell w-full max-w-md p-6">
          <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">{{ viewCopy.limitModal.eyebrow }}</p>
          <h3 class="mt-2 text-xl font-bold text-slate-900">{{ viewCopy.limitModal.title }}</h3>
          <p class="mt-2 text-sm text-slate-600">
            {{ limitModal.message || viewCopy.limitModal.description }}
          </p>

          <div class="mt-4 flex flex-wrap gap-2">
            <button
              @click="limitModal.open = false"
              class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            >
              {{ viewCopy.actions.close }}
            </button>

            <button
              @click="goPlans"
              class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark"
            >
              {{ viewCopy.actions.viewPlans }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Diálogo de confirmação ao sair sem salvar -->
    <Teleport to="body" v-if="unsavedNavigationModal.open">
      <div class="fixed inset-0 z-50 flex items-center justify-center px-4 page-editor-overlay">
        <div class="editor-dialog-shell w-full max-w-lg p-6">
          <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">{{ viewCopy.unsavedModal.eyebrow }}</p>
          <h3 class="mt-2 text-xl font-bold text-slate-900">{{ viewCopy.unsavedModal.title }}</h3>
          <p class="mt-2 text-sm text-slate-600">
            {{ viewCopy.unsavedModal.description }}
          </p>

          <div class="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              class="editor-dialog-action editor-dialog-action--neutral"
              @click="cancelNavigationModal"
            >
              {{ viewCopy.unsavedModal.continueEditing }}
            </button>
            <button
              type="button"
              class="editor-dialog-action editor-dialog-action--danger"
              @click="discardAndLeave"
            >
              {{ viewCopy.unsavedModal.discardAndExit }}
            </button>
            <button
              type="button"
              class="editor-dialog-action editor-dialog-action--primary"
              :disabled="unsavedNavigationModal.saving"
              @click="saveAndLeave"
            >
              {{ unsavedNavigationModal.saving ? viewCopy.unsavedModal.saving : viewCopy.unsavedModal.saveAndLeave }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body" v-if="unsavedSectionModal.open">
      <div class="fixed inset-0 z-50 flex items-center justify-center px-4 page-editor-overlay">
        <div class="editor-dialog-shell w-full max-w-lg p-6">
          <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">{{ viewCopy.unsavedModal.eyebrow }}</p>
          <h3 class="mt-2 text-xl font-bold text-slate-900">{{ viewCopy.sectionUnsavedModal.title }}</h3>
          <p class="mt-2 text-sm text-slate-600">
            {{ viewCopy.sectionUnsavedModal.description }}
          </p>

          <div class="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              class="editor-dialog-action editor-dialog-action--neutral"
              @click="cancelUnsavedSectionModal"
            >
              {{ viewCopy.unsavedModal.continueEditing }}
            </button>
            <button
              type="button"
              class="editor-dialog-action editor-dialog-action--danger"
              @click="discardUnsavedSectionChanges"
            >
              {{ viewCopy.unsavedModal.discardAndExit }}
            </button>
            <button
              type="button"
              class="editor-dialog-action editor-dialog-action--primary"
              :disabled="unsavedSectionModal.saving"
              @click="saveUnsavedSectionChanges"
            >
              {{ unsavedSectionModal.saving ? viewCopy.unsavedModal.saving : viewCopy.sectionUnsavedModal.saveSection }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body" v-if="unsavedFlightSegmentModal.open">
      <div class="fixed inset-0 z-50 flex items-center justify-center px-4 page-editor-overlay">
        <div class="editor-dialog-shell w-full max-w-lg p-6">
          <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">{{ viewCopy.unsavedModal.eyebrow }}</p>
          <h3 class="mt-2 text-xl font-bold text-slate-900">{{ viewCopy.flightUnsavedModal.title }}</h3>
          <p class="mt-2 text-sm text-slate-600">
            {{ viewCopy.flightUnsavedModal.description }}
          </p>

          <div class="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              class="editor-dialog-action editor-dialog-action--neutral"
              @click="cancelUnsavedFlightSegmentModal"
            >
              {{ viewCopy.unsavedModal.continueEditing }}
            </button>
            <button
              type="button"
              class="editor-dialog-action editor-dialog-action--primary"
              @click="confirmSaveSectionWithUnsavedFlightSegment"
            >
              {{ viewCopy.flightUnsavedModal.confirm }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Dialog de sucesso ao publicar -->
    <Teleport to="body" v-if="successModal.open">
      <div class="fixed inset-0 z-50 flex items-center justify-center px-4 page-editor-overlay">
        <div class="editor-dialog-shell w-full max-w-md p-6">
          <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">{{ viewCopy.successModal.eyebrow }}</p>
          <h3 class="mt-2 text-xl font-bold text-slate-900">{{ viewCopy.successModal.title }}</h3>
          <p class="mt-2 text-sm text-slate-600">{{ viewCopy.successModal.description }}</p>

          <div class="mt-5 flex flex-col gap-2 md:flex-row md:flex-nowrap md:items-center">
            <button
              @click="successModal.open = false"
              class="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 md:w-auto md:flex-shrink-0"
            >
              {{ viewCopy.actions.close }}
            </button>

            <button
              @click="goPages"
              class="w-full rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 md:w-auto md:flex-shrink-0"
            >
              {{ viewCopy.successModal.viewPages }}
            </button>

            <button
              :disabled="!publicUrl"
              @click="viewPublicPage"
              class="w-full rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:opacity-50 md:w-auto md:flex-shrink-0"
            >
              {{ viewCopy.actions.viewPage }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    <SectionPickerV2
      v-if="sectionPicker.open && newEditor"
      :after-label="sectionPickerAfterLabel"
      :types="sectionTypes"
      :unavailable="sections.some(isHeaderSection) ? ['header'] : []"
      :viajeon-connected="viajeonConnected"
      :accent="ctaColor"
      @select="handleSectionPickerSelect"
      @close="closeSectionPicker"
      @integrate="goViajeonIntegration"
    />
    <Transition name="fade">
      <div v-if="insertedToast" class="v2ed-toast" role="status">
        <span class="v2ed-toast-ico" aria-hidden="true"><CheckIcon /></span>
        <span><b>{{ insertedToast.label }}</b> entrou na página</span>
        <button type="button" @click="undoInsertedSection">Desfazer</button>
      </div>
    </Transition>
    <Teleport to="body" v-if="sectionPicker.open && !newEditor">
      <div
      class="app-modal-overlay fixed inset-0 z-40 flex items-center justify-center px-4 py-8"
      @click.self="closeSectionPicker"
      >
        <div class="editor-dialog-shell w-full max-w-5xl">
        <div class="flex flex-col gap-2 border-b border-slate-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between dark:border-white/10">
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
            <div
              v-for="catalog in sectionCatalog"
              :key="catalog.type"
              role="button"
              :tabindex="catalog.type === 'viajeon_checkout' && !viajeonConnected ? -1 : 0"
              class="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition dark:border-[#2b2b2b] dark:bg-[#181818]"
              :class="catalog.type === 'viajeon_checkout' && !viajeonConnected ? 'cursor-default' : 'cursor-pointer hover:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand/40'"
              @click="handleSectionPickerSelect(catalog.type)"
              @keydown.enter="handleSectionPickerSelect(catalog.type)"
            >
              <div class="relative h-44 w-full overflow-hidden rounded-t-2xl border-b border-slate-100 bg-slate-50 dark:border-white/10 dark:bg-[#121212]">
                <template v-if="catalog.thumbnail">
                  <img :src="catalog.thumbnail" alt="" class="h-full w-full object-cover" />
                  <div class="absolute inset-0 bg-gradient-to-t from-black/35 to-transparent"></div>
                </template>
                <template v-else>
                  <div class="absolute inset-0 bg-gradient-to-br" :class="catalog.accent"></div>
                  <div class="relative flex h-full w-full items-center justify-center overflow-hidden p-3">
                    <div class="public-tokens pointer-events-none origin-center scale-[0.55] transform rounded-[30px] border border-white/50 bg-white shadow">
                      <component
                        :is="publicComponents[catalog.type]"
                        :section="catalog.previewSection"
                        :previewDevice="'desktop'"
                        v-bind="sectionRequiresBranding(catalog.type) ? { branding } : {}"
                      />
                    </div>
                  </div>
                </template>
                <div
                  v-if="catalog.type === 'viajeon_checkout' && !viajeonConnected"
                  class="absolute inset-0 flex items-center justify-center gap-2 bg-slate-900/55"
                >
                  <button
                    type="button"
                    class="rounded-full bg-emerald-500 px-4 py-2 text-xs font-bold text-white shadow-lg transition hover:bg-emerald-600"
                    @click.stop="goViajeonIntegration"
                  >
                    Integrar agora
                  </button>
                  <button
                    type="button"
                    class="catalog-info-tooltip border-white/60 bg-white/20 text-white backdrop-blur"
                    title="O Checkout ViajeOn exibe os pacotes ativos da sua operação e envia a seleção do cliente ao checkout."
                    data-tooltip="O Checkout ViajeOn exibe os pacotes ativos da sua operação e envia a seleção do cliente ao checkout."
                    aria-label="O Checkout ViajeOn exibe os pacotes ativos da sua operação e envia a seleção do cliente ao checkout."
                    @click.stop
                  >i</button>
                </div>
              </div>
              <div class="p-4">
                <p class="text-sm font-semibold text-slate-800">{{ catalog.label }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ catalog.description }}</p>
              </div>
              <div v-if="catalog.type !== 'viajeon_checkout' || viajeonConnected" class="pointer-events-none absolute inset-0 flex items-center justify-center bg-slate-900/70 opacity-0 transition group-hover:opacity-100">
                <span class="rounded-full bg-white/20 px-4 py-1 text-xs font-semibold text-white backdrop-blur">Clique para inserir</span>
              </div>
            </div>
          </div>
        </div>
        </div>
      </div>
    </Teleport>

    <div
      :class="['editor-body flex-1 min-w-0 space-y-4', showAiAssistant ? 'ai-assistant-open' : '']"
      :style="showAiAssistant && !isMobileViewport ? { paddingRight: `${aiAssistantSidebarWidth + 8}px` } : undefined"
    >
      <nav v-if="!newEditor" class="ed-tabs" role="tablist">
        <button type="button" class="ed-tab" :class="{ on: activeSettingsTab === 'content' }" @click="selectSettingsTab('content')">
          <PanelsTopLeftIcon aria-hidden="true" />
          Conteúdo
        </button>
        <button type="button" class="ed-tab" :class="{ on: activeSettingsTab === 'general' }" @click="selectSettingsTab('general')">
          <PencilIcon aria-hidden="true" />
          Título e link
        </button>
        <button type="button" class="ed-tab" :class="{ on: activeSettingsTab === 'colors' }" @click="selectSettingsTab('colors')">
          <PaletteIcon aria-hidden="true" />
          Cores
        </button>
        <button type="button" class="ed-tab" :class="{ on: activeSettingsTab === 'pixels' }" @click="selectSettingsTab('pixels')">
          <ActivityIcon aria-hidden="true" />
          Rastreamento
          <span v-if="!selectedPixels.meta && !selectedPixels.ga" class="ed-tab-badge">Não configurado</span>
        </button>
        <button type="button" class="ed-tab" :class="{ on: activeSettingsTab === 'capture' }" @click="selectSettingsTab('capture')">
          <UserPlusIcon aria-hidden="true" />
          Captação de leads
        </button>
      </nav>

      <div
        class="ed-grid"
        :class="{
          'is-wide': activeSettingsTab !== 'content',
          'is-v2': newEditor,
          'left-closed': newEditor && !leftPanelOpen,
          'right-closed': newEditor && (!layersOpen || showAiAssistant)
        }"
      >
      <aside v-if="newEditor || activeSettingsTab !== 'content'" class="ed-side">
      <nav v-if="newEditor" class="ed-rail" aria-label="Configurações da página">
        <button
          type="button"
          class="ed-rail-btn"
          :aria-expanded="leftPanelOpen"
          :aria-label="leftPanelOpen ? 'Recolher configurações' : 'Abrir configurações'"
          :title="leftPanelOpen ? 'Recolher configurações' : 'Abrir configurações'"
          @click="leftPanelOpen = !leftPanelOpen"
        >
          <PanelLeftCloseIcon v-if="leftPanelOpen" aria-hidden="true" />
          <PanelLeftOpenIcon v-else aria-hidden="true" />
        </button>
        <button
          v-for="tab in railTabs"
          :key="tab.id"
          type="button"
          class="ed-rail-btn"
          :class="{ on: leftPanelOpen && activeSettingsTab === tab.id }"
          :aria-label="tab.label"
          :title="tab.label"
          @click="openRailTab(tab.id)"
        >
          <component :is="tab.icon" aria-hidden="true" />
          <span v-if="tab.id === 'pixels' && !selectedPixels.meta && !selectedPixels.ga" class="ed-rail-dot" aria-hidden="true"></span>
        </button>
      </nav>
      <section v-if="sectionPanelOpen && editingSectionDraft" class="ed-section-panel" aria-label="Editar seção">
        <header class="esp-top">
          <button type="button" class="esp-back" @click="requestCloseSectionEditor">
            <ChevronLeftIcon aria-hidden="true" />
            Configurações
          </button>
          <button
            type="button"
            class="esp-icon-btn"
            :title="(editingSectionDraft as any).enabled === false ? 'Mostrar seção' : 'Esconder seção'"
            :aria-label="(editingSectionDraft as any).enabled === false ? 'Mostrar seção' : 'Esconder seção'"
            @click="toggleEditingSectionVisibility"
          >
            <EyeOffIcon v-if="(editingSectionDraft as any).enabled !== false" aria-hidden="true" />
            <EyeIcon v-else aria-hidden="true" />
          </button>
          <div class="esp-menu-wrap">
            <button type="button" class="esp-icon-btn" aria-label="Mais ações" title="Duplicar, mover, excluir" @click.stop="sectionPanelMenuOpen = !sectionPanelMenuOpen">
              <EllipsisIcon aria-hidden="true" />
            </button>
            <div v-if="sectionPanelMenuOpen" class="esp-menu" @click="sectionPanelMenuOpen = false">
              <button v-if="editingSectionType !== 'header'" type="button" :disabled="editingSectionIndex === 0" @click="runPanelAction('up')"><ArrowUpIcon aria-hidden="true" />Subir</button>
              <button v-if="editingSectionType !== 'header'" type="button" :disabled="editingSectionIndex === sections.length - 1" @click="runPanelAction('down')"><ArrowDownIcon aria-hidden="true" />Descer</button>
              <button v-if="editingSectionType !== 'header'" type="button" @click="runPanelAction('duplicate')"><CopyIcon aria-hidden="true" />Duplicar</button>
              <button type="button" class="danger" @click="runPanelAction('delete')"><Trash2Icon aria-hidden="true" />Excluir</button>
            </div>
          </div>
        </header>
        <div class="esp-title">
          <span class="esp-ico" :class="sectionTone(editingSectionDraft)" aria-hidden="true"><component :is="sectionIcon(editingSectionDraft)" /></span>
          <span class="min-w-0">
            <h2>{{ editingSectionHeaderLabel }}</h2>
            <span>Seção {{ (editingSectionIndex ?? 0) + 1 }} de {{ sections.length }}</span>
          </span>
        </div>
        <div class="esp-body">
          <component :is="editingSectionComponent" ref="editingSectionFormRef" :modelValue="editingSectionDraft" @update:modelValue="updateEditingDraft" />
        </div>
        <footer class="esp-foot">
          <span v-if="hasUnsavedSectionDraftChanges" class="section-editor-dirty"><i aria-hidden="true"></i>Alterações não salvas</span>
          <button type="button" class="esp-btn" @click="requestCloseSectionEditor">Descartar</button>
          <button type="button" class="esp-btn is-primary" @click="saveEditingSection">Salvar seção</button>
        </footer>
      </section>
      <div v-if="newEditor && leftPanelOpen && !sectionPanelOpen" class="ed-settings-v2">
        <div class="esv-head">
          <p class="ed-panel-eyebrow">Configurações da página</p>
          <h2 class="ed-panel-title">{{ railTabs.find(tab => tab.id === activeSettingsTab)?.label }}</h2>
        </div>
        <div class="esv-body ved">
          <template v-if="activeSettingsTab === 'general'">
            <EdGroup title="Página">
              <EdText :model-value="pageTitle" label="Título da página" @update:model-value="pageTitle = $event; scheduleWhatsAppUpdate()" />
              <label class="ved-field">
                <span class="ved-label">Link da página</span>
                <span class="esv-slug">
                  <span class="esv-slug-base" :title="slugBaseLabel">{{ slugBaseLabel }}</span>
                  <input class="ved-input" :value="pageSlug" @input="handleSlugInput" />
                </span>
                <span class="ved-hint">Use apenas letras, números e hífens, sem espaços nem acentos.</span>
              </label>
              <EdText
                :model-value="pageShortDescription"
                label="Descrição curta"
                multiline
                hint="Aparece no Google e ao compartilhar no WhatsApp."
                placeholder="Ex.: Pacote completo com transporte, hospedagem e ingressos."
                @update:model-value="pageShortDescription = $event"
              />
            </EdGroup>
          </template>

          <template v-else-if="activeSettingsTab === 'colors'">
            <EdGroup title="Cor de destaque">
              <p class="ved-hint">Botões, selos e ícones de todas as seções.</p>
              <label class="esv-color">
                <input v-model="ctaColor" type="color" aria-label="Cor de destaque" />
                <input class="ved-input" :value="ctaColor" @input="ctaColor = normalizeHexColor(($event.target as HTMLInputElement).value, ctaColor)" />
              </label>
            </EdGroup>
            <EdGroup title="Fundo das seções">
              <p class="ved-hint">As seções alternam entre as duas cores, menos a capa. Cada seção pode ter o próprio fundo em Aparência.</p>
              <label class="esv-color">
                <span class="ved-label">Cor 1</span>
                <input v-model="colorA" type="color" aria-label="Cor de fundo 1" />
                <input class="ved-input" :value="colorA" @input="colorA = normalizeHexColor(($event.target as HTMLInputElement).value, colorA)" />
              </label>
              <label class="esv-color">
                <span class="ved-label">Cor 2</span>
                <input v-model="colorB" type="color" aria-label="Cor de fundo 2" />
                <input class="ved-input" :value="colorB" @input="colorB = normalizeHexColor(($event.target as HTMLInputElement).value, colorB)" />
              </label>
            </EdGroup>
            <EdGroup v-if="designV2Enabled" title="Visual das seções">
              <EdToggle v-model="useLegacyDesign" :label="viewCopy.form.legacyDesignLabel" :hint="viewCopy.form.legacyDesignHint" />
            </EdGroup>
          </template>

          <template v-else-if="activeSettingsTab === 'pixels'">
            <div v-if="!selectedPixels.meta && !selectedPixels.ga" class="esv-warn">
              <b>Nenhum pixel nesta página</b>
              <span>Sem pixel, as visitas e os cliques não chegam no Meta Ads nem no Google Analytics.</span>
            </div>
            <EdGroup title="Pixels">
              <p v-if="!canSelectPixel" class="ved-info">{{ viewCopy.pixels.planHint }}</p>
              <template v-else>
                <label class="ved-field">
                  <span class="ved-label">{{ viewCopy.pixels.metaLabel }}</span>
                  <select v-model="selectedPixels.meta" class="ved-select" :disabled="!metaPixelOptions.length">
                    <option value="">{{ viewCopy.pixels.metaPlaceholder }}</option>
                    <option v-for="p in metaPixelOptions" :key="p.name" :value="p.name">{{ p.name }}</option>
                  </select>
                  <span v-if="!metaPixelOptions.length" class="ved-hint">{{ viewCopy.pixels.metaEmptyHint }}</span>
                </label>
                <label class="ved-field">
                  <span class="ved-label">{{ viewCopy.pixels.googleLabel }}</span>
                  <select v-model="selectedPixels.ga" class="ved-select" :disabled="!gaPixelOptions.length">
                    <option value="">{{ viewCopy.pixels.googlePlaceholder }}</option>
                    <option v-for="p in gaPixelOptions" :key="p.name" :value="p.name">{{ p.name }}</option>
                  </select>
                  <span v-if="!gaPixelOptions.length" class="ved-hint">{{ viewCopy.pixels.googleEmptyHint }}</span>
                </label>
              </template>
              <button type="button" class="esv-link" @click="goIntegrations">Gerenciar pixels em Integrações</button>
            </EdGroup>
            <EdGroup v-if="canSelectPixel" title="Eventos enviados">
              <EdToggle v-model="trackingEvents.pageView" :label="viewCopy.pixels.eventPageView" />
              <EdToggle v-model="trackingEvents.ctaClicks" :label="viewCopy.pixels.eventCtaClicks" />
              <EdToggle v-model="trackingEvents.leads" :label="viewCopy.pixels.eventLeads" />
            </EdGroup>
          </template>

          <template v-else-if="activeSettingsTab === 'capture'">
            <EdGroup v-if="leadFeatureAllowed" title="Formulário">
              <p class="ved-hint">{{ viewCopy.leadSection.description }}</p>
              <p v-if="leadFormsLoading" class="ved-info">{{ viewCopy.leadSection.loading }}</p>
              <p v-else-if="!leadForms.length" class="ved-info">{{ viewCopy.leadSection.empty }} <b>{{ viewCopy.leadSection.emptyAction }}</b></p>
              <template v-else>
                <label class="ved-field">
                  <span class="ved-label">{{ viewCopy.leadSection.selectLabel }}</span>
                  <select v-model="selectedLeadFormId" class="ved-select">
                    <option value="">{{ viewCopy.leadSection.selectPlaceholder }}</option>
                    <option v-for="form in leadForms" :key="form.id" :value="String(form.id)">{{ form.name || form.title }} ({{ form.total_leads ?? 0 }} leads)</option>
                  </select>
                  <span class="ved-hint">{{ viewCopy.leadSection.selectHint }}</span>
                </label>
                <template v-if="selectedLeadForm">
                  <EdToggle v-model="leadCaptureOptional" :label="viewCopy.leadSection.optionalToggle" />
                  <button type="button" class="esv-btn" @click="openLeadFormPreview(selectedLeadForm)">{{ viewCopy.leadSection.previewButton }}</button>
                </template>
              </template>
              <button type="button" class="esv-link" @click="goLeads">{{ viewCopy.leadSection.manageButton }}</button>
            </EdGroup>
            <EdGroup v-else :title="viewCopy.leadSection.blockedTitle">
              <p class="ved-hint">{{ viewCopy.leadSection.blockedDescription }}</p>
              <button type="button" class="esv-btn is-primary" @click="goPlans">{{ viewCopy.actions.viewPlans }}</button>
            </EdGroup>
          </template>
        </div>
      </div>
      <div v-show="!newEditor" class="editor-settings-shell ed-settings-card">
        <div class="editor-settings-grid">
          <div
            ref="settingsPanelRef"
            class="settings-panel rounded-2xl p-4 md:p-5"
          >
        <div
          class="settings-panel-content mt-0 h-full overflow-y-auto pr-1"
          :class="activeSettingsTab==='colors' ? 'flex min-h-full w-full items-center' : 'space-y-2'"
        >
          <div class="w-full space-y-4 px-2 py-0">
            <div v-if="activeSettingsTab==='general'" ref="generalSettingsRef" class="space-y-2">
              <div class="grid gap-4 lg:grid-cols-[3fr_2fr]">
                <div class="space-y-3">
                  <div>
                    <label class="text-[13px] font-semibold uppercase tracking-[0.04em] text-slate-500">TÍTULO DA PÁGINA</label>
                    <input
                      v-model="pageTitle"
                      @blur="scheduleWhatsAppUpdate"
                      class="mt-1 w-full rounded-[12px] border border-slate-200 bg-white px-4 py-2 text-[17px] text-slate-900 dark:border-white/15 dark:bg-[#05070F] dark:text-white"
                    />
                  </div>
                  <div>
                    <label class="text-[13px] font-semibold uppercase tracking-[0.04em] text-slate-500">LINK DA PÁGINA</label>
                    <div class="slug-row mt-1 flex w-full overflow-hidden rounded-[12px] border border-slate-200">
                      <div class="slug-prefix shrink-0 border-r border-slate-200 bg-slate-50 px-4 py-2 text-[16px] font-semibold text-slate-600">
                        {{ slugBaseLabel }}
                      </div>
                      <input
                        :value="pageSlug"
                        @input="handleSlugInput"
                        class="slug-input w-full border-0 bg-white px-4 py-2 text-[16px] text-slate-800 focus:outline-none dark:bg-[#05070F] dark:text-white"
                      />
                    </div>
                    <p class="mt-1 text-[13px] text-slate-500">
                      Use apenas letras, números e hífens. Evite espaços e acentos.
                    </p>
                  </div>
                </div>
                <div>
                  <label class="text-[13px] font-semibold uppercase tracking-[0.04em] text-slate-500">DESCRIÇÃO CURTA</label>
                  <textarea
                    v-model="pageShortDescription"
                    rows="5"
                    placeholder="Ex: Pacote completo para Beto Carrero com transporte, hospedagem e ingressos inclusos."
                    class="mt-1 w-full rounded-[12px] border border-slate-200 bg-white px-4 py-2 text-[16px] text-slate-700 placeholder:text-slate-400 dark:border-white/15 dark:bg-[#05070F] dark:text-white"
                  />
                </div>
              </div>
            </div>
            <div v-if="activeSettingsTab==='colors'" class="mt-0 w-full">
              <div
                class="settings-colors-grid grid w-full items-start gap-x-8 gap-y-4 text-sm text-slate-600"
                style="grid-template-columns: minmax(0, 1fr);"
              >
                <div class="min-w-0 space-y-3 pt-0.5">
                <p class="text-[17px] font-bold uppercase tracking-[0.03em] leading-none text-slate-700">{{ viewCopy.form.backgroundLabel }}</p>
                <p class="text-[14px] leading-tight text-slate-500">{{ viewCopy.form.backgroundHint }}</p>
                  <div class="space-y-4 pt-2">
                    <label class="flex items-center gap-4">
                    <span class="w-[70px] whitespace-nowrap text-[18px] font-semibold text-slate-700">{{ viewCopy.form.colorA }}</span>
                    <input type="color" v-model="colorA" class="color-chip" />
                    <input
                      :value="colorA"
                      @input="colorA = normalizeHexColor(($event.target as HTMLInputElement).value, colorA)"
                      class="w-[112px] rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[17px] font-semibold uppercase tracking-wide text-slate-700"
                    />
                  </label>
                    <label class="flex items-center gap-4">
                    <span class="w-[70px] whitespace-nowrap text-[18px] font-semibold text-slate-700">{{ viewCopy.form.colorB }}</span>
                    <input type="color" v-model="colorB" class="color-chip" />
                    <input
                      :value="colorB"
                      @input="colorB = normalizeHexColor(($event.target as HTMLInputElement).value, colorB)"
                      class="w-[112px] rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[17px] font-semibold uppercase tracking-wide text-slate-700"
                    />
                  </label>
                </div>
              </div>
                <div class="min-w-0 space-y-3 pt-0.5">
                <p class="text-[17px] font-bold uppercase tracking-[0.03em] leading-none text-slate-700">{{ viewCopy.form.ctaColorLabel }}</p>
                <p class="text-[14px] leading-tight text-slate-500">{{ viewCopy.form.ctaColorHint }}</p>
                  <label class="flex items-center gap-4 pt-2">
                  <span class="w-[70px] whitespace-nowrap text-[18px] font-semibold text-slate-700">Cor</span>
                  <input
                    type="color"
                    v-model="ctaColor"
                    class="color-chip"
                  />
                  <input
                    :value="ctaColor"
                    @input="ctaColor = normalizeHexColor(($event.target as HTMLInputElement).value, ctaColor)"
                    class="w-[112px] rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[17px] font-semibold uppercase tracking-wide text-slate-700"
                  />
                </label>
              </div>
                <div v-if="designV2Enabled" class="min-w-0 space-y-3 border-t border-slate-200 pt-4">
                  <label class="flex cursor-pointer items-start justify-between gap-4">
                    <span class="space-y-1">
                      <span class="block text-[17px] font-bold uppercase tracking-[0.03em] leading-none text-slate-700">{{ viewCopy.form.legacyDesignLabel }}</span>
                      <span class="block text-[14px] leading-tight text-slate-500">{{ viewCopy.form.legacyDesignHint }}</span>
                    </span>
                    <input v-model="useLegacyDesign" type="checkbox" class="mt-1 h-5 w-5 flex-shrink-0 accent-[var(--primary)]" />
                  </label>
                </div>
              </div>
            </div>
          </div>
          <div class="px-2 pt-0" :class="activeSettingsTab==='pixels' ? 'space-y-1' : 'space-y-4'">
            <div v-if="activeSettingsTab==='pixels'" class="-mt-[6px] space-y-0">
              <div class="flex items-start justify-between gap-3">
                <p class="text-[17px] font-bold uppercase leading-none tracking-[0.03em] text-slate-700">{{ viewCopy.pixels.title }}</p>
                <button
                  type="button"
                  class="inline-flex items-center self-start rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                  @click="goIntegrations"
                >
                  Gerenciar pixels
                </button>
              </div>
              <p class="text-xs text-slate-500">
                {{ viewCopy.pixels.helper }}
              </p>
              <p v-if="!canSelectPixel" class="text-xs text-slate-500">
                {{ viewCopy.pixels.planHint }}
              </p>
            </div>

            <div v-if="activeSettingsTab==='pixels'" class="mt-0 space-y-1">
              <div
                v-if="!canSelectPixel"
                class="rounded-lg border border-dashed border-slate-200 bg-white/80 px-3 py-2 text-sm text-slate-500 dark:border-[#363636] dark:bg-[#0d0d0d] dark:text-slate-300"
              >
              </div>

              <template v-else>
                <div class="grid gap-2 sm:grid-cols-2">
                  <div>
                    <label class="font-semibold uppercase tracking-[0.03em] text-slate-800 dark:text-white">{{ viewCopy.pixels.metaLabel }}</label>
                    <select
                      v-model="selectedPixels.meta"
                      class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-[#363636] dark:bg-[#101010] dark:text-white"
                      :disabled="!metaPixelOptions.length"
                    >
                      <option value="">{{ viewCopy.pixels.metaPlaceholder }}</option>
                      <option v-for="p in metaPixelOptions" :key="p.name" :value="p.name">
                        {{ p.name }} - Meta
                      </option>
                    </select>
                    <p v-if="!metaPixelOptions.length" class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ viewCopy.pixels.metaEmptyHint }}</p>
                  </div>
                  <div>
                    <label class="font-semibold uppercase tracking-[0.03em] text-slate-800 dark:text-white">{{ viewCopy.pixels.googleLabel }}</label>
                    <select
                      v-model="selectedPixels.ga"
                      class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-[#363636] dark:bg-[#101010] dark:text-white"
                      :disabled="!gaPixelOptions.length"
                    >
                      <option value="">{{ viewCopy.pixels.googlePlaceholder }}</option>
                      <option v-for="p in gaPixelOptions" :key="p.name" :value="p.name">
                        {{ p.name }} - GA4
                      </option>
                    </select>
                    <p v-if="!gaPixelOptions.length" class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ viewCopy.pixels.googleEmptyHint }}</p>
                  </div>
                </div>

                <div class="px-0 py-1 text-sm text-slate-700 dark:text-slate-200">
                  <p class="font-semibold uppercase tracking-[0.03em] text-slate-800 dark:text-white">{{ viewCopy.pixels.eventsTitle }}</p>

                  <div class="mt-2 flex flex-wrap gap-4">
                    <label class="flex items-center gap-2">
                      <input type="checkbox" v-model="trackingEvents.pageView" class="h-4 w-4" />
                      {{ viewCopy.pixels.eventPageView }}
                    </label>

                    <label class="flex items-center gap-2">
                      <input type="checkbox" v-model="trackingEvents.ctaClicks" class="h-4 w-4" />
                      {{ viewCopy.pixels.eventCtaClicks }}
                    </label>

                    <label class="flex items-center gap-2">
                      <input type="checkbox" v-model="trackingEvents.leads" class="h-4 w-4" />
                      {{ viewCopy.pixels.eventLeads }}
                    </label>
                  </div>
                </div>
              </template>
            </div>
          </div>

    <div class="space-y-4 px-2 pt-0 dark:text-white">
      <div v-if="leadFeatureAllowed && activeSettingsTab==='capture'" class="-mt-1">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 class="text-[17px] font-bold uppercase tracking-[0.03em] leading-none text-slate-700 dark:text-white">{{ viewCopy.leadSection.title }}</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">
            {{ viewCopy.leadSection.description }}
          </p>
        </div>
        <button
          type="button"
          class="w-full rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 dark:border-white/20 dark:text-white dark:hover:bg-white/10 sm:w-auto lg:shrink-0"
          @click="goLeads"
        >
          {{ viewCopy.leadSection.manageButton }}
        </button>
      </div>
      <div class="mt-2 space-y-3">
        <div
          v-if="leadFormsLoading"
          class="rounded-xl border border-dashed border-slate-200 px-3 py-2 text-sm text-slate-500 dark:border-white/20 dark:text-slate-300"
        >
          {{ viewCopy.leadSection.loading }}
        </div>
        <div
          v-else-if="!leadForms.length"
          class="rounded-xl border border-dashed border-slate-200 px-4 py-4 text-sm text-slate-500 dark:border-white/20 dark:text-slate-300"
        >
          {{ viewCopy.leadSection.empty }}
          <span class="font-semibold">{{ viewCopy.leadSection.emptyAction }}</span>
        </div>
        <div v-else class="space-y-4">
          <div class="flex flex-col gap-4 md:flex-row md:items-center">
            <div class="flex-1 space-y-1">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">{{ viewCopy.leadSection.selectLabel }}</label>
              <select
                v-model="selectedLeadFormId"
                class="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/15 dark:bg-[#05070F] dark:text-white"
              >
                <option value="">{{ viewCopy.leadSection.selectPlaceholder }}</option>
                <option v-for="form in leadForms" :key="form.id" :value="String(form.id)">
                  {{ form.name || form.title }} ({{ form.total_leads ?? 0 }} leads)
                </option>
              </select>
              <p class="text-xs text-slate-500 dark:text-slate-400">
                {{ viewCopy.leadSection.selectHint }}
              </p>
            </div>
            <template v-if="selectedLeadForm">
              <div class="flex items-center md:w-48 md:justify-center">
                <button
                  type="button"
                  class="preview-pill w-full justify-center md:w-auto md:min-w-[10rem]"
                  @click="openLeadFormPreview(selectedLeadForm)"
                >
                  {{ viewCopy.leadSection.previewButton }}
                </button>
              </div>
              <div class="flex items-center gap-3 px-1 py-1 text-sm text-slate-600 dark:text-slate-300 md:w-auto">
                <input
                  type="checkbox"
                  v-model="leadCaptureOptional"
                  class="h-4 w-4 rounded border-slate-200 text-brand focus:ring-brand/40 dark:border-white/30"
                />
                <p class="font-semibold text-slate-800 dark:text-white">{{ viewCopy.leadSection.optionalToggle }}</p>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
    <div
      v-else-if="activeSettingsTab==='capture'"
      class="mt-3 rounded-2xl border border-dashed border-slate-200 bg-white/70 p-6 text-center shadow-inner dark:border-white/10 dark:bg-[#101010]/70"
    >
      <h3 class="text-xl font-semibold text-slate-900 dark:text-white">{{ viewCopy.leadSection.blockedTitle }}</h3>
      <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">
        {{ viewCopy.leadSection.blockedDescription }}
      </p>
      <button
        type="button"
        class="mt-4 rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-brand-dark"
        @click="goPlans"
      >
        {{ viewCopy.actions.viewPlans }}
      </button>
    </div>

    </div>
  </div>
  </div>
  </div>
  </div>
  </aside>
      <section v-if="newEditor ? layersOpen && !showAiAssistant : activeSettingsTab === 'content'" class="ed-sections">
        <div class="ed-sections-head">
          <button
            v-if="newEditor"
            type="button"
            class="ed-rail-btn is-small"
            aria-label="Recolher camadas"
            title="Recolher camadas"
            @click="layersOpen = false"
          >
            <PanelRightCloseIcon aria-hidden="true" />
          </button>
          <div class="ed-sections-titles">
            <h2>{{ newEditor ? "Camadas" : "Seções da página" }}</h2>
            <span>{{ newEditor ? `${visibleSectionsCount} de ${sections.length} visíveis` : `${visibleSectionsCount} ${visibleSectionsCount === 1 ? "visível" : "visíveis"}` }}</span>
          </div>
          <button v-if="newEditor" type="button" class="ed-layers-add" @click="openSectionPicker(null)">
            <PlusIcon aria-hidden="true" />
            Seção
          </button>
        </div>
        <ul class="ed-section-list">
          <li
            v-for="(section, idx) in sections"
            :key="(section as any)?.anchorId || idx"
            class="ed-section-row"
            :class="{
              'is-off': !(section as any).enabled,
              'is-drag-over': sectionDragOver === idx && sectionDragFrom !== idx,
              'is-dragging': sectionDragFrom === idx
            }"
            :draggable="canDragSection(idx)"
            @dragstart="handleSectionDragStart(idx, $event)"
            @dragover.prevent="sectionDragOver = idx"
            @dragleave="sectionDragOver = sectionDragOver === idx ? null : sectionDragOver"
            @drop.prevent="handleSectionDrop(idx)"
            @dragend="resetSectionDrag"
          >
            <span class="ed-grip" :class="{ 'is-locked': !canDragSection(idx) }" aria-hidden="true">
              <GripVerticalIcon aria-hidden="true" />
            </span>
            <button type="button" class="ed-section-main" :disabled="isLockedFooterSection(section)" @click="openSectionEditor(idx)">
              <span class="ed-section-icon" :class="sectionTone(section)" aria-hidden="true">
                <component :is="sectionIcon(section)" aria-hidden="true" />
              </span>
              <span class="min-w-0">
                <span class="ed-section-name">{{ sectionLabelOf(section) }}</span>
                <span class="ed-section-sub">{{ (section as any).enabled ? sectionSummary(section) : "Oculta" }}</span>
              </span>
            </button>
            <button
              type="button"
              role="switch"
              class="ed-switch"
              :class="{ on: (section as any).enabled }"
              :aria-checked="!!(section as any).enabled"
              :disabled="isLockedFooterSection(section)"
              :title="(section as any).enabled ? 'Esconder seção' : 'Mostrar seção'"
              @click="toggleSectionEnabled(idx)"
            ><i></i></button>
          </li>
        </ul>
        <button v-if="!newEditor" type="button" class="ed-add-section" @click="openSectionPicker(null)">
          <PlusIcon aria-hidden="true" />
          Adicionar seção
        </button>
        <p class="ed-sections-hint">{{ newEditor ? "Arraste para reordenar. O interruptor esconde a seção sem apagar." : "Clique numa seção (aqui ou na prévia) para editar. Arraste para mudar a ordem; o interruptor esconde a seção sem apagar." }}</p>
      </section>
      <aside v-if="newEditor && !layersOpen && !showAiAssistant" class="ed-layers-mini" aria-label="Camadas">
        <button type="button" class="ed-rail-btn" aria-label="Abrir camadas" title="Abrir camadas" @click="layersOpen = true">
          <PanelRightOpenIcon aria-hidden="true" />
        </button>
        <span class="ed-layers-mini-sep" aria-hidden="true"></span>
        <button
          v-for="(section, idx) in sections"
          :key="(section as any)?.anchorId || idx"
          type="button"
          class="ed-layers-mini-item"
          :class="[sectionTone(section), { 'is-off': !(section as any).enabled }]"
          :title="sectionLabelOf(section)"
          :disabled="isLockedFooterSection(section)"
          @click="openSectionEditor(idx)"
        >{{ idx + 1 }}</button>
        <button type="button" class="ed-layers-mini-add" aria-label="Adicionar seção" title="Adicionar seção" @click="openSectionPicker(null)">
          <PlusIcon aria-hidden="true" />
        </button>
      </aside>

      <div
        :class="[
          'editor-preview-shell md:sticky md:top-6 rounded-2xl border border-border bg-card p-4 text-card-foreground shadow-soft',
          showAiAssistant ? 'ai-assistant-open' : ''
        ]"
      >
      <div class="ed-preview-head">
        <div class="flex flex-col gap-1">
          <p class="ed-preview-eyebrow">{{ viewCopy.preview.title }}</p>
          <p
            v-if="isMobileViewport && previewDevice === 'mobile'"
            class="rounded-2xl bg-amber-100 px-3 py-2 text-center text-sm font-semibold text-amber-700"
          >
            {{ viewCopy.preview.mobileHint }}
          </p>
        </div>
        <div
          v-if="!isMobileViewport"
          class="inline-flex select-none items-center rounded-full bg-muted p-1 text-sm font-semibold text-muted-foreground"
        >
          <button
            v-if="!isMobileViewport"
            type="button"
            class="inline-flex select-none items-center gap-1.5 rounded-full px-3.5 py-1.5 transition"
            :class="previewDevice === 'desktop' ? 'bg-card text-accent-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
            @click="previewDevice = 'desktop'"
          >
            <MonitorIcon aria-hidden="true" class="h-3.5 w-3.5" />
            {{ viewCopy.preview.desktopLabel }}
          </button>
          <button
            type="button"
            class="inline-flex select-none items-center gap-1.5 rounded-full px-3.5 py-1.5 transition"
            :class="previewDevice === 'mobile' ? 'bg-card text-accent-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
            @click="previewDevice = 'mobile'"
          >
            <SmartphoneIcon aria-hidden="true" class="h-3.5 w-3.5" />
            {{ viewCopy.preview.mobileLabel }}
          </button>
        </div>
        <span v-if="!isMobileViewport" class="editor-preview-scale">
          {{
            newEditor
              ? (previewDevice === 'mobile' ? "390 px" : `${desktopPreviewWidth} px · ${Math.round(desktopPreviewZoom * 100)}%`)
              : (previewDevice === 'mobile' ? "Largura de celular (390 px)" : `Largura de computador (${desktopPreviewWidth} px) · ${Math.round(desktopPreviewZoom * 100)}%`)
          }}
        </span>
      </div>
      <div class="ed-stage" :class="{ 'is-framed': !isMobileViewport, 'is-mobile-preview': previewDevice === 'mobile' }">
        <div
          :class="isMobileViewport
            ? (previewDevice === 'mobile' ? '-mx-4 w-[calc(100%+2rem)] overflow-hidden' : '')
            : (previewDevice === 'mobile' ? 'ed-phone' : 'ed-browser')"
        >
          <div v-if="!isMobileViewport && previewDevice === 'desktop'" class="ed-browser-bar">
            <i></i><i></i><i></i>
            <span>{{ previewAddressLabel }}</span>
          </div>
          <div ref="previewCanvasRef" class="ed-screen">
          <div :style="desktopPreviewStyle">
            <div class="space-y-0 preview-light">
              <template v-if="sections.length === 0">
                <div class="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 px-4 py-12 text-center text-sm text-slate-500">
                  <p>{{ viewCopy.preview.emptyState }}</p>
                  <div class="mt-6 flex justify-center">
                    <button
                      type="button"
                      class="inline-flex items-center gap-2 rounded-full border border-emerald-400 bg-emerald-50 px-5 py-3 text-sm font-semibold text-emerald-700 shadow-sm transition hover:bg-emerald-100"
                      @click="openSectionPicker(null)"
                    >
                      <PlusIcon class="h-3.5 w-3.5" aria-hidden="true" />
                      {{ viewCopy.preview.emptyAction }}
                    </button>
                  </div>
                </div>
              </template>
              <template v-else>
                <template v-for="(section, idx) in sections" :key="(section as any)?.anchorId || idx">
                    <div v-if="section" class="space-y-0" :class="{ 'v2ed-slot': newEditor }">
                    <div v-if="newEditor && idx > 0 && canInsertBefore(idx)" class="v2ed-ins">
                      <span class="v2ed-ins-line" aria-hidden="true"></span>
                      <button type="button" class="v2ed-ins-btn" @click.stop="openSectionPicker(idx - 1)">
                        <PlusIcon aria-hidden="true" />
                        <span>Adicionar seção</span>
                      </button>
                    </div>
                    <div
                      class="group relative"
                      :class="[
                        (section as any).type === 'header' ? 'z-30 overflow-visible' : 'overflow-hidden',
                        { 'v2ed-sec': newEditor && (section as any).enabled, 'is-editing': sectionPanelOpen && editingSectionIndex === idx }
                      ]"
                      :data-preview-index="idx"
                      @click.capture="handleSectionTap(idx, $event)"
                      :ref="el => registerPreviewSection(el, idx)"
                    >
                      <div v-if="(section as any).enabled" class="preview-section-host public-tokens">
                        <component
                          :is="pickSectionComponent((section as any).type, previewDesign, publicComponents)"
                          :section="sectionPanelOpen && editingSectionIndex === idx && editingSectionDraft ? livePreviewDraft : previewSections[idx]?.type === section.type && previewSections[idx]?.anchorId === section.anchorId ? previewSections[idx] : section"
                          :previewDevice="previewDevice"
                          v-bind="previewSectionExtraProps(section)"
                          :class="[
                            'transition duration-200',
                            desktopHoverEnabled && !newEditor ? 'group-hover:opacity-80 group-hover:brightness-95' : ''
                          ]"
                        />
                      </div>
                      <template v-if="newEditor && (section as any).enabled">
                        <span class="v2ed-ring" aria-hidden="true"></span>
                        <span class="v2ed-tag">{{ sectionLabelOf(section) }}</span>
                        <div
                          class="v2ed-bar"
                          role="toolbar"
                          :aria-label="`Ações da seção ${sectionLabelOf(section)}`"
                          data-overlay-control="true"
                          @click.stop
                        >
                          <span v-if="isLockedFooterSection(section)" class="v2ed-locked">{{ viewCopy.overlay.footerLocked }}</span>
                          <template v-else>
                            <button type="button" class="v2ed-edit" @click.stop="openSectionEditor(idx)">
                              <PencilIcon aria-hidden="true" />
                              <span>{{ viewCopy.overlay.edit }}</span>
                            </button>
                            <template v-if="(section as any).type !== 'header'">
                              <i class="v2ed-sep" aria-hidden="true"></i>
                              <button type="button" class="v2ed-btn" :disabled="idx === 0" :title="viewCopy.overlay.moveUp" :aria-label="viewCopy.overlay.moveUp" @click.stop="moveSection(idx, -1)">
                                <ArrowUpIcon aria-hidden="true" />
                              </button>
                              <button type="button" class="v2ed-btn" :disabled="idx === sections.length - 1" :title="viewCopy.overlay.moveDown" :aria-label="viewCopy.overlay.moveDown" @click.stop="moveSection(idx, 1)">
                                <ArrowDownIcon aria-hidden="true" />
                              </button>
                              <button type="button" class="v2ed-btn" :title="viewCopy.overlay.duplicate" :aria-label="viewCopy.overlay.duplicate" @click.stop="duplicateSection(idx)">
                                <CopyIcon aria-hidden="true" />
                              </button>
                            </template>
                            <button type="button" class="v2ed-btn" title="Esconder seção" aria-label="Esconder seção" @click.stop="toggleSectionEnabled(idx)">
                              <EyeOffIcon aria-hidden="true" />
                            </button>
                            <i class="v2ed-sep" aria-hidden="true"></i>
                            <button type="button" class="v2ed-btn is-danger" :title="viewCopy.overlay.delete" :aria-label="viewCopy.overlay.delete" @click.stop="removeSection(idx)">
                              <Trash2Icon aria-hidden="true" />
                            </button>
                          </template>
                        </div>
                      </template>
                        <div
                          v-if="(section as any).enabled && !newEditor"
                          :class="[
                            'pointer-events-none absolute inset-0 z-10 flex flex-col bg-slate-900/0 opacity-0 transition duration-200 px-4 py-5',
                            (section as any).type === 'header' ? '!z-[60]' : '',
                            !isMobileOverlayMode ? 'group-hover:opacity-100 group-hover:bg-slate-900/15 group-focus-within:opacity-100' : '',
                            isMobileOverlayMode && mobileOverlayVisible[idx] ? '!opacity-100 !bg-slate-900/20' : ''
                          ]"
                        >
                          <div v-if="(section as any).type !== 'header'" class="flex items-start justify-between gap-3 pb-3">
                            <span class="pointer-events-auto inline-flex items-center rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate-700 shadow">
                              {{ sectionLabels[(section as any).type] || (section as any).type }}
                              <span v-if="(section as any).enabled === false" class="ml-1 text-red-500">(desativada)</span>
                            </span>
                          </div>
                        <div
                          class="flex flex-1 items-center px-4"
                          :class="(section as any).type === 'header' ? 'justify-center pb-0' : 'justify-center pb-8'"
                        >
                          <div
                            class="pointer-events-auto relative rounded-[36px] bg-[#1f2330] px-7 py-6 text-center shadow-2xl backdrop-blur-lg"
                            :class="(section as any).type === 'header' ? '!rounded-full !px-2 !py-2' : ''"
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
                                class="overlay-action-button inline-flex items-center gap-2 rounded-full border border-white/40 bg-white/20 text-xs font-semibold text-white !text-white shadow-md transition hover:bg-white/30 dark:border-white/40 dark:bg-white/25 dark:text-white dark:hover:bg-white/40 dark:shadow-white/45"
                                :class="[overlayButtonSizingClass, isMobileOverlayMode ? 'col-span-2' : '']"
                                @click.stop="openSectionEditor(idx)"
                              >
                            <PencilIcon class="h-4 w-4" aria-hidden="true" />
                            <span class="overlay-label text-white">{{ viewCopy.overlay.edit }}</span>
                          </button>

                          <button
                            v-if="(section as any).type !== 'header'"
                            type="button"
                            class="overlay-action-button inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 text-xs font-semibold text-white !text-white transition hover:bg-white/20 dark:border-white/35 dark:bg-white/22 dark:text-white dark:hover:bg-white/35"
                            :class="overlayButtonSizingClass"
                            :disabled="idx === 0"
                            @click.stop="moveSection(idx, -1)"
                          >
                            <ArrowUpIcon class="h-4 w-4" aria-hidden="true" />
                            <span class="overlay-label text-white">{{ viewCopy.overlay.moveUp }}</span>
                          </button>

                          <button
                            v-if="(section as any).type !== 'header'"
                            type="button"
                            class="overlay-action-button inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 text-xs font-semibold text-white !text-white transition hover:bg-white/20 dark:border-white/35 dark:bg-white/22 dark:text-white dark:hover(bg-white/35"
                            :class="overlayButtonSizingClass"
                            :disabled="idx === sections.length - 1"
                            @click.stop="moveSection(idx, 1)"
                          >
                            <ArrowDownIcon class="h-4 w-4" aria-hidden="true" />
                            <span class="overlay-label text-white">{{ viewCopy.overlay.moveDown }}</span>
                          </button>

                          <button
                            v-if="(section as any).type !== 'header'"
                            type="button"
                            class="overlay-action-button inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 text-xs font-semibold text-white !text-white shadow-sm transition hover:bg-white/20 dark:border-white/25 dark:bg-white/15 dark:text-white dark:hover(bg-white/30"
                            :class="overlayButtonSizingClass"
                            @click.stop="duplicateSection(idx)"
                          >
                            <CopyIcon class="h-4 w-4" aria-hidden="true" />
                            <span class="overlay-label text-white">{{ viewCopy.overlay.duplicate }}</span>
                          </button>

                          <button
                            type="button"
                            class="overlay-action-button inline-flex items-center gap-2 rounded-full border border-red-300/70 bg-red-400/10 text-xs font-semibold text-red-100 transition hover:bg-red-400/20 dark:border-red-400/60 dark:bg-red-500/25 dark:text-white dark:hover:bg-red-500/40 !text-white"
                            :class="overlayButtonSizingClass"
                            @click.stop="removeSection(idx)"
                          >
                            <Trash2Icon class="h-4 w-4" aria-hidden="true" />
                            <span class="overlay-label text-white">{{ viewCopy.overlay.delete }}</span>
                          </button>
                        </div>
                      </template>
                          <template v-else>
                            <div class="rounded-full border border-white/30 bg-white/10 px-4 py-2 text-center text-xs font-semibold text-white dark:border-white/18 dark:bg-white/10 dark:text-white">
                              {{ viewCopy.overlay.footerLocked }}
                            </div>
                          </template>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
                <div v-if="newEditor" class="v2ed-end">
                  <div class="v2ed-ins is-end">
                    <span class="v2ed-ins-line" aria-hidden="true"></span>
                    <button type="button" class="v2ed-ins-btn" @click.stop="openSectionPicker(null)">
                      <PlusIcon aria-hidden="true" />
                      <span>Adicionar seção</span>
                    </button>
                  </div>
                  <span class="v2ed-end-label">Fim da página</span>
                </div>
              </template>
            </div>
          </div>
          </div>
        </div>
      </div>
      </div>
      </div>
    </div>

    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="previewModalVisible && previewForm"
          class="fixed inset-0 z-[120] flex min-h-screen items-center justify-center px-4 py-6"
        >
          <div
            class="absolute inset-0 bg-slate-950/65 backdrop-blur-sm"
            @click="hideLeadFormPreview"
          ></div>
          <div class="relative z-10 w-full max-w-xl">
            <button
              type="button"
              class="absolute right-3 top-3 rounded-full bg-black/70 p-2 text-white shadow-lg"
              @click="hideLeadFormPreview"
            >
              <XIcon class="h-4 w-4" aria-hidden="true" />
            </button>
            <LeadFormPreview v-if="previewForm" :form="previewForm" />
          </div>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body">
      <div
        v-if="isSectionEditorOpen && editingSectionComponent && editingSectionDraft && !sectionPanelOpen"
        class="app-modal-overlay fixed inset-0 z-40 flex h-full w-full items-center justify-center px-4 py-10 md:py-20"
        @click.self="requestCloseSectionEditor"
      >
        <div
          ref="sectionModalPanelRef"
          class="editor-dialog-shell section-editor-dialog w-full overflow-hidden flex flex-col"
          :class="[isMobileViewport ? '' : 'md:rounded-[20px] md:shadow-2xl', { 'is-v2-form': usesV2Form }]"
          :style="usesV2Form ? undefined : sectionModalPanelStyle"
        >
          <div ref="sectionModalHeaderRef" class="section-editor-header flex items-center justify-between px-6 py-4">
            <div>
              <p class="section-editor-eyebrow">Editando seção</p>
              <h3 class="section-editor-title">{{ editingSectionHeaderLabel }}</h3>
            </div>
            <button
              class="section-editor-close"
              @click="requestCloseSectionEditor"
              aria-label="Fechar"
            >
              ×
            </button>
          </div>
          <div
            ref="sectionModalBodyRef"
            class="section-editor-body flex-1 overflow-y-auto border-t border-border bg-background pl-0 pr-0"
            :class="{ 'is-v2-form': usesV2Form }"
          >
            <component
              :is="editingSectionComponent"
              ref="editingSectionFormRef"
              class="block h-full"
              :modelValue="editingSectionDraft"
              v-bind="editingSectionType === 'header' ? { pageSections: sections } : {}"
              @update:modelValue="updateEditingDraft"
            />
          </div>
          <div ref="sectionModalFooterRef" class="section-editor-footer flex flex-wrap items-center justify-end gap-2 border-t border-border px-6 py-4">
            <span v-if="usesV2Form && hasUnsavedSectionDraftChanges" class="section-editor-dirty"><i aria-hidden="true"></i>Alterações não salvas</span>
            <button
              class="h-10 rounded-full bg-muted px-5 text-sm font-semibold text-foreground hover:bg-accent"
              @click="requestCloseSectionEditor"
            >
              {{ usesV2Form ? "Descartar" : viewCopy.sectionDialog.cancel }}
            </button>
            <button
              class="h-10 rounded-full bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-brand-dark"
              @click="saveEditingSection"
            >
              {{ viewCopy.sectionDialog.save }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    <transition name="fade">
      <div
        v-if="snackbar.open"
        class="app-snackbar-layer z-50 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-2xl"
      >
        {{ snackbar.text }}
      </div>
    </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ActivityIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  BadgeDollarSignIcon,
  CheckIcon,
  ChevronLeftIcon,
  CircleQuestionMarkIcon,
  CopyIcon,
  EllipsisVerticalIcon,
  ExternalLinkIcon,
  GripVerticalIcon,
  ImageIcon,
  LinkIcon,
  ListIcon,
  MessageCircleIcon,
  MonitorIcon,
  PaletteIcon,
  EllipsisIcon,
  EyeIcon,
  EyeOffIcon,
  PanelLeftCloseIcon,
  PanelLeftOpenIcon,
  PanelRightCloseIcon,
  PanelRightOpenIcon,
  PanelsTopLeftIcon,
  PaperclipIcon,
  PencilIcon,
  PlaneIcon,
  PlusIcon,
  SendIcon,
  SmartphoneIcon,
  SparkleIcon,
  TimerIcon,
  Trash2Icon,
  UserIcon,
  UserPlusIcon,
  VideoIcon,
  XIcon
} from "lucide-vue-next";
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, provide, reactive, ref, shallowRef, watch } from "vue";
import type { Component } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import {
  previewAiAssistantPageBase,
  fetchAiAssistantHistory,
  fetchAiAssistantUsage,
  sendAiAssistantConversation,
  type AiAssistantChatMessage,
  type AiAssistantUsageResponse
} from "../../services/aiAssistant";
import { useAuthStore } from "../../store/useAuthStore";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useLeadCaptureStore } from "../../store/useLeadCaptureStore";
import type {
  BannerCardSection,
  BiographySection,
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
  VideoVslSection,
  TestimonialsSection,
  StorySection,
  ReasonsSection,
  LinksSection,
  CountdownSection,
  AgencyFooterSection,
  FlightDetailsSection,
  ViajeonCheckoutSection,
  InternalFormSection,
  HeaderSection,
  SectionType,
  ThemeConfig
} from "../../types/page";
import LeadFormPreview from "../../components/admin/leads/LeadFormPreview.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sectionsInjectionKey } from "../../components/admin/sectionsContext";
import { sectionUploadGuardKey } from "../../components/admin/sectionUploadGuard";
import { describeSection, sectionLabels as defaultSectionLabels } from "../../utils/sectionLabels";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { resolvePageDesign } from "../../utils/pageDesign";
import { sectionNameV2 } from "../../utils/sectionCatalogV2";
import { getLocalizedValue } from "../../utils/i18n";
import SectionPickerV2 from "../../components/admin/SectionPickerV2.vue";
import EdGroup from "../../components/admin/v2edit/EdGroup.vue";
import EdText from "../../components/admin/v2edit/EdText.vue";
import EdToggle from "../../components/admin/v2edit/EdToggle.vue";
import "../../components/admin/v2edit/v2edit.css";
import { pickSectionComponent } from "../../components/public/v2/registry";
import { DEFAULT_ACCENT, PAGE_DESIGN_KEY } from "../../components/public/v2/designContext";
import { getReadableTextColor } from "../../utils/colorContrast";
import { useLeadFeatureGate } from "../../composables/useLeadFeatureGate";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";
import heroThumb from "../../assets/hero-thumb.jpg";
import headerThumb from "../../assets/header-thumb.png";
import internalFormThumb from "../../assets/internal-form-thumb.png";
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
import videoVslThumb from "../../assets/video-vsl-thumb-optimized.jpg";
import biographyThumb from "../../assets/biografia.png";
import flightsThumb from "../../assets/voos-thumb.png";
import viajeonCheckoutThumb from "../../assets/viajeon-checkout-thumb.png";
import linksThumb from "../../assets/links-thumb.png";
interface Page {
  id: number;
  title: string;
  slug: string;
  status: string;
  config_json?: PageConfig | string | null;
  cover_image_url?: string;
  seo_title?: string | null;
  design_v2_enabled?: boolean;
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
  if (hasUnsavedSectionDraftChanges.value) {
    pendingNavigationPath.value = to.fullPath || null;
    requestLeaveWithUnsavedSectionDraft();
    next(false);
    return;
  }
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
const pageShortDescription = ref("");
const slugAutoSyncEnabled = ref(true);
const PAGE_SLUG_FALLBACK = "pagina";

const normalizeSlugInput = (value: string | undefined | null) => {
  const trimmed = (value || "").trim();
  if (!trimmed) return "";
  const normalized = trimmed
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return normalized || PAGE_SLUG_FALLBACK;
};

const normalizeHexColor = (value: string, fallback = "#000000") => {
  const cleaned = (value || "").trim().replace(/[^0-9a-fA-F]/g, "");
  const candidate = `#${cleaned}`.toUpperCase();
  return /^#[0-9A-F]{6}$/.test(candidate) ? candidate : fallback;
};

const handleSlugInput = (event: Event) => {
  slugAutoSyncEnabled.value = false;
  const target = event.target as HTMLInputElement;
  const normalized = normalizeSlugInput(target.value);
  pageSlug.value = normalized;
  target.value = normalized;
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
watch(pageShortDescription, () => markUnsavedChanges());

const auth = useAuthStore();
const agencyStore = useAgencyStore();
const leadCaptureStore = useLeadCaptureStore();
const publicSiteBaseUrl = (
  (import.meta.env.VITE_PUBLIC_SITE_URL as string | undefined)?.trim() || "https://roteiroonline.com"
).replace(/\/+$/, "");
const { hasLeadFeatureAccess } = useLeadFeatureGate();
const leadFeatureAllowed = hasLeadFeatureAccess;
const t = createAdminLocalizer();

const viewCopy = {
  header: {
    eyebrow: t({ pt: "Editor de página", es: "Editor de páginas" }),
    defaultTitle: t({ pt: "Roteiro", es: "Itinerario" }),
    subtitle: t({
      pt: "Monte a página por seções, salve e visualize ao lado.",
      es: "Arma la página por secciones, guarda y visualiza al lado."
    })
  },
  toolbar: {
    saveTemplate: t({ pt: "Salvar como template", es: "Guardar como plantilla" }),
    save: t({ pt: "Salvar", es: "Guardar" }),
    publish: t({ pt: "Publicar", es: "Publicar" }),
    published: t({ pt: "Publicada", es: "Publicada" }),
    unpublish: t({ pt: "Despublicar", es: "Despublicar" })
  },
  actions: {
    goBack: t({ pt: "Voltar", es: "Volver" }),
    viewPage: t({ pt: "Visualizar página", es: "Ver página" }),
    close: t({ pt: "Fechar", es: "Cerrar" }),
    viewPlans: t({ pt: "Ver planos", es: "Ver planes" })
  },
  limitModal: {
    eyebrow: t({ pt: "Limite do plano", es: "Límite del plan" }),
    title: t({ pt: "Ação indisponível", es: "Acción no disponible" }),
    description: t({
      pt: "Seu plano atual atingiu o limite. Atualize para continuar.",
      es: "Tu plan actual alcanzó el límite. Actualiza para continuar."
    }),
    templatePlan: t({
      pt: "Salvar template está disponível apenas a partir do plano Essencial. Atualize seu plano para liberar.",
      es: "Guardar plantillas está disponible solo a partir del plan Esencial. Actualiza tu plan para desbloquearlo."
    })
  },
  unsavedModal: {
    eyebrow: t({ pt: "Atenção", es: "Atención" }),
    title: t({ pt: "Alterações não salvas", es: "Cambios no guardados" }),
    description: t({
      pt: "Você tem mudanças não salvas nesta página. Deseja salvar antes de sair?",
      es: "Tienes cambios no guardados en esta página. ¿Quieres guardar antes de salir?"
    }),
    continueEditing: t({ pt: "Continuar editando", es: "Seguir editando" }),
    discardAndExit: t({ pt: "Descartar e sair", es: "Descartar y salir" }),
    saving: t({ pt: "Salvando...", es: "Guardando..." }),
    saveAndLeave: t({ pt: "Salvar e sair", es: "Guardar y salir" })
  },
  flightUnsavedModal: {
    title: t({ pt: "Há alterações de trecho não salvas", es: "Hay cambios de tramo sin guardar" }),
    description: t({
      pt: "Você alterou um trecho de voo, mas ainda não clicou em “Salvar trecho”. Deseja salvar a seção mesmo assim?",
      es: "Editaste un tramo de vuelo, pero aún no hiciste clic en “Guardar tramo”. ¿Deseas guardar la sección de todos modos?"
    }),
    confirm: t({ pt: "Salvar seção mesmo assim", es: "Guardar sección de todos modos" })
  },
  sectionUnsavedModal: {
    title: t({ pt: "Há alterações não salvas na seção", es: "Hay cambios sin guardar en la sección" }),
    description: t({
      pt: "Você fez alterações nesta seção e ainda não salvou. Deseja salvar antes de continuar?",
      es: "Hiciste cambios en esta sección y aún no guardaste. ¿Deseas guardar antes de continuar?"
    }),
    saveSection: t({ pt: "Salvar seção", es: "Guardar sección" })
  },
  successModal: {
    eyebrow: t({ pt: "Publicação", es: "Publicación" }),
    title: t({ pt: "Página publicada com sucesso", es: "Página publicada con éxito" }),
    description: t({
      pt: "Escolha o que deseja fazer em seguida.",
      es: "Elige qué hacer a continuación."
    }),
    viewPages: t({ pt: "Voltar para páginas", es: "Volver a páginas" })
  },
  form: {
    titleLabel: t({ pt: "Título", es: "Título" }),
    slugLabel: t({ pt: "Slug", es: "Slug" }),
    slugHint: t({
      pt: "Slug é a parte do link depois da barra, sem espaços ou acentos. Ex.: meu-roteiro-incrivel.",
      es: "Slug es la parte del enlace después de la barra, sin espacios ni acentos. Ej.: mi-itinerario-increible."
    }),
    backgroundLabel: t({ pt: "Cores de fundo", es: "Colores de fondo" }),
    backgroundHint: t({
      pt: "Aplica alternância em todas as seções (exceto hero).",
      es: "Aplica alternancia en todas las secciones (excepto hero)."
    }),
    colorA: t({ pt: "Cor 1", es: "Color 1" }),
    colorB: t({ pt: "Cor 2", es: "Color 2" }),
    legacyDesignLabel: t({ pt: "Usar visual antigo", es: "Usar diseño anterior" }),
    legacyDesignHint: t({
      pt: "As seções da página voltam ao visual anterior. O conteúdo não muda e dá para desligar quando quiser.",
      es: "Las secciones vuelven al diseño anterior. El contenido no cambia y puedes desactivarlo cuando quieras."
    }),
    ctaColorLabel: t({ pt: "Cor de botões e destaques", es: "Color de botones y destacados" }),
    ctaColorHint: t({
      pt: "Afeta CTAs, chips e elementos em destaque.",
      es: "Afecta CTAs, chips y elementos destacados."
    })
  },
  pixels: {
    title: t({ pt: "Pixel de rastreamento", es: "Pixel de seguimiento" }),
    helper: t({
      pt: "Escolha um pixel cadastrado em Integrações e quais eventos deseja enviar.",
      es: "Elige un pixel registrado en Integraciones y qué eventos deseas enviar."
    }),
    planHint: t({ pt: "Disponível a partir do plano Essencial.", es: "Disponible a partir del plan Esencial." }),
    lockedHint: t({
      pt: "Adicione pixels na página Integrações.",
      es: "Agrega píxeles en la página Integraciones (plan Esencial o superior)."
    }),
    metaLabel: t({ pt: "Pixel Meta", es: "Pixel Meta" }),
    metaPlaceholder: t({ pt: "Sem pixel Meta", es: "Sin pixel Meta" }),
    metaEmptyHint: t({
      pt: "Cadastre uma conexão Meta em Integrações.",
      es: "Registra una conexión Meta en Integraciones."
    }),
    googleLabel: t({ pt: "Pixel Google", es: "Pixel Google" }),
    googlePlaceholder: t({ pt: "Sem pixel Google", es: "Sin pixel Google" }),
    googleEmptyHint: t({
      pt: "Cadastre uma conexão GA4 em Integrações.",
      es: "Registra una conexión GA4 en Integraciones."
    }),
    eventsTitle: t({ pt: "Eventos a enviar", es: "Eventos a enviar" }),
    eventPageView: t({ pt: "Page view (carregamento da página)", es: "Page view (carga de la página)" }),
    eventCtaClicks: t({ pt: "Cliques em CTAs", es: "Clics en CTAs" }),
    eventLeads: t({ pt: "Leads (envios de formulários)", es: "Leads (envíos de formularios)" })
  },
  validation: {
    slugRequired: t({ pt: "Defina um slug válido para a página.", es: "Define un slug válido para la página." })
  },
  leadSection: {
    badge: t({ pt: "Captação de leads", es: "Captación de leads" }),
    title: t({ pt: "Formulário", es: "Formulario" }),
    description: t({
      pt: "Escolha um formulário de captação para abrir antes do visitante acessar a página.",
      es: "Elige un formulario de captación para abrir antes de que el visitante acceda a la página."
    }),
    manageButton: t({ pt: "Gerenciar formulários", es: "Gestionar formularios" }),
    loading: t({ pt: "Carregando formulários cadastrados...", es: "Cargando formularios registrados..." }),
    empty: t({ pt: "Nenhum formulário disponível. Clique em", es: "No hay formularios disponibles. Haz clic en" }),
    emptyAction: t({ pt: "“Gerenciar formulários” para criar.", es: "“Gestionar formularios” para crear uno." }),
    selectLabel: t({ pt: "Escolha um formulário", es: "Elige un formulario" }),
    selectPlaceholder: t({ pt: "Nenhum formulário selecionado", es: "Ningún formulario seleccionado" }),
    selectHint: t({
      pt: "Selecione o formulário e clique em “Ver prévia” para abrir o modal real.",
      es: "Selecciona el formulario y haz clic en “Ver previa” para abrir el modal real."
    }),
    previewButton: t({ pt: "Ver prévia", es: "Ver previa" }),
    optionalToggle: t({ pt: "Permitir fechar sem enviar", es: "Permitir cerrar sin enviar" }),
    optionalActive: t({ pt: "Formulário opcional ativo para esta página.", es: "Formulario opcional activo para esta página." }),
    requiredActive: t({ pt: "Formulário obrigatório ativo para esta página.", es: "Formulario obligatorio activo para esta página." }),
    blockedTitle: t({ pt: "Captação de leads bloqueada", es: "Captación de leads bloqueada" }),
    blockedDescription: t({
      pt: "Este recurso está disponível apenas nos planos Agência e Escala. Atualize seu plano para ativar o formulário obrigatório de leads.",
      es: "Este recurso está disponible solo en los planes Agencia y Escala. Actualiza tu plan para activar el formulario obligatorio de leads."
    })
  },
  preview: {
    title: t({ pt: "Prévia ao vivo", es: "Vista previa en vivo" }),
    helper: t({
      pt: "Clique no botão do topo para aplicar as alterações do formulário.",
      es: "Haz clic en el botón superior para aplicar los cambios del formulario."
    }),
    mobileHint: t({ pt: "Toque sobre as seções para editar.", es: "Toca las secciones para editarlas." }),
    desktopLabel: t({ pt: "Computador", es: "Computadora" }),
    mobileLabel: t({ pt: "Celular", es: "Celular" }),
    emptyState: t({
      pt: "Nenhuma seção adicionada ainda. Use o botão abaixo para criar o conteúdo.",
      es: "Aún no hay secciones añadidas. Usa el botón de abajo para crear el contenido."
    }),
    emptyAction: t({ pt: "Adicionar primeira seção", es: "Agregar primera sección" })
  },
  overlay: {
    edit: t({ pt: "Editar seção", es: "Editar sección" }),
    moveUp: t({ pt: "Subir", es: "Subir" }),
    moveDown: t({ pt: "Descer", es: "Bajar" }),
    duplicate: t({ pt: "Duplicar", es: "Duplicar" }),
    delete: t({ pt: "Excluir", es: "Eliminar" }),
    footerLocked: t({
      pt: "Rodapé obrigatório no plano gratuito. Não é possível editar, mover ou remover esta seção.",
      es: "El pie de página es obligatorio en el plan gratuito. No es posible editar, mover ni eliminar esta sección."
    }),
    disabledSection: t({
      pt: "Seção desativada. Clique em editar para ajustar e ativar novamente.",
      es: "Sección desactivada. Haz clic en editar para ajustarla y activarla nuevamente."
    }),
    addBelow: t({ pt: "Adicionar seção abaixo", es: "Agregar sección abajo" })
  },
  sectionDialog: {
    eyebrow: t({ pt: "Editar seção", es: "Editar sección" }),
    cancel: t({ pt: "Cancelar", es: "Cancelar" }),
    save: t({ pt: "Salvar seção", es: "Guardar sección" })
  },
  feedback: {
    loginAgain: t({ pt: "Faça login novamente para editar.", es: "Vuelve a iniciar sesión para editar." }),
    sessionExpired: t({ pt: "Sessão expirada. Faça login novamente.", es: "Sesión expirada. Inicia sesión nuevamente." }),
    pageLoadError: t({ pt: "Não foi possível carregar a página.", es: "No fue posible cargar la página." }),
    configSaved: t({ pt: "Configuração salva!", es: "¡Configuración guardada!" }),
    configSavedToast: t({ pt: "Configuração salva", es: "Configuración guardada" }),
    configSaveError: t({ pt: "Erro ao salvar configuração.", es: "Error al guardar la configuración." }),
    publishSuccess: t({ pt: "Página publicada!", es: "¡Página publicada!" }),
    publishError: t({
      pt: "Erro ao publicar. Verifique se está logado e tem acesso à agência.",
      es: "Error al publicar. Verifica si estás logueado y tienes acceso a la agencia."
    }),
    unpublishSuccess: t({ pt: "Página despublicada.", es: "Página despublicada." }),
    unpublishError: t({ pt: "Erro ao despublicar. Tente novamente.", es: "Error al despublicar. Intenta nuevamente." }),
    imageUploading: t({
      pt: "A imagem ainda está sendo enviada. Aguarde antes de salvar.",
      es: "La imagen aún se está enviando. Espera antes de guardar."
    }),
    templateLoginRequired: t({ pt: "Faça login para salvar um template.", es: "Inicia sesión para guardar una plantilla." }),
    templateUnavailable: t({ pt: "Recurso indisponível no momento.", es: "Recurso no disponible en este momento." }),
    templateSaved: t({
      pt: "Template salvo! Novas páginas iniciarão com essa estrutura.",
      es: "¡Plantilla guardada! Las nuevas páginas iniciarán con esta estructura."
    }),
    templateSavedToast: t({ pt: "Template salvo com sucesso", es: "Plantilla guardada con éxito" }),
    templateSaveError: t({ pt: "Não foi possível salvar o template.", es: "No fue posible guardar la plantilla." })
  }
};

const message = ref("");
const errorMessage = ref("");

const ensureValidPageSlug = () => {
  const normalized = normalizeSlugInput(pageSlug.value);
  if (!normalized) {
    const slugError = viewCopy.validation.slugRequired;
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
const showAiAssistant = ref(false);
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
    design: useLegacyDesign.value ? "legacy" : "default",
    sections: sections.value,
    leadCapture: selectedLeadFormId.value ? { formId: selectedLeadFormId.value, optional: leadCaptureOptional.value } : null,
    tracking: {
      meta: selectedPixels.meta,
      ga: selectedPixels.ga,
      events: { ...trackingEvents.value }
    }
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
const canUseAiAssistant = computed(() => !!auth.user);
const activeSettingsTab = ref<"content" | "general" | "colors" | "pixels" | "capture">("content");
const topbarMenuOpen = ref(false);
const settingsSidebarRef = ref<HTMLElement | null>(null);
const settingsPanelRef = ref<HTMLElement | null>(null);
const generalSettingsRef = ref<HTMLElement | null>(null);
const settingsPanelHeight = ref<number | null>(null);
const settingsPanelStyle = computed(() =>
  settingsPanelHeight.value ? { height: `${settingsPanelHeight.value}px` } : {}
);

const syncSettingsPanelHeight = () => {
  // Com as abas na horizontal, a altura fixa do painel vem do conteúdo de "Título e link".
  const generalHeight = generalSettingsRef.value?.offsetHeight || 0;
  const nextHeight = generalHeight ? Math.max(generalHeight + 40, 220) : 0;
  if (nextHeight > 0) settingsPanelHeight.value = nextHeight;
};

const selectSettingsTab = (tab: "content" | "general" | "colors" | "pixels" | "capture") => {
  activeSettingsTab.value = tab;
  if (tab === "general") {
    nextTick(syncSettingsPanelHeight);
  }
};

onMounted(() => {
  if (hasWindow) {
    const storedWidth = Number(window.localStorage.getItem(aiAssistantSidebarStorageKey));
    if (Number.isFinite(storedWidth) && storedWidth > 0) {
      aiAssistantSidebarWidth.value = storedWidth;
    }
    syncAiAssistantSidebarWidth();
  }
  nextTick(syncSettingsPanelHeight);
  if (typeof window !== "undefined") {
    window.addEventListener("resize", syncSettingsPanelHeight);
    window.addEventListener("resize", syncAiAssistantSidebarWidth);
  }
  void refreshAiAssistantUsage();
});

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", syncSettingsPanelHeight);
    window.removeEventListener("resize", syncAiAssistantSidebarWidth);
  }
  removeAiAssistantSidebarResizeListeners?.();
  removeAiAssistantSidebarResizeListeners = null;
});

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

const useLegacyDesign = ref(false);
const designV2Enabled = computed(() => Boolean(page.value?.design_v2_enabled));
const previewDesign = computed(() =>
  resolvePageDesign(designV2Enabled.value, { design: useLegacyDesign.value ? "legacy" : undefined })
);
const colorA = ref(theme.value.color1);
const colorB = ref(theme.value.color2);
const ctaColor = ref(theme.value.ctaDefaultColor || fallbackPrimaryColor);
const previewDevice = ref<"desktop" | "mobile">(editorPrefs.value.previewDevice || "desktop");
const isMobileViewport = ref(false);
const isMobileOverlayMode = computed(() => isMobileViewport.value);
// Editor novo (painel à esquerda, camadas à direita): por enquanto só para quem já tem o visual novo.
const newEditor = computed(() => designV2Enabled.value && !isMobileViewport.value);
const EDITOR_PANELS_KEY = "editor_v2_panels";
const readPanelPrefs = () => {
  try {
    return JSON.parse(window.localStorage.getItem(EDITOR_PANELS_KEY) || "{}") as { left?: boolean; layers?: boolean };
  } catch {
    return {};
  }
};
const panelPrefs = typeof window !== "undefined" ? readPanelPrefs() : {};
// Em telas menores a prévia precisa do espaço: o painel começa recolhido, só com os ícones.
const leftPanelOpen = ref(panelPrefs.left ?? (typeof window === "undefined" || window.innerWidth >= 1600));
const layersOpen = ref(panelPrefs.layers ?? true);
watch([leftPanelOpen, layersOpen], ([left, layers]) => {
  try {
    window.localStorage.setItem(EDITOR_PANELS_KEY, JSON.stringify({ left, layers }));
  } catch {
    /* sem armazenamento local: os painéis só não ficam lembrados */
  }
});
type RailTab = "general" | "colors" | "pixels" | "capture";
const railTabs: { id: RailTab; label: string; icon: Component }[] = [
  { id: "general", label: "Título e link", icon: PencilIcon },
  { id: "colors", label: "Cores", icon: PaletteIcon },
  { id: "pixels", label: "Rastreamento", icon: ActivityIcon },
  { id: "capture", label: "Captação de leads", icon: UserPlusIcon }
];
const openRailTab = (tab: RailTab) => {
  if (sectionPanelOpen.value) {
    requestCloseSectionEditor();
    leftPanelOpen.value = true;
    selectSettingsTab(tab);
    return;
  }
  if (leftPanelOpen.value && activeSettingsTab.value === tab) {
    leftPanelOpen.value = false;
    return;
  }
  leftPanelOpen.value = true;
  selectSettingsTab(tab);
};
watch(
  newEditor,
  enabled => {
    if (enabled && activeSettingsTab.value === "content") selectSettingsTab("general");
  },
  { immediate: true }
);
// No computador, a prévia é desenhada em 1280 px e reduzida para caber, sem espremer as seções.
const DESKTOP_PREVIEW_WIDTH = 1280;
// O editor novo simula uma tela de até 1440 px, mostrando as margens laterais da página.
// Com pouco espaço (os dois painéis abertos), simula uma tela menor, de até 1100 px,
// para a prévia não ficar pequena demais; abaixo disso só o zoom diminui.
const desktopPreviewWidth = computed(() => {
  if (!newEditor.value) return DESKTOP_PREVIEW_WIDTH;
  if (!previewCanvasWidth.value) return 1440;
  return Math.min(1440, Math.max(1100, Math.round(previewCanvasWidth.value / 0.62)));
});
const previewCanvasRef = ref<HTMLElement | null>(null);
const previewCanvasWidth = ref(0);
let previewCanvasObserver: ResizeObserver | null = null;
const desktopPreviewZoom = computed(() => {
  if (previewDevice.value !== "desktop" || isMobileViewport.value || !previewCanvasWidth.value) return 1;
  return Math.min(1, previewCanvasWidth.value / desktopPreviewWidth.value);
});
const desktopPreviewStyle = computed(() =>
  desktopPreviewZoom.value < 1
    ? { width: `${desktopPreviewWidth.value}px`, zoom: String(desktopPreviewZoom.value), "--ed-unzoom": String(1 / desktopPreviewZoom.value) }
    : {}
);
watch(previewCanvasRef, (el, prev) => {
  if (typeof ResizeObserver === "undefined") return;
  previewCanvasObserver ??= new ResizeObserver(entries => {
    previewCanvasWidth.value = Math.floor(entries[0]?.contentRect.width || 0);
  });
  if (prev) previewCanvasObserver.unobserve(prev);
  if (el) previewCanvasObserver.observe(el);
}, { flush: "post" });
onBeforeUnmount(() => previewCanvasObserver?.disconnect());
const desktopHoverEnabled = computed(() => previewDevice.value === "desktop" && !isMobileViewport.value);
const hasWindow = typeof window !== "undefined";
const beforeUnloadHandler = (event: BeforeUnloadEvent) => {
  if (!hasUnsavedChanges.value && !hasUnsavedSectionDraftChanges.value) return;
  event.preventDefault();
  event.returnValue = "";
};
  const toolbarSecondaryButtonClass =
    "inline-flex h-10 items-center gap-2 rounded-full border border-border bg-card px-4 text-sm font-semibold text-foreground transition-colors hover:bg-accent";
  const floatingAiButtonClass =
    "editor-ai-fab hidden md:inline-flex cursor-pointer items-center justify-center rounded-l-2xl border border-primary bg-primary text-sm font-semibold text-white transition hover:bg-brand-dark";
  const floatingAiButtonStyle = {
    position: "fixed",
    top: "50%",
    right: "5px",
    zIndex: "9999",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "0",
    transform: "translateY(-50%)",
    transformOrigin: "center center",
    borderRadius: "16px",
    boxShadow: "0 14px 32px rgba(15, 23, 42, 0.18)",
    width: "52px",
    minHeight: "156px",
    padding: "10px 4px",
    whiteSpace: "nowrap"
  } as const;
  const floatingAiButtonContentStyle = {
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "center",
        gap: "8px",
        transform: "rotate(90deg)",
        transformOrigin: "center center",
        padding: "6px 14px",
        whiteSpace: "nowrap"
      } as const;
  const floatingAiButtonLabelStyle = {
      color: "#ffffff",
      letterSpacing: "0.12em"
    } as const;
  const toolbarPrimaryButtonClass =
    "inline-flex h-10 items-center gap-2 rounded-full border border-primary bg-primary px-5 text-sm font-semibold text-primary-foreground transition hover:bg-brand-dark";
const toolbarWarningButtonClass =
  "inline-flex h-10 items-center gap-2 rounded-full border border-transparent bg-status-danger px-4 text-sm font-semibold text-status-danger-foreground transition hover:brightness-95";
const toolbarStatusPillClass =
  "inline-flex h-10 items-center gap-2 rounded-full border border-transparent bg-status-success px-4 text-sm font-semibold text-status-success-foreground";
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

const aiAssistantUrl = "https://chatgpt.com/g/g-6a0f578cbca48191b3073e3aa3556c5d-construtor-roteiro-online";
const aiAssistantMessages = ref<Array<{ role: "user" | "assistant"; content: string }>>([]);
const aiAssistantVisibleMessages = computed(() =>
  aiAssistantMessages.value.filter(message => message.role === "user" || message.content.trim().length > 0)
);
const aiStructureApplying = ref(false);
const aiStructureError = ref("");
const aiStructurePreviousSections = shallowRef<PageSection[] | null>(null);
const hasAiStructure = (content: string) => /^\s*(?:🟩\s*)?(?:SECAO|SEÇÃO)\s*:\s*.+$/im.test(content);
// Editor novo: a resposta com estrutura vira uma lista de seções, com o texto completo sob demanda.
const AI_SECTION_LINE = /^\s*(?:🟩\s*)?(?:SECAO|SEÇÃO)\s*:\s*(.+)$/gim;
const aiStructureNames = (content: string) =>
  [...content.matchAll(AI_SECTION_LINE)].map(match => match[1].replace(/[*_`#]/g, "").trim()).filter(Boolean);
const aiIntroText = (content: string) => {
  const first = content.search(/^\s*(?:🟩\s*)?(?:SECAO|SEÇÃO)\s*:/im);
  return (first > 0 ? content.slice(0, first) : "").trim();
};
const aiExpanded = reactive(new Set<number>());
const aiDetails = reactive(new Set<number>());
const toggleAiExpanded = (index: number) => (aiExpanded.has(index) ? aiExpanded.delete(index) : aiExpanded.add(index));
const toggleAiDetails = (index: number) => (aiDetails.has(index) ? aiDetails.delete(index) : aiDetails.add(index));
const applyAiStructure = async (reply: string, mode: "insert" | "replace") => {
  if (aiStructureApplying.value || aiAssistantLoading.value || isSectionEditorOpen.value) return;
  aiStructureApplying.value = true;
  aiStructureError.value = "";
  try {
    const generated = await previewAiAssistantPageBase(pageId, reply);
    if (isSectionEditorOpen.value) {
      aiStructureError.value = "Feche a edição da seção e tente inserir ou substituir a estrutura novamente.";
      return;
    }
    flushPendingSectionUpdates();
    const agencyLogo = currentAgency.value?.logo_url;
    const additions = applySectionBackgrounds(generated.map(section =>
      section.type === "hero" && !section.logoUrl && agencyLogo
        ? { ...section, logoUrl: agencyLogo }
        : section
    ));
    let nextSections = additions;
    if (mode === "insert") {
      const existing = sections.value;
      const usedIds = new Set(existing.flatMap(section => [section.anchorId, (section as any).sectionId]).filter(Boolean));
      const renamedIds = new Map<string, string>();
      for (const section of additions) {
        for (const key of ["anchorId", "sectionId"] as const) {
          const oldId = (section as any)[key] as string | undefined;
          if (!oldId) continue;
          let newId = oldId;
          let suffix = 2;
          while (usedIds.has(newId)) newId = `${oldId}-${suffix++}`;
          usedIds.add(newId);
          renamedIds.set(oldId, newId);
          (section as any)[key] = newId;
        }
      }
      for (const section of additions) {
        const remapTarget = (item: any) => {
          if (item.ctaSectionId && renamedIds.has(item.ctaSectionId)) {
            item.ctaSectionId = renamedIds.get(item.ctaSectionId);
          }
        };
        remapTarget(section);
        if ("items" in section) section.items.forEach(remapTarget);
      }
      // The mandatory plan footer is returned by the backend as well.
      // Keep a single copy at the bottom when appending content.
      const content = existing.filter(section => section.type !== "free_footer_brand");
      const footer = existing.filter(section => section.type === "free_footer_brand");
      nextSections = [
        ...content,
        ...additions.filter(section => section.type !== "free_footer_brand"),
        ...(footer.length ? footer : additions.filter(section => section.type === "free_footer_brand"))
      ];
    }
    aiStructurePreviousSections.value = JSON.parse(JSON.stringify(sections.value));
    setSections(nextSections);
    refreshPreview(true);
    showSnackbar(mode === "insert"
      ? "Seções adicionadas ao final. Revise e salve quando terminar."
      : "Estrutura substituída. Revise e salve quando terminar.");
  } catch (err: any) {
    const detail = err?.response?.data?.detail;
    aiStructureError.value = typeof detail === "string" ? detail : "Não foi possível aplicar a estrutura. Tente novamente.";
  } finally {
    aiStructureApplying.value = false;
  }
};
const undoAiStructure = () => {
  if (!aiStructurePreviousSections.value || aiStructureApplying.value || isSectionEditorOpen.value) return;
  flushPendingSectionUpdates();
  setSections(aiStructurePreviousSections.value);
  refreshPreview(true);
  aiStructurePreviousSections.value = null;
  aiStructureError.value = "";
  showSnackbar("Seções anteriores restauradas no editor.");
};
const aiAssistantLoading = ref(false);
const aiAssistantChatLogRef = ref<HTMLElement | null>(null);
const aiAssistantFileInputRef = ref<HTMLInputElement | null>(null);
const aiAssistantDraft = ref("");
const aiAssistantAttachments = ref<File[]>([]);
const aiAssistantUsage = ref<AiAssistantUsageResponse | null>(null);
const aiAssistantHistoryLoaded = ref(false);
const aiAssistantSidebarWidth = ref(464);
const aiAssistantSidebarMinWidth = 320;
const aiAssistantSidebarMaxWidth = 720;
const aiAssistantSidebarStorageKey = "page-editor-ai-assistant-sidebar-width";
const aiAssistantSidebarResizeState = reactive({
  active: false,
  startX: 0,
  startWidth: 0
});
let removeAiAssistantSidebarResizeListeners: (() => void) | null = null;
let aiAssistantLoadingTimer: number | null = null;
let aiAssistantTypingTimer: number | null = null;
const aiAssistantPromptTemplate = `👋 Bem-vindo(a) ao Assistente de Construção de Páginas da Roteiro Online!

Sou um assistente que ajuda a planejar o conteúdo da sua página de viagem.

Você pode me enviar as informações da viagem em texto, PDF, prints, fotos ou até mesmo informações soltas. Com base nelas, vou sugerir uma página organizada e pronta para utilizar no Construtor Roteiro Online.`;
const scrollAiAssistantToEnd = () => {
  nextTick(() => {
    aiAssistantChatLogRef.value?.scrollTo({ top: aiAssistantChatLogRef.value.scrollHeight, behavior: "smooth" });
  });
};
const refreshAiAssistantUsage = async () => {
  if (!canUseAiAssistant.value) return;
  try {
    aiAssistantUsage.value = await fetchAiAssistantUsage();
  } catch (error) {
    console.error("Erro ao carregar uso da ajuda IA", error);
  }
};
const loadAiAssistantHistory = async () => {
  if (!canUseAiAssistant.value || !Number.isFinite(pageId) || pageId <= 0) return;
  try {
    const history = await fetchAiAssistantHistory(pageId);
    aiAssistantMessages.value = history.map(item => ({
      role: item.role,
      content: item.content
    }));
  } catch (error) {
    console.error("Erro ao carregar o histórico do assistente IA", error);
  } finally {
    aiAssistantHistoryLoaded.value = true;
    if (showAiAssistant.value && aiAssistantMessages.value.length === 0) {
      prefillAiAssistantPrompt();
    }
    scrollAiAssistantToEnd();
  }
};
const stopAiAssistantTimers = () => {
  if (aiAssistantLoadingTimer !== null) {
    window.clearTimeout(aiAssistantLoadingTimer);
    aiAssistantLoadingTimer = null;
  }

  if (aiAssistantTypingTimer !== null) {
    window.clearInterval(aiAssistantTypingTimer);
    aiAssistantTypingTimer = null;
  }
};
const getAiAssistantSidebarWidthBounds = () => {
  const viewportWidth = hasWindow ? window.innerWidth : aiAssistantSidebarMaxWidth;
  const maxWidth = Math.max(aiAssistantSidebarMinWidth, Math.min(aiAssistantSidebarMaxWidth, viewportWidth - 96));
  return {
    minWidth: aiAssistantSidebarMinWidth,
    maxWidth
  };
};
const clampAiAssistantSidebarWidth = (value: number) => {
  const bounds = getAiAssistantSidebarWidthBounds();
  return Math.max(bounds.minWidth, Math.min(bounds.maxWidth, Math.round(value)));
};
const applyAiAssistantSidebarWidth = (value: number) => {
  const nextWidth = clampAiAssistantSidebarWidth(value);
  aiAssistantSidebarWidth.value = nextWidth;
  if (hasWindow) {
    window.localStorage.setItem(aiAssistantSidebarStorageKey, String(nextWidth));
  }
};
const syncAiAssistantSidebarWidth = () => {
  aiAssistantSidebarWidth.value = clampAiAssistantSidebarWidth(aiAssistantSidebarWidth.value);
};
const startAiAssistantSidebarResize = (event: PointerEvent) => {
  if (event.button !== 0) return;
  event.preventDefault();
  removeAiAssistantSidebarResizeListeners?.();
  aiAssistantSidebarResizeState.active = true;
  aiAssistantSidebarResizeState.startX = event.clientX;
  aiAssistantSidebarResizeState.startWidth = aiAssistantSidebarWidth.value;
  document.body.style.cursor = "col-resize";
  document.body.style.userSelect = "none";

  const onMove = (moveEvent: PointerEvent) => {
    if (!aiAssistantSidebarResizeState.active) return;
    const delta = aiAssistantSidebarResizeState.startX - moveEvent.clientX;
    applyAiAssistantSidebarWidth(aiAssistantSidebarResizeState.startWidth + delta);
  };

  const stopResize = () => {
    if (!aiAssistantSidebarResizeState.active) return;
    aiAssistantSidebarResizeState.active = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    removeAiAssistantSidebarResizeListeners?.();
    removeAiAssistantSidebarResizeListeners = null;
  };

  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", stopResize);
  window.addEventListener("pointercancel", stopResize);
  removeAiAssistantSidebarResizeListeners = () => {
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", stopResize);
    window.removeEventListener("pointercancel", stopResize);
  };
};
const animateAiAssistantMessage = (messageIndex: number, fullText: string) => {
  return new Promise<void>(resolve => {
  if (!fullText) {
    aiAssistantMessages.value[messageIndex].content = "";
    aiAssistantLoading.value = false;
      resolve();
      return;
  }

  let index = 0;
  aiAssistantMessages.value[messageIndex].content = "";
  scrollAiAssistantToEnd();

  aiAssistantTypingTimer = window.setInterval(() => {
    index += 1;
    aiAssistantMessages.value[messageIndex].content = fullText.slice(0, index);
    scrollAiAssistantToEnd();

    if (index >= fullText.length && aiAssistantTypingTimer !== null) {
      window.clearInterval(aiAssistantTypingTimer);
      aiAssistantTypingTimer = null;
      aiAssistantLoading.value = false;
      scrollAiAssistantToEnd();
      resolve();
    }
    }, 6);
    });
  };
const startAiAssistantReply = () => {
  stopAiAssistantTimers();
  aiAssistantLoading.value = true;
  aiAssistantMessages.value = [
    ...aiAssistantMessages.value,
    { role: "assistant", content: "" }
  ];
  const assistantIndex = aiAssistantMessages.value.length - 1;

  scrollAiAssistantToEnd();

  aiAssistantLoadingTimer = window.setTimeout(() => {
    void animateAiAssistantMessage(assistantIndex, aiAssistantPromptTemplate);

    aiAssistantLoadingTimer = null;
  }, 600);
};
const prefillAiAssistantPrompt = () => {
  if (aiAssistantMessages.value.length > 0) return;
  aiAssistantMessages.value = [
    ...aiAssistantMessages.value,
    { role: "assistant", content: aiAssistantPromptTemplate }
  ];
  scrollAiAssistantToEnd();
};
const aiAssistantUsageLabel = computed(() => {
  if (!canUseAiAssistant.value) return "";
  const usage = aiAssistantUsage.value;
  if (!usage) return "-/- restantes";
  if (usage.unlimited) return "∞/∞ restantes";
  const limit = usage.limit ?? 0;
  const remaining = usage.remaining ?? 0;
  return `${remaining}/${limit} restantes`;
});
const aiAssistantUsageText = computed(() => {
  const usage = aiAssistantUsage.value;
  if (!usage) return "";
  if (usage.unlimited) return "Mensagens ilimitadas";
  return `${usage.used ?? 0} de ${usage.limit ?? 0} mensagens no mês`;
});
// Sugestões prontas na primeira conversa (editor novo).
const aiSuggestions = computed(() => {
  const hero = sections.value.find(section => section.type === "hero") as HeroSection | undefined;
  const heroTitle = hero ? getLocalizedValue(hero.title) : "";
  const heroText = hero ? getLocalizedValue(hero.subtitle).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim() : "";
  const pageName = (pageTitle.value || page.value?.title || "").trim();
  return [
    { label: "Montar estrutura da página", text: "Monte a estrutura completa desta página com as informações da viagem que vou enviar (texto, PDF ou prints).", send: false },
    {
      label: "Melhorar texto da capa",
      text: `Melhore o título e o texto da capa, mantendo as informações.\nTítulo atual: ${heroTitle || "(vazio)"}\nTexto atual: ${heroText || "(vazio)"}`,
      send: true
    },
    { label: "Criar perguntas frequentes", text: `Crie uma seção de perguntas frequentes para a página "${pageName || "desta viagem"}".`, send: true }
  ];
});
const useAiSuggestion = (suggestion: { text: string; send: boolean }) => {
  aiAssistantDraft.value = suggestion.text;
  if (suggestion.send) sendAiAssistantMessage();
};
const aiAssistantSidebarStyle = computed(() => ({
  width: `${aiAssistantSidebarWidth.value}px`,
  maxWidth: "calc(100vw - 48px)"
}));
const aiAssistantLimitReached = computed(() => {
  const usage = aiAssistantUsage.value;
  return Boolean(usage && !usage.unlimited && typeof usage.limit === "number" && usage.used >= usage.limit);
});
const formatAiAssistantRenewalDate = (value?: string | null) => {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleDateString("pt-BR");
};
const aiAssistantSendButtonLabel = computed(() => {
  if (!aiAssistantLimitReached.value) return "Enviar";
  const renewal = formatAiAssistantRenewalDate(aiAssistantUsage.value?.renewal_at);
  return renewal
    ? `Limite de solicitações mensais atingido. Renova em ${renewal}`
    : "Limite de solicitações mensais atingido";
});
const openAiAssistantFilePicker = () => {
  aiAssistantFileInputRef.value?.click();
};
const handleAiAssistantFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement | null;
  aiAssistantAttachments.value = input?.files ? Array.from(input.files) : [];
};
const sendAiAssistantMessage = async () => {
  const trimmedMessage = aiAssistantDraft.value.trim();
  if (!trimmedMessage && aiAssistantAttachments.value.length === 0) {
    return;
  }

  stopAiAssistantTimers();

  const attachmentsSnapshot = [...aiAssistantAttachments.value];
  const conversationSnapshot: AiAssistantChatMessage[] = [
    ...aiAssistantMessages.value.map(message => ({
      role: message.role,
      content: message.content
    })),
    {
      role: "user",
      content: trimmedMessage || "Mensagem com arquivos"
    }
  ];

  aiAssistantMessages.value = [
    ...aiAssistantMessages.value,
    {
      role: "user",
      content: trimmedMessage || "Mensagem com arquivos"
    },
    { role: "assistant", content: "" }
  ];
  const assistantIndex = aiAssistantMessages.value.length - 1;
  aiAssistantDraft.value = "";
  aiAssistantAttachments.value = [];
  if (aiAssistantFileInputRef.value) {
    aiAssistantFileInputRef.value.value = "";
  }

  aiAssistantLoading.value = true;
  scrollAiAssistantToEnd();

  try {
    const result = await sendAiAssistantConversation(pageId, conversationSnapshot, attachmentsSnapshot);
    if (result.usage) {
      aiAssistantUsage.value = result.usage;
    }
    await animateAiAssistantMessage(assistantIndex, result.reply);
  } catch (error) {
    console.error("Erro ao consultar a ajuda IA", error);
    const status = (error as any)?.response?.status;
    const detail = (error as any)?.response?.data?.detail;
    let errorText = "Não consegui consultar a IA agora. Tente novamente em alguns instantes.";
    if (status === 503 && detail === "GPT_KEY não configurada no backend.") {
      errorText = "A IA não está configurada neste ambiente. Configure GPT_KEY no backend e reinicie o serviço para usar o assistente.";
    } else if (status === 503 && detail === "Dependência openai não instalada.") {
      errorText = "O serviço de IA está sem uma dependência necessária. Instale as dependências do backend e reinicie o serviço.";
    } else if (status === 401) {
      errorText = "Sua sessão expirou. Entre novamente para consultar a IA.";
    } else if ([403, 429].includes(status) && typeof detail === "string") {
      errorText = detail;
    }
    aiAssistantMessages.value[assistantIndex].content = errorText;
  } finally {
    aiAssistantLoading.value = false;
    scrollAiAssistantToEnd();
  }
};
const toggleAiAssistant = () => {
  if (!canUseAiAssistant.value) return;
  showAiAssistant.value = !showAiAssistant.value;
};

watch(showAiAssistant, isOpen => {
  if (isOpen && aiAssistantHistoryLoaded.value && aiAssistantMessages.value.length === 0) {
    prefillAiAssistantPrompt();
  }
  if (isOpen) {
    void refreshAiAssistantUsage();
  }
});

const buildCountdownTargetDate = () => {
  const date = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  return date.toISOString().slice(0, 16);
};

const SectionHeroForm = defineAsyncComponent(() => import("../../components/admin/SectionHeroForm.vue"));
const SectionBannerCardForm = defineAsyncComponent(() => import("../../components/admin/SectionBannerCardForm.vue"));
const SectionPricesForm = defineAsyncComponent(() => import("../../components/admin/SectionPricesForm.vue"));
const SectionPhotoForm = defineAsyncComponent(() => import("../../components/admin/SectionPhotoForm.vue"));
const SectionBiographyForm = defineAsyncComponent(() => import("../../components/admin/SectionBiographyForm.vue"));
const SectionItineraryForm = defineAsyncComponent(() => import("../../components/admin/SectionItineraryForm.vue"));
const SectionFaqForm = defineAsyncComponent(() => import("../../components/admin/SectionFaqForm.vue"));
const SectionTestimonialsForm = defineAsyncComponent(() => import("../../components/admin/SectionTestimonialsForm.vue"));
const SectionFeaturedVideoForm = defineAsyncComponent(() => import("../../components/admin/SectionFeaturedVideoForm.vue"));
const SectionVideoVslForm = defineAsyncComponent(() => import("../../components/admin/SectionVideoVslForm.vue"));
const SectionCtaForm = defineAsyncComponent(() => import("../../components/admin/SectionCtaForm.vue"));
const SectionStoryForm = defineAsyncComponent(() => import("../../components/admin/SectionStoryForm.vue"));
const SectionReasonsForm = defineAsyncComponent(() => import("../../components/admin/SectionReasonsForm.vue"));
const SectionLinksForm = defineAsyncComponent(() => import("../../components/admin/SectionLinksForm.vue"));
const SectionCountdownForm = defineAsyncComponent(() => import("../../components/admin/SectionCountdownForm.vue"));
const SectionAgencyFooterForm = defineAsyncComponent(() => import("../../components/admin/SectionAgencyFooterForm.vue"));
const SectionFlightDetailsForm = defineAsyncComponent(() => import("../../components/admin/SectionFlightDetailsForm.vue"));
const SectionViajeonCheckoutForm = defineAsyncComponent(() => import("../../components/admin/SectionViajeonCheckoutForm.vue"));
const SectionInternalFormForm = defineAsyncComponent(() => import("../../components/admin/SectionInternalFormForm.vue"));
const SectionHeaderForm = defineAsyncComponent(() => import("../../components/admin/SectionHeaderForm.vue"));
const PublicHeaderSection = defineAsyncComponent(() => import("../../components/public/PublicHeaderSection.vue"));
const PublicHeroSection = defineAsyncComponent(() => import("../../components/public/PublicHeroSection.vue"));
const PublicBannerCardSection = defineAsyncComponent(() => import("../../components/public/PublicBannerCardSection.vue"));
const PublicPricesSection = defineAsyncComponent(() => import("../../components/public/PublicPricesSection.vue"));
const PublicPhotoSection = defineAsyncComponent(() => import("../../components/public/PublicPhotoSection.vue"));
const PublicBiographySection = defineAsyncComponent(() => import("../../components/public/PublicBiographySection.vue"));
const PublicItinerarySection = defineAsyncComponent(() => import("../../components/public/PublicItinerarySection.vue"));
const PublicFaqSection = defineAsyncComponent(() => import("../../components/public/PublicFaqSection.vue"));
const PublicTestimonialsSection = defineAsyncComponent(() => import("../../components/public/PublicTestimonialsSection.vue"));
const PublicFeaturedVideoSection = defineAsyncComponent(() => import("../../components/public/PublicFeaturedVideoSection.vue"));
const PublicVideoVslSection = defineAsyncComponent(() => import("../../components/public/PublicVideoVslSection.vue"));
const PublicCtaSection = defineAsyncComponent(() => import("../../components/public/PublicCtaSection.vue"));
const PublicStorySection = defineAsyncComponent(() => import("../../components/public/PublicStorySection.vue"));
const PublicReasonsSection = defineAsyncComponent(() => import("../../components/public/PublicReasonsSection.vue"));
const PublicLinksSection = defineAsyncComponent(() => import("../../components/public/PublicLinksSection.vue"));
const PublicCountdownSection = defineAsyncComponent(() => import("../../components/public/PublicCountdownSection.vue"));
const PublicFreeFooterBrandSection = defineAsyncComponent(() => import("../../components/public/PublicFreeFooterBrandSection.vue"));
const PublicAgencyFooterSection = defineAsyncComponent(() => import("../../components/public/PublicAgencyFooterSection.vue"));
const PublicFlightDetailsSection = defineAsyncComponent(() => import("../../components/public/PublicFlightDetailsSection.vue"));
const PublicViajeonCheckoutSection = defineAsyncComponent(() => import("../../components/public/PublicViajeonCheckoutSection.vue"));
const PublicInternalFormSection = defineAsyncComponent(() => import("../../components/public/PublicInternalFormSection.vue"));

const sectionTypes: SectionType[] = [
  "header",
  "hero",
  "banner_card",
  "photo",
  "biography",
  "prices",
  "itinerary",
  "faq",
  "testimonials",
  "featured_video",
  "video_vsl",
  "cta",
  "story",
  "reasons",
  "links",
  "countdown",
  "flight_details",
  "viajeon_checkout",
  "internal_form",
  "agency_footer"
];
const sectionLabels = defaultSectionLabels;
// No editor novo as seções usam os nomes novos ("Capa da viagem", "Menu do topo"...).
const sectionLabelOf = (section: PageSection) =>
  (newEditor.value && sectionNameV2(section.type)) || sectionLabels[section.type as SectionType] || section.type;
const sectionDescriptions: Partial<Record<SectionType, string>> = {
  header: t({
    pt: "Cabeçalho de navegação com logo, links, redes sociais ou botão de contato.",
    es: "Encabezado de navegación con logo, enlaces, redes sociales o botón de contacto."
  }),
  hero: t({
    pt: "Bloco inicial com destaque visual, título, subtítulo e CTA principal.",
    es: "Bloque inicial con destaque visual, título, subtítulo y CTA principal."
  }),
  banner_card: t({
    pt: "Banner em card com imagem de fundo, gradiente e CTA destacado.",
    es: "Banner en formato card con imagen de fondo, gradiente y CTA destacado."
  }),
  photo: t({
    pt: "Uma única imagem em destaque. Escolha o layout card ou largura total.",
    es: "Una única imagen destacada. Elige entre layout card o ancho completo."
  }),
  biography: t({
    pt: "Imagem em largura total com título sobreposto e texto descritivo.",
    es: "Imagen a ancho completo con título superpuesto y texto descriptivo."
  }),
  prices: t({
    pt: "Tabela com planos, valores e diferenciais para cada oferta.",
    es: "Tabla con planes, precios y diferenciales para cada oferta."
  }),
  itinerary: t({
    pt: "Sequência de etapas/benefícios para explicar seu serviço ou roteiro.",
    es: "Secuencia de etapas/beneficios para explicar tu servicio o itinerario."
  }),
  faq: t({
    pt: "Perguntas e respostas para antecipar dúvidas frequentes.",
    es: "Preguntas y respuestas para anticipar dudas frecuentes."
  }),
  testimonials: t({
    pt: "Carrossel ou lista com depoimentos de clientes.",
    es: "Carrusel o lista con testimonios de clientes."
  }),
  featured_video: t({
    pt: "Destaque um vídeo com título, subtítulo e CTA centralizado.",
    es: "Destaca un video con título, subtítulo y CTA centrado."
  }),
  cta: t({
    pt: "Chamada final impulsionando o lead para a ação desejada.",
    es: "Llamado final que impulsa al lead hacia la acción deseada."
  }),
  story: t({
    pt: "Bloco de storytelling para contar sua história, bastidores ou roteiro.",
    es: "Bloque de storytelling para contar tu historia, bastidores o itinerario."
  }),
  reasons: t({
    pt: "Liste motivos, benefícios e serviços para reforçar a decisão.",
    es: "Lista motivos, beneficios y servicios para reforzar la decisión."
  }),
  countdown: t({
    pt: "Cria urgência com contador regressivo para promoções ou eventos.",
    es: "Crea urgencia con un contador regresivo para promociones o eventos."
  }),
  flight_details: t({
    pt: "Mostra voos de ida e volta com multiplos trechos, bagagens e visual premium.",
    es: "Muestra vuelos de ida y vuelta con multiples tramos, equipajes y visual premium."
  }),
  video_vsl: t({
    pt: "Vídeo de vendas com liberação programada de botão e conteúdo da página.",
    es: "Video de ventas con liberación programada de botón y contenido de la página."
  }),
  links: t({
    pt: "Carrossel de páginas e links externos com imagem, título e descrição.",
    es: "Carrusel de páginas y enlaces externos con imagen, título y descripción."
  }),
  viajeon_checkout: t({
    pt: "Lista todos os pacotes ativos de um checkout Viajeon e envia a seleção para o pagamento externo.",
    es: "Lista todos los paquetes activos de un checkout Viajeon y envía la selección al pago externo."
  }),
  internal_form: t({
    pt: "Formulário incorporado à página, com fundo personalizável e confirmação após o envio.",
    es: "Formulario integrado en la página, con fondo personalizable y confirmación tras el envío."
  }),
  agency_footer: t({
    pt: "Cartão institucional com contatos, redes sociais e mapa da agência.",
    es: "Tarjeta institucional con contactos, redes sociales y mapa de la agencia."
  })
};

const catalogFallbackDescription = t({
  pt: "Bloco personalizável para compor sua página.",
  es: "Bloque personalizable para componer tu página."
});

const sectionThumbnails: Partial<Record<SectionType, string>> = {
  header: headerThumb,
  hero: heroThumb,
  banner_card: bannerCardThumb,
  photo: photoThumb,
  biography: biographyThumb,
  prices: pricesThumb,
  itinerary: itineraryThumb,
  faq: faqThumb,
  testimonials: testimonialsThumb,
  featured_video: featuredVideoThumb,
  video_vsl: videoVslThumb,
  cta: ctaThumb,
  story: storyThumb,
  reasons: reasonsThumb,
  links: linksThumb,
  countdown: countdownThumb,
  flight_details: flightsThumb,
  viajeon_checkout: viajeonCheckoutThumb,
  internal_form: internalFormThumb,
  agency_footer: footerThumb
};
const sectionAccents: Partial<Record<SectionType, string>> = {
  header: "from-slate-800/90 to-slate-600/70",
  hero: "from-sky-100 to-slate-50",
  banner_card: "from-emerald-600/90 to-emerald-400/70",
  photo: "from-slate-100 to-white",
  biography: "from-slate-900/80 to-slate-800/60",
  prices: "from-amber-100 to-white",
  itinerary: "from-emerald-100/70 to-white",
  faq: "from-slate-100 to-white",
  testimonials: "from-purple-100/70 to-white",
  featured_video: "from-indigo-100/70 to-white",
  video_vsl: "from-violet-100/70 to-white",
  cta: "from-cyan-100/70 to-white",
  story: "from-rose-100/70 to-white",
  reasons: "from-indigo-100/70 to-white",
  links: "from-lime-100/70 to-white",
  countdown: "from-orange-100/70 to-white",
  flight_details: "from-sky-100/70 to-white",
  viajeon_checkout: "from-emerald-100/70 to-white",
  internal_form: "from-blue-100/70 to-white",
  agency_footer: "from-slate-900/90 to-slate-800/70"
};
const formComponents: Partial<Record<SectionType, any>> = {
  header: SectionHeaderForm,
  hero: SectionHeroForm,
  banner_card: SectionBannerCardForm,
  photo: SectionPhotoForm,
  biography: SectionBiographyForm,
  prices: SectionPricesForm,
  itinerary: SectionItineraryForm,
  faq: SectionFaqForm,
  testimonials: SectionTestimonialsForm,
  featured_video: SectionFeaturedVideoForm,
  video_vsl: SectionVideoVslForm,
  cta: SectionCtaForm,
  story: SectionStoryForm,
  reasons: SectionReasonsForm,
  links: SectionLinksForm,
  countdown: SectionCountdownForm,
  flight_details: SectionFlightDetailsForm,
  viajeon_checkout: SectionViajeonCheckoutForm,
  internal_form: SectionInternalFormForm,
  agency_footer: SectionAgencyFooterForm
};

const publicComponents: Partial<Record<SectionType, any>> = {
  header: PublicHeaderSection,
  hero: PublicHeroSection,
  banner_card: PublicBannerCardSection,
  photo: PublicPhotoSection,
  biography: PublicBiographySection,
  prices: PublicPricesSection,
  itinerary: PublicItinerarySection,
  faq: PublicFaqSection,
  testimonials: PublicTestimonialsSection,
  featured_video: PublicFeaturedVideoSection,
  video_vsl: PublicVideoVslSection,
  cta: PublicCtaSection,
  story: PublicStorySection,
  reasons: PublicReasonsSection,
  links: PublicLinksSection,
  countdown: PublicCountdownSection,
  flight_details: PublicFlightDetailsSection,
  viajeon_checkout: PublicViajeonCheckoutSection,
  internal_form: PublicInternalFormSection,
  free_footer_brand: PublicFreeFooterBrandSection,
  agency_footer: PublicAgencyFooterSection
};

const sectionRequiresBranding = (type?: SectionType | string | null) => type === "hero" || type === "agency_footer";

const sections = shallowRef<PageSection[]>([]);
const previewSectionExtraProps = (section: PageSection) => {
  const extra: Record<string, unknown> = {};
  if (sectionRequiresBranding(section.type)) extra.branding = branding.value;
  if (section.type === "video_vsl") {
    extra.highlightColor = theme.value.ctaDefaultColor || section.ctaColor;
    const hero = sections.value.find(item => item.type === "hero") as HeroSection | undefined;
    extra.logoUrl = hero?.logoUrl || branding.value.logo_url || currentAgency.value?.logo_url || "";
  }
  const activeHeader = sections.value.some(item => item.type === "header" && item.enabled);
  if (section.type === "hero") extra.hideLogo = activeHeader;
  if (section.type === "itinerary" && previewDesign.value === "v2") {
    const hero = sections.value.find(item => item.type === "hero") as HeroSection | undefined;
    extra.tripStartDate = hero?.departureDate || "";
  }
  if (section.type === "header") {
    const hero = sections.value.find(item => item.type === "hero") as HeroSection | undefined;
    extra.logoUrl = hero?.logoUrl || branding.value.logo_url || "";
    extra.previewBackgroundImage = hero?.backgroundImage || "";
    extra.previewOverlayColor = hero?.gradientColor || hero?.backgroundColor || "#05060f";
    extra.agencyName = branding.value.agency_name || currentAgency.value?.name || "";
    extra.agencySocialLinks = currentAgency.value?.social_links || branding.value.agency_profile?.social_links || [];
  }
  return extra;
};
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
const editingSectionOriginalSnapshot = ref("");
const editingSectionFormRef = ref<any>(null);
const sectionModalPanelRef = ref<HTMLElement | null>(null);
const sectionModalHeaderRef = ref<HTMLElement | null>(null);
const sectionModalBodyRef = ref<HTMLElement | null>(null);
const sectionModalFooterRef = ref<HTMLElement | null>(null);
const sectionModalObservedBodyMax = ref(0);
let sectionModalResizeObserver: ResizeObserver | null = null;
const unsavedFlightSegmentModal = ref({ open: false });
const unsavedSectionModal = ref({ open: false, saving: false });
let pendingUnsavedSectionAction: null | (() => void | Promise<void>) = null;
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
const editingSectionHeaderLabel = computed(() => {
  const type = editingSectionType.value;
  if (!type) return "";
  if (newEditor.value && sectionNameV2(type)) return sectionNameV2(type)!;
  if (type === "banner_card") return "Banner em Card";
  if (type === "featured_video") return "Vídeo";
  if (type === "video_vsl") return "Video VSL";
  if (type === "flight_details") return "Voos";
  return editingSectionLabel.value;
});
// No editor novo, todas as seções usam o formulário no padrão novo (Conteúdo / Aparência).
const v2FormComponents: Partial<Record<SectionType, any>> = {
  hero: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormHero.vue")),
  banner_card: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormBannerCard.vue")),
  video_vsl: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormVideoVsl.vue")),
  story: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormStory.vue")),
  reasons: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormReasons.vue")),
  photo: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormPhoto.vue")),
  featured_video: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormFeaturedVideo.vue")),
  biography: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormBiography.vue")),
  itinerary: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormItinerary.vue")),
  prices: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormPrices.vue")),
  countdown: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormCountdown.vue")),
  cta: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormCta.vue")),
  testimonials: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormTestimonials.vue")),
  faq: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormFaq.vue")),
  agency_footer: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormAgencyFooter.vue")),
  header: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormHeader.vue")),
  links: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormLinks.vue")),
  flight_details: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormFlightDetails.vue")),
  viajeon_checkout: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormViajeonCheckout.vue")),
  internal_form: defineAsyncComponent(() => import("../../components/admin/v2edit/forms/FormInternalForm.vue"))
};
const usesV2Form = computed(() => newEditor.value && !!editingSectionType.value && !!v2FormComponents[editingSectionType.value]);
const editingSectionComponent = computed(() => {
  const type = editingSectionType.value;
  if (!type) return null;
  return (usesV2Form.value && v2FormComponents[type]) || formComponents[type];
});
const isSectionEditorOpen = computed(() => editingSectionIndex.value !== null && !!editingSectionDraft.value);
// Editor novo: a seção abre no painel da esquerda, no lugar das configurações da página,
// e a prévia mostra o rascunho enquanto a pessoa digita. Seções sem formulário novo seguem no modal.
const sectionPanelOpen = computed(() => isSectionEditorOpen.value && usesV2Form.value);
const sectionPanelMenuOpen = ref(false);
const livePreviewDraft = computed(() => {
  const draft = editingSectionDraft.value;
  const index = editingSectionIndex.value;
  if (!draft || index === null) return null;
  const base = previewSections.value[index];
  // Mantém o fundo calculado da página até a pessoa escolher outro na própria seção.
  return base && !(draft as any).customBackground ? ({ ...draft, backgroundColor: (base as any).backgroundColor } as PageSection) : draft;
});
watch(sectionPanelOpen, open => {
  sectionPanelMenuOpen.value = false;
  if (!open) return;
  // Espera a prévia se ajustar à largura do painel antes de rolar até a seção.
  setTimeout(() => {
    const el = previewCanvasRef.value?.querySelector(`[data-preview-index="${editingSectionIndex.value}"]`);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 350);
});
const toggleEditingSectionVisibility = () => {
  const draft = editingSectionDraft.value as any;
  if (!draft) return;
  updateEditingDraft({ ...draft, enabled: draft.enabled === false });
};
// Ações do menu "⋯": fecham o painel (pedindo para salvar, se houver mudança) e agem na seção.
const runPanelAction = (action: "up" | "down" | "duplicate" | "delete") => {
  const index = editingSectionIndex.value;
  if (index === null) return;
  const run = () => {
    forceCloseSectionEditor();
    if (action === "up") return moveSection(index, -1);
    if (action === "down") return moveSection(index, 1);
    if (action === "duplicate") return duplicateSection(index);
    return removeSection(index);
  };
  if (hasUnsavedSectionDraftChanges.value) requestUnsavedSectionConfirmation(run);
  else run();
};
// Voos: os trechos são salvos à parte (um a um) e o editor de trechos completa a seção ao abrir,
// então a comparação olha só os campos que a pessoa edita no painel.
const sectionDraftSnapshot = (section: PageSection | null) => {
  if (!section) return "";
  if (section.type !== "flight_details") return JSON.stringify(section);
  const flight = section as any;
  return JSON.stringify({
    enabled: flight.enabled !== false,
    headingLabel: flight.headingLabel ?? null,
    title: flight.title ?? "",
    subtitle: flight.subtitle ?? "",
    generalInfo: flight.generalInfo ?? "",
    showOutbound: flight.showOutbound !== false,
    showInbound: flight.showInbound !== false,
    backgroundColor: flight.customBackground ? flight.backgroundColor : null
  });
};
const hasUnsavedSectionDraftChanges = computed(() => {
  if (!isSectionEditorOpen.value || !editingSectionDraft.value || !editingSectionOriginalSnapshot.value) return false;
  return sectionDraftSnapshot(editingSectionDraft.value) !== editingSectionOriginalSnapshot.value;
});
watch(
  [hasUnsavedChanges, hasUnsavedSectionDraftChanges],
  ([pageUnsaved, sectionUnsaved]) => {
    if (!hasWindow) return;
    if (pageUnsaved || sectionUnsaved) {
      window.addEventListener("beforeunload", beforeUnloadHandler);
    } else {
      window.removeEventListener("beforeunload", beforeUnloadHandler);
    }
  },
  { immediate: false }
);
const sectionModalPanelStyle = computed(() => {
  if (!isSectionEditorOpen.value) return {};
  const headerHeight = sectionModalHeaderRef.value?.offsetHeight || 0;
  const footerHeight = sectionModalFooterRef.value?.offsetHeight || 0;
  const bodyHeight = Math.max(560, sectionModalObservedBodyMax.value || 0);
  const desiredHeight = headerHeight + footerHeight + bodyHeight;
  const viewportCap = Math.round((hasWindow ? window.innerHeight : 900) * (isMobileViewport.value ? 0.88 : 0.9));
  return {
    height: `${Math.min(desiredHeight, viewportCap)}px`,
    minHeight: `${Math.min(headerHeight + footerHeight + 520, viewportCap)}px`,
    maxHeight: `${viewportCap}px`
  };
});
const getBrowserStorage = () => {
  if (!hasWindow) return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
};
provide(sectionsInjectionKey, sections);
provide(
  PAGE_DESIGN_KEY,
  computed(() => ({ accent: ctaColor.value || DEFAULT_ACCENT }))
);
watch(useLegacyDesign, () => markUnsavedChanges());
provide(
  PUBLIC_BRANDING_KEY,
  computed(() => ({
    ...branding.value,
    theme: theme.value
  }))
);

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
// Linha de inserir entre seções: nunca acima do Menu do topo.
const canInsertBefore = (index: number) => !isHeaderSection(sections.value[index]);
const isHeaderSection = (section?: PageSection | null) => !!section && (section as any).type === "header";
const isVideoVslSection = (section?: PageSection | null) => !!section && (section as any).type === "video_vsl";
const enforceFooterConstraints = (list?: PageSection[] | null) => {
  const normalized = (list || []).filter(Boolean).filter((section, index, all) => !isHeaderSection(section) || index === all.findIndex(isHeaderSection));
  const hasActiveHero = normalized.some(section => section.type === "hero" && section.enabled !== false);
  if (!hasActiveHero) {
    const headerIndex = normalized.findIndex(isHeaderSection);
    if (headerIndex >= 0) {
      const header = normalized[headerIndex] as HeaderSection;
      if (header.mode !== "solid") normalized[headerIndex] = { ...header, mode:"solid", backgroundColor:"#ffffff", textColor:"#0f172a", linkTextColor:"#0f172a" };
    }
  }
  const headerIndex = normalized.findIndex(isHeaderSection);
  if (headerIndex > 0) normalized.unshift(normalized.splice(headerIndex, 1)[0]);
  const videoVslSections = normalized.filter(isVideoVslSection);
  if (videoVslSections.length) {
    normalized.splice(0, normalized.length, ...videoVslSections, ...normalized.filter(section => !isVideoVslSection(section)));
  }
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
const collectStoryVideos = (videos?: string[], fallback?: string) => {
  const normalized = Array.isArray(videos)
    ? videos.map(video => (typeof video === "string" ? video.trim() : "")).filter(video => video.length > 0)
    : [];
  if (typeof fallback === "string") {
    const trimmed = fallback.trim();
    if (trimmed && !normalized.includes(trimmed)) {
      normalized.unshift(trimmed);
    }
  }
  return normalized;
};
const countStoryVideos = (videos?: string[], fallback?: string) => collectStoryVideos(videos, fallback).length;
const automaticStoryLayout = (images?: string[], videos?: string[], fallbackVideo?: string) =>
  countStoryImages(images) + countStoryVideos(videos, fallbackVideo) > 1 ? "gallery" : "single";
const applyAutomaticStoryLayout = (story: StorySection) => {
  const desired = automaticStoryLayout(story.images, story.videoUrls, story.videoUrl);
  if (story.layout !== desired) {
    story.layout = desired;
  }
};

const storyMediaErrorText = t({
  pt: "Adicione ao menos uma imagem ou vídeo na seção Story antes de salvar.",
  es: "Agrega al menos una imagen o video en la seccion Story antes de guardar."
});
const hasStoryImage = (section: StorySection) => countStoryImages(section.images) > 0;
const hasStoryVideo = (section: StorySection) => countStoryVideos(section.videoUrls, section.videoUrl) > 0;
const validateSection = (section: PageSection | null): string | null => {
  if (!section) return null;
  if ((section as any).type === "story") {
    const story = section as StorySection;
    applyAutomaticStoryLayout(story);
    if (!hasStoryImage(story) && !hasStoryVideo(story)) return storyMediaErrorText;
  }
  if ((section as any).type === "viajeon_checkout" && section.enabled !== false) {
    const viajeon = section as ViajeonCheckoutSection;
    if (!viajeon.checkoutId) return "Selecione um checkout ativo do Viajeon antes de salvar a seção.";
  }
  if ((section as any).type === "internal_form" && section.enabled !== false) {
    const internalForm = section as InternalFormSection;
    if (!internalForm.formId) return "Selecione um formulário antes de salvar a seção Formulário interno.";
  }
  if ((section as any).type === "header" && ((section as HeaderSection).links || []).length > 7) {
    return "O cabeçalho permite no máximo 7 links de navegação.";
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
  const agencyDigits = normalizeWhatsappDigits(agency?.cta_whatsapp || "");
  if (agencyDigits) return agencyDigits;
  return normalizeWhatsappDigits(auth.user?.whatsapp || "");
});
const buildWhatsappLink = (title: string, _planName?: string) => {
  if (!whatsappDigits.value) return "";
  const message = `Oi, tenho interesse no roteiro: ${title || "Roteiro"}`;
  return `https://wa.me/${whatsappDigits.value}?text=${encodeURIComponent(message)}`;
};
const lastAutoWhatsAppLink = ref<string | null>(null);

const pixels = ref<{ id: number; name: string; type: "meta" | "ga"; value: string }[]>([]);
const viajeonConnected = ref(false);
const selectedPixels = reactive<{ meta: string; ga: string }>({ meta: "", ga: "" });
const trackingEvents = ref({ pageView: true, ctaClicks: true, leads: true });
const metaPixelOptions = computed(() => pixels.value.filter(p => p.type === "meta"));
const gaPixelOptions = computed(() => pixels.value.filter(p => p.type === "ga"));
const selectedPixelsSummary = computed(() => {
  const parts: string[] = [];
  if (selectedPixels.meta) parts.push(`Meta: ${selectedPixels.meta}`);
  if (selectedPixels.ga) parts.push(`Google: ${selectedPixels.ga}`);
  return parts.length ? parts.join(" • ") : "não configurado";
});
const resolveSelectedPixel = (type: "meta" | "ga", name: string) =>
  name ? pixels.value.find(p => p.type === type && p.name === name) || null : null;
const leadForms = computed(() => leadCaptureStore.forms);
const leadFormsLoading = computed(() => leadCaptureStore.formsLoading);
const selectedLeadFormId = ref<string>("");
const leadCaptureOptional = ref(false);
const selectedLeadForm = computed(() => leadCaptureStore.getFormById(selectedLeadFormId.value));

const previewModalVisible = ref(false);
const previewForm = ref<LeadForm | null>(null);

watch(
  () => ({ meta: selectedPixels.meta, ga: selectedPixels.ga }),
  () => markUnsavedChanges()
);
watch(
  () => ({ ...trackingEvents.value }),
  () => markUnsavedChanges(),
  { deep: true }
);
watch(selectedLeadFormId, value => {
  if (!value) {
    leadCaptureOptional.value = false;
    hideLeadFormPreview();
  }
  markUnsavedChanges();
});
watch(leadCaptureOptional, () => markUnsavedChanges());
watch(
  leadForms,
  () => {
    if (selectedLeadFormId.value && !leadCaptureStore.getFormById(selectedLeadFormId.value)) {
      selectedLeadFormId.value = "";
    }
  },
  { deep: true }
);

watch(leadFormsLoading, value => {
  if (value) {
    hideLeadFormPreview();
  }
});

const openLeadFormPreview = (form?: LeadForm | null) => {
  const target = form || selectedLeadForm.value;
  if (!target) return;
  previewForm.value = { ...target };
  previewModalVisible.value = true;
};

const hideLeadFormPreview = () => {
  previewModalVisible.value = false;
  previewForm.value = null;
};

const canSelectPixel = computed(() => (auth.user?.plan || "free") !== "free");

const currentAgency = computed(() => {
  const selected = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return selected || agencyStore.agencies[0] || null;
});
const normalizeHostUrl = (host: string | null | undefined) => {
  const trimmed = (host || "").trim();
  if (!trimmed) return "";
  const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  return withProtocol.replace(/\/+$/, "");
};
const activeCustomDomainUrl = computed(() => normalizeHostUrl(agencyStore.currentPrimaryDomain));
const slugBaseLabel = computed(() => {
  if (activeCustomDomainUrl.value) {
    return `${activeCustomDomainUrl.value.replace(/^https?:\/\//i, "")}/`;
  }
  const agencySlug = currentAgency.value?.slug || "nomedaagencia";
  return `${publicSiteBaseUrl.replace(/^https?:\/\//i, "")}/${agencySlug}/`;
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
  const cpfDigits = sanitizeDigits(user?.cpf || "");
  const phone = (agency?.cta_whatsapp || user?.whatsapp || "").trim();
  const email = (agency?.contact_email || user?.email || "").trim();
  const cadasturCnpjUrl = cnpjDigits
    ? `https://cadastur.turismo.gov.br/cadastur/#!/public/qrcode/${cnpjDigits}`
    : "";
  const cadasturCpfUrl = cpfDigits
    ? `https://cadastur.turismo.gov.br/cadastur/#!/public/qrcode/${cpfDigits}`
    : "";

  return {
    name: agency?.name || user?.name || "",
    description: (agency?.description || "").trim(),
    cpf: user?.cpf || "",
    cpf_digits: cpfDigits || undefined,
    cnpj: user?.cnpj || "",
    cnpj_digits: cnpjDigits || undefined,
    email,
    phone,
    social_links: agency?.social_links || [],
    address,
    address_text: addressText || "",
    map_query: addressText || "",
    map_embed_url: addressText
      ? `https://www.google.com/maps?q=${encodeURIComponent(addressText)}&output=embed`
      : "",
    cadastur_url: cadasturCnpjUrl,
    cadastur_urls: {
      cnpj: cadasturCnpjUrl,
      cpf: cadasturCpfUrl
    }
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

const loadPixels = async () => {
  try {
    const res = await api.get("/pixels/");
    pixels.value = res.data;
  } catch (err) {
    console.error("Erro ao carregar pixels", err);
  }
};

const loadViajeonStatus = async () => {
  try {
    const response = await api.get("/integrations/viajeon");
    viajeonConnected.value = response.data?.connected === true;
  } catch (err) {
    console.error("Erro ao consultar integração Viajeon", err);
    viajeonConnected.value = false;
  }
};

const clone = <T>(val: T): T => {
  try {
    // structuredClone pode não existir em browsers antigos; fallback seguro
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

    if (type === "prices") {
      const priceSection = section as PricesSection;
      if ((priceSection as any).ctaMode !== "section") {
        const current = priceSection.ctaLink;
        if (!current || isAutoLink(current, autoLink)) {
          priceSection.ctaLink = autoLink;
        }
      }
      priceSection.items = (priceSection.items || []).map(item => {
        if (item.ctaMode === "section") return item;
        const itemAutoLink = buildWhatsappLink(pageTitle.value, String(item.title || "")) || autoLink;
        if (!item.ctaLink || isAutoLink(item.ctaLink, itemAutoLink)) {
          item.ctaLink = itemAutoLink;
        }
        item.ctaMode = item.ctaMode || "link";
        item.ctaSectionId = null;
        return item;
      });
      return priceSection;
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

    // Fundo escolhido na seção (editor novo): fica como está, só ajusta a cor do texto.
    if ((normalized as any).customBackground && (normalized as any).backgroundColor) {
      const readable = getReadableTextColor((normalized as any).backgroundColor);
      if (readable) (normalized as any).textColor = readable;
      if (type !== "header" && type !== "hero" && type !== "countdown" && type !== "free_footer_brand" && type !== "banner_card" && type !== "agency_footer") {
        altIndex += 1;
      }
      return normalized;
    }
    if (
      type === "header" ||
      type === "hero" ||
      type === "countdown" ||
      type === "free_footer_brand" ||
      type === "banner_card"
    ) {
      if ((normalized as any).type === "banner_card" && (!(normalized as any).backgroundColor || newEditor.value)) {
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
        if (!(normalized as any).backgroundColor || newEditor.value) {
          (normalized as any).backgroundColor = nextColor;
        }
        altIndex += 1;
      } else {
        delete (normalized as any).backgroundColor;
      }
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

watch(currentAgency, agency => {
  applyAgencyBranding();
  if (agency && !(agency.id in agencyStore.primaryDomains)) {
    agencyStore.loadPrimaryDomain(agency.id);
  }
}, { immediate: true });
watch(
  () => ({
    cpf: auth.user?.cpf,
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
  ...(useLegacyDesign.value ? { design: "legacy" as const } : {}),
  general: {
    shortDescription: pageShortDescription.value || ""
  },
  theme: { ...theme.value, color1: colorA.value, color2: colorB.value },
  editor: { ...editorPrefs.value, previewEnabled: true, previewDevice: previewDevice.value },
  sections: applySectionBackgrounds(sections.value),
  leadCapture: selectedLeadFormId.value ? { formId: selectedLeadFormId.value, optional: leadCaptureOptional.value } : null,
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
} as any);

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
  clearPreviewScheduler();
  if (!previewReady.value) {
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
  if (type === "header") {
    return ensureSectionAnchor({
      type: "header",
      enabled: true,
      mode: "solid",
      backgroundColor: "#ffffff",
      blurAmount: 14,
      textColor: "#0f172a",
      linkTextColor: "#0f172a",
      linkFontSize: 14,
      linkHoverColor: theme.value.ctaDefaultColor || "#22c55e",
      linkHoverAnimation: "underline",
      logoSize: 56,
      logoActionType: "top",
      logoActionTarget: "",
      logoOpenInNewTab: false,
      stickyEnabled: true,
      links: [],
      actionType: "none",
      socialLinks: [
        { platform: "instagram", url: "" },
        { platform: "facebook", url: "" },
        { platform: "youtube", url: "" },
        { platform: "tiktok", url: "" },
        { platform: "linkedin", url: "" }
      ],
      contactLabel: "Entrar em contato",
      contactType: "whatsapp",
      contactValue: whatsappDigits.value,
      whatsappMessage: `Olá! Gostaria de mais informações sobre ${pageTitle.value || "este roteiro"}.`,
      buttonColor: theme.value.ctaDefaultColor || "#22c55e"
    } as HeaderSection);
  }
  if (type === "internal_form") {
    return ensureSectionAnchor({
      type: "internal_form",
      enabled: true,
      title: "Fale com um especialista",
      subtitle: "Preencha seus dados e entraremos em contato.",
      headingLabel: "Fale conosco",
      headingLabelStyle: "outline",
      formId: "",
      backgroundType: "solid",
      backgroundColor: colorA.value || "#f8fafc",
      gradientStart: "#0f172a",
      gradientEnd: theme.value.ctaDefaultColor || "#2563eb",
      gradientDirection: "to bottom right",
      overlayOpacity: 0.35,
      alignment: "center",
      textColor: "#0f172a",
      buttonColor: theme.value.ctaDefaultColor || "#22c55e",
      successMessage: "Obrigado! Recebemos suas informações com sucesso.",
      successDurationSeconds: 5
    } as InternalFormSection);
  }
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
    ctaSectionId: null,
    enableAnimation: true,
    animationDuration: 1000,
    ctaShimmer: true
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
    ctaEnabled: true,
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

if (type === "biography") {
  return ensureSectionAnchor({
    type: "biography",
    enabled: true,
    fullWidth: true,
    title: { pt: "BIOGRAFIA", es: "BIOGRAFÍA" },
    text: {
      pt: "Use esta seção para compartilhar sua trajetória, conquistas e bastidores. Histórias reais criam conexão com o visitante e reforçam sua autoridade no assunto.",
      es: "Usa esta sección para compartir tu trayectoria, logros y bastidores. Las historias reales generan conexión con el visitante y refuerzan tu autoridad."
    },
    image:
      "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
    overlayOpacity: 0.45,
    titleColor: "#ffffff",
    textColor: "#0f172a",
    titleFontSize: 72,
    textFontSize: 18
  } as BiographySection);
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
        highlight: false,
        ctaLink: buildWhatsappLink(pageTitle.value, "Apartamento duplo") || "",
        ctaMode: "link",
        ctaSectionId: null,
        ctaOpenInNewTab: true
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
    items: [{ name: "Mariana", text: "Viagem incrível, super bem organizada!", avatar: "" }],
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
    subtitle: "Mostre o clima da experiência com um vídeo curto e objetivo.",
    videoUrl: "https://www.youtube.com/watch?v=ysz5S6PUM-U",
    ctaEnabled: true,
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
    enableAnimation: true,
    ctaShimmer: true,
    ctaMode: "link",
    ctaSectionId: null,
    borderEnabled: false,
    borderColor: "#cbd5e1",
    images: defaultImages,
    videoUrls: []
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
    countdownMode: "fixed",
    sessionDuration: 15,
    sessionUnit: "minutes",
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
    subtitle: "Benefícios claros para ajudar na conversão",
    items: [
      { icon: "💸", title: "Economize dinheiro", description: "Aproveite negociações especiais e otimize seu orçamento." },
      { icon: "🧭", title: "Mais liberdade", description: "Planeje quando quiser com apoio de especialistas locais." },
      { icon: "🤝", title: "Apoio dedicado", description: "Suporte próximo antes, durante e depois da viagem." },
      { icon: "✨", title: "Experiência única", description: "Curadoria de passeios e hospedagens memoráveis." }
    ],
    enableAnimation: true,
    animationDuration: 1000,
    cardAnimationStagger: 300
  } as ReasonsSection);
}

if (type === "flight_details") {
  return ensureSectionAnchor({
    type: "flight_details",
    enabled: true,
    sectionId: `flight-${Math.random().toString(36).slice(2, 10)}`,
    title: "Informações do voo",
    subtitle: "Confira os detalhes dos voos inclusos no pacote",
    generalInfo: "",
    ctaColor: theme.value.ctaDefaultColor,
    visualStyle: "decolar",
    showOutbound: true,
    showInbound: true,
    journeys: []
  } as FlightDetailsSection);
}

if (type === "video_vsl") {
  const headingDefaults = getSectionHeadingDefaults("video_vsl");
  return ensureSectionAnchor({
    type: "video_vsl",
    enabled: true,
    headingLabel: headingDefaults.label,
    headingLabelStyle: headingDefaults.style,
    title: "Assista ao vídeo antes de continuar",
    subtitle: "Descubra todos os detalhes desta oferta especial.",
    videoUrl: "https://www.youtube.com/watch?v=ysz5S6PUM-U",
    videoAspectRatio: "horizontal",
    logoEnabled: true,
    logoSize: 88,
    backgroundImageOpacity: 70,
    progressBarEnabled: true,
    unlockAfterSeconds: 60,
    unlockAction: "reveal_page",
    ctaLabel: "Quero aproveitar esta oferta",
    ctaLink: "https://wa.me/",
    ctaOpenInNewTab: true,
    ctaColor: theme.value.ctaDefaultColor
  } as VideoVslSection);
}

if (type === "links") {
  const headingDefaults = getSectionHeadingDefaults("links");
  return ensureSectionAnchor({
    type: "links",
    enabled: true,
    headingLabel: headingDefaults.label,
    headingLabelStyle: headingDefaults.style,
    title: "Explore outros roteiros",
    subtitle: "Conheça outras experiências selecionadas para você.",
    items: [],
    carouselEnabled: true,
    backgroundColor: "#f8fafc",
    textColor: "#111827",
    cardBackgroundColor: "#ffffff",
    buttonColor: theme.value.ctaDefaultColor || "#6df56d",
    buttonTextColor: theme.value.ctaTextColor || "#071107"
  } as LinksSection);
}

if (type === "viajeon_checkout") {
  return ensureSectionAnchor({
    type: "viajeon_checkout",
    enabled: true,
    checkoutId: "",
    checkoutName: "",
    title: "Escolha seu pacote",
    subtitle: "Selecione as quantidades e continue para o pagamento.",
    buttonLabel: "Continuar para o checkout",
    backgroundColor: colorA.value || "#F8FAFC",
    textColor: "#0F172A",
    accentColor: theme.value.ctaDefaultColor || "#12B981",
    cardBackgroundColor: "#FFFFFF",
    cardTextColor: "#0F172A",
    buttonColor: theme.value.ctaDefaultColor || "#12B981",
    buttonTextColor: theme.value.ctaTextColor || "#FFFFFF",
    checkoutSnapshot: null
  } as ViajeonCheckoutSection);
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
    useLegacyDesign.value = parsed.design === "legacy";

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

    const general = (parsed as any).general;
    pageShortDescription.value = typeof general?.shortDescription === "string" ? general.shortDescription : "";

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
        ctaClicks: tracking.events.ctaClicks !== false,
        leads: tracking.events.leads !== false
      };
    }

  const leadCapture = (parsed as any).leadCapture;
  if (leadCapture?.formId) {
    selectedLeadFormId.value = String(leadCapture.formId);
    leadCaptureOptional.value = !!leadCapture.optional;
  } else {
    selectedLeadFormId.value = "";
    leadCaptureOptional.value = false;
  }

    applyPrimaryToThemeAndSections(oldDefaultCta);
  } catch (err) {
    console.error("Erro ao ler config_json", err);
  }
};

const defaultPageSlugPattern = /^roteiro-\d+$/i;
const fetchPage = async () => {
  if (!auth.token) {
    errorMessage.value = viewCopy.feedback.loginAgain;
    return;
  }

  if (!auth.user) {
    try {
      await auth.fetchProfile();
    } catch (err) {
      errorMessage.value = viewCopy.feedback.sessionExpired;
      return;
    }
  }

  try {
    const res = await api.get<Page>(`/pages/${pageId}`);
    page.value = res.data;
    const loadedTitle = res.data.title || "";
    const existingSlug = (res.data.slug || "").trim();
    const normalizedExistingSlug = normalizeSlugInput(existingSlug);
    const generatedSlug = normalizeSlugInput(loadedTitle);
    const shouldReplaceWithGenerated = !normalizedExistingSlug || defaultPageSlugPattern.test(existingSlug);
    slugAutoSyncEnabled.value = shouldReplaceWithGenerated || normalizedExistingSlug === generatedSlug;
    pageTitle.value = loadedTitle;
    pageSlug.value = shouldReplaceWithGenerated ? generatedSlug : normalizedExistingSlug || generatedSlug;

    hydrateFromConfig(res.data.config_json);
    await nextTick();
    syncSavedSnapshot();
    initialLoadComplete.value = true;
    message.value = "";
  } catch (err) {
    console.error(err);
    errorMessage.value = viewCopy.feedback.pageLoadError;
  }
};

const saveConfig = async (): Promise<boolean> => {
  if (!auth.token) {
    errorMessage.value = viewCopy.feedback.sessionExpired;
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
    await api.put(`/pages/${pageId}`, { title: pageTitle.value, slug: pageSlug.value, seo_title: null });

    const configPayload = buildConfig();
    await api.put(`/pages/${pageId}/config`, { config: configPayload });

    message.value = viewCopy.feedback.configSaved;
    showSnackbar(viewCopy.feedback.configSavedToast);
    syncSavedSnapshot();
    return true;
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    if (detail) {
      limitModal.value = { open: true, message: String(detail) };
    } else {
      errorMessage.value = viewCopy.feedback.configSaveError;
      showSnackbar(viewCopy.feedback.configSaveError);
    }
    return false;
  }
};

const publishPage = async () => {
  if (!auth.token) {
    errorMessage.value = viewCopy.feedback.sessionExpired;
    return;
  }

  errorMessage.value = "";
  message.value = "";

  try {
    const saved = await saveConfig();
    if (!saved) return;
    const res = await api.post(`/pages/${pageId}/publish`, { publish: true });
    page.value = res.data;

    message.value = viewCopy.feedback.publishSuccess;
    successModal.value.open = true;
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;

    if (detail) {
      limitModal.value = { open: true, message: String(detail) };
    } else {
      errorMessage.value = viewCopy.feedback.publishError;
      showSnackbar(viewCopy.feedback.publishError);
    }
  }
  };

const unpublishPage = async () => {
  if (!auth.token) {
    errorMessage.value = viewCopy.feedback.sessionExpired;
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
    message.value = viewCopy.feedback.unpublishSuccess;
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    if (detail) {
      errorMessage.value = String(detail);
    } else {
      errorMessage.value = viewCopy.feedback.unpublishError;
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

const sectionPickerAfterLabel = computed(() => {
  const index = sectionPicker.value.index;
  const section = typeof index === "number" ? sections.value[index] : null;
  return section ? `${index! + 1}. ${sectionLabelOf(section)}` : "";
});
const insertedToast = ref<{ index: number; type: string; anchorId?: string; label: string } | null>(null);
let insertedToastTimer: ReturnType<typeof setTimeout> | null = null;
const undoInsertedSection = () => {
  const added = insertedToast.value;
  insertedToast.value = null;
  if (!added) return;
  // Os objetos das seções são recriados ao salvar no estado, então procuramos pela âncora ou pela posição.
  const index = added.anchorId
    ? sections.value.findIndex(section => (section as any).anchorId === added.anchorId)
    : sections.value[added.index]?.type === added.type
      ? added.index
      : -1;
  if (index < 0) return;
  setSections(current => current.filter((_, idx) => idx !== index));
  refreshPreview(true);
};
onBeforeUnmount(() => {
  if (insertedToastTimer) clearTimeout(insertedToastTimer);
});

const handleSectionPickerSelect = (type: SectionType) => {
  if (type === "viajeon_checkout" && !viajeonConnected.value) return;
  const afterIndex = sectionPicker.value.index;
  const insertAt = typeof afterIndex === "number" ? afterIndex + 1 : sections.value.length;
  const before = new Set(sections.value);
  addSection(type, insertAt);
  closeSectionPicker();
  const addedIndex = sections.value.findIndex(section => !before.has(section));
  const added = sections.value[addedIndex];
  if (newEditor.value && added) {
    insertedToast.value = { index: addedIndex, type: added.type, anchorId: (added as any).anchorId || undefined, label: sectionLabelOf(added) };
    if (insertedToastTimer) clearTimeout(insertedToastTimer);
    insertedToastTimer = setTimeout(() => {
      insertedToast.value = null;
    }, 6000);
  }
};

const addSection = (type: SectionType, insertIndex?: number) => {
  if (type === "header" && sections.value.some(isHeaderSection)) return;
  const next = clone(defaultSection(type));
  const current = sections.value.slice();
  const footerIndex = current.findIndex(isFooterSection);
  const maxInsertIndex = footerIndex >= 0 ? footerIndex : current.length;
  if (type === "header") {
    current.unshift(next);
  } else if (typeof insertIndex === "number") {
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

const duplicateSection = async (index: number) => {
  if (isLockedFooterSection(sections.value[index])) return;
  if (isHeaderSection(sections.value[index])) return;
  const copy = cloneWithNewAnchor(clone(sections.value[index]));
  const next = sections.value.slice();
  next.splice(index + 1, 0, copy);
  setSections(next);
  refreshPreview(true);
  await saveConfig();
};

const removeSection = async (index: number) => {
  if (isLockedFooterSection(sections.value[index])) return;
  const next = sections.value.slice();
  next.splice(index, 1);
  setSections(next);
  refreshPreview(true);
  await saveConfig();
};

const moveSection = async (index: number, direction: number) => {
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
  await saveConfig();
};

// Lista "Seções da página" (aba Conteúdo): ligar/desligar e arrastar para mudar a ordem.
const visibleSectionsCount = computed(() => sections.value.filter(section => (section as any)?.enabled).length);
const sectionDragFrom = ref<number | null>(null);
const sectionDragOver = ref<number | null>(null);
const canDragSection = (index: number) => {
  const section = sections.value[index];
  return !!section && !isHeaderSection(section) && !isLockedFooterSection(section) && !isFooterSection(section);
};
const handleSectionDragStart = (index: number, event: DragEvent) => {
  if (!canDragSection(index)) {
    event.preventDefault();
    return;
  }
  sectionDragFrom.value = index;
  event.dataTransfer?.setData("text/plain", String(index));
};
const resetSectionDrag = () => {
  sectionDragFrom.value = null;
  sectionDragOver.value = null;
};
const handleSectionDrop = async (target: number) => {
  const from = sectionDragFrom.value;
  resetSectionDrag();
  if (from === null || from === target || !canDragSection(target)) return;
  setSections(current => {
    const next = [...current];
    const [moved] = next.splice(from, 1);
    next.splice(target, 0, moved);
    return next;
  });
  refreshPreview(true);
  await saveConfig();
};
const toggleSectionEnabled = async (index: number) => {
  const target = sections.value[index];
  if (!target || isLockedFooterSection(target)) return;
  setSections(current => current.map((section, idx) => (idx === index ? ({ ...section, enabled: !(section as any).enabled } as PageSection) : section)));
  refreshPreview(true);
  await saveConfig();
};
const countLabel = (count: number, singular: string, plural: string) => `${count} ${count === 1 ? singular : plural}`;
const sectionSummary = (section: PageSection) => {
  const data = section as any;
  switch (data.type) {
    case "prices":
      return countLabel(data.items?.length || 0, "pacote", "pacotes");
    case "itinerary":
      return countLabel(data.days?.length || 0, "dia", "dias");
    case "faq":
      return countLabel(data.items?.length || 0, "pergunta", "perguntas");
    case "testimonials":
      return countLabel(data.items?.length || 0, "depoimento", "depoimentos");
    case "reasons":
    case "links":
      return countLabel(data.items?.length || 0, "item", "itens");
  }
  const text = describeSection(section);
  return typeof text === "string" ? text.replace(/<[^>]+>/g, "") : "";
};
const sectionTones = ["tone-success", "tone-warning", "tone-info", "tone-violet"];
const sectionTone = (section: PageSection) => {
  const type = String((section as any)?.type || "");
  let hash = 0;
  for (const char of type) hash = (hash + char.charCodeAt(0)) % sectionTones.length;
  return sectionTones[hash];
};
const sectionIconComponents: Record<string, Component> = {
  image: ImageIcon,
  money: BadgeDollarSignIcon,
  list: ListIcon,
  question: CircleQuestionMarkIcon,
  chat: MessageCircleIcon,
  video: VideoIcon,
  user: UserIcon,
  link: LinkIcon,
  clock: TimerIcon,
  plane: PlaneIcon,
  layout: PanelsTopLeftIcon
};
const sectionIconByType: Record<string, keyof typeof sectionIconComponents> = {
  hero: "image", banner_card: "image", photo: "image", gallery: "image",
  prices: "money", viajeon_checkout: "money",
  itinerary: "list", reasons: "list", story: "list",
  faq: "question", testimonials: "chat", internal_form: "chat",
  featured_video: "video", video_vsl: "video",
  biography: "user", agency_footer: "user", links: "link", cta: "link",
  countdown: "clock", flight_details: "plane"
};
const sectionIcon = (section: PageSection): Component => sectionIconComponents[sectionIconByType[String((section as any)?.type)] || "layout"];
const previewAddressLabel = computed(() => {
  const url = publicUrl.value || "";
  return url ? url.replace(/^https?:\/\//, "") : pageSlug.value || "";
});
const closeTopbarMenu = (event: MouseEvent) => {
  if (!(event.target as HTMLElement | null)?.closest(".ed-menu-wrap")) topbarMenuOpen.value = false;
};
onMounted(() => document.addEventListener("click", closeTopbarMenu));
onBeforeUnmount(() => document.removeEventListener("click", closeTopbarMenu));

const openSectionEditor = (index: number) => {
  const target = sections.value[index];
  if (!target) return;
  if (isLockedFooterSection(target)) return;
  editingSectionIndex.value = index;
  editingSectionDraft.value = clone(target);
  editingSectionOriginalSnapshot.value = sectionDraftSnapshot(editingSectionDraft.value);
};

const forceCloseSectionEditor = () => {
  editingSectionIndex.value = null;
  editingSectionDraft.value = null;
  editingSectionOriginalSnapshot.value = "";
  editingSectionFormRef.value = null;
  sectionModalObservedBodyMax.value = 0;
  sectionModalResizeObserver?.disconnect();
  sectionModalResizeObserver = null;
  unsavedFlightSegmentModal.value.open = false;
  unsavedSectionModal.value.open = false;
  unsavedSectionModal.value.saving = false;
  pendingUnsavedSectionAction = null;
};

const requestUnsavedSectionConfirmation = (action: () => void | Promise<void>) => {
  pendingUnsavedSectionAction = action;
  unsavedSectionModal.value.open = true;
  unsavedSectionModal.value.saving = false;
};

const closeSectionEditor = () => {
  if (!hasUnsavedSectionDraftChanges.value) {
    forceCloseSectionEditor();
    return;
  }
  requestUnsavedSectionConfirmation(() => {
    forceCloseSectionEditor();
  });
};

const requestCloseSectionEditor = () => {
  closeSectionEditor();
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
  refreshPreview(false);
});

watch(colorB, value => {
  theme.value.color2 = value;
  markUnsavedChanges();
  refreshPreview(false);
});

watch(ctaColor, (value, previous) => {
  if (!value) return;
  if (skipCtaWatcher) {
    skipCtaWatcher = false;
    return;
  }
  applyPrimaryToThemeAndSections(previous, value);
  markUnsavedChanges();
  refreshPreview(false);
});

watch(previewDevice, value => {
  editorPrefs.value.previewDevice = value;
});

const measureSectionModalBody = () => {
  const el = sectionModalBodyRef.value;
  if (!el) return;
  const next = Math.ceil(el.scrollHeight);
  if (next > sectionModalObservedBodyMax.value) {
    sectionModalObservedBodyMax.value = next;
  }
};

watch(
  () => isSectionEditorOpen.value,
  async opened => {
    if (!opened) return;
    sectionModalObservedBodyMax.value = 0;
    await nextTick();
    measureSectionModalBody();
    sectionModalResizeObserver?.disconnect();
    if (typeof ResizeObserver !== "undefined" && sectionModalBodyRef.value) {
      sectionModalResizeObserver = new ResizeObserver(() => {
        measureSectionModalBody();
      });
      sectionModalResizeObserver.observe(sectionModalBodyRef.value);
    }
  }
);

const refreshPreview = (immediate = false) => {
  flushPendingSectionUpdates();
  schedulePreviewHydration(immediate);
};

const persistEditingSection = async () => {
  if (editingSectionIndex.value === null || !editingSectionDraft.value) return;
  if (hasPendingImageUploads.value) {
    showSnackbar(viewCopy.feedback.imageUploading);
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
  forceCloseSectionEditor();
  refreshPreview(true);
  await saveConfig();
};

const cancelUnsavedFlightSegmentModal = () => {
  unsavedFlightSegmentModal.value.open = false;
};

const confirmSaveSectionWithUnsavedFlightSegment = async () => {
  unsavedFlightSegmentModal.value.open = false;
  await persistEditingSection();
};

const saveEditingSection = async () => {
  if (typeof editingSectionFormRef.value?.savePendingSegmentDraft === "function") {
    const segmentSaved = await editingSectionFormRef.value.savePendingSegmentDraft();
    if (!segmentSaved) return;
  }
  await persistEditingSection();
};

const cancelUnsavedSectionModal = () => {
  unsavedSectionModal.value.open = false;
  unsavedSectionModal.value.saving = false;
  pendingUnsavedSectionAction = null;
};

const discardUnsavedSectionChanges = async () => {
  const pendingAction = pendingUnsavedSectionAction;
  unsavedSectionModal.value.open = false;
  unsavedSectionModal.value.saving = false;
  pendingUnsavedSectionAction = null;
  if (pendingAction) await pendingAction();
};

const saveUnsavedSectionChanges = async () => {
  if (unsavedSectionModal.value.saving) return;
  unsavedSectionModal.value.saving = true;
  const pendingAction = pendingUnsavedSectionAction;
  await saveEditingSection();
  unsavedSectionModal.value.saving = false;
  unsavedSectionModal.value.open = false;
  pendingUnsavedSectionAction = null;
  if (pendingAction && !isSectionEditorOpen.value) await pendingAction();
};

const requestLeaveWithUnsavedSectionDraft = () => {
  requestUnsavedSectionConfirmation(async () => {
    const target = pendingNavigationPath.value;
    if (!target) return;
    pendingNavigationPath.value = null;
    await router.push(target).catch(() => undefined);
  });
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

const showSnackbar = (text: string) => {
  snackbar.value = { open: true, text };
  setTimeout(() => (snackbar.value.open = false), 3000);
};

/**
 * BLOQUEIO: plano free NÃO pode salvar template.
 * Deve abrir dialog com Fechar / Ver planos.
 */
const saveTemplate = () => {
  // se não logou
  if (!auth.user) {
    errorMessage.value = viewCopy.feedback.templateLoginRequired;
    return;
  }

  // bloqueio do plano free
  const plan = auth.user?.plan || "free";
  if (plan === "free") {
    limitModal.value = {
      open: true,
      message: viewCopy.limitModal.templatePlan
    };
    return;
  }

  const key = templateKey.value;
  if (!key) {
    errorMessage.value = viewCopy.feedback.templateLoginRequired;
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
      errorMessage.value = viewCopy.feedback.templateUnavailable;
      return;
    }

    storage.setItem(key, JSON.stringify(payload));
    message.value = viewCopy.feedback.templateSaved;
    showSnackbar(viewCopy.feedback.templateSavedToast);
  } catch (err) {
    console.error(err);
    errorMessage.value = viewCopy.feedback.templateSaveError;
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
  const agencySlug = currentAgency.value?.slug;
  const slug = pageSlug.value || page.value?.slug;
  if (!slug) return null;
  if (activeCustomDomainUrl.value) return `${activeCustomDomainUrl.value}/${slug}`;
  if (!agencySlug) return null;
  return `${publicSiteBaseUrl}/${agencySlug}/${slug}`;
});

const goPages = () => {
  router.push({ name: "pages" });
};

const goLeads = () => {
  router.push({ name: "leads" });
};

const goIntegrations = () => {
  router.push({ name: "integrations-tracking" });
};

const goViajeonIntegration = () => {
  closeSectionPicker();
  router.push({ name: "integrations-viajeon" });
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
  await agencyStore.loadPrimaryDomain(currentAgency.value?.id ?? null);
  applyAgencyBranding();
  await Promise.all([
    loadPixels(),
    loadViajeonStatus(),
    leadCaptureStore.fetchForms().catch(() => undefined)
  ]);

  await fetchPage();
  await loadAiAssistantHistory();
  sectionCatalog.value = sectionTypes
    .map(type => ({
    type,
    label: sectionLabels[type] || type,
    description: type === "viajeon_checkout" && !viajeonConnected.value
      ? "Conecte sua conta ViajeOn para adicionar esta seção."
      : sectionDescriptions[type] || catalogFallbackDescription,
    accent: sectionAccents[type] || "from-slate-100 to-white",
    previewSection: buildCatalogPreview(type),
    thumbnail: sectionThumbnails[type]
    }));
  previewReady.value = true;
  schedulePreviewHydration(true);
});
</script>

<style scoped>
.page-editor-overlay {
  background-color: #05070f80;
}

.catalog-info-tooltip {
  position: relative;
  display: inline-grid;
  height: 22px;
  width: 22px;
  place-items: center;
  border: 1px solid rgb(148 163 184 / 0.55);
  border-radius: 9999px;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  cursor: help;
}

.catalog-info-tooltip::after {
  position: absolute;
  z-index: 20;
  top: calc(100% + 8px);
  right: 0;
  width: 220px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #0f172a;
  color: white;
  content: attr(data-tooltip);
  font-size: 11px;
  font-weight: 500;
  line-height: 1.4;
  text-align: left;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-3px);
  transition: opacity .15s, transform .15s;
}

.catalog-info-tooltip:hover::after,
.catalog-info-tooltip:focus::after {
  opacity: 1;
  transform: translateY(0);
}

@media (min-width: 768px) {
  .editor-workspace.ai-assistant-open {
    padding-right: 0;
  }
}

.ai-sidebar-slide-enter-active,
.ai-sidebar-slide-leave-active {
  transform-origin: right center;
  will-change: transform, opacity;
  transition: opacity 0.26s ease, transform 0.26s ease;
}

.ai-sidebar-slide-enter-from,
.ai-sidebar-slide-leave-to {
  opacity: 0;
  transform: scaleX(0.94);
}

.ai-sidebar-slide-enter-to,
.ai-sidebar-slide-leave-from {
  opacity: 1;
  transform: scaleX(1);
}

.editor-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 4px 0;
}

.editor-topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.editor-back-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid #e5ece6;
  background: #f4f7f4;
  color: #748c7f;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.editor-breadcrumb {
  font-size: 12px;
  color: #8aa693;
  font-weight: 600;
  white-space: nowrap;
}

.editor-divider {
  color: #a7b8ad;
  font-weight: 700;
}

.editor-page-title {
  font-size: 26px;
  line-height: 1;
  font-weight: 800;
  color: #1c2c22;
  white-space: nowrap;
}

.editor-topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.editor-topbar-actions-mobile {
  display: none;
}

  .editor-ai-sidebar {
    position: fixed;
    top: 93px;
    right: 24px;
    bottom: 16px;
    width: 29rem;
  max-width: calc(100vw - 48px);
  z-index: 60;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid #d9e6dc;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: none;
  padding: 18px;
  backdrop-filter: blur(14px);
  overflow: hidden;
  box-sizing: border-box;
}

.editor-ai-sidebar-resize-handle {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 12px;
  border: 0;
  padding: 0;
  background: transparent;
  cursor: col-resize;
  touch-action: none;
  z-index: 2;
}

.editor-ai-sidebar-resize-grip {
  position: absolute;
  top: 50%;
  left: 4px;
  width: 2px;
  height: 36px;
  border-radius: 999px;
  transform: translateY(-50%);
  background: rgba(61, 204, 95, 0.34);
  box-shadow:
    4px 0 0 rgba(61, 204, 95, 0.2),
    -4px 0 0 rgba(61, 204, 95, 0.2);
}

.editor-ai-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(217, 230, 220, 0.85);
}

.editor-ai-sidebar-header-copy {
  flex: 1;
  min-width: 0;
}

.editor-ai-sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.editor-ai-sidebar-logo {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  object-fit: contain;
}

.editor-ai-sidebar-eyebrow {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #63a275;
}

.editor-ai-sidebar-title {
  margin-top: 0;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.05;
  color: #0f172a;
}

.editor-ai-sidebar-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
  min-width: 0;
}

.editor-ai-sidebar-usage-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid #bfe7c7;
  background: #eaf8ee;
  color: #24703b;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  white-space: nowrap;
  margin-left: auto;
  transform: translateY(-5px);
}

.editor-ai-sidebar-close {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  border: 1px solid #d8e3db;
  background: #f7faf8;
  color: #45624f;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transform: translateY(-5px);
}

.editor-ai-sidebar-cta {
  border: 1px solid #35bd57;
  border-radius: 20px;
  background: #3dcc5f;
  color: #ffffff;
  font-size: 16px;
  line-height: 1.5;
  font-weight: 700;
  text-align: center;
  padding: 18px 20px;
  width: min(100%, 280px);
  margin: 0 auto;
  display: block;
  transition: transform 0.15s ease, border-color 0.15s ease, background-color 0.15s ease;
}

.editor-ai-sidebar-cta:hover {
  background: #5be07a;
  border-color: #2fa84f;
  transform: translateY(-1px);
}

.editor-ai-sidebar-cta.is-active {
  border-color: #2fa84f;
  background: #48d766;
}

.editor-ai-sidebar-chat {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editor-ai-sidebar-base-action {
  display: flex;
  justify-content: center;
}

.editor-ai-sidebar-base-button {
  border-radius: 999px;
  border: 1px solid #35bd57;
  background: #f0fff4;
  color: #0f7a36;
  font-size: 13px;
  font-weight: 700;
  padding: 10px 16px;
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    opacity 0.2s ease,
    transform 0.2s ease;
}

.editor-ai-sidebar-base-button:hover:not(:disabled) {
  background: #dff8e7;
  transform: translateY(-1px);
}

.editor-ai-sidebar-base-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.editor-ai-sidebar-chat-log {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  border: 0;
  border-radius: 0;
  background: transparent;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  gap: 12px;
}

  .editor-ai-sidebar-bubble {
  width: fit-content;
  max-width: 88%;
  border-radius: 18px;
  padding: 12px 14px;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.editor-ai-sidebar-bubble.is-user {
  margin-left: auto;
  background: #111111;
  color: #ffffff;
}

.editor-ai-sidebar-bubble.is-assistant {
  margin-right: auto;
  background: #f8fbf9;
  border: 1px solid #d9e6dc;
  color: #344054;
}

.editor-ai-sidebar-bubble.is-user .editor-ai-sidebar-response-text {
  color: #ffffff;
}

.editor-ai-sidebar-bubble.is-assistant .editor-ai-sidebar-response-text {
  color: #344054;
}

.editor-ai-sidebar-response-text {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.65;
  color: #344054;
  width: 100%;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.editor-ai-sidebar-composer {
  border-top: 1px solid rgba(217, 230, 220, 0.85);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.editor-ai-sidebar-composer-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.editor-ai-sidebar-icon-button {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  border: 1px solid #d8e3db;
  background: #f7faf8;
  color: #45624f;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  transition: background-color 0.15s ease, transform 0.15s ease, opacity 0.15s ease;
}

.editor-ai-sidebar-icon-button:hover:not(:disabled) {
  background: #eef5ef;
  transform: translateY(-1px);
}

.editor-ai-sidebar-icon-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.editor-ai-sidebar-attach-count {
  min-width: 26px;
  height: 26px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(61, 204, 95, 0.12);
  border: 1px solid rgba(61, 204, 95, 0.2);
  color: #2d7f44;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex: 0 0 auto;
}

.editor-ai-sidebar-input {
  width: 100%;
  min-width: 0;
  min-height: 42px;
  max-height: 220px;
  border-radius: 0;
  border: 1px solid #d9e6dc;
  background: #ffffff;
  padding: 11px 14px;
  font-size: 14px;
  line-height: 1.35;
  color: #0f172a;
  outline: none;
  resize: vertical;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  flex: 1 1 auto;
}

.editor-ai-sidebar-input-shell {
  width: 100%;
  min-width: 0;
}

.editor-ai-sidebar-input:focus {
  border-color: #35bd57;
  box-shadow: 0 0 0 3px rgba(61, 204, 95, 0.12);
}

.editor-ai-sidebar-send {
  border-color: #35bd57;
  background: #3dcc5f;
  color: #ffffff;
}

.editor-ai-sidebar-send:hover:not(:disabled) {
  background: #5be07a;
  transform: translateY(-1px);
}

.editor-ai-sidebar-send svg {
  margin-left: 1px;
}

.editor-ai-sidebar-typing {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 44px;
}

.editor-ai-sidebar-typing span {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #41ce5f;
  animation: editorAiTyping 1s infinite ease-in-out;
}

.editor-ai-sidebar-typing span:nth-child(2) {
  animation-delay: 0.15s;
}

.editor-ai-sidebar-typing span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes editorAiTyping {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.45;
  }
  40% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

@media (max-width: 767px) {
  .editor-topbar-actions {
    display: none !important;
  }

  .editor-topbar-actions-mobile {
    display: block;
    width: 100%;
  }
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #39b857;
}

.editor-accordion-trigger {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #d9e2dc;
  border-radius: 12px;
  background: #fff;
  padding: 10px 14px;
  text-align: left;
}

.form-card {
  width: 100%;
  border-radius: 1.25rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background-color: #ffffff;
  padding: 1rem 1.25rem;
  text-align: left;
  transition: border-color 0.2s ease;
}
.form-card:hover {
  border-color: rgba(59, 130, 246, 0.4);
}
.form-card--selected {
  border-color: rgba(34, 197, 94, 0.6);
  background-color: #ffffff;
}
.badge-success {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  padding: 0.15rem 0.75rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #065f46;
  background-color: rgba(16, 185, 129, 0.12);
}
:global(.dark-theme) .badge-success,
:global(.dark) .badge-success {
  color: #d1fae5;
  background-color: rgba(16, 185, 129, 0.3);
}
.preview-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  padding: 0.25rem 0.9rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background-color: #f1f5f9;
  color: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.4);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.editor-settings-shell {
  background: #ffffff;
}

.editor-side-tab {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 13px 16px;
  text-align: left;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: #0f172a;
  background: #eef2f5;
  transition: all 0.2s ease;
}

.editor-side-tab-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  color: #0f172a;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  flex-shrink: 0;
}
.editor-side-tab-step svg{
  width:18px;
  height:18px;
  fill:none;
  stroke:currentColor;
  stroke-width:2;
  stroke-linecap:round;
  stroke-linejoin:round;
}
.editor-side-tab-step .editor-settings-gear{
  fill:currentColor;
  stroke:none;
  transform: scale(1.12);
  transform-origin: center;
}

.editor-side-tab-step .editor-colors-palette{
  fill:currentColor;
  stroke:none;
}
.editor-side-tab-step .editor-colors-palette path,
.editor-side-tab-step .editor-colors-palette circle{
  stroke:none;
}
.editor-side-tab-step .editor-capture-leads{
  fill:currentColor;
  stroke:none;
}
.editor-side-tab-step .editor-capture-leads path{
  stroke:none;
}

.editor-side-tab.active {
  background: #3dd463;
  border-color: #3dd463;
  color: #062710;
  box-shadow: 0 10px 24px rgba(61, 212, 99, 0.28);
}

.editor-side-tab.active .editor-side-tab-step {
  color: #062710;
}

.color-chip {
  width: 30px;
  height: 30px;
  padding: 0;
  border: 0;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
}

.color-chip::-webkit-color-swatch-wrapper {
  padding: 0;
  border-radius: 8px;
}

.color-chip::-webkit-color-swatch {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

.color-chip::-moz-color-swatch {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

@media (max-width: 767px) {
  .settings-panel {
    height: auto !important;
  }

.settings-panel-content {
    height: auto !important;
    min-height: 0 !important;
    overflow: visible !important;
    padding-right: 0 !important;
  }
}

@media (min-width: 768px) {
  .settings-colors-grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  }
}

.preview-pill:hover {
  background-color: #e2e8f0;
}
:global(.dark-theme) .preview-pill,
:global(.dark) .preview-pill {
  background-color: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
  border-color: rgba(255, 255, 255, 0.2);
}
:global(.dark-theme) .preview-pill:hover,
:global(.dark) .preview-pill:hover {
  background-color: rgba(255, 255, 255, 0.15);
}
:global(.dark-theme .preview-light .bg-white),
:global(.dark .preview-light .bg-white) {
  background-color: #ffffff !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/90),
:global(.dark .preview-light .bg-white\/90) {
  background-color: rgba(255, 255, 255, 0.9) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/80),
:global(.dark .preview-light .bg-white\/80) {
  background-color: rgba(255, 255, 255, 0.8) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/70),
:global(.dark .preview-light .bg-white\/70) {
  background-color: rgba(255, 255, 255, 0.7) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/60),
:global(.dark .preview-light .bg-white\/60) {
  background-color: rgba(255, 255, 255, 0.6) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/50),
:global(.dark .preview-light .bg-white\/50) {
  background-color: rgba(255, 255, 255, 0.5) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/40),
:global(.dark .preview-light .bg-white\/40) {
  background-color: rgba(255, 255, 255, 0.4) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/30),
:global(.dark .preview-light .bg-white\/30) {
  background-color: rgba(255, 255, 255, 0.3) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/20),
:global(.dark .preview-light .bg-white\/20) {
  background-color: rgba(255, 255, 255, 0.2) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/10),
:global(.dark .preview-light .bg-white\/10) {
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-white\/5),
:global(.dark .preview-light .bg-white\/5) {
  background-color: rgba(255, 255, 255, 0.05) !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .bg-slate-50),
:global(.dark .preview-light .bg-slate-50),
:global(.dark-theme .preview-light .bg-slate-100),
:global(.dark .preview-light .bg-slate-100),
:global(.dark-theme .preview-light .bg-slate-200),
:global(.dark .preview-light .bg-slate-200),
:global(.dark-theme .preview-light .bg-gray-50),
:global(.dark .preview-light .bg-gray-50) {
  background-color: #f8fafc !important;
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .text-slate-900),
:global(.dark .preview-light .text-slate-900),
:global(.dark-theme .preview-light .text-slate-800),
:global(.dark .preview-light .text-slate-800),
:global(.dark-theme .preview-light .text-slate-700),
:global(.dark .preview-light .text-slate-700) {
  color: #0f172a !important;
}
:global(.dark-theme .preview-light .text-slate-600),
:global(.dark .preview-light .text-slate-600),
:global(.dark-theme .preview-light .text-slate-500),
:global(.dark .preview-light .text-slate-500),
:global(.dark-theme .preview-light .text-slate-400),
:global(.dark .preview-light .text-slate-400) {
  color: #475569 !important;
}
:global(.dark-theme .preview-light .border-slate-100),
:global(.dark .preview-light .border-slate-100),
:global(.dark-theme .preview-light .border-slate-200),
:global(.dark .preview-light .border-slate-200),
:global(.dark-theme .preview-light .border-slate-300),
:global(.dark .preview-light .border-slate-300) {
  border-color: #e2e8f0 !important;
}
.preview-toolbar button {
  color: #ffffff !important;
}
.preview-toolbar button * {
  color: inherit !important;
  stroke: currentColor !important;
}
.preview-toolbar button:disabled {
  opacity: 0.65 !important;
  cursor: not-allowed !important;
}


:deep(.preview-section-host > *) {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

:deep(.overlay-action-button svg) {
  color: inherit !important;
  stroke: currentColor !important;
}
:deep(.overlay-action-button svg *) {
  color: inherit !important;
  stroke: currentColor !important;
  fill: none !important;
}

@media (max-width: 768px) {
  .page-editor-view aside.space-y-3 {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
  }
  .page-editor-view aside.space-y-3 > :not([hidden]) ~ :not([hidden]) {
    margin-top: 0 !important;
  }

  .page-editor-view aside.space-y-3 .editor-side-tab {
    justify-content: center;
    width: 100%;
    height: 44px;
    min-height: 44px;
    padding: 0;
    box-sizing: border-box;
  }

  .page-editor-view aside.space-y-3 .editor-side-tab.active {
    box-shadow: none;
  }

  .page-editor-view aside.space-y-3 .editor-side-tab > span:last-child {
    display: none;
  }

  .editor-settings-title {
    font-size: 18px !important;
    line-height: 1.15 !important;
    white-space: nowrap;
  }

  .page-editor-view {
    font-size: 12px;
  }

  .editor-settings-shell {
    font-size: 12px;
  }

  .page-editor-view,
  .editor-settings-shell,
  .settings-panel,
  .settings-panel-content {
    min-width: 0;
    max-width: 100%;
    overflow-x: hidden;
  }

  .editor-topbar {
    align-items: flex-start;
    gap: 8px;
  }

  .editor-topbar-left {
    width: 100%;
    min-width: 0;
  }

  .editor-breadcrumb {
    display: inline;
    font-size: 12px;
    white-space: nowrap;
  }

  .editor-divider {
    display: inline;
  }

  .editor-page-title {
    font-size: 20px;
    line-height: 1.15;
    flex: 1 1 auto;
    min-width: 0;
    white-space: normal;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow-wrap: anywhere;
  }

  :global(.page-editor-view input),
  :global(.page-editor-view textarea),
  :global(.page-editor-view select) {
    font-size: 16px;
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
  }

  .slug-row {
    min-width: 0;
    max-width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 40%) minmax(0, 60%);
  }

  .slug-prefix {
    max-width: 100%;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .slug-input {
    min-width: 0 !important;
    width: 100%;
    max-width: 100%;
    font-size: 15px;
  }

  .settings-panel textarea {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box;
    overflow-wrap: anywhere;
    word-break: break-word;
    padding-left: 12px !important;
    padding-right: 12px !important;
    font-size: 15px !important;
    line-height: 1.4 !important;
  }

  .editor-side-tab {
    font-size: 12px;
    min-width: 0;
    overflow: hidden;
  }

  .editor-ai-fab {
    position: fixed;
    top: 180px;
    right: 0;
    z-index: 62;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    transform: none;
    border-radius: 16px 0 0 16px;
    box-shadow: 0 14px 32px rgba(15, 23, 42, 0.18);
    min-width: 52px;
    padding: 13px 9px;
  }

  .editor-ai-fab-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
  }

  .editor-ai-fab-label {
      color: #ffffff;
      font-size: 11px;
      font-weight: 800;
      line-height: 1;
      text-transform: uppercase;
      white-space: nowrap;
      letter-spacing: 0.08em;
    }

  .editor-side-tab-step {
    width: 19px;
    height: 19px;
    font-size: 10px;
  }

  .editor-side-tab > span:last-child {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

@media (max-width: 420px) {
  .slug-prefix {
    max-width: 100%;
    padding-left: 10px;
    padding-right: 10px;
    font-size: 13px;
  }

  .slug-input {
    min-width: 0 !important;
    width: 100%;
  }
}
</style>













<style scoped>
.page-editor-view {
  color: var(--foreground);
}

.editor-settings-shell,
.editor-preview-shell {
  border-color: var(--border) !important;
  background: var(--card) !important;
  color: var(--card-foreground);
}

.editor-settings-title {
  color: var(--foreground) !important;
}

.editor-settings-shell .editor-side-tab {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}

.editor-settings-shell .editor-side-tab:hover {
  border-color: color-mix(in srgb, var(--primary) 34%, var(--border));
  background: var(--accent);
}

.editor-settings-shell .editor-side-tab.active {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-foreground);
  box-shadow: 0 10px 24px color-mix(in srgb, var(--primary) 22%, transparent);
}

.editor-settings-shell .editor-side-tab-step,
.editor-settings-shell .editor-side-tab.active .editor-side-tab-step {
  color: inherit;
}

.editor-settings-shell .settings-panel {
  border-color: color-mix(in srgb, var(--border) 58%, transparent) !important;
  background: var(--background) !important;
}

.editor-settings-shell .slug-row {
  border-color: var(--input) !important;
  background: var(--background);
}

.editor-settings-shell .slug-prefix {
  border-color: var(--input) !important;
  background: var(--muted) !important;
  color: var(--muted-foreground) !important;
}

.editor-preview-shell > .mt-4 {
  overflow: hidden;
  border-radius: var(--radius-xl);
  background: var(--background);
}

.editor-preview-shell .preview-light {
  background: var(--background);
}

.editor-topbar {
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--card);
  padding: 10px 12px;
  color: var(--card-foreground);
  box-shadow: var(--shadow-soft);
}

.editor-back-btn {
  border-color: var(--border);
  background: var(--muted);
  color: var(--muted-foreground);
}

.editor-back-btn:hover {
  background: var(--accent);
  color: var(--foreground);
}

.editor-breadcrumb,
.editor-divider {
  color: var(--muted-foreground);
}

.editor-page-title {
  color: var(--foreground);
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 650;
}

.editor-dialog-shell {
  border: 1px solid var(--border);
  border-radius: var(--radius-2xl);
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-elegant);
}

.editor-dialog-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 650;
  line-height: 1.2;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease, filter 0.15s ease;
}

.editor-dialog-action--neutral {
  border-color: var(--border);
  background: transparent;
  color: var(--foreground);
}

.editor-dialog-action--neutral:hover {
  border-color: color-mix(in srgb, var(--foreground) 20%, var(--border));
  background: var(--accent);
  color: var(--accent-foreground);
}

.editor-dialog-action--danger {
  border-color: color-mix(in srgb, var(--destructive) 35%, var(--border));
  background: color-mix(in srgb, var(--destructive) 10%, var(--card));
  color: var(--destructive);
}

.editor-dialog-action--danger:hover {
  border-color: color-mix(in srgb, var(--destructive) 58%, var(--border));
  background: color-mix(in srgb, var(--destructive) 18%, var(--card));
  color: var(--destructive);
}

.editor-dialog-action--primary {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-foreground);
  box-shadow: var(--shadow-soft);
}

.editor-dialog-action--primary:hover {
  filter: brightness(0.94);
}

.editor-dialog-action:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.editor-dialog-shell :deep(.text-slate-900),
.editor-dialog-shell :deep(.text-slate-800),
.editor-dialog-shell :deep(.text-slate-700),
.editor-settings-shell :deep(.text-slate-900),
.editor-settings-shell :deep(.text-slate-800),
.editor-settings-shell :deep(.text-slate-700) {
  color: var(--foreground) !important;
}

.editor-dialog-shell :deep(.text-slate-600),
.editor-dialog-shell :deep(.text-slate-500),
.editor-dialog-shell :deep(.text-slate-400),
.editor-settings-shell :deep(.text-slate-600),
.editor-settings-shell :deep(.text-slate-500),
.editor-settings-shell :deep(.text-slate-400) {
  color: var(--muted-foreground) !important;
}

.editor-dialog-shell :deep(.border-slate-100),
.editor-dialog-shell :deep(.border-slate-200),
.editor-dialog-shell :deep(.border-slate-300),
.editor-settings-shell :deep(.border-slate-100),
.editor-settings-shell :deep(.border-slate-200),
.editor-settings-shell :deep(.border-slate-300) {
  border-color: var(--border) !important;
}

.editor-dialog-shell :deep(.bg-white),
.editor-settings-shell :deep(.bg-white) {
  background-color: var(--card) !important;
}

.editor-dialog-shell :deep(.bg-slate-50),
.editor-dialog-shell :deep(.bg-slate-100),
.editor-settings-shell :deep(.bg-slate-50) {
  background-color: var(--muted) !important;
}

.editor-dialog-shell :deep(input),
.editor-dialog-shell :deep(textarea),
.editor-dialog-shell :deep(select),
.editor-settings-shell :deep(input),
.editor-settings-shell :deep(textarea),
.editor-settings-shell :deep(select) {
  border-color: var(--input) !important;
  background: var(--background) !important;
  color: var(--foreground) !important;
}

.editor-settings-shell :deep(.settings-panel) {
  border-color: color-mix(in srgb, var(--border) 58%, transparent) !important;
  background: var(--background);
}

.editor-ai-sidebar {
  border-color: var(--border);
  background: color-mix(in srgb, var(--card) 96%, transparent);
  color: var(--card-foreground);
  box-shadow: none;
}

.editor-ai-sidebar-header,
.editor-ai-sidebar-composer {
  border-color: color-mix(in srgb, var(--border) 42%, transparent);
}

.editor-ai-sidebar-title,
.editor-ai-sidebar-response-text {
  color: var(--foreground);
}

.editor-ai-sidebar-usage-pill {
  border-color: color-mix(in srgb, var(--primary) 25%, var(--border));
  background: color-mix(in srgb, var(--primary) 10%, var(--card));
  color: var(--primary);
}

.editor-ai-sidebar-close,
.editor-ai-sidebar-icon-button {
  border-color: var(--border);
  background: var(--muted);
  color: var(--muted-foreground);
}

.editor-ai-sidebar-bubble.is-user {
  background: var(--primary);
  color: var(--primary-foreground);
}

.editor-ai-sidebar-bubble.is-assistant {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}

.editor-ai-sidebar-bubble.is-assistant .editor-ai-sidebar-response-text {
  color: var(--foreground);
}

.editor-ai-sidebar-input {
  border-color: var(--input);
  background: var(--background);
  color: var(--foreground);
}

.editor-ai-sidebar-send {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-foreground);
}

.overlay-label {
  color: #ffffff !important;
}

.editor-ai-fab,
.editor-ai-fab-icon,
.editor-ai-fab-label {
  color: #ffffff !important;
}

.section-editor-header,
.section-editor-footer {
  border-color: color-mix(in srgb, var(--border) 62%, transparent) !important;
  background: var(--card);
}

.section-editor-body {
  border-color: color-mix(in srgb, var(--border) 62%, transparent) !important;
  background: var(--background) !important;
  color: var(--foreground);
}

.section-editor-dialog {
  width: min(72.8rem, calc(100vw - 2rem));
  max-width: min(72.8rem, calc(100vw - 2rem));
}

@media (min-width: 901px) {
  .section-editor-body :deep(.hero-proto-body),
  .section-editor-body :deep(.cta-proto-body),
  .section-editor-body :deep(.faq-proto-body),
  .section-editor-body :deep(.featured-video-proto-body),
  .section-editor-body :deep(.footer-proto-body),
  .section-editor-body :deep(.photo-proto-body),
  .section-editor-body :deep(.prices-proto-body),
  .section-editor-body :deep(.items-proto-body),
  .section-editor-body :deep(.testimonials-proto-body),
  .section-editor-body :deep(.banner-form-shell),
  .section-editor-body :deep(.bio-form-shell),
  .section-editor-body :deep(.countdown-shell),
  .section-editor-body :deep(.flight-shell),
  .section-editor-body :deep(.itinerary-shell),
  .section-editor-body :deep(.story-form-shell),
  .section-editor-body :deep(.links-editor),
  .section-editor-body :deep(.header-editor),
  .section-editor-body :deep(.section-editor),
  .section-editor-body :deep(.viajeon-form-shell) {
    grid-template-columns: 267px minmax(0, 1fr) !important;
  }
}

/* Mantém o formulário VSL íntegro dentro do modal, inclusive após carregamento assíncrono. */
.section-editor-body :deep(.video-vsl-form) {
  display: grid !important;
  grid-template-columns: 267px minmax(0, 1fr) !important;
  min-height: 100% !important;
  align-items: stretch !important;
}

.section-editor-body :deep(.video-vsl-form > .tabs) {
  display: flex !important;
  flex-direction: column !important;
  gap: 8px !important;
  padding: 16px 12px !important;
  border-right: 1px solid var(--border) !important;
}

.section-editor-body :deep(.video-vsl-form .tab) {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  padding: 8px 10px !important;
  border-radius: 14px !important;
}

.section-editor-body :deep(.video-vsl-form .content-area) {
  display: grid !important;
  align-content: start !important;
  gap: 12px !important;
  padding: 14px 16px !important;
}

.section-editor-body :deep(.video-vsl-form .field) {
  display: grid !important;
  gap: 6px !important;
}

.section-editor-body :deep(.video-vsl-form .field > label) {
  display: flex !important;
}

.section-editor-body :deep(.video-vsl-form .field > input),
.section-editor-body :deep(.video-vsl-form .field > select) {
  display: block !important;
  width: 100% !important;
  min-height: 40px !important;
  padding: 9px 12px !important;
  border: 1px solid var(--input) !important;
  border-radius: 12px !important;
}

.section-editor-body :deep(.video-vsl-form .grid-2) {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 10px !important;
}

.section-editor-body :deep(.video-vsl-form .choice-grid) {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 8px !important;
}

@media (max-width: 900px) {
  .section-editor-body :deep(.video-vsl-form) { grid-template-columns: 1fr !important; }
  .section-editor-body :deep(.video-vsl-form > .tabs) { flex-direction: row !important; border-right: 0 !important; border-bottom: 1px solid var(--border) !important; }
  .section-editor-body :deep(.video-vsl-form .tab) { flex: 1 !important; }
  .section-editor-body :deep(.video-vsl-form .grid-2),
  .section-editor-body :deep(.video-vsl-form .choice-grid) { grid-template-columns: 1fr !important; }
}

.section-editor-body :deep(.hero-proto-body),
.section-editor-body :deep(.cta-proto-body),
.section-editor-body :deep(.faq-proto-body),
.section-editor-body :deep(.featured-video-proto-body),
.section-editor-body :deep(.footer-proto-body),
.section-editor-body :deep(.photo-proto-body),
.section-editor-body :deep(.prices-proto-body),
.section-editor-body :deep(.items-proto-body),
.section-editor-body :deep(.testimonials-proto-body),
.section-editor-body :deep(.banner-form-shell),
.section-editor-body :deep(.bio-form-shell),
.section-editor-body :deep(.countdown-shell),
.section-editor-body :deep(.flight-shell),
.section-editor-body :deep(.itinerary-shell),
.section-editor-body :deep(.story-form-shell) {
  background: var(--background) !important;
  color: var(--foreground);
}

.section-editor-body :deep(.tabs),
.section-editor-body :deep(.banner-form-nav),
.section-editor-body :deep(.bio-form-nav),
.section-editor-body :deep(.countdown-nav),
.section-editor-body :deep(.flight-nav),
.section-editor-body :deep(.itinerary-nav),
.section-editor-body :deep(.story-form-nav) {
  border-color: color-mix(in srgb, var(--border) 62%, transparent) !important;
  background: var(--card) !important;
}

.section-editor-body :deep(.tab),
.section-editor-body :deep(.banner-nav-item),
.section-editor-body :deep(.bio-nav-item),
.section-editor-body :deep(.countdown-nav-item),
.section-editor-body :deep(.flight-nav-item),
.section-editor-body :deep(.itinerary-nav-item),
.section-editor-body :deep(.story-nav-item) {
  border-color: var(--border) !important;
  background: var(--muted) !important;
  color: var(--foreground) !important;
  box-shadow: none !important;
}

.section-editor-body :deep(.tab:hover),
.section-editor-body :deep(.banner-nav-item:hover),
.section-editor-body :deep(.bio-nav-item:hover),
.section-editor-body :deep(.countdown-nav-item:hover),
.section-editor-body :deep(.flight-nav-item:hover),
.section-editor-body :deep(.itinerary-nav-item:hover),
.section-editor-body :deep(.story-nav-item:hover) {
  border-color: color-mix(in srgb, var(--primary) 32%, var(--border)) !important;
  background: var(--accent) !important;
}

.section-editor-body :deep(.tab.active),
.section-editor-body :deep(.banner-nav-item.active),
.section-editor-body :deep(.bio-nav-item.active),
.section-editor-body :deep(.countdown-nav-item.active),
.section-editor-body :deep(.flight-nav-item.active),
.section-editor-body :deep(.itinerary-nav-item.active),
.section-editor-body :deep(.story-nav-item.active) {
  border-color: var(--primary) !important;
  background: var(--primary) !important;
  color: var(--primary-foreground) !important;
}

.section-editor-body :deep(.tab-icon),
.section-editor-body :deep(.banner-nav-icon),
.section-editor-body :deep(.bio-nav-icon),
.section-editor-body :deep(.countdown-nav-icon),
.section-editor-body :deep(.flight-nav-icon),
.section-editor-body :deep(.itinerary-nav-icon),
.section-editor-body :deep(.story-nav-icon) {
  background: color-mix(in srgb, var(--card) 84%, transparent) !important;
  color: inherit !important;
}

.section-editor-body :deep(.tab small),
.section-editor-body :deep(.banner-nav-item small),
.section-editor-body :deep(.bio-nav-item small),
.section-editor-body :deep(.story-nav-item small) {
  color: var(--muted-foreground) !important;
}

.section-editor-body :deep(.tab.active small),
.section-editor-body :deep(.banner-nav-item.active small),
.section-editor-body :deep(.bio-nav-item.active small),
.section-editor-body :deep(.story-nav-item.active small) {
  color: color-mix(in srgb, var(--primary-foreground) 72%, transparent) !important;
}

.section-editor-body :deep(.pill.active),
.section-editor-body :deep(.flight-pill.active),
.section-editor-body :deep(.story-pill.active) {
  border-color: var(--primary) !important;
  background: var(--primary) !important;
  color: var(--primary-foreground) !important;
}

.section-editor-body :deep(.tab.active .tab-icon),
.section-editor-body :deep(.banner-nav-item.active .banner-nav-icon),
.section-editor-body :deep(.bio-nav-item.active .bio-nav-icon),
.section-editor-body :deep(.countdown-nav-item.active .countdown-nav-icon),
.section-editor-body :deep(.flight-nav-item.active .flight-nav-icon),
.section-editor-body :deep(.itinerary-nav-item.active .itinerary-nav-icon),
.section-editor-body :deep(.story-nav-item.active .story-nav-icon) {
  border-color: color-mix(in srgb, var(--primary-foreground) 28%, transparent) !important;
  background: color-mix(in srgb, var(--primary-foreground) 16%, transparent) !important;
  color: var(--primary-foreground) !important;
}

.section-editor-body :deep(.tab.active .tab-icon svg),
.section-editor-body :deep(.banner-nav-item.active .banner-nav-icon svg),
.section-editor-body :deep(.bio-nav-item.active .bio-nav-icon svg),
.section-editor-body :deep(.countdown-nav-item.active .countdown-nav-icon svg),
.section-editor-body :deep(.flight-nav-item.active .flight-nav-icon svg),
.section-editor-body :deep(.itinerary-nav-item.active .itinerary-nav-icon svg),
.section-editor-body :deep(.story-nav-item.active .story-nav-icon svg) {
  color: var(--primary-foreground) !important;
  fill: none;
  stroke: currentColor !important;
}

.section-editor-body :deep(.tab.active .tab-icon svg [fill]:not([fill="none"])),
.section-editor-body :deep(.banner-nav-item.active .banner-nav-icon svg [fill]:not([fill="none"])),
.section-editor-body :deep(.bio-nav-item.active .bio-nav-icon svg [fill]:not([fill="none"])),
.section-editor-body :deep(.countdown-nav-item.active .countdown-nav-icon svg [fill]:not([fill="none"])),
.section-editor-body :deep(.flight-nav-item.active .flight-nav-icon svg [fill]:not([fill="none"])),
.section-editor-body :deep(.itinerary-nav-item.active .itinerary-nav-icon svg [fill]:not([fill="none"])),
.section-editor-body :deep(.story-nav-item.active .story-nav-icon svg [fill]:not([fill="none"])) {
  fill: currentColor !important;
}

.section-editor-body :deep(.tab.active .tab-icon svg [stroke]),
.section-editor-body :deep(.banner-nav-item.active .banner-nav-icon svg [stroke]),
.section-editor-body :deep(.bio-nav-item.active .bio-nav-icon svg [stroke]),
.section-editor-body :deep(.countdown-nav-item.active .countdown-nav-icon svg [stroke]),
.section-editor-body :deep(.flight-nav-item.active .flight-nav-icon svg [stroke]),
.section-editor-body :deep(.itinerary-nav-item.active .itinerary-nav-icon svg [stroke]),
.section-editor-body :deep(.story-nav-item.active .story-nav-icon svg [stroke]) {
  stroke: currentColor !important;
}

.section-editor-body :deep(.editor),
.section-editor-body :deep(.banner-form-content),
.section-editor-body :deep(.bio-form-content),
.section-editor-body :deep(.countdown-content),
.section-editor-body :deep(.flight-content),
.section-editor-body :deep(.itinerary-content),
.section-editor-body :deep(.story-form-content),
.section-editor-body :deep(.section-card) {
  background: var(--background) !important;
  color: var(--foreground);
}

.section-editor-body :deep(.section-head) {
  border-color: color-mix(in srgb, var(--border) 58%, transparent) !important;
}

.section-editor-body :deep(.section-title),
.section-editor-body :deep(.banner-form-title),
.section-editor-body :deep(.bio-form-title),
.section-editor-body :deep(.countdown-title),
.section-editor-body :deep(.flight-title),
.section-editor-body :deep(.story-form-title) {
  color: var(--foreground) !important;
  font-family: var(--font-display);
}

.section-editor-body :deep(.section-desc),
.section-editor-body :deep(.banner-form-subtitle),
.section-editor-body :deep(.bio-form-subtitle),
.section-editor-body :deep(.countdown-subtitle),
.section-editor-body :deep(.flight-subtitle),
.section-editor-body :deep(.story-form-subtitle),
.section-editor-body :deep(.bio-hint) {
  color: var(--muted-foreground) !important;
}

.section-editor-body:not(.is-v2-form) :deep(label),
.section-editor-body :deep(.banner-label),
.section-editor-body :deep(.bio-label),
.section-editor-body :deep(.countdown-label),
.section-editor-body :deep(.flight-field-title),
.section-editor-body :deep(.story-label) {
  color: var(--muted-foreground) !important;
}

.section-editor-body:not(.is-v2-form) :deep(input:not([type="checkbox"]):not([type="radio"]):not([type="color"])),
.section-editor-body:not(.is-v2-form) :deep(textarea),
.section-editor-body:not(.is-v2-form) :deep(select),
.section-editor-body :deep(.banner-input),
.section-editor-body :deep(.bio-input),
.section-editor-body :deep(.countdown-input),
.section-editor-body :deep(.flight-input),
.section-editor-body :deep(.story-input) {
  border-color: var(--input) !important;
  background: var(--card) !important;
  color: var(--foreground) !important;
  box-shadow: none;
}

.section-editor-body :deep(input::placeholder),
.section-editor-body :deep(textarea::placeholder) {
  color: color-mix(in srgb, var(--muted-foreground) 72%, transparent) !important;
}

.section-editor-body :deep(input:focus),
.section-editor-body :deep(textarea:focus),
.section-editor-body :deep(select:focus) {
  border-color: var(--ring) !important;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 15%, transparent) !important;
}

.section-editor-body :deep(.help),
.section-editor-body :deep(.hint-dot),
.section-editor-body :deep(.countdown-help),
.section-editor-body :deep(.flight-help) {
  border-color: var(--border) !important;
  background: var(--muted) !important;
  color: var(--muted-foreground) !important;
}

.section-editor-body :deep(.help:hover::after),
.section-editor-body :deep(.hint-help:hover::after),
.section-editor-body :deep(.countdown-help:hover::after),
.section-editor-body :deep(.flight-help:hover::after) {
  border: 1px solid var(--border) !important;
  background: var(--popover) !important;
  color: var(--popover-foreground) !important;
  box-shadow: var(--shadow-elegant) !important;
}

.section-editor-body :deep(.list),
.section-editor-body :deep(.media-item),
.section-editor-body :deep(.highlight-box),
.section-editor-body :deep(.note-box),
.section-editor-body :deep(.info-box),
.section-editor-body :deep(.banner-upload-card),
.section-editor-body :deep(.bio-upload-card),
.section-editor-body :deep(.story-upload-card),
.section-editor-body :deep(.rich-box),
.section-editor-body :deep(.bio-rich-shell),
.section-editor-body :deep(.story-rich-shell) {
  border-color: color-mix(in srgb, var(--border) 72%, transparent) !important;
  background: var(--card) !important;
  color: var(--foreground) !important;
}

.section-editor-body :deep(.note-box),
.section-editor-body :deep(.info-text),
.section-editor-body :deep(.info-list),
.section-editor-body :deep(.media-info p) {
  color: var(--muted-foreground) !important;
}

.section-editor-body :deep(.media-info strong),
.section-editor-body :deep(.info-strong) {
  color: var(--foreground) !important;
}

.section-editor-body :deep(.media-preview) {
  border-color: var(--border) !important;
  background: var(--muted) !important;
  color: var(--muted-foreground) !important;
}

:global(body.admin-body-dark) .editor-ai-fab,
:global(body.admin-body-dark) .editor-ai-fab-icon,
:global(body.admin-body-dark) .editor-ai-fab-label,
:global(html.dark) .editor-ai-fab,
:global(html.dark) .editor-ai-fab-icon,
:global(html.dark) .editor-ai-fab-label {
  color: #000000 !important;
}

/* Redesign: editor de páginas */
.editor-topbar { border-radius: 20px; padding: 10px 12px 10px 10px; box-shadow: var(--shadow-card); }
.editor-back-btn { width: 40px; height: 40px; border-radius: 999px; border: 0; }
.editor-breadcrumb { font-size: 12.5px; font-weight: 500; }
.editor-page-title { font-size: 20px; font-weight: 600; }
.editor-settings-shell { border-radius: 20px !important; box-shadow: var(--shadow-card) !important; border: 0 !important; }
.editor-preview-shell { border-radius: 20px !important; box-shadow: var(--shadow-card) !important; border: 0 !important; }
.editor-settings-title { font-family: var(--font-display); font-size: 22px !important; font-weight: 600 !important; letter-spacing: 0 !important; }
.editor-settings-grid { display: flex; flex-direction: column; gap: 16px; }
.editor-settings-tabs { display: flex; flex-wrap: wrap; gap: 4px; border-bottom: 1px solid var(--border); }
.editor-settings-shell .editor-settings-tabs .editor-side-tab {
  width: auto; margin-bottom: -1px; border: 0; border-bottom: 2px solid transparent; border-radius: 0;
  padding: 10px 14px; background: transparent; box-shadow: none;
  font-size: 13.5px; font-weight: 600; letter-spacing: 0; color: var(--muted-foreground);
}
.editor-settings-shell .editor-settings-tabs .editor-side-tab:hover { background: transparent; color: var(--foreground); }
.editor-settings-shell .editor-settings-tabs .editor-side-tab.active {
  border-bottom-color: var(--primary); background: transparent; box-shadow: none; color: var(--foreground);
}
.editor-settings-shell .editor-settings-tabs .editor-side-tab.active .editor-side-tab-step { color: var(--primary); }
.editor-settings-tabs .editor-side-tab-step, .editor-settings-tabs .editor-side-tab-step svg { width: 16px; height: 16px; }
.editor-settings-shell .settings-panel { border: 0 !important; border-radius: 16px; }
.editor-preview-scale { margin-top: 8px; text-align: right; font-size: 12px; color: var(--muted-foreground); }
.section-editor-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted-foreground); }
.section-editor-title { margin-top: 2px; font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--foreground); }
.section-editor-close { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 999px; background: var(--muted); font-size: 20px; line-height: 1; color: var(--muted-foreground); }
.section-editor-close:hover { background: var(--accent); color: var(--foreground); }
@media (max-width: 640px) {
  .editor-settings-tabs { flex-wrap: nowrap; overflow-x: auto; }
  .editor-settings-shell .editor-settings-tabs .editor-side-tab { flex-shrink: 0; white-space: nowrap; }
}

/* Redesign v2: editor com lista de seções + prévia em moldura */
.ed-topbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.ed-back { display: grid; place-items: center; width: 40px; height: 40px; flex-shrink: 0; border-radius: 999px; background: var(--card); color: var(--muted-foreground); box-shadow: var(--shadow-card); }
.ed-back:hover { color: var(--foreground); }
.ed-back svg { width: 16px; height: 16px; }
.ed-title-block { min-width: 0; flex: 1; }
.ed-crumb { font-size: 12.5px; color: var(--muted-foreground); }
.ed-title-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.ed-title { overflow: hidden; font-family: var(--font-display); font-size: 21px; line-height: 28px; font-weight: 600; white-space: nowrap; text-overflow: ellipsis; color: var(--foreground); }
.ed-pill { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 2px 10px; font-size: 12px; font-weight: 600; }
.ed-pill i { width: 6px; height: 6px; border-radius: 999px; background: currentColor; }
.ed-pill.is-on { background: var(--status-success); color: var(--status-success-foreground); }
.ed-pill.is-off { background: var(--status-warning); color: var(--status-warning-foreground); }
.ed-saved { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--muted-foreground); }
.ed-saved svg { width: 14px; height: 14px; }
.ed-saved i { width: 7px; height: 7px; border-radius: 999px; background: var(--status-warning-foreground); }
.ed-saved.is-dirty { color: var(--status-warning-foreground); }
.ed-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ed-btn { display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 18px; border-radius: 999px; font-size: 13.5px; font-weight: 600; transition: background 0.15s, opacity 0.15s; }
.ed-btn svg { width: 16px; height: 16px; }
.ed-btn:disabled { cursor: not-allowed; opacity: 0.55; }
.ed-btn-ai { background: var(--status-violet); color: var(--status-violet-foreground); }
.ed-btn-ghost { background: var(--card); color: var(--foreground); box-shadow: var(--shadow-card); }
.ed-btn-ghost:hover:not(:disabled) { background: var(--accent); }
.ed-btn-primary { background: var(--primary); color: var(--primary-foreground); }
.ed-btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 88%, black); }
.ed-icon-btn { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 999px; background: var(--card); color: var(--muted-foreground); box-shadow: var(--shadow-card); }
.ed-icon-btn svg { width: 16px; height: 16px; }
.ed-menu-wrap { position: relative; }
.ed-menu { position: absolute; top: calc(100% + 6px); right: 0; z-index: 60; display: flex; min-width: 200px; flex-direction: column; border-radius: 14px; background: var(--popover); padding: 6px; box-shadow: var(--shadow-elegant); }
.ed-menu button { border-radius: 10px; padding: 8px 10px; text-align: left; font-size: 13px; color: var(--popover-foreground); }
.ed-menu button:hover { background: var(--muted); }
.ed-menu button.danger { color: var(--status-danger-foreground); }

.ed-tabs { display: flex; gap: 4px; overflow-x: auto; border-bottom: 1px solid var(--border); }
.ed-tab { display: inline-flex; flex-shrink: 0; align-items: center; gap: 8px; padding: 10px 14px; font-size: 13.5px; font-weight: 600; white-space: nowrap; color: var(--muted-foreground); }
.ed-tab svg { width: 15px; height: 15px; }
.ed-tab:hover { color: var(--foreground); }
.ed-tab.on { box-shadow: inset 0 -2px 0 var(--primary); color: var(--foreground); }
.ed-tab-badge { border-radius: 999px; background: var(--status-warning); padding: 1px 8px; font-size: 10.5px; color: var(--status-warning-foreground); }

.ed-grid { display: grid; grid-template-columns: 340px minmax(0, 1fr); gap: 16px; height: calc(100dvh / var(--app-scale, 1) - 184px); min-height: 560px; }
.ed-grid.is-wide { grid-template-columns: minmax(380px, 440px) minmax(0, 1fr); }
.ed-side { min-height: 0; overflow-y: auto; }
.ed-sections { display: flex; min-height: 100%; flex-direction: column; border-radius: 20px; background: var(--card); padding: 16px; box-shadow: var(--shadow-card); }
.ed-sections-head { display: flex; align-items: center; justify-content: space-between; padding: 0 4px 8px; }
.ed-sections-head h2 { font-size: 15px; font-weight: 600; color: var(--foreground); }
.ed-sections-head span { font-size: 12px; color: var(--muted-foreground); }
.ed-section-list { display: flex; flex-direction: column; gap: 2px; }
.ed-section-row { display: flex; align-items: center; gap: 6px; border-radius: 14px; padding: 6px 6px 6px 2px; transition: background 0.15s; }
.ed-section-row:hover { background: var(--muted); }
.ed-section-row.is-drag-over { box-shadow: inset 0 2px 0 var(--primary); }
.ed-section-row.is-dragging { opacity: 0.5; }
.ed-section-row.is-off .ed-section-name, .ed-section-row.is-off .ed-section-icon { opacity: 0.5; }
.ed-grip { display: grid; place-items: center; width: 18px; color: var(--muted-foreground); cursor: grab; }
.ed-grip svg { width: 14px; height: 14px; }
.ed-grip.is-locked { visibility: hidden; }
.ed-section-main { display: flex; min-width: 0; flex: 1; align-items: center; gap: 10px; text-align: left; }
.ed-section-icon { display: grid; place-items: center; width: 34px; height: 34px; flex-shrink: 0; border-radius: 999px; }
.ed-section-icon svg { width: 16px; height: 16px; }
.ed-section-name { display: block; overflow: hidden; font-size: 14px; font-weight: 600; white-space: nowrap; text-overflow: ellipsis; color: var(--foreground); }
.ed-section-sub { display: block; overflow: hidden; font-size: 12px; white-space: nowrap; text-overflow: ellipsis; color: var(--muted-foreground); }
.tone-success { background: var(--status-success); color: var(--status-success-foreground); }
.tone-warning { background: var(--status-warning); color: var(--status-warning-foreground); }
.tone-info { background: var(--status-info); color: var(--status-info-foreground); }
.tone-violet { background: var(--status-violet); color: var(--status-violet-foreground); }
.ed-switch { position: relative; width: 36px; height: 20px; flex-shrink: 0; border-radius: 999px; background: var(--muted); box-shadow: inset 0 0 0 1px var(--border); transition: background 0.15s; }
.ed-switch i { position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; border-radius: 999px; background: #fff; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25); transition: transform 0.15s; }
.ed-switch.on { background: var(--primary); box-shadow: none; }
.ed-switch.on i { transform: translateX(16px); }
.ed-switch:disabled { cursor: not-allowed; opacity: 0.5; }
.ed-add-section { display: inline-flex; align-items: center; justify-content: center; gap: 8px; margin-top: 10px; border: 1px dashed var(--border); border-radius: 14px; padding: 10px; font-size: 13.5px; font-weight: 600; color: var(--primary); }
.ed-add-section:hover { background: var(--accent); }
.ed-add-section svg { width: 15px; height: 15px; }
.ed-sections-hint { margin-top: auto; padding: 16px 4px 0; font-size: 12px; line-height: 1.45; color: var(--muted-foreground); }
.ed-settings-card { min-height: 100%; padding: 16px !important; }
.ed-settings-card .editor-settings-grid { gap: 0; }
.ed-settings-card .settings-panel { height: auto !important; padding: 4px !important; background: transparent !important; }
.ed-settings-card .settings-panel-content { height: auto !important; overflow: visible !important; }
.ed-settings-card :deep(.grid) { grid-template-columns: minmax(0, 1fr) !important; }
.ed-settings-card :deep(.text-\[17px\]), .ed-settings-card :deep(.text-\[18px\]) { font-size: 14px !important; }
.ed-settings-card :deep(p.text-\[17px\].uppercase) { font-size: 13px !important; color: var(--muted-foreground) !important; }
.ed-settings-card :deep(.slug-prefix) { font-size: 13px !important; }

.editor-preview-shell { display: flex; min-height: 0; flex-direction: column; padding: 14px 16px 16px !important; }
.ed-preview-head { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 12px; }
.ed-preview-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted-foreground); }
.ed-preview-head .editor-preview-scale { margin: 0; text-align: right; }
.ed-preview-eyebrow, .ed-preview-head .editor-preview-scale { white-space: nowrap; }
.editor-body.ai-assistant-open .ed-preview-head { grid-template-columns: auto; justify-content: center; }
.editor-body.ai-assistant-open .ed-preview-eyebrow,
.editor-body.ai-assistant-open .ed-preview-head .editor-preview-scale { display: none; }
.ed-stage { margin-top: 12px; min-height: 0; flex: 1; }
.ed-stage.is-framed { display: flex; justify-content: center; }
.ed-browser { display: flex; width: 100%; min-height: 0; flex-direction: column; overflow: hidden; border-radius: 14px; background: #fff; box-shadow: var(--shadow-elegant); }
.ed-browser-bar { display: flex; height: 30px; flex-shrink: 0; align-items: center; gap: 6px; background: #e9eeea; padding: 0 12px; }
.ed-browser-bar i { width: 9px; height: 9px; border-radius: 999px; background: #cfd6d1; }
.ed-browser-bar span { overflow: hidden; margin-left: 10px; border-radius: 999px; background: #fff; padding: 2px 12px; font-size: 11px; white-space: nowrap; text-overflow: ellipsis; color: #66706b; }
:global(.dark .ed-browser) { background: #0f1513; }
:global(.dark .ed-browser-bar) { background: #1a2320; }
:global(.dark .ed-browser-bar i) { background: #34403b; }
:global(.dark .ed-browser-bar span) { background: #0f1513; color: #9aa7a1; }
.ed-phone { display: flex; width: 410px; max-width: 100%; min-height: 0; flex-direction: column; border-radius: 40px; background: #0b100e; padding: 10px; box-shadow: var(--shadow-elegant); }
.ed-phone .ed-screen { border-radius: 30px; background: #fff; scrollbar-width: none; }
.ed-phone .ed-screen::-webkit-scrollbar { display: none; }
.ed-stage.is-framed .ed-screen { min-height: 0; flex: 1; overflow-x: hidden; overflow-y: auto; }

@media (max-width: 1023px) {
  .ed-grid, .ed-grid.is-wide { grid-template-columns: minmax(0, 1fr); height: auto; min-height: 0; }
  .ed-side { overflow: visible; }
  .ed-sections-hint { margin-top: 12px; }
  .ed-stage.is-framed .ed-screen { max-height: 80vh; }
}
@media (max-width: 640px) {
  .ed-actions { width: 100%; }
  .ed-btn-primary { flex: 1; justify-content: center; }
}

/* Editor novo: configurações recolhíveis à esquerda, prévia no meio, camadas (ou IA) à direita. */
.ed-sections-titles { display: flex; flex: 1; min-width: 0; align-items: center; justify-content: space-between; gap: 8px; }
.ed-grid > .ed-sections { min-height: 0; overflow-y: auto; }
.ed-grid.is-v2 { grid-template-columns: auto minmax(0, 1fr) auto; gap: 8px; height: calc(100dvh / var(--app-scale, 1) - 92px); min-height: 520px; }
.page-editor-view.is-v2 .ed-topbar { gap: 10px; min-height: 52px; }
.page-editor-view.is-v2 .ed-back { width: 36px; height: 36px; }
.page-editor-view.is-v2 .ed-crumb { display: none; }
.page-editor-view.is-v2 .ed-title { overflow: hidden; max-width: 46vw; font-size: 18px; line-height: 1.25; white-space: nowrap; text-overflow: ellipsis; }
.page-editor-view.is-v2 .editor-body { padding-top: 0; }
.ed-grid.is-v2 > .editor-preview-shell { padding: 8px 10px 10px !important; border-radius: 18px !important; }
.ed-grid.is-v2 .ed-preview-head { min-height: 40px; }
.ed-grid.is-v2 .ed-preview-eyebrow { display: none; }
.ed-grid.is-v2 .ed-stage { margin-top: 8px; }
.ed-grid.is-v2 > .ed-side, .ed-grid.is-v2 > .ed-sections, .ed-grid.is-v2 > .ed-layers-mini { border-radius: 18px; }
.ed-grid.is-v2 > .ed-side { grid-column: 1; grid-row: 1; }
.ed-grid.is-v2 > .editor-preview-shell { grid-column: 2; grid-row: 1; }
.ed-grid.is-v2 > .ed-sections, .ed-grid.is-v2 > .ed-layers-mini { grid-column: 3; grid-row: 1; }
.v2ed-tag, .v2ed-bar, .v2ed-ins { zoom: var(--ed-unzoom, 1); }
.ed-grid.is-v2 > .ed-side { display: flex; min-height: 0; overflow: hidden; border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.ed-grid.is-v2 .ed-settings-card { width: 360px; min-height: 0; overflow-y: auto; border-radius: 0 !important; box-shadow: none !important; padding: 18px 18px 24px; }
.ed-grid.is-v2 .slug-row { flex-direction: column; }
.ed-grid.is-v2 .slug-prefix { overflow: hidden; border-right: 0; border-bottom: 1px solid #e2e8f0; padding-top: 6px; padding-bottom: 6px; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.editor-workspace.is-v2 .editor-ai-sidebar { top: 100px; bottom: 8px; border-radius: 20px; }
.v2ed-toast { position: fixed; bottom: 24px; left: 50%; z-index: 90; display: flex; align-items: center; gap: 12px; transform: translateX(-50%); padding: 10px 10px 10px 12px; border-radius: 16px; background: #0f1713; color: #fff; font-size: 14px; box-shadow: 0 20px 50px -20px rgba(6, 12, 9, 0.7); }
.v2ed-toast-ico { display: grid; place-items: center; width: 26px; height: 26px; border-radius: 999px; background: #12b981; }
.v2ed-toast-ico svg { width: 15px; height: 15px; }
.v2ed-toast button { height: 34px; padding: 0 14px; border-radius: 10px; background: rgba(255, 255, 255, 0.14); color: #fff; font-weight: 700; }
.v2ed-toast button:hover { background: rgba(255, 255, 255, 0.24); }
.section-editor-dialog.is-v2-form { width: min(46rem, calc(100vw - 2rem)); max-width: min(46rem, calc(100vw - 2rem)); height: min(90vh, 920px); }
.section-editor-body.is-v2-form { padding: 16px 20px 0 !important; background: var(--muted); }
.section-editor-dirty { display: inline-flex; align-items: center; gap: 8px; margin-right: auto; font-size: 13px; font-weight: 600; color: #b4530b; }
.section-editor-dirty i { width: 8px; height: 8px; border-radius: 999px; background: #e8590c; }
.ed-section-panel { display: flex; width: 420px; min-height: 0; flex-direction: column; }
.esp-top { display: flex; align-items: center; gap: 4px; padding: 10px 10px 6px 6px; }
.esp-back { display: inline-flex; flex: 1; align-items: center; gap: 4px; height: 34px; padding: 0 8px 0 4px; border-radius: 9px; color: var(--muted-foreground); font-size: 13px; font-weight: 600; }
.esp-back:hover { color: var(--foreground); }
.esp-back svg { width: 16px; height: 16px; }
.esp-icon-btn { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 9px; color: var(--muted-foreground); }
.esp-icon-btn:hover { background: var(--muted); color: var(--foreground); }
.esp-icon-btn svg { width: 17px; height: 17px; }
.esp-menu-wrap { position: relative; }
.esp-menu { position: absolute; top: 38px; right: 0; z-index: 20; display: flex; min-width: 160px; flex-direction: column; padding: 6px; border-radius: 14px; background: var(--card); box-shadow: 0 18px 40px -16px rgba(6, 12, 9, 0.45), 0 0 0 1px var(--border); }
.esp-menu button { display: flex; align-items: center; gap: 8px; height: 36px; padding: 0 10px; border-radius: 9px; font-size: 13px; font-weight: 600; text-align: left; }
.esp-menu button:hover:not(:disabled) { background: var(--muted); }
.esp-menu button:disabled { opacity: 0.4; }
.esp-menu button.danger { color: #c2261c; }
.esp-menu svg { width: 15px; height: 15px; }
.esp-title { display: flex; align-items: center; gap: 12px; padding: 4px 16px 12px; }
.esp-ico { display: grid; flex-shrink: 0; place-items: center; width: 40px; height: 40px; border-radius: 12px; }
.esp-ico svg { width: 19px; height: 19px; }
.esp-title h2 { margin: 0; overflow: hidden; font-size: 17px; font-weight: 700; white-space: nowrap; text-overflow: ellipsis; color: var(--foreground); }
.esp-title span span, .esp-title > span > span { font-size: 12px; color: var(--muted-foreground); }
.esp-body { flex: 1; min-height: 0; overflow-y: auto; padding: 0 12px; background: var(--muted); border-top: 1px solid var(--border); }
.esp-body .ved-tabs { margin-top: 10px; }
.esp-foot { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 10px 12px; border-top: 1px solid var(--border); }
.esp-btn { height: 38px; padding: 0 16px; border-radius: 999px; background: var(--muted); font-size: 13px; font-weight: 700; color: var(--foreground); }
.esp-btn.is-primary { background: var(--primary); color: var(--primary-foreground); }
.v2ed-sec.is-editing { z-index: 4; }
.v2ed-sec.is-editing .v2ed-ring { opacity: 1; box-shadow: inset 0 0 0 2px #12b981; }
.ed-settings-v2 { display: flex; width: 360px; min-height: 0; flex-direction: column; }
.esv-head { padding: 14px 16px 12px; }
.esv-head .ed-panel-title { margin-bottom: 0; }
.esv-body { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding: 12px; border-top: 1px solid var(--border); background: var(--muted); }
.esv-slug { display: flex; flex-direction: column; overflow: hidden; border-radius: 12px; background: var(--muted); }
.esv-slug-base { overflow: hidden; padding: 8px 12px 0; font-size: 12px; font-weight: 600; color: var(--muted-foreground); white-space: nowrap; text-overflow: ellipsis; }
.esv-slug .ved-input { height: 38px; }
.esv-color { display: flex; align-items: center; gap: 10px; }
.esv-color .ved-label { width: 48px; flex-shrink: 0; }
.esv-color input[type="color"] { width: 44px; height: 44px; flex-shrink: 0; padding: 0; border: 0; border-radius: 12px; background: none; cursor: pointer; }
.esv-color input[type="color"]::-webkit-color-swatch-wrapper { padding: 0; }
.esv-color input[type="color"]::-webkit-color-swatch { border: 1px solid var(--border); border-radius: 12px; }
.esv-color .ved-input { flex: 1; font-weight: 600; text-transform: uppercase; letter-spacing: 0.02em; }
.esv-warn { display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; border-radius: 14px; background: #fff4ec; color: #8a3c08; font-size: 13px; line-height: 1.45; }
.esv-warn b { font-size: 14px; }
.esv-link { align-self: flex-start; padding: 2px 0; font-size: 13px; font-weight: 700; color: var(--primary); text-decoration: underline; text-underline-offset: 3px; }
.esv-btn { height: 40px; padding: 0 16px; border-radius: 999px; background: var(--muted); font-size: 13px; font-weight: 700; color: var(--foreground); }
.esv-btn.is-primary { background: var(--primary); color: var(--primary-foreground); }
.ed-stage.is-mobile-preview .v2ed-bar { top: 50px; }
.ed-stage.is-mobile-preview .v2ed-edit span { display: none; }
.ed-stage.is-mobile-preview .v2ed-edit { padding: 0 10px; }
.editor-workspace.is-v2 .editor-ai-sidebar-header { display: flex; align-items: center; gap: 10px; }
.ai-v2-mark { display: grid; flex-shrink: 0; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: #e7f6ee; color: #0b7a55; }
.ai-v2-mark svg { width: 18px; height: 18px; }
.editor-workspace.is-v2 .editor-ai-sidebar-header-copy { flex: 1; min-width: 0; }
.ai-v2-usage { display: block; font-size: 12px; color: var(--muted-foreground); }
.editor-workspace.is-v2 .editor-ai-sidebar-bubble.is-user { background: var(--foreground); color: var(--background); }
.editor-workspace.is-v2 .editor-ai-sidebar-bubble.is-assistant { background: var(--muted); color: var(--foreground); border-color: transparent; }
.ai-v2-structure { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
.ai-v2-structure-title { margin: 0; font-size: 13px; font-weight: 700; }
.ai-v2-structure ol { display: flex; flex-direction: column; gap: 2px; margin: 0; padding: 6px; list-style: none; border-radius: 12px; background: var(--card); box-shadow: inset 0 0 0 1px var(--border); }
.ai-v2-structure li { display: flex; align-items: center; gap: 10px; padding: 6px 8px; font-size: 13px; }
.ai-v2-structure li b { width: 16px; flex-shrink: 0; text-align: right; color: var(--muted-foreground); font-size: 12px; }
.ai-v2-structure li.is-more button { padding-left: 26px; font-size: 13px; font-weight: 700; color: var(--primary); }
.ai-v2-actions { display: flex; gap: 8px; }
.ai-v2-actions button { flex: 1; height: 38px; border-radius: 999px; background: var(--card); box-shadow: inset 0 0 0 1px var(--border); font-size: 13px; font-weight: 700; color: var(--foreground); }
.ai-v2-actions button.is-primary { background: #12b981; box-shadow: none; color: #fff; }
.ai-v2-actions button:disabled { opacity: 0.5; }
.ai-v2-hint { font-size: 12px; color: var(--muted-foreground); }
.ai-v2-details { align-self: flex-start; font-size: 12px; font-weight: 700; color: var(--muted-foreground); text-decoration: underline; text-underline-offset: 3px; }
.ai-v2-full { padding: 10px; border-radius: 10px; background: var(--card); font-size: 12px; }
.ai-v2-chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 8px; }
.ai-v2-chips button { padding: 7px 12px; border-radius: 999px; background: var(--card); box-shadow: inset 0 0 0 1px var(--border); font-size: 13px; font-weight: 600; color: var(--foreground); }
.ai-v2-chips button:hover { box-shadow: inset 0 0 0 1.5px #12b981; }
.editor-workspace.is-v2 .editor-ai-sidebar-send:not(:disabled) { background: var(--foreground); color: var(--background); }
.ed-panel-eyebrow { margin: 0 0 2px; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted-foreground); }
.ed-panel-title { margin: 0 0 16px; font-size: 18px; font-weight: 700; color: var(--foreground); }
.ed-rail { display: flex; flex: 0 0 64px; flex-direction: column; align-items: center; gap: 4px; padding: 12px 0; border-right: 1px solid var(--border); }
.ed-grid.left-closed .ed-rail { border-right: 0; }
.ed-rail-btn { position: relative; display: grid; flex-shrink: 0; place-items: center; width: 44px; height: 44px; border-radius: 12px; color: var(--muted-foreground); transition: background-color 0.15s ease, color 0.15s ease; }
.ed-rail-btn:first-child { margin-bottom: 8px; }
.ed-rail-btn:hover { background: var(--muted); color: var(--foreground); }
.ed-rail-btn.on { background: var(--status-success); color: var(--status-success-foreground); }
.ed-rail-btn svg { width: 20px; height: 20px; }
.ed-rail-btn.is-small { width: 34px; height: 34px; margin: 0; }
.ed-rail-btn.is-small svg { width: 18px; height: 18px; }
.ed-rail-dot { position: absolute; top: 9px; right: 9px; width: 8px; height: 8px; border-radius: 999px; background: #e8590c; box-shadow: 0 0 0 2px var(--card); }
.ed-grid.is-v2 > .ed-sections { width: 272px; padding: 12px 8px; }
.ed-grid.is-v2 .ed-sections-head { gap: 8px; padding: 0 4px 10px; }
.ed-grid.is-v2 .ed-sections-titles { flex-direction: column; align-items: flex-start; gap: 0; }
.ed-layers-add { display: inline-flex; flex-shrink: 0; align-items: center; gap: 4px; height: 32px; padding: 0 12px 0 9px; border-radius: 999px; background: var(--foreground); color: var(--background); font-size: 13px; font-weight: 700; }
.ed-layers-add svg { width: 15px; height: 15px; }
.ed-layers-mini { display: flex; width: 64px; min-height: 0; flex-direction: column; align-items: center; gap: 6px; overflow-y: auto; padding: 12px 0; border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.ed-layers-mini .ed-rail-btn { margin-bottom: 0; }
.ed-layers-mini-sep { width: 28px; height: 1px; flex-shrink: 0; background: var(--border); }
.ed-layers-mini-item { display: grid; flex-shrink: 0; place-items: center; width: 36px; height: 32px; border-radius: 8px; font-size: 12px; font-weight: 800; }
.ed-layers-mini-item.is-off { opacity: 0.45; }
.ed-layers-mini-add { display: grid; flex-shrink: 0; place-items: center; width: 36px; height: 36px; margin-top: 4px; border-radius: 999px; background: var(--foreground); color: var(--background); }
.ed-layers-mini-add svg { width: 16px; height: 16px; }

/* Prévia do editor novo: sombra ao passar o mouse, ações no topo e linha para inserir seção. */
.v2ed-slot { position: relative; }
.v2ed-sec { transition: box-shadow 0.2s ease; }
.v2ed-sec:hover, .v2ed-sec:focus-within { z-index: 5; box-shadow: 0 24px 60px -18px rgba(6, 12, 9, 0.55), 0 4px 14px -6px rgba(6, 12, 9, 0.3); }
.v2ed-ring, .v2ed-tag, .v2ed-bar { opacity: 0; transition: opacity 0.18s ease, transform 0.24s cubic-bezier(0.22, 0.8, 0.24, 1); }
.v2ed-tag, .v2ed-bar { transform: translateY(-4px); }
.v2ed-sec:hover .v2ed-ring, .v2ed-sec:hover .v2ed-tag, .v2ed-sec:hover .v2ed-bar,
.v2ed-sec:focus-within .v2ed-ring, .v2ed-sec:focus-within .v2ed-tag, .v2ed-sec:focus-within .v2ed-bar { opacity: 1; transform: none; }
.v2ed-ring { position: absolute; inset: 0; z-index: 70; pointer-events: none; box-shadow: inset 0 0 0 1px rgba(18, 185, 129, 0.55), inset 0 0 60px -10px rgba(6, 12, 9, 0.28); }
.v2ed-tag { position: absolute; top: 12px; left: 12px; z-index: 71; display: inline-flex; align-items: center; padding: 6px 12px; border-radius: 999px; background: #12b981; color: #fff; font: 700 13px Figtree, sans-serif; box-shadow: 0 6px 16px -6px rgba(6, 12, 9, 0.5); pointer-events: none; }
.v2ed-bar { position: absolute; top: 12px; right: 12px; z-index: 71; display: flex; align-items: center; gap: 2px; padding: 4px; border-radius: 14px; background: #fff; color: #0f1713; box-shadow: 0 2px 6px rgba(6, 12, 9, 0.18), 0 14px 32px -12px rgba(6, 12, 9, 0.45); font-family: Figtree, sans-serif; }
.v2ed-edit { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 12px; border-radius: 10px; background: #0f1713; color: #fff; font-size: 13px; font-weight: 700; }
.v2ed-edit:hover { background: #000; }
.v2ed-edit svg, .v2ed-btn svg { width: 16px; height: 16px; }
.v2ed-btn { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 10px; color: #0f1713; transition: background-color 0.15s ease, color 0.15s ease; }
.v2ed-btn:hover { background: #eef1ec; }
.v2ed-btn:disabled { opacity: 0.3; pointer-events: none; }
.v2ed-btn.is-danger:hover { background: #fdecec; color: #c2261c; }
.v2ed-sep { width: 1px; height: 22px; margin: 0 4px; background: #e3e8e2; }
.v2ed-locked { padding: 6px 10px; font-size: 12px; font-weight: 600; color: #4f5c55; }
.v2ed-ins { position: absolute; top: -24px; left: 0; right: 0; z-index: 80; display: flex; height: 48px; align-items: center; justify-content: center; }
.v2ed-ins-line { position: absolute; top: 50%; left: 0; right: 0; height: 3px; margin-top: -1.5px; background: #12b981; box-shadow: 0 1px 3px rgba(6, 12, 9, 0.55), 0 6px 18px rgba(6, 12, 9, 0.35); opacity: 0; transform: scaleX(0.6); transition: opacity 0.18s ease, transform 0.28s cubic-bezier(0.22, 0.8, 0.24, 1); }
.v2ed-ins-btn { position: relative; display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px 0 10px; border-radius: 999px; background: #12b981; color: #fff; font: 700 13px Figtree, sans-serif; box-shadow: 0 2px 4px rgba(6, 12, 9, 0.35), 0 10px 24px -6px rgba(6, 12, 9, 0.5); opacity: 0; transform: scale(0.85); transition: opacity 0.18s ease, transform 0.24s cubic-bezier(0.22, 0.8, 0.24, 1), background-color 0.18s ease; }
.v2ed-ins-btn svg { width: 16px; height: 16px; }
.v2ed-ins-btn:hover { background: #0e9f6e; }
.v2ed-ins:hover .v2ed-ins-line, .v2ed-ins:focus-within .v2ed-ins-line { opacity: 1; transform: none; }
.v2ed-ins:hover .v2ed-ins-btn, .v2ed-ins:focus-within .v2ed-ins-btn { opacity: 1; transform: none; }
.v2ed-end { position: relative; display: grid; height: 72px; place-items: center; border-top: 1px dashed #dce1da; background: #f4f6f3; }
.v2ed-ins.is-end { top: -24px; }
.v2ed-end-label { padding-top: 18px; font: 600 12px Figtree, sans-serif; color: #9aa59f; }
@media (prefers-reduced-motion: reduce) {
  .v2ed-ring, .v2ed-tag, .v2ed-bar, .v2ed-ins-line, .v2ed-ins-btn, .v2ed-sec { transition: none; }
}
@media (max-width: 1279px) {
  .ed-grid.is-v2 .ed-settings-card { width: 320px; }
  .ed-section-panel { width: 360px; }
  .ed-settings-v2 { width: 320px; }
  .ed-grid.is-v2 > .ed-sections { width: 248px; }
}
</style>


















