<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <!-- HEADER -->
    

    <!-- ERROR -->
    <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ error }}
    </div>

    <!-- TABS -->
    <section class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-100">
      <div class="flex flex-wrap gap-3">
        <button
          v-for="tab in adminTabs"
          :key="tab.id"
          type="button"
          class="flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition"
          :class="tabButtonClass(tab.id)"
          @click="activeTab = tab.id"
        >
          <span>{{ tab.label }}</span>
          <span class="text-xs font-normal text-slate-400" v-if="activeTab !== tab.id">
            {{ tab.description }}
          </span>
        </button>
      </div>
    </section>

    <!-- DASHBOARD -->
    <template v-if="activeTab === 'dashboard'">
      <header class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p :class="['text-xs uppercase tracking-[0.25em]', premiumMode ? 'text-white/50' : 'text-slate-500']">
          Administracao
        </p>
        <h1 :class="['text-3xl font-bold', premiumMode ? 'text-white' : 'text-slate-900']">
          Visao gerencial
        </h1>
        <p :class="['text-sm', premiumMode ? 'text-white/60' : 'text-slate-500']">
          Resumo de usuários, planos, validade e MRR.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <select
          v-model="days"
          class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition focus:outline-none focus:ring-2 focus:ring-brand/20 dark:border-white/15 dark:bg-[#202020] dark:text-white"
        >
          <option value="7">Ultimos 7 dias</option>
          <option value="30">Ultimos 30 dias</option>
          <option value="90">Ultimos 90 dias</option>
          <option value="custom">Personalizado</option>
        </select>
        <div v-if="days === 'custom'" class="flex flex-wrap items-center gap-2 text-xs text-slate-600">
          <label class="font-semibold">De</label>
          <input
            type="date"
            v-model="customStartDate"
            class="rounded-lg border border-slate-200 px-3 py-1 text-sm text-slate-700"
          />
          <span class="font-semibold">at├®</span>
          <input
            type="date"
            v-model="customEndDate"
            class="rounded-lg border border-slate-200 px-3 py-1 text-sm text-slate-700"
          />
        </div>

        <button
          @click="exportPdf"
          class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-white/15 dark:bg-[#202020] dark:text-white dark:hover:bg-[#1a1a1a]"
        >
          Exportar PDF
        </button>
      </div>
    </header>
    
      <section class="grid gap-4 md:grid-cols-4">
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Usuários</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.total_users ?? "--" }}</p>
          <p class="text-xs text-slate-400">Contas ativas no SaaS.</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Agências</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.total_agencies ?? "--" }}</p>
          <p class="text-xs text-slate-400">Times cadastrados.</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Páginas totais</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.total_pages ?? "--" }}</p>
          <p class="text-xs text-slate-400">Inclui rascunhos e publicadas.</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Paginas publicadas</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.published_pages ?? "--" }}</p>
          <p class="text-xs text-slate-400">Visiveis ao publico.</p>
        </div>
      </section>

      <section class="grid gap-4 md:grid-cols-3">
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">MRR estimado</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">R$ {{ metrics?.mrr?.toFixed(2) ?? "--" }}</p>
          <p class="text-xs text-slate-400">Somatório dos planos ativos.</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">ARR estimado</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">
            <span v-if="arrValue !== null">R$ {{ arrValue.toFixed(2) }}</span>
            <span v-else>--</span>
          </p>
          <p class="text-xs text-slate-400">Projeção anual baseada no MRR.</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Faturamento total</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">
            <span v-if="lifetimeRevenue !== null">R$ {{ lifetimeRevenue.toFixed(2) }}</span>
            <span v-else>--</span>
          </p>
          <p class="text-xs text-slate-400">Somatório de todo o faturamento.</p>
        </div>
      </section>

      <section class="grid gap-4 lg:grid-cols-3">
        <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100 lg:col-span-2">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Novos usuários ({{ adminPeriodLabel }})</h2>
              <p class="text-sm text-slate-500">Entradas diárias.</p>
            </div>
          </div>

          <div class="mt-4">
            <div
              v-if="newUsersPoints.length"
              class="space-y-3 rounded-2xl border border-slate-100 bg-white/90 p-6 shadow-inner"
            >
              <div class="relative rounded-2xl bg-transparent p-4">
                <div class="pointer-events-none absolute inset-4">
                  <div
                    v-for="line in newUsersGridLines"
                    :key="'grid-' + line"
                    class="absolute left-0 right-0 border-t border-dashed border-emerald-100"
                    :style="{ top: line + 'px' }"
                  ></div>
                </div>
                <div class="relative" :style="{ height: newUsersChartHeight + 'px' }">
                  <svg :viewBox="`0 0 ${newUsersChartWidth} ${newUsersChartHeight}`" preserveAspectRatio="none" class="h-full w-full">
                    <defs>
                      <linearGradient id="new-users-bar" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#41ce5f" stop-opacity="0.95"></stop>
                        <stop offset="100%" stop-color="#2ca751" stop-opacity="0.75"></stop>
                      </linearGradient>
                    </defs>
                    <template v-for="point in newUsersPoints" :key="point.label + '-bar'">
                      <rect
                        :x="point.barX"
                        :y="point.y"
                        :width="point.barWidth"
                        :height="point.barHeight"
                        rx="8"
                        fill="url(#new-users-bar)"
                      />
                    </template>
                  </svg>
                  <div
                    ref="newUsersSurfaceRef"
                    class="absolute inset-0 cursor-crosshair"
                    @mousemove="handleNewUsersMove"
                    @mouseleave="clearNewUsersHover"
                  ></div>
                  <div
                    v-if="newUsersHoverPoint"
                    class="pointer-events-none absolute -translate-x-1/2 rounded-xl border border-white bg-slate-900/90 px-4 py-2 text-xs text-white shadow-lg"
                    :style="newUsersTooltipStyle"
                  >
                    <p class="font-semibold">{{ newUsersHoverPoint.label }}</p>
                    <p>Novos usuários: {{ newUsersHoverPoint.value }}</p>
                  </div>
                </div>
              </div>

              <div class="text-xs text-slate-500">
                <template v-if="compactNewUsersLabels && newUsersLabelRange">
                  <div class="flex items-center justify-between font-semibold text-slate-700">
                    <span>{{ newUsersLabelRange.start }}</span>
                    <span>{{ newUsersLabelRange.end }}</span>
                  </div>
                </template>
                <template v-else>
                  <div class="flex flex-wrap justify-between gap-2 font-semibold text-slate-700">
                    <span v-for="point in newUsersPoints" :key="point.label + '-label'">{{ point.label }}</span>
                  </div>
                </template>
              </div>
            </div>
            <div
              class="flex h-64 items-center justify-center rounded-2xl bg-slate-50 text-sm text-slate-500"
              v-else
            >
              Sem dados no período.
            </div>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
          <h3 class="text-sm font-semibold text-slate-900">Distribuição de planos</h3>
          <ul class="mt-3 space-y-1 text-sm text-slate-600">
            <li v-for="p in metrics?.plans || []" :key="p.plan" class="flex justify-between">
              <span class="capitalize">{{ planLabel(p.plan) }}</span>
              <span class="font-semibold">{{ p.count }}</span>
            </li>
            <li v-if="!(metrics?.plans?.length)" class="text-xs text-slate-400">Sem dados ainda.</li>
          </ul>
        </div>
      </section>
    </template>

    <template v-else-if="activeTab === 'monitor'">
      <section class="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100 dark:bg-[#0f1118] dark:ring-white/10">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500 dark:text-white/60">
              Monitoramento em tempo real
            </p>
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">Usuários online agora</h2>
            <p class="text-sm text-slate-500 dark:text-white/60">Sessões autenticadas nos últimos 10 minutos.</p>
            <p class="text-xs text-slate-400 dark:text-white/50">
              {{ onlineSessionsMeta?.total_online ?? 0 }} sessões acompanhadas em tempo real.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-white/70">
            <p v-if="monitorLastUpdated">Atualizado ás {{ monitorLastUpdated }}</p>
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2 font-semibold text-white transition hover:bg-slate-800 dark:bg-white/10 dark:text-white dark:hover:bg-white/20"
              :disabled="onlineSessionsLoading"
              @click="loadOnlineSessions(true)"
            >
              <svg
                v-if="onlineSessionsLoading"
                class="h-4 w-4 animate-spin text-white"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              <span>{{ onlineSessionsLoading ? "Atualizando..." : "Atualizar monitor" }}</span>
            </button>
          </div>
        </div>

        <div class="mt-4">
          <div
            class="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-slate-800 shadow-sm dark:border-white/10 dark:bg-white/5 dark:text-white flex flex-wrap gap-6"
          >
            <div class="min-w-[180px] flex-1">
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">Usuários únicos</p>
              <p class="mt-2 text-3xl font-bold">{{ onlineSessionsMeta?.unique_users ?? 0 }}</p>
            </div>
            <div class="min-w-[180px] flex-1">
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">Status do monitor</p>
              <p class="mt-2 text-3xl font-bold">{{ monitorStatusLabel }}</p>
            </div>
          </div>
        </div>

        <div class="mt-6 space-y-4">
          <div
            v-if="onlineSessionsLoading && !onlineSessions.length"
            class="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/70"
          >
            Carregando sess├Áes ativas...
          </div>
          <div
            v-else-if="onlineSessionsError"
            class="rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-sm font-semibold text-red-600 dark:border-red-400/40 dark:bg-red-500/10 dark:text-red-200"
          >
            {{ onlineSessionsError }}
          </div>
          <div
            v-else-if="!onlineSessions.length"
            class="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/70"
          >
            Nenhum usuário est├í online neste momento.
          </div>
          <div v-else class="grid gap-4 lg:grid-cols-2">
            <article
              v-for="session in onlineSessions"
              :key="session.session_id"
              class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-[#05070f]"
            >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center gap-3">
                  <div
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-base font-semibold text-slate-700 dark:bg-white/10 dark:text-white"
                  >
                    {{ (session.user_name || "U").slice(0, 1).toUpperCase() }}
                  </div>
                  <div>
                    <p class="text-base font-semibold text-slate-900 dark:text-white">{{ session.user_name }}</p>
                    <p class="text-xs text-slate-500 dark:text-white/60">{{ session.user_email }}</p>
                  </div>
                </div>
                <span
                  class="inline-flex items-center rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-600 dark:border-white/20 dark:text-white/80"
                >
                  {{ planLabel(session.user_plan) }}
                </span>
              </div>
              <div class="mt-3 grid gap-3 text-sm text-slate-700 dark:text-white/80 md:grid-cols-2">
                <div>
                  <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400 dark:text-white/50">Dispositivo</p>
                  <p class="font-semibold">
                    {{ session.device_label || "Desconhecido" }} | {{ session.client_name || "Navegador" }}
                  </p>
                </div>
                <div>
                  <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400 dark:text-white/50">├Ültima atividade</p>
                  <p class="font-semibold">
                    {{ formatRelativeMoment(session.last_seen_at) }} há {{ formatClock(session.last_seen_at) }}
                  </p>
                </div>
                <div>
                  <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400 dark:text-white/50">Origem</p>
                  <p class="font-semibold">{{ session.ip_address || "IP não identificado" }}</p>
                </div>
                <div v-if="session.last_path">
                  <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400 dark:text-white/50">página atual</p>
                  <p class="font-semibold break-all">{{ session.last_path }}</p>
                </div>
              </div>
              <div class="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 dark:text-white/70">
                <span>{{ formatDurationSince(session.created_at) }}</span>
                <span>{{ session.active_sessions }} {{ session.active_sessions === 1 ? "sessão" : "sessões" }}</span>
                <button
                  type="button"
                  class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-white/30 dark:text-white dark:hover:bg-white/10"
                  :disabled="revokingUserId === session.user_id"
                  @click="revokeUserSessions(session)"
                >
                  {{ revokingUserId === session.user_id ? "Deslogando..." : "Deslogar usuário" }}
                </button>
              </div>
            </article>
          </div>
        </div>
      </section>
    </template>

    <!-- USERS -->
    <template v-else-if="activeTab === 'users'">
      <section class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Usuarios</h2>
            <p class="text-sm text-slate-500">Plano, validade e data de entrada.</p>
          </div>
        </div>

        <div class="mt-4 overflow-x-auto">
          <table class="min-w-full text-sm text-slate-800 divide-y divide-slate-100 interactive-table">
            <thead class="bg-slate-50 text-left text-slate-600">
              <tr>
                <th v-for="column in userTableColumns" :key="column.key" class="px-3 py-2">
                  <div
                    class="relative flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500"
                    :class="column.align === 'right' ? 'justify-end text-right' : 'text-left'"
                    :data-column-filter="column.key"
                  >
                    <button
                      class="flex items-center gap-1 text-left"
                      :class="column.sortable ? 'cursor-pointer select-none' : ''"
                      type="button"
                      @click.stop="column.sortable && toggleColumnSort(column.key)"
                    >
                      <span>{{ column.label }}</span>
                      <span v-if="column.sortable" class="flex flex-col text-[10px] leading-3 text-slate-400">
                        <svg
                          class="h-3 w-3"
                          :class="userSort.key === column.key && userSort.direction === 'desc' ? 'text-slate-900' : ''"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        >
                          <path d="m6 9 6-6 6 6" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>
                        <svg
                          class="h-3 w-3 -mt-0.5"
                          :class="userSort.key === column.key && userSort.direction === 'asc' ? 'text-slate-900' : ''"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        >
                          <path d="m6 15 6 6 6-6" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>
                      </span>
                    </button>
                    <button
                      :ref="el => setFilterButtonRef(column.key, el as HTMLElement | null)"
                      class="ml-auto inline-flex items-center justify-center rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-widest transition"
                      :class="isFilterActive(column.key) ? 'border-emerald-400 bg-emerald-50 text-emerald-600' : 'border-slate-200 text-slate-400 hover:text-slate-600'"
                      type="button"
                      :data-column-filter="column.key"
                      @click.stop="toggleColumnFilter(column.key, $event)"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <path d="M4 5h16M7 12h10M10 19h4" stroke-linecap="round" />
                      </svg>
                    </button>
                    <Teleport to="body" v-if="openFilterKey === column.key">
                      <div
                        class="fixed z-50 rounded-2xl border border-slate-200 bg-white/95 px-4 py-3 text-[11px] text-slate-600 shadow-[0_20px_45px_-25px_rgba(15,23,42,0.4)] backdrop-blur-sm"
                        :data-column-filter="column.key"
                        :style="filterPopoverStyle"
                        @click.stop
                      >
                      <template v-if="column.key === 'name'">
                        <p class="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                          Filtrar nome
                        </p>
                        <input
                          v-model="userFilters.name"
                          type="text"
                          placeholder="Nome ou email"
                          class="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2 text-xs focus:border-emerald-500 focus:outline-none"
                        />
                        <div class="mt-3 flex justify-end gap-4 text-[10px] font-semibold uppercase tracking-[0.2em]">
                          <button class="text-slate-400 hover:text-slate-600" type="button" @click="clearColumnFilter(column.key)">
                            Limpar
                          </button>
                          <button class="text-emerald-600 hover:text-emerald-500" type="button" @click="toggleColumnFilter(column.key)">
                            Fechar
                          </button>
                        </div>
                      </template>
                      <template v-else-if="column.key === 'agency_name'">
                        <p class="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                          Agências
                        </p>
                        <input
                          v-model="agencyFilterSearch"
                          type="text"
                          placeholder="Buscar agência"
                          class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-emerald-500 focus:outline-none"
                        />
                        <div class="mt-2 max-h-48 space-y-2 overflow-y-auto pr-1">
                          <label
                            v-for="option in filteredAgencyFilterOptions"
                            :key="option.value"
                            class="flex cursor-pointer items-center gap-2 text-[11px]"
                          >
                            <input
                              v-model="userFilters.agencies"
                              type="checkbox"
                              :value="option.value"
                              class="rounded border-slate-300 text-emerald-500 focus:ring-emerald-500"
                            />
                            <span>{{ option.label }}</span>
                          </label>
                          <p v-if="!filteredAgencyFilterOptions.length" class="text-[10px] text-slate-400">
                            Nenhuma agência encontrada.
                          </p>
                        </div>
                        <div class="mt-3 flex justify-end gap-4 text-[10px] font-semibold uppercase tracking-[0.2em]">
                          <button class="text-slate-400 hover:text-slate-600" type="button" @click="clearColumnFilter(column.key)">
                            Limpar
                          </button>
                          <button class="text-emerald-600 hover:text-emerald-500" type="button" @click="toggleColumnFilter(column.key)">
                            Fechar
                          </button>
                        </div>
                      </template>
                      <template v-else-if="column.key === 'plan'">
                        <p class="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                          Planos
                        </p>
                        <div class="mt-2 max-h-48 space-y-2 overflow-y-auto pr-1">
                          <label
                            v-for="plan in userPlanOptions"
                            :key="plan"
                            class="flex cursor-pointer items-center gap-2 text-[11px]"
                          >
                            <input
                              v-model="userFilters.plans"
                              type="checkbox"
                              :value="plan"
                              class="rounded border-slate-300 text-emerald-500 focus:ring-emerald-500"
                            />
                            <span>{{ planLabel(plan) }}</span>
                          </label>
                          <p v-if="!userPlanOptions.length" class="text-[10px] text-slate-400">Sem planos.</p>
                        </div>
                        <div class="mt-3 flex justify-end gap-4 text-[10px] font-semibold uppercase tracking-[0.2em]">
                          <button class="text-slate-400 hover:text-slate-600" type="button" @click="clearColumnFilter(column.key)">
                            Limpar
                          </button>
                          <button class="text-emerald-600 hover:text-emerald-500" type="button" @click="toggleColumnFilter(column.key)">
                            Fechar
                          </button>
                        </div>
                      </template>
                      <template v-else-if="column.key === 'active_pages'">
                        <p class="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                          Qtde. páginas ativas
                        </p>
                        <div class="mt-2 flex gap-2">
                          <input
                            v-model="userFilters.activeMin"
                            type="number"
                            placeholder="Min"
                            class="w-1/2 rounded-xl border border-slate-200 px-2 py-1 focus:border-emerald-500 focus:outline-none"
                          />
                          <input
                            v-model="userFilters.activeMax"
                            type="number"
                            placeholder="M├íx"
                            class="w-1/2 rounded-xl border border-slate-200 px-2 py-1 focus:border-emerald-500 focus:outline-none"
                          />
                        </div>
                        <div class="mt-3 flex justify-end gap-4 text-[10px] font-semibold uppercase tracking-[0.2em]">
                          <button class="text-slate-400 hover:text-slate-600" type="button" @click="clearColumnFilter(column.key)">
                            Limpar
                          </button>
                          <button class="text-emerald-600 hover:text-emerald-500" type="button" @click="toggleColumnFilter(column.key)">
                            Fechar
                          </button>
                        </div>
                      </template>
                      <template v-else-if="column.key === 'draft_pages'">
                        <p class="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                          Qtde. páginas rascunho
                        </p>
                        <div class="mt-2 flex gap-2">
                          <input
                            v-model="userFilters.draftMin"
                            type="number"
                            placeholder="Min"
                            class="w-1/2 rounded-xl border border-slate-200 px-2 py-1 focus:border-emerald-500 focus:outline-none"
                          />
                          <input
                            v-model="userFilters.draftMax"
                            type="number"
                            placeholder="M├íx"
                            class="w-1/2 rounded-xl border border-slate-200 px-2 py-1 focus:border-emerald-500 focus:outline-none"
                          />
                        </div>
                        <div class="mt-3 flex justify-end gap-4 text-[10px] font-semibold uppercase tracking-[0.2em]">
                          <button class="text-slate-400 hover:text-slate-600" type="button" @click="clearColumnFilter(column.key)">
                            Limpar
                          </button>
                          <button class="text-emerald-600 hover:text-emerald-500" type="button" @click="toggleColumnFilter(column.key)">
                            Fechar
                          </button>
                        </div>
                      </template>
                      <template v-else-if="column.key === 'valid_until'">
                        <p class="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                          Validade (intervalo)
                        </p>
                        <div class="mt-2 space-y-2">
                          <input
                            v-model="userFilters.validFrom"
                            type="date"
                            class="w-full rounded-xl border border-slate-200 px-2 py-1 focus:border-emerald-500 focus:outline-none"
                          />
                          <input
                            v-model="userFilters.validTo"
                            type="date"
                            class="w-full rounded-xl border border-slate-200 px-2 py-1 focus:border-emerald-500 focus:outline-none"
                          />
                        </div>
                        <div class="mt-3 flex justify-end gap-4 text-[10px] font-semibold uppercase tracking-[0.2em]">
                          <button class="text-slate-400 hover:text-slate-600" type="button" @click="clearColumnFilter(column.key)">
                            Limpar
                          </button>
                          <button class="text-emerald-600 hover:text-emerald-500" type="button" @click="toggleColumnFilter(column.key)">
                            Fechar
                          </button>
                        </div>
                      </template>
                      <template v-else-if="column.key === 'created_at'">
                        <p class="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                          Entrada (intervalo)
                        </p>
                        <div class="mt-2 space-y-2">
                          <input
                            v-model="userFilters.createdFrom"
                            type="date"
                            class="w-full rounded-xl border border-slate-200 px-2 py-1 focus:border-emerald-500 focus:outline-none"
                          />
                          <input
                            v-model="userFilters.createdTo"
                            type="date"
                            class="w-full rounded-xl border border-slate-200 px-2 py-1 focus:border-emerald-500 focus:outline-none"
                          />
                        </div>
                        <div class="mt-3 flex justify-end gap-4 text-[10px] font-semibold uppercase tracking-[0.2em]">
                          <button class="text-slate-400 hover:text-slate-600" type="button" @click="clearColumnFilter(column.key)">
                            Limpar
                          </button>
                          <button class="text-emerald-600 hover:text-emerald-500" type="button" @click="toggleColumnFilter(column.key)">
                            Fechar
                          </button>
                        </div>
                      </template>
                      </div>
                    </Teleport>
                  </div>
                </th>
              </tr>
            </thead>

            <tbody class="divide-y divide-slate-100">
              <template v-for="u in filteredUsers" :key="u.id">
                <tr class="transition hover:bg-slate-50/70 dark:hover:bg-white/5" @click="toggleUserRow(u.id)">
                  <td class="px-3 py-3">
                    <div class="flex items-start gap-3">
                      <button
                        type="button"
                        class="mt-1 rounded-full border border-slate-300 p-1 text-xs transition hover:bg-slate-100"
                        @click.stop="toggleUserRow(u.id)"
                      >
                        <span
                          :class="expandedUser === u.id ? 'rotate-90 inline-block transition' : 'inline-block transition'"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                          </svg>
                        </span>
                      </button>
                      <div>
                        <p class="font-semibold text-slate-900">{{ u.name }}</p>
                        <p class="text-xs text-slate-500">{{ u.email }}</p>
                      </div>
                    </div>
                  </td>

                  <td class="px-3 py-3">
                    <span class="text-slate-800">{{ u.agency_name || 'Sem agência' }}</span>
                  </td>

                  <td class="px-3 py-3 font-semibold text-slate-900">
                    {{ u.active_pages ?? 0 }}
                  </td>

                  <td class="px-3 py-3 font-semibold text-slate-900">
                    {{ u.draft_pages?.length ?? u.draft_pages_count ?? 0 }}
                  </td>

                  <td class="px-3 py-3 capitalize">
                    <span class="text-slate-800">{{ planLabel(u.plan) }}</span>
                    <span
                      v-if="u.trial_plan"
                      class="ml-2 inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-700"
                    >
                      Trial at├® {{ formatDate(u.trial_ends_at) }}
                    </span>
                  </td>

                  <td class="px-3 py-3">{{ formatDate(u.valid_until) }}</td>
                  <td class="px-3 py-3 whitespace-nowrap">{{ formatDateTime(u.created_at) }}</td>
                </tr>

                <tr v-if="expandedUser === u.id">
                  <td colspan="7" class="px-3 pb-4">
                    <div
                      class="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 text-sm text-slate-800 shadow-inner dark:border-white/10 dark:bg-[#202020] dark:text-white dark:shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]"
                    >
                      <div class="grid gap-4 md:grid-cols-2">
                        <div class="space-y-1 copyable">
                          <p class="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-white/50">Contato</p>
                          <p class="mt-1 font-semibold">{{ u.name }}</p>
                          <p class="text-xs text-slate-500 dark:text-white/60">{{ u.email }}</p>
                          <p class="text-xs text-slate-500 dark:text-white/60">{{ u.whatsapp || 'Sem telefone' }}</p>
                        </div>

                        <div>
                          <p class="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-white/50">Agência</p>
                          <p class="mt-1 font-semibold">{{ u.agency_name || 'N├úo vinculada' }}</p>
                          <p class="text-xs text-slate-500 dark:text-white/60">
                            {{ u.active_pages ?? 0 }} páginas publicadas ┬À Plano {{ planLabel(u.plan) }}
                          </p>
                        </div>
                      </div>

                      <div class="mt-4">
                        <p class="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-white/50">Origem / UTMs</p>
                        <div
                          v-if="u.tracking?.length"
                          class="mt-2 space-y-3 rounded-2xl border border-white/40 bg-white/80 p-4 shadow-inner dark:border-white/5 dark:bg-[#05070F] dark:shadow-none"
                        >
                          <div
                            v-for="entry in u.tracking"
                            :key="entry.id"
                            class="rounded-2xl border border-slate-200 bg-white/90 p-3 shadow-sm dark:border-white/10 dark:bg-[#05070F]"
                          >
                            <div class="flex flex-wrap gap-2">
                              <span
                                v-for="chip in buildUtmChips(entry)"
                                :key="chip.label + chip.value"
                                class="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold text-slate-600 dark:border-white/10 dark:bg-white/10 dark:text-white/80"
                              >
                                <span class="text-slate-400 dark:text-white/60">{{ chip.label }}:</span>
                                <span class="text-slate-900 dark:text-white">{{ chip.value }}</span>
                              </span>
                            </div>
                            <p class="mt-2 text-[11px] text-slate-500 dark:text-white/60">
                              Capturado em {{ formatDateTime(entry.created_at) || 'data desconhecida' }}
                            </p>
                          </div>
                        </div>
                        <p
                          v-else
                          class="mt-2 rounded-2xl border border-dashed border-slate-200 px-3 py-3 text-center text-xs text-slate-500 dark:border-white/10 dark:text-white/60"
                        >
                          Nenhuma informa├º├úo de UTM registrada.
                        </p>
                      </div>

                      <div class="mt-4 flex flex-wrap items-center gap-3">
                        <button
                          v-if="!u.is_superuser"
                          :class="[
                            'rounded-full border px-4 py-2 text-xs font-semibold text-slate-700 transition disabled:opacity-60',
                            'border-slate-200 hover:bg-emerald-50 hover:text-emerald-700 dark:border-emerald-400/60 dark:text-emerald-100 dark:hover:bg-emerald-500/20'
                          ]"
                          :disabled="granting === u.id || Boolean(u.trial_plan)"
                          @click.stop="openTrialDialog(u)"
                        >
                          {{ u.trial_plan ? 'Trial ativo' : 'Liberar 7 dias' }}
                        </button>

                        <button
                          v-if="auth.user?.is_superuser"
                          class="rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:text-white dark:hover:bg-white/10"
                          :disabled="!u.agency_id || !agencyStore.currentAgencyId"
                          @click.stop="openLinkPageDialog(u)"
                          :title="
                            !agencyStore.currentAgencyId
                              ? 'Selecione uma Agência de origem no painel'
                              : !u.agency_id
                                ? 'usuário sem Agência vinculada'
                                : 'Vincular página pronta'
                          "
                        >
                          Vincular página
                        </button>

                        <button
                          v-if="canRefundUser(u)"
                          class="rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-xs font-semibold text-amber-700 transition hover:bg-amber-100 disabled:opacity-60 dark:border-amber-400/60 dark:bg-amber-500/10 dark:text-amber-100 dark:hover:bg-amber-500/20"
                          :disabled="refundDialog.loading"
                          @click.stop="openRefundDialog(u)"
                        >
                          Reembolsar usuário
                        </button>

                        <button
                          v-if="!u.is_superuser"
                          class="rounded-full border border-red-200 bg-red-50 px-4 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-100 dark:border-red-500/60 dark:bg-red-500/10 dark:text-red-100 dark:hover:bg-red-500/20"
                          @click.stop="openDeleteDialog(u)"
                        >
                          Excluir usuário
                        </button>

                        <span
                          v-if="u.is_superuser"
                          class="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-white/10 dark:text-white"
                        >
                          Superuser
                        </span>
                      </div>

                      <div class="mt-6">
                        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/50">páginas publicadas</p>

                        <div
                          v-if="u.published_pages?.length"
                          class="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-[#05070F]"
                        >
                          <table class="min-w-full divide-y divide-slate-100 text-xs text-slate-700 interactive-table dark:divide-white/5 dark:text-white/80">
                            <thead class="bg-slate-50 text-left text-slate-500 dark:bg-[#05070F] dark:text-white/60">
                              <tr>
                                <th class="px-3 py-2">Título</th>
                                <th class="px-3 py-2">Slug</th>
                                <th class="px-3 py-2 text-right">Visualiza├º├Áes</th>
                                <th class="px-3 py-2 text-right">Cliques CTA</th>
                                <th class="px-3 py-2 text-right">A├º├Áes</th>
                              </tr>
                            </thead>

                            <tbody class="divide-y divide-slate-100 dark:divide-white/5">
                              <tr v-for="page in u.published_pages" :key="page.id">
                                <td class="px-3 py-2 font-semibold text-slate-900 dark:text-white">{{ page.title }}</td>
                                <td class="px-3 py-2 text-[11px] text-slate-500 dark:text-white/60">/{{ page.slug }}</td>
                                <td class="px-3 py-2 text-right font-semibold text-slate-900 dark:text-white">{{ page.total_visits ?? 0 }}</td>
                                <td class="px-3 py-2 text-right font-semibold text-slate-900 dark:text-white">{{ page.total_cta_clicks ?? 0 }}</td>
                                <td class="px-3 py-2">
                                  <div class="flex justify-end gap-2">
                                    <button
                                      class="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-white/10 dark:text-white dark:hover:bg-white/10"
                                      @click.stop="viewPublishedPage(page)"
                                    >
                                      Visualizar
                                    </button>

                                    <button
                                      class="inline-flex items-center gap-1 rounded-full border border-slate-900/20 bg-slate-900/90 px-3 py-1 text-[11px] font-semibold text-white transition hover:bg-slate-900 disabled:opacity-60 dark:border-white/10 dark:bg-white/15 dark:text-white dark:hover:bg-white/25"
                                      :disabled="savingPageId === page.id || !agencyStore.currentAgencyId"
                                      @click.stop="clonePublishedPage(u, page)"
                                    >
                                      {{ savingPageId === page.id ? 'Salvando...' : 'Salvar' }}
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>

                        <p
                          v-else
                          class="mt-3 rounded-xl border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-500 dark:border-white/10 dark:text-white/60"
                        >
                          Nenhuma página publicada ainda.
                        </p>
                      </div>

                      <div class="mt-6">
                        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/50">páginas em rascunho</p>

                        <div
                          v-if="u.draft_pages?.length"
                          class="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-[#05070F]"
                        >
                          <table class="min-w-full divide-y divide-slate-100 text-xs text-slate-700 interactive-table dark:divide-white/5 dark:text-white/80">
                            <thead class="bg-slate-50 text-left text-slate-500 dark:bg-[#05070F] dark:text-white/60">
                              <tr>
                                <th class="px-3 py-2">Título</th>
                                <th class="px-3 py-2">Slug</th>
                                <th class="px-3 py-2 text-right">A├º├Áes</th>
                              </tr>
                            </thead>

                            <tbody class="divide-y divide-slate-100 dark:divide-white/5">
                              <tr v-for="page in u.draft_pages" :key="page.id">
                                <td class="px-3 py-2 font-semibold text-slate-900 dark:text-white">{{ page.title }}</td>
                                <td class="px-3 py-2 text-[11px] text-slate-500 dark:text-white/60">/{{ page.slug }}</td>
                                <td class="px-3 py-2">
                                  <div class="flex justify-end">
                                    <button
                                      class="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-white/10 dark:text-white dark:hover:bg-white/10"
                                      @click.stop="goToPageEditor(page)"
                                    >
                                      Editar
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>

                        <p
                          v-else
                          class="mt-3 rounded-xl border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-500 dark:border-white/10 dark:text-white/60"
                        >
                          Nenhum rascunho registrado.
                        </p>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>

              <tr v-if="!filteredUsers.length">
                <td colspan="7" class="px-3 py-4 text-center text-slate-500">
                  Nenhum usuario encontrado.
                </td>
              </tr>
            </tbody>
          </table>

          <div class="mt-4 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-500">
            <p>
              Mostrando
              <span class="font-semibold text-slate-700">{{ userPageRange.start }}-{{ userPageRange.end }}</span>
              de
              <span class="font-semibold text-slate-700">{{ filteredUsersTotal }}</span>
              usuários
            </p>
            <div class="flex flex-wrap items-center gap-3">
              <label class="flex items-center gap-2">
                Linhas
                <select
                  v-model.number="userPageSize"
                  class="rounded-full border border-slate-200 px-3 py-1 text-xs focus:border-emerald-500 focus:outline-none"
                >
                  <option v-for="option in userPageSizeOptions" :key="option" :value="option">
                    {{ option }}
                  </option>
                </select>
              </label>
              <div class="flex items-center gap-2">
                <button
                  class="rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-600 disabled:opacity-40"
                  type="button"
                  :disabled="userPage === 1"
                  @click="userPage = Math.max(1, userPage - 1)"
                >
                  Anterior
                </button>
                <span>página {{ userPage }} de {{ totalUserPages }}</span>
                <button
                  class="rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-600 disabled:opacity-40"
                  type="button"
                  :disabled="userPage >= totalUserPages"
                  @click="userPage = Math.min(totalUserPages, userPage + 1)"
                >
                  Próxima
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <!-- LESSONS -->
    <template v-else-if="activeTab === 'lessons'">
      <section class="rounded-3xl bg-white p-6 shadow-md ring-1 ring-slate-100 dark:bg-[#181818] dark:text-white dark:ring-white/10">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500 dark:text-white/60">Conteúdoo exclusivo</p>
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">Gerenciar aulas</h2>
            <p class="text-sm text-slate-500 dark:text-white/70">As aulas cadastradas aqui aparecem para todos os administradores na aba "Aulas".</p>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-white/20 dark:bg-white/10 dark:text-white dark:hover:bg-white/20"
              @click="resetLessonForm"
            >
              Nova aula
            </button>

            <button
              type="button"
              class="rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 transition hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-70 dark:border-amber-400/60 dark:bg-amber-500/15 dark:text-amber-50 dark:hover:bg-amber-500/25"
              :disabled="resettingLessons"
              @click="handleResetLessons"
            >
              Restaurar padrão
            </button>
          </div>
        </div>

        <div class="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <div class="space-y-4">
            <p
              v-if="lessonsLoading"
              class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/60"
            >
              Carregando aulas...
            </p>

            <p
              v-else-if="!adminLessons.length"
              class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/60"
            >
              Nenhuma aula cadastrada ainda.
            </p>

            <template v-else>
              <article
                v-for="lesson in adminLessons"
                :key="lesson.id"
                class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#181818] dark:text-white"
              >
                <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p class="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">
                      {{ lesson.level || "Aula" }} Duração {{ lesson.duration || "Livre" }}
                    </p>
                    <h4 class="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{{ lesson.title }}</h4>
                    <p class="mt-1 text-sm text-slate-600 dark:text-white/70">{{ lesson.description }}</p>
                    <p class="mt-3 text-xs text-slate-500 dark:text-white/60">
                      Fonte:
                      <span class="font-semibold text-slate-700 dark:text-white">
                        {{ lesson.videoType === "file" ? "Arquivo/URL direto" : "Embed/Youtube" }}
                      </span>
                    </p>
                  </div>

                  <img v-if="lesson.thumbnail" :src="lesson.thumbnail" alt="" class="h-20 w-32 rounded-xl object-cover shadow-sm" />
                </div>

                <div class="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-white/15 dark:text-white dark:hover:bg-white/10"
                    @click="startLessonEdit(lesson)"
                  >
                    Editar
                  </button>

                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-full border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-400/50 dark:bg-red-500/15 dark:text-red-100 dark:hover:bg-red-500/25"
                    :disabled="deletingLessonId === lesson.id"
                    @click="deleteLesson(lesson.id)"
                  >
                    Excluir
                  </button>
                </div>
              </article>
            </template>
          </div>

          <form class="lessons-form space-y-4 rounded-2xl bg-slate-50/70 p-5 dark:bg-[#181818] dark:border dark:border-white/15" @submit.prevent="saveLesson">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">{{ isEditingLesson ? "Editando aula" : "Cadastrar nova aula" }}</p>
              <h3 class="text-xl font-semibold text-slate-900 dark:text-white">{{ isEditingLesson ? "Atualizar conteudo" : "Adicionar conteudo" }}</h3>
              <p class="text-sm text-slate-500 dark:text-white/70">Informe titulo, descricao e o link ou iframe do video.</p>
            </div>

            <label class="block text-sm font-semibold text-slate-700 dark:text-white">
              Título
              <input
                v-model="lessonForm.title"
                type="text"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand"
                placeholder="Ex.: Dominando o editor"
                required
              />
            </label>

            <label class="block text-sm font-semibold text-slate-700 dark:text-white">
              Descrição / legenda
              <textarea
                v-model="lessonForm.description"
                rows="3"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand dark:border-white/20 dark:bg-[#181818] dark:text-white dark:placeholder-white/70"
                placeholder="Explique o que o usuário aprende nessa aula."
              ></textarea>
            </label>

            <div class="grid gap-3 md:grid-cols-2">
              <label class="block text-sm font-semibold text-slate-700 dark:text-white">
                Duraçao
                <input
                  v-model="lessonForm.duration"
                  type="text"
                  class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand"
                  placeholder="Ex.: 10:45"
                />
              </label>

              <label class="block text-sm font-semibold text-slate-700 dark:text-white">
                Nível
                <input
                  v-model="lessonForm.level"
                  type="text"
                  class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand"
                  placeholder="Fundamentos, Estrat├®gia..."
                />
              </label>
            </div>

            <label class="block text-sm font-semibold text-slate-700 dark:text-white">
              Thumbnail por link (opcional)
              <input
                v-model="lessonForm.thumbnailUrl"
                type="url"
                :disabled="Boolean(lessonForm.thumbnailData)"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand disabled:cursor-not-allowed disabled:bg-slate-100"
                placeholder="https://..."
              />
              <span v-if="lessonForm.thumbnailData" class="mt-1 block text-xs text-slate-500 dark:text-white/60">
                Limpe a imagem enviada para editar o link.
              </span>
            </label>

            <div class="upload-zone rounded-2xl border border-dashed border-slate-300 bg-white/70 p-4 dark:border-white/15">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">Upload opcional</p>

              <div class="mt-2 flex flex-wrap items-center gap-3">
                <input
                  type="file"
                  accept="image/*"
                  @change="handleThumbnailUpload"
                  class="text-sm text-slate-600 file:mr-3 file:rounded-full file:border file:border-slate-300 file:bg-slate-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-700 hover:file:bg-slate-100 dark:text-white dark:file:border-white/30 dark:file:bg-white/10 dark:file:text-white dark:hover:file:bg-white/20"
                />

                <button
                  v-if="lessonForm.thumbnailData"
                  type="button"
                  class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-white/15 dark:text-white dark:hover:bg-white/10"
                  @click="clearThumbnailUpload"
                >
                  Remover imagem
                </button>
              </div>

              <p v-if="lessonForm.thumbnailUploadName" class="mt-2 text-xs text-slate-500 dark:text-white/60">
                Selecionado: {{ lessonForm.thumbnailUploadName }}
              </p>
            </div>

            <label class="block text-sm font-semibold text-slate-700 dark:text-white">
              Link ou iframe do vídeo
              <textarea
                v-model="lessonForm.videoInput"
                rows="3"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand dark:border-white/20 dark:bg-[#181818] dark:text-white dark:placeholder-white/70"
                placeholder="Cole o link do YouTube ou o iframe completo."
                required
              ></textarea>
            </label>

            <div v-if="lessonPreview.videoUrl" class="rounded-2xl border border-slate-200 bg-white p-3 dark:border-white/15 dark:bg-[#181818]">
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Prévia</p>
              <div class="mt-2 overflow-hidden rounded-xl">
                <iframe
                  v-if="lessonPreview.videoType !== 'file'"
                  :src="lessonPreview.videoUrl"
                  class="aspect-video w-full border-0"
                  allowfullscreen
                ></iframe>

                <video v-else class="aspect-video w-full rounded-xl bg-black object-cover" controls>
                  <source :src="lessonPreview.videoUrl" type="video/mp4" />
                </video>
              </div>
            </div>

            <div class="flex flex-wrap gap-2">
              <button
                type="submit"
                class="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="lessonSaving"
              >
                {{
                  lessonSaving
                    ? isEditingLesson
                      ? "Salvando..."
                      : "Adicionando..."
                    : isEditingLesson
                      ? "Atualizar aula"
                      : "Adicionar aula"
                }}
              </button>

              <button
                v-if="isEditingLesson"
                type="button"
                class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                @click="resetLessonForm"
              >
                Cancelar edi├º├úo
              </button>
            </div>
          </form>
        </div>
      </section>
    </template>

    <!-- TEMPLATES -->
    <template v-else-if="activeTab === 'templates'">
      <section class="rounded-3xl bg-white p-6 shadow-md ring-1 ring-slate-100 dark:bg-[#181818] dark:text-white dark:ring-white/10">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div class="flex-1">
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500 dark:text-white/60">Curadoria</p>
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">Biblioteca de modelos</h2>
            <p class="text-sm text-slate-500 dark:text-white/70">
              Selecione uma Agência de origem para transformar páginas em modelos oficiais.
            </p>
          </div>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div data-template-agency-selector="true">
              <label class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">Agência</label>
              <div class="relative mt-1 w-64">
                <input
                  ref="templateAgencySearchInput"
                  v-model="templateAgencySearch"
                  type="text"
                  placeholder="Buscar agência"
                  class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2 pr-10 text-sm text-slate-900 focus:border-brand focus:outline-none dark:border-white/15 dark:bg-[#101010] dark:text-white"
                  @focus="handleTemplateAgencyInputFocus"
                />
                <button
                  type="button"
                  class="absolute inset-y-0 right-3 flex items-center text-slate-400 transition hover:text-slate-600 dark:hover:text-white"
                  @click="toggleTemplateAgencyDropdown"
                >
                  <svg
                    class="h-4 w-4 transition"
                    :class="templateAgencyDropdownOpen ? 'rotate-180' : ''"
                    viewBox="0 0 20 20"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="M5 8l5 5 5-5" />
                  </svg>
                </button>
                <div
                  v-if="templateAgencyDropdownOpen"
                  class="absolute left-0 right-0 z-30 mt-2 w-full rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-white/15 dark:bg-[#101010]"
                >
                  <p v-if="templateAgencyLoading" class="px-4 py-3 text-sm text-slate-500 dark:text-white/70">Buscando Agências...</p>
                  <p v-else-if="templateAgencyError" class="px-4 py-3 text-sm text-red-600 dark:text-red-200">{{ templateAgencyError }}</p>
                  <ul
                    v-else-if="templateAgencyOptions.length"
                    class="max-h-60 divide-y divide-slate-100 overflow-y-auto py-1 dark:divide-white/5"
                  >
                    <li v-for="agency in templateAgencyOptions" :key="agency.id">
                      <button
                        type="button"
                        class="flex w-full flex-col gap-0.5 px-4 py-2 text-left transition hover:bg-slate-50 dark:hover:bg-white/10"
                        :class="agency.id === templateAgencyId ? 'bg-slate-50 dark:bg-white/5' : ''"
                        @click="selectTemplateAgency(agency)"
                      >
                        <span class="text-sm font-semibold text-slate-900 dark:text-white">{{ agency.name }}</span>
                        <span class="text-xs text-slate-500 dark:text-white/70">
                          /{{ agency.slug }} ┬À {{ agency.pages_count }} páginas
                        </span>
                      </button>
                    </li>
                  </ul>
                  <p v-else class="px-4 py-3 text-sm text-slate-500 dark:text-white/70">Nenhuma Agência encontrada.</p>
                </div>
              </div>
            </div>
            <button
              type="button"
              class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-white/15 dark:bg-white/10 dark:text-white dark:hover:bg-white/20"
              :disabled="templatePagesLoading || !templateAgencyId"
              @click="loadTemplatePages"
            >
              Recarregar páginas
            </button>
            <button
              type="button"
              class="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-white/15 dark:bg-white/10 dark:text-white dark:hover:bg-white/20"
              :disabled="pageTemplatesLoading"
              @click="loadTemplates"
            >
              Atualizar modelos
            </button>
          </div>
        </div>
      </section>

      <section class="rounded-3xl bg-white p-6 shadow-md ring-1 ring-slate-100 dark:bg-[#181818] dark:text-white dark:ring-white/10">
        <header class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500 dark:text-white/60">Origem</p>
            <h3 class="text-xl font-semibold text-slate-900 dark:text-white">Roteiros disponíveis</h3>
            <p class="text-sm text-slate-500 dark:text-white/70">
              Escolha um roteiro pronto para salvar como modelo. Apenas páginas publicadas são recomendadas.
            </p>
          </div>
          <span class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400 dark:text-white/60">
            {{ templatePages.length }} páginas
          </span>
        </header>
        <div class="mt-6">
          <p v-if="!templateAgencyId" class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/70">
            Selecione uma Agência para listar as páginas disponíveis.
          </p>
          <p v-else-if="templatePagesLoading" class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/70">
            Carregando páginas...
          </p>
          <p v-else-if="templatePagesError" class="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700 dark:border-red-400/40 dark:bg-red-500/10 dark:text-red-200">
            {{ templatePagesError }}
          </p>
          <p v-else-if="!templatePages.length" class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/70">
            Nenhum roteiro encontrado para a Agência selecionada.
          </p>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-slate-100 text-sm dark:divide-white/5">
              <thead>
                <tr class="text-left text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">
                  <th class="px-3 py-2">Título</th>
                  <th class="px-3 py-2">Status</th>
                  <th class="px-3 py-2">Slug</th>
                  <th class="px-3 py-2 text-right">Ações</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-white/5">
                <tr v-for="page in templatePages" :key="page.id" class="text-slate-700 dark:text-white/80">
                  <td class="px-3 py-3 font-semibold">{{ page.title }}</td>
                  <td class="px-3 py-3">
                    <span
                      class="rounded-full px-3 py-1 text-xs font-semibold"
                      :class="page.status === 'published' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200' : 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-100'"
                    >
                      {{ page.status === 'published' ? 'Publicado' : 'Rascunho' }}
                    </span>
                  </td>
                  <td class="px-3 py-3 text-sm text-slate-500 dark:text-white/60">/{{ page.slug }}</td>
                  <td class="px-3 py-3">
                    <div class="flex flex-wrap justify-end gap-2">
                      <a
                        v-if="templatePublicUrl(page)"
                        :href="templatePublicUrl(page)"
                        class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 dark:border-white/15 dark:text-white"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Visualizar
                      </a>
                      <button
                        type="button"
                        class="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900"
                        @click="openTemplateDialog(page)"
                      >
                        Adicionar como modelo
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section class="rounded-3xl bg-white p-6 shadow-md ring-1 ring-slate-100 dark:bg-[#181818] dark:text-white dark:ring-white/10">
        <header class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500 dark:text-white/60">Coleção</p>
            <h3 class="text-xl font-semibold text-slate-900 dark:text-white">Modelos publicados</h3>
            <p class="text-sm text-slate-500 dark:text-white/70">
              Utilize os modelos para acelerar a criação de novas páginas com identidade consistente.
            </p>
          </div>
          <span class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400 dark:text-white/60">
            {{ pageTemplates.length }} modelos
          </span>
        </header>
        <div class="mt-6">
          <p v-if="pageTemplatesLoading" class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/70">
            Carregando modelos...
          </p>
          <p v-else-if="pageTemplatesError" class="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700 dark:border-red-400/40 dark:bg-red-500/10 dark:text-red-200">
            {{ pageTemplatesError }}
          </p>
          <p v-else-if="!pageTemplates.length" class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/70">
            Nenhum modelo cadastrado ainda. Crie um usando os roteiros da sua rede.
          </p>
          <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <article
              v-for="template in pageTemplates"
              :key="template.id"
              class="flex flex-col rounded-2xl border border-slate-100 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg dark:border-white/10 dark:bg-[#1a1a1a]"
            >
              <div class="flex flex-1 flex-col p-4">
                <div class="flex items-center gap-2">
                  <h4 class="flex-1 text-lg font-semibold text-slate-900 dark:text-white">{{ template.name }}</h4>
                  <span
                    v-if="template.is_default"
                    class="rounded-full bg-emerald-100 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200"
                  >
                    Padrão
                  </span>
                </div>
                <p class="mt-1 text-sm text-slate-500 dark:text-white/60">
                  {{ template.description || "Sem descrição" }}
                </p>
                <div class="mt-3 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-white/60">
                  <span class="rounded-full bg-slate-100 px-3 py-1 dark:bg-white/10">
                    {{ templateStats(template).enabledSections }} sessões ativas
                  </span>
                  <span class="rounded-full bg-slate-100 px-3 py-1 dark:bg-white/10">
                    Total: {{ templateStats(template).totalSections }}
                  </span>
                </div>
                <div class="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/15 dark:bg-white/10 dark:text-white dark:hover:bg-white/20"
                    @click="openTemplatePreview(template)"
                  >
                    Visualizar
                  </button>
                  <button
                    type="button"
                    class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900"
                    @click="openTemplateEditDialog(template)"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    class="rounded-full border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-50 dark:border-red-400/40 dark:bg-red-500/10 dark:text-red-200"
                    :disabled="deletingTemplateId === template.id"
                    @click="handleDeleteTemplate(template)"
                  >
                    {{ deletingTemplateId === template.id ? "Excluindo..." : "Excluir" }}
                  </button>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>

      <div
        v-if="templateDialog.open"
        class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/70 px-4 py-8"
        @click.self="closeTemplateDialog"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl dark:bg-[#202020] dark:text-white">
          <h3 class="text-xl font-semibold text-slate-900 dark:text-white">
            {{ templateDialog.mode === "edit" ? "Editar modelo" : "Adicionar modelo" }}
          </h3>
          <p class="mt-1 text-sm text-slate-500 dark:text-white/70">
            {{
              templateDialog.mode === "edit"
                ? "Atualize o nome, slug e descrição do modelo."
                : "Defina o nome e o identificador público para este template."
            }}
          </p>
          <div class="mt-4 space-y-3">
            <div>
              <label class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">Nome</label>
              <input
                v-model="templateDialog.name"
                type="text"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand focus:outline-none dark:border-white/15 dark:bg-[#101010] dark:text-white"
              />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">Slug</label>
              <input
                v-model="templateDialog.slug"
                type="text"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand focus:outline-none dark:border-white/15 dark:bg-[#101010] dark:text-white"
                @input="handleTemplateSlugInput"
              />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">Descrição</label>
              <textarea
                v-model="templateDialog.description"
                rows="3"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand focus:outline-none dark:border-white/15 dark:bg-[#101010] dark:text-white"
                placeholder="Resumo do que este modelo entrega"
              ></textarea>
            </div>
            <p v-if="templateDialog.error" class="text-sm text-red-600 dark:text-red-300">
              {{ templateDialog.error }}
            </p>
          </div>
          <div class="mt-6 flex justify-end gap-2">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/15 dark:text-white"
              @click="closeTemplateDialog"
            >
              Cancelar
            </button>
            <button
              type="button"
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900"
              :disabled="templateDialog.saving"
              @click="submitTemplateDialog"
            >
              {{
                templateDialog.saving
                  ? "Salvando..."
                  : templateDialog.mode === "edit"
                    ? "Salvar alterações"
                    : "Salvar modelo"
              }}
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="templatePreviewDialog.open"
        class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/80 px-4 py-8"
        @click.self="closeTemplatePreview"
      >
        <div class="h-[90vh] w-full max-w-4xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl dark:bg-[#101010] dark:text-white">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.4em] text-slate-500 dark:text-white/60">Pr├®-visualiza├º├úo</p>
              <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
                {{ templatePreviewDialog.template?.name }}
              </h3>
            </div>
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/20 dark:text-white"
              @click="closeTemplatePreview"
            >
              Fechar
            </button>
          </div>
          <PageTemplatePreview
            v-if="templatePreviewConfig"
            :config="templatePreviewConfig"
            :branding="templatePreviewBranding"
          />
          <p v-else class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500 dark:border-white/15 dark:text-white/70">
            N├úo conseguimos renderizar este modelo.
          </p>
        </div>
      </div>
    </template>
  </div>

  <!-- SNACKBAR -->
  <transition name="fade">
    <div
      v-if="snackbar?.open"
      class="fixed bottom-6 right-6 z-50 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-2xl"
    >
      {{ snackbar.text }}
    </div>
  </transition>
 
  <!-- TRIAL MODAL -->
  <transition name="fade">
    <div
      v-if="trialDialog.open && trialDialog.user"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
    >
      <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Upgrade exclusivo</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">Liberar 7 dias do plano {{ planLabels.infinity }}</h2>

        <div class="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
          <p class="font-semibold text-slate-900">{{ trialDialog.user.name }}</p>
          <p class="text-xs text-slate-500">{{ trialDialog.user.email }}</p>

          <div class="mt-3 grid grid-cols-2 gap-3 text-xs">
            <div class="rounded-xl bg-white p-3 shadow-sm">
              <p class="text-slate-500">Plano atual</p>
              <p class="text-base font-semibold capitalize">{{ planLabel(trialDialog.user.plan) }}</p>
            </div>
            <div class="rounded-xl bg-white p-3 shadow-sm">
              <p class="text-slate-500">Validade atual</p>
              <p class="text-base font-semibold">{{ formatDate(trialDialog.user.valid_until) }}</p>
            </div>
          </div>
        </div>

        <p class="mt-5 text-sm text-slate-600">
          O usuário receber├í acesso total ao plano {{ planLabels.infinity }} por 7 dias. Enviaremos alertas no painel dele para aproveitar o período promocional.
        </p>

        <div class="mt-6 flex justify-end gap-3">
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            @click="closeTrialDialog"
          >
            Cancelar
          </button>

          <button
            class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            :disabled="granting === trialDialog.user.id"
            @click="grantTrial"
          >
            {{ granting === trialDialog.user.id ? "Processando..." : "Liberar agora" }}
          </button>
        </div>
      </div>
    </div>
  </transition>

  <!-- LINK PAGE MODAL -->
  <transition name="fade">
    <div
      v-if="linkPageDialog.open && linkPageDialog.user"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
    >
      <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-indigo-500">Vincular página</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">
          Escolha uma página para {{ linkPageDialog.user.name }}
        </h2>
        <p class="mt-2 text-sm text-slate-600">
          Selecionamos as páginas da sua Agência atual ({{ agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId)?.name || 'sem nome' }}).
          A c├│pia ser├í adicionada ├á Agência do usuário.
        </p>

          <div class="mt-5 space-y-4">
          <div
            v-if="linkPageDialog.loading"
            class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-600"
          >
            Carregando suas páginas...
          </div>
          <label
            v-else-if="linkPageDialog.pages.length"
            class="block text-sm font-semibold text-slate-700 dark:text-white"
          >
            Selecione a página base
            <select
              v-model="linkPageDialog.selectedPageId"
              class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm"
            >
              <option value="" disabled>Escolha uma página</option>
              <option
                v-for="page in linkPageDialog.pages"
                :key="page.id"
                :value="page.id"
              >
                {{ page.title }} ┬À {{ page.status === 'published' ? 'Publicada' : 'Rascunho' }}
              </option>
            </select>
          </label>
          <div
            v-else
            class="rounded-2xl border border-dashed border-slate-200 px-4 py-3 text-sm text-slate-500"
          >
            Nenhuma página encontrada na sua Agência atual. Crie uma página primeiro.
          </div>

          <label class="block text-sm font-semibold text-slate-700 dark:text-white">
            Nome do roteiro
            <input
              v-model="linkPageDialog.newTitle"
              type="text"
              class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm"
              placeholder="Digite o novo nome"
            />
          </label>

          <div class="rounded-2xl border border-dashed border-slate-200 px-3 py-2 text-xs text-slate-500">
            Slug sugerido: <span class="font-semibold text-slate-900">/{{ linkPageDialog.newSlug }}</span>
          </div>

          <p v-if="linkPageDialog.error" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600">
            {{ linkPageDialog.error }}
          </p>
        </div>

        <div class="mt-6 flex flex-wrap justify-end gap-3">
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            :disabled="linkPageDialog.saving"
            @click="closeLinkPageDialog"
          >
            Cancelar
          </button>
          <button
            class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-slate-800 disabled:opacity-60"
            :disabled="linkPageDialog.saving || !linkPageDialog.selectedPageId || !linkPageDialog.newTitle.trim()"
            @click="confirmLinkPage"
          >
            {{ linkPageDialog.saving ? "Publicando..." : "Publicar" }}
          </button>
        </div>
      </div>
    </div>
  </transition>

  <!-- DELETE USER MODAL -->
  <transition name="fade">
    <div
      v-if="deleteDialog.open && deleteDialog.user"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
    >
      <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">Excluir usuário</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">Remover {{ deleteDialog.user.name }}?</h2>
        <p class="mt-2 text-sm text-slate-600">
          Essa a├º├úo apaga a conta, Agências, páginas e registros de tracking vinculados. Ela n├úo pode ser desfeita.
        </p>
        <p
          v-if="deleteDialog.error"
          class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600"
        >
          {{ deleteDialog.error }}
        </p>
        <div class="mt-6 flex flex-wrap justify-end gap-3">
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            :disabled="deleteDialog.loading"
            @click="closeDeleteDialog"
          >
            Cancelar
          </button>
          <button
            class="rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-red-500 disabled:opacity-60"
            :disabled="deleteDialog.loading"
            @click="confirmDeleteUser"
          >
            {{ deleteDialog.loading ? "Excluindo..." : "Excluir usuário" }}
          </button>
        </div>
      </div>
    </div>
  </transition>

  <!-- REFUND USER MODAL -->
  <transition name="fade">
    <div
      v-if="refundDialog.open && refundDialog.user"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
    >
      <div class="w-full max-w-xl rounded-3xl bg-white p-8 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-600">Reembolsar usuário</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">Reembolsar {{ refundDialog.user.name }}?</h2>
        <p class="mt-2 text-sm text-slate-600">
          Ao confirmar, vamos acionar o reembolso na Cakto, cancelar a assinatura, despublicar todas as páginas deste cliente
          e bloquear o acesso imediatamente. Essa a├º├úo n├úo pode ser desfeita.
        </p>
        <p
          v-if="refundDialog.error"
          class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600"
        >
          {{ refundDialog.error }}
        </p>
        <div class="mt-6 flex flex-wrap justify-end gap-3">
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            :disabled="refundDialog.loading"
            @click="closeRefundDialog"
          >
            Cancelar
          </button>
          <button
            class="rounded-full bg-amber-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-amber-500 disabled:opacity-60"
            :disabled="refundDialog.loading"
            @click="confirmRefund"
          >
            {{ refundDialog.loading ? "Processando..." : "Confirmar reembolso" }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch, computed } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { useAgencyStore } from "../../store/useAgencyStore";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { getPlanLabel, planLabels } from "../../utils/planLabels";
import { normalizeVideoInput, useLessonsStore, type Lesson } from "../../store/useLessonsStore";
import { slugify } from "../../utils/slugify";
import PageTemplatePreview from "../../components/admin/PageTemplatePreview.vue";
import { listPageTemplates, createTemplateFromPage, deleteTemplate, updateTemplate } from "../../services/templates";
import type { PageTemplate } from "../../types/templates";
import { applyTemplateBranding, summarizeTemplate } from "../../utils/pageTemplates";
import { sanitizeDigits, buildWhatsappLink } from "../../utils/whatsapp";

interface MetricsUserPage {
  id: number;
  title: string;
  slug: string;
  status: string;
  total_visits?: number;
  total_cta_clicks?: number;
  agency_slug?: string | null;
}

interface MetricsUserTracking {
  id: number;
  utm_source?: string | null;
  utm_medium?: string | null;
  utm_campaign?: string | null;
  utm_term?: string | null;
  utm_content?: string | null;
  referrer?: string | null;
  created_at?: string | null;
}

interface Metrics {
  total_users: number;
  total_agencies: number;
  total_pages: number;
  published_pages: number;
  mrr: number;
  total_revenue?: number;
  lifetime_revenue?: number;
  new_users_last_days: number;
  plans: { plan: string; count: number }[];
  new_users_timeseries: { label: string; value: number }[];
  users: {
    id: number;
    name: string;
    email: string;
    plan: string;
    is_active: boolean;
    is_superuser: boolean;
    created_at?: string;
    valid_until?: string;
    trial_plan?: string | null;
    trial_ends_at?: string | null;
    agency_id?: number | null;
    agency_name?: string | null;
    agency_slug?: string | null;
    active_pages?: number | null;
    whatsapp?: string | null;
    published_pages?: MetricsUserPage[];
    draft_pages?: MetricsUserPage[];
    draft_pages_count?: number | null;
    tracking?: MetricsUserTracking[];
    subscription_provider?: string | null;
    subscription_status?: string | null;
    subscription_cakto_order_id?: string | null;
    subscription_cakto_subscription_code?: string | null;
  }[];
  agencies: {
    id: number;
    name: string;
    slug: string;
    created_at?: string;
    pages_count: number;
  }[];
  pages: {
    id: number;
    title: string;
    agency_name: string;
    status: string;
    created_at?: string;
    published_at?: string;
  }[];
}

type AdminAgencySummary = Metrics["agencies"][number];

interface AdminOnlineSession {
  session_id: string;
  user_id: number;
  user_name: string;
  user_email: string;
  user_plan: string;
  ip_address?: string | null;
  device_label?: string | null;
  client_name?: string | null;
  created_at: string;
  last_seen_at: string;
  active_sessions: number;
  last_path?: string | null;
}

interface AdminOnlineSessionsResponse {
  sessions: AdminOnlineSession[];
  total_online: number;
  unique_users: number;
  generated_at: string;
}

type AdminTab = "dashboard" | "monitor" | "users" | "lessons" | "templates";
type TemplateDialogMode = "create" | "edit";

const adminTabs: { id: AdminTab; label: string; description: string }[] = [
  { id: "dashboard", label: "Dashboard", description: "Resumo e métricas" },
  { id: "monitor", label: "Monitor", description: "Sessões online" },
  { id: "users", label: "Usuários", description: "Perfis e status" },
  { id: "lessons", label: "Gestão de aulas", description: "Treinamentos públicos" },
  { id: "templates", label: "Templates", description: "Modelos oficiais" }
];

type AdminPeriodOption = "7" | "30" | "90" | "custom";
const days = ref<AdminPeriodOption>("30");
const metrics = ref<Metrics | null>(null);
const isMobile = ref(false);
const customStartDate = ref("");
const customEndDate = ref("");
const arrValue = computed(() => {
  const mrrValue = metrics.value?.mrr;
  return typeof mrrValue === "number" ? mrrValue * 12 : null;
});
const lifetimeRevenue = computed(() => {
  const value = metrics.value?.total_revenue ?? metrics.value?.lifetime_revenue ?? null;
  return typeof value === "number" ? value : null;
});
const newUsersSeries = computed(() => metrics.value?.new_users_timeseries ?? []);

const onlineSessions = ref<AdminOnlineSession[]>([]);
const onlineSessionsMeta = ref<AdminOnlineSessionsResponse | null>(null);
const onlineSessionsLoading = ref(false);
const onlineSessionsError = ref("");
const revokingUserId = ref<number | null>(null);
let onlineSessionsInterval: number | null = null;
const monitorStatusLabel = computed(() => (onlineSessionsLoading.value ? "Atualizando" : "Operacional"));
const monitorLastUpdated = computed(() => {
  const value = onlineSessionsMeta.value?.generated_at;
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
});
const NEW_USERS_CHART_HEIGHT = 240;
const NEW_USERS_CHART_WIDTH = 640;
const NEW_USERS_CHART_PADDING_Y = 28;
const NEW_USERS_CHART_PADDING_X = 28;
const newUsersChartHeight = NEW_USERS_CHART_HEIGHT;
const newUsersChartWidth = NEW_USERS_CHART_WIDTH;
const newUsersChartInnerHeight = NEW_USERS_CHART_HEIGHT - NEW_USERS_CHART_PADDING_Y * 2;
const newUsersChartInnerWidth = NEW_USERS_CHART_WIDTH - NEW_USERS_CHART_PADDING_X * 2;
const newUsersGridLineRatios = [0.2, 0.4, 0.6, 0.8];
const newUsersGridLines = computed(() =>
  newUsersGridLineRatios.map((ratio) => NEW_USERS_CHART_PADDING_Y + ratio * newUsersChartInnerHeight)
);
const isCustomAdminPeriod = computed(() => days.value === "custom");
const adminCustomRangeReady = computed(
  () => isCustomAdminPeriod.value && Boolean(customStartDate.value) && Boolean(customEndDate.value)
);
const adminOrderedRange = computed(() => {
  if (!adminCustomRangeReady.value) return null;
  const start = new Date(customStartDate.value);
  const end = new Date(customEndDate.value);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  if (start.getTime() <= end.getTime()) {
    return { startISO: customStartDate.value, endISO: customEndDate.value, startDate: start, endDate: end };
  }
  return { startISO: customEndDate.value, endISO: customStartDate.value, startDate: end, endDate: start };
});
const adminPeriodDays = computed(() => {
  if (adminOrderedRange.value) {
    const diff =
      Math.floor(
        (adminOrderedRange.value.endDate.getTime() - adminOrderedRange.value.startDate.getTime()) /
          (1000 * 60 * 60 * 24)
      ) + 1;
    return Math.max(diff, 1);
  }
  return Number(days.value) || 30;
});
const adminPeriodLabel = computed(() => {
  if (adminOrderedRange.value) {
    return `${formatDate(adminOrderedRange.value.startISO)} a ${formatDate(adminOrderedRange.value.endISO)}`;
  }
  if (isCustomAdminPeriod.value) {
    return "período personalizado";
  }
  return `Ultimos ${adminPeriodDays.value} dias`;
});
const newUsersMaxValue = computed(() => {
  if (!newUsersSeries.value.length) return 1;
  const maxValue = Math.max(...newUsersSeries.value.map((point) => point.value ?? 0));
  return maxValue > 0 ? maxValue : 1;
});
const newUsersPoints = computed(() => {
  const series = newUsersSeries.value;
  if (!series.length) return [];
  const safeMax = newUsersMaxValue.value > 0 ? newUsersMaxValue.value : 1;
  const count = series.length;
  const step = count > 1 ? newUsersChartInnerWidth / (count - 1) : newUsersChartInnerWidth;
  const baseWidth =
    count > 1 ? Math.max(8, Math.min(32, step * 0.7)) : Math.min(96, newUsersChartInnerWidth * 0.35);
  return series.map((point, index) => {
    const value = point.value ?? 0;
    const ratio = value / safeMax;
    const centerX = count === 1 ? NEW_USERS_CHART_WIDTH / 2 : NEW_USERS_CHART_PADDING_X + index * step;
    const barHeight = ratio * newUsersChartInnerHeight;
    const y = NEW_USERS_CHART_PADDING_Y + (newUsersChartInnerHeight - barHeight);
    const barX = centerX - baseWidth / 2;
    return {
      label: point.label,
      value,
      centerX,
      y,
      barX,
      barWidth: baseWidth,
      barHeight
    };
  });
});
const newUsersSurfaceRef = ref<HTMLDivElement | null>(null);
const newUsersHoverPoint = ref<{ label: string; value: number; centerX: number; y: number } | null>(null);
const newUsersTooltipStyle = computed(() => {
  if (!newUsersHoverPoint.value) return { opacity: 0 };
  const padding = 60;
  const left = Math.min(
    Math.max(newUsersHoverPoint.value.centerX, padding),
    NEW_USERS_CHART_WIDTH - padding
  );
  const top = Math.max(newUsersHoverPoint.value.y - 60, 16);
  return { left: `${left}px`, top: `${top}px`, opacity: 1 };
});
const handleNewUsersMove = (event: MouseEvent) => {
  const surface = newUsersSurfaceRef.value;
  const points = newUsersPoints.value;
  if (!surface || !points.length) return;
  const rect = surface.getBoundingClientRect();
  const offsetX = event.clientX - rect.left;
  let nearest = points[0];
  let distance = Math.abs(offsetX - nearest.centerX);
  for (const point of points) {
    const diff = Math.abs(offsetX - point.centerX);
    if (diff < distance) {
      nearest = point;
      distance = diff;
    }
  }
  newUsersHoverPoint.value = nearest;
};
const clearNewUsersHover = () => {
  newUsersHoverPoint.value = null;
};
const compactNewUsersLabels = computed(() => isMobile.value || adminPeriodDays.value >= 14);
const newUsersLabelRange = computed(() => {
  if (!compactNewUsersLabels.value || newUsersSeries.value.length < 2) return null;
  const first = newUsersSeries.value[0]?.label || "";
  const last = newUsersSeries.value[newUsersSeries.value.length - 1]?.label || "";
  return { start: first, end: last };
});
const updateIsMobile = () => {
  if (typeof window === "undefined") return;
  isMobile.value = window.matchMedia("(max-width: 768px)").matches;
  if (openFilterKey.value) {
    updatePopoverPosition(openFilterKey.value);
  }
};
const error = ref("");
const auth = useAuthStore();
const agencyStore = useAgencyStore();
const router = useRouter();
const granting = ref<number | null>(null);
const snackbar = ref<{ open: boolean; text: string } | null>(null);
const trialDialog = ref<{ open: boolean; user: any | null }>({ open: false, user: null });
const deleteDialog = ref<{
  open: boolean;
  user: Metrics["users"][number] | null;
  loading: boolean;
  error: string;
}>({
  open: false,
  user: null,
  loading: false,
  error: ""
});
const refundDialog = ref<{
  open: boolean;
  user: Metrics["users"][number] | null;
  loading: boolean;
  error: string;
}>({
  open: false,
  user: null,
  loading: false,
  error: ""
});
const linkPageDialog = ref<{
  open: boolean;
  user: Metrics["users"][number] | null;
  pages: AdminPageSummary[];
  selectedPageId: number | null;
  newTitle: string;
  newSlug: string;
  saving: boolean;
  loading: boolean;
  error: string;
}>({
  open: false,
  user: null,
  pages: [],
  selectedPageId: null,
  newTitle: "",
  newSlug: "",
  saving: false,
  loading: false,
  error: ""
});
const templateAgencyId = ref<number | null>(null);
const templateAgencyOptions = ref<AdminAgencySummary[]>([]);
const templateAgencySearch = ref("");
const templateAgencyDropdownOpen = ref(false);
const templateAgencyLoading = ref(false);
const templateAgencyError = ref("");
const templateAgencyFetchedOnce = ref(false);
const templateAgencySearchInput = ref<HTMLInputElement | null>(null);
let templateAgencySearchDebounce: ReturnType<typeof setTimeout> | null = null;
let templateAgencySearchRequestId = 0;
let skipTemplateAgencySearchWatcher = false;
const templatePages = ref<AdminPageSummary[]>([]);
const templatePagesLoading = ref(false);
const templatePagesError = ref("");
const pageTemplates = ref<PageTemplate[]>([]);
const pageTemplatesLoading = ref(false);
const pageTemplatesError = ref("");
const deletingTemplateId = ref<number | null>(null);
const templateDialog = reactive({
  open: false,
  mode: "create" as TemplateDialogMode,
  page: null as AdminPageSummary | null,
  templateId: null as number | null,
  name: "",
  slug: "",
  description: "",
  error: "",
  saving: false
});
const templateSlugAuto = ref("");
const templatePreviewDialog = reactive({
  open: false,
  template: null as PageTemplate | null
});
const updateTemplateAgencySearchLabel = (value: string) => {
  skipTemplateAgencySearchWatcher = true;
  templateAgencySearch.value = value;
};
const fetchTemplateAgencies = async (term?: string) => {
  const requestId = ++templateAgencySearchRequestId;
  templateAgencyLoading.value = true;
  templateAgencyError.value = "";
  const params: Record<string, string | number> = { limit: 40 };
  const query = term?.trim();
  if (query) {
    params.q = query;
  }
  try {
    const { data } = await api.get<AdminAgencySummary[]>("/admin/agencies/search", { params });
    if (requestId === templateAgencySearchRequestId) {
      templateAgencyOptions.value = data || [];
      templateAgencyFetchedOnce.value = true;
    }
  } catch (err: any) {
    console.error(err);
    if (requestId === templateAgencySearchRequestId) {
      templateAgencyError.value = err?.response?.data?.detail || "N├úo foi poss├¡vel buscar Agências.";
      templateAgencyOptions.value = [];
    }
  } finally {
    if (requestId === templateAgencySearchRequestId) {
      templateAgencyLoading.value = false;
    }
  }
};
const ensureTemplateAgencyOptions = () => {
  if (!templateAgencyFetchedOnce.value && !templateAgencyLoading.value) {
    void fetchTemplateAgencies(templateAgencySearch.value);
  }
};
const openTemplateAgencyDropdown = () => {
  templateAgencyDropdownOpen.value = true;
  ensureTemplateAgencyOptions();
};
const toggleTemplateAgencyDropdown = () => {
  if (templateAgencyDropdownOpen.value) {
    templateAgencyDropdownOpen.value = false;
    return;
  }
  openTemplateAgencyDropdown();
  templateAgencySearchInput.value?.focus();
};
const handleTemplateAgencyInputFocus = () => {
  openTemplateAgencyDropdown();
};
const selectTemplateAgency = (agency: AdminAgencySummary) => {
  templateAgencyId.value = agency.id;
  updateTemplateAgencySearchLabel(agency.name);
  templateAgencyDropdownOpen.value = false;
};
const premiumMode = computed(() => (auth.user?.plan || "").toLowerCase() === "infinity");
const activeTab = ref<AdminTab>("dashboard");
const tabButtonClass = (tab: AdminTab) =>
  activeTab.value === tab
    ? "bg-slate-900 text-white shadow-lg shadow-slate-900/30 dark:bg-white dark:text-slate-900"
    : "border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:text-white/80 dark:hover:bg-white/5";
const selectedTemplateAgency = computed(() => {
  return templateAgencyOptions.value.find(agency => agency.id === templateAgencyId.value) || null;
});
const templatePublicUrl = (page: AdminPageSummary) => {
  const agencySlug = selectedTemplateAgency.value?.slug;
  if (!agencySlug) return "";
  return `/${agencySlug}/${page.slug}`;
};
const loadTemplatePages = async () => {
  if (!templateAgencyId.value) {
    templatePages.value = [];
    return;
  }
  try {
    templatePagesLoading.value = true;
    templatePagesError.value = "";
    const { data } = await api.get<AdminPageSummary[]>("/pages", {
      params: { agency_id: templateAgencyId.value }
    });
    templatePages.value = data || [];
  } catch (err: any) {
    console.error(err);
    templatePagesError.value = err?.response?.data?.detail || "N├úo foi poss├¡vel carregar as páginas.";
  } finally {
    templatePagesLoading.value = false;
  }
};
const loadTemplates = async () => {
  try {
    pageTemplatesLoading.value = true;
    pageTemplatesError.value = "";
    pageTemplates.value = await listPageTemplates();
  } catch (err: any) {
    console.error(err);
    pageTemplatesError.value = err?.response?.data?.detail || "N├úo foi poss├¡vel carregar os modelos.";
  } finally {
    pageTemplatesLoading.value = false;
  }
};
const openTemplateCreateDialog = (page: AdminPageSummary) => {
  templateDialog.mode = "create";
  templateDialog.templateId = null;
  templateDialog.page = page;
  templateDialog.name = page.title;
  templateDialog.slug = slugify(page.title, "modelo");
  templateDialog.description = "";
  templateDialog.error = "";
  templateDialog.saving = false;
  templateSlugAuto.value = templateDialog.slug;
  templateDialog.open = true;
};
const closeTemplateDialog = () => {
  templateDialog.open = false;
  templateDialog.mode = "create";
  templateDialog.page = null;
  templateDialog.templateId = null;
  templateDialog.name = "";
  templateDialog.slug = "";
  templateDialog.description = "";
  templateDialog.error = "";
  templateDialog.saving = false;
  templateSlugAuto.value = "";
};
const handleTemplateSlugInput = () => {
  templateSlugAuto.value = templateDialog.slug;
};
const submitTemplateDialog = async () => {
  const name = templateDialog.name.trim();
  const slug = templateDialog.slug.trim();
  if (!name || !slug) {
    templateDialog.error = "Informe nome e slug do template.";
    return;
  }
  templateDialog.saving = true;
  templateDialog.error = "";
  try {
    if (templateDialog.mode === "edit") {
      if (!templateDialog.templateId) {
        templateDialog.error = "Modelo inválido.";
        templateDialog.saving = false;
        return;
      }
      await updateTemplate(templateDialog.templateId, {
        name,
        slug,
        description: templateDialog.description.trim() || null
      });
      showSnackbar("Modelo atualizado com sucesso.");
    } else {
      if (!templateDialog.page) {
        templateDialog.error = "Selecione uma página para criar o modelo.";
        templateDialog.saving = false;
        return;
      }
      await createTemplateFromPage({
        page_id: templateDialog.page.id,
        name,
        slug,
        description: templateDialog.description.trim() || undefined
      });
      showSnackbar("Modelo criado com sucesso.");
    }
    closeTemplateDialog();
    await loadTemplates();
  } catch (err: any) {
    console.error(err);
    templateDialog.error =
      err?.response?.data?.detail ||
      (templateDialog.mode === "edit" ? "Não foi possível atualizar o modelo." : "Não foi possível criar o modelo.");
    templateDialog.saving = false;
  }
};
const openTemplatePreview = (template: PageTemplate) => {
  templatePreviewDialog.template = template;
  templatePreviewDialog.open = true;
};
const closeTemplatePreview = () => {
  templatePreviewDialog.open = false;
  templatePreviewDialog.template = null;
};
const openTemplateEditDialog = (template: PageTemplate) => {
  templateDialog.mode = "edit";
  templateDialog.page = null;
  templateDialog.templateId = template.id;
  templateDialog.name = template.name;
  templateDialog.slug = template.slug;
  templateDialog.description = template.description || "";
  templateDialog.error = "";
  templateDialog.saving = false;
  templateSlugAuto.value = templateDialog.slug;
  templateDialog.open = true;
};
const handleDeleteTemplate = async (template: PageTemplate) => {
  if (deletingTemplateId.value) return;
  const confirmed = window.confirm(`Deseja realmente excluir o modelo "${template.name}"?`);
  if (!confirmed) return;
  try {
    deletingTemplateId.value = template.id;
    await deleteTemplate(template.id);
    pageTemplates.value = pageTemplates.value.filter(item => item.id !== template.id);
    showSnackbar("Modelo removido com sucesso.");
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail || "N├úo foi poss├¡vel remover o modelo.";
    showSnackbar(detail);
  } finally {
    deletingTemplateId.value = null;
  }
};
const previewAgency = computed(() => selectedTemplateAgency.value || agencyStore.agencies[0] || null);
const previewWhatsappDigits = computed(() => {
  const agencyDigits = sanitizeDigits(previewAgency.value?.cta_whatsapp || "");
  if (agencyDigits) return agencyDigits;
  return sanitizeDigits(auth.user?.whatsapp || "");
});
const templatePreviewBranding = computed(() => {
  const agency = previewAgency.value;
  return {
    agency_name: agency?.name || "Sua Agência",
    logo_url: agency?.logo_url || "",
    primary_color: agency?.primary_color || "#0f172a",
    secondary_color: agency?.secondary_color || agency?.primary_color || "#1f2937",
    whatsapp_link: templatePreviewDialog.template
      ? buildWhatsappLink(previewWhatsappDigits.value, templatePreviewDialog.template.name)
      : ""
  };
});
const templatePreviewConfig = computed(() => {
  if (!templatePreviewDialog.template) return null;
  return applyTemplateBranding(templatePreviewDialog.template.config_json, {
    logoUrl: templatePreviewBranding.value.logo_url,
    whatsappLink: templatePreviewBranding.value.whatsapp_link,
    primaryColor: templatePreviewBranding.value.primary_color,
    enforcePrimaryColor: !!templatePreviewBranding.value.primary_color
  });
});
const templateStats = (template: PageTemplate) => summarizeTemplate(template);

type UserColumnKey = "name" | "agency_name" | "active_pages" | "draft_pages" | "plan" | "valid_until" | "created_at";
interface UserColumn {
  key: UserColumnKey;
  label: string;
  align?: "left" | "right";
  sortable?: boolean;
}

const userTableColumns: UserColumn[] = [
  { key: "name", label: "Nome", sortable: true },
  { key: "agency_name", label: "Agência", sortable: true },
  { key: "active_pages", label: "Qtd páginas ativas", align: "right", sortable: true },
  { key: "draft_pages", label: "Qtd páginas rascunho", align: "right", sortable: true },
  { key: "plan", label: "Plano", sortable: true },
  { key: "valid_until", label: "Validade", sortable: true },
  { key: "created_at", label: "Entrada", sortable: true }
];

const userFilters = reactive({
  name: "",
  agencies: [] as string[],
  plans: [] as string[],
  activeMin: "",
  activeMax: "",
  draftMin: "",
  draftMax: "",
  validFrom: "",
  validTo: "",
  createdFrom: "",
  createdTo: ""
});
const userSort = reactive<{ key: UserColumnKey; direction: "asc" | "desc" }>({
  key: "created_at",
  direction: "desc"
});
const openFilterKey = ref<UserColumnKey | null>(null);
const filterButtonRefs = ref<Record<UserColumnKey, HTMLElement | null>>({
  name: null,
  agency_name: null,
  active_pages: null,
  draft_pages: null,
  plan: null,
  valid_until: null,
  created_at: null
});
const filterPopoverPosition = reactive({ left: 0, top: 0 });
const filterPopoverWidth = 268;
const filterPopoverStyle = computed(() => ({
  left: `${filterPopoverPosition.left}px`,
  top: `${filterPopoverPosition.top}px`,
  width: `${filterPopoverWidth}px`
}));
const resetFilterSearch = (key: UserColumnKey) => {
  if (key === "agency_name") {
    agencyFilterSearch.value = "";
  }
};
const userPage = ref(1);
const userPageSizeOptions = [10, 25, 50];
const userPageSize = ref(10);
const expandedUser = ref<number | null>(null);
const savingPageId = ref<number | null>(null);
const lessonsStore = useLessonsStore();
const adminLessons = computed(() => lessonsStore.sortedLessons);
const lessonsLoading = computed(() => lessonsStore.loading);
const lessonSaving = ref(false);
const deletingLessonId = ref<number | null>(null);
const resettingLessons = ref(false);
const lessonForm = reactive({
  title: "",
  description: "",
  duration: "",
  level: "",
  videoInput: "",
  thumbnailUrl: "",
  thumbnailData: "",
  thumbnailUploadName: ""
});
const editingLessonId = ref<number | null>(null);
const isEditingLesson = computed(() => editingLessonId.value !== null);
const lessonPreview = computed(() => normalizeVideoInput(lessonForm.videoInput || ""));

const utmFieldMap: { key: keyof MetricsUserTracking; label: string }[] = [
  { key: "utm_source", label: "Fonte" },
  { key: "utm_medium", label: "M├¡dia" },
  { key: "utm_campaign", label: "Campanha" },
  { key: "utm_term", label: "Termo" },
  { key: "utm_content", label: "Conteúdoo" },
  { key: "referrer", label: "Referrer" }
];

const buildUtmChips = (entry: MetricsUserTracking) => {
  return utmFieldMap
    .map(field => {
      const value = entry[field.key];
      if (!value) return null;
      return { label: field.label, value };
    })
    .filter((item): item is { label: string; value: string } => Boolean(item));
};

const loadMetrics = async () => {
  error.value = "";
  if (days.value === "custom" && !adminOrderedRange.value) {
    return;
  }
  try {
    const params: Record<string, string | number> = {};
    if (adminOrderedRange.value) {
      params.start_date = adminOrderedRange.value.startISO;
      params.end_date = adminOrderedRange.value.endISO;
    } else {
      params.days = Number(days.value);
    }
    const res = await api.get("/admin/metrics", { params });
    metrics.value = res.data;
  } catch (err: any) {
    metrics.value = null;
    if (err?.response?.status === 403) {
      error.value = "Acesso restrito a administradores.";
    } else {
      error.value = "Nao foi possivel carregar os dados.";
    }
  }
};

const formatDate = (val?: string) => {
  if (!val) return "--";
  const d = new Date(val);
  if (isNaN(d.getTime())) return "--";
  return d.toLocaleDateString();
};

const formatDateTime = (val?: string) => {
  if (!val) return "--";
  const d = new Date(val);
  if (isNaN(d.getTime())) return "--";
  const date = d.toLocaleDateString();
  const time = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return `${date} ${time}`;
};

const formatClock = (val?: string | null) => {
  if (!val) return "--";
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return "--";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

const formatRelativeMoment = (val?: string | null) => {
  if (!val) return "--";
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return "--";
  const diff = Date.now() - d.getTime();
  if (diff < 30_000) return "há instantes";
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "há instantes";
  if (minutes < 60) return `há ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `há ${hours} h`;
  const days = Math.floor(hours / 24);
  return `há ${days} d`;
};

const formatDurationSince = (val?: string | null) => {
  if (!val) return "--";
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return "--";
  const diff = Date.now() - d.getTime();
  if (diff < 60_000) return "Ativo há instantes";
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `Ativo há ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Ativo há ${hours} h`;
  const days = Math.floor(hours / 24);
  return `Ativo há ${days} d`;
};

const showSnackbar = (text: string) => {
  snackbar.value = { open: true, text };
  setTimeout(() => {
    snackbar.value = null;
  }, 3000);
};

const loadOnlineSessions = async (notify = false) => {
  try {
    onlineSessionsLoading.value = true;
    onlineSessionsError.value = "";
    const { data } = await api.get<AdminOnlineSessionsResponse>("/admin/online-sessions");
    onlineSessions.value = data.sessions;
    onlineSessionsMeta.value = data;
    if (notify) {
      showSnackbar("Monitor atualizado.");
    }
  } catch (err: any) {
    console.error(err);
    const message = err?.response?.data?.detail || "N├úo foi poss├¡vel carregar o monitor agora.";
    onlineSessionsError.value = message;
    if (notify) {
      showSnackbar(message);
    }
  } finally {
    onlineSessionsLoading.value = false;
  }
};

const startOnlineSessionsPolling = () => {
  if (typeof window === "undefined") return;
  if (onlineSessionsInterval) {
    window.clearInterval(onlineSessionsInterval);
  }
  onlineSessionsInterval = window.setInterval(() => {
    if (activeTab.value === "monitor") {
      loadOnlineSessions();
    }
  }, 20000);
};

const stopOnlineSessionsPolling = () => {
  if (typeof window === "undefined") return;
  if (onlineSessionsInterval) {
    window.clearInterval(onlineSessionsInterval);
    onlineSessionsInterval = null;
  }
};

const revokeUserSessions = async (session: AdminOnlineSession) => {
  if (revokingUserId.value) return;
  revokingUserId.value = session.user_id;
  try {
    await api.post(`/admin/online-sessions/user/${session.user_id}/revoke`);
    showSnackbar(`Sess├Áes de ${session.user_name} encerradas.`);
    await loadOnlineSessions();
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail || "N├úo foi poss├¡vel deslogar este usuário.";
    showSnackbar(detail);
  } finally {
    revokingUserId.value = null;
  }
};

const handleThumbnailUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    showSnackbar("Envie apenas imagens.");
    input.value = "";
    return;
  }
  const maxSize = 4 * 1024 * 1024;
  if (file.size > maxSize) {
    showSnackbar("Imagem muito grande (m├íximo 4MB).");
    input.value = "";
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    lessonForm.thumbnailData = reader.result as string;
    lessonForm.thumbnailUploadName = file.name;
    lessonForm.thumbnailUrl = "";
  };
  reader.readAsDataURL(file);
};

const clearThumbnailUpload = () => {
  lessonForm.thumbnailData = "";
  lessonForm.thumbnailUploadName = "";
};

const resetLessonForm = () => {
  editingLessonId.value = null;
  lessonForm.title = "";
  lessonForm.description = "";
  lessonForm.duration = "";
  lessonForm.level = "";
  lessonForm.videoInput = "";
  lessonForm.thumbnailUrl = "";
  lessonForm.thumbnailData = "";
  lessonForm.thumbnailUploadName = "";
};

const startLessonEdit = (lesson: Lesson) => {
  editingLessonId.value = lesson.id;
  lessonForm.title = lesson.title;
  lessonForm.description = lesson.description;
  lessonForm.duration = lesson.duration;
  lessonForm.level = lesson.level;
  lessonForm.videoInput = lesson.videoUrl;
  const isDataUrl = Boolean(lesson.thumbnail?.startsWith("data:"));
  lessonForm.thumbnailUrl = isDataUrl ? "" : lesson.thumbnail || "";
  lessonForm.thumbnailData = isDataUrl ? lesson.thumbnail || "" : "";
  lessonForm.thumbnailUploadName = isDataUrl ? "Imagem enviada" : "";
};

const saveLesson = async () => {
  if (!lessonForm.title.trim() || !lessonForm.videoInput.trim()) {
    showSnackbar("Informe Título e link do v├¡deo.");
    return;
  }
  const parsed = normalizeVideoInput(lessonForm.videoInput);
  if (!parsed.videoUrl) {
    showSnackbar("Link de v├¡deo inv├ílido.");
    return;
  }
  const payload = {
    title: lessonForm.title.trim(),
    description: lessonForm.description.trim(),
    duration: lessonForm.duration.trim(),
    level: lessonForm.level.trim(),
    videoType: parsed.videoType,
    videoUrl: parsed.videoUrl,
    thumbnailUrl: lessonForm.thumbnailUrl || undefined,
    thumbnailBase64: lessonForm.thumbnailData || undefined
  };
  lessonSaving.value = true;
  try {
    if (editingLessonId.value) {
      await lessonsStore.updateLesson(editingLessonId.value, payload);
      showSnackbar("Aula atualizada.");
    } else {
      await lessonsStore.addLesson(payload);
      showSnackbar("Aula adicionada.");
    }
    resetLessonForm();
  } catch (err) {
    console.error(err);
    showSnackbar("N├úo foi poss├¡vel salvar a aula.");
  } finally {
    lessonSaving.value = false;
  }
};

const deleteLesson = async (lessonId: number) => {
  if (!confirm("Deseja remover esta aula?")) return;
  deletingLessonId.value = lessonId;
  try {
    await lessonsStore.deleteLesson(lessonId);
    if (editingLessonId.value === lessonId) {
      resetLessonForm();
    }
    showSnackbar("Aula removida.");
  } catch (err) {
    console.error(err);
    showSnackbar("N├úo foi poss├¡vel remover a aula.");
  } finally {
    deletingLessonId.value = null;
  }
};

const handleResetLessons = () => {
  if (!confirm("Restaurar a lista padr├úo de aulas?")) return;
  lessonsStore.resetLessons();
  resetLessonForm();
  showSnackbar("Aulas restauradas.");
};

const viewPublishedPage = (page: MetricsUserPage) => {
  if (!page.agency_slug) {
    showSnackbar("página sem Agência vinculada.");
    return;
  }
  const url = `/${page.agency_slug}/${page.slug}`;
  window.open(url, "_blank", "noopener,noreferrer");
};

const clonePublishedPage = async (user: Metrics["users"][number], page: MetricsUserPage) => {
  if (!agencyStore.currentAgencyId) {
    showSnackbar("Selecione uma Agência para salvar a página.");
    return;
  }
  savingPageId.value = page.id;
  try {
    await api.post(`/admin/pages/${page.id}/clone`, {
      target_agency_id: agencyStore.currentAgencyId,
      title: `${page.title} - ${user.name}`.trim()
    });
    showSnackbar("página salva na Agência selecionada.");
  } catch (err) {
    console.error(err);
    showSnackbar("N├úo foi poss├¡vel salvar esta página.");
  } finally {
    savingPageId.value = null;
  }
};

const goToPageEditor = (page: MetricsUserPage) => {
  router.push({ name: "page-edit", params: { id: page.id } });
};

const userPlanOptions = computed(() => {
  const plans = new Set<string>();
  metrics.value?.users?.forEach(user => {
    if (user.plan) plans.add(user.plan);
  });
  return Array.from(plans).sort();
});

const userAgencyOptions = computed(() => {
  const agencies = new Set<string>();
  metrics.value?.users?.forEach(user => {
    if (user.agency_name) agencies.add(user.agency_name);
  });
  return Array.from(agencies).sort();
});

const setFilterButtonRef = (key: UserColumnKey, el: HTMLElement | null) => {
  if (!el) return;
  filterButtonRefs.value[key] = el;
};

const agencyFilterOptions = computed(() => {
  const base = userAgencyOptions.value.map(name => ({ value: name, label: name }));
  return [{ value: "__none", label: "Sem Agência" }, ...base];
});
const agencyFilterSearch = ref("");
const filteredAgencyFilterOptions = computed(() => {
  const term = agencyFilterSearch.value.trim().toLowerCase();
  if (!term) return agencyFilterOptions.value;
  return agencyFilterOptions.value.filter(option => option.label.toLowerCase().includes(term));
});

const coerceNumber = (value: string) => {
  if (value === "" || value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const matchesNumberRange = (value: number, min: number | null, max: number | null) => {
  if (min !== null && value < min) return false;
  if (max !== null && value > max) return false;
  return true;
};

const matchesDateRange = (target: string | null | undefined, from: string, to: string) => {
  if (!from && !to) return true;
  const targetTime = target ? new Date(target).getTime() : null;
  const fromTime = from ? new Date(from).getTime() : null;
  const toTime = to ? new Date(to).getTime() : null;
  if (fromTime !== null && (targetTime === null || targetTime < fromTime)) return false;
  if (toTime !== null && (targetTime === null || targetTime > toTime)) return false;
  return true;
};

const baseFilteredUsers = computed(() => {
  const list = metrics.value?.users || [];
  const nameTerm = userFilters.name.trim().toLowerCase();
  const selectedAgencies = userFilters.agencies;
  const selectedPlans = userFilters.plans;
  const activeMin = coerceNumber(userFilters.activeMin);
  const activeMax = coerceNumber(userFilters.activeMax);
  const draftMin = coerceNumber(userFilters.draftMin);
  const draftMax = coerceNumber(userFilters.draftMax);

  return list.filter(user => {
    const matchesName =
      !nameTerm ||
      [user.name, user.email]
        .filter(Boolean)
        .some(field => field!.toLowerCase().includes(nameTerm));

    const agencyKey = user.agency_name || "__none";
    const matchesAgency = !selectedAgencies.length || selectedAgencies.includes(agencyKey);
    const matchesPlan = !selectedPlans.length || selectedPlans.includes(user.plan);

    const activePages = user.active_pages ?? 0;
    const draftPages =
      typeof user.draft_pages_count === "number"
        ? user.draft_pages_count
        : user.draft_pages?.length ?? 0;

    const matchesActive = matchesNumberRange(activePages, activeMin, activeMax);
    const matchesDraft = matchesNumberRange(draftPages, draftMin, draftMax);
    const matchesValid = matchesDateRange(user.valid_until, userFilters.validFrom, userFilters.validTo);
    const matchesCreated = matchesDateRange(
      user.created_at,
      userFilters.createdFrom,
      userFilters.createdTo
    );

    return matchesName && matchesAgency && matchesPlan && matchesActive && matchesDraft && matchesValid && matchesCreated;
  });
});

const sortedUsers = computed(() => {
  const list = [...baseFilteredUsers.value];
  const key = userSort.key;
  const direction = userSort.direction === "asc" ? 1 : -1;
  const getValue = (user: Metrics["users"][number]) => {
    switch (key) {
      case "name":
        return user.name?.toLowerCase() || "";
      case "agency_name":
        return user.agency_name?.toLowerCase() || "";
      case "plan":
        return user.plan?.toLowerCase() || "";
      case "active_pages":
        return user.active_pages ?? 0;
      case "draft_pages":
        return typeof user.draft_pages_count === "number"
          ? user.draft_pages_count
          : user.draft_pages?.length ?? 0;
      case "valid_until":
        return user.valid_until ? new Date(user.valid_until).getTime() : null;
      case "created_at":
        return user.created_at ? new Date(user.created_at).getTime() : null;
      default:
        return null;
    }
  };
  return list.sort((a, b) => {
    const aValue = getValue(a);
    const bValue = getValue(b);
    if (aValue === bValue) return 0;
    if (aValue === null || aValue === undefined) return 1 * direction;
    if (bValue === null || bValue === undefined) return -1 * direction;
    if (typeof aValue === "number" && typeof bValue === "number") {
      return (aValue - bValue) * direction;
    }
    return String(aValue).localeCompare(String(bValue)) * direction;
  });
});

const filteredUsersTotal = computed(() => sortedUsers.value.length);

const filteredUsers = computed(() => {
  const start = (userPage.value - 1) * userPageSize.value;
  return sortedUsers.value.slice(start, start + userPageSize.value);
});

const totalUserPages = computed(() => {
  const total = filteredUsersTotal.value;
  if (!total) return 1;
  return Math.max(1, Math.ceil(total / userPageSize.value));
});

const userPageRange = computed(() => {
  if (!filteredUsersTotal.value) return { start: 0, end: 0 };
  const start = (userPage.value - 1) * userPageSize.value + 1;
  const end = Math.min(filteredUsersTotal.value, start + userPageSize.value - 1);
  return { start, end };
});

const updatePopoverPosition = (key: UserColumnKey, target?: HTMLElement | null) => {
  const element = target || filterButtonRefs.value[key];
  if (!element) return;
  const rect = element.getBoundingClientRect();
  const padding = 16;
  const viewportWidth = typeof window !== "undefined" ? window.innerWidth : 0;
  let left = rect.left + rect.width - filterPopoverWidth;
  if (viewportWidth) {
    left = Math.min(Math.max(left, padding), Math.max(padding, viewportWidth - filterPopoverWidth - padding));
  }
  filterPopoverPosition.left = left;
  filterPopoverPosition.top = rect.bottom + 8;
};

const closeFilterPanel = (key?: UserColumnKey | null) => {
  const current = key ?? openFilterKey.value;
  if (!current) return;
  resetFilterSearch(current);
  openFilterKey.value = null;
};

const toggleColumnFilter = (key: UserColumnKey, event?: Event) => {
  if (openFilterKey.value === key) {
    closeFilterPanel(key);
    return;
  }
  resetFilterSearch(key);
  updatePopoverPosition(key, event?.currentTarget as HTMLElement | undefined | null);
  openFilterKey.value = key;
};

const toggleColumnSort = (key: UserColumnKey) => {
  if (userSort.key === key) {
    userSort.direction = userSort.direction === "asc" ? "desc" : "asc";
  } else {
    userSort.key = key;
    userSort.direction = "asc";
  }
};

const clearColumnFilter = (key: UserColumnKey) => {
  switch (key) {
    case "name":
      userFilters.name = "";
      break;
    case "agency_name":
      userFilters.agencies = [];
      break;
    case "plan":
      userFilters.plans = [];
      break;
    case "active_pages":
      userFilters.activeMin = "";
      userFilters.activeMax = "";
      break;
    case "draft_pages":
      userFilters.draftMin = "";
      userFilters.draftMax = "";
      break;
    case "valid_until":
      userFilters.validFrom = "";
      userFilters.validTo = "";
      break;
    case "created_at":
      userFilters.createdFrom = "";
      userFilters.createdTo = "";
      break;
  }
};

const isFilterActive = (key: UserColumnKey) => {
  switch (key) {
    case "name":
      return Boolean(userFilters.name.trim());
    case "agency_name":
      return userFilters.agencies.length > 0;
    case "plan":
      return userFilters.plans.length > 0;
    case "active_pages":
      return Boolean(userFilters.activeMin || userFilters.activeMax);
    case "draft_pages":
      return Boolean(userFilters.draftMin || userFilters.draftMax);
    case "valid_until":
      return Boolean(userFilters.validFrom || userFilters.validTo);
    case "created_at":
      return Boolean(userFilters.createdFrom || userFilters.createdTo);
    default:
      return false;
  }
};

const handleFilterOutsideClick = (event: MouseEvent) => {
  const path = event.composedPath();
  if (openFilterKey.value) {
    const shouldKeepOpen = path.some(
      el => (el as HTMLElement)?.dataset?.columnFilter === openFilterKey.value!
    );
    if (!shouldKeepOpen) {
      closeFilterPanel();
    }
  }
  if (templateAgencyDropdownOpen.value) {
    const insideAgencySelector = path.some(
      el => (el as HTMLElement)?.dataset?.templateAgencySelector === "true"
    );
    if (!insideAgencySelector) {
      templateAgencyDropdownOpen.value = false;
    }
  }
};

const toggleUserRow = (userId: number) => {
  expandedUser.value = expandedUser.value === userId ? null : userId;
};

const exportPdf = () => {
  if (!metrics.value) return;
  const doc = new jsPDF("p", "mm", "a4");
  const margin = 14;
  const lineHeight = 8;
  let cursor = margin;

  doc.setFillColor(22, 27, 34);
  doc.rect(0, 0, 210, 40, "F");
  doc.setTextColor("#ffffff");
  doc.setFontSize(18);
  doc.text("Vis├úo Gerencial ┬À Relat├│rio Premium", margin, cursor);
  cursor += lineHeight;
  doc.setFontSize(11);
  doc.text(`período: ${adminPeriodLabel.value}`, margin, cursor);
  cursor += lineHeight;
  doc.text(`Emitido em ${new Date().toLocaleString()}`, margin, cursor);
  cursor = 50;

  doc.setTextColor("#111111");
  doc.setFontSize(14);
  doc.text("KPIs principais", margin, cursor);
  cursor += lineHeight;

  const KPI_ROWS = [
    ["usuários ativos", metrics.value.total_users ?? "--"],
    ["Agências", metrics.value.total_agencies ?? "--"],
    ["páginas totais", metrics.value.total_pages ?? "--"],
    ["páginas publicadas", metrics.value.published_pages ?? "--"],
    ["MRR estimado", `R$ ${(metrics.value.mrr ?? 0).toFixed(2)}`],
    ["Novos usuários (período)", metrics.value.new_users_last_days ?? "--"]
  ];
  autoTable(doc, {
    startY: cursor,
    head: [["Indicador", "Valor"]],
    body: KPI_ROWS,
    theme: "striped",
    styles: { fontSize: 10, cellPadding: 3 },
    headStyles: { fillColor: [67, 56, 202], textColor: 255 }
  });
  cursor = (doc as any).lastAutoTable.finalY + 10;

  doc.setFontSize(14);
  doc.text("Distribui├º├úo de planos", margin, cursor);
  cursor += lineHeight;
  const planRows = (metrics.value.plans || []).map(plan => [planLabel(plan.plan), String(plan.count)]);
  autoTable(doc, {
    startY: cursor,
    head: [["Plano", "Total"]],
    body: planRows,
    theme: "grid",
    styles: { fontSize: 10, cellPadding: 3 },
    headStyles: { fillColor: [14, 116, 144], textColor: 255 }
  });
  cursor = (doc as any).lastAutoTable.finalY + 10;

  doc.setFontSize(14);
  doc.text("usuários ┬À Trial e planos", margin, cursor);
  cursor += lineHeight;
  const userRows = (metrics.value.users || []).slice(0, 12).map(u => [
    u.name,
    u.email,
    planLabel(u.plan),
    u.trial_plan ? `Trial at├® ${formatDate(u.trial_ends_at)}` : "-",
    formatDateTime(u.created_at)
  ]);
  autoTable(doc, {
    startY: cursor,
    head: [["Nome", "Email", "Plano", "Trial", "Entrada"]],
    body: userRows,
    theme: "grid",
    styles: { fontSize: 9, cellPadding: 2 },
    headStyles: { fillColor: [15, 118, 110], textColor: 255 }
  });

  doc.save(`relatorio-admin-${new Date().toISOString().slice(0, 10)}.pdf`);
};

const openTrialDialog = (user: Metrics["users"][number]) => {
  trialDialog.value = { open: true, user };
};

const closeTrialDialog = () => {
  trialDialog.value = { open: false, user: null };
};

const grantTrial = async () => {
  if (!auth.user?.is_superuser || !trialDialog.value.user) return;
  granting.value = trialDialog.value.user.id;
  error.value = "";
  try {
    await api.post(`/admin/users/${trialDialog.value.user.id}/grant-trial`, { plan: "infinity", days: 7 });
    showSnackbar("Trial premium liberado por 7 dias.");
    closeTrialDialog();
    await loadMetrics();
  } catch (err) {
    console.error(err);
    error.value = "N├úo foi poss├¡vel liberar o trial para este usuário.";
    showSnackbar("N├úo foi poss├¡vel liberar o trial para este usuário.");
  } finally {
    granting.value = null;
  }
};

const openDeleteDialog = (user: Metrics["users"][number]) => {
  deleteDialog.value = { open: true, user, loading: false, error: "" };
};

const closeDeleteDialog = () => {
  deleteDialog.value = { open: false, user: null, loading: false, error: "" };
};

const confirmDeleteUser = async () => {
  const user = deleteDialog.value.user;
  if (!user) return;
  deleteDialog.value.loading = true;
  deleteDialog.value.error = "";
  try {
    await api.delete(`/admin/users/${user.id}`);
    deleteDialog.value.loading = false;
    deleteDialog.value.open = false;
    deleteDialog.value.user = null;
    expandedUser.value = null;
    await loadMetrics();
    showSnackbar("usuário exclu├¡do com sucesso.");
  } catch (err: any) {
    console.error(err);
    deleteDialog.value.error =
      err?.response?.data?.detail || "N├úo foi poss├¡vel excluir o usuário. Tente novamente.";
    deleteDialog.value.loading = false;
  }
};

const updateLinkDialogSlug = () => {
  linkPageDialog.value.newSlug = slugify(linkPageDialog.value.newTitle, "pagina");
};

const canRefundUser = (user: Metrics["users"][number]) => {
  if (user.is_superuser) return false;
  const provider = (user.subscription_provider || "").toLowerCase();
  const status = (user.subscription_status || "").toLowerCase();
  return provider === "cakto" && Boolean(user.subscription_cakto_order_id) && status === "active" && user.is_active !== false;
};

const openRefundDialog = (user: Metrics["users"][number]) => {
  if (!auth.user?.is_superuser) return;
  refundDialog.value = { open: true, user, loading: false, error: "" };
};

const closeRefundDialog = () => {
  refundDialog.value = { open: false, user: null, loading: false, error: "" };
};

const confirmRefund = async () => {
  const dialog = refundDialog.value;
  if (!dialog.user) return;
  dialog.loading = true;
  dialog.error = "";
  try {
    await api.post(`/admin/users/${dialog.user.id}/refund`, {});
    showSnackbar("Reembolso solicitado e conta bloqueada.");
    closeRefundDialog();
    expandedUser.value = null;
    await loadMetrics();
  } catch (err: any) {
    console.error(err);
    dialog.error = err?.response?.data?.detail || "N├úo foi poss├¡vel solicitar o reembolso agora.";
    dialog.loading = false;
  }
};

watch(
  () => linkPageDialog.value.newTitle,
  () => updateLinkDialogSlug()
);

const handleLinkPageSelection = () => {
  const page = linkPageDialog.value.pages.find(p => p.id === linkPageDialog.value.selectedPageId);
  linkPageDialog.value.newTitle = page?.title || "";
};

watch(
  () => linkPageDialog.value.selectedPageId,
  () => handleLinkPageSelection()
);

const closeLinkPageDialog = () => {
  linkPageDialog.value = {
    open: false,
    user: null,
    pages: [],
    selectedPageId: null,
    newTitle: "",
    newSlug: "",
    saving: false,
    loading: false,
    error: ""
  };
};

const openLinkPageDialog = async (user: Metrics["users"][number]) => {
  if (!auth.user?.is_superuser) return;
  if (!user.agency_id) {
    showSnackbar("usuário n├úo possui Agência vinculada.");
    return;
  }
  if (!agencyStore.currentAgencyId) {
    showSnackbar("Selecione uma Agência de origem para listar suas páginas.");
    return;
  }
  linkPageDialog.value.open = true;
  linkPageDialog.value.user = user;
  linkPageDialog.value.pages = [];
  linkPageDialog.value.selectedPageId = null;
  linkPageDialog.value.newTitle = "";
  linkPageDialog.value.newSlug = "";
  linkPageDialog.value.saving = false;
  linkPageDialog.value.error = "";
  linkPageDialog.value.loading = true;
  try {
    const res = await api.get<AdminPageSummary[]>(`/pages`, {
      params: { agency_id: agencyStore.currentAgencyId }
    });
    linkPageDialog.value.pages = res.data || [];
    if (linkPageDialog.value.pages.length) {
      linkPageDialog.value.selectedPageId = linkPageDialog.value.pages[0].id;
      linkPageDialog.value.newTitle = linkPageDialog.value.pages[0].title;
      updateLinkDialogSlug();
    }
  } catch (err) {
    console.error(err);
    linkPageDialog.value.error = "N├úo foi poss├¡vel carregar suas páginas.";
  } finally {
    linkPageDialog.value.loading = false;
  }
};

const confirmLinkPage = async () => {
  const dialog = linkPageDialog.value;
  if (!dialog.user || !dialog.user.agency_id) {
    dialog.error = "usuário sem Agência para vincular página.";
    return;
  }
  if (!dialog.selectedPageId) {
    dialog.error = "Selecione uma página para copiar.";
    return;
  }
  const title = dialog.newTitle.trim();
  if (!title) {
    dialog.error = "Informe o nome do roteiro.";
    return;
  }
  dialog.saving = true;
  dialog.error = "";
  try {
    await api.post(`/admin/pages/${dialog.selectedPageId}/clone`, {
      target_agency_id: dialog.user.agency_id,
      title
    });
    showSnackbar("página vinculada ao usuário.");
    closeLinkPageDialog();
    await loadMetrics();
  } catch (err: any) {
    console.error(err);
    dialog.error = err?.response?.data?.detail || "N├úo foi poss├¡vel vincular a página.";
    dialog.saving = false;
  }
};
const planLabel = (plan: string) => {
  if (!plan) return "Indefinido";
  const lower = plan.toLowerCase();
  if (lower.includes("trial")) return plan;
  return getPlanLabel(plan);
};

watch(
  userFilters,
  () => {
    expandedUser.value = null;
    userPage.value = 1;
  },
  { deep: true }
);

watch(
  () => [userSort.key, userSort.direction],
  () => {
    expandedUser.value = null;
  }
);

watch(filteredUsersTotal, total => {
  if (!total) {
    userPage.value = 1;
    return;
  }
  const maxPage = Math.max(1, Math.ceil(total / userPageSize.value));
  if (userPage.value > maxPage) {
    userPage.value = maxPage;
  }
});

watch(userPageSize, () => {
  userPage.value = 1;
});

watch(metrics, value => {
  expandedUser.value = null;
  if (!templateAgencyOptions.value.length && value?.agencies?.length) {
    templateAgencyOptions.value = value.agencies;
  }
});

watch(
  () => templateDialog.name,
  value => {
    if (!templateDialog.open || templateDialog.mode !== "create") return;
    if (!templateDialog.slug || templateDialog.slug === templateSlugAuto.value) {
      const next = slugify(value, "modelo");
      templateDialog.slug = next;
      templateSlugAuto.value = next;
    }
  }
);

watch(
  templateAgencySearch,
  value => {
    if (skipTemplateAgencySearchWatcher) {
      skipTemplateAgencySearchWatcher = false;
      return;
    }
    if (templateAgencySearchDebounce) {
      clearTimeout(templateAgencySearchDebounce);
    }
    templateAgencyDropdownOpen.value = true;
    templateAgencySearchDebounce = setTimeout(() => {
      void fetchTemplateAgencies(value);
    }, 250);
  }
);

watch(
  templateAgencyOptions,
  options => {
    if (!options?.length) {
      if (!templateAgencySearch.value.trim()) {
        templateAgencyId.value = null;
        updateTemplateAgencySearchLabel("");
      }
      return;
    }
    const exists = options.some(option => option.id === templateAgencyId.value);
    if (!templateAgencyId.value && options[0] && !templateAgencySearch.value.trim()) {
      templateAgencyId.value = options[0].id;
      updateTemplateAgencySearchLabel(options[0].name);
      return;
    }
    if (!exists && options[0] && !templateAgencySearch.value.trim()) {
      templateAgencyId.value = options[0].id;
      updateTemplateAgencySearchLabel(options[0].name);
    }
  },
  { immediate: true }
);

watch(
  templateAgencyId,
  async value => {
    if (activeTab.value === "templates" && value) {
      await loadTemplatePages();
    }
    if (!value) {
      templatePages.value = [];
    }
  }
);

onMounted(async () => {
  updateIsMobile();
  if (typeof window !== "undefined") {
    window.addEventListener("resize", updateIsMobile);
    window.addEventListener("click", handleFilterOutsideClick);
  }
  if (!auth.user && auth.token) {
    await auth.fetchProfile();
  }
  if (!agencyStore.agencies.length) {
    try {
      await agencyStore.loadAgencies();
    } catch (err) {
      console.error(err);
    }
  }
  await lessonsStore.ensureLessons();
  await loadMetrics();
  await loadOnlineSessions();
  startOnlineSessionsPolling();
});

watch(
  days,
  async (value) => {
    if (value === "custom" && !adminOrderedRange.value) return;
    await loadMetrics();
  }
);

watch(
  [customStartDate, customEndDate],
  async () => {
    if (days.value !== "custom" || !adminOrderedRange.value) return;
    await loadMetrics();
  }
);

watch(activeTab, (tab) => {
  if (tab === "monitor") {
    loadOnlineSessions();
  }
  if (tab === "templates") {
    ensureTemplateAgencyOptions();
    if (!pageTemplates.value.length) {
      loadTemplates();
    }
    if (templateAgencyId.value) {
      loadTemplatePages();
    }
  }
});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", updateIsMobile);
    window.removeEventListener("click", handleFilterOutsideClick);
  }
  if (templateAgencySearchDebounce) {
    clearTimeout(templateAgencySearchDebounce);
    templateAgencySearchDebounce = null;
  }
  stopOnlineSessionsPolling();
});
</script>

<style scoped>
.premium-panel {
  background: radial-gradient(circle at top, #101828 0%, #05060f 60%);
  min-height: 100vh;
  color: #f8fafc;
  border-radius: 0;
  margin: 0;
  padding: 0;
}

.premium-panel .premium-card {
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.03);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(14px);
}

.interactive-table,
.interactive-table * {
  user-select: auto;
  caret-color: inherit;
}

.copyable {
  user-select: text !important;
  caret-color: auto !important;
}

:global(.dark-theme .lessons-form input:not([type='file']),
.dark-theme .lessons-form textarea,
.dark-theme .lessons-form select) {
  background-color: #181818 !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
  color: #f8fafc !important;
}
:global(.dark-theme .lessons-form input:not([type='file'])::placeholder,
.dark-theme .lessons-form textarea::placeholder,
.dark-theme .lessons-form select::placeholder) {
  color: rgba(255, 255, 255, 0.55) !important;
}
:global(.dark-theme .lessons-form input[type='file']) {
  color: #f8fafc !important;
}
:global(.dark-theme .lessons-form input[type='file']::file-selector-button) {
  background-color: #181818 !important;
  color: #f8fafc !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}
:global(.dark-theme .lessons-form input[type='file']::-webkit-file-upload-button) {
  background-color: #181818 !important;
  color: #f8fafc !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}
:global(.dark-theme .lessons-form .upload-zone) {
  background-color: #181818;
  border-color: rgba(255, 255, 255, 0.2);
}
:global(.dark-theme .lessons-form .upload-zone input[type='file']) {
  color: #e2e8f0;
}
</style>

interface AdminPageSummary {
  id: number;
  title: string;
  slug: string;
  status: string;
}
