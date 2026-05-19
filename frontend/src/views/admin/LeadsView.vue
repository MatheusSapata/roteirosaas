<template>
<div v-if="isBootstrappingLeads" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8">
  <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
</div>
<div
  v-else
  class="leads-page-shell relative flex h-full min-h-0 w-full flex-col overflow-hidden"
>



    <div



      class="leads-page flex min-h-0 flex-1 flex-col gap-5 px-4 py-4 md:px-5"
      :class="[
        'overflow-hidden',
        { 'pointer-events-none select-none opacity-60': !planAllowed }
      ]"



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

        <div v-else-if="activeTab === 'contacts'" class="contacts-create-top flex items-center gap-2 md:gap-4">

  <button
    type="button"
    class="inline-flex items-center gap-2 rounded-[10px] bg-[#3DCC5F] px-4 py-[9px] text-[13px] font-semibold text-[#0F1F14] transition hover:bg-[#5BE07A]"
    @click="openManualOpportunityModal"
  >
    <span class="text-[15px] leading-none font-bold">+</span>
    <span>Nova oportunidade</span>
  </button>
    </div>

    <transition name="fade">
      <div
        v-if="feedback.message"
        class="pointer-events-none fixed bottom-6 right-6 z-[4200] max-w-[360px] rounded-xl px-4 py-3 text-sm font-semibold shadow-xl"
        :class="feedback.isError ? 'bg-rose-600 text-white' : 'bg-slate-900 text-white'"
      >
        {{ feedback.message }}
      </div>
    </transition>
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
                    <option value="all">Todas as etapas</option>
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



              <div v-if="contactViewMode === 'list'" class="crm-list-view flex min-h-0 flex-1 flex-col overflow-visible">
  <section class="crm-toolbar p-4 dark:bg-[#202020]">
    <div v-if="!isMobileViewport" class="opportunities-filter-bar opportunities-filter-bar--desktop">
      <div class="opportunities-filter-row opportunities-filter-row--primary">
        <span class="opportunities-filter-label">FILTRAR:</span>
        <div class="toolbar-ms">
          <button type="button" class="toolbar-ms-btn" :class="{ open: openToolbarFilter === 'stage' }" @click="toggleToolbarFilter('stage', $event)">Etapa <span v-if="listFilters.status.length" class="toolbar-ms-count">{{ listFilters.status.length }}</span></button>
        </div>
        <div class="toolbar-ms">
          <button type="button" class="toolbar-ms-btn" :class="{ open: openToolbarFilter === 'opportunityStatus' }" @click="toggleToolbarFilter('opportunityStatus', $event)">Status <span v-if="opportunityStatusSelections.length" class="toolbar-ms-count">{{ opportunityStatusSelections.length }}</span></button>
        </div>
        <div class="toolbar-ms">
          <button type="button" class="toolbar-ms-btn" :class="{ open: openToolbarFilter === 'page' }" @click="toggleToolbarFilter('page', $event)">Página <span v-if="listFilters.page.length" class="toolbar-ms-count">{{ listFilters.page.length }}</span></button>
        </div>
        <div class="toolbar-ms">
          <button type="button" class="toolbar-ms-btn" :class="{ open: openToolbarFilter === 'idle' }" @click="toggleToolbarFilter('idle', $event)">Sem interação <span v-if="crmIdleSelections.length" class="toolbar-ms-count">{{ crmIdleSelections.length }}</span></button>
        </div>
      </div>
      <div class="toolbar-spacer"></div>
      <div class="toolbar-right-actions">
        <div class="toolbar-search"><svg viewBox="0 0 24 24" class="toolbar-search-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input v-model="crmSearchQuery" type="text" placeholder="Buscar oportunidade..." /></div>
        <button type="button" class="toolbar-ghost-btn toolbar-ghost-btn--square" @click="openColumnsSidebar">
          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/></svg>
          Colunas
        </button>
        <button type="button" class="toolbar-ghost-btn toolbar-ghost-btn--square" @click="saveCurrentView">
          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/></svg>
          Salvar visualização
        </button>
      </div>
    </div>
    <div v-else class="opportunities-filter-bar">
      <div class="opportunities-filter-row opportunities-filter-row--search">
        <div class="toolbar-search"><svg viewBox="0 0 24 24" class="toolbar-search-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input v-model="crmSearchQuery" type="text" placeholder="Buscar cliente..." /></div>
        <button type="button" class="mobile-create-btn" @click="openManualOpportunityModal">
          <span class="mobile-create-btn-plus">+</span>
          <span>Criar</span>
        </button>
      </div>
      <div class="opportunities-filter-row opportunities-filter-row--primary">
        <div class="toolbar-ms">
          <button type="button" class="toolbar-ms-btn" :class="{ open: openToolbarFilter === 'stage' }" @click="toggleToolbarFilter('stage', $event)"><svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18"/><path d="M6 12h12"/><path d="M10 19h4"/></svg>Etapa <span v-if="listFilters.status.length" class="toolbar-ms-count">{{ listFilters.status.length }}</span></button>
        </div>
        <div class="toolbar-ms">
          <button type="button" class="toolbar-ms-btn" :class="{ open: openToolbarFilter === 'opportunityStatus' }" @click="toggleToolbarFilter('opportunityStatus', $event)"><svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18"/><path d="M6 12h12"/><path d="M10 19h4"/></svg>Status <span v-if="opportunityStatusSelections.length" class="toolbar-ms-count">{{ opportunityStatusSelections.length }}</span></button>
        </div>
        <div class="toolbar-ms">
          <button type="button" class="toolbar-ms-btn" :class="{ open: openToolbarFilter === 'page' }" @click="toggleToolbarFilter('page', $event)"><svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18"/><path d="M6 12h12"/><path d="M10 19h4"/></svg>Página <span v-if="listFilters.page.length" class="toolbar-ms-count">{{ listFilters.page.length }}</span></button>
        </div>
      </div>
    </div>
  </section>
  <article v-if="!isMobileViewport" class="opps-table-shell relative mt-2 flex flex-1 flex-col overflow-visible">
    <div class="flex-1 overflow-visible">
      <table class="opps-table table-fixed min-w-full text-sm">
        <thead class="sticky top-0 z-10"><tr class="text-left text-xs font-semibold uppercase tracking-wide"><th class="w-[40px] px-2 py-3"><div class="flex justify-center"><input class="h-4 w-4 cursor-pointer accent-emerald-500" type="checkbox" :checked="areAllVisibleOpportunitiesSelected" @change="toggleAllVisibleOpportunities" /></div></th><th v-if="isColumnVisible('cliente')" class="w-[180px] px-3 py-3" style="width:180px;min-width:180px;max-width:180px;">Nome</th><template v-for="col in orderedOptionalColumns" :key="`head-${col.key}`"><th v-if="col.visible && col.key === 'telefone'" class="w-[150px] px-2 py-3">Telefone</th><th v-if="col.visible && col.key === 'status'" class="w-[170px] px-2 py-3">Etapa</th><th v-if="col.visible && col.key === 'pagina'" class="w-[230px] px-2 py-3" style="width:230px;min-width:230px;max-width:230px;">Origem</th><th v-if="col.visible && col.key === 'valor'" class="w-[105px] px-2 py-3 text-center">Valor</th><th v-if="col.visible && col.key === 'chegouEm'" class="w-[100px] px-2 py-3">Chegou em</th><th v-if="col.visible && col.key === 'ultima'" class="w-[130px] px-2 py-3 text-center">Sem interação</th></template><th v-if="isColumnVisible('acoes')" class="w-[108px] px-2 py-3 text-right">Ações</th></tr></thead>
        <tbody>
          <template v-for="group in groupedContactsForCrm" :key="group.key">
            <tr class="opps-group-row" @click="toggleGroupCollapse(group.key)"><td :colspan="visibleCrmColumnsCount + 2" class="px-4 py-1 text-xs font-semibold" :style="groupHeaderStyle(group.key)"><button type="button" class="opps-group-toggle-btn" :class="{ collapsed: isGroupCollapsed(group.key) }" @click.stop="toggleGroupCollapse(group.key)"><svg viewBox="0 0 20 20" class="h-3.5 w-3.5" fill="currentColor" aria-hidden="true"><path d="M5.2 7.5a.75.75 0 0 1 1.06 0L10 11.24l3.74-3.74a.75.75 0 1 1 1.06 1.06l-4.27 4.27a.75.75 0 0 1-1.06 0L5.2 8.56a.75.75 0 0 1 0-1.06Z" /></svg></button><span class="inline-flex items-center gap-2 rounded-full border px-2.5 py-1" :style="groupPillStyle(group.key)">{{ group.label }}</span> <span class="opps-group-meta">{{ group.contacts.length }} contatos · {{ formatOpportunityValue(group.totalValueCents) }}</span></td></tr>
            <tr v-for="contact in visibleGroupContacts(group)" :key="contact.id" class="opps-data-row cursor-pointer transition" :class="opportunityRowClass(contact)" :style="contactRowStyle(contact)" @click="openOpportunityDrawer(contact)">
              <td class="w-[40px] px-2 py-2.5" @click.stop><div class="flex justify-center"><input class="h-4 w-4 cursor-pointer accent-emerald-500" type="checkbox" :checked="isOpportunitySelected(contact)" @change="toggleOpportunitySelection(contact)" /></div></td>
              <td v-if="isColumnVisible('cliente')" class="w-[180px] px-4 py-2.5" style="width:180px;min-width:180px;max-width:180px;">
                <div class="min-w-0 max-w-[180px]">
                  <div class="flex flex-wrap items-center gap-2">
                    <p class="truncate font-semibold text-slate-900 dark:text-white" :title="contact.name || fallbackLabels.noName">{{ truncatedContactName(contact.name) }}</p>
                  </div>
                </div>
              </td>
              <template v-for="col in orderedOptionalColumns" :key="`cell-${contact.id}-${col.key}`">
              <td v-if="col.visible && col.key === 'telefone'" class="w-[150px] px-2 py-2.5" @click.stop>
                <button
                  v-if="contact.phone"
                  type="button"
                  class="phone-link inline-flex max-w-[170px] items-center gap-1 text-[12px] font-normal text-[#8A9E8A] transition hover:text-[#718771]"
                  :title="getWhatsappTitle(contact.phone)"
                  @click.stop="openWhatsapp(contact)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 shrink-0 text-[#25D366]" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M16.75 13.96c-.25-.13-1.47-.72-1.7-.8-.23-.08-.4-.12-.57.12-.17.25-.65.8-.8.96-.14.17-.3.19-.55.06-.25-.13-1.06-.39-2.02-1.23-.74-.66-1.25-1.47-1.4-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.3.37-.45.12-.14.17-.25.25-.42.08-.17.04-.31-.02-.45-.06-.14-.57-1.37-.78-1.87-.2-.49-.41-.42-.57-.43h-.48c-.17 0-.45.06-.68.31-.23.25-.88.86-.88 2.1s.9 2.43 1.02 2.6c.12.17 1.76 2.69 4.25 3.77.59.26 1.06.42 1.42.54.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.17.21-.57.21-1.06.15-1.17-.06-.11-.23-.17-.48-.3Z" />
                    <path d="M12.04 2C6.77 2 2.5 6.26 2.5 11.52c0 1.85.53 3.65 1.52 5.2L2.4 21.5l4.9-1.57c1.43.78 3.04 1.2 4.7 1.2h.04c5.26 0 9.53-4.26 9.53-9.52C21.57 6.26 17.3 2 12.04 2Zm0 17.42h-.03c-1.5 0-2.97-.4-4.25-1.16l-.3-.18-2.9.93.95-2.82-.2-.29a7.83 7.83 0 0 1-1.2-4.18c0-4.3 3.5-7.8 7.82-7.8 2.08 0 4.03.8 5.5 2.28a7.75 7.75 0 0 1 2.29 5.5c0 4.3-3.5 7.8-7.8 7.8Z" />
                  </svg>
                  <span class="truncate">{{ contact.phone }}</span>
                </button>
                <span v-else class="text-xs text-slate-400">-</span>
              </td>
              <td v-if="col.visible && col.key === 'status'" class="w-[170px] px-2 py-2.5" @click.stop>
                <div class="status-chip-container relative inline-flex">
                  <button
                    type="button"
                    class="status-chip-button inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold"
                    :style="statusChipStyle(contact)"
                    @click.stop="toggleStatusDropdown(contact, $event)"
                  >
                    <span>{{ contact.status_name || fallbackLabels.noStage }}</span>
                    <svg viewBox="0 0 20 20" class="h-3.5 w-3.5" fill="currentColor" aria-hidden="true">
                      <path d="M5.2 7.5a.75.75 0 0 1 1.06 0L10 11.24l3.74-3.74a.75.75 0 1 1 1.06 1.06l-4.27 4.27a.75.75 0 0 1-1.06 0L5.2 8.56a.75.75 0 0 1 0-1.06Z" />
                    </svg>
                  </button>

                </div>
              </td>
              <td v-if="col.visible && col.key === 'pagina'" class="w-[230px] px-2 py-2.5 text-[13px]" style="width:230px;min-width:230px;max-width:230px;" @click.stop>
                <button
                  v-if="!isManualOpportunity(contact)"
                  type="button"
                  class="origin-link truncate text-[#8A9E8A] transition hover:text-[#718771]"
                  :title="truncatedPageLabel(contact)"
                  @click.stop="openContactOrigin(contact)"
                >
                  {{ truncatedPageLabel(contact) }}
                </button>
                <span v-else class="text-[#8A9E8A]">{{ truncatedPageLabel(contact) }}</span>
              </td>
              <td v-if="col.visible && col.key === 'valor'" class="w-[105px] px-2 py-2.5 text-center text-xs" @click.stop>
                <template v-if="inlineValueContactId === idKey(contact.id)">
                  <div class="inline-flex items-center gap-1">
                    <input v-model="inlineValueInput" type="text" placeholder="R$ 0,00" class="w-[78px] rounded-md border border-slate-200 px-2 py-1 text-[11px] text-slate-700 outline-none focus:border-brand" />
                    <button type="button" class="inline-flex h-5 w-5 items-center justify-center rounded border border-emerald-200 bg-emerald-50 text-emerald-700" @click.stop="saveInlineValue(contact)">
                      <svg viewBox="0 0 20 20" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="m4 10 4 4 8-8"/></svg>
                    </button>
</div>
</template>
                <button
                  v-else-if="!contact.estimated_value_cents"
                  type="button"
                  class="text-[#8A9E8A] transition hover:underline"
                  @click.stop="beginInlineValueEdit(contact)"
                >
                  Sem valor
                </button>
                <span v-else class="font-semibold text-[#111A14]">{{ formatOpportunityValue(contact.estimated_value_cents) }}</span>
              </td>
              <td v-if="col.visible && col.key === 'chegouEm'" class="w-[100px] px-2 py-2.5 text-xs text-[#8A9E8A]">{{ formatDateDayMonthTime(contact.created_at) }}</td>
              <td v-if="col.visible && col.key === 'ultima'" class="w-[130px] px-2 py-2.5 text-center">
                <div class="flex justify-center">
                  <span
                    v-if="shouldShowIdleChip(contact)"
                    class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium"
                    :class="idleChipClass(contact)"
                  >
                    <span class="h-1.5 w-1.5 rounded-full" :class="idleDotClass(contact)"></span>
                    <span>{{ idleChipLabel(contact) }}</span>
                  </span>
                  <span v-else class="text-xs text-slate-400">-</span>
                </div>
              </td>
              </template>
              <td v-if="isColumnVisible('acoes')" class="w-[108px] px-2 py-2.5 text-right" @click.stop>
                <div class="inline-flex items-center gap-1">
                  <button type="button" class="action-icon-btn action-muted" title="Ver oportunidade" @click.stop="openOpportunityDrawer(contact)">
                    <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                  </button>
                  <button type="button" class="action-icon-btn action-like" :class="getOpportunityOutcome(contact) === 'won' ? 'is-selected' : ''" title="Ganho" @click.stop="markOpportunityOutcome(contact, 'won')">
                    <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                  </button>
                  <button type="button" class="action-icon-btn action-dislike" :class="getOpportunityOutcome(contact) === 'lost' ? 'is-selected' : ''" title="Perda" @click.stop="markOpportunityOutcome(contact, 'lost')">
                    <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
                  </button>
                  <button v-if="canDeleteLeads" type="button" class="action-icon-btn action-muted" title="Excluir" @click.stop="handleDeleteContact(contact)">
                    <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16"/><path d="M9 4h6"/><path d="M7 7l1 13h8l1-13"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
                  </button>
                </div>
              </td>
            </tr>
          </template>
          <tr v-if="!groupedContactsForCrm.length"><td :colspan="visibleCrmColumnsCount + 2" class="px-4 py-10 text-center text-sm text-slate-500 dark:text-slate-300">{{ viewCopy.emptyStates.contacts.noFilters }}</td></tr>
        </tbody>
      </table>
    </div>
  </article>
  <section v-else class="mobile-opps-list mt-1">
    <template v-for="group in groupedContactsForCrm" :key="`m-${group.key}`">
      <div class="mobile-group-strip" :style="groupHeaderStyle(group.key)" @click="toggleGroupCollapse(group.key)">
        <button type="button" class="opps-group-toggle-btn" :class="{ collapsed: isGroupCollapsed(group.key) }" @click.stop="toggleGroupCollapse(group.key)">
          <svg viewBox="0 0 20 20" class="h-3.5 w-3.5" fill="currentColor" aria-hidden="true"><path d="M5.2 7.5a.75.75 0 0 1 1.06 0L10 11.24l3.74-3.74a.75.75 0 1 1 1.06 1.06l-4.27 4.27a.75.75 0 0 1-1.06 0L5.2 8.56a.75.75 0 0 1 0-1.06Z" /></svg>
        </button>
        <span class="mobile-group-title mobile-group-pill" :style="groupPillStyle(group.key)">{{ group.label }}</span>
        <span class="mobile-group-meta">{{ group.contacts.length }} contatos · {{ formatOpportunityValue(group.totalValueCents) }}</span>
      </div>
      <article
        v-for="contact in visibleGroupContacts(group)"
        :key="`mc-${contact.id}`"
        class="mobile-opps-card"
        :class="opportunityRowClass(contact)"
        :style="contactRowStyle(contact)"
        @click="openOpportunityDrawer(contact)"
      >
        <div class="mobile-card-layout">
          <div class="mobile-card-main">
        <div class="mobile-card-top-row">
          <div class="mobile-card-top">{{ formatDateDayMonthTime(contact.created_at) }}</div>
          <div class="mobile-card-origin">{{ truncatedPageLabel(contact) }}</div>
        </div>
            <div class="mobile-card-name">{{ contact.name || fallbackLabels.noName }}</div>
            <div class="mobile-card-phone" @click.stop>
              <button
                v-if="contact.phone"
                type="button"
                class="phone-link inline-flex items-center gap-1 text-[10px] font-normal text-[#8A9E8A] transition hover:text-[#718771]"
                :title="getWhatsappTitle(contact.phone)"
                @click.stop="openWhatsapp(contact)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 shrink-0 text-[#25D366]" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M16.75 13.96c-.25-.13-1.47-.72-1.7-.8-.23-.08-.4-.12-.57.12-.17.25-.65.8-.8.96-.14.17-.3.19-.55.06-.25-.13-1.06-.39-2.02-1.23-.74-.66-1.25-1.47-1.4-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.3.37-.45.12-.14.17-.25.25-.42.08-.17.04-.31-.02-.45-.06-.14-.57-1.37-.78-1.87-.2-.49-.41-.42-.57-.43h-.48c-.17 0-.45.06-.68.31-.23.25-.88.86-.88 2.1s.9 2.43 1.02 2.6c.12.17 1.76 2.69 4.25 3.77.59.26 1.06.42 1.42.54.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.17.21-.57.21-1.06.15-1.17-.06-.11-.23-.17-.48-.3Z" />
                  <path d="M12.04 2C6.77 2 2.5 6.26 2.5 11.52c0 1.85.53 3.65 1.52 5.2L2.4 21.5l4.9-1.57c1.43.78 3.04 1.2 4.7 1.2h.04c5.26 0 9.53-4.26 9.53-9.52C21.57 6.26 17.3 2 12.04 2Zm0 17.42h-.03c-1.5 0-2.97-.4-4.25-1.16l-.3-.18-2.9.93.95-2.82-.2-.29a7.83 7.83 0 0 1-1.2-4.18c0-4.3 3.5-7.8 7.82-7.8 2.08 0 4.03.8 5.5 2.28a7.75 7.75 0 0 1 2.29 5.5c0 4.3-3.5 7.8-7.8 7.8Z" />
                </svg>
                <span>{{ contact.phone }}</span>
              </button>
              <span v-else class="text-[12px] text-slate-400">-</span>
            </div>
          </div>
          <div class="mobile-card-actions mobile-card-actions--row" @click.stop>
            <button type="button" class="action-icon-btn action-muted" title="Ver oportunidade" @click.stop="openOpportunityDrawer(contact)">
              <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </button>
            <button type="button" class="action-icon-btn action-like" :class="getOpportunityOutcome(contact) === 'won' ? 'is-selected' : ''" title="Ganho" @click.stop="markOpportunityOutcome(contact, 'won')">
              <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
            </button>
            <button type="button" class="action-icon-btn action-dislike" :class="getOpportunityOutcome(contact) === 'lost' ? 'is-selected' : ''" title="Perda" @click.stop="markOpportunityOutcome(contact, 'lost')">
              <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
            </button>
            <button v-if="canDeleteLeads" type="button" class="action-icon-btn action-muted" title="Excluir" @click.stop="handleDeleteContact(contact)">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M9 4h6"/><path d="M7 7l1 13h8l1-13"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
            </button>
          </div>
        </div>
      </article>
    </template>
    <div v-if="!groupedContactsForCrm.length" class="px-4 py-8 text-center text-sm text-slate-500">{{ viewCopy.emptyStates.contacts.noFilters }}</div>
  </section>
  <teleport to="body">
    <div
      v-if="openToolbarFilter"
      class="toolbar-ms-dropdown toolbar-ms-dropdown-portal"
      :style="toolbarDropdownFloatingStyle"
    >
      <template v-if="openToolbarFilter === 'stage'">
        <label v-for="option in stageFilterOptions" :key="option.value" class="toolbar-ms-option"><input type="checkbox" :checked="listFilters.status.includes(option.value)" @change="toggleStageFilterOption(option.value)" /><span>{{ option.label }}</span></label>
        <div class="toolbar-ms-actions">
          <button type="button" @click="selectAllStageFilters">Selecionar todos</button>
          <button type="button" @click="clearStageFilters">Limpar</button>
        </div>
      </template>
      <template v-else-if="openToolbarFilter === 'opportunityStatus'">
        <label v-for="option in opportunityStatusOptions" :key="option.value" class="toolbar-ms-option"><input type="checkbox" :checked="opportunityStatusSelections.includes(option.value)" @change="toggleOpportunityStatusSelection(option.value)" /><span>{{ option.label }}</span></label>
        <div class="toolbar-ms-actions">
          <button type="button" @click="selectAllStatusFilters">Selecionar todos</button>
          <button type="button" @click="clearStatusFilters">Limpar</button>
        </div>
      </template>
      <template v-else-if="openToolbarFilter === 'page'">
        <label v-for="option in crmPageOptions" :key="option" class="toolbar-ms-option"><input type="checkbox" :checked="listFilters.page.includes(option)" @change="togglePageFilterOption(option)" /><span>{{ option }}</span></label>
        <div class="toolbar-ms-actions">
          <button type="button" @click="selectAllPageFilters">Selecionar todos</button>
          <button type="button" @click="clearPageFilters">Limpar</button>
        </div>
      </template>
      <template v-else-if="openToolbarFilter === 'idle'">
        <p class="toolbar-ms-subtitle">Sem interação há</p>
        <label v-for="option in idleFilterOptions" :key="option.value" class="toolbar-ms-option"><input type="checkbox" :checked="crmIdleSelections.includes(option.value)" @change="toggleIdleFilterSelection(option.value)" /><span>{{ option.label }}</span></label>
        <div class="toolbar-ms-actions">
          <button type="button" @click="selectAllIdleFilters">Selecionar todos</button>
          <button type="button" @click="clearIdleFilters">Limpar</button>
        </div>
      </template>
    </div>
  </teleport>
  <teleport to="body">
    <div
      v-if="openStatusDropdown && dropdownStatusContact"
      class="status-dropdown status-dropdown-portal"
      :style="statusDropdownFloatingStyle"
    >
      <button
        type="button"
        class="status-option-badge"
        :style="statusOptionDefaultStyle"
        @click.stop="selectStatusOption(dropdownStatusContact, null)"
      >
        {{ fallbackLabels.noStage }}
      </button>
      <button
        v-for="status in leadStatuses"
        :key="status.id"
        type="button"
        class="status-option-badge"
        :style="statusOptionStyle(status)"
        @click.stop="selectStatusOption(dropdownStatusContact, String(status.id))"
      >
        {{ status.name }}
      </button>
    </div>
  </teleport>
  <teleport to="body">
    <div v-if="columnsMenuOpen" class="columns-overlay" @click="columnsMenuOpen = false"></div>
    <aside v-if="columnsMenuOpen" class="columns-sidebar">
      <div class="columns-sidebar-head">
        <p class="columns-sidebar-title">Colunas visíveis</p>
        <button type="button" class="columns-sidebar-close" @click="columnsMenuOpen = false">✕</button>
      </div>
      <div class="columns-sidebar-body">
        <p class="columns-sidebar-section">Obrigatórias</p>
        <label v-for="col in crmColumnConfig.filter(c => isMandatoryColumn(c.key))" :key="col.key" class="columns-sidebar-item">
          <input type="checkbox" checked disabled class="h-4 w-4" />
          <span>{{ col.label === "Cliente" ? "Nome" : col.label }}</span>
          <span class="columns-fixed-tag">fixo</span>
        </label>
        <p class="columns-sidebar-section">Opcionais</p>
        <label
          v-for="col in draftOptionalColumns"
          :key="col.key"
          class="columns-sidebar-item"
          :class="{ 'is-dragging': draggingColumnKey === col.key, 'is-drag-over': dragOverColumnKey === col.key }"
          draggable="true"
          @dragstart="handleColumnDragStart(col.key)"
          @dragenter.prevent="handleColumnDragEnter(col.key)"
          @dragover.prevent
          @drop.prevent="handleColumnDrop(col.key)"
          @dragend="handleColumnDragEnd"
        >
          <span class="columns-drag-handle" aria-hidden="true">
            <svg viewBox="0 0 20 20" class="h-3.5 w-3.5" fill="currentColor">
              <circle cx="6" cy="5" r="1.2" />
              <circle cx="6" cy="10" r="1.2" />
              <circle cx="6" cy="15" r="1.2" />
              <circle cx="12" cy="5" r="1.2" />
              <circle cx="12" cy="10" r="1.2" />
              <circle cx="12" cy="15" r="1.2" />
            </svg>
          </span>
          <input v-model="draftColumnVisibility[col.key]" type="checkbox" class="h-4 w-4" />
          <span>{{ col.label === "Última interação" ? "Sem interação" : col.label }}</span>
        </label>
        <p class="columns-drag-tip">Arraste as colunas opcionais para reordenar.</p>
      </div>
      <div class="columns-sidebar-foot">
        <button type="button" class="columns-foot-btn columns-foot-btn--ghost" @click="resetColumnsToDefault">Redefinir padrão</button>
        <button type="button" class="columns-foot-btn columns-foot-btn--apply" @click="applyColumnsSelection">Aplicar</button>
      </div>
    </aside>
  </teleport>
  <div class="opportunity-bulk-bar" :class="{ visible: selectedOpportunityIds.length > 0 }">
    <span class="bulk-count">{{ selectedOpportunityIds.length }} selecionadas</span>
    <div class="bulk-spacer"></div>
    <button type="button" class="bulk-btn bulk-won" @click="applyBulkOutcome('won')">
      <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
      Marcar como ganhas
    </button>
    <button type="button" class="bulk-btn bulk-lost" @click="applyBulkOutcome('lost')">
      <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
      Marcar como perdidas
    </button>
    <button v-if="canDeleteLeads" type="button" class="bulk-btn bulk-del" @click="deleteSelectedOpportunities">
      <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/></svg>
      Excluir
    </button>
    <div class="bulk-stage-wrap">
      <button type="button" class="bulk-btn bulk-stage-btn" @click="bulkStageMenuOpen = !bulkStageMenuOpen">
        <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>
        Mover para etapa
        <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 opacity-70" fill="currentColor"><path d="M5.2 7.5a.75.75 0 0 1 1.06 0L10 11.24l3.74-3.74a.75.75 0 1 1 1.06 1.06l-4.27 4.27a.75.75 0 0 1-1.06 0L5.2 8.56a.75.75 0 0 1 0-1.06Z"/></svg>
      </button>
      <div v-if="bulkStageMenuOpen" class="bulk-stage-menu">
        <button type="button" class="bulk-stage-opt" @click="selectBulkStage('null')">Sem etapa</button>
        <button v-for="status in leadStatuses" :key="status.id" type="button" class="bulk-stage-opt" @click="selectBulkStage(String(status.id))">
          {{ status.name }}
        </button>
      </div>
    </div>
    <button type="button" class="bulk-btn bulk-cancel" @click="clearBulkSelection">
      <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
      Cancelar
    </button>
  </div>
</div>

<div

  v-else-if="false"



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



                {{ contact.status_name || fallbackLabels.noStage }}



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
    @invalid="handleBuilderInvalid"



  />



  <Teleport to="body">
    <div v-if="opportunityWhatsAppModalOpen" class="fixed inset-0 z-[3200] flex items-center justify-center bg-slate-950/55 p-4" @click="closeOpportunityWhatsAppModal">
      <div class="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl" @click.stop>
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-slate-900">Enviar WhatsApp</h3>
          <button type="button" class="rounded-md px-2 py-1 text-sm text-slate-500 hover:bg-slate-100" @click="closeOpportunityWhatsAppModal">Fechar</button>
        </div>
        <p class="mb-3 text-sm text-slate-600">{{ opportunityWhatsAppTargetName || "Contato" }} · {{ opportunityWhatsAppTargetPhone || "-" }}</p>
        <textarea
          v-model="opportunityWhatsAppDraft"
          rows="5"
          class="w-full resize-y rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
          placeholder="Digite a mensagem..."
        />
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700" @click="openOpportunityWhatsAppWeb">
            Abrir conversa
          </button>
          <button type="button" class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" :disabled="opportunityWhatsAppSending || !opportunityWhatsAppDraft.trim()" @click="sendOpportunityWhatsAppMessage">
            {{ opportunityWhatsAppSending ? "Enviando..." : "Enviar mensagem" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <Teleport to="body">
    <div v-if="opportunityWhatsAppSuccessModalOpen" class="fixed inset-0 z-[3210] flex items-center justify-center bg-slate-950/55 p-4" @click="closeOpportunityWhatsAppSuccessModal">
      <div class="w-full max-w-md rounded-2xl border border-emerald-100 bg-white p-5 shadow-2xl" @click.stop>
        <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
          <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="m5 13 4 4L19 7" />
          </svg>
        </div>
        <h3 class="text-center text-lg font-semibold text-slate-900">Mensagem enviada</h3>
        <p class="mt-2 text-center text-sm text-slate-600">A mensagem foi enviada com sucesso para o contato.</p>
        <div class="mt-5 flex justify-center">
          <button type="button" class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700" @click="closeOpportunityWhatsAppSuccessModal">
            Ok, entendi
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <Teleport to="body">
    <div v-if="manualOpportunityModalOpen" class="app-modal-overlay fixed inset-0 z-[150] flex items-center justify-center px-4">
      <div class="w-full max-w-3xl rounded-[28px] bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Oportunidades</p>
            <h2 class="mt-2 text-2xl font-bold text-slate-900">Nova oportunidade manual</h2>
            <p class="mt-2 text-sm text-slate-500">Cadastre uma oportunidade sem depender de formulário.</p>
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
              <option value="">Sem etapa</option>
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
    mode="drawer"
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
import api, { API_PERMISSION_DENIED_EVENT } from "../../services/api";
import { ensureWhatsAppConversation, sendWhatsAppText } from "../../services/whatsapp";



import { useThemeStore } from "../../store/useThemeStore";
import { useAuthStore } from "../../store/useAuthStore";



import { useLeadFeatureGate } from "../../composables/useLeadFeatureGate";
import { hasAnyPermission } from "../../utils/permissions";



import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";
import type { AdminLanguage, AdminTranslatable } from "../../utils/adminI18n";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";
import { useAgencyStore } from "../../store/useAgencyStore";







type TabKey = "forms" | "contacts" | "clients" | "settings";



type FilterKey = "name" | "form" | "phone" | "email" | "city" | "page" | "status" | "received";



type ValueFilterKey = Exclude<FilterKey, "received">;



type ContactViewMode = "list" | "kanban";







const router = useRouter();
const route = useRoute();



const leadStore = useLeadCaptureStore();
const authStore = useAuthStore();
const agencyStore = useAgencyStore();



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
      status: { pt: "Etapa", es: "Etapa" },
      actions: { pt: "Ações", es: "Acciones" }
    },
    kanban: {
      allPages: { pt: "Todas as páginas", es: "Todas las páginas" },
      allForms: { pt: "Todos os formulários", es: "Todos los formularios" }
    },
    opportunity: {
      all: { pt: "Todos", es: "Todos" },
      open: { pt: "Aberta", es: "Abierta" },
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
    statusUpdated: { pt: "Etapa atualizada.", es: "Etapa actualizada." },
    statusUpdateError: { pt: "Não foi possível atualizar a etapa.", es: "No se pudo actualizar la etapa." },
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
      noStage: { pt: "Sem etapa", es: "Sin etapa" },
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
const opportunityStatusFilter = ref<"all" | "open" | "won" | "lost">("all");
const crmSearchQuery = ref("");
const crmPageFilter = ref("all");
const crmIdleFilter = ref<"all" | "today" | "upto7" | "8to14" | "gt15">("all");
const opportunityStatusSelections = ref<Array<"open" | "won" | "lost">>([]);
const crmIdleSelections = ref<Array<"today" | "upto7" | "8to14" | "gt15">>([]);
const openToolbarFilter = ref<"stage" | "opportunityStatus" | "page" | "idle" | null>(null);
const toolbarDropdownFloatingStyle = ref<CSSProperties>({});
const selectedOpportunityIds = ref<string[]>([]);
const bulkTargetStatusId = ref<string>("");
const bulkStageMenuOpen = ref(false);
const activeSavedView = ref("default");
const loadedSavedViewsKey = ref<string | null>(null);
type CrmViewSnapshot = {
  search: string;
  status?: "all" | "open" | "won" | "lost";
  statusSelections?: Array<"open" | "won" | "lost">;
  page: string;
  pageSelections?: string[];
  idle: "all" | "today" | "upto7" | "8to14" | "gt15";
  idleSelections?: Array<"today" | "upto7" | "8to14" | "gt15">;
  columns: Record<string, boolean>;
  columnOrder?: string[];
  filters?: {
    name: string[];
    form: string[];
    phone: string[];
    email: string[];
    city: string[];
    page: string[];
    status: string[];
    receivedFrom: string;
    receivedTo: string;
  };
};
type SavedViewChip = {
  id: string;
  label: string;
  preset?: boolean;
  snapshot?: CrmViewSnapshot;
};
const CRM_SAVED_VIEWS_STORAGE_KEY = "agencia.crm.saved_views.v1";
const getSavedViewsStorageKey = () => {
  const userId = authStore.user?.id || "anon";
  return `${CRM_SAVED_VIEWS_STORAGE_KEY}.${userId}`;
};
const savedViewChips = ref<SavedViewChip[]>([
  { id: "default", label: "Padrão" },
  { id: "no-status", label: "Sem etapa", preset: true },
  { id: "open", label: "Abertas", preset: true },
  { id: "won", label: "Ganhas", preset: true },
  { id: "lost", label: "Perdidas", preset: true }
]);
const columnsMenuOpen = ref(false);
const mandatoryColumnKeys = new Set(["cliente", "acoes"]);
const columnDefaults = [
  { key: "cliente", label: "Cliente", visible: true },
  { key: "telefone", label: "Telefone", visible: true },
  { key: "status", label: "Etapa", visible: true },
  { key: "pagina", label: "Origem", visible: true },
  { key: "chegouEm", label: "Chegou em", visible: true },
  { key: "valor", label: "Valor", visible: true },
  { key: "ultima", label: "Sem interação", visible: true },
  { key: "acoes", label: "Ações", visible: true }
];
const crmColumnConfig = reactive(columnDefaults.map(col => ({ ...col })));
const draftColumnVisibility = reactive<Record<string, boolean>>({});
const draftColumnOrder = ref<string[]>([]);
const draggingColumnKey = ref<string | null>(null);
const dragOverColumnKey = ref<string | null>(null);
const draftOptionalColumns = computed(() =>
  draftColumnOrder.value.map(key => crmColumnConfig.find(col => col.key === key)).filter((col): col is { key: string; label: string; visible: boolean } => !!col)
);
const orderedOptionalColumns = computed(() => crmColumnConfig.filter(col => !mandatoryColumnKeys.has(col.key)));
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
const opportunityWhatsAppModalOpen = ref(false);
const opportunityWhatsAppSending = ref(false);
const opportunityWhatsAppSuccessModalOpen = ref(false);
const opportunityWhatsAppTargetPhone = ref("");
const opportunityWhatsAppTargetName = ref("");
const opportunityWhatsAppTargetContact = ref<LeadContact | null>(null);
const opportunityWhatsAppDraft = ref("");



const currentForm = ref<LeadForm | null>(null);



const feedback = ref<{ message: string; isError: boolean }>({ message: "", isError: false });
const collapsedGroupKeys = ref<string[]>([]);
const inlineValueContactId = ref<string | null>(null);
const inlineValueInput = ref("");



const getWhatsappTitle = (phone: string) => `${whatsappCopy.call} ${phone} ${whatsappCopy.suffix}`;



const getDeleteFormMessage = (title: string) => viewCopy.dialogs.deleteForm.replace("{title}", title);



const getDeleteLeadMessage = (name: string) => viewCopy.dialogs.deleteLead.replace("{name}", name);







const contactStatusSaving = reactive<Record<string, boolean>>({});



const contactDeleting = reactive<Record<string, boolean>>({});



const openStatusDropdown = ref<string | null>(null);
const statusDropdownDirection = ref<"up" | "down">("down");
const statusDropdownFloatingStyle = ref<CSSProperties>({});



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
  const outcome = contact?.close_outcome;
  return outcome === "won" || outcome === "lost" ? outcome : null;
};

const getOpportunityStatus = (contact: LeadContact | null | undefined): "open" | "won" | "lost" => getOpportunityOutcome(contact) || "open";

const isOpportunityClosed = (contact: LeadContact | null | undefined) => getOpportunityOutcome(contact) !== null;

const opportunityStatusLabel = (contact: LeadContact | null | undefined) => {
  const status = getOpportunityStatus(contact);
  if (status === "won") return viewCopy.filters.opportunity.won;
  if (status === "lost") return viewCopy.filters.opportunity.lost;
  return viewCopy.filters.opportunity.open;
};

const opportunityStatusChipClass = (contact: LeadContact | null | undefined) => {
  const status = getOpportunityStatus(contact);
  if (status === "won") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (status === "lost") return "border-rose-200 bg-rose-50 text-rose-700";
  return "border-sky-200 bg-sky-50 text-sky-700";
};







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



      { label: fallbackLabels.noStage, value: "null" },



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
    opportunityStatusSelections.value.length ||
    crmIdleSelections.value.length ||



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







  if (opportunityStatusFilter.value !== "all") {
    if (getOpportunityStatus(contact) !== opportunityStatusFilter.value) return false;
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

const crmPageOptions = computed(() =>
  Array.from(
    new Set(
      filteredContacts.value
        .map(contact => (contact.page_title || contact.form_name || "").trim())
        .filter(Boolean)
    )
  ).sort((a, b) => a.localeCompare(b))
);

const opportunityStatusOptions = [
  { label: "Abertas", value: "open" as const },
  { label: "Ganhas", value: "won" as const },
  { label: "Perdidas", value: "lost" as const }
];

const idleFilterOptions = [
  { label: "Hoje", value: "today" as const },
  { label: "Até 7 dias", value: "upto7" as const },
  { label: "8 a 14 dias", value: "8to14" as const },
  { label: "+15 dias", value: "gt15" as const }
];

const stageFilterOptions = computed(() => {
  const options = [{ label: fallbackLabels.noStage, value: "null" }];
  leadStatuses.value.forEach(status => options.push({ label: status.name, value: String(status.id) }));
  return options;
});

const idleDays = (contact: LeadContact) => {
  const backendDays = Number(contact.sem_interacao_days);
  if (Number.isFinite(backendDays) && backendDays >= 0) return Math.floor(backendDays);
  const lastInteraction = contact.updated_at || contact.created_at;
  const baseTime = lastInteraction ? new Date(lastInteraction).getTime() : Number.NaN;
  if (Number.isFinite(baseTime) && baseTime > 0) {
    const diff = Math.max(0, Date.now() - baseTime);
    return Math.floor(diff / 86400000);
  }
  return 0;
};

const idleBucketForDays = (days: number): "today" | "upto7" | "8to14" | "gt15" => {
  if (days <= 0) return "today";
  if (days <= 7) return "upto7";
  if (days <= 14) return "8to14";
  return "gt15";
};

const idleChipLabel = (contact: LeadContact) => {
  const days = idleDays(contact);
  return `${Math.max(0, days)} dias`;
};

const idleChipClass = (contact: LeadContact) => {
  const days = idleDays(contact);
  if (days <= 7) return "border-transparent bg-[rgba(61,204,95,.10)] text-[#1A7A35]";
  if (days <= 14) return "border-transparent bg-[rgba(245,158,11,.09)] text-[#92400E]";
  return "border-transparent bg-[rgba(239,68,68,.09)] text-[#991B1B]";
};

const idleDotClass = (contact: LeadContact) => {
  const days = idleDays(contact);
  if (days <= 7) return "bg-[#2EAD4C]";
  if (days <= 14) return "bg-[#F59E0B]";
  return "bg-[#EF4444]";
};

const shouldShowIdleChip = (contact: LeadContact) => {
  const outcome = getOpportunityOutcome(contact);
  return outcome !== "won" && outcome !== "lost";
};

const opportunityRowClass = (contact: LeadContact) => {
  const outcome = getOpportunityOutcome(contact);
  if (outcome === "won") return "is-won";
  if (outcome === "lost") return "is-lost";
  if (!contact.status_id) return "is-no-status";
  return "";
};

const contactInitials = (contact: LeadContact) => {
  const name = (contact.name || "?").trim();
  if (!name) return "?";
  const parts = name.split(" ").filter(Boolean);
  return (parts[0]?.[0] || "?").concat(parts.length > 1 ? parts[parts.length - 1][0] : "").toUpperCase();
};

const syncDraftFromColumns = () => {
  crmColumnConfig.forEach(col => {
    draftColumnVisibility[col.key] = !!col.visible;
  });
  draftColumnOrder.value = crmColumnConfig.filter(col => !mandatoryColumnKeys.has(col.key)).map(col => col.key);
};

const openColumnsSidebar = () => {
  syncDraftFromColumns();
  columnsMenuOpen.value = true;
};

const resetColumnsToDefault = () => {
  columnDefaults.forEach(col => {
    draftColumnVisibility[col.key] = mandatoryColumnKeys.has(col.key) ? true : !!col.visible;
  });
  draftColumnOrder.value = columnDefaults.filter(col => !mandatoryColumnKeys.has(col.key)).map(col => col.key);
  dragOverColumnKey.value = null;
  draggingColumnKey.value = null;
};

const reorderCrmColumns = (optionalOrder: string[]) => {
  const keySet = new Set(optionalOrder);
  const mergedOptionalOrder = [
    ...optionalOrder,
    ...crmColumnConfig.filter(col => !mandatoryColumnKeys.has(col.key) && !keySet.has(col.key)).map(col => col.key)
  ];
  const byKey = new Map(crmColumnConfig.map(col => [col.key, col]));
  const next = [
    byKey.get("cliente"),
    ...mergedOptionalOrder.map(key => byKey.get(key)),
    byKey.get("acoes")
  ].filter(Boolean);
  crmColumnConfig.splice(0, crmColumnConfig.length, ...next);
};

const applyColumnsSelection = () => {
  reorderCrmColumns(draftColumnOrder.value);
  crmColumnConfig.forEach(col => {
    if (mandatoryColumnKeys.has(col.key)) {
      col.visible = true;
      return;
    }
    col.visible = !!draftColumnVisibility[col.key];
  });
  dragOverColumnKey.value = null;
  draggingColumnKey.value = null;
  columnsMenuOpen.value = false;
};

const handleColumnDragStart = (columnKey: string) => {
  draggingColumnKey.value = columnKey;
  dragOverColumnKey.value = columnKey;
};

const handleColumnDragEnter = (targetKey: string) => {
  if (!draggingColumnKey.value || draggingColumnKey.value === targetKey) return;
  dragOverColumnKey.value = targetKey;
  const order = [...draftColumnOrder.value];
  const from = order.indexOf(draggingColumnKey.value);
  const to = order.indexOf(targetKey);
  if (from < 0 || to < 0) return;
  order.splice(from, 1);
  order.splice(to, 0, draggingColumnKey.value);
  draftColumnOrder.value = order;
};

const handleColumnDrop = (targetKey: string) => {
  handleColumnDragEnter(targetKey);
  dragOverColumnKey.value = null;
};

const handleColumnDragEnd = () => {
  draggingColumnKey.value = null;
  dragOverColumnKey.value = null;
};

const isMandatoryColumn = (key: string) => mandatoryColumnKeys.has(key);

const isColumnVisible = (key: string) => crmColumnConfig.find(col => col.key === key)?.visible ?? true;
const visibleCrmColumnsCount = computed(() => crmColumnConfig.filter(col => col.visible).length || 1);
const truncatedPageLabel = (contact: LeadContact) => {
  const raw = isManualOpportunity(contact) ? "Criada manualmente" : contact.page_title || contact.form_name || viewCopy.labels.dash;
  const text = String(raw || viewCopy.labels.dash).trim();
  if (text.length <= 25) return text;
  return `${text.slice(0, 25)}...`;
};

const truncatedContactName = (name?: string | null) => {
  const text = String(name || fallbackLabels.noName).trim();
  if (text.length <= 25) return text;
  return `${text.slice(0, 25)}...`;
};
const groupHeaderStyle = (groupKey: string) => {
  if (groupKey === "null") {
    return {
      backgroundColor: "transparent",
      color: "#334155",
      "--group-accent": "#cbd5e1",
      borderRadius: "8px",
      height: "28px"
    };
  }
  const color = statusColorMap.value[groupKey];
  if (!color) return {};
  return {
    backgroundColor: "transparent",
    color: "#334155",
    "--group-accent": color,
    borderRadius: "8px",
    height: "28px"
  };
};

const contactRowStyle = (contact: LeadContact): CSSProperties => ({
  borderLeft: "none"
});

const groupPillStyle = (groupKey: string): CSSProperties => {
  if (groupKey === "null") return { backgroundColor: "#f8fafc", borderColor: "#e2e8f0", color: "#475569" };
  const color = statusColorMap.value[groupKey];
  if (!color) return { backgroundColor: "#f8fafc", borderColor: "#e2e8f0", color: "#475569" };
  return {
    backgroundColor: `color-mix(in srgb, ${color} 10%, white)`,
    borderColor: `color-mix(in srgb, ${color} 30%, white)`,
    color
  };
};

const toggleToolbarFilter = (key: "stage" | "opportunityStatus" | "page" | "idle", event?: MouseEvent) => {
  if (openToolbarFilter.value === key) {
    openToolbarFilter.value = null;
    toolbarDropdownFloatingStyle.value = {};
    return;
  }
  const target = event?.currentTarget as HTMLElement | null;
  if (target) {
    const rect = target.getBoundingClientRect();
    const minWidth = Math.max(200, Math.round(rect.width));
    const estimatedHeight = key === "idle" ? 260 : 320;
    const gap = 8;
    const left = Math.min(
      Math.max(gap, rect.left),
      Math.max(gap, window.innerWidth - minWidth - gap)
    );
    const top = Math.min(window.innerHeight - estimatedHeight - gap, rect.bottom + 6);
    toolbarDropdownFloatingStyle.value = {
      position: "fixed",
      top: `${Math.max(gap, top)}px`,
      left: `${left}px`,
      minWidth: `${minWidth}px`,
      zIndex: "2550"
    };
  } else {
    toolbarDropdownFloatingStyle.value = {};
  }
  openToolbarFilter.value = key;
};

const toggleValueInArray = <T extends string>(list: T[], value: T) => (list.includes(value) ? list.filter(v => v !== value) : [...list, value]);

const toggleStageFilterOption = (value: string) => {
  listFilters.status = toggleValueInArray(listFilters.status, value);
};

const togglePageFilterOption = (value: string) => {
  listFilters.page = toggleValueInArray(listFilters.page, value);
};

const toggleOpportunityStatusSelection = (value: "open" | "won" | "lost") => {
  opportunityStatusSelections.value = toggleValueInArray(opportunityStatusSelections.value, value);
  opportunityStatusFilter.value = opportunityStatusSelections.value.length === 1 ? opportunityStatusSelections.value[0] : "all";
};

const toggleIdleFilterSelection = (value: "today" | "upto7" | "8to14" | "gt15") => {
  crmIdleSelections.value = toggleValueInArray(crmIdleSelections.value, value);
  crmIdleFilter.value = crmIdleSelections.value.length === 1 ? crmIdleSelections.value[0] : "all";
};

const selectAllStageFilters = () => {
  listFilters.status = stageFilterOptions.value.map(option => option.value);
};

const clearStageFilters = () => {
  listFilters.status = [];
};

const selectAllStatusFilters = () => {
  opportunityStatusSelections.value = opportunityStatusOptions.map(option => option.value);
  opportunityStatusFilter.value = "all";
};

const clearStatusFilters = () => {
  opportunityStatusSelections.value = [];
  opportunityStatusFilter.value = "all";
};

const selectAllPageFilters = () => {
  listFilters.page = [...crmPageOptions.value];
};

const clearPageFilters = () => {
  listFilters.page = [];
};

const selectAllIdleFilters = () => {
  crmIdleSelections.value = idleFilterOptions.map(option => option.value);
  crmIdleFilter.value = "all";
};

const clearIdleFilters = () => {
  crmIdleSelections.value = [];
  crmIdleFilter.value = "all";
};

const isGroupCollapsed = (groupKey: string) => collapsedGroupKeys.value.includes(groupKey);

const visibleGroupContacts = (group: { key: string; contacts: LeadContact[] }) =>
  isGroupCollapsed(group.key) ? [] : group.contacts;

const toggleGroupCollapse = (groupKey: string) => {
  closeStatusDropdown();
  collapsedGroupKeys.value = collapsedGroupKeys.value.includes(groupKey)
    ? collapsedGroupKeys.value.filter(key => key !== groupKey)
    : [...collapsedGroupKeys.value, groupKey];
};

const visibleOpportunityIds = computed(() =>
  groupedContactsForCrm.value.flatMap(group => visibleGroupContacts(group).map(contact => idKey(contact.id)))
);

const areAllVisibleOpportunitiesSelected = computed(() => {
  const visible = visibleOpportunityIds.value;
  if (!visible.length) return false;
  return visible.every(id => selectedOpportunityIds.value.includes(id));
});

const isOpportunitySelected = (contact: LeadContact) => selectedOpportunityIds.value.includes(idKey(contact.id));

const toggleOpportunitySelection = (contact: LeadContact) => {
  const key = idKey(contact.id);
  selectedOpportunityIds.value = selectedOpportunityIds.value.includes(key)
    ? selectedOpportunityIds.value.filter(id => id !== key)
    : [...selectedOpportunityIds.value, key];
};

const toggleAllVisibleOpportunities = () => {
  if (areAllVisibleOpportunitiesSelected.value) {
    const visibleSet = new Set(visibleOpportunityIds.value);
    selectedOpportunityIds.value = selectedOpportunityIds.value.filter(id => !visibleSet.has(id));
    return;
  }
  const merged = new Set([...selectedOpportunityIds.value, ...visibleOpportunityIds.value]);
  selectedOpportunityIds.value = Array.from(merged);
};

const groupedContactsForCrm = computed(() => {
  const search = crmSearchQuery.value.trim().toLowerCase();
  const byView = filteredContacts.value.filter(contact => {
    if (activeSavedView.value === "no-status" && contact.status_id) return false;
    if (activeSavedView.value === "open" && getOpportunityStatus(contact) !== "open") return false;
    if (activeSavedView.value === "won" && getOpportunityOutcome(contact) !== "won") return false;
    if (activeSavedView.value === "lost" && getOpportunityOutcome(contact) !== "lost") return false;
    if (search) {
      const hay = `${contact.name || ""} ${contact.email || ""} ${contact.phone || ""}`.toLowerCase();
      if (!hay.includes(search)) return false;
    }
    if (listFilters.page.length && !listFilters.page.includes((contact.page_title || contact.form_name || "").trim())) return false;
    const days = idleDays(contact);
    if (crmIdleSelections.value.length) {
      const idleBucket = idleBucketForDays(days);
      if (!crmIdleSelections.value.includes(idleBucket)) return false;
    }
    if (opportunityStatusSelections.value.length) {
      const status = getOpportunityStatus(contact);
      if (!opportunityStatusSelections.value.includes(status)) return false;
    }
    return true;
  });

  const sortedStatuses = [...leadStatuses.value].sort((a, b) => {
    const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
    const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
    return dateA - dateB;
  });

  const baseGroups = [
    { key: "null", label: fallbackLabels.noStage },
    ...sortedStatuses.map(status => ({ key: String(status.id), label: status.name }))
  ];

  const map = new Map<string, { key: string; label: string; contacts: LeadContact[]; totalValueCents: number }>();
  baseGroups.forEach(group => {
    map.set(group.key, { ...group, contacts: [], totalValueCents: 0 });
  });

  byView.forEach(contact => {
    const key = contact.status_id ? String(contact.status_id) : "null";
    const label = contact.status_name || fallbackLabels.noStage;
    if (!map.has(key)) map.set(key, { key, label, contacts: [], totalValueCents: 0 });
    const bucket = map.get(key)!;
    bucket.contacts.push(contact);
    bucket.totalValueCents += contact.estimated_value_cents || 0;
  });

  const orderMap = new Map(baseGroups.map((group, index) => [group.key, index]));
  return Array.from(map.values()).sort((a, b) => {
    const orderA = orderMap.get(a.key);
    const orderB = orderMap.get(b.key);
    if (orderA != null && orderB != null) return orderA - orderB;
    if (orderA != null) return -1;
    if (orderB != null) return 1;
    if (a.key === "null") return -1;
    if (b.key === "null") return 1;
    return a.label.localeCompare(b.label);
  });
});

const markOpportunityOutcome = async (contact: LeadContact, outcome: "won" | "lost") => {
  try {
    const currentOutcome = getOpportunityOutcome(contact);
    if (currentOutcome === outcome) {
      await leadStore.updateOpportunity(contact.id, { closeOutcome: null });
      await leadStore.fetchContacts(undefined, true);
      showFeedback("Status da oportunidade removido.");
      return;
    }
    await leadStore.finalizeOpportunity(contact.id, { outcome });
    await leadStore.fetchContacts(undefined, true);
    showFeedback(outcome === "won" ? "Oportunidade marcada como ganha." : "Oportunidade marcada como perdida.");
  } catch (err) {
    console.error(err);
    showFeedback("Não foi possível atualizar o resultado.", true);
  }
};

const applyBulkOutcome = async (outcome: "won" | "lost") => {
  if (!selectedOpportunityIds.value.length) return;
  try {
    await Promise.all(selectedOpportunityIds.value.map(id => leadStore.finalizeOpportunity(id, { outcome })));
    await leadStore.fetchContacts(undefined, true);
    selectedOpportunityIds.value = [];
    showFeedback(outcome === "won" ? "Oportunidades marcadas como ganhas." : "Oportunidades marcadas como perdidas.");
  } catch (err) {
    console.error(err);
    showFeedback("Não foi possível atualizar as oportunidades selecionadas.", true);
  }
};

const deleteSelectedOpportunities = async () => {
  if (!selectedOpportunityIds.value.length) return;
  if (!window.confirm(`Excluir ${selectedOpportunityIds.value.length} oportunidade(s)?`)) return;
  try {
    await Promise.all(selectedOpportunityIds.value.map(id => leadStore.deleteContact(id)));
    await leadStore.fetchContacts(undefined, true);
    selectedOpportunityIds.value = [];
    showFeedback("Oportunidades excluídas.");
  } catch (err) {
    console.error(err);
    showFeedback("Não foi possível excluir as oportunidades selecionadas.", true);
  }
};

const applyBulkMoveStage = async () => {
  if (!selectedOpportunityIds.value.length) return;
  if (!bulkTargetStatusId.value) {
    showFeedback("Selecione uma etapa para mover.", true);
    return;
  }
  const targetStatus = bulkTargetStatusId.value === "null" ? null : bulkTargetStatusId.value;
  try {
    await Promise.all(selectedOpportunityIds.value.map(id => leadStore.setContactStatus(id, targetStatus)));
    await leadStore.fetchContacts(undefined, true);
    selectedOpportunityIds.value = [];
    bulkTargetStatusId.value = "";
    showFeedback("Oportunidades movidas de etapa.");
  } catch (err) {
    console.error(err);
    showFeedback("Não foi possível mover as oportunidades selecionadas.", true);
  }
};

const selectBulkStage = async (statusId: string) => {
  bulkTargetStatusId.value = statusId;
  bulkStageMenuOpen.value = false;
  await applyBulkMoveStage();
};

const clearBulkSelection = () => {
  selectedOpportunityIds.value = [];
  bulkTargetStatusId.value = "";
  bulkStageMenuOpen.value = false;
};







const kanbanColumns = computed(() => {



  const sortedStatuses = [...leadStatuses.value].sort((a, b) => {



    const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;



    const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;



    return dateA - dateB;



  });







  const baseOptions = [



    { id: "null", name: fallbackLabels.noStage },

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

const reaisInputToCents = (value: string) => {
  const raw = String(value || "").trim();
  if (!raw) return null;
  const normalized = raw.replace(/\s+/g, "").replace(/^R\$\s?/i, "");
  if (!normalized) return null;

  // pt-BR: "." thousands, "," decimals. If separator is present, parse decimal.
  if (normalized.includes(",") || normalized.includes(".")) {
    const canonical = normalized.replace(/\./g, "").replace(",", ".");
    const amount = Number(canonical);
    if (!Number.isFinite(amount) || amount <= 0) return null;
    return Math.round(amount * 100);
  }

  // No separator: treat as reais directly.
  const reais = Number(normalized.replace(/\D/g, ""));
  if (!Number.isFinite(reais) || reais <= 0) return null;
  return Math.round(reais * 100);
};

const beginInlineValueEdit = (contact: LeadContact) => {
  inlineValueContactId.value = idKey(contact.id);
  inlineValueInput.value = "";
};

const saveInlineValue = async (contact: LeadContact) => {
  const cents = reaisInputToCents(inlineValueInput.value);
  if (!cents || cents <= 0) {
    inlineValueContactId.value = null;
    inlineValueInput.value = "";
    return;
  }
  try {
    await leadStore.updateOpportunity(contact.id, { estimatedValueCents: cents });
    showFeedback("Valor atualizado.");
  } catch (err) {
    console.error(err);
    showFeedback("Não foi possível atualizar o valor.", true);
  } finally {
    inlineValueContactId.value = null;
    inlineValueInput.value = "";
  }
};

const openContactOrigin = (contact: LeadContact) => {
  if (isManualOpportunity(contact)) return;
  const pageUrl = String(contact.page_url || "").trim();
  if (pageUrl) {
    window.open(pageUrl, "_blank", "noopener,noreferrer");
    return;
  }
  void router.push("/admin/pages");
};

const handleCreateManualOpportunity = async () => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  if (!selectedManualOpportunityClient.value && !manualOpportunityForm.name?.trim()) return;
  manualOpportunitySaving.value = true;
  try {
    await leadStore.createManualOpportunity({
      clientId: selectedManualOpportunityClient.value?.id || null,
      name: selectedManualOpportunityClient.value?.name || manualOpportunityForm.name.trim(),
      opportunityName: manualOpportunityForm.opportunityName?.trim() || null,
      cpf: selectedManualOpportunityClient.value ? null : manualOpportunityForm.cpf?.trim() || null,
      phone: selectedManualOpportunityClient.value ? null : manualOpportunityForm.phone?.trim() || null,
      email: selectedManualOpportunityClient.value ? null : manualOpportunityForm.email?.trim() || null,
      city: selectedManualOpportunityClient.value ? null : manualOpportunityForm.city?.trim() || null,
      birthdate: selectedManualOpportunityClient.value ? null : manualOpportunityForm.birthdate || null,
      estimatedValueCents: reaisInputToCents(manualOpportunityForm.estimatedValue),
      statusId: manualOpportunityForm.statusId ? Number(manualOpportunityForm.statusId) : null,
      internalNotes: manualOpportunityForm.internalNotes?.trim() || null,
      expectedCloseDate: manualOpportunityForm.expectedCloseDate || null
    });
    closeManualOpportunityModal();
    showFeedback("Oportunidade criada com sucesso.");
  } catch (err) {
    console.error(err);
    showFeedback("Não foi possível criar a oportunidade.", true);
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













const buildWhatsAppFallbackUrl = (contact: LeadContact | null | undefined, digits: string) => {
  if (isManualOpportunity(contact)) return `https://wa.me/${digits}`;
  const pageLabel = contact?.page_title || contact?.page_slug || fallbackLabels.noPage;
  const template =
    typeof whatsappCopy.formMessage === "string" && whatsappCopy.formMessage.includes("{page}")
      ? whatsappCopy.formMessage
      : "Olá! Recebemos seu interesse na página {page}.";
  const message = template.replace("{page}", pageLabel);
  return `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
};

const handleBuilderInvalid = (message: string) => {
  showFeedback(message || "Não foi possível salvar o formulário.", true);
};

const closeOpportunityWhatsAppModal = () => {
  opportunityWhatsAppModalOpen.value = false;
  opportunityWhatsAppSending.value = false;
  opportunityWhatsAppTargetPhone.value = "";
  opportunityWhatsAppTargetName.value = "";
  opportunityWhatsAppTargetContact.value = null;
  opportunityWhatsAppDraft.value = "";
};

const closeOpportunityWhatsAppSuccessModal = () => {
  opportunityWhatsAppSuccessModalOpen.value = false;
};

const openOpportunityWhatsAppWeb = () => {
  const digits = String(opportunityWhatsAppTargetPhone.value || "").replace(/\D+/g, "");
  if (!digits) {
    showFeedback("Telefone inválido para WhatsApp.", true);
    return;
  }
  const url = `https://web.whatsapp.com/send?phone=${encodeURIComponent(digits)}`;
  openFallbackWhatsApp(url);
};

const sendOpportunityWhatsAppMessage = async () => {
  const agencyId = Number(agencyStore.currentAgencyId || 0);
  const contact = opportunityWhatsAppTargetContact.value;
  const digits = opportunityWhatsAppTargetPhone.value;
  const text = opportunityWhatsAppDraft.value.trim();
  if (!agencyId || !contact || !digits || !text || opportunityWhatsAppSending.value) return;
  opportunityWhatsAppSending.value = true;
  try {
    const conversation = await ensureWhatsAppConversation(agencyId, {
      remotePhone: digits,
      remoteName: opportunityWhatsAppTargetName.value || contact.name || undefined,
      clientId: contact.client_id ? Number(contact.client_id) : undefined
    });
    await sendWhatsAppText(conversation.id, agencyId, text);
    showFeedback("Mensagem enviada com sucesso.");
    closeOpportunityWhatsAppModal();
    opportunityWhatsAppSuccessModalOpen.value = true;
  } catch (err) {
    console.error(err);
    showFeedback("Não foi possível enviar a mensagem.", true);
  } finally {
    opportunityWhatsAppSending.value = false;
  }
};

const openFallbackWhatsApp = (url: string) => {
  if (!url) return;
  const popup = window.open(url, "_blank", "noopener,noreferrer");
  if (!popup) {
    showFeedback("Seu navegador bloqueou a nova aba. Permita pop-ups para este site.", true);
  }
};

const isWhatsAppConnectedStatus = (value: unknown) => {
  const status = String(value || "").trim().toLowerCase();
  return ["connected", "open", "online"].includes(status);
};

const hasConnectedWhatsApp = async (agencyId: number) => {
  try {
    const { data } = await api.get("/whatsapp/connections", { params: { agencyId } });
    const items = Array.isArray(data)
      ? data
      : Array.isArray((data as any)?.items)
        ? (data as any).items
        : [];

    const connected = items.some((item: any) =>
      isWhatsAppConnectedStatus(item?.status) ||
      isWhatsAppConnectedStatus(item?.connectionStatus) ||
      isWhatsAppConnectedStatus(item?.state) ||
      item?.connected === true
    );
    console.debug("[LeadsView] whatsapp connections", { agencyId, items, connected });
    return connected;
  } catch {
    return false;
  }
};

const openWhatsapp = async (contact: LeadContact | null | undefined) => {
  const digits = normalizeWhatsappDigits(contact?.phone);
  if (!digits) {
    showFeedback("Telefone inválido para WhatsApp.", true);
    return;
  }

  const fallbackUrl = buildWhatsAppFallbackUrl(contact, digits);
  const agencyId = Number(agencyStore.currentAgencyId || 0);
  if (!agencyId) {
    openFallbackWhatsApp(fallbackUrl);
    return;
  }

  try {
    const pageLabel = contact?.page_title || contact?.page_slug || fallbackLabels.noPage;
    const connected = await hasConnectedWhatsApp(agencyId);
    if (!connected) {
      openFallbackWhatsApp(fallbackUrl);
      return;
    }

    const defaultTemplate =
      typeof whatsappCopy.formMessage === "string" && whatsappCopy.formMessage.includes("{page}")
        ? whatsappCopy.formMessage
        : "Olá! Recebemos seu interesse na página {page}.";

    opportunityWhatsAppTargetContact.value = contact || null;
    opportunityWhatsAppTargetPhone.value = digits;
    opportunityWhatsAppTargetName.value = (contact?.name || "").trim();
    opportunityWhatsAppDraft.value = isManualOpportunity(contact)
      ? `Olá ${opportunityWhatsAppTargetName.value || ""}, tudo bem?`
      : defaultTemplate.replace("{page}", pageLabel);
    opportunityWhatsAppModalOpen.value = true;
  } catch (error) {
    console.error(error);
    openFallbackWhatsApp(fallbackUrl);
  }
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



  if (!color) {
    return {
      backgroundColor: "#f1f5f9",
      borderColor: "#e2e8f0",
      color: "#334155"
    };
  }



  return {



    backgroundColor: `color-mix(in srgb, ${color} 12%, white)`,



    borderColor: `color-mix(in srgb, ${color} 35%, white)`,



    color



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



    backgroundColor: `color-mix(in srgb, ${originalColor} 10%, white)`,



    borderColor: `color-mix(in srgb, ${originalColor} 24%, white)`,



    color: originalColor



  };



};







const statusOptionStyle = (status: LeadStatus): CSSProperties => {



  const color = normalizeStatusColor(status.color);



  if (!color) {
    return {
      backgroundColor: "#f1f5f9",
      borderColor: "#e2e8f0",
      color: "#334155"
    };
  }



  return {



    backgroundColor: `color-mix(in srgb, ${color} 12%, white)`,



    borderColor: `color-mix(in srgb, ${color} 35%, white)`,



    color



  };



};

const statusOptionDefaultStyle: CSSProperties = {
  backgroundColor: "#eef2f7",
  borderColor: "#d8e0ea",
  color: "#334155"
};

const dropdownStatusContact = computed(() => {
  if (!openStatusDropdown.value) return null;
  return contacts.value.find(contact => idKey(contact.id) === openStatusDropdown.value) || null;
});







const closeStatusDropdown = () => {
  openStatusDropdown.value = null;
  statusDropdownFloatingStyle.value = {};
};

const closeToolbarDropdown = () => {
  openToolbarFilter.value = null;
  toolbarDropdownFloatingStyle.value = {};
};







const toggleStatusDropdown = (contact: LeadContact, event?: MouseEvent) => {



  const key = idKey(contact.id);


  if (openStatusDropdown.value === key) {
    openStatusDropdown.value = null;
    return;
  }
  const target = event?.currentTarget as HTMLElement | null;
  if (target) {
    const rect = target.getBoundingClientRect();
    const estimatedMenuHeight = Math.min((leadStatuses.value.length + 1) * 38 + 12, 248);
    const menuMinWidth = Math.max(180, Math.round(rect.width));
    const gap = 12;
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;
    statusDropdownDirection.value =
      spaceBelow < estimatedMenuHeight + gap && spaceAbove > spaceBelow ? "up" : "down";
    const top = statusDropdownDirection.value === "up"
      ? Math.max(gap, rect.top - estimatedMenuHeight - gap)
      : Math.min(window.innerHeight - estimatedMenuHeight - gap, rect.bottom + gap);
    const left = Math.min(
      Math.max(gap, rect.left),
      Math.max(gap, window.innerWidth - menuMinWidth - gap)
    );
    statusDropdownFloatingStyle.value = {
      position: "fixed",
      top: `${top}px`,
      left: `${left}px`,
      minWidth: `${menuMinWidth}px`,
      zIndex: "2600"
    };
  } else {
    statusDropdownDirection.value = "down";
    statusDropdownFloatingStyle.value = {};
  }
  openStatusDropdown.value = key;



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
  if (target.closest(".status-dropdown-portal")) return;
  if (target.closest(".toolbar-ms-dropdown-portal")) return;
  if (target.closest(".columns-sidebar")) return;
  if (target.closest(".bulk-stage-wrap")) return;
  if (target.closest(".crm-toolbar")) {
    bulkStageMenuOpen.value = false;
    return;
  }
  closeStatusDropdown();
  columnsMenuOpen.value = false;
  closeToolbarDropdown();
  bulkStageMenuOpen.value = false;



};







const handleGlobalKeydown = (event: KeyboardEvent) => {



  if (event.key === "Escape") {
    closeStatusDropdown();
    columnsMenuOpen.value = false;
    closeToolbarDropdown();
    bulkStageMenuOpen.value = false;
  }



};

const handleViewportInteraction = () => {
  if (openStatusDropdown.value) closeStatusDropdown();
  if (openToolbarFilter.value) closeToolbarDropdown();
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



  opportunityStatusFilter.value = "all";
  opportunityStatusSelections.value = [];
  crmSearchQuery.value = "";
  crmPageFilter.value = "all";
  crmIdleFilter.value = "all";
  crmIdleSelections.value = [];
  activeSavedView.value = "default";
  selectedOpportunityIds.value = [];
  listFilters.receivedFrom = "";



  listFilters.receivedTo = "";



  closeFilterPopover();
  closeToolbarDropdown();



};

const captureCurrentViewSnapshot = (): CrmViewSnapshot => ({
  search: crmSearchQuery.value,
  status: opportunityStatusFilter.value,
  statusSelections: [...opportunityStatusSelections.value],
  page: crmPageFilter.value,
  pageSelections: [...listFilters.page],
  idle: crmIdleFilter.value,
  idleSelections: [...crmIdleSelections.value],
  columns: Object.fromEntries(crmColumnConfig.map(col => [col.key, !!col.visible])),
  columnOrder: crmColumnConfig.filter(col => !mandatoryColumnKeys.has(col.key)).map(col => col.key),
  filters: {
    name: [...listFilters.name],
    form: [...listFilters.form],
    phone: [...listFilters.phone],
    email: [...listFilters.email],
    city: [...listFilters.city],
    page: [...listFilters.page],
    status: [...listFilters.status],
    receivedFrom: listFilters.receivedFrom,
    receivedTo: listFilters.receivedTo
  }
});

const resetViewFilterState = () => {
  listFilters.name = [];
  listFilters.form = [];
  listFilters.phone = [];
  listFilters.email = [];
  listFilters.city = [];
  listFilters.page = [];
  listFilters.status = [];
  opportunityStatusFilter.value = "all";
  opportunityStatusSelections.value = [];
  crmSearchQuery.value = "";
  crmPageFilter.value = "all";
  crmIdleFilter.value = "all";
  crmIdleSelections.value = [];
  listFilters.receivedFrom = "";
  listFilters.receivedTo = "";
  closeFilterPopover();
  closeToolbarDropdown();
};

const formatDateOnly = (value?: string) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(date);
};

const formatDateDayMonthTime = (value?: string) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const formatted = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
  return formatted.replace(", ", "   ");
};

const applyViewSnapshot = (snapshot?: CrmViewSnapshot) => {
  resetViewFilterState();
  if (!snapshot) return;
  if (snapshot.columnOrder?.length) {
    reorderCrmColumns(snapshot.columnOrder);
  }
  crmSearchQuery.value = snapshot.search ?? "";
  opportunityStatusFilter.value = snapshot.status ?? "all";
  opportunityStatusSelections.value = [...(snapshot.statusSelections || (snapshot.status && snapshot.status !== "all" ? [snapshot.status] : []))];
  crmPageFilter.value = snapshot.page ?? "all";
  listFilters.page = [...(snapshot.pageSelections || (snapshot.page && snapshot.page !== "all" ? [snapshot.page] : []))];
  crmIdleFilter.value = snapshot.idle ?? "all";
  crmIdleSelections.value = [...(snapshot.idleSelections || (snapshot.idle && snapshot.idle !== "all" ? [snapshot.idle] : []))];
  crmColumnConfig.forEach(col => {
    if (snapshot.columns && Object.prototype.hasOwnProperty.call(snapshot.columns, col.key)) {
      col.visible = !!snapshot.columns[col.key];
    }
  });
  if (snapshot.filters) {
    listFilters.name = [...(snapshot.filters.name || [])];
    listFilters.form = [...(snapshot.filters.form || [])];
    listFilters.phone = [...(snapshot.filters.phone || [])];
    listFilters.email = [...(snapshot.filters.email || [])];
    listFilters.city = [...(snapshot.filters.city || [])];
    if (!snapshot.pageSelections?.length) listFilters.page = [...(snapshot.filters.page || [])];
    listFilters.status = [...(snapshot.filters.status || [])];
    listFilters.receivedFrom = snapshot.filters.receivedFrom || "";
    listFilters.receivedTo = snapshot.filters.receivedTo || "";
  }
};

type RemoteCrmViewPreferences = {
  defaultSnapshot?: CrmViewSnapshot | null;
  customViews?: SavedViewChip[];
};

const hydrateSavedViews = (payload?: RemoteCrmViewPreferences | null) => {
  const parsedCustom = payload?.customViews || [];
  const defaultSnapshot = payload?.defaultSnapshot || undefined;
  const customViews = Array.isArray(parsedCustom)
    ? parsedCustom.filter(view => view && typeof view.id === "string" && typeof view.label === "string")
    : [];
  savedViewChips.value = [
    { id: "default", label: "Padrão", snapshot: defaultSnapshot || undefined },
    { id: "no-status", label: "Sem etapa", preset: true },
    { id: "open", label: "Abertas", preset: true },
    { id: "won", label: "Ganhas", preset: true },
    { id: "lost", label: "Perdidas", preset: true },
    ...customViews
  ];
  activeSavedView.value = "default";
  if (defaultSnapshot) applyViewSnapshot(defaultSnapshot);
};

const buildSavedViewsPayload = (): RemoteCrmViewPreferences => {
  const customViews = savedViewChips.value.filter(view => !view.preset && view.id !== "default");
  const defaultSnapshot = savedViewChips.value.find(view => view.id === "default")?.snapshot || null;
  return { customViews, defaultSnapshot };
};

const syncSavedViewsToServer = async () => {
  try {
    await api.put("/auth/me/crm-view-preferences", buildSavedViewsPayload());
  } catch (err) {
    console.error(err);
  }
};

const persistSavedViews = () => {
  try {
    localStorage.setItem(getSavedViewsStorageKey(), JSON.stringify(buildSavedViewsPayload()));
  } catch (err) {
    console.error(err);
  }
  void syncSavedViewsToServer();
};

const loadSavedViews = async () => {
  try {
    const { data } = await api.get<RemoteCrmViewPreferences>("/auth/me/crm-view-preferences");
    if (data && (data.defaultSnapshot || (Array.isArray(data.customViews) && data.customViews.length))) {
      hydrateSavedViews(data);
      try {
        loadedSavedViewsKey.value = getSavedViewsStorageKey();
        localStorage.setItem(getSavedViewsStorageKey(), JSON.stringify(data));
      } catch (err) {
        console.error(err);
      }
      return;
    }
  } catch (err) {
    console.error(err);
  }

  try {
    const storageKey = getSavedViewsStorageKey();
    loadedSavedViewsKey.value = storageKey;
    const raw = localStorage.getItem(storageKey);
    if (!raw) return;
    const parsed = JSON.parse(raw) as { customViews?: SavedViewChip[]; defaultSnapshot?: CrmViewSnapshot } | SavedViewChip[];
    if (Array.isArray(parsed)) {
      const customViews = parsed.filter(view => view && typeof view.id === "string" && typeof view.label === "string");
      hydrateSavedViews({ customViews, defaultSnapshot: null });
    } else {
      hydrateSavedViews({ customViews: parsed.customViews || [], defaultSnapshot: parsed.defaultSnapshot || null });
    }
    await syncSavedViewsToServer();
  } catch (err) {
    console.error(err);
  }
};

const selectSavedView = (viewId: string) => {
  activeSavedView.value = viewId;
  const selected = savedViewChips.value.find(view => view.id === viewId);
  applyViewSnapshot(selected?.snapshot);
};

const createSavedView = () => {
  const name = window.prompt("Nome da nova view:");
  if (!name || !name.trim()) return;
  const label = name.trim();
  const baseId = `custom-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "view"}`;
  let id = baseId;
  let idx = 2;
  while (savedViewChips.value.some(view => view.id === id)) {
    id = `${baseId}-${idx}`;
    idx += 1;
  }
  const newView: SavedViewChip = {
    id,
    label,
    snapshot: captureCurrentViewSnapshot()
  };
  savedViewChips.value.push(newView);
  activeSavedView.value = id;
  persistSavedViews();
  showFeedback("Nova visualização criada.");
};

const saveCurrentView = () => {
  const snapshot = captureCurrentViewSnapshot();
  const defaultView = savedViewChips.value.find(view => view.id === "default");
  if (defaultView) defaultView.snapshot = snapshot;
  persistSavedViews();
  activeSavedView.value = "default";
  showFeedback("Visualização padrão atualizada.");
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
  window.addEventListener("resize", handleViewportInteraction);
  window.addEventListener("scroll", handleViewportInteraction, true);



  await bootstrapLeads();
  const expectedStorageKey = getSavedViewsStorageKey();
  if (loadedSavedViewsKey.value !== expectedStorageKey) {
    await loadSavedViews();
  }
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
  window.removeEventListener("resize", handleViewportInteraction);
  window.removeEventListener("scroll", handleViewportInteraction, true);



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

watch(visibleOpportunityIds, ids => {
  const allowed = new Set(ids);
  selectedOpportunityIds.value = selectedOpportunityIds.value.filter(id => allowed.has(id));
});
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

.opportunities-filter-bar {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.opportunities-filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.opportunities-filter-row--primary {
  flex-wrap: wrap;
}

.opportunities-filter-row--search .toolbar-search {
  width: 100%;
  min-width: 0;
}

.opportunities-filter-bar--desktop {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.opportunities-filter-bar--desktop .opportunities-filter-row--primary {
  flex-wrap: nowrap;
}

.opportunities-filter-bar--desktop .opportunities-filter-label {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #6f846f;
  margin-right: 2px;
}

.opportunities-filter-bar--desktop .toolbar-right-actions {
  margin-left: auto;
}

@media (min-width: 769px) {
  .crm-toolbar {
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-top: 6px !important;
  }
}

.mobile-create-btn {
  display: none;
}

.toolbar-ms {
  position: relative;
}

.toolbar-ms-btn {
  height: 34px;
  border: 1px solid #e4e9e4;
  background: #fff;
  color: #4a5e4a;
  border-radius: 9px;
  font-size: 12px;
  font-weight: 700;
  padding: 0 11px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.toolbar-ms-btn.open,
.toolbar-ms-btn:hover {
  border-color: #cdd8cd;
}

.toolbar-ms-count {
  background: #3dcc5f;
  color: #0f1f14;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
}

.toolbar-ms-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 200px;
  background: #fff;
  border: 1px solid #e4e9e4;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  z-index: 80;
  padding: 6px;
}

.toolbar-ms-dropdown-portal {
  position: fixed;
  z-index: 2550;
}

.toolbar-ms-actions {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 6px 4px;
  border-top: 1px solid #edf1ed;
  margin-top: 4px;
}

.toolbar-ms-actions button {
  border: none;
  background: transparent;
  color: #6f846f;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  padding: 2px 0;
}

.toolbar-ms-subtitle {
  margin: 6px 8px 4px;
  font-size: 11px;
  font-weight: 700;
  color: #8aa08a;
}

.toolbar-ms-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  font-size: 12px;
  color: #4a5e4a;
  border-radius: 8px;
  cursor: pointer;
}

.toolbar-ms-option:hover {
  background: #f5f7f5;
}

.toolbar-ms-option input {
  width: 14px;
  height: 14px;
  accent-color: #3dcc5f;
}

.toolbar-search {
  border: 1px solid #e4e9e4;
  border-radius: 9px;
  background: #fff;
  height: 34px;
  min-width: 220px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  gap: 6px;
}

.toolbar-search-icon {
  width: 14px;
  height: 14px;
  color: #9aa89a;
  flex-shrink: 0;
}

.toolbar-search input {
  border: none;
  outline: none;
  width: 100%;
  font-size: 14px;
  color: #111a14;
  background: transparent;
}

.phone-link:hover,
.origin-link:hover {
  text-decoration: underline;
  text-decoration-color: currentColor;
  text-underline-offset: 2px;
}

.toolbar-spacer {
  flex: 1;
}

.toolbar-right-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.opportunities-filter-row--secondary {
  justify-content: space-between;
}

.toolbar-ghost-btn {
  height: 34px;
  border: 1px solid #e4e9e4;
  background: #fff;
  color: #1f3a27;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.toolbar-ghost-btn--square {
  border-radius: 10px;
}

.toolbar-ghost-btn:hover {
  border-color: #cdd8cd;
}

.columns-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.2);
  z-index: 210;
}

.columns-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 300px;
  max-width: 90vw;
  height: 100vh;
  background: #f3f5f3;
  border-left: 1px solid #e4e9e4;
  box-shadow: -8px 0 24px rgba(0, 0, 0, 0.12);
  z-index: 211;
  display: flex;
  flex-direction: column;
}

.columns-sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #d7ddd7;
  background: #f3f5f3;
}

.columns-sidebar-title {
  font-size: 14px;
  font-weight: 800;
  color: #111a14;
}

.columns-sidebar-close {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid #e4e9e4;
  background: #e9efea;
  color: #4a5e4a;
  cursor: pointer;
}

.columns-sidebar-body {
  padding: 10px 14px;
  overflow-y: auto;
}

.columns-sidebar-section {
  margin: 12px 4px 8px;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-weight: 800;
  color: #8a9e8a;
}

.columns-sidebar-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 6px;
  border-radius: 8px;
  color: #586b58;
  font-size: 13px;
  font-weight: 700;
  cursor: grab;
  user-select: none;
}

.columns-sidebar-item:hover {
  background: #ebf0eb;
}

.columns-drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #90a18f;
  margin-right: 2px;
  flex-shrink: 0;
}

.columns-sidebar-item.is-dragging {
  opacity: 0.65;
}

.columns-sidebar-item.is-drag-over {
  background: #dff3e4;
  outline: 1px solid #87d29b;
}

.columns-sidebar-item input {
  accent-color: #3dcc5f;
}

.columns-sidebar-item input:disabled {
  accent-color: #bfc9bf;
}

.columns-drag-tip {
  margin: 10px 6px 0;
  color: #7f937f;
  font-size: 12px;
  font-weight: 600;
}

.columns-fixed-tag {
  margin-left: auto;
  font-size: 12px;
  color: #8a9e8a;
  font-weight: 700;
}

.columns-sidebar-foot {
  padding: 12px 14px 14px;
  border-top: 1px solid #d7ddd7;
  background: #f3f5f3;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.columns-foot-btn {
  height: 40px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid #d3dbd3;
}

.columns-foot-btn--ghost {
  background: #f3f5f3;
  color: #1f3a27;
}

.columns-foot-btn--apply {
  background: #43c45b;
  color: #0f1f14;
  border-color: #43c45b;
}

.opps-table-shell {
  background: #fff;
  border: 1px solid #e4e9e4;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(15, 31, 20, 0.04);
  overflow: hidden;
}

.opps-table thead tr {
  background: #f5f7f5;
  border-bottom: 1.5px solid #e4e9e4;
}

.opps-table {
  border-collapse: collapse;
  border-spacing: 0;
}

.opps-table thead th {
  color: #8a9e8a;
}

.opps-group-row td {
  border-top: 1.5px solid #e4e9e4;
  background: #fff;
  position: relative;
}

.opps-group-row td::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--group-accent, transparent);
}

.opps-group-meta {
  color: #8a9e8a;
  margin-left: 10px;
}

.opps-group-toggle-btn {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  border: 1px solid transparent !important;
  border-radius: 8px;
  background-color: transparent !important;
  color: #7b8794;
  vertical-align: middle;
  box-shadow: none;
}

.opps-group-toggle-btn:hover {
  background-color: transparent !important;
}

.opps-group-toggle-btn.collapsed svg {
  transform: rotate(-90deg);
}

.opps-data-row {
  border-bottom: 1px solid #e4e9e4;
  background: #fafbfa;
  color: #111a14;
}

.opps-data-row:hover {
  background: #eef3ee;
}

.opps-data-row.is-won {
  background: rgba(61, 204, 95, 0.08);
}

.opps-data-row.is-won:hover {
  background: rgba(61, 204, 95, 0.12);
}

.opps-data-row.is-lost {
  background: rgba(239, 68, 68, 0.07);
}

.opps-data-row.is-lost:hover {
  background: rgba(239, 68, 68, 0.11);
}

.opps-data-row.is-no-status {
}

.opps-data-row > td {
  background: inherit;
}


.mobile-opps-list {
  border: 1px solid #e4e9e4;
  border-radius: 6px;
  overflow: hidden;
}

.mobile-group-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  min-height: 34px;
  background: #fafcfb;
  border-top: 1px solid #edf2ed;
  border-bottom: 1px solid #e9efea;
  position: relative;
}

.mobile-group-strip::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--group-accent, transparent);
}

.mobile-group-title {
  font-size: 12px;
  font-weight: 700;
  color: #516651;
}

.mobile-group-pill {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border-radius: 999px;
  border: 1px solid transparent;
  padding: 3px 9px;
}

.mobile-group-meta {
  font-size: 11px;
  color: #8a9e8a;
  margin-left: auto;
}

.mobile-opps-card {
  border-bottom: 1px solid #e4e9e4;
  border-radius: 0;
  padding: 3px 10px 0;
  background: #fff;
}

.mobile-opps-list > .mobile-group-strip:first-child {
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

.mobile-opps-list > article.mobile-opps-card:last-of-type {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.mobile-opps-card.is-won {
  background: rgba(61, 204, 95, 0.08);
}

.mobile-opps-card.is-lost {
  background: rgba(239, 68, 68, 0.07);
}

.mobile-card-top-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 4px;
  margin-top: 4px;
}

.mobile-card-top {
  min-width: 58px;
  font-size: 10px;
  color: #8a9e8a;
  line-height: 1.1;
}

.mobile-card-origin {
  flex: 1;
  min-width: 0;
  font-size: 10px;
  color: #8a9e8a;
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-card-name {
  margin-top: 0;
  font-size: 14px;
  font-weight: 700;
  color: #0f1f14;
  line-height: 1.1;
}

.mobile-card-header {
  margin-top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.mobile-card-phone {
  margin-top: 0;
  margin-bottom: 0;
  font-size: 10px;
}

.mobile-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 1px;
}

.mobile-card-layout {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.mobile-card-main {
  min-width: 0;
  flex: 1;
}

.mobile-card-actions--row {
  flex-direction: row;
  align-items: center;
  justify-content: center;
  align-self: center;
  gap: 6px;
}

.opportunity-bulk-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  transform: translateY(100%);
  transition: transform 0.2s ease;
  z-index: 120;
  background: linear-gradient(180deg, #041a13 0%, #081e16 100%);
  color: #fff;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.opportunity-bulk-bar.visible {
  transform: translateY(0);
}

.bulk-count {
  font-size: 13px;
  font-weight: 700;
}

.bulk-spacer {
  flex: 1;
}

.bulk-btn {
  cursor: pointer;
  border: none;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 700;
  padding: 9px 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  white-space: nowrap;
}

.bulk-btn svg {
  flex-shrink: 0;
}

.bulk-stage-btn svg:last-child {
  margin-left: 2px;
}

.bulk-won {
  background: #3dcc5f;
  color: #0f1f14;
}

.bulk-lost,
.bulk-del {
  background: rgba(239, 68, 68, 0.1);
  color: #ff5b5b;
  border: 1px solid rgba(239, 68, 68, 0.35);
}

.action-icon-btn {
  width: 24px;
  height: 24px;
  border: 1px solid transparent;
  border-radius: 7px;
  background: transparent;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: color .15s ease, background-color .15s ease;
}

.action-icon-btn:hover {
  color: #334155;
}

.action-muted {
  color: #9aa8b8;
}

.action-muted:hover {
  color: #6b7f95;
}

.action-like {
  color: #7fb79b;
}

.action-like.is-selected {
  background: #dcfce7;
  border-color: transparent;
  color: #0f9f5c;
}

.action-dislike {
  color: #d39ca8;
}

.action-dislike.is-selected {
  background: #ffe4e6;
  border-color: transparent;
  color: #e11d48;
}

.bulk-stage-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.bulk-stage-btn {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.bulk-stage-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  max-height: 260px;
  overflow-y: auto;
  border: 1px solid #284138;
  border-radius: 12px;
  background: #0e241b;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35);
  padding: 6px;
  z-index: 20;
}

.bulk-stage-opt {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  color: #e6f0eb;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.bulk-stage-opt:hover {
  background: rgba(61, 204, 95, 0.14);
}

.bulk-cancel {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.bulk-stage-btn:hover,
.bulk-cancel:hover {
  background: rgba(255, 255, 255, 0.14);
}

@media (min-width: 1024px) {
  .opportunity-bulk-bar {
    left: 210px;
  }
}

@media (max-width: 920px) {
  .forms-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .leads-page {
    gap: 8px !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
  }

  .leads-page > .shrink-0 {
    margin-bottom: 2px;
  }

  .contacts-create-top {
    display: none !important;
  }

  .crm-toolbar {
    padding: 8px 0 !important;
  }

  .opportunities-filter-row--search,
  .opportunities-filter-row--primary {
    padding-left: 0;
    padding-right: 0;
  }

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

  .opportunities-filter-row--primary {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    padding-bottom: 2px;
  }

  .toolbar-search {
    min-width: 0;
    flex: 1 1 auto;
  }

  .toolbar-ms-btn {
    width: 100%;
    justify-content: center;
  }

  .mobile-create-btn {
    height: 32px;
    border: 1px solid #37be57;
    background: #3dcc5f;
    color: #0f1f14;
    border-radius: 9px;
    padding: 0 10px;
    font-size: 12px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    flex: 0 0 auto;
  }

  .mobile-create-btn-plus {
    font-size: 14px;
    line-height: 1;
    font-weight: 700;
  }

  .toolbar-ms-btn {
    height: 32px;
    padding: 0 10px;
    font-size: 12px;
    white-space: nowrap;
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



  border: 1px solid #e2e8f0;



  background-color: #f1f5f9;



  color: #334155;



  transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease;



}



.status-chip-button:hover {



  background-color: #e2e8f0;



}



.status-chip-button svg {



  color: inherit;



}



.status-chip-button:disabled {



  cursor: not-allowed;



}



.status-dropdown {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
  max-height: 13.6rem;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 0.25rem;
}

.status-dropdown-portal {
  position: fixed;
}

.status-option-badge {
  width: 100%;
  display: block;
  text-align: left;
  border: 1px solid;
  border-radius: 10px;
  padding: 0.4rem 0.7rem;
  font-size: 0.78rem;
  font-weight: 700;
  line-height: 1.15;
  margin-top: 0.24rem;
  transition: filter 0.15s ease;
}

.status-option-badge:first-child {
  margin-top: 0;
}

.status-option-badge:hover {
  filter: brightness(0.97);
}



.status-option {



  width: 100%;



  display: flex;



  align-items: center;



  gap: 0.5rem;



  border-radius: 0.875rem;



  border: 1px solid #e2e8f0;



  padding: 0.45rem 0.75rem;



  margin-top: 0.25rem;



  font-size: 0.78rem;



  font-weight: 600;



  background-color: #f8fafc;



  color: #334155;



  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;



}



.status-option--neutral {



  background-color: #f1f5f9;



  color: #334155;



}



.status-option--active {



  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.08);



}



.status-option:not(.status-option--active):hover {



  background-color: #f1f5f9;



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

:global(.dark-theme) .status-dropdown {
  background: #111319;
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
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






















































