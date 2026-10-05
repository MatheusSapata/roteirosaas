<template>
  <div v-if="isBootstrappingIntegrations" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8 md:px-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
  </div>

  <div v-else class="integrations-view w-full space-y-6 px-4 py-6 md:px-8">
    <IntegrationsHeader />

    <!-- Visão geral -->
    <template v-if="isOverviewRoute">
      <section class="iv-group">
        <h2 class="iv-group-title">Rastreamento <span>Medir visitas e conversões das suas páginas</span></h2>
        <div class="iv-cards">
          <article v-for="kind in trackingKinds" :key="kind.type" class="iv-card">
            <header class="iv-card-head">
              <span class="iv-logo" :class="kind.tone">
                <template v-if="kind.type === 'meta'">M</template>
                <ChartLineIcon v-else aria-hidden="true" />
              </span>
              <div class="min-w-0">
                <h3>{{ kind.label }}</h3>
                <span class="iv-pill" :class="kind.count ? 'is-on' : 'is-off'">{{ kind.count ? `${kind.count} ${kind.count === 1 ? "código" : "códigos"}` : "Não configurado" }}</span>
              </div>
            </header>
            <p class="iv-card-text">{{ kind.description }}</p>
            <p v-if="kind.first" class="iv-card-meta">{{ kind.first }}</p>
            <footer class="iv-card-foot">
              <router-link to="/admin/integracoes/rastreamento" :class="kind.count ? 'iv-soft' : 'iv-btn-primary iv-btn-sm'">{{ kind.count ? "Gerenciar" : "Conectar" }}</router-link>
            </footer>
          </article>
        </div>
      </section>

      <section class="iv-group">
        <h2 class="iv-group-title">Sistemas e atendimento <span>Pacotes, conversas e WhatsApp</span></h2>
        <div class="iv-cards">
          <article class="iv-card">
            <header class="iv-card-head">
              <span class="iv-logo iv-logo-vo">VO</span>
              <div class="min-w-0">
                <h3>Viaje On</h3>
                <span class="iv-pill" :class="viajeonStatus.connected ? 'is-on' : 'is-off'">{{ viajeonStatus.connected ? "Conectado" : viajeonStatus.configured ? "Com problema" : "Não configurado" }}</span>
              </div>
            </header>
            <p class="iv-card-text">Mostra os pacotes ativos do Viaje On direto nas suas páginas.</p>
            <p v-if="viajeonStatus.sso_email" class="iv-card-meta">Entra com {{ viajeonStatus.sso_email }}</p>
            <footer class="iv-card-foot">
              <router-link to="/admin/integracoes/viajeon" :class="viajeonStatus.configured ? 'iv-soft' : 'iv-btn-primary iv-btn-sm'">{{ viajeonStatus.configured ? "Gerenciar" : "Conectar" }}</router-link>
            </footer>
          </article>
          <article class="iv-card">
            <header class="iv-card-head">
              <span class="iv-logo tone-violet">
                <MessageSquareIcon aria-hidden="true" />
              </span>
              <div class="min-w-0">
                <h3>ViajeChat</h3>
                <span class="iv-pill" :class="viajechatStatus.configured ? 'is-on' : 'is-off'">{{ viajechatStatus.configured ? "Conectado" : "Não configurado" }}</span>
              </div>
            </header>
            <p class="iv-card-text">Envia os leads para o funil do ViajeChat, com etiquetas e campos.</p>
            <p v-if="viajechatStatus.api_key_masked" class="iv-card-meta">Chave {{ viajechatStatus.api_key_masked }}</p>
            <footer class="iv-card-foot">
              <router-link to="/admin/integracoes/viajechat" :class="viajechatStatus.configured ? 'iv-soft' : 'iv-btn-primary iv-btn-sm'">{{ viajechatStatus.configured ? "Gerenciar" : "Conectar" }}</router-link>
            </footer>
          </article>
          <article v-if="hasWhatsAppPlanAccess" class="iv-card">
            <header class="iv-card-head">
              <span class="iv-logo tone-success">
                <MessageCircleIcon aria-hidden="true" />
              </span>
              <div class="min-w-0">
                <h3>WhatsApp</h3>
                <span class="iv-pill" :class="integrationStatus.whatsapp ? 'is-on' : 'is-off'">{{ integrationStatus.whatsapp ? "Conectado" : "Não conectado" }}</span>
              </div>
            </header>
            <p class="iv-card-text">Número da agência usado no atendimento e nas mensagens automáticas.</p>
            <footer class="iv-card-foot">
              <router-link to="/admin/integracoes/atendimento" :class="integrationStatus.whatsapp ? 'iv-soft' : 'iv-btn-primary iv-btn-sm'">{{ integrationStatus.whatsapp ? "Gerenciar" : "Conectar" }}</router-link>
            </footer>
          </article>
        </div>
      </section>
    </template>

    <!-- Viaje On -->
    <div v-else-if="isViajeonRoute" class="iv-split">
      <section class="iv-panel">
        <header class="iv-panel-top">
          <span class="iv-logo iv-logo-vo">VO</span>
          <div class="min-w-0 flex-1">
            <h2>Viaje On</h2>
            <p>Mostra os pacotes ativos do Viaje On direto nas suas páginas.</p>
          </div>
          <span class="iv-pill" :class="viajeonStatus.connected ? 'is-on' : 'is-off'">{{ viajeonStatus.connected ? "Conectado" : viajeonStatus.configured ? "Com problema" : "Não configurado" }}</span>
        </header>

        <div v-if="viajeonStatus.configured" class="iv-band" :class="viajeonStatus.connected ? 'is-ok' : 'is-bad'">
          <span class="iv-band-icon" aria-hidden="true">
            <CheckIcon v-if="viajeonStatus.connected" aria-hidden="true" />
            <CircleAlertIcon v-else aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <p class="iv-band-title">{{ viajeonStatus.connected ? "Conexão funcionando" : "Conexão com problema" }}</p>
            <p class="iv-band-text">{{ viajeonStatus.connected ? "As páginas já mostram os pacotes ativos do Viaje On." : (viajeonStatus.last_error || "Teste a conexão ou reconecte com um token novo.") }}</p>
          </div>
          <button type="button" class="iv-band-btn" :disabled="viajeonTesting" @click="testViajeon">
            <RotateCwIcon aria-hidden="true" />
            {{ viajeonTesting ? "Testando..." : "Testar conexão" }}
          </button>
        </div>

        <div v-if="!viajeonStatus.configured" class="iv-line">
          <div class="iv-line-label">
            <p>Conectar</p>
            <span>Cole o token e o secret gerados no painel do Viaje On.</span>
          </div>
          <div class="iv-line-field">
            <button type="button" class="iv-btn-primary iv-btn-sm" :disabled="isReadOnly" @click="openViajeonModal">Conectar Viaje On</button>
          </div>
        </div>

        <template v-else>
          <div class="iv-line">
            <div class="iv-line-label">
              <p>Token de acesso</p>
              <span>Gerado no Viaje On. Reconecte se ele mudar.</span>
            </div>
            <div class="iv-line-field">
              <code class="iv-input iv-input-static">{{ viajeonStatus.token_masked || "configurado" }}</code>
              <button type="button" class="iv-ghost" :disabled="isReadOnly" @click="openViajeonModal">Reconectar</button>
            </div>
          </div>
          <div class="iv-line">
            <div class="iv-line-label">
              <p>E-mail para entrar no Viaje On</p>
              <span>Usado para abrir o painel do Viaje On. Pode ser diferente do e-mail desta conta.</span>
            </div>
            <div class="iv-line-field">
              <input
                v-model="viajeonEmail"
                type="email"
                autocomplete="email"
                placeholder="usuario@empresa.com"
                class="iv-input"
                :disabled="isReadOnly || viajeonEmailSaving"
                @keyup.enter="saveViajeonEmail"
              />
              <button type="button" class="iv-btn-primary iv-btn-sm" :disabled="isReadOnly || viajeonEmailSaving || !viajeonEmail.trim()" @click="saveViajeonEmail">
                {{ viajeonEmailSaving ? "Salvando..." : "Salvar" }}
              </button>
            </div>
          </div>
          <div class="iv-line">
            <div class="iv-line-label">
              <p>Desconectar</p>
              <span>As páginas param de mostrar os pacotes do Viaje On.</span>
            </div>
            <div class="iv-line-field">
              <button type="button" class="iv-ghost danger" :disabled="isReadOnly || viajeonSaving" @click="disconnectViajeon">Desconectar</button>
            </div>
          </div>
        </template>
      </section>

      <aside class="iv-info">
        <span class="iv-info-icon is-success" aria-hidden="true">
          <InfoIcon aria-hidden="true" />
        </span>
        <div>
          <p class="iv-info-title">Onde os pacotes aparecem</p>
          <p class="iv-info-text">No editor de página, adicione a seção de checkout do Viaje On. Ela mostra os pacotes ativos e leva o cliente para o checkout do Viaje On.</p>
        </div>
      </aside>
    </div>

    <!-- ViajeChat -->
    <div v-else-if="isViajechatRoute" class="iv-split">
      <section class="iv-panel">
        <header class="iv-panel-top">
          <span class="iv-logo tone-violet">
            <MessageSquareIcon aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <h2>ViajeChat</h2>
            <p>Envia os leads dos formulários para o funil do ViajeChat.</p>
          </div>
          <span class="iv-pill" :class="viajechatStatus.configured ? 'is-on' : 'is-off'">{{ viajechatStatus.configured ? "Conectado" : "Não configurado" }}</span>
        </header>

        <form class="iv-line" @submit.prevent="connectViajechat">
          <div class="iv-line-label">
            <p>Chave da API</p>
            <span>{{ viajechatStatus.configured ? `Chave atual: ${viajechatStatus.api_key_masked || "configurada"}. Cole outra para trocar.` : "Gerada nas configurações do ViajeChat." }}</span>
          </div>
          <div class="iv-line-field">
            <input v-model="viajechatApiKey" type="password" autocomplete="new-password" class="iv-input" placeholder="Cole a chave aqui" :disabled="viajechatSaving || isReadOnly" />
            <button type="submit" class="iv-btn-primary iv-btn-sm" :disabled="viajechatSaving || isReadOnly || viajechatApiKey.trim().length < 8">
              {{ viajechatSaving ? "Conectando..." : viajechatStatus.configured ? "Trocar chave" : "Conectar" }}
            </button>
          </div>
        </form>

        <div class="iv-line">
          <div class="iv-line-label">
            <p>Depois de conectar</p>
            <span>Cada formulário escolhe o funil, a coluna, a etiqueta e os campos que vão para o ViajeChat.</span>
          </div>
          <div class="iv-line-field">
            <p class="iv-note">Configure isso em Captação de leads › Formulários, ao editar o formulário.</p>
          </div>
        </div>

        <div v-if="viajechatStatus.configured" class="iv-kanbans">
          <div class="iv-kanbans-head">
            <div>
              <p class="iv-line-title">Funis encontrados</p>
              <span class="iv-line-sub">Funis e colunas da sua conta no ViajeChat.</span>
            </div>
            <button type="button" class="iv-ghost" :disabled="viajechatLoading" @click="fetchViajechatKanbans">{{ viajechatLoading ? "Atualizando..." : "Atualizar" }}</button>
          </div>
          <div v-if="viajechatLoading && !viajechatKanbans.length" class="iv-empty">Carregando funis...</div>
          <div v-else-if="!viajechatKanbans.length" class="iv-empty">Nenhum funil encontrado.</div>
          <article v-for="kanban in viajechatKanbans" :key="kanban.id || kanban.name" class="iv-kanban">
            <button type="button" class="iv-kanban-head" :aria-expanded="!isKanbanCollapsed(kanban)" @click="toggleKanbanColumns(kanban)">
              <span><b>{{ kanban.name }}</b><small>{{ kanban.columns.length }} {{ kanban.columns.length === 1 ? "coluna" : "colunas" }}</small></span>
              <ChevronUpIcon :class="{ collapsed: isKanbanCollapsed(kanban) }" aria-hidden="true" />
            </button>
            <div v-if="!isKanbanCollapsed(kanban)" class="iv-columns">
              <span v-for="column in kanban.columns" :key="column.id || column.name">{{ column.name }}</span>
              <p v-if="!kanban.columns.length">Nenhuma coluna retornada.</p>
            </div>
          </article>
        </div>

        <div v-if="viajechatStatus.configured" class="iv-line">
          <div class="iv-line-label">
            <p>Desconectar</p>
            <span>Os leads param de ir para o ViajeChat.</span>
          </div>
          <div class="iv-line-field">
            <button type="button" class="iv-ghost danger" :disabled="viajechatSaving || isReadOnly" @click="disconnectViajechat">Desconectar</button>
          </div>
        </div>
      </section>

      <aside class="iv-info">
        <span class="iv-info-icon is-violet" aria-hidden="true">
          <InfoIcon aria-hidden="true" />
        </span>
        <div>
          <p class="iv-info-title">O que é enviado</p>
          <p class="iv-info-text">Nome, WhatsApp e os campos do formulário que você escolher, além da página de origem. A chave fica guardada de forma criptografada.</p>
        </div>
      </aside>
    </div>

    <!-- Rastreamento -->
    <div v-else class="iv-split">
      <section class="iv-panel">
        <div class="iv-panel-head">
          <div class="min-w-0">
            <p class="iv-eyebrow">Rastreamento</p>
            <h2>Códigos cadastrados</h2>
            <p>Cadastre aqui e escolha em cada página quais códigos ela usa.</p>
          </div>
          <button type="button" class="iv-btn-primary" :disabled="isReadOnly" @click="prepareNewIntegration">
            <PlusIcon aria-hidden="true" />
            Novo código
          </button>
        </div>

        <div v-if="!pixels.length" class="iv-empty">{{ viewCopy.list.empty }}</div>

        <ul v-else class="iv-list">
          <li v-for="pixel in pixels" :key="pixel.id" class="iv-row">
            <span class="iv-logo" :class="pixel.type === 'meta' ? 'tone-info' : 'tone-warning'">
              <template v-if="pixel.type === 'meta'">M</template>
              <ChartLineIcon v-else aria-hidden="true" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="iv-row-name">{{ pixel.name }}</p>
              <p class="iv-row-code">
                <span class="iv-tag" :class="pixel.type === 'meta' ? 'tone-info' : 'tone-warning'">{{ pixel.type === "meta" ? "Meta" : "Google" }}</span>
                <code>{{ displayCode(pixel.value) }}</code>
              </p>
            </div>
            <div class="iv-row-actions">
              <button type="button" class="iv-ghost" @click="copyPixelCode(pixel)">
                <CopyIcon aria-hidden="true" />
                Copiar
              </button>
              <button type="button" class="iv-ghost" :disabled="isReadOnly" @click="editPixel(pixel)">
                <PencilIcon aria-hidden="true" />
                {{ viewCopy.actions.edit }}
              </button>
              <div class="iv-menu-wrap">
                <button type="button" class="iv-icon-btn" aria-label="Mais ações" title="Mais ações" @click.stop="openPixelMenuId = openPixelMenuId === pixel.id ? null : pixel.id">
                  <EllipsisVerticalIcon aria-hidden="true" />
                </button>
                <div v-if="openPixelMenuId === pixel.id" class="iv-menu" @click="openPixelMenuId = null">
                  <button type="button" class="danger" :disabled="isReadOnly" @click="removePixel(pixel)">{{ viewCopy.actions.remove }}</button>
                </div>
              </div>
            </div>
          </li>
        </ul>
        <button type="button" class="iv-add" :disabled="isReadOnly" @click="prepareNewIntegration">+ Adicionar código</button>
      </section>

      <aside class="iv-info">
        <span class="iv-info-icon" aria-hidden="true">
          <InfoIcon aria-hidden="true" />
        </span>
        <div>
          <p class="iv-info-title">Como usar nas páginas</p>
          <ol class="iv-info-text">
            <li>Cadastre o código do Meta ou do Google aqui.</li>
            <li>Abra a página no editor, aba Rastreamento.</li>
            <li>Escolha o código e os eventos que quer enviar.</li>
          </ol>
        </div>
      </aside>
    </div>

    <Teleport to="body">
      <div v-if="viajeonModalOpen" class="app-modal-overlay fixed inset-0 z-[185] flex items-center justify-center px-4">
        <div class="integration-secret-modal w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-500">Integração</p>
              <h2 class="mt-2 text-2xl font-bold text-slate-900">Conectar Viajeon</h2>
              <p class="mt-1 text-sm text-slate-500">Cole o token e o secret gerados no painel do Viajeon.</p>
            </div>
            <button type="button" class="rounded-xl border border-slate-200 p-2 text-slate-500" @click="closeViajeonModal">
              <XIcon class="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          <div class="mt-5 space-y-4">
            <label class="block space-y-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-500">Token</span>
              <input v-model="viajeonToken" autocomplete="off" placeholder="rvo_..." class="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" />
            </label>
            <label class="block space-y-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-500">Secret</span>
              <input v-model="viajeonSecret" type="password" autocomplete="new-password" placeholder="rvs_..." class="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" />
            </label>
            <p class="rounded-xl border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-slate-600">
              O secret é enviado apenas ao backend e armazenado de forma criptografada.
            </p>
          </div>

          <div class="mt-5 flex justify-end gap-2 border-t border-slate-100 pt-4">
            <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="closeViajeonModal">Cancelar</button>
            <button
              type="button"
              class="rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              :disabled="viajeonSaving || !viajeonToken.trim() || !viajeonSecret.trim()"
              @click="connectViajeon"
            >
              {{ viajeonSaving ? "Conectando..." : "Conectar e testar" }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="modalOpen && isTrackingRoute" class="app-modal-overlay fixed inset-0 z-[180] flex items-center justify-center px-4">
        <div class="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl md:p-5">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ viewCopy.form.eyebrow }}</p>
              <h2 class="mt-2 text-2xl font-bold text-slate-900">
                {{ isEditing ? viewCopy.form.editTitle : viewCopy.form.createTitle }}
              </h2>
            </div>
            <button type="button" class="rounded-full border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50" @click="closeModal">
              <XIcon class="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <label class="space-y-2 md:col-span-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.form.nameLabel }}</span>
              <input
                v-model="nameInput"
                type="text"
                :placeholder="viewCopy.form.namePlaceholder"
                :disabled="!canSubmit"
                class="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 disabled:cursor-not-allowed disabled:bg-slate-100"
              />
            </label>
            <label class="space-y-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.form.platformLabel }}</span>
              <select
                v-model="typeInput"
                :disabled="!canSubmit"
                class="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 disabled:cursor-not-allowed disabled:bg-slate-100"
              >
                <option value="meta">{{ viewCopy.form.platformOptions.meta }}</option>
                <option value="ga">{{ viewCopy.form.platformOptions.ga }}</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.form.codeLabel }}</span>
              <input
                v-model="idInput"
                type="text"
                :placeholder="viewCopy.form.codePlaceholder"
                :disabled="!canSubmit"
                class="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 disabled:cursor-not-allowed disabled:bg-slate-100"
              />
            </label>
          </div>

          <div class="mt-4 flex flex-col-reverse gap-3 border-t border-slate-100 pt-4 md:flex-row md:items-center md:justify-between">
            <p class="text-xs font-semibold text-slate-500">{{ isEditing ? viewCopy.form.editingHint : viewCopy.form.createHint }}</p>
            <div class="flex w-full gap-2 md:w-auto">
              <button
                v-if="isEditing"
                type="button"
                class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="saving"
                @click="cancelEditing"
              >
                {{ viewCopy.actions.cancel }}
              </button>
              <button
                type="button"
                class="w-full rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50 md:w-auto"
                :disabled="!canSubmit || saving"
                @click="savePixel"
              >
                {{ saving ? viewCopy.actions.saving : isEditing ? viewCopy.actions.update : viewCopy.actions.save }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="toastMessage"
        class="app-snackbar-layer z-[10020] rounded-full border px-4 py-2 text-sm font-semibold shadow-lg"
        :class="toastError ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'"
      >
        {{ toastMessage }}
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.integrations-view { color: var(--foreground); }
.integrations-view :deep(.bg-white) { background: var(--card) !important; }
.integrations-view :deep(.bg-slate-50),
.integrations-view :deep(.bg-slate-100) { background: var(--muted) !important; }
.integrations-view :deep(.border-slate-200),
.integrations-view :deep(.border-slate-300) { border-color: var(--border) !important; }
.integrations-view :deep(.text-slate-900),
.integrations-view :deep(.text-slate-800),
.integrations-view :deep(.text-slate-700) { color: var(--foreground) !important; }
.integrations-view :deep(.text-slate-600),
.integrations-view :deep(.text-slate-500) { color: var(--muted-foreground) !important; }
.integrations-view :deep(input),
.integrations-view :deep(select),
.integrations-view :deep(textarea) {
  border-color: var(--input) !important;
  background: var(--background) !important;
  color: var(--foreground) !important;
}
.integration-secret-modal {
  background: var(--card);
  border-color: var(--border);
  color: var(--foreground);
}
.integration-secret-modal input {
  border-color: var(--input);
  background: var(--background);
  color: var(--foreground);
}
.integration-secret-modal .text-slate-900,
.integration-secret-modal .text-slate-700 { color: var(--foreground) !important; }
.integration-secret-modal .text-slate-600,
.integration-secret-modal .text-slate-500 { color: var(--muted-foreground) !important; }
.external-integrations{max-width:1100px}.external-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.external-card{display:flex;min-height:220px;cursor:pointer;flex-direction:column;border:1px solid var(--border);border-radius:14px;background:var(--card);padding:16px;box-shadow:0 2px 4px rgba(15,23,42,.06);transition:.2s}.external-card:hover{transform:translateY(-2px);border-color:#86efac;box-shadow:0 10px 24px rgba(15,23,42,.1)}.external-card-top{display:flex;align-items:center;justify-content:space-between}.external-icon{display:grid;width:38px;height:38px;place-items:center;border-radius:12px;background:#e2f8ef;color:#0fbd83;font-weight:900}.external-icon.chat{font-size:25px}.external-badge{border-radius:7px;background:#f1f5f9;padding:5px 11px;font-size:11px;font-weight:700}.external-card h2{margin-top:16px;font-size:16px;font-weight:800}.external-card p{margin-top:3px;flex:1;color:var(--muted-foreground);font-size:13px;line-height:1.4}.external-card>button{margin-top:14px;width:100%;border:1px solid var(--border);border-radius:8px;background:var(--background);padding:8px;font-size:13px;font-weight:700;box-shadow:0 1px 3px rgba(15,23,42,.08)}.drawer-backdrop{position:fixed;inset:0;z-index:190;background:rgba(15,23,42,.42);backdrop-filter:blur(2px)}.external-drawer{position:fixed;z-index:195;right:0;top:0;height:100vh;width:min(620px,94vw);overflow-y:auto;background:var(--card);padding:22px;box-shadow:-20px 0 50px rgba(15,23,42,.2);animation:drawer-in .22s ease-out}.drawer-header{display:flex;align-items:flex-start;justify-content:space-between;border-bottom:1px solid var(--border);padding-bottom:16px;margin-bottom:22px}.drawer-header span{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.16em;color:#10b981}.drawer-header h2{margin-top:3px;font-size:24px;font-weight:800}.drawer-header button{display:grid;width:36px;height:36px;place-items:center;border:1px solid var(--border);border-radius:10px;font-size:24px}.coming-soon{display:flex;min-height:60vh;align-items:center;justify-content:center;flex-direction:column;text-align:center}.coming-soon>div{display:grid;width:64px;height:64px;place-items:center;border-radius:20px;background:#e2f8ef;color:#10b981;font-size:36px}.coming-soon h3{margin-top:18px;font-size:24px;font-weight:800}.coming-soon p{margin-top:6px;color:var(--muted-foreground)}@keyframes drawer-in{from{transform:translateX(100%)}to{transform:translateX(0)}}@media(max-width:680px){.external-grid{grid-template-columns:1fr}}
.drawer-backdrop{z-index:9998}.external-drawer{z-index:9999;top:0;bottom:0;height:100dvh;max-height:100dvh}.viajechat-panel{display:grid;gap:18px}.integration-status-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;border:1px solid var(--border);border-radius:14px;padding:14px}.integration-status-row strong{font-size:14px}.integration-status-row p{margin-top:3px;color:var(--muted-foreground);font-size:12px}.integration-status-row>span{border-radius:999px;background:#f1f5f9;padding:5px 9px;color:#64748b;font-size:10px;font-weight:800;text-transform:uppercase}.integration-status-row>span.connected{background:#dcfce7;color:#15803d}.api-key-form{display:grid;grid-template-columns:1fr auto;align-items:end;gap:10px}.api-key-form label{display:grid;gap:6px;font-size:11px;font-weight:800;text-transform:uppercase;color:var(--muted-foreground)}.api-key-form input{border:1px solid var(--input);border-radius:10px;background:var(--background);padding:10px 12px;color:var(--foreground);font-size:13px;text-transform:none}.api-key-form button,.kanban-head button{border-radius:10px;background:#16c784;padding:10px 14px;color:#052e1c;font-size:12px;font-weight:800}.api-key-form button:disabled,.kanban-head button:disabled{opacity:.5}.security-note{border-radius:10px;background:#f0fdf4;padding:10px 12px;color:#166534;font-size:11px}.kanban-section{display:grid;gap:12px;border-top:1px solid var(--border);padding-top:18px}.kanban-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.kanban-head h3{font-size:17px;font-weight:800}.kanban-head p{color:var(--muted-foreground);font-size:11px}.kanban-card{border:1px solid var(--border);border-radius:14px;background:var(--background);padding:14px}.kanban-card h4{font-size:14px;font-weight:800}.kanban-card>p,.kanban-empty{color:var(--muted-foreground);font-size:12px}.kanban-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.kanban-card-head small{display:block;margin-top:2px;color:var(--muted-foreground);font-size:10px}.kanban-card-head button{display:inline-flex;min-height:30px;align-items:center;justify-content:center;gap:6px;border:1px solid var(--border);border-radius:8px;padding:6px 9px;color:var(--muted-foreground);font-size:10px;font-weight:800;line-height:1}.kanban-card-head button:hover{background:var(--muted)}.kanban-card-head button svg{display:block;width:13px;height:13px;flex:0 0 13px;transition:transform .18s ease}.kanban-card-head button svg.collapsed{transform:rotate(180deg)}.column-list{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}.column-list span{border:1px solid var(--border);border-radius:999px;background:var(--muted);padding:5px 9px;font-size:11px;font-weight:700}.kanban-empty{border:1px dashed var(--border);border-radius:12px;padding:22px;text-align:center}.disconnect-chat{justify-self:start;border:1px solid #fecdd3;border-radius:10px;padding:8px 12px;color:#e11d48;font-size:12px;font-weight:700}@media(max-width:520px){.api-key-form{grid-template-columns:1fr}}

/* Redesign: integrações */
.iv-btn-primary { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 40px; padding: 0 18px; border-radius: 999px; background: var(--primary); font-size: 13.5px; font-weight: 600; color: var(--primary-foreground); }
.iv-btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 88%, black); }
.iv-btn-primary:disabled { cursor: not-allowed; opacity: 0.55; }
.iv-btn-primary svg { width: 16px; height: 16px; }
.iv-soft { display: inline-flex; align-items: center; height: 36px; padding: 0 16px; border-radius: 999px; background: var(--accent); font-size: 13px; font-weight: 600; color: var(--accent-foreground); }
.iv-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.iv-card { display: flex; flex-direction: column; gap: 10px; border-radius: 20px; background: var(--card); padding: 18px; box-shadow: var(--shadow-card); }
.iv-card-head { display: flex; align-items: center; gap: 12px; }
.iv-card-head h2 { font-size: 16px; font-weight: 600; color: var(--foreground); }
.iv-card-text { font-size: 13px; line-height: 1.5; color: var(--muted-foreground); }
.iv-card-meta { font-size: 12.5px; color: var(--foreground); }
.iv-card-foot { display: flex; justify-content: flex-end; margin-top: auto; border-top: 1px solid var(--border); padding-top: 12px; }
.iv-card-foot .iv-btn-primary { height: 36px; font-size: 13px; }
.iv-logo { display: grid; place-items: center; width: 44px; height: 44px; flex-shrink: 0; border-radius: 14px; font-size: 16px; font-weight: 700; }
.iv-logo svg { width: 20px; height: 20px; }
.iv-logo-vo { background: #0b1f17; color: #34d399; }
.iv-pill { display: inline-block; margin-top: 2px; border-radius: 999px; padding: 1px 8px; font-size: 11.5px; font-weight: 600; }
.iv-pill.is-on { background: var(--status-success); color: var(--status-success-foreground); }
.iv-pill.is-off { background: var(--muted); color: var(--muted-foreground); }
.tone-info { background: var(--status-info); color: var(--status-info-foreground); }
.tone-warning { background: var(--status-warning); color: var(--status-warning-foreground); }
.tone-violet { background: var(--status-violet); color: var(--status-violet-foreground); }
.iv-split { display: grid; grid-template-columns: minmax(0, 1fr) 360px; align-items: start; gap: 16px; }
.iv-panel { border-radius: 20px; background: var(--card); padding: 20px; box-shadow: var(--shadow-card); }
.iv-panel-head { border-bottom: 1px solid var(--border); padding-bottom: 12px; }
.iv-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted-foreground); }
.iv-panel-head h2 { margin-top: 2px; font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--foreground); }
.iv-panel-head p:last-child { margin-top: 2px; font-size: 13px; color: var(--muted-foreground); }
.iv-empty { margin-top: 12px; border-radius: 14px; background: var(--muted); padding: 28px 16px; text-align: center; font-size: 13.5px; color: var(--muted-foreground); }
.iv-list { display: flex; flex-direction: column; }
.iv-row { display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--border); padding: 12px 0; }
.iv-row-name { font-size: 14.5px; font-weight: 600; color: var(--foreground); }
.iv-row-code { display: flex; align-items: center; gap: 8px; margin-top: 2px; min-width: 0; font-size: 12.5px; color: var(--muted-foreground); }
.iv-row-code code { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.iv-tag { flex-shrink: 0; border-radius: 999px; padding: 0 8px; font-size: 11px; font-weight: 600; }
.iv-row-actions { display: flex; flex-shrink: 0; gap: 6px; }
.iv-ghost { height: 32px; padding: 0 12px; border-radius: 999px; background: var(--muted); font-size: 12.5px; font-weight: 600; color: var(--foreground); }
.iv-ghost:hover:not(:disabled) { background: var(--accent); color: var(--accent-foreground); }
.iv-ghost.danger { background: var(--status-danger); color: var(--status-danger-foreground); }
.iv-ghost:disabled { cursor: not-allowed; opacity: 0.55; }
.iv-add { display: block; width: 100%; margin-top: 12px; border: 1px dashed var(--border); border-radius: 14px; padding: 10px; font-size: 13px; font-weight: 600; color: var(--primary); }
.iv-add:hover:not(:disabled) { background: var(--accent); }
.iv-add:disabled { cursor: not-allowed; opacity: 0.55; }
.iv-info { display: flex; gap: 12px; border-radius: 20px; background: var(--card); padding: 18px; box-shadow: var(--shadow-card); }
.iv-info-icon { display: grid; place-items: center; width: 36px; height: 36px; flex-shrink: 0; border-radius: 999px; background: var(--status-info); color: var(--status-info-foreground); }
.iv-info-icon svg { width: 18px; height: 18px; }
.iv-info-title { font-size: 14px; font-weight: 600; color: var(--foreground); }
.iv-info-text { margin-top: 4px; padding-left: 16px; list-style: decimal; font-size: 12.5px; line-height: 1.6; color: var(--muted-foreground); }
@media (max-width: 1024px) { .iv-split { grid-template-columns: 1fr; } }
@media (max-width: 640px) {
  .iv-row { flex-wrap: wrap; }
  .iv-row-actions { width: 100%; justify-content: flex-end; }
}

/* Redesign: gavetas do Viaje On e do ViajeChat */
.external-drawer { color: var(--foreground); border-radius: 24px 0 0 24px; padding: 24px !important; }
.drawer-header span { color: var(--primary) !important; letter-spacing: 0.06em !important; }
.drawer-header h2 { font-family: var(--font-display); font-weight: 600 !important; color: var(--foreground); }
.drawer-header button { border: 0 !important; border-radius: 999px !important; background: var(--muted); font-size: 20px !important; color: var(--muted-foreground); }
.external-drawer > .md\:flex-row { flex-direction: column !important; align-items: stretch !important; }
.external-drawer button.rounded-xl, .iv-panel button.rounded-xl { border-radius: 999px !important; }
.integration-status-row { border: 0 !important; border-radius: 16px !important; background: var(--muted); }
.integration-status-row strong { color: var(--foreground); }
.integration-status-row > span { background: var(--card) !important; color: var(--muted-foreground) !important; text-transform: none !important; font-size: 11.5px !important; }
.integration-status-row > span.connected { background: var(--status-success) !important; color: var(--status-success-foreground) !important; }
.api-key-form button, .kanban-head button { border-radius: 999px !important; background: var(--primary) !important; color: var(--primary-foreground) !important; }
.security-note { background: var(--status-success) !important; color: var(--status-success-foreground) !important; border-radius: 12px !important; }
.kanban-card { border: 0 !important; border-radius: 16px !important; background: var(--muted) !important; }
.disconnect-chat { border: 0 !important; border-radius: 999px !important; background: var(--status-danger); color: var(--status-danger-foreground) !important; }
.external-drawer .text-slate-900, .iv-panel .text-slate-900, .external-drawer .text-slate-700, .iv-panel .text-slate-700 { color: var(--foreground) !important; }
.external-drawer .text-slate-500, .iv-panel .text-slate-500 { color: var(--muted-foreground) !important; }
.external-drawer input, .iv-panel input { border-color: var(--input) !important; background: var(--background) !important; color: var(--foreground) !important; }
.external-drawer .border-slate-200, .iv-panel .border-slate-200 { border-color: var(--border) !important; }
.external-drawer button.border-slate-200:hover, .iv-panel button.border-slate-200:hover { background: var(--muted) !important; }

/* Redesign v2: visão geral, Viaje On e ViajeChat como abas */
.iv-group { display: flex; flex-direction: column; gap: 12px; }
.iv-group-title { font-size: 15px; font-weight: 600; color: var(--foreground); }
.iv-group-title span { margin-left: 8px; font-size: 13px; font-weight: 400; color: var(--muted-foreground); }
.iv-card-head h3 { font-size: 16px; font-weight: 600; color: var(--foreground); }
.iv-btn-sm { height: 36px !important; padding: 0 16px !important; font-size: 13px !important; }
.tone-success { background: var(--status-success); color: var(--status-success-foreground); }
.iv-panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.iv-panel-top { display: flex; align-items: flex-start; gap: 12px; border-bottom: 1px solid var(--border); padding-bottom: 14px; }
.iv-panel-top h2 { font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--foreground); }
.iv-panel-top p { margin-top: 2px; font-size: 13px; color: var(--muted-foreground); }
.iv-panel-top .iv-pill { flex-shrink: 0; margin-top: 4px; }
.iv-band { display: flex; align-items: center; gap: 12px; margin-top: 14px; border-radius: 16px; padding: 12px 14px; }
.iv-band.is-ok { background: var(--status-success); color: var(--status-success-foreground); }
.iv-band.is-bad { background: var(--status-danger); color: var(--status-danger-foreground); }
.iv-band-icon { display: grid; place-items: center; width: 36px; height: 36px; flex-shrink: 0; border-radius: 999px; background: color-mix(in srgb, currentColor 14%, transparent); }
.iv-band-icon svg { width: 18px; height: 18px; }
.iv-band-title { font-size: 14px; font-weight: 600; }
.iv-band-text { margin-top: 1px; font-size: 12.5px; opacity: 0.9; }
.iv-band-btn { display: inline-flex; flex-shrink: 0; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 999px; background: var(--card); font-size: 12.5px; font-weight: 600; color: var(--foreground); }
.iv-band-btn svg { width: 14px; height: 14px; }
.iv-band-btn:disabled { opacity: 0.6; }
.iv-line { display: grid; grid-template-columns: minmax(0, 200px) minmax(0, 1fr); align-items: center; gap: 16px; border-bottom: 1px solid var(--border); padding: 14px 0; }
.iv-line:last-child { border-bottom: 0; padding-bottom: 0; }
.iv-line-label p, .iv-line-title { font-size: 14px; font-weight: 600; color: var(--foreground); }
.iv-line-label span, .iv-line-sub { display: block; margin-top: 2px; font-size: 12.5px; line-height: 1.45; color: var(--muted-foreground); }
.iv-line-field { display: flex; align-items: center; gap: 8px; min-width: 0; }
.iv-input { flex: 1; min-width: 0; height: 40px; border: 0; border-radius: 999px; background: var(--muted); padding: 0 16px; font-size: 13.5px; color: var(--foreground); outline: none; }
.iv-input:focus { box-shadow: 0 0 0 2px var(--ring); }
.iv-input-static { display: flex; align-items: center; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; font-size: 13px; }
.iv-note { border-radius: 14px; background: var(--status-info); padding: 10px 14px; font-size: 12.5px; color: var(--status-info-foreground); }
.iv-kanbans { display: flex; flex-direction: column; gap: 8px; border-bottom: 1px solid var(--border); padding: 14px 0; }
.iv-kanbans-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.iv-kanban { border-radius: 14px; background: var(--muted); }
.iv-kanban-head { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 14px; text-align: left; }
.iv-kanban-head b { display: block; font-size: 13.5px; color: var(--foreground); }
.iv-kanban-head small { font-size: 12px; color: var(--muted-foreground); }
.iv-kanban-head svg { width: 14px; height: 14px; flex-shrink: 0; color: var(--muted-foreground); transition: transform 0.18s; }
.iv-kanban-head svg.collapsed { transform: rotate(180deg); }
.iv-columns { display: flex; flex-wrap: wrap; gap: 6px; padding: 0 14px 12px; }
.iv-columns span { border-radius: 999px; background: var(--card); padding: 3px 10px; font-size: 12px; color: var(--foreground); }
.iv-columns p { font-size: 12px; color: var(--muted-foreground); }
.iv-ghost { display: inline-flex; flex-shrink: 0; align-items: center; gap: 6px; }
.iv-ghost svg { width: 14px; height: 14px; }
.iv-icon-btn { display: grid; place-items: center; width: 32px; height: 32px; border-radius: 999px; background: var(--muted); color: var(--muted-foreground); }
.iv-icon-btn svg { width: 16px; height: 16px; }
.iv-menu-wrap { position: relative; }
.iv-menu { position: absolute; top: calc(100% + 6px); right: 0; z-index: 30; display: flex; min-width: 160px; flex-direction: column; border-radius: 14px; background: var(--popover); padding: 6px; box-shadow: var(--shadow-elegant); }
.iv-menu button { border-radius: 10px; padding: 8px 10px; text-align: left; font-size: 13px; color: var(--popover-foreground); }
.iv-menu button:hover { background: var(--muted); }
.iv-menu button.danger { color: var(--status-danger-foreground); }
.iv-info-icon.is-success { background: var(--status-success); color: var(--status-success-foreground); }
.iv-info-icon.is-violet { background: var(--status-violet); color: var(--status-violet-foreground); }
@media (max-width: 640px) {
  .iv-line { grid-template-columns: 1fr; gap: 8px; }
  .iv-band { flex-wrap: wrap; }
  .iv-panel-head { flex-direction: column; }
}
</style>

<script setup lang="ts">
import {
  ChartLineIcon,
  CheckIcon,
  ChevronUpIcon,
  CircleAlertIcon,
  CopyIcon,
  EllipsisVerticalIcon,
  InfoIcon,
  MessageCircleIcon,
  MessageSquareIcon,
  PencilIcon,
  PlusIcon,
  RotateCwIcon,
  XIcon
} from "lucide-vue-next";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../../store/useAuthStore";
import IntegrationsHeader from "../../components/admin/integrations/IntegrationsHeader.vue";
import { integrationStatus } from "../../composables/useIntegrationStatus";
import api from "../../services/api";
import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";

type PixelType = "meta" | "ga";

interface PixelEntry {
  id?: number | string;
  name: string;
  type: PixelType;
  value: string;
}

interface ViajeonStatus {
  configured: boolean;
  connected: boolean;
  status: string;
  token_masked?: string;
  last_error?: string | null;
  sso_email?: string;
}
interface ViajechatStatus { configured: boolean; connected: boolean; status: string; api_key_masked?: string; last_error?: string | null }
interface ViajechatKanban { id: string; name: string; columns: Array<{ id: string; name: string }> }

const auth = useAuthStore();
const route = useRoute();
const isViajeonRoute = computed(() => route.name === "integrations-viajeon");
const isExternalRoute = computed(() => false);
const isOverviewRoute = computed(() => route.name === "integrations-overview");
const isViajechatRoute = computed(() => route.name === "integrations-viajechat");
const isTrackingRoute = computed(() => !isOverviewRoute.value && !isViajeonRoute.value && !isViajechatRoute.value);
const openPixelMenuId = ref<number | string | null>(null);
const closePixelMenu = (event: MouseEvent) => {
  if (!(event.target as HTMLElement | null)?.closest(".iv-menu-wrap")) openPixelMenuId.value = null;
};
onMounted(() => document.addEventListener("click", closePixelMenu));
onBeforeUnmount(() => document.removeEventListener("click", closePixelMenu));
// WhatsApp na visão geral: mesma regra de plano do menu lateral.
const hasWhatsAppPlanAccess = computed(() => {
  const plan = (value: unknown) => String(value || "").trim().toLowerCase();
  const allowed = new Set(["escala", "infinity", "scale", "teste", "test"]);
  return allowed.has(plan((auth.user as any)?.trial_plan)) || allowed.has(plan(auth.user?.plan));
});
const trackingKinds = computed(() => {
  const meta = pixels.value.filter((pixel: any) => pixel.type === "meta");
  const ga = pixels.value.filter((pixel: any) => pixel.type !== "meta");
  return [
    { type: "meta", label: "Meta Pixel", tone: "tone-info", count: meta.length, first: meta[0]?.name || "", description: "Conta visitas e cliques das páginas para os anúncios do Facebook e Instagram." },
    { type: "ga", label: "Google Analytics", tone: "tone-warning", count: ga.length, first: ga[0]?.name || "", description: "Envia as visitas das páginas para o Google Analytics da agência." }
  ];
});
const adminLanguage = getAdminLanguage();
const t = createAdminLocalizer(adminLanguage);

const viewCopy = {
  header: {
    get title() {
      return isExternalRoute.value ? "Integrações externas" : isViajeonRoute.value ? "Viajeon" : t({ pt: "Rastreamento", es: "Rastreo" });
    },
    get description() {
      return isExternalRoute.value
        ? "Aplicativos, módulos e serviços externos disponíveis para sua agência."
        : isViajeonRoute.value
        ? t({
          pt: "Conecte o Viajeon para exibir pacotes ativos nas suas páginas.",
          es: "Conecta Viajeon para mostrar paquetes activos en tus páginas."
        })
        : t({
          pt: "Cadastre códigos Meta ou Google para utilizar nas suas páginas.",
          es: "Registra códigos Meta o Google para usarlos en tus páginas."
        });
    }
  },
  form: {
    eyebrow: t({ pt: "Integração", es: "Integración" }),
    createTitle: t({ pt: "Nova integração", es: "Nueva integración" }),
    editTitle: t({ pt: "Editar integração", es: "Editar integración" }),
    nameLabel: t({ pt: "Nome da integração", es: "Nombre de la integración" }),
    namePlaceholder: t({ pt: "Ex.: Roteiro São Paulo", es: "Ej.: Itinerario São Paulo" }),
    platformLabel: t({ pt: "Plataforma", es: "Plataforma" }),
    codeLabel: t({ pt: "Código de acompanhamento", es: "Código de seguimiento" }),
    codePlaceholder: t({ pt: "Ex.: 1234567890 ou G-XXXXXXX", es: "Ej.: 1234567890 o G-XXXXXXX" }),
    platformOptions: {
      meta: t({ pt: "Meta", es: "Meta" }),
      ga: t({ pt: "Google", es: "Google" })
    },
    createHint: t({ pt: "Cadastre o código para usar nas páginas.", es: "Registra el código para usarlo en las páginas." }),
    editingHint: t({ pt: "Editando integração selecionada.", es: "Editando integración seleccionada." })
  },
  summary: {
    label: t({ pt: "Integrações cadastradas", es: "Integraciones registradas" })
  },
  list: {
    title: t({ pt: "Integrações cadastradas", es: "Integraciones registradas" }),
    typeMeta: t({ pt: "Meta", es: "Meta" }),
    typeGa: t({ pt: "Google", es: "Google" }),
    codePrefix: t({ pt: "Código:", es: "Código:" }),
    empty: t({ pt: "Nenhuma integração cadastrada.", es: "No hay integraciones registradas." })
  },
  actions: {
    new: t({ pt: "Nova integração", es: "Nueva integración" }),
    save: t({ pt: "Salvar integração", es: "Guardar integración" }),
    update: t({ pt: "Salvar alterações", es: "Guardar cambios" }),
    saving: t({ pt: "Salvando...", es: "Guardando..." }),
    cancel: t({ pt: "Cancelar", es: "Cancelar" }),
    edit: t({ pt: "Editar", es: "Editar" }),
    remove: t({ pt: "Remover", es: "Eliminar" })
  },
  messages: {
    loadError: t({ pt: "Não foi possível carregar as integrações.", es: "No fue posible cargar las integraciones." }),
    missingFields: t({ pt: "Preencha nome e código da integração.", es: "Completa el nombre y el código de la integración." }),
    saveSuccess: t({ pt: "Integração salva com sucesso.", es: "Integración guardada con éxito." }),
    saveError: t({ pt: "Não foi possível salvar a integração.", es: "No fue posible guardar la integración." }),
    removeSuccess: t({ pt: "Integração removida.", es: "Integración eliminada." }),
    removeError: t({ pt: "Não foi possível remover a integração.", es: "No fue posible eliminar la integración." }),
    confirmRemove: t({ pt: "Remover esta integração?", es: "¿Eliminar esta integración?" }),
    readOnly: t({ pt: "Seu perfil permite apenas visualização.", es: "Tu perfil permite solo visualización." })
  }
};

const nameInput = ref("");
const typeInput = ref<PixelType>("meta");
const idInput = ref("");
const pixels = ref<PixelEntry[]>([]);
const saving = ref(false);
const isBootstrappingIntegrations = ref(true);
const editingId = ref<string | number | null>(null);
const modalOpen = ref(false);
const viajeonStatus = ref<ViajeonStatus>({ configured: false, connected: false, status: "disconnected" });
const viajeonModalOpen = ref(false);
const viajeonToken = ref("");
const viajeonSecret = ref("");
const viajeonSaving = ref(false);
const viajeonTesting = ref(false);
const viajeonEmail = ref("");
const viajeonEmailSaving = ref(false);
const viajechatStatus = ref<ViajechatStatus>({ configured: false, connected: false, status: "disconnected" });
const viajechatApiKey = ref("");
const viajechatKanbans = ref<ViajechatKanban[]>([]);
const collapsedViajechatKanbans = ref<Set<string>>(new Set());
const viajechatSaving = ref(false);
const viajechatLoading = ref(false);

const toastMessage = ref("");
const toastError = ref(false);
let toastTimer: ReturnType<typeof setTimeout> | null = null;

const isReadOnly = computed(() => {
  const user = auth.user;
  if (!user) return false;
  if (user.is_owner ?? true) return false;
  return (user.role || "member").toLowerCase() === "viewer";
});

const canSubmit = computed(() => !isReadOnly.value);
const isEditing = computed(() => editingId.value !== null);

const copyPixelCode = async (pixel: { value?: string | null }) => {
  try {
    await navigator.clipboard.writeText(String(pixel.value || ""));
    showToast("Código copiado.");
  } catch {
    showToast("Não foi possível copiar o código.", true);
  }
};
const showToast = (message: string, error = false) => {
  toastMessage.value = message;
  toastError.value = error;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMessage.value = "";
    toastError.value = false;
  }, 2600);
};

const fetchPixels = async () => {
  try {
    const res = await api.get("/pixels/");
    pixels.value = Array.isArray(res.data) ? res.data : [];
  } catch (err) {
    console.error(err);
    showToast(viewCopy.messages.loadError, true);
  }
};

const fetchViajeonStatus = async () => {
  try {
    const res = await api.get("/integrations/viajeon");
    viajeonStatus.value = res.data;
    viajeonEmail.value = res.data?.sso_email || auth.user?.email || "";
  } catch (err) {
    console.error(err);
    viajeonStatus.value = { configured: false, connected: false, status: "disconnected" };
  }
};
const fetchViajechatStatus = async () => { try { viajechatStatus.value = (await api.get("/integrations/viajechat")).data; if (viajechatStatus.value.configured) await fetchViajechatKanbans(); } catch { viajechatStatus.value = { configured:false, connected:false, status:"disconnected" }; } };
const kanbanCollapseKey = (kanban: ViajechatKanban) => String(kanban.id || kanban.name);
const isKanbanCollapsed = (kanban: ViajechatKanban) => collapsedViajechatKanbans.value.has(kanbanCollapseKey(kanban));
const toggleKanbanColumns = (kanban: ViajechatKanban) => { const next = new Set(collapsedViajechatKanbans.value); const key = kanbanCollapseKey(kanban); if (next.has(key)) next.delete(key); else next.add(key); collapsedViajechatKanbans.value = next; };
const setViajechatKanbans = (rows: unknown) => { viajechatKanbans.value = Array.isArray(rows) ? rows : []; collapsedViajechatKanbans.value = new Set(viajechatKanbans.value.map(kanbanCollapseKey)); };
const fetchViajechatKanbans = async () => { if (!viajechatStatus.value.configured) return; viajechatLoading.value=true; try { const res=await api.get("/integrations/viajechat/kanbans"); setViajechatKanbans(res.data?.kanbans); viajechatStatus.value.connected=true; } catch(err:any) { viajechatStatus.value.connected=false; showToast(err?.response?.data?.detail||"Não foi possível carregar os kanbans.",true); } finally { viajechatLoading.value=false; } };
const connectViajechat = async () => { const key=viajechatApiKey.value.trim(); if(!key)return; viajechatSaving.value=true; try { const res=await api.put("/integrations/viajechat",{api_key:key}); viajechatStatus.value=res.data; setViajechatKanbans(res.data?.kanbans); viajechatApiKey.value=""; showToast("ViajeChat conectado com sucesso."); } catch(err:any) { showToast(err?.response?.data?.detail||"Não foi possível conectar o ViajeChat.",true); } finally { viajechatSaving.value=false; } };
const disconnectViajechat = async () => { if(!window.confirm("Desconectar a integração ViajeChat?"))return; viajechatSaving.value=true; try { await api.delete("/integrations/viajechat"); viajechatStatus.value={configured:false,connected:false,status:"disconnected"}; viajechatKanbans.value=[]; showToast("ViajeChat desconectado."); } catch(err:any) { showToast(err?.response?.data?.detail||"Não foi possível desconectar o ViajeChat.",true); } finally { viajechatSaving.value=false; } };

const saveViajeonEmail = async () => {
  const email = viajeonEmail.value.trim();
  if (!email || viajeonEmailSaving.value || isReadOnly.value) return;
  viajeonEmailSaving.value = true;
  try {
    const res = await api.patch("/integrations/viajeon/sso-email", { email });
    viajeonStatus.value = res.data;
    viajeonEmail.value = res.data?.sso_email || email;
    showToast("Email de login do Viajeon salvo.");
  } catch (err: any) {
    showToast(err?.response?.data?.detail || "Não foi possível salvar o email do Viajeon.", true);
  } finally {
    viajeonEmailSaving.value = false;
  }
};

const openViajeonModal = () => {
  if (isReadOnly.value) return;
  viajeonToken.value = "";
  viajeonSecret.value = "";
  viajeonModalOpen.value = true;
};

const closeViajeonModal = () => {
  if (viajeonSaving.value) return;
  viajeonModalOpen.value = false;
  viajeonToken.value = "";
  viajeonSecret.value = "";
};

const connectViajeon = async () => {
  viajeonSaving.value = true;
  try {
    const res = await api.put("/integrations/viajeon", {
      token: viajeonToken.value.trim(),
      secret: viajeonSecret.value.trim()
    });
    viajeonStatus.value = res.data;
    viajeonEmail.value = res.data?.sso_email || auth.user?.email || "";
    viajeonModalOpen.value = false;
    viajeonToken.value = "";
    viajeonSecret.value = "";
    showToast("Viajeon conectado com sucesso.");
  } catch (err: any) {
    console.error(err);
    showToast(err?.response?.data?.detail || "Não foi possível conectar ao Viajeon.", true);
  } finally {
    viajeonSaving.value = false;
  }
};

const testViajeon = async () => {
  viajeonTesting.value = true;
  try {
    await api.post("/integrations/viajeon/test");
    await fetchViajeonStatus();
    showToast("Conexão com o Viajeon validada.");
  } catch (err: any) {
    await fetchViajeonStatus();
    showToast(err?.response?.data?.detail || "A conexão com o Viajeon falhou.", true);
  } finally {
    viajeonTesting.value = false;
  }
};

const disconnectViajeon = async () => {
  if (!window.confirm("Desconectar a integração Viajeon?")) return;
  viajeonSaving.value = true;
  try {
    await api.delete("/integrations/viajeon");
    await fetchViajeonStatus();
    showToast("Viajeon desconectado.");
  } catch (err: any) {
    showToast(err?.response?.data?.detail || "Não foi possível desconectar o Viajeon.", true);
  } finally {
    viajeonSaving.value = false;
  }
};

const resetForm = () => {
  editingId.value = null;
  nameInput.value = "";
  typeInput.value = "meta";
  idInput.value = "";
};

const prepareNewIntegration = () => {
  if (isReadOnly.value) {
    showToast(viewCopy.messages.readOnly, true);
    return;
  }
  resetForm();
  modalOpen.value = true;
};

const editPixel = (pixel: PixelEntry) => {
  if (isReadOnly.value) {
    showToast(viewCopy.messages.readOnly, true);
    return;
  }
  editingId.value = pixel.id || null;
  nameInput.value = pixel.name;
  typeInput.value = pixel.type;
  idInput.value = pixel.value;
  modalOpen.value = true;
};

const cancelEditing = () => {
  resetForm();
  modalOpen.value = false;
};

const closeModal = () => {
  if (saving.value) return;
  resetForm();
  modalOpen.value = false;
};

const savePixel = async () => {
  if (!canSubmit.value) {
    showToast(viewCopy.messages.readOnly, true);
    return;
  }

  const name = nameInput.value.trim();
  const value = idInput.value.trim();
  if (!name || !value) {
    showToast(viewCopy.messages.missingFields, true);
    return;
  }

  saving.value = true;
  try {
    if (editingId.value !== null) {
      await api.put(`/pixels/${editingId.value}`, {
        name,
        type: typeInput.value,
        value
      });
    } else {
      await api.post("/pixels/", {
        name,
        type: typeInput.value,
        value
      });
    }

    await fetchPixels();
    resetForm();
    modalOpen.value = false;
    showToast(viewCopy.messages.saveSuccess);
  } catch (err: any) {
    console.error(err);
    showToast(err?.response?.data?.detail || viewCopy.messages.saveError, true);
  } finally {
    saving.value = false;
  }
};

const removePixel = async (pixel: PixelEntry) => {
  if (!pixel.id) return;
  if (isReadOnly.value) {
    showToast(viewCopy.messages.readOnly, true);
    return;
  }

  const confirmed = window.confirm(viewCopy.messages.confirmRemove);
  if (!confirmed) return;

  try {
    await api.delete(`/pixels/${pixel.id}`);
    if (editingId.value === pixel.id) resetForm();
    await fetchPixels();
    showToast(viewCopy.messages.removeSuccess);
  } catch (err) {
    console.error(err);
    showToast(viewCopy.messages.removeError, true);
  }
};

const displayCode = (raw: string) => {
  const value = String(raw || "").trim();
  return value || "-";
};

// Mantém os pontos das abas em dia quando algo é conectado ou desconectado aqui.
watch(() => pixels.value.length, count => { integrationStatus.pixels = count; });
watch(() => viajeonStatus.value.connected, value => { integrationStatus.viajeon = !!value; });
watch(() => viajechatStatus.value.configured, value => { integrationStatus.viajechat = !!value; });

onMounted(async () => {
  try {
    await Promise.all([fetchPixels(), fetchViajeonStatus(), fetchViajechatStatus()]);
  } finally {
    isBootstrappingIntegrations.value = false;
  }
});
</script>
