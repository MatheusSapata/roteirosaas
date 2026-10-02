<template>
  <div v-if="isBootstrappingPages" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8 md:px-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-border border-t-primary"></div>
  </div>
  <div v-else class="pages-reference w-full space-y-6 px-4 py-4 md:px-8 md:py-8">
    <div class="pl-head">
      <div>
        <p class="pl-eyebrow">Conteúdo</p>
        <h1 class="pl-title">{{ viewCopy.header.eyebrow }}</h1>
        <p class="pl-sub">Crie, publique e acompanhe as páginas de venda da sua agência.</p>
      </div>
      <button
        @click="openCreateModal"
        class="pl-btn pl-btn-primary"
        :class="!canEditPages ? 'cursor-not-allowed opacity-50' : ''"
        :disabled="!hasAgency"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14" /></svg>
        {{ viewCopy.header.newPage }}
      </button>
    </div>

    <div class="pl-stats">
      <article class="pl-stat">
        <span class="pl-icon tone-success"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg></span>
        <div><p class="pl-stat-k">Páginas no ar</p><p class="pl-stat-v">{{ publishedPagesCount }}<small>de {{ pages.length }}</small></p></div>
      </article>
      <article class="pl-stat">
        <span class="pl-icon tone-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg></span>
        <div><p class="pl-stat-k">Visitas</p><p class="pl-stat-v">{{ totalPageVisits.toLocaleString("pt-BR") }}</p></div>
      </article>
      <article class="pl-stat">
        <span class="pl-icon tone-warning"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m4 3 7.5 17 2.4-7.1L21 10.5 4 3z" /></svg></span>
        <div><p class="pl-stat-k">Cliques</p><p class="pl-stat-v">{{ totalPageClicks.toLocaleString("pt-BR") }}<small>{{ formatRate(totalPageClicks, totalPageVisits) }}</small></p></div>
      </article>
      <article class="pl-stat">
        <span class="pl-icon tone-violet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M19 8v6M22 11h-6" /></svg></span>
        <div><p class="pl-stat-k">Leads</p><p class="pl-stat-v">{{ totalPageLeads.toLocaleString("pt-BR") }}<small>{{ formatRate(totalPageLeads, totalPageVisits) }} das visitas</small></p></div>
      </article>
    </div>

    <div class="pl-toolbar">
      <label class="pl-search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
        <input v-model="searchQuery" type="text" :placeholder="viewCopy.table.searchPlaceholder" />
      </label>
      <div class="pl-filters" role="group" aria-label="Situação">
        <button type="button" class="pl-filter" :class="{ on: statusFilter === '' }" @click="statusFilter = ''">Todas <span>{{ pages.length }}</span></button>
        <button type="button" class="pl-filter" :class="{ on: statusFilter === 'published' }" @click="statusFilter = 'published'">Publicadas <span>{{ publishedPagesCount }}</span></button>
        <button type="button" class="pl-filter" :class="{ on: statusFilter === 'draft' }" @click="statusFilter = 'draft'">Rascunhos <span>{{ pages.length - publishedPagesCount }}</span></button>
      </div>
      <span class="pl-grow"></span>
      <select v-model="sortFilter" class="pl-select" aria-label="Ordenar">
        <option value="recent">{{ viewCopy.table.filters.sortRecent }}</option>
        <option value="name">{{ viewCopy.table.filters.sortName }}</option>
        <option value="visits">{{ viewCopy.table.filters.sortVisits }}</option>
        <option value="leads">{{ viewCopy.table.filters.sortLeads }}</option>
      </select>
    </div>

    <teleport to="body">
      <div
        v-if="templateModal.open"
        class="app-modal-overlay fixed inset-0 z-[200] flex items-center justify-center px-4 py-6"
      >
        <div class="pages-modal-shell relative w-full max-w-7xl">
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
                <p class="text-sm text-slate-500 dark:text-white/70">
                  {{ viewCopy.templateModal.previewDescription }}
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
                    <p class="text-sm text-slate-500 dark:text-white/70">
                      {{ viewCopy.templateModal.previewDescription }}
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
      class="flex flex-col gap-3 rounded-xl border border-border bg-status-warning px-4 py-3 text-sm text-status-warning-foreground sm:flex-row sm:items-center sm:justify-between"
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
        class="inline-flex items-center justify-center rounded-lg bg-status-warning-foreground px-4 py-2 text-sm font-semibold text-white shadow-soft"
      >
        {{ viewCopy.emptyStates.noAgency.cta }}
      </router-link>
    </div>

    <teleport to="body">
      <div
        v-if="createOptionsOpen"
        class="app-modal-overlay fixed inset-0 z-[200] flex items-center justify-center px-4 py-8"
      >
        <div class="pages-modal-shell w-full max-w-4xl p-8">
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

          <div class="grid gap-4 md:grid-cols-2">
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

          </div>

        </div>
      </div>
    </teleport>

    <transition name="fade">
      <div v-if="planLimitDialog.open" class="app-modal-overlay fixed inset-0 z-40 flex items-center justify-center px-4">
        <div class="pages-modal-shell w-full max-w-lg p-8">
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

    <div v-if="filteredPages.length" class="pl-cards">
      <article v-for="(page, index) in filteredPages" :key="page.id" class="pl-card">
        <div class="pl-cover" :style="coverStyle(page, index)">
          <div class="pl-cover-badges">
            <span class="pl-pill"><i :class="page.status === 'published' ? 'dot-on' : 'dot-off'"></i>{{ getStatusLabel(page.status) }}</span>
            <span v-if="page.is_default" class="pl-pill">
              <svg viewBox="0 0 24 24" class="pl-star"><path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1Z" /></svg>
              {{ viewCopy.table.badges.default }}
            </span>
          </div>
          <div class="pl-cover-title">
            <b>{{ page.title }}</b>
          </div>
        </div>
        <div class="pl-body">
          <div class="pl-link">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M2 12h20" /></svg>
            <template v-if="page.status === 'published' && pagePublicUrl(page)">
              <a :href="pagePublicUrl(page)" target="_blank" rel="noopener">{{ pagePublicUrl(page) }}</a>
              <button type="button" class="pl-copy" @click="copyLink(page)">{{ viewCopy.actions.copy.button }}</button>
            </template>
            <span v-else>{{ viewCopy.table.linkUnavailable }}</span>
          </div>
          <div class="pl-metrics">
            <div><p>Visitas</p><b>{{ getPageVisits(page.id).toLocaleString("pt-BR") }}</b></div>
            <div><p>Cliques</p><b>{{ getPageClicks(page.id).toLocaleString("pt-BR") }}</b></div>
            <div v-if="showLeadColumn"><p>Leads</p><b>{{ getPageLeads(page.id).toLocaleString("pt-BR") }}</b></div>
          </div>
          <div class="pl-foot">
            <span class="pl-grow pl-conv">
              <template v-if="getPageVisits(page.id) > 0">
                <span class="pl-badge">{{ formatRate(getPageLeads(page.id), getPageVisits(page.id)) }}</span> viram lead
              </template>
              <template v-else>Sem visitas ainda</template>
            </span>
            <a
              v-if="pagePublicUrl(page)"
              :href="pagePublicUrl(page)"
              target="_blank"
              rel="noopener"
              class="pl-icon-btn"
              :title="viewCopy.actions.rowMenu.viewPage"
              :aria-label="viewCopy.actions.rowMenu.viewPage"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></svg>
            </a>
            <div class="pl-menu-wrap">
              <button type="button" class="pl-icon-btn" aria-label="Mais ações" :aria-expanded="openMenuId === page.id" @click.stop="toggleMenu(page.id)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="5" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="12" cy="19" r="1" /></svg>
              </button>
              <div v-if="openMenuId === page.id" class="pl-menu" @click.stop>
                <button type="button" :disabled="!canEditPages" @click="runMenu(() => openDuplicateDialog(page))">{{ viewCopy.actions.rowMenu.duplicate }}</button>
                <button
                  type="button"
                  :disabled="page.status !== 'published' || page.is_default || !canEditPages"
                  @click="runMenu(() => setDefaultPage(page))"
                >
                  {{ viewCopy.actions.rowMenu.setDefault }}
                </button>
                <button type="button" :disabled="page.status !== 'published'" @click="runMenu(() => unpublishPage(page))">{{ viewCopy.actions.rowMenu.unpublish }}</button>
                <button v-if="canDeletePages" type="button" class="danger" @click="runMenu(() => deletePage(page))">{{ viewCopy.actions.rowMenu.delete }}</button>
              </div>
            </div>
            <router-link v-if="canEditPages" :to="`/admin/pages/${page.id}/edit`" class="pl-edit">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z" /></svg>
              {{ viewCopy.actions.rowMenu.edit }}
            </router-link>
          </div>
        </div>
      </article>
    </div>
    <div v-else class="pl-empty">
      {{ viewCopy.emptyStates.noPages.title }}
    </div>

    <div
      v-if="duplicateDialogOpen"
      class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4"
      role="dialog"
      aria-modal="true"
    >
      <div class="pages-modal-shell duplicate-modal w-full max-w-md p-6">
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
      class="app-snackbar-layer fixed bottom-6 left-1/2 z-[300] max-w-[90vw] -translate-x-1/2 rounded-3xl px-5 py-3 text-sm font-semibold text-white shadow-2xl sm:max-w-md"
      :class="snackbar.tone === 'error' ? 'bg-rose-600' : 'bg-slate-900'"
    >
      {{ snackbar.text }}
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { storeToRefs } from "pinia";
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
import { resolveMediaUrl } from "../../utils/media";
import { hasAnyPermission } from "../../utils/permissions";

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
const { currentPrimaryDomain } = storeToRefs(agencyStore);
const authStore = useAuthStore();
const publicSiteBaseUrl = (
  (import.meta.env.VITE_PUBLIC_SITE_URL as string | undefined)?.trim() || "https://roteiroonline.com"
).replace(/\/+$/, "");
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
    newPage: { pt: "Nova Página", es: "Nueva página" }
  },
  actions: {
    createModal: {
      eyebrow: { pt: "Novo roteiro", es: "Nuevo itinerario" },
      title: { pt: "Como deseja começar?", es: "¿Cómo deseas empezar?" },
      description: {
        pt: "Escolha entre montar do zero ou começar por um modelo pronto.",
        es: "Elige entre construir desde cero o empezar con un modelo listo."
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
      limitUnit: { pt: "páginas publicadas", es: "páginas publicadas" },
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
    previewHeading: { pt: "Preview visual", es: "Vista previa visual" },
    previewDescription: {
      pt: "Veja como o roteiro ficará antes de usar este modelo.",
      es: "Mira cómo quedará el itinerario antes de usar este modelo."
    },
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
    searchPlaceholder: { pt: "Buscar página...", es: "Buscar página..." },
    countLabel: { pt: "páginas", es: "páginas" },
    filters: {
      statusAll: { pt: "Todos os status", es: "Todos los estados" },
      sortRecent: { pt: "Mais recentes", es: "Más recientes" },
      sortName: { pt: "Nome", es: "Nombre" },
      sortVisits: { pt: "Mais visitadas", es: "Más visitadas" },
      sortLeads: { pt: "Mais leads", es: "Más leads" }
    },
    columns: {
      name: { pt: "Nome", es: "Nombre" },
      views: { pt: "Visual.", es: "Visualizaciones" },
      ctaClicks: { pt: "Cliques", es: "Clics" },
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
      published: { pt: "Publicada", es: "Publicada" },
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
const searchQuery = ref("");
const statusFilter = ref("");
const sortFilter = ref<"recent" | "name" | "visits" | "leads">("recent");
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
const currentAgencyPrimaryDomain = currentPrimaryDomain;

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
const canEditPages = computed(() => {
  const user = authStore.user;
  if (!user) return true;
  if (user.is_owner ?? true) return true;
  if ((user.role || "member").toLowerCase() === "admin") return true;
  const effective = user.effective_permissions || [];
  return hasAnyPermission(effective, ["pages_editor"]);
});
const canDeletePages = computed(() => {
  const user = authStore.user;
  if (!user) return true;
  const role = (user.role || "member").toLowerCase();
  if (role === "editor") return false;
  return canEditPages.value;
});
const memberPagesReadOnlyMessage = "Seu perfil é visualizador de páginas.";
const editorDeleteBlockedMessage = "Perfil Editor não pode excluir páginas.";
const showLeadColumn = computed(() => true);
const hasLeadStatsAccess = computed(() => true);
const isBootstrappingPages = ref(true);
const headerGridColumns = computed(() =>
  showLeadColumn.value
    ? "grid-cols-[1.78fr,0.54fr,0.54fr,0.54fr,1.73fr,0.62fr,1.05fr]"
    : "grid-cols-[1.78fr,0.54fr,0.54fr,1.73fr,0.62fr,1.05fr]"
);
const rowGridColumns = computed(() =>
  showLeadColumn.value
    ? "md:grid-cols-[1.78fr,0.54fr,0.54fr,0.54fr,1.73fr,0.62fr,1.05fr]"
    : "md:grid-cols-[1.78fr,0.54fr,0.54fr,1.73fr,0.62fr,1.05fr]"
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

const bootstrapPages = async () => {
  try {
    await loadPages();
  } finally {
    isBootstrappingPages.value = false;
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
  const slug = buildUniqueAgencySlug(template.name);
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

const buildUniqueAgencySlug = (raw: string) => {
  const base = slugify(raw);
  const existing = new Set(
    pages.value
      .map(page => (page.slug || "").toLowerCase().trim())
      .filter(Boolean)
  );
  if (!existing.has(base)) return base;
  let counter = 1;
  let candidate = `${base}-${counter}`;
  while (existing.has(candidate)) {
    counter += 1;
    candidate = `${base}-${counter}`;
  }
  return candidate;
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
  const selectedTitle = (templateModal.value.pageTitle || template.name || "").trim() || template.name;
  const selectedSlug = buildUniqueAgencySlug((templateModal.value.pageSlug || template.slug || selectedTitle || "").trim());
  templateModal.value.pageTitle = selectedTitle;
  templateModal.value.pageSlug = selectedSlug;
  templateModal.value.slugAuto = selectedSlug;
  try {
    const page = await createPageFromTemplateApi(template.id, selectedTitle, selectedSlug);
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
  if (!canEditPages.value) {
    showSnackbar(memberPagesReadOnlyMessage, "error");
    return;
  }
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
  if (!canEditPages.value) {
    showSnackbar(memberPagesReadOnlyMessage, "error");
    return;
  }
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
  if (!canEditPages.value) {
    showSnackbar(memberPagesReadOnlyMessage, "error");
    return;
  }
  createOptionsOpen.value = false;
  openTemplateModal();
};

const createPageWithAi = () => {
  if (!canEditPages.value) {
    showSnackbar(memberPagesReadOnlyMessage, "error");
    return;
  }
  showSnackbar(viewCopy.messages.aiWip);
};

const slugify = (value: string) =>
  value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    || `pagina-${Date.now()}`;

const buildDeleteConfirmMessage = (title: string) =>
  viewCopy.dialogs.deleteConfirm.message.replace("{title}", title);

const openDuplicateDialog = (page: Page) => {
  if (!canEditPages.value) {
    showSnackbar(memberPagesReadOnlyMessage, "error");
    return;
  }
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
  return `${publicSiteBaseUrl}/${currentAgencySlug.value}/${page.slug}`;
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
  if (!canEditPages.value) {
    showSnackbar(memberPagesReadOnlyMessage, "error");
    return;
  }
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
  if (!canDeletePages.value) {
    const role = (authStore.user?.role || "member").toLowerCase();
    showSnackbar(role === "editor" ? editorDeleteBlockedMessage : memberPagesReadOnlyMessage, "error");
    return;
  }
  if (!canEditPages.value) {
    showSnackbar(memberPagesReadOnlyMessage, "error");
    return;
  }
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
    return "status-ativo";
  }
  if (status === "draft") {
    return "status-inativo";
  }
  return "status-inativo";
};
const getPageVisits = (pageId: number) => pageStats.value[pageId]?.visits ?? 0;
const getPageClicks = (pageId: number) => {
  const stats = pageStats.value[pageId];
  if (!stats) return 0;
  return (stats.cta ?? 0) + (stats.whatsapp ?? 0);
};
const getPageLeads = (pageId: number) => pageStats.value[pageId]?.leads ?? 0;
const getPageHeroThumbnail = (page: Page) => {
  const config = page.config_json as any;
  const sections = Array.isArray(config?.sections) ? config.sections : [];
  const hero = sections.find((section: any) => section?.type === "hero");
  const raw =
    (typeof hero?.backgroundImage === "string" && hero.backgroundImage) ||
    (typeof hero?.image === "string" && hero.image) ||
    (typeof hero?.bannerImage === "string" && hero.bannerImage) ||
    "";
  if (!raw) return "";
  return resolveMediaUrl(raw) || raw;
};

const filteredPages = computed(() => {
  const term = searchQuery.value.trim().toLowerCase();
  const filtered = pages.value.filter(page => {
    const matchesTerm = !term || page.title.toLowerCase().includes(term) || (page.slug || "").toLowerCase().includes(term);
    const matchesStatus = !statusFilter.value || page.status === statusFilter.value;
    return matchesTerm && matchesStatus;
  });

  const sorted = [...filtered];
  if (sortFilter.value === "name") {
    sorted.sort((a, b) => a.title.localeCompare(b.title, "pt-BR"));
    return sorted;
  }
  if (sortFilter.value === "visits") {
    sorted.sort((a, b) => getPageVisits(b.id) - getPageVisits(a.id));
    return sorted;
  }
  if (sortFilter.value === "leads") {
    sorted.sort((a, b) => getPageLeads(b.id) - getPageLeads(a.id));
    return sorted;
  }
  sorted.sort((a, b) => {
    const left = a.created_at ? new Date(a.created_at).getTime() : 0;
    const right = b.created_at ? new Date(b.created_at).getTime() : 0;
    if (right !== left) return right - left;
    return b.id - a.id;
  });
  return sorted;
});

const publishedPagesCount = computed(() => pages.value.filter(page => page.status === "published").length);
const totalPageClicks = computed(() => pages.value.reduce((total, page) => total + getPageClicks(page.id), 0));
const formatRate = (part: number, total: number) => {
  if (!total) return "0%";
  return `${((part / total) * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
};
const coverGradients = [
  "linear-gradient(135deg,#1e3a5f,#3b6e8f 55%,#d9a066)",
  "linear-gradient(135deg,#0f4c5c,#1f8a8a 55%,#f2c14e)",
  "linear-gradient(135deg,#2b5876,#4e9fbf 55%,#f6d365)",
  "linear-gradient(135deg,#0c1f18,#12302a 55%,#1de9a0)"
];
const coverStyle = (page: Page, index: number) => {
  const thumb = getPageHeroThumbnail(page);
  if (thumb) return { backgroundImage: `url("${thumb}")` };
  return { backgroundImage: coverGradients[index % coverGradients.length] };
};
const openMenuId = ref<number | null>(null);
const toggleMenu = (id: number) => {
  openMenuId.value = openMenuId.value === id ? null : id;
};
const runMenu = (action: () => unknown) => {
  openMenuId.value = null;
  action();
};
const closeMenuOnOutside = () => {
  openMenuId.value = null;
};
const totalPageVisits = computed(() => pages.value.reduce((total, page) => total + getPageVisits(page.id), 0));
const totalPageLeads = computed(() => pages.value.reduce((total, page) => total + getPageLeads(page.id), 0));

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
  document.addEventListener("click", closeMenuOnOutside);
});
onBeforeUnmount(() => {
  teardownPreviewViewportListener();
  previewResizeObserver?.disconnect();
  previewContentObserver?.disconnect();
  window.removeEventListener("resize", handleWindowResize);
  document.removeEventListener("click", closeMenuOnOutside);
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

onMounted(bootstrapPages);
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

.pages-reference {
  --verde: var(--primary);
  --verde-border: color-mix(in srgb, var(--primary) 30%, var(--border));
  --surface: var(--card);
  --text: var(--foreground);
  --text-2: var(--card-foreground);
  --text-3: var(--muted-foreground);
  color: var(--foreground);
}

.page-eyebrow,
.pages-summary-label {
  color: var(--muted-foreground);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.page-heading {
  color: var(--foreground);
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 650;
  letter-spacing: -0.4px;
}

.page-description {
  margin-top: 5px;
  color: var(--muted-foreground);
  font-size: 13px;
}

.pages-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.pages-summary-card {
  position: relative;
  overflow: hidden;
  display: flex;
  min-height: 122px;
  flex-direction: column;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--card);
  padding: 18px;
  box-shadow: var(--shadow-soft);
}

.pages-summary-card::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--summary-color, var(--primary));
  content: "";
}

.pages-summary-card--published {
  --summary-color: var(--status-success-foreground);
}

.pages-summary-card--visits {
  --summary-color: var(--status-info-foreground);
}

.pages-summary-card--leads {
  --summary-color: var(--chart-6);
}

.pages-summary-card strong {
  margin-top: 10px;
  color: var(--foreground);
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 650;
}

.pages-summary-helper {
  margin-top: 3px;
  color: var(--muted-foreground);
  font-size: 12px;
}

.pages-modal-shell {
  border: 1px solid var(--border);
  border-radius: var(--radius-2xl);
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-elegant);
}

.pages-modal-shell :deep(.text-slate-900),
.pages-modal-shell :deep(.text-slate-800),
.pages-modal-shell :deep(.text-slate-700) {
  color: var(--foreground) !important;
}

.pages-modal-shell :deep(.text-slate-600),
.pages-modal-shell :deep(.text-slate-500),
.pages-modal-shell :deep(.text-slate-400) {
  color: var(--muted-foreground) !important;
}

.pages-modal-shell :deep(.border-slate-100),
.pages-modal-shell :deep(.border-slate-200),
.pages-modal-shell :deep(.border-slate-300) {
  border-color: var(--border) !important;
}

.pages-modal-shell :deep(.bg-white) {
  background-color: var(--card) !important;
}

.pages-modal-shell :deep(.bg-slate-50) {
  background-color: var(--muted) !important;
}

.pages-modal-shell :deep(input),
.pages-modal-shell :deep(select) {
  border-color: var(--input) !important;
  background: var(--background);
  color: var(--foreground);
}

.pages-modal-shell :deep(input::placeholder) {
  color: var(--muted-foreground);
}

.pages-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.pages-toolbar-top {
  display: contents;
}

.pages-toolbar-filters {
  display: contents;
}

.table-card {
  border-color: var(--border) !important;
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-soft);
}

.table-card > div:first-child {
  border-bottom-color: color-mix(in srgb, var(--border) 45%, transparent) !important;
  background: color-mix(in srgb, var(--muted) 45%, var(--card));
  color: var(--muted-foreground);
}

.pages-table-body > .page-table-row + .page-table-row {
  border-top: 1px solid color-mix(in srgb, var(--border) 38%, transparent) !important;
}

.page-table-row {
  border-color: var(--border);
  background: var(--card);
  color: var(--card-foreground);
}

.page-table-row:hover {
  background: color-mix(in srgb, var(--accent) 45%, var(--card));
}

.page-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: color-mix(in srgb, var(--primary) 10%, var(--card));
  border: 1px solid color-mix(in srgb, var(--primary) 25%, var(--border));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.page-icon svg {
  width: 14px;
  height: 14px;
  stroke: var(--primary);
}

.stat-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.stat-visits {
  background: var(--status-success);
  color: var(--status-success-foreground);
}

.stat-clicks {
  background: color-mix(in srgb, var(--chart-8) 10%, var(--card));
  color: var(--chart-8);
}

.stat-leads {
  background: color-mix(in srgb, var(--chart-6) 10%, var(--card));
  color: var(--chart-6);
}

.stat-zero {
  background: var(--muted);
  color: var(--muted-foreground);
}

.copy-btn {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted-foreground);
  background: var(--muted);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 3px 8px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.copy-btn:hover {
  background: color-mix(in srgb, var(--primary) 10%, var(--card));
  border-color: color-mix(in srgb, var(--primary) 25%, var(--border));
  color: var(--primary);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 999px;
  width: fit-content;
  max-width: max-content;
  align-self: center;
  line-height: 1;
  white-space: nowrap;
}

.status-badge::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-ativo {
  background: var(--status-success);
  color: var(--status-success-foreground);
}

.status-ativo::before {
  background: var(--status-success-foreground);
}

.status-inativo {
  background: var(--status-warning);
  color: var(--status-warning-foreground);
}

.status-inativo::before {
  background: var(--status-warning-foreground);
}

.act-btn {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  flex-shrink: 0;
  background: transparent;
  color: var(--muted-foreground);
}

.act-btn svg {
  width: 16px;
  height: 16px;
}

@media (min-width: 768px) {
  .page-actions-row {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: nowrap;
    gap: 4px;
  }
}

.act-btn.dup:hover,
.act-btn.edit:hover,
.act-btn.view:hover {
  background: color-mix(in srgb, var(--primary) 10%, var(--card));
  color: var(--primary);
}

.act-btn.share:hover {
  background: color-mix(in srgb, var(--chart-8) 10%, var(--card));
  color: var(--chart-8);
}

.act-btn.fav:hover {
  background: var(--status-warning);
  color: var(--status-warning-foreground);
}

.act-btn.fav.is-active {
  background: var(--status-warning);
  color: var(--status-warning-foreground);
}

.act-btn.del:hover {
  background: color-mix(in srgb, var(--destructive) 8%, var(--card));
  color: var(--destructive);
}

@media (max-width: 767px) {
  .page-actions-row {
    width: 100%;
    justify-content: space-between;
    gap: 6px;
    flex-wrap: nowrap;
  }

  .act-btn {
    width: 30px;
    height: 30px;
    border-radius: 8px;
  }

  .act-btn svg {
    width: 18px;
    height: 18px;
  }
}

.search-wrap {
  position: relative;
  flex: 1;
  min-width: 200px;
  max-width: 500px;
}

.search-wrap svg {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  width: 15px;
  height: 15px;
  stroke: var(--text-3);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 9px 12px 9px 34px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 13px;
  color: var(--text);
  background: var(--surface);
  outline: none;
  transition: border-color 0.15s;
}

.search-input:focus,
.filter-select:focus {
  border-color: var(--verde-border);
}

.search-input::placeholder {
  color: var(--text-3);
}

.filter-select {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-2);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 9px 12px;
  cursor: pointer;
  outline: none;
}

.filter-select option {
  background: var(--popover);
  color: var(--popover-foreground);
}

.toolbar-count {
  font-size: 13px;
  color: var(--text-3);
  margin-left: auto;
  white-space: nowrap;
}

@media (min-width: 768px) {
  .link-status-mobile {
    display: none !important;
  }
}

@media (max-width: 768px) {
  :global(input),
  :global(textarea),
  :global(select) {
    font-size: 16px;
  }

  .pages-toolbar {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .pages-toolbar-top {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .search-wrap {
    max-width: 100%;
    min-width: 0;
    flex: 1 1 auto;
  }

  .toolbar-count {
    margin-left: 0;
    flex: 0 0 auto;
  }

  .pages-toolbar-filters {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .pages-toolbar-filters .filter-select {
    width: 100%;
  }

  .pages-summary-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 520px) {
  .pages-summary-grid {
    grid-template-columns: 1fr;
  }
}

/* Redesign: lista de páginas em cartões */
.pl-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.pl-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: color-mix(in srgb, var(--muted-foreground) 80%, transparent); }
.pl-title { margin-top: 4px; font-family: var(--font-display); font-size: 30px; line-height: 38px; font-weight: 600; color: var(--foreground); }
.pl-sub { margin-top: 4px; font-size: 14px; color: var(--muted-foreground); }
.pl-btn { display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 18px; border-radius: 999px; font-size: 13.5px; font-weight: 600; }
.pl-btn svg { width: 16px; height: 16px; }
.pl-btn-primary { background: var(--primary); color: var(--primary-foreground); }
.pl-btn-primary:hover { background: color-mix(in srgb, var(--primary) 88%, black); }
.pl-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.pl-stat { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.pl-icon { display: grid; place-items: center; width: 40px; height: 40px; flex-shrink: 0; border-radius: 999px; }
.pl-icon svg { width: 18px; height: 18px; }
.tone-success { background: var(--status-success); color: var(--status-success-foreground); }
.tone-info { background: var(--status-info); color: var(--status-info-foreground); }
.tone-warning { background: var(--status-warning); color: var(--status-warning-foreground); }
.tone-violet { background: var(--status-violet); color: var(--status-violet-foreground); }
.pl-stat-k { font-size: 12.5px; color: var(--muted-foreground); }
.pl-stat-v { font-family: var(--font-display); font-size: 20px; line-height: 26px; font-weight: 600; color: var(--foreground); font-variant-numeric: tabular-nums; }
.pl-stat-v small { margin-left: 6px; font-family: var(--font-sans); font-size: 12px; font-weight: 500; color: var(--muted-foreground); }
.pl-toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.pl-search { display: flex; align-items: center; gap: 8px; flex: 0 1 340px; height: 40px; padding: 0 16px; border-radius: 999px; background: var(--card); box-shadow: var(--shadow-card); color: var(--muted-foreground); }
.pl-search svg { width: 16px; height: 16px; flex-shrink: 0; }
.pl-search input { flex: 1; min-width: 0; border: 0; background: transparent; outline: none; font-size: 13.5px; color: var(--foreground); }
.pl-filters { display: flex; gap: 4px; }
.pl-filter { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px; border-radius: 999px; font-size: 13px; font-weight: 600; color: var(--muted-foreground); }
.pl-filter span { border-radius: 999px; background: var(--muted); padding: 0 7px; font-size: 11px; }
.pl-filter.on { background: var(--card); color: var(--foreground); box-shadow: var(--shadow-card); }
.pl-filter.on span { background: var(--accent); color: var(--accent-foreground); }
.pl-grow { flex: 1; }
.pl-select { height: 36px; border: 0; border-radius: 999px; background: var(--card); box-shadow: var(--shadow-card); padding: 0 32px 0 14px; font-size: 13px; font-weight: 600; color: var(--foreground); }
.pl-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.pl-card { display: flex; flex-direction: column; overflow: visible; border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.pl-cover { position: relative; height: 132px; overflow: hidden; border-radius: 20px 20px 0 0; background-size: cover; background-position: center; }
.pl-cover::after { content: ""; position: absolute; inset: 0; background: linear-gradient(to top, rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0) 65%); }
.pl-cover-badges { position: absolute; top: 12px; left: 12px; right: 12px; z-index: 1; display: flex; justify-content: space-between; gap: 8px; }
.pl-pill { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; background: rgba(255, 255, 255, 0.92); padding: 3px 10px; font-size: 11.5px; font-weight: 600; color: #111814; }
.pl-pill i { width: 7px; height: 7px; border-radius: 999px; }
.dot-on { background: #12b981; }
.dot-off { background: #f59e0b; }
.pl-star { width: 13px; height: 13px; fill: #a35d06; }
.pl-cover-title { position: absolute; right: 16px; bottom: 12px; left: 16px; z-index: 1; color: #fff; }
.pl-cover-title b { display: block; overflow: hidden; font-family: var(--font-display); font-size: 18px; font-weight: 600; white-space: nowrap; text-overflow: ellipsis; }
.pl-body { display: flex; flex: 1; flex-direction: column; gap: 14px; padding: 14px 16px 16px; }
.pl-link { display: flex; align-items: center; gap: 8px; min-height: 36px; border-radius: 12px; background: var(--muted); padding: 6px 8px 6px 12px; font-size: 12.5px; color: var(--muted-foreground); }
.pl-link svg { width: 14px; height: 14px; flex-shrink: 0; }
.pl-link a, .pl-link > span { flex: 1; min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.pl-link a { color: var(--foreground); }
.pl-copy { border-radius: 999px; background: var(--card); padding: 4px 10px; font-size: 12px; font-weight: 600; color: var(--foreground); box-shadow: var(--shadow-card); }
.pl-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.pl-metrics p { font-size: 11.5px; color: var(--muted-foreground); }
.pl-metrics b { font-family: var(--font-display); font-size: 17px; font-weight: 600; color: var(--foreground); font-variant-numeric: tabular-nums; }
.pl-foot { display: flex; align-items: center; gap: 8px; margin-top: auto; border-top: 1px solid var(--border); padding-top: 12px; }
.pl-conv { font-size: 12px; color: var(--muted-foreground); }
.pl-badge { margin-right: 4px; border-radius: 999px; background: var(--status-success); padding: 2px 8px; font-size: 11.5px; font-weight: 600; color: var(--status-success-foreground); }
.pl-icon-btn { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 999px; background: var(--muted); color: var(--muted-foreground); }
.pl-icon-btn:hover { background: var(--accent); color: var(--accent-foreground); }
.pl-icon-btn svg { width: 16px; height: 16px; }
.pl-edit { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 999px; background: var(--accent); font-size: 13px; font-weight: 600; color: var(--accent-foreground); }
.pl-edit svg { width: 14px; height: 14px; }
.pl-menu-wrap { position: relative; }
.pl-menu { position: absolute; right: 0; bottom: calc(100% + 6px); z-index: 30; display: flex; min-width: 190px; flex-direction: column; border-radius: 14px; background: var(--popover); padding: 6px; box-shadow: var(--shadow-elegant); }
.pl-menu button { border-radius: 10px; padding: 8px 10px; text-align: left; font-size: 13px; color: var(--popover-foreground); }
.pl-menu button:hover:not(:disabled) { background: var(--muted); }
.pl-menu button:disabled { cursor: not-allowed; opacity: 0.45; }
.pl-menu button.danger { color: var(--status-danger-foreground); }
.pl-empty { border-radius: 20px; background: var(--card); padding: 40px 24px; text-align: center; font-size: 14px; color: var(--muted-foreground); box-shadow: var(--shadow-card); }
@media (max-width: 1100px) { .pl-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) {
  .pl-head { flex-direction: column; align-items: flex-start; }
  .pl-stats { grid-template-columns: 1fr; }
  .pl-search { flex-basis: 100%; }
}
</style>
