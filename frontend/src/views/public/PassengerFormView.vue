<template>
  <div class="passenger-page relative min-h-screen bg-slate-50 px-4 py-6 text-slate-950 sm:px-6">
    <div class="passenger-page__bg-shape"></div>

    <div
      class="passenger-page__container relative z-10 mx-auto grid w-full gap-5"
      :class="{ 'passenger-page__container--seats': viewMode === 'seats' }"
    >
      <ReservationWizardHeader
        :agency-name="agencyName"
        :agency-initials="agencyInitials"
        :logo-url="agencyLogoUrl"
        :eyebrow="'Preenchimento da reserva'"
        :title="wizardHeaderTitle"
        :subtitle="wizardHeaderSubtitle"
        :support-href="supportWhatsappHref"
        :payment-label="currentStep === 1 ? paymentStatusLabel(formInfo?.payment_status || 'processing') : null"
        :show-back="true"
        :back-label="currentStep === 1 ? 'Voltar' : 'Voltar para passageiros'"
        @back="handleWizardBack"
      />

      <ReservationWizardStepper
        :steps="wizardSteps"
      />

      <section v-if="false" class="hero-card flex flex-col gap-5 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-center md:justify-between">
        <div class="hero-card__brand flex items-center gap-4">
          <div class="hero-card__logo grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-2xl bg-white ring-1 ring-slate-200">
            <img
              v-if="agencyLogoUrl"
              :src="agencyLogoUrl"
              :alt="agencyName"
              class="h-full w-full object-contain p-1.5"
            />
            <span v-else class="text-sm font-extrabold tracking-widest text-emerald-700">{{ agencyInitials }}</span>
          </div>
          <div>
            <p class="hero-card__eyebrow text-xs font-bold uppercase tracking-[0.18em] text-emerald-700">Preenchimento de passageiros</p>
            <h1 class="hero-card__title mt-1 text-2xl font-extrabold leading-tight text-slate-950 sm:text-3xl">Sua reserva foi confirmada</h1>
            <p class="hero-card__subtitle mt-1 text-sm leading-6 text-slate-600">Complete os dados dos viajantes para finalizar a organização da sua compra.</p>
          </div>
        </div>

        <div class="hero-card__actions flex flex-wrap gap-2 md:justify-end">
          <a
            v-if="supportWhatsappHref"
            :href="supportWhatsappHref"
            target="_blank"
            rel="noopener"
            class="hero-action hero-action--support rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-700 transition hover:border-emerald-300"
          >
            Suporte WhatsApp
          </a>
          <button
            v-else
            type="button"
            class="hero-action hero-action--support hero-action--disabled rounded-full border border-emerald-100 bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-700 opacity-50"
            disabled
          >
            Suporte WhatsApp
          </button>
          <button type="button" class="hero-action rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 transition hover:border-slate-300" @click="$router.back()">Voltar</button>
          <span class="hero-status rounded-full border border-emerald-200 bg-emerald-100 px-4 py-2 text-sm font-bold text-emerald-800">{{ paymentStatusLabel(formInfo?.payment_status || "processing") }}</span>
        </div>
      </section>

      <section v-if="false" class="seat-stage-header">
        <div class="seat-stage-header__brand">
          <div class="seat-stage-header__logo">
            <img
              v-if="agencyLogoUrl"
              :src="agencyLogoUrl"
              :alt="agencyName"
              class="h-full w-full object-contain p-1.5"
            />
            <span v-else>{{ agencyInitials }}</span>
          </div>
          <div class="seat-stage-header__copy">
            <h1>Selecao de assentos</h1>
            <p>
              {{ seatHeaderMeta }}
            </p>
          </div>
        </div>

        <div class="seat-stage-header__actions">
          <button type="button" class="seat-stage-action" @click="viewMode = 'passengers'">Voltar</button>
          <a
            v-if="supportWhatsappHref"
            :href="supportWhatsappHref"
            target="_blank"
            rel="noopener"
            class="seat-stage-action seat-stage-action--support"
          >
            Suporte
          </a>
        </div>
      </section>

      <transition name="step-swap" mode="out-in">
      <div v-if="viewMode === 'passengers'" key="passenger-form" class="passenger-layout grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
        <main class="passenger-main min-w-0">
          <section class="section-card section-card--main grid gap-5 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="section-head flex flex-col gap-3 border-b border-slate-100 pb-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="section-head__eyebrow text-xs font-bold uppercase tracking-[0.18em] text-slate-400">Produtos da reserva</p>
                <h2 class="section-head__title mt-1 text-lg font-extrabold text-slate-950">Selecione o produto</h2>
              </div>
              <button
                type="button"
                class="section-refresh rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 transition hover:border-slate-300 disabled:opacity-50"
                :disabled="groupsLoading"
                @click="loadPassengerGroups"
              >
                Atualizar lista
              </button>
            </div>

            <template v-if="loading || groupsLoading">
              <div class="state-card rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm font-semibold text-slate-500">Carregando formulário...</div>
            </template>

            <template v-else-if="!passengerGroups.length">
              <div class="state-card rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm font-semibold text-slate-500">Nenhum grupo disponível.</div>
            </template>

            <template v-else>
              <div class="product-tabs flex gap-3 overflow-x-auto pb-2">
                <button
                  v-for="(product, index) in productSections"
                  :key="product.key"
                  type="button"
                  class="product-tab flex min-w-[260px] items-center gap-3 rounded-2xl border bg-slate-50 p-3 text-left transition hover:-translate-y-0.5 hover:border-slate-300"
                  :class="index === activeProductIndex ? 'border-emerald-300 bg-emerald-50 shadow-sm shadow-emerald-100' : 'border-slate-200'"
                  @click="selectProduct(index)"
                >
                  <div class="product-tab__thumb grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-xl bg-slate-200 text-xs font-extrabold text-slate-700">
                    <img
                      v-if="productImageUrl(product.groups[0])"
                      :src="productImageUrl(product.groups[0]) || undefined"
                      :alt="product.name"
                      class="h-full w-full object-cover"
                    />
                    <span v-else>{{ groupInitials(product.name) }}</span>
                  </div>

                  <div class="product-tab__content min-w-0">
                    <p class="product-tab__title truncate text-sm font-extrabold text-slate-950">{{ product.name }}</p>
                    <p class="product-tab__meta mt-0.5 text-xs font-semibold text-slate-500">{{ product.groups.length }} pacote(s)</p>
                    <p class="product-tab__pending mt-1 text-xs font-bold text-emerald-700">{{ product.pending }} pendente(s)</p>
                  </div>
                </button>
              </div>

              <div v-if="activeProductGroups.length" class="grid gap-2">
                <p class="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">Pacotes do produto</p>
                <div class="flex gap-3 overflow-x-auto pb-2">
                  <button
                    v-for="group in activeProductGroups"
                    :key="group.id"
                    type="button"
                    class="flex min-w-[230px] items-center gap-3 rounded-2xl border bg-slate-50 p-3 text-left transition hover:border-slate-300"
                    :class="group.id === activeGroup?.id ? 'border-slate-950 bg-white shadow-sm' : 'border-slate-200'"
                    @click="selectGroupById(group.id)"
                  >
                    <div class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-white text-xs font-extrabold text-slate-700 ring-1 ring-slate-200">
                      {{ groupInitials(group.label) }}
                    </div>
                    <div class="min-w-0">
                      <p class="truncate text-sm font-extrabold text-slate-950">{{ groupPackageName(group) }}</p>
                      <p v-if="group.label !== groupPackageName(group)" class="mt-0.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">{{ group.label }}</p>
                      <p class="mt-0.5 text-xs font-semibold text-slate-500">{{ groupMetaLine(group) }}</p>
                      <p class="mt-1 text-xs font-bold text-emerald-700">{{ groupCompletedCount(group) }}/{{ group.capacity }} preenchidos</p>
                    </div>
                  </button>
                </div>
              </div>

              <transition name="fade-slide" mode="out-in">
                <article v-if="activeGroup" :key="activeGroup.id" class="active-product grid gap-5 rounded-3xl border border-slate-200 bg-white p-5">
                  <div class="active-product__hero grid gap-4 sm:grid-cols-[88px_minmax(0,1fr)] lg:grid-cols-[88px_minmax(0,1fr)_auto] lg:items-center">
                    <div class="active-product__image grid h-[88px] w-[88px] place-items-center overflow-hidden rounded-2xl bg-emerald-100 text-sm font-extrabold text-emerald-700">
                      <img
                        v-if="productImageUrl(activeGroup)"
                        :src="productImageUrl(activeGroup) || undefined"
                        :alt="groupProductName(activeGroup)"
                        class="h-full w-full object-cover"
                      />
                      <span v-else>{{ groupInitials(groupProductName(activeGroup)) }}</span>
                    </div>

                    <div class="active-product__copy min-w-0">
                      <p class="active-product__eyebrow text-xs font-bold uppercase tracking-[0.18em] text-slate-400">{{ activeProductSection?.name }}</p>
                      <h3 class="active-product__title mt-1 text-2xl font-extrabold leading-tight text-slate-950">{{ groupPackageName(activeGroup) }}</h3>
                      <p class="active-product__meta mt-1 text-sm font-semibold text-slate-600">{{ groupMetaLine(activeGroup) }}</p>
                      <p class="active-product__helper mt-1 text-sm text-slate-500">
                        {{ groupPendingCount(activeGroup) }} passageiro(s) pendente(s) neste produto.
                      </p>
                    </div>

                    <span class="active-product__badge w-fit rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-extrabold text-emerald-800">
                      {{ activeGroupCompletedCount }} / {{ activeGroup.capacity }} preenchidos
                    </span>
                  </div>

                  <div class="progress-panel rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div class="progress-panel__head flex justify-between gap-3 text-sm font-bold text-slate-700">
                      <p>Passageiros preenchidos: {{ activeGroupCompletedCount }} de {{ activeGroup.capacity }}</p>
                      <strong>{{ activeGroupProgressPercent }}%</strong>
                    </div>
                    <div class="progress-track mt-3 h-2.5 overflow-hidden rounded-full bg-slate-200">
                      <div class="progress-track__bar h-full rounded-full bg-emerald-600 transition-all" :style="{ width: `${activeGroupProgressPercent}%` }"></div>
                    </div>
                  </div>

                  <div class="passenger-tabs flex gap-2 overflow-x-auto pb-1">
                    <button
                      v-for="(passenger, index) in activeGroup.passengers"
                      :key="`slot-${passenger.passenger_index}`"
                      type="button"
                      class="passenger-tab grid min-w-[140px] gap-0.5 rounded-full border px-4 py-2 text-left text-xs font-extrabold transition"
                      :class="[
                        passengerChipState(passengerSlotState(passenger)),
                        index === activePassengerIndex ? 'passenger-tab--active border-emerald-600 bg-emerald-600 text-white' : '',
                      ]"
                      @click="selectPassenger(index)"
                    >
                      <span>Passageiro {{ passenger.passenger_index }}</span>
                      <small class="text-[10px] uppercase tracking-wider opacity-80">{{ passengerSlotLabel(passengerSlotState(passenger)) }}</small>
                    </button>
                  </div>

                  <form class="passenger-form rounded-3xl border border-slate-200 bg-slate-50 p-4" @submit.prevent>
                    <div v-if="activePassenger" class="passenger-form__grid grid gap-4 md:grid-cols-2">
                      <div>
                        <label class="input-label mb-1 block text-xs font-bold uppercase tracking-wider text-slate-500">Tipo</label>
                        <select v-model="activePassenger.type" class="input w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100">
                          <option value="adult">Adulto</option>
                          <option value="child_paid">Criança paga</option>
                          <option value="child_free">Criança gratuita</option>
                        </select>
                      </div>

                      <div>
                        <label class="input-label mb-1 block text-xs font-bold uppercase tracking-wider text-slate-500">Data nascimento</label>
                        <input v-model="activePassenger.birthdate" type="date" class="input w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100" />
                      </div>

                      <div>
                        <label class="input-label mb-1 block text-xs font-bold uppercase tracking-wider text-slate-500">Nome completo</label>
                        <input v-model="activePassenger.name" class="input w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100" placeholder="Nome completo" />
                      </div>

                      <div>
                        <label class="input-label mb-1 block text-xs font-bold uppercase tracking-wider text-slate-500">CPF</label>
                        <input v-model="activePassenger.cpf" class="input w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100" placeholder="000.000.000-00" />
                      </div>

                      <div>
                        <label class="input-label mb-1 block text-xs font-bold uppercase tracking-wider text-slate-500">Telefone</label>
                        <input v-model="activePassenger.phone" class="input w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100" placeholder="(00) 00000-0000" />
                      </div>

                      <div>
                        <label class="input-label mb-1 block text-xs font-bold uppercase tracking-wider text-slate-500">WhatsApp</label>
                        <input v-model="activePassenger.whatsapp" class="input w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100" placeholder="(00) 00000-0000" />
                      </div>

                      <div>
                        <label class="input-label mb-1 block text-xs font-bold uppercase tracking-wider text-slate-500">Local de embarque</label>
                        <select v-model="activePassenger.boarding_location" class="input w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100">
                          <option value="">Não definir</option>
                          <option v-for="option in boardingOptions" :key="option" :value="option">{{ option }}</option>
                        </select>
                      </div>

                      <div>
                        <label class="input-label mb-1 block text-xs font-bold uppercase tracking-wider text-slate-500">Observações</label>
                        <textarea
                          v-model="activePassenger.extras"
                          rows="3"
                          class="input w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100"
                          placeholder="Informações importantes"
                        ></textarea>
                      </div>
                    </div>
                  </form>

                  <p v-if="!boardingOptions.length" class="hint-text text-sm text-slate-500">
                    Nenhum local de embarque cadastrado para este produto.
                  </p>
                </article>
              </transition>

              <p v-if="errorMessage" class="feedback feedback--error rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{{ errorMessage }}</p>
              <p v-if="successMessage" class="feedback feedback--success rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-800">{{ successMessage }}</p>

              <div class="actions-row flex flex-wrap justify-end gap-3">
                <button class="btn btn--ghost rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-extrabold text-slate-700 transition hover:border-slate-300 disabled:opacity-50" type="button" :disabled="saving || !activeGroup" @click="saveCurrentGroup">
                  {{ saving && savingGroupMode === "group" ? "Salvando..." : "Salvar passageiro" }}
                </button>
                <button class="btn btn--soft rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm font-extrabold text-emerald-800 transition hover:border-emerald-300 disabled:opacity-50" type="button" :disabled="saving || !activeGroup" @click="goToNextPassenger">
                  Próximo passageiro
                </button>
                <button
                  type="button"
                  class="btn btn--primary rounded-2xl bg-emerald-600 px-5 py-3 text-sm font-extrabold text-white shadow-lg shadow-emerald-600/20 transition hover:bg-emerald-700 disabled:opacity-50"
                  :disabled="saving || !passengerGroups.length"
                  @click="submitPassengers"
                >
                  {{ saving && savingGroupMode === "all" ? "Salvando..." : primaryStepCtaLabel }}
                </button>
              </div>
            </template>
          </section>
        </main>

        <aside class="passenger-sidebar lg:sticky lg:top-5">
          <section class="summary-card grid gap-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p class="summary-card__eyebrow text-xs font-bold uppercase tracking-[0.18em] text-slate-400">Resumo da reserva</p>
            <h3 class="summary-card__title text-lg font-extrabold leading-tight text-slate-950">{{ formInfo?.product_title || "Reserva" }}</h3>
            <p class="summary-card__meta text-sm font-semibold text-slate-500">
              Venda #{{ formInfo?.sale_id || "-" }} • {{ saleChannelLabel(formInfo?.channel || "checkout") }}
            </p>

            <div class="summary-card__list grid gap-2">
              <article v-for="product in productSections" :key="`summary-${product.key}`" class="summary-item rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <p class="summary-item__name text-sm font-extrabold text-slate-900">{{ product.name }}</p>
                <p class="summary-item__sub mt-1 text-xs font-semibold text-slate-500">
                  {{ product.completed }}/{{ product.capacity }} preenchidos • {{ product.pending }} pendente(s)
                </p>
              </article>
            </div>

            <div class="summary-card__totals grid gap-2 border-t border-slate-100 pt-3 text-sm">
              <p class="flex justify-between gap-3 text-slate-600"><span>Preenchidos</span><strong class="text-slate-950">{{ completedSlots }}/{{ totalSlots }}</strong></p>
              <p class="flex justify-between gap-3 text-slate-600"><span>Pendentes</span><strong class="text-slate-950">{{ pendingSlots }}</strong></p>
              <p class="flex justify-between gap-3 text-slate-600"><span>Status</span><strong class="text-slate-950">{{ passengerStatusLabel(formInfo?.passenger_status || "pending") }}</strong></p>
            </div>

            <a
              v-if="supportWhatsappHref"
              :href="supportWhatsappHref"
              target="_blank"
              rel="noopener"
              class="summary-support rounded-full border border-emerald-200 bg-emerald-50 px-4 py-3 text-center text-sm font-extrabold text-emerald-800"
            >
              WhatsApp suporte
            </a>
          </section>
        </aside>
      </div>
      </transition>

      <transition name="step-swap">
      <SeatSelectionStep
        v-if="token && canUseSeatSelection && seatStepVisited"
        v-show="viewMode === 'seats'"
        key="seat-selection"
        :token="token"
        token-type="sale"
        :show-header="false"
        @back="viewMode = 'passengers'"
        @context-loaded="handleSeatSelectionContextLoaded"
        @updated="handleSeatSelectionUpdated"
      />
      </transition>
    </div>

    <div v-if="viewMode === 'passengers'" class="mobile-sticky-cta sticky bottom-0 z-30 border-t border-slate-200 bg-white/95 p-3 backdrop-blur lg:hidden">
      <button
        type="button"
        class="btn btn--primary w-full rounded-2xl bg-emerald-600 px-5 py-3 text-sm font-extrabold text-white shadow-lg shadow-emerald-600/20 transition hover:bg-emerald-700 disabled:opacity-50"
        :disabled="saving || !passengerGroups.length"
        @click="submitPassengers"
      >
        {{ saving && savingGroupMode === "all" ? "Salvando..." : primaryStepCtaLabel }}
      </button>
    </div>
  </div>

</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import ReservationWizardHeader from "../../components/public/ReservationWizardHeader.vue";
import ReservationWizardStepper from "../../components/public/ReservationWizardStepper.vue";
import SeatSelectionStep from "../../components/public/SeatSelectionStep.vue";
import {
  getPublicPassengerForm,
  getPublicPassengerGroups,
  savePublicPassengerGroup,
} from "../../services/finance";
import type { SeatSelectionContext } from "../../types/transport";
import type {
  Passenger,
  PassengerFormResponse,
  PassengerGroup,
  PassengerGroupSavePayload,
  PassengerType,
  SaleItem,
} from "../../types/finance";

type PassengerSlot = {
  id?: number;
  passenger_group_id: number;
  passenger_index: number;
  type: PassengerType;
  name: string;
  cpf?: string | null;
  birthdate?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  boarding_location?: string | null;
  extras?: string | null;
};

type PassengerGroupForm = PassengerGroup & { passengers: PassengerSlot[] };

type ProductSection = {
  key: string;
  name: string;
  groups: PassengerGroupForm[];
  capacity: number;
  completed: number;
  pending: number;
};

const route = useRoute();
const formInfo = ref<PassengerFormResponse | null>(null);
const loading = ref(false);
const groupsLoading = ref(false);
const saving = ref(false);
const savingGroupMode = ref<"group" | "all" | null>(null);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);
const passengerGroups = ref<PassengerGroupForm[]>([]);
const activeProductIndex = ref(0);
const activeGroupIndex = ref(0);
const activePassengerIndex = ref(0);
const viewMode = ref<"passengers" | "seats">("passengers");
const seatStepVisited = ref(false);
const seatSelectionContext = ref<SeatSelectionContext | null>(null);

let successTimer: ReturnType<typeof setTimeout> | null = null;

const token = computed(() => {
  const value = route.params.token;
  return typeof value === "string" ? value : null;
});

const agencyName = computed(() => formInfo.value?.agency_name || "Agência");
const agencyLogoUrl = computed(() => (formInfo.value?.agency_logo_url || "").trim());
const agencyInitials = computed(() => groupInitials(agencyName.value));

const supportWhatsappHref = computed(() => {
  const querySupport = typeof route.query.support === "string" ? route.query.support : "";
  const queryWhatsapp = typeof route.query.whatsapp === "string" ? route.query.whatsapp : "";
  const agencyWhatsapp = formInfo.value?.agency_whatsapp || "";
  const envSupport = (import.meta.env.VITE_PUBLIC_SUPPORT_WHATSAPP || "") as string;
  const raw = querySupport || queryWhatsapp || agencyWhatsapp || envSupport;
  const digits = raw.replace(/\D+/g, "");
  if (!digits) return "";
  const normalized = digits.startsWith("55") ? digits : `55${digits}`;
  const message = encodeURIComponent("Olá! Preciso de ajuda para preencher os passageiros da minha reserva.");
  return `https://wa.me/${normalized}?text=${message}`;
});

const formItems = computed<SaleItem[]>(() => formInfo.value?.items || []);
const formItemsMap = computed(() => new Map(formItems.value.map(item => [item.id, item])));
const activeGroup = computed(() => passengerGroups.value[activeGroupIndex.value] || null);
const activePassenger = computed(() => activeGroup.value?.passengers[activePassengerIndex.value] || null);
const boardingOptions = computed(() => formInfo.value?.boarding_locations || []);
const hasSeatMap = computed(() => Boolean(!formInfo.value?.contract_signature_link && formInfo.value?.is_road_trip));
const canUseSeatSelection = hasSeatMap;
const currentStep = computed<1 | 2>(() => (viewMode.value === "seats" ? 2 : 1));
const wizardHeaderTitle = computed(() => "Complete sua reserva");
const wizardHeaderSubtitle = computed(() =>
  currentStep.value === 1
    ? "Finalize os dados dos viajantes para concluir sua compra com seguranca."
    : "Finalize os ultimos detalhes da reserva e escolha os assentos dos passageiros."
);
const primaryStepCtaLabel = computed(() =>
  hasSeatMap.value ? "Continuar para assentos" : "Enviar passageiros"
);
const wizardSteps = computed(() => {
  const steps = [
    {
      key: "passengers",
      label: "Passageiros",
      hint: "Dados dos viajantes",
      state: currentStep.value === 1 ? "active" : "done",
    },
  ] as Array<{ key: string; label: string; hint: string; state: "done" | "active" | "upcoming" }>;

  if (hasSeatMap.value) {
    steps.push({
      key: "seats",
      label: "Assentos",
      hint: "Selecao do mapa",
      state: currentStep.value === 2 ? "active" : "upcoming",
    });
  }

  return steps;
});
const seatHeaderMeta = computed(() => {
  const ctx = seatSelectionContext.value;
  const product = ctx?.product_name || formInfo.value?.product_title || "Produto";
  const vehicle = ctx?.trip_vehicle?.display_name || "Veiculo 1";
  const occupancy = ctx?.trip_vehicle ? `${ctx.trip_vehicle.occupied_seats}/${ctx.trip_vehicle.capacity} ocupados` : "Ocupacao a confirmar";
  return `${product} • ${vehicle} • ${occupancy} • Etapa 2 de 2`;
});

const passengerSlotHasData = (slot?: PassengerSlot | null) => {
  if (!slot) return false;
  return Boolean(
    slot.name?.trim() ||
      slot.cpf?.trim() ||
      slot.phone?.trim() ||
      slot.whatsapp?.trim() ||
      slot.boarding_location?.trim() ||
      slot.extras?.trim(),
  );
};

const passengerSlotState = (slot?: PassengerSlot | null): "empty" | "partial" | "complete" => {
  if (!passengerSlotHasData(slot)) return "empty";
  if (slot?.name && slot?.cpf) return "complete";
  return "partial";
};

const passengerSlotLabel = (state: "empty" | "partial" | "complete") => {
  if (state === "complete") return "Completo";
  if (state === "partial") return "Incompleto";
  return "Livre";
};

const passengerChipState = (state: "empty" | "partial" | "complete") => {
  if (state === "complete") return "passenger-chip-complete";
  if (state === "partial") return "passenger-chip-partial";
  return "passenger-chip-empty";
};

const groupCompletedCount = (group: PassengerGroupForm) =>
  group.passengers.filter(slot => passengerSlotState(slot) === "complete").length;

const groupPendingCount = (group: PassengerGroupForm) => Math.max(group.capacity - groupCompletedCount(group), 0);

const groupProductKey = (group: PassengerGroupForm) => `${group.product_id || groupProductName(group)}`;

const groupProductName = (group: PassengerGroupForm) => {
  const item = saleItemByGroup(group);
  return item?.product_name || group.product_name || formInfo.value?.product_title || "Produto";
};

const groupPackageName = (group: PassengerGroupForm) => {
  const item = saleItemByGroup(group);
  return group.package_name || item?.variation_name || group.label || "Pacote";
};

const productSections = computed<ProductSection[]>(() => {
  const sections = new Map<string, ProductSection>();
  passengerGroups.value.forEach(group => {
    const key = groupProductKey(group);
    const current =
      sections.get(key) ||
      ({
        key,
        name: groupProductName(group),
        groups: [],
        capacity: 0,
        completed: 0,
        pending: 0,
      } satisfies ProductSection);

    const completed = groupCompletedCount(group);
    current.groups.push(group);
    current.capacity += group.capacity;
    current.completed += completed;
    current.pending += Math.max(group.capacity - completed, 0);
    sections.set(key, current);
  });
  return Array.from(sections.values());
});

const activeProductSection = computed(() => productSections.value[activeProductIndex.value] || productSections.value[0] || null);
const activeProductGroups = computed(() => activeProductSection.value?.groups || []);

const activeGroupCompletedCount = computed(() => (activeGroup.value ? groupCompletedCount(activeGroup.value) : 0));

const activeGroupProgressPercent = computed(() => {
  if (!activeGroup.value || !activeGroup.value.capacity) return 0;
  return Math.round((activeGroupCompletedCount.value / activeGroup.value.capacity) * 100);
});

const totalSlots = computed(() => passengerGroups.value.reduce((sum, group) => sum + group.capacity, 0));
const completedSlots = computed(() => passengerGroups.value.reduce((sum, group) => sum + groupCompletedCount(group), 0));
const pendingSlots = computed(() => Math.max(totalSlots.value - completedSlots.value, 0));

const setSuccessMessage = (message: string) => {
  successMessage.value = message;
  if (successTimer) clearTimeout(successTimer);
  successTimer = setTimeout(() => {
    successMessage.value = null;
  }, 2200);
};

const saleItemByGroup = (group: PassengerGroupForm) => formItemsMap.value.get(group.sale_item_id) || null;

const productImageUrl = (group?: PassengerGroupForm | null) => {
  if (!group) return null;
  const item = saleItemByGroup(group) as Record<string, unknown> | null;
  const fromProduct = typeof item?.product_image_url === "string" ? item.product_image_url : "";
  const fromLegacyItem = typeof item?.checkout_product_image_url === "string" ? item.checkout_product_image_url : "";
  const fromForm =
    typeof (formInfo.value as Record<string, unknown> | null)?.checkout_product_image_url === "string"
      ? ((formInfo.value as Record<string, unknown>).checkout_product_image_url as string)
      : "";
  const resolved = (fromProduct || fromLegacyItem || fromForm || "").trim();
  return resolved || null;
};

const groupInitials = (name: string) =>
  (name || "Produto")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part.charAt(0).toUpperCase())
    .join("");

const formatDateShort = (value?: string | null) => {
  if (!value) return "";
  const parsed = new Date(`${value}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return "";
  return new Intl.DateTimeFormat("pt-BR").format(parsed);
};

const groupMetaLine = (group: PassengerGroupForm) => {
  const item = saleItemByGroup(group);
  const date = formatDateShort(item?.departure_date || "");
  const time = (item?.departure_time || "").trim();
  const tokens = [date, time].filter(Boolean);
  if (tokens.length) return tokens.join(" • ");
  return `${group.capacity} passageiro(s)`;
};

const createSlot = (groupId: number, index: number, passenger?: Passenger): PassengerSlot => ({
  id: passenger?.id ?? undefined,
  passenger_group_id: groupId,
  passenger_index: index,
  type: (passenger?.type as PassengerType) || "adult",
  name: passenger?.name || "",
  cpf: passenger?.cpf || "",
  birthdate: passenger?.birthdate || "",
  phone: passenger?.phone || "",
  whatsapp: passenger?.whatsapp || "",
  boarding_location: passenger?.boarding_location || "",
  extras: passenger?.extras || "",
});

const normalizeGroup = (group: PassengerGroup): PassengerGroupForm => {
  const passengers: PassengerSlot[] = Array.from({ length: group.capacity }, (_, idx) => {
    const existing = (group.passengers || []).find(entry => entry.passenger_index === idx + 1);
    return createSlot(group.id, idx + 1, existing);
  });
  return { ...group, passengers };
};

const syncActiveProductFromGroup = (group: PassengerGroupForm) => {
  const productIndex = productSections.value.findIndex(product => product.key === groupProductKey(group));
  if (productIndex >= 0) {
    activeProductIndex.value = productIndex;
  }
};

const selectGroup = (index: number) => {
  if (!passengerGroups.value.length) return;
  const safeIndex = Math.max(0, Math.min(index, passengerGroups.value.length - 1));
  activeGroupIndex.value = safeIndex;
  const group = passengerGroups.value[safeIndex];
  syncActiveProductFromGroup(group);
  const nextPassenger = group.passengers.findIndex(slot => passengerSlotState(slot) !== "complete");
  activePassengerIndex.value = nextPassenger >= 0 ? nextPassenger : 0;
};

const selectGroupById = (groupId: number) => {
  const index = passengerGroups.value.findIndex(group => group.id === groupId);
  if (index >= 0) selectGroup(index);
};

const selectProduct = (index: number) => {
  if (!productSections.value.length) return;
  const safeIndex = Math.max(0, Math.min(index, productSections.value.length - 1));
  activeProductIndex.value = safeIndex;
  const product = productSections.value[safeIndex];
  const firstPending = product.groups.find(group => groupPendingCount(group) > 0);
  const nextGroup = firstPending || product.groups[0];
  if (nextGroup) selectGroupById(nextGroup.id);
};

const selectPassenger = (index: number) => {
  const group = activeGroup.value;
  if (!group) return;
  activePassengerIndex.value = Math.max(0, Math.min(index, group.passengers.length - 1));
};

const goToNextPassenger = () => {
  const group = activeGroup.value;
  if (!group) return;

  const nextCurrentGroup = group.passengers.findIndex((_, idx) => idx > activePassengerIndex.value);
  if (nextCurrentGroup >= 0) {
    selectPassenger(nextCurrentGroup);
    return;
  }

  for (let i = activeGroupIndex.value + 1; i < passengerGroups.value.length; i += 1) {
    const target = passengerGroups.value[i];
    const pendingIndex = target.passengers.findIndex(slot => passengerSlotState(slot) !== "complete");
    selectGroup(i);
    if (pendingIndex >= 0) selectPassenger(pendingIndex);
    return;
  }

  selectGroup(0);
};

const applyGroupResponse = (groups: PassengerGroup[]) => {
  passengerGroups.value = groups.map(normalizeGroup);
  if (passengerGroups.value.length) {
    const firstProductPending = productSections.value.findIndex(product => product.pending > 0);
    selectProduct(firstProductPending >= 0 ? firstProductPending : 0);
  } else {
    activeProductIndex.value = 0;
    activeGroupIndex.value = 0;
    activePassengerIndex.value = 0;
  }
};

const loadPassengerGroups = async () => {
  if (!token.value) return;
  groupsLoading.value = true;
  errorMessage.value = null;
  try {
    const { data } = await getPublicPassengerGroups(token.value);
    applyGroupResponse(data.groups);
    if (formInfo.value) {
      formInfo.value.passenger_status = data.passenger_status;
      formInfo.value.passengers_required = data.passengers_required;
      formInfo.value.contract_id = data.contract_id || null;
      formInfo.value.contract_signature_link = data.contract_signature_link || null;
      formInfo.value.contract_signature_token = data.contract_signature_token || null;
    }
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível carregar os grupos.";
  } finally {
    groupsLoading.value = false;
  }
};

const loadForm = async () => {
  if (!token.value) {
    errorMessage.value = "Link inválido.";
    return;
  }
  loading.value = true;
  errorMessage.value = null;
  try {
    const { data } = await getPublicPassengerForm(token.value);
    formInfo.value = data;
    await loadPassengerGroups();
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível carregar o formulário.";
  } finally {
    loading.value = false;
  }
};

const buildGroupPayload = (group: PassengerGroupForm): PassengerGroupSavePayload => ({
  passengers: group.passengers
    .filter(passengerSlotHasData)
    .map(slot => ({
      passenger_index: slot.passenger_index,
      type: slot.type,
      name: slot.name,
      cpf: slot.cpf || "",
      birth_date: slot.birthdate || "",
      birthdate: slot.birthdate || "",
      phone: slot.phone || "",
      whatsapp: slot.whatsapp || "",
      boarding_location: slot.boarding_location || "",
      notes: slot.extras || "",
      extras: slot.extras || "",
    })),
});

const updateGroup = (updated: PassengerGroup) => {
  const normalized = normalizeGroup(updated);
  const index = passengerGroups.value.findIndex(group => group.id === updated.id);
  if (index >= 0) {
    passengerGroups.value.splice(index, 1, normalized);
    selectGroup(index);
  }
};

const saveGroup = async (group: PassengerGroupForm) => {
  if (!token.value) throw new Error("Token ausente.");
  const payload = buildGroupPayload(group);
  const { data } = await savePublicPassengerGroup(token.value, group.id, payload);
  updateGroup(data);
};

const saveCurrentGroup = async () => {
  const group = activeGroup.value;
  if (!group) return;
  saving.value = true;
  savingGroupMode.value = "group";
  errorMessage.value = null;
  try {
    await saveGroup(group);
    await loadPassengerGroups();
    setSuccessMessage("Passageiro salvo com sucesso.");
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar o grupo.";
  } finally {
    saving.value = false;
    savingGroupMode.value = null;
  }
};

const submitPassengers = async () => {
  if (!token.value || !passengerGroups.value.length) return;
  saving.value = true;
  savingGroupMode.value = "all";
  errorMessage.value = null;
  try {
    for (const group of passengerGroups.value) {
      await saveGroup(group);
    }
    await loadPassengerGroups();
    setSuccessMessage(hasSeatMap.value ? "Passageiros salvos. Continue para a etapa de assentos." : "Passageiros enviados com sucesso.");
    if (canUseSeatSelection.value) {
      seatStepVisited.value = true;
      viewMode.value = "seats";
    }
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar os passageiros.";
  } finally {
    saving.value = false;
    savingGroupMode.value = null;
  }
};

const handleSeatSelectionUpdated = (_context: SeatSelectionContext) => {
  seatSelectionContext.value = _context;
  void loadPassengerGroups();
};

const handleSeatSelectionContextLoaded = (context: SeatSelectionContext) => {
  seatSelectionContext.value = context;
};

const handleWizardBack = () => {
  if (currentStep.value === 2) {
    viewMode.value = "passengers";
    return;
  }
  history.back();
};

watch(
  () => passengerGroups.value.length,
  length => {
    if (!length) {
      activeProductIndex.value = 0;
      activeGroupIndex.value = 0;
      activePassengerIndex.value = 0;
    } else if (activeGroupIndex.value >= length) {
      selectGroup(length - 1);
    } else if (activeProductIndex.value >= productSections.value.length) {
      selectProduct(Math.max(productSections.value.length - 1, 0));
    }
  },
);

onMounted(loadForm);

const paymentStatusLabel = (status: string) =>
  (
    {
      pending: "Pagamento pendente",
      processing: "Processando pagamento",
      paid: "Pagamento confirmado",
      canceled: "Pagamento cancelado",
      refunded: "Pagamento reembolsado",
    } as Record<string, string>
  )[status] || status;

const passengerStatusLabel = (status: string) =>
  (
    {
      not_started: "Passageiros pendentes",
      pending: "Grupo pendente",
      partial: "Passageiros parciais",
      completed: "Passageiros completos",
    } as Record<string, string>
  )[status] || status;

const saleChannelLabel = (channel: string) => {
  if (channel === "pos") return "PDV";
  if (channel === "link") return "Link";
  return "Checkout";
};
</script>

<style scoped>
.passenger-page {
  position: relative;
  min-height: 100vh;
  padding: 32px 24px;
  background:
    radial-gradient(circle at 8% -8%, rgba(16, 185, 129, 0.14) 0, rgba(16, 185, 129, 0) 34%),
    radial-gradient(circle at 94% 4%, rgba(14, 165, 233, 0.1) 0, rgba(14, 165, 233, 0) 30%),
    linear-gradient(180deg, #fbfdfa 0%, #f6f8f7 44%, #f8fafc 100%);
  color: #0f172a;
}

.passenger-page__bg-shape {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(120deg, rgba(15, 23, 42, 0.035), rgba(15, 23, 42, 0)),
    linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: auto, 42px 42px, 42px 42px;
  mask-image: linear-gradient(180deg, #000 0%, transparent 72%);
  pointer-events: none;
}

.passenger-page__container {
  position: relative;
  z-index: 1;
  width: min(1240px, 100%);
  margin: 0 auto;
  display: grid;
  gap: 24px;
}

.passenger-page__container--seats {
  width: min(1560px, 100%);
}

.step-swap-enter-active,
.step-swap-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.step-swap-enter-from,
.step-swap-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.hero-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.92));
  border: 1px solid rgba(203, 213, 225, 0.72);
  border-radius: 28px;
  padding: 28px;
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.hero-card__brand {
  display: flex;
  gap: 18px;
  align-items: center;
}

.hero-card__logo {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #064e3b, #047857 58%, #0f766e);
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  box-shadow: 0 18px 38px rgba(4, 120, 87, 0.22);
}

.hero-card__eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #0f766e;
  font-weight: 800;
}

.hero-card__title {
  margin-top: 0.35rem;
  font-size: clamp(1.7rem, 2.8vw, 2.55rem);
  line-height: 1.02;
  font-weight: 800;
  letter-spacing: 0;
  color: #08111f;
}

.hero-card__subtitle {
  margin-top: 0.65rem;
  color: #5b6878;
  font-size: 0.98rem;
  line-height: 1.65;
}

.hero-card__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.hero-action,
.hero-status {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 1px solid #dbe4ee;
  background: #ffffff;
  color: #334155;
  font-size: 0.82rem;
  font-weight: 800;
  padding: 10px 15px;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.hero-action:hover {
  transform: translateY(-1px);
  border-color: #b7c2d0;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.hero-action--support {
  border-color: rgba(16, 185, 129, 0.24);
  background: linear-gradient(180deg, #ecfdf5, #f7fffb);
  color: #065f46;
}

.hero-action--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.hero-status {
  border-color: rgba(16, 185, 129, 0.28);
  background: linear-gradient(135deg, #064e3b, #059669);
  color: #ffffff;
  box-shadow: 0 12px 30px rgba(5, 150, 105, 0.2);
}

.seat-stage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 88px;
  padding: 1rem 1.25rem;
  border-radius: 22px;
  border: 1px solid rgba(203, 213, 225, 0.78);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92));
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
}

.seat-stage-header__brand {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  min-width: 0;
}

.seat-stage-header__logo {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: linear-gradient(145deg, #064e3b, #047857 58%, #0f766e);
  color: #ffffff;
  font-size: 0.8rem;
  font-weight: 800;
  box-shadow: 0 12px 26px rgba(4, 120, 87, 0.18);
  overflow: hidden;
}

.seat-stage-header__copy {
  min-width: 0;
}

.seat-stage-header__copy h1 {
  font-size: 1.08rem;
  font-weight: 800;
  line-height: 1.1;
  color: #08111f;
}

.seat-stage-header__copy p {
  margin-top: 0.3rem;
  font-size: 0.82rem;
  line-height: 1.45;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.seat-stage-header__actions {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-shrink: 0;
}

.seat-stage-action {
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 1px solid #dbe4ee;
  background: #ffffff;
  color: #334155;
  padding: 0.7rem 0.95rem;
  font-size: 0.78rem;
  font-weight: 800;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.seat-stage-action:hover {
  transform: translateY(-1px);
  border-color: #b7c2d0;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06);
}

.seat-stage-action--support {
  border-color: rgba(16, 185, 129, 0.2);
  background: linear-gradient(180deg, #ecfdf5, #ffffff);
  color: #065f46;
}

.passenger-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  align-items: start;
}

.section-card {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 28px;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.055);
}

.section-card--main {
  padding: 28px;
  display: grid;
  gap: 22px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.section-head__eyebrow {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: #64748b;
  font-weight: 700;
}

.section-head__title {
  margin-top: 0.25rem;
  font-size: 1.28rem;
  font-weight: 800;
}

.section-refresh {
  border: 1px solid #dbe4ee;
  border-radius: 999px;
  background: #ffffff;
  color: #334155;
  font-size: 0.76rem;
  font-weight: 700;
  padding: 8px 14px;
}

.state-card {
  border: 1px dashed #cbd5e1;
  border-radius: 16px;
  padding: 22px;
  text-align: center;
  color: #64748b;
}

.product-tabs {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.product-tab {
  min-width: 260px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  padding: 12px;
  text-align: left;
  transition: all 0.2s ease;
}

.product-tab:hover {
  transform: translateY(-2px);
  border-color: #cbd5e1;
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06);
}

.product-tab--active {
  border-color: rgba(16, 185, 129, 0.42);
  background: linear-gradient(180deg, #ecfdf5, #ffffff);
  box-shadow: 0 16px 32px rgba(5, 150, 105, 0.12);
}

.product-tab__thumb {
  width: 54px;
  height: 54px;
  border-radius: 14px;
  background: #e2e8f0;
  color: #0f172a;
  font-weight: 700;
  font-size: 0.72rem;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.product-tab__thumb img,
.active-product__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-tab__title {
  font-size: 0.87rem;
  font-weight: 800;
  color: #0f172a;
}

.product-tab__meta,
.product-tab__pending {
  margin-top: 0.15rem;
  font-size: 0.74rem;
  color: #64748b;
}

.product-tab__pending {
  color: #0f766e;
  font-weight: 600;
}

.active-product {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  padding: 22px;
  display: grid;
  gap: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.active-product__hero {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.active-product__image {
  width: 88px;
  height: 88px;
  border-radius: 18px;
  background: linear-gradient(140deg, #bbf7d0, #dcfce7);
  color: #047857;
  font-weight: 800;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.active-product__eyebrow {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: #64748b;
  font-weight: 700;
}

.active-product__title {
  margin-top: 0.2rem;
  font-size: 1.35rem;
  line-height: 1.1;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.active-product__meta,
.active-product__helper {
  margin-top: 0.2rem;
  font-size: 0.82rem;
  color: #475569;
}

.active-product__badge {
  border: 1px solid #bbf7d0;
  background: #dcfce7;
  color: #065f46;
  font-size: 0.72rem;
  font-weight: 700;
  border-radius: 999px;
  padding: 8px 12px;
  white-space: nowrap;
}

.progress-panel {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 20px;
  padding: 16px;
  background: linear-gradient(180deg, #f8fafc, #ffffff);
}

.progress-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.82rem;
  color: #334155;
  font-weight: 600;
}

.progress-track {
  margin-top: 10px;
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.progress-track__bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #064e3b, #059669, #0ea5e9);
  transition: width 0.3s ease;
}

.passenger-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.passenger-tab {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #475569;
  padding: 9px 14px;
  min-width: 138px;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  display: grid;
  gap: 2px;
  transition: all 0.2s ease;
}

.passenger-tab small {
  font-size: 0.63rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.passenger-tab--active {
  border-color: #047857;
  background: linear-gradient(135deg, #064e3b, #059669);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(5, 150, 105, 0.18);
}

.passenger-chip-complete {
  border-color: #a7f3d0;
  background: #ecfdf5;
  color: #047857;
}

.passenger-chip-partial {
  border-color: #fcd34d;
  background: #fffbeb;
  color: #b45309;
}

.passenger-chip-empty {
  border-color: #e2e8f0;
  background: #ffffff;
  color: #64748b;
}

.passenger-form {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 22px;
  padding: 18px;
  background: linear-gradient(180deg, #f8fafc, #ffffff);
}

.passenger-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.input-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.input {
  width: 100%;
  border-radius: 15px;
  border: 1px solid #dbe4ee;
  background: #ffffff;
  padding: 13px 14px;
  font-size: 0.92rem;
  color: #0f172a;
  transition: all 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: #34d399;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.16);
}

.hint-text {
  margin-top: -2px;
  font-size: 0.8rem;
  color: #64748b;
}

.feedback {
  font-size: 0.84rem;
  border-radius: 12px;
  padding: 10px 12px;
  font-weight: 600;
}

.feedback--error {
  background: #fff1f2;
  color: #be123c;
  border: 1px solid #fecdd3;
}

.feedback--success {
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.actions-row {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  border-radius: 15px;
  padding: 13px 18px;
  font-size: 0.86rem;
  font-weight: 700;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn--ghost {
  border-color: #dbe4ee;
  background: #ffffff;
  color: #334155;
}

.btn--soft {
  border-color: #bbf7d0;
  background: #ecfdf5;
  color: #065f46;
}

.btn--primary {
  border-color: #065f46;
  background: linear-gradient(135deg, #064e3b, #059669);
  color: #ffffff;
  box-shadow: 0 12px 26px rgba(5, 150, 105, 0.24);
}

.btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  background: #047857;
}

.passenger-sidebar {
  position: sticky;
  top: 20px;
}

.summary-card {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
  padding: 22px;
  display: grid;
  gap: 16px;
}

.summary-card__eyebrow {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #64748b;
  font-weight: 700;
}

.summary-card__title {
  font-size: 1.15rem;
  font-weight: 800;
  line-height: 1.15;
}

.summary-card__meta {
  font-size: 0.8rem;
  color: #64748b;
}

.summary-card__list {
  display: grid;
  gap: 8px;
}

.summary-item {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fafc, #ffffff);
  padding: 12px;
}

.summary-item__name {
  font-size: 0.8rem;
  font-weight: 700;
}

.summary-item__sub {
  margin-top: 0.2rem;
  color: #64748b;
  font-size: 0.75rem;
}

.summary-card__totals {
  border-top: 1px solid #e2e8f0;
  padding-top: 10px;
  display: grid;
  gap: 6px;
}

.summary-card__totals p {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 0.82rem;
  color: #475569;
}

.summary-card__totals strong {
  color: #0f172a;
  font-weight: 800;
}

.summary-support {
  text-align: center;
  border: 1px solid #a7f3d0;
  border-radius: 15px;
  background: linear-gradient(180deg, #ecfdf5, #ffffff);
  color: #065f46;
  font-size: 0.78rem;
  font-weight: 700;
  padding: 9px 14px;
}

.mobile-sticky-cta {
  display: none;
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px;
  background: linear-gradient(to top, #f8fafc, rgba(248, 250, 252, 0.88));
  backdrop-filter: blur(8px);
  border-top: 1px solid #dbe4ee;
  z-index: 30;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

@media (max-width: 1080px) {
  .passenger-layout {
    grid-template-columns: 1fr;
  }

  .passenger-sidebar {
    position: static;
  }
}

@media (max-width: 760px) {
  .passenger-page {
    padding: 16px;
  }

  .hero-card {
    flex-direction: column;
    border-radius: 20px;
    padding: 18px;
  }

  .seat-stage-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 0.95rem 1rem;
  }

  .seat-stage-header__copy p {
    white-space: normal;
  }

  .hero-card__actions {
    width: 100%;
    justify-content: flex-start;
  }

  .seat-stage-header__actions {
    width: 100%;
    justify-content: flex-start;
  }

  .hero-status {
    width: 100%;
    text-align: center;
  }

  .section-card--main {
    padding: 16px;
    border-radius: 20px;
  }

  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .active-product__hero {
    grid-template-columns: 70px 1fr;
  }

  .active-product__badge {
    grid-column: 1 / -1;
    justify-self: flex-start;
  }

  .passenger-form__grid {
    grid-template-columns: 1fr;
  }

  .actions-row {
    display: none;
  }

  .mobile-sticky-cta {
    display: block;
  }
}
</style>
