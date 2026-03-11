<template>
  <div class="min-h-screen light-theme overflow-x-hidden">
    <div class="flex min-h-screen">
      <aside
        class="hidden w-64 flex-shrink-0 flex-col justify-between border-r border-slate-200 bg-white/90 px-4 py-6 text-slate-800 shadow-md md:fixed md:inset-y-0 md:left-0 md:flex"
      >
        <div class="flex flex-1 flex-col overflow-y-auto">
          <div class="mb-8 flex items-center justify-center">
            <img :src="sidebarLogoSrc" alt="Roteiro Online" class="max-h-16 w-full object-contain" />
          </div>
          <nav class="flex-1 space-y-1">
            <RouterLink
              v-for="item in navItems"
              :key="item.to"
              :to="item.to"
              class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition"
              :class="isActive(item.to) ? activeClass : inactiveClass"
            >
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-slate-600">
                <svg
                  :viewBox="navIconViewBoxes[item.to] || navIconViewBoxes.default"
                  :class="['h-4 w-4', navIconSizes[item.to]]"
                  :stroke-width="navIconStrokeWidths[item.to] || null"
                  v-html="navIcons[item.to] || navIcons.default"
                ></svg>
              </span>
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>
        </div>

        <div class="mt-8 border-t border-slate-200 pt-4">
          <button
            type="button"
            @click="handleLogout"
            class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-red-50 hover:text-red-600"
          >
            <span class="flex h-7 w-7 items-center justify-center rounded-full bg-red-50 text-red-600">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3v9m5.657-6.657a8 8 0 1 1-11.314 0" />
              </svg>
            </span>
            <span>Sair</span>
          </button>
        </div>
      </aside>

      <main class="flex-1 overflow-x-hidden md:ml-64">
        <header class="sticky top-0 z-30 bg-white px-4 py-3 text-slate-900 shadow-sm md:static">
          <div class="flex items-center justify-between md:hidden">
            <img
              v-if="sidebarLogoSrc"
              :src="sidebarLogoSrc"
              alt="Roteiro Online"
              class="h-12 w-auto"
            />
          <div class="flex items-center gap-2">
            <h1 class="text-lg font-bold">{{ currentPageTitle }}</h1>
            <button
              type="button"
              class="inline-flex h-12 w-12 items-center justify-center rounded-full text-white shadow-lg transition"
                style="background-color: #41ce5f;"
                @click="mobileMenuOpen = true"
              >
                <span class="sr-only">Abrir menu</span>
                <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <path d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
          <div class="hidden items-center justify-between md:flex">
            <div class="flex items-center gap-3">
              <h1 class="text-lg font-bold">{{ currentPageTitle }}</h1>
            </div>
          </div>
        </header>
        <div class="px-3 py-4 md:px-6 md:py-6">
          <RouterView />
        </div>
      </main>
    </div>

    <transition name="fade">
      <div
        v-if="mobileMenuOpen"
        class="fixed inset-0 z-40 flex justify-end md:hidden"
      >
        <div class="flex-1 bg-slate-900/60" @click="mobileMenuOpen = false"></div>
        <div class="w-72 max-w-full bg-white p-5 shadow-2xl">
          <div class="mb-6 flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Menu</p>
              <p class="text-sm font-semibold text-slate-900 truncate">{{ agencyName || 'Agencia' }}</p>
            </div>
            <button
              type="button"
              class="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 text-slate-600"
              @click="mobileMenuOpen = false"
            >
              <span class="sr-only">Fechar</span>
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M6 6l12 12M6 18 18 6" />
              </svg>
            </button>
          </div>
          <nav class="space-y-1">
            <RouterLink
              v-for="item in navItems"
              :key="'mobile-' + item.to"
              :to="item.to"
              class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition"
              :class="isActive(item.to) ? activeClass : inactiveClass"
              @click="mobileMenuOpen = false"
            >
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-slate-600">
                <svg
                  :viewBox="navIconViewBoxes[item.to] || navIconViewBoxes.default"
                  :class="['h-4 w-4', navIconSizes[item.to]]"
                  :stroke-width="navIconStrokeWidths[item.to] || null"
                  v-html="navIcons[item.to] || navIcons.default"
                ></svg>
              </span>
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>
          <div class="mt-6 border-t border-slate-200 pt-4">
            <button
              type="button"
              @click="handleLogout"
              class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-red-50 hover:text-red-600"
            >
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-red-50 text-red-600">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 3v9m5.657-6.657a8 8 0 1 1-11.314 0" />
                </svg>
              </span>
              <span>Sair</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showWelcomeDialog"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Bem-vindo ao trial profissional</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Plano {{ trialPlanName }} liberado até {{ formattedDate }}</h2>
          <p class="mt-2 text-sm text-slate-600">
            Durante estes 7 dias você pode testar tudo que usamos nos planos pagos:
          </p>
          <ul class="mt-4 list-disc space-y-1 pl-6 text-sm text-slate-600">
            <li>Criar até 3 páginas completas, com seções ilimitadas.</li>
            <li>Duplicar roteiros, personalizar blocos premium e usar pixels ilimitados.</li>
            <li>Publicar páginas sem rodapé da versão gratuita e acompanhar métricas em tempo real.</li>
          </ul>
          <p class="mt-4 text-sm text-slate-600">Explore à vontade e peça ajuda se quiser montar um roteiro profissional.</p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="startAgencySetupFlow"
            >
              Começar agora
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showAgencySetupFlow"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/80 px-4 py-6"
      >
        <div class="w-full max-w-2xl rounded-3xl bg-white p-8 shadow-2xl">
          <template v-if="agencySetupStep === 'name'">
            <div class="space-y-6">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Comece por aqui</p>
                <h2 class="mt-3 text-3xl font-bold text-slate-900">Qual nome da sua agência?</h2>
                <p class="mt-2 text-base text-slate-500">Esse nome aparece no painel e nas páginas. Você pode alterar depois.</p>
              </div>
              <div>
                <label class="text-sm font-semibold text-slate-600">Nome da agência</label>
                <input
                  v-model="agencySetupForm.name"
                  class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-lg font-semibold text-slate-900"
                  placeholder="Ex.: MariaTur"
                />
              </div>
              <p v-if="agencySetupError" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
                {{ agencySetupError }}
              </p>
              <div class="mt-6 flex flex-wrap justify-end gap-3">
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50" @click="requestAgencySetupClose">
                  Fechar
                </button>
                <button
                  class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
                  @click="goToNextAgencySetupStep"
                  :disabled="agencySetupStepLoading"
                >
                  {{ agencySetupStepLoading ? "Avançando..." : "Avançar" }}
                </button>
              </div>
            </div>
          </template>
          <template v-else-if="agencySetupStep === 'logo'">
            <div class="space-y-6">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Personalize</p>
                <h2 class="mt-3 text-3xl font-bold text-slate-900">Logo da sua agência</h2>
                <p class="mt-2 text-base text-slate-500">Envie o arquivo da sua marca. Você pode trocar depois.</p>
              </div>
              <ImageUploadField
                v-model="agencySetupForm.logo_url"
                label="Logo"
                hint="Formatos permitidos: JPG e PNG · Tamanho máximo: 10MB"
                :enable-crop="true"
                editor-title="Ajuste a logo da agência"
              />
              <p v-if="agencySetupError" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
                {{ agencySetupError }}
              </p>
              <div class="mt-6 flex flex-wrap justify-end gap-3">
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50" @click="requestAgencySetupClose">
                  Fechar
                </button>
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="goToPreviousAgencySetupStep">
                  Voltar
                </button>
                <button
                  class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark"
                  @click="goToNextAgencySetupStep"
                >
                  Avançar
                </button>
              </div>
            </div>
          </template>
          <template v-else-if="agencySetupStep === 'color'">
            <div class="space-y-6">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Defina o estilo</p>
                <h2 class="mt-3 text-3xl font-bold text-slate-900">Qual a cor principal da sua agência?</h2>
                <p class="mt-2 text-base text-slate-500">Usamos essa cor nos botões e destaques padrão do editor.</p>
              </div>
              <div class="flex flex-col gap-4 rounded-2xl border border-slate-100 p-4">
                <div class="flex items-center gap-4">
                  <div class="flex flex-col items-center">
                    <input
                      type="color"
                      v-model="agencySetupForm.primary_color"
                      class="h-16 w-16 cursor-pointer rounded-full border border-slate-200 bg-white p-2"
                    />
                    <span class="mt-2 text-xs font-semibold text-slate-500">Clique aqui para alterar</span>
                  </div>
                  <div class="flex-1">
                    <label class="text-sm font-semibold text-slate-600">Código hexadecimal</label>
                    <input
                      v-model="agencySetupForm.primary_color"
                      placeholder="#41ce5f"
                      class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-lg font-semibold uppercase tracking-wide text-slate-900"
                    />
                  </div>
                </div>
              </div>
              <p v-if="agencySetupError" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
                {{ agencySetupError }}
              </p>
              <div class="mt-6 flex flex-wrap justify-end gap-3">
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50" @click="requestAgencySetupClose">
                  Fechar
                </button>
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="goToPreviousAgencySetupStep">
                  Voltar
                </button>
                <button
                  class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
                  @click="submitAgencySetup"
                  :disabled="agencySetupSaving"
                >
                  {{ agencySetupSaving ? "Criando..." : "Criar agência" }}
                </button>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="space-y-6 text-center">
              <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <svg viewBox="0 0 24 24" class="h-8 w-8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h2 class="text-3xl font-bold text-slate-900">Parabéns, sua agência foi criada!</h2>
                <p class="mt-3 text-base text-slate-500">Agora você pode criar sua primeira página personalizada.</p>
              </div>
              <p v-if="createFirstPageError" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
                {{ createFirstPageError }}
              </p>
              <div class="mt-6 flex flex-wrap justify-center gap-3">
                <button class="rounded-full border border-slate-200 px-6 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="closeAgencySetupFlow">
                  Fechar
                </button>
                <button
                  class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
                  @click="createFirstPageFromOnboarding"
                  :disabled="createFirstPageLoading"
                >
                  {{ createFirstPageLoading ? "Criando..." : "Criar minha primeira página" }}
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showAgencySetupUnsavedDialog"
        class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-md rounded-3xl bg-white p-6 text-center shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-500">Atenção</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Há alterações não salvas</h2>
          <p class="mt-2 text-sm text-slate-600">Se fechar agora, você perderá o que preencheu. Deseja realmente sair?</p>
          <div class="mt-6 flex flex-wrap justify-center gap-3">
            <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50" @click="keepAgencySetupEditing">
              Continuar editando
            </button>
            <button class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark" @click="confirmAgencySetupDiscard">
              Descartar e fechar
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showTrialWarning3Days"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-500">Faltam 3 dias</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Seu periodo trial termina em breve</h2>
          <p class="mt-2 text-sm text-slate-600">
            Em 3 dias o acesso ao editor sera bloqueado. Escolha um plano para continuar criando roteiros ilimitados.
          </p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="acknowledgeTrial('warn3')"
            >
              Depois
            </button>
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="acknowledgeTrial('warn3', true)"
            >
              Ver planos
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showTrialWarning1Day"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">Últimas horas</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Seu trial termina amanha</h2>
          <p class="mt-2 text-sm text-slate-600">
            Contrate agora para manter suas paginas ativas e seguir publicando novos roteiros sem interrupcao.
          </p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="acknowledgeTrial('warn1', true)"
            >
              Assinar agora
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showEndDialog"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">Trial encerrado</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Você atingiu o limite do plano trial</h2>
          <p class="mt-2 text-sm text-slate-600">Assine um plano para desbloquear seu painel e republicar seus roteiros.</p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="goToPlans"
            >
              Ir para os planos
            </button>
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="dismissBlockedModal"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showCookieConsent"
        class="fixed inset-x-6 bottom-4 z-50 md:left-1/2 md:top-auto md:bottom-8 md:-translate-x-1/2 md:w-3/4"
      >
        <div class="flex flex-col gap-2 rounded-3xl border border-slate-200 bg-white/95 p-4 shadow-2xl backdrop-blur">
          <div class="flex flex-col items-center gap-3 text-center md:flex-row md:items-center md:justify-center md:text-left">
            <div class="md:flex-1">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Cookies</p>
              <p class="text-sm text-slate-600">
                <span class="block">Utilizamos cookies e armazenamento local para manter sua sessão segura e salvar preferências.</span>
                <span class="block">Se optar por continuar sem aceitar, alguns recursos podem apresentar limitações.</span>
              </p>
            </div>
            <div class="flex w-full flex-wrap items-center justify-center gap-2 md:w-auto md:justify-center">
              <button
                type="button"
                class="order-1 text-[11px] font-semibold text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline md:order-none"
                @click="dismissCookies"
              >
                Continuar sem aceitar
              </button>
              <button
                type="button"
                class="order-2 w-full rounded-full bg-slate-900 px-5 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 md:order-none md:w-auto md:text-sm"
                @click="acceptCookies"
              >
                Aceitar cookies
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import SidebarLogo from "../assets/Logo Cor - Roteiro Online.png";
import ImageUploadField from "../components/admin/inputs/ImageUploadField.vue";
import api from "../services/api";
import { useAgencyStore } from "../store/useAgencyStore";
import { useAuthStore } from "../store/useAuthStore";
import { getPlanLabel } from "../utils/planLabels";
import { addTagsToContactByEmail, syncPlanTagForEmail, viajeChatTagIds } from "../services/viajeChat";
import { slugify } from "../utils/slugify";

const route = useRoute();
const router = useRouter();
const agencyStore = useAgencyStore();
const auth = useAuthStore();
const COOKIE_KEY = "global_cookie_consent";

const showCookieConsent = ref(false);

const navIcons: Record<string, string> = {
  default: '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 2a8 8 0 1 1-8 8 8 8 0 0 1 8-8zm0 3v6l4 2" />',
  "/admin/dashboard": '<path fill="none" stroke="currentColor" stroke-width="1.8" d="M4 5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1zm10 0a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1zM4 16a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1zm10-3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1z"/>' ,
  "/admin/pages": '<g fill="none" stroke="currentColor" stroke-width="2"><path d="M6.142 6.142C8.904 3.381 10.284 2 12 2s3.096 1.38 5.858 4.142S22 10.284 22 12s-1.38 3.096-4.142 5.858S13.716 22 12 22s-3.096-1.38-5.858-4.142S2 13.716 2 12s1.38-3.096 4.142-5.858Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M16 11.5L13.333 9M16 11.5L13.333 14M16 11.5h-5.333C9.777 11.5 8 12 8 14"/></g>',
  "/admin/integracoes": '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M18.364 19.364a9 9 0 1 0-12.728 0"/><path d="M15.536 16.536a5 5 0 1 0-7.072 0"/><path d="M11 13a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/></g>',
  "/admin/agency": '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.3" d="M4 11.452V16.8c0 1.12 0 1.68.218 2.109c.192.376.497.682.874.873c.427.218.987.218 2.105.218h9.606c1.118 0 1.677 0 2.104-.218a2 2 0 0 0 .875-.873c.218-.428.218-.987.218-2.105v-5.352c0-.534 0-.801-.065-1.05a2 2 0 0 0-.28-.617c-.145-.213-.345-.39-.748-.741l-4.8-4.2c-.746-.653-1.12-.98-1.54-1.104c-.37-.11-.764-.11-1.135 0c-.42.124-.792.45-1.538 1.102L5.093 9.044c-.402.352-.603.528-.747.74a2 2 0 0 0-.281.618C4 10.65 4 10.918 4 11.452"/>',
  "/admin/perfil": '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/></g>',
  "/admin/planos": '<path fill="currentColor" d="m21.41 11.58-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58s1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41s-.23-1.06-.59-1.42M13 20.01L4 11V4h7v-.01l9 9z"/><circle cx="6.5" cy="6.5" r="1.5" fill="currentColor"/>',
  "/admin/administracao": '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m12 17.75l-6.172 3.245l1.179-6.873l-5-4.867l6.9-1l3.086-6.253l3.086 6.253l6.9 1l-5 4.867l1.179 6.873z"/>',
  "/admin/aulas": '<path fill="currentColor" d="m164.44 105.34l-48-32A8 8 0 0 0 104 80v64a8 8 0 0 0 12.44 6.66l48-32a8 8 0 0 0 0-13.32M120 129.05V95l25.58 17ZM216 40H40a16 16 0 0 0-16 16v112a16 16 0 0 0 16 16h176a16 16 0 0 0 16-16V56a16 16 0 0 0-16-16m0 128H40V56h176zm16 40a8 8 0 0 1-8 8H32a8 8 0 0 1 0-16h192a8 8 0 0 1 8 8"/>' ,

};

const navIconSizes: Record<string, string> = {
  "/admin/agency": "h-4 w-4"
};

const navIconViewBoxes: Record<string, string> = {
  default: "0 0 24 24",
  "/admin/aulas": "0 0 256 256"
};

const navIconStrokeWidths: Record<string, string> = {};

const routeTitleMap: Record<string, string> = {
  dashboard: "Dashboard",
  pages: "Páginas",
  "page-edit": "Editar página",
  lessons: "Aulas",
  "agency-settings": "Minha Agência",
  plans: "Planos",
  integrations: "Integrações",
  profile: "Perfil",
  "admin-management": "Admin Master"
};

const navItems = computed(() => {
  const items = [
    { label: "Dashboard", to: "/admin/dashboard" },
    { label: "Páginas", to: "/admin/pages" },
    { label: "Integrações", to: "/admin/integracoes" },
    { label: "Minha Agência", to: "/admin/agency" },
    { label: "Perfil", to: "/admin/perfil" },
    { label: "Aulas", to: "/admin/aulas" }
  ];
  if (auth.user?.is_superuser) {
    items.splice(1, 0, { label: "Admin Master", to: "/admin/administracao" });
  }
  return items;
});

const currentPageTitle = computed(() => {
  const routeName = typeof route.name === "string" ? route.name : null;
  if (routeName && routeTitleMap[routeName]) {
    return routeTitleMap[routeName];
  }
  const matchedNav = navItems.value.find(item => route.path.startsWith(item.to));
  return matchedNav?.label || "Dashboard";
});

const activeClass = "bg-slate-100 text-slate-900";
const inactiveClass = "text-slate-700 hover:bg-slate-100";

const agencyName = computed(() => agencyStore.currentAgency?.name || agencyStore.agencies[0]?.name || "");
const sidebarLogoSrc = SidebarLogo;

const isActive = (to: string) => route.path.startsWith(to);

const checkCookieConsent = () => {
  if (typeof window === "undefined") return;
  const consent = localStorage.getItem(COOKIE_KEY);
  showCookieConsent.value = !consent;
};

const acceptCookies = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem(COOKIE_KEY, "accepted");
  }
  showCookieConsent.value = false;
};

const dismissCookies = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem(COOKIE_KEY, "dismissed");
  }
  showCookieConsent.value = false;
};

const handleLogout = () => {
  auth.logout();
  router.push({ name: "login" });
};

const showWelcomeDialog = ref(false);
const showEndDialog = ref(false);
const showTrialWarning3Days = ref(false);
const showTrialWarning1Day = ref(false);
const mobileMenuOpen = ref(false);
const trialPlanName = computed(() => getPlanLabel(auth.user?.trial_plan));
const trialModalDismissed = ref(false);
const planTagMap: Record<string, string> = {
  essencial: viajeChatTagIds.PLANO_PROFISSIONAL,
  growth: viajeChatTagIds.PLANO_AGENCIA,
  infinity: viajeChatTagIds.PLANO_ESCALA
};
const planTagIds = Object.values(planTagMap);
const lastSyncedPlan = ref<string | null>(null);
let planTagSyncQueue = Promise.resolve();

type AgencySetupStep = "name" | "logo" | "color" | "success";
interface AgencySetupFormState {
  name: string;
  logo_url: string | null;
  primary_color: string;
}

const DEFAULT_AGENCY_COLOR = "#41ce5f";
const createEmptyAgencySetup = (): AgencySetupFormState => ({
  name: "",
  logo_url: null,
  primary_color: DEFAULT_AGENCY_COLOR
});

const agencySetupForm = reactive<AgencySetupFormState>(createEmptyAgencySetup());
const agencySetupStep = ref<AgencySetupStep>("name");
const showAgencySetupFlow = ref(false);
const agencySetupCreatedId = ref<number | null>(null);
const agencySetupSaving = ref(false);
const agencySetupStepLoading = ref(false);
const agencySetupError = ref("");
const createFirstPageLoading = ref(false);
const createFirstPageError = ref("");
const showAgencySetupUnsavedDialog = ref(false);

const serializeAgencySetup = () => ({
  name: agencySetupForm.name || "",
  logo_url: agencySetupForm.logo_url || null,
  primary_color: agencySetupForm.primary_color || DEFAULT_AGENCY_COLOR
});

const agencySetupSnapshot = ref(JSON.stringify(serializeAgencySetup()));
const agencySetupDirty = computed(
  () => showAgencySetupFlow.value && JSON.stringify(serializeAgencySetup()) !== agencySetupSnapshot.value
);

const markAgencySetupSnapshot = () => {
  agencySetupSnapshot.value = JSON.stringify(serializeAgencySetup());
};

const resetAgencySetupForm = () => {
  agencySetupForm.name = "";
  agencySetupForm.logo_url = null;
  agencySetupForm.primary_color = DEFAULT_AGENCY_COLOR;
  agencySetupStep.value = "name";
  agencySetupError.value = "";
  createFirstPageError.value = "";
  createFirstPageLoading.value = false;
  agencySetupCreatedId.value = null;
  agencySetupStepLoading.value = false;
  markAgencySetupSnapshot();
};

markAgencySetupSnapshot();

const trialStartDate = computed(() => (auth.user?.trial_started_at ? new Date(auth.user.trial_started_at) : null));
const trialEndDate = computed(() => (auth.user?.trial_ends_at ? new Date(auth.user.trial_ends_at) : null));
const trialActive = computed(() => {
  if (!auth.user?.trial_plan) return false;
  if (!trialStartDate.value || !trialEndDate.value) return false;
  const now = new Date();
  return now >= trialStartDate.value && now <= trialEndDate.value;
});
const trialBlocked = computed(() => Boolean(auth.user?.trial_blocked));
const trialDaysLeft = computed(() => {
  if (!trialActive.value || !trialEndDate.value) return null;
  const diff = trialEndDate.value.getTime() - Date.now();
  if (diff <= 0) return 0;
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
});

watch(
  () => [auth.user?.id, trialActive.value, auth.user?.trial_ack_start],
  () => {
    showWelcomeDialog.value = Boolean(trialActive.value && auth.user?.trial_ack_start === false);
  },
  { immediate: true }
);

watch(
  () => route.path,
  () => {
    mobileMenuOpen.value = false;
    scrollToTop();
  }
);

watch(
  () => [trialBlocked.value, route.fullPath],
  () => {
    if (trialBlocked.value) {
      if (route.path !== "/admin/planos" && route.path !== "/admin/dashboard") {
        router.push("/admin/planos");
        trialModalDismissed.value = false;
        showEndDialog.value = false;
        return;
      }
      if (route.path === "/admin/dashboard" && !trialModalDismissed.value) {
        showEndDialog.value = true;
      } else {
        showEndDialog.value = false;
      }
    } else {
      showEndDialog.value = false;
      trialModalDismissed.value = false;
    }
  },
  { immediate: true }
);

watch(
  () => [trialActive.value, auth.user?.trial_warn_3days_ack, trialDaysLeft.value],
  () => {
    const daysLeft = trialDaysLeft.value;
    showTrialWarning3Days.value = Boolean(
      trialActive.value && auth.user?.trial_warn_3days_ack === false && daysLeft !== null && daysLeft <= 3 && daysLeft > 1
    );
  },
  { immediate: true }
);

watch(
  () => [trialActive.value, auth.user?.trial_warn_1day_ack, trialDaysLeft.value],
  () => {
    const daysLeft = trialDaysLeft.value;
    showTrialWarning1Day.value = Boolean(
      trialActive.value && auth.user?.trial_warn_1day_ack === false && daysLeft !== null && daysLeft <= 1
    );
  },
  { immediate: true }
);

const dismissBlockedModal = () => {
  trialModalDismissed.value = true;
  showEndDialog.value = false;
};

const goToPlans = () => {
  router.push("/admin/planos");
};

const acknowledgeTrial = async (stage: "start" | "end" | "warn3" | "warn1", redirectToPlans = false) => {
  try {
    await api.post("/auth/trial/ack", { stage });
    await auth.fetchProfile();
    if (stage === "start") {
      showWelcomeDialog.value = false;
    } else if (stage === "warn3") {
      showTrialWarning3Days.value = false;
    } else if (stage === "warn1") {
      showTrialWarning1Day.value = false;
      showTrialWarning3Days.value = false;
    } else {
      showEndDialog.value = false;
    }
    if (redirectToPlans) {
      goToPlans();
    }
  } catch (err) {
    console.error("Erro ao confirmar trial", err);
  }
};

const ensureAgencySelection = (id: number | null) => {
  if (!id) return;
  agencyStore.currentAgencyId = id;
};

const isSlugInUseError = (detail?: string | null) => {
  if (!detail) return false;
  const normalized = detail.toLowerCase();
  return normalized.includes("slug") && (normalized.includes("uso") || normalized.includes("use"));
};

type AgencyPayload = {
  name: string;
  primary_color?: string | null;
  secondary_color?: string | null;
  logo_url?: string | null;
  cta_whatsapp?: string | null;
};

const createAgencyWithSlugFallback = async (payload: AgencyPayload) => {
  const baseSlug = slugify(payload.name, "agencia");
  const maxAttempts = 8;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const suffix = attempt === 0 ? "" : `-${attempt}`;
    const slugCandidate = `${baseSlug}${suffix}`;
    try {
      const res = await api.post("/agencies", { ...payload, slug: slugCandidate });
      return res;
    } catch (err) {
      const detail = (err as any)?.response?.data?.detail || (err as Error)?.message;
      if (isSlugInUseError(detail)) continue;
      throw err;
    }
  }
  throw new Error("Não foi possível gerar um slug disponível para esta agência. Ajuste o nome e tente novamente.");
};

const upsertAgencyDuringSetup = async (name: string) => {
  const payload: AgencyPayload = {
    name,
    primary_color: agencySetupForm.primary_color || DEFAULT_AGENCY_COLOR,
    secondary_color: agencySetupForm.secondary_color || null,
    logo_url: agencySetupForm.logo_url || null,
    cta_whatsapp: ""
  };
  if (!agencySetupCreatedId.value) {
    const res = await createAgencyWithSlugFallback(payload);
    const createdId = res.data?.id ?? null;
    agencySetupCreatedId.value = createdId;
    await agencyStore.loadAgencies();
    ensureAgencySelection(createdId);
    return createdId;
  }
  const targetId = agencySetupCreatedId.value;
  await api.put(`/agencies/${targetId}`, {
    ...payload,
    slug: slugify(name, "agencia")
  });
  await agencyStore.loadAgencies();
  ensureAgencySelection(targetId);
  return targetId;
};

const startAgencySetupFlow = async () => {
  await acknowledgeTrial("start");
  resetAgencySetupForm();
  showAgencySetupFlow.value = true;
};

const goToNextAgencySetupStep = async () => {
  if (agencySetupStepLoading.value) return;
  agencySetupError.value = "";
  if (agencySetupStep.value === "name") {
    const trimmed = agencySetupForm.name.trim();
    if (!trimmed) {
      agencySetupError.value = "Informe o nome da sua agência.";
      return;
    }
    agencySetupForm.name = trimmed;
    agencySetupStepLoading.value = true;
    try {
      await upsertAgencyDuringSetup(trimmed);
      agencySetupStep.value = "logo";
    } catch (err) {
      console.error(err);
      const detail = (err as any)?.response?.data?.detail || (err as Error)?.message;
      agencySetupError.value = detail || "Não foi possível avançar. Tente novamente.";
    } finally {
      agencySetupStepLoading.value = false;
    }
    return;
  }
  if (agencySetupStep.value === "logo") {
    agencySetupStep.value = "color";
  }
};

const goToPreviousAgencySetupStep = () => {
  agencySetupError.value = "";
  if (agencySetupStep.value === "logo") {
    agencySetupStep.value = "name";
  } else if (agencySetupStep.value === "color") {
    agencySetupStep.value = "logo";
  }
};

const closeAgencySetupFlow = () => {
  showAgencySetupFlow.value = false;
  showAgencySetupUnsavedDialog.value = false;
  resetAgencySetupForm();
};

const requestAgencySetupClose = () => {
  if (agencySetupStepLoading.value || agencySetupSaving.value) return;
  if (agencySetupDirty.value) {
    showAgencySetupUnsavedDialog.value = true;
    return;
  }
  closeAgencySetupFlow();
};

const keepAgencySetupEditing = () => {
  showAgencySetupUnsavedDialog.value = false;
};

const confirmAgencySetupDiscard = () => {
  showAgencySetupUnsavedDialog.value = false;
  closeAgencySetupFlow();
};

const submitAgencySetup = async () => {
  if (agencySetupSaving.value) return;
  agencySetupError.value = "";
  const trimmed = agencySetupForm.name.trim();
  if (!trimmed) {
    agencySetupStep.value = "name";
    agencySetupError.value = "Informe o nome da sua agência.";
    return;
  }

  const payload: AgencyPayload = {
    name: trimmed,
    logo_url: agencySetupForm.logo_url || null,
    primary_color: agencySetupForm.primary_color || DEFAULT_AGENCY_COLOR,
    secondary_color: agencySetupForm.secondary_color || null,
    cta_whatsapp: ""
  };

  try {
    agencySetupSaving.value = true;
    let agencyId = agencySetupCreatedId.value;
    if (!agencyId) {
      const res = await createAgencyWithSlugFallback(payload);
      agencyId = res.data?.id ?? null;
      agencySetupCreatedId.value = agencyId;
    } else {
      await api.put(`/agencies/${agencyId}`, {
        ...payload,
        slug: slugify(trimmed, "agencia")
      });
    }
    await agencyStore.loadAgencies();
    ensureAgencySelection(agencyId ?? null);
    if (auth.user?.email) {
      await addTagsToContactByEmail(auth.user.email, [viajeChatTagIds.AGENCIA_CRIADA]);
    }
    agencySetupStep.value = "success";
    agencySetupError.value = "";
    markAgencySetupSnapshot();
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail || (err as Error)?.message;
    agencySetupError.value = detail || "Não foi possível criar a agência. Tente novamente.";
  } finally {
    agencySetupSaving.value = false;
  }
};

const createFirstPageFromOnboarding = async () => {
  if (!agencyStore.currentAgencyId && agencySetupCreatedId.value) {
    ensureAgencySelection(agencySetupCreatedId.value);
  }
  if (!agencyStore.currentAgencyId) {
    createFirstPageError.value = "Crie sua agência antes de adicionar páginas.";
    return;
  }
  createFirstPageError.value = "";
  try {
    createFirstPageLoading.value = true;
    const slug = slugify(`${agencySetupForm.name || "pagina"}-inicial`, "pagina");
    const res = await api.post<{ id: number }>("/pages", {
      agency_id: agencyStore.currentAgencyId,
      title: "Meu primeiro roteiro",
      slug,
      status: "draft"
    });
    closeAgencySetupFlow();
    router.push(`/admin/pages/${res.data.id}/edit`);
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail || (err as Error)?.message;
    createFirstPageError.value = detail || "Não foi possível criar a página agora.";
  } finally {
    createFirstPageLoading.value = false;
  }
};

const formattedDate = computed(() => (trialEndDate.value ? trialEndDate.value.toLocaleDateString() : ""));
const scrollToTop = () => {
  if (typeof window === "undefined") return;
  window.scrollTo({ top: 0, behavior: "auto" });
};

onMounted(async () => {
  if (!agencyStore.agencies.length) {
    await agencyStore.loadAgencies();
  }
  if (!agencyStore.currentAgencyId && agencyStore.agencies.length) {
    agencyStore.currentAgencyId = agencyStore.agencies[0].id;
  }
  if (!auth.user && auth.token) {
    await auth.fetchProfile();
  }
  checkCookieConsent();
  scrollToTop();
});

watch(
  () => agencyStore.agencies.length,
  length => {
    if (!agencyStore.currentAgencyId && length > 0) {
      agencyStore.currentAgencyId = agencyStore.agencies[0].id;
    }
  }
);

const queuePlanTagSync = (plan: string | null | undefined) => {
  const email = auth.user?.email;
  if (!email) return;
  const normalizedPlan = plan ?? null;
  const desiredTagId = normalizedPlan ? planTagMap[normalizedPlan] ?? null : null;
  planTagSyncQueue = planTagSyncQueue
    .catch(() => {})
    .then(async () => {
      await syncPlanTagForEmail(email, desiredTagId ?? null, planTagIds);
      lastSyncedPlan.value = normalizedPlan;
    });
};

watch(
  () => auth.user?.plan,
  plan => {
    const normalizedPlan = plan ?? null;
    if (normalizedPlan === lastSyncedPlan.value) return;
    queuePlanTagSync(normalizedPlan);
  },
  { immediate: true }
);

watch(
  () => auth.user?.email,
  () => {
    lastSyncedPlan.value = null;
  }
);
</script>

<style>
.light-theme {
  background: #f8fafc;
  color: #0f172a;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>





