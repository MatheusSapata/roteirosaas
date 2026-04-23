<template>
  <section class="w-full" :id="section.anchorId || undefined" :style="sectionStyle">
    <div class="mx-auto max-w-6xl space-y-6 px-6 py-12">
      <div class="text-center">
        <div class="flex justify-center">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accentColor" />
        </div>
        <h2 class="mt-2 text-3xl font-bold md:text-4xl" :style="{ color: primaryText }">{{ title }}</h2>
        <p v-if="subtitle" class="text-sm" :style="{ color: mutedText }">{{ subtitle }}</p>
      </div>

      <div v-if="loading" class="rounded-2xl border border-dashed border-slate-200 bg-white/70 p-6 text-center text-sm text-slate-500">
        Carregando produtos...
      </div>
      <div v-else-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-sm text-rose-600">
        {{ errorMessage }}
      </div>
      <div v-else-if="!products.length" class="rounded-2xl border border-dashed border-slate-200 bg-white/70 p-6 text-center text-sm text-slate-500">
        Nenhum produto configurado nesta seção.
      </div>

      <div v-else-if="isSingleMode && singleProduct?.schedule_mode !== 'recurring'" class="grid gap-8 lg:grid-cols-[minmax(0,2fr),minmax(320px,1fr)]">
        <div class="space-y-4">
          <article
            v-for="variation in activeVariations(singleProduct!)"
            :key="variation.public_id"
            class="space-y-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
            :class="{ 'opacity-60': singleProduct?.status !== 'active' }"
          >
            <div class="flex items-center justify-between gap-2">
              <div>
                <h3 class="text-lg font-semibold text-slate-900">{{ variation.name }}</h3>
                <p v-if="variation.description" class="text-sm text-slate-500">{{ variation.description }}</p>
              </div>
              <p class="text-lg font-bold text-slate-900">{{ formatCurrency(variation.price_cents, variation.currency) }}</p>
            </div>

            <div v-if="singleProduct?.schedule_mode === 'recurring'" class="grid gap-2 md:grid-cols-2">
              <input
                :value="getSingleScheduleState(variation.public_id).date"
                type="date"
                class="input"
                @change="setSingleScheduleDate(variation.public_id, ($event.target as HTMLInputElement).value)"
              />
              <select
                :value="getSingleScheduleState(variation.public_id).departureId ?? ''"
                class="input"
                @change="setSingleScheduleDeparture(variation.public_id, ($event.target as HTMLSelectElement).value)"
              >
                <option value="">Selecione horário</option>
                <option
                  v-for="slot in getSingleScheduleState(variation.public_id).departureSlots"
                  :key="slot.departure_id"
                  :value="slot.departure_id"
                  :disabled="!slot.available"
                >
                  {{ slot.label }}
                </option>
              </select>
            </div>

            <div class="flex items-center gap-2">
              <button type="button" class="qty-btn" @click="setSingleQuantity(variation.public_id, getSingleQuantity(variation.public_id) - 1)">-</button>
              <span class="min-w-[2ch] text-center font-semibold">{{ getSingleQuantity(variation.public_id) }}</span>
              <button type="button" class="qty-btn" @click="setSingleQuantity(variation.public_id, getSingleQuantity(variation.public_id) + 1)">+</button>
            </div>
          </article>
        </div>
        <aside class="space-y-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
          <h3 class="text-sm font-semibold text-slate-900">Resumo</h3>
          <div v-for="item in singleSelectedItems" :key="item.variation.public_id" class="flex items-center justify-between text-sm">
            <span>{{ item.quantity }}x {{ item.variation.name }}</span>
            <span>{{ formatCurrency(item.total, item.variation.currency) }}</span>
          </div>
          <div class="border-t border-slate-200 pt-2 text-sm font-semibold text-slate-900">
            Total: {{ formatCurrency(singleTotal, singleCurrency) }}
          </div>
          <button type="button" class="checkout-btn" :style="{ backgroundColor: accentColor }" :disabled="!singleCanCheckout" @click="checkoutSingle">
            {{ checkoutButtonLabel }}
          </button>
        </aside>
      </div>

      <div v-else class="grid gap-8 lg:grid-cols-[minmax(0,2fr),minmax(320px,1fr)]">
        <div class="space-y-4">
          <div
            v-if="selectionWarning"
            class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800"
          >
            {{ selectionWarning }}
          </div>
          <article
            v-for="product in products"
            :key="product.public_id"
            :id="`multi-product-${product.public_id}`"
            class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm transition"
            :class="isProductExpanded(product.public_id) ? 'space-y-5 ring-1 ring-slate-200' : 'space-y-3'"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="space-y-2">
                <h3 class="text-lg font-semibold text-slate-900">{{ product.name }}</h3>
                <p v-if="isProductExpanded(product.public_id) && product.description" class="text-sm text-slate-500">{{ product.description }}</p>
                <span class="mt-2 inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
                  Disponível
                </span>
              </div>
              <button type="button" class="expand-btn" @click="toggleProductExpand(product.public_id)">
                {{ isProductExpanded(product.public_id) ? "Recolher" : "Expandir" }}
                <span class="expand-btn__chevron" :class="{ 'expand-btn__chevron--open': isProductExpanded(product.public_id) }" aria-hidden="true"></span>
              </button>
            </div>

            <div v-if="isProductExpanded(product.public_id) && getMultiProductState(product.public_id)" class="space-y-5 border-t border-slate-100 pt-4">
              <template v-if="product.schedule_mode === 'recurring'">
                <div class="recurring-flow">
                  <section class="recurring-step">
                    <p class="recurring-step__label">Passo 1 — Escolha seu pacote</p>
                    <div class="recurring-package-grid">
                      <button
                        v-for="variation in activeVariations(product)"
                        :key="variation.public_id"
                        type="button"
                        class="recurring-package-card"
                        :class="{ 'recurring-package-card--active': isVariationSelectedForProduct(product, variation.public_id) }"
                        @click="selectMultiVariation(product.public_id, variation.public_id)"
                      >
                        <span class="recurring-package-card__name">{{ variation.name }}</span>
                        <span class="recurring-package-card__price">{{ formatCurrency(variation.price_cents, variation.currency) }}</span>
                      </button>
                    </div>
                  </section>

                  <div class="recurring-schedule-grid">
                    <section class="recurring-step recurring-calendar-card">
                      <div class="recurring-step-head">
                        <p class="recurring-step__label">Passo 2 — Escolha a data</p>
                        <div class="recurring-calendar-nav">
                          <button type="button" @click="changeMultiCalendarMonth(product.public_id, -1)">‹</button>
                          <span>{{ buildCalendarMonthLabel(getMultiProductState(product.public_id)?.calendarMonth || '') }}</span>
                          <button type="button" @click="changeMultiCalendarMonth(product.public_id, 1)">›</button>
                        </div>
                      </div>
                      <div class="recurring-weekdays">
                        <span>Dom</span>
                        <span>Seg</span>
                        <span>Ter</span>
                        <span>Qua</span>
                        <span>Qui</span>
                        <span>Sex</span>
                        <span>Sáb</span>
                      </div>
                      <div class="recurring-calendar-grid">
                        <template v-for="cell in recurringCalendarCells(product.public_id)" :key="cell.key">
                          <span v-if="cell.blank" class="recurring-calendar-day recurring-calendar-day--blank"></span>
                          <button
                            v-else
                            type="button"
                            class="recurring-calendar-day"
                            :class="{
                              'recurring-calendar-day--active': getMultiProductState(product.public_id)?.date === cell.day.date,
                              'recurring-calendar-day--today': cell.day.date === todayIso(),
                              'recurring-calendar-day--disabled': !cell.day.available,
                              'recurring-calendar-day--low': cell.day.low_availability,
                            }"
                            :disabled="!cell.day.available || getMultiProductState(product.public_id)?.calendarLoading"
                            @click="selectMultiDate(product.public_id, cell.day.date)"
                          >
                            <span>{{ cell.day.day }}</span>
                            <small v-if="cell.day.departures_count > 0">{{ cell.day.departures_count }}</small>
                          </button>
                        </template>
                      </div>
                      <span v-if="getMultiProductState(product.public_id)?.calendarLoading" class="recurring-loading-chip">
                        Carregando calendário...
                      </span>
                    </section>

                    <section class="recurring-step recurring-slots-card">
                      <p class="recurring-step__label">Passo 3 — Horários do dia</p>
                      <div class="recurring-slots-head">
                        <strong>{{ buildFullDateLabel(getMultiProductState(product.public_id)?.date || '') }}</strong>
                        <span>{{ (getMultiProductState(product.public_id)?.departureSlots || []).filter(slot => slot.available).length }} saída(s) disponível(is)</span>
                      </div>
                      <transition name="recurring-fade" mode="out-in">
                        <div :key="getMultiProductState(product.public_id)?.date" class="recurring-slot-grid">
                          <button
                            v-for="slot in getMultiProductState(product.public_id)?.departureSlots || []"
                            :key="slot.departure_id"
                            type="button"
                            class="recurring-slot-pill"
                            :class="{ 'recurring-slot-pill--active': getMultiProductState(product.public_id)?.departureId === slot.departure_id }"
                            :disabled="!slot.available || getMultiProductState(product.public_id)?.departuresLoading"
                            @click="selectMultiDeparture(product.public_id, slot.departure_id)"
                          >
                            <span>{{ slot.time }}</span>
                            <small v-if="slot.remaining_capacity >= 0">{{ slot.remaining_capacity }} vagas</small>
                          </button>
                          <span v-if="getMultiProductState(product.public_id)?.departuresLoading" class="recurring-loading-chip">
                            Carregando horários...
                          </span>
                          <span v-else-if="!(getMultiProductState(product.public_id)?.departureSlots || []).length" class="recurring-empty-slot">
                            Nenhuma saída neste dia.
                          </span>
                        </div>
                      </transition>
                      <p class="recurring-slot-helper">
                        {{ getMultiProductState(product.public_id)?.departureId ? 'Horário selecionado.' : 'Selecione um horário para continuar.' }}
                      </p>
                    </section>
                  </div>

                  <section class="recurring-step">
                    <p class="recurring-step__label">Passo 4 — Passageiros</p>
                    <div v-if="selectedVariationsForProduct(product).length" class="recurring-passenger-list">
                      <div
                        v-for="variation in selectedVariationsForProduct(product)"
                        :key="`qty-${product.public_id}-${variation.public_id}`"
                        class="recurring-passenger-row"
                      >
                        <span class="recurring-passenger-row__name">{{ variation.name }}</span>
                        <div class="recurring-stepper">
                          <button
                            type="button"
                            class="recurring-stepper__btn"
                            @click="setMultiVariationQuantity(product.public_id, variation.public_id, getMultiVariationQuantity(product.public_id, variation.public_id) - 1)"
                          >
                            -
                          </button>
                          <span class="recurring-stepper__value">{{ getMultiVariationQuantity(product.public_id, variation.public_id) }}</span>
                          <button
                            type="button"
                            class="recurring-stepper__btn"
                            @click="setMultiVariationQuantity(product.public_id, variation.public_id, getMultiVariationQuantity(product.public_id, variation.public_id) + 1)"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    </div>
                    <p v-else class="text-xs text-slate-500">Escolha pelo menos um pacote.</p>
                  </section>

                </div>
              </template>

              <template v-else>
                <div class="space-y-2">
                  <p class="section-title">Pacote</p>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="variation in activeVariations(product)"
                      :key="variation.public_id"
                      type="button"
                      class="chip"
                      :class="isVariationSelectedForProduct(product, variation.public_id) ? 'chip-active' : ''"
                      @click="selectMultiVariation(product.public_id, variation.public_id)"
                    >
                      {{ variation.name }} — {{ formatCurrency(variation.price_cents, variation.currency) }}
                    </button>
                  </div>
                </div>

                <div class="space-y-2">
                  <p class="section-title">Passageiros</p>
                  <div v-if="selectedVariationsForProduct(product).length" class="space-y-2">
                    <div
                      v-for="variation in selectedVariationsForProduct(product)"
                      :key="`qty-${product.public_id}-${variation.public_id}`"
                      class="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2"
                    >
                      <span class="text-sm font-medium text-slate-700">{{ variation.name }}</span>
                      <div class="flex items-center gap-2">
                        <button
                          type="button"
                          class="qty-btn"
                          @click="setMultiVariationQuantity(product.public_id, variation.public_id, getMultiVariationQuantity(product.public_id, variation.public_id) - 1)"
                        >
                          -
                        </button>
                        <span class="min-w-[2ch] text-center font-semibold">{{ getMultiVariationQuantity(product.public_id, variation.public_id) }}</span>
                        <button
                          type="button"
                          class="qty-btn"
                          @click="setMultiVariationQuantity(product.public_id, variation.public_id, getMultiVariationQuantity(product.public_id, variation.public_id) + 1)"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-xs text-slate-500">Escolha pelo menos um pacote.</p>
                </div>

                <div class="summary-box">
                  {{ productFooterSummary(product) }}
                </div>
              </template>
            </div>
          </article>
        </div>

        <aside class="space-y-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm lg:sticky lg:top-6 lg:h-fit">
          <h3 class="text-base font-semibold text-slate-900">Resumo da compra</h3>
          <div
            v-for="entry in multiSummaryByProduct"
            :key="entry.productId"
            class="space-y-1 rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700"
          >
            <p class="font-semibold text-slate-900">{{ entry.productName }}</p>
            <p>{{ entry.summary }}</p>
            <div class="flex items-center justify-between pt-1 font-semibold text-slate-900">
              <span>Valor</span>
              <span>{{ formatCurrency(entry.total, entry.currency) }}</span>
            </div>
          </div>

          <div class="text-xs text-slate-500">Subtotal: {{ formatCurrency(multiSubtotal, multiCurrency) }}</div>
          <div v-if="multiDiscount > 0" class="text-xs font-semibold text-emerald-600">
            Desconto combo: -{{ formatCurrency(multiDiscount, multiCurrency) }}
          </div>
          <div class="border-t border-slate-200 pt-2 text-sm font-semibold text-slate-900">
            Total: {{ formatCurrency(multiTotal, multiCurrency) }}
          </div>
          <button type="button" class="checkout-btn" :style="{ backgroundColor: accentColor }" :disabled="!multiCanCheckout" @click="checkoutMulti">
            {{ checkoutButtonLabel }}
          </button>
        </aside>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, inject, nextTick, onMounted, reactive, ref, watch } from "vue";
import { getPublicDepartureCalendar, getPublicDepartureTimes, getPublicProductDetail } from "../../services/finance";
import type { ProductDetail, ProductVariation, PublicDepartureCalendarDay, PublicDepartureTimeSlot, SectionDiscountConfig } from "../../types/finance";
import type { ProductsSection } from "../../types/page";
import { PUBLIC_PRODUCT_CHECKOUT_KEY, type ProductCheckoutPayload } from "../../utils/checkoutKeys";
import { deriveTextPalette } from "../../utils/colorContrast";
import { createLocalizer, getCurrentLanguage, type LocalizedString } from "../../utils/i18n";
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../utils/sectionHeadings";
import SectionHeadingChip from "./SectionHeadingChip.vue";

const props = defineProps<{ section: ProductsSection; sectionIndex?: number }>();
const checkoutBridge = inject(PUBLIC_PRODUCT_CHECKOUT_KEY, null);
const headingDefaults = getSectionHeadingDefaults("products");
const currentLanguage = getCurrentLanguage();
const localize = createLocalizer(currentLanguage);

const loading = ref(false);
const errorMessage = ref<string | null>(null);
const selectionWarning = ref<string | null>(null);
const products = ref<ProductDetail[]>([]);

const singleState = reactive<{
  quantities: Record<string, number>;
  schedules: Record<string, { date: string; departureId: number | null; departureSlots: PublicDepartureTimeSlot[] }>;
}>({
  quantities: {},
  schedules: {},
});

type MultiDateOption = {
  date: string;
  label: string;
  available: boolean;
};

type MultiProductState = {
  selected: boolean;
  expanded: boolean;
  selectedVariationIds: string[];
  variationQuantities: Record<string, number>;
  date: string;
  calendarMonth: string;
  calendarDays: PublicDepartureCalendarDay[];
  departureId: number | null;
  departureSlots: PublicDepartureTimeSlot[];
  dateOptions: MultiDateOption[];
  calendarLoading: boolean;
  departuresLoading: boolean;
  datesLoading: boolean;
};

const multiState = reactive<Record<string, MultiProductState>>({});

const sectionStyle = computed(() => ({ background: props.section.backgroundColor || "linear-gradient(180deg,#f8fafc,#fff)" }));
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);
const headingLabel = computed(() => resolveHeadingLabel(props.section.headingLabel, headingDefaults.label, localize));
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const accentColor = computed(() => props.section.accentColor || "#059669");
const defaultTitle: LocalizedString = { pt: "Pacotes disponíveis", es: "Paquetes disponibles" };
const defaultSubtitle: LocalizedString = { pt: "Escolha uma ou mais experiências", es: "Elige una o más experiencias" };
const defaultButton: LocalizedString = { pt: "Ir para checkout", es: "Ir al checkout" };
const title = computed(() => localize(props.section.title || defaultTitle));
const subtitle = computed(() => localize(props.section.subtitle || defaultSubtitle));
const checkoutButtonLabel = computed(() => localize(props.section.ctaLabel || defaultButton));

const configuredIds = computed(() => {
  const sectionRaw = props.section as ProductsSection & {
    product_ids?: string[];
    product_id?: string | null;
  };
  const modernIds = props.section.productIds?.length ? props.section.productIds : [];
  const legacyIds = sectionRaw.product_ids?.length ? sectionRaw.product_ids : [];
  const fallbackSingle =
    props.section.productId ||
    sectionRaw.product_id ||
    null;
  const ids = modernIds.length ? modernIds : legacyIds.length ? legacyIds : fallbackSingle ? [fallbackSingle] : [];
  return Array.from(new Set(ids.filter(Boolean)));
});
const isSingleMode = computed(() => configuredIds.value.length <= 1);
const singleProduct = computed(() => products.value[0] || null);

const activeVariations = (product: ProductDetail) => (product.variations || []).filter(variation => variation.status === "active");

const loadProducts = async () => {
  loading.value = true;
  errorMessage.value = null;
  try {
    const loaded: ProductDetail[] = [];
    for (const productId of configuredIds.value) {
      const { data } = await getPublicProductDetail(productId);
      loaded.push(data);
    }
    products.value = loaded;
    bootstrapStates();
    for (const product of products.value) {
      if (product.schedule_mode !== "recurring") continue;
      await loadMultiDateOptions(product.public_id);
      await loadProductDepartures(product.public_id);
    }
    if (isSingleMode.value && singleProduct.value?.schedule_mode === "recurring" && singleProduct.value) {
      for (const variation of activeVariations(singleProduct.value)) {
        await loadSingleDepartures(variation.public_id);
      }
    }
  } catch (err) {
    console.error("Erro ao carregar produtos da seção", err);
    errorMessage.value = "Não foi possível carregar os produtos.";
    products.value = [];
  } finally {
    loading.value = false;
  }
};

const buildDateLabel = (date: string) => {
  try {
    return new Date(`${date}T00:00:00`).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
  } catch {
    return date;
  }
};

const buildWeekdayLabel = (date: string) => {
  try {
    return new Date(`${date}T00:00:00`)
      .toLocaleDateString("pt-BR", { weekday: "short" })
      .replace(".", "")
      .slice(0, 3)
      .toUpperCase();
  } catch {
    return "--";
  }
};

const buildDayLabel = (date: string) => {
  try {
    return new Date(`${date}T00:00:00`).toLocaleDateString("pt-BR", { day: "2-digit" });
  } catch {
    return "--";
  }
};

const buildFullDateLabel = (date: string) => {
  try {
    return new Date(`${date}T00:00:00`).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      weekday: "long",
    });
  } catch {
    return date;
  }
};

const buildCalendarMonthLabel = (month: string) => {
  try {
    const parsed = new Date(`${month || monthKeyFromDate(todayIso())}-01T00:00:00`);
    const label = parsed.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
    return label.charAt(0).toUpperCase() + label.slice(1);
  } catch {
    return month;
  }
};

const shiftMonthKey = (month: string, offset: number) => {
  const parsed = new Date(`${month || monthKeyFromDate(todayIso())}-01T00:00:00`);
  parsed.setMonth(parsed.getMonth() + offset);
  return parsed.toISOString().slice(0, 7);
};

const buildDateCandidates = (days = 7) => {
  const base = new Date();
  const values: string[] = [];
  for (let index = 0; index < days; index += 1) {
    const day = new Date(base);
    day.setDate(base.getDate() + index);
    values.push(day.toISOString().slice(0, 10));
  }
  return values;
};

const todayIso = () => new Date().toISOString().slice(0, 10);
const monthKeyFromDate = (date: string) => (date || todayIso()).slice(0, 7);
const pad2 = (value: number) => String(value).padStart(2, "0");

const buildMonthDate = (year: number, monthIndex: number, day: number) =>
  `${year}-${pad2(monthIndex + 1)}-${pad2(day)}`;

const buildCompleteMonthDays = (month: string, sourceDays: PublicDepartureCalendarDay[]) => {
  const [rawYear, rawMonth] = (month || monthKeyFromDate(todayIso())).split("-").map(Number);
  const year = Number.isFinite(rawYear) ? rawYear : new Date().getFullYear();
  const monthIndex = Number.isFinite(rawMonth) ? rawMonth - 1 : new Date().getMonth();
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const byDate = new Map(sourceDays.map(day => [day.date, day]));

  return Array.from({ length: daysInMonth }).map((_, index) => {
    const dayNumber = index + 1;
    const date = buildMonthDate(year, monthIndex, dayNumber);
    const existing = byDate.get(date);
    return (
      existing || {
        date,
        day: dayNumber,
        available: false,
        departures_count: 0,
        low_availability: false,
        status: "unavailable",
      }
    );
  });
};

const ensureMultiState = (product: ProductDetail): MultiProductState => {
  if (!multiState[product.public_id]) {
    multiState[product.public_id] = {
      selected: false,
      expanded: false,
      selectedVariationIds: [],
      variationQuantities: {},
      date: todayIso(),
      calendarMonth: monthKeyFromDate(todayIso()),
      calendarDays: [],
      departureId: null,
      departureSlots: [],
      dateOptions: [],
      calendarLoading: false,
      departuresLoading: false,
      datesLoading: false,
    };
  }
  return multiState[product.public_id];
};

const bootstrapStates = () => {
  let hasExpandedCard = false;
  for (const product of products.value) {
    const state = ensureMultiState(product);
    const validIds = new Set(activeVariations(product).map(variation => variation.public_id));
    state.selectedVariationIds = state.selectedVariationIds.filter(variationId => validIds.has(variationId));
    Object.keys(state.variationQuantities).forEach(variationId => {
      if (!validIds.has(variationId)) {
        delete state.variationQuantities[variationId];
      }
    });
    state.selected = state.selectedVariationIds.length > 0;
    if (state.expanded) hasExpandedCard = true;
  }
  if (!hasExpandedCard && products.value.length > 0) {
    ensureMultiState(products.value[0]).expanded = true;
  }

  if (singleProduct.value) {
    for (const variation of activeVariations(singleProduct.value)) {
      ensureSingleScheduleState(variation.public_id);
    }
  }
};

const ensureSingleScheduleState = (variationId: string) => {
  if (!singleState.schedules[variationId]) {
    singleState.schedules[variationId] = {
      date: new Date().toISOString().slice(0, 10),
      departureId: null,
      departureSlots: [],
    };
  }
  return singleState.schedules[variationId];
};

const getSingleScheduleState = (variationId: string) => ensureSingleScheduleState(variationId);

const setSingleScheduleDate = async (variationId: string, value: string) => {
  const state = ensureSingleScheduleState(variationId);
  state.date = value || new Date().toISOString().slice(0, 10);
  await loadSingleDepartures(variationId);
};

const setSingleScheduleDeparture = (variationId: string, value: string) => {
  const state = ensureSingleScheduleState(variationId);
  if (!value) {
    state.departureId = null;
    return;
  }
  const parsed = Number(value);
  state.departureId = Number.isFinite(parsed) ? parsed : null;
};

const loadSingleDepartures = async (variationId: string) => {
  if (!singleProduct.value) return;
  const product = singleProduct.value;
  if (product.schedule_mode !== "recurring") return;
  const state = ensureSingleScheduleState(variationId);
  try {
    const { data } = await getPublicDepartureTimes(product.public_id, state.date);
    state.departureSlots = data.slots || [];
    if (!state.departureSlots.some(slot => slot.departure_id === state.departureId)) {
      state.departureId = null;
    }
  } catch (err) {
    console.error("Erro ao carregar horários", err);
    state.departureSlots = [];
  }
};
const loadMultiDateOptions = async (productId: string) => {
  const product = products.value.find(entry => entry.public_id === productId);
  if (!product || product.schedule_mode !== "recurring") return;
  const state = ensureMultiState(product);
  state.datesLoading = true;
  state.calendarLoading = true;
  try {
    const { data } = await getPublicDepartureCalendar(productId, state.calendarMonth);
    const days = buildCompleteMonthDays(state.calendarMonth, data.days || []);
    state.calendarDays = days;
    state.dateOptions = days.map(day => ({
      date: day.date,
      label: buildDateLabel(day.date),
      available: day.available,
    }));
    if (!days.some(day => day.date === state.date && day.available)) {
      state.date = days.find(day => day.available)?.date || days[0]?.date || state.date;
    }
  } catch {
    const candidates = buildDateCandidates(7);
    const responses = await Promise.all(
      candidates.map(async date => {
        try {
          const { data } = await getPublicDepartureTimes(productId, date);
          const hasAvailable = (data.slots || []).some(slot => slot.available);
          return { date, label: buildDateLabel(date), available: hasAvailable };
        } catch {
          return { date, label: buildDateLabel(date), available: false };
        }
      }),
    );
    state.dateOptions = responses;
    state.calendarDays = buildCompleteMonthDays(
      state.calendarMonth,
      responses.map((option, index) => ({
        date: option.date,
        day: Number(option.date.slice(-2)) || index + 1,
        available: option.available,
        departures_count: option.available ? 1 : 0,
        low_availability: false,
        status: option.available ? "available" : "unavailable",
      })),
    );
    state.date = responses.find(option => option.available)?.date || responses[0]?.date || state.date;
  } finally {
    state.datesLoading = false;
    state.calendarLoading = false;
  }
};
const loadProductDepartures = async (productId: string) => {
  const product = products.value.find(entry => entry.public_id === productId);
  if (!product || product.schedule_mode !== "recurring") return;
  const state = ensureMultiState(product);
  state.departuresLoading = true;
  try {
    const { data } = await getPublicDepartureTimes(productId, state.date);
    state.departureSlots = data.slots || [];
    if (!state.departureSlots.some(slot => slot.departure_id === state.departureId)) {
      state.departureId = null;
    }
  } catch (err) {
    console.error("Erro ao carregar horários do produto", err);
    state.departureSlots = [];
    state.departureId = null;
  } finally {
    state.departuresLoading = false;
  }
};

const getSingleQuantity = (variationId: string) => singleState.quantities[variationId] || 0;
const setSingleQuantity = (variationId: string, quantity: number) => {
  const next = Math.max(0, Math.floor(quantity));
  if (next === 0) {
    delete singleState.quantities[variationId];
    return;
  }
  singleState.quantities[variationId] = next;
};

const singleSelectedItems = computed(() => {
  if (!singleProduct.value) return [];
  return activeVariations(singleProduct.value)
    .map(variation => ({ variation, quantity: getSingleQuantity(variation.public_id), total: getSingleQuantity(variation.public_id) * variation.price_cents }))
    .filter(entry => entry.quantity > 0);
});
const singleTotal = computed(() => singleSelectedItems.value.reduce((sum, item) => sum + item.total, 0));
const singleCurrency = computed(() => singleProduct.value?.variations?.[0]?.currency || "BRL");
const singleCanCheckout = computed(() => {
  if (!checkoutBridge || !singleProduct.value || singleTotal.value <= 0 || singleProduct.value.status !== "active") return false;
  if (singleProduct.value.schedule_mode === "recurring") {
    for (const item of singleSelectedItems.value) {
      const schedule = singleState.schedules[item.variation.public_id];
      if (!schedule?.departureId) return false;
    }
  }
  return true;
});

const isProductExpanded = (productId: string) => !!multiState[productId]?.expanded;
const getMultiProductState = (productId: string) => {
  const product = products.value.find(item => item.public_id === productId);
  if (!product) return null;
  return ensureMultiState(product);
};

const toggleProductExpand = async (productId: string) => {
  const product = products.value.find(item => item.public_id === productId);
  if (!product) return;
  const nextExpanded = !ensureMultiState(product).expanded;
  for (const item of products.value) {
    ensureMultiState(item).expanded = false;
  }
  const state = ensureMultiState(product);
  state.expanded = nextExpanded;
  if (!nextExpanded) return;
  await nextTick();
  document.getElementById(`multi-product-${productId}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  if (product.schedule_mode === "recurring") {
    await loadMultiDateOptions(productId);
    await loadProductDepartures(productId);
  }
};

const selectMultiVariation = async (productId: string, variationId: string) => {
  const product = products.value.find(item => item.public_id === productId);
  if (!product) return;
  const state = ensureMultiState(product);
  const index = state.selectedVariationIds.indexOf(variationId);
  if (index >= 0) {
    state.selectedVariationIds.splice(index, 1);
    delete state.variationQuantities[variationId];
  } else {
    if (!state.selected) {
      const baseline = baselineMethodsFromSelection();
      const current = normalizedAllowedMethods(product);
      if (baseline && methodsSignature(baseline) !== methodsSignature(current)) {
        selectionWarning.value =
          "Este produto nao pode ser selecionado junto com os atuais porque possui formas de pagamento diferentes.";
        return;
      }
    }
    state.selectedVariationIds.push(variationId);
    state.variationQuantities[variationId] = Math.max(1, state.variationQuantities[variationId] || 1);
    selectionWarning.value = null;
  }
  state.selected = state.selectedVariationIds.length > 0;
  if (!state.selected) {
    state.departureId = null;
    return;
  }
  if (product.schedule_mode === "recurring" && (!state.dateOptions.length || !state.departureSlots.length)) {
    await loadMultiDateOptions(productId);
    await loadProductDepartures(productId);
  }
};

const selectMultiDate = async (productId: string, date: string) => {
  const state = getMultiProductState(productId);
  if (!state) return;
  state.date = date;
  state.calendarMonth = monthKeyFromDate(date);
  state.departureId = null;
  await loadProductDepartures(productId);
};

const changeMultiCalendarMonth = async (productId: string, offset: number) => {
  const state = getMultiProductState(productId);
  if (!state) return;
  state.calendarMonth = shiftMonthKey(state.calendarMonth, offset);
  state.departureId = null;
  await loadMultiDateOptions(productId);
  await loadProductDepartures(productId);
};

const recurringCalendarCells = (productId: string) => {
  const state = getMultiProductState(productId);
  const days = state?.calendarDays || [];
  const firstDate = days[0]?.date;
  let blanks = 0;
  if (firstDate) {
    const parsed = new Date(`${firstDate}T00:00:00`);
    blanks = Number.isNaN(parsed.getTime()) ? 0 : parsed.getDay();
  }
  return [
    ...Array.from({ length: blanks }).map((_, index) => ({ key: `blank-${index}`, blank: true as const })),
    ...days.map(day => ({ key: day.date, blank: false as const, day })),
  ];
};

const selectMultiDeparture = (productId: string, departureId: number) => {
  const state = getMultiProductState(productId);
  if (!state) return;
  state.departureId = departureId;
};

const selectedVariationsForProduct = (product: ProductDetail) => {
  const state = getMultiProductState(product.public_id);
  if (!state) return [];
  return activeVariations(product).filter(entry => state.selectedVariationIds.includes(entry.public_id));
};

const normalizedAllowedMethods = (product: ProductDetail) => {
  const raw = Array.isArray(product.allowed_payment_methods) ? product.allowed_payment_methods : ["pix", "credit_card", "boleto"];
  const normalized = Array.from(
    new Set(
      raw
        .map(item => String(item || "").trim().toLowerCase())
        .filter(item => item === "pix" || item === "credit_card" || item === "boleto"),
    ),
  );
  return normalized.length ? normalized : ["pix", "credit_card", "boleto"];
};

const methodsSignature = (methods: string[]) => [...methods].sort().join("|");

const baselineMethodsFromSelection = () => {
  for (const product of products.value) {
    const state = getMultiProductState(product.public_id);
    if (state?.selected) {
      return normalizedAllowedMethods(product);
    }
  }
  return null;
};

const selectedDepartureLabelForProduct = (product: ProductDetail) => {
  const state = getMultiProductState(product.public_id);
  if (!state?.departureId) return "";
  const slot = state.departureSlots.find(entry => entry.departure_id === state.departureId);
  return slot?.time || slot?.label || "";
};

const selectedDepartureForProduct = (product: ProductDetail) => {
  const state = getMultiProductState(product.public_id);
  if (!state?.departureId) return null;
  return state.departureSlots.find(entry => entry.departure_id === state.departureId) || null;
};

const isVariationSelectedForProduct = (product: ProductDetail, variationId: string) => {
  const state = getMultiProductState(product.public_id);
  return !!state?.selectedVariationIds.includes(variationId);
};

const setMultiVariationQuantity = (productId: string, variationId: string, quantity: number) => {
  const state = getMultiProductState(productId);
  if (!state) return;
  if (!state.selectedVariationIds.includes(variationId)) return;
  state.variationQuantities[variationId] = Math.max(1, Math.floor(quantity));
};

const getMultiVariationQuantity = (productId: string, variationId: string) => {
  const state = getMultiProductState(productId);
  if (!state) return 1;
  return Math.max(1, state.variationQuantities[variationId] || 1);
};

const totalUnitsForProduct = (product: ProductDetail) =>
  selectedVariationsForProduct(product).reduce(
    (sum, variation) => sum + getMultiVariationQuantity(product.public_id, variation.public_id),
    0,
  );

const compactSummaryForProduct = (product: ProductDetail) => {
  const state = getMultiProductState(product.public_id);
  if (!state) return "Escolha os passageiros";
  const variations = selectedVariationsForProduct(product);
  if (!variations.length) {
    return product.schedule_mode === "recurring" ? `Escolha os passageiros · ${buildDateLabel(state.date)}` : "Escolha os passageiros";
  }
  const parts = variations.map(variation => `${variation.name} ${getMultiVariationQuantity(product.public_id, variation.public_id)}x`);
  if (product.schedule_mode === "recurring") {
    parts.push(buildDateLabel(state.date));
  }
  return parts.join(" · ");
};

const productFooterSummary = (product: ProductDetail) => {
  const state = getMultiProductState(product.public_id);
  if (!state) return "";
  if (!state.selectedVariationIds.length) return "Escolha os passageiros";
  const units = totalUnitsForProduct(product);
  const peopleLabel = `${units} ${units === 1 ? "pessoa" : "pessoas"}`;
  if (product.schedule_mode !== "recurring") return peopleLabel;
  if (!state.departureId) return "Selecione horário";
  const departure = selectedDepartureLabelForProduct(product);
  return `${peopleLabel} · ${buildDateLabel(state.date)} · ${departure}`;
};

const multiSummary = computed(() => {
  const result: Array<{
    productId: string;
    productName: string;
    variationId: string;
    variationName: string;
    quantity: number;
    total: number;
    currency: string;
    departureId?: number | null;
    dateLabel?: string | null;
    departureLabel?: string | null;
  }> = [];
  for (const product of products.value) {
    const state = getMultiProductState(product.public_id);
    if (!state?.selected) continue;
    const slot = state.departureSlots.find(entry => entry.departure_id === state.departureId);
    for (const variation of selectedVariationsForProduct(product)) {
      const quantity = getMultiVariationQuantity(product.public_id, variation.public_id);
      result.push({
        productId: product.public_id,
        productName: product.name,
        variationId: variation.public_id,
        variationName: variation.name,
        quantity,
        total: quantity * variation.price_cents,
        currency: variation.currency,
        departureId: product.schedule_mode === "recurring" ? state.departureId : null,
        dateLabel: product.schedule_mode === "recurring" ? buildDateLabel(state.date) : null,
        departureLabel: product.schedule_mode === "recurring" ? (slot?.time || slot?.label || null) : null,
      });
    }
  }
  return result;
});

const multiSummaryByProduct = computed(() => {
  const grouped = new Map<string, { productName: string; summary: string; total: number; currency: string }>();
  for (const entry of multiSummary.value) {
    const existing = grouped.get(entry.productId);
    if (existing) {
      existing.total += entry.total;
      continue;
    }
    const product = products.value.find(item => item.public_id === entry.productId);
    grouped.set(entry.productId, {
      productName: entry.productName,
      summary: product ? compactSummaryForProduct(product) : "",
      total: entry.total,
      currency: entry.currency,
    });
  }
  return Array.from(grouped.entries()).map(([productId, values]) => ({ productId, ...values }));
});

const multiCurrency = computed(() => multiSummary.value[0]?.currency || "BRL");
const multiSubtotal = computed(() => multiSummary.value.reduce((sum, item) => sum + item.total, 0));

const parseDiscountConfig = computed<SectionDiscountConfig | null>(() => {
  const raw = props.section.discount;
  if (!raw?.ruleType || !raw?.discountType || typeof raw.discountValue !== "number") return null;
  return {
    rule_type: raw.ruleType,
    min_selected_products: raw.minSelectedProducts ?? null,
    required_product_ids: raw.requiredProductIds || [],
    discount_type: raw.discountType,
    discount_value: raw.discountValue,
  };
});

const multiDiscount = computed(() => {
  const config = parseDiscountConfig.value;
  if (!config) return 0;
  const selected = multiSummary.value.map(item => item.productId);
  const uniqueSelected = new Set(selected);
  let eligible = false;
  if (config.rule_type === "min_quantity") {
    eligible = uniqueSelected.size >= Math.max(config.min_selected_products || 1, 1);
  } else if (config.rule_type === "exact_combination") {
    const required = new Set((config.required_product_ids || []).filter(Boolean));
    eligible = required.size > 0 && [...required].every(id => uniqueSelected.has(id));
  }
  if (!eligible) return 0;
  if (config.discount_type === "fixed") {
    return Math.min(Math.max(config.discount_value || 0, 0), multiSubtotal.value);
  }
  const percentage = Math.max(0, Math.min(config.discount_value || 0, 100));
  return Math.round((multiSubtotal.value * percentage) / 100);
});
const multiTotal = computed(() => Math.max(0, multiSubtotal.value - multiDiscount.value));
const multiCanCheckout = computed(() => {
  if (!checkoutBridge || !multiSummary.value.length || multiTotal.value <= 0) return false;
  for (const product of products.value) {
    const state = getMultiProductState(product.public_id);
    if (!state?.selected) continue;
    if (product.schedule_mode === "recurring" && !state.departureId) return false;
  }
  return true;
});

const resolveSectionInstallments = () => {
  const parsed = Number(props.section.installments);
  if (!Number.isFinite(parsed)) return 12;
  return Math.max(1, Math.min(Math.trunc(parsed), 12));
};

const checkoutSingle = () => {
  if (!checkoutBridge || !singleProduct.value) return;
  const product = singleProduct.value;
  const items = singleSelectedItems.value.map(item => {
    const schedule = singleState.schedules[item.variation.public_id];
    const slot = schedule?.departureSlots.find(entry => entry.departure_id === schedule?.departureId);
    return {
      productId: product.public_id,
      productName: product.name,
      productImageUrl: product.checkout_product_image_url || product.checkout_banner_url || null,
      variationId: item.variation.public_id,
      name: item.variation.name,
      dateLabel: product.schedule_mode === "recurring" ? buildDateLabel(schedule?.date || "") : null,
      departureLabel: product.schedule_mode === "recurring" ? (slot?.time || slot?.label || null) : null,
      quantity: item.quantity,
      unitAmount: item.variation.price_cents,
      currency: item.variation.currency,
      peopleCount: item.quantity * item.variation.people_included,
      consumedCapacity: item.quantity * item.variation.people_included,
      childExtraAmount: 0,
      childBreakdown: [],
      children: {},
      departureId: product.schedule_mode === "recurring" ? (schedule?.departureId ?? null) : null,
    };
  });
  const payload: ProductCheckoutPayload = {
    mode: "single",
    sectionId:
      props.section.anchorId ||
      (props.section as any).id ||
      (props.section as any).sectionId ||
      (props.section as any).section_id ||
      (typeof props.sectionIndex === "number" ? `products-${props.sectionIndex}` : ""),
    feeMode: props.section.feeMode === "pass_through" ? "pass_through" : "absorb",
    productId: product.public_id,
    productName: product.name,
    productDescription: product.description,
    installments: resolveSectionInstallments(),
    interestMode: props.section.interestMode || "merchant",
    maxInstallmentsNoInterest: props.section.maxInstallmentsNoInterest ?? null,
    allowedPaymentMethods: normalizedAllowedMethods(product),
    currency: singleCurrency.value,
    totalAmount: singleTotal.value,
    passengersRequired: items.reduce((sum, item) => sum + item.peopleCount, 0),
    consumedCapacity: items.reduce((sum, item) => sum + item.consumedCapacity, 0),
    items,
  };
  checkoutBridge.startCheckout(payload);
};

const checkoutMulti = () => {
  if (!checkoutBridge) return;
  const selectedProducts = products.value.filter(product => getMultiProductState(product.public_id)?.selected);
  if (selectedProducts.length > 1) {
    const baseline = methodsSignature(normalizedAllowedMethods(selectedProducts[0]));
    const hasIncompatibility = selectedProducts
      .slice(1)
      .some(product => methodsSignature(normalizedAllowedMethods(product)) !== baseline);
    if (hasIncompatibility) {
      selectionWarning.value = "Os produtos selecionados possuem formas de pagamento incompativeis.";
      return;
    }
  }
  const sectionId =
    props.section.anchorId ||
    (props.section as any).id ||
    (props.section as any).sectionId ||
    (props.section as any).section_id ||
    (typeof props.sectionIndex === "number" ? `products-${props.sectionIndex}` : "");
  const items: ProductCheckoutPayload["items"] = [];
  for (const entry of multiSummary.value) {
    const product = products.value.find(item => item.public_id === entry.productId);
    const variation = product?.variations.find(item => item.public_id === entry.variationId);
    if (!product || !variation) continue;
    items.push({
      productId: product.public_id,
      productName: product.name,
      productImageUrl: product.checkout_product_image_url || product.checkout_banner_url || null,
      variationId: variation.public_id,
      name: variation.name,
      dateLabel: entry.dateLabel ?? null,
      departureLabel: entry.departureLabel ?? null,
      quantity: entry.quantity,
      unitAmount: variation.price_cents,
      currency: variation.currency,
      peopleCount: entry.quantity * variation.people_included,
      consumedCapacity: entry.quantity * variation.people_included,
      childExtraAmount: 0,
      childBreakdown: [],
      children: {},
      departureId: entry.departureId ?? null,
    });
  }
  const payload: ProductCheckoutPayload = {
    mode: "multi",
    sectionId,
    feeMode: props.section.feeMode === "pass_through" ? "pass_through" : "absorb",
    installments: resolveSectionInstallments(),
    interestMode: props.section.interestMode || "merchant",
    maxInstallmentsNoInterest: props.section.maxInstallmentsNoInterest ?? null,
    allowedPaymentMethods: selectedProducts.length ? normalizedAllowedMethods(selectedProducts[0]) : ["pix", "credit_card", "boleto"],
    currency: multiCurrency.value,
    subtotalAmount: multiSubtotal.value,
    discountAmount: multiDiscount.value,
    discountLabel: multiDiscount.value > 0 ? "Desconto combo aplicado" : null,
    totalAmount: multiTotal.value,
    passengersRequired: items.reduce((sum, item) => sum + item.peopleCount, 0),
    consumedCapacity: items.reduce((sum, item) => sum + item.consumedCapacity, 0),
    items,
  };
  selectionWarning.value = null;
  checkoutBridge.startCheckout(payload);
};

const formatCurrency = (amountCents: number, currency = "BRL") => {
  const value = (amountCents || 0) / 100;
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(value);
  } catch {
    return `R$ ${value.toFixed(2)}`;
  }
};

onMounted(loadProducts);
watch(configuredIds, () => loadProducts());
</script>

<style scoped>
.input {
  @apply w-full rounded-xl border border-slate-200 px-3 py-2 text-sm;
}
.qty-btn {
  @apply grid h-8 w-8 place-items-center rounded-full border border-slate-300 text-lg font-semibold text-slate-700;
}
.checkout-btn {
  @apply w-full rounded-full px-4 py-3 text-sm font-semibold text-white;
}
.expand-btn {
  @apply inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-sm;
}
.expand-btn__chevron {
  @apply block h-1.5 w-1.5 shrink-0 rotate-45 border-r-2 border-b-2 border-current transition-transform duration-200;
  transform: translateY(-1px) rotate(45deg);
}
.expand-btn__chevron--open {
  transform: translateY(1px) rotate(225deg);
}
.section-title {
  @apply text-xs font-semibold uppercase tracking-[0.14em] text-slate-500;
}
.summary-box {
  @apply rounded-xl border border-slate-200 bg-gradient-to-b from-slate-50 to-white px-3 py-2 text-sm font-medium text-slate-700;
}
.recurring-flow {
  @apply space-y-6 rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm;
}
.recurring-step {
  @apply space-y-3;
}
.recurring-step-head {
  @apply flex flex-wrap items-center justify-between gap-3;
}
.recurring-step__label {
  @apply text-xs font-semibold uppercase tracking-[0.16em] text-slate-500;
}
.recurring-package-grid {
  @apply grid gap-3 sm:grid-cols-2;
}
.recurring-package-card {
  @apply rounded-2xl border border-slate-200 bg-white p-4 text-left transition duration-150 hover:-translate-y-0.5 hover:shadow-md;
}
.recurring-package-card--active {
  @apply border-emerald-500 bg-emerald-50/60 shadow-sm ring-1 ring-emerald-200;
}
.recurring-package-card__name {
  @apply block text-sm font-semibold text-slate-800;
}
.recurring-package-card__price {
  @apply mt-1 block text-lg font-bold text-slate-900;
}
.recurring-date-rail {
  @apply -mx-1 flex gap-2 overflow-x-auto px-1 pb-1;
  scrollbar-width: thin;
}
.recurring-date-pill {
  @apply flex min-w-[76px] flex-col items-center rounded-2xl border border-slate-200 bg-white px-3 py-2 text-center transition duration-150 hover:border-slate-300 hover:shadow-sm;
}
.recurring-date-pill:disabled {
  @apply cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400 shadow-none;
}
.recurring-date-pill--active {
  @apply border-slate-900 bg-slate-900 text-white;
}
.recurring-date-pill__weekday {
  @apply text-[11px] font-semibold tracking-[0.08em];
}
.recurring-date-pill__day {
  @apply mt-0.5 text-lg font-bold leading-none;
}
.recurring-schedule-grid {
  @apply grid gap-4 lg:grid-cols-[minmax(0,1.08fr)_minmax(280px,0.92fr)];
}
.recurring-calendar-card,
.recurring-slots-card {
  @apply rounded-[22px] border border-slate-200 bg-gradient-to-b from-white to-slate-50/80 p-4 shadow-sm;
}
.recurring-calendar-card {
  @apply overflow-hidden;
}
.recurring-calendar-subtitle {
  @apply mt-1 text-xs font-semibold text-slate-500;
}
.recurring-calendar-nav {
  @apply inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-2 py-1 text-sm font-bold text-slate-800 shadow-sm;
}
.recurring-calendar-nav button {
  @apply grid h-8 w-8 place-items-center rounded-full text-lg leading-none text-slate-600 transition hover:bg-slate-100 hover:text-slate-950;
}
.recurring-calendar-nav span {
  @apply min-w-[132px] text-center;
}
.recurring-weekdays {
  @apply grid grid-cols-7 gap-1 text-center text-[10px] font-extrabold uppercase tracking-[0.12em] text-slate-400;
}
.recurring-calendar-grid {
  @apply grid grid-cols-7 gap-1.5 rounded-[18px] bg-white/70 p-1 ring-1 ring-slate-100;
}
.recurring-calendar-day {
  @apply relative grid aspect-square min-h-11 place-items-center rounded-2xl border border-slate-200 bg-white text-sm font-extrabold text-slate-800 transition duration-150 hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-sm;
}
.recurring-calendar-day small {
  @apply absolute bottom-1 h-1.5 min-w-1.5 rounded-full bg-emerald-500 px-1 text-[0px] leading-none;
}
.recurring-calendar-day--today {
  @apply border-slate-900;
}
.recurring-calendar-day--disabled {
  @apply cursor-not-allowed border-transparent bg-transparent text-slate-300 shadow-none hover:translate-y-0 hover:border-transparent hover:shadow-none;
}
.recurring-calendar-day--active {
  @apply scale-[1.03] border-slate-950 bg-slate-950 text-white shadow-lg shadow-slate-900/15;
}
.recurring-calendar-day--active small {
  @apply bg-white;
}
.recurring-calendar-day--low small {
  @apply bg-amber-500;
}
.recurring-calendar-day--blank {
  @apply pointer-events-none border-transparent bg-transparent shadow-none;
}
.recurring-slots-head {
  @apply rounded-2xl border border-slate-200 bg-white p-3 shadow-sm;
}
.recurring-slots-head strong {
  @apply block text-base font-extrabold capitalize text-slate-950;
}
.recurring-slots-head span {
  @apply mt-1 block text-xs font-bold text-emerald-700;
}
.recurring-slot-grid {
  @apply flex flex-wrap gap-2;
}
.recurring-slot-pill {
  @apply min-w-[92px] rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm font-extrabold text-slate-800 transition duration-150 hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-md;
}
.recurring-slot-pill small {
  @apply mt-0.5 block text-[11px] font-semibold text-slate-500;
}
.recurring-slot-pill:disabled {
  @apply cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400 shadow-none;
}
.recurring-slot-pill--active {
  @apply border-slate-900 bg-slate-900 text-white shadow-lg shadow-slate-900/15;
}
.recurring-slot-pill--active small {
  @apply text-white/75;
}
.recurring-slot-helper {
  @apply text-xs font-semibold text-slate-500;
}
.recurring-empty-slot {
  @apply w-full rounded-2xl border border-dashed border-slate-200 bg-white p-4 text-center text-sm font-semibold text-slate-500;
}
.recurring-loading-chip {
  @apply inline-flex rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500;
}
.recurring-passenger-list {
  @apply space-y-2;
}
.recurring-passenger-row {
  @apply flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-3 py-2;
}
.recurring-passenger-row__name {
  @apply text-sm font-medium text-slate-700;
}
.recurring-stepper {
  @apply inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-1 py-1;
}
.recurring-stepper__btn {
  @apply grid h-8 w-8 place-items-center rounded-full border border-slate-300 bg-white text-lg font-semibold text-slate-700 transition hover:border-slate-400;
}
.recurring-stepper__value {
  @apply min-w-[2ch] text-center text-sm font-semibold text-slate-800;
}
.recurring-fade-enter-active,
.recurring-fade-leave-active {
  transition: all 0.18s ease;
}
.recurring-fade-enter-from,
.recurring-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
.chip {
  @apply rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:border-slate-400;
}
.chip:disabled {
  @apply cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400;
}
.chip-active {
  @apply border-slate-900 bg-slate-900 text-white hover:border-slate-900;
}
@media (max-width: 720px) {
  .recurring-flow {
    @apply px-4 py-4;
  }
  .recurring-package-grid {
    @apply grid-cols-1;
  }
}
</style>








