<template>
  <transition name="fade">
    <div
      v-if="open"
      class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/70 px-4 py-8"
    >
      <div class="w-full max-w-5xl rounded-3xl bg-white p-8 shadow-2xl">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.4em] text-slate-400">Criar com IA</p>
            <h2 class="text-2xl font-bold text-slate-900">Monte um roteiro automaticamente</h2>
            <p class="text-sm text-slate-500">Compartilhe o briefing, confirme os detalhes e deixe o Gemini organizar a página completa.</p>
          </div>
          <div class="text-right text-sm text-slate-600">
            <p class="font-semibold text-slate-900">Créditos disponíveis: <span class="text-brand">{{ creditsLabel }}</span></p>
            <p class="text-xs text-slate-500">1 crédito por página + 1 crédito opcional para pacote de imagens</p>
          </div>
        </div>

        <div class="mt-6">
          <div class="flex items-center gap-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <template v-for="n in totalSteps" :key="n">
              <div class="flex items-center gap-2">
                <div :class="['flex h-8 w-8 items-center justify-center rounded-full border', step === n ? 'border-brand text-brand' : 'border-slate-200 text-slate-400']">
                  {{ n }}
                </div>
                <div v-if="n < totalSteps" class="h-px w-6 bg-slate-200"></div>
              </div>
            </template>
          </div>
        </div>

        <div class="mt-6 space-y-6 max-h-[65vh] overflow-y-auto pr-2">
          <section v-if="step === 1" class="space-y-6">
            <div>
              <h3 class="text-lg font-semibold text-slate-900">Conte tudo sobre a viagem</h3>
              <p class="text-sm text-slate-500">Quanto mais contexto você der, mais precisa ficará a estrutura.</p>
              <textarea
                v-model="briefing"
                class="mt-3 h-48 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 focus:border-brand focus:outline-none"
                placeholder="Ex: Expedição exclusiva para Jalapão com saída de Goiânia, roteiro 5 dias, grupo reduzido..."
              ></textarea>
              <div class="mt-3 flex items-center gap-3">
                <label class="inline-flex cursor-pointer items-center gap-2 rounded-full border border-dashed border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:border-brand hover:text-brand">
                  <input type="file" class="hidden" multiple @change="handleBriefingFiles" />
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                    <path d="M21.44 11.05 12.97 19.5a5 5 0 0 1-7.07-7.07l8.49-8.49a3.5 3.5 0 0 1 4.95 4.95l-8.49 8.49a2 2 0 0 1-2.83-2.83l7.78-7.78" />
                  </svg>
                  Anexar briefing
                </label>
                <span v-if="attachmentsLoading" class="text-xs text-slate-500">Processando arquivos...</span>
              </div>
              <ul v-if="attachmentPreviews.length" class="mt-3 space-y-2 text-sm text-slate-600">
                <li v-for="file in attachmentPreviews" :key="file.id" class="flex items-center justify-between rounded-xl border border-slate-100 px-3 py-2">
                  <span class="truncate">{{ file.name }}</span>
                  <button class="text-xs font-semibold uppercase tracking-wide text-rose-500 hover:text-rose-600" @click="removeAttachment(file.id)">remover</button>
                </li>
              </ul>
            </div>

          </section>

          <section v-else-if="step === 2 && interpretingBriefing" class="flex flex-col items-center justify-center space-y-4 py-16 text-center">
            <div class="flex h-20 w-20 items-center justify-center rounded-full border-4 border-slate-100">
              <div class="h-14 w-14 rounded-full border-4 border-brand border-t-transparent animate-spin"></div>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-slate-900">Interpretando briefing com IA…</h3>
              <p class="mt-1 text-sm text-slate-500">Estamos detectando lacunas e organizando as informações principais.</p>
            </div>
            <div class="rounded-full border border-slate-200 px-4 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
              Tempo estimado: {{ interpretationCountdownLabel }}
            </div>
            <p class="text-xs text-slate-400">Esse passo leva em torno de 40 a 60 segundos.</p>
          </section>

          <section v-else-if="step === 2" class="space-y-6">
            <div>
              <h3 class="text-lg font-semibold text-slate-900">Revisar lacunas do briefing</h3>
              <p class="text-sm text-slate-500">Veja o que ainda falta e complemente as informacoes antes de seguir.</p>
            </div>
            <div class="rounded-2xl border border-slate-100 bg-slate-50/80 p-4">
              <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p class="text-sm font-semibold text-slate-800">O que ainda precisamos?</p>
                  <p class="text-xs text-slate-500">Detectamos automaticamente quais campos ainda nao apareceram no briefing.</p>
                </div>
                <button
                  type="button"
                  class="inline-flex items-center justify-center rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600 transition hover:border-brand hover:text-brand disabled:opacity-50"
                  :disabled="autoDetecting"
                  @click="runBriefingInterpretation"
                >
                  {{ autoDetecting ? "Interpretando..." : "Reprocessar briefing" }}
                </button>
              </div>
              <div
                v-if="autoDetecting || autoInsights || autoFillError"
                class="mt-4 rounded-xl border border-dashed border-slate-200 bg-white/70 p-3 text-sm text-slate-600"
              >
                <p v-if="autoDetecting" class="text-xs text-slate-500">Interpretando briefing com Gemini 2.5 Fast...</p>
                <p v-else-if="autoFillError" class="text-xs text-rose-500">{{ autoFillError }}</p>
                <div v-else class="space-y-2">
                  <p>Gemini preencheu {{ autoFilledCount }} de {{ followUpQuestions.length }} campos automaticamente.</p>
                  <p v-if="autoInsights?.summary" class="text-xs text-slate-500">Resumo: {{ autoInsights.summary }}</p>
                  <div v-if="autoMissingLabels.length" class="flex flex-wrap gap-2 text-xs">
                    <span
                      v-for="label in autoMissingLabels"
                      :key="label"
                      class="rounded-full bg-amber-100 px-3 py-1 font-semibold text-amber-700"
                    >
                      Sem dados: {{ label }}
                    </span>
                  </div>
                  <ul v-if="autoInsights?.notes?.length" class="list-disc pl-5 text-xs text-slate-500">
                    <li v-for="note in autoInsights.notes" :key="note">{{ note }}</li>
                  </ul>
                </div>
              </div>
              <div class="mt-4 grid gap-4 md:grid-cols-2">
                <div
                  v-for="question in followUpQuestions"
                  :key="question.key"
                  class="rounded-xl border px-3 py-3"
                  :class="missingMap[question.key] ? 'border-amber-200 bg-amber-50/40' : 'border-slate-200 bg-white'"
                >
                  <div class="flex items-center justify-between gap-2">
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ question.label }}</label>
                    <span
                      v-if="autoFilledTracker[question.key]"
                      class="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700"
                    >
                      via briefing
                    </span>
                    <span
                      v-else-if="missingMap[question.key]"
                      class="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-600"
                    >
                      falta info
                    </span>
                  </div>
                  <textarea
                    v-model="answers[question.key]"
                    :placeholder="question.placeholder"
                    class="mt-2 h-20 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
                  ></textarea>
                  <p class="mt-1 text-xs text-slate-400">{{ missingMap[question.key] ? question.missingHint : "Use se quiser complementar." }}</p>
                </div>
              </div>
            </div>
          </section>

          <section v-else-if="step === 3" class="space-y-5">
            <div>
              <h3 class="text-lg font-semibold text-slate-900">Personalize detalhes finais</h3>
              <p class="text-sm text-slate-500">Título sugerido da página e CTAs.</p>
              <div class="mt-3 grid gap-4 md:grid-cols-2">
                <div>
                  <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Título preferido</label>
                  <input
                    v-model="preferredTitle"
                    class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
                    placeholder="Ex: Expedição Jalapão Imersiva"
                  />
                </div>
                <div>
                  <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Link de vídeo (opcional)</label>
                  <input
                    v-model="videoUrl"
                    class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
                    placeholder="https://www.youtube.com/watch?v=..."
                  />
                </div>
              </div>
              <div class="mt-4">
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Tema da página</label>
                <p class="mt-1 text-xs text-slate-500">Escolha entre fundo claro tradicional ou um visual escuro com contraste elevado.</p>
                <div class="mt-3 inline-flex w-full max-w-sm rounded-full border border-slate-200 bg-slate-50 p-1 text-[11px] font-semibold uppercase tracking-wide">
                  <button
                    type="button"
                    class="flex-1 rounded-full px-4 py-2 transition"
                    :class="themeMode === 'light' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
                    @click="setThemeMode('light')"
                  >
                    Tema claro
                  </button>
                  <button
                    type="button"
                    class="flex-1 rounded-full px-4 py-2 transition"
                    :class="themeMode === 'dark' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-500'"
                    @click="setThemeMode('dark')"
                  >
                    Tema escuro
                  </button>
                </div>
                <p class="mt-2 text-xs text-slate-500">
                  No tema escuro aplicamos fundo #050505/#0C0C0C e o gradiente principal segue a cor base automaticamente.
                </p>
              </div>
            </div>

            <div>
              <h4 class="text-sm font-semibold text-slate-800">Fotos da agência</h4>
              <p class="text-xs text-slate-500">Faça upload das imagens que deseja usar (Hero, Story, Galeria...).</p>
              <div class="mt-2 flex items-center gap-3">
                <label class="inline-flex cursor-pointer items-center gap-2 rounded-full border border-dashed border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:border-brand hover:text-brand">
                  <input type="file" multiple accept="image/*" class="hidden" @change="handleMediaUpload" />
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
                    <path d="M3 16.5V5a2 2 0 0 1 2-2h8l6 6v7.5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                    <path d="M13 3v5h5" />
                    <path d="M6 21l3.828-3.828a2 2 0 0 1 2.828 0L16.5 21" />
                    <path d="M15 16h6" />
                    <path d="M18 13v6" />
                  </svg>
                  Selecionar fotos
                </label>
                <span v-if="uploadingMedia" class="text-xs text-slate-500">Enviando arquivos...</span>
              </div>
              <div v-if="manualMedia.length" class="mt-3 space-y-3">
                <div
                  v-for="media in manualMedia"
                  :key="media.id"
                  class="flex flex-col gap-2 rounded-xl border border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div class="text-sm text-slate-600">
                    <p class="font-semibold text-slate-900">{{ media.fileName }}</p>
                    <a :href="media.url" target="_blank" class="text-xs text-brand underline">Visualizar</a>
                  </div>
                  <div class="flex items-center gap-2">
                    <select
                      v-model="media.section_hint"
                      class="rounded-lg border border-slate-200 px-2 py-1 text-sm focus:border-brand focus:outline-none"
                    >
                      <option value="generic">Sem destino fixo</option>
                      <option value="hero">Hero</option>
                      <option value="story">Story</option>
                      <option value="gallery">Galeria</option>
                      <option value="photo">Bloco de foto</option>
                      <option value="banner">Banner / Destaque</option>
                    </select>
                    <button class="text-xs font-semibold uppercase tracking-wide text-rose-500 hover:text-rose-600" @click="removeMedia(media.id)">remover</button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section v-else-if="step === 4" class="space-y-5">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-slate-900">Gerar imagens com IA</h3>
                <p class="text-sm text-slate-500">O pacote de imagens (+1 crédito) pode ser distribuído livremente entre as seções abaixo (até {{ maxSectionImages }} por seção).</p>
              </div>
              <label class="inline-flex items-center gap-2 text-sm font-semibold text-slate-700">
                <input type="checkbox" v-model="generateAiImages" class="h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand" />
                Ativar pacote
              </label>
            </div>

            <div v-if="generateAiImages" class="space-y-4">
              <div
                v-for="option in imageTargetOptions"
                :key="option.value"
                class="rounded-2xl border border-slate-100 p-4"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-semibold text-slate-900">{{ option.label }}</p>
                    <p class="text-xs text-slate-500">{{ option.description }}</p>
                  </div>
                  <label class="inline-flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      :value="option.value"
                      :checked="isTargetSelected(option.value)"
                      :disabled="!isTargetSelected(option.value) && selectedImageTargets.length >= 5"
                      class="h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
                      @change="toggleImageTarget(option.value)"
                    />
                    Usar IA
                  </label>
                </div>
                <textarea
                  v-if="isTargetSelected(option.value)"
                  :value="getPromptValue(option.value)"
                  @input="setPromptValue(option.value, ($event.target as HTMLTextAreaElement).value)"
                  class="mt-3 h-20 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
                  placeholder="Descreva rapidamente o clima desejado para esta seção"
                ></textarea>
                <div v-if="isTargetSelected(option.value)" class="mt-3 flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-600">
                  <label class="flex items-center gap-2">
                    <span>Qtd. de imagens</span>
                    <input
                      type="number"
                      :min="1"
                      :max="maxSectionImages"
                      class="w-20 rounded-xl border border-slate-200 px-2 py-1 text-sm focus:border-brand focus:outline-none"
                      :disabled="option.value === 'itinerary' && isPerDaySelected(option.value)"
                      :value="getCountValue(option.value)"
                      @input="setCountValue(option.value, Number(($event.target as HTMLInputElement).value))"
                    />
                  </label>
                  <label
                    v-if="option.value === 'itinerary'"
                    class="inline-flex items-center gap-2 text-xs font-semibold text-slate-600"
                  >
                    <input
                      type="checkbox"
                      class="h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
                      :checked="isPerDaySelected(option.value)"
                      @change="togglePerDay(option.value, ($event.target as HTMLInputElement).checked)"
                    />
                    Uma imagem para cada dia
                  </label>
                </div>
                <p
                  v-if="option.value === 'itinerary' && isPerDaySelected(option.value)"
                  class="mt-1 text-xs text-slate-500"
                >
                  Usaremos automaticamente cada dia do itinerário para distribuir as imagens.
                </p>
              </div>
            </div>
            <p v-else class="text-sm text-slate-500">Você pode pular e enviar imagens depois. O sistema colocará placeholders “Adicione imagem aqui”.</p>
          </section>

          <section v-else-if="step === 5" class="space-y-5">
            <div class="rounded-2xl border border-slate-100 bg-slate-50/70 p-5">
              <h3 class="text-lg font-semibold text-slate-900">Revisar antes de gerar</h3>
              <ul class="mt-3 space-y-2 text-sm text-slate-600">
                <li><strong>Briefing:</strong> {{ briefingSnippet }}</li>
                <li><strong>Detalhes extras:</strong> {{ filledAnswersLabel }}</li>
                <li><strong>Tema:</strong> {{ themeModeSummary }}</li>
                <li><strong>Mídias enviadas:</strong> {{ manualMedia.length || "Nenhuma" }}</li>
                <li><strong>Pacote de imagens IA:</strong> {{ generateAiImages && selectedImageTargets.length ? `${selectedImageTargets.length} seções` : "Não usar agora" }}</li>
                <li><strong>Créditos necessários:</strong> {{ creditBreakdown }}</li>
              </ul>
              <div class="mt-4 rounded-xl bg-white/80 p-4 text-xs text-slate-500">
                A página será criada no status <span class="font-semibold text-slate-800">publicado</span> e você será redirecionado ao editor para ajustes finos.
              </div>
            </div>
          </section>

          <section v-else-if="step === PROGRESS_STEP" class="space-y-5">
            <div>
              <h3 class="text-lg font-semibold text-slate-900">
                {{ generationErrorMessage ? "Precisamos da sua ajuda" : generationSuccessData ? "Tudo pronto!" : "Gerando e publicando sua pagina" }}
              </h3>
              <p class="text-sm text-slate-500">
                <span v-if="generationErrorMessage">Corrija o briefing ou tente novamente.</span>
                <span v-else-if="generationSuccessData">Estamos abrindo o editor automaticamente em alguns segundos.</span>
                <span v-else>Esse processo leva cerca de 1 minuto. Acompanhe o checklist abaixo.</span>
              </p>
            </div>
            <div class="space-y-3">
              <div
                v-for="stage in generationStages"
                :key="stage.key"
                class="flex items-start gap-3 rounded-2xl border border-slate-100 p-4"
              >
                <div
                  :class="[
                    'flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm',
                    stage.status === 'done'
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-600'
                      : stage.status === 'active'
                        ? 'border-brand/50 bg-brand/5 text-brand animate-pulse'
                        : stage.status === 'error'
                          ? 'border-rose-200 bg-rose-50 text-rose-600'
                          : 'border-slate-200 bg-white text-slate-400',
                  ]"
                >
                  <template v-if="stage.status === 'done'">
                    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </template>
                  <template v-else-if="stage.status === 'active'">
                    <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 2a10 10 0 1 0 10 10" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </template>
                  <template v-else-if="stage.status === 'error'">
                    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M6 6l12 12M6 18L18 6" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </template>
                  <template v-else>
                    <svg class="h-2 w-2" viewBox="0 0 8 8" fill="currentColor">
                      <circle cx="4" cy="4" r="4" />
                    </svg>
                  </template>
                </div>
                <div>
                  <p class="font-semibold text-slate-900">{{ stage.label }}</p>
                  <p class="text-sm text-slate-500">{{ stage.description }}</p>
                  <p v-if="stage.details" class="text-xs text-slate-400">{{ stage.details }}</p>
                </div>
              </div>
            </div>
            <div
              v-if="generationErrorMessage"
              class="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
            >
              {{ generationErrorMessage }}
            </div>
            <div
              v-else-if="generationSuccessData"
              class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700"
            >
              {{ generationSuccessData.message || "Pagina criada com sucesso." }}
            </div>
            <div v-else class="rounded-2xl border border-slate-100 bg-slate-50/80 p-4 text-xs text-slate-500">
              Estamos organizando textos, midias e layout automaticamente para voce.
            </div>
          </section>
        </div>

        <div class="mt-8 flex flex-col gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="step === 1 || submitting || interpretingBriefing || generationProgressActive || isProgressStep"
            @click="previous"
          >
            Voltar
          </button>
          <div class="flex flex-col gap-3 sm:flex-row">
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100"
              @click="closeModal"
              :disabled="submitting || generationProgressActive"
            >
              Cancelar
            </button>
            <button
              v-if="showContinueButton"
              class="rounded-full bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="!canProceed || submitting || interpretingBriefing"
              @click="next"
            >
              Continuar
            </button>
            <button
              v-else-if="showSubmitButton"
              class="inline-flex items-center justify-center rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="!canSubmit || submitting || !agencyId"
              @click="submit"
            >
              <svg
                v-if="submitting"
                class="mr-2 h-4 w-4 animate-spin text-white"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <circle cx="12" cy="12" r="9" opacity="0.3" />
                <path d="M21 12a9 9 0 0 1-9 9" />
              </svg>
              Criar e publicar
            </button>
            <template v-else>
              <button
                v-if="generationSuccessData"
                class="rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white shadow hover:bg-brand-dark"
                @click="finishGenerationSuccess"
              >
                Ir para o editor agora
              </button>
              <button
                v-if="generationErrorMessage"
                class="rounded-full border border-rose-200 px-6 py-3 text-sm font-semibold text-rose-600 hover:bg-rose-50"
                @click="returnToFormFromError"
              >
                Voltar e ajustar
              </button>
            </template>
          </div>
        </div>
        <p v-if="errorMessage && !isProgressStep" class="mt-2 text-sm text-rose-500">{{ errorMessage }}</p>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import api from "../../services/api";
import {
  createAiPage,
  fetchAiCredits,
  interpretBriefing,
  type AiAttachmentPayload,
  type AiBriefingInterpretResponse,
  type AiCreditWallet,
  type AiImageSelectionPayload,
  type AiManualMediaPayload,
  type AiPagePayload,
  type AiPageResponse,
  type FollowUpKey,
} from "../../services/ai";

interface AttachmentPreview {
  id: string;
  name: string;
}

const props = defineProps<{
  open: boolean;
  agencyId: number | null;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "created", payload: { pageId: number; redirect: string }): void;
  (e: "snackbar", payload: { text: string; tone?: "success" | "error" }): void;
}>();

const FINAL_FORM_STEP = 5;
const PROGRESS_STEP = 6;
const step = ref(1);
const totalSteps = PROGRESS_STEP;
type StageStatus = "pending" | "active" | "done" | "error";
interface GenerationStage {
  key: string;
  label: string;
  description: string;
  status: StageStatus;
  details?: string | null;
}
interface GenerationSuccessState {
  pageId: number;
  redirect: string;
  message: string;
}
const briefing = ref("");
const preferredTitle = ref("");
const attachments = ref<AiAttachmentPayload[]>([]);
const attachmentPreviews = ref<AttachmentPreview[]>([]);
const attachmentsLoading = ref(false);
const answers = reactive<Record<FollowUpKey, string | null>>({
  destination: null,
  travel_dates: null,
  audience: null,
  included_services: null,
  highlights: null,
  pricing: null,
  call_to_action: null,
  urgency: null,
});
const manualMedia = ref<
  { id: string; url: string; fileName: string; section_hint: "hero" | "story" | "gallery" | "photo" | "banner" | "generic" }[]
>([]);
const videoUrl = ref("");
const themeMode = ref<"light" | "dark">("light");
const uploadingMedia = ref(false);
const generateAiImages = ref(false);
const selectedImageTargets = ref<AiImageSelectionPayload[]>([]);
const maxSectionImages = 6;
const INTERPRETATION_COUNTDOWN_SECONDS = 45;
const interpretingBriefing = ref(false);
const interpretationCountdown = ref(INTERPRETATION_COUNTDOWN_SECONDS);
let interpretationTimer: ReturnType<typeof setInterval> | null = null;
const generationStages = ref<GenerationStage[]>([]);
const generationProgressActive = ref(false);
const generationErrorMessage = ref("");
const generationSuccessData = ref<GenerationSuccessState | null>(null);
let generationStageTimers: ReturnType<typeof setTimeout>[] = [];
let generationAutoRedirectTimer: ReturnType<typeof setTimeout> | null = null;
const STAGE_DURATION_MS: Record<string, number> = {
  text: 15000,
  images: 20000,
  layout: 12000,
  publish: 8000,
};

const defaultImageCount = (section: AiImageSelectionPayload["section"]) => {
  if (section === "story" || section === "gallery") return 3;
  if (section === "itinerary") return 1;
  return 1;
};

const getCountValue = (section: AiImageSelectionPayload["section"]) => {
  const target = selectedImageTargets.value.find(item => item.section === section);
  return target?.count ?? defaultImageCount(section);
};

const setCountValue = (section: AiImageSelectionPayload["section"], value: number) => {
  const target = selectedImageTargets.value.find(item => item.section === section);
  if (!target) return;
  const safeValue = Number.isFinite(value) ? Math.floor(value) : defaultImageCount(section);
  const normalized = Math.min(maxSectionImages, Math.max(1, safeValue));
  target.count = normalized;
};

const isPerDaySelected = (section: AiImageSelectionPayload["section"]) =>
  selectedImageTargets.value.find(item => item.section === section)?.per_day ?? false;

const togglePerDay = (section: AiImageSelectionPayload["section"], enabled: boolean) => {
  const target = selectedImageTargets.value.find(item => item.section === section);
  if (!target) return;
  target.per_day = enabled;
};
const credits = ref<AiCreditWallet | null>(null);
const loadingCredits = ref(false);
const submitting = ref(false);
const errorMessage = ref("");
const autoDetecting = ref(false);
const autoFillError = ref("");
const autoInsights = ref<AiBriefingInterpretResponse | null>(null);
const autoFilledTracker = reactive<Record<FollowUpKey, boolean>>({
  destination: false,
  travel_dates: false,
  audience: false,
  included_services: false,
  highlights: false,
  pricing: false,
  call_to_action: false,
  urgency: false,
});

const followUpQuestions = [
  {
    key: "destination" as FollowUpKey,
    label: "Destino / Nome do roteiro",
    placeholder: "Ex: Jalapão Imersivo - saída Goiânia",
    missingHint: "Ajuda a IA a criar títulos e CTA coerentes.",
  },
  {
    key: "travel_dates" as FollowUpKey,
    label: "Datas ou período",
    placeholder: "Ex: 15 a 20 de maio, feriado de Corpus Christi...",
    missingHint: "Mencione datas ou periodicidade.",
  },
  {
    key: "audience" as FollowUpKey,
    label: "Público ideal",
    placeholder: "Famílias, casais, mochileiros...",
    missingHint: "Quem deve sentir desejo pela viagem?",
  },
  {
    key: "included_services" as FollowUpKey,
    label: "Serviços incluídos",
    placeholder: "Hospedagem premium, 8 refeições, traslados...",
    missingHint: "Liste o que já está incluso.",
  },
  {
    key: "highlights" as FollowUpKey,
    label: "Diferenciais",
    placeholder: "Equipe local, guias especialistas, grupo reduzido...",
    missingHint: "Traga 2 ou 3 motivos fortes.",
  },
  {
    key: "pricing" as FollowUpKey,
    label: "Valores e condições",
    placeholder: "A partir de R$ 3.490 | parcelado em até 10x...",
    missingHint: "Ajuda no bloco de preços.",
  },
  {
    key: "call_to_action" as FollowUpKey,
    label: "CTA preferido",
    placeholder: "Falar no WhatsApp, reservar formulário...",
    missingHint: "Define o texto dos botões.",
  },
  {
    key: "urgency" as FollowUpKey,
    label: "Urgência ou vagas",
    placeholder: "12 vagas, saída confirmada, última chamada...",
    missingHint: "Usado no countdown/banner.",
  },
];

const followUpKeys = followUpQuestions.map(question => question.key);

const imageTargetOptions = [
  { value: "hero", label: "Hero", description: "Imagem principal de impacto" },
  { value: "story", label: "Story / Descritivo", description: "Foto para bloco com storytelling" },
  { value: "gallery", label: "Galeria", description: "Composição com 2 a 3 imagens" },
  { value: "photo", label: "Bloco de foto único", description: "Foto ampla para respiro visual" },
  { value: "banner", label: "Banner intermediário", description: "Arte para destaque/escassez" },
  { value: "itinerary", label: "Itinerário", description: "Imagens para cada dia do cronograma" },
] as const;

const missingMap = computed<Record<FollowUpKey, boolean>>(() => {

  if (autoInsights.value) {

    const result: Record<FollowUpKey, boolean> = {} as Record<FollowUpKey, boolean>;

    const missing = new Set(autoInsights.value.missing || []);

    followUpKeys.forEach(key => {

      const value = answers[key];

      result[key] = missing.has(key) && !(value && value.trim().length);

    });

    return result;

  }

  const normalized = normalizeText(briefing.value);

  const map: Record<FollowUpKey, boolean> = {

    destination: !containsPattern(normalized, [/destino/, /viagem/, /\bpara\b/]) && !answers.destination,

    travel_dates: !containsPattern(normalized, [/dia/, /noite/, /\b\d{1,2}\/\d{1,2}\b/, /202\d/, /m�s/, /seman/]) && !answers.travel_dates,

    audience: !containsPattern(normalized, [/famil/, /casal/, /grupo/, /turma/, /adult/]) && !answers.audience,

    included_services: !containsPattern(normalized, [/inclu/i, /hosped/, /refei/, /transporte/]) && !answers.included_services,

    highlights: !containsPattern(normalized, [/exclusivo/, /premium/, /�nico/, /imperd�vel/]) && !answers.highlights,

    pricing: !containsPattern(normalized, [/r\$/, /parcel/, /\d+\s*x/, /investimento/]) && !answers.pricing,

    call_to_action: !answers.call_to_action,

    urgency: !containsPattern(normalized, [/vaga/, /�ltim/, /restam/, /lote/]) && !answers.urgency,

  };

  return map;

});
const autoMissingLabels = computed(() => {
  if (!autoInsights.value) return [];
  const missingSet = new Set(autoInsights.value.missing || []);
  return followUpQuestions.filter(question => missingSet.has(question.key)).map(question => question.label);
});

const autoFilledCount = computed(() => followUpQuestions.filter(question => autoFilledTracker[question.key]).length);
const interpretationCountdownLabel = computed(() => {
  const seconds = Math.max(0, interpretationCountdown.value);
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
});

const creditsLabel = computed(() => {
  if (loadingCredits.value) return "consultando...";
  return credits.value ? credits.value.balance : "—";
});

const hasBriefingContent = computed(() => briefing.value.trim().length >= 20 || attachments.value.length > 0);

const canProceed = computed(() => {
  if (step.value === 1) {
    return hasBriefingContent.value;
  }
  if (step.value === 4) {
    return !generateAiImages.value || selectedImageTargets.value.length > 0;
  }
  return true;
});

const canSubmit = computed(() => hasBriefingContent.value && !!props.agencyId);
const themeModeSummary = computed(() => (themeMode.value === "dark" ? "Tema escuro" : "Tema claro"));
const briefingSnippet = computed(() => (briefing.value.length > 120 ? `${briefing.value.slice(0, 120)}...` : briefing.value));
const filledAnswersLabel = computed(() => {
  const filled = followUpQuestions.filter(q => answers[q.key]);
  if (!filled.length) return "Nenhum";
  return filled.map(q => q.label).join(", ");
});
const creditBreakdown = computed(() => {
  const base = 1;
  const extra = generateAiImages.value && selectedImageTargets.value.length ? "+1 crédito de imagens" : "+0";
  return `${base} crédito base ${extra}`;
});
const isProgressStep = computed(() => step.value === PROGRESS_STEP);
const showContinueButton = computed(() => step.value < FINAL_FORM_STEP);
const showSubmitButton = computed(() => step.value === FINAL_FORM_STEP);

let applyingAutoAnswers = false;
followUpKeys.forEach(key => {
  watch(
    () => answers[key],
    (newValue, oldValue) => {
      if (applyingAutoAnswers) return;
      if (newValue !== oldValue) {
        autoFilledTracker[key] = false;
      }
    }
  );
});

watch(
  () => props.open,
  value => {
    if (value) {
      resetForm();
      loadCredits();
    } else {
      stopInterpretationCountdown();
      interpretingBriefing.value = false;
      resetGenerationStages();
    }
  },
  { immediate: true }
);

watch(
  () => briefing.value,
  () => {
    if (step.value === 1) {
      resetAutoFillState();
    }
  }
);

onBeforeUnmount(() => {
  stopInterpretationCountdown();
  resetGenerationStages();
});

function resetForm() {
  step.value = 1;
  interpretingBriefing.value = false;
  stopInterpretationCountdown();
  resetGenerationStages();
  briefing.value = "";
  preferredTitle.value = "";
  videoUrl.value = "";
  themeMode.value = "light";
  attachments.value = [];
  attachmentPreviews.value = [];
  manualMedia.value = [];
  generateAiImages.value = false;
  selectedImageTargets.value = [];
  errorMessage.value = "";
  resetAutoFillState();
  Object.keys(answers).forEach(key => {
    answers[key as FollowUpKey] = null;
  });
}

function resetAutoFillState() {
  autoInsights.value = null;
  autoFillError.value = "";
  autoDetecting.value = false;
  followUpKeys.forEach(key => {
    autoFilledTracker[key] = false;
  });
}

async function loadCredits() {
  loadingCredits.value = true;
  try {
    credits.value = await fetchAiCredits();
  } catch {
    credits.value = null;
  } finally {
    loadingCredits.value = false;
  }
}

function closeModal() {
  if (submitting.value || generationProgressActive.value) return;
  emit("close");
}

function previous() {
  if (step.value > 1) {
    step.value -= 1;
  }
}

function next() {
  if (!canProceed.value || interpretingBriefing.value) return;
  const previousStep = step.value;
  if (step.value < FINAL_FORM_STEP) {
    step.value += 1;
  }
  if (previousStep === 1 && step.value === 2) {
    autoInterpretBriefing();
  }
}

async function autoInterpretBriefing() {
  interpretingBriefing.value = true;
  startInterpretationCountdown();
  try {
    await runBriefingInterpretation();
  } finally {
    interpretingBriefing.value = false;
    stopInterpretationCountdown();
  }
}

function startInterpretationCountdown() {
  stopInterpretationCountdown();
  interpretationCountdown.value = INTERPRETATION_COUNTDOWN_SECONDS;
  interpretationTimer = setInterval(() => {
    if (interpretationCountdown.value > 0) {
      interpretationCountdown.value -= 1;
    } else {
      stopInterpretationCountdown(false);
    }
  }, 1000);
}

function stopInterpretationCountdown(resetValue = true) {
  if (interpretationTimer) {
    clearInterval(interpretationTimer);
    interpretationTimer = null;
  }
  if (resetValue) {
    interpretationCountdown.value = INTERPRETATION_COUNTDOWN_SECONDS;
  }
}

function resetGenerationStages() {
  clearGenerationStageTimers();
  clearAutoRedirectTimer();
  generationStages.value = [];
  generationProgressActive.value = false;
  generationErrorMessage.value = "";
  generationSuccessData.value = null;
}

function clearGenerationStageTimers() {
  generationStageTimers.forEach(timer => clearTimeout(timer));
  generationStageTimers = [];
}

function clearAutoRedirectTimer() {
  if (generationAutoRedirectTimer) {
    clearTimeout(generationAutoRedirectTimer);
    generationAutoRedirectTimer = null;
  }
}

function shouldGenerateImages() {
  return generateAiImages.value && selectedImageTargets.value.length > 0;
}

function resolveTargetCount(target: AiImageSelectionPayload) {
  const base = typeof target.count === "number" && target.count > 0 ? Math.floor(target.count) : defaultImageCount(target.section);
  return Math.max(1, base);
}

function totalRequestedImages() {
  if (!shouldGenerateImages()) return 0;
  return selectedImageTargets.value.reduce((sum, target) => sum + resolveTargetCount(target), 0);
}

function getStageDuration(key: string) {
  const base = STAGE_DURATION_MS[key] ?? 3200;
  if (key === "images") {
    const total = Math.max(1, totalRequestedImages());
    return base * total;
  }
  return base;
}

function buildGenerationStages(): GenerationStage[] {
  const stages: GenerationStage[] = [
    {
      key: "text",
      label: "Gerando textos principais",
      description: "Organizando Hero, Story, diferenciais e FAQ.",
      status: "pending",
    },
  ];
  if (shouldGenerateImages()) {
    const labelMap = Object.fromEntries(imageTargetOptions.map(option => [option.value, option.label]));
    const targets = selectedImageTargets.value
      .map(target => labelMap[target.section] || target.section)
      .join(", ");
    const countLabel = totalRequestedImages();
    const detailPieces = [];
    if (targets) {
      detailPieces.push(`Alvos: ${targets}`);
    }
    if (countLabel > 0) {
      detailPieces.push(`${countLabel} ${countLabel === 1 ? "imagem" : "imagens"}`);
    }
    stages.push({
      key: "images",
      label: selectedImageTargets.value.length > 1 ? "Gerando pacote de imagens IA" : "Gerando imagem com IA",
      description: "Criando variacoes visuais com base no briefing.",
      details: detailPieces.length ? detailPieces.join(" • ") : null,
      status: "pending",
    });
  }
  stages.push(
    {
      key: "layout",
      label: "Estruturando sua pagina",
      description: "Agrupando secoes, itinerario e chamadas.",
      status: "pending",
    },
    {
      key: "publish",
      label: "Publicando e liberando o editor",
      description: "Criando rota publica e abrindo no painel.",
      status: "pending",
    },
  );
  return stages;
}

function startGenerationProgress() {
  resetGenerationStages();
  generationStages.value = buildGenerationStages();
  if (!generationStages.value.length) return;
  generationProgressActive.value = true;
  setStageStatus(0, "active");
  if (generationStages.value.length <= 1) return;
  let delay = 0;
  for (let index = 0; index < generationStages.value.length - 1; index += 1) {
    const stageKey = generationStages.value[index].key;
    const duration = getStageDuration(stageKey);
    delay += duration;
    generationStageTimers.push(
      setTimeout(() => {
        if (!generationProgressActive.value) return;
        setStageStatus(index, "done");
        setStageStatus(index + 1, "active");
      }, delay),
    );
  }
}

function setStageStatus(index: number, status: StageStatus) {
  const stage = generationStages.value[index];
  if (!stage) return;
  stage.status = status;
}

function handleGenerationSuccess(response: AiPageResponse) {
  clearGenerationStageTimers();
  generationStages.value.forEach((_, index) => setStageStatus(index, "done"));
  generationSuccessData.value = {
    pageId: response.page_id,
    redirect: response.redirect_url,
    message: response.message,
  };
  emit("snackbar", { text: response.message, tone: "success" });
  scheduleAutoRedirect();
}

function scheduleAutoRedirect() {
  clearAutoRedirectTimer();
  generationAutoRedirectTimer = setTimeout(() => {
    finishGenerationSuccess();
  }, 2000);
}

function finishGenerationSuccess() {
  const payload = generationSuccessData.value;
  if (!payload) return;
  clearAutoRedirectTimer();
  emit("created", { pageId: payload.pageId, redirect: payload.redirect });
  emit("close");
  generationSuccessData.value = null;
}

function handleGenerationError(detail: string) {
  clearGenerationStageTimers();
  generationProgressActive.value = false;
  generationErrorMessage.value = detail;
  errorMessage.value = detail;
  const currentIndex = generationStages.value.findIndex(stage => stage.status === "active");
  const fallbackIndex = currentIndex >= 0 ? currentIndex : generationStages.value.length - 1;
  if (fallbackIndex >= 0) {
    setStageStatus(fallbackIndex, "error");
  }
  emit("snackbar", { text: detail, tone: "error" });
}

function returnToFormFromError() {
  resetGenerationStages();
  step.value = FINAL_FORM_STEP;
}

function normalizeText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function containsPattern(text: string, patterns: RegExp[]) {
  return patterns.some(pattern => pattern.test(text));
}

async function handleBriefingFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = input.files;
  if (!files || !files.length) return;
  attachmentsLoading.value = true;
  for (const file of Array.from(files).slice(0, 3)) {
    if (file.size > 5 * 1024 * 1024) {
      emit("snackbar", { text: `${file.name} é maior que 5MB.`, tone: "error" });
      continue;
    }
    const data = await toBase64(file);
    const payload: AiAttachmentPayload = {
      name: file.name,
      mime_type: file.type || "application/octet-stream",
      data,
    };
    attachments.value.push(payload);
    attachmentPreviews.value.push({ id: crypto.randomUUID(), name: file.name });
  }
  attachmentsLoading.value = false;
  input.value = "";
}

function removeAttachment(id: string) {
  const index = attachmentPreviews.value.findIndex(item => item.id === id);
  if (index >= 0) {
    attachmentPreviews.value.splice(index, 1);
    attachments.value.splice(index, 1);
  }
}

async function runBriefingInterpretation() {
  if (!props.agencyId) {
    autoFillError.value = "Selecione uma agǦncia antes de interpretar o briefing.";
    return;
  }
  const hasEnoughText = briefing.value.trim().length >= 10;
  if (!hasEnoughText && attachments.value.length === 0) {
    autoFillError.value = "Escreva um breve resumo ou anexe o briefing antes de interpretar.";
    return;
  }
  autoDetecting.value = true;
  autoFillError.value = "";
  try {
    const response = await interpretBriefing({
      agency_id: props.agencyId,
      briefing: briefing.value.trim(),
      attachments: attachments.value,
    });
    applyAutoAnswers(response);
    autoInsights.value = response;
  } catch (err: any) {
    autoInsights.value = null;
    autoFillError.value =
      err?.response?.data?.detail || "Nǜo foi poss��vel interpretar o briefing automaticamente.";
  } finally {
    autoDetecting.value = false;
  }
}

function applyAutoAnswers(result: AiBriefingInterpretResponse) {
  if (!result?.answers) return;
  applyingAutoAnswers = true;
  try {
    followUpKeys.forEach(key => {
      const rawValue = result.answers?.[key];
      if (typeof rawValue !== "string") return;
      const trimmed = rawValue.trim();
      if (!trimmed) return;
      if (!answers[key] || autoFilledTracker[key]) {
        answers[key] = trimmed;
        autoFilledTracker[key] = true;
      }
    });
  } finally {
    applyingAutoAnswers = false;
  }
}

async function handleMediaUpload(event: Event) {
  if (!props.agencyId) {
    emit("snackbar", { text: "Selecione uma agência antes de enviar mídias.", tone: "error" });
    return;
  }
  const input = event.target as HTMLInputElement;
  const files = input.files;
  if (!files || !files.length) return;
  uploadingMedia.value = true;
  try {
    for (const file of Array.from(files)) {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post(`/media/upload?agency_id=${props.agencyId}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      manualMedia.value.push({
        id: crypto.randomUUID(),
        url: data.url,
        fileName: file.name,
        section_hint: "generic",
      });
    }
  } catch (err) {
    emit("snackbar", { text: "Não foi possível enviar as fotos.", tone: "error" });
  } finally {
    uploadingMedia.value = false;
    input.value = "";
  }
}

function removeMedia(id: string) {
  manualMedia.value = manualMedia.value.filter(item => item.id !== id);
}

function toggleImageTarget(section: AiImageSelectionPayload["section"]) {
  const exists = selectedImageTargets.value.some(item => item.section === section);
  if (exists) {
    selectedImageTargets.value = selectedImageTargets.value.filter(item => item.section !== section);
    return;
  }
  if (selectedImageTargets.value.length >= 5) return;
  selectedImageTargets.value.push({
    section,
    prompt_hint: "",
    count: defaultImageCount(section),
    per_day: section === "itinerary",
  });
}

function isTargetSelected(section: AiImageSelectionPayload["section"]) {
  return selectedImageTargets.value.some(item => item.section === section);
}

function getPromptValue(section: AiImageSelectionPayload["section"]) {
  const target = selectedImageTargets.value.find(item => item.section === section);
  return target?.prompt_hint || "";
}

function setPromptValue(section: AiImageSelectionPayload["section"], value: string) {
  const target = selectedImageTargets.value.find(item => item.section === section);
  if (target) {
    target.prompt_hint = value;
  }
}

async function submit() {
  if (!props.agencyId || submitting.value) return;
  submitting.value = true;
  errorMessage.value = "";
  generationErrorMessage.value = "";
  try {
    const parsedVideo = videoUrl.value.trim();
    const safeVideo = parsedVideo && isValidUrl(parsedVideo) ? parsedVideo : null;
    const answersPayload = buildAnswersPayload();
    const payload: AiPagePayload = {
      agency_id: props.agencyId,
      briefing: briefing.value.trim(),
      preferred_title: preferredTitle.value || null,
      answers: answersPayload,
      attachments: attachments.value,
      manual_media: manualMedia.value.map(media => ({
        url: media.url,
        label: media.fileName,
        section_hint: media.section_hint === "generic" ? null : media.section_hint,
      })) as AiManualMediaPayload[],
      video_url: safeVideo,
      generate_ai_images: generateAiImages.value && selectedImageTargets.value.length > 0,
      ai_image_targets: generateAiImages.value ? selectedImageTargets.value : [],
      auto_publish: true,
      theme_mode: themeMode.value,
    };
    step.value = PROGRESS_STEP;
    startGenerationProgress();
    const response = await createAiPage(payload);
    handleGenerationSuccess(response);
  } catch (err: any) {
    const detail = err?.response?.data?.detail || "Nao foi possivel gerar a pagina. Tente novamente.";
    handleGenerationError(detail);
  } finally {
    submitting.value = false;
  }
}

function toBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const [, base64] = result.split("base64,");
      resolve(base64 || result);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function isValidUrl(value: string) {
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

function buildAnswersPayload() {
  const payload: Record<string, string | null> = {};
  for (const key of Object.keys(answers) as FollowUpKey[]) {
    const value = answers[key];
    payload[key] = value && value.trim().length > 0 ? value.trim() : null;
  }
  return payload;
}

function setThemeMode(mode: "light" | "dark") {
  themeMode.value = mode;
}
</script>
