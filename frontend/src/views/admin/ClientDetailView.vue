<template>
  <div class="det-page">
    <section v-if="loading && !client" class="flex min-h-[60vh] items-center justify-center">
      <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
    </section>

    <template v-else-if="client">
      <button type="button" class="det-back-btn" @click="goBack">
        <svg class="det-back-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m15 18-6-6 6-6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
        Clientes
      </button>

      <section class="det-card">
        <div class="det-hd-top">
          <div class="det-hd-inner">
            <div class="det-hd-left">
              <div class="det-avatar">{{ clientInitial }}</div>
              <div class="det-name-block">
                <p class="det-eyebrow">Cliente</p>
                <h1 class="det-name">{{ client.name }}</h1>
                <div class="det-meta">
                  <span class="det-meta-item val"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.12.9.33 1.77.63 2.61a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.47-1.2a2 2 0 0 1 2.11-.45c.84.3 1.71.51 2.61.63A2 2 0 0 1 22 16.92z" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>{{ formatPhone(client.phone) || "Telefone não informado" }}</span>
                  <span class="det-meta-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 4h16a2 2 0 0 1 2 2v.01L12 13 2 6.01V6a2 2 0 0 1 2-2Z" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/><path d="M22 8v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>{{ client.email || "E-mail não informado" }}</span>
                  <span class="det-meta-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 1 1 18 0Z" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="10" r="3" stroke-width="1.9"/></svg>{{ client.city || "Cidade não informada" }}</span>
                  <span class="det-meta-item">Cliente desde <strong>{{ clientSinceLabel }}</strong></span>
                </div>
              </div>
            </div>
            <div class="det-hd-actions">
              <a v-if="clientWhatsappLink" :href="clientWhatsappLink" target="_blank" rel="noopener" class="btn btn-p btn-wpp">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M16.75 13.96c-.25-.13-1.47-.72-1.7-.8-.23-.08-.4-.12-.57.12-.17.25-.65.8-.8.96-.14.17-.3.19-.55.06-.25-.13-1.06-.39-2.02-1.23-.74-.66-1.25-1.47-1.4-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.3.37-.45.12-.14.17-.25.25-.42.08-.17.04-.31-.02-.45-.06-.14-.57-1.37-.78-1.87-.2-.49-.41-.42-.57-.43h-.48c-.17 0-.45.06-.68.31-.23.25-.88.86-.88 2.1s.9 2.43 1.02 2.6c.12.17 1.76 2.69 4.25 3.77.59.26 1.06.42 1.42.54.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.17.21-.57.21-1.06.15-1.17-.06-.11-.23-.17-.48-.3Z" />
                  <path d="M12.04 2C6.77 2 2.5 6.26 2.5 11.52c0 1.85.53 3.65 1.52 5.2L2.4 21.5l4.9-1.57c1.43.78 3.04 1.2 4.7 1.2h.04c5.26 0 9.53-4.26 9.53-9.52C21.57 6.26 17.3 2 12.04 2Zm0 17.42h-.03c-1.5 0-2.97-.4-4.25-1.16l-.3-.18-2.9.93.95-2.82-.2-.29a7.83 7.83 0 0 1-1.2-4.18c0-4.3 3.5-7.8 7.82-7.8 2.08 0 4.03.8 5.5 2.28a7.75 7.75 0 0 1 2.29 5.5c0 4.3-3.5 7.8-7.8 7.8Z" />
                </svg>
                <span class="btn-wpp-label">WhatsApp</span>
              </a>
              <button type="button" class="btn btn-o" @click="openClientDataTab">Editar</button>
              <button type="button" class="btn btn-p" @click="newOpportunityOpen = !newOpportunityOpen">+ Nova oportunidade</button>
            </div>
          </div>
        </div>

        <div class="det-stats-inner">
          <div class="ds"><span class="ds-icon ds-icon--violet"><svg viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v3h3"/></svg></span><p class="ds-lbl">Total de oportunidades</p><p class="ds-val">{{ client.opportunitiesCount }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--amber"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg></span><p class="ds-lbl">Abertas</p><p class="ds-val">{{ openOpportunitiesCount }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--blue"><svg viewBox="0 0 24 24"><path d="M12 2v20"/><path d="M17 6H9.5a3.5 3.5 0 0 0 0 7H14.5a3.5 3.5 0 0 1 0 7H6"/></svg></span><p class="ds-lbl">Valores em aberto</p><p class="ds-val">{{ formatCurrency(futureEstimatedValueCents) }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--green"><svg viewBox="0 0 24 24"><path d="M4 14l5-5 4 4 7-7"/><path d="M15 6h5v5"/></svg></span><p class="ds-lbl">Valor já ganho</p><p class="ds-val g">{{ formatCurrency(wonValueCents) }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--red"><svg viewBox="0 0 24 24"><path d="M4 10l5 5 4-4 7 7"/><path d="M15 18h5v-5"/></svg></span><p class="ds-lbl">Valor perdido</p><p class="ds-val r">{{ formatCurrency(lostValueCents) }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--purple"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l2 2"/></svg></span><p class="ds-lbl">Última interação</p><p class="ds-val ds-time">{{ formatDateTime(lastInteractionAt) }}</p></div>
        </div>

        <div class="det-tabs">
          <button v-for="tab in tabs" :key="tab.id" type="button" class="tab-btn" :class="{ on: activeTab === tab.id }" @click="activeTab = tab.id">
            {{ tab.label }}
          </button>
        </div>

        <div class="det-body">
          <section v-if="editing" class="dados-block">
            <div class="dados-block-head">
              <p class="dados-block-eye">Editar cliente</p>
              <h2 class="dados-block-title">Dados do cliente</h2>
            </div>
            <div class="dados-grid2">
              <input v-model="editForm.name" type="text" placeholder="Nome" class="crm-input full" />
              <input v-model="editForm.cpf" type="text" placeholder="CPF" class="crm-input" />
              <input v-model="editForm.phone" type="text" placeholder="Telefone" class="crm-input" />
              <input v-model="editForm.email" type="email" placeholder="E-mail" class="crm-input" />
              <input v-model="editForm.city" type="text" placeholder="Cidade" class="crm-input" />
              <input v-model="editForm.state" type="text" maxlength="2" placeholder="UF" class="crm-input" />
              <input v-model="editForm.zipcode" type="text" placeholder="CEP" class="crm-input" />
              <input v-model="editForm.street" type="text" placeholder="Logradouro" class="crm-input full" />
              <input v-model="editForm.number" type="text" placeholder="Número" class="crm-input" />
              <input v-model="editForm.complement" type="text" placeholder="Complemento" class="crm-input" />
              <input v-model="editForm.neighborhood" type="text" placeholder="Bairro" class="crm-input full" />
              <input v-model="editForm.birthdate" type="date" class="crm-input" />
              <textarea v-model="editForm.notes" rows="4" class="crm-input full" placeholder="Observações"></textarea>
            </div>
            <div class="det-actions-row">
              <button type="button" class="btn btn-o" @click="resetEditForm">Cancelar</button>
              <button type="button" class="btn btn-p" @click="handleUpdateClient">Salvar alterações</button>
            </div>
          </section>

          <section v-if="newOpportunityOpen" class="dados-block">
            <div class="dados-block-head">
              <p class="dados-block-eye">Nova oportunidade</p>
              <h2 class="dados-block-title">Cadastrar oportunidade</h2>
            </div>
            <div class="dados-grid2">
              <input v-model="opportunityForm.opportunityName" type="text" placeholder="Nome da oportunidade" class="crm-input full" />
              <input v-model="opportunityForm.estimatedValue" type="text" placeholder="R$ 0,00" class="crm-input" />
              <select v-model="opportunityForm.statusId" class="crm-input">
                <option value="">Sem status</option>
                <option v-for="status in statuses" :key="status.id" :value="String(status.id)">{{ status.name }}</option>
              </select>
              <textarea v-model="opportunityForm.internalNotes" rows="4" class="crm-input full" placeholder="Observação inicial"></textarea>
            </div>
            <div class="det-actions-row">
              <button type="button" class="btn btn-o" @click="newOpportunityOpen = false">Cancelar</button>
              <button type="button" class="btn btn-p" @click="handleCreateOpportunity">Criar oportunidade</button>
            </div>
          </section>

          <div v-if="activeTab === 'opportunities'" class="space-y-3">
            <article v-for="opportunity in client.opportunities" :key="opportunity.id" class="opp-item">
              <div class="opp-item-main">
                <div class="opp-item-top">
                  <h3 class="opp-item-name">{{ opportunity.opportunityName || opportunity.name || "Nova oportunidade" }}</h3>
                  <span class="stg" :class="stageBadgeClass(opportunity)">{{ opportunity.statusName || "Sem etapa" }}</span>
                  <span v-if="opportunity.closeOutcome" :class="outcomeBadgeClass(opportunity.closeOutcome)">
                    {{ outcomeLabel(opportunity.closeOutcome) }}
                  </span>
                </div>
                <p class="opp-item-meta">
                  <span class="opp-src">
                    <svg viewBox="0 0 24 24"><path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 2v5h5" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    {{ opportunity.formName || "Formulário" }}
                  </span>
                  <span class="opp-meta-sep">·</span>
                  <span>R$ {{ formatCurrency(opportunity.estimatedValueCents || 0).replace("R$", "").trim() }}</span>
                  <span class="opp-meta-sep">·</span>
                  <span>{{ formatDateTime(opportunity.created_at || opportunity.updated_at || null) }}</span>
                </p>
              </div>
              <button type="button" class="btn btn-o btn-sm opp-open-btn" @click="openOpportunityModal(opportunity.id)">Abrir</button>
            </article>
            <p v-if="!client.opportunities.length" class="text-sm text-slate-500">Nenhuma oportunidade vinculada.</p>
          </div>

          <div v-else-if="activeTab === 'notes'" class="notes-tab-wrap">
            <div class="note-add-card">
              <textarea v-model="newClientNote" rows="4" class="note-ta" placeholder="Adicionar uma nota sobre este cliente..."></textarea>
              <div class="note-add-foot">
                <button type="button" class="btn btn-p btn-sm" @click="handleCreateClientNote">Salvar nota</button>
              </div>
            </div>
            <article v-for="note in client.notesTimeline" :key="note.id" class="note-card">
              <p class="note-meta">{{ formatDateTime(note.created_at) }}{{ note.author?.name ? ` · ${note.author.name}` : "" }}</p>
              <p class="note-txt">{{ note.content }}</p>
            </article>
            <p v-if="!client.notesTimeline.length" class="text-sm text-slate-500">Nenhuma nota do cliente.</p>
          </div>

          <div v-else-if="activeTab === 'documents'" class="docs-tab-wrap">
            <div v-if="!client.documents.length" class="docs-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 2v5h5" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <p>Nenhum documento anexado ainda.</p>
              <label class="btn btn-o btn-sm">
                + Adicionar documento
                <input type="file" class="hidden" @change="handleClientDocumentInput" />
              </label>
            </div>
            <div v-else class="space-y-3">
              <article v-for="document in client.documents" :key="document.id" class="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 p-4">
                <div class="min-w-0">
                  <a :href="document.fileUrl" target="_blank" rel="noopener" class="block truncate text-sm font-semibold text-brand hover:underline">{{ document.fileName }}</a>
                  <p class="mt-1 text-xs text-slate-400">{{ document.sourceLabel || "Cliente" }}</p>
                </div>
                <button type="button" class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50" @click="handleDeleteDocument(document.id)">Remover</button>
              </article>
            </div>
          </div>

          <div v-else-if="activeTab === 'history'" class="tl-wrap">
            <div v-if="!historyItems.length" class="docs-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 8v4l3 2"/><circle cx="12" cy="12" r="9"/></svg>
              <p>Nenhum evento no histórico.</p>
            </div>
            <article v-for="item in paginatedHistoryItems" :key="item.key" class="tl-item">
              <div class="tl-left">
                <div class="tl-dot" :class="`tl-dot--${item.kind}`">
                  <svg v-if="item.kind === 'opportunity'" viewBox="0 0 24 24"><path d="M12 2v20"/><path d="M17 6H9.5a3.5 3.5 0 0 0 0 7H14.5a3.5 3.5 0 0 1 0 7H6"/></svg>
                  <svg v-else-if="item.kind === 'note'" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                  <svg v-else-if="item.kind === 'document'" viewBox="0 0 24 24"><path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"/><path d="M14 2v5h5"/></svg>
                  <svg v-else viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/></svg>
                </div>
                <div class="tl-line"></div>
              </div>
              <div class="tl-body">
                <p class="tl-evt">{{ item.title }}</p>
                <p class="tl-detail">{{ item.detail }}</p>
                <p class="tl-time">{{ formatDateTime(item.date) }}</p>
              </div>
            </article>
            <div v-if="historyTotalPages > 1" class="tl-pagination">
              <button type="button" class="tl-page-btn" :disabled="historyPage === 1" @click="historyPage -= 1">Anterior</button>
              <span class="tl-page-info">Página {{ historyPage }} de {{ historyTotalPages }}</span>
              <button type="button" class="tl-page-btn" :disabled="historyPage === historyTotalPages" @click="historyPage += 1">Próxima</button>
            </div>
          </div>

          <div v-else>
            <section class="cd-wrap">
              <div class="cd-sec">Identificação</div>
              <div class="cd-grid">
                <div class="cd-cell cd-l">
                  <div class="cd-lbl">Tipo de cliente</div>
                  <div class="cd-val"><span class="cd-tipo-pf">{{ clientTypeLabel }}</span></div>
                </div>
                <div class="cd-cell">
                  <div class="cd-lbl">Nome</div>
                  <div class="cd-val" :class="{ empty: !displayFieldValue('name') }">{{ displayFieldValue("name") || "—" }}</div>
                  <button type="button" class="cd-edit-btn" @click="startInlineEdit('name')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button>
                  <div class="cd-inp-wrap" v-if="isInlineEditing('name')">
                    <input v-model="inlineEditDraft" type="text" class="cd-inp" />
                    <div class="cd-act">
                      <button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('name')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button>
                      <button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button>
                    </div>
                  </div>
                </div>
                <div class="cd-cell cd-l">
                  <div class="cd-lbl">CPF</div>
                  <div class="cd-val" :class="{ empty: !displayFieldValue('cpf') }">{{ displayFieldValue("cpf") || "—" }}</div>
                  <button type="button" class="cd-edit-btn" @click="startInlineEdit('cpf')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button>
                  <div class="cd-inp-wrap" v-if="isInlineEditing('cpf')">
                    <input v-model="inlineEditDraft" type="text" class="cd-inp" />
                    <div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('cpf')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div>
                  </div>
                </div>
                <div class="cd-cell">
                  <div class="cd-lbl">Nascimento</div>
                  <div class="cd-val" :class="{ empty: !displayFieldValue('birthdate') }">{{ displayFieldValue("birthdate") || "—" }}</div>
                  <button type="button" class="cd-edit-btn" @click="startInlineEdit('birthdate')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button>
                  <div class="cd-inp-wrap" v-if="isInlineEditing('birthdate')">
                    <input v-model="inlineEditDraft" type="date" class="cd-inp" />
                    <div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('birthdate')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div>
                  </div>
                </div>
              </div>

              <div class="cd-sec">Contato</div>
              <div class="cd-grid">
                <div class="cd-cell cd-l">
                  <div class="cd-lbl">Telefone</div>
                  <div class="cd-val" :class="{ empty: !displayFieldValue('phone') }">{{ displayFieldValue("phone") || "—" }}</div>
                  <button type="button" class="cd-edit-btn" @click="startInlineEdit('phone')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button>
                  <div class="cd-inp-wrap" v-if="isInlineEditing('phone')">
                    <input v-model="inlineEditDraft" type="text" class="cd-inp" />
                    <div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('phone')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div>
                  </div>
                </div>
                <div class="cd-cell">
                  <div class="cd-lbl">E-mail</div>
                  <div class="cd-val" :class="{ empty: !displayFieldValue('email') }">{{ displayFieldValue("email") || "—" }}</div>
                  <button type="button" class="cd-edit-btn" @click="startInlineEdit('email')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button>
                  <div class="cd-inp-wrap" v-if="isInlineEditing('email')">
                    <input v-model="inlineEditDraft" type="email" class="cd-inp" />
                    <div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('email')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div>
                  </div>
                </div>
              </div>

              <div class="cd-sec">Endereço</div>
              <div class="cd-grid">
                <div class="cd-cell cd-l"><div class="cd-lbl">CEP</div><div class="cd-val" :class="{ empty: !displayFieldValue('zipcode') }">{{ displayFieldValue("zipcode") || "—" }}</div><button type="button" class="cd-edit-btn" @click="startInlineEdit('zipcode')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button><div class="cd-inp-wrap" v-if="isInlineEditing('zipcode')"><input v-model="inlineEditDraft" type="text" class="cd-inp" /><div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('zipcode')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div></div></div>
                <div class="cd-cell"><div class="cd-lbl">UF</div><div class="cd-val" :class="{ empty: !displayFieldValue('state') }">{{ displayFieldValue("state") || "—" }}</div><button type="button" class="cd-edit-btn" @click="startInlineEdit('state')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button><div class="cd-inp-wrap" v-if="isInlineEditing('state')"><input v-model="inlineEditDraft" type="text" maxlength="2" class="cd-inp" /><div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('state')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div></div></div>
                <div class="cd-cell cd-cell-full"><div class="cd-lbl">Logradouro</div><div class="cd-val" :class="{ empty: !displayFieldValue('street') }">{{ displayFieldValue("street") || "—" }}</div><button type="button" class="cd-edit-btn" @click="startInlineEdit('street')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button><div class="cd-inp-wrap" v-if="isInlineEditing('street')"><input v-model="inlineEditDraft" type="text" class="cd-inp" /><div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('street')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div></div></div>
                <div class="cd-cell cd-l"><div class="cd-lbl">Número</div><div class="cd-val" :class="{ empty: !displayFieldValue('number') }">{{ displayFieldValue("number") || "—" }}</div><button type="button" class="cd-edit-btn" @click="startInlineEdit('number')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button><div class="cd-inp-wrap" v-if="isInlineEditing('number')"><input v-model="inlineEditDraft" type="text" class="cd-inp" /><div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('number')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div></div></div>
                <div class="cd-cell"><div class="cd-lbl">Complemento</div><div class="cd-val" :class="{ empty: !displayFieldValue('complement') }">{{ displayFieldValue("complement") || "—" }}</div><button type="button" class="cd-edit-btn" @click="startInlineEdit('complement')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button><div class="cd-inp-wrap" v-if="isInlineEditing('complement')"><input v-model="inlineEditDraft" type="text" class="cd-inp" /><div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('complement')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div></div></div>
                <div class="cd-cell cd-l"><div class="cd-lbl">Bairro</div><div class="cd-val" :class="{ empty: !displayFieldValue('neighborhood') }">{{ displayFieldValue("neighborhood") || "—" }}</div><button type="button" class="cd-edit-btn" @click="startInlineEdit('neighborhood')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button><div class="cd-inp-wrap" v-if="isInlineEditing('neighborhood')"><input v-model="inlineEditDraft" type="text" class="cd-inp" /><div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('neighborhood')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div></div></div>
                <div class="cd-cell"><div class="cd-lbl">Cidade</div><div class="cd-val" :class="{ empty: !displayFieldValue('city') }">{{ displayFieldValue("city") || "—" }}</div><button type="button" class="cd-edit-btn" @click="startInlineEdit('city')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button><div class="cd-inp-wrap" v-if="isInlineEditing('city')"><input v-model="inlineEditDraft" type="text" class="cd-inp" /><div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('city')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div></div></div>
              </div>

              <div class="cd-sec">Observações</div>
              <div class="cd-grid">
                <div class="cd-cell cd-cell-full cd-cell-ta">
                  <div class="cd-lbl">Observações</div>
                  <div class="cd-val" :class="{ empty: !displayFieldValue('notes') }">{{ displayFieldValue("notes") || "—" }}</div>
                  <button type="button" class="cd-edit-btn" @click="startInlineEdit('notes')"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg></button>
                  <div class="cd-inp-wrap" v-if="isInlineEditing('notes')">
                    <textarea v-model="inlineEditDraft" rows="3" class="cd-inp cd-ta"></textarea>
                    <div class="cd-act"><button type="button" class="cd-ok" :disabled="inlineEditSaving" @click="saveInlineEdit('notes')"><svg viewBox="0 0 24 24"><path d="m5 13 4 4L19 7"/></svg></button><button type="button" class="cd-cl" :disabled="inlineEditSaving" @click="cancelInlineEdit"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18 18 6"/></svg></button></div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </section>

      <OpportunityDrawer v-model="isOpportunityModalOpen" :contact-id="selectedOpportunityId" :statuses="statuses" mode="modal" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import OpportunityDrawer from "../../components/admin/leads/OpportunityDrawer.vue";
import { useLeadCaptureStore } from "../../store/useLeadCaptureStore";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";

const route = useRoute();
const leadStore = useLeadCaptureStore();

const client = computed(() => leadStore.clientDetail);
const loading = computed(() => leadStore.clientDetailLoading);
const statuses = computed(() => leadStore.statuses);

const tabs = [
  { id: "opportunities", label: "Oportunidades" },
  { id: "notes", label: "Notas" },
  { id: "documents", label: "Documentos" },
  { id: "history", label: "Histórico" },
  { id: "data", label: "Dados do cliente" }
] as const;

const activeTab = ref<(typeof tabs)[number]["id"]>("opportunities");
const editing = ref(false);
const newOpportunityOpen = ref(false);
const newClientNote = ref("");
const isOpportunityModalOpen = ref(false);
const selectedOpportunityId = ref<number | null>(null);
const historyPage = ref(1);
const historyPageSize = 10;
const inlineEditingField = ref<string | null>(null);
const inlineEditDraft = ref("");
const inlineEditSaving = ref(false);
const editForm = reactive({
  name: "",
  cpf: "",
  phone: "",
  email: "",
  city: "",
  zipcode: "",
  street: "",
  number: "",
  complement: "",
  neighborhood: "",
  state: "",
  birthdate: "",
  notes: ""
});
const opportunityForm = reactive({
  opportunityName: "",
  estimatedValue: "",
  statusId: "",
  internalNotes: ""
});

const clientId = computed(() => Number(route.params.id));
const clientInitial = computed(() => (client.value?.name?.trim()?.charAt(0) || "C").toUpperCase());
const clientSinceLabel = computed(() => {
  const raw = (client.value as any)?.createdAt || (client.value as any)?.created_at || null;
  return formatDateOnly(raw) || "-";
});
const lastInteractionAt = computed(() => {
  const noteDate = client.value?.notesTimeline?.[0]?.created_at || null;
  const opportunityDate = client.value?.lastOpportunityAt || null;
  return noteDate || opportunityDate;
});
const futureEstimatedValueCents = computed(() =>
  (client.value?.opportunities || []).reduce((total, opportunity) => {
    if (opportunity.closeOutcome === "won" || opportunity.closeOutcome === "lost") return total;
    return total + (opportunity.estimatedValueCents || 0);
  }, 0)
);
const openOpportunitiesCount = computed(
  () => (client.value?.opportunities || []).filter(opportunity => !opportunity.closeOutcome).length
);
const wonValueCents = computed(() =>
  (client.value?.opportunities || []).reduce((total, opportunity) => {
    if (opportunity.closeOutcome !== "won") return total;
    return total + (opportunity.estimatedValueCents || 0);
  }, 0)
);
const lostValueCents = computed(() =>
  (client.value?.opportunities || []).reduce((total, opportunity) => {
    if (opportunity.closeOutcome !== "lost") return total;
    return total + (opportunity.estimatedValueCents || 0);
  }, 0)
);
const clientWhatsappLink = computed(() => {
  const digits = normalizeWhatsappDigits(client.value?.phone || "");
  return digits ? `https://wa.me/${digits}` : "";
});
const clientTypeLabel = computed(() => {
  const digits = (client.value?.cpf || "").replace(/\D/g, "");
  return digits.length === 11 ? "Pessoa física" : "Cliente";
});
const historyItems = computed(() => {
  const events: Array<{
    key: string;
    kind: "opportunity" | "note" | "document" | "client";
    title: string;
    detail: string;
    date: string;
    order: number;
    source?: "form_submitted" | "opportunity_created" | "opportunity_closed" | "note" | "document" | "client_created";
    opportunityId?: number;
  }> = [];
  const c = client.value;
  if (!c) return events;

  const createdAt = (c as any)?.created_at || (c as any)?.createdAt || "";
  if (createdAt) {
      events.push({
        key: `client-created-${createdAt}`,
        kind: "client",
        title: "Cliente criado",
        detail: c.name ? `Cadastro de ${c.name}` : "Cadastro do cliente",
        date: String(createdAt),
        order: 50,
        source: "client_created"
      });
  }

  for (const opp of c.opportunities || []) {
    const baseName = opp.opportunityName || opp.name || `Oportunidade #${opp.id}`;
    const created = opp.created_at || "";
    if (created) {
      const formLabel = opp.formName || "Formulário";
      const pageLabel = opp.pageTitle || opp.pageSlug || "";
      events.push({
        key: `form-submitted-${opp.id}-${created}`,
        kind: "client",
        title: "Respondeu formulário",
        detail: pageLabel ? `${formLabel} · Página: ${pageLabel}` : formLabel,
        date: String(created),
        order: 10,
        source: "form_submitted",
        opportunityId: opp.id
      });
      events.push({
        key: `opp-created-${opp.id}-${created}`,
        kind: "opportunity",
        title: "Oportunidade criada",
        detail: `${baseName} · ${formatCurrency(opp.estimatedValueCents || 0)}`,
        date: String(created),
        order: 20,
        source: "opportunity_created",
        opportunityId: opp.id
      });
    }
    if (opp.closeOutcome && (opp.closedAt || opp.updated_at)) {
      events.push({
        key: `opp-close-${opp.id}-${opp.closedAt || opp.updated_at}`,
        kind: "opportunity",
        title: opp.closeOutcome === "won" ? "Oportunidade ganha" : "Oportunidade perdida",
        detail: `${baseName} · ${formatCurrency(opp.estimatedValueCents || 0)}`,
        date: String(opp.closedAt || opp.updated_at),
        order: 30,
        source: "opportunity_closed",
        opportunityId: opp.id
      });
    }
  }

  for (const note of c.notesTimeline || []) {
    if (!note.created_at) continue;
    events.push({
      key: `note-${note.id}-${note.created_at}`,
      kind: "note",
      title: "Nota adicionada",
      detail: note.content || "Sem conteúdo",
      date: String(note.created_at),
      order: 40,
      source: "note"
    });
  }

  for (const doc of c.documents || []) {
    if (!doc.created_at) continue;
    events.push({
      key: `doc-${doc.id}-${doc.created_at}`,
      kind: "document",
      title: "Documento anexado",
      detail: doc.fileName || "Documento",
      date: String(doc.created_at),
      order: 45,
      source: "document"
    });
  }

  return events
    .filter(item => item.date)
    .sort((a, b) => {
      const aTime = Number.isNaN(new Date(a.date).getTime()) ? 0 : new Date(a.date).getTime();
      const bTime = Number.isNaN(new Date(b.date).getTime()) ? 0 : new Date(b.date).getTime();
      const byDate = bTime - aTime;
      if (byDate !== 0) return byDate;

      if (a.opportunityId && b.opportunityId && a.opportunityId === b.opportunityId) {
        const aIsForm = a.source === "form_submitted";
        const bIsForm = b.source === "form_submitted";
        const aIsCreated = a.source === "opportunity_created";
        const bIsCreated = b.source === "opportunity_created";
        if (aIsCreated && bIsForm) return -1;
        if (aIsForm && bIsCreated) return 1;
      }

      return a.order - b.order;
    });
});
const historyTotalPages = computed(() => Math.max(1, Math.ceil(historyItems.value.length / historyPageSize)));
const paginatedHistoryItems = computed(() => {
  const start = (historyPage.value - 1) * historyPageSize;
  return historyItems.value.slice(start, start + historyPageSize);
});

const load = async () => {
  if (!clientId.value) return;
  await Promise.all([leadStore.fetchClientDetail(clientId.value), leadStore.fetchStatuses()]);
  resetEditForm();
};

const goBack = () => {
  window.history.back();
};

const openClientDataTab = () => {
  editing.value = false;
  activeTab.value = "data";
};

const resetEditForm = () => {
  editForm.name = client.value?.name || "";
  editForm.cpf = client.value?.cpf || "";
  editForm.phone = client.value?.phone || "";
  editForm.email = client.value?.email || "";
  editForm.city = client.value?.city || "";
  editForm.zipcode = client.value?.zipcode || "";
  editForm.street = client.value?.street || "";
  editForm.number = client.value?.number || "";
  editForm.complement = client.value?.complement || "";
  editForm.neighborhood = client.value?.neighborhood || "";
  editForm.state = client.value?.state || "";
  editForm.birthdate = client.value?.birthdate || "";
  editForm.notes = client.value?.notes || "";
  editing.value = false;
};

const handleUpdateClient = async () => {
  if (!clientId.value) return;
  try {
    await leadStore.updateClient(clientId.value, {
      name: editForm.name.trim() || undefined,
      cpf: editForm.cpf.trim() || null,
      phone: editForm.phone.trim() || null,
      email: editForm.email.trim() || null,
      city: editForm.city.trim() || null,
      zipcode: editForm.zipcode.trim() || null,
      street: editForm.street.trim() || null,
      number: editForm.number.trim() || null,
      complement: editForm.complement.trim() || null,
      neighborhood: editForm.neighborhood.trim() || null,
      state: editForm.state.trim().toUpperCase() || null,
      birthdate: editForm.birthdate || null,
      notes: editForm.notes.trim() || null
    });
    await leadStore.fetchClientDetail(clientId.value);
    resetEditForm();
  } catch (error) {
    console.error(error);
  }
};

const handleCreateOpportunity = async () => {
  if (!clientId.value || !opportunityForm.opportunityName.trim()) return;
  try {
    await leadStore.createOpportunityFromClient(clientId.value, {
      opportunityName: opportunityForm.opportunityName.trim(),
      estimatedValueCents: inputToCents(opportunityForm.estimatedValue),
      statusId: opportunityForm.statusId ? Number(opportunityForm.statusId) : null,
      internalNotes: opportunityForm.internalNotes.trim() || null
    });
    opportunityForm.opportunityName = "";
    opportunityForm.estimatedValue = "";
    opportunityForm.statusId = "";
    opportunityForm.internalNotes = "";
    newOpportunityOpen.value = false;
  } catch (error) {
    console.error(error);
  }
};

const handleCreateClientNote = async () => {
  if (!clientId.value || !newClientNote.value.trim()) return;
  try {
    await leadStore.createClientNote(clientId.value, newClientNote.value.trim());
    newClientNote.value = "";
  } catch (error) {
    console.error(error);
  }
};

const handleClientDocumentInput = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!clientId.value || !file) return;
  try {
    await leadStore.uploadClientDocument(clientId.value, file);
  } catch (error) {
    console.error(error);
  } finally {
    input.value = "";
  }
};

const handleDeleteDocument = async (documentId: number) => {
  if (!window.confirm("Remover este documento?")) return;
  try {
    await leadStore.deleteDocument(documentId);
    await leadStore.fetchClientDetail(clientId.value);
  } catch (error) {
    console.error(error);
  }
};

const openOpportunityModal = (opportunityId: number) => {
  selectedOpportunityId.value = opportunityId;
  isOpportunityModalOpen.value = true;
};

watch(
  () => route.params.id,
  () => {
    load().catch(error => console.error(error));
  },
  { immediate: true }
);

watch(isOpportunityModalOpen, value => {
  if (!value) {
    load().catch(error => console.error(error));
  }
});
watch(historyItems, () => {
  if (historyPage.value > historyTotalPages.value) historyPage.value = historyTotalPages.value;
});
watch(activeTab, tab => {
  if (tab === "history") historyPage.value = 1;
});

function inputToCents(value: string) {
  const digits = value.replace(/\D/g, "");
  if (!digits) return null;
  return Number(digits);
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format((value || 0) / 100);
}

function formatDateOnly(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(date);
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: value.includes("T") ? "short" : undefined
  }).format(date);
}

function formatPhone(value?: string | null) {
  const digits = (value || "").replace(/\D/g, "");
  if (digits.length === 13 && digits.startsWith("55")) return `+55 (${digits.slice(2, 4)}) ${digits.slice(4, 9)}-${digits.slice(9, 13)}`;
  if (digits.length === 11) return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
  if (digits.length === 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6, 10)}`;
  return value || "";
}

function formatCpf(value?: string | null) {
  const digits = (value || "").replace(/\D/g, "");
  if (digits.length !== 11) return value || "";
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9, 11)}`;
}

function isInlineEditing(field: string) {
  return inlineEditingField.value === field;
}

function displayFieldValue(field: string) {
  const value = (editForm as any)[field];
  if (!value) return "";
  if (field === "phone") return formatPhone(String(value));
  if (field === "cpf") return formatCpf(String(value));
  if (field === "birthdate") return formatDateOnly(String(value));
  return String(value);
}

function startInlineEdit(field: string) {
  inlineEditingField.value = field;
  inlineEditDraft.value = String((editForm as any)[field] || "");
}

function cancelInlineEdit() {
  inlineEditingField.value = null;
  inlineEditDraft.value = "";
}

async function saveInlineEdit(field: string) {
  if (!clientId.value || inlineEditSaving.value) return;
  (editForm as any)[field] = field === "state" ? inlineEditDraft.value.trim().toUpperCase() : inlineEditDraft.value;
  inlineEditSaving.value = true;
  try {
    await leadStore.updateClient(clientId.value, {
      name: editForm.name.trim() || undefined,
      cpf: editForm.cpf.trim() || null,
      phone: editForm.phone.trim() || null,
      email: editForm.email.trim() || null,
      city: editForm.city.trim() || null,
      zipcode: editForm.zipcode.trim() || null,
      street: editForm.street.trim() || null,
      number: editForm.number.trim() || null,
      complement: editForm.complement.trim() || null,
      neighborhood: editForm.neighborhood.trim() || null,
      state: editForm.state.trim().toUpperCase() || null,
      birthdate: editForm.birthdate || null,
      notes: editForm.notes.trim() || null
    });
    await leadStore.fetchClientDetail(clientId.value);
    resetEditForm();
    cancelInlineEdit();
  } catch (error) {
    console.error(error);
  } finally {
    inlineEditSaving.value = false;
  }
}

function stageBadgeClass(opportunity: any) {
  const name = String(opportunity?.statusName || "").toLowerCase();
  if (!name) return "s-sem";
  if (name.includes("aten")) return "s-atencao";
  if (name.includes("aberto") || name.includes("contato")) return "s-contato";
  if (name.includes("qual")) return "s-qualif";
  if (name.includes("proposta")) return "s-proposta";
  if (name.includes("ganh")) return "s-ganha";
  if (name.includes("perd")) return "s-perdida";
  return "s-sem";
}

function outcomeLabel(outcome: "won" | "lost") {
  return outcome === "won" ? "Ganha" : "Perdida";
}

function outcomeBadgeClass(outcome: "won" | "lost") {
  return outcome === "won" ? "st-ganha" : "st-perdida";
}

</script>

<style scoped>
.det-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px 20px 0;
}

.det-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
  margin: 2px 0;
  padding: 6px 12px;
  border-radius: 9px;
  background: #f5f7f5;
  border: 1.5px solid #e4e9e4;
  font-size: 12px;
  font-weight: 600;
  color: #4a5e4a;
}
.det-back-ic {
  width: 13px;
  height: 13px;
}

.det-card {
  background: #fff;
  border: 1.5px solid #e4e9e4;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.det-hd-top {
  padding: 16px 20px;
  border-bottom: 1.5px solid #e4e9e4;
}

.det-hd-inner {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.det-hd-left {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.det-avatar {
  width: 48px;
  height: 48px;
  border-radius: 999px;
  background: #2fb752;
  color: #fff;
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.det-eyebrow {
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 700;
  color: #8a9e8a;
  letter-spacing: 0.08em;
}

.det-name {
  font-size: 22px;
  line-height: 1.15;
  font-weight: 800;
  color: #111a14;
}

.det-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
  color: #8a9e8a;
  font-size: 13px;
}

.det-meta-item.val {
  color: #4a5e4a;
}
.det-meta-item svg {
  width: 13px;
  height: 13px;
  opacity: 0.75;
  flex-shrink: 0;
}

.det-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  line-height: 1;
}

.det-hd-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  border: 1.5px solid transparent;
  transition: all 0.15s ease;
}

.btn-p {
  background: #3dcc5f;
  color: #0f1f14;
  border-color: #3dcc5f;
}
.btn-p:hover {
  background: #2ead4c;
  border-color: #2ead4c;
}

.btn-o {
  background: #fff;
  color: #4a5e4a;
  border-color: #d7e1d7;
}
.btn-o:hover {
  border-color: #c7d4c7;
  color: #111a14;
  background: #f7faf7;
}

.btn-sm {
  padding: 8px 12px;
}

.btn-wpp {
  background: #25d366;
  border-color: #25d366;
  color: #fff;
}
.btn-wpp:hover {
  background: #22c55e;
  border-color: #22c55e;
  box-shadow: 0 4px 14px rgba(34, 197, 94, 0.28);
}
.btn-wpp svg {
  width: 13px;
  height: 13px;
  margin-right: 2px;
  color: #fff;
}

.btn-wpp:hover .btn-wpp-label {
  color: #0f1f14;
}

.det-stats-inner {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1.5px solid #e4e9e4;
}

.ds {
  border: 1.5px solid #e4e9e4;
  border-radius: 12px;
  padding: 12px 14px;
  background: #fff;
}
.ds-icon {
  display: inline-flex;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  margin-bottom: 8px;
  align-items: center;
  justify-content: center;
}
.ds-icon svg {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ds-icon--violet { background: rgba(99, 102, 241, 0.16); color: #6366f1; }
.ds-icon--amber { background: rgba(245, 158, 11, 0.16); color: #d97706; }
.ds-icon--blue { background: rgba(59, 130, 246, 0.16); color: #2563eb; }
.ds-icon--green { background: rgba(34, 197, 94, 0.16); color: #16a34a; }
.ds-icon--red { background: rgba(239, 68, 68, 0.16); color: #dc2626; }
.ds-icon--purple { background: rgba(139, 92, 246, 0.16); color: #7c3aed; }

.ds-lbl {
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #8a9e8a;
}

.ds-val {
  margin-top: 4px;
  font-size: 18px;
  line-height: 1;
  font-weight: 800;
  color: #111a14;
}

.ds-val.g {
  color: #1a7a35;
}

.ds-val.r {
  color: #c0392b;
}

.ds-time {
  font-size: 16px;
}

.det-tabs {
  display: flex;
  gap: 0;
  padding: 0 20px;
  border-bottom: 1.5px solid #e4e9e4;
}

.tab-btn {
  border: none;
  background: transparent;
  padding: 12px 16px;
  margin-bottom: -1px;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  font-weight: 600;
  color: #8a9e8a;
}

.tab-btn.on {
  color: #2ead4c;
  border-bottom-color: #2ead4c;
}

.det-body {
  padding: 20px;
}

.opp-item {
  background: #fff;
  border: 1.5px solid #e4e9e4;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}
.opp-item:hover {
  border-color: #cdd8cd;
  background: #fafcfa;
}
.opp-item-main { flex: 1; min-width: 0; }
.opp-item-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 5px; }

.opp-item-name {
  font-size: 14px;
  font-weight: 700;
  color: #111a14;
}

.opp-item-meta {
  color: #8a9e8a;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
}
.opp-meta-sep { color: #cdd8cd; font-size: 14px; }
.opp-src { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: #8a9e8a; }
.opp-src svg { width: 10px; height: 10px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; opacity: .7; flex-shrink: 0; }
.opp-open-btn { min-width: 88px; }

.stg{display:inline-flex;align-items:center;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;border:1.5px solid transparent}
.s-sem{background:#f5f7f5;color:#8a9e8a;border-color:#e4e9e4}
.s-atencao{background:rgba(239,68,68,.07);color:#C0392B;border-color:rgba(239,68,68,.2)}
.s-contato{background:rgba(245,158,11,.07);color:#92400E;border-color:rgba(245,158,11,.2)}
.s-qualif{background:rgba(99,102,241,.07);color:#4338CA;border-color:rgba(99,102,241,.18)}
.s-proposta{background:rgba(139,92,246,.07);color:#6D28D9;border-color:rgba(139,92,246,.18)}
.s-ganha{background:rgba(61,204,95,.10);color:#1A7A35;border-color:rgba(61,204,95,.22)}
.s-perdida{background:rgba(239,68,68,.07);color:#C0392B;border-color:rgba(239,68,68,.2)}
.st-ganha{background:rgba(61,204,95,.10);color:#1A7A35;border:1.5px solid rgba(61,204,95,.22);border-radius:6px;padding:2px 8px;font-size:11px;font-weight:600}
.st-perdida{background:rgba(239,68,68,.07);color:#C0392B;border:1.5px solid rgba(239,68,68,.2);border-radius:6px;padding:2px 8px;font-size:11px;font-weight:600}

.notes-tab-wrap{display:flex;flex-direction:column;gap:10px}
.note-add-card{background:#fff;border:1.5px solid #e4e9e4;border-radius:12px;overflow:hidden}
.note-ta{width:100%;padding:13px 16px;border:none;outline:none;font-family:inherit;font-size:13px;color:#111a14;resize:vertical;min-height:80px;line-height:1.55;background:transparent}
.note-ta::placeholder{color:#8a9e8a}
.note-add-foot{padding:10px 14px;border-top:1.5px solid #e4e9e4;display:flex;justify-content:flex-end}
.note-card{background:#fff;border:1.5px solid #e4e9e4;border-radius:12px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.05),0 1px 2px rgba(0,0,0,.03)}
.note-meta{font-size:11px;color:#8a9e8a;margin-bottom:6px}
.note-txt{font-size:13px;color:#4a5e4a;line-height:1.6;white-space:pre-wrap}

.cd-wrap{background:#fff;border:1.5px solid #e4e9e4;border-radius:12px;overflow:hidden}
.cd-sec{font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#8a9e8a;padding:9px 18px;background:#f5f7f5;border-bottom:1px solid #e4e9e4}
.cd-sec:not(:first-child){border-top:1.5px solid #e4e9e4}
.cd-grid{display:grid;grid-template-columns:1fr 1fr}
.cd-cell{padding:12px 18px;border-bottom:1px solid #e4e9e4;position:relative;transition:background .1s;min-height:56px}
.cd-cell:hover{background:#F9FBF9}
.cd-l{border-right:1px solid #e4e9e4}
.cd-cell-full{grid-column:1/-1}
.cd-grid:last-of-type .cd-cell:last-child{border-bottom:none}
.cd-grid:last-of-type .cd-cell:nth-last-child(2):not(.cd-cell-full){border-bottom:none}
.cd-lbl{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#8a9e8a;margin-bottom:5px}
.cd-val{font-size:13px;color:#111a14;line-height:1.4;padding-right:30px}
.cd-val.empty{color:#8a9e8a;font-style:italic}
.cd-edit-btn{position:absolute;top:10px;right:10px;width:24px;height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center;cursor:pointer;border:1.5px solid transparent;background:transparent;transition:all .15s;opacity:0}
.cd-cell:hover .cd-edit-btn{opacity:1}
.cd-edit-btn:hover{background:#f5f7f5;border-color:#e4e9e4}
.cd-edit-btn svg{width:11px;height:11px;stroke:#8a9e8a;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.cd-inp-wrap{display:flex;align-items:center;gap:5px}
.cd-cell:has(.cd-inp-wrap) .cd-val,
.cd-cell:has(.cd-inp-wrap) .cd-edit-btn{display:none}
.cd-inp{flex:1;padding:7px 10px;border:1.5px solid rgba(61,204,95,.22);border-radius:8px;font-family:inherit;font-size:13px;color:#111a14;outline:none;background:#fff;min-width:0}
.cd-inp:focus{border-color:#2EAD4C}
.cd-ta{min-height:72px;resize:vertical;line-height:1.5}
.cd-cell-ta .cd-inp-wrap{align-items:flex-start}
.cd-act{display:flex;gap:4px;flex-shrink:0}
.cd-ok,.cd-cl{width:26px;height:26px;border-radius:6px;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0}
.cd-ok{border:1.5px solid rgba(61,204,95,.22);background:rgba(61,204,95,.10)}
.cd-ok svg{width:11px;height:11px;stroke:#1A7A35;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
.cd-cl{border:1.5px solid #e4e9e4;background:#f5f7f5}
.cd-cl svg{width:11px;height:11px;stroke:#8a9e8a;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.cd-tipo-pf{background:rgba(61,204,95,.10);color:#1A7A35;border:1.5px solid rgba(61,204,95,.22);padding:2px 9px;border-radius:6px;font-size:11px;font-weight:700;display:inline-block}
.cd-tipo-emp{background:rgba(99,102,241,.08);color:#4338CA;border:1.5px solid rgba(99,102,241,.2);padding:2px 9px;border-radius:6px;font-size:11px;font-weight:700;display:inline-block}

.tl-wrap{display:flex;flex-direction:column}
.tl-item{display:flex;gap:12px;padding-bottom:18px}
.tl-item:last-child{padding-bottom:0}
.tl-left{display:flex;flex-direction:column;align-items:center;flex-shrink:0;width:30px}
.tl-dot{width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.tl-dot svg{width:13px;height:13px;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke:currentColor}
.tl-dot--opportunity{background:rgba(59,130,246,.14);color:#2563eb}
.tl-dot--note{background:rgba(245,158,11,.14);color:#d97706}
.tl-dot--document{background:rgba(99,102,241,.14);color:#6366f1}
.tl-dot--client{background:rgba(61,204,95,.12);color:#1A7A35}
.tl-line{width:1.5px;background:#e4e9e4;flex:1;margin-top:4px;min-height:12px}
.tl-item:last-child .tl-line{display:none}
.tl-body{flex:1;padding-top:4px}
.tl-evt{font-size:13px;font-weight:600;color:#111a14;line-height:1.3}
.tl-detail{font-size:12px;color:#8a9e8a;margin-top:3px;line-height:1.5;white-space:pre-wrap}
.tl-time{font-size:10px;color:#8a9e8a;margin-top:5px}
.tl-pagination{display:flex;align-items:center;justify-content:flex-end;gap:10px;padding-top:12px}
.tl-page-info{font-size:12px;color:#6b7f6b}
.tl-page-btn{height:32px;padding:0 12px;border-radius:9px;border:1.5px solid #d8e2d8;background:#fff;color:#375237;font-size:12px;font-weight:700}
.tl-page-btn:disabled{opacity:.45;cursor:not-allowed}

.dados-block {
  border: 1.5px solid #e4e9e4;
  border-radius: 12px;
  margin-bottom: 14px;
  overflow: hidden;
}

.dados-block-head {
  padding: 14px 18px;
  border-bottom: 1.5px solid #e4e9e4;
}

.dados-block-eye {
  font-size: 11px;
  text-transform: uppercase;
  color: #8a9e8a;
  font-weight: 700;
}

.dados-block-title {
  font-size: 16px;
  font-weight: 700;
  color: #111a14;
}

.dados-grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 16px;
}

.crm-input {
  width: 100%;
  border-radius: 10px;
  border: 1.5px solid #d8e1d8;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
}

.crm-input.full {
  grid-column: 1 / -1;
}

.det-actions-row {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 16px 16px;
}

.det-actions-row--left {
  justify-content: flex-start;
  align-items: center;
}

.docs-tab-wrap {
  min-height: 240px;
}

.docs-empty {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #8a9e8a;
}

.docs-empty svg {
  width: 34px;
  height: 34px;
}

@media (max-width: 1100px) {
  .det-stats-inner {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .det-name {
    font-size: 20px;
  }

  .ds-val {
    font-size: 16px;
  }

  .opp-item-name {
    font-size: 13px;
  }

  .opp-item-meta {
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .det-page {
    padding: 14px 10px 0;
  }

  .dados-grid2 {
    grid-template-columns: 1fr;
  }

  .det-stats-inner {
    grid-template-columns: 1fr 1fr;
  }

  .det-body {
    padding: 14px;
  }

  .det-tabs {
    padding: 0 8px;
    overflow-x: auto;
  }

  .tab-btn {
    white-space: nowrap;
  }
}
</style>

