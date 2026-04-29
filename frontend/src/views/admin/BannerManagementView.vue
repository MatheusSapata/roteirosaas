<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <section class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">Banners do sistema</h1>
          <p class="mt-1 text-sm text-slate-500">Gerencie mensagens internas exibidas para usuários/agências.</p>
        </div>
        <button class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800" @click="openCreate">
          + Novo banner
        </button>
      </div>

      <div class="mt-5 grid gap-3 md:grid-cols-5">
        <input v-model="filters.q" type="text" placeholder="Buscar por título" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
        <select v-model="filters.status" class="rounded-xl border border-slate-200 px-3 py-2 text-sm">
          <option value="all">Todos</option>
          <option value="active">Ativos</option>
          <option value="inactive">Inativos</option>
        </select>
        <select v-model="filters.placement" class="rounded-xl border border-slate-200 px-3 py-2 text-sm">
          <option value="">Todos locais</option>
          <option value="dashboard">Dashboard</option>
          <option value="leads">Leads</option>
          <option value="pages">Páginas</option>
          <option value="clients">Clientes</option>
          <option value="opportunities">Oportunidades</option>
          <option value="settings">Configurações</option>
          <option value="global">Global</option>
        </select>
        <select v-model="filters.plan" class="rounded-xl border border-slate-200 px-3 py-2 text-sm">
          <option value="">Todos planos</option>
          <option v-for="plan in planOptions" :key="plan.value" :value="plan.value">{{ plan.label }}</option>
        </select>
        <button class="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="loadBanners">
          Atualizar
        </button>
      </div>
    </section>

    <section class="overflow-visible rounded-2xl bg-white shadow-sm ring-1 ring-slate-100">
      <div class="overflow-x-auto overflow-y-visible">
        <table class="min-w-full divide-y divide-slate-100 text-sm">
          <thead class="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th class="px-3 py-3 text-left">Preview</th>
              <th class="px-3 py-3 text-left">Título</th>
              <th class="px-3 py-3 text-left">Status</th>
              <th class="px-3 py-3 text-left">Local</th>
              <th class="px-3 py-3 text-left">Planos</th>
              <th class="px-3 py-3 text-right">Prioridade</th>
              <th class="px-3 py-3 text-right">Início</th>
              <th class="px-3 py-3 text-right">Fim</th>
              <th class="px-3 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-for="item in banners" :key="item.id">
              <td class="px-3 py-3">
                <div class="w-[320px] origin-left">
                  <SystemBanner
                    :title="item.title"
                    :subtitle="item.subtitle || ''"
                    :has-icon="item.has_icon"
                    :icon-name="item.icon_name"
                    :background-variant="item.background_variant"
                    :has-cta="item.has_cta"
                    :cta-label="item.cta_label"
                    :dismissible="item.dismissible"
                  />
                </div>
              </td>
              <td class="px-3 py-3 font-semibold text-slate-900">{{ item.title }}</td>
              <td class="px-3 py-3">
                <span :class="item.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'" class="rounded-full px-2 py-1 text-xs font-semibold">
                  {{ item.is_active ? "Ativo" : "Inativo" }}
                </span>
              </td>
              <td class="px-3 py-3">{{ item.placement }}</td>
              <td class="px-3 py-3">{{ item.target_plans?.length ? item.target_plans.join(", ") : "Todos" }}</td>
              <td class="px-3 py-3 text-right font-semibold">{{ item.priority }}</td>
              <td class="px-3 py-3 text-right">{{ formatDate(item.starts_at) }}</td>
              <td class="px-3 py-3 text-right">{{ formatDate(item.ends_at) }}</td>
              <td class="px-3 py-3">
                <div class="flex justify-end" @click.stop>
                  <button
                    type="button"
                    class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-600 hover:bg-slate-50"
                    @click="toggleActionsMenu(item.id, $event)"
                  >
                    <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor" aria-hidden="true">
                      <circle cx="6" cy="12" r="1.8" />
                      <circle cx="12" cy="12" r="1.8" />
                      <circle cx="18" cy="12" r="1.8" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!banners.length">
              <td colspan="9" class="px-3 py-8 text-center text-sm text-slate-500">Nenhum banner encontrado.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <teleport to="body">
      <div
        v-if="actionsMenuOpenId !== null"
        class="fixed z-[400] min-w-[150px] rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg"
        :style="{ top: `${actionsMenuPosition.top}px`, left: `${actionsMenuPosition.left}px` }"
        @click.stop
      >
        <template v-if="currentActionBanner">
          <button class="block w-full rounded-lg px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="handleEdit(currentActionBanner)">
            Editar
          </button>
          <button class="block w-full rounded-lg px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="handleDuplicate(currentActionBanner.id)">
            Duplicar
          </button>
          <button class="block w-full rounded-lg px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="handleToggleActive(currentActionBanner.id)">
            {{ currentActionBanner.is_active ? "Inativar" : "Ativar" }}
          </button>
          <button class="block w-full rounded-lg px-3 py-2 text-left text-xs font-semibold text-red-600 hover:bg-red-50" @click="handleRemove(currentActionBanner.id)">
            Excluir
          </button>
        </template>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="editorOpen" class="fixed inset-0 z-[300] bg-slate-900/60 p-4 md:p-8">
        <div class="mx-auto flex h-full max-w-[1400px] flex-col overflow-hidden rounded-3xl bg-slate-50 p-4 md:p-6">
          <div class="flex shrink-0 items-center justify-between rounded-2xl bg-white p-4 ring-1 ring-slate-100">
            <div>
              <h2 class="text-xl font-bold text-slate-900">{{ editingId ? "Editar banner" : "Criar banner" }}</h2>
              <p class="text-sm text-slate-500">Configure conteúdo, segmentação e regras avançadas de exibição.</p>
            </div>
            <button class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="closeEditor">Fechar</button>
          </div>

          <div class="mt-4 grid min-h-0 flex-1 gap-6 md:grid-cols-2">
            <div class="h-full min-h-0 space-y-4 overflow-y-auto pr-1">
              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <h3 class="text-sm font-bold uppercase tracking-wide text-slate-800">1. Identificação</h3>
                <div class="mt-3 grid gap-4 md:grid-cols-2">
                  <label class="text-sm font-semibold text-slate-600">
                    Nome interno
                    <input v-model="builder.identification.internal_name" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                  </label>
                  <label class="text-sm font-semibold text-slate-600">
                    Prioridade
                    <input v-model.number="builder.identification.priority" type="number" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                  </label>
                </div>
                <div class="mt-3 grid gap-4 md:grid-cols-2">
                  <label class="text-sm font-semibold text-slate-600">
                    Local de exibição
                    <select v-model="builder.identification.placement" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                      <option value="dashboard">Dashboard</option>
                      <option value="leads">Página de leads</option>
                      <option value="pages">Página de produtos</option>
                      <option value="opportunities">Financeiro / oportunidades</option>
                      <option value="clients">Clientes</option>
                      <option value="settings">Configurações</option>
                      <option value="global">Todas as páginas internas</option>
                    </select>
                  </label>
                  <div class="grid grid-cols-2 gap-2 pt-6">
                    <label class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
                      <input v-model="builder.identification.is_active" type="checkbox" />
                      Ativo
                    </label>
                    <label class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
                      <input v-model="builder.content.dismissible" type="checkbox" />
                      Fechável
                    </label>
                  </div>
                </div>
              </section>

              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <h3 class="text-sm font-bold uppercase tracking-wide text-slate-800">2. Conteúdo do banner</h3>
                <div class="mt-3 space-y-4">
                  <label class="text-sm font-semibold text-slate-600">
                    Título
                    <input v-model="builder.content.title" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                  </label>
                  <label class="text-sm font-semibold text-slate-600">
                    Subtítulo
                    <textarea v-model="builder.content.subtitle" rows="3" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"></textarea>
                  </label>

                  <div class="grid gap-4 md:grid-cols-2">
                    <label class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
                      <input v-model="builder.content.show_icon" type="checkbox" />
                      Mostrar ícone
                    </label>
                    <label class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
                      <input v-model="builder.cta.enabled" type="checkbox" />
                      CTA habilitado
                    </label>
                  </div>

                  <div class="grid gap-4 md:grid-cols-2">
                    <label class="text-sm font-semibold text-slate-600">
                      Ícone
                      <select v-model="builder.content.icon" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                        <option v-for="icon in iconOptions" :key="icon" :value="icon">{{ icon }}</option>
                      </select>
                    </label>
                    <label class="text-sm font-semibold text-slate-600">
                      Background
                      <select v-model="builder.content.background" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                        <option value="green_gradient">verde_escuro_premium</option>
                        <option value="green_solid">verde_gradiente</option>
                        <option value="green_light">verde_suave</option>
                        <option value="warning">verde_alerta</option>
                        <option value="success">neutro_claro</option>
                        <option value="info">info_azul</option>
                      </select>
                    </label>
                  </div>
                </div>
              </section>

              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <h3 class="text-sm font-bold uppercase tracking-wide text-slate-800">3. Ação do CTA</h3>
                <div class="mt-3 space-y-4">
                  <div class="grid gap-4 md:grid-cols-3">
                    <label class="text-sm font-semibold text-slate-600">
                      Tipo de ação
                      <select v-model="builder.cta.type" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                        <option value="internal_route">Página interna</option>
                        <option value="external_url">Link externo</option>
                        <option value="open_modal">Abrir modal</option>
                        <option value="system_action">Executar ação do sistema</option>
                        <option value="none">Sem ação</option>
                      </select>
                    </label>
                    <label class="text-sm font-semibold text-slate-600 md:col-span-2">
                      Texto do botão
                      <input v-model="builder.cta.label" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                    </label>
                  </div>

                  <div v-if="builder.cta.type === 'internal_route'" class="grid gap-4 md:grid-cols-2">
                    <label class="text-sm font-semibold text-slate-600">
                      Página interna
                      <select v-model="builder.cta.internal_target" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                        <option v-for="item in internalRouteOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
                        <option value="__custom__">Outra rota</option>
                      </select>
                    </label>
                    <label v-if="builder.cta.internal_target === '__custom__'" class="text-sm font-semibold text-slate-600">
                      Rota customizada
                      <input v-model="builder.cta.custom_route" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="/admin/..." />
                    </label>
                  </div>

                  <div v-if="builder.cta.type === 'external_url'" class="grid gap-4 md:grid-cols-2">
                    <label class="text-sm font-semibold text-slate-600">
                      URL externa
                      <input v-model="builder.cta.external_url" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="https://..." />
                    </label>
                    <label class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 md:mt-7">
                      <input v-model="builder.cta.open_new_tab" type="checkbox" />
                      Abrir em nova aba
                    </label>
                  </div>

                  <div v-if="builder.cta.type === 'open_modal'" class="grid gap-4 md:grid-cols-2">
                    <label class="text-sm font-semibold text-slate-600">
                      Modal alvo
                      <select v-model="builder.cta.modal_target" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                        <option value="connect_pixel">conectar pixel</option>
                        <option value="upgrade_plan">upgrade de plano</option>
                        <option value="setup_domain">configurar domínio</option>
                        <option value="create_product">criar produto</option>
                        <option value="invite_user">convidar usuário</option>
                      </select>
                    </label>
                  </div>

                  <div v-if="builder.cta.type === 'system_action'" class="grid gap-4 md:grid-cols-2">
                    <label class="text-sm font-semibold text-slate-600">
                      Ação do sistema
                      <select v-model="builder.cta.system_action" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                        <option value="start_onboarding">start_onboarding</option>
                        <option value="open_upgrade_flow">open_upgrade_flow</option>
                        <option value="open_pixel_connection">open_pixel_connection</option>
                        <option value="open_domain_setup">open_domain_setup</option>
                        <option value="open_create_product">open_create_product</option>
                      </select>
                    </label>
                  </div>
                </div>
              </section>

              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <h3 class="text-sm font-bold uppercase tracking-wide text-slate-800">4. Público-alvo</h3>
                <div class="mt-3 space-y-4">
                  <label class="text-sm font-semibold text-slate-600">
                    Quem deve ver este banner?
                    <select v-model="builder.audience.mode" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                      <option value="all_users">Todos os usuários</option>
                      <option value="logged_users">Todos os usuários logados</option>
                      <option value="specific_agencies">Apenas agências específicas</option>
                      <option value="specific_plans">Apenas planos específicos</option>
                      <option value="advanced">Regras avançadas</option>
                    </select>
                  </label>

                  <div class="space-y-2">
                    <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Planos</p>
                    <div class="flex flex-wrap gap-2">
                      <button
                        v-for="plan in planOptions"
                        :key="`chip-${plan.value}`"
                        type="button"
                        class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                        :class="builder.audience.plans.includes(plan.value) ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
                        @click="togglePlan(plan.value)"
                      >
                        {{ plan.label }}
                      </button>
                    </div>
                  </div>

                  <div class="space-y-3 rounded-xl border border-slate-200 p-3">
                    <div class="flex flex-wrap items-end gap-2">
                      <label class="min-w-[240px] flex-1 text-sm font-semibold text-slate-600">
                        Buscar agências
                        <input
                          v-model="agencySearchQuery"
                          class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                          placeholder="Nome ou slug"
                          @input="searchAgencies(agencySearchQuery)"
                        />
                      </label>
                      <button class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="searchAgencies(agencySearchQuery)">
                        {{ agencySearchLoading ? "Buscando..." : "Buscar" }}
                      </button>
                    </div>
                    <div class="max-h-40 overflow-y-auto rounded-xl border border-slate-100 bg-slate-50 p-2">
                      <div v-if="availableAgencyOptions.length" class="space-y-1">
                        <div v-for="agency in availableAgencyOptions" :key="agency.id" class="flex items-center justify-between rounded-lg bg-white px-2 py-2 text-xs">
                          <div>
                            <p class="font-semibold text-slate-800">{{ agency.name }}</p>
                            <p class="text-slate-500">{{ agency.slug || `#${agency.id}` }}</p>
                          </div>
                          <div class="flex gap-1">
                            <button class="rounded-lg border border-emerald-200 px-2 py-1 font-semibold text-emerald-700 hover:bg-emerald-50" @click="addAudienceAgency(agency.id)">Incluir</button>
                            <button class="rounded-lg border border-amber-200 px-2 py-1 font-semibold text-amber-700 hover:bg-amber-50" @click="addExcludedAgency(agency.id)">Excluir</button>
                          </div>
                        </div>
                      </div>
                      <p v-else class="px-2 py-3 text-xs text-slate-500">Nenhuma agência disponível para seleção.</p>
                    </div>
                    <div class="grid gap-3 md:grid-cols-2">
                      <div>
                        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Agências incluídas</p>
                        <div class="flex flex-wrap gap-2">
                          <span v-for="agency in selectedAgencyLabels" :key="`sel-${agency.id}`" class="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                            {{ agency.name }}
                            <button type="button" class="text-emerald-700" @click="removeAudienceAgency(agency.id)">x</button>
                          </span>
                          <span v-if="!selectedAgencyLabels.length" class="text-xs text-slate-400">Todas as agências</span>
                        </div>
                      </div>
                      <div>
                        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Agências excluídas</p>
                        <div class="flex flex-wrap gap-2">
                          <span v-for="agency in excludedAgencyLabels" :key="`exc-${agency.id}`" class="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                            {{ agency.name }}
                            <button type="button" class="text-amber-700" @click="removeExcludedAgency(agency.id)">x</button>
                          </span>
                          <span v-if="!excludedAgencyLabels.length" class="text-xs text-slate-400">Nenhuma exclusão</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="role in roleOptions"
                      :key="role.value"
                      type="button"
                      class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                      :class="builder.audience.roles.includes(role.value) ? 'border-indigo-300 bg-indigo-50 text-indigo-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
                      @click="toggleRole(role.value)"
                    >
                      {{ role.label }}
                    </button>
                  </div>
                </div>
              </section>

              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <h3 class="text-sm font-bold uppercase tracking-wide text-slate-800">5. Regras de exibição</h3>
                <div class="mt-3 space-y-4">
                  <label class="text-sm font-semibold text-slate-600">
                    Lógica das regras
                    <select v-model="builder.rules.logic" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                      <option value="AND">Todas precisam bater (AND)</option>
                      <option value="OR">Qualquer uma pode bater (OR)</option>
                    </select>
                  </label>

                  <div class="space-y-2">
                    <div v-for="(condition, index) in builder.rules.conditions" :key="index" class="grid gap-2 rounded-xl border border-slate-200 p-3 md:grid-cols-4">
                      <select v-model="condition.field" class="rounded-lg border border-slate-200 px-2 py-2 text-xs">
                        <option v-for="field in ruleFields" :key="field.value" :value="field.value">{{ field.label }}</option>
                      </select>
                      <select v-model="condition.operator" class="rounded-lg border border-slate-200 px-2 py-2 text-xs">
                        <option v-for="operator in operatorOptions" :key="operator.value" :value="operator.value">{{ operator.label }}</option>
                      </select>
                      <input v-model="condition.value" class="rounded-lg border border-slate-200 px-2 py-2 text-xs" placeholder="Valor" />
                      <button class="rounded-lg border border-red-200 px-2 py-2 text-xs font-semibold text-red-600 hover:bg-red-50" @click="removeCondition(index)">Remover</button>
                    </div>
                    <button class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50" @click="addCondition">
                      + Adicionar regra
                    </button>
                  </div>
                </div>
              </section>

              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <h3 class="text-sm font-bold uppercase tracking-wide text-slate-800">6. Frequência e limite</h3>
                <div class="mt-3 grid gap-4 md:grid-cols-2">
                  <label class="text-sm font-semibold text-slate-600">
                    Início
                    <input v-model="builder.schedule.starts_at" type="datetime-local" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                  </label>
                  <label class="text-sm font-semibold text-slate-600">
                    Fim
                    <input v-model="builder.schedule.ends_at" type="datetime-local" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                  </label>
                  <label class="text-sm font-semibold text-slate-600">
                    Max visualizações por usuário
                    <input v-model.number="builder.frequency.max_views_per_user" type="number" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                  </label>
                  <label class="text-sm font-semibold text-slate-600">
                    Max visualizações por agência
                    <input v-model.number="builder.frequency.max_views_per_agency" type="number" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                  </label>
                  <label class="text-sm font-semibold text-slate-600">
                    Mostrar novamente após fechar
                    <select v-model="builder.frequency.dismiss_mode" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm">
                      <option value="hide_forever">nunca</option>
                      <option value="hide_for_days">depois de X dias</option>
                    </select>
                  </label>
                  <label v-if="builder.frequency.dismiss_mode === 'hide_for_days'" class="text-sm font-semibold text-slate-600">
                    Dias para reexibir
                    <input v-model.number="builder.frequency.show_again_after_dismiss_days" type="number" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
                  </label>
                </div>
              </section>

              <div class="flex items-center justify-end gap-2">
                <button class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="closeEditor">
                  Cancelar
                </button>
                <button class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="testEligibility">
                  {{ eligibilityLoading ? "Testando..." : "Testar elegibilidade" }}
                </button>
                <button class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800" @click="saveBanner">
                  Salvar banner
                </button>
              </div>
            </div>

            <aside class="space-y-4 md:max-w-[420px] md:justify-self-end md:w-full md:self-start">
              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Preview</p>
                <div class="mt-3">
                  <SystemBanner
                    :title="builder.content.title || 'Título do banner'"
                    :subtitle="builder.content.subtitle || 'Subtítulo do banner'"
                    :has-icon="builder.content.show_icon"
                    :icon-name="builder.content.icon"
                    :background-variant="builder.content.background"
                    :has-cta="builder.cta.enabled"
                    :cta-label="builder.cta.label || 'Conectar Pixel'"
                    :dismissible="builder.content.dismissible"
                  />
                </div>
              </section>

              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Resumo</p>
                <ul class="mt-3 space-y-2 text-sm text-slate-700">
                  <li><b>Local:</b> {{ builder.identification.placement }}</li>
                  <li><b>Público:</b> {{ builder.audience.mode }}</li>
                  <li><b>CTA:</b> {{ builder.cta.enabled ? builder.cta.type : "desativado" }}</li>
                  <li><b>Período:</b> {{ builder.schedule.starts_at || "sem início" }} → {{ builder.schedule.ends_at || "sem fim" }}</li>
                  <li><b>Regras:</b> {{ builder.rules.conditions.length }} condição(ões) / {{ builder.rules.logic }}</li>
                </ul>
              </section>

              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Avisos</p>
                <div class="mt-3 space-y-2 text-xs">
                  <p v-if="builder.audience.mode === 'all_users'" class="rounded-lg bg-amber-50 px-3 py-2 font-semibold text-amber-700">
                    Este banner será exibido para todos os usuários elegíveis ao local.
                  </p>
                  <p v-if="!builder.schedule.ends_at" class="rounded-lg bg-sky-50 px-3 py-2 font-semibold text-sky-700">
                    Este banner não possui regra de fim.
                  </p>
                  <p v-if="builder.audience.plans.length" class="rounded-lg bg-emerald-50 px-3 py-2 font-semibold text-emerald-700">
                    Este banner está segmentado para planos: {{ builder.audience.plans.join(", ") }}.
                  </p>
                </div>
              </section>

              <section class="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Teste de elegibilidade</p>
                <div class="mt-3 space-y-2 text-xs">
                  <p v-if="!eligibilityResult" class="rounded-lg bg-slate-50 px-3 py-2 font-semibold text-slate-600">
                    Clique em "Testar elegibilidade" para validar este banner.
                  </p>
                  <div v-else>
                    <p :class="eligibilityResult.eligible ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'" class="rounded-lg px-3 py-2 font-semibold">
                      {{ eligibilityResult.eligible ? "Elegível no contexto atual" : "Não elegível no contexto atual" }}
                    </p>
                    <ul class="mt-2 space-y-1">
                      <li v-for="reason in eligibilityResult.reasons" :key="reason" class="rounded-md bg-slate-50 px-2 py-1 text-slate-600">
                        {{ reason }}
                      </li>
                    </ul>
                  </div>
                </div>
              </section>
            </aside>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import api from "../../services/api";
import SystemBanner from "../../components/admin/SystemBanner.vue";

type BannerListItem = {
  id: number;
  internal_name: string;
  title: string;
  subtitle: string | null;
  is_active: boolean;
  priority: number;
  has_icon: boolean;
  icon_name: string | null;
  background_variant: string;
  dismissible: boolean;
  has_cta: boolean;
  cta_label: string | null;
  cta_type: string | null;
  cta_target: string | null;
  placement: string;
  target_plans: string[] | null;
  target_agency_ids: number[] | null;
  starts_at: string | null;
  ends_at: string | null;
  dismiss_behavior?: string | null;
  dismiss_duration_days?: number | null;
  max_views_per_user?: number | null;
  max_views_per_agency?: number | null;
  rule_config?: Record<string, unknown> | null;
  impressions: number;
  clicks: number;
  ctr: number;
};

type RuleCondition = { field: string; operator: string; value: string };
type AgencyOption = { id: number; name: string; slug: string };
type EligibilityResult = { eligible: boolean; reasons: string[] };

const filters = reactive({
  q: "",
  status: "all",
  placement: "",
  plan: ""
});

const banners = ref<BannerListItem[]>([]);
const actionsMenuOpenId = ref<number | null>(null);
const actionsMenuPosition = ref({ top: 0, left: 0 });
const editorOpen = ref(false);
const editingId = ref<number | null>(null);
const agencySearchQuery = ref("");
const agencySearchLoading = ref(false);
const agencyOptions = ref<AgencyOption[]>([]);
const eligibilityLoading = ref(false);
const eligibilityResult = ref<EligibilityResult | null>(null);
const currentActionBanner = computed(() => banners.value.find(item => item.id === actionsMenuOpenId.value) || null);

const iconOptions = [
  "TrendingUp",
  "Megaphone",
  "AlertCircle",
  "Sparkles",
  "Zap",
  "Globe",
  "Users",
  "CreditCard",
  "Calendar",
  "Settings",
  "ExternalLink",
  "CheckCircle"
];

const planOptions = [
  { label: "Free", value: "free" },
  { label: "Essencial", value: "essencial" },
  { label: "Growth", value: "growth" },
  { label: "Infinity", value: "infinity" },
  { label: "Teste", value: "teste" }
];

const roleOptions = [
  { label: "Admin da agência", value: "agency_admin" },
  { label: "Funcionário", value: "agency_staff" },
  { label: "Todos", value: "all" }
];

const internalRouteOptions = [
  { label: "Dashboard", value: "/admin/dashboard" },
  { label: "Leads / Kanban", value: "/admin/leads/opportunities" },
  { label: "Produtos (Páginas)", value: "/admin/pages" },
  { label: "Criar produto", value: "/admin/pages" },
  { label: "Vendas", value: "/admin/leads/opportunities" },
  { label: "Financeiro", value: "/admin/planos" },
  { label: "Configurações", value: "/admin/agency" },
  { label: "Integrações", value: "/admin/integracoes" },
  { label: "Pixel / Tracking", value: "/admin/integracoes" },
  { label: "Domínio próprio", value: "/admin/domains" },
  { label: "Checkout", value: "/admin/planos" },
  { label: "Assinatura / Plano", value: "/admin/planos" },
  { label: "Equipe / Usuários", value: "/admin/administracao/usuarios" },
  { label: "Central de ajuda", value: "/admin/aulas" }
];

const ruleFields = [
  { label: "Plano é", value: "plan" },
  { label: "Trial ativo", value: "trial_active" },
  { label: "Assinatura ativa", value: "subscription_active" },
  { label: "Assinatura expira em X dias", value: "subscription_expires_days" },
  { label: "Não configurou pixel", value: "pixel_configured" },
  { label: "Não configurou domínio", value: "custom_domain_configured" },
  { label: "Não tem leads", value: "leads_count" },
  { label: "Não tem vendas", value: "sales_count" },
  { label: "Criado há menos de X dias", value: "agency_age_days_lte" },
  { label: "Último login há mais de X dias", value: "last_login_days_gte" },
  { label: "Usuário já clicou no banner", value: "user_clicked_banner" },
  { label: "Usuário fechou o banner", value: "user_dismissed_banner" }
];

const operatorOptions = [
  { label: "igual", value: "equals" },
  { label: "diferente", value: "not_equals" },
  { label: "maior que", value: "gt" },
  { label: "menor que", value: "lt" },
  { label: "maior ou igual", value: "gte" },
  { label: "menor ou igual", value: "lte" },
  { label: "contém", value: "contains" },
  { label: "não contém", value: "not_contains" },
  { label: "existe", value: "exists" },
  { label: "não existe", value: "not_exists" }
];

const buildInitialBuilder = () => ({
  identification: {
    internal_name: "",
    is_active: true,
    priority: 0,
    placement: "dashboard"
  },
  content: {
    title: "",
    subtitle: "",
    show_icon: true,
    icon: "TrendingUp",
    dismissible: true,
    background: "green_gradient"
  },
  cta: {
    enabled: true,
    label: "Conectar Pixel",
    type: "internal_route",
    internal_target: "/admin/integracoes",
    custom_route: "",
    external_url: "",
    modal_target: "connect_pixel",
    system_action: "open_pixel_connection",
    open_new_tab: false
  },
  audience: {
    mode: "all_users",
    plans: [] as string[],
    agency_ids: [] as number[],
    excluded_agency_ids: [] as number[],
    roles: [] as string[]
  },
  rules: {
    logic: "AND",
    conditions: [] as RuleCondition[]
  },
  schedule: {
    starts_at: "",
    ends_at: ""
  },
  frequency: {
    max_views_per_user: null as number | null,
    max_views_per_agency: null as number | null,
    dismiss_mode: "hide_forever",
    show_again_after_dismiss_days: null as number | null,
    dismiss_scope: "user"
  }
});

const builder = reactive(buildInitialBuilder());

const formatDate = (value?: string | null) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleDateString("pt-BR");
};

const normalizeDateTime = (value: string) => (value ? new Date(value).toISOString() : null);
const upsertAgencyOptions = (items: AgencyOption[]) => {
  const map = new Map<number, AgencyOption>();
  for (const item of agencyOptions.value) map.set(item.id, item);
  for (const item of items) map.set(item.id, item);
  agencyOptions.value = Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
};

const selectedAgencyIdsSet = computed(() => new Set(builder.audience.agency_ids));
const selectedExcludedAgencyIdsSet = computed(() => new Set(builder.audience.excluded_agency_ids));

const availableAgencyOptions = computed(() =>
  agencyOptions.value.filter(
    item => !selectedAgencyIdsSet.value.has(item.id) && !selectedExcludedAgencyIdsSet.value.has(item.id)
  )
);

const selectedAgencyLabels = computed(() =>
  builder.audience.agency_ids.map(id => agencyOptions.value.find(item => item.id === id) || { id, name: `Agência #${id}`, slug: "" })
);

const excludedAgencyLabels = computed(() =>
  builder.audience.excluded_agency_ids.map(id => agencyOptions.value.find(item => item.id === id) || { id, name: `Agência #${id}`, slug: "" })
);

const searchAgencies = async (q = "") => {
  agencySearchLoading.value = true;
  try {
    const { data } = await api.get<Array<{ id: number; name: string; slug: string }>>("/admin/agencies/search", {
      params: { q, limit: 50 }
    });
    upsertAgencyOptions((data || []).map(item => ({ id: item.id, name: item.name, slug: item.slug })));
  } finally {
    agencySearchLoading.value = false;
  }
};

const addAudienceAgency = (agencyId: number) => {
  if (!builder.audience.agency_ids.includes(agencyId)) {
    builder.audience.agency_ids.push(agencyId);
  }
  builder.audience.excluded_agency_ids = builder.audience.excluded_agency_ids.filter(id => id !== agencyId);
};

const addExcludedAgency = (agencyId: number) => {
  if (!builder.audience.excluded_agency_ids.includes(agencyId)) {
    builder.audience.excluded_agency_ids.push(agencyId);
  }
  builder.audience.agency_ids = builder.audience.agency_ids.filter(id => id !== agencyId);
};

const removeAudienceAgency = (agencyId: number) => {
  builder.audience.agency_ids = builder.audience.agency_ids.filter(id => id !== agencyId);
};

const removeExcludedAgency = (agencyId: number) => {
  builder.audience.excluded_agency_ids = builder.audience.excluded_agency_ids.filter(id => id !== agencyId);
};

const togglePlan = (plan: string) => {
  const idx = builder.audience.plans.indexOf(plan);
  if (idx >= 0) builder.audience.plans.splice(idx, 1);
  else builder.audience.plans.push(plan);
};

const toggleRole = (role: string) => {
  const idx = builder.audience.roles.indexOf(role);
  if (idx >= 0) builder.audience.roles.splice(idx, 1);
  else builder.audience.roles.push(role);
};

const addCondition = () => {
  builder.rules.conditions.push({ field: "pixel_configured", operator: "equals", value: "false" });
};

const removeCondition = (index: number) => {
  builder.rules.conditions.splice(index, 1);
};

const loadBanners = async () => {
  const params: Record<string, string | boolean> = {};
  if (filters.q.trim()) params.q = filters.q.trim();
  if (filters.status === "active") params.is_active = true;
  if (filters.status === "inactive") params.is_active = false;
  if (filters.placement) params.placement = filters.placement;
  if (filters.plan) params.plan = filters.plan;
  const { data } = await api.get<{ items: BannerListItem[] }>("/admin/system-banners", { params });
  banners.value = data.items || [];
};

const resetBuilder = () => {
  Object.assign(builder, buildInitialBuilder());
  eligibilityResult.value = null;
};

const openCreate = () => {
  editingId.value = null;
  resetBuilder();
  editorOpen.value = true;
  void searchAgencies("");
};

const resolveBuilderFromBanner = (item: BannerListItem) => {
  const rulesPayload = (item.rule_config || {}) as { logic?: string; conditions?: RuleCondition[]; audience?: any; cta?: any };
  const ctaFromRule = rulesPayload.cta || {};
  const audienceFromRule = rulesPayload.audience || {};
  const targetPlans = item.target_plans || [];
  const targetAgencyIds = item.target_agency_ids || [];
  const ctaType = item.cta_type || "none";
  const internalTarget = ctaType === "internal_route" ? item.cta_target || "/admin/integracoes" : "/admin/integracoes";
  const externalUrl = ctaType === "external_url" ? item.cta_target || "" : "";

  Object.assign(builder, {
    identification: {
      internal_name: item.internal_name,
      is_active: item.is_active,
      priority: item.priority,
      placement: item.placement
    },
    content: {
      title: item.title,
      subtitle: item.subtitle || "",
      show_icon: item.has_icon,
      icon: item.icon_name || "TrendingUp",
      dismissible: item.dismissible,
      background: item.background_variant
    },
    cta: {
      enabled: item.has_cta,
      label: item.cta_label || "Conectar Pixel",
      type: ctaType === "none" ? "none" : ctaType,
      internal_target: internalTarget,
      custom_route: "",
      external_url: externalUrl,
      modal_target: ctaFromRule.modal_target || "connect_pixel",
      system_action: ctaFromRule.system_action || "open_pixel_connection",
      open_new_tab: Boolean(ctaFromRule.open_new_tab)
    },
    audience: {
      mode: audienceFromRule.mode || (targetPlans.length ? "specific_plans" : "all_users"),
      plans: [...targetPlans],
      agency_ids: [...targetAgencyIds],
      excluded_agency_ids: [...(audienceFromRule.excluded_agency_ids || [])],
      roles: audienceFromRule.roles || []
    },
    rules: {
      logic: rulesPayload.logic || "AND",
      conditions: rulesPayload.conditions || []
    },
    schedule: {
      starts_at: item.starts_at ? item.starts_at.slice(0, 16) : "",
      ends_at: item.ends_at ? item.ends_at.slice(0, 16) : ""
    },
    frequency: {
      max_views_per_user: item.max_views_per_user || null,
      max_views_per_agency: item.max_views_per_agency || null,
      dismiss_mode: item.dismiss_behavior || "hide_forever",
      show_again_after_dismiss_days: item.dismiss_duration_days || null,
      dismiss_scope: "user"
    }
  });
};

const openEdit = (item: BannerListItem) => {
  editingId.value = item.id;
  resolveBuilderFromBanner(item);
  editorOpen.value = true;
  const knownIds = [...builder.audience.agency_ids, ...builder.audience.excluded_agency_ids];
  upsertAgencyOptions(knownIds.map(id => ({ id, name: `Agência #${id}`, slug: "" })));
  void searchAgencies("");
};

const closeEditor = () => {
  editorOpen.value = false;
  eligibilityResult.value = null;
};

const resolveCtaPayload = () => {
  if (!builder.cta.enabled || builder.cta.type === "none") {
    return { has_cta: false, cta_type: "none", cta_label: null, cta_target: null };
  }
  if (builder.cta.type === "internal_route") {
    const target = builder.cta.internal_target === "__custom__" ? builder.cta.custom_route : builder.cta.internal_target;
    return { has_cta: true, cta_type: "internal_route", cta_label: builder.cta.label, cta_target: target };
  }
  if (builder.cta.type === "external_url") {
    return { has_cta: true, cta_type: "external_url", cta_label: builder.cta.label, cta_target: builder.cta.external_url };
  }
  return {
    has_cta: true,
    cta_type: "none",
    cta_label: builder.cta.label,
    cta_target: builder.cta.type === "open_modal" ? builder.cta.modal_target : builder.cta.system_action
  };
};

const resolveInternalName = () => {
  const raw = builder.identification.internal_name.trim();
  if (raw) return raw;
  const titleBased = builder.content.title.trim();
  if (titleBased) return titleBased;
  return "banner-sem-nome";
};

const buildBannerPayload = () => {
  const cta = resolveCtaPayload();
  const targetAgencyIds = [...builder.audience.agency_ids];
  const excludedAgencyIds = [...builder.audience.excluded_agency_ids];
  return {
    internal_name: resolveInternalName(),
    title: builder.content.title.trim(),
    subtitle: builder.content.subtitle.trim() || null,
    is_active: builder.identification.is_active,
    priority: Number(builder.identification.priority || 0),
    placement: builder.identification.placement,
    has_icon: builder.content.show_icon,
    icon_name: builder.content.show_icon ? builder.content.icon : null,
    background_variant: builder.content.background,
    dismissible: builder.content.dismissible,
    dismiss_behavior: builder.frequency.dismiss_mode,
    dismiss_duration_days:
      builder.frequency.dismiss_mode === "hide_for_days" ? Number(builder.frequency.show_again_after_dismiss_days || 0) || 7 : null,
    starts_at: normalizeDateTime(builder.schedule.starts_at),
    ends_at: normalizeDateTime(builder.schedule.ends_at),
    target_plans: builder.audience.plans.length ? builder.audience.plans : null,
    target_agency_ids: targetAgencyIds.length ? targetAgencyIds : null,
    target_user_roles: builder.audience.roles.length ? builder.audience.roles : null,
    max_views_per_user: builder.frequency.max_views_per_user || null,
    max_views_per_agency: builder.frequency.max_views_per_agency || null,
    hide_after_click: builder.rules.conditions.some(c => c.field === "user_clicked_banner" && c.operator === "equals" && c.value === "true"),
    ...cta,
    rule_config: {
      logic: builder.rules.logic,
      conditions: builder.rules.conditions,
      audience: {
        mode: builder.audience.mode,
        plans: builder.audience.plans,
        agency_ids: targetAgencyIds,
        excluded_agency_ids: excludedAgencyIds,
        roles: builder.audience.roles
      },
      cta: {
        type: builder.cta.type,
        internal_target: builder.cta.internal_target,
        modal_target: builder.cta.modal_target,
        system_action: builder.cta.system_action,
        open_new_tab: builder.cta.open_new_tab
      },
      frequency: {
        dismiss_scope: builder.frequency.dismiss_scope,
        show_again_after_dismiss_days: builder.frequency.show_again_after_dismiss_days
      }
    }
  };
};

const testEligibility = async () => {
  eligibilityLoading.value = true;
  eligibilityResult.value = null;
  try {
    const payload = buildBannerPayload();
    const { data } = await api.post<EligibilityResult>("/admin/system-banners/test-eligibility", {
      ...payload,
      context: {
        placement: builder.identification.placement,
        plan: builder.audience.plans[0] || null,
        agency_id: builder.audience.agency_ids[0] || null,
        role: builder.audience.roles[0] || "agency_admin"
      }
    });
    eligibilityResult.value = data;
  } finally {
    eligibilityLoading.value = false;
  }
};

const saveBanner = async () => {
  const payload = buildBannerPayload();
  if (editingId.value) {
    await api.patch(`/admin/system-banners/${editingId.value}`, payload);
  } else {
    await api.post("/admin/system-banners", payload);
  }
  editorOpen.value = false;
  await loadBanners();
};

const duplicateBanner = async (id: number) => {
  await api.post(`/admin/system-banners/${id}/duplicate`);
  await loadBanners();
};

const toggleActive = async (id: number) => {
  await api.post(`/admin/system-banners/${id}/toggle-active`);
  await loadBanners();
};

const removeBanner = async (id: number) => {
  if (!confirm("Excluir este banner?")) return;
  await api.delete(`/admin/system-banners/${id}`);
  await loadBanners();
};

const toggleActionsMenu = (id: number, event: MouseEvent) => {
  if (actionsMenuOpenId.value === id) {
    actionsMenuOpenId.value = null;
    return;
  }
  const target = event.currentTarget as HTMLElement | null;
  if (target) {
    const rect = target.getBoundingClientRect();
    const menuWidth = 160;
    const viewportWidth = window.innerWidth;
    const left = Math.min(rect.right - menuWidth, viewportWidth - menuWidth - 8);
    actionsMenuPosition.value = { top: rect.bottom + 8, left: Math.max(8, left) };
  }
  actionsMenuOpenId.value = id;
};

const closeActionsMenu = () => {
  actionsMenuOpenId.value = null;
};

const handleEdit = (item: BannerListItem) => {
  closeActionsMenu();
  openEdit(item);
};

const handleDuplicate = async (id: number) => {
  closeActionsMenu();
  await duplicateBanner(id);
};

const handleToggleActive = async (id: number) => {
  closeActionsMenu();
  await toggleActive(id);
};

const handleRemove = async (id: number) => {
  closeActionsMenu();
  await removeBanner(id);
};

const onGlobalClick = () => {
  closeActionsMenu();
};

onMounted(async () => {
  document.addEventListener("click", onGlobalClick);
  await loadBanners();
  await searchAgencies("");
});

onBeforeUnmount(() => {
  document.removeEventListener("click", onGlobalClick);
});
</script>





