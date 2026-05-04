<template>
<div v-if="isBootstrappingLeads" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8">
  <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
</div>
<div v-else class="leads-page-shell relative flex h-full min-h-0 w-full flex-col overflow-hidden">



    <div



      class="leads-page flex min-h-0 flex-1 flex-col gap-5 overflow-hidden px-4 py-4 md:px-5"



      :class="{ 'pointer-events-none select-none opacity-60': !planAllowed }"



    >



      <div class="shrink-0 flex w-full items-center justify-between gap-3">
        <h1 class="text-2xl font-semibold tracking-[-0.2px] text-[#0F1F14] dark:text-white">{{ pageTitle }}</h1>

        <div v-if="activeTab === 'forms'" class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-[10px] bg-[#3DCC5F] px-4 py-[9px] text-[13px] font-semibold text-[#0F1F14] transition hover:bg-[#5BE07A]"
            @click="openCreateModal"
          >
            <span class="text-[15px] leading-none font-bold">+</span>
            {{ viewCopy.actions.newForm }}
          </button>
        </div>
        <div v-else-if="activeTab === 'settings'" class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-[10px] bg-[#3DCC5F] px-4 py-[9px] text-[13px] font-semibold text-[#0F1F14] transition hover:bg-[#5BE07A]"
            @click="openPipelineStageModal"
          >
            <span class="text-[15px] leading-none font-bold">+</span>
            Nova etapa do funil
          </button>
        </div>
        <div v-else-if="activeTab === 'clients'" class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-[10px] bg-[#3DCC5F] px-4 py-[9px] text-[13px] font-semibold text-[#0F1F14] transition hover:bg-[#5BE07A]"
            @click="openClientCreateModal"
          >
            <span class="text-[15px] leading-none font-bold">+</span>
            Novo cliente
          </button>
        </div>

        <div v-else-if="activeTab === 'contacts'" class="flex items-center gap-2 md:gap-4">
  <div v-if="!isMobileViewport && contactViewMode === 'kanban'" class="flex items-center gap-3">
    <div class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
      {{ filteredContactsCount }} {{ viewCopy.contacts.summary }}
    </div>
    <select
      v-model="kanbanPageFilter"
      class="min-w-[160px] rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm outline-none transition focus:ring-2 focus:ring-brand dark:border-white/10 dark:bg-[#111319] dark:text-white"
    >
      <option v-for="option in kanbanPageOptions" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <select
      v-model="kanbanFormFilter"
      class="min-w-[180px] rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm outline-none transition focus:ring-2 focus:ring-brand dark:border-white/10 dark:bg-[#111319] dark:text-white"
    >
      <option v-for="option in kanbanFormOptions" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
  </div>

  <button
    type="button"
    class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-brand-dark"
    @click="openManualOpportunityModal"
  >
    <span v-if="isMobileViewport">+</span>
    <span v-else>+ {{ viewCopy.actions.newManualOpportunity }}</span>
  </button>

  <div v-if="!isMobileViewport" class="inline-flex rounded-full bg-slate-100 p-1 dark:bg-white/10">
    <button
      type="button"
      class="rounded-full px-4 py-2 text-sm font-semibold transition"
      :class="contactViewMode === 'list' ? activeTabClass : inactiveTabClass"
      @click="contactViewMode = 'list'"
    >
      {{ viewCopy.actions.viewModes.list }}
    </button>
    <button
      type="button"
      class="rounded-full px-4 py-2 text-sm font-semibold transition"
      :class="contactViewMode === 'kanban' ? activeTabClass : inactiveTabClass"
      @click="contactViewMode = 'kanban'"
    >
      {{ viewCopy.actions.viewModes.kanban }}
    </button>
  </div>
</div>
      </div>

      <div class="flex min-h-0 flex-1 flex-col">



        <div class="flex min-h-0 flex-1 flex-col">



          <section v-if="activeTab === 'forms'" class="forms-premium space-y-4">
            <div class="forms-kpi-grid">
              <article class="forms-kpi-card">
                <div class="forms-kpi-top">
                  <span class="forms-kpi-icon forms-kpi-icon--forms">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </span>
                  <span class="forms-kpi-badge">{{ forms.length > 0 ? `+${forms.length}` : "0" }}</span>
                </div>
                <p class="forms-kpi-value">{{ forms.length }}</p>
                <p class="forms-kpi-label">FORMULÁRIOS</p>
                <p class="forms-kpi-foot">Total criado na conta</p>
              </article>

              <article class="forms-kpi-card">
                <div class="forms-kpi-top">
                  <span class="forms-kpi-icon forms-kpi-icon--leads">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                  </span>
                  <span class="forms-kpi-badge">{{ totalFormLeads > 0 ? "Ativo" : "Sem leads" }}</span>
                </div>
                <p class="forms-kpi-value">{{ totalFormLeads }}</p>
                <p class="forms-kpi-label">LEADS</p>
                <p class="forms-kpi-foot">Capturados nos formulários</p>
              </article>

              <article class="forms-kpi-card">
                <div class="forms-kpi-top">
                  <span class="forms-kpi-icon forms-kpi-icon--month">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
                      <polyline points="16 7 22 7 22 13" />
                    </svg>
                  </span>
                  <span class="forms-kpi-badge">+{{ leadsThisMonth }} este mês</span>
                </div>
                <p class="forms-kpi-value">{{ leadsThisMonth }}</p>
                <p class="forms-kpi-label">ESTE MÊS</p>
                <p class="forms-kpi-foot">Novos leads capturados</p>
              </article>

              <article class="forms-kpi-card">
                <div class="forms-kpi-top">
                  <span class="forms-kpi-icon forms-kpi-icon--latest">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                  </span>
                  <span class="forms-kpi-badge">Recente</span>
                </div>
                <p class="forms-kpi-value forms-kpi-value--date">{{ latestLeadDateLabel }}</p>
                <p class="forms-kpi-label">ÚLTIMO LEAD</p>
                <p class="forms-kpi-foot">Captura mais recente</p>
              </article>
            </div>

            <article class="list-card forms-list-card">
              <header class="list-header forms-list-header">
                <div class="list-title">Formulários</div>
                <div class="forms-list-filters">
                  <div class="search-wrap">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <input v-model="formSearchQuery" class="search-input" type="text" placeholder="Buscar formulário..." />
                  </div>
                  <select v-model="formStatusFilter" class="filter-select">
                    <option value="all">Todos os status</option>
                    <option value="with-leads">Com leads</option>
                    <option value="no-leads">Sem leads</option>
                  </select>
                </div>
              </header>

              <div v-if="formsLoading && !forms.length" class="forms-empty">
                {{ viewCopy.forms.loading }}
              </div>

              <div v-else-if="!filteredForms.length" class="forms-empty">
                <svg viewBox="0 0 24 24" class="forms-empty-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                <p>Você ainda não criou formulários</p>
                <button type="button" class="btn btn-primary forms-empty-cta" @click="openCreateModal">Criar primeiro formulário</button>
              </div>

              <div v-else class="forms-list-body">
                <div
                  v-for="form in filteredForms"
                  :key="form.id"
                  class="page-item form-row"
                  :title="form.name || fallbackLabels.noNameDefined"
                  @click="openEditModal(form)"
                >
                  <div class="form-row-left">
                    <div class="page-thumb">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                    </div>

                    <div class="page-info">
                      <div class="page-name" :title="form.name || fallbackLabels.noNameDefined">{{ form.name || fallbackLabels.noNameDefined }}</div>
                      <div class="page-dest">
                        {{ form.fields?.length || 0 }} campos · Atualizado em {{ formatDate(form.updated_at || form.created_at) }}
                      </div>
                      <div class="fields-row">
                        <span
                          v-for="field in visibleFormFields(form)"
                          :key="`${form.id}-${field.id}`"
                          class="field-chip"
                        >
                          {{ field.label }}
                        </span>
                        <span v-if="hiddenFieldCount(form) > 0" class="field-chip">+{{ hiddenFieldCount(form) }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="form-row-right" @click.stop>
                    <div class="page-visits form-leads-badge" :class="{ 'is-zero': (form.total_leads ?? 0) === 0 }" :title="(form.total_leads ?? 0) === 0 ? 'Nenhum lead capturado ainda' : ''">
                      {{ form.total_leads ?? 0 }} leads
                    </div>
                    <div class="page-actions form-actions-inline">
                      <button type="button" class="page-action-btn page-action-btn--label view" title="Ver leads" @click="openFormLeads(form)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                        <span>Leads</span>
                      </button>
                      <button type="button" class="page-action-btn page-action-btn--label edit" title="Editar" @click="openEditModal(form)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg>
                        <span>Editar</span>
                      </button>
                      <button type="button" class="page-action-btn page-action-btn--label duplicate" title="Duplicar formulário" @click="duplicateFormQuick(form)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>
                        <span>Duplicar</span>
                      </button>
                      <button v-if="canDeleteLeads" type="button" class="page-action-btn page-action-btn--label danger" title="Excluir" @click="confirmDeleteForm(form)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
                        <span>Excluir</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          </section>







          <section
            v-else-if="activeTab === 'contacts'"
            ref="contactsSectionRef"
            class="flex min-h-0 flex-1 flex-col gap-6 overflow-hidden"
            :style="contactViewMode === 'kanban' ? { height: kanbanViewportHeight, maxHeight: kanbanViewportHeight } : undefined"
          >



            <div



              v-if="contactsLoading && !contacts.length"



              class="rounded-2xl border border-slate-100 px-4 py-6 text-center text-sm text-slate-500 dark:border-white/10 dark:text-slate-300"



            >



              {{ viewCopy.contacts.loading }}



            </div>







            <div



              v-else-if="!contacts.length"



              class="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500 dark:border-white/20 dark:text-slate-300"



            >



              {{ viewCopy.emptyStates.contacts.noLeads }}



            </div>







            <div v-else class="flex min-h-0 flex-1 flex-col overflow-hidden">



              <div v-if="contactViewMode === 'list'" class="flex min-h-0 flex-1 flex-col overflow-hidden">



                <div class="opportunity-filters mb-3">
                  <div class="opportunity-filter-item">
                    <span class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">{{ viewCopy.filters.opportunity.stateLabel }}</span>
                    <select
                      v-model="opportunityStateFilter"
                      class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm outline-none transition focus:border-slate-300 focus:ring-0 dark:border-white/10 dark:bg-[#111319] dark:text-white"
                    >
                      <option value="all">{{ viewCopy.filters.opportunity.all }}</option>
                      <option value="open">{{ viewCopy.filters.opportunity.open }}</option>
                      <option value="closed">{{ viewCopy.filters.opportunity.closed }}</option>
                    </select>
                  </div>

                  <div class="opportunity-filter-item">
                    <span class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">{{ viewCopy.filters.opportunity.outcomeLabel }}</span>
                    <select
                      v-model="opportunityOutcomeFilter"
                      class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm outline-none transition focus:border-slate-300 focus:ring-0 dark:border-white/10 dark:bg-[#111319] dark:text-white"
                    >
                      <option value="all">{{ viewCopy.filters.opportunity.all }}</option>
                      <option value="won">{{ viewCopy.filters.opportunity.won }}</option>
                      <option value="lost">{{ viewCopy.filters.opportunity.lost }}</option>
                    </select>
                  </div>

                  <div v-if="hasActiveFilters" class="opportunity-filter-active flex items-center gap-2 text-xs text-slate-500 dark:text-slate-300">
                    <span>{{ filterCopy.active }}</span>
                    <button
                      type="button"
                      class="rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-600 transition hover:bg-slate-100 dark:border-white/10 dark:text-white dark:hover:bg-white/10"
                      @click.stop="clearAllFilters"
                    >
                      {{ filterCopy.clearAll }}
                    </button>
                  </div>
                </div>

                <article



                  class="flex flex-1 flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white p-0 shadow-sm dark:border-white/10 dark:bg-[#202020]"



                  :style="{ height: listTableHeight, minHeight: listTableHeight, maxHeight: listTableHeight }"



                >



                  <div class="flex flex-1 flex-col min-h-0" @click="closeFilterPopover">



                    <div class="flex-1 min-h-0 overflow-auto">



                      <table v-if="!isMobileViewport" class="min-w-full divide-y divide-slate-200 text-sm dark:divide-white/10">



                        <thead class="sticky top-0 z-10 border-b border-slate-200 bg-white dark:border-white/10 dark:bg-[#202020]">



                          <tr class="whitespace-nowrap text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">



                            <th class="px-4 py-3 text-center">



                              <div class="flex items-center gap-1">



                                <span>{{ filterCopy.columns.name }}</span>



                                <button



                                  type="button"



                                  class="filter-button"



                                  :class="{ 'text-brand': isFilterActive('name') }"



                                  @click.stop="toggleFilterPopover('name')"



                                >



                                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor">



                                    <path d="M3 4h18l-7 8v6l-4 2v-8Z" />



                                  </svg>



                                </button>



                              </div>







                              <div v-if="openFilterKey === 'name'" class="filter-popover" @click.stop>



                                <div class="filter-options">



                                  <label v-for="option in filterOptions.name" :key="option.value" class="filter-option">



                                    <input



                                      type="checkbox"



                                      class="filter-checkbox"



                                      :checked="listFilters.name.includes(option.value)"



                                      @change="toggleFilterValue('name', option.value)"



                                    />



                                    <span>{{ option.label }}</span>



                                  </label>



                                </div>







                                <div class="mt-2 flex gap-2 text-xs">



                                  <button type="button" class="text-slate-500 hover:text-slate-700" @click="clearFilter('name')">



                                    {{ filterCopy.clear }}



                                  </button>



                                  <button type="button" class="text-brand hover:text-brand-dark" @click="closeFilterPopover">



                                    {{ filterCopy.close }}



                                  </button>



                                </div>



                              </div>



                            </th>

                            <th class="px-2 py-2 text-left">Modo</th>

                            <th class="relative px-2 py-2">



                              <div class="flex items-center gap-1">



                                <span>{{ filterCopy.columns.form }}</span>



                                <button



                                  type="button"



                                  class="filter-button"



                                  :class="{ 'text-brand': isFilterActive('form') }"



                                  @click.stop="toggleFilterPopover('form')"



                                >



                                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor">



                                    <path d="M3 4h18l-7 8v6l-4 2v-8Z" />



                                  </svg>



                                </button>



                              </div>







                              <div v-if="openFilterKey === 'form'" class="filter-popover" @click.stop>



                                <div class="filter-options">



                                  <label v-for="option in filterOptions.form" :key="option.value" class="filter-option">



                                    <input



                                      type="checkbox"



                                      class="filter-checkbox"



                                      :checked="listFilters.form.includes(option.value)"



                                      @change="toggleFilterValue('form', option.value)"



                                    />



                                    <span>{{ option.label }}</span>



                                  </label>



                                </div>







                                <div class="mt-2 flex gap-2 text-xs">



                                  <button type="button" class="text-slate-500 hover:text-slate-700" @click="clearFilter('form')">



                                    {{ filterCopy.clear }}



                                  </button>



                                  <button type="button" class="text-brand hover:text-brand-dark" @click="closeFilterPopover">



                                    {{ filterCopy.close }}



                                  </button>



                                </div>



                              </div>



                            </th>







                            <th class="relative px-2 py-2">



                              <div class="flex items-center gap-1">



                                <span>{{ filterCopy.columns.phone }}</span>



                                <button



                                  type="button"



                                  class="filter-button"



                                  :class="{ 'text-brand': isFilterActive('phone') }"



                                  @click.stop="toggleFilterPopover('phone')"



                                >



                                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor">



                                    <path d="M3 4h18l-7 8v6l-4 2v-8Z" />



                                  </svg>



                                </button>



                              </div>







                              <div v-if="openFilterKey === 'phone'" class="filter-popover" @click.stop>



                                <div class="filter-options">



                                  <label v-for="option in filterOptions.phone" :key="option.value" class="filter-option">



                                    <input



                                      type="checkbox"



                                      class="filter-checkbox"



                                      :checked="listFilters.phone.includes(option.value)"



                                      @change="toggleFilterValue('phone', option.value)"



                                    />



                                    <span>{{ option.label }}</span>



                                  </label>



                                </div>







                                <div class="mt-2 flex gap-2 text-xs">



                                  <button type="button" class="text-slate-500 hover:text-slate-700" @click="clearFilter('phone')">



                                    {{ filterCopy.clear }}



                                  </button>



                                  <button type="button" class="text-brand hover:text-brand-dark" @click="closeFilterPopover">



                                    {{ filterCopy.close }}



                                  </button>



                                </div>



                              </div>



                            </th>







                            <th class="relative px-2 py-2">



                              <div class="flex items-center gap-1">



                                <span>{{ filterCopy.columns.email }}</span>



                                <button



                                  type="button"



                                  class="filter-button"



                                  :class="{ 'text-brand': isFilterActive('email') }"



                                  @click.stop="toggleFilterPopover('email')"



                                >



                                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor">



                                    <path d="M3 4h18l-7 8v6l-4 2v-8Z" />



                                  </svg>



                                </button>



                              </div>







                              <div v-if="openFilterKey === 'email'" class="filter-popover" @click.stop>



                                <div class="filter-options">



                                  <label v-for="option in filterOptions.email" :key="option.value" class="filter-option">



                                    <input



                                      type="checkbox"



                                      class="filter-checkbox"



                                      :checked="listFilters.email.includes(option.value)"



                                      @change="toggleFilterValue('email', option.value)"



                                    />



                                    <span>{{ option.label }}</span>



                                  </label>



                                </div>







                                <div class="mt-2 flex gap-2 text-xs">



                                  <button type="button" class="text-slate-500 hover:text-slate-700" @click="clearFilter('email')">



                                    {{ filterCopy.clear }}



                                  </button>



                                  <button type="button" class="text-brand hover:text-brand-dark" @click="closeFilterPopover">



                                    {{ filterCopy.close }}



                                  </button>



                                </div>



                              </div>



                            </th>







                            <th class="relative px-2 py-2">



                              <div class="flex items-center gap-1">



                                <span>{{ filterCopy.columns.city }}</span>



                                <button



                                  type="button"



                                  class="filter-button"



                                  :class="{ 'text-brand': isFilterActive('city') }"



                                  @click.stop="toggleFilterPopover('city')"



                                >



                                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor">



                                    <path d="M3 4h18l-7 8v6l-4 2v-8Z" />



                                  </svg>



                                </button>



                              </div>







                              <div v-if="openFilterKey === 'city'" class="filter-popover" @click.stop>



                                <div class="filter-options">



                                  <label v-for="option in filterOptions.city" :key="option.value" class="filter-option">



                                    <input



                                      type="checkbox"



                                      class="filter-checkbox"



                                      :checked="listFilters.city.includes(option.value)"



                                      @change="toggleFilterValue('city', option.value)"



                                    />



                                    <span>{{ option.label }}</span>



                                  </label>



                                </div>







                                <div class="mt-2 flex gap-2 text-xs">



                                  <button type="button" class="text-slate-500 hover:text-slate-700" @click="clearFilter('city')">



                                    {{ filterCopy.clear }}



                                  </button>



                                  <button type="button" class="text-brand hover:text-brand-dark" @click="closeFilterPopover">



                                    {{ filterCopy.close }}



                                  </button>



                                </div>



                              </div>



                            </th>







                            <th class="relative px-2 py-2">



                              <div class="flex items-center gap-1">



                                <span>{{ filterCopy.columns.page }}</span>



                                <button



                                  type="button"



                                  class="filter-button"



                                  :class="{ 'text-brand': isFilterActive('page') }"



                                  @click.stop="toggleFilterPopover('page')"



                                >



                                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor">



                                    <path d="M3 4h18l-7 8v6l-4 2v-8Z" />



                                  </svg>



                                </button>



                              </div>







                              <div v-if="openFilterKey === 'page'" class="filter-popover w-60" @click.stop>



                                <div class="filter-options max-h-48 space-y-1 overflow-y-auto pr-1">



                                  <label v-for="option in filterOptions.page" :key="option.value" class="filter-option">



                                    <input



                                      type="checkbox"



                                      class="filter-checkbox"



                                      :checked="listFilters.page.includes(option.value)"



                                      @change="toggleFilterValue('page', option.value)"



                                    />



                                    <span>{{ option.label }}</span>



                                  </label>



                                </div>







                                <div class="mt-2 flex gap-2 text-xs">



                                  <button type="button" class="text-slate-500 hover:text-slate-700" @click="clearFilter('page')">



                                    {{ filterCopy.clear }}



                                  </button>



                                  <button type="button" class="text-brand hover:text-brand-dark" @click="closeFilterPopover">



                                    {{ filterCopy.close }}



                                  </button>



                                </div>



                              </div>



                            </th>







                            <th class="px-2 py-2 text-left">Valor</th>



                            <th class="relative px-2 py-2">



                              <div class="flex items-center gap-1">



                                <span>{{ filterCopy.columns.status }}</span>



                                <button



                                  type="button"



                                  class="filter-button"



                                  :class="{ 'text-brand': isFilterActive('status') }"



                                  @click.stop="toggleFilterPopover('status')"



                                >



                                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor">



                                    <path d="M3 4h18l-7 8v6l-4 2v-8Z" />



                                  </svg>



                                </button>



                              </div>







                              <div v-if="openFilterKey === 'status'" class="filter-popover" @click.stop>



                                <div class="filter-options">



                                  <label v-for="option in filterOptions.status" :key="option.value" class="filter-option">



                                    <input



                                      type="checkbox"



                                      class="filter-checkbox"



                                      :checked="listFilters.status.includes(option.value)"



                                      @change="toggleFilterValue('status', option.value)"



                                    />



                                    <span>{{ option.label }}</span>



                                  </label>



                                </div>







                                <div class="mt-2 flex gap-2 text-xs">



                                  <button type="button" class="text-slate-500 hover:text-slate-700" @click="clearFilter('status')">



                                    {{ filterCopy.clear }}



                                  </button>



                                  <button type="button" class="text-brand hover:text-brand-dark" @click="closeFilterPopover">



                                    {{ filterCopy.close }}



                                  </button>



                                </div>



                              </div>



                            </th>







                            <th class="px-2 py-2 text-center">{{ filterCopy.columns.actions }}</th>



                          </tr>



                        </thead>







                        <tbody class="divide-y divide-slate-200 dark:divide-white/5">

                          <tr v-if="!filteredContacts.length">
                            <td colspan="10" class="px-4 py-12 text-center text-sm text-slate-500 dark:text-slate-300">
                              {{ viewCopy.emptyStates.contacts.noFilters }}
                            </td>
                          </tr>

                          <tr

                            v-for="contact in filteredContacts"



                            :key="contact.id"



                            class="cursor-pointer text-slate-700 transition hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-white/[0.03]"
                            @click="openOpportunityDrawer(contact)"



                          >



                            <td class="px-2 py-2 font-semibold">{{ contact.name || fallbackLabels.noName }}</td>



                            <td class="px-2 py-2 font-semibold">{{ getContactModeLabel(contact) }}</td>

                            <td class="px-2 py-2 text-xs font-semibold">{{ getOpportunityFormColumnLabel(contact) }}</td>







                            <td class="px-2 py-2">



                              <div class="flex items-center gap-2">



                                <span class="font-mono text-sm">{{ contact.phone || viewCopy.labels.dash }}</span>



                                <button



                                  v-if="contact.phone"



                                  type="button"



                                  class="transition hover:opacity-80"



                                  :style="{ color: '#29E870' }"



                                  :title="getWhatsappTitle(contact.phone)"



                                  @click.stop="openWhatsapp(contact)"



                                >



                                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">



                                    <path



                                      d="M12.001 2c5.523 0 10 4.477 10 10s-4.477 10-10 10a9.95 9.95 0 0 1-5.03-1.355L2.005 22l1.352-4.968A9.95 9.95 0 0 1 2.001 12c0-5.523 4.477-10 10-10M8.593 7.3l-.2.008a1 1 0 0 0-.372.1a1.3 1.3 0 0 0-.294.228c-.12.113-.188.211-.261.306A2.73 2.73 0 0 0 6.9 9.62c.002.49.13.967.33 1.413c.409.902 1.082 1.857 1.97 2.742c.214.213.424.427.65.626a9.45 9.45 0 0 0 3.84 2.046l.568.087c.185.01.37-.004.556-.013a2 2 0 0 0 .833-.231a5 5 0 0 0 .383-.22q.001.002.125-.09c.135-.1.218-.171.33-.288q.126-.13.21-.302c.078-.163.156-.474.188-.733c.024-.198.017-.306.014-.373c-.004-.107-.093-.218-.19-.265l-.582-.261s-.87-.379-1.402-.621a.5.5 0 0 0-.176-.041a.48.48 0 0 0-.378.127c-.005-.002-.072.055-.795.931a.35.35 0 0 1-.368.13a1.4 1.4 0 0 1-.191-.066c-.124-.052-.167-.072-.252-.108a6 6 0 0 1-1.575-1.003c-.126-.11-.243-.23-.363-.346a6.3 6.3 0 0 1-1.02-1.268l-.059-.095a1 1 0 0 1-.102-.205c-.038-.147.061-.265.061-.265s.243-.266.356-.41c.11-.14.203-.276.263-.373c.118-.19.155-.385.093-.536q-.42-1.026-.868-2.041c-.059-.134-.234-.23-.393-.249q-.081-.01-.162-.016a3 3 0 0 0-.403.004z"



                                    />



                                  </svg>



                                </button>



                              </div>



                            </td>







                            <td class="px-2 py-2">



                              <span class="text-xs">{{ contact.email || viewCopy.labels.emDash }}</span>



                            </td>







                            <td class="px-2 py-2 text-xs">{{ contact.city || viewCopy.labels.dash }}</td>







                            <td class="px-2 py-2 text-xs">



                              <template v-if="contact.page_title || contact.page_slug">



                                <a



                                  v-if="contact.page_url"



                                  :href="contact.page_url"



                                  target="_blank"



                                  rel="noopener"



                                  class="text-brand underline decoration-dotted"
                                  @click.stop



                                >



                                  {{ contact.page_title || contact.page_slug }}



                                </a>



                                <span v-else>{{ contact.page_title || contact.page_slug }}</span>

                              </template>



                              <span v-else>{{ viewCopy.labels.dash }}</span>



                            </td>







                            <td class="px-2 py-2 text-xs font-semibold">{{ formatOpportunityValue(contact.estimated_value_cents) }}</td>







                            <td class="px-2 py-2 text-xs">



                              <div class="relative status-chip-container">



                                <button



                                  type="button"



                                  class="status-chip-button w-full rounded-2xl border px-3 py-1 text-left text-xs font-semibold shadow-sm transition focus:outline-none"



                                  :class="{ 'opacity-60': contactStatusSaving[idKey(contact.id)] }"



                                  :style="statusChipStyle(contact)"



                                  :disabled="contactStatusSaving[idKey(contact.id)]"



                                  @click.stop="toggleStatusDropdown(contact)"



                                >



                                  <span class="flex items-center justify-between gap-2">



                                    <span class="truncate">{{ contact.status_name || fallbackLabels.noStatus }}</span>



                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">



                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />



                                    </svg>



                                  </span>



                                </button>







                                <transition name="fade">



                                  <div



                                    v-if="openStatusDropdown === idKey(contact.id)"



                                    class="status-dropdown absolute right-0 z-20 mt-2 w-52 rounded-2xl border border-slate-100 bg-white/95 p-2 shadow-2xl dark:border-white/10 dark:bg-[#0f1524]"



                                    @click.stop



                                  >



                                    <button



                                      type="button"



                                      class="status-option status-option--neutral"



                                      :class="{ 'status-option--active': !contact.status_id }"



                                      @click="selectStatusOption(contact, null)"



                                    >



                                      <span class="status-dot bg-slate-200 dark:bg-slate-500"></span>



                                      <span>{{ fallbackLabels.noStatus }}</span>



                                    </button>







                                    <button



                                      v-for="status in leadStatuses"



                                      :key="status.id"



                                      type="button"



                                      class="status-option"



                                      :style="statusOptionStyle(status)"



                                      :class="{ 'status-option--active': String(contact.status_id ?? '') === String(status.id) }"



                                      @click="selectStatusOption(contact, String(status.id))"



                                    >



                                      <span class="status-dot" :style="{ backgroundColor: status.color }"></span>



                                      <span>{{ status.name }}</span>



                                    </button>



                                  </div>



                                </transition>



                              </div>



                            </td>







                            <td class="px-2 py-2 text-center">



                              <button
                                v-if="canDeleteLeads"



                                type="button"



                                class="text-rose-500 transition hover:text-rose-600 disabled:opacity-50"



                                :disabled="contactDeleting[idKey(contact.id)]"



                                @click.stop="handleDeleteContact(contact)"



                                @mousedown.stop



                              >



                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">



                                  <path d="M19 4h-3.5l-1-1h-5l-1 1H5v2h14M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6z"/>



                                </svg>



                              </button>



                            </td>



                          </tr>



                        </tbody>



                      </table>

                      <div v-else class="space-y-3 p-3">
                        <div
                          v-if="!filteredContacts.length"
                          class="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500 dark:border-white/20 dark:text-slate-300"
                        >
                          {{ viewCopy.emptyStates.contacts.noFilters }}
                        </div>
                        <article
                          v-for="contact in filteredContacts"
                          :key="`m-${contact.id}`"
                          class="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm dark:border-white/10 dark:bg-[#202020]"
                          @click="openOpportunityDrawer(contact)"
                        >
                          <div class="flex items-start justify-between gap-2">
                            <div class="min-w-0">
                              <p class="truncate text-base font-semibold text-slate-900 dark:text-white">{{ contact.name || fallbackLabels.noName }}</p>
                              <p class="mt-0.5 text-xs font-semibold text-slate-500 dark:text-slate-300">{{ getOpportunityFormColumnLabel(contact) }}</p>
                            </div>
                            <p class="text-xs text-slate-500 dark:text-slate-300">{{ formatDate(contact.created_at) }}</p>
                          </div>

                          <div class="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-600 dark:text-slate-300">
                            <p class="truncate"><span class="font-semibold">{{ filterCopy.columns.phone }}:</span> {{ contact.phone || viewCopy.labels.dash }}</p>
                            <p class="truncate"><span class="font-semibold">{{ filterCopy.columns.city }}:</span> {{ contact.city || viewCopy.labels.dash }}</p>
                            <p class="col-span-2 truncate"><span class="font-semibold">{{ filterCopy.columns.email }}:</span> {{ contact.email || viewCopy.labels.emDash }}</p>
                            <p><span class="font-semibold">{{ filterCopy.columns.value }}:</span> {{ formatOpportunityValue(contact.estimated_value_cents) }}</p>
                            <p class="truncate"><span class="font-semibold">{{ filterCopy.columns.status }}:</span> {{ contact.status_name || fallbackLabels.noStatus }}</p>
                          </div>

                          <div class="mt-3 flex items-center justify-between">
                            <button
                              type="button"
                              class="status-chip-button rounded-2xl border px-3 py-1 text-xs font-semibold"
                              :style="statusChipStyle(contact)"
                              @click.stop="toggleStatusDropdown(contact)"
                            >
                              {{ contact.status_name || fallbackLabels.noStatus }}
                            </button>
                            <button
                              v-if="canDeleteLeads"
                              type="button"
                              class="rounded-xl border border-rose-200 px-2.5 py-1 text-xs font-semibold text-rose-600"
                              :disabled="contactDeleting[idKey(contact.id)]"
                              @click.stop="handleDeleteContact(contact)"
                            >
                              {{ viewCopy.actions.delete }}
                            </button>
                          </div>
                        </article>
                      </div>



                    </div>







                    <div class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">



                      {{ filteredContactsCount }} {{ viewCopy.contacts.summary }}



                    </div>



                  </div>



                </article>



              </div>







<div



  v-else



  class="kanban-scroll flex-1 min-h-0 overflow-x-auto overflow-y-hidden rounded-3xl border border-slate-100 bg-white/90 p-4 pb-6 shadow-sm dark:border-white/10 dark:bg-white/5"
  ref="kanbanScrollRef"
  :style="contactViewMode === 'kanban' ? { height: '100%', minHeight: '100%' } : undefined"






>



  <div class="flex h-full min-h-0 items-stretch gap-4">



    <div



      v-for="column in kanbanColumns"



      :key="column.id"



      class="kanban-column flex h-full w-80 min-w-[20rem] flex-shrink-0 flex-col overflow-hidden rounded-2xl border p-3"



      :style="kanbanColumnStyle(column.id)"



    >



      <div



        class="kanban-column__header sticky top-0 z-10 flex shrink-0 items-center justify-between rounded-2xl border px-3 py-2"



        :style="kanbanHeaderStyle(column.id)"



      >



        <h4 class="text-sm font-semibold">{{ column.name }}</h4>



        <span class="text-xs font-semibold">{{ column.leads.length }}</span>



      </div>







      <div



        class="mt-3 flex-1 min-h-0 overflow-y-auto overflow-x-hidden rounded-2xl bg-transparent pr-1"
        :style="{ height: kanbanColumnBodyHeight, maxHeight: kanbanColumnBodyHeight }"



        :class="dragOverColumn === column.id ? 'ring-2 ring-brand/70' : ''"



        @dragover.prevent="handleDragEnter(column.id)"



        @dragenter.prevent="handleDragEnter(column.id)"



        @drop.prevent="handleDrop(column.id)"



      >



        <div class="flex min-h-full flex-col gap-3">



          <p v-if="!column.leads.length" class="py-6 text-center text-xs text-slate-400">



            {{ viewCopy.emptyStates.kanban.emptyColumn }}



          </p>







          <article



            v-for="contact in column.leads"



            :key="contact.id"



            class="cursor-pointer rounded-2xl border border-slate-100 bg-white p-3 text-xs shadow-sm transition dark:border-white/10 dark:bg-[#05070F]"



            :class="{ 'opacity-40': contactStatusSaving[idKey(contact.id)] }"



            draggable="true"
            @click="openOpportunityDrawer(contact)"



            @dragstart="handleDragStart(contact.id)"



            @dragend="handleDragEnd"



          >



            <div class="flex items-start justify-between gap-2">



              <div>



                <p class="text-sm font-semibold text-slate-800 dark:text-white">



                  {{ contact.name || fallbackLabels.noName }}



                </p>



                <p class="text-[11px] text-slate-500 dark:text-slate-300">



                  {{ getContactFormLabel(contact) }}



                </p>



              </div>







              <button
                v-if="canDeleteLeads"



                type="button"



                class="text-rose-500 transition hover:text-rose-600 disabled:opacity-50"



                :disabled="contactDeleting[idKey(contact.id)]"



                @click.stop="handleDeleteContact(contact)"



                @mousedown.stop



              >



                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">



                  <path d="M19 4h-3.5l-1-1h-5l-1 1H5v2h14M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6z"/>



                </svg>



              </button>



            </div>







            <div class="mt-2 space-y-1 text-slate-600 dark:text-slate-300">



              <p v-if="contact.phone" class="flex items-center gap-2 font-mono text-sm">



                {{ contact.phone }}



                <button



                  type="button"



                  class="transition hover:opacity-80"



                  :style="{ color: '#29E870' }"



                :title="getWhatsappTitle(contact.phone)"



                  @click.stop="openWhatsapp(contact)"



                >



                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">



                    <path



                      d="M12.001 2c5.523 0 10 4.477 10 10s-4.477 10-10 10a9.95 9.95 0 0 1-5.03-1.355L2.005 22l1.352-4.968A9.95 9.95 0 0 1 2.001 12c0-5.523 4.477-10 10-10M8.593 7.3l-.2.008a1 1 0 0 0-.372.1a1.3 1.3 0 0 0-.294.228c-.12.113-.188.211-.261.306A2.73 2.73 0 0 0 6.9 9.62c.002.49.13.967.33 1.413c.409.902 1.082 1.857 1.97 2.742c.214.213.424.427.65.626a9.45 9.45 0 0 0 3.84 2.046l.568.087c.185.01.37-.004.556-.013a2 2 0 0 0 .833-.231a5 5 0 0 0 .383-.22q.001.002.125-.09c.135-.1.218-.171.33-.288q.126-.13.21-.302c.078-.163.156-.474.188-.733c.024-.198.017-.306.014-.373c-.004-.107-.093-.218-.19-.265l-.582-.261s-.87-.379-1.402-.621a.5.5 0 0 0-.176-.041a.48.48 0 0 0-.378.127c-.005-.002-.072.055-.795.931a.35.35 0 0 1-.368.13a1.4 1.4 0 0 1-.191-.066c-.124-.052-.167-.072-.252-.108a6 6 0 0 1-1.575-1.003c-.126-.11-.243-.23-.363-.346a6.3 6.3 0 0 1-1.02-1.268l-.059-.095a1 1 0 0 1-.102-.205c-.038-.147.061-.265.061-.265s.243-.266.356-.41c.11-.14.203-.276.263-.373c.118-.19.155-.385.093-.536q-.42-1.026-.868-2.041c-.059-.134-.234-.23-.393-.249q-.081-.01-.162-.016a3 3 0 0 0-.403.004z"



                    />



                  </svg>



                </button>



              </p>







              <p v-if="contact.email" class="truncate text-[11px]">{{ contact.email }}</p>



              <p v-if="contact.city" class="text-[11px]">{{ contact.city }}</p>



              <p class="text-[11px] font-semibold text-slate-700 dark:text-slate-200">{{ formatOpportunityValue(contact.estimated_value_cents) }}</p>



            </div>







            <div class="mt-3 flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500">



              <span>{{ formatDate(contact.created_at) }}</span>



              <span



                class="rounded-full border border-slate-200 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-600 transition dark:border-white/10 dark:text-slate-300"



                :style="statusChipStyle(contact)"



              >



                {{ contact.status_name || fallbackLabels.noStatus }}



              </span>



            </div>



          </article>



        </div>



      </div>



    </div>



  </div>










</div>



            </div>



          </section>







          <section v-else-if="activeTab === 'clients'" class="space-y-6">

            <ClientsView ref="clientsPanelRef" />

          </section>

          <section v-else class="space-y-6">



            <LeadStatusManagerPanel ref="statusPanelRef" :can-delete="canDeleteLeads" />



          </section>



        </div>



      </div>







      <div



        v-if="!planAllowed"



        class="pointer-events-auto absolute inset-x-0 -top-6 bottom-0 z-10 flex flex-col items-center justify-center bg-black/80 px-4 text-center text-white backdrop-blur-sm"



      >



        <div class="max-w-md rounded-3xl bg-[#202020] p-6 text-white shadow-2xl">



          <h2 class="text-2xl font-bold">



            {{ viewCopy.settings.planGate.title }}



          </h2>



          <p class="mt-2 text-sm text-slate-200">



            {{ viewCopy.settings.planGate.description }}



          </p>



          <button



            type="button"



            class="mt-4 w-full rounded-full bg-brand px-4 py-3 text-sm font-semibold text-white shadow transition hover:bg-brand-dark"



            @click="goToPlans"



          >



            {{ viewCopy.settings.planGate.cta }}



          </button>



        </div>



      </div>



    </div>



  </div>







  <LeadFormBuilderModal



    v-model="builderOpen"



    :form="currentForm"



    :saving="builderSaving"



    @save="handleBuilderSave"



  />



  <Teleport to="body">
    <div v-if="manualOpportunityModalOpen" class="app-modal-overlay fixed inset-0 z-[150] flex items-center justify-center px-4">
      <div class="w-full max-w-3xl rounded-[28px] bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Oportunidades</p>
            <h2 class="mt-2 text-2xl font-bold text-slate-900">Nova oportunidade manual</h2>
            <p class="mt-2 text-sm text-slate-500">Cadastre uma oportunidade sem depender de formul?rio.</p>
          </div>
          <button type="button" class="rounded-full border border-slate-200 p-2 text-slate-500" @click="closeManualOpportunityModal">
            <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
        <div class="mt-5 space-y-4">
          <div class="flex flex-wrap items-center gap-2">
            <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50" @click="manualOpportunityClientSearchOpen = !manualOpportunityClientSearchOpen">
              Buscar cliente
            </button>
            <button v-if="selectedManualOpportunityClient" type="button" class="rounded-full border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:bg-rose-50" @click="clearSelectedManualOpportunityClient">
              Remover cliente
            </button>
          </div>

          <div v-if="manualOpportunityClientSearchOpen" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div class="flex flex-col gap-3 md:flex-row">
              <input v-model="manualOpportunityClientSearchQuery" type="text" placeholder="Buscar cliente por nome, CPF, telefone ou e-mail" class="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
              <button type="button" class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60" :disabled="manualOpportunityClientSearchLoading || manualOpportunityClientSearchQuery.trim().length < 2" @click="handleSearchManualOpportunityClients">
                {{ manualOpportunityClientSearchLoading ? "Buscando..." : "Buscar" }}
              </button>
            </div>
            <div v-if="manualOpportunityClientResults.length" class="mt-3 space-y-2">
              <button v-for="client in manualOpportunityClientResults" :key="client.id" type="button" class="flex w-full items-start justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left transition hover:border-brand/40 hover:bg-brand/5" @click="selectManualOpportunityClient(client)">
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ client.name }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ client.cpf || "Sem CPF" }} | {{ client.phone || "Sem telefone" }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ client.email || "Sem e-mail" }}</p>
                </div>
                <span class="text-xs font-semibold text-brand">Usar cliente</span>
              </button>
            </div>
          </div>

          <div v-if="selectedManualOpportunityClient" class="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">Cliente selecionado</p>
            <p class="mt-2 text-base font-semibold text-slate-900">{{ selectedManualOpportunityClient.name }}</p>
            <p class="mt-1 text-sm text-slate-600">{{ selectedManualOpportunityClient.cpf || "Sem CPF" }} | {{ selectedManualOpportunityClient.phone || "Sem telefone" }}</p>
            <p class="mt-1 text-sm text-slate-500">{{ selectedManualOpportunityClient.email || "Sem e-mail" }}</p>
          </div>

          <div class="grid gap-3 md:grid-cols-2">
            <template v-if="!selectedManualOpportunityClient">
              <input v-model="manualOpportunityForm.name" type="text" placeholder="Nome" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
              <input v-model="manualOpportunityForm.cpf" type="text" placeholder="CPF" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
              <input v-model="manualOpportunityForm.phone" type="text" placeholder="Telefone" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
              <input v-model="manualOpportunityForm.email" type="email" placeholder="E-mail" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
              <input v-model="manualOpportunityForm.city" type="text" placeholder="Cidade" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
              <input v-model="manualOpportunityForm.birthdate" type="date" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
            </template>
            <input v-model="manualOpportunityForm.opportunityName" type="text" placeholder="Nome da oportunidade" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 md:col-span-2" />
            <input v-model="manualOpportunityForm.estimatedValue" type="text" placeholder="R$ 0,00" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20" />
            <select v-model="manualOpportunityForm.statusId" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20">
              <option value="">Sem status</option>
              <option v-for="status in leadStatuses" :key="status.id" :value="String(status.id)">{{ status.name }}</option>
            </select>
            <input v-model="manualOpportunityForm.expectedCloseDate" type="date" class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 md:col-span-2" />
          </div>
        </div>
        <textarea
          v-model="manualOpportunityForm.internalNotes"
          rows="4"
          placeholder="Observação inicial"
          class="mt-3 w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
        ></textarea>
        <div class="mt-5 flex justify-end gap-2">
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="closeManualOpportunityModal">
            Cancelar
          </button>
          <button
            type="button"
            class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
            :disabled="manualOpportunitySaving || (!selectedManualOpportunityClient && !manualOpportunityForm.name.trim())"
            @click="handleCreateManualOpportunity"
          >
            {{ manualOpportunitySaving ? "Salvando..." : "Criar oportunidade" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>



  <OpportunityDrawer
    v-model="isOpportunityDrawerOpen"
    :contact-id="selectedOpportunityId"
    :statuses="leadStatuses"
    mode="modal"
  />

</template>







<script setup lang="ts">



import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";



import type { CSSProperties } from "vue";



import { useRoute, useRouter } from "vue-router";



import LeadFormBuilderModal from "../../components/admin/leads/LeadFormBuilderModal.vue";
import OpportunityDrawer from "../../components/admin/leads/OpportunityDrawer.vue";
import ClientsView from "./ClientsView.vue";



import LeadStatusManagerPanel from "../../components/admin/leads/LeadStatusManagerPanel.vue";



import type { ClientSummary, LeadContact, LeadForm, LeadFormPayload, LeadStatus } from "../../types/leads";



import { useLeadCaptureStore } from "../../store/useLeadCaptureStore";
import { API_PERMISSION_DENIED_EVENT } from "../../services/api";



import { useThemeStore } from "../../store/useThemeStore";
import { useAuthStore } from "../../store/useAuthStore";



import { useLeadFeatureGate } from "../../composables/useLeadFeatureGate";
import { hasAnyPermission } from "../../utils/permissions";



import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";
import type { AdminLanguage, AdminTranslatable } from "../../utils/adminI18n";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";







type TabKey = "forms" | "contacts" | "clients" | "settings";



type FilterKey = "name" | "form" | "phone" | "email" | "city" | "page" | "status" | "received";



type ValueFilterKey = Exclude<FilterKey, "received">;



type ContactViewMode = "list" | "kanban";







const router = useRouter();
const route = useRoute();



const leadStore = useLeadCaptureStore();
const authStore = useAuthStore();



const themeStore = useThemeStore();
const isBootstrappingLeads = ref(true);



const { hasLeadFeatureAccess } = useLeadFeatureGate();
const canDeleteLeads = computed(() => {
  const user = authStore.user;
  if (!user) return true;
  if (user.is_owner ?? true) return true;
  if ((user.role || "member").toLowerCase() === "admin") return true;
  return hasAnyPermission(user.effective_permissions || [], ["leads_full"]);
});
const canManageLeads = computed(() => {
  const user = authStore.user;
  if (!user) return true;
  if (user.is_owner ?? true) return true;
  if ((user.role || "member").toLowerCase() === "admin") return true;
  return hasAnyPermission(user.effective_permissions || [], ["leads_manager", "leads_full"]);
});



const adminLanguage = getAdminLanguage();



const t = createAdminLocalizer(adminLanguage);



type Localized<T> = T extends AdminTranslatable
  ? string
  : T extends Array<infer U>
    ? Localized<U>[]
    : T extends Record<string, unknown>
      ? { [K in keyof T]: Localized<T[K]> }
      : T;

const languageKeySet = new Set<AdminLanguage>(["pt", "es"]);

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const isTranslatableValue = (value: unknown): value is AdminTranslatable => {
  if (value === null || typeof value === "undefined") return true;
  if (typeof value === "string") return true;
  if (!isPlainObject(value)) return false;
  const keys = Object.keys(value);
  if (!keys.length) return false;
  return keys.every(key => languageKeySet.has(key as AdminLanguage));
};

const localizeViewCopy = <T>(value: T): Localized<T> => {
  if (Array.isArray(value)) {
    return value.map(item => localizeViewCopy(item)) as Localized<T>;
  }
  if (isTranslatableValue(value)) {
    return t(value) as Localized<T>;
  }
  if (isPlainObject(value)) {
    const result: Record<string, unknown> = {};
    Object.entries(value).forEach(([key, entry]) => {
      result[key] = localizeViewCopy(entry);
    });
    return result as Localized<T>;
  }
  return value as Localized<T>;
};

const viewCopySource = {
  header: {
    eyebrow: { pt: "Captação", es: "Captación" },
    title: { pt: "Leads", es: "Leads" },
    description: {
      pt: "Crie formulários e acompanhe contatos gerados pelas páginas.",
      es: "Crea formularios y acompaña los contactos generados por tus páginas."
    },
  },
  tabs: {
    forms: { pt: "Formulários", es: "Formularios" },
    contacts: { pt: "Oportunidades", es: "Oportunidades" },
    clients: { pt: "Clientes", es: "Clientes" },
    settings: { pt: "Configurações", es: "Configuraciones" }
  },
  actions: {
    newForm: { pt: "Novo formulário", es: "Nuevo formulario" },
    edit: { pt: "Editar", es: "Editar" },
    delete: { pt: "Excluir", es: "Eliminar" },
    viewModes: {
      list: { pt: "Lista", es: "Lista" },
      kanban: { pt: "Kanban", es: "Kanban" }
    },
    whatsapp: {
      call: { pt: "Chamar", es: "Contactar" },
      suffix: { pt: "no WhatsApp", es: "por WhatsApp" },
      formMessage: {
        pt: "Olá! Recebi o seu interesse no roteiro: {page} e gostaria de falar com você.",
        es: "¡Hola! Recibí tu interés en el itinerario: {page} y me gustaría hablar contigo."
      }
    }
  },
  forms: {
    loading: { pt: "Carregando formulários...", es: "Cargando formularios..." },
    card: {
      eyebrow: { pt: "Formulário", es: "Formulario" },
      nameLabel: { pt: "Nome", es: "Nombre" },
      titleLabel: { pt: "Título", es: "Título" },
      totalLeadsSuffix: { pt: "leads", es: "leads" },
      updatedAt: { pt: "Atualizado em", es: "Actualizado el" }
    }
  },
  contacts: {
    loading: { pt: "Carregando contatos...", es: "Cargando contactos..." },
    summary: { pt: "lead(s) exibidos", es: "lead(s) mostrados" }
  },
  filters: {
    active: { pt: "Filtros ativos", es: "Filtros activos" },
    clearAll: { pt: "Limpar filtros", es: "Limpiar filtros" },
    clear: { pt: "Limpar", es: "Limpiar" },
    close: { pt: "Fechar", es: "Cerrar" },
    from: { pt: "De", es: "Desde" },
    to: { pt: "Até", es: "Hasta" },
    columns: {
      name: { pt: "Nome", es: "Nombre" },
      form: { pt: "Formulário", es: "Formulario" },
      phone: { pt: "Telefone", es: "Teléfono" },
      email: { pt: "E-mail", es: "E-mail" },
      city: { pt: "Cidade", es: "Ciudad" },
      page: { pt: "Página", es: "Página" },
      received: { pt: "Valor", es: "Valor" },
      status: { pt: "Status", es: "Estado" },
      actions: { pt: "Ações", es: "Acciones" }
    },
    kanban: {
      allPages: { pt: "Todas as páginas", es: "Todas las páginas" },
      allForms: { pt: "Todos os formulários", es: "Todos los formularios" }
    },
    opportunity: {
      stateLabel: { pt: "Situação", es: "Situación" },
      outcomeLabel: { pt: "Resultado", es: "Resultado" },
      all: { pt: "Todos", es: "Todos" },
      open: { pt: "Aberta", es: "Abierta" },
      closed: { pt: "Fechada", es: "Cerrada" },
      won: { pt: "Ganha", es: "Ganada" },
      lost: { pt: "Perdida", es: "Perdida" }
    }
  },
  settings: {
    planGate: {
      title: { pt: "Disponível no plano Agência", es: "Disponible en el plan Agencia" },
      description: {
        pt: "A captação de leads está liberada a partir do plano Agência ou superior. Atualize seu plano para desbloquear essa funcionalidade.",
        es: "La captación de leads se libera a partir del plan Agencia o superior. Actualiza tu plan para desbloquear esta funcionalidad."
      },
      cta: { pt: "Conhecer planos", es: "Conocer planes" }
    }
  },
  dialogs: {
    deleteForm: {
      pt: 'Excluir o formulário "{title}"? Essa ação não pode ser desfeita.',
      es: '¿Eliminar el formulario "{title}"? Esta acción no se puede deshacer.'
    },
    deleteLead: {
      pt: 'Excluir o lead "{name}"?',
      es: '¿Eliminar el lead "{name}"?'
    }
  },
  messages: {
    formDeleted: { pt: "Formulário excluído.", es: "Formulario eliminado." },
    formDeleteError: { pt: "Não foi possível excluir o formulário.", es: "No se pudo eliminar el formulario." },
    formUpdated: { pt: "Formulário atualizado.", es: "Formulario actualizado." },
    formCreated: { pt: "Formulário criado com sucesso.", es: "Formulario creado con éxito." },
    formSaveError: { pt: "Não foi possível salvar o formulário.", es: "No se pudo guardar el formulario." },
    statusUpdated: { pt: "Status atualizado.", es: "Estado actualizado." },
    statusUpdateError: { pt: "Não foi possível atualizar o status.", es: "No se pudo actualizar el estado." },
    leadDeleted: { pt: "Lead excluído.", es: "Lead eliminado." },
    leadDeleteError: { pt: "Não foi possível excluir o lead.", es: "No se pudo eliminar el lead." }
  },
  emptyStates: {
    forms: {
      prefix: { pt: "Nenhum formulário cadastrado ainda. Clique em", es: "Ningún formulario creado aún. Haz clic en" },
      suffix: { pt: "para começar.", es: "para empezar." }
    },
    contacts: {
      noLeads: {
        pt: "Nenhum lead captado ainda. Divulgue as páginas com formulário obrigatório para começar.",
        es: "Aún no hay leads captados. Divulga las páginas con formulario obligatorio para empezar."
      },
      noFilters: {
        pt: "Nenhum contato encontrado com os filtros aplicados.",
        es: "Ningún contacto encontrado con los filtros aplicados."
      }
    },
    kanban: {
      emptyColumn: { pt: "Sem leads.", es: "Sin leads." }
    }
  },
  labels: {
    fallback: {
      noNameDefined: { pt: "Sem nome definido.", es: "Sin nombre definido." },
      noTitleDefined: { pt: "Sem título definido.", es: "Sin título definido." },
      noName: { pt: "Sem nome", es: "Sin nombre" },
      noForm: { pt: "Sem formulário", es: "Sin formulario" },
      noStatus: { pt: "Sem status", es: "Sin estado" },
      noPage: { pt: "Sem página", es: "Sin página" },
      noPhone: { pt: "Sem telefone", es: "Sin teléfono" },
      noEmail: { pt: "Sem e-mail", es: "Sin e-mail" },
      noCity: { pt: "Sem cidade", es: "Sin ciudad" },
      noValue: { pt: "Sem valor", es: "Sin valor" }
    },
    dash: "-",
    emDash: "—",
    formSingular: { pt: "Formulário", es: "Formulario" }
  }
};
const viewCopy = localizeViewCopy(viewCopySource);



const fallbackLabels = viewCopy.labels.fallback;



const filterCopy = viewCopy.filters;



const whatsappCopy = viewCopy.actions.whatsapp;







const planAllowed = hasLeadFeatureAccess;



const isDarkTheme = computed(() => themeStore.isDark);







const listTableHeight = computed(() => {



  if (typeof window === "undefined") return "24rem";



  const viewportHeight = viewportHeightPx.value || 768;



  const usable = Math.max(viewportHeight - (isMobileViewport.value ? 250 : 230), isMobileViewport.value ? 340 : 420);



  return `${usable}px`;



});

const contactsSectionRef = ref<HTMLElement | null>(null);
const kanbanScrollRef = ref<HTMLElement | null>(null);
const statusPanelRef = ref<{ openCreateModal?: () => void } | null>(null);
const clientsPanelRef = ref<{ openCreateModal?: () => void } | null>(null);
const kanbanViewportHeight = ref("calc(100dvh - 240px)");
const kanbanColumnBodyHeight = computed(() => {
  const raw = Number.parseInt(kanbanViewportHeight.value, 10);
  if (Number.isNaN(raw)) return "420px";
  return `${Math.max(220, raw - 110)}px`;
});

const recalculateKanbanHeight = () => {
  if (typeof window === "undefined") return;
  const el = contactsSectionRef.value || kanbanScrollRef.value;
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const bottomGap = isMobileViewport.value ? 12 : 16;
  const available = Math.floor(window.innerHeight - rect.top - bottomGap);
  kanbanViewportHeight.value = `${Math.max(300, available)}px`;
};

const scheduleKanbanHeightRecalc = () => {
  if (typeof window === "undefined") return;
  if (activeTab.value !== "contacts" || contactViewMode.value !== "kanban") return;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      recalculateKanbanHeight();
    });
  });
};







const activeTab = ref<TabKey>("forms");
const pageTitle = computed(() => {
  if (activeTab.value === "contacts") return viewCopy.tabs.contacts;
  if (activeTab.value === "clients") return viewCopy.tabs.clients;
  if (activeTab.value === "settings") return viewCopy.tabs.settings;
  return viewCopy.tabs.forms;
});



const contactViewMode = ref<ContactViewMode>("list");
const opportunityStateFilter = ref<"all" | "open" | "closed">("all");
const opportunityOutcomeFilter = ref<"all" | "won" | "lost">("all");
const isOpportunityDrawerOpen = ref(false);
const selectedOpportunityId = ref<string | number | null>(null);



const isMobileViewport = ref(false);
const viewportHeightPx = ref(768);



const builderOpen = ref(false);



const builderSaving = ref(false);
const manualOpportunityModalOpen = ref(false);
const manualOpportunitySaving = ref(false);
const manualOpportunityClientSearchOpen = ref(false);
const manualOpportunityClientSearchLoading = ref(false);
const manualOpportunityClientSearchQuery = ref("");
const manualOpportunityClientResults = ref<ClientSummary[]>([]);
const selectedManualOpportunityClient = ref<ClientSummary | null>(null);
const manualOpportunityForm = reactive({
  name: "",
  opportunityName: "",
  cpf: "",
  phone: "",
  email: "",
  city: "",
  birthdate: "",
  estimatedValue: "",
  statusId: "",
  internalNotes: "",
  expectedCloseDate: ""
});



const currentForm = ref<LeadForm | null>(null);



const feedback = ref<{ message: string; isError: boolean }>({ message: "", isError: false });



const getWhatsappTitle = (phone: string) => `${whatsappCopy.call} ${phone} ${whatsappCopy.suffix}`;



const getDeleteFormMessage = (title: string) => viewCopy.dialogs.deleteForm.replace("{title}", title);



const getDeleteLeadMessage = (name: string) => viewCopy.dialogs.deleteLead.replace("{name}", name);







const contactStatusSaving = reactive<Record<string, boolean>>({});



const contactDeleting = reactive<Record<string, boolean>>({});



const openStatusDropdown = ref<string | null>(null);



const openFilterKey = ref<FilterKey | null>(null);



const dragOverColumn = ref<string | null>(null);



const draggingLeadId = ref<string | null>(null);







const listFilters = reactive({



  name: [] as string[],



  form: [] as string[],



  phone: [] as string[],



  email: [] as string[],



  city: [] as string[],



  page: [] as string[],



  status: [] as string[],



  receivedFrom: "",



  receivedTo: ""



});







const activeTabClass = "bg-[#54D36F] text-white shadow-sm dark:bg-white dark:text-slate-900";



const inactiveTabClass = "text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white";







const forms = computed(() => leadStore.forms);



const formsLoading = computed(() => leadStore.formsLoading);

const formSearchQuery = ref("");
const formStatusFilter = ref<"all" | "with-leads" | "no-leads">("all");
const openFormMenuId = ref<number | string | null>(null);

const getFormTotalLeads = (form: LeadForm) => {
  if (typeof form.total_leads === "number") return form.total_leads;
  return contacts.value.filter(contact => String(contact.form_id) === String(form.id)).length;
};

const totalFormLeads = computed(() => forms.value.reduce((acc, form) => acc + getFormTotalLeads(form), 0));

const leadsThisMonth = computed(() => {
  const now = new Date();
  const month = now.getMonth();
  const year = now.getFullYear();
  return contacts.value.reduce((acc, contact) => {
    if (!contact.created_at) return acc;
    const dt = new Date(contact.created_at);
    if (Number.isNaN(dt.getTime())) return acc;
    return dt.getMonth() === month && dt.getFullYear() === year ? acc + 1 : acc;
  }, 0);
});

const latestLeadDateLabel = computed(() => {
  let latest: Date | null = null;
  contacts.value.forEach(contact => {
    if (!contact.created_at) return;
    const dt = new Date(contact.created_at);
    if (Number.isNaN(dt.getTime())) return;
    if (!latest || dt.getTime() > latest.getTime()) latest = dt;
  });
  if (!latest) return "—";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(latest);
});

const filteredForms = computed(() => {
  const term = formSearchQuery.value.trim().toLowerCase();
  return forms.value.filter(form => {
    const leads = getFormTotalLeads(form);
    const matchesStatus =
      formStatusFilter.value === "all" ||
      (formStatusFilter.value === "with-leads" && leads > 0) ||
      (formStatusFilter.value === "no-leads" && leads === 0);
    const matchesSearch =
      !term ||
      (form.name || "").toLowerCase().includes(term) ||
      (form.title || "").toLowerCase().includes(term);
    return matchesStatus && matchesSearch;
  });
});

const visibleFormFields = (form: LeadForm) => (form.fields || []).slice(0, 4);
const hiddenFieldCount = (form: LeadForm) => Math.max((form.fields || []).length - 4, 0);

const toggleFormMenu = (formId: number | string) => {
  openFormMenuId.value = openFormMenuId.value === formId ? null : formId;
};

const openFormLeads = (form: LeadForm) => {
  openFormMenuId.value = null;
  activeTab.value = "contacts";
  contactViewMode.value = "list";
  listFilters.form = [String(form.id)];
};

const duplicateFormQuick = async (form: LeadForm) => {
  openFormMenuId.value = null;
  try {
    await leadStore.createForm({
      name: `${form.name || "Formulário"} (cópia)`,
      title: form.title || "",
      subtitle: form.subtitle || "",
      buttonLabel: form.buttonLabel || "Enviar",
      buttonColor: form.buttonColor || "#3DCC5F",
      showLogo: form.showLogo ?? true,
      fields: (form.fields || []).map(field => ({ ...field })),
      defaultStatusId: form.defaultStatusId ?? null
    });
    showFeedback("Formulário duplicado com sucesso.");
  } catch (err) {
    console.error(err);
    showFeedback("Não foi possível duplicar o formulário.", true);
  }
};

const copyFormLink = async (form: LeadForm) => {
  openFormMenuId.value = null;
  const url = `${window.location.origin}/admin/leads?form=${encodeURIComponent(String(form.id))}`;
  try {
    await navigator.clipboard.writeText(url);
    showFeedback("Link copiado.");
  } catch {
    showFeedback("Não foi possível copiar o link.", true);
  }
};

const embedFormInPage = (form: LeadForm) => {
  openFormMenuId.value = null;
  showFeedback(`Use o formulário "${form.name || "Formulário"}" na captura de leads da página.`);
};



const contacts = computed(() => leadStore.contacts);



const allContacts = computed(() => leadStore.contacts);



const contactsLoading = computed(() => leadStore.contactsLoading);



const leadStatuses = computed(() => leadStore.statuses);







const DEFAULT_FORM_LABEL = fallbackLabels.noForm;







const contactPageFilterValue = (contact: LeadContact) =>



  contact.page_id === null || typeof contact.page_id === "undefined" ? "none" : String(contact.page_id);







const contactFormFilterValue = (contact: LeadContact) =>



  contact.form_id === null || typeof contact.form_id === "undefined" ? "none" : String(contact.form_id);







const kanbanPageFilter = ref("all");



const kanbanFormFilter = ref("all");







const normalizeFormId = (value: string | number | null | undefined) => {



  if (value === null || typeof value === "undefined") return null;



  return String(value);



};







const findFormById = (formId: string | number | null | undefined): LeadForm | null => {



  const targetId = normalizeFormId(formId);



  if (!targetId) return null;



  return forms.value.find(form => normalizeFormId(form.id) === targetId) || null;



};







const getContactFormLabel = (contact: LeadContact | null | undefined) => {



  if (!contact) return DEFAULT_FORM_LABEL;



  const found = findFormById(contact.form_id);



  if (found?.name?.trim()) return found.name.trim();



  if (contact.form_name?.trim()) return contact.form_name.trim();



  if (found?.title?.trim()) return found.title.trim();



  return DEFAULT_FORM_LABEL;



};

const isManualOpportunity = (contact: LeadContact | null | undefined) => {
  const source = String(contact?.source || "").trim().toLowerCase();
  return source.includes("manual");
};

const getContactModeLabel = (contact: LeadContact | null | undefined) =>
  isManualOpportunity(contact) ? "Manual" : "Formulário";

const getOpportunityFormColumnLabel = (contact: LeadContact | null | undefined) =>
  isManualOpportunity(contact) ? "-" : getContactFormLabel(contact);

const getOpportunityOutcome = (contact: LeadContact | null | undefined): "won" | "lost" | null => {
  const status = String(contact?.status_name || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
  if (!status) return null;
  if (status === "ganho" || status === "won" || status.includes("ganh")) return "won";
  if (status === "perdido" || status === "lost" || status.includes("perd")) return "lost";
  return null;
};

const isOpportunityClosed = (contact: LeadContact | null | undefined) => getOpportunityOutcome(contact) !== null;







const kanbanPageOptions = computed(() => {



  const map = new Map<string, string>();







  allContacts.value.forEach(contact => {



    const value = contactPageFilterValue(contact);



  const label = contact.page_title || contact.page_slug || fallbackLabels.noPage;



    if (!map.has(value)) {



      map.set(value, label);



    }



  });







  const options = [{ label: viewCopy.filters.kanban.allPages, value: "all" }];



  map.forEach((label, value) => options.push({ value, label }));



  return options;



});







const kanbanFormOptions = computed(() => {



  const map = new Map<string, string>();







  forms.value.forEach(form => {



    const label = form.name?.trim() || form.title || `${viewCopy.labels.formSingular} ${form.id}`;



    map.set(String(form.id), label);



  });







  let hasEmptyForm = false;







  allContacts.value.forEach(contact => {



    const value = contactFormFilterValue(contact);



    if (value === "none") {



      hasEmptyForm = true;



      return;



    }



    if (!map.has(value)) {



      map.set(value, contact.form_name?.trim() || DEFAULT_FORM_LABEL);



    }



  });







  const options = [{ label: viewCopy.filters.kanban.allForms, value: "all" }];



  map.forEach((label, value) => options.push({ value, label }));







  if (hasEmptyForm) {



    options.push({ label: DEFAULT_FORM_LABEL, value: "none" });



  }







  return options;



});







watch(kanbanPageOptions, options => {



  if (!options.some(option => option.value === kanbanPageFilter.value)) {



    kanbanPageFilter.value = "all";



  }



});







watch(kanbanFormOptions, options => {



  if (!options.some(option => option.value === kanbanFormFilter.value)) {



    kanbanFormFilter.value = "all";



  }



});







const statusColorMap = computed<Record<string, string>>(() => {



  const map: Record<string, string> = {};



  leadStatuses.value.forEach(status => {



    const color = status.color?.trim();



    if (color) {



      map[String(status.id)] = color;



    }



  });



  return map;



});







const filterOptions = computed(() => {



const buildOptions = (values: (string | null | undefined)[], emptyLabel = fallbackLabels.noValue) => {



    const map = new Map<string, string>();







    values.forEach(value => {



      const label = value && value.trim() ? value : emptyLabel;



      if (!map.has(label)) {



        map.set(label, label);



      }



    });







    return Array.from(map.entries())



      .map(([label, value]) => ({ label, value }))



      .sort((a, b) => a.label.localeCompare(b.label));



  };







  const pageLabels = allContacts.value.map(contact => contact.page_title || contact.page_slug || fallbackLabels.noPage);







  return {



    name: buildOptions(allContacts.value.map(contact => contact.name || fallbackLabels.noName), fallbackLabels.noName),



    form: buildOptions(allContacts.value.map(contact => getOpportunityFormColumnLabel(contact)), DEFAULT_FORM_LABEL),



    phone: buildOptions(allContacts.value.map(contact => contact.phone || fallbackLabels.noPhone), fallbackLabels.noPhone),



    email: buildOptions(allContacts.value.map(contact => contact.email || fallbackLabels.noEmail), fallbackLabels.noEmail),



    city: buildOptions(allContacts.value.map(contact => contact.city || fallbackLabels.noCity), fallbackLabels.noCity),



    page: buildOptions(pageLabels, fallbackLabels.noPage),



    status: [



      { label: fallbackLabels.noStatus, value: "null" },



      ...leadStatuses.value.map(status => ({ label: status.name, value: String(status.id) }))



    ]



  };



});







const hasActiveFilters = computed(() => {



  return (



    listFilters.name.length ||



    listFilters.form.length ||



    listFilters.phone.length ||



    listFilters.email.length ||



    listFilters.city.length ||



    listFilters.page.length ||



    listFilters.status.length ||

    opportunityStateFilter.value !== "all" ||

    opportunityOutcomeFilter.value !== "all" ||



    !!listFilters.receivedFrom ||



    !!listFilters.receivedTo



  );



});







const matchesFilter = (contact: LeadContact) => {



  const matchArray = (arr: string[], value: string | null | undefined, fallback: string) => {



    if (!arr.length) return true;



    const normalized = value && value.trim() ? value : fallback;



    return arr.includes(normalized);



  };







  if (!matchArray(listFilters.name, contact.name, fallbackLabels.noName)) return false;



  if (!matchArray(listFilters.form, getOpportunityFormColumnLabel(contact), DEFAULT_FORM_LABEL)) return false;



  if (!matchArray(listFilters.phone, contact.phone, fallbackLabels.noPhone)) return false;



  if (!matchArray(listFilters.email, contact.email, fallbackLabels.noEmail)) return false;



  if (!matchArray(listFilters.city, contact.city, fallbackLabels.noCity)) return false;







  if (listFilters.page.length) {



    const pageLabel = contact.page_title || contact.page_slug || fallbackLabels.noPage;



    if (!listFilters.page.includes(pageLabel)) return false;



  }







  if (listFilters.status.length) {



    const key = contact.status_id ? String(contact.status_id) : "null";



    if (!listFilters.status.includes(key)) return false;



  }







  if (opportunityStateFilter.value !== "all") {
    const closed = isOpportunityClosed(contact);
    if (opportunityStateFilter.value === "open" && closed) return false;
    if (opportunityStateFilter.value === "closed" && !closed) return false;
  }

  if (opportunityOutcomeFilter.value !== "all") {
    const outcome = getOpportunityOutcome(contact);
    if (opportunityOutcomeFilter.value === "won" && outcome !== "won") return false;
    if (opportunityOutcomeFilter.value === "lost" && outcome !== "lost") return false;
  }

  if (listFilters.receivedFrom) {



    const created = contact.created_at ? new Date(contact.created_at).getTime() : null;



    if (!created || created < new Date(listFilters.receivedFrom).getTime()) return false;



  }







  if (listFilters.receivedTo) {



    const created = contact.created_at ? new Date(contact.created_at).getTime() : null;



    if (!created || created > new Date(listFilters.receivedTo).getTime()) return false;



  }







  return true;



};







const filteredContacts = computed(() => {



  if (!hasActiveFilters.value) return contacts.value;



  return contacts.value.filter(matchesFilter);



});







const kanbanFilteredContacts = computed(() =>



  filteredContacts.value.filter(contact => {



    if (kanbanPageFilter.value !== "all" && contactPageFilterValue(contact) !== kanbanPageFilter.value) {



      return false;



    }



    if (kanbanFormFilter.value !== "all" && contactFormFilterValue(contact) !== kanbanFormFilter.value) {



      return false;



    }



    return true;



  })



);







const filteredContactsCount = computed(() => filteredContacts.value.length);







const kanbanColumns = computed(() => {



  const sortedStatuses = [...leadStatuses.value].sort((a, b) => {



    const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;



    const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;



    return dateA - dateB;



  });







  const baseOptions = [



    { id: "null", name: fallbackLabels.noStatus },

    ...sortedStatuses.map(status => ({ id: String(status.id), name: status.name }))



  ];







  const map: Record<string, LeadContact[]> = {};



  baseOptions.forEach(option => {



    map[option.id] = [];



  });







  kanbanFilteredContacts.value.forEach(contact => {



    const key = contact.status_id ? String(contact.status_id) : "null";



    if (!map[key]) map[key] = [];



    map[key].push(contact);



  });







  return baseOptions.map(option => ({



    ...option,



    leads: map[option.id] || []



  }));



});







const formatDate = (value?: string) => {



  if (!value) return "—";



  const date = new Date(value);



  if (Number.isNaN(date.getTime())) return "—";



  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(date);



};







const formatOpportunityValue = (value?: number | null) => {



  if (typeof value !== "number" || Number.isNaN(value) || value <= 0) return fallbackLabels.noValue;



  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);



};







const showFeedback = (message: string, isError = false) => {



  feedback.value = { message, isError };



  setTimeout(() => {



    feedback.value = { message: "", isError: false };



  }, 4000);



};

const getForbiddenMessage = (err: any, fallback: string) => {
  const status = err?.response?.status;
  if (status !== 403) return null;
  return err?.response?.data?.detail || fallback;
};

const showReadOnlySnackbar = (message = "Seu perfil permite apenas visualização.") => {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent(API_PERMISSION_DENIED_EVENT, {
      detail: { message, status: 403, method: "post" }
    })
  );
};







const openCreateModal = () => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }



  currentForm.value = null;



  builderOpen.value = true;



};

const openManualOpportunityModal = () => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  manualOpportunityModalOpen.value = true;
};

const openPipelineStageModal = () => {
  statusPanelRef.value?.openCreateModal?.();
};

const openClientCreateModal = () => {
  clientsPanelRef.value?.openCreateModal?.();
};

const selectManualOpportunityClient = (client: ClientSummary) => {
  selectedManualOpportunityClient.value = client;
  manualOpportunityForm.name = client.name || "";
  manualOpportunityForm.cpf = client.cpf || "";
  manualOpportunityForm.phone = client.phone || "";
  manualOpportunityForm.email = client.email || "";
  manualOpportunityForm.city = client.city || "";
  manualOpportunityClientSearchOpen.value = false;
};

const clearSelectedManualOpportunityClient = () => {
  selectedManualOpportunityClient.value = null;
};

const handleSearchManualOpportunityClients = async () => {
  const query = manualOpportunityClientSearchQuery.value.trim();
  if (query.length < 2) {
    manualOpportunityClientResults.value = [];
    return;
  }
  manualOpportunityClientSearchLoading.value = true;
  try {
    manualOpportunityClientResults.value = await leadStore.searchClients(query);
  } catch (err) {
    console.error(err);
    manualOpportunityClientResults.value = [];
  } finally {
    manualOpportunityClientSearchLoading.value = false;
  }
};

const closeManualOpportunityModal = () => {
  manualOpportunityModalOpen.value = false;
  manualOpportunityClientSearchOpen.value = false;
  manualOpportunityClientSearchLoading.value = false;
  manualOpportunityClientSearchQuery.value = "";
  manualOpportunityClientResults.value = [];
  selectedManualOpportunityClient.value = null;
  manualOpportunityForm.name = "";
  manualOpportunityForm.opportunityName = "";
  manualOpportunityForm.cpf = "";
  manualOpportunityForm.phone = "";
  manualOpportunityForm.email = "";
  manualOpportunityForm.city = "";
  manualOpportunityForm.birthdate = "";
  manualOpportunityForm.estimatedValue = "";
  manualOpportunityForm.statusId = "";
  manualOpportunityForm.internalNotes = "";
  manualOpportunityForm.expectedCloseDate = "";
};

const currencyInputToCents = (value: string) => {
  const digits = value.replace(/\D/g, "");
  if (!digits) return null;
  return Number(digits);
};

const handleCreateManualOpportunity = async () => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  if (!selectedManualOpportunityClient.value && !manualOpportunityForm.name?.trim()) return;
  manualOpportunitySaving.value = true;
  try {
    const opportunity = await leadStore.createManualOpportunity({
      clientId: selectedManualOpportunityClient.value?.id || null,
      name: selectedManualOpportunityClient.value?.name || manualOpportunityForm.name.trim(),
      opportunityName: manualOpportunityForm.opportunityName?.trim() || null,
      cpf: selectedManualOpportunityClient.value ? null : manualOpportunityForm.cpf?.trim() || null,
      phone: selectedManualOpportunityClient.value ? null : manualOpportunityForm.phone?.trim() || null,
      email: selectedManualOpportunityClient.value ? null : manualOpportunityForm.email?.trim() || null,
      city: selectedManualOpportunityClient.value ? null : manualOpportunityForm.city?.trim() || null,
      birthdate: selectedManualOpportunityClient.value ? null : manualOpportunityForm.birthdate || null,
      estimatedValueCents: currencyInputToCents(manualOpportunityForm.estimatedValue),
      statusId: manualOpportunityForm.statusId ? Number(manualOpportunityForm.statusId) : null,
      internalNotes: manualOpportunityForm.internalNotes?.trim() || null,
      expectedCloseDate: manualOpportunityForm.expectedCloseDate || null
    });
    closeManualOpportunityModal();
    selectedOpportunityId.value = opportunity.id;
    isOpportunityDrawerOpen.value = true;
    showFeedback("Oportunidade criada com sucesso.");
  } catch (err) {
    console.error(err);
    showFeedback("Nao foi possivel criar a oportunidade.", true);
  } finally {
    manualOpportunitySaving.value = false;
  }
};







const openEditModal = (form: LeadForm) => {



  currentForm.value = form;



  builderOpen.value = true;



};







const confirmDeleteForm = async (form: LeadForm) => {
  if (!canDeleteLeads.value) {
    showFeedback("Seu nível gerencial não permite excluir.", true);
    return;
  }



  const confirmed = window.confirm(getDeleteFormMessage(form.title));



  if (!confirmed) return;







  try {



    await leadStore.deleteForm(form.id);



    showFeedback(viewCopy.messages.formDeleted);



  } catch (err) {



    console.error(err);



    showFeedback(viewCopy.messages.formDeleteError, true);



  }



};







const handleBuilderSave = async (payload: { id: string | null; form: LeadFormPayload }) => {



  builderSaving.value = true;



  try {



    if (payload.id) {



      await leadStore.updateForm(payload.id, payload.form);



      showFeedback(viewCopy.messages.formUpdated);



    } else {



      await leadStore.createForm(payload.form);



      showFeedback(viewCopy.messages.formCreated);



    }



    builderOpen.value = false;



  } catch (err) {



    console.error(err);
    const forbiddenMessage = getForbiddenMessage(err, "Seu perfil permite apenas visualização.");
    showFeedback(forbiddenMessage || viewCopy.messages.formSaveError, true);



  } finally {



    builderSaving.value = false;



  }



};













const openWhatsapp = (contact: LeadContact | null | undefined) => {



  const digits = normalizeWhatsappDigits(contact?.phone);



  if (!digits) return;



  if (isManualOpportunity(contact)) {
    window.open(`https://wa.me/${digits}`, "_blank", "noopener");
    return;
  }

  const pageLabel = contact?.page_title || contact?.page_slug || fallbackLabels.noPage;

  const message = whatsappCopy.formMessage.replace("{page}", pageLabel);



  const text = encodeURIComponent(message);



  const url = `https://wa.me/${digits}?text=${text}`;



  window.open(url, "_blank", "noopener");



};







const idKey = (value: string | number) => String(value);







const normalizeStatusColor = (value?: string | null) => {



  if (!value) return null;



  const color = value.trim();



  return color || null;



};







const parseHexColor = (value: string) => {



  let hex = value.trim();



  if (!hex.startsWith("#")) return null;







  hex = hex.slice(1);







  if (hex.length === 3) {



    hex = hex



      .split("")



      .map(char => char + char)



      .join("");



  }







  if (hex.length !== 6) return null;







  const num = Number.parseInt(hex, 16);



  if (Number.isNaN(num)) return null;







  return {



    r: (num >> 16) & 255,



    g: (num >> 8) & 255,



    b: num & 255



  };



};







const convertHexToHsl = (value: string) => {



  const rgb = parseHexColor(value);



  if (!rgb) return null;







  let { r, g, b } = rgb;



  r /= 255;



  g /= 255;



  b /= 255;







  const max = Math.max(r, g, b);



  const min = Math.min(r, g, b);







  let h = 0;



  let s = 0;



  const l = (max + min) / 2;







  if (max !== min) {



    const delta = max - min;



    s = l > 0.5 ? delta / (2 - max - min) : delta / (max + min);







    switch (max) {



      case r:



        h = (g - b) / delta + (g < b ? 6 : 0);



        break;



      case g:



        h = (b - r) / delta + 2;



        break;



      case b:



        h = (r - g) / delta + 4;



        break;



    }







    h /= 6;



  }







  return {



    hue: Math.round(h * 360),



    saturation: Math.round(s * 100),



    lightness: Math.round(l * 100)



  };



};







const getContrastingTextColor = (background: string) => {



  const rgb = parseHexColor(background);



  if (!rgb) return "#0f172a";



  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;



  return luminance > 0.6 ? "#0f172a" : "#ffffff";



};







const getStatusColorForContact = (contact: LeadContact) => {



  const direct = normalizeStatusColor(contact.status_color);



  if (direct) return direct;



  const key = contact.status_id ? String(contact.status_id) : "";



  if (!key) return null;



  return normalizeStatusColor(statusColorMap.value[key]);



};







const statusChipStyle = (contact: LeadContact): CSSProperties => {



  const color = getStatusColorForContact(contact);



  if (!color) return {};



  return {



    backgroundColor: color,



    borderColor: color,



    color: getContrastingTextColor(color)



  };



};







const hexToHslWithLightness = (value: string, lightness = 95) => {



  const hsl = convertHexToHsl(value);



  if (!hsl) return null;



  return `hsl(${hsl.hue}, ${hsl.saturation}%, ${lightness}%)`;



};







const derivedColumnBackground = (columnId: string) => {



  const baseColor = statusColorMap.value[columnId];



  if (!baseColor) return null;



  return hexToHslWithLightness(baseColor, 95);



};







const derivedDarkColumnBackground = (columnId: string) => {



  const baseColor = statusColorMap.value[columnId];



  if (!baseColor) return null;



  const hsl = convertHexToHsl(baseColor);



  if (!hsl) return null;



  return `hsl(${hsl.hue}, 50%, 25%)`;



};







const kanbanColumnStyle = (columnId: string): CSSProperties => {



  const background = isDarkTheme.value



    ? derivedDarkColumnBackground(columnId)



    : derivedColumnBackground(columnId);







  const fallbackBg = isDarkTheme.value ? "hsl(220, 22%, 16%)" : "hsl(221, 33%, 96%)";



  const fallbackBorder = isDarkTheme.value ? "rgba(15, 23, 42, 0.6)" : "rgba(148, 163, 184, 0.35)";







  return {



    backgroundColor: background || fallbackBg,



    borderColor: background || fallbackBorder



  };



};







const kanbanHeaderStyle = (columnId: string): CSSProperties => {



  const originalColor = normalizeStatusColor(statusColorMap.value[columnId]);







  if (!originalColor || columnId === "null") {



    return {



      backgroundColor: isDarkTheme.value ? "#1f2738" : "#f8fafc",



      borderColor: isDarkTheme.value ? "#1f2738" : "rgba(148, 163, 184, 0.35)",



      color: isDarkTheme.value ? "#f8fafc" : "#0f172a"



    };



  }







  return {



    backgroundColor: originalColor,



    borderColor: originalColor,



    color: getContrastingTextColor(originalColor)



  };



};







const statusOptionStyle = (status: LeadStatus): CSSProperties => {



  const color = normalizeStatusColor(status.color);



  if (!color) return {};



  return {



    backgroundColor: color,



    borderColor: color,



    color: getContrastingTextColor(color)



  };



};







const closeStatusDropdown = () => {



  openStatusDropdown.value = null;



};







const toggleStatusDropdown = (contact: LeadContact) => {



  const key = idKey(contact.id);



  openStatusDropdown.value = openStatusDropdown.value === key ? null : key;



};







const selectStatusOption = async (contact: LeadContact, statusId: string | null) => {



  const key = idKey(contact.id);



  if (contactStatusSaving[key]) return;







  closeStatusDropdown();







  const current = contact.status_id ? String(contact.status_id) : null;



  if (current === statusId) return;







  contactStatusSaving[key] = true;



  try {



    await leadStore.setContactStatus(contact.id, statusId);



    showFeedback(viewCopy.messages.statusUpdated);



  } catch (err) {



    console.error(err);



    showFeedback(viewCopy.messages.statusUpdateError, true);



  } finally {



    contactStatusSaving[key] = false;



  }



};







const handleGlobalClick = (event: MouseEvent) => {



  const target = event.target as HTMLElement | null;



  if (!target) return;



  if (target.closest(".status-chip-container")) return;



  closeStatusDropdown();



};







const handleGlobalKeydown = (event: KeyboardEvent) => {



  if (event.key === "Escape") {



    closeStatusDropdown();



  }



};







const handleDeleteContact = async (contact: LeadContact) => {
  if (!canDeleteLeads.value) {
    showFeedback("Seu nível gerencial não permite excluir.", true);
    return;
  }



  const key = idKey(contact.id);



  if (contactDeleting[key]) return;







  const confirmed = window.confirm(getDeleteLeadMessage(contact.name || fallbackLabels.noName));



  if (!confirmed) return;







  contactDeleting[key] = true;



  try {



    await leadStore.deleteContact(contact.id);



    showFeedback(viewCopy.messages.leadDeleted);



  } catch (err) {



    console.error(err);



    showFeedback(viewCopy.messages.leadDeleteError, true);



  } finally {



    contactDeleting[key] = false;



  }



};

const openOpportunityDrawer = (contact: LeadContact) => {
  selectedOpportunityId.value = contact.id;
  isOpportunityDrawerOpen.value = true;
};

const syncOpportunityQuery = () => {
  const rawOpportunityId = route.query.opportunityId;
  if (!rawOpportunityId) return;
  selectedOpportunityId.value = Array.isArray(rawOpportunityId) ? rawOpportunityId[0] : rawOpportunityId;
  isOpportunityDrawerOpen.value = true;
  const nextQuery = { ...route.query };
  delete nextQuery.opportunityId;
  router.replace({ query: nextQuery });
};

const syncActiveTabFromRoute = () => {
  const routeName = typeof route.name === "string" ? route.name : "";
  if (routeName === "leads-forms") {
    activeTab.value = "forms";
    return;
  }
  if (routeName === "leads-clients" || routeName === "client-detail") {
    activeTab.value = "clients";
    return;
  }
  if (routeName === "leads-settings") {
    activeTab.value = "settings";
    return;
  }
  activeTab.value = "contacts";
};







const handleDragStart = (leadId: string | number) => {



  draggingLeadId.value = String(leadId);



};







const handleDragEnd = () => {



  draggingLeadId.value = null;



  dragOverColumn.value = null;



};







const handleDragEnter = (columnId: string) => {



  dragOverColumn.value = columnId;



};







const handleDrop = async (columnId: string) => {



  const leadId = draggingLeadId.value;



  dragOverColumn.value = null;



  draggingLeadId.value = null;



  if (!leadId) return;







  const contact = allContacts.value.find(item => idKey(item.id) === leadId);



  if (!contact) return;







  const targetStatus = columnId === "null" ? null : columnId;



  const currentStatus = contact.status_id ? String(contact.status_id) : null;



  if (currentStatus === targetStatus) return;







  contactStatusSaving[leadId] = true;



  try {



    await leadStore.setContactStatus(contact.id, targetStatus);



    showFeedback(viewCopy.messages.statusUpdated);



  } catch (err) {



    console.error(err);



    showFeedback(viewCopy.messages.statusUpdateError, true);



  } finally {



    contactStatusSaving[leadId] = false;



  }



};







const loadForms = () => leadStore.fetchForms(true).catch(() => undefined);



const loadContacts = () => leadStore.fetchContacts(undefined, true).catch(() => undefined);



const ensureStatuses = () => leadStore.fetchStatuses().catch(() => undefined);



const bootstrapLeads = async () => {



  try {



    await Promise.all([loadForms(), loadContacts(), ensureStatuses()]);



  } finally {



    isBootstrappingLeads.value = false;



  }



};







const toggleFilterPopover = (key: FilterKey) => {



  openFilterKey.value = openFilterKey.value === key ? null : key;



};







const closeFilterPopover = () => {



  openFilterKey.value = null;



};







const clearFilter = (key: FilterKey) => {



  if (key === "received") {



    listFilters.receivedFrom = "";



    listFilters.receivedTo = "";



  } else {



    (listFilters as any)[key] = [];



  }



};







const clearAllFilters = () => {



  listFilters.name = [];



  listFilters.form = [];



  listFilters.phone = [];



  listFilters.email = [];



  listFilters.city = [];



  listFilters.page = [];



  listFilters.status = [];



  opportunityStateFilter.value = "all";
  opportunityOutcomeFilter.value = "all";
  listFilters.receivedFrom = "";



  listFilters.receivedTo = "";



  closeFilterPopover();



};







const isFilterActive = (key: FilterKey) => {



  if (key === "received") return !!listFilters.receivedFrom || !!listFilters.receivedTo;



  return Boolean((listFilters as any)[key].length);



};







const toggleFilterValue = (key: ValueFilterKey, value: string) => {



  const target = (listFilters as Record<ValueFilterKey, string[]>)[key];



  const index = target.findIndex(item => item === value);



  if (index >= 0) {



    target.splice(index, 1);



  } else {



    target.push(value);



  }



};







const updateViewportMode = () => {



  const isMobile = window.innerWidth < 768;
  viewportHeightPx.value = window.innerHeight || 768;



  isMobileViewport.value = isMobile;



  if (isMobile && contactViewMode.value !== "list") {



    contactViewMode.value = "list";



  }

  nextTick(() => {
    scheduleKanbanHeightRecalc();
  });



};







const goToPlans = () => {



  router.push("/admin/planos");



};







onMounted(async () => {



  document.addEventListener("click", handleGlobalClick);



  document.addEventListener("keydown", handleGlobalKeydown);



  updateViewportMode();



  window.addEventListener("resize", updateViewportMode);



  await bootstrapLeads();
  syncActiveTabFromRoute();
  syncOpportunityQuery();
  nextTick(() => {
    scheduleKanbanHeightRecalc();
  });



});







onUnmounted(() => {



  document.removeEventListener("click", handleGlobalClick);



  document.removeEventListener("keydown", handleGlobalKeydown);



  window.removeEventListener("resize", updateViewportMode);



});







watch(activeTab, value => {



  if (value === "forms") {



    loadForms();



  } else {



    loadContacts();



    ensureStatuses();



  }

  nextTick(() => {
    scheduleKanbanHeightRecalc();
  });



});

watch(contactViewMode, () => {
  nextTick(() => {
    scheduleKanbanHeightRecalc();
  });
});

watch(kanbanScrollRef, el => {
  if (!el) return;
  scheduleKanbanHeightRecalc();
});

watch(contactsSectionRef, el => {
  if (!el) return;
  scheduleKanbanHeightRecalc();
});

watch(kanbanColumns, () => {
  scheduleKanbanHeightRecalc();
});



watch(
  () => route.query.opportunityId,
  value => {
    if (!value) return;
    syncOpportunityQuery();
  }
);

watch(
  () => route.name,
  () => {
    syncActiveTabFromRoute();
  },
  { immediate: true }
);
</script>







<style scoped>
.forms-premium {
  --verde: #3dcc5f;
  --verde-dim: #e9f9ee;
  --verde-border: rgba(61, 204, 95, 0.25);
  --surface: #ffffff;
  --surface2: #f7faf8;
  --text: #0f1f14;
  --text-2: #5d7567;
  --text-3: #8aa693;
  --border: #dbe8df;
}

.forms-create-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: none;
  border-radius: 10px;
  background: var(--verde);
  color: #0f1f14;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  transition: background-color 0.18s ease;
}

.forms-create-btn svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.forms-create-btn:hover {
  background: #48d666;
}

.forms-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.forms-kpi-card {
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--surface);
  padding: 18px 20px;
  min-height: 156px;
  box-shadow: 0 1px 2px rgba(15, 31, 20, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.forms-kpi-card:hover {
  transform: translateY(-2px);
  border-color: #cde2d3;
  box-shadow: 0 10px 20px rgba(15, 31, 20, 0.08);
}

.forms-kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.forms-kpi-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.forms-kpi-icon svg {
  width: 18px;
  height: 18px;
}

.forms-kpi-icon--forms {
  background: var(--verde-dim);
  color: #2f9a4e;
}

.forms-kpi-icon--leads {
  background: #eef8f2;
  color: #2e8a63;
}

.forms-kpi-icon--month {
  background: #eef9f1;
  color: #2d9a49;
}

.forms-kpi-icon--latest {
  background: #edf4ef;
  color: #4f6758;
}

.forms-kpi-badge {
  border-radius: 999px;
  border: 1px solid var(--border);
  background: #f6faf7;
  color: var(--text-2);
  font-size: 11px;
  line-height: 1;
  font-weight: 700;
  padding: 6px 9px;
}

.forms-kpi-value {
  margin: 0;
  color: var(--text);
  font-size: 32px;
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.forms-kpi-value--date {
  font-size: 28px;
}

.forms-kpi-label {
  margin-top: 4px;
  color: var(--text-2);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.forms-kpi-foot {
  margin-top: 6px;
  color: var(--text-3);
  font-size: 11px;
  line-height: 1.35;
  font-weight: 500;
}

.forms-list-card {
  border: 1px solid var(--border);
  border-radius: 1rem;
  background: var(--surface);
  overflow: hidden;
}

.forms-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
}

.list-title {
  color: var(--text);
  font-size: 1rem;
  font-weight: 600;
}

.forms-list-filters {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.search-wrap {
  position: relative;
  width: 320px;
  max-width: 100%;
}

.search-wrap svg {
  position: absolute;
  left: 10px;
  top: 50%;
  width: 15px;
  height: 15px;
  color: var(--text-3);
  transform: translateY(-50%);
}

.search-input,
.filter-select {
  width: 100%;
  height: 38px;
  border-radius: 0.75rem;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--text);
  font-size: 0.91rem;
  font-weight: 500;
}

.search-input {
  padding: 0 12px 0 33px;
}

.filter-select {
  width: 170px;
  padding: 0 12px;
}

.forms-list-body {
  display: flex;
  flex-direction: column;
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.form-row:last-child {
  border-bottom: 0;
}

.form-row:hover {
  background: var(--surface2);
}

.form-row-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.form-row-right {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  flex-shrink: 0;
}

.page-info {
  min-width: 0;
}

.page-name {
  color: var(--text);
  font-size: 1.03rem;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.page-dest {
  margin-top: 4px;
  color: var(--text-3);
  font-size: 0.84rem;
  line-height: 1.25;
}

.fields-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.field-chip {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface2);
  color: #4b6355;
  font-size: 11px;
  line-height: 1;
  font-weight: 600;
  padding: 4px 10px;
}

.form-leads-badge {
  min-width: 72px;
  text-align: center;
  border-radius: 999px;
  border: 1px solid var(--verde-border);
  background: var(--verde-dim);
  color: #1f7d37;
  font-weight: 600;
  font-size: 0.82rem;
  padding: 4px 10px;
}

.form-leads-badge.is-zero {
  color: var(--text-3);
  border-color: var(--border);
  background: #f2f6f3;
}

.page-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.page-action-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #fff;
  color: #5f7a6b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.18s ease;
}

.page-action-btn svg {
  width: 14px;
  height: 14px;
}

.page-action-btn--label {
  width: auto;
  min-width: 0;
  height: 34px;
  gap: 6px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
}

.page-action-btn--label svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.page-action-btn--label span {
  line-height: 1;
}

.page-action-btn.view {
  background: #e8f8ed;
  border-color: #c9ebd4;
  color: #2f9a4e;
}

.page-action-btn.view:hover {
  background: #3dcc5f;
  border-color: #3dcc5f;
  color: #fff;
}

.page-action-btn.edit:hover,
.page-action-btn.duplicate:hover {
  border-color: var(--verde-border);
  color: #2b8a46;
  background: #f6fcf8;
}

.page-action-btn.danger {
  color: #d93a45;
  border-color: #f2c7cb;
  background: #fff7f7;
}

.page-action-btn.danger:hover {
  color: #fff;
  border-color: #de3841;
  background: #de3841;
}

.form-actions-inline {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.forms-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem 1rem;
  color: var(--text-2);
  text-align: center;
}

.forms-empty-icon {
  width: 28px;
  height: 28px;
  color: var(--text-3);
}

.forms-empty-cta {
  margin-top: 0.35rem;
}

.opportunity-filters {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, max-content));
  align-items: center;
  gap: 8px 12px;
}

.opportunity-filter-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.opportunity-filter-active {
  justify-self: end;
}

@media (max-width: 920px) {
  .forms-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .forms-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .forms-kpi-card {
    min-height: 142px;
    padding: 16px 14px;
  }

  .forms-kpi-value {
    font-size: 28px;
  }

  .forms-list-header {
    flex-direction: column;
    align-items: stretch;
  }

  .forms-list-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .search-wrap,
  .filter-select {
    width: 100%;
  }

  .form-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .form-row-left {
    width: 100%;
  }

  .form-row-right {
    width: 100%;
    justify-content: space-between;
    margin-left: 0;
  }

  .form-leads-badge {
    margin-top: 2px;
  }

  .page-actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }

  .opportunity-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .opportunity-filter-item {
    display: grid;
    grid-template-columns: 1fr;
    align-items: stretch;
    gap: 6px;
  }

  .opportunity-filter-item select {
    width: 100%;
  }

  .opportunity-filter-active {
    grid-column: 1 / -1;
    justify-self: start;
  }
}

@media (max-width: 520px) {
  .forms-kpi-grid {
    grid-template-columns: 1fr;
  }
}



.status-chip-container {



  position: relative;



}



.status-chip-button {



  border: 1px solid rgba(148, 163, 184, 0.4);



  background-color: #f8fafc;



  color: #0f172a;



}



.status-chip-button svg {



  color: inherit;



}



.status-chip-button:disabled {



  cursor: not-allowed;



}



.status-dropdown {



  max-height: 16rem;



  overflow-y: auto;



}



.status-option {



  width: 100%;



  display: flex;



  align-items: center;



  gap: 0.5rem;



  border-radius: 9999px;



  border: 1px solid transparent;



  padding: 0.35rem 0.75rem;



  margin-top: 0.4rem;



  font-size: 0.78rem;



  font-weight: 600;



  text-transform: uppercase;



  letter-spacing: 0.03em;



  background-color: #f8fafc;



  color: #0f172a;



  transition: box-shadow 0.15s ease, transform 0.15s ease;



}



.status-option--neutral {



  background-color: #f1f5f9;



  color: #0f172a;



}



.status-option--active {



  box-shadow: 0 0 0 2px rgba(15, 23, 42, 0.15);



}



.status-option:not(.status-option--active):hover {



  transform: translateY(-1px);



  box-shadow: 0 12px 18px rgba(15, 23, 42, 0.18);



}



.status-dot {



  width: 0.8rem;



  height: 0.8rem;



  border-radius: 9999px;



  border: 1px solid rgba(15, 23, 42, 0.15);



}



.status-dropdown::-webkit-scrollbar {



  width: 6px;



}



.status-dropdown::-webkit-scrollbar-track {



  background-color: transparent;



}



.status-dropdown::-webkit-scrollbar-thumb {



  background-color: rgba(15, 23, 42, 0.15);



  border-radius: 9999px;



}



.kanban-column {



  background-color: #f8fafc;



}



.kanban-column__header {



  background-color: #f8fafc;



  border-color: rgba(148, 163, 184, 0.4);



  color: #0f172a;



  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;



}



.kanban-scroll::-webkit-scrollbar {



  height: 10px;



}



.kanban-scroll::-webkit-scrollbar-track {



  background-color: rgba(148, 163, 184, 0.25);



  border-radius: 9999px;



}



.kanban-scroll::-webkit-scrollbar-thumb {



  background-color: rgba(100, 116, 139, 0.6);



  border-radius: 9999px;



}



:global(.dark-theme) .kanban-scroll {



  background-color: #0f1118;



}



:global(.dark-theme) .kanban-scroll::-webkit-scrollbar-track {



  background-color: rgba(15, 23, 42, 0.5);



}



:global(.dark-theme) .kanban-scroll::-webkit-scrollbar-thumb {



  background-color: rgba(148, 163, 184, 0.7);



}



.filter-button {



  padding: 2px;



  border-radius: 9999px;



  color: #94a3b8;



  transition: background-color 0.15s ease, color 0.15s ease;



}



.filter-button:hover {



  background-color: rgba(148, 163, 184, 0.2);



}



.filter-popover {



  position: absolute;



  top: calc(100% + 6px);



  left: 0;



  z-index: 20;



  width: 12rem;



  border-radius: 0.75rem;



  border: 1px solid rgba(148, 163, 184, 0.35);



  background-color: #ffffff;



  padding: 0.75rem;



  box-shadow: 0 15px 30px rgba(15, 23, 42, 0.15);



}



.filter-option {



  display: flex;



  align-items: center;



  gap: 0.5rem;



  font-size: 0.75rem;



  color: #475569;



}



.filter-options {



  max-height: 11rem;



  overflow-y: auto;



  padding-right: 0.25rem;



}



.filter-option + .filter-option {



  margin-top: 0.35rem;



}



.filter-checkbox {



  width: 0.9rem;



  height: 0.9rem;



}



.filter-popover input,



.filter-popover select {



  background-color: #ffffff;



}



.kanban-scroll {



  overflow-x: auto;



  overflow-y: hidden;



}







.kanban-scroll::-webkit-scrollbar {



  height: 10px;



  width: 10px;



}







.kanban-scroll::-webkit-scrollbar-track {



  background-color: rgba(148, 163, 184, 0.25);



  border-radius: 9999px;



}







.kanban-scroll::-webkit-scrollbar-thumb {



  background-color: rgba(100, 116, 139, 0.6);



  border-radius: 9999px;



}







.kanban-column {



  background-color: #f8fafc;



  min-height: 0;



}







.kanban-column__header {



  background-color: #f8fafc;



  border-color: rgba(148, 163, 184, 0.4);



  color: #0f172a;



  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;



}







.kanban-column > .overflow-y-auto {



  min-height: 0;



  scrollbar-width: thin;



  scrollbar-color: rgba(100, 116, 139, 0.6) transparent;



}







.kanban-column > .overflow-y-auto::-webkit-scrollbar {



  width: 8px;



}







.kanban-column > .overflow-y-auto::-webkit-scrollbar-track {



  background: transparent;



}







.kanban-column > .overflow-y-auto::-webkit-scrollbar-thumb {



  background-color: rgba(100, 116, 139, 0.55);



  border-radius: 9999px;



}







:global(.dark-theme) .kanban-scroll {



  background-color: #0f1118;



}







:global(.dark-theme) .kanban-scroll::-webkit-scrollbar-track {



  background-color: rgba(15, 23, 42, 0.5);



}







:global(.dark-theme) .kanban-scroll::-webkit-scrollbar-thumb {



  background-color: rgba(148, 163, 184, 0.7);



}







:global(.dark-theme) .kanban-column > .overflow-y-auto::-webkit-scrollbar-thumb {



  background-color: rgba(148, 163, 184, 0.45);



}







:global(.dark-theme) .kanban-column {
  background-color: #0f1524;
  border-color: rgba(255, 255, 255, 0.08);
}

:global(.dark-theme) .kanban-column__header {
  background-color: #131b2f;
  border-color: rgba(255, 255, 255, 0.15);
  color: #f8fafc;
}

:global(.dark-theme) .filter-popover {



  background-color: #0f1524;



  border-color: rgba(255, 255, 255, 0.15);



}



:global(.dark-theme) .kanban-column {
  background-color: #0f1524;
  border-color: rgba(255, 255, 255, 0.08);
}

:global(.dark-theme) .kanban-column__header {
  background-color: #131b2f;
  border-color: rgba(255, 255, 255, 0.15);
  color: #f8fafc;
}

:global(.dark-theme) .filter-popover input,



:global(.dark-theme) .kanban-column {
  background-color: #0f1524;
  border-color: rgba(255, 255, 255, 0.08);
}

:global(.dark-theme) .kanban-column__header {
  background-color: #131b2f;
  border-color: rgba(255, 255, 255, 0.15);
  color: #f8fafc;
}

:global(.dark-theme) .filter-popover select {



  background-color: #0f1524;



}



:global(.dark-theme) .filter-option {



  color: #e2e8f0;



}



:global(.dark-theme) .filter-checkbox {



  accent-color: #3ed17a;



}

.leads-page-shell,
.leads-page,
.kanban-scroll {
  min-height: 0;
}

.kanban-column__header {
  flex-shrink: 0;
}



</style>


































