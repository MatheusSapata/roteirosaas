<template>
  <div v-if="isBootstrappingIntegrations" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8 md:px-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
  </div>

  <div v-else class="integrations-view w-full space-y-6 px-4 py-6 md:px-8">
    <header class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div>
        <h1 class="text-3xl font-bold text-slate-900">{{ viewCopy.header.title }}</h1>
        <p class="mt-1 text-sm text-slate-600">{{ viewCopy.header.description }}</p>
      </div>

      <button
        v-if="!isViajeonRoute && !isExternalRoute"
        type="button"
        class="inline-flex items-center gap-2 rounded-[10px] bg-[#3DCC5F] px-4 py-[9px] text-[13px] font-semibold text-[#0F1F14] transition hover:bg-[#5BE07A] disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="isReadOnly"
        @click="prepareNewIntegration"
      >
        <span class="text-[15px] leading-none font-bold">+</span>
        {{ viewCopy.actions.new }}
      </button>
    </header>

    <section v-if="isExternalRoute" class="external-integrations">
      <div class="external-grid">
        <article class="external-card" @click="externalDrawer = 'viajeon'">
          <div class="external-card-top"><span class="external-icon">V</span><span class="external-badge">Integração</span></div>
          <h2>ViajeOn</h2><p>Exiba pacotes ativos e conecte sua operação às páginas do Roteiro Online.</p>
          <button type="button">⚙ Configurar</button>
        </article>
        <article class="external-card" @click="externalDrawer = 'viajechat'">
          <div class="external-card-top"><span class="external-icon chat">◌</span><span class="external-badge">Integração</span></div>
          <h2>ViajeChat</h2><p>Atendimento, conversas e automações integradas à sua agência.</p>
          <button type="button">⚙ Visualizar</button>
        </article>
      </div>
    </section>
    <section v-if="!isViajeonRoute && !isExternalRoute" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
      <p class="text-sm font-semibold text-slate-700">
        {{ viewCopy.summary.label }}: <span class="text-slate-900">{{ pixels.length }}</span>
      </p>
    </section>

    <Teleport to="body" :disabled="!isExternalRoute">
    <div v-if="isExternalRoute && externalDrawer" class="drawer-backdrop" @click="externalDrawer = null"></div>
    <aside v-if="isViajeonRoute || (isExternalRoute && externalDrawer === 'viajeon')" :class="isExternalRoute ? 'external-drawer' : 'rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5'">
      <div v-if="isExternalRoute" class="drawer-header"><div><span>Integração externa</span><h2>ViajeOn</h2></div><button type="button" @click="externalDrawer = null">×</button></div>
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex min-w-0 items-start gap-3">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-lg font-extrabold text-emerald-500">V</div>
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="text-lg font-semibold text-slate-900">Viajeon</h2>
              <span
                class="rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide"
                :class="viajeonStatus.connected ? 'bg-emerald-500/15 text-emerald-500' : 'bg-slate-500/10 text-slate-500'"
              >
                {{ viajeonStatus.connected ? "Conectado" : "Desconectado" }}
              </span>
            </div>
            <p class="mt-1 text-sm text-slate-500">Exiba os pacotes ativos do Viajeon diretamente nas páginas públicas.</p>
            <p v-if="viajeonStatus.configured" class="mt-1 text-xs font-semibold text-slate-500">
              Token: {{ viajeonStatus.token_masked || "configurado" }}
            </p>
            <p v-if="viajeonStatus.last_error" class="mt-2 text-xs font-semibold text-rose-500">
              {{ viajeonStatus.last_error }}
            </p>
            <div v-if="viajeonStatus.configured" class="mt-3 flex max-w-xl flex-col gap-2 sm:flex-row sm:items-end">
              <label class="min-w-0 flex-1 space-y-1.5">
                <span class="block text-[11px] font-bold uppercase tracking-wide text-slate-500">Email para login no Viajeon</span>
                <input
                  v-model="viajeonEmail"
                  type="email"
                  autocomplete="email"
                  placeholder="usuario@empresa.com"
                  :disabled="isReadOnly || viajeonEmailSaving"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 disabled:bg-slate-100"
                  @keyup.enter="saveViajeonEmail"
                />
              </label>
              <button
                type="button"
                class="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="isReadOnly || viajeonEmailSaving || !viajeonEmail.trim()"
                @click="saveViajeonEmail"
              >
                {{ viajeonEmailSaving ? "Salvando..." : "Salvar email" }}
              </button>
            </div>
            <p v-if="viajeonStatus.configured" class="mt-1 text-[11px] text-slate-500">
              Este email será usado para abrir o painel. Ele pode ser diferente do email da conta do Roteiro Online.
            </p>
          </div>
        </div>

        <div class="flex flex-wrap gap-2">
          <button
            v-if="viajeonStatus.connected"
            type="button"
            class="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
            :disabled="viajeonTesting"
            @click="testViajeon"
          >
            {{ viajeonTesting ? "Testando..." : "Testar conexão" }}
          </button>
          <button
            type="button"
            class="rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50"
            :disabled="isReadOnly"
            @click="openViajeonModal"
          >
            {{ viajeonStatus.configured ? "Reconectar" : "Conectar" }}
          </button>
          <button
            v-if="viajeonStatus.configured"
            type="button"
            class="rounded-xl border border-rose-500/30 px-3 py-2 text-sm font-semibold text-rose-500 transition hover:bg-rose-500/10 disabled:opacity-50"
            :disabled="isReadOnly || viajeonSaving"
            @click="disconnectViajeon"
          >
            Desconectar
          </button>
        </div>
      </div>
    </aside>

    <aside v-if="isExternalRoute && externalDrawer === 'viajechat'" class="external-drawer">
      <div class="drawer-header"><div><span>Integração externa</span><h2>ViajeChat</h2></div><button type="button" @click="externalDrawer = null">×</button></div>
      <div class="viajechat-panel">
        <div class="integration-status-row"><div><strong>{{ viajechatStatus.connected ? 'ViajeChat conectado' : 'Conecte sua conta' }}</strong><p>{{ viajechatStatus.connected ? `API key ${viajechatStatus.api_key_masked || 'configurada'}` : 'Informe a API key gerada no painel do ViajeChat.' }}</p></div><span :class="viajechatStatus.connected ? 'connected' : ''">{{ viajechatStatus.connected ? 'Conectado' : 'Desconectado' }}</span></div>
        <form class="api-key-form" @submit.prevent="connectViajechat"><label>API key<input v-model="viajechatApiKey" type="password" autocomplete="new-password" placeholder="Cole sua API key" :disabled="viajechatSaving || isReadOnly" /></label><button type="submit" :disabled="viajechatSaving || isReadOnly || viajechatApiKey.trim().length < 8">{{ viajechatSaving ? 'Conectando...' : (viajechatStatus.configured ? 'Atualizar API key' : 'Conectar') }}</button></form>
        <p class="security-note">A chave é enviada diretamente ao backend e armazenada de forma criptografada.</p>
        <div v-if="viajechatStatus.configured" class="kanban-section"><div class="kanban-head"><div><h3>Kanbans</h3><p>Funis e respectivas colunas encontrados na sua conta.</p></div><button type="button" :disabled="viajechatLoading" @click="fetchViajechatKanbans">{{ viajechatLoading ? 'Atualizando...' : 'Atualizar' }}</button></div>
          <div v-if="viajechatLoading && !viajechatKanbans.length" class="kanban-empty">Carregando kanbans...</div><div v-else-if="!viajechatKanbans.length" class="kanban-empty">Nenhum kanban foi encontrado.</div>
          <article v-for="kanban in viajechatKanbans" :key="kanban.id || kanban.name" class="kanban-card">
            <div class="kanban-card-head">
              <div><h4>{{ kanban.name }}</h4><small>{{ kanban.columns.length }} {{ kanban.columns.length === 1 ? 'coluna' : 'colunas' }}</small></div>
              <button type="button" :aria-expanded="!isKanbanCollapsed(kanban)" @click="toggleKanbanColumns(kanban)">
                {{ isKanbanCollapsed(kanban) ? 'Expandir' : 'Colapsar' }}
                <svg :class="{ collapsed: isKanbanCollapsed(kanban) }" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m5 12 5-5 5 5" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </button>
            </div>
            <template v-if="!isKanbanCollapsed(kanban)">
              <div v-if="kanban.columns.length" class="column-list"><span v-for="column in kanban.columns" :key="column.id || column.name">{{ column.name }}</span></div>
              <p v-else>Nenhuma coluna retornada.</p>
            </template>
          </article>
        </div>
        <button v-if="viajechatStatus.configured" type="button" class="disconnect-chat" :disabled="viajechatSaving || isReadOnly" @click="disconnectViajechat">Desconectar ViajeChat</button>
      </div>
    </aside>
    </Teleport>

    <section v-if="!isViajeonRoute && !isExternalRoute" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
      <div class="mb-4 flex items-center justify-between gap-3">
        <h2 class="text-lg font-semibold text-slate-900">{{ viewCopy.list.title }}</h2>
      </div>

      <div v-if="!pixels.length" class="rounded-xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
        {{ viewCopy.list.empty }}
      </div>

      <div v-else class="space-y-3">
        <article
          v-for="pixel in pixels"
          :key="pixel.id"
          class="integration-item flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-4 transition hover:-translate-y-[1px] hover:shadow-md md:flex-row md:items-center md:justify-between"
        >
          <div class="min-w-0 flex-1">
            <span
              class="inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide"
              :class="pixel.type === 'meta' ? 'bg-blue-100 text-blue-700' : 'bg-rose-100 text-rose-700'"
            >
              {{ pixel.type === "meta" ? viewCopy.list.typeMeta : viewCopy.list.typeGa }}
            </span>

            <p class="mt-2 text-base font-semibold text-slate-900">{{ pixel.name }}</p>
            <p class="mt-1 break-all text-sm text-slate-500">{{ viewCopy.list.codePrefix }} {{ displayCode(pixel.value) }}</p>
          </div>

          <div class="flex items-center gap-2">
            <button
              type="button"
              class="rounded-xl border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="isReadOnly"
              @click="editPixel(pixel)"
            >
              {{ viewCopy.actions.edit }}
            </button>
            <button
              type="button"
              class="rounded-xl border border-rose-200 px-3 py-1.5 text-sm font-semibold text-rose-600 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="isReadOnly"
              @click="removePixel(pixel)"
            >
              {{ viewCopy.actions.remove }}
            </button>
          </div>
        </article>
      </div>
    </section>

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
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M6 18 18 6" /></svg>
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

      <div v-if="modalOpen && !isViajeonRoute && !isExternalRoute" class="app-modal-overlay fixed inset-0 z-[180] flex items-center justify-center px-4">
        <div class="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl md:p-5">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ viewCopy.form.eyebrow }}</p>
              <h2 class="mt-2 text-2xl font-bold text-slate-900">
                {{ isEditing ? viewCopy.form.editTitle : viewCopy.form.createTitle }}
              </h2>
            </div>
            <button type="button" class="rounded-full border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50" @click="closeModal">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" /></svg>
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
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../../store/useAuthStore";
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
const isExternalRoute = computed(() => route.name === "integrations-external");
const externalDrawer = ref<"viajeon" | "viajechat" | null>(null);
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

onMounted(async () => {
  try {
    await Promise.all([fetchPixels(), fetchViajeonStatus(), fetchViajechatStatus()]);
  } finally {
    isBootstrappingIntegrations.value = false;
  }
});
</script>
