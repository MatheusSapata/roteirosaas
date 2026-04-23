<template>
<div v-if="isBootstrappingLeads" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8">
  <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
</div>
<div v-else class="leads-page-shell relative flex h-full min-h-0 w-full flex-col overflow-hidden">



    <div



      class="leads-page flex min-h-0 flex-1 flex-col gap-5 overflow-hidden px-4 py-4 md:px-5"



      :class="{ 'pointer-events-none select-none opacity-60': !planAllowed }"



    >



      <div class="shrink-0">



        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400">



          {{ viewCopy.header.eyebrow }}


        </p>



        <h1 class="text-3xl font-bold text-slate-900 dark:text-white">{{ viewCopy.header.title }}</h1>


        <p class="text-sm text-slate-500 dark:text-slate-400">



          {{ viewCopy.header.description }}



        </p>



      </div>







      <div class="shrink-0 flex w-full flex-wrap items-center justify-between gap-3 text-sm font-semibold">



        <div class="flex flex-wrap gap-2">



          <button



            type="button"



            class="rounded-full px-4 py-2 transition"



            :class="activeTab === 'forms' ? activeTabClass : inactiveTabClass"



            @click="activeTab = 'forms'"



          >



            {{ viewCopy.tabs.forms }}



          </button>



          <button



            type="button"



            class="rounded-full px-4 py-2 transition"



            :class="activeTab === 'contacts' ? activeTabClass : inactiveTabClass"



            @click="activeTab = 'contacts'"



          >



            {{ viewCopy.tabs.contacts }}



          </button>



          <button



            type="button"



            class="rounded-full px-4 py-2 transition"



            :class="activeTab === 'settings' ? activeTabClass : inactiveTabClass"



            @click="activeTab = 'settings'"



          >



            {{ viewCopy.tabs.settings }}



          </button>



        </div>







        <div class="flex items-center gap-3">



          <button



            v-if="activeTab === 'forms'"



            type="button"



            class="hidden rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-brand-dark md:inline-flex"



            @click="openCreateModal"



          >



            + {{ viewCopy.actions.newForm }}



          </button>







          <div v-if="activeTab === 'contacts' && !isMobileViewport" class="flex items-center gap-3">



            <div v-if="contactViewMode === 'kanban'" class="flex items-center gap-3">

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







            <div class="inline-flex rounded-full bg-slate-100 p-1 dark:bg-white/10">



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



      </div>







      <div class="flex min-h-0 flex-1 flex-col">



        <div class="mt-3 mb-5 w-full md:hidden">



          <button



            v-if="activeTab === 'forms'"



            type="button"



            class="w-full rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-brand-dark"



            @click="openCreateModal"



          >



            + {{ viewCopy.actions.newForm }}



          </button>



        </div>







        <div class="flex min-h-0 flex-1 flex-col">



          <section v-if="activeTab === 'forms'" class="space-y-4">



            <div



              v-if="formsLoading && !forms.length"



              class="rounded-2xl border border-slate-100 px-4 py-6 text-center text-sm text-slate-500 dark:border-white/10 dark:text-slate-400"



            >



              {{ viewCopy.forms.loading }}



            </div>







            <div



              v-else-if="!forms.length"



              class="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500 dark:border-white/20 dark:text-slate-300"



            >



              {{ viewCopy.emptyStates.forms.prefix }}



              <strong>&ldquo;{{ viewCopy.actions.newForm }}&rdquo;</strong>



              {{ viewCopy.emptyStates.forms.suffix }}



            </div>







            <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">



              <article



                v-for="form in forms"



                :key="form.id"



                class="flex flex-col rounded-3xl border border-slate-100 bg-white/80 p-5 shadow-sm transition hover:shadow-lg dark:border-white/10 dark:bg-white/5"



              >



                <div class="flex items-start justify-between gap-3">



                  <div class="space-y-2">



                    <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">



                      {{ viewCopy.forms.card.eyebrow }}



                    </p>







                    <div>



                      <p class="text-[11px] font-semibold uppercase tracking-wide text-slate-400">



                        {{ viewCopy.forms.card.nameLabel }}



                      </p>



                      <h3 class="text-xl font-semibold text-slate-900 dark:text-white">



                        {{ form.name || fallbackLabels.noNameDefined }}



                      </h3>



                    </div>







                    <div>



                      <p class="text-[11px] font-semibold uppercase tracking-wide text-slate-400">



                        {{ viewCopy.forms.card.titleLabel }}



                      </p>



                      <p class="text-sm text-slate-500 dark:text-slate-400">



                        {{ form.title || fallbackLabels.noTitleDefined }}



                      </p>



                    </div>



                  </div>







                  <span class="rounded-full bg-slate-900/5 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-white/10 dark:text-white">



                    {{ form.total_leads ?? 0 }} {{ viewCopy.forms.card.totalLeadsSuffix }}



                  </span>



                </div>







                <div class="mt-4 flex flex-wrap gap-2">



                  <span



                    v-for="field in form.fields"



                    :key="field.id"



                    class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-white/10 dark:text-slate-200"



                  >



                    {{ field.label }}



                  </span>



                </div>







                <div class="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">



                  <span>



                    {{ viewCopy.forms.card.updatedAt }} {{ formatDate(form.updated_at || form.created_at) }}



                  </span>







                  <div class="flex gap-2">



                    <button



                      type="button"



                      class="rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-600 transition hover:bg-slate-100 dark:border-white/20 dark:text-white dark:hover:bg-white/10"



                      @click="openEditModal(form)"



                    >



                      {{ viewCopy.actions.edit }}



                    </button>







                    <button



                      type="button"



                      class="rounded-full border border-rose-300 px-3 py-1 font-semibold text-rose-600 transition hover:bg-rose-50 dark:border-rose-500/40 dark:text-rose-200 dark:hover:bg-rose-500/10"



                      @click="confirmDeleteForm(form)"



                    >



                      {{ viewCopy.actions.delete }}



                    </button>



                  </div>



                </div>



              </article>



            </div>



          </section>







          <section v-else-if="activeTab === 'contacts'" class="flex min-h-0 flex-1 flex-col gap-6 overflow-hidden">



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



              <div



                v-if="contactViewMode === 'list' && !filteredContacts.length"



                class="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500 dark:border-white/20 dark:text-slate-300"



              >



                {{ viewCopy.emptyStates.contacts.noFilters }}



              </div>







              <div v-else-if="contactViewMode === 'list'" class="flex min-h-0 flex-1 flex-col overflow-hidden">



                <article



                  class="flex flex-1 flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white p-0 shadow-sm dark:border-white/10 dark:bg-[#202020]"



                  :style="{ minHeight: listTableMinHeight }"



                >



                  <div class="flex flex-1 flex-col min-h-0" @click="closeFilterPopover">



                    <div



                      v-if="hasActiveFilters"



                      class="mb-3 flex flex-wrap items-center gap-2 px-4 pt-4 text-xs text-slate-500 dark:text-slate-300"



                    >



                      <span>{{ filterCopy.active }}</span>



                      <button



                        type="button"



                        class="rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-600 transition hover:bg-slate-100 dark:border-white/10 dark:text-white dark:hover:bg-white/10"



                        @click.stop="clearAllFilters"



                      >



                        {{ filterCopy.clearAll }}



                      </button>



                    </div>







                    <div class="flex-1 min-h-0 overflow-auto">



                      <table class="min-w-full divide-y divide-slate-200 text-sm dark:divide-white/10">



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







                            <th class="relative px-2 py-2">



                              <div class="flex items-center gap-1">



                                <span>{{ filterCopy.columns.received }}</span>



                                <button



                                  type="button"



                                  class="filter-button"



                                  :class="{ 'text-brand': isFilterActive('received') }"



                                  @click.stop="toggleFilterPopover('received')"



                                >



                                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor">



                                    <path d="M3 4h18l-7 8v6l-4 2v-8Z" />



                                  </svg>



                                </button>



                              </div>







                              <div v-if="openFilterKey === 'received'" class="filter-popover w-60" @click.stop>



                                <label class="text-[11px] uppercase text-slate-400">{{ filterCopy.from }}</label>



                                <input



                                  v-model="listFilters.receivedFrom"



                                  type="date"



                                  class="mb-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-white/20 dark:bg-[#0f1524]"



                                />







                                <label class="text-[11px] uppercase text-slate-400">{{ filterCopy.to }}</label>



                                <input



                                  v-model="listFilters.receivedTo"



                                  type="date"



                                  class="mb-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-white/20 dark:bg-[#0f1524]"



                                />







                                <div class="mt-2 flex gap-2 text-xs">



                                  <button type="button" class="text-slate-500 hover:text-slate-700" @click="clearFilter('received')">



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



                          <tr



                            v-for="contact in filteredContacts"



                            :key="contact.id"



                            class="text-slate-700 transition hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-white/[0.03]"



                          >



                            <td class="px-2 py-2 font-semibold">{{ contact.name || fallbackLabels.noName }}</td>



                            <td class="px-2 py-2 font-semibold">{{ getContactFormLabel(contact) }}</td>







                            <td class="px-2 py-2">



                              <div class="flex items-center gap-2">



                                <span class="font-mono text-sm">{{ contact.phone || viewCopy.labels.dash }}</span>



                                <button



                                  v-if="contact.phone"



                                  type="button"



                                  class="transition hover:opacity-80"



                                  :style="{ color: '#29E870' }"



                                  :title="getWhatsappTitle(contact.phone)"



                                  @click="openWhatsapp(contact.phone, getContactFormLabel(contact))"



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



                                >



                                  {{ contact.page_title || contact.page_slug }}



                                </a>



                                <span v-else>{{ contact.page_title || contact.page_slug }}</span>



                              </template>



                              <span v-else>{{ viewCopy.labels.dash }}</span>



                            </td>







                            <td class="px-2 py-2 text-xs">{{ formatDate(contact.created_at) }}</td>







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



            class="rounded-2xl border border-slate-100 bg-white p-3 text-xs shadow-sm transition dark:border-white/10 dark:bg-[#05070F]"



            :class="{ 'opacity-40': contactStatusSaving[idKey(contact.id)] }"



            draggable="true"



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



                  @click="openWhatsapp(contact.phone, getContactFormLabel(contact))"



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







          <section v-else class="space-y-6">



            <LeadStatusManagerPanel />



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



</template>







<script setup lang="ts">



import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";



import type { CSSProperties } from "vue";



import { useRouter } from "vue-router";



import LeadFormBuilderModal from "../../components/admin/leads/LeadFormBuilderModal.vue";



import LeadStatusManagerPanel from "../../components/admin/leads/LeadStatusManagerPanel.vue";



import type { LeadContact, LeadForm, LeadFormPayload, LeadStatus } from "../../types/leads";



import { useLeadCaptureStore } from "../../store/useLeadCaptureStore";



import { useThemeStore } from "../../store/useThemeStore";



import { useLeadFeatureGate } from "../../composables/useLeadFeatureGate";



import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";
import type { AdminLanguage, AdminTranslatable } from "../../utils/adminI18n";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";







type TabKey = "forms" | "contacts" | "settings";



type FilterKey = "name" | "form" | "phone" | "email" | "city" | "page" | "status" | "received";



type ValueFilterKey = Exclude<FilterKey, "received">;



type ContactViewMode = "list" | "kanban";







const router = useRouter();



const leadStore = useLeadCaptureStore();



const themeStore = useThemeStore();
const isBootstrappingLeads = ref(true);



const { hasLeadFeatureAccess } = useLeadFeatureGate();



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
    }
  },
  tabs: {
    forms: { pt: "Formulários", es: "Formularios" },
    contacts: { pt: "Oportunidades", es: "Oportunidades" },
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
      message: {
        pt: 'Olá! Recebi o formulário "{form}" e gostaria de falar com você.',
        es: '¡Hola! Recibí el formulario "{form}" y me gustaría hablar contigo.'
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
      received: { pt: "Recebido", es: "Recibido" },
      status: { pt: "Status", es: "Estado" },
      actions: { pt: "Ações", es: "Acciones" }
    },
    kanban: {
      allPages: { pt: "Todas as páginas", es: "Todas las páginas" },
      allForms: { pt: "Todos os formulários", es: "Todos los formularios" }
    }
  },
  settings: {
    planGate: {
      title: { pt: "Disponível no plano Agência", es: "Disponible en el plan Agencia" },
      description: {
        pt: "A captação de leads está liberada a partir do plano Agência ou superior. Atualize seu plano para desbloquear essa funcionalidade.",
        es: "La captación de leads se libera a partir del plan Agencia ou superior. Actualiza tu plan para desbloquear esta funcionalidad."
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
        es: "Aún no hay leads captados. Divulga las páginas con formulario obrigatório para empezar."
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







const listTableMinHeight = computed(() => {



  if (typeof window === "undefined") return "24rem";



  const viewportHeight = window.innerHeight || 768;



  const usable = Math.max(viewportHeight - 360, 320);



  return `${usable}px`;



});







const activeTab = ref<TabKey>("forms");



const contactViewMode = ref<ContactViewMode>("list");



const isMobileViewport = ref(false);



const builderOpen = ref(false);



const builderSaving = ref(false);



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



    form: buildOptions(allContacts.value.map(contact => getContactFormLabel(contact)), DEFAULT_FORM_LABEL),



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



  if (!matchArray(listFilters.form, getContactFormLabel(contact), DEFAULT_FORM_LABEL)) return false;



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







const showFeedback = (message: string, isError = false) => {



  feedback.value = { message, isError };



  setTimeout(() => {



    feedback.value = { message: "", isError: false };



  }, 4000);



};







const openCreateModal = () => {



  currentForm.value = null;



  builderOpen.value = true;



};







const openEditModal = (form: LeadForm) => {



  currentForm.value = form;



  builderOpen.value = true;



};







const confirmDeleteForm = async (form: LeadForm) => {



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



    showFeedback(viewCopy.messages.formSaveError, true);



  } finally {



    builderSaving.value = false;



  }



};













const openWhatsapp = (phone: string | undefined, formName: string) => {



  const digits = normalizeWhatsappDigits(phone);



  if (!digits) return;



  const message = whatsappCopy.message.replace("{form}", formName);



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



  isMobileViewport.value = isMobile;



  if (isMobile && contactViewMode.value !== "list") {



    contactViewMode.value = "list";



  }



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



});



</script>







<style scoped>



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
















