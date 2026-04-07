<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <div class="flex flex-wrap items-center justify-between gap-3 dark:text-white">
      <div>
        <p class="text-sm font-bold uppercase tracking-[0.3em] text-slate-500 dark:text-white">
          {{ viewCopy.header.eyebrow }}
        </p>
      </div>
      <button
        @click="openCreateModal"
        class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
        :disabled="!hasAgency"
      >
        {{ viewCopy.header.newPage }}
      </button>
    </div>

    <teleport to="body">
      <div
        v-if="templateModal.open"
        class="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/80 px-4 py-6"
      >
        <div class="relative w-full max-w-7xl rounded-3xl bg-white shadow-2xl dark:bg-[#202020] dark:text-white">
          <div class="max-h-[90vh] overflow-y-auto p-6">
            <div class="relative flex flex-col gap-2 border-b border-slate-100 pb-4 md:flex-row md:items-center md:justify-between dark:border-white/10">
              <div>
                <p class="text-xs uppercase tracking-[0.4em] text-slate-500 dark:text-white/60">
                  {{ viewCopy.templateModal.title }}
                </p>
                <h2 class="text-2xl font-semibold text-slate-900 dark:text-white">
                  {{ viewCopy.templateModal.listTitle }}
                </h2>
                <p class="text-sm text-slate-500 dark:text-white/70">
                  {{ viewCopy.templateModal.subtitle }}
                </p>
              </div>
              <button
                type="button"
                class="absolute -right-2 -top-2 inline-flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:bg-slate-50 dark:border-white/15 dark:bg-[#202020] dark:text-white dark:hover:bg-white/10"
                @click="closeTemplateModal"
                aria-label="Fechar"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M6 6l12 12M6 18L18 6" />
                </svg>
              </button>
            </div>

            <div class="mt-6 grid gap-6 overflow-hidden lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
              <div class="space-y-4">
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">
                  {{ viewCopy.templateModal.listTitle }}
                </p>

              <p
                v-if="templateModal.loading"
                class="rounded-2xl border border-dashed border-slate-200 p-4 text-center text-sm text-slate-500 dark:border-white/10 dark:text-white/70"
              >
                {{ viewCopy.templateModal.listLoading }}
              </p>

              <p
                v-else-if="templateModal.error && !templateModal.templates.length"
                class="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-400/40 dark:bg-red-500/10 dark:text-red-200"
              >
                {{ templateModal.error }}
              </p>

              <p
                v-else-if="!templateModal.templates.length"
                class="rounded-2xl border border-dashed border-slate-200 p-4 text-center text-sm text-slate-500 dark:border-white/10 dark:text-white/70"
              >
                {{ viewCopy.templateModal.listEmpty }}
              </p>

              <div v-else class="h-[55vh] space-y-3 overflow-y-auto pr-2">
                <p class="text-xs text-slate-500 dark:text-white/60">
                  {{ viewCopy.templateModal.selectHint }}
                </p>

                <div
                  v-for="template in templateModal.templates"
                  :key="template.id"
                  class="flex flex-col gap-3 rounded-2xl border px-4 py-3 transition sm:flex-row sm:items-center"
                  :class="
                    templateModal.selectedTemplate && templateModal.selectedTemplate.id === template.id
                      ? 'border-slate-900 bg-slate-900/5 text-slate-900 dark:border-white dark:bg-white/10 dark:text-white'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 dark:border-white/15 dark:hover:bg-white/5'
                  "
                >
                  <button
                    type="button"
                    class="flex flex-1 items-center gap-3 text-left"
                    :class="isMobileViewport ? 'cursor-default opacity-80' : ''"
                    @click="handleTemplateCardClick(template)"
                    :disabled="isMobileViewport"
                  >
                    <div>
                      <p class="text-sm font-semibold">{{ template.name }}</p>
                      <p class="text-xs text-slate-500 dark:text-white/60">
                        {{ template.description || "Sem descrição" }}
                      </p>
                    </div>
                  </button>

                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/15 dark:text-white"
                      @click="handleTemplatePreview(template)"
                    >
                      Visualizar
                    </button>
                    <button
                      type="button"
                      class="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900"
                      @click="useTemplateNow(template)"
                    >
                      Usar esse
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div class="space-y-4" v-if="!isMobileViewport">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">
                  {{ viewCopy.templateModal.previewHeading }}
                </p>

                <div class="inline-flex items-center rounded-full border border-slate-200 bg-white p-1 text-xs font-semibold dark:border-white/10 dark:bg-[#101010]">
                  <button
                    type="button"
                    class="rounded-full px-3 py-1 transition"
                    :class="templatePreviewDevice === 'desktop' ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500 dark:text-white/70'"
                    @click="setTemplatePreviewDevice('desktop', true)"
                  >
                    Desktop
                  </button>
                  <button
                    type="button"
                    class="rounded-full px-3 py-1 transition"
                    :class="templatePreviewDevice === 'mobile' ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500 dark:text-white/70'"
                    @click="setTemplatePreviewDevice('mobile', true)"
                  >
                    Mobile
                  </button>
                </div>
              </div>

              <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4 dark:border-white/10 dark:bg-[#111111]">
                <div
                  v-if="!isMobileViewport || !previewFullscreen"
                  ref="templatePreviewContainer"
                  class="preview-scroll max-h-[55vh] overflow-y-auto rounded-xl bg-white pb-4 dark:bg-[#181818] dark:text-white"
                >
                  <template v-if="templateModal.selectedTemplate && templatePreviewConfig">
                    <div
                      class="preview-scale-wrapper"
                      :class="{ 'preview-mobile-center': templatePreviewDevice === 'mobile' }"
                      :style="templatePreviewWrapperStyle"
                    >
                      <div class="preview-scale" :style="templatePreviewStyle">
                        <div ref="templatePreviewContent">
                          <PageTemplatePreview
                            :config="templatePreviewConfig"
                            :preview-device="templatePreviewDevice"
                            :branding="{
                              agency_name: currentAgency?.name || authStore.user?.name || '',
                              logo_url: currentAgency?.logo_url || '',
                              primary_color: currentAgency?.primary_color || '#0f172a',
                              secondary_color: currentAgency?.secondary_color || '#1f2937'
                            }"
                          />
                        </div>
                      </div>
                    </div>
                  </template>

                  <template v-else>
                    <p class="py-10 text-center text-sm text-slate-500 dark:text-white/70">
                      {{ viewCopy.templateModal.previewEmpty }}
                    </p>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
          <transition name="fade">
            <div
              v-if="isMobileViewport && previewFullscreen && templateModal.selectedTemplate && templatePreviewConfig"
              class="absolute inset-0 z-20 m-3 flex flex-col rounded-3xl bg-white px-4 pb-6 pt-5 shadow-2xl dark:bg-[#202020]"
            >
              <div class="relative mb-4 border-b border-slate-100 pb-3 dark:border-white/10">
                <button
                  type="button"
                  class="absolute right-0 top-0 rounded-full border border-slate-200 px-4 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600 transition hover:bg-slate-50 dark:border-white/15 dark:text-white dark:hover:bg-white/10"
                  @click="closePreviewFullscreen"
                >
                  {{ viewCopy.templateModal.back }}
                </button>
                <div class="flex flex-wrap items-center justify-between gap-3 pr-24">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">
                      {{ viewCopy.templateModal.previewHeading }}
                    </p>
                    <p class="text-sm font-semibold text-slate-900 dark:text-white">
                      {{ templateModal.selectedTemplate?.name }}
                    </p>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="inline-flex items-center rounded-full border border-slate-200 bg-white p-1 text-xs font-semibold dark:border-white/10 dark:bg-[#101010]">
                      <button
                        type="button"
                        class="rounded-full px-3 py-1 transition"
                        :class="templatePreviewDevice === 'desktop' ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500 dark:text-white/70'"
                        @click="setTemplatePreviewDevice('desktop', true)"
                      >
                        Desktop
                      </button>
                      <button
                        type="button"
                        class="rounded-full px-3 py-1 transition"
                        :class="templatePreviewDevice === 'mobile' ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500 dark:text-white/70'"
                        @click="setTemplatePreviewDevice('mobile', true)"
                      >
                        Mobile
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="flex-1 overflow-hidden">
                <div
                  ref="templatePreviewContainer"
                  class="preview-scroll h-full overflow-y-auto rounded-xl bg-white pb-4 dark:bg-[#181818] dark:text-white"
                >
                  <template v-if="templateModal.selectedTemplate && templatePreviewConfig">
                    <div
                      class="preview-scale-wrapper"
                      :class="{ 'preview-mobile-center': templatePreviewDevice === 'mobile' }"
                      :style="templatePreviewWrapperStyle"
                    >
                      <div class="preview-scale" :style="templatePreviewStyle">
                        <div ref="templatePreviewContent">
                          <PageTemplatePreview
                            :config="templatePreviewConfig"
                            :preview-device="templatePreviewDevice"
                            :branding="{
                              agency_name: currentAgency?.name || authStore.user?.name || '',
                              logo_url: currentAgency?.logo_url || '',
                              primary_color: currentAgency?.primary_color || '#0f172a',
                              secondary_color: currentAgency?.secondary_color || '#1f2937'
                            }"
                          />
                        </div>
                      </div>
                    </div>
                  </template>

                  <template v-else>
                    <p class="py-10 text-center text-sm text-slate-500 dark:text-white/70">
                      {{ viewCopy.templateModal.previewEmpty }}
                    </p>
                  </template>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </teleport>

    <div
      v-if="!hasAgency"
      class="flex flex-col gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 sm:flex-row sm:items-center sm:justify-between"
    >
      <span>
        {{ viewCopy.emptyStates.noAgency.prefix }}
        <router-link to="/admin/agency" class="font-semibold underline">
          {{ viewCopy.emptyStates.noAgency.link }}
        </router-link>
        {{ viewCopy.emptyStates.noAgency.suffix }}
      </span>
      <router-link
        to="/admin/agency"
        class="inline-flex items-center justify-center rounded-full bg-amber-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-amber-500"
      >
        {{ viewCopy.emptyStates.noAgency.cta }}
      </router-link>
    </div>

    <teleport to="body">
      <div
        v-if="createOptionsOpen"
        class="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/60 px-4 py-8"
      >
        <div class="w-full max-w-4xl rounded-3xl bg-white p-8 shadow-2xl dark:bg-[#202020] dark:text-white">
          <div class="relative mb-6 space-y-1">
            <h2 class="text-2xl font-bold text-slate-900">
              {{ viewCopy.actions.createModal.title }}
            </h2>
            <button
              type="button"
              class="absolute -right-2 -top-2 inline-flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:bg-slate-50 dark:border-[#363636] dark:bg-[#202020] dark:text-white dark:hover:bg-white/10"
              @click="closeCreateModal"
              aria-label="Fechar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 6l12 12M6 18L18 6" />
              </svg>
            </button>
          </div>

          <div class="grid gap-4 md:grid-cols-3">
            <button
              class="rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50 dark:border-[#363636] dark:bg-[#101010] dark:text-white dark:hover:bg-white/5"
              @click="createPageFromScratch"
            >
              <span
                class="inline-flex items-center rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700"
              >
                {{ viewCopy.actions.createModal.scratch.badge }}
              </span>
              <h3 class="mt-3 text-lg font-semibold text-slate-900 dark:text-white">
                {{ viewCopy.actions.createModal.scratch.title }}
              </h3>
              <p class="mt-1 text-sm text-slate-600 dark:text-slate-200">
                {{ viewCopy.actions.createModal.scratch.description }}
              </p>
            </button>

            <button
              class="rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50 dark:border-[#363636] dark:bg-[#101010] dark:text-white dark:hover:bg-white/5"
              @click="createPageFromTemplate"
            >
              <span
                class="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700"
              >
                {{ viewCopy.actions.createModal.template.badge }}
              </span>
              <h3 class="mt-3 text-lg font-semibold text-slate-900 dark:text-white">
                {{ viewCopy.actions.createModal.template.title }}
              </h3>
              <p class="mt-1 text-sm text-slate-600 dark:text-slate-200">
                {{ viewCopy.actions.createModal.template.description }}
              </p>
            </button>

            <button
              class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-left text-slate-600 transition hover:-translate-y-0.5 hover:border-slate-300 dark:border-[#363636] dark:bg-[#181818] dark:text-slate-200 dark:hover:border-white/10 dark:hover:bg-white/5"
              @click="createPageWithAi"
            >
              <span
                class="inline-flex items-center rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700"
              >
                {{ viewCopy.actions.createModal.ai.badge }}
              </span>
              <h3 class="mt-3 text-lg font-semibold text-slate-900 dark:text-white">
                {{ viewCopy.actions.createModal.ai.title }}
              </h3>
              <p class="mt-1 text-sm text-slate-600 dark:text-slate-200">
                {{ viewCopy.actions.createModal.ai.description }}
              </p>
            </button>
          </div>

        </div>
      </div>
    </teleport>

    <transition name="fade">
      <div v-if="planLimitDialog.open" class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/70 px-4">
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl dark:bg-[#202020] dark:text-white">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">
            {{ viewCopy.actions.planLimit.badge }}
          </p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">
            {{ planLimitHeading }}{{ planLimitDialog.planLabel }}.
          </h2>
          <p class="mt-2 text-sm text-slate-600 dark:text-slate-200">
            {{ viewCopy.actions.planLimit.description }}
          </p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-[#363636] dark:text-white dark:hover:bg-white/10"
              @click="planLimitDialog.open = false"
            >
              {{ viewCopy.actions.planLimit.close }}
            </button>
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 dark:bg-brand dark:hover:bg-brand-dark"
              @click="goPlans"
            >
              {{ viewCopy.actions.planLimit.viewPlans }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <div class="overflow-x-auto">
      <div class="overflow-hidden border-0 bg-transparent md:min-w-[880px] md:rounded-3xl md:border md:border-slate-100 md:bg-white md:shadow-md dark:md:border-[#2b2b2b] dark:md:bg-[#202020]">
        <div
          :class="[
            'hidden gap-6 border-b border-slate-100 px-6 py-4 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 md:grid dark:border-[#2b2b2b] dark:text-white',
            headerGridColumns
          ]"
        >
          <span>{{ viewCopy.table.columns.name }}</span>
          <span class="text-center">{{ viewCopy.table.columns.views }}</span>
          <span class="text-center">{{ viewCopy.table.columns.ctaClicks }}</span>
          <span v-if="showLeadColumn" class="text-center">{{ viewCopy.table.columns.leads }}</span>
          <span>{{ viewCopy.table.columns.link }}</span>
          <span>{{ viewCopy.table.columns.status }}</span>
          <span class="text-right">{{ viewCopy.table.columns.actions }}</span>
        </div>

        <div v-if="pages.length" class="space-y-4 md:space-y-0 md:divide-y md:divide-slate-100 dark:md:divide-[#2b2b2b]">
          <div
            v-for="page in pages"
            :key="page.id"
            :class="[
              'grid grid-cols-1 gap-4 rounded-2xl border border-slate-100 bg-white px-5 py-5 shadow-sm transition hover:border-slate-200 hover:bg-slate-50/70 md:items-center md:gap-6 md:rounded-none md:border-0 md:bg-transparent md:px-6 md:py-5 md:shadow-none dark:border-[#2b2b2b] dark:bg-[#202020] dark:hover:bg-white/5',
              rowGridColumns
            ]"
          >
            <div class="flex flex-wrap items-center gap-3">
              <p class="text-base font-semibold text-slate-900">{{ page.title }}</p>
              <span
                v-if="page.is_default"
                class="rounded-full bg-emerald-50 px-3 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-emerald-600 ring-1 ring-emerald-100"
              >
                {{ viewCopy.table.badges.default }}
              </span>
            </div>

            <div class="hidden md:flex md:w-full md:justify-center">
              <button
                v-if="isFree"
                type="button"
                class="inline-flex min-w-[3rem] items-center justify-center rounded-full border border-emerald-200 bg-white px-4 py-1.5 text-sm font-semibold text-emerald-600 shadow-sm transition hover:bg-emerald-50"
                :title="viewCopy.table.premiumHints.stats"
                @click="goPlans"
              >
                <svg class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.329 19.159q-.323-.14-.566-.432L3.267 9.731q-.186-.217-.28-.475t-.093-.55q0-.187.047-.366q.048-.18.134-.361l1.779-3.59q.217-.405.603-.647t.845-.242h11.396q.46 0 .845.242t.603.646l1.779 3.59q.087.182.134.362t.047.366q0 .292-.094.55t-.28.475l-7.495 8.996q-.243.292-.566.432q-.323.139-.671.139t-.671-.14M8.817 8.5h6.366l-2-4h-2.366zm2.683 9.56V9.5H4.392zm1 0l7.108-8.56H12.5zm3.792-9.56h3.766L18.23 4.846q-.077-.154-.231-.25t-.327-.096h-3.38zm-12.35 0h3.766l2-4H6.327q-.173 0-.327.096t-.23.25z" />
                </svg>
              </button>
              <span
                v-else
                class="inline-flex min-w-[3rem] justify-center rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-600 dark:bg-[#1EA751] dark:text-white"
              >
                {{ getPageVisits(page.id) }}
              </span>
            </div>

            <div class="hidden md:flex md:w-full md:justify-center">
              <button
                v-if="isFree"
                type="button"
                class="inline-flex min-w-[3rem] items-center justify-center rounded-full border border-indigo-200 bg-white px-4 py-1.5 text-sm font-semibold text-indigo-600 shadow-sm transition hover:bg-indigo-50"
                :title="viewCopy.table.premiumHints.stats"
                @click="goPlans"
              >
                <svg class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.329 19.159q-.323-.14-.566-.432L3.267 9.731q-.186-.217-.28-.475t-.093-.55q0-.187.047-.366q.048-.18.134-.361l1.779-3.59q.217-.405.603-.647t.845-.242h11.396q.46 0 .845.242t.603.646l1.779 3.59q.087.182.134.362t.047.366q0 .292-.094.55t-.28.475l-7.495 8.996q-.243.292-.566.432q-.323.139-.671.139t-.671-.14M8.817 8.5h6.366l-2-4h-2.366zm2.683 9.56V9.5H4.392zm1 0l7.108-8.56H12.5zm3.792-9.56h3.766L18.23 4.846q-.077-.154-.231-.25t-.327-.096h-3.38zm-12.35 0h3.766l2-4H6.327q-.173 0-.327.096t-.23.25z" />
                </svg>
              </button>
              <span
                v-else
                class="inline-flex min-w-[3rem] justify-center rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-600 dark:bg-[#8544CE] dark:text-white"
              >
                {{ getPageClicks(page.id) }}
              </span>
            </div>

            <div v-if="showLeadColumn" class="hidden md:flex md:w-full md:justify-center">
              <button
                v-if="!hasLeadStatsAccess"
                type="button"
                class="inline-flex min-w-[3rem] items-center justify-center rounded-full border border-[#0185FB] bg-white px-4 py-1.5 text-xs font-semibold text-[#0185FB] shadow-sm transition hover:bg-slate-50"
                :title="viewCopy.table.premiumHints.leads"
                @click="goPlans"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="m12 2 2.09 6.26h6.58L15.29 11l2.12 6.24L12 13.77l-5.41 3.47L8.71 11 3.33 8.26h6.58Z" />
                </svg>
              </button>
              <span
                v-else
                class="inline-flex min-w-[3rem] justify-center rounded-full bg-[#0185FB] px-3 py-1 text-sm font-semibold text-white"
              >
                {{ getPageLeads(page.id) }}
              </span>
            </div>

            <div class="flex flex-col gap-2 md:hidden">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">
                {{ viewCopy.table.columns.status }}
              </p>
              <span
                class="inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide"
                :class="getStatusClasses(page.status)"
              >
                {{ getStatusLabel(page.status) }}
              </span>
            </div>

            <div class="flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-400 md:hidden">
                {{ viewCopy.table.columns.link }}
              </p>
              <div
                class="flex flex-wrap items-center gap-3"
                :class="{ 'md:justify-center md:text-center': !(page.status === 'published' && pagePublicUrl(page)) }"
              >
                <template v-if="page.status === 'published' && pagePublicUrl(page)">
                  <a
                    :href="pagePublicUrl(page)"
                    target="_blank"
                    class="max-w-[220px] truncate text-sm font-medium text-brand hover:text-brand-dark"
                  >
                    {{ pagePublicUrl(page) }}
                  </a>
                  <button
                    class="text-xs font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-600"
                    @click="copyLink(page)"
                  >
                    {{ viewCopy.actions.copy.button }}
                  </button>
                </template>
                <span v-else class="text-xs uppercase tracking-wide text-slate-400">
                  {{ viewCopy.table.linkUnavailable }}
                </span>
              </div>
            </div>

            <div class="hidden flex-col gap-2 md:flex">
              <span
                class="inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide"
                :class="getStatusClasses(page.status)"
              >
                {{ getStatusLabel(page.status) }}
              </span>
            </div>

            <div class="flex flex-col gap-2">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-400 md:hidden">
                {{ viewCopy.table.columns.actions }}
              </p>
              <div class="flex flex-wrap items-center gap-2 md:justify-end">
                <button
                  class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
                  :title="viewCopy.actions.rowMenu.duplicate"
                  @click="openDuplicateDialog(page)"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                    <rect x="9" y="9" width="11" height="11" rx="2" />
                    <rect x="4" y="4" width="11" height="11" rx="2" />
                  </svg>
                </button>

                <router-link
                  :to="`/admin/pages/${page.id}/edit`"
                  class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
                  :title="viewCopy.actions.rowMenu.edit"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                    <path d="M12 20h9" />
                    <path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z" />
                  </svg>
                </router-link>

                <a
                  v-if="pagePublicUrl(page)"
                  :href="pagePublicUrl(page)"
                  target="_blank"
                  class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
                  :title="viewCopy.actions.rowMenu.viewPage"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                    <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7Z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </a>

                <button
                  v-if="page.status === 'published'"
                  class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-amber-200 text-amber-500 transition hover:border-amber-300 hover:text-amber-600"
                  :title="viewCopy.actions.rowMenu.unpublish"
                  @click="unpublishPage(page)"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                    <path d="m7 10 5 5 5-5" />
                    <path d="M12 4v10" />
                  </svg>
                </button>

                <button
                  v-if="page.status === 'published'"
                  class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="page.is_default"
                  :title="viewCopy.actions.rowMenu.setDefault"
                  @click="setDefaultPage(page)"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                    <path d="m12 3 2.09 6.26h6.58L15.29 13l2.12 6.24L12 15.77l-5.41 3.47L8.71 13 3.33 9.26h6.58Z" />
                  </svg>
                </button>

                <button
                  class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-red-200 text-red-500 transition hover:border-red-300 hover:text-red-600"
                  :title="viewCopy.actions.rowMenu.delete"
                  @click="deletePage(page)"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                    <path d="M3 6h18" />
                    <path d="M8 6V4h8v2" />
                    <path d="m9 10 1 8" />
                    <path d="m15 10-1 8" />
                    <path d="M5 6l1 14h12l1-14" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="px-6 py-10 text-center text-sm text-slate-500">
          {{ viewCopy.emptyStates.noPages.title }}
        </div>
      </div>
    </div>

    <div
      v-if="duplicateDialogOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-slate-200">
        <div class="flex items-start justify-between">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">
              {{ viewCopy.dialogs.duplicate.title }}
            </h3>
            <p class="text-sm text-slate-500">
              {{ viewCopy.dialogs.duplicate.description }}
            </p>
          </div>
          <button class="text-slate-500 hover:text-slate-700" @click="closeDuplicateDialog">x</button>
        </div>

        <div class="mt-4 space-y-4">
          <div>
            <label class="text-sm font-semibold text-slate-700">
              {{ viewCopy.dialogs.duplicate.titleLabel }}
            </label>
            <input
              v-model="duplicateTitle"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              :placeholder="viewCopy.dialogs.duplicate.titlePlaceholder"
              @input="autoSlugFromTitle"
            />
          </div>

          <div>
            <label class="text-sm font-semibold text-slate-700">
              {{ viewCopy.dialogs.duplicate.slugLabel }}
            </label>
            <input
              v-model="duplicateSlug"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              :placeholder="viewCopy.dialogs.duplicate.slugPlaceholder"
            />
            <p class="mt-1 text-xs text-slate-500">
              {{ viewCopy.dialogs.duplicate.finalLink }}: /{{ currentAgencySlug }}/{{ duplicateSlug || "slug" }}
            </p>
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-3">
          <button
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100"
            @click="closeDuplicateDialog"
          >
            {{ viewCopy.dialogs.duplicate.cancel }}
          </button>
          <button
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="!duplicateTitle || !duplicateSlug"
            @click="confirmDuplicate"
          >
            {{ viewCopy.dialogs.duplicate.confirm }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <transition name="fade">
    <div
      v-if="snackbar.open"
      class="fixed bottom-6 left-1/2 z-[300] max-w-[90vw] -translate-x-1/2 rounded-3xl px-5 py-3 text-sm font-semibold text-white shadow-2xl sm:max-w-md"
      :class="snackbar.tone === 'error' ? 'bg-rose-600' : 'bg-slate-900'"
    >
      {{ snackbar.text }}
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";
import { getPlanLabel } from "../../utils/planLabels";
import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";
import PageTemplatePreview from "../../components/admin/PageTemplatePreview.vue";
import { listPageTemplates } from "../../services/templates";
import type { PageTemplate } from "../../types/templates";
import { applyTemplateBranding } from "../../utils/pageTemplates";
import { sanitizeDigits, buildWhatsappLink } from "../../utils/whatsapp";

interface Page {
  id: number;
  title: string;
  status: string;
  created_at?: string;
  slug?: string;
  config_json?: unknown;
  template_id?: number | null;
  is_default?: boolean;
}

interface PageStatsSummary {
  page_id: number;
  visits: number;
  clicks_cta: number;
  clicks_whatsapp: number;
  leads: number;
}

const router = useRouter();
const agencyStore = useAgencyStore();
const authStore = useAuthStore();
const adminLanguage = getAdminLanguage();
const t = createAdminLocalizer(adminLanguage);

const localizeViewCopy = (value: unknown): any => {
  if (Array.isArray(value)) {
    return value.map(item => localizeViewCopy(item));
  }
  if (value && typeof value === "object") {
    const entry = value as Record<string, unknown>;
    if ("pt" in entry || "es" in entry) {
      return t(entry as any);
    }
    return Object.fromEntries(Object.entries(entry).map(([key, child]) => [key, localizeViewCopy(child)]));
  }
  return value;
};

const viewCopySource = {
  header: {
    eyebrow: { pt: "Páginas", es: "Páginas" },
    newPage: { pt: "Nova página", es: "Nueva página" }
  },
  actions: {
    createModal: {
      eyebrow: { pt: "Novo roteiro", es: "Nuevo itinerario" },
      title: { pt: "Como deseja começar?", es: "¿Cómo deseas empezar?" },
      description: {
        pt: "Escolha entre montar tudo do zero ou partir de um template pronto.",
        es: "Elige entre construir todo desde cero o partir de un template listo."
      },
      scratch: {
        badge: { pt: "Crie como quiser", es: "Plantillas" },
        title: { pt: "Criar página do zero", es: "Crear página desde cero" },
        description: {
          pt: "Acesse o editor completo para personalizar cada seção do seu roteiro.",
          es: "Accede al editor completo para personalizar cada sección de tu itinerario."
        }
      },
      template: {
        badge: { pt: "Recomendado", es: "Recomendado" },
        title: { pt: "Criar a partir de modelo", es: "Crear desde un modelo" },
        description: {
          pt: "Selecione um layout pronto e personalize apenas o conteúdo.",
          es: "Elige un layout listo y personaliza solo el contenido."
        }
      },
      ai: {
        badge: { pt: "Em breve", es: "Pronto" },
        title: { pt: "Criar com IA", es: "Crear con IA" },
        description: {
          pt: "Gere um roteiro inicial com inteligência artificial e refine os detalhes depois.",
          es: "Genera un itinerario inicial con inteligencia artificial y ajusta los detalles después."
        }
      },
      cancel: { pt: "Cancelar", es: "Cancelar" }
    },
    planLimit: {
      badge: { pt: "Limite atingido", es: "Límite alcanzado" },
      heading: { pt: "Você atingiu o limite", es: "Alcanzaste el límite" },
      limitIntro: { pt: "de", es: "de" },
      limitUnit: { pt: "páginas", es: "páginas" },
      planPrefix: { pt: "do plano", es: "del plan" },
      description: {
        pt: "Atualize seu plano para continuar publicando roteiros profissionais para sua agência.",
        es: "Actualiza tu plan para seguir publicando itinerarios profesionales para tu agencia."
      },
      close: { pt: "Fechar", es: "Cerrar" },
      viewPlans: { pt: "Ver planos", es: "Ver planes" }
    },
    rowMenu: {
      duplicate: { pt: "Duplicar", es: "Duplicar" },
      edit: { pt: "Editar", es: "Editar" },
      viewPage: { pt: "Ver página", es: "Ver página" },
      unpublish: { pt: "Despublicar", es: "Anular publicación" },
      setDefault: { pt: "Definir como principal", es: "Marcar como principal" },
      delete: { pt: "Excluir", es: "Eliminar" }
    },
    copy: { button: { pt: "Copiar", es: "Copiar" } }
  },
  templateModal: {
    title: { pt: "Escolha um modelo", es: "Elige un modelo" },
    subtitle: {
      pt: "Use modelos oficiais para acelerar a criacao e foque apenas nos detalhes do roteiro.",
      es: "Usa plantillas oficiales para acelerar la creacion y enfocate en los detalles."
    },
    listTitle: { pt: "Modelos disponiveis", es: "Modelos disponibles" },
    listLoading: { pt: "Carregando modelos...", es: "Cargando modelos..." },
    listEmpty: {
      pt: "Nenhum modelo disponivel no momento.",
      es: "No hay modelos disponibles en este momento."
    },
    listError: {
      pt: "Nao foi possivel carregar os modelos.",
      es: "No fue posible cargar los modelos."
    },
    selectHint: {
      pt: "Selecione um modelo para visualizar e criar sua pagina.",
      es: "Selecciona un modelo para visualizar y crear tu pagina."
    },
    previewHeading: { pt: "Pre-visualizacão", es: "Previsualizacion" },
    previewEmpty: {
      pt: "Escolha um modelo para visualizar o design.",
      es: "Elige un modelo para visualizar el diseno."
    },
    formTitle: { pt: "Detalhes da nova pagina", es: "Detalles de la nueva pagina" },
    nameLabel: { pt: "Titulo da pagina", es: "Titulo de la pagina" },
    slugLabel: { pt: "Slug", es: "Slug" },
    slugHint: {
      pt: "Este slug completa o link publico do roteiro.",
      es: "Este slug completa el enlace publico del itinerario."
    },
    back: { pt: "Voltar", es: "Volver" },
    cancel: { pt: "Cancelar", es: "Cancelar" },
    create: { pt: "Criar pagina", es: "Crear pagina" }
  },
  dialogs: {
    duplicate: {
      title: { pt: "Duplicar página", es: "Duplicar página" },
      description: {
        pt: "Crie um rascunho copiando conteúdo e ajustando o slug.",
        es: "Crea un borrador copiando el contenido y ajustando el slug."
      },
      titleLabel: { pt: "Título", es: "Título" },
      titlePlaceholder: { pt: "Novo título", es: "Nuevo título" },
      slugLabel: { pt: "Slug", es: "Slug" },
      slugPlaceholder: { pt: "novo-slug", es: "nuevo-slug" },
      finalLink: { pt: "Link final", es: "Link final" },
      cancel: { pt: "Cancelar", es: "Cancelar" },
      confirm: { pt: "Duplicar", es: "Duplicar" }
    },
    deleteConfirm: {
      message: {
        pt: 'Tem certeza que deseja excluir "{title}"? Esta ação não pode ser desfeita.',
        es: '¿Seguro que deseas eliminar "{title}"? Esta acción no se puede deshacer.'
      }
    }
  },
  emptyStates: {
    noAgency: {
      prefix: { pt: "Crie uma agência primeiro em", es: "Crea una agencia primero en" },
      link: { pt: "Configuração da agência", es: "Configuración de la agencia" },
      suffix: { pt: "para poder criar páginas.", es: "para poder crear páginas." },
      cta: { pt: "Criar minha agência", es: "Crear mi agencia" }
    },
    noPages: {
      title: { pt: "Nenhuma página ainda.", es: "Aún no hay páginas." }
    }
  },
  table: {
    columns: {
      name: { pt: "Nome", es: "Nombre" },
      views: { pt: "Visualizações", es: "Visualizaciones" },
      ctaClicks: { pt: "Cliques CTA", es: "Clics CTA" },
      leads: { pt: "Leads", es: "Leads" },
      link: { pt: "Link", es: "Link" },
      status: { pt: "Status", es: "Estado" },
      actions: { pt: "Ações", es: "Acciones" }
    },
    badges: {
      default: { pt: "Padrão", es: "Predeterminado" }
    },
    premiumHints: {
      stats: { pt: "Funcionalidade premium. Faça upgrade.", es: "Funcionalidad premium. Haz upgrade." },
      leads: {
        pt: "Disponível a partir do plano Essencial. Faça upgrade para ver os leads por página.",
        es: "Disponible desde el plan Esencial. Haz upgrade para ver los leads por página."
      }
    },
    linkUnavailable: { pt: "Link disponível após publicar", es: "Link disponible después de publicar" }
  },
  labels: {
    planCurrentFallback: { pt: "seu plano atual", es: "tu plan actual" },
    creation: {
      titleBase: { pt: "Novo roteiro", es: "Nuevo itinerario" },
      slugBase: { pt: "novo-roteiro", es: "nuevo-itinerario" }
    },
    duplicateSuffix: {
      title: { pt: "cópia", es: "copia" },
      slug: { pt: "copia", es: "copia" }
    },
    statuses: {
      published: { pt: "Ativo", es: "Activo" },
      draft: { pt: "Rascunho", es: "Borrador" }
    }
  },
  messages: {
    loadError: {
      pt: "Não foi possível carregar as páginas.",
      es: "No fue posible cargar las páginas."
    },
    createAgencyRequired: {
      pt: "Crie uma agência antes de adicionar páginas.",
      es: "Crea una agencia antes de añadir páginas."
    },
    createPageError: {
      pt: "Não foi possível criar a página. Verifique se você está logado e possui acesso à agência.",
      es: "No fue posible crear la página. Verifica si iniciaste sesión y tienes acceso a la agencia."
    },
    templateLoadError: {
      pt: "Não foi possível carregar os modelos.",
      es: "No fue posible cargar los modelos."
    },
    templateSelectPrompt: {
      pt: "Selecione um modelo para continuar.",
      es: "Selecciona un modelo para continuar."
    },
    templateCreateSuccess: {
      pt: "Página criada a partir do modelo.",
      es: "Página creada desde la plantilla."
    },
    templateCreateError: {
      pt: "Não foi possível criar a página com este modelo.",
      es: "No fue posible crear la página con esta plantilla."
    },
    aiWip: {
      pt: "Funcionalidade em desenvolvimento.",
      es: "Funcionalidad en desarrollo."
    },
    duplicateSuccess: { pt: "Página duplicada.", es: "Página duplicada." },
    duplicateError: {
      pt: "Não foi possível duplicar. Verifique se o slug já existe ou se você está logado.",
      es: "No fue posible duplicar. Verifica si el slug ya existe o si iniciaste sesión."
    },
    selectAgency: { pt: "Selecione uma agência.", es: "Selecciona una agencia." },
    copySuccess: {
      pt: "Link copiado para a área de transferência.",
      es: "Link copiado al portapapeles."
    },
    copyError: {
      pt: "Não foi possível copiar o link.",
      es: "No fue posible copiar el enlace."
    },
    onlyPublishedDefault: {
      pt: "Apenas páginas publicadas podem ser padrão.",
      es: "Solo las páginas publicadas pueden ser predeterminadas."
    },
    setDefaultSuccess: {
      pt: '"{title}" definida como página padrão.',
      es: '"{title}" definida como página principal.'
    },
    setDefaultError: {
      pt: "Não foi possível definir a página padrão.",
      es: "No fue posible definir la página principal."
    },
    unpublishSuccess: {
      pt: '"{title}" movida para rascunho.',
      es: '"{title}" movida a borrador.'
    },
    unpublishError: {
      pt: "Não foi possível despublicar a página.",
      es: "No fue posible despublicar la página."
    },
    deleteSuccess: { pt: "Página excluída.", es: "Página eliminada." },
    deleteError: {
      pt: "Não foi possível excluir a página.",
      es: "No fue posible eliminar la página."
    }
  }
};

const viewCopy = localizeViewCopy(viewCopySource);

const pages = ref<Page[]>([]);
const pageStats = ref<Record<number, { visits: number; cta: number; whatsapp: number; leads: number }>>({});
const hasAgency = ref(false);
const errorMessage = ref("");
const message = ref("");
const duplicateDialogOpen = ref(false);
const createOptionsOpen = ref(false);
const snackbar = ref<{ open: boolean; text: string; tone: "success" | "error" }>({
  open: false,
  text: "",
  tone: "success"
});
const duplicateTitle = ref("");
const duplicateSlug = ref("");
const duplicateSourcePage = ref<Page | null>(null);
const planLimitDialog = ref<{ open: boolean; planLabel: string; limit: number | null }>({
  open: false,
  planLabel: "",
  limit: null
});
const planLimitHeading = computed(() => {
  const limit = planLimitDialog.value.limit;
  const limitPart = limit
    ? ` ${viewCopy.actions.planLimit.limitIntro} ${limit} ${viewCopy.actions.planLimit.limitUnit}`
    : "";
  return `${viewCopy.actions.planLimit.heading}${limitPart} ${viewCopy.actions.planLimit.planPrefix} `;
});

const currentAgencySlug = computed(() => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return agency?.slug || "";
});
const currentAgency = computed(() => {
  return agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId) || null;
});
const currentAgencyPrimaryDomain = agencyStore.currentPrimaryDomain;

watch(
  () => agencyStore.currentAgencyId,
  id => {
    if (id) {
      agencyStore.loadPrimaryDomain(id);
    }
  },
  { immediate: true }
);
const templateModal = ref<{
  open: boolean;
  loading: boolean;
  templates: PageTemplate[];
  error: string;
  selectedTemplate: PageTemplate | null;
  pageTitle: string;
  pageSlug: string;
  slugAuto: string;
  saving: boolean;
}>({
  open: false,
  loading: false,
  templates: [],
  error: "",
  selectedTemplate: null,
  pageTitle: "",
  pageSlug: "",
  slugAuto: "",
  saving: false
});
const templatePreviewConfig = computed(() => {
  if (!templateModal.value.selectedTemplate) return null;
  const brandingAgency = currentAgency.value;
  const digits = sanitizeDigits(brandingAgency?.cta_whatsapp || authStore.user?.whatsapp || "");
  const whatsappLink = templateModal.value.selectedTemplate
    ? buildWhatsappLink(digits, templateModal.value.selectedTemplate.name)
    : "";
  const logoUrl = brandingAgency?.logo_url || "";
  const primaryColor = brandingAgency?.primary_color || null;
  return applyTemplateBranding(templateModal.value.selectedTemplate.config_json, {
    logoUrl,
    whatsappLink,
    primaryColor,
    enforcePrimaryColor: !!primaryColor
  });
});
const templatePreviewDevice = ref<"desktop" | "mobile">("desktop");
const templatePreviewDeviceLocked = ref(false);
const setTemplatePreviewDevice = (device: "desktop" | "mobile", lock = false) => {
  if (!lock && templatePreviewDeviceLocked.value) return;
  if (templatePreviewDevice.value !== device) {
    templatePreviewDevice.value = device;
  }
  if (lock) {
    templatePreviewDeviceLocked.value = true;
  }
};
const templatePreviewContainer = ref<HTMLElement | null>(null);
const templatePreviewContent = ref<HTMLElement | null>(null);
const templatePreviewScale = ref(0.55);
const previewFullscreen = ref(false);
const isMobileViewport = ref(false);
const resetTemplatePreviewDevice = () => {
  templatePreviewDeviceLocked.value = false;
  templatePreviewDevice.value = isMobileViewport.value ? "mobile" : "desktop";
};
let previewViewportQuery: MediaQueryList | null = null;
let previewViewportListener: ((event: MediaQueryListEvent) => void) | null = null;
const basePreviewWidth = computed(() => (templatePreviewDevice.value === "desktop" ? 1440 : 384));
const templatePreviewContentHeight = ref(0);
const scaledPreviewHeight = computed(() => templatePreviewContentHeight.value * templatePreviewScale.value);
const updatePreviewViewportMatch = (matches?: boolean) => {
  const isMatch = typeof matches === "boolean" ? matches : previewViewportQuery?.matches ?? false;
  isMobileViewport.value = isMatch;
  if (!isMatch) {
    previewFullscreen.value = false;
  }
};
const setupPreviewViewportListener = () => {
  if (typeof window === "undefined" || !window.matchMedia) return;
  previewViewportQuery = window.matchMedia("(max-width: 768px)");
  updatePreviewViewportMatch(previewViewportQuery.matches);
  previewViewportListener = (event: MediaQueryListEvent) => updatePreviewViewportMatch(event.matches);
  if (previewViewportQuery.addEventListener) {
    previewViewportQuery.addEventListener("change", previewViewportListener);
  } else if (previewViewportListener) {
    previewViewportQuery.addListener(previewViewportListener);
  }
};
const teardownPreviewViewportListener = () => {
  if (previewViewportQuery && previewViewportListener) {
    if (previewViewportQuery.removeEventListener) {
      previewViewportQuery.removeEventListener("change", previewViewportListener);
    } else {
      previewViewportQuery.removeListener(previewViewportListener);
    }
  }
  previewViewportQuery = null;
  previewViewportListener = null;
};
const recomputePreviewScale = () => {
  if (!templateModal.value.open) return;
  const container = templatePreviewContainer.value;
  if (!container) return;
  const available = container.clientWidth;
  const baseWidth = basePreviewWidth.value;
  const scale = Math.min(available / baseWidth, 1);
  templatePreviewScale.value = scale > 0 ? scale : 1;
};
const templatePreviewStyle = computed(() => {
  const scale = templatePreviewScale.value;
  return {
    width: `${basePreviewWidth.value}px`,
    transform: `scale(${scale})`,
    transformOrigin: templatePreviewDevice.value === "mobile" ? "top center" : "top left"
  };
});
const templatePreviewWrapperStyle = computed(() => {
  const height = scaledPreviewHeight.value;
  if (!height) return {};
  return { height: `${height}px` };
});
watch(templatePreviewDevice, () => {
  nextTick(() => {
    recomputePreviewScale();
    if (templatePreviewContainer.value) {
      templatePreviewContainer.value.scrollTo({ top: 0 });
    }
  });
});

watch(isMobileViewport, value => {
  setTemplatePreviewDevice(value ? "mobile" : "desktop");
});
watch(
  () => templateModal.value.open,
  open => {
    if (open) {
      nextTick(recomputePreviewScale);
    } else {
      previewFullscreen.value = false;
    }
  }
);
watch(
  () => templatePreviewContainer.value,
  el => {
    if (!previewResizeObserver) return;
    previewResizeObserver.disconnect();
    if (el) {
      previewResizeObserver.observe(el);
      nextTick(recomputePreviewScale);
    }
  }
);
watch(
  () => templatePreviewContent.value,
  el => {
    previewContentObserver?.disconnect();
    if (!el) {
      templatePreviewContentHeight.value = 0;
      return;
    }
    templatePreviewContentHeight.value = el.offsetHeight;
    previewContentObserver = new ResizeObserver(entries => {
      if (!entries.length) return;
      templatePreviewContentHeight.value = entries[0].contentRect.height;
    });
    previewContentObserver.observe(el);
  }
);
const planKey = computed(() => (authStore.user?.plan || "free").toLowerCase());
const isFree = computed(() => planKey.value === "free");
const showLeadColumn = computed(() => planKey.value !== "essencial");
const hasLeadStatsAccess = computed(() => ["growth", "infinity", "teste"].includes(planKey.value));
const headerGridColumns = computed(() =>
  showLeadColumn.value
    ? "grid-cols-[1.2fr,0.9fr,0.9fr,0.8fr,1.6fr,0.8fr,1.9fr]"
    : "grid-cols-[1.2fr,0.9fr,0.9fr,1.6fr,0.8fr,1.9fr]"
);
const rowGridColumns = computed(() =>
  showLeadColumn.value
    ? "md:grid-cols-[1.2fr,0.9fr,0.9fr,0.8fr,1.6fr,0.8fr,1.9fr]"
    : "md:grid-cols-[1.2fr,0.9fr,0.9fr,1.6fr,0.8fr,1.9fr]"
);

const loadPages = async () => {
  errorMessage.value = "";
  await agencyStore.loadAgencies();
  hasAgency.value = !!agencyStore.currentAgencyId;
  if (!hasAgency.value) return;
  try {
    const res = await api.get<Page[]>("/pages", { params: { agency_id: agencyStore.currentAgencyId } });
    pages.value = res.data;
    await loadPageStats();
  } catch (err) {
    console.error(err);
    showSnackbar(viewCopy.messages.loadError, "error");
  }
};

const loadPageStats = async () => {
  if (!agencyStore.currentAgencyId) return;
  try {
    const res = await api.get<PageStatsSummary[]>("/stats/pages", { params: { agency_id: agencyStore.currentAgencyId } });
    const map: Record<number, { visits: number; cta: number; whatsapp: number; leads: number }> = {};
    res.data.forEach(item => {
      map[item.page_id] = {
        visits: item.visits ?? 0,
        cta: item.clicks_cta ?? 0,
        whatsapp: item.clicks_whatsapp ?? 0,
        leads: item.leads ?? 0
      };
    });
    pages.value.forEach(page => {
      if (!map[page.id]) {
        map[page.id] = { visits: 0, cta: 0, whatsapp: 0, leads: 0 };
      }
    });
    pageStats.value = map;
  } catch (err) {
    console.error(err);
  }
};

const loadTemplateOptions = async () => {
  templateModal.value.loading = true;
  templateModal.value.error = "";
  try {
    templateModal.value.templates = await listPageTemplates();
  } catch (err) {
    console.error(err);
    templateModal.value.error = viewCopy.messages.templateLoadError;
  } finally {
    templateModal.value.loading = false;
  }
};

const openTemplateModal = async () => {
  if (!agencyStore.currentAgencyId) {
    showSnackbar(viewCopy.messages.createAgencyRequired, "error");
    return;
  }
  templateModal.value.open = true;
  templateModal.value.selectedTemplate = null;
  templateModal.value.pageTitle = "";
  templateModal.value.pageSlug = "";
  templateModal.value.slugAuto = "";
  templateModal.value.error = "";
  previewFullscreen.value = false;
  resetTemplatePreviewDevice();
  if (!templateModal.value.templates.length) {
    await loadTemplateOptions();
  }
};

const closeTemplateModal = () => {
  templateModal.value.open = false;
  templateModal.value.selectedTemplate = null;
  templateModal.value.pageTitle = "";
  templateModal.value.pageSlug = "";
  templateModal.value.slugAuto = "";
  templateModal.value.error = "";
  templateModal.value.saving = false;
  previewFullscreen.value = false;
  resetTemplatePreviewDevice();
};

const selectTemplateForModal = (template: PageTemplate) => {
  templateModal.value.selectedTemplate = template;
  templateModal.value.pageTitle = template.name;
  const slug = slugify(template.name);
  templateModal.value.pageSlug = slug;
  templateModal.value.slugAuto = slug;
  templateModal.value.error = "";
};
const handleTemplateCardClick = (template: PageTemplate) => {
  if (isMobileViewport.value) return;
  selectTemplateForModal(template);
};
const handleTemplatePreview = (template: PageTemplate) => {
  selectTemplateForModal(template);
  if (isMobileViewport.value) {
    setTemplatePreviewDevice("mobile");
    previewFullscreen.value = true;
  }
};

const handleTemplateSlugInput = () => {
  templateModal.value.slugAuto = templateModal.value.pageSlug;
};
const closePreviewFullscreen = () => {
  previewFullscreen.value = false;
};

const createPageFromTemplateApi = async (templateId: number, title: string, slug: string) => {
  if (!agencyStore.currentAgencyId) {
    throw new Error(viewCopy.messages.createAgencyRequired);
  }
  const res = await api.post<Page>("/pages", {
    agency_id: agencyStore.currentAgencyId,
    title,
    slug,
    status: "draft",
    template_id: templateId
  });
  pages.value.push({ ...res.data });
  return res.data;
};

const submitTemplateModal = async () => {
  /* Form removed; delegate creation to useTemplateNow */
  useTemplateNow(templateModal.value.selectedTemplate!);
};

const useTemplateNow = async (template: PageTemplate) => {
  templateModal.value.selectedTemplate = template;
  templateModal.value.pageTitle = template.name;
  templateModal.value.pageSlug = template.slug;
  templateModal.value.slugAuto = template.slug;
  try {
    const page = await createPageFromTemplateApi(template.id, template.name, template.slug);
    showSnackbar(viewCopy.messages.templateCreateSuccess);
    closeTemplateModal();
    createOptionsOpen.value = false;
    router.push(`/admin/pages/${page.id}/edit`);
  } catch (err: any) {
    console.error(err);
    if (handlePlanLimitError(err)) {
      closeTemplateModal();
      createOptionsOpen.value = false;
      return;
    }
    const detail = err?.response?.data?.detail || err?.message;
    showSnackbar(detail || viewCopy.messages.templateCreateError, "error");
  }
};

const extractPlanLimitInfo = (err: unknown) => {
  const response = (err as any)?.response;
  if (!response) return null;
  const headers = response.headers || {};
  const getHeader = (key: string) => headers?.[key] ?? headers?.[key.toLowerCase()];
  const detail = typeof response.data?.detail === "string" ? response.data.detail : "";
  const detailLower = detail.toLowerCase();
  const code = String(getHeader("X-Error-Code") || "").toLowerCase();
  const isKnownCode = code === "trial_page_limit" || code === "plan_page_limit";
  if (!isKnownCode && !detailLower.includes("plano")) {
    return null;
  }
  let planKey = String(getHeader("X-Plan-Key") || "").toLowerCase();
  if (!planKey) {
    const planMatch = detailLower.match(/plano\s+([a-z]+)/);
    if (planMatch?.[1]) {
      planKey = planMatch[1];
    }
  }
  let planLabel = planKey ? getPlanLabel(planKey) : "";
  if (!planLabel && detail) {
    planLabel = detail;
  }
  const limitHeader = String(getHeader("X-Plan-Max-Pages") ?? "");
  let limit: number | null = null;
  if (limitHeader) {
    const parsed = Number.parseInt(limitHeader, 10);
    if (!Number.isNaN(parsed)) {
      limit = parsed;
    }
  }
  if (!limit) {
    const limitMatch = detailLower.match(/limite\s+de\s+(\d+)/);
    if (limitMatch?.[1]) {
      const parsed = Number.parseInt(limitMatch[1], 10);
      if (!Number.isNaN(parsed)) {
        limit = parsed;
      }
    }
  }
  if (!planLabel) {
    planLabel = viewCopy.labels.planCurrentFallback;
  }
  return { planLabel, limit };
};

const handlePlanLimitError = (err: unknown) => {
  const info = extractPlanLimitInfo(err);
  if (!info) return false;
  planLimitDialog.value.planLabel = info.planLabel;
  planLimitDialog.value.limit = info.limit ?? null;
  planLimitDialog.value.open = true;
  return true;
};

const buildDefaultTitleAndSlug = () => {
  const titleBase = viewCopy.labels.creation.titleBase;
  const slugBase = viewCopy.labels.creation.slugBase;

  const existingSlugs = new Set(
    pages.value
      .map(page => page.slug)
      .filter((slug): slug is string => Boolean(slug))
      .map(slug => slug.toLowerCase())
  );

  const usedNumbers = new Set<number>();
  const registerTitle = (value?: string | null) => {
    if (!value) return;
    const normalized = value.trim().toLowerCase();
    const regex = new RegExp(`^${titleBase.toLowerCase()}(?:\\s+(\\d+))?$`);
    const match = normalized.match(regex);
    if (!match) return;
    const number = match[1] ? Number.parseInt(match[1], 10) : 1;
    if (!Number.isNaN(number)) usedNumbers.add(number);
  };
  const registerSlug = (value?: string | null) => {
    if (!value) return;
    const match = value.toLowerCase().match(new RegExp(`^${slugBase}-(\\d+)$`));
    if (!match) return;
    const number = match[1] ? Number.parseInt(match[1], 10) : 1;
    if (!Number.isNaN(number)) usedNumbers.add(number);
  };

  pages.value.forEach(page => {
    registerTitle(page.title);
    registerSlug(page.slug);
  });

  let counter = 1;
  while (usedNumbers.has(counter)) {
    counter += 1;
  }

  let slugCandidate = `${slugBase}-${counter}`;
  while (existingSlugs.has(slugCandidate)) {
    counter += 1;
    slugCandidate = `${slugBase}-${counter}`;
  }

  return {
    title: `${titleBase} ${counter}`,
    slug: slugCandidate
  };
};

const openCreateModal = () => {
  if (!agencyStore.currentAgencyId) {
    showSnackbar(viewCopy.messages.createAgencyRequired, "error");
    return;
  }
  createOptionsOpen.value = true;
};

const closeCreateModal = () => {
  createOptionsOpen.value = false;
};

const createPageFromScratch = async () => {
  errorMessage.value = "";
  message.value = "";
  if (!agencyStore.currentAgencyId) {
    errorMessage.value = viewCopy.messages.createAgencyRequired;
    return;
  }
  try {
    const defaults = buildDefaultTitleAndSlug();
    const res = await api.post<Page>("/pages", {
      agency_id: agencyStore.currentAgencyId,
      title: defaults.title,
      slug: defaults.slug,
      status: "draft"
    });
    pages.value.push({ ...res.data });
    router.push(`/admin/pages/${res.data.id}/edit`);
    createOptionsOpen.value = false;
  } catch (err) {
    console.error(err);
    if (handlePlanLimitError(err)) {
      createOptionsOpen.value = false;
      return;
    }
    const detail = (err as any)?.response?.data?.detail;
    errorMessage.value = detail || viewCopy.messages.createPageError;
    createOptionsOpen.value = false;
  }
};

const showSnackbar = (text: string, tone: "success" | "error" = "success") => {
  snackbar.value = { open: true, text, tone };
  setTimeout(() => (snackbar.value.open = false), 4000);
};

const createPageFromTemplate = () => {
  createOptionsOpen.value = false;
  openTemplateModal();
};

const createPageWithAi = () => {
  showSnackbar(viewCopy.messages.aiWip);
};

const slugify = (value: string) =>
  value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .substring(0, 80) || `pagina-${Date.now()}`;

const buildDeleteConfirmMessage = (title: string) =>
  viewCopy.dialogs.deleteConfirm.message.replace("{title}", title);

const openDuplicateDialog = (page: Page) => {
  duplicateSourcePage.value = page;
  duplicateTitle.value = `${page.title} (${viewCopy.labels.duplicateSuffix.title})`;
  const baseSlug = page.slug
    ? `${page.slug}-${viewCopy.labels.duplicateSuffix.slug}`
    : duplicateTitle.value;
  duplicateSlug.value = slugify(baseSlug);
  duplicateDialogOpen.value = true;
};

const closeDuplicateDialog = () => {
  duplicateDialogOpen.value = false;
  duplicateTitle.value = "";
  duplicateSlug.value = "";
  duplicateSourcePage.value = null;
};

const autoSlugFromTitle = () => {
  if (!duplicateTitle.value) return;
  duplicateSlug.value = slugify(duplicateTitle.value);
};

const confirmDuplicate = async () => {
  if (!duplicateSourcePage.value) return;
  errorMessage.value = "";
  message.value = "";
  if (!agencyStore.currentAgencyId) {
    showSnackbar(viewCopy.messages.selectAgency, "error");
    return;
  }
  try {
    const fullPage =
      duplicateSourcePage.value.config_json !== undefined
        ? duplicateSourcePage.value
        : (await api.get<Page>(`/pages/${duplicateSourcePage.value.id}`)).data;
    const res = await api.post<Page>("/pages", {
      agency_id: agencyStore.currentAgencyId,
      title: duplicateTitle.value,
      slug: slugify(duplicateSlug.value),
      status: "draft",
      template_id: fullPage.template_id || null,
      config_json: fullPage.config_json || null
    });
    showSnackbar(viewCopy.messages.duplicateSuccess);
    closeDuplicateDialog();
    router.push(`/admin/pages/${res.data.id}/edit`);
  } catch (err) {
    console.error(err);
    if (handlePlanLimitError(err)) {
      closeDuplicateDialog();
      return;
    }
    showSnackbar(viewCopy.messages.duplicateError, "error");
  }
};

const normalizeHostUrl = (host: string | null | undefined) => {
  if (!host) return "";
  const trimmed = host.trim();
  if (!trimmed) return "";
  const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  return withProtocol.replace(/\/+$/, "");
};

const pagePublicUrl = (page: Page) => {
  if (!page.slug) return "";
  const customHost = normalizeHostUrl(currentAgencyPrimaryDomain.value);
  if (customHost) {
    return `${customHost}/${page.slug}`;
  }
  if (!currentAgencySlug.value) return "";
  return `${window.location.origin}/${currentAgencySlug.value}/${page.slug}`;
};

const copyLink = async (page: Page) => {
  const url = pagePublicUrl(page);
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    showSnackbar(viewCopy.messages.copySuccess);
  } catch {
    showSnackbar(viewCopy.messages.copyError, "error");
  }
};

const setDefaultPage = async (page: Page) => {
  if (page.status !== "published") {
    showSnackbar(viewCopy.messages.onlyPublishedDefault, "error");
    return;
  }
  try {
    await api.post(`/pages/${page.id}/set-default`);
    showSnackbar(viewCopy.messages.setDefaultSuccess.replace("{title}", page.title));
    pages.value = pages.value.map(p => ({ ...p, is_default: p.id === page.id }));
    const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
    if (agency) {
      agency.default_page_id = page.id;
    }
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    showSnackbar(detail || viewCopy.messages.setDefaultError, "error");
  }
};

const unpublishPage = async (page: Page) => {
  if (page.status !== "published") return;
  try {
    await api.post(`/pages/${page.id}/publish`, { publish: false });
    pages.value = pages.value.map(p => {
      if (p.id !== page.id) return p;
      return { ...p, status: "draft", is_default: false };
    });
    showSnackbar(viewCopy.messages.unpublishSuccess.replace("{title}", page.title));
    if (page.is_default) {
      const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
      if (agency) {
        agency.default_page_id = null;
      }
    }
  } catch (err) {
    console.error(err);
    showSnackbar(viewCopy.messages.unpublishError, "error");
  }
};

const deletePage = async (page: Page) => {
  if (!confirm(buildDeleteConfirmMessage(page.title))) {
    return;
  }
  try {
    await api.delete(`/pages/${page.id}`);
    pages.value = pages.value.filter(p => p.id !== page.id);
    showSnackbar(viewCopy.messages.deleteSuccess);
    if (page.is_default) {
      const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
      if (agency) {
        agency.default_page_id = null;
      }
    }
  } catch (err) {
    console.error(err);
    showSnackbar(viewCopy.messages.deleteError, "error");
  }
};

const getStatusLabel = (status: string) => {
  if (status === "published") {
    return viewCopy.labels.statuses.published;
  }
  if (status === "draft") {
    return viewCopy.labels.statuses.draft;
  }
  return status;
};
const getStatusClasses = (status: string) => {
  if (status === "published") {
    return "bg-emerald-50 text-[#2F9E49] dark:bg-[#2F9E49] dark:text-emerald-50";
  }
  if (status === "draft") {
    return "bg-amber-50 text-amber-600 dark:bg-amber-600 dark:text-amber-50";
  }
  return "bg-slate-100 text-slate-600 dark:bg-slate-600 dark:text-slate-100";
};
const getPageVisits = (pageId: number) => pageStats.value[pageId]?.visits ?? 0;
const getPageClicks = (pageId: number) => {
  const stats = pageStats.value[pageId];
  if (!stats) return 0;
  return (stats.cta ?? 0) + (stats.whatsapp ?? 0);
};
const getPageLeads = (pageId: number) => pageStats.value[pageId]?.leads ?? 0;

const goPlans = () => {
  router.push("/admin/planos");
};
let previewResizeObserver: ResizeObserver | null = null;
let previewContentObserver: ResizeObserver | null = null;
const handleWindowResize = () => recomputePreviewScale();
onMounted(() => {
  setupPreviewViewportListener();
  previewResizeObserver = new ResizeObserver(() => recomputePreviewScale());
  if (templatePreviewContainer.value) {
    previewResizeObserver.observe(templatePreviewContainer.value);
  }
  window.addEventListener("resize", handleWindowResize);
});
onBeforeUnmount(() => {
  teardownPreviewViewportListener();
  previewResizeObserver?.disconnect();
  previewContentObserver?.disconnect();
  window.removeEventListener("resize", handleWindowResize);
});

watch(
  () => templateModal.value.pageTitle,
  value => {
    if (!templateModal.value.open) return;
    if (!templateModal.value.pageSlug || templateModal.value.pageSlug === templateModal.value.slugAuto) {
      const slug = slugify(value);
      templateModal.value.pageSlug = slug;
      templateModal.value.slugAuto = slug;
    }
  }
);

onMounted(loadPages);
</script>

<style scoped>
.blurred-value {
  filter: blur(8px);
  opacity: 0.15;
  pointer-events: none;
  user-select: none;
}

.preview-scroll {
  padding-bottom: 2rem;
  overflow-x: hidden;
}

.preview-scale-wrapper {
  width: 100%;
  display: block;
  position: relative;
  overflow: hidden;
}

.preview-mobile-center {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.preview-scale {
  transition: transform 0.2s ease, width 0.2s ease;
  display: block;
}

@media (max-width: 768px) {
  :global(input),
  :global(textarea),
  :global(select) {
    font-size: 16px;
  }
}
</style>
