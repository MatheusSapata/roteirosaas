<template>
  <div class="inbox-page h-full min-h-[680px] w-full overflow-hidden bg-background text-foreground">
    <div class="grid h-full grid-cols-1 lg:grid-cols-[350px_minmax(0,1fr)_330px]">
      <aside v-show="!isMobileViewport || !isMobileChatOpen" class="inbox-sidebar flex h-full min-h-0 flex-col overflow-hidden border-r">
        <div class="border-b border-slate-200/80 px-5 py-5">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h1 class="font-display text-xl font-semibold text-foreground">Caixa de entrada</h1>
              <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">{{ totalUnread }}</span>
              <p class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold shadow-sm" :class="wsStatusClass">
                <span class="inline-flex h-1.5 w-1.5 rounded-full" :class="wsDotClass"></span>
                {{ wsStatusLabel }}
              </p>
            </div>
            <button
              type="button"
              class="inline-flex h-8 w-8 items-center justify-center rounded-md bg-emerald-500 text-lg font-bold leading-none text-white shadow-sm transition hover:bg-emerald-600"
              @click="openStartConversationModal"
              title="Nova conversa"
              aria-label="Nova conversa"
            >
              +
            </button>
          </div>
          <p class="mt-1 text-xs text-slate-500">Atendimento WhatsApp em tempo real</p>
          <input
            v-model="search"
            type="text"
            placeholder="Buscar conversa..."
            class="mt-3 w-full rounded-2xl border border-slate-200/80 bg-white px-3.5 py-2.5 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
          />
          <div class="mt-3 flex flex-wrap items-center gap-5">
            <label class="inline-flex items-center gap-2 text-[11px] font-semibold text-slate-600">
              <span>Notificações</span>
              <span class="relative inline-flex h-5 w-9 items-center">
                <input v-model="floatingNotificationsEnabled" type="checkbox" class="peer sr-only" />
                <span class="absolute inset-0 rounded-full bg-slate-300 transition peer-checked:bg-emerald-500"></span>
                <span class="absolute left-0.5 h-4 w-4 rounded-full bg-white shadow transition peer-checked:translate-x-4"></span>
              </span>
            </label>
            <label class="inline-flex items-center gap-2 text-[11px] font-semibold text-slate-600">
              <span>Som</span>
              <span class="relative inline-flex h-5 w-9 items-center">
                <input v-model="floatingNotificationSoundEnabled" type="checkbox" class="peer sr-only" />
                <span class="absolute inset-0 rounded-full bg-slate-300 transition peer-checked:bg-emerald-500"></span>
                <span class="absolute left-0.5 h-4 w-4 rounded-full bg-white shadow transition peer-checked:translate-x-4"></span>
              </span>
            </label>
            <label class="inline-flex items-center gap-2 text-[11px] font-semibold text-slate-600">
              <span>Grupos</span>
              <span class="relative inline-flex h-5 w-9 items-center">
                <input v-model="hideGroupConversations" type="checkbox" class="peer sr-only" />
                <span class="absolute inset-0 rounded-full bg-slate-300 transition peer-checked:bg-emerald-500"></span>
                <span class="absolute left-0.5 h-4 w-4 rounded-full bg-white shadow transition peer-checked:translate-x-4"></span>
              </span>
            </label>
          </div>
          <div class="mt-3">
            <div class="grid grid-cols-3 items-end">
              <button
                type="button"
                class="pb-1 text-center text-[11px] font-semibold uppercase tracking-wide transition"
                :class="conversationTab === 'all' ? 'text-emerald-700' : 'text-slate-500 hover:text-slate-700'"
                @click="conversationTab = 'all'"
              >
                todos
              </button>
              <button
                type="button"
                class="pb-1 text-center text-[11px] font-semibold uppercase tracking-wide transition"
                :class="conversationTab === 'linked' ? 'text-emerald-700' : 'text-slate-500 hover:text-slate-700'"
                @click="conversationTab = 'linked'"
              >
                cliente
              </button>
              <button
                type="button"
                class="pb-1 text-center text-[11px] font-semibold uppercase tracking-wide transition"
                :class="conversationTab === 'unlinked' ? 'text-emerald-700' : 'text-slate-500 hover:text-slate-700'"
                @click="conversationTab = 'unlinked'"
              >
                não cliente
              </button>
            </div>
            <div class="grid grid-cols-3 gap-1">
              <div class="h-[2px] rounded-full transition" :class="conversationTab === 'all' ? 'bg-emerald-500' : 'bg-slate-200'"></div>
              <div class="h-[2px] rounded-full transition" :class="conversationTab === 'linked' ? 'bg-emerald-500' : 'bg-slate-200'"></div>
              <div class="h-[2px] rounded-full transition" :class="conversationTab === 'unlinked' ? 'bg-emerald-500' : 'bg-slate-200'"></div>
            </div>
          </div>
        </div>

        <div class="premium-scroll min-h-0 flex-1 overflow-y-auto">
          <div v-if="conversationsLoading" class="space-y-3 p-3">
            <div v-for="n in 7" :key="n" class="h-16 animate-pulse rounded-xl bg-slate-100"></div>
          </div>
          <div v-else-if="filteredConversations.length === 0" class="p-6 text-center text-sm text-slate-500">
            Nenhuma conversa encontrada.
          </div>
          <button
            v-for="item in filteredConversations"
            :key="item.id"
            type="button"
            class="inbox-conversation group mx-2 my-1 w-[calc(100%-16px)] rounded-xl px-3 py-3 text-left transition-all duration-200"
            :class="{ 'is-selected': selectedConversationId === item.id }"
            @click="selectConversation(item.id)"
          >
            <div class="flex items-start gap-3">
              <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-100 text-sm font-semibold text-slate-700">
                <img
                  v-if="item.avatarUrl"
                  :src="item.avatarUrl"
                  :alt="titleForConversation(item)"
                  class="h-full w-full object-cover"
                  loading="lazy"
                  @error="onAvatarError(item)"
                />
                <span v-else class="avatar-fallback">{{ avatarInitial(item) }}</span>
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-2">
                  <p class="flex min-w-0 items-center gap-1.5 truncate text-sm font-semibold text-slate-900">
                    <span class="truncate">{{ titleForConversation(item) }}</span>
                    <span
                      v-if="isConversationMuted(item.id)"
                      class="inline-flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500"
                      title="Notificações silenciadas"
                    >
                      <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M10 5a2 2 0 0 1 4 0v1.4a6 6 0 0 0 1.7 4.2l1.1 1.2a1 1 0 0 1-.7 1.7H7.9a1 1 0 0 1-.7-1.7l1.1-1.2A6 6 0 0 0 10 6.4V5" />
                        <path d="M9 18a3 3 0 0 0 6 0" />
                        <path d="m4 4 16 16" />
                      </svg>
                    </span>
                  </p>
                  <p class="text-[11px] text-slate-500">{{ formatTime(item.lastMessageAt || item.updatedAt) }}</p>
                </div>
                <p class="mt-0.5 text-xs text-slate-500 leading-tight line-clamp-2">
                  <template v-if="groupPreviewSenderName(item)">
                    <strong class="font-semibold text-slate-700">{{ groupPreviewSenderName(item) }}</strong><br />
                    <span>{{ groupPreviewMessageText(item) }}</span>
                  </template>
                  <template v-else>{{ item.lastMessageText || "Sem mensagens" }}</template>
                </p>
                <div
                  v-if="item.clientId && ((item.openOpportunitiesCount || 0) > 0 || (item.openOpportunitiesValueCents || 0) > 0)"
                  class="mt-1 flex flex-wrap items-center gap-1.5"
                >
                  <span
                    v-if="(item.openOpportunitiesCount || 0) > 0"
                    class="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700"
                  >
                    {{ item.openOpportunitiesCount }} abertas
                  </span>
                  <span
                    v-if="(item.openOpportunitiesValueCents || 0) > 0"
                    class="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700"
                  >
                    {{ formatCurrency(item.openOpportunitiesValueCents) }}
                  </span>
                </div>
              </div>
              <span v-if="item.unreadCount > 0" class="inline-flex min-w-5 items-center justify-center rounded-full bg-emerald-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
                {{ item.unreadCount > 99 ? "99+" : item.unreadCount }}
              </span>
            </div>
          </button>
        </div>
      </aside>

      <section class="inbox-chat relative flex h-full min-h-0 flex-col overflow-hidden">
        <header class="inbox-chat-header flex items-center justify-between gap-3 border-b px-5 py-3.5 backdrop-blur-sm">
          <button
            v-if="isMobileViewport && isMobileChatOpen"
            type="button"
            class="rounded-lg border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-700 lg:hidden"
            @click="isMobileChatOpen = false"
          >
            Voltar
          </button>
          <div v-if="selectedConversation" class="min-w-0 flex items-center gap-3">
            <div class="flex h-11 w-11 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-slate-100 text-sm font-semibold text-slate-700 shadow-sm">
              <img
                v-if="selectedClientAvatarUrl"
                :src="selectedClientAvatarUrl"
                :alt="titleForConversation(selectedConversation)"
                class="h-full w-full object-cover"
              />
              <span v-else>{{ avatarInitial(selectedConversation) }}</span>
            </div>
            <div class="min-w-0">
              <p class="truncate text-[15px] font-semibold text-slate-900">{{ titleForConversation(selectedConversation) }}</p>
              <p class="truncate text-xs text-slate-500">{{ formatPhone(selectedConversation.remotePhone) }}</p>
              <p class="mt-0.5 inline-flex items-center gap-1 text-[11px] font-medium" :class="wsStatusClass">
                <span class="inline-flex h-1.5 w-1.5 rounded-full" :class="wsDotClass"></span>
                {{ wsStatusLabel }}
              </p>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500">Selecione uma conversa</div>
          <div class="header-menu-root relative hidden lg:block">
            <button
              type="button"
              class="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm transition hover:bg-slate-50"
              @click="toggleHeaderMenu"
            >
              ⋮
            </button>
            <div v-if="showHeaderMenu" class="absolute right-0 top-10 z-30 w-52 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg">
              <button
                type="button"
                class="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                :disabled="!selectedConversation"
                @click="openClientInfoModal"
              >
                Ver infos do cliente
              </button>
              <button
                type="button"
                class="mt-1 w-full rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                :disabled="!selectedConversation"
                @click="openRenameModal"
              >
                Editar nome
              </button>
              <button
                type="button"
                class="mt-1 w-full rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                :disabled="!selectedConversation"
                @click="toggleConversationMute"
              >
                {{ isSelectedConversationMuted ? "Reativar notificações" : "Silenciar notificações" }}
              </button>
            </div>
          </div>
        </header>

        <div ref="messagesScrollRef" class="premium-scroll chat-surface min-h-0 flex-1 overflow-y-auto px-5 py-6" @scroll="onMessagesScroll">
          <div v-if="messagesLoading && selectedConversation" class="space-y-3">
            <div v-for="n in 6" :key="n" class="h-12 animate-pulse rounded-xl bg-slate-100"></div>
          </div>
          <div v-else-if="!selectedConversation" class="flex h-full items-center justify-center">
            <div class="rounded-2xl border border-slate-200 bg-white px-6 py-5 text-center shadow-sm">
              <p class="text-sm font-semibold text-slate-800">Selecione uma conversa</p>
              <p class="mt-1 text-xs text-slate-500">As mensagens aparecerão aqui em tempo real.</p>
            </div>
          </div>
          <div v-else-if="selectedMessages.length === 0" class="flex h-full items-center justify-center">
            <div class="rounded-2xl border border-slate-200 bg-white px-6 py-5 text-center shadow-sm">
              <p class="text-sm font-semibold text-slate-800">Sem mensagens nesta conversa</p>
              <p class="mt-1 text-xs text-slate-500">Envie a primeira mensagem para iniciar o atendimento.</p>
            </div>
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="item in renderedMessageItems"
              :key="item.key"
            >
              <div v-if="item.type === 'divider'" class="my-1 flex items-center gap-3 px-2">
                <div class="h-px flex-1 bg-slate-200/80"></div>
                <span class="rounded-full bg-white/80 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                  {{ item.label }}
                </span>
                <div class="h-px flex-1 bg-slate-200/80"></div>
              </div>
              <div
                v-else
                class="flex"
                :class="item.message.direction === 'outbound' ? 'justify-end' : 'justify-start'"
              >
                <div
                  class="message-bubble max-w-[78%] rounded-[18px] px-4 py-3 text-[14px] shadow-[0_10px_24px_-16px_rgba(15,23,42,0.45)] transition-all duration-200"
                  :class="item.message.direction === 'outbound' ? 'message-bubble--outbound' : 'message-bubble--inbound'"
                >
                  <template v-if="item.message.mediaUrl">
                    <img
                      v-if="isImageMessage(item.message)"
                      :src="item.message.mediaUrl"
                      alt="Imagem"
                      class="mb-2 max-h-72 w-auto max-w-full cursor-zoom-in rounded-xl object-contain"
                      @click="openImageLightbox(item.message.mediaUrl)"
                      @load="onMessageMediaLoaded"
                    />
                    <video
                      v-else-if="isVideoMessage(item.message)"
                      :src="item.message.mediaUrl"
                      controls
                      class="mb-2 max-h-72 w-auto max-w-full rounded-xl"
                      @loadedmetadata="onMessageMediaLoaded"
                    />
                    <audio
                      v-else-if="isAudioMessage(item.message)"
                      :src="item.message.mediaUrl"
                      controls
                      preload="metadata"
                      class="audio-player mb-2"
                      @loadedmetadata="onMessageMediaLoaded"
                    />
                    <a
                      v-else
                      :href="item.message.mediaUrl"
                      target="_blank"
                      rel="noopener"
                      class="mb-2 block rounded-xl border px-3 py-2 text-xs underline"
                      :class="item.message.direction === 'outbound' ? 'border-emerald-300 text-white' : 'border-slate-200 text-slate-700'"
                    >
                      {{ item.message.mediaFileName || "Abrir documento" }}
                    </a>
                  </template>
                  <p v-if="!shouldHideBody(item.message)" class="whitespace-pre-wrap break-words leading-relaxed">
                    <template v-if="groupSenderName(item.message)">
                      <strong>{{ groupSenderName(item.message) }}</strong><br />
                      {{ groupMessageText(item.message) }}
                    </template>
                    <template v-else>{{ item.message.body }}</template>
                  </p>
                  <p class="mt-1.5 text-[10px]" :class="item.message.direction === 'outbound' ? 'text-emerald-100' : 'text-slate-500'">
                    {{ formatTime(item.message.createdAt || item.message.sentAt || item.message.receivedAt) }}
                    <span v-if="isTempMessage(item.message)"> · enviando...</span>
                    <span v-else-if="item.message.status === 'failed'"> · falhou</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <footer class="inbox-composer sticky bottom-0 z-10 border-t px-4 py-3 backdrop-blur-sm">
          <form class="inbox-composer-form relative flex items-end gap-2 rounded-2xl border p-2" @submit.prevent="sendMessage">
            <input ref="attachmentInputRef" type="file" class="hidden" accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar" @change="onAttachmentPicked" />
            <input ref="cameraInputRef" type="file" class="hidden" accept="image/*" capture="environment" @change="onCameraPicked" />
            <div class="relative">
              <button
                type="button"
                class="inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition hover:bg-slate-100"
                title="Emoji"
                @click="toggleEmojiPicker"
              >
                😊
              </button>
              <div
                v-if="showEmojiPicker"
                class="absolute bottom-11 left-0 z-30 w-[360px] rounded-2xl border border-slate-200 bg-white p-2.5 shadow-xl"
              >
                <div class="mb-2 px-1 text-[11px] font-semibold text-slate-500">Emojis</div>
                <div class="mb-2 flex items-center gap-1 overflow-x-auto pb-1">
                  <button
                    v-for="cat in emojiCategories"
                    :key="cat.key"
                    type="button"
                    class="inline-flex h-7 min-w-7 items-center justify-center rounded-lg px-1 text-sm transition"
                    :class="activeEmojiCategory === cat.key ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'"
                    @click="activeEmojiCategory = cat.key"
                    :title="cat.label"
                  >
                    {{ cat.icon }}
                  </button>
                </div>
                <div class="premium-scroll max-h-52 overflow-y-auto pr-1">
                  <div class="grid grid-cols-9 gap-1">
                  <button
                    v-for="emoji in displayedEmojis"
                    :key="emoji"
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-md text-lg transition hover:bg-slate-100"
                    @click="insertEmoji(emoji)"
                  >
                    {{ emoji }}
                  </button>
                  </div>
                </div>
              </div>
            </div>
            <textarea
              ref="messageInputRef"
              v-model="draft"
              rows="1"
              :disabled="!selectedConversation || sending || Boolean(attachmentFile)"
              placeholder="Digite uma mensagem..."
              class="max-h-28 min-h-[42px] flex-1 resize-none rounded-xl border border-slate-200/80 bg-slate-50 px-3 py-2 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 disabled:cursor-not-allowed disabled:bg-slate-100"
              @keydown.enter.exact.prevent="sendMessage"
              @keydown.enter.shift.exact.stop
              @input="autoResize"
              @focus="showEmojiPicker = false"
            />
            <button
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition hover:bg-slate-100"
              title="Câmera"
              :disabled="!selectedConversation || sending"
              @click="openCameraPicker"
            >
              📷
            </button>
            <button
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-xl transition hover:bg-slate-100"
              :class="isRecording ? 'text-rose-600' : 'text-slate-500'"
              :title="isRecording ? `Parar gravação (${formatRecordSeconds(recordSeconds)})` : 'Gravar áudio'"
              :disabled="!selectedConversation || sending"
              @click="toggleAudioRecording"
            >
              {{ isRecording ? "⏹️" : "🎤" }}
            </button>
            <button
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition hover:bg-slate-100"
              title="Anexo"
              :disabled="!selectedConversation || sending"
              @click="openAttachmentPicker"
            >
              📎
            </button>
            <button
              type="submit"
              class="h-[42px] rounded-xl bg-emerald-500 px-4 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-[1px] hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="!canSend"
            >
              {{ sending ? "Enviando..." : "Enviar" }}
            </button>
          </form>
          <div v-if="attachmentFile" class="mt-2 rounded-xl border border-slate-200 bg-slate-50 p-2.5">
            <div class="mb-2 flex items-center justify-between gap-3">
              <p class="truncate text-xs font-semibold text-slate-700">{{ attachmentFile.name }}</p>
              <button type="button" class="text-xs text-slate-500 hover:text-slate-700" @click="clearAttachment">Remover</button>
            </div>
            <img v-if="attachmentPreviewUrl && attachmentKind === 'image'" :src="attachmentPreviewUrl" alt="Preview" class="max-h-48 rounded-lg object-contain" />
            <video v-else-if="attachmentPreviewUrl && attachmentKind === 'video'" :src="attachmentPreviewUrl" controls class="max-h-48 rounded-lg" />
            <audio
              v-else-if="attachmentPreviewUrl && attachmentKind === 'audio'"
              :src="attachmentPreviewUrl"
              controls
              preload="metadata"
              class="audio-player"
            />
            <p v-else class="text-xs text-slate-500">Documento pronto para envio.</p>
            <input
              v-model="attachmentCaption"
              type="text"
              placeholder="Legenda (opcional)"
              class="mt-2 w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs outline-none focus:border-emerald-400"
            />
            <div class="mt-2 flex justify-end">
              <button
                type="button"
                class="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                :disabled="sending || !selectedConversation"
                @click="sendAttachment"
              >
                {{ sending ? "Enviando..." : "Enviar arquivo" }}
              </button>
            </div>
          </div>
        </footer>
      </section>

      <aside class="inbox-context-panel hidden h-full min-h-0 flex-col overflow-hidden border-l lg:flex">
        <div class="border-b border-slate-200/80 px-5 py-4">
          <h2 class="text-sm font-semibold text-slate-900">Oportunidades</h2>
        </div>
        <div class="premium-scroll min-h-0 flex-1 overflow-y-auto p-4">
          <div v-if="!selectedConversation" class="empty-state-wrap">
            <div class="empty-state-icon">💬</div>
            <p class="empty-state-title">Selecione uma conversa</p>
            <p class="empty-state-subtitle">As oportunidades vinculadas aparecerão aqui.</p>
          </div>
          <div v-else-if="panelLoading" class="space-y-3">
            <div class="h-5 animate-pulse rounded bg-slate-100"></div>
            <div class="h-5 animate-pulse rounded bg-slate-100"></div>
            <div class="h-5 animate-pulse rounded bg-slate-100"></div>
          </div>
          <div v-else>
            <div v-if="!selectedConversation.clientId" class="empty-state-wrap !min-h-[180px]">
              <div class="empty-state-icon">🔗</div>
              <p class="empty-state-title">Sem cliente vinculado</p>
              <p class="empty-state-subtitle">Vincule um cliente à conversa para gerenciar oportunidades aqui.</p>
              <button
                type="button"
                class="mt-3 inline-flex items-center rounded-xl bg-emerald-500 px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-600"
                @click="openManualLinkModal"
              >
                Vincular manualmente
              </button>
            </div>
            <div v-else class="space-y-3 text-sm">
              <div class="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
                <label class="text-xs uppercase tracking-wide text-slate-500">Selecionar oportunidade</label>
                <select
                  v-model.number="selectedOpportunityId"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
                >
                  <option :value="0" disabled>Selecione...</option>
                  <option v-for="opp in panelOpportunities" :key="opp.id" :value="opp.id">
                    {{ opportunityOptionLabel(opp) }}
                  </option>
                </select>
              </div>

              <template v-if="selectedPanelOpportunity">
                <div class="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
                  <p class="text-xs uppercase tracking-wide text-slate-500">Oportunidade</p>
                  <p class="mt-1 font-semibold text-slate-900">#{{ panelOpportunityView?.id || selectedPanelOpportunity.id }} · {{ panelOpportunityView?.opportunityName || selectedPanelOpportunity.opportunityName || "Sem nome" }}</p>
                </div>

                <div class="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-xs uppercase tracking-wide text-slate-500">Valor</p>
                    <button
                      v-if="!valueEditOpen"
                      type="button"
                      class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
                      :disabled="panelSaving"
                      @click="openValueEdit"
                      title="Editar valor"
                    >
                      ✎
                    </button>
                  </div>
                  <p v-if="!valueEditOpen" class="mt-1 font-semibold text-slate-900">{{ formatCurrency(panelOpportunityView?.estimatedValueCents) }}</p>
                  <div v-else class="mt-2 flex items-center gap-2">
                    <input
                      v-model="valueEditDraft"
                      type="text"
                      inputmode="decimal"
                      class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-900 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
                      placeholder="0,00"
                    />
                    <button
                      type="button"
                      class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
                      :disabled="valueEditSaving"
                      @click="cancelValueEdit"
                      title="Cancelar"
                    >
                      ✕
                    </button>
                    <button
                      type="button"
                      class="inline-flex h-8 w-8 items-center justify-center rounded-md bg-emerald-500 text-white transition hover:bg-emerald-600 disabled:opacity-50"
                      :disabled="valueEditSaving"
                      @click="saveValueEdit"
                      title="Salvar"
                    >
                      ✓
                    </button>
                  </div>
                </div>

                <div class="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
                  <label class="text-xs uppercase tracking-wide text-slate-500">Etapa (pipeline)</label>
                  <div class="stage-dropdown-root relative mt-2">
                    <button
                      ref="stageDropdownTriggerRef"
                      type="button"
                      class="flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-sm font-semibold outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 disabled:opacity-60"
                      :style="stageSelectButtonStyle"
                      :disabled="panelSaving || !leadStatuses.length"
                      @click="toggleStageDropdown"
                    >
                      <span class="truncate">{{ selectedStageOption?.name || "Sem etapa" }}</span>
                      <svg
                        viewBox="0 0 24 24"
                        class="ml-2 h-4 w-4 flex-shrink-0 transition-transform duration-150"
                        :class="stageDropdownOpen ? 'rotate-180' : 'rotate-0'"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path d="m6 9 6 6 6-6" />
                      </svg>
                    </button>
                  </div>
                </div>

                <div class="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
                  <label class="text-xs uppercase tracking-wide text-slate-500">Status comercial</label>
                  <div class="outcome-dropdown-root relative mt-2">
                    <button
                      ref="outcomeDropdownTriggerRef"
                      type="button"
                      class="flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-sm font-semibold outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 disabled:opacity-60"
                      :style="outcomeSelectStyle"
                      :disabled="panelSaving"
                      @click="toggleOutcomeDropdown"
                    >
                      <span class="truncate">{{ selectedOutcomeLabel }}</span>
                      <svg
                        viewBox="0 0 24 24"
                        class="ml-2 h-4 w-4 flex-shrink-0 transition-transform duration-150"
                        :class="outcomeDropdownOpen ? 'rotate-180' : 'rotate-0'"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path d="m6 9 6 6 6-6" />
                      </svg>
                    </button>
                  </div>
                </div>

                <div class="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
                  <p class="text-xs uppercase tracking-wide text-slate-500">Nota da oportunidade</p>
                  <textarea
                    v-model="opportunityNoteDraft"
                    rows="3"
                    class="mt-2 w-full resize-none rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
                    placeholder="Escreva uma nota..."
                  />
                  <div class="mt-2 flex justify-end">
                    <button
                      type="button"
                      class="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                      :disabled="!opportunityNoteDraft.trim() || opportunityNoteSaving"
                      @click="submitOpportunityNote"
                    >
                      {{ opportunityNoteSaving ? "Salvando..." : "Salvar nota" }}
                    </button>
                  </div>
                </div>

                <div class="rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
                  <p class="text-xs uppercase tracking-wide text-slate-500">Documentos</p>
                  <input ref="opportunityDocumentInputRef" type="file" class="hidden" @change="onOpportunityDocumentPicked" />
                  <button
                    type="button"
                    class="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 hover:shadow-sm disabled:opacity-50"
                    :disabled="opportunityDocumentUploading"
                    @click="openOpportunityDocumentPicker"
                  >
                    {{ opportunityDocumentUploading ? "Enviando documento..." : "Anexar documento" }}
                  </button>
                  <ul v-if="(panelOpportunityView?.documents || []).length" class="mt-3 space-y-1.5">
                    <li v-for="doc in panelOpportunityView?.documents || []" :key="doc.id">
                      <a :href="doc.fileUrl" target="_blank" rel="noopener" class="text-xs text-emerald-700 underline">
                        {{ doc.fileName }}
                      </a>
                    </li>
                  </ul>
                </div>
              </template>
              <div v-else class="rounded-2xl border border-slate-200/80 bg-white p-3 text-xs text-slate-500 shadow-sm">
                Nenhuma oportunidade disponível para este cliente.
              </div>
            </div>
            <div class="mt-5 space-y-2 rounded-2xl border border-slate-200/80 bg-white p-3 shadow-sm">
              <button
                type="button"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 hover:shadow-sm disabled:opacity-50"
                :disabled="!selectedOpportunityId || isGroupTarget(selectedConversation.remotePhone)"
                @click="goToOpportunity"
              >
                Abrir oportunidade
              </button>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <Teleport to="body">
      <div
        v-if="stageDropdownOpen"
        class="status-dropdown stage-dropdown-portal"
        :style="stageDropdownFloatingStyle"
      >
        <button
          type="button"
          class="status-option-badge"
          :style="stageOptionButtonStyle(null)"
          :disabled="panelSaving"
          @click.stop="setStageStatus(null)"
        >
          Sem etapa
        </button>
        <button
          v-for="status in leadStatuses"
          :key="status.id"
          type="button"
          class="status-option-badge"
          :style="stageOptionButtonStyle(status.color)"
          :disabled="panelSaving"
          @click.stop="setStageStatus(status.id)"
        >
          {{ status.name }}
        </button>
      </div>
    </Teleport>
    <Teleport to="body">
      <div
        v-if="outcomeDropdownOpen"
        class="status-dropdown outcome-dropdown-portal"
        :style="outcomeDropdownFloatingStyle"
      >
        <button type="button" class="status-option-badge" :style="outcomeOptionButtonStyle('open')" :disabled="panelSaving" @click.stop="setOutcomeStatus('open')">
          Aberta
        </button>
        <button type="button" class="status-option-badge" :style="outcomeOptionButtonStyle('won')" :disabled="panelSaving" @click.stop="setOutcomeStatus('won')">
          Ganha
        </button>
        <button type="button" class="status-option-badge" :style="outcomeOptionButtonStyle('lost')" :disabled="panelSaving" @click.stop="setOutcomeStatus('lost')">
          Perdida
        </button>
      </div>
    </Teleport>
    <Teleport to="body">
      <div
        v-if="toastMessage"
        class="app-snackbar-layer z-[200] rounded-full border px-4 py-2 text-sm font-semibold shadow-lg"
        :class="toastError ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'"
      >
        {{ toastMessage }}
      </div>
    </Teleport>
    <Teleport to="body">
      <div v-if="imageLightboxUrl" class="fixed inset-0 z-[300] flex items-center justify-center bg-slate-950/80 p-6" @click="closeImageLightbox">
        <button
          type="button"
          class="absolute right-5 top-5 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate-700"
          @click.stop="closeImageLightbox"
        >
          Fechar
        </button>
        <img
          :src="imageLightboxUrl"
          alt="Imagem ampliada"
          class="max-h-[90vh] max-w-[92vw] rounded-xl object-contain shadow-2xl"
          @click.stop
        />
      </div>
    </Teleport>
    <Teleport to="body">
      <div v-if="showClientInfoModal" class="fixed inset-0 z-[320] flex items-center justify-center bg-slate-950/45 p-4" @click="closeClientInfoModal">
        <div class="inbox-modal w-full max-w-md p-5" @click.stop>
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-slate-900">Infos do cliente</h3>
            <button type="button" class="rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100" @click="closeClientInfoModal">Fechar</button>
          </div>
          <div class="mt-4 flex flex-col items-center text-center">
            <div class="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-slate-100 text-base font-semibold text-slate-700">
              <img v-if="selectedClientAvatarUrl" :src="selectedClientAvatarUrl" alt="Avatar" class="h-full w-full object-cover" />
              <span v-else>{{ selectedConversation ? avatarInitial(selectedConversation) : "?" }}</span>
            </div>
            <div class="mt-2 min-w-0">
              <p class="truncate text-base font-semibold text-slate-900">{{ displayClientName }}</p>
              <p class="truncate text-xs text-slate-500">{{ displayClientPhone }}</p>
            </div>
          </div>
          <dl class="mt-4 grid grid-cols-1 gap-2 text-sm">
            <div class="rounded-xl border border-slate-200/80 bg-slate-50/60 px-3 py-2">
              <dt class="text-[11px] uppercase tracking-wide text-slate-500">Email</dt>
              <dd class="mt-1 inline-flex max-w-full items-center rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-700">
                <span class="truncate">{{ displayClientEmail }}</span>
              </dd>
            </div>
            <div class="rounded-xl border border-slate-200/80 bg-slate-50/60 px-3 py-2">
              <dt class="text-[11px] uppercase tracking-wide text-slate-500">Cliente desde</dt>
              <dd class="mt-1 inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                {{ displayClientSince }}
              </dd>
            </div>
            <div class="rounded-xl border border-slate-200/80 bg-slate-50/60 px-3 py-2">
              <dt class="text-[11px] uppercase tracking-wide text-slate-500">Total de oportunidades</dt>
              <dd class="mt-1 inline-flex items-center rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                {{ displayClientOpportunitiesCount }}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </Teleport>
    <Teleport to="body">
      <div v-if="showStartConversationModal" class="fixed inset-0 z-[320] flex items-center justify-center bg-slate-950/45 p-4" @click="closeStartConversationModal">
        <div class="inbox-modal w-full max-w-lg p-5" @click.stop>
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-slate-900">Iniciar nova conversa</h3>
            <button type="button" class="rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100" @click="closeStartConversationModal">Fechar</button>
          </div>
          <div class="mt-4 grid grid-cols-2 gap-2 rounded-xl border border-slate-200 bg-slate-50 p-1">
            <button type="button" class="rounded-lg px-3 py-2 text-sm font-semibold transition" :class="startConversationMode === 'client' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:bg-white/70'" @click="startConversationMode = 'client'">
              Escolher cliente
            </button>
            <button type="button" class="rounded-lg px-3 py-2 text-sm font-semibold transition" :class="startConversationMode === 'number' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:bg-white/70'" @click="startConversationMode = 'number'">
              Número manual
            </button>
          </div>

          <div v-if="startConversationMode === 'client'" class="mt-4 space-y-3">
            <div>
              <label class="text-xs uppercase tracking-wide text-slate-500">Buscar cliente</label>
              <input v-model="startConversationQuery" type="text" placeholder="Nome, telefone, email..." class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
            </div>
            <div>
              <label class="text-xs uppercase tracking-wide text-slate-500">Cliente</label>
              <select v-model.number="startConversationClientId" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" :disabled="startConversationSearching || !startConversationClientOptions.length">
                <option :value="0" disabled>Selecione um cliente...</option>
                <option v-for="item in startConversationClientOptions" :key="item.id" :value="item.id">
                  {{ item.name }}{{ item.phone ? ` · ${item.phone}` : "" }}
                </option>
              </select>
            </div>
          </div>
          <div v-else class="mt-4">
            <label class="text-xs uppercase tracking-wide text-slate-500">Número do WhatsApp</label>
            <input v-model="startConversationPhone" type="text" placeholder="Ex: 11999998888" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
            <label class="mt-3 block text-xs uppercase tracking-wide text-slate-500">Nome (opcional)</label>
            <input v-model="startConversationName" type="text" maxlength="120" placeholder="Ex: João Silva" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
          </div>

          <div class="mt-4 flex justify-end gap-2">
            <button
              v-if="canOpenWhatsWebConversation"
              type="button"
              class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700"
              @click="openConversationInWhatsWeb"
            >
              Abrir conversa
            </button>
            <button v-else type="button" class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700" @click="closeStartConversationModal">Cancelar</button>
            <button type="button" class="rounded-lg bg-emerald-500 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60" :disabled="startConversationCreating" @click="startConversation">
              {{ startConversationCreating ? "Enviando..." : "Enviar mensagem" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    <Teleport to="body">
      <div v-if="showManualLinkModal" class="fixed inset-0 z-[320] flex items-center justify-center bg-slate-950/45 p-4" @click="closeManualLinkModal">
        <div class="inbox-modal w-full max-w-lg p-5" @click.stop>
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-slate-900">Vincular cliente e oportunidade</h3>
            <button type="button" class="rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100" @click="closeManualLinkModal">Fechar</button>
          </div>

          <div class="mt-4 rounded-xl border border-slate-200 bg-slate-50/60 p-3">
            <label class="text-xs uppercase tracking-wide text-slate-500">Buscar cliente</label>
            <div class="mt-2 flex items-center gap-2">
              <input
                v-model="manualLinkQuery"
                type="text"
                placeholder="Nome, telefone, email..."
                class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
              />
              <button
                type="button"
                class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
                :disabled="manualLinkSearching || manualLinkQuery.trim().length < 2"
                @click="searchManualLinkClients"
              >
                {{ manualLinkSearching ? "Buscando..." : "Buscar" }}
              </button>
            </div>
          </div>

          <div class="mt-3">
            <label class="text-xs uppercase tracking-wide text-slate-500">Cliente</label>
            <select
              v-model.number="manualLinkClientId"
              class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
              :disabled="manualLinkSearching || !manualLinkClientOptions.length"
            >
              <option :value="0" disabled>Selecione um cliente...</option>
              <option v-for="item in manualLinkClientOptions" :key="item.id" :value="item.id">
                {{ item.name }}{{ item.phone ? ` · ${item.phone}` : "" }}
              </option>
            </select>
          </div>

          <div class="mt-3">
            <label class="text-xs uppercase tracking-wide text-slate-500">Oportunidade (opcional)</label>
            <select
              v-model.number="manualLinkOpportunityId"
              class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
              :disabled="manualLinkLoadingOpportunities || !manualLinkOpportunities.length"
            >
              <option :value="0">Sem oportunidade</option>
              <option v-for="opp in manualLinkOpportunities" :key="opp.id" :value="opp.id">
                {{ opportunityOptionLabel(opp) }}
              </option>
            </select>
            <p v-if="manualLinkLoadingOpportunities" class="mt-1 text-[11px] text-slate-500">Carregando oportunidades...</p>
          </div>

          <div class="mt-4 flex justify-end gap-2">
            <button type="button" class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700" @click="closeManualLinkModal">Cancelar</button>
            <button
              type="button"
              class="rounded-lg bg-emerald-500 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
              :disabled="manualLinkSaving || !manualLinkClientId"
              @click="saveManualLink"
            >
              {{ manualLinkSaving ? "Salvando..." : "Vincular" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    <Teleport to="body">
      <div v-if="showRenameModal" class="fixed inset-0 z-[320] flex items-center justify-center bg-slate-950/45 p-4" @click="closeRenameModal">
        <div class="inbox-modal w-full max-w-md p-5" @click.stop>
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-slate-900">Editar nome da conversa</h3>
            <button type="button" class="rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100" @click="closeRenameModal">Fechar</button>
          </div>
          <input
            v-model="renameDraft"
            type="text"
            maxlength="120"
            placeholder="Novo nome"
            class="mt-4 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
          />
          <div class="mt-4 flex justify-end gap-2">
            <button type="button" class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700" @click="closeRenameModal">Cancelar</button>
            <button
              type="button"
              class="rounded-lg bg-emerald-500 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
              :disabled="renameSaving || !renameDraft.trim()"
              @click="saveRename"
            >
              {{ renameSaving ? "Salvando..." : "Salvar nome" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";
import api from "../../services/api";
import { API_ROOT_URL } from "../../utils/apiBase";
import {
  ensureWhatsAppConversation,
  getWhatsAppUnreadCount,
  listWhatsAppConversations,
  listWhatsAppMessages,
  markWhatsAppConversationRead,
  sendWhatsAppMedia,
  sendWhatsAppText,
  updateWhatsAppConversation
} from "../../services/whatsapp";
import type { WhatsAppConversation, WhatsAppMessage } from "../../types/whatsapp";
import type { LeadDocument, LeadStatus, OpportunityDetails, OpportunityNote } from "../../types/leads";

type WsState = "connecting" | "connected" | "reconnecting" | "disconnected";
type MessageRenderItem =
  | { type: "divider"; key: string; label: string }
  | { type: "message"; key: string; message: WhatsAppMessage };

const router = useRouter();
const route = useRoute();
const agencyStore = useAgencyStore();
const authStore = useAuthStore();

const conversations = ref<WhatsAppConversation[]>([]);
const conversationsLoading = ref(false);
const selectedConversationId = ref<number | null>(null);
const messagesLoading = ref(false);
const messagesByConversation = ref<Record<number, WhatsAppMessage[]>>({});
const draft = ref("");
const attachmentFile = ref<File | null>(null);
const attachmentPreviewUrl = ref<string | null>(null);
const attachmentCaption = ref("");
const attachmentKind = ref<"image" | "video" | "audio" | "document">("document");
const cameraInputRef = ref<HTMLInputElement | null>(null);
const imageLightboxUrl = ref<string | null>(null);
const isRecording = ref(false);
const recordSeconds = ref(0);
const mediaRecorderRef = ref<MediaRecorder | null>(null);
const recordingStreamRef = ref<MediaStream | null>(null);
const recordingTimerRef = ref<ReturnType<typeof setInterval> | null>(null);
const showEmojiPicker = ref(false);
const activeEmojiCategory = ref("smileys");
const sending = ref(false);
const totalUnread = ref(0);
const search = ref("");
const conversationTab = ref<"all" | "linked" | "unlinked">("all");
const panelLoading = ref(false);
const panelOpportunities = ref<OpportunityDetails[]>([]);
const selectedOpportunityId = ref<number>(0);
const leadStatuses = ref<LeadStatus[]>([]);
const panelSaving = ref(false);
const selectedOpportunityDetails = ref<OpportunityDetails | null>(null);
const stageDropdownOpen = ref(false);
const stageDropdownTriggerRef = ref<HTMLElement | null>(null);
const stageDropdownFloatingStyle = ref<Record<string, string>>({});
const outcomeDropdownOpen = ref(false);
const outcomeDropdownTriggerRef = ref<HTMLElement | null>(null);
const outcomeDropdownFloatingStyle = ref<Record<string, string>>({});
const valueEditOpen = ref(false);
const valueEditDraft = ref("");
const valueEditSaving = ref(false);
const opportunityNoteDraft = ref("");
const opportunityNoteSaving = ref(false);
const opportunityDocumentUploading = ref(false);
const opportunityDocumentInputRef = ref<HTMLInputElement | null>(null);
const isMobileChatOpen = ref(false);
const isMobileViewport = ref(false);
const floatingNotificationsEnabled = ref(false);
const floatingNotificationSoundEnabled = ref(false);
const hideGroupConversations = ref(true);
const mutedConversationIds = ref<number[]>([]);

const wsState = ref<WsState>("disconnected");
const ws = ref<WebSocket | null>(null);
const reconnectTimer = ref<ReturnType<typeof setTimeout> | null>(null);

const toastMessage = ref("");
const toastError = ref(false);
const showHeaderMenu = ref(false);
const showClientInfoModal = ref(false);
const showStartConversationModal = ref(false);
const showManualLinkModal = ref(false);
const showRenameModal = ref(false);
const startConversationMode = ref<"client" | "number">("client");
const startConversationQuery = ref("");
const startConversationSearching = ref(false);
const startConversationClientOptions = ref<Array<{ id: number; name: string; phone?: string | null }>>([]);
const startConversationClientId = ref<number>(0);
const startConversationPhone = ref("");
const startConversationName = ref("");
const startConversationCreating = ref(false);
const renameDraft = ref("");
const renameSaving = ref(false);
const manualLinkQuery = ref("");
const manualLinkSearching = ref(false);
const manualLinkClientOptions = ref<Array<{ id: number; name: string; phone?: string | null }>>([]);
const manualLinkClientId = ref<number>(0);
const manualLinkOpportunities = ref<OpportunityDetails[]>([]);
const manualLinkOpportunityId = ref<number>(0);
const manualLinkLoadingOpportunities = ref(false);
const manualLinkSaving = ref(false);
const selectedClientProfile = ref<{
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  createdAt?: string | null;
  opportunitiesCount?: number | null;
} | null>(null);
let toastTimer: ReturnType<typeof setTimeout> | null = null;
let removeViewportListener: (() => void) | null = null;
let wsConnectTimeout: ReturnType<typeof setTimeout> | null = null;
let wsHeartbeatTimer: ReturnType<typeof setInterval> | null = null;
let wsReconnectToken = 0;
let wsIntentionalClose = false;
let inboxPollTimer: ReturnType<typeof setInterval> | null = null;
let removeOutsideEmojiListener: (() => void) | null = null;
let manualLinkSearchTimer: ReturnType<typeof setTimeout> | null = null;
let startConversationSearchTimer: ReturnType<typeof setTimeout> | null = null;
let removeStageDropdownPositionListeners: (() => void) | null = null;
let removeOutcomeDropdownPositionListeners: (() => void) | null = null;

const messagesScrollRef = ref<HTMLElement | null>(null);
const messageInputRef = ref<HTMLTextAreaElement | null>(null);
const attachmentInputRef = ref<HTMLInputElement | null>(null);
const userNearBottom = ref(true);
const emojiCategories: Array<{ key: string; label: string; icon: string; emojis: string[] }> = [
  {
    key: "smileys",
    label: "Carinhas",
    icon: "😀",
    emojis: ["😀","😁","😂","🤣","😃","😄","😅","😆","😉","😊","🙂","🙃","😍","😘","😗","😙","😚","😋","😛","😜","🤪","🤗","🤔","🫠","😎","🤩","🥳","😇","😴","🤤","😭","😤"]
  },
  {
    key: "people",
    label: "Pessoas",
    icon: "🧑",
    emojis: ["👍","👎","👌","👏","🙌","🙏","🤝","👋","✌️","🤟","💪","🫶","👀","🔥","❤️","🧡","💛","💚","💙","💜","🤍","🖤","💯","✅","❌","⚠️","💡","🎉","🎊","🚀","✨","💬"]
  },
  {
    key: "nature",
    label: "Natureza",
    icon: "🌿",
    emojis: ["🌞","🌝","⭐","🌈","☁️","🌧️","⚡","🔥","🌊","🍀","🌷","🌹","🌻","🌴","🌵","🍁","🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸","🐵","🦋"]
  },
  {
    key: "food",
    label: "Comidas",
    icon: "🍔",
    emojis: ["🍎","🍉","🍇","🍓","🍍","🥭","🍌","🍋","🍒","🥥","🥑","🥕","🌽","🍞","🧀","🥚","🍗","🍔","🍟","🍕","🌭","🥪","🌮","🌯","🍝","🍣","🍤","🍰","🍪","🍩","☕","🥤"]
  },
  {
    key: "activities",
    label: "Atividades",
    icon: "⚽",
    emojis: ["⚽","🏀","🏈","⚾","🎾","🏐","🎱","🏓","🏸","🥊","🥋","🎯","🎮","🕹️","🎲","🧩","🎼","🎤","🎧","🎷","🎸","🎹","🥁","🎬","📸","📷","🎥","📺","🧠","🧪","💻","📱"]
  },
  {
    key: "travel",
    label: "Viagens",
    icon: "✈️",
    emojis: ["🚗","🚕","🚌","🚎","🏎️","🚓","🚑","🚒","🚚","🚜","🏍️","🚲","✈️","🛫","🛬","🚀","🛸","🚢","⛵","🚤","🏝️","🏖️","🗽","🗼","🏰","🏙️","🌆","🌇","🗺️","📍","🧳","🏨"]
  },
  {
    key: "objects",
    label: "Objetos",
    icon: "📎",
    emojis: ["📱","💻","⌚","📷","📹","🎥","📞","☎️","📟","📠","🔋","🔌","💡","🕯️","🧯","🧲","💰","💳","🧾","📦","📄","📁","📌","📎","✂️","🔒","🔑","🛠️","⚙️","🧰","🧹","🗑️"]
  },
  {
    key: "symbols",
    label: "Símbolos",
    icon: "🔣",
    emojis: ["❤️","💔","❣️","💕","💞","💯","✅","☑️","✔️","❌","❗","❓","‼️","⚠️","🚫","⛔","🔔","🔕","♻️","🆗","🆒","🆕","🆙","🟢","🟡","🔴","⚫","⚪","⭐","🌟","✨","➕"]
  }
];
const displayedEmojis = computed(
  () => emojiCategories.find(cat => cat.key === activeEmojiCategory.value)?.emojis ?? emojiCategories[0].emojis
);

const agencyId = computed(() => agencyStore.currentAgencyId);
const floatingNotifStorageKey = computed(() => {
  const userId = authStore.user?.id || "anon";
  const currentAgencyId = agencyStore.currentAgencyId || "noagency";
  return `inbox-floating-notif:${userId}:${currentAgencyId}`;
});
const floatingNotifSoundStorageKey = computed(() => {
  const userId = authStore.user?.id || "anon";
  const currentAgencyId = agencyStore.currentAgencyId || "noagency";
  return `inbox-floating-sound:${userId}:${currentAgencyId}`;
});
const mutedConversationStorageKey = computed(() => {
  const userId = authStore.user?.id || "anon";
  const currentAgencyId = agencyStore.currentAgencyId || "noagency";
  return `inbox-muted-conversations:${userId}:${currentAgencyId}`;
});
const hideGroupConversationsStorageKey = computed(() => {
  const userId = authStore.user?.id || "anon";
  const currentAgencyId = agencyStore.currentAgencyId || "noagency";
  return `inbox-hide-groups:${userId}:${currentAgencyId}`;
});
const isConversationMuted = (conversationId: number | null | undefined) => {
  if (!conversationId) return false;
  return mutedConversationIds.value.includes(conversationId);
};
const isSelectedConversationMuted = computed(() => isConversationMuted(selectedConversationId.value));
const selectedConversation = computed(() => conversations.value.find(item => item.id === selectedConversationId.value) || null);
const selectedMessages = computed(() => {
  const id = selectedConversationId.value;
  if (!id) return [];
  return messagesByConversation.value[id] || [];
});
const renderedMessageItems = computed<MessageRenderItem[]>(() => {
  const items: MessageRenderItem[] = [];
  let previousLabel: string | null = null;
  for (const msg of selectedMessages.value) {
    const label = getDayDividerLabel(msg.createdAt || msg.sentAt || msg.receivedAt);
    if (label && label !== previousLabel) {
      items.push({ type: "divider", key: `divider-${label}-${msg.id}`, label });
      previousLabel = label;
    }
    items.push({ type: "message", key: `msg-${msg.id}`, message: msg });
  }
  return items;
});
const filteredConversations = computed(() => {
  const q = search.value.trim().toLowerCase();
  const ordered = [...conversations.value].sort((a, b) => {
    const t1 = new Date(a.lastMessageAt || a.updatedAt || a.createdAt || 0).getTime();
    const t2 = new Date(b.lastMessageAt || b.updatedAt || b.createdAt || 0).getTime();
    return t2 - t1;
  });
  const byTab = ordered.filter(item => {
    if (!hideGroupConversations.value && isGroupTarget(item.remotePhone)) return false;
    if (conversationTab.value === "linked") return Boolean(item.clientId);
    if (conversationTab.value === "unlinked") return !item.clientId;
    return true;
  });
  if (!q) return byTab;
  return byTab.filter(item =>
    titleForConversation(item).toLowerCase().includes(q) ||
    String(item.remotePhone || "").toLowerCase().includes(q) ||
    String(item.lastMessageText || "").toLowerCase().includes(q)
  );
});
const canSend = computed(() => Boolean(selectedConversation.value && draft.value.trim() && !sending.value && !attachmentFile.value));
const wsStatusLabel = computed(() => {
  if (wsState.value === "connected") return "Realtime conectado";
  if (wsState.value === "connecting") return "Conectando realtime...";
  if (wsState.value === "reconnecting") return "Reconectando realtime...";
  return "Realtime desconectado";
});
const wsStatusClass = computed(() => {
  if (wsState.value === "connected") return "text-emerald-600";
  if (wsState.value === "connecting" || wsState.value === "reconnecting") return "text-amber-600";
  return "text-rose-600";
});
const wsDotClass = computed(() => {
  if (wsState.value === "connected") return "bg-emerald-500";
  if (wsState.value === "connecting" || wsState.value === "reconnecting") return "bg-amber-500";
  return "bg-rose-500";
});

const selectedPanelOpportunity = computed(() => {
  if (!selectedOpportunityId.value) return null;
  return panelOpportunities.value.find(item => item.id === selectedOpportunityId.value) || null;
});
const panelOpportunityView = computed<OpportunityDetails | null>(() => {
  const selected = selectedPanelOpportunity.value;
  if (!selected) return null;
  if (selectedOpportunityDetails.value?.id === selected.id) return selectedOpportunityDetails.value;
  return selected;
});
const selectedStageOption = computed(() => {
  const id = Number(panelOpportunityView.value?.statusId || 0);
  if (!id) return null;
  return leadStatuses.value.find(item => item.id === id) || null;
});

const normalizeStatusColor = (value: string | null | undefined) => {
  const raw = String(value || "").trim();
  if (!raw) return "";
  if (!/^#?[0-9a-fA-F]{3,8}$/.test(raw)) return "";
  return raw.startsWith("#") ? raw : `#${raw}`;
};

const hexToRgba = (hex: string, alpha: number) => {
  const safe = normalizeStatusColor(hex).replace("#", "");
  if (!(safe.length === 3 || safe.length === 6)) return "";
  const full = safe.length === 3 ? safe.split("").map(ch => ch + ch).join("") : safe;
  const num = Number.parseInt(full, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const stageOptionButtonStyle = (statusColor: string | null | undefined): Record<string, string> => {
  const color = normalizeStatusColor(statusColor);
  if (!color) {
    return {
      borderColor: "#cbd5e1",
      backgroundColor: "#f1f5f9",
      color: "#475569"
    };
  }
  return {
    borderColor: `${color}66`,
    backgroundColor: hexToRgba(color, 0.16),
    color
  };
};

const stageSelectButtonStyle = computed<Record<string, string>>(() =>
  stageOptionButtonStyle(selectedStageOption.value?.color || panelOpportunityView.value?.statusColor || null)
);

const outcomeSelectStyle = computed<Record<string, string>>(() => {
  const outcome = panelOpportunityView.value?.closeOutcome || "open";
  if (outcome === "won") {
    return { borderColor: "#16a34a", backgroundColor: "rgba(22, 163, 74, 0.12)", color: "#166534" };
  }
  if (outcome === "lost") {
    return { borderColor: "#ef4444", backgroundColor: "rgba(239, 68, 68, 0.12)", color: "#991b1b" };
  }
  return { borderColor: "#475569", backgroundColor: "rgba(71, 85, 105, 0.08)", color: "#334155" };
});

const outcomeOptionStyle = (outcome: "open" | "won" | "lost"): Record<string, string> => {
  if (outcome === "won") return { color: "#166534", backgroundColor: "rgba(22, 163, 74, 0.12)" };
  if (outcome === "lost") return { color: "#991b1b", backgroundColor: "rgba(239, 68, 68, 0.12)" };
  return { color: "#334155", backgroundColor: "rgba(71, 85, 105, 0.08)" };
};
const selectedOutcomeLabel = computed(() => {
  const value = panelOpportunityView.value?.closeOutcome || "open";
  if (value === "won") return "Ganha";
  if (value === "lost") return "Perdida";
  return "Aberta";
});
const outcomeOptionButtonStyle = (outcome: "open" | "won" | "lost"): Record<string, string> => {
  const base = outcomeOptionStyle(outcome);
  const borderColor = outcome === "won" ? "#16a34a66" : outcome === "lost" ? "#ef444466" : "#47556966";
  return { ...base, borderColor };
};

const displayClientName = computed(() => {
  const conversationName = selectedConversation.value?.remoteName?.trim();
  return selectedClientProfile.value?.name?.trim() || conversationName || "Não informado";
});
const displayClientPhone = computed(() => {
  const profilePhone = selectedClientProfile.value?.phone;
  if (profilePhone?.trim()) return profilePhone.trim();
  return formatPhone(selectedConversation.value?.remotePhone);
});
const displayClientEmail = computed(() => {
  return selectedClientProfile.value?.email?.trim() || "—";
});
const selectedClientAvatarUrl = computed(() => selectedConversation.value?.avatarUrl || null);
const displayClientSince = computed(() => {
  const raw = selectedClientProfile.value?.createdAt;
  if (!raw) return "—";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("pt-BR");
});
const displayClientOpportunitiesCount = computed(() => {
  const total = selectedClientProfile.value?.opportunitiesCount;
  if (typeof total !== "number" || Number.isNaN(total)) return "—";
  return String(total);
});

const showToast = (message: string, isError = false) => {
  toastMessage.value = message;
  toastError.value = isError;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMessage.value = "";
    toastError.value = false;
  }, 2600);
};

const toggleHeaderMenu = () => {
  showHeaderMenu.value = !showHeaderMenu.value;
};

const openClientInfoModal = async () => {
  showHeaderMenu.value = false;
  showClientInfoModal.value = true;
  selectedClientProfile.value = null;
  const conversation = selectedConversation.value;
  if (!conversation?.clientId) return;
  try {
    const { data } = await api.get(`/clients/${conversation.clientId}`);
    selectedClientProfile.value = {
      name: data?.name ?? null,
      phone: data?.phone ?? null,
      email: data?.email ?? null,
      createdAt: data?.created_at ?? null,
      opportunitiesCount: typeof data?.opportunitiesCount === "number" ? data.opportunitiesCount : null
    };
  } catch {
    // best effort
  }
};

const closeClientInfoModal = () => {
  showClientInfoModal.value = false;
};

const normalizePhoneDigits = (value: string | null | undefined) => String(value || "").replace(/\D+/g, "");
const phoneComparable = (value: string | null | undefined) => {
  const digits = normalizePhoneDigits(value);
  if (digits.startsWith("55") && digits.length > 11) return digits.slice(2);
  return digits;
};
const normalizePhoneForWhatsApp = (value: string | null | undefined) => {
  const digits = normalizePhoneDigits(value);
  if (digits.length === 10 || digits.length === 11) return `55${digits}`;
  return digits;
};

const selectedStartConversationClient = computed(
  () => startConversationClientOptions.value.find(item => item.id === startConversationClientId.value) || null
);

const startConversationTargetPhone = computed(() => {
  if (startConversationMode.value === "client") {
    const digits = normalizePhoneForWhatsApp(selectedStartConversationClient.value?.phone);
    return digits.length >= 10 ? digits : "";
  }
  const digits = normalizePhoneForWhatsApp(startConversationPhone.value);
  return digits.length >= 10 ? digits : "";
});

const canOpenWhatsWebConversation = computed(() => Boolean(startConversationTargetPhone.value));

const openStartConversationModal = () => {
  showStartConversationModal.value = true;
  startConversationMode.value = "client";
  startConversationQuery.value = "";
  startConversationSearching.value = false;
  startConversationClientOptions.value = [];
  startConversationClientId.value = 0;
  startConversationPhone.value = "";
  startConversationName.value = "";
};

const closeStartConversationModal = () => {
  showStartConversationModal.value = false;
};

const openConversationInWhatsWeb = () => {
  const digits = startConversationTargetPhone.value;
  if (!digits) {
    showToast("Informe um número válido com DDD.", true);
    return;
  }
  window.open(`https://web.whatsapp.com/send?phone=${encodeURIComponent(digits)}`, "_blank", "noopener");
};

const searchStartConversationClients = async () => {
  if (!agencyId.value || startConversationQuery.value.trim().length < 2) return;
  startConversationSearching.value = true;
  try {
    const { data } = await api.get<Array<{ id: number; name: string; phone?: string | null }>>("/clients/search", {
      params: { agencyId: agencyId.value, q: startConversationQuery.value.trim() }
    });
    startConversationClientOptions.value = Array.isArray(data) ? data : [];
    if (!startConversationClientOptions.value.some(item => item.id === startConversationClientId.value)) {
      startConversationClientId.value = 0;
    }
  } catch {
    startConversationClientOptions.value = [];
    showToast("Erro ao buscar clientes.", true);
  } finally {
    startConversationSearching.value = false;
  }
};

const startConversation = async () => {
  if (!agencyId.value || startConversationCreating.value) return;
  startConversationCreating.value = true;
  try {
    if (startConversationMode.value === "client") {
      if (!startConversationClientId.value) {
        showToast("Selecione um cliente.", true);
        return;
      }
      const byClient = conversations.value.find(item => item.clientId === startConversationClientId.value);
      if (byClient) {
        closeStartConversationModal();
        await selectConversation(byClient.id);
        showToast("Conversa existente aberta.");
        return;
      }
      const selectedClient = startConversationClientOptions.value.find(item => item.id === startConversationClientId.value);
      const selectedClientDigits = normalizePhoneDigits(selectedClient?.phone);
      if (selectedClientDigits) {
        const byPhone = conversations.value.find(item => phoneComparable(item.remotePhone) === phoneComparable(selectedClientDigits));
        if (byPhone) {
          closeStartConversationModal();
          await selectConversation(byPhone.id);
          showToast("Conversa existente aberta.");
          return;
        }
      }
      const ensured = await ensureWhatsAppConversation(agencyId.value, { clientId: startConversationClientId.value });
      applyConversationUpdate(ensured);
      closeStartConversationModal();
      await selectConversation(ensured.id);
      showToast("Conversa aberta.");
      return;
    }

    const digits = normalizePhoneForWhatsApp(startConversationPhone.value);
    if (digits.length < 10) {
      showToast("Informe um número válido com DDD.", true);
      return;
    }
    const existing = conversations.value.find(item => phoneComparable(item.remotePhone) === phoneComparable(digits));
    if (existing) {
      closeStartConversationModal();
      await selectConversation(existing.id);
      showToast("Conversa existente aberta.");
      return;
    }
    const ensured = await ensureWhatsAppConversation(agencyId.value, { remotePhone: digits, remoteName: startConversationName.value.trim() || undefined });
    applyConversationUpdate(ensured);
    closeStartConversationModal();
    await selectConversation(ensured.id);
    showToast("Conversa aberta.");
  } catch {
    showToast("Erro ao iniciar conversa.", true);
  } finally {
    startConversationCreating.value = false;
  }
};

const openManualLinkModal = () => {
  showManualLinkModal.value = true;
  manualLinkQuery.value = selectedConversation.value?.remoteName || "";
  manualLinkClientOptions.value = [];
  manualLinkClientId.value = 0;
  manualLinkOpportunities.value = [];
  manualLinkOpportunityId.value = 0;
  if (manualLinkQuery.value.trim().length >= 2) {
    void searchManualLinkClients();
  }
};

const closeManualLinkModal = () => {
  showManualLinkModal.value = false;
};

const searchManualLinkClients = async () => {
  if (!agencyId.value || manualLinkQuery.value.trim().length < 2) return;
  manualLinkSearching.value = true;
  try {
    const { data } = await api.get<Array<{ id: number; name: string; phone?: string | null }>>("/clients/search", {
      params: { agencyId: agencyId.value, q: manualLinkQuery.value.trim() }
    });
    manualLinkClientOptions.value = Array.isArray(data) ? data : [];
    if (!manualLinkClientOptions.value.some(item => item.id === manualLinkClientId.value)) {
      manualLinkClientId.value = 0;
    }
  } catch {
    manualLinkClientOptions.value = [];
    showToast("Erro ao buscar clientes.", true);
  } finally {
    manualLinkSearching.value = false;
  }
};

const loadManualLinkOpportunities = async () => {
  if (!manualLinkClientId.value) {
    manualLinkOpportunities.value = [];
    manualLinkOpportunityId.value = 0;
    return;
  }
  manualLinkLoadingOpportunities.value = true;
  try {
    const { data } = await api.get<{ opportunities?: OpportunityDetails[] }>(`/clients/${manualLinkClientId.value}`);
    manualLinkOpportunities.value = Array.isArray(data?.opportunities) ? data.opportunities : [];
    if (!manualLinkOpportunities.value.some(item => item.id === manualLinkOpportunityId.value)) {
      manualLinkOpportunityId.value = 0;
    }
  } catch {
    manualLinkOpportunities.value = [];
    manualLinkOpportunityId.value = 0;
    showToast("Erro ao carregar oportunidades do cliente.", true);
  } finally {
    manualLinkLoadingOpportunities.value = false;
  }
};

const saveManualLink = async () => {
  const conversation = selectedConversation.value;
  if (!conversation || !agencyId.value || !manualLinkClientId.value || manualLinkSaving.value) return;
  manualLinkSaving.value = true;
  try {
    const updated = await updateWhatsAppConversation(conversation.id, agencyId.value, {
      clientId: manualLinkClientId.value,
      opportunityId: manualLinkOpportunityId.value || undefined
    });
    applyConversationUpdate(updated);
    selectedConversationId.value = updated.id;
    closeManualLinkModal();
    await loadSidePanel();
    showToast("Cliente vinculado com sucesso.");
  } catch {
    showToast("Erro ao vincular cliente/oportunidade.", true);
  } finally {
    manualLinkSaving.value = false;
  }
};

const openRenameModal = () => {
  showHeaderMenu.value = false;
  renameDraft.value = selectedConversation.value?.remoteName || "";
  showRenameModal.value = true;
};

const closeRenameModal = () => {
  showRenameModal.value = false;
};

const saveRename = async () => {
  const conversation = selectedConversation.value;
  if (!conversation || !agencyId.value || !renameDraft.value.trim() || renameSaving.value) return;
  renameSaving.value = true;
  try {
    const updated = await updateWhatsAppConversation(conversation.id, agencyId.value, {
      remoteName: renameDraft.value.trim()
    });
    applyConversationUpdate(updated);
    showRenameModal.value = false;
    showToast("Nome atualizado.");
  } catch {
    showToast("Erro ao salvar nome.", true);
  } finally {
    renameSaving.value = false;
  }
};

const formatTime = (value: string | null | undefined) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
};

const getDayDividerLabel = (value: string | null | undefined) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  const today = new Date();
  const startOf = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const diffDays = Math.floor((startOf(today) - startOf(date)) / 86400000);

  if (diffDays === 0) return "Hoje";
  if (diffDays === 1) return "Ontem";
  if (diffDays > 1 && diffDays < 7) {
    return date.toLocaleDateString("pt-BR", { weekday: "long" });
  }
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
};

const formatCurrency = (value: number | null | undefined) => {
  const cents = Number(value || 0);
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
};

const isGroupTarget = (raw: string | null | undefined) => String(raw || "").toLowerCase().endsWith("@g.us");

const formatPhone = (raw: string | null | undefined) => {
  if (isGroupTarget(raw)) return "Grupo WhatsApp";
  const digits = String(raw || "").replace(/\D+/g, "");
  if (!digits) return "—";
  const cc = digits.startsWith("55") ? "55" : "55";
  const local = digits.startsWith("55") ? digits.slice(2) : digits;
  const ddd = local.slice(0, 2);
  const prefix = local.slice(2, 7);
  const suffix = local.slice(7, 11);
  return `+${cc} ${ddd} ${prefix}-${suffix}`;
};

const titleForConversation = (item: WhatsAppConversation) =>
  item.remoteName?.trim() || (isGroupTarget(item.remotePhone) ? "Grupo WhatsApp" : formatPhone(item.remotePhone));
const avatarInitial = (item: WhatsAppConversation) => (titleForConversation(item).charAt(0) || "?").toUpperCase();
const isTempMessage = (msg: WhatsAppMessage) => String(msg.id).startsWith("tmp-");
const isImageMessage = (msg: WhatsAppMessage) =>
  msg.messageType?.toLowerCase().includes("image") || (msg.mediaMimeType || "").toLowerCase().startsWith("image/");
const isVideoMessage = (msg: WhatsAppMessage) =>
  msg.messageType?.toLowerCase().includes("video") || (msg.mediaMimeType || "").toLowerCase().startsWith("video/");
const isAudioMessage = (msg: WhatsAppMessage) =>
  msg.messageType?.toLowerCase().includes("audio") || (msg.mediaMimeType || "").toLowerCase().startsWith("audio/");
const shouldHideBody = (msg: WhatsAppMessage) => {
  if (!msg.mediaUrl) return false;
  const body = (msg.body || "").trim().toLowerCase();
  const placeholders = new Set([
    "📷 imagem",
    "🎥 vídeo",
    "🎥 video",
    "🎵 áudio",
    "🎵 audio",
    "📄 documento",
    "📎 arquivo",
  ]);
  return placeholders.has(body);
};

const parseGroupSenderMessage = (remotePhone: string | null | undefined, text: string | null | undefined) => {
  if (!isGroupTarget(remotePhone)) return null;
  const body = String(text || "");
  const match = body.match(/^\s*\[([^\]]+)\]\s*([\s\S]*)$/);
  if (!match) return null;
  const sender = String(match[1] || "").trim();
  if (!sender) return null;
  return {
    sender,
    text: String(match[2] || "")
  };
};

const groupSenderName = (msg: WhatsAppMessage) => parseGroupSenderMessage(selectedConversation.value?.remotePhone, msg.body)?.sender || "";
const groupMessageText = (msg: WhatsAppMessage) => parseGroupSenderMessage(selectedConversation.value?.remotePhone, msg.body)?.text || "";
const groupPreviewSenderName = (item: WhatsAppConversation) => parseGroupSenderMessage(item.remotePhone, item.lastMessageText)?.sender || "";
const groupPreviewMessageText = (item: WhatsAppConversation) => parseGroupSenderMessage(item.remotePhone, item.lastMessageText)?.text || "";

const onAvatarError = (item: WhatsAppConversation) => {
  item.avatarUrl = null;
};

const clearAttachment = () => {
  attachmentFile.value = null;
  attachmentCaption.value = "";
  attachmentKind.value = "document";
  if (attachmentPreviewUrl.value?.startsWith("blob:")) {
    URL.revokeObjectURL(attachmentPreviewUrl.value);
  }
  attachmentPreviewUrl.value = null;
  if (attachmentInputRef.value) {
    attachmentInputRef.value.value = "";
  }
};

const openImageLightbox = (url: string | null | undefined) => {
  if (!url) return;
  imageLightboxUrl.value = url;
};

const closeImageLightbox = () => {
  imageLightboxUrl.value = null;
};

const openAttachmentPicker = () => {
  attachmentInputRef.value?.click();
};

const openCameraPicker = () => {
  cameraInputRef.value?.click();
};

const onAttachmentPicked = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] || null;
  if (!file) return;
  clearAttachment();
  attachmentFile.value = file;
  const mime = (file.type || "").toLowerCase();
  if (mime.startsWith("image/")) attachmentKind.value = "image";
  else if (mime.startsWith("video/")) attachmentKind.value = "video";
  else if (mime.startsWith("audio/")) attachmentKind.value = "audio";
  else attachmentKind.value = "document";
  if (attachmentKind.value !== "document") {
    attachmentPreviewUrl.value = URL.createObjectURL(file);
  }
  draft.value = "";
};

const onCameraPicked = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] || null;
  if (!file) return;
  clearAttachment();
  attachmentFile.value = file;
  attachmentKind.value = "image";
  attachmentPreviewUrl.value = URL.createObjectURL(file);
  attachmentCaption.value = "";
  draft.value = "";
  input.value = "";
};

const stopRecordingResources = () => {
  if (recordingTimerRef.value) {
    clearInterval(recordingTimerRef.value);
    recordingTimerRef.value = null;
  }
  if (recordingStreamRef.value) {
    for (const track of recordingStreamRef.value.getTracks()) track.stop();
    recordingStreamRef.value = null;
  }
  mediaRecorderRef.value = null;
  isRecording.value = false;
};

const startAudioRecording = async () => {
  if (!navigator?.mediaDevices?.getUserMedia) {
    showToast("Seu navegador não suporta gravação de áudio.", true);
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const options: MediaRecorderOptions = MediaRecorder.isTypeSupported("audio/webm")
      ? { mimeType: "audio/webm" }
      : {};
    const recorder = new MediaRecorder(stream, options);
    const chunks: BlobPart[] = [];
    recorder.ondataavailable = evt => {
      if (evt.data && evt.data.size > 0) chunks.push(evt.data);
    };
    recorder.onstop = () => {
      const mimeType = recorder.mimeType || "audio/webm";
      const ext = mimeType.includes("ogg") ? "ogg" : "webm";
      const blob = new Blob(chunks, { type: mimeType });
      if (blob.size > 0) {
        clearAttachment();
        const file = new File([blob], `audio-${Date.now()}.${ext}`, { type: mimeType });
        attachmentFile.value = file;
        attachmentKind.value = "audio";
        attachmentPreviewUrl.value = URL.createObjectURL(file);
        attachmentCaption.value = "";
      }
      stopRecordingResources();
    };
    mediaRecorderRef.value = recorder;
    recordingStreamRef.value = stream;
    recordSeconds.value = 0;
    isRecording.value = true;
    recordingTimerRef.value = setInterval(() => {
      recordSeconds.value += 1;
    }, 1000);
    recorder.start();
  } catch {
    showToast("Não foi possível acessar o microfone.", true);
    stopRecordingResources();
  }
};

const stopAudioRecording = () => {
  const recorder = mediaRecorderRef.value;
  if (!recorder) return;
  if (recorder.state !== "inactive") recorder.stop();
};

const toggleAudioRecording = async () => {
  if (isRecording.value) {
    stopAudioRecording();
    return;
  }
  await startAudioRecording();
};

const formatRecordSeconds = (seconds: number) => {
  const m = String(Math.floor(seconds / 60)).padStart(2, "0");
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
};

const autoResize = () => {
  const input = messageInputRef.value;
  if (!input) return;
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 112)}px`;
};

const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value;
};

const insertEmoji = async (emoji: string) => {
  const input = messageInputRef.value;
  if (!input) {
    draft.value += emoji;
    showEmojiPicker.value = false;
    return;
  }
  const start = input.selectionStart ?? draft.value.length;
  const end = input.selectionEnd ?? draft.value.length;
  draft.value = `${draft.value.slice(0, start)}${emoji}${draft.value.slice(end)}`;
  showEmojiPicker.value = false;
  await nextTick();
  input.focus();
  const cursor = start + emoji.length;
  input.setSelectionRange(cursor, cursor);
  autoResize();
};

const isAtBottom = () => {
  const el = messagesScrollRef.value;
  if (!el) return true;
  return el.scrollHeight - el.scrollTop - el.clientHeight < 50;
};

const stickToBottom = (attempts = 4) => {
  const el = messagesScrollRef.value;
  if (!el) return;
  let count = 0;
  const apply = () => {
    const target = messagesScrollRef.value;
    if (!target) return;
    target.scrollTop = target.scrollHeight;
    count += 1;
    if (count < attempts) requestAnimationFrame(apply);
  };
  requestAnimationFrame(apply);
};

const scrollToBottom = async (force = false) => {
  await nextTick();
  const el = messagesScrollRef.value;
  if (!el) return;
  if (!force && !userNearBottom.value) return;
  el.scrollTop = el.scrollHeight;
  stickToBottom(force ? 6 : 3);
};

const onMessagesScroll = () => {
  userNearBottom.value = isAtBottom();
};

const onMessageMediaLoaded = () => {
  void scrollToBottom(true);
};

const applyConversationUpdate = (incoming: WhatsAppConversation) => {
  const idx = conversations.value.findIndex(item => item.id === incoming.id);
  if (idx === -1) {
    conversations.value = [incoming, ...conversations.value];
  } else {
    const next = [...conversations.value];
    next[idx] = { ...next[idx], ...incoming };
    conversations.value = next;
  }
};

const loadConversations = async () => {
  if (!agencyId.value) return;
  conversationsLoading.value = true;
  try {
    conversations.value = await listWhatsAppConversations(agencyId.value);
    const unread = await getWhatsAppUnreadCount(agencyId.value);
    totalUnread.value = Number(unread.total_unread || 0);
    if (!selectedConversationId.value && conversations.value.length) {
      selectedConversationId.value = conversations.value[0].id;
    }
  } catch {
    showToast("Erro ao carregar conversas.", true);
  } finally {
    conversationsLoading.value = false;
  }
};

const pollConversationsFallback = async () => {
  if (!agencyId.value || conversationsLoading.value) return;
  try {
    const rows = await listWhatsAppConversations(agencyId.value);
    const byId = new Map(conversations.value.map(item => [item.id, item]));
    let changed = false;
    for (const row of rows) {
      const prev = byId.get(row.id);
      if (!prev) {
        changed = true;
        break;
      }
      if (
        prev.lastMessageAt !== row.lastMessageAt ||
        prev.lastMessageText !== row.lastMessageText ||
        prev.unreadCount !== row.unreadCount
      ) {
        changed = true;
        break;
      }
    }
    if (changed || rows.length !== conversations.value.length) {
      conversations.value = rows;
      if (selectedConversationId.value) {
        const active = rows.find(item => item.id === selectedConversationId.value) || null;
        const prev = byId.get(selectedConversationId.value);
        const needsReload =
          !prev ||
          !active ||
          prev.lastMessageAt !== active.lastMessageAt ||
          prev.lastMessageText !== active.lastMessageText;
        if (needsReload && active) {
          await loadMessages(active.id, true);
        }
      }
      const unread = await getWhatsAppUnreadCount(agencyId.value);
      totalUnread.value = Number(unread.total_unread || 0);
    }
  } catch {
    // fallback silencioso
  }
};

const startInboxPolling = () => {
  if (inboxPollTimer) clearInterval(inboxPollTimer);
  inboxPollTimer = setInterval(() => {
    void pollConversationsFallback();
  }, 5000);
};

const stopInboxPolling = () => {
  if (inboxPollTimer) {
    clearInterval(inboxPollTimer);
    inboxPollTimer = null;
  }
};

const loadMessages = async (conversationId: number, forceScroll = true) => {
  if (!agencyId.value) return;
  messagesLoading.value = true;
  try {
    const rows = await listWhatsAppMessages(conversationId, agencyId.value);
    messagesByConversation.value = { ...messagesByConversation.value, [conversationId]: rows };
    await scrollToBottom(forceScroll);
  } catch {
    showToast("Erro ao carregar mensagens.", true);
  } finally {
    messagesLoading.value = false;
  }
};

const loadSidePanel = async () => {
  panelOpportunities.value = [];
  selectedOpportunityId.value = 0;
  leadStatuses.value = [];
  selectedOpportunityDetails.value = null;
  opportunityNoteDraft.value = "";
  const conversation = selectedConversation.value;
  if (!conversation) return;
  panelLoading.value = true;
  try {
    if (agencyId.value) {
      const { data } = await api.get<LeadStatus[]>("/lead-forms/statuses", {
        params: { agencyId: agencyId.value }
      });
      leadStatuses.value = Array.isArray(data) ? data : [];
    }
    if (conversation.clientId) {
      const { data } = await api.get<{ opportunities?: OpportunityDetails[] }>(`/clients/${conversation.clientId}`);
      const opportunities: OpportunityDetails[] = Array.isArray(data?.opportunities) ? data.opportunities : [];
      panelOpportunities.value = opportunities;
      if (conversation.opportunityId && opportunities.some(item => item.id === conversation.opportunityId)) {
        selectedOpportunityId.value = conversation.opportunityId;
      } else if (opportunities.length > 0) {
        selectedOpportunityId.value = opportunities[0].id;
      }
    }
  } catch {
    panelOpportunities.value = [];
    selectedOpportunityId.value = 0;
  } finally {
    panelLoading.value = false;
  }
};

const loadSelectedOpportunityDetails = async () => {
  const selected = selectedPanelOpportunity.value;
  if (!selected) {
    selectedOpportunityDetails.value = null;
    return;
  }
  try {
    const { data } = await api.get<OpportunityDetails>(`/lead-forms/contacts/${selected.id}/details`);
    selectedOpportunityDetails.value = data;
    panelOpportunities.value = panelOpportunities.value.map(item => (item.id === data.id ? { ...item, ...data } : item));
  } catch {
    selectedOpportunityDetails.value = selected;
  }
};

const opportunityOptionLabel = (opp: OpportunityDetails) => {
  const id = `#${opp.id}`;
  const name = (opp.opportunityName || "Sem nome").trim();
  const value = formatCurrency(opp.estimatedValueCents);
  return `${id} · ${name} · ${value}`;
};

const formatCentsToInput = (value: number | null | undefined) => {
  const cents = Math.max(0, Number(value || 0));
  const brl = (cents / 100).toFixed(2);
  return brl.replace(".", ",");
};

const parseInputToCents = (value: string) => {
  const normalized = String(value || "")
    .trim()
    .replace(/\s+/g, "")
    .replace(/\./g, "")
    .replace(",", ".");
  const asNumber = Number(normalized);
  if (!Number.isFinite(asNumber) || asNumber <= 0) return 0;
  return Math.round(asNumber * 100);
};

const openValueEdit = () => {
  valueEditDraft.value = formatCentsToInput(panelOpportunityView.value?.estimatedValueCents);
  valueEditOpen.value = true;
};

const cancelValueEdit = () => {
  valueEditOpen.value = false;
  valueEditDraft.value = "";
};

const saveValueEdit = async () => {
  const selected = selectedPanelOpportunity.value;
  if (!selected || valueEditSaving.value) return;
  const nextValueCents = parseInputToCents(valueEditDraft.value);
  const currentValueCents = Number(selected.estimatedValueCents || 0);
  if (nextValueCents === currentValueCents) {
    cancelValueEdit();
    return;
  }
  valueEditSaving.value = true;
  panelSaving.value = true;
  try {
    const { data } = await api.patch<OpportunityDetails>(`/lead-forms/contacts/${selected.id}`, {
      estimatedValueCents: nextValueCents
    });
    panelOpportunities.value = panelOpportunities.value.map(item => (item.id === selected.id ? data : item));
    selectedOpportunityDetails.value = data;
    cancelValueEdit();
    showToast("Valor atualizado.");
  } catch {
    showToast("Erro ao atualizar valor.", true);
  } finally {
    valueEditSaving.value = false;
    panelSaving.value = false;
  }
};

const setStageStatus = async (nextStatusId: number | null) => {
  const selected = selectedPanelOpportunity.value;
  stageDropdownOpen.value = false;
  if (removeStageDropdownPositionListeners) {
    removeStageDropdownPositionListeners();
    removeStageDropdownPositionListeners = null;
  }
  if (!selected) return;
  const currentStatusId = Number(selected.statusId || 0) || null;
  const targetStatusId = nextStatusId ? Number(nextStatusId) : null;
  if (currentStatusId === targetStatusId) return;
  panelSaving.value = true;
  try {
    const { data } = await api.patch<OpportunityDetails>(`/lead-forms/contacts/${selected.id}`, {
      statusId: targetStatusId
    });
    panelOpportunities.value = panelOpportunities.value.map(item => (item.id === selected.id ? data : item));
    selectedOpportunityDetails.value = data;
    showToast("Etapa atualizada.");
  } catch {
    showToast("Erro ao atualizar etapa.", true);
  } finally {
    panelSaving.value = false;
  }
};

const toggleStageDropdown = () => {
  if (panelSaving.value || !leadStatuses.value.length) return;
  if (stageDropdownOpen.value) {
    stageDropdownOpen.value = false;
    if (removeStageDropdownPositionListeners) {
      removeStageDropdownPositionListeners();
      removeStageDropdownPositionListeners = null;
    }
    return;
  }
  stageDropdownOpen.value = true;
  const syncStageDropdownPosition = () => {
    const el = stageDropdownTriggerRef.value;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    stageDropdownFloatingStyle.value = {
      top: `${rect.bottom + 6}px`,
      left: `${rect.left}px`,
      width: `${rect.width}px`,
      zIndex: "400"
    };
  };
  syncStageDropdownPosition();
  const onMove = () => syncStageDropdownPosition();
  window.addEventListener("resize", onMove);
  window.addEventListener("scroll", onMove, true);
  removeStageDropdownPositionListeners = () => {
    window.removeEventListener("resize", onMove);
    window.removeEventListener("scroll", onMove, true);
  };
};

const setOutcomeStatus = async (nextOutcomeRaw: "open" | "won" | "lost") => {
  const selected = selectedPanelOpportunity.value;
  outcomeDropdownOpen.value = false;
  if (removeOutcomeDropdownPositionListeners) {
    removeOutcomeDropdownPositionListeners();
    removeOutcomeDropdownPositionListeners = null;
  }
  if (!selected) return;
  const nextOutcome = nextOutcomeRaw === "open" ? null : nextOutcomeRaw;
  if ((selected.closeOutcome || null) === nextOutcome) return;
  panelSaving.value = true;
  try {
    const { data } = await api.patch<OpportunityDetails>(`/lead-forms/contacts/${selected.id}`, {
      closeOutcome: nextOutcome
    });
    panelOpportunities.value = panelOpportunities.value.map(item => (item.id === selected.id ? data : item));
    selectedOpportunityDetails.value = data;
    showToast("Status comercial atualizado.");
  } catch {
    showToast("Erro ao atualizar status.", true);
  } finally {
    panelSaving.value = false;
  }
};

const toggleOutcomeDropdown = () => {
  if (panelSaving.value) return;
  if (outcomeDropdownOpen.value) {
    outcomeDropdownOpen.value = false;
    if (removeOutcomeDropdownPositionListeners) {
      removeOutcomeDropdownPositionListeners();
      removeOutcomeDropdownPositionListeners = null;
    }
    return;
  }
  outcomeDropdownOpen.value = true;
  const syncOutcomeDropdownPosition = () => {
    const el = outcomeDropdownTriggerRef.value;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    outcomeDropdownFloatingStyle.value = {
      top: `${rect.bottom + 6}px`,
      left: `${rect.left}px`,
      width: `${rect.width}px`,
      zIndex: "400"
    };
  };
  syncOutcomeDropdownPosition();
  const onMove = () => syncOutcomeDropdownPosition();
  window.addEventListener("resize", onMove);
  window.addEventListener("scroll", onMove, true);
  removeOutcomeDropdownPositionListeners = () => {
    window.removeEventListener("resize", onMove);
    window.removeEventListener("scroll", onMove, true);
  };
};

const submitOpportunityNote = async () => {
  const selected = selectedPanelOpportunity.value;
  const content = opportunityNoteDraft.value.trim();
  if (!selected || !content || opportunityNoteSaving.value) return;
  opportunityNoteSaving.value = true;
  try {
    await api.post<OpportunityNote>(`/lead-forms/contacts/${selected.id}/notes`, { content });
    opportunityNoteDraft.value = "";
    await loadSelectedOpportunityDetails();
    showToast("Nota adicionada.");
  } catch {
    showToast("Erro ao adicionar nota.", true);
  } finally {
    opportunityNoteSaving.value = false;
  }
};

const openOpportunityDocumentPicker = () => {
  if (!selectedPanelOpportunity.value || opportunityDocumentUploading.value) return;
  opportunityDocumentInputRef.value?.click();
};

const onOpportunityDocumentPicked = async (event: Event) => {
  const selected = selectedPanelOpportunity.value;
  const input = event.target as HTMLInputElement | null;
  const file = input?.files?.[0] || null;
  if (!selected || !file) return;
  opportunityDocumentUploading.value = true;
  try {
    const form = new FormData();
    form.append("file", file);
    await api.post<LeadDocument>(`/lead-forms/contacts/${selected.id}/documents`, form, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    await loadSelectedOpportunityDetails();
    showToast("Documento anexado.");
  } catch {
    showToast("Erro ao anexar documento.", true);
  } finally {
    if (input) input.value = "";
    opportunityDocumentUploading.value = false;
  }
};

const markReadIfNeeded = async (conversation: WhatsAppConversation | null) => {
  if (!agencyId.value || !conversation) return;
  if ((conversation.unreadCount || 0) <= 0) return;
  try {
    await markWhatsAppConversationRead(conversation.id, agencyId.value);
    const idx = conversations.value.findIndex(item => item.id === conversation.id);
    if (idx >= 0) {
      const next = [...conversations.value];
      const oldUnread = Number(next[idx].unreadCount || 0);
      next[idx] = { ...next[idx], unreadCount: 0 };
      conversations.value = next;
      totalUnread.value = Math.max(0, totalUnread.value - oldUnread);
    }
  } catch {
    // best effort
  }
};

const selectConversation = async (id: number) => {
  selectedConversationId.value = id;
  isMobileChatOpen.value = true;
  userNearBottom.value = true;
  if (!messagesByConversation.value[id]) {
    await loadMessages(id, true);
  } else {
    await scrollToBottom(true);
  }
  await markReadIfNeeded(selectedConversation.value);
  await loadSidePanel();
};

const sendAttachment = async () => {
  if (!agencyId.value || !selectedConversation.value || !attachmentFile.value || sending.value) return;
  const conversationId = selectedConversation.value.id;
  const file = attachmentFile.value;
  const caption = attachmentCaption.value.trim();
  sending.value = true;
  try {
    const sent = await sendWhatsAppMedia(conversationId, agencyId.value, file, caption);
    const current = messagesByConversation.value[conversationId] || [];
    messagesByConversation.value = { ...messagesByConversation.value, [conversationId]: [...current, sent] };
    const idx = conversations.value.findIndex(item => item.id === conversationId);
    if (idx >= 0) {
      const next = [...conversations.value];
      next[idx] = {
        ...next[idx],
        lastMessageText: sent.body,
        lastMessageAt: sent.createdAt || sent.sentAt || new Date().toISOString()
      };
      conversations.value = next;
    }
    clearAttachment();
    await scrollToBottom(true);
  } catch {
    showToast("Erro ao enviar arquivo.", true);
  } finally {
    sending.value = false;
  }
};

const sendMessage = async () => {
  if (!canSend.value || !agencyId.value || !selectedConversation.value) return;
  const text = draft.value.trim();
  const conversationId = selectedConversation.value.id;
  const tempId = `tmp-${Date.now()}`;
  const optimistic: WhatsAppMessage = {
    id: tempId as unknown as number,
    agencyId: selectedConversation.value.agencyId,
    connectionId: selectedConversation.value.connectionId,
    conversationId,
    externalMessageId: null,
    direction: "outbound",
    messageType: "text",
    body: text,
    status: "pending",
    remotePhone: selectedConversation.value.remotePhone,
    sentAt: new Date().toISOString(),
    receivedAt: null,
    createdAt: new Date().toISOString()
  };
  const current = messagesByConversation.value[conversationId] || [];
  messagesByConversation.value = { ...messagesByConversation.value, [conversationId]: [...current, optimistic] };
  draft.value = "";
  autoResize();
  userNearBottom.value = true;
  await scrollToBottom(true);
  sending.value = true;
  try {
    const sent = await sendWhatsAppText(conversationId, agencyId.value, text);
    const list = (messagesByConversation.value[conversationId] || []).map(msg => (msg.id === (tempId as unknown as number) ? sent : msg));
    messagesByConversation.value = { ...messagesByConversation.value, [conversationId]: list };
    const idx = conversations.value.findIndex(item => item.id === conversationId);
    if (idx >= 0) {
      const next = [...conversations.value];
      next[idx] = { ...next[idx], lastMessageText: text, lastMessageAt: sent.createdAt || new Date().toISOString() };
      conversations.value = next;
    }
    await scrollToBottom(true);
  } catch {
    const list = (messagesByConversation.value[conversationId] || []).map(msg =>
      msg.id === (tempId as unknown as number) ? { ...msg, status: "failed" } : msg
    );
    messagesByConversation.value = { ...messagesByConversation.value, [conversationId]: list };
    showToast("Erro ao enviar mensagem.", true);
  } finally {
    sending.value = false;
  }
};

const handleRealtimeMessage = async (message: WhatsAppMessage, conversationId: number) => {
  const current = messagesByConversation.value[conversationId] || [];
  if (!current.some(item => String(item.id) === String(message.id))) {
    const isActiveConversation = selectedConversationId.value === conversationId;
    messagesByConversation.value = { ...messagesByConversation.value, [conversationId]: [...current, message] };
    if (isActiveConversation) {
      await scrollToBottom(true);
    }
  }
};

const handleWsEvent = async (raw: MessageEvent) => {
  let payload: any = null;
  try {
    payload = JSON.parse(raw.data);
  } catch {
    return;
  }
  if (!payload?.type) return;
  if (payload.type === "whatsapp.message.created" && payload.message && payload.conversation_id) {
    await handleRealtimeMessage(payload.message, Number(payload.conversation_id));
    const idx = conversations.value.findIndex(item => item.id === Number(payload.conversation_id));
    if (idx >= 0) {
      const next = [...conversations.value];
      const item = next[idx];
      next[idx] = {
        ...item,
        lastMessageText: payload.message.body || item.lastMessageText,
        lastMessageAt: payload.message.createdAt || payload.message.sentAt || payload.message.receivedAt || new Date().toISOString(),
        unreadCount:
          payload.message.direction === "inbound" && selectedConversationId.value !== item.id
            ? Number(item.unreadCount || 0) + 1
            : item.unreadCount
      };
      conversations.value = next;
    } else if (agencyId.value) {
      await loadConversations();
    }
  } else if (payload.type === "whatsapp.conversation.updated" && payload.conversation) {
    applyConversationUpdate(payload.conversation as WhatsAppConversation);
    if (selectedConversationId.value === payload.conversation.id) {
      await markReadIfNeeded(payload.conversation as WhatsAppConversation);
    }
  } else if (payload.type === "whatsapp.unread_count.updated") {
    totalUnread.value = Number(payload.total_unread || 0);
  }
};

const buildWsUrl = () => {
  const token = authStore.token;
  if (!token || !agencyId.value) return null;
  const root = resolveWsApiRoot();
  const wsBase = root.replace(/^http/i, "ws");
  const url = new URL(`${wsBase}/api/v1/whatsapp/ws`);
  url.searchParams.set("token", token);
  url.searchParams.set("agencyId", String(agencyId.value));
  return url.toString();
};

const resolveWsApiRoot = () => {
  const devWsRoot = (import.meta.env.VITE_WS_API_ROOT || "").trim().replace(/\/$/, "");
  if (devWsRoot) return devWsRoot;
  if (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
    return "http://localhost:8000";
  }
  const configuredRoot = API_ROOT_URL.replace(/\/$/, "");
  if (typeof window === "undefined") return configuredRoot;
  try {
    const parsed = new URL(configuredRoot);
    if (parsed.host === window.location.host) return window.location.origin.replace(/\/$/, "");
  } catch {
    // noop
  }
  return configuredRoot;
};

const disconnectWs = () => {
  wsIntentionalClose = true;
  wsReconnectToken += 1;
  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value);
    reconnectTimer.value = null;
  }
  if (wsConnectTimeout) {
    clearTimeout(wsConnectTimeout);
    wsConnectTimeout = null;
  }
  if (ws.value) {
    ws.value.onclose = null;
    ws.value.onopen = null;
    ws.value.onerror = null;
    ws.value.onmessage = null;
    ws.value.close();
    ws.value = null;
  }
  if (wsHeartbeatTimer) {
    clearInterval(wsHeartbeatTimer);
    wsHeartbeatTimer = null;
  }
  wsState.value = "disconnected";
};

const connectWs = () => {
  const url = buildWsUrl();
  if (!url) return;
  const myToken = ++wsReconnectToken;
  wsIntentionalClose = false;
  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value);
    reconnectTimer.value = null;
  }
  if (wsConnectTimeout) {
    clearTimeout(wsConnectTimeout);
    wsConnectTimeout = null;
  }
  if (wsHeartbeatTimer) {
    clearInterval(wsHeartbeatTimer);
    wsHeartbeatTimer = null;
  }
  if (ws.value) {
    ws.value.onclose = null;
    ws.value.onopen = null;
    ws.value.onerror = null;
    ws.value.onmessage = null;
    try {
      ws.value.close();
    } catch {
      // noop
    }
    ws.value = null;
  }
  wsState.value = "connecting";
  const socket = new WebSocket(url);
  ws.value = socket;
  wsConnectTimeout = setTimeout(() => {
    if (myToken !== wsReconnectToken) return;
    if (wsState.value === "connecting") {
      try {
        socket.close();
      } catch {
        // noop
      }
      wsState.value = "reconnecting";
    }
  }, 5000);
  socket.onopen = () => {
    if (myToken !== wsReconnectToken) return;
    if (wsConnectTimeout) {
      clearTimeout(wsConnectTimeout);
      wsConnectTimeout = null;
    }
    wsState.value = "connected";
    wsHeartbeatTimer = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        try {
          socket.send("ping");
        } catch {
          // noop
        }
      }
    }, 20000);
  };
  socket.onmessage = evt => {
    if (myToken !== wsReconnectToken) return;
    try {
      const payload = JSON.parse(evt.data);
      if (payload?.type === "ws.ready") {
        wsState.value = "connected";
        return;
      }
    } catch {
      // noop
    }
    void handleWsEvent(evt);
  };
  socket.onclose = event => {
    if (myToken !== wsReconnectToken) return;
    if (wsConnectTimeout) {
      clearTimeout(wsConnectTimeout);
      wsConnectTimeout = null;
    }
    if (wsHeartbeatTimer) {
      clearInterval(wsHeartbeatTimer);
      wsHeartbeatTimer = null;
    }
    ws.value = null;
    if (wsIntentionalClose) {
      wsState.value = "disconnected";
      return;
    }
    if (event.code === 1008 || event.code === 1003) {
      wsState.value = "disconnected";
      showToast("Realtime bloqueado: sessão/permissão inválida. Atualize a página e faça login novamente.", true);
      return;
    }
    wsState.value = "reconnecting";
    reconnectTimer.value = setTimeout(() => {
      if (myToken !== wsReconnectToken) return;
      connectWs();
    }, 2500);
  };
  socket.onerror = () => {
    if (myToken !== wsReconnectToken) return;
    wsState.value = "reconnecting";
  };
};

const goToClient = () => {
  if (!selectedConversation.value?.clientId) return;
  router.push(`/admin/leads/clients/${selectedConversation.value.clientId}`);
};

const goToOpportunity = () => {
  if (!selectedOpportunityId.value) return;
  router.push(`/admin/leads/opportunities?opportunityId=${selectedOpportunityId.value}`);
};

const applyConversationIdFromQuery = async () => {
  const raw = route.query.conversationId;
  const parsed = Number(Array.isArray(raw) ? raw[0] : raw);
  if (!Number.isFinite(parsed) || parsed <= 0) return;
  const found = conversations.value.find(item => item.id === parsed);
  if (!found) return;
  await selectConversation(parsed);
};

const loadFloatingNotificationPreference = () => {
  try {
    floatingNotificationsEnabled.value = localStorage.getItem(floatingNotifStorageKey.value) === "1";
  } catch {
    floatingNotificationsEnabled.value = false;
  }
  try {
    floatingNotificationSoundEnabled.value = localStorage.getItem(floatingNotifSoundStorageKey.value) === "1";
  } catch {
    floatingNotificationSoundEnabled.value = false;
  }
};

const loadMutedConversations = () => {
  try {
    const raw = localStorage.getItem(mutedConversationStorageKey.value);
    if (!raw) {
      mutedConversationIds.value = [];
      return;
    }
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      mutedConversationIds.value = parsed
        .map(item => Number(item))
        .filter(value => Number.isFinite(value) && value > 0);
      return;
    }
    mutedConversationIds.value = [];
  } catch {
    mutedConversationIds.value = [];
  }
};

const loadHideGroupConversationsPreference = () => {
  try {
    const raw = localStorage.getItem(hideGroupConversationsStorageKey.value);
    hideGroupConversations.value = raw === null ? true : raw === "1";
  } catch {
    hideGroupConversations.value = true;
  }
};

const persistMutedConversations = () => {
  try {
    localStorage.setItem(mutedConversationStorageKey.value, JSON.stringify(mutedConversationIds.value));
  } catch {
    // ignore
  }
};

const toggleConversationMute = () => {
  const id = selectedConversationId.value;
  if (!id) return;
  showHeaderMenu.value = false;
  if (mutedConversationIds.value.includes(id)) {
    mutedConversationIds.value = mutedConversationIds.value.filter(item => item !== id);
    showToast("Notificações reativadas para esta conversa.");
  } else {
    mutedConversationIds.value = [...mutedConversationIds.value, id];
    showToast("Conversa silenciada.");
  }
  persistMutedConversations();
};

watch(
  () => agencyId.value,
  async value => {
    conversations.value = [];
    messagesByConversation.value = {};
    selectedConversationId.value = null;
    totalUnread.value = 0;
    disconnectWs();
    stopInboxPolling();
    if (!value) return;
    await loadConversations();
    await applyConversationIdFromQuery();
    connectWs();
    startInboxPolling();
  },
  { immediate: true }
);

watch(
  () => selectedConversationId.value,
  async value => {
    stageDropdownOpen.value = false;
    outcomeDropdownOpen.value = false;
    if (removeStageDropdownPositionListeners) {
      removeStageDropdownPositionListeners();
      removeStageDropdownPositionListeners = null;
    }
    if (removeOutcomeDropdownPositionListeners) {
      removeOutcomeDropdownPositionListeners();
      removeOutcomeDropdownPositionListeners = null;
    }
    cancelValueEdit();
    if (!value) return;
    if (!messagesByConversation.value[value]) {
      await loadMessages(value, true);
    }
    await markReadIfNeeded(selectedConversation.value);
    await loadSidePanel();
  }
);

watch(
  () => selectedOpportunityId.value,
  async value => {
    stageDropdownOpen.value = false;
    outcomeDropdownOpen.value = false;
    if (removeStageDropdownPositionListeners) {
      removeStageDropdownPositionListeners();
      removeStageDropdownPositionListeners = null;
    }
    if (removeOutcomeDropdownPositionListeners) {
      removeOutcomeDropdownPositionListeners();
      removeOutcomeDropdownPositionListeners = null;
    }
    cancelValueEdit();
    if (!value) {
      selectedOpportunityDetails.value = null;
      return;
    }
    await loadSelectedOpportunityDetails();
  }
);

watch(
  () => route.query.conversationId,
  async () => {
    await applyConversationIdFromQuery();
  }
);

watch(
  () => floatingNotifStorageKey.value,
  () => {
    loadFloatingNotificationPreference();
  },
  { immediate: true }
);

watch(
  () => floatingNotifSoundStorageKey.value,
  () => {
    loadFloatingNotificationPreference();
  }
);

watch(
  () => mutedConversationStorageKey.value,
  () => {
    loadMutedConversations();
  },
  { immediate: true }
);

watch(
  () => hideGroupConversationsStorageKey.value,
  () => {
    loadHideGroupConversationsPreference();
  },
  { immediate: true }
);

watch(
  () => floatingNotificationsEnabled.value,
  value => {
    try {
      localStorage.setItem(floatingNotifStorageKey.value, value ? "1" : "0");
    } catch {
      // ignore
    }
  }
);

watch(
  () => floatingNotificationSoundEnabled.value,
  value => {
    try {
      localStorage.setItem(floatingNotifSoundStorageKey.value, value ? "1" : "0");
    } catch {
      // ignore
    }
  }
);

watch(
  () => hideGroupConversations.value,
  value => {
    try {
      localStorage.setItem(hideGroupConversationsStorageKey.value, value ? "1" : "0");
    } catch {
      // ignore
    }
  }
);

watch(
  () => startConversationQuery.value,
  value => {
    if (startConversationSearchTimer) clearTimeout(startConversationSearchTimer);
    if (!showStartConversationModal.value || startConversationMode.value !== "client" || value.trim().length < 2) return;
    startConversationSearchTimer = setTimeout(() => {
      void searchStartConversationClients();
    }, 350);
  }
);

watch(
  () => manualLinkQuery.value,
  value => {
    if (manualLinkSearchTimer) clearTimeout(manualLinkSearchTimer);
    if (!showManualLinkModal.value || value.trim().length < 2) return;
    manualLinkSearchTimer = setTimeout(() => {
      void searchManualLinkClients();
    }, 350);
  }
);

watch(
  () => manualLinkClientId.value,
  async () => {
    await loadManualLinkOpportunities();
  }
);

onMounted(async () => {
  const syncViewport = () => {
    isMobileViewport.value = window.innerWidth < 1024;
  };
  syncViewport();
  window.addEventListener("resize", syncViewport);
  removeViewportListener = () => window.removeEventListener("resize", syncViewport);
  const handleOutsideClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement | null;
    if (!target) return;
    if (!target.closest("form")) {
      showEmojiPicker.value = false;
    }
    if (!target.closest(".header-menu-root")) {
      showHeaderMenu.value = false;
    }
    if (!target.closest(".stage-dropdown-root")) {
      stageDropdownOpen.value = false;
      if (removeStageDropdownPositionListeners) {
        removeStageDropdownPositionListeners();
        removeStageDropdownPositionListeners = null;
      }
    }
    if (!target.closest(".outcome-dropdown-root")) {
      outcomeDropdownOpen.value = false;
      if (removeOutcomeDropdownPositionListeners) {
        removeOutcomeDropdownPositionListeners();
        removeOutcomeDropdownPositionListeners = null;
      }
    }
  };
  document.addEventListener("click", handleOutsideClick);
  removeOutsideEmojiListener = () => document.removeEventListener("click", handleOutsideClick);
  if (!agencyStore.agencies.length) {
    await agencyStore.loadAgencies().catch(() => undefined);
  }
  loadFloatingNotificationPreference();
});

onBeforeUnmount(() => {
  disconnectWs();
  stopInboxPolling();
  closeImageLightbox();
  stopRecordingResources();
  clearAttachment();
  if (toastTimer) clearTimeout(toastTimer);
  if (removeViewportListener) removeViewportListener();
  if (removeOutsideEmojiListener) removeOutsideEmojiListener();
  if (wsConnectTimeout) clearTimeout(wsConnectTimeout);
  if (wsHeartbeatTimer) clearInterval(wsHeartbeatTimer);
  if (manualLinkSearchTimer) clearTimeout(manualLinkSearchTimer);
  if (startConversationSearchTimer) clearTimeout(startConversationSearchTimer);
  if (removeStageDropdownPositionListeners) removeStageDropdownPositionListeners();
  if (removeOutcomeDropdownPositionListeners) removeOutcomeDropdownPositionListeners();
});
</script>

<style scoped>
.inbox-page {
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--background);
  box-shadow: var(--shadow-soft);
}

.inbox-sidebar,
.inbox-context-panel {
  border-color: var(--border);
  background: var(--card);
  color: var(--card-foreground);
}

.inbox-chat {
  background: var(--background);
}

.inbox-chat-header,
.inbox-composer {
  border-color: var(--border);
  background: color-mix(in srgb, var(--card) 94%, transparent);
}

.inbox-composer-form {
  border-color: var(--border);
  background: var(--card);
  box-shadow: var(--shadow-soft);
}

.inbox-conversation {
  border: 1px solid transparent;
  color: var(--foreground);
}

.inbox-conversation:hover {
  border-color: color-mix(in srgb, var(--foreground) 10%, var(--border));
  background: var(--accent);
}

.inbox-conversation.is-selected {
  border-color: color-mix(in srgb, var(--primary) 28%, var(--border));
  background: color-mix(in srgb, var(--primary) 10%, var(--card));
  box-shadow: var(--shadow-soft);
}

.message-bubble--outbound {
  background: var(--primary);
  color: var(--primary-foreground);
}

.message-bubble--inbound {
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--card-foreground);
}

.inbox-modal {
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-soft);
}

.inbox-page :deep(.border-slate-200),
.inbox-page :deep(.border-slate-200\/80) {
  border-color: var(--border) !important;
}

.inbox-page :deep(.bg-white),
.inbox-page :deep(.bg-white\/80),
.inbox-page :deep(.bg-white\/85),
.inbox-page :deep(.bg-white\/95) {
  background-color: var(--card) !important;
}

.inbox-page :deep(.bg-slate-50),
.inbox-page :deep(.bg-slate-50\/60),
.inbox-page :deep(.bg-slate-100) {
  background-color: var(--muted) !important;
}

.inbox-page :deep(.bg-slate-300) {
  background-color: var(--input) !important;
}

.inbox-page :deep(.text-slate-900),
.inbox-page :deep(.text-slate-800),
.inbox-page :deep(.text-slate-700) {
  color: var(--foreground) !important;
}

.inbox-page :deep(.text-slate-600),
.inbox-page :deep(.text-slate-500),
.inbox-page :deep(.text-slate-400) {
  color: var(--muted-foreground) !important;
}

.inbox-page :deep(input),
.inbox-page :deep(textarea),
.inbox-page :deep(select) {
  border-color: var(--input) !important;
  background-color: var(--background) !important;
  color: var(--foreground) !important;
}

.inbox-page :deep(input::placeholder),
.inbox-page :deep(textarea::placeholder) {
  color: var(--muted-foreground);
}

.inbox-page :deep(select option) {
  background: var(--popover);
  color: var(--popover-foreground);
}

.inbox-modal :deep(.text-slate-900),
.inbox-modal :deep(.text-slate-800),
.inbox-modal :deep(.text-slate-700) {
  color: var(--foreground) !important;
}

.inbox-modal :deep(.text-slate-600),
.inbox-modal :deep(.text-slate-500) {
  color: var(--muted-foreground) !important;
}

.inbox-modal :deep(.bg-white) {
  background-color: var(--card) !important;
}

.inbox-modal :deep(.bg-slate-50),
.inbox-modal :deep(.bg-slate-50\/60),
.inbox-modal :deep(.bg-slate-100) {
  background-color: var(--muted) !important;
}

.inbox-modal :deep(.border-slate-200),
.inbox-modal :deep(.border-slate-200\/80) {
  border-color: var(--border) !important;
}

.inbox-modal :deep(input),
.inbox-modal :deep(select) {
  border-color: var(--input) !important;
  background: var(--background) !important;
  color: var(--foreground) !important;
}

.chat-surface {
  background:
    radial-gradient(1150px 260px at 50% 0%, color-mix(in srgb, var(--primary) 7%, transparent), transparent),
    radial-gradient(840px 220px at 0% 100%, color-mix(in srgb, var(--primary) 3%, transparent), transparent),
    var(--background);
  background-size: auto, auto, auto;
}

.avatar-fallback {
  background: var(--muted);
}

.premium-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.45) transparent;
}

.premium-scroll::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.premium-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.premium-scroll::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.45);
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: content-box;
}

.premium-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.55);
  background-clip: content-box;
}

.empty-state-wrap {
  display: flex;
  min-height: 220px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-state-icon {
  display: inline-flex;
  height: 52px;
  width: 52px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--muted);
  font-size: 22px;
}

.empty-state-title {
  margin-top: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--foreground);
}

.empty-state-subtitle {
  margin-top: 4px;
  max-width: 240px;
  font-size: 12px;
  color: var(--muted-foreground);
}

.audio-player {
  display: block;
  width: min(320px, 100%);
  min-width: 220px;
  height: 38px;
  border-radius: 999px;
}

.status-dropdown {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-soft);
  max-height: 13.6rem;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 0.25rem;
}

.stage-dropdown-portal {
  position: fixed;
}

.outcome-dropdown-portal {
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

@media (max-width: 480px) {
  .audio-player {
    min-width: 0;
  }
}

@media (max-width: 1023px) {
  .inbox-page {
    border-radius: 0;
  }
}
</style>
