<template>
  <div v-if="isBootstrappingAdminManagement" class="am-empty min-h-[60vh]">
    <div class="am-spinner"></div>
  </div>
  <div v-else class="admin-master-view admin-master-surface am-page w-full">
    <div v-if="error" class="am-notice am-tone-danger">
      <AmIcon name="alert" />
      <span>{{ error }}</span>
    </div>

    <!-- PAINEL -->
    <template v-if="activeTab === 'dashboard'">
      <AdminMasterHeader title="Painel da plataforma" subtitle="Assinaturas, receita e uso do Roteiro Online.">
        <div class="am-seg" role="group" aria-label="Período">
          <button
            v-for="option in periodOptions"
            :key="option.value"
            type="button"
            :class="{ on: days === option.value }"
            @click="days = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <button type="button" class="am-btn" @click="exportPdf">
          <AmIcon name="dl" />
          Exportar PDF
        </button>
      </AdminMasterHeader>

      <div v-if="days === 'custom'" class="am-card flex flex-wrap items-center gap-3 !py-3">
        <label class="am-label !mb-0" for="am-period-from">De</label>
        <input id="am-period-from" v-model="customStartDate" type="date" class="am-input !w-auto" />
        <label class="am-label !mb-0" for="am-period-to">até</label>
        <input id="am-period-to" v-model="customEndDate" type="date" class="am-input !w-auto" />
      </div>

      <section class="am-grid-4">
        <AdminMasterKpi icon="wallet" tone="success" label="MRR" :value="formatMoney(metrics?.mrr)" hint="Soma dos planos ativos" />
        <AdminMasterKpi icon="trend" tone="info" label="ARR estimado" :value="formatMoney(arrValue)" hint="MRR × 12" />
        <AdminMasterKpi icon="card" tone="violet" label="Faturamento total" :value="formatMoney(lifetimeRevenue)" hint="Desde o início" />
        <AdminMasterKpi
          icon="alert"
          tone="warning"
          label="Churn do mês"
          :value="formatPercent(monthlyChurnRate)"
          :hint="`${formatInt(metrics?.monthly_churn_cancelled ?? 0)} cancelamentos de ${formatInt(metrics?.monthly_churn_base ?? 0)}`"
        />
      </section>

      <section class="am-grid-3">
        <article v-for="item in platformTotals" :key="item.label" class="am-kpi flex items-center gap-3.5">
          <span class="am-tile am-tone-neutral !h-10 !w-10"><AmIcon :name="item.icon" /></span>
          <div class="min-w-0">
            <p class="am-kpi-label">{{ item.label }}</p>
            <p class="am-kpi-value !mt-0 !text-xl">{{ item.value }}</p>
          </div>
          <p class="am-kpi-hint ml-auto text-right">{{ item.hint }}</p>
        </article>
      </section>

      <section class="grid gap-3.5 xl:grid-cols-[1.6fr_1fr]">
        <div class="am-card">
          <div class="am-card-head flex-wrap">
            <div>
              <h2 class="am-card-title">Assinaturas por dia</h2>
              <p class="am-card-sub">{{ adminPeriodLabel }} · clique na legenda para esconder uma linha</p>
            </div>
            <div class="flex flex-wrap items-center gap-3.5 text-xs font-semibold">
              <button type="button" class="legend-toggle-sub inline-flex items-center gap-1.5 text-[color:var(--chart-1)]" :class="{ off: !visibleSubscriptionSeries.new }" @click="toggleSubscriptionSeries('new')"><span class="h-2 w-2 rounded-full bg-chart-1"></span>Novas {{ formatInt(subscriptionsTotals.new) }}</button>
              <button type="button" class="legend-toggle-sub inline-flex items-center gap-1.5 text-[color:var(--chart-3)]" :class="{ off: !visibleSubscriptionSeries.renewed }" @click="toggleSubscriptionSeries('renewed')"><span class="h-2 w-2 rounded-full bg-chart-3"></span>Renovadas {{ formatInt(subscriptionsTotals.renewed) }}</button>
              <button type="button" class="legend-toggle-sub inline-flex items-center gap-1.5 text-[color:var(--chart-5)]" :class="{ off: !visibleSubscriptionSeries.cancelled }" @click="toggleSubscriptionSeries('cancelled')"><span class="h-2 w-2 rounded-full bg-chart-5"></span>Canceladas {{ formatInt(subscriptionsTotals.cancelled) }}</button>
            </div>
          </div>

          <div v-if="subscriptionChartPoints.length">
            <div class="relative">
              <div class="pointer-events-none absolute inset-0">
                <div
                  v-for="line in newUsersGridLines"
                  :key="'grid-' + line"
                  class="absolute left-0 right-0 border-t border-dashed border-border"
                  :style="{ top: line + 'px' }"
                ></div>
              </div>
              <div class="relative" :style="{ height: newUsersChartHeight + 'px' }">
                <svg :viewBox="`0 0 ${newUsersChartWidth} ${newUsersChartHeight}`" preserveAspectRatio="none" class="h-full w-full">
                  <defs>
                    <linearGradient id="g-sub-new" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="var(--chart-1)" stop-opacity="0.22" />
                      <stop offset="100%" stop-color="var(--chart-1)" stop-opacity="0.01" />
                    </linearGradient>
                    <linearGradient id="g-sub-renewed" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="var(--chart-3)" stop-opacity="0.18" />
                      <stop offset="100%" stop-color="var(--chart-3)" stop-opacity="0.01" />
                    </linearGradient>
                    <linearGradient id="g-sub-cancelled" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="var(--chart-5)" stop-opacity="0.16" />
                      <stop offset="100%" stop-color="var(--chart-5)" stop-opacity="0.01" />
                    </linearGradient>
                  </defs>
                  <path v-if="visibleSubscriptionSeries.renewed && subscriptionRenewedAreaPath" :d="subscriptionRenewedAreaPath" fill="url(#g-sub-renewed)" />
                  <path v-if="visibleSubscriptionSeries.new && subscriptionNewAreaPath" :d="subscriptionNewAreaPath" fill="url(#g-sub-new)" />
                  <path v-if="visibleSubscriptionSeries.cancelled && subscriptionCancelledAreaPath" :d="subscriptionCancelledAreaPath" fill="url(#g-sub-cancelled)" />
                  <path v-if="visibleSubscriptionSeries.renewed" :d="subscriptionRenewedPath" fill="none" stroke="var(--chart-3)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
                  <path v-if="visibleSubscriptionSeries.new" :d="subscriptionNewPath" fill="none" stroke="var(--chart-1)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
                  <path v-if="visibleSubscriptionSeries.cancelled" :d="subscriptionCancelledPath" fill="none" stroke="var(--chart-5)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
                  <rect
                    v-for="hit in subscriptionHitAreas"
                    :key="`sub-hit-${hit.index}`"
                    :x="hit.x"
                    y="0"
                    :width="hit.width"
                    :height="newUsersChartHeight"
                    fill="transparent"
                    @mouseenter="showSubscriptionTooltip(hit.index, $event)"
                    @mousemove="moveSubscriptionTooltip(hit.index, $event)"
                    @mouseleave="hideSubscriptionTooltip"
                  />
                </svg>
                <div v-if="subscriptionTooltip.visible" class="chart-tooltip" :style="subscriptionTooltipStyle">
                  <p class="chart-tooltip-date">{{ subscriptionTooltip.label }}</p>
                  <p class="text-[color:var(--chart-1)]">Novas: {{ subscriptionTooltip.newValue }}</p>
                  <p class="text-[color:var(--chart-3)]">Renovadas: {{ subscriptionTooltip.renewedValue }}</p>
                  <p class="text-[color:var(--chart-5)]">Canceladas: {{ subscriptionTooltip.cancelledValue }}</p>
                </div>
              </div>
            </div>
            <div class="mt-2 text-[11px] text-muted-foreground">
              <div v-if="compactNewUsersLabels && subscriptionLabelRange" class="flex items-center justify-between">
                <span>{{ subscriptionLabelRange.start }}</span>
                <span>{{ subscriptionLabelRange.end }}</span>
              </div>
              <div v-else class="flex flex-wrap justify-between gap-2">
                <span v-for="point in subscriptionChartPoints" :key="point.label + '-label'">{{ point.label }}</span>
              </div>
            </div>
          </div>
          <div v-else class="am-empty h-56">Sem dados de assinatura no período.</div>
        </div>

        <div class="am-card">
          <div class="am-card-head">
            <div>
              <h2 class="am-card-title">Planos ativos</h2>
              <p class="am-card-sub">{{ formatInt(planDistributionTotal) }} contas</p>
            </div>
          </div>
          <div v-if="planDistribution.length" class="space-y-3">
            <div v-for="item in planDistribution" :key="item.plan">
              <div class="mb-1.5 flex items-center justify-between text-[13px]">
                <span class="flex items-center gap-2">
                  <i class="h-2 w-2 rounded-[3px]" :style="{ background: item.color }"></i>
                  {{ item.label }}
                </span>
                <b class="am-num">{{ formatInt(item.count) }} <span class="font-medium text-muted-foreground">· {{ item.percent }}%</span></b>
              </div>
              <div class="am-bar"><i :style="{ width: item.bar + '%', background: item.color }"></i></div>
            </div>
          </div>
          <p v-else class="am-empty">Sem dados ainda.</p>
        </div>
      </section>

      <section class="am-card">
        <div class="am-card-head">
          <div>
            <h2 class="am-card-title">Precisa de atenção</h2>
            <p class="am-card-sub">Atalhos para o que pede ação hoje</p>
          </div>
        </div>
        <div class="am-grid-4">
          <RouterLink
            v-for="item in attentionItems"
            :key="item.id"
            :to="item.to"
            class="flex items-start gap-3 rounded-[14px] bg-muted p-3 transition hover:ring-1 hover:ring-border"
          >
            <span class="am-tile !h-8 !w-8" :class="`am-tone-${item.count ? item.tone : 'neutral'}`"><AmIcon :name="item.icon" /></span>
            <div class="min-w-0">
              <b class="text-[13.5px]">{{ item.title }}</b>
              <p class="am-card-sub !mt-0">{{ item.description }}</p>
              <p class="mt-1.5 text-xs font-semibold text-primary">Abrir {{ item.target }} →</p>
            </div>
          </RouterLink>
        </div>
      </section>
    </template>

    <!-- AO VIVO -->
    <template v-else-if="activeTab === 'monitor'">
      <AdminMasterHeader title="Ao vivo" subtitle="Quem está usando o sistema agora (sessões ativas nos últimos 10 minutos).">
        <span v-if="monitorLastUpdated" class="am-sub !mt-0">Atualizado às {{ monitorLastUpdated }}</span>
        <button type="button" class="am-btn" :disabled="onlineSessionsLoading" @click="loadOnlineSessions(true)">
          <AmIcon name="refresh" :class="onlineSessionsLoading ? 'animate-spin' : ''" />
          {{ onlineSessionsLoading ? "Atualizando..." : "Atualizar" }}
        </button>
      </AdminMasterHeader>

      <section class="am-grid-4">
        <AdminMasterKpi icon="pulse" tone="success" label="Online agora" :value="formatInt(onlineSessionsMeta?.unique_users ?? 0)" :hint="`${formatInt(onlineSessionsMeta?.total_online ?? 0)} sessões abertas`" />
        <AdminMasterKpi icon="monitor" tone="info" label="No computador" :value="formatInt(monitorDeviceSplit.desktop)" :hint="`${formatInt(monitorDeviceSplit.mobile)} no celular`" />
        <AdminMasterKpi icon="pages" tone="violet" label="No editor de página" :value="formatInt(monitorInEditor)" hint="Editando uma página agora" />
        <AdminMasterKpi icon="history" tone="neutral" label="Monitor" :value="monitorStatusLabel" hint="Atualiza sozinho a cada 20 segundos" />
      </section>

      <section class="am-card am-card-flush">
        <div v-if="onlineSessionsLoading && !onlineSessions.length" class="am-empty">
          <div class="am-spinner"></div>
          Carregando sessões ativas...
        </div>
        <div v-else-if="onlineSessionsError" class="am-empty !text-status-danger-foreground">{{ onlineSessionsError }}</div>
        <div v-else-if="!onlineSessions.length" class="am-empty">Ninguém está online neste momento.</div>
        <div v-else class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Pessoa</th>
                <th>Plano</th>
                <th>Onde está</th>
                <th>Dispositivo</th>
                <th>Última ação</th>
                <th>Na sessão</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in onlineSessions" :key="session.session_id">
                <td>
                  <div class="am-who">
                    <span class="am-avatar relative">
                      {{ initials(session.user_name) }}
                      <i class="absolute -bottom-px -right-px h-2.5 w-2.5 rounded-full border-2 border-card bg-status-success-foreground"></i>
                    </span>
                    <div class="min-w-0">
                      <b class="truncate">{{ session.user_name }}</b>
                      <small class="truncate">{{ session.user_email }}</small>
                    </div>
                  </div>
                </td>
                <td><span class="am-badge" :class="planToneClass(session.user_plan)">{{ planLabel(session.user_plan) }}</span></td>
                <td>
                  <b class="font-semibold">{{ pathLabel(session.last_path) }}</b>
                  <div v-if="session.last_path" class="am-mono am-muted max-w-[260px] truncate">{{ session.last_path }}</div>
                </td>
                <td>
                  {{ session.device_label || "Desconhecido" }}<span v-if="session.client_name"> · {{ session.client_name }}</span>
                  <span v-if="session.active_sessions > 1" class="am-badge am-tone-neutral ml-1">{{ session.active_sessions }} sessões</span>
                  <div v-if="session.ip_address" class="am-mono am-muted">{{ session.ip_address }}</div>
                </td>
                <td class="am-num">{{ formatRelativeMoment(session.last_seen_at) }}</td>
                <td class="am-num">{{ formatDurationSince(session.created_at) }}</td>
                <td class="am-right">
                  <button
                    type="button"
                    class="am-btn am-btn-sm"
                    :disabled="revokingUserId === session.user_id"
                    @click="revokeUserSessions(session)"
                  >
                    <AmIcon name="logout" />
                    {{ revokingUserId === session.user_id ? "Deslogando..." : "Deslogar" }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <!-- USERS -->
    <template v-else-if="activeTab === 'users'">
      <AdminMasterHeader title="Usuários" subtitle="Contas do Roteiro Online: plano, cobrança, validade e uso.">
        <button type="button" class="am-btn am-btn-primary" @click="openCreateUserDialog">
          <AmIcon name="plus" />
          Criar usuário
        </button>
      </AdminMasterHeader>

      <section class="am-card am-card-flush">
        <div class="am-toolbar">
          <button
            v-for="option in userQuickFilterOptions"
            :key="option.id"
            type="button"
            class="am-chip"
            :class="{ on: userQuickFilter === option.id }"
            @click="userQuickFilter = option.id"
          >
            {{ option.label }}
            <span class="am-count am-num">{{ formatInt(userQuickFilterCounts[option.id]) }}</span>
          </button>
        </div>
        <div class="am-toolbar">
          <label class="am-search">
            <AmIcon name="search" />
            <input v-model="userFilters.name" type="search" placeholder="Buscar por nome ou e-mail" aria-label="Buscar usuário" />
          </label>
          <select v-model="userPlanSelect" class="am-select" aria-label="Filtrar por plano">
            <option value="">Plano: todos</option>
            <option v-for="plan in userPlanOptions" :key="plan" :value="plan">{{ planLabel(plan) }}</option>
          </select>
          <select v-model="userGatewaySelect" class="am-select" aria-label="Filtrar por cobrança">
            <option value="">Cobrança: todas</option>
            <option v-for="gateway in userGatewayOptions" :key="gateway" :value="gateway">
              {{ gateway === "__none" ? "Sem cobrança" : gatewayLabel(gateway) }}
            </option>
          </select>
          <button type="button" class="am-chip" :class="{ on: showMoreUserFilters || moreUserFiltersActive }" @click="showMoreUserFilters = !showMoreUserFilters">
            Mais filtros
            <span v-if="moreUserFiltersActive" class="am-count">ativos</span>
          </button>
        </div>
        <div v-if="showMoreUserFilters" class="am-toolbar grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div class="am-field">
            <label for="am-f-whats">WhatsApp</label>
            <input id="am-f-whats" v-model="userFilters.whatsapp" type="text" class="am-input" placeholder="Telefone" />
          </div>
          <div class="am-field">
            <label for="am-f-agency">Agência</label>
            <select id="am-f-agency" v-model="userAgencySelect" class="am-input">
              <option value="">Todas</option>
              <option v-for="option in agencyFilterOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </div>
          <div class="am-field">
            <label>Páginas publicadas</label>
            <div class="flex gap-2">
              <input v-model="userFilters.activeMin" type="number" min="0" class="am-input" placeholder="Mín." aria-label="Mínimo de páginas publicadas" />
              <input v-model="userFilters.activeMax" type="number" min="0" class="am-input" placeholder="Máx." aria-label="Máximo de páginas publicadas" />
            </div>
          </div>
          <div class="am-field">
            <label>Rascunhos</label>
            <div class="flex gap-2">
              <input v-model="userFilters.draftMin" type="number" min="0" class="am-input" placeholder="Mín." aria-label="Mínimo de rascunhos" />
              <input v-model="userFilters.draftMax" type="number" min="0" class="am-input" placeholder="Máx." aria-label="Máximo de rascunhos" />
            </div>
          </div>
          <div class="am-field">
            <label>Validade entre</label>
            <div class="flex gap-2">
              <input v-model="userFilters.validFrom" type="date" class="am-input" aria-label="Validade a partir de" />
              <input v-model="userFilters.validTo" type="date" class="am-input" aria-label="Validade até" />
            </div>
          </div>
          <div class="am-field">
            <label>Entrou entre</label>
            <div class="flex gap-2">
              <input v-model="userFilters.createdFrom" type="date" class="am-input" aria-label="Entrou a partir de" />
              <input v-model="userFilters.createdTo" type="date" class="am-input" aria-label="Entrou até" />
            </div>
          </div>
          <div class="flex items-end">
            <button type="button" class="am-btn am-btn-sm" @click="clearAllUserFilters">Limpar filtros</button>
          </div>
        </div>

        <div class="am-table-wrap">
          <table class="am-table interactive-table">
            <thead>
              <tr>
                <th v-for="column in userListColumns" :key="column.key" :class="column.class">
                  <button
                    v-if="column.sort"
                    type="button"
                    class="inline-flex items-center gap-1 uppercase"
                    @click="toggleColumnSort(column.sort)"
                  >
                    {{ column.label }}
                    <span v-if="userSort.key === column.sort" aria-hidden="true">{{ userSort.direction === "asc" ? "↑" : "↓" }}</span>
                  </button>
                  <span v-else>{{ column.label }}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <template v-for="u in filteredUsers" :key="u.id">
                <tr class="cursor-pointer" @click="toggleUserRow(u.id)">
                  <td>
                    <div class="am-who">
                      <span class="am-avatar">{{ initials(u.name) }}</span>
                      <div class="min-w-0">
                        <b class="max-w-[220px] truncate">{{ u.name }}</b>
                        <small class="max-w-[220px] truncate">{{ u.email }}</small>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span class="block max-w-[180px] truncate">{{ u.agency_name || "Sem agência" }}</span>
                    <small v-if="u.whatsapp" class="am-muted block text-xs">{{ u.whatsapp }}</small>
                  </td>
                  <td>
                    <span class="am-badge" :class="planToneClass(u.plan)">{{ planLabel(u.plan) }}</span>
                    <span v-if="u.trial_plan" class="am-badge am-tone-warning ml-1">Teste até {{ formatDate(u.trial_ends_at || undefined) }}</span>
                  </td>
                  <td>{{ u.subscription_provider ? gatewayLabel(u.subscription_provider) : "—" }}</td>
                  <td class="am-num">
                    {{ formatInt(u.active_pages ?? 0) }} {{ (u.active_pages ?? 0) === 1 ? "publicada" : "publicadas" }}
                    <span v-if="draftCount(u)" class="am-muted"> · {{ formatInt(draftCount(u)) }} {{ draftCount(u) === 1 ? "rascunho" : "rascunhos" }}</span>
                  </td>
                  <td class="am-num">
                    <span v-if="validityState(u) === 'expired'" class="am-badge am-tone-danger">Vencido · {{ formatDate(u.valid_until) }}</span>
                    <span v-else-if="validityState(u) === 'soon'" class="am-badge am-tone-warning">{{ formatDate(u.valid_until) }} · {{ daysLeftLabel(u.valid_until) }}</span>
                    <span v-else>{{ u.valid_until ? formatDate(u.valid_until) : "—" }}</span>
                  </td>
                  <td class="am-num">{{ formatDate(u.created_at) }}</td>
                  <td class="am-right" @click.stop>
                    <div class="relative inline-block" data-row-menu="true">
                      <button
                        type="button"
                        class="am-icon-btn"
                        :aria-label="`Ações de ${u.name}`"
                        :aria-expanded="rowMenuUserId === u.id"
                        @click="rowMenuUserId = rowMenuUserId === u.id ? null : u.id"
                      >
                        <AmIcon name="dots" />
                      </button>
                      <div v-if="rowMenuUserId === u.id" class="am-menu right-0 top-full mt-1">
                        <button type="button" @click="runUserMenu(() => (expandedUser = u.id))"><AmIcon name="eye" />Ver detalhes</button>
                        <button type="button" @click="runUserMenu(() => openValidityDialog(u))"><AmIcon name="cal" />Alterar validade</button>
                        <button v-if="!u.is_superuser" type="button" :disabled="granting === u.id || Boolean(u.trial_plan)" @click="runUserMenu(() => openTrialDialog(u))">
                          <AmIcon name="history" />{{ u.trial_plan ? "Teste já ativo" : "Liberar 7 dias de teste" }}
                        </button>
                        <button type="button" :disabled="!u.agency_id || !agencyStore.currentAgencyId" @click="runUserMenu(() => openLinkPageDialog(u))"><AmIcon name="link" />Vincular página</button>
                        <button v-if="canRefundUser(u)" type="button" :disabled="refundDialog.loading" @click="runUserMenu(() => openRefundDialog(u))"><AmIcon name="wallet" />Reembolsar</button>
                        <button v-if="!u.is_superuser" type="button" class="is-danger" @click="runUserMenu(() => openDeleteDialog(u))"><AmIcon name="trash" />Excluir usuário</button>
                      </div>
                    </div>
                  </td>
                </tr>

                <tr v-if="expandedUser === u.id" class="am-detail-row">
                  <td colspan="8" class="!bg-transparent">
                    <div class="am-user-detail">
                      <div class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                        <div class="copyable">
                          <p class="am-eyebrow">Contato</p>
                          <p class="mt-1 font-semibold">{{ u.name }}</p>
                          <p class="am-muted text-xs">{{ u.email }}</p>
                          <p class="am-muted text-xs">{{ u.whatsapp || "Sem telefone" }}</p>
                          <span v-if="u.is_superuser" class="am-badge am-tone-violet mt-2">Superusuário</span>
                        </div>

                        <div>
                          <p class="am-eyebrow">Agência</p>
                          <p class="mt-1 font-semibold">{{ u.agency_name || "Não vinculada" }}</p>
                          <p class="am-muted text-xs">{{ formatInt(u.active_pages ?? 0) }} páginas publicadas · Plano {{ planLabel(u.plan) }}</p>
                        </div>

                        <div class="space-y-1.5">
                          <p class="am-eyebrow">Assinatura</p>
                          <p class="text-xs">
                            <span class="am-muted">Situação:</span>
                            <span class="font-semibold"> {{ formatSubscriptionStatus(u) }}</span>
                          </p>
                          <p class="text-xs">
                            <span class="am-muted">Cobrança:</span>
                            <span class="font-semibold"> {{ subscriptionProviderLabel(u) }}</span>
                          </p>
                          <p class="text-xs">
                            <span class="am-muted">ID:</span>
                            <span class="am-mono"> {{ subscriptionProviderIdentifier(u) }}</span>
                          </p>
                          <p v-if="isCancelAtPeriodEnd(u)" class="text-xs font-semibold text-status-warning-foreground">
                            Cancelamento programado para {{ formatDate(u.valid_until) || "—" }}
                          </p>
                        </div>
                      </div>

                      <div class="mt-4 flex flex-wrap gap-2">
                        <div class="relative" data-subscription-action-menu="true">
                          <button type="button" class="am-btn am-btn-sm" @click.stop="toggleSubscriptionActionMenu(u.id, 'plan')">
                            Alterar plano
                            <AmIcon name="chevron" />
                          </button>
                          <div
                            v-if="subscriptionActionMenu.open && subscriptionActionMenu.userId === u.id && subscriptionActionMenu.kind === 'plan'"
                            class="am-menu left-0 top-full mt-1"
                          >
                            <button
                              v-for="option in adminPlanOptions"
                              :key="option.value"
                              type="button"
                              class="justify-between"
                              @click.stop="openSubscriptionActionDialog(u, 'plan', option)"
                            >
                              <span>{{ option.label }}</span>
                              <span v-if="option.value === u.plan" class="am-badge am-tone-success">Atual</span>
                            </button>
                          </div>
                        </div>
                        <div class="relative" data-subscription-action-menu="true">
                          <button type="button" class="am-btn am-btn-sm" @click.stop="toggleSubscriptionActionMenu(u.id, 'status')">
                            Alterar situação
                            <AmIcon name="chevron" />
                          </button>
                          <div
                            v-if="subscriptionActionMenu.open && subscriptionActionMenu.userId === u.id && subscriptionActionMenu.kind === 'status'"
                            class="am-menu left-0 top-full mt-1"
                          >
                            <button
                              v-for="option in adminSubscriptionStatusOptions"
                              :key="option.value"
                              type="button"
                              class="justify-between"
                              @click.stop="openSubscriptionActionDialog(u, 'status', option)"
                            >
                              <span>{{ option.label }}</span>
                              <span v-if="option.value === (u.subscription_status || '').toLowerCase()" class="am-badge am-tone-success">Atual</span>
                            </button>
                          </div>
                        </div>
                        <button type="button" class="am-btn am-btn-sm" @click.stop="openValidityDialog(u)">Alterar validade</button>
                        <button
                          type="button"
                          class="am-btn am-btn-sm"
                          :disabled="adminAsaasActionLoadingUserId === u.id || isCancelAtPeriodEnd(u)"
                          @click.stop="adminScheduleAsaasCancelAtPeriodEnd(u)"
                        >
                          {{ isCancelAtPeriodEnd(u) ? "Cancelamento agendado" : "Cancelar no fim da validade" }}
                        </button>
                        <button
                          v-if="isCancelAtPeriodEnd(u)"
                          type="button"
                          class="am-btn am-btn-sm"
                          :disabled="adminAsaasActionLoadingUserId === u.id"
                          @click.stop="adminCancelScheduledAsaasCancellation(u)"
                        >
                          Desfazer cancelamento programado
                        </button>
                        <button
                          type="button"
                          class="am-btn am-btn-sm am-btn-danger"
                          :disabled="adminAsaasActionLoadingUserId === u.id"
                          @click.stop="adminCancelAsaasImmediate(u)"
                        >
                          {{ adminAsaasActionLoadingUserId === u.id ? "Processando..." : "Cancelar agora" }}
                        </button>
                      </div>

                      <div class="mt-5">
                        <p class="am-eyebrow">Origem e UTMs</p>
                        <div v-if="u.tracking?.length" class="mt-2 space-y-2">
                          <div v-for="entry in u.tracking" :key="entry.id" class="rounded-xl border border-border p-3">
                            <div class="flex flex-wrap gap-1.5">
                              <span v-for="chip in buildUtmChips(entry)" :key="chip.label + chip.value" class="am-badge am-tone-neutral">
                                <span class="am-muted">{{ chip.label }}:</span>{{ chip.value }}
                              </span>
                            </div>
                            <p class="am-muted mt-2 text-[11px]">Capturado em {{ formatDateTime(entry.created_at) || "data desconhecida" }}</p>
                          </div>
                        </div>
                        <p v-else class="am-muted mt-2 text-xs">Nenhuma UTM registrada.</p>
                      </div>

                      <div class="mt-5 grid gap-4 xl:grid-cols-2">
                        <div>
                          <p class="am-eyebrow">Páginas publicadas</p>
                          <div v-if="u.published_pages?.length" class="mt-2 overflow-x-auto rounded-xl border border-border">
                            <table class="am-table">
                              <thead>
                                <tr>
                                  <th>Título</th>
                                  <th class="am-right">Visitas</th>
                                  <th class="am-right">Cliques</th>
                                  <th></th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr v-for="page in u.published_pages" :key="page.id">
                                  <td>
                                    <b class="font-semibold">{{ page.title }}</b>
                                    <div class="am-mono am-muted">/{{ page.slug }}</div>
                                  </td>
                                  <td class="am-right am-num">{{ formatInt(page.total_visits ?? 0) }}</td>
                                  <td class="am-right am-num">{{ formatInt(page.total_cta_clicks ?? 0) }}</td>
                                  <td class="am-right whitespace-nowrap">
                                    <button type="button" class="am-btn am-btn-sm" @click.stop="viewPublishedPage(page)">Ver</button>
                                    <button
                                      type="button"
                                      class="am-btn am-btn-sm am-btn-primary ml-1"
                                      :disabled="savingPageId === page.id || !agencyStore.currentAgencyId"
                                      @click.stop="clonePublishedPage(u, page)"
                                    >
                                      {{ savingPageId === page.id ? "Copiando..." : "Copiar para mim" }}
                                    </button>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                          <p v-else class="am-muted mt-2 text-xs">Nenhuma página publicada ainda.</p>
                        </div>
                        <div>
                          <p class="am-eyebrow">Rascunhos</p>
                          <div v-if="u.draft_pages?.length" class="mt-2 overflow-x-auto rounded-xl border border-border">
                            <table class="am-table">
                              <thead>
                                <tr>
                                  <th>Título</th>
                                  <th></th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr v-for="page in u.draft_pages" :key="page.id">
                                  <td>
                                    <b class="font-semibold">{{ page.title }}</b>
                                    <div class="am-mono am-muted">/{{ page.slug }}</div>
                                  </td>
                                  <td class="am-right">
                                    <button type="button" class="am-btn am-btn-sm" @click.stop="goToPageEditor(page)">Editar</button>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                          <p v-else class="am-muted mt-2 text-xs">Nenhum rascunho.</p>
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>

              <tr v-if="!filteredUsers.length">
                <td colspan="8"><div class="am-empty">Nenhum usuário encontrado.</div></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="am-foot">
          <span>
            Mostrando {{ formatInt(userPageRange.start) }}–{{ formatInt(userPageRange.end) }} de {{ formatInt(filteredUsersTotal) }}
          </span>
          <div class="flex flex-wrap items-center gap-2">
            <label class="flex items-center gap-2">
              Linhas
              <select v-model.number="userPageSize" class="am-select">
                <option v-for="option in userPageSizeOptions" :key="option" :value="option">{{ option }}</option>
              </select>
            </label>
            <button type="button" class="am-chip" :disabled="userPage === 1" @click="userPage = Math.max(1, userPage - 1)">Anterior</button>
            <span>Página {{ userPage }} de {{ totalUserPages }}</span>
            <button type="button" class="am-chip" :disabled="userPage >= totalUserPages" @click="userPage = Math.min(totalUserPages, userPage + 1)">Próxima</button>
          </div>
        </div>
      </section>
    </template>

    <!-- LESSONS -->
    <template v-else-if="activeTab === 'lessons'">
      <AdminMasterHeader title="Aulas" subtitle="As aulas aparecem para todas as agências em Aprender › Aulas.">
        <button type="button" class="am-btn" :disabled="resettingLessons" @click="handleResetLessons"><AmIcon name="undo" />Restaurar padrão</button>
        <button type="button" class="am-btn am-btn-primary" @click="openNewLesson()"><AmIcon name="plus" />Nova aula</button>
      </AdminMasterHeader>

      <section class="am-grid-3">
        <AdminMasterKpi icon="video" tone="success" label="Aulas publicadas" :value="formatInt(adminLessons.length)" :hint="`em ${formatInt(lessonGroups.length)} ${lessonGroups.length === 1 ? 'módulo' : 'módulos'}`" />
        <AdminMasterKpi icon="layout" tone="info" label="Com capa" :value="formatInt(adminLessons.filter(lesson => lesson.thumbnail).length)" hint="As outras usam a capa do vídeo" />
        <AdminMasterKpi icon="play" tone="violet" label="Vídeos do YouTube" :value="formatInt(adminLessons.filter(lesson => lesson.videoType !== 'file').length)" :hint="`${formatInt(adminLessons.filter(lesson => lesson.videoType === 'file').length)} por arquivo ou link direto`" />
      </section>

      <div v-if="lessonsLoading" class="am-card am-empty"><div class="am-spinner"></div>Carregando aulas...</div>
      <div v-else-if="!adminLessons.length" class="am-card am-empty">
        Nenhuma aula cadastrada ainda.
        <button type="button" class="am-btn am-btn-primary" @click="openNewLesson()"><AmIcon name="plus" />Nova aula</button>
      </div>
      <template v-else>
        <section v-for="group in lessonGroups" :key="group.key" class="am-card am-card-flush">
          <div class="am-toolbar justify-between">
            <div>
              <h2 class="am-card-title">{{ group.label }}</h2>
              <p class="am-card-sub">{{ group.lessons.length }} {{ group.lessons.length === 1 ? "aula" : "aulas" }} · use as setas para ordenar</p>
            </div>
            <button type="button" class="am-btn am-btn-sm" @click="openNewLesson(group.key === '__default__' ? '' : group.label)"><AmIcon name="plus" />Aula neste módulo</button>
          </div>
          <div class="am-list">
            <div v-for="(lesson, index) in group.lessons" :key="lesson.id" class="flex flex-wrap items-center gap-3 px-3.5 py-2.5">
              <div class="flex flex-col">
                <button type="button" class="am-icon-btn !h-6 !w-6" :disabled="index === 0 || lessonSaving" :aria-label="`Subir ${lesson.title}`" @click="moveLessonInGroup(group, index, -1)">
                  <AmIcon name="chevron" class="rotate-180" />
                </button>
                <button type="button" class="am-icon-btn !h-6 !w-6" :disabled="index === group.lessons.length - 1 || lessonSaving" :aria-label="`Descer ${lesson.title}`" @click="moveLessonInGroup(group, index, 1)">
                  <AmIcon name="chevron" />
                </button>
              </div>
              <div class="lesson-thumb">
                <img v-if="lesson.thumbnail" :src="lesson.thumbnail" alt="" class="h-full w-full object-cover" />
                <AmIcon v-else name="play" />
              </div>
              <div class="min-w-[180px] flex-1">
                <b class="block font-semibold">{{ lesson.title }}</b>
                <p class="am-card-sub !mt-0">
                  {{ lesson.videoType === "file" ? "Arquivo ou link direto" : "YouTube" }}<template v-if="lesson.level"> · {{ lesson.level }}</template><template v-if="lesson.duration"> · {{ lesson.duration }}</template>
                </p>
                <p v-if="lessonReplacement(lesson)" class="am-card-sub !mt-0.5">
                  <span class="am-badge am-tone-warning mr-1">Desatualizada</span>
                  As agências veem o artigo “{{ lessonReplacement(lesson)!.titulo }}”, revisado em {{ formatHelpDate(lessonReplacement(lesson)!.atualizado) }}. Grave um vídeo novo para voltar a mostrar a aula.
                </p>
              </div>
              <button type="button" class="am-btn am-btn-sm" @click="openLessonEdit(lesson)"><AmIcon name="edit" />Editar</button>
              <button type="button" class="am-icon-btn" :disabled="deletingLessonId === lesson.id" :aria-label="`Excluir ${lesson.title}`" @click="deleteLesson(lesson.id)">
                <AmIcon name="trash" />
              </button>
            </div>
          </div>
        </section>
      </template>

      <AdminMasterDrawer
        :open="lessonDrawerOpen"
        :title="isEditingLesson ? 'Editar aula' : 'Nova aula'"
        subtitle="Título, descrição e o link ou iframe do vídeo."
        icon="video"
        :width="600"
        @close="closeLessonDrawer"
      >
        <form id="lesson-form" class="space-y-3.5" @submit.prevent="saveLesson">
          <div class="am-field">
            <label for="ls-title">Título</label>
            <input id="ls-title" v-model="lessonForm.title" type="text" class="am-input" placeholder="Ex.: Dominando o editor" required />
          </div>
          <div class="am-field">
            <label for="ls-desc">Descrição</label>
            <textarea id="ls-desc" v-model="lessonForm.description" rows="3" class="am-input" placeholder="O que a pessoa aprende nessa aula"></textarea>
          </div>
          <div class="grid gap-3.5 sm:grid-cols-3">
            <div class="am-field">
              <label for="ls-module">Módulo</label>
              <input id="ls-module" v-model="lessonForm.moduleName" type="text" list="lesson-module-options" class="am-input" placeholder="Ex.: Primeiros passos" />
              <datalist id="lesson-module-options">
                <option v-for="module in lessonModuleOptions" :key="module" :value="module"></option>
              </datalist>
            </div>
            <div class="am-field">
              <label for="ls-duration">Duração</label>
              <input id="ls-duration" v-model="lessonForm.duration" type="text" class="am-input" placeholder="Ex.: 10:45" />
            </div>
            <div class="am-field">
              <label for="ls-level">Nível</label>
              <input id="ls-level" v-model="lessonForm.level" type="text" class="am-input" placeholder="Ex.: Iniciante" />
            </div>
          </div>
          <div class="am-field">
            <label for="ls-help">Artigo da Central de Ajuda <span class="font-normal text-muted-foreground">(opcional)</span></label>
            <select id="ls-help" v-model="lessonForm.helpArticle" class="am-input">
              <option value="">Nenhum</option>
              <optgroup v-for="group in helpArticleOptions" :key="group.label" :label="group.label">
                <option v-for="article in group.articles" :key="article.id" :value="article.id">{{ article.titulo }}</option>
              </optgroup>
            </select>
            <p class="am-card-sub">Quando o artigo for revisado depois do vídeo desta aula, a aula passa a mostrar o artigo atualizado no lugar.</p>
          </div>
          <div class="am-field">
            <label for="ls-video">Link ou iframe do vídeo</label>
            <textarea id="ls-video" v-model="lessonForm.videoInput" rows="2" class="am-input am-mono" placeholder="Cole o link do YouTube ou o iframe completo" required></textarea>
          </div>
          <div class="am-field">
            <label for="ls-thumb">Capa por link <span class="font-normal text-muted-foreground">(opcional)</span></label>
            <input id="ls-thumb" v-model="lessonForm.thumbnailUrl" type="url" :disabled="Boolean(lessonForm.thumbnailData)" class="am-input" placeholder="https://..." />
            <p v-if="lessonForm.thumbnailData" class="am-card-sub">Remova a imagem enviada para usar um link.</p>
          </div>
          <div class="rounded-[14px] border border-dashed border-border p-3.5">
            <p class="am-eyebrow">Ou envie uma imagem de capa</p>
            <div class="mt-2 flex flex-wrap items-center gap-3">
              <input type="file" accept="image/*" aria-label="Enviar capa da aula" @change="handleThumbnailUpload" />
              <button v-if="lessonForm.thumbnailData" type="button" class="am-btn am-btn-sm" @click="clearThumbnailUpload">Remover imagem</button>
            </div>
            <p v-if="lessonForm.thumbnailUploadName" class="am-card-sub">Selecionada: {{ lessonForm.thumbnailUploadName }}</p>
          </div>
          <div v-if="lessonPreview.videoUrl">
            <p class="am-eyebrow mb-2">Prévia</p>
            <div class="overflow-hidden rounded-xl border border-border">
              <iframe v-if="lessonPreview.videoType !== 'file'" :src="lessonPreview.videoUrl" class="aspect-video w-full border-0" allowfullscreen></iframe>
              <video v-else class="aspect-video w-full bg-black object-cover" controls>
                <source :src="lessonPreview.videoUrl" type="video/mp4" />
              </video>
            </div>
          </div>
        </form>
        <template #footer>
          <button type="button" class="am-btn" @click="closeLessonDrawer">Cancelar</button>
          <button type="submit" form="lesson-form" class="am-btn am-btn-primary" :disabled="lessonSaving">
            {{ lessonSaving ? "Salvando..." : isEditingLesson ? "Salvar aula" : "Adicionar aula" }}
          </button>
        </template>
      </AdminMasterDrawer>
    </template>

    <!-- TEMPLATES -->
    <template v-else-if="activeTab === 'templates'">
      <AdminMasterHeader title="Modelos de página" subtitle="Modelos que as agências escolhem ao criar uma página nova.">
        <button type="button" class="am-btn" :disabled="pageTemplatesLoading" @click="loadTemplates"><AmIcon name="refresh" />Atualizar</button>
        <button type="button" class="am-btn am-btn-primary" @click="templatesTab = 'create'"><AmIcon name="plus" />Novo modelo</button>
      </AdminMasterHeader>

      <nav class="am-tabs" aria-label="Seções de modelos">
        <button type="button" class="am-tab" :class="{ on: templatesTab === 'published' }" @click="templatesTab = 'published'">
          Publicados <span class="am-count">{{ pageTemplates.length }}</span>
        </button>
        <button type="button" class="am-tab" :class="{ on: templatesTab === 'create' }" @click="templatesTab = 'create'">Criar a partir de uma página</button>
      </nav>

      <template v-if="templatesTab === 'published'">
        <div v-if="pageTemplatesLoading" class="am-card am-empty"><div class="am-spinner"></div>Carregando modelos...</div>
        <div v-else-if="pageTemplatesError" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ pageTemplatesError }}</span></div>
        <div v-else-if="!pageTemplates.length" class="am-card am-empty">
          Nenhum modelo publicado ainda.
          <button type="button" class="am-btn am-btn-primary" @click="templatesTab = 'create'">Criar a partir de uma página</button>
        </div>
        <div v-else class="am-grid-3">
          <article v-for="template in pageTemplates" :key="template.id" class="tpl-card">
            <div class="tpl-cover" :style="templateCoverStyle(template)">
              <span v-if="template.is_default" class="am-badge am-tone-success absolute left-2.5 top-2.5">Padrão</span>
            </div>
            <div class="p-3.5">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <b class="block truncate font-semibold">{{ template.name }}</b>
                  <small class="am-mono am-muted block truncate">/{{ template.slug }}</small>
                </div>
                <div class="relative" data-template-menu="true">
                  <button type="button" class="am-icon-btn" :aria-label="`Ações de ${template.name}`" @click="templateMenuId = templateMenuId === template.id ? null : template.id">
                    <AmIcon name="dots" />
                  </button>
                  <div v-if="templateMenuId === template.id" class="am-menu right-0 top-full mt-1">
                    <button type="button" @click="runTemplateMenu(() => openTemplatePreview(template))"><AmIcon name="eye" />Pré-visualizar</button>
                    <button type="button" @click="runTemplateMenu(() => openTemplateEditDialog(template))"><AmIcon name="edit" />Editar nome e descrição</button>
                    <button type="button" class="is-danger" :disabled="deletingTemplateId === template.id" @click="runTemplateMenu(() => handleDeleteTemplate(template))">
                      <AmIcon name="trash" />{{ deletingTemplateId === template.id ? "Excluindo..." : "Excluir" }}
                    </button>
                  </div>
                </div>
              </div>
              <p class="am-card-sub line-clamp-2 min-h-[36px]">{{ template.description || "Sem descrição" }}</p>
              <div class="mt-2.5 flex items-center justify-between">
                <span class="am-card-sub !mt-0">{{ templateStats(template).enabledSections }} de {{ templateStats(template).totalSections }} seções ativas</span>
                <button type="button" class="text-xs font-semibold text-primary" @click="openTemplatePreview(template)">Pré-visualizar</button>
              </div>
            </div>
          </article>
        </div>
      </template>

      <section v-else class="am-card am-card-flush">
        <div class="am-toolbar">
          <div class="relative w-full max-w-[320px]" data-template-agency-selector="true">
            <label class="am-search">
              <AmIcon name="search" />
              <input
                ref="templateAgencySearchInput"
                v-model="templateAgencySearch"
                type="search"
                placeholder="Buscar a agência de origem"
                aria-label="Buscar agência de origem"
                @focus="handleTemplateAgencyInputFocus"
              />
              <button type="button" class="am-icon-btn !h-6 !w-6" aria-label="Abrir lista de agências" @click="toggleTemplateAgencyDropdown">
                <AmIcon name="chevron" :class="templateAgencyDropdownOpen ? 'rotate-180' : ''" />
              </button>
            </label>
            <div v-if="templateAgencyDropdownOpen" class="am-menu left-0 right-0 top-full mt-1 max-h-64 overflow-y-auto">
              <p v-if="templateAgencyLoading" class="am-card-sub px-2.5 py-2">Buscando agências...</p>
              <p v-else-if="templateAgencyError" class="px-2.5 py-2 text-sm text-status-danger-foreground">{{ templateAgencyError }}</p>
              <template v-else-if="templateAgencyOptions.length">
                <button v-for="agency in templateAgencyOptions" :key="agency.id" type="button" class="!items-start" @click="selectTemplateAgency(agency)">
                  <span class="min-w-0">
                    <b class="block truncate font-semibold">{{ agency.name }}</b>
                    <small class="am-muted block text-xs">/{{ agency.slug }} · {{ agency.pages_count }} páginas</small>
                  </span>
                </button>
              </template>
              <p v-else class="am-card-sub px-2.5 py-2">Nenhuma agência encontrada.</p>
            </div>
          </div>
          <span v-if="selectedTemplateAgency" class="am-chip on">{{ selectedTemplateAgency.name }}</span>
          <button type="button" class="am-btn am-btn-sm ml-auto" :disabled="templatePagesLoading || !templateAgencyId" @click="loadTemplatePages">
            <AmIcon name="refresh" />Recarregar páginas
          </button>
        </div>

        <div v-if="!templateAgencyId" class="am-empty">Escolha a agência de origem para listar as páginas dela.</div>
        <div v-else-if="templatePagesLoading" class="am-empty"><div class="am-spinner"></div>Carregando páginas...</div>
        <div v-else-if="templatePagesError" class="am-empty !text-status-danger-foreground">{{ templatePagesError }}</div>
        <div v-else-if="!templatePages.length" class="am-empty">Essa agência não tem páginas.</div>
        <div v-else class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Página</th>
                <th>Situação</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="page in templatePages" :key="page.id">
                <td>
                  <b class="font-semibold">{{ page.title }}</b>
                  <small class="am-mono am-muted block">/{{ page.slug }}</small>
                </td>
                <td>
                  <span class="am-badge" :class="page.status === 'published' ? 'am-tone-success' : 'am-tone-warning'">
                    {{ page.status === "published" ? "Publicada" : "Rascunho" }}
                  </span>
                </td>
                <td class="am-right whitespace-nowrap">
                  <a v-if="templatePublicUrl(page)" :href="templatePublicUrl(page)" class="am-btn am-btn-sm" target="_blank" rel="noopener noreferrer">Ver página</a>
                  <button type="button" class="am-btn am-btn-sm am-btn-primary ml-1.5" @click="openTemplateDialog(page)">Usar como modelo</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="am-foot"><span>Prefira páginas publicadas: elas já foram revisadas pela agência.</span></div>
      </section>

      <AdminMasterDrawer
        :open="templateDialog.open"
        :title="templateDialog.mode === 'edit' ? 'Editar modelo' : 'Novo modelo'"
        :subtitle="templateDialog.mode === 'edit' ? 'Nome, identificador e descrição do modelo.' : 'Como o modelo aparece para as agências.'"
        icon="layout"
        tone="info"
        @close="closeTemplateDialog"
      >
        <div class="space-y-3.5">
          <div class="am-field">
            <label for="tp-name">Nome</label>
            <input id="tp-name" v-model="templateDialog.name" type="text" class="am-input" />
          </div>
          <div class="am-field">
            <label for="tp-slug">Identificador</label>
            <input id="tp-slug" v-model="templateDialog.slug" type="text" class="am-input am-mono" @input="handleTemplateSlugInput" />
          </div>
          <div class="am-field">
            <label for="tp-desc">Descrição</label>
            <textarea id="tp-desc" v-model="templateDialog.description" rows="3" class="am-input" placeholder="Resumo do que este modelo entrega"></textarea>
          </div>
          <div v-if="templateDialog.error" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ templateDialog.error }}</span></div>
        </div>
        <template #footer>
          <button type="button" class="am-btn" @click="closeTemplateDialog">Cancelar</button>
          <button type="button" class="am-btn am-btn-primary" :disabled="templateDialog.saving" @click="submitTemplateDialog">
            {{ templateDialog.saving ? "Salvando..." : templateDialog.mode === "edit" ? "Salvar alterações" : "Criar modelo" }}
          </button>
        </template>
      </AdminMasterDrawer>

      <div
        v-if="templatePreviewDialog.open"
        class="app-modal-overlay admin-master-surface fixed inset-0 z-40 flex items-center justify-center px-4 py-8"
        @click.self="closeTemplatePreview"
      >
        <div class="h-[90vh] w-full max-w-4xl overflow-y-auto rounded-[22px] border border-border bg-card p-5 shadow-elegant">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="am-eyebrow">Pré-visualização</p>
              <h3 class="am-card-title">{{ templatePreviewDialog.template?.name }}</h3>
            </div>
            <button type="button" class="am-icon-btn" aria-label="Fechar" @click="closeTemplatePreview"><AmIcon name="x" /></button>
          </div>
          <PageTemplatePreview v-if="templatePreviewConfig" :config="templatePreviewConfig" :branding="templatePreviewBranding" />
          <p v-else class="am-empty">Não foi possível mostrar este modelo.</p>
        </div>
      </div>
    </template>
    <template v-else-if="activeTab === 'flight_apis'">
      <FlightApiKeysPanel />
    </template>
    <template v-else-if="activeTab === 'revenue_forecast'">
      <AdminMasterHeader
        title="Previsão de receita"
        subtitle="Assinaturas ativas no Asaas e na Cakto nos próximos 30 dias. A entrada prevista é no dia seguinte à validade."
      >
        <button type="button" class="am-btn" :disabled="revenueForecastLoading" @click="loadRevenueForecast">
          <AmIcon name="refresh" :class="revenueForecastLoading ? 'animate-spin' : ''" />
          {{ revenueForecastLoading ? "Atualizando..." : "Atualizar" }}
        </button>
      </AdminMasterHeader>

      <section class="am-grid-4">
        <AdminMasterKpi icon="wallet" tone="success" label="Previsto em 30 dias" :value="formatCurrencyBRL(forecastTotalMrr)" :hint="forecastMonthLabel ? `A partir de ${forecastMonthLabel}` : ''" />
        <AdminMasterKpi icon="cal" tone="info" label="Cobranças previstas" :value="formatInt(forecastTotalCount)" :hint="`${formatInt(forecastBusyDays)} dias com entrada`" />
        <AdminMasterKpi icon="card" tone="violet" label="Ticket médio" :value="formatCurrencyBRL(forecastTotalCount ? forecastTotalMrr / forecastTotalCount : 0)" hint="Por cobrança" />
        <AdminMasterKpi icon="trend" tone="neutral" label="Por forma de cobrança" :value="forecastProviderSplit.label" :hint="forecastProviderSplit.hint" />
      </section>

      <div v-if="revenueForecastError" class="am-notice am-tone-danger">
        <AmIcon name="alert" />
        <span>{{ revenueForecastError }}</span>
      </div>
      <div v-else-if="revenueForecastLoading && !revenueForecastDays.length" class="am-card am-empty">
        <div class="am-spinner"></div>
        Carregando previsão...
      </div>
      <section v-else class="grid gap-3.5 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
        <div class="am-card">
          <div class="am-card-head">
            <div>
              <h2 class="am-card-title">Calendário</h2>
              <p class="am-card-sub">Quanto mais forte o verde, mais entra no dia. Clique num dia para ver as cobranças.</p>
            </div>
          </div>
          <div class="grid grid-cols-7 gap-1.5">
            <span v-for="weekday in ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']" :key="weekday" class="pb-0.5 text-center text-[11px] font-semibold uppercase text-muted-foreground">
              {{ weekday }}
            </span>
            <button
              v-for="cell in forecastCalendarCells"
              :key="cell.key"
              type="button"
              class="am-cal-day"
              :class="[
                cell.iso ? forecastHeatClass(cell.day?.total_mrr || 0) : 'is-off',
                cell.iso && cell.iso === selectedForecastDate ? 'is-selected' : ''
              ]"
              :disabled="!cell.iso"
              @click="cell.iso && (selectedForecastDate = cell.iso)"
            >
              <template v-if="cell.date">
                <span class="text-[11.5px]">{{ cell.date.getDate() }}</span>
                <b v-if="cell.day?.total_mrr" class="am-num">{{ formatCompactMoney(cell.day.total_mrr) }}</b>
              </template>
            </button>
          </div>
        </div>

        <div class="am-card">
          <p class="am-eyebrow">{{ selectedForecastDay ? formatForecastWeekday(selectedForecastDay.date) : "Escolha um dia" }}</p>
          <p class="am-kpi-value">{{ formatCurrencyBRL(selectedForecastDay?.total_mrr || 0) }}</p>
          <p class="am-card-sub">
            {{ formatInt(selectedForecastDay?.subscriptions_count || 0) }}
            {{ (selectedForecastDay?.subscriptions_count || 0) === 1 ? "cobrança" : "cobranças" }}
          </p>
          <div class="am-list mt-3 max-h-[440px] overflow-auto pr-1">
            <div
              v-for="entry in selectedForecastEntries"
              :key="`${entry.subscription_id}-${entry.user_id}`"
              class="flex items-center gap-3 py-2.5"
            >
              <span class="am-avatar">{{ initials(entry.user_name) }}</span>
              <div class="min-w-0 flex-1">
                <b class="block truncate font-semibold">{{ entry.user_name }}</b>
                <p class="am-card-sub !mt-0 truncate">{{ planLabel(entry.plan) }} · {{ gatewayLabel(entry.provider) }} · validade {{ formatDate(entry.valid_until) }}</p>
              </div>
              <b class="am-num">{{ formatCurrencyBRL(entry.mrr_amount) }}</b>
            </div>
            <p v-if="!selectedForecastEntries.length" class="am-empty">Sem cobrança prevista neste dia.</p>
          </div>
        </div>
      </section>
    </template>
  </div>

  <!-- SNACKBAR -->
  <transition name="fade">
    <div
      v-if="snackbar?.open"
      class="app-snackbar-layer z-50 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-2xl"
    >
      {{ snackbar.text }}
    </div>
  </transition>
 
  <!-- CREATE USER MODAL -->
  <transition name="fade">
    <div
      v-if="createUserDialog.open"
      class="app-modal-overlay admin-master-surface fixed inset-0 z-50 flex items-center justify-center overflow-y-auto px-4 py-8"
      @click.self="closeCreateUserDialog"
    >
      <form class="w-full max-w-2xl rounded-3xl bg-white p-8 shadow-2xl" @submit.prevent="submitCreateUser">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Novo acesso</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">Criar usuário</h2>
        <p class="mt-2 text-sm text-slate-600">A conta será criada ativa, com agência própria e assinatura pronta para uso.</p>

        <div class="mt-6 grid gap-4 sm:grid-cols-2">
          <label class="text-sm font-semibold text-slate-700 sm:col-span-2">
            Nome completo
            <input v-model="createUserDialog.name" required minlength="2" type="text" autocomplete="off" class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 font-normal outline-none focus:border-emerald-500" />
          </label>
          <label class="text-sm font-semibold text-slate-700">
            E-mail
            <input v-model="createUserDialog.email" required type="email" autocomplete="off" class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 font-normal outline-none focus:border-emerald-500" />
          </label>
          <label class="text-sm font-semibold text-slate-700">
            WhatsApp
            <input v-model="createUserDialog.whatsapp" type="tel" autocomplete="off" placeholder="(00) 00000-0000" class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 font-normal outline-none focus:border-emerald-500" />
          </label>
          <label class="text-sm font-semibold text-slate-700">
            Plano
            <select v-model="createUserDialog.plan" required class="mt-1 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 font-normal outline-none focus:border-emerald-500">
              <option v-for="option in adminPlanOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </label>
          <label class="text-sm font-semibold text-slate-700">
            Validade da assinatura
            <input v-model="createUserDialog.validUntil" required :min="todayDateInput" type="date" class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 font-normal outline-none focus:border-emerald-500" />
          </label>
          <label class="text-sm font-semibold text-slate-700 sm:col-span-2">
            Senha inicial
            <input v-model="createUserDialog.password" required minlength="8" type="password" autocomplete="new-password" class="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2.5 font-normal outline-none focus:border-emerald-500" />
            <span class="mt-1 block text-xs font-normal text-slate-500">Mínimo de 8 caracteres, com letra maiúscula, minúscula e número.</span>
          </label>
        </div>

        <p v-if="createUserDialog.error" class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600">{{ createUserDialog.error }}</p>
        <div class="mt-6 flex justify-end gap-3">
          <button type="button" class="rounded-full border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60" :disabled="createUserDialog.saving" @click="closeCreateUserDialog">Cancelar</button>
          <button type="submit" class="rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60" :disabled="createUserDialog.saving">
            {{ createUserDialog.saving ? "Criando..." : "Criar usuário" }}
          </button>
        </div>
      </form>
    </div>
  </transition>

  <!-- TRIAL MODAL -->
  <transition name="fade">
    <div
      v-if="trialDialog.open && trialDialog.user"
      class="app-modal-overlay admin-master-surface fixed inset-0 z-50 flex items-center justify-center px-4"
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
      class="app-modal-overlay admin-master-surface fixed inset-0 z-50 flex items-center justify-center px-4"
    >
      <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-indigo-500">Vincular página</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">
          Escolha uma página para {{ linkPageDialog.user.name }}
        </h2>
        <p class="mt-2 text-sm text-slate-600">
          Selecionamos as páginas da sua Agência atual ({{ agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId)?.name || 'sem nome' }}).
          A cópia será adicionada à Agência do usuário.
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
                {{ page.title }}  {{ page.status === 'published' ? 'Publicada' : 'Rascunho' }}
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
      class="app-modal-overlay admin-master-surface fixed inset-0 z-50 flex items-center justify-center px-4"
    >
      <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">Excluir usuário</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">Remover {{ deleteDialog.user.name }}?</h2>
        <p class="mt-2 text-sm text-slate-600">
          Essa ação apaga a conta, Agências, páginas e registros de tracking vinculados. Ela não pode ser desfeita.
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
      class="app-modal-overlay admin-master-surface fixed inset-0 z-50 flex items-center justify-center px-4"
    >
      <div class="w-full max-w-xl rounded-3xl bg-white p-8 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-600">Reembolsar usuário</p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900">Reembolsar {{ refundDialog.user.name }}?</h2>
        <p class="mt-2 text-sm text-slate-600">
          Ao confirmar, vamos acionar o reembolso na Cakto, cancelar a assinatura, despublicar todas as páginas deste cliente
          e bloquear o acesso imediatamente. Essa ação não pode ser desfeita.
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

  <transition name="fade">
    <div
      v-if="subscriptionActionDialog.open && subscriptionActionDialog.user"
      class="app-modal-overlay admin-master-surface fixed inset-0 z-50 flex items-center justify-center px-4"
    >
      <div class="w-full max-w-xl rounded-3xl bg-white p-8 shadow-2xl dark:bg-[#101010] dark:text-white">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-white/60">
          {{
            subscriptionActionDialog.kind === "plan"
              ? "Alterar plano"
              : subscriptionActionDialog.kind === "status"
                ? "Alterar status"
                : "Alterar validade"
          }}
        </p>
        <h2 class="mt-3 text-2xl font-bold text-slate-900 dark:text-white">
          Confirmar mudança de
          {{
            subscriptionActionDialog.kind === "plan"
              ? "plano"
              : subscriptionActionDialog.kind === "status"
                ? "status"
                : "validade"
          }}?
        </h2>
        <p class="mt-2 text-sm text-slate-600 dark:text-white/70">
          Usuário:
          <span class="font-semibold text-slate-900 dark:text-white">{{ subscriptionActionDialog.user.name }}</span>
        </p>
        <div class="mt-4 grid gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-white/10 dark:bg-white/5">
          <div class="flex items-center justify-between gap-4">
            <span class="text-slate-500 dark:text-white/60">
              {{ subscriptionActionDialog.kind === "validity" ? "Validade atual" : "Valor atual" }}
            </span>
            <span class="font-semibold text-slate-900 dark:text-white">
              {{
                subscriptionActionDialog.kind === "plan"
                  ? planLabel(subscriptionActionDialog.user.plan)
                  : subscriptionActionDialog.kind === "validity"
                    ? (formatDate(subscriptionActionDialog.user.valid_until) || "Sem validade definida")
                    : formatSubscriptionStatus(subscriptionActionDialog.user)
              }}
            </span>
          </div>
          <div v-if="subscriptionActionDialog.kind === 'validity'" class="space-y-2">
            <label class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500 dark:text-white/60">Nova validade</label>
            <input
              v-model="subscriptionActionDialog.value"
              type="date"
              class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 outline-none focus:border-slate-900 dark:border-white/10 dark:bg-[#151515] dark:text-white"
            />
          </div>
          <div v-else class="flex items-center justify-between gap-4">
            <span class="text-slate-500 dark:text-white/60">Novo valor</span>
            <span class="font-semibold text-slate-900 dark:text-white">{{ subscriptionActionDialog.label }}</span>
          </div>
          <p class="text-xs text-slate-500 dark:text-white/60">
            Essa alteração será refletida no usuário e na assinatura.
          </p>
        </div>
        <p
          v-if="subscriptionActionDialog.error"
          class="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600 dark:bg-rose-500/10 dark:text-rose-200"
        >
          {{ subscriptionActionDialog.error }}
        </p>
        <div class="mt-6 flex flex-wrap justify-end gap-3">
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60 dark:border-white/10 dark:text-white dark:hover:bg-white/10"
            :disabled="subscriptionActionDialog.saving"
            @click="closeSubscriptionActionDialog"
          >
            Cancelar
          </button>
          <button
            class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-slate-800 disabled:opacity-60 dark:bg-white dark:text-slate-900 dark:hover:bg-white/90"
            :disabled="subscriptionActionDialog.saving || (subscriptionActionDialog.kind === 'validity' && !subscriptionActionDialog.value)"
            @click="confirmSubscriptionAction"
          >
            {{ subscriptionActionDialog.saving ? "Salvando..." : "Confirmar alteração" }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { useAgencyStore } from "../../store/useAgencyStore";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { getPlanLabel, planLabels } from "../../utils/planLabels";
import { normalizeVideoInput, useLessonsStore, type Lesson } from "../../store/useLessonsStore";
import { HELP_MODULES, articleReplacingLesson, articlesOf, formatDate as formatHelpDate } from "../../help";
import { slugify } from "../../utils/slugify";
import PageTemplatePreview from "../../components/admin/PageTemplatePreview.vue";
import FlightApiKeysPanel from "../../components/admin/FlightApiKeysPanel.vue";
import { listPageTemplates, createTemplateFromPage, deleteTemplate, updateTemplate } from "../../services/templates";
import type { PageTemplate } from "../../types/templates";
import { applyTemplateBranding, summarizeTemplate } from "../../utils/pageTemplates";
import { sanitizeDigits, buildWhatsappLink } from "../../utils/whatsapp";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import AdminMasterKpi from "../../components/admin/master/AdminMasterKpi.vue";
import AdminMasterDrawer from "../../components/admin/master/AdminMasterDrawer.vue";
import { adminMasterCounts } from "../../composables/useAdminMasterCounts";

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
  subscriptions_timeseries: {
    label: string;
    new_subscriptions: number;
    renewed_subscriptions: number;
    cancelled_subscriptions: number;
    churn_rate: number;
  }[];
  monthly_churn_rate?: number;
  monthly_churn_cancelled?: number;
  monthly_churn_base?: number;
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
    subscription_asaas_subscription_id?: string | null;
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

interface RevenueForecastEntry {
  subscription_id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  plan: string;
  provider: string;
  valid_until: string;
  expected_on: string;
  mrr_amount: number;
}

interface RevenueForecastDay {
  date: string;
  total_mrr: number;
  subscriptions_count: number;
  entries: RevenueForecastEntry[];
}

interface RevenueForecastOut {
  start_date: string;
  end_date: string;
  days: number;
  total_mrr: number;
  subscriptions_count: number;
  forecast_days: RevenueForecastDay[];
}

type AdminTab = "dashboard" | "monitor" | "users" | "lessons" | "templates" | "flight_apis" | "revenue_forecast";
type TemplateDialogMode = "create" | "edit";
type SubscriptionActionKind = "plan" | "status" | "validity";

interface SubscriptionActionOption {
  value: string;
  label: string;
}

const adminPlanOptions: SubscriptionActionOption[] = [
  { value: "free", label: "Começo" },
  { value: "trial", label: "Trial" },
  { value: "essencial", label: "Profissional" },
  { value: "growth", label: "Agência" },
  { value: "infinity", label: "Escala" },
  { value: "teste", label: "Teste" }
];

const adminSubscriptionStatusOptions: SubscriptionActionOption[] = [
  { value: "active", label: "Ativa" },
  { value: "pending", label: "Pendente" },
  { value: "failed", label: "Falha" },
  { value: "past_due", label: "Em atraso" },
  { value: "cancel_at_period_end", label: "Cancelar no fim da validade" },
  { value: "cancelled", label: "Cancelada" },
  { value: "cancelled_admin", label: "Cancelada pelo admin" },
  { value: "inactive", label: "Inativa" }
];

const toDateInputValue = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

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
const subscriptionsSeries = computed(() => metrics.value?.subscriptions_timeseries ?? []);
const visibleSubscriptionSeries = reactive({
  new: true,
  renewed: true,
  cancelled: true
});
const toggleSubscriptionSeries = (key: "new" | "renewed" | "cancelled") => {
  visibleSubscriptionSeries[key] = !visibleSubscriptionSeries[key];
};

const onlineSessions = ref<AdminOnlineSession[]>([]);
const onlineSessionsMeta = ref<AdminOnlineSessionsResponse | null>(null);
const onlineSessionsLoading = ref(false);
const onlineSessionsError = ref("");
const revokingUserId = ref<number | null>(null);
let onlineSessionsInterval: number | null = null;
const revenueForecast = ref<RevenueForecastOut | null>(null);
const revenueForecastLoading = ref(false);
const revenueForecastError = ref("");
const selectedForecastDate = ref("");
const monitorStatusLabel = computed(() => (onlineSessionsLoading.value ? "Atualizando" : "Operacional"));
const monitorLastUpdated = computed(() => {
  const value = onlineSessionsMeta.value?.generated_at;
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
});
const revenueForecastDays = computed(() => revenueForecast.value?.forecast_days || []);
const forecastByDate = computed(() => {
  const map = new Map<string, RevenueForecastDay>();
  for (const day of revenueForecastDays.value) {
    map.set(day.date.slice(0, 10), day);
  }
  return map;
});
const parseForecastIsoDate = (iso: string) => new Date(`${iso}T12:00:00`);
const forecastMonthLabel = computed(() => {
  const first = revenueForecastDays.value[0];
  if (!first) return "";
  const date = parseForecastIsoDate(first.date.slice(0, 10));
  return date.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
});
const forecastCalendarCells = computed(() => {
  const cells: Array<{ key: string; date: Date | null; iso: string | null; day: RevenueForecastDay | null }> = [];
  if (!revenueForecastDays.value.length) return cells;
  const start = parseForecastIsoDate(revenueForecastDays.value[0].date.slice(0, 10));
  const firstWeekday = start.getDay();
  for (let i = 0; i < firstWeekday; i += 1) {
    cells.push({ key: `empty-start-${i}`, date: null, iso: null, day: null });
  }
  for (const day of revenueForecastDays.value) {
    const iso = day.date.slice(0, 10);
    const date = parseForecastIsoDate(iso);
    cells.push({ key: iso, date, iso, day });
  }
  const remainder = cells.length % 7;
  if (remainder > 0) {
    for (let i = 0; i < 7 - remainder; i += 1) {
      cells.push({ key: `empty-end-${i}`, date: null, iso: null, day: null });
    }
  }
  return cells;
});
const selectedForecastDay = computed(() => {
  if (!selectedForecastDate.value) return null;
  return forecastByDate.value.get(selectedForecastDate.value) || null;
});
const selectedForecastEntries = computed(() => selectedForecastDay.value?.entries || []);
const forecastTotalMrr = computed(() => revenueForecast.value?.total_mrr || 0);
const forecastTotalCount = computed(() => revenueForecast.value?.subscriptions_count || 0);
const formatCurrencyBRL = (value: number) =>
  Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const NEW_USERS_CHART_HEIGHT = 180;
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
  return `Últimos ${adminPeriodDays.value} dias`;
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
const isBootstrappingAdminManagement = ref(true);
const auth = useAuthStore();
const agencyStore = useAgencyStore();
const route = useRoute();
const router = useRouter();
const granting = ref<number | null>(null);
const adminAsaasActionLoadingUserId = ref<number | null>(null);
const snackbar = ref<{ open: boolean; text: string } | null>(null);
const trialDialog = ref<{ open: boolean; user: any | null }>({ open: false, user: null });
const todayDateInput = new Date().toLocaleDateString("en-CA");
const createUserDialog = reactive({
  open: false,
  name: "",
  email: "",
  whatsapp: "",
  password: "",
  plan: "essencial",
  validUntil: "",
  saving: false,
  error: ""
});
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
const subscriptionActionMenu = reactive<{
  open: boolean;
  userId: number | null;
  kind: SubscriptionActionKind | null;
}>({
  open: false,
  userId: null,
  kind: null
});
const subscriptionActionDialog = reactive<{
  open: boolean;
  user: Metrics["users"][number] | null;
  kind: SubscriptionActionKind | null;
  value: string;
  label: string;
  saving: boolean;
  error: string;
}>({
  open: false,
  user: null,
  kind: null,
  value: "",
  label: "",
  saving: false,
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
      templateAgencyError.value = err?.response?.data?.detail || "Não foi possível buscar Agências.";
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
const syncActiveTabFromRoute = () => {
  const routeName = typeof route.name === "string" ? route.name : "";
  if (routeName === "admin-management-monitor") {
    activeTab.value = "monitor";
    return;
  }
  if (routeName === "admin-management-users") {
    activeTab.value = "users";
    return;
  }
  if (routeName === "admin-management-lessons") {
    activeTab.value = "lessons";
    return;
  }
  if (routeName === "admin-management-templates") {
    activeTab.value = "templates";
    return;
  }
  if (routeName === "admin-management-flight-apis") {
    activeTab.value = "flight_apis";
    return;
  }
  if (routeName === "admin-management-revenue-forecast") {
    activeTab.value = "revenue_forecast";
    return;
  }
  activeTab.value = "dashboard";
};
const selectedTemplateAgency = computed(() => {
  return templateAgencyOptions.value.find(agency => agency.id === templateAgencyId.value) || null;
});
const subscriptionLabelRange = computed(() => {
  if (!compactNewUsersLabels.value || subscriptionsSeries.value.length < 2) return null;
  const first = subscriptionsSeries.value[0]?.label || "";
  const last = subscriptionsSeries.value[subscriptionsSeries.value.length - 1]?.label || "";
  return { start: first, end: last };
});
const subscriptionMaxValue = computed(() => {
  if (!subscriptionsSeries.value.length) return 1;
  const maxValue = Math.max(
    ...subscriptionsSeries.value.map((point) =>
      Math.max(
        point.new_subscriptions ?? 0,
        point.renewed_subscriptions ?? 0,
        point.cancelled_subscriptions ?? 0
      )
    )
  );
  return maxValue > 0 ? maxValue : 1;
});
const subscriptionChartPoints = computed(() => {
  const series = subscriptionsSeries.value;
  if (!series.length) return [];
  const safeMax = subscriptionMaxValue.value > 0 ? subscriptionMaxValue.value : 1;
  const count = series.length;
  const step = count > 1 ? newUsersChartInnerWidth / (count - 1) : newUsersChartInnerWidth;
  const toY = (value: number) =>
    NEW_USERS_CHART_PADDING_Y + (newUsersChartInnerHeight - (Math.max(value, 0) / safeMax) * newUsersChartInnerHeight);
  return series.map((point, index) => {
    const x = count === 1 ? NEW_USERS_CHART_WIDTH / 2 : NEW_USERS_CHART_PADDING_X + index * step;
    return {
      label: point.label,
      x,
      newY: toY(point.new_subscriptions ?? 0),
      renewedY: toY(point.renewed_subscriptions ?? 0),
      cancelledY: toY(point.cancelled_subscriptions ?? 0),
      newValue: point.new_subscriptions ?? 0,
      renewedValue: point.renewed_subscriptions ?? 0,
      cancelledValue: point.cancelled_subscriptions ?? 0
    };
  });
});
const buildSmoothPath = (coords: Array<{ x: number; y: number }>) => {
  if (!coords.length) return "";
  if (coords.length === 1) return `M${coords[0].x},${coords[0].y}`;
  let d = `M${coords[0].x},${coords[0].y}`;
  for (let i = 0; i < coords.length - 1; i += 1) {
    const p0 = coords[i];
    const p1 = coords[i + 1];
    const cp1x = p0.x + (p1.x - p0.x) / 2;
    const cp1y = p0.y;
    const cp2x = p0.x + (p1.x - p0.x) / 2;
    const cp2y = p1.y;
    d += ` C${cp1x},${cp1y} ${cp2x},${cp2y} ${p1.x},${p1.y}`;
  }
  return d;
};
const makeLinePath = (key: "newY" | "renewedY" | "cancelledY") => {
  const points = subscriptionChartPoints.value;
  if (!points.length) return "";
  return buildSmoothPath(points.map(point => ({ x: point.x, y: point[key] })));
};
const subscriptionNewPath = computed(() => makeLinePath("newY"));
const subscriptionRenewedPath = computed(() => makeLinePath("renewedY"));
const subscriptionCancelledPath = computed(() => makeLinePath("cancelledY"));
const makeAreaPath = (key: "newY" | "renewedY" | "cancelledY") => {
  const points = subscriptionChartPoints.value;
  if (!points.length) return "";
  const baseY = NEW_USERS_CHART_PADDING_Y + newUsersChartInnerHeight;
  const line = buildSmoothPath(points.map(point => ({ x: point.x, y: point[key] })));
  const last = points[points.length - 1];
  const first = points[0];
  return `${line} L${last.x},${baseY} L${first.x},${baseY} Z`;
};
const subscriptionNewAreaPath = computed(() => makeAreaPath("newY"));
const subscriptionRenewedAreaPath = computed(() => makeAreaPath("renewedY"));
const subscriptionCancelledAreaPath = computed(() => makeAreaPath("cancelledY"));
const subscriptionHitAreas = computed(() => {
  const points = subscriptionChartPoints.value;
  if (!points.length) return [];
  const width = points.length > 1 ? Math.max(14, newUsersChartInnerWidth / points.length) : 56;
  return points.map((point, index) => ({
    index,
    x: point.x - width / 2,
    width
  }));
});
const subscriptionTooltip = ref<{
  visible: boolean;
  x: number;
  y: number;
  label: string;
  newValue: number;
  renewedValue: number;
  cancelledValue: number;
}>({
  visible: false,
  x: 0,
  y: 0,
  label: "",
  newValue: 0,
  renewedValue: 0,
  cancelledValue: 0
});
const subscriptionTooltipStyle = computed(() => {
  if (!subscriptionTooltip.value.visible) return { opacity: 0 };
  const minX = 84;
  const maxX = newUsersChartWidth - 84;
  const safeX = Math.min(Math.max(subscriptionTooltip.value.x, minX), maxX);
  const minY = 28;
  const maxY = newUsersChartHeight - 10;
  const safeY = Math.min(Math.max(subscriptionTooltip.value.y, minY), maxY);
  return {
    left: `${safeX}px`,
    top: `${safeY}px`,
    opacity: 1
  };
});
const setSubscriptionTooltip = (index: number, event: MouseEvent) => {
  const point = subscriptionChartPoints.value[index];
  if (!point) return;
  const host = event.currentTarget as SVGRectElement | null;
  const svg = host?.ownerSVGElement;
  if (!svg) return;
  const rect = svg.getBoundingClientRect();
  const scaleX = rect.width / newUsersChartWidth;
  const scaleY = rect.height / newUsersChartHeight;
  const pointScreenX = point.x * scaleX;
  const pointScreenY = Math.min(point.newY, point.renewedY, point.cancelledY) * scaleY;
  subscriptionTooltip.value = {
    visible: true,
    x: pointScreenX,
    y: pointScreenY - 8,
    label: point.label,
    newValue: point.newValue,
    renewedValue: point.renewedValue,
    cancelledValue: point.cancelledValue
  };
};
const showSubscriptionTooltip = (index: number, event: MouseEvent) => {
  setSubscriptionTooltip(index, event);
};
const moveSubscriptionTooltip = (index: number, event: MouseEvent) => {
  setSubscriptionTooltip(index, event);
};
const hideSubscriptionTooltip = () => {
  subscriptionTooltip.value.visible = false;
};
const monthlyChurnRate = computed(() => {
  const value = metrics.value?.monthly_churn_rate;
  return typeof value === "number" ? value : 0;
});
const subscriptionsTotals = computed(() => {
  return subscriptionsSeries.value.reduce(
    (acc, item) => {
      acc.new += item.new_subscriptions || 0;
      acc.renewed += item.renewed_subscriptions || 0;
      acc.cancelled += item.cancelled_subscriptions || 0;
      return acc;
    },
    { new: 0, renewed: 0, cancelled: 0 }
  );
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
    templatePagesError.value = err?.response?.data?.detail || "Não foi possível carregar as páginas.";
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
    pageTemplatesError.value = err?.response?.data?.detail || "Não foi possível carregar os modelos.";
  } finally {
    pageTemplatesLoading.value = false;
  }
};
const openTemplateDialog = (page: AdminPageSummary) => {
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
    const detail = err?.response?.data?.detail || "Não foi possível remover o modelo.";
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

type UserColumnKey = "name" | "gateway" | "whatsapp" | "agency_name" | "active_pages" | "draft_pages" | "plan" | "valid_until" | "created_at";
interface UserColumn {
  key: UserColumnKey;
  label: string;
  align?: "left" | "right";
  sortable?: boolean;
  widthClass?: string;
  cellClass?: string;
}

const userTableColumns: UserColumn[] = [
  {
    key: "name",
    label: "Nome",
    sortable: true,
    widthClass: "w-[12rem] min-w-[12rem] max-w-[12rem]",
    cellClass: "w-[12rem] min-w-[12rem] max-w-[12rem]"
  },
  {
    key: "gateway",
    label: "Gateway",
    sortable: true,
    widthClass: "w-[7rem] min-w-[7rem] max-w-[7rem]",
    cellClass: "w-[7rem] min-w-[7rem] max-w-[7rem]"
  },
  { key: "whatsapp", label: "WhatsApp", sortable: true },
  { key: "agency_name", label: "Agência", sortable: true },
  {
    key: "active_pages",
    label: "Ativas",
    align: "right",
    sortable: true,
    widthClass: "w-[5.5rem] min-w-[5.5rem] max-w-[5.5rem]",
    cellClass: "w-[5.5rem] min-w-[5.5rem] max-w-[5.5rem]"
  },
  {
    key: "draft_pages",
    label: "Rascunho",
    align: "right",
    sortable: true,
    widthClass: "w-[5.5rem] min-w-[5.5rem] max-w-[5.5rem]",
    cellClass: "w-[5.5rem] min-w-[5.5rem] max-w-[5.5rem]"
  },
  { key: "plan", label: "Plano", sortable: true },
  { key: "valid_until", label: "Validade", sortable: true },
  { key: "created_at", label: "Entrada", sortable: true }
];

const userFilters = reactive({
  name: "",
  gateways: [] as string[],
  whatsapp: "",
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
  gateway: null,
  whatsapp: null,
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
type LessonGroup = {
  key: string;
  label: string;
  moduleName: string;
  lessons: Lesson[];
};
const lessonGroups = computed<LessonGroup[]>(() => {
  const groups = new Map<string, LessonGroup>();
  for (const lesson of adminLessons.value) {
    const moduleName = (lesson.moduleName || "").trim();
    const key = moduleName || "__default__";
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        label: moduleName || "Sem módulo",
        moduleName,
        lessons: []
      });
    }
    groups.get(key)!.lessons.push(lesson);
  }
  return Array.from(groups.values());
});
const lessonModuleOptions = computed(() =>
  Array.from(new Set(adminLessons.value.map(lesson => lesson.moduleName.trim()).filter(Boolean))).sort((a, b) => a.localeCompare(b))
);
const lessonsLoading = computed(() => lessonsStore.loading);
const lessonSaving = ref(false);
const deletingLessonId = ref<number | null>(null);
const resettingLessons = ref(false);
const lessonForm = reactive({
  moduleName: "",
  title: "",
  description: "",
  duration: "",
  level: "",
  videoInput: "",
  thumbnailUrl: "",
  thumbnailData: "",
  thumbnailUploadName: "",
  helpArticle: ""
});
const lessonReplacement = (lesson: Lesson) =>
  articleReplacingLesson({ titulo: lesson.title, artigo: lesson.helpArticle, atualizadaEm: lesson.videoUpdatedAt });
const helpArticleOptions = HELP_MODULES.map(module => ({ label: module.titulo, articles: articlesOf(module.id) })).filter(group => group.articles.length);
const editingLessonId = ref<number | null>(null);
const isEditingLesson = computed(() => editingLessonId.value !== null);
const lessonPreview = computed(() => normalizeVideoInput(lessonForm.videoInput || ""));
const persistLessonGroupOrder = async (group: LessonGroup, lessonIds: number[]) => {
  const reorderAction = (lessonsStore as any).reorderLessonsInModule;
  if (typeof reorderAction === "function") {
    await reorderAction.call(lessonsStore, group.moduleName, lessonIds);
    return;
  }
  const { data } = await api.post("/lessons/reorder", {
    module_name: group.moduleName.trim() || null,
    lesson_ids: lessonIds
  });
  lessonsStore.lessons = data.map((lesson: any) => ({
    id: lesson.id,
    moduleName: (lesson.module_name || "").trim(),
    sortOrder: lesson.sort_order ?? 0,
    title: lesson.title,
    description: lesson.description || "",
    duration: lesson.duration || "",
    level: lesson.level || "",
    videoType: lesson.video_type,
    videoUrl: lesson.video_url,
    thumbnail: lesson.thumbnail_url || undefined,
    helpArticle: lesson.help_article || undefined,
    videoUpdatedAt: lesson.video_updated_at || lesson.updated_at || lesson.created_at || undefined
  }));
  lessonsStore.loaded = true;
};

const moveLessonInGroup = async (group: LessonGroup, index: number, delta: -1 | 1) => {
  const targetIndex = index + delta;
  if (targetIndex < 0 || targetIndex >= group.lessons.length) return;
  const reordered = [...group.lessons];
  const [moved] = reordered.splice(index, 1);
  if (!moved) return;
  reordered.splice(targetIndex, 0, moved);
  lessonSaving.value = true;
  try {
    await persistLessonGroupOrder(group, reordered.map(lesson => lesson.id));
    showSnackbar("Ordem atualizada.");
  } catch (err) {
    console.error(err);
    showSnackbar("Não foi possível reordenar as aulas.");
  } finally {
    lessonSaving.value = false;
  }
};

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
    error.value = "Não foi possível carregar os dados.";
    }
  }
};

const loadRevenueForecast = async () => {
  revenueForecastLoading.value = true;
  revenueForecastError.value = "";
  try {
    const { data } = await api.get<RevenueForecastOut>("/admin/revenue-forecast", {
      params: { days: 30 }
    });
    revenueForecast.value = data;    const firstWithEntries = (data.forecast_days || []).find(day => (day.subscriptions_count || 0) > 0);
    selectedForecastDate.value = (firstWithEntries?.date || data.forecast_days?.[0]?.date || "").slice(0, 10);
  } catch (err: any) {
    console.error(err);
    revenueForecast.value = null;    selectedForecastDate.value = "";
    revenueForecastError.value = err?.response?.data?.detail || "Não foi possível carregar a previsão de receita.";
  } finally {
    revenueForecastLoading.value = false;
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
    const message = err?.response?.data?.detail || "Não foi possível carregar o monitor agora.";
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
    showSnackbar(`Sessões de ${session.user_name} encerradas.`);
    await loadOnlineSessions();
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail || "Não foi possível deslogar este usuário.";
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
  lessonForm.moduleName = "";
  lessonForm.title = "";
  lessonForm.description = "";
  lessonForm.duration = "";
  lessonForm.level = "";
  lessonForm.videoInput = "";
  lessonForm.thumbnailUrl = "";
  lessonForm.thumbnailData = "";
  lessonForm.thumbnailUploadName = "";
  lessonForm.helpArticle = "";
};

const startLessonEdit = (lesson: Lesson) => {
  editingLessonId.value = lesson.id;
  lessonForm.moduleName = lesson.moduleName || "";
  lessonForm.title = lesson.title;
  lessonForm.description = lesson.description;
  lessonForm.duration = lesson.duration;
  lessonForm.level = lesson.level;
  lessonForm.videoInput = lesson.videoUrl;
  const isDataUrl = Boolean(lesson.thumbnail?.startsWith("data:"));
  lessonForm.thumbnailUrl = isDataUrl ? "" : lesson.thumbnail || "";
  lessonForm.thumbnailData = isDataUrl ? lesson.thumbnail || "" : "";
  lessonForm.thumbnailUploadName = isDataUrl ? "Imagem enviada" : "";
  lessonForm.helpArticle = lesson.helpArticle || "";
};

const saveLesson = async () => {
  if (!lessonForm.title.trim() || !lessonForm.videoInput.trim()) {
    showSnackbar("Informe Título e link do vídeo.");
    return;
  }
  const parsed = normalizeVideoInput(lessonForm.videoInput);
  if (!parsed.videoUrl) {
    showSnackbar("Link de vídeo inválido.");
    return;
  }
  const payload = {
    moduleName: lessonForm.moduleName.trim(),
    title: lessonForm.title.trim(),
    description: lessonForm.description.trim(),
    duration: lessonForm.duration.trim(),
    level: lessonForm.level.trim(),
    videoType: parsed.videoType,
    videoUrl: parsed.videoUrl,
    thumbnailUrl: lessonForm.thumbnailUrl || undefined,
    thumbnailBase64: lessonForm.thumbnailData || undefined,
    helpArticle: lessonForm.helpArticle
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
    lessonDrawerOpen.value = false;
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

const userGatewayOptions = computed(() => {
  const providers = new Set<string>();
  metrics.value?.users?.forEach(user => {
    const provider = String(user.subscription_provider || "").trim().toLowerCase();
    if (provider) providers.add(provider);
  });
  providers.add("__none");
  return Array.from(providers).sort();
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
  const selectedGateways = userFilters.gateways;
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
    const whatsappTerm = userFilters.whatsapp.trim().toLowerCase();
    const matchesWhatsapp = !whatsappTerm || (user.whatsapp || "").toLowerCase().includes(whatsappTerm);

    const gatewayKey = (user.subscription_provider || "__none").toLowerCase();
    const matchesGateway = !selectedGateways.length || selectedGateways.includes(gatewayKey);

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

    return (
      matchesUserQuickFilter(user, userQuickFilter.value) &&
      matchesName &&
      matchesGateway &&
      matchesWhatsapp &&
      matchesAgency &&
      matchesPlan &&
      matchesActive &&
      matchesDraft &&
      matchesValid &&
      matchesCreated
    );
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
      case "whatsapp":
        return user.whatsapp?.toLowerCase() || "";
      case "gateway":
        return (user.subscription_provider || "").toLowerCase();
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
    case "whatsapp":
      userFilters.whatsapp = "";
      break;
    case "gateway":
      userFilters.gateways = [];
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
    case "whatsapp":
      return Boolean(userFilters.whatsapp.trim());
    case "gateway":
      return userFilters.gateways.length > 0;
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
  if (templateMenuId.value !== null) {
    const insideTemplateMenu = path.some(el => (el as HTMLElement)?.dataset?.templateMenu === "true");
    if (!insideTemplateMenu) templateMenuId.value = null;
  }
  if (rowMenuUserId.value !== null) {
    const insideRowMenu = path.some(el => (el as HTMLElement)?.dataset?.rowMenu === "true");
    if (!insideRowMenu) rowMenuUserId.value = null;
  }
  if (subscriptionActionMenu.open) {
    const insideSubscriptionAction = path.some(
      el => (el as HTMLElement)?.dataset?.subscriptionActionMenu === "true"
    );
    if (!insideSubscriptionAction) {
      closeSubscriptionActionMenu();
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
  doc.text("Visão Gerencial  Relatório Premium", margin, cursor);
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
  doc.text("usuários  Trial e planos", margin, cursor);
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

const openCreateUserDialog = () => {
  Object.assign(createUserDialog, {
    open: true,
    name: "",
    email: "",
    whatsapp: "",
    password: "",
    plan: "essencial",
    validUntil: "",
    saving: false,
    error: ""
  });
};

const closeCreateUserDialog = () => {
  if (createUserDialog.saving) return;
  createUserDialog.open = false;
  createUserDialog.error = "";
};

const submitCreateUser = async () => {
  createUserDialog.saving = true;
  createUserDialog.error = "";
  try {
    await api.post("/admin/users", {
      name: createUserDialog.name.trim(),
      email: createUserDialog.email.trim().toLowerCase(),
      whatsapp: createUserDialog.whatsapp.trim() || null,
      password: createUserDialog.password,
      plan: createUserDialog.plan,
      valid_until: createUserDialog.validUntil
    });
    createUserDialog.open = false;
    showSnackbar("Usuário criado com sucesso.");
    await loadMetrics();
  } catch (err: any) {
    console.error(err);
    createUserDialog.error = err?.response?.data?.detail || "Não foi possível criar o usuário.";
  } finally {
    createUserDialog.saving = false;
  }
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
    showSnackbar("usuário excluído com sucesso.");
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

const canRefundUser = (user: Metrics["users"][number]) => {
  if (user.is_superuser) return false;
  const provider = (user.subscription_provider || "").toLowerCase();
  const status = (user.subscription_status || "").toLowerCase();
  return provider === "cakto" && Boolean(user.subscription_cakto_order_id) && status === "active" && user.is_active !== false;
};

const subscriptionProviderLabel = (user: Metrics["users"][number]) => {
  const provider = (user.subscription_provider || "").trim().toLowerCase();
  if (!provider) return "Indefinido";
  if (provider === "asaas") return "Asaas";
  if (provider === "cakto") return "Cakto";
  return provider.charAt(0).toUpperCase() + provider.slice(1);
};

const subscriptionProviderIdentifier = (user: Metrics["users"][number]) => {
  const provider = (user.subscription_provider || "").trim().toLowerCase();
  if (provider === "asaas") return user.subscription_asaas_subscription_id || "-";
  if (provider === "cakto") return user.subscription_cakto_subscription_code || user.subscription_cakto_order_id || "-";
  return user.subscription_asaas_subscription_id || user.subscription_cakto_subscription_code || user.subscription_cakto_order_id || "-";
};

const isCancelAtPeriodEnd = (user: Metrics["users"][number]) => {
  return (user.subscription_status || "").toLowerCase() === "cancel_at_period_end";
};

const formatSubscriptionStatus = (user: Metrics["users"][number]) => {
  const raw = (user.subscription_status || "").toLowerCase();
  const provider = (user.subscription_provider || "").toLowerCase();
  const hasAsaasSubId = Boolean((user.subscription_asaas_subscription_id || "").trim());

  // Backward compatibility: before introducing `cancelled_admin`, immediate cancels were saved as `past_due`.
  // If Asaas subscription id no longer exists, treat it as cancelled in admin view.
  if (raw === "past_due" && provider === "asaas" && !hasAsaasSubId) return "Cancelada";

  if (raw === "active") return "Ativa";
  if (raw === "cancelled") return "Cancelada";
  if (raw === "cancelled_admin") return "Cancelada";
  if (raw === "cancel_at_period_end") return "Cancelamento agendado";
  if (raw === "past_due") return "Vencida";
  if (!raw) return "Indefinido";
  return user.subscription_status || "Indefinido";
};

const adminCancelAsaasImmediate = async (user: Metrics["users"][number]) => {
  if (!auth.user?.is_superuser) return;
  adminAsaasActionLoadingUserId.value = user.id;
  error.value = "";
  try {
    await api.post(`/admin/users/${user.id}/asaas-cancel-immediate`, {});
    showSnackbar("Assinatura cancelada imediatamente.");
    await loadMetrics();
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || "Não foi possível cancelar a assinatura agora.";
    showSnackbar(error.value);
  } finally {
    adminAsaasActionLoadingUserId.value = null;
  }
};

const adminScheduleAsaasCancelAtPeriodEnd = async (user: Metrics["users"][number]) => {
  if (!auth.user?.is_superuser) return;
  adminAsaasActionLoadingUserId.value = user.id;
  error.value = "";
  try {
    await api.post(`/admin/users/${user.id}/asaas-cancel-at-period-end`, {});
    showSnackbar("Cancelamento programado para o fim da validade.");
    await loadMetrics();
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || "Não foi possível programar o cancelamento.";
    showSnackbar(error.value);
  } finally {
    adminAsaasActionLoadingUserId.value = null;
  }
};

const adminCancelScheduledAsaasCancellation = async (user: Metrics["users"][number]) => {
  if (!auth.user?.is_superuser) return;
  adminAsaasActionLoadingUserId.value = user.id;
  error.value = "";
  try {
    await api.post(`/admin/users/${user.id}/asaas-cancel-scheduled-cancellation`, {});
    showSnackbar("Cancelamento programado removido.");
    await loadMetrics();
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || "Não foi possível desfazer o cancelamento programado.";
    showSnackbar(error.value);
  } finally {
    adminAsaasActionLoadingUserId.value = null;
  }
};

const closeSubscriptionActionMenu = () => {
  subscriptionActionMenu.open = false;
  subscriptionActionMenu.userId = null;
  subscriptionActionMenu.kind = null;
};

const toggleSubscriptionActionMenu = (userId: number, kind: SubscriptionActionKind) => {
  if (subscriptionActionMenu.open && subscriptionActionMenu.userId === userId && subscriptionActionMenu.kind === kind) {
    closeSubscriptionActionMenu();
    return;
  }
  subscriptionActionMenu.open = true;
  subscriptionActionMenu.userId = userId;
  subscriptionActionMenu.kind = kind;
};

const closeSubscriptionActionDialog = () => {
  subscriptionActionDialog.open = false;
  subscriptionActionDialog.user = null;
  subscriptionActionDialog.kind = null;
  subscriptionActionDialog.value = "";
  subscriptionActionDialog.label = "";
  subscriptionActionDialog.saving = false;
  subscriptionActionDialog.error = "";
};

const openSubscriptionActionDialog = (
  user: Metrics["users"][number],
  kind: SubscriptionActionKind,
  option: SubscriptionActionOption
) => {
  subscriptionActionDialog.open = true;
  subscriptionActionDialog.user = user;
  subscriptionActionDialog.kind = kind;
  subscriptionActionDialog.value = option.value;
  subscriptionActionDialog.label = option.label;
  subscriptionActionDialog.saving = false;
  subscriptionActionDialog.error = "";
  closeSubscriptionActionMenu();
};

const openValidityDialog = (user: Metrics["users"][number]) => {
  subscriptionActionDialog.open = true;
  subscriptionActionDialog.user = user;
  subscriptionActionDialog.kind = "validity";
  subscriptionActionDialog.value = toDateInputValue(user.valid_until);
  subscriptionActionDialog.label = user.valid_until ? formatDate(user.valid_until) : "Sem validade definida";
  subscriptionActionDialog.saving = false;
  subscriptionActionDialog.error = "";
  closeSubscriptionActionMenu();
};

const confirmSubscriptionAction = async () => {
  const dialog = subscriptionActionDialog;
  if (!dialog.user || !dialog.kind) return;
  if (dialog.kind === "validity" && !dialog.value) {
    dialog.error = "Informe a nova validade.";
    return;
  }
  if (dialog.kind !== "validity" && !dialog.value) return;
  dialog.saving = true;
  dialog.error = "";
  try {
    const payload =
      dialog.kind === "validity"
        ? { valid_until: dialog.value }
        : { [dialog.kind]: dialog.value };
    await api.patch(`/admin/users/${dialog.user.id}/subscription`, payload);
    showSnackbar(
      dialog.kind === "plan"
        ? `Plano atualizado para ${dialog.label}.`
        : dialog.kind === "status"
          ? `Status atualizado para ${dialog.label}.`
          : `Validade atualizada para ${formatDate(dialog.value) || dialog.value}.`
    );
    closeSubscriptionActionDialog();
    expandedUser.value = null;
    await loadMetrics();
  } catch (err: any) {
    console.error(err);
    dialog.error = err?.response?.data?.detail || "Não foi possível atualizar a assinatura agora.";
    dialog.saving = false;
  }
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
    dialog.error = err?.response?.data?.detail || "Não foi possível solicitar o reembolso agora.";
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
    showSnackbar("usuário não possui Agência vinculada.");
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
    linkPageDialog.value.error = "Não foi possível carregar suas páginas.";
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
    dialog.error = err?.response?.data?.detail || "Não foi possível vincular a página.";
    dialog.saving = false;
  }
};
// ---------- Visual do admin master ----------
const intFormatter = new Intl.NumberFormat("pt-BR");
const formatInt = (value?: number | null) => intFormatter.format(Number(value || 0));
const formatMoney = (value?: number | null) =>
  value === null || value === undefined || !Number.isFinite(Number(value))
    ? "—"
    : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value));
const formatPercent = (value?: number | null) =>
  `${new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value || 0))}%`;
const initials = (name?: string | null) =>
  String(name || "?")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase() || "")
    .join("") || "?";

const periodOptions: Array<{ value: AdminPeriodOption; label: string }> = [
  { value: "7", label: "7 dias" },
  { value: "30", label: "30 dias" },
  { value: "90", label: "90 dias" },
  { value: "custom", label: "Personalizado" }
];

const normalizedPlan = (plan?: string | null) => String(plan || "").trim().toLowerCase();
const isTrialUser = (user: Metrics["users"][number]) =>
  Boolean(user.trial_plan) || ["trial", "teste", "test"].includes(normalizedPlan(user.plan));
const isCancelledUser = (user: Metrics["users"][number]) => {
  const status = String(user.subscription_status || "").toLowerCase();
  return status.startsWith("cancelled") || status === "inactive";
};
const daysUntil = (value?: string | null) => {
  if (!value) return null;
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return null;
  return Math.ceil((time - Date.now()) / 86_400_000);
};

const planToneClass = (plan?: string | null) => {
  const label = getPlanLabel(plan);
  if (label === "Escala") return "am-tone-success";
  if (label === "Agência") return "am-tone-info";
  if (label === "Teste" || label === "Trial") return "am-tone-warning";
  return "am-tone-neutral";
};

const platformTotals = computed(() => [
  {
    label: "Usuários",
    icon: "users",
    value: formatInt(metrics.value?.total_users ?? 0),
    hint: `+${formatInt(metrics.value?.new_users_last_days ?? 0)} no período`
  },
  {
    label: "Agências",
    icon: "home",
    value: formatInt(metrics.value?.total_agencies ?? 0),
    hint: "Times cadastrados"
  },
  {
    label: "Páginas",
    icon: "pages",
    value: formatInt(metrics.value?.total_pages ?? 0),
    hint: `${formatInt(metrics.value?.published_pages ?? 0)} publicadas`
  }
]);

const planColors = ["var(--chart-1)", "var(--chart-3)", "var(--chart-4)", "var(--chart-6)", "var(--chart-7)", "var(--muted-foreground)"];
const planDistributionTotal = computed(() =>
  (metrics.value?.plans || []).reduce((sum, item) => sum + Number(item.count || 0), 0)
);
const planDistribution = computed(() => {
  const items = [...(metrics.value?.plans || [])].sort((a, b) => b.count - a.count);
  const total = planDistributionTotal.value || 1;
  const max = Math.max(1, ...items.map(item => item.count));
  return items.map((item, index) => ({
    plan: item.plan,
    label: planLabel(item.plan),
    count: item.count,
    percent: Math.round((item.count / total) * 100),
    bar: (item.count / max) * 100,
    color: planColors[index % planColors.length]
  }));
});

const attentionItems = computed(() => {
  const users = metrics.value?.users || [];
  const paymentIssues = users.filter(user =>
    ["failed", "past_due", "pending"].includes(String(user.subscription_status || "").toLowerCase())
  ).length;
  const expiring = users.filter(user => {
    if (isCancelledUser(user) || isTrialUser(user)) return false;
    const left = daysUntil(user.valid_until);
    return left !== null && left >= 0 && left <= 7;
  }).length;
  const trialsEnding = users.filter(user => {
    if (!isTrialUser(user)) return false;
    const left = daysUntil(user.trial_ends_at || user.valid_until);
    return left !== null && left >= 0 && left <= 3;
  }).length;
  const whatsapp = adminMasterCounts.whatsappIssues ?? 0;
  return [
    {
      id: "payments",
      icon: "alert",
      tone: "danger",
      title: `${formatInt(paymentIssues)} ${paymentIssues === 1 ? "pagamento" : "pagamentos"} com problema`,
      description: "Assinaturas pendentes, em atraso ou com falha",
      target: "Conciliação",
      to: "/admin/administracao/conciliacao"
    },
    {
      id: "expiring",
      icon: "cal",
      tone: "warning",
      title: `${formatInt(expiring)} ${expiring === 1 ? "vencimento" : "vencimentos"}`,
      description: "Nos próximos 7 dias",
      target: "Usuários",
      to: { path: "/admin/administracao/usuarios", query: { filtro: "vencem" } }
    },
    {
      id: "whatsapp",
      icon: "wa",
      tone: "warning",
      title: `${formatInt(whatsapp)} WhatsApp ${whatsapp === 1 ? "desconectado" : "desconectados"}`,
      description: "Conexões das agências fora do ar",
      target: "WhatsApp",
      to: "/admin/administracao/whatsapp"
    },
    {
      id: "trials",
      icon: "user",
      tone: "info",
      title: `${formatInt(trialsEnding)} ${trialsEnding === 1 ? "teste termina" : "testes terminam"}`,
      description: "Em até 3 dias",
      target: "Usuários",
      to: { path: "/admin/administracao/usuarios", query: { filtro: "teste" } }
    }
  ];
});

const isMobileDevice = (label?: string | null) => /android|iphone|ipad|ios|mobile|celular/i.test(String(label || ""));
const monitorDeviceSplit = computed(() => {
  const mobile = onlineSessions.value.filter(session => isMobileDevice(`${session.device_label} ${session.client_name}`)).length;
  return { mobile, desktop: onlineSessions.value.length - mobile };
});
const monitorInEditor = computed(
  () => onlineSessions.value.filter(session => /\/admin\/pages\/[^/]+\/edit/.test(String(session.last_path || ""))).length
);

const pathLabels: Array<[RegExp, string]> = [
  [/^\/admin\/pages\/[^/]+\/edit/, "Editor de página"],
  [/^\/admin\/pages/, "Páginas"],
  [/^\/admin\/dashboard/, "Dashboard"],
  [/^\/admin\/leads\/forms/, "Leads › Formulários"],
  [/^\/admin\/leads\/opportunities/, "Leads › Oportunidades"],
  [/^\/admin\/leads\/clients/, "Leads › Clientes"],
  [/^\/admin\/leads\/settings/, "Leads › Configurações"],
  [/^\/admin\/inbox/, "Caixa de entrada"],
  [/^\/admin\/integracoes/, "Integrações"],
  [/^\/admin\/agency\/team/, "Minha agência › Equipe"],
  [/^\/admin\/agency\/invoices/, "Minha agência › Faturas"],
  [/^\/admin\/agency/, "Minha agência"],
  [/^\/admin\/domains/, "Domínios"],
  [/^\/admin\/aulas/, "Aulas"],
  [/^\/admin\/perfil/, "Perfil"],
  [/^\/admin\/planos/, "Planos"],
  [/^\/admin\/administracao/, "Admin master"]
];
const pathLabel = (path?: string | null) => {
  if (!path) return "Não identificado";
  const clean = path.split("?")[0];
  return pathLabels.find(([pattern]) => pattern.test(clean))?.[1] || "Outra tela";
};

type UserQuickFilter = "all" | "paying" | "trial" | "soon" | "expired" | "cancelled";
const userQuickFilterOptions: Array<{ id: UserQuickFilter; label: string }> = [
  { id: "all", label: "Todos" },
  { id: "paying", label: "Pagantes" },
  { id: "trial", label: "Em teste" },
  { id: "soon", label: "Vencem em 7 dias" },
  { id: "expired", label: "Vencidos" },
  { id: "cancelled", label: "Cancelados" }
];
const quickFilterFromQuery = (value: unknown): UserQuickFilter => {
  const raw = String(Array.isArray(value) ? value[0] : value || "");
  if (raw === "vencem") return "soon";
  if (raw === "teste") return "trial";
  if (raw === "vencidos") return "expired";
  if (raw === "pagantes") return "paying";
  if (raw === "cancelados") return "cancelled";
  return "all";
};
const userQuickFilter = ref<UserQuickFilter>(quickFilterFromQuery(route.query.filtro));
const validityState = (user: Metrics["users"][number]) => {
  const left = daysUntil(user.valid_until);
  if (left === null) return "none";
  if (left < 0) return "expired";
  if (left <= 7) return "soon";
  return "ok";
};
const daysLeftLabel = (value?: string | null) => {
  const left = daysUntil(value);
  if (left === null) return "";
  if (left <= 0) return "hoje";
  return left === 1 ? "1 dia" : `${left} dias`;
};
const matchesUserQuickFilter = (user: Metrics["users"][number], filter: UserQuickFilter) => {
  if (filter === "all") return true;
  const cancelled = isCancelledUser(user);
  const trial = isTrialUser(user);
  const validity = validityState(user);
  if (filter === "cancelled") return cancelled;
  if (filter === "trial") return trial && !cancelled;
  if (filter === "soon") return !cancelled && validity === "soon";
  if (filter === "expired") return !cancelled && validity === "expired";
  const status = String(user.subscription_status || "").toLowerCase();
  return !trial && !cancelled && normalizedPlan(user.plan) !== "free" && ["active", "cancel_at_period_end"].includes(status);
};
const userQuickFilterCounts = computed(() => {
  const users = metrics.value?.users || [];
  return userQuickFilterOptions.reduce(
    (acc, option) => {
      acc[option.id] = users.filter(user => matchesUserQuickFilter(user, option.id)).length;
      return acc;
    },
    {} as Record<UserQuickFilter, number>
  );
});
watch(userQuickFilter, () => {
  expandedUser.value = null;
  userPage.value = 1;
});
watch(
  () => route.query.filtro,
  value => {
    if (value !== undefined) userQuickFilter.value = quickFilterFromQuery(value);
  }
);

const singleSelect = (key: "plans" | "gateways" | "agencies") =>
  computed<string>({
    get: () => userFilters[key][0] || "",
    set: value => {
      userFilters[key] = value ? [value] : [];
    }
  });
const userPlanSelect = singleSelect("plans");
const userGatewaySelect = singleSelect("gateways");
const userAgencySelect = singleSelect("agencies");
const showMoreUserFilters = ref(false);
const moreUserFiltersActive = computed(() =>
  Boolean(
    userFilters.whatsapp ||
      userFilters.agencies.length ||
      userFilters.activeMin ||
      userFilters.activeMax ||
      userFilters.draftMin ||
      userFilters.draftMax ||
      userFilters.validFrom ||
      userFilters.validTo ||
      userFilters.createdFrom ||
      userFilters.createdTo
  )
);
const clearAllUserFilters = () => {
  userFilters.name = "";
  userFilters.whatsapp = "";
  userFilters.gateways = [];
  userFilters.agencies = [];
  userFilters.plans = [];
  userFilters.activeMin = "";
  userFilters.activeMax = "";
  userFilters.draftMin = "";
  userFilters.draftMax = "";
  userFilters.validFrom = "";
  userFilters.validTo = "";
  userFilters.createdFrom = "";
  userFilters.createdTo = "";
};
const userListColumns: Array<{ key: string; label: string; sort?: UserColumnKey; class?: string }> = [
  { key: "name", label: "Pessoa", sort: "name" },
  { key: "agency", label: "Agência", sort: "agency_name" },
  { key: "plan", label: "Plano", sort: "plan" },
  { key: "gateway", label: "Cobrança", sort: "gateway" },
  { key: "pages", label: "Páginas", sort: "active_pages" },
  { key: "valid", label: "Validade", sort: "valid_until" },
  { key: "created", label: "Entrou em", sort: "created_at" },
  { key: "actions", label: "", class: "w-12" }
];
const draftCount = (user: Metrics["users"][number]) =>
  typeof user.draft_pages_count === "number" ? user.draft_pages_count : user.draft_pages?.length ?? 0;
const gatewayLabel = (value?: string | null) => {
  const provider = String(value || "").trim().toLowerCase();
  if (!provider) return "—";
  if (provider === "asaas") return "Asaas";
  if (provider === "cakto") return "Cakto";
  return provider.charAt(0).toUpperCase() + provider.slice(1);
};
const rowMenuUserId = ref<number | null>(null);
const runUserMenu = (action: () => unknown) => {
  rowMenuUserId.value = null;
  action();
};

const forecastBusyDays = computed(() => revenueForecastDays.value.filter(day => day.subscriptions_count > 0).length);
const forecastProviderSplit = computed(() => {
  const totals = new Map<string, number>();
  let sum = 0;
  revenueForecastDays.value.forEach(day =>
    day.entries.forEach(entry => {
      const key = gatewayLabel(entry.provider);
      totals.set(key, (totals.get(key) || 0) + Number(entry.mrr_amount || 0));
      sum += Number(entry.mrr_amount || 0);
    })
  );
  const parts = [...totals.entries()].sort((a, b) => b[1] - a[1]);
  if (!parts.length || !sum) return { label: "—", hint: "Sem cobranças no período" };
  const [first] = parts;
  return {
    label: `${first[0]} ${Math.round((first[1] / sum) * 100)}%`,
    hint: parts
      .slice(1)
      .map(([name, value]) => `${name} ${Math.round((value / sum) * 100)}%`)
      .join(" · ") || "Única forma de cobrança"
  };
});
const forecastMaxDay = computed(() => Math.max(1, ...revenueForecastDays.value.map(day => Number(day.total_mrr || 0))));
const forecastHeatClass = (value: number) => {
  if (!value) return "";
  const ratio = value / forecastMaxDay.value;
  if (ratio > 0.66) return "heat-3";
  if (ratio > 0.33) return "heat-2";
  return "heat-1";
};
const formatCompactMoney = (value: number) =>
  `R$ ${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(Math.round(Number(value || 0)))}`;
const formatForecastWeekday = (value: string) => {
  const date = parseForecastIsoDate(value.slice(0, 10));
  return date.toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "2-digit" });
};

const lessonDrawerOpen = ref(false);
const openNewLesson = (moduleName = "") => {
  resetLessonForm();
  lessonForm.moduleName = moduleName;
  lessonDrawerOpen.value = true;
};
const openLessonEdit = (lesson: Lesson) => {
  startLessonEdit(lesson);
  lessonDrawerOpen.value = true;
};
const closeLessonDrawer = () => {
  lessonDrawerOpen.value = false;
  resetLessonForm();
};

const templatesTab = ref<"published" | "create">("published");
const templateMenuId = ref<number | null>(null);
const runTemplateMenu = (action: () => unknown) => {
  templateMenuId.value = null;
  void action();
};
const coverGradients = [
  "linear-gradient(135deg, #1e3a5f, #3b6e8f 55%, #d9a066)",
  "linear-gradient(135deg, #0e4d64, #1fa2b8 60%, #f3d28b)",
  "linear-gradient(135deg, #4a1d6b, #a23d8f 55%, #f6b73c)",
  "linear-gradient(135deg, #1a1a2e, #3e2a5e 60%, #e94560)",
  "linear-gradient(135deg, #3b2f1e, #8a6a3a 55%, #e8d5a8)",
  "linear-gradient(135deg, #0b3d2e, #1a7f5a 55%, #b6e3c9)"
];
const templateCoverStyle = (template: PageTemplate) => {
  const match = JSON.stringify(template.config_json || {}).match(/https?:[^"\s]+?\.(?:jpe?g|png|webp|avif)(?:\?[^"\s]*)?/i);
  const gradient = coverGradients[template.id % coverGradients.length];
  return match
    ? { backgroundImage: `linear-gradient(180deg, transparent 40%, rgba(0,0,0,.35)), url("${match[0].replace(/\\\//g, "/")}")`, backgroundSize: "cover", backgroundPosition: "center" }
    : { backgroundImage: gradient };
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
  try {
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
    if (activeTab.value === "revenue_forecast") {
      await loadRevenueForecast();
    }
    startOnlineSessionsPolling();
  } finally {
    isBootstrappingAdminManagement.value = false;
  }
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

watch(
  () => route.name,
  () => {
    syncActiveTabFromRoute();
  },
  { immediate: true }
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
  if (tab === "revenue_forecast" && !revenueForecast.value && !revenueForecastLoading.value) {
    loadRevenueForecast();
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
.admin-master-view {
  --card-border: var(--border);
  --ink-900: var(--foreground);
  --ink-500: var(--muted-foreground);
  --surface: var(--card);
  --shadow: var(--shadow-soft);
}

.topbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (min-width: 768px) {
  .topbar {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.page-kicker {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.24em;
  color: var(--ink-500);
  font-weight: 700;
}

.page-title {
  margin-top: 4px;
  font-size: 22px;
  line-height: 1.1;
  font-weight: 800;
  color: var(--ink-900);
}

.page-sub {
  margin-top: 4px;
  color: var(--ink-500);
  font-size: 14px;
}

.metrics-grid {
  display: grid;
  gap: 16px;
}

.metrics-grid-4 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.metrics-grid-3 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

@media (min-width: 768px) {
  .metrics-grid-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .metrics-grid-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.metric-card {
  border-radius: 18px;
  border: 1px solid var(--card-border);
  background: var(--surface);
  box-shadow: var(--shadow);
  padding: 16px 18px;
}

.metric-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.34em;
  color: #5f7990;
  font-weight: 700;
}

.metric-value {
  margin-top: 8px;
  font-size: 30px;
  line-height: 1;
  font-weight: 800;
  color: var(--ink-900);
}

.metric-footer-text {
  margin-top: 6px;
  color: var(--ink-500);
  font-size: 13px;
}

.chart-card,
.list-card {
  border-radius: 18px;
  border: 1px solid var(--card-border);
  background: var(--surface);
  box-shadow: var(--shadow);
  padding: 18px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

@media (min-width: 1024px) {
  .bottom-grid {
    grid-template-columns: 2fr 1fr;
  }
}

.chart-tooltip {
  position: absolute;
  transform: translate(-50%, -100%);
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.4;
  box-shadow: var(--shadow-elegant);
  pointer-events: none;
  z-index: 20;
}

.chart-tooltip-date {
  font-weight: 700;
  margin-bottom: 4px;
}

.am-cal-day {
  display: flex;
  min-height: 62px;
  flex-direction: column;
  justify-content: space-between;
  border-radius: 12px;
  background: var(--muted);
  padding: 7px 8px;
  text-align: left;
  color: var(--muted-foreground);
  transition: box-shadow 0.15s ease;
}
.am-cal-day b {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--foreground);
}
.am-cal-day:not(:disabled):hover {
  box-shadow: inset 0 0 0 1px var(--border);
}
.am-cal-day.is-off {
  border: 1px dashed var(--border);
  background: transparent;
}
.am-cal-day.heat-1 {
  background: color-mix(in srgb, var(--primary) 10%, var(--muted));
}
.am-cal-day.heat-2 {
  background: color-mix(in srgb, var(--primary) 22%, var(--muted));
}
.am-cal-day.heat-3 {
  background: color-mix(in srgb, var(--primary) 36%, var(--muted));
}
.am-cal-day.is-selected {
  box-shadow: inset 0 0 0 2px var(--primary);
  color: var(--foreground);
}
@media (max-width: 640px) {
  .am-cal-day {
    min-height: 48px;
    padding: 5px;
  }
  .am-cal-day b {
    font-size: 10px;
  }
}

.tpl-card {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--card);
  box-shadow: var(--shadow-card);
}
.tpl-cover {
  position: relative;
  height: 128px;
  background-color: var(--muted);
}

.lesson-thumb {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 72px;
  height: 42px;
  overflow: hidden;
  border-radius: 8px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--chart-3) 55%, var(--muted)), color-mix(in srgb, var(--chart-1) 45%, var(--muted)));
  color: #fff;
}
.lesson-thumb svg {
  width: 16px;
  height: 16px;
}

.am-user-detail {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: color-mix(in srgb, var(--muted) 55%, var(--card));
  padding: 16px;
}
.am-detail-row:hover td {
  background: transparent !important;
}

.legend-toggle-sub {
  transition: opacity 0.15s ease;
}

.legend-toggle-sub.off {
  opacity: 0.35;
}

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

</style>

interface AdminPageSummary {
  id: number;
  title: string;
  slug: string;
  status: string;
}




