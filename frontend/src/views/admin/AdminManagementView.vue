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
          Resumo de usuarios, planos, validade e MRR.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <select v-model="days" class="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
          <option value="7">Ultimos 7 dias</option>
          <option value="30">Ultimos 30 dias</option>
          <option value="90">Ultimos 90 dias</option>
        </select>

        <button
          @click="exportPdf"
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
          Exportar PDF
        </button>
      </div>
    </header>
    
      <section class="grid gap-4 md:grid-cols-4">
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Usuarios</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.total_users ?? "--" }}</p>
          <p class="text-xs text-slate-400">Contas ativas no SaaS.</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Agencias</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.total_agencies ?? "--" }}</p>
          <p class="text-xs text-slate-400">Times cadastrados.</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Paginas totais</p>
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
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Novos usuarios ({{ days }}d)</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ metrics?.new_users_last_days ?? "--" }}</p>
          <p class="text-xs text-slate-400">Entradas recentes.</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Distribuicao de planos</p>
          <ul class="mt-3 space-y-1 text-sm text-slate-600">
            <li v-for="p in metrics?.plans || []" :key="p.plan" class="flex justify-between">
              <span class="capitalize">{{ planLabel(p.plan) }}</span>
              <span class="font-semibold">{{ p.count }}</span>
            </li>
            <li v-if="!(metrics?.plans?.length)" class="text-xs text-slate-400">Sem dados ainda.</li>
          </ul>
        </div>
      </section>

      <section class="grid gap-4 lg:grid-cols-3">
        <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100 lg:col-span-2">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Novos usuarios ({{ days }}d)</h2>
              <p class="text-sm text-slate-500">Entradas diárias.</p>
            </div>
          </div>

          <div class="mt-4 h-64 rounded-xl bg-slate-50 p-4">
            <div v-if="metrics?.new_users_timeseries?.length" class="flex h-full items-end gap-3">
              <div
                v-for="point in metrics.new_users_timeseries"
                :key="point.label"
                class="flex-1 rounded-2xl bg-white p-2 text-center shadow-sm"
              >
                <div
                  class="mx-auto w-8 rounded-xl bg-gradient-to-t from-emerald-200 to-emerald-500"
                  :style="{ height: Math.min(point.value * 10 + 10, 140) + 'px' }"
                ></div>
                <p class="mt-2 text-xs text-slate-500">{{ point.label }}</p>
                <p class="text-sm font-semibold text-slate-900">{{ point.value }}</p>
              </div>
            </div>
            <div class="flex h-full items-center justify-center text-sm text-slate-500" v-else>
              Sem dados no periodo.
            </div>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
          <h3 class="text-sm font-semibold text-slate-900">Resumo geral</h3>
          <ul class="mt-3 space-y-3 text-sm text-slate-700">
            <li class="flex items-center justify-between">
              <span>Usuarios ativos</span>
              <span class="font-semibold">{{ metrics?.total_users ?? "--" }}</span>
            </li>
            <li class="flex items-center justify-between">
              <span>Agencias</span>
              <span class="font-semibold">{{ metrics?.total_agencies ?? "--" }}</span>
            </li>
            <li class="flex items-center justify-between">
              <span>Paginas publicadas</span>
              <span class="font-semibold">{{ metrics?.published_pages ?? "--" }}</span>
            </li>
          </ul>
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

        <div class="mt-4 grid gap-4 md:grid-cols-3">
          <div class="md:col-span-1">
            <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Buscar</label>
            <input
              v-model="userSearch"
              type="text"
              placeholder="Nome ou email"
              class="mt-1 w-full rounded-full border border-slate-200 px-4 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Plano</label>
            <select
              v-model="userPlanFilter"
              class="mt-1 w-full rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none"
            >
              <option value="all">Todos os planos</option>
              <option v-for="plan in userPlanOptions" :key="plan" :value="plan">
                {{ planLabel(plan) }}
              </option>
            </select>
          </div>

          <div>
            <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Agência</label>
            <select
              v-model="userAgencyFilter"
              class="mt-1 w-full rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none"
            >
              <option value="all">Todas</option>
              <option value="__none">Sem agência</option>
              <option v-for="agency in userAgencyOptions" :key="agency" :value="agency">
                {{ agency }}
              </option>
            </select>
          </div>
        </div>

        <div class="mt-4 overflow-x-auto">
          <table class="min-w-full text-sm text-slate-800 divide-y divide-slate-100 interactive-table">
            <thead class="bg-slate-50 text-left text-slate-600">
              <tr>
                <th class="px-3 py-2 text-left">Nome</th>
                <th class="px-3 py-2 text-left">Agência</th>
                <th class="px-3 py-2 text-left">Qtd páginas ativas</th>
                <th class="px-3 py-2 text-left">Qtd páginas rascunho</th>
                <th class="px-3 py-2 text-left">Plano</th>
                <th class="px-3 py-2 text-left">Validade</th>
                <th class="px-3 py-2 text-left">Entrada</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-slate-100">
              <template v-for="u in filteredUsers" :key="u.id">
                <tr class="transition hover:bg-slate-50/70" @click="toggleUserRow(u.id)">
                  <td class="px-3 py-3">
                    <div class="flex items-start gap-3">
                      <button
                        type="button"
                        class="mt-1 rounded-full border border-slate-300 p-1 text-xs transition hover:bg-slate-100"
                        @click.stop="toggleUserRow(u.id)"
                      >
                        <span :class="expandedUser === u.id ? 'rotate-90 inline-block transition' : 'inline-block transition'">
                          ▶
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
                      Trial até {{ formatDate(u.trial_ends_at) }}
                    </span>
                  </td>

                  <td class="px-3 py-3">{{ formatDate(u.valid_until) }}</td>
                  <td class="px-3 py-3 whitespace-nowrap">{{ formatDateTime(u.created_at) }}</td>
                </tr>

                <tr v-if="expandedUser === u.id">
                  <td colspan="7" class="px-3 pb-4">
                    <div class="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 text-sm text-slate-800 shadow-inner">
                      <div class="grid gap-4 md:grid-cols-2">
                        <div>
                          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Contato</p>
                          <p class="mt-1 font-semibold no-caret">{{ u.name }}</p>
                          <p class="text-xs text-slate-500 no-caret">{{ u.email }}</p>
                          <p class="text-xs text-slate-500 no-caret">{{ u.whatsapp || 'Sem telefone' }}</p>
                        </div>

                        <div>
                          <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Agência</p>
                          <p class="mt-1 font-semibold">{{ u.agency_name || 'Não vinculada' }}</p>
                          <p class="text-xs text-slate-500">
                            {{ u.active_pages ?? 0 }} páginas publicadas · Plano {{ planLabel(u.plan) }}
                          </p>
                        </div>
                      </div>

                      <div class="mt-4">
                        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Origem / UTMs</p>
                        <div
                          v-if="u.tracking?.length"
                          class="mt-2 space-y-3 rounded-2xl border border-white/40 bg-white/80 p-4 shadow-inner"
                        >
                          <div
                            v-for="entry in u.tracking"
                            :key="entry.id"
                            class="rounded-2xl border border-slate-200 bg-white/90 p-3 shadow-sm"
                          >
                            <div class="flex flex-wrap gap-2">
                              <span
                                v-for="chip in buildUtmChips(entry)"
                                :key="chip.label + chip.value"
                                class="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold text-slate-600"
                              >
                                <span class="text-slate-400">{{ chip.label }}:</span>
                                <span class="text-slate-900">{{ chip.value }}</span>
                              </span>
                            </div>
                            <p class="mt-2 text-[11px] text-slate-500">
                              Capturado em {{ formatDateTime(entry.created_at) || 'data desconhecida' }}
                            </p>
                          </div>
                        </div>
                        <p
                          v-else
                          class="mt-2 rounded-2xl border border-dashed border-slate-200 px-3 py-3 text-center text-xs text-slate-500"
                        >
                          Nenhuma informação de UTM registrada.
                        </p>
                      </div>

                      <div class="mt-4 flex flex-wrap items-center gap-3">
                        <button
                          v-if="!u.is_superuser"
                          :class="[
                            'rounded-full border px-4 py-2 text-xs font-semibold text-slate-700 transition disabled:opacity-60',
                            'border-slate-200 hover:bg-emerald-50 hover:text-emerald-700'
                          ]"
                          :disabled="granting === u.id || Boolean(u.trial_plan)"
                          @click.stop="openTrialDialog(u)"
                        >
                          {{ u.trial_plan ? 'Trial ativo' : 'Liberar 7 dias' }}
                        </button>

                        <button
                          v-if="auth.user?.is_superuser"
                          class="rounded-full border border-indigo-200 px-4 py-2 text-xs font-semibold text-indigo-600 transition hover:bg-indigo-50 disabled:opacity-50"
                          :disabled="!u.agency_id || !agencyStore.currentAgencyId"
                          @click.stop="openLinkPageDialog(u)"
                          :title="
                            !agencyStore.currentAgencyId
                              ? 'Selecione uma agência de origem no painel'
                              : !u.agency_id
                                ? 'Usuário sem agência vinculada'
                                : 'Vincular página pronta'
                          "
                        >
                          Vincular página
                        </button>

                        <button
                          v-if="!u.is_superuser"
                          class="rounded-full border border-red-200 bg-red-50 px-4 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-100"
                          @click.stop="openDeleteDialog(u)"
                        >
                          Excluir usuário
                        </button>

                        <span
                          v-if="u.is_superuser"
                          class="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                        >
                          Superuser
                        </span>
                      </div>

                      <div class="mt-6">
                        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Páginas publicadas</p>

                        <div v-if="u.published_pages?.length" class="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
                          <table class="min-w-full divide-y divide-slate-100 text-xs text-slate-700 interactive-table">
                            <thead class="bg-slate-50 text-left text-slate-500">
                              <tr>
                                <th class="px-3 py-2">Título</th>
                                <th class="px-3 py-2">Slug</th>
                                <th class="px-3 py-2 text-right">Ações</th>
                              </tr>
                            </thead>

                            <tbody class="divide-y divide-slate-100">
                              <tr v-for="page in u.published_pages" :key="page.id">
                                <td class="px-3 py-2 font-semibold text-slate-900">{{ page.title }}</td>
                                <td class="px-3 py-2 text-[11px] text-slate-500">/{{ page.slug }}</td>
                                <td class="px-3 py-2">
                                  <div class="flex justify-end gap-2">
                                    <button
                                      class="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-700 transition hover:bg-slate-100"
                                      @click.stop="viewPublishedPage(page)"
                                    >
                                      Visualizar
                                    </button>

                                    <button
                                      class="inline-flex items-center gap-1 rounded-full border border-slate-900/20 bg-slate-900/90 px-3 py-1 text-[11px] font-semibold text-white transition hover:bg-slate-900 disabled:opacity-60"
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
                          class="mt-3 rounded-xl border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-500"
                        >
                          Nenhuma página publicada ainda.
                        </p>
                      </div>

                      <div class="mt-6">
                        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Páginas em rascunho</p>

                        <div v-if="u.draft_pages?.length" class="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
                          <table class="min-w-full divide-y divide-slate-100 text-xs text-slate-700 interactive-table">
                            <thead class="bg-slate-50 text-left text-slate-500">
                              <tr>
                                <th class="px-3 py-2">Título</th>
                                <th class="px-3 py-2">Slug</th>
                                <th class="px-3 py-2 text-right">Ações</th>
                              </tr>
                            </thead>

                            <tbody class="divide-y divide-slate-100">
                              <tr v-for="page in u.draft_pages" :key="page.id">
                                <td class="px-3 py-2 font-semibold text-slate-900">{{ page.title }}</td>
                                <td class="px-3 py-2 text-[11px] text-slate-500">/{{ page.slug }}</td>
                                <td class="px-3 py-2">
                                  <div class="flex justify-end">
                                    <button
                                      class="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-700 transition hover:bg-slate-100"
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
                          class="mt-3 rounded-xl border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-500"
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
        </div>
      </section>
    </template>

    <!-- LESSONS -->
    <template v-else-if="activeTab === 'lessons'">
      <section class="rounded-3xl bg-white p-6 shadow-md ring-1 ring-slate-100">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500">Conteúdo exclusivo</p>
            <h2 class="text-2xl font-bold text-slate-900">Gerenciar aulas</h2>
            <p class="text-sm text-slate-500">As aulas cadastradas aqui aparecem para todos os administradores na aba "Aulas".</p>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              @click="resetLessonForm"
            >
              Nova aula
            </button>

            <button
              type="button"
              class="rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 transition hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-70"
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
              class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500"
            >
              Carregando aulas...
            </p>

            <p
              v-else-if="!adminLessons.length"
              class="rounded-2xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500"
            >
              Nenhuma aula cadastrada ainda.
            </p>

            <template v-else>
              <article
                v-for="lesson in adminLessons"
                :key="lesson.id"
                class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"
              >
                <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p class="text-xs uppercase tracking-[0.3em] text-slate-500">
                      {{ lesson.level || "Aula" }} • {{ lesson.duration || "Livre" }}
                    </p>
                    <h4 class="mt-2 text-lg font-semibold text-slate-900">{{ lesson.title }}</h4>
                    <p class="mt-1 text-sm text-slate-600">{{ lesson.description }}</p>
                    <p class="mt-3 text-xs text-slate-500">
                      Fonte:
                      <span class="font-semibold text-slate-700">
                        {{ lesson.videoType === "file" ? "Arquivo/URL direto" : "Embed/Youtube" }}
                      </span>
                    </p>
                  </div>

                  <img v-if="lesson.thumbnail" :src="lesson.thumbnail" alt="" class="h-20 w-32 rounded-xl object-cover shadow-sm" />
                </div>

                <div class="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                    @click="startLessonEdit(lesson)"
                  >
                    Editar
                  </button>

                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-full border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="deletingLessonId === lesson.id"
                    @click="deleteLesson(lesson.id)"
                  >
                    Excluir
                  </button>
                </div>
              </article>
            </template>
          </div>

          <form class="space-y-4 rounded-2xl bg-slate-50/70 p-5" @submit.prevent="saveLesson">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500">{{ isEditingLesson ? "Editando aula" : "Cadastrar nova aula" }}</p>
              <h3 class="text-xl font-semibold text-slate-900">{{ isEditingLesson ? "Atualizar conteúdo" : "Adicionar conteúdo" }}</h3>
              <p class="text-sm text-slate-500">Informe título, descrição e o link ou iframe do vídeo.</p>
            </div>

            <label class="block text-sm font-semibold text-slate-700">
              Título
              <input
                v-model="lessonForm.title"
                type="text"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand"
                placeholder="Ex.: Dominando o editor"
                required
              />
            </label>

            <label class="block text-sm font-semibold text-slate-700">
              Descrição / legenda
              <textarea
                v-model="lessonForm.description"
                rows="3"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand"
                placeholder="Explique o que o usuário aprende nessa aula."
              ></textarea>
            </label>

            <div class="grid gap-3 md:grid-cols-2">
              <label class="block text-sm font-semibold text-slate-700">
                Duração
                <input
                  v-model="lessonForm.duration"
                  type="text"
                  class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand"
                  placeholder="Ex.: 10:45"
                />
              </label>

              <label class="block text-sm font-semibold text-slate-700">
                Nível
                <input
                  v-model="lessonForm.level"
                  type="text"
                  class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand"
                  placeholder="Fundamentos, Estratégia..."
                />
              </label>
            </div>

            <label class="block text-sm font-semibold text-slate-700">
              Thumbnail por link (opcional)
              <input
                v-model="lessonForm.thumbnailUrl"
                type="url"
                :disabled="Boolean(lessonForm.thumbnailData)"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand disabled:cursor-not-allowed disabled:bg-slate-100"
                placeholder="https://..."
              />
              <span v-if="lessonForm.thumbnailData" class="mt-1 block text-xs text-slate-500">
                Limpe a imagem enviada para editar o link.
              </span>
            </label>

            <div class="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Upload opcional</p>

              <div class="mt-2 flex flex-wrap items-center gap-3">
                <input
                  type="file"
                  accept="image/*"
                  @change="handleThumbnailUpload"
                  class="text-sm text-slate-600 file:mr-3 file:rounded-full file:border file:border-slate-300 file:bg-slate-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-700 hover:file:bg-slate-100"
                />

                <button
                  v-if="lessonForm.thumbnailData"
                  type="button"
                  class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                  @click="clearThumbnailUpload"
                >
                  Remover imagem
                </button>
              </div>

              <p v-if="lessonForm.thumbnailUploadName" class="mt-2 text-xs text-slate-500">
                Selecionado: {{ lessonForm.thumbnailUploadName }}
              </p>
            </div>

            <label class="block text-sm font-semibold text-slate-700">
              Link ou iframe do vídeo
              <textarea
                v-model="lessonForm.videoInput"
                rows="3"
                class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-brand focus:ring-brand"
                placeholder="Cole o link do YouTube ou o iframe completo."
                required
              ></textarea>
            </label>

            <div v-if="lessonPreview.videoUrl" class="rounded-2xl border border-slate-200 bg-white p-3">
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
                Cancelar edição
              </button>
            </div>
          </form>
        </div>
      </section>
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
          O usuário receberá acesso total ao plano {{ planLabels.infinity }} por 7 dias. Enviaremos alertas no painel dele para aproveitar o período promocional.
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
          Selecionamos as páginas da sua agência atual ({{ agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId)?.name || 'sem nome' }}).
          A cópia será adicionada à agência do usuário.
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
            class="block text-sm font-semibold text-slate-700"
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
                {{ page.title }} · {{ page.status === 'published' ? 'Publicada' : 'Rascunho' }}
              </option>
            </select>
          </label>
          <div
            v-else
            class="rounded-2xl border border-dashed border-slate-200 px-4 py-3 text-sm text-slate-500"
          >
            Nenhuma página encontrada na sua agência atual. Crie uma página primeiro.
          </div>

          <label class="block text-sm font-semibold text-slate-700">
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
          Essa ação apaga a conta, agências, páginas e registros de tracking vinculados. Ela não pode ser desfeita.
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
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch, computed } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { useAgencyStore } from "../../store/useAgencyStore";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { getPlanLabel, planLabels } from "../../utils/planLabels";
import { normalizeVideoInput, useLessonsStore, type Lesson } from "../../store/useLessonsStore";
import { slugify } from "../../utils/slugify";

interface MetricsUserPage {
  id: number;
  title: string;
  slug: string;
  status: string;
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
  new_users_last_days: number;
  plans: { plan: string; count: number }[];
  new_users_timeseries: { label: string; value: number }[];
  users: {
    id: number;
    name: string;
    email: string;
    plan: string;
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

type AdminTab = "dashboard" | "users" | "lessons";

const adminTabs: { id: AdminTab; label: string; description: string }[] = [
  { id: "dashboard", label: "Dashboard", description: "Resumo e métricas" },
  { id: "users", label: "Usuários", description: "Perfis e status" },
  { id: "lessons", label: "Gestão de aulas", description: "Treinamentos públicos" }
];

const days = ref<"7" | "30" | "90">("30");
const metrics = ref<Metrics | null>(null);
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
const premiumMode = computed(() => (auth.user?.plan || "").toLowerCase() === "infinity");
const activeTab = ref<AdminTab>("dashboard");
const tabButtonClass = (tab: AdminTab) =>
  activeTab.value === tab
    ? "bg-slate-900 text-white shadow-lg shadow-slate-900/30"
    : "border border-slate-200 text-slate-600 hover:bg-slate-50";
const userSearch = ref("");
const userPlanFilter = ref<string | "all">("all");
const userAgencyFilter = ref<string>("all");
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
  { key: "utm_medium", label: "Mídia" },
  { key: "utm_campaign", label: "Campanha" },
  { key: "utm_term", label: "Termo" },
  { key: "utm_content", label: "Conteúdo" },
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
  try {
    const res = await api.get("/admin/metrics", { params: { days: days.value } });
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

const showSnackbar = (text: string) => {
  snackbar.value = { open: true, text };
  setTimeout(() => {
    snackbar.value = null;
  }, 3000);
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
    showSnackbar("Imagem muito grande (máximo 4MB).");
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
    showSnackbar("Informe título e link do vídeo.");
    return;
  }
  const parsed = normalizeVideoInput(lessonForm.videoInput);
  if (!parsed.videoUrl) {
    showSnackbar("Link de vídeo inválido.");
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
    showSnackbar("Não foi possível salvar a aula.");
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
    showSnackbar("Não foi possível remover a aula.");
  } finally {
    deletingLessonId.value = null;
  }
};

const handleResetLessons = () => {
  if (!confirm("Restaurar a lista padrão de aulas?")) return;
  lessonsStore.resetLessons();
  resetLessonForm();
  showSnackbar("Aulas restauradas.");
};

const viewPublishedPage = (page: MetricsUserPage) => {
  if (!page.agency_slug) {
    showSnackbar("Página sem agência vinculada.");
    return;
  }
  const url = `/${page.agency_slug}/${page.slug}`;
  window.open(url, "_blank", "noopener,noreferrer");
};

const clonePublishedPage = async (user: Metrics["users"][number], page: MetricsUserPage) => {
  if (!agencyStore.currentAgencyId) {
    showSnackbar("Selecione uma agência para salvar a página.");
    return;
  }
  savingPageId.value = page.id;
  try {
    await api.post(`/admin/pages/${page.id}/clone`, {
      target_agency_id: agencyStore.currentAgencyId,
      title: `${page.title} - ${user.name}`.trim()
    });
    showSnackbar("Página salva na agência selecionada.");
  } catch (err) {
    console.error(err);
    showSnackbar("Não foi possível salvar esta página.");
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

const filteredUsers = computed(() => {
  const list = metrics.value?.users || [];
  const search = userSearch.value.trim().toLowerCase();
  return list
    .filter(user => {
      const matchesSearch =
        !search ||
        [user.name, user.email, user.agency_name]
          .filter(Boolean)
          .some(field => field!.toLowerCase().includes(search));
      const matchesPlan = userPlanFilter.value === "all" || user.plan === userPlanFilter.value;
      const matchesAgency =
        userAgencyFilter.value === "all" ||
        (userAgencyFilter.value === "__none"
          ? !user.agency_name
          : user.agency_name === userAgencyFilter.value);
      return matchesSearch && matchesPlan && matchesAgency;
    })
    .sort((a, b) => {
      const aDate = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bDate = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bDate - aDate;
    });
});

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
  doc.text("Visão Gerencial · Relatório Premium", margin, cursor);
  cursor += lineHeight;
  doc.setFontSize(11);
  doc.text(`Período: últimos ${days.value} dias`, margin, cursor);
  cursor += lineHeight;
  doc.text(`Emitido em ${new Date().toLocaleString()}`, margin, cursor);
  cursor = 50;

  doc.setTextColor("#111111");
  doc.setFontSize(14);
  doc.text("KPIs principais", margin, cursor);
  cursor += lineHeight;

  const KPI_ROWS = [
    ["Usuários ativos", metrics.value.total_users ?? "--"],
    ["Agências", metrics.value.total_agencies ?? "--"],
    ["Páginas totais", metrics.value.total_pages ?? "--"],
    ["Páginas publicadas", metrics.value.published_pages ?? "--"],
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
  doc.text("Distribuição de planos", margin, cursor);
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
  doc.text("Usuários · Trial e planos", margin, cursor);
  cursor += lineHeight;
  const userRows = (metrics.value.users || []).slice(0, 12).map(u => [
    u.name,
    u.email,
    planLabel(u.plan),
    u.trial_plan ? `Trial até ${formatDate(u.trial_ends_at)}` : "-",
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
    error.value = "Não foi possível liberar o trial para este usuário.";
    showSnackbar("Não foi possível liberar o trial para este usuário.");
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
    showSnackbar("Usuário excluído com sucesso.");
  } catch (err: any) {
    console.error(err);
    deleteDialog.value.error =
      err?.response?.data?.detail || "Não foi possível excluir o usuário. Tente novamente.";
    deleteDialog.value.loading = false;
  }
};

const updateLinkDialogSlug = () => {
  linkPageDialog.value.newSlug = slugify(linkPageDialog.value.newTitle, "pagina");
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
    showSnackbar("Usuário não possui agência vinculada.");
    return;
  }
  if (!agencyStore.currentAgencyId) {
    showSnackbar("Selecione uma agência de origem para listar suas páginas.");
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
    linkPageDialog.value.error = "Não foi possível carregar suas páginas.";
  } finally {
    linkPageDialog.value.loading = false;
  }
};

const confirmLinkPage = async () => {
  const dialog = linkPageDialog.value;
  if (!dialog.user || !dialog.user.agency_id) {
    dialog.error = "Usuário sem agência para vincular página.";
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
    showSnackbar("Página vinculada ao usuário.");
    closeLinkPageDialog();
    await loadMetrics();
  } catch (err: any) {
    console.error(err);
    dialog.error = err?.response?.data?.detail || "Não foi possível vincular a página.";
    dialog.saving = false;
  }
};
const planLabel = (plan: string) => {
  if (!plan) return "Indefinido";
  const lower = plan.toLowerCase();
  if (lower.includes("trial")) return plan;
  return getPlanLabel(plan);
};

watch([userSearch, userPlanFilter, userAgencyFilter], () => {
  expandedUser.value = null;
});

watch(metrics, () => {
  expandedUser.value = null;
});

onMounted(async () => {
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
});

watch(days, loadMetrics);
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

.no-caret {
  user-select: none;
  caret-color: transparent;
}

.interactive-table,
.interactive-table * {
  user-select: none;
  caret-color: transparent;
}
</style>

interface AdminPageSummary {
  id: number;
  title: string;
  slug: string;
  status: string;
}
