<template>
  <div class="product-page" v-if="!loading && productReady">
    <ProductDetailHero
      :title="productForm.name || 'Produto sem nome'"
      :subtitle="heroSubtitle"
      :status-label="statusLabel"
      :status-tone="statusTone"
      :hero-meta="heroMeta"
      :trip-date-label="tripDateDisplay"
      :operation-label="productForm.is_road_trip ? 'Operacao rodoviaria' : 'Produto comercial'"
      :inventory-label="inventoryStrategyLabel"
      :image-url="heroImage"
      :is-create="isCreate"
      :saving="saving"
      :disabled="!productPublicId"
      :status-action-label="productForm.status === 'active' ? 'Desativar' : 'Ativar'"
      :stats="heroStats"
      :quick-actions="heroQuickActions"
      @create="createNewProduct"
      @sale="startNewSale"
      @duplicate="duplicateProduct"
      @toggle-status="toggleProductStatus"
      @edit="openDrawer('general')"
      @quick-action="handleQuickAction"
    />

    <section v-if="packageReports.length" class="package-report-section">
      <div class="package-report-section__header">
        <div>
          <p class="package-report-section__eyebrow">Relatorio por pacote</p>
          <h2>Pacotes e total consolidado</h2>
        </div>
        <div class="package-report-section__total">
          <span>Total</span>
          <strong>{{ packageReportsTotal.revenue }}</strong>
          <small>{{ packageReportsTotal.sold }} venda(s)</small>
        </div>
      </div>

      <div class="package-report-section__list">
        <article v-for="report in packageReports" :key="report.name" class="package-report-item">
          <div>
            <strong>{{ report.name }}</strong>
            <p>{{ report.occupancyLabel }}</p>
          </div>
          <div class="package-report-item__meta">
            <span>{{ report.sold }} venda(s)</span>
            <strong>{{ report.revenue }}</strong>
          </div>
        </article>
      </div>
    </section>

    <div class="product-layout">
      <main class="product-main">
        <section v-if="productForm.schedule_mode === 'recurring'" class="recurring-panel">
          <ScheduleTemplateEditor
            v-if="productPublicId"
            v-model="scheduleTemplateForm"
            :loading="scheduleLoading"
            @save="saveScheduleTemplate"
            @generate="generateDeparturesPreview"
          />
          <DeparturePreviewList :departures="scheduleDepartures" />
        </section>

        <PackagesSection
          :variations="productForm.variations"
          @add="openPackageDrawer()"
          @edit="openPackageDrawer"
          @duplicate="duplicateVariation"
          @remove="removeVariationAt"
        />

        <ProductChildrenRulesSection
          :variations="productForm.variations"
          @edit="openChildrenDrawer"
          @edit-summary="manageChildPolicies"
        />

        <ProductCheckoutMediaSection
          :banner-url="productForm.checkout_banner_url"
          :product-image-url="productForm.checkout_product_image_url"
          @edit="openMediaDrawer"
        />

        <ProductContractSection
          :has-template="!!productForm.template_contract_id"
          :template-name="currentTemplateName"
          :template-description="currentTemplateDescription"
          :disabled="!canEditContracts"
          @change="openContractDrawer"
          @view="viewCurrentTemplate"
          @manage="goToContractManagement"
        />
      </main>
    </div>

    <PackageDrawer
      v-if="drawerState.package"
      :variation="editingVariation"
      :visible="drawerState.package"
      @close="closeDrawer('package')"
      @save="saveVariation"
      @remove="removeVariation"
    />
    <ProductGeneralDrawer
      v-if="drawerState.general"
      :visible="drawerState.general"
      :value="productForm"
      :saving="saving"
      @close="closeDrawer('general')"
      @save="saveGeneral"
    />
    <TransportConfigDrawer
      v-if="drawerState.transport"
      :visible="drawerState.transport"
      :value="transportFormValue"
      :can-open-seatmap="!!productPublicId"
      :saving="saving"
      @close="closeDrawer('transport')"
      @save="saveTransport"
      @open-seatmap="goToSeatMap"
    />
    <BoardingLocationsDrawer
      v-if="drawerState.boarding"
      :visible="drawerState.boarding"
      :value="productForm.boarding_locations"
      :loading="boardingLoading"
      :saving="boardingSaving"
      @close="closeDrawer('boarding')"
      @save="saveBoardingLocations"
    />
    <ChildrenRuleDrawer
      v-if="drawerState.childRule"
      :visible="drawerState.childRule"
      :variation-name="childDrawerTarget.variationName"
      :rule="childDrawerTarget.rule"
      :saving="childDrawerSaving"
      @close="closeDrawer('childRule')"
      @save="saveChildRule"
    />
    <CheckoutMediaDrawer
      v-if="drawerState.media"
      :visible="drawerState.media"
      :value="{ banner: productForm.checkout_banner_url, product: productForm.checkout_product_image_url }"
      :saving="mediaSaving"
      @close="closeDrawer('media')"
      @save="saveMedia"
    />
    <ContractDrawer
      v-if="drawerState.contract"
      :visible="drawerState.contract"
      :templates="contractTemplates"
      :selected-id="productForm.template_contract_id"
      :loading="contractTemplatesLoading"
      :saving="contractSaving"
      @close="closeDrawer('contract')"
      @save="saveContractTemplate"
      @manage="goToContractManagement"
    />
  </div>

  <div v-else class="product-loader">
    <p>Carregando produto...</p>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import ProductDetailHero from "../../components/products/ProductDetailHero.vue";
import PackagesSection from "../../components/products/PackagesSection.vue";
import PackageDrawer from "../../components/products/PackageDrawer.vue";
import ProductGeneralDrawer from "../../components/products/ProductGeneralDrawer.vue";
import ProductCheckoutMediaSection from "../../components/products/ProductCheckoutMediaSection.vue";
import ProductChildrenRulesSection from "../../components/products/ProductChildrenRulesSection.vue";
import ProductContractSection from "../../components/products/ProductContractSection.vue";
import DeparturePreviewList from "../../components/schedule/DeparturePreviewList.vue";
import ScheduleTemplateEditor from "../../components/schedule/ScheduleTemplateEditor.vue";
import TransportConfigDrawer from "../../components/products/TransportConfigDrawer.vue";
import BoardingLocationsDrawer from "../../components/products/BoardingLocationsDrawer.vue";
import ChildrenRuleDrawer from "../../components/products/ChildrenRuleDrawer.vue";
import CheckoutMediaDrawer from "../../components/products/CheckoutMediaDrawer.vue";
import ContractDrawer from "../../components/products/ContractDrawer.vue";
import {
  createProduct,
  createScheduleTemplate,
  generateScheduleDepartures,
  getProductDetail,
  listScheduleDepartures,
  listScheduleTemplates,
  updateProduct,
  updateProductBoardingLocations,
  updateScheduleTemplate,
} from "../../services/finance";
import { listLegalTemplates } from "../../services/legal";
import type {
  ChildPricingRule,
  ChildPricingRulePayload,
  DepartureSummary,
  ProductDetail,
  ProductPayload,
  ScheduleTemplate,
  ScheduleTemplatePayload,
} from "../../types/finance";
import type { LegalTemplateSummary } from "../../types/legal";

type ChildRuleKey = "under_5" | "age_5_12";

type ChildRuleForm = {
  key: ChildRuleKey;
  label: string;
  min_age: number;
  max_age: number;
  enabled: boolean;
  pricing_mode: "free" | "extra";
  extra_amount: number;
  counts_towards_capacity: boolean;
  counts_as_passenger: boolean;
  max_quantity: number | null;
};

const CHILD_RULE_KEYS: ChildRuleKey[] = ["under_5", "age_5_12"];

type ProductVariationForm = {
  public_id: string | null;
  name: string;
  description: string | null;
  price: number;
  people_included: number;
  status: string;
  stock_mode: string;
  has_accommodation: boolean;
  accommodation_mode: "private" | "shared";
  room_capacity: number;
  slots_per_unit: number;
  total_slots: number | null;
  available_slots: number | null;
  child_policy_enabled: boolean;
  child_pricing_rules: ChildRuleForm[];
  sold_slots?: number | null;
};

type ProductFormState = {
  name: string;
  description: string | null;
  status: string;
  trip_date: string | null;
  date_is_flexible: boolean;
  inventory_strategy: "manual" | "unlimited";
  total_slots: number;
  available_slots: number;
  allow_oversell: boolean;
  template_contract_id: number | null;
  template_contract_name: string | null;
  checkout_banner_url: string | null;
  checkout_product_image_url: string | null;
  schedule_mode: "fixed_date" | "recurring";
  timezone: string | null;
  variations: ProductVariationForm[];
  boarding_locations: string[];
  is_road_trip: boolean;
  allowed_payment_methods: Array<"pix" | "credit_card" | "boleto">;
};

type DrawerKey = "general" | "package" | "transport" | "boarding" | "childRule" | "media" | "contract";

const defaultChildRules = (): ChildRuleForm[] => [
  {
    key: "under_5",
    label: "Menores de 5 anos",
    min_age: 0,
    max_age: 4,
    enabled: false,
    pricing_mode: "free",
    extra_amount: 0,
    counts_towards_capacity: false,
    counts_as_passenger: true,
    max_quantity: null,
  },
  {
    key: "age_5_12",
    label: "De 5 a 12 anos",
    min_age: 5,
    max_age: 12,
    enabled: false,
    pricing_mode: "extra",
    extra_amount: 0,
    counts_towards_capacity: true,
    counts_as_passenger: true,
    max_quantity: null,
  },
];

const toRuleForm = (rule?: ChildPricingRule): ChildRuleForm => {
  if (!rule) {
    return { ...defaultChildRules()[0] };
  }
  return {
    key: (rule.key as ChildRuleKey) || "under_5",
    label: rule.label || "",
    min_age: rule.min_age ?? 0,
    max_age: rule.max_age ?? 0,
    enabled: !!rule.enabled,
    pricing_mode: rule.pricing_mode === "extra" ? "extra" : "free",
    extra_amount: Math.max(0, (rule.extra_amount_cents || 0) / 100),
    counts_towards_capacity: !!rule.counts_towards_capacity,
    counts_as_passenger: rule.counts_as_passenger ?? true,
    max_quantity: typeof rule.max_quantity === "number" ? Math.max(0, rule.max_quantity) : null,
  };
};

const resolveRuleForms = (rules: ChildPricingRule[] | undefined | null): ChildRuleForm[] => {
  if (!rules || !rules.length) {
    return defaultChildRules();
  }
  const base = defaultChildRules();
  const filled = base.map(rule => {
    const match = rules.find(item => item.key === rule.key);
    return match ? toRuleForm(match) : rule;
  });
  return filled;
};

const serializeRuleForm = (rule: ChildRuleForm): ChildPricingRulePayload => ({
  key: rule.key,
  label: rule.label,
  min_age: Math.max(0, Math.floor(rule.min_age ?? 0)),
  max_age: Math.max(Math.max(0, Math.floor(rule.min_age ?? 0)), Math.floor(rule.max_age ?? 0)),
  enabled: rule.enabled,
  pricing_mode: rule.pricing_mode,
  extra_amount_cents: Math.round((rule.extra_amount || 0) * 100),
  counts_towards_capacity: !!rule.counts_towards_capacity,
  counts_as_passenger: !!rule.counts_as_passenger,
  max_quantity: typeof rule.max_quantity === "number" ? Math.max(0, rule.max_quantity) : null,
});

const defaultVariation = (): ProductVariationForm => ({
  public_id: null,
  name: "",
  description: null,
  price: 0,
  people_included: 1,
  status: "active",
  stock_mode: "shared",
  has_accommodation: false,
  accommodation_mode: "private",
  room_capacity: 1,
  slots_per_unit: 1,
  total_slots: null,
  available_slots: null,
  child_policy_enabled: false,
  child_pricing_rules: defaultChildRules(),
  sold_slots: 0,
});

const router = useRouter();
const route = useRoute();
const productForm = reactive<ProductFormState>({
  name: "",
  description: null,
  status: "draft",
  trip_date: null,
  date_is_flexible: false,
  inventory_strategy: "manual",
  total_slots: 0,
  available_slots: 0,
  allow_oversell: false,
  template_contract_id: null,
  template_contract_name: null,
  checkout_banner_url: null,
  checkout_product_image_url: null,
  schedule_mode: "fixed_date",
  timezone: "America/Sao_Paulo",
  variations: [],
  boarding_locations: [],
  is_road_trip: false,
  allowed_payment_methods: ["pix", "credit_card", "boleto"],
});
const loading = ref(true);
const saving = ref(false);
const autoSaveState = ref<"idle" | "dirty" | "saving" | "saved" | "error">("idle");
const lastSavedAt = ref<Date | null>(null);
const drawerState = reactive<Record<DrawerKey, boolean>>({
  general: false,
  package: false,
  transport: false,
  boarding: false,
  childRule: false,
  media: false,
  contract: false,
});
const editingVariation = ref<ProductVariationForm | null>(null);
const editingVariationIndex = ref<number | null>(null);
const productPublicId = computed(() => (route.params.productId as string) || null);
const isCreate = computed(() => route.name === "product-create");
const productReady = computed(() => isCreate.value || !!productPublicId.value);
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;
const boardingLoading = ref(false);
const boardingSaving = ref(false);
const childDrawerTarget = reactive<{ variationIndex: number; variationName: string; rule: ChildRuleForm | null }>({
  variationIndex: -1,
  variationName: "",
  rule: null,
});
const childDrawerSaving = ref(false);
const mediaSaving = ref(false);
const contractTemplates = ref<LegalTemplateSummary[]>([]);
const contractTemplatesLoading = ref(false);
const contractSaving = ref(false);
const scheduleLoading = ref(false);
const scheduleTemplateId = ref<number | null>(null);
const scheduleDepartures = ref<DepartureSummary[]>([]);
const scheduleTemplateForm = reactive<ScheduleTemplatePayload>({
  template_type: "weekday",
  start_date: new Date().toISOString().slice(0, 10),
  end_date: null,
  timezone: "America/Sao_Paulo",
  default_capacity: 0,
  default_price: null,
  generation_horizon_days: 90,
  is_active: true,
  weekdays: [0, 1, 2, 3, 4, 5, 6].map(weekday => ({ weekday, is_enabled: false })),
  times: [{ time: "09:00", capacity_override: null, price_override: null, sort_order: 0, is_active: true }],
  calendar_dates: [],
});

const heroImage = computed(() => productForm.checkout_banner_url || productForm.checkout_product_image_url);
const hasAccommodation = computed(() => productForm.variations.some(variation => variation.has_accommodation));
const heroSubtitle = computed(() => {
  if (productForm.description) {
    const trimmed = productForm.description.trim();
    return trimmed.length > 140 ? `${trimmed.slice(0, 137)}...` : trimmed;
  }
  if (productForm.is_road_trip) return "Operacao rodoviaria com experiencia completa";
  return "Produto exclusivo configurado para vendas premium";
});
const heroMeta = computed(() => {
  const bits: string[] = [];
  bits.push(productForm.is_road_trip ? "Excursao rodoviaria" : "Produto comercial");
  bits.push(hasAccommodation.value ? "inclui hospedagem" : "sem hospedagem");
  bits.push(productForm.inventory_strategy === "manual" ? "estoque controlado" : "estoque infinito");
  return bits.join(" · ");
});
const statusLabel = computed(() => {
  if (productForm.status === "active") return "Ativo";
  if (productForm.status === "archived") return "Arquivado";
  return "Rascunho";
});
const statusTone = computed<"success" | "muted" | "warning">(() => {
  if (productForm.status === "active") return "success";
  if (productForm.status === "archived") return "muted";
  return "warning";
});
const inventoryStrategyLabel = computed(() =>
  productForm.inventory_strategy === "unlimited" ? "Estoque ilimitado" : "Estoque manual",
);
const tripDateDisplay = computed(() => {
  if (!productForm.trip_date) return "Sem data definida";
  try {
    return new Date(productForm.trip_date).toLocaleDateString("pt-BR");
  } catch {
    return productForm.trip_date;
  }
});
const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
  }).format(value || 0);

const sidebarMetrics = computed(() => {
  const total = Math.max(0, productForm.total_slots);
  const available = Math.max(0, Math.min(productForm.available_slots, total));
  const reserved = Math.max(0, total - available);
  const sold = productForm.variations.reduce((sum, variation) => sum + (variation.sold_slots || 0), 0);
  const occupancy = total > 0 ? ((total - available) / total) * 100 : 0;
  return { total, available, reserved, sold, occupancy };
});
const estimatedRevenueTotal = computed(() =>
  productForm.variations.reduce((sum, variation) => sum + (variation.price || 0) * (variation.sold_slots || 0), 0),
);
const occupancyStatLabel = computed(() => {
  if (productForm.is_road_trip && hasAccommodation.value) return "Assento + quarto";
  if (productForm.is_road_trip) return "Assentos ocupados";
  if (hasAccommodation.value) return "Vagas no quarto";
  return "Ocupacao";
});
const heroStats = computed(() => [
  { label: "Vagas livres", value: sidebarMetrics.value.available },
  { label: "Vendidas", value: sidebarMetrics.value.sold },
  { label: occupancyStatLabel.value, value: `${sidebarMetrics.value.occupancy.toFixed(0)}%` },
  { label: "Faturamento total", value: formatCurrency(estimatedRevenueTotal.value) },
]);
const resolvePackageOccupancyLabel = (variation: ProductVariationForm) => {
  if (productForm.is_road_trip && variation.has_accommodation) return "Ocupa assento no onibus e vaga no quarto";
  if (productForm.is_road_trip) return "Ocupa assento no onibus";
  if (variation.has_accommodation) return "Ocupa vaga no quarto";
  return "Ocupa capacidade do produto";
};
const packageReports = computed(() =>
  productForm.variations.map(variation => ({
    name: variation.name || "Pacote sem nome",
    sold: variation.sold_slots || 0,
    revenue: formatCurrency((variation.price || 0) * (variation.sold_slots || 0)),
    occupancyLabel: resolvePackageOccupancyLabel(variation),
  })),
);
const packageReportsTotal = computed(() => ({
  sold: packageReports.value.reduce((sum, variation) => sum + variation.sold, 0),
  revenue: formatCurrency(estimatedRevenueTotal.value),
}));
const heroQuickActions = computed(() => {
  const items: Array<{ key: "payment-link" | "passengers" | "rooming" | "seatmap"; label: string; disabled: boolean }> = [
    { key: "payment-link", label: "Link de pagamento", disabled: !productPublicId.value },
    { key: "passengers", label: "Passageiros", disabled: !productPublicId.value },
  ];
  if (productForm.is_road_trip) {
    items.push({ key: "seatmap", label: "Mapa de assentos", disabled: !productPublicId.value });
  }
  if (hasAccommodation.value) {
    items.push({ key: "rooming", label: "Rooming list", disabled: !productPublicId.value });
  }
  return items;
});
const transportReady = computed(() => productForm.is_road_trip && productForm.boarding_locations.length > 0);
const transportFormValue = computed(() => ({
  is_road_trip: productForm.is_road_trip,
  allow_oversell: productForm.allow_oversell,
  inventory_strategy: productForm.inventory_strategy,
  total_slots: productForm.total_slots,
  available_slots: productForm.available_slots,
}));
const canEditContracts = computed(() => !!productPublicId.value);
const currentTemplate = computed(() => {
  if (!productForm.template_contract_id) return null;
  return (
    contractTemplates.value.find(template => template.id === productForm.template_contract_id) || null
  );
});
const currentTemplateName = computed(() => currentTemplate.value?.name || productForm.template_contract_name || "");
const currentTemplateDescription = computed(() => currentTemplate.value?.description || null);
const childRuleEntries = computed(() =>
  productForm.variations.flatMap((variation, variationIndex) =>
    (variation.child_pricing_rules || []).map(rule => ({
      variationIndex,
      variationName: variation.name,
      ...rule,
    })),
  ),
);
const childPolicySummary = computed(() => {
  if (!childRuleEntries.value.length) return "Nenhuma faixa infantil configurada.";
  const enabled = childRuleEntries.value.filter(rule => rule.enabled);
  if (!enabled.length) return "Politica pronta, mas nenhuma faixa ativa.";
  const labels = enabled
    .map(rule => `${rule.label || rule.key} (${rule.min_age}-${rule.max_age})`)
    .slice(0, 3)
    .join(", ");
  const more = enabled.length > 3 ? ` +${enabled.length - 3}` : "";
  return `${enabled.length} faixa(s) ativas: ${labels}${more}`;
});

const resetForm = () => {
  productForm.name = "";
  productForm.description = null;
  productForm.status = "draft";
  productForm.trip_date = null;
  productForm.date_is_flexible = false;
  productForm.inventory_strategy = "manual";
  productForm.total_slots = 0;
  productForm.available_slots = 0;
  productForm.allow_oversell = false;
  productForm.template_contract_id = null;
  productForm.template_contract_name = null;
  productForm.checkout_banner_url = null;
  productForm.checkout_product_image_url = null;
  productForm.schedule_mode = "fixed_date";
  productForm.timezone = "America/Sao_Paulo";
  productForm.boarding_locations = [];
  productForm.is_road_trip = false;
  productForm.allowed_payment_methods = ["pix", "credit_card", "boleto"];
  productForm.variations = [defaultVariation()];
};

const mapDetailToForm = (detail: ProductDetail) => {
  productForm.name = detail.name;
  productForm.description = detail.description ?? null;
  productForm.status = detail.status;
  productForm.trip_date = detail.trip_date ?? null;
  productForm.date_is_flexible = detail.date_is_flexible;
  productForm.inventory_strategy = detail.inventory_strategy;
  productForm.total_slots = detail.total_slots;
  productForm.available_slots = detail.available_slots;
  productForm.allow_oversell = detail.allow_oversell;
  productForm.template_contract_id = detail.template_contract_id ?? null;
  productForm.template_contract_name = detail.template_contract_name ?? null;
  productForm.checkout_banner_url = detail.checkout_banner_url ?? null;
  productForm.checkout_product_image_url = detail.checkout_product_image_url ?? null;
  productForm.schedule_mode = detail.schedule_mode || "fixed_date";
  productForm.timezone = detail.timezone ?? "America/Sao_Paulo";
  productForm.boarding_locations = detail.boarding_locations ? [...detail.boarding_locations] : [];
  productForm.is_road_trip = detail.is_road_trip;
  productForm.allowed_payment_methods = Array.isArray(detail.allowed_payment_methods) && detail.allowed_payment_methods.length
    ? [...detail.allowed_payment_methods]
    : ["pix", "credit_card", "boleto"];
  productForm.variations = detail.variations.map(variation => ({
    public_id: variation.public_id,
    name: variation.name,
    description: variation.description ?? null,
    price: variation.price_cents / 100,
    people_included: variation.people_included,
    status: variation.status,
    stock_mode: variation.stock_mode,
    has_accommodation: variation.has_accommodation ?? false,
    accommodation_mode: variation.accommodation_mode ?? "private",
    room_capacity: variation.room_capacity ?? variation.people_included ?? 1,
    slots_per_unit: variation.slots_per_unit ?? variation.people_included ?? 1,
    total_slots: variation.total_slots ?? null,
    available_slots: variation.available_slots ?? null,
    child_policy_enabled: variation.child_policy_enabled,
    child_pricing_rules: resolveRuleForms(variation.child_pricing_rules || []),
    sold_slots: variation.sold_slots || 0,
  }));
  if (!productForm.variations.length) {
    productForm.variations = [defaultVariation()];
  }
};

const applyScheduleTemplate = (template?: ScheduleTemplate | null) => {
  if (!template) {
    scheduleTemplateId.value = null;
    scheduleTemplateForm.template_type = "weekday";
    scheduleTemplateForm.start_date = new Date().toISOString().slice(0, 10);
    scheduleTemplateForm.end_date = null;
    scheduleTemplateForm.timezone = productForm.timezone || "America/Sao_Paulo";
    scheduleTemplateForm.default_capacity = productForm.total_slots || 0;
    scheduleTemplateForm.default_price = null;
    scheduleTemplateForm.generation_horizon_days = 90;
    scheduleTemplateForm.is_active = true;
    scheduleTemplateForm.weekdays = [0, 1, 2, 3, 4, 5, 6].map(weekday => ({ weekday, is_enabled: false }));
    scheduleTemplateForm.times = [{ time: "09:00", capacity_override: null, price_override: null, sort_order: 0, is_active: true }];
    scheduleTemplateForm.calendar_dates = [];
    return;
  }
  scheduleTemplateId.value = template.id;
  scheduleTemplateForm.template_type = template.template_type;
  scheduleTemplateForm.start_date = template.start_date;
  scheduleTemplateForm.end_date = template.end_date ?? null;
  scheduleTemplateForm.timezone = template.timezone;
  scheduleTemplateForm.default_capacity = template.default_capacity ?? null;
  scheduleTemplateForm.default_price = template.default_price ?? null;
  scheduleTemplateForm.generation_horizon_days = template.generation_horizon_days;
  scheduleTemplateForm.is_active = template.is_active;
  scheduleTemplateForm.weekdays = template.weekdays?.length
    ? template.weekdays.map(entry => ({ ...entry }))
    : [0, 1, 2, 3, 4, 5, 6].map(weekday => ({ weekday, is_enabled: false }));
  scheduleTemplateForm.times = template.times?.length
    ? template.times.map(entry => ({ ...entry }))
    : [{ time: "09:00", capacity_override: null, price_override: null, sort_order: 0, is_active: true }];
  scheduleTemplateForm.calendar_dates = template.calendar_dates?.length
    ? template.calendar_dates.map(entry => ({
        ...entry,
        times: (entry.times || []).map(time => ({ ...time })),
      }))
    : [];
};

const loadScheduleState = async () => {
  if (!productPublicId.value || productForm.schedule_mode !== "recurring") {
    scheduleDepartures.value = [];
    applyScheduleTemplate(null);
    return;
  }
  scheduleLoading.value = true;
  try {
    const [{ data: templates }, { data: departures }] = await Promise.all([
      listScheduleTemplates(productPublicId.value),
      listScheduleDepartures(
        productPublicId.value,
        new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString().slice(0, 10),
        new Date(Date.now() + 1000 * 60 * 60 * 24 * 60).toISOString().slice(0, 10),
      ),
    ]);
    applyScheduleTemplate(templates[0] || null);
    scheduleDepartures.value = departures.items || [];
  } catch (err) {
    console.error("Erro ao carregar agenda recorrente", err);
  } finally {
    scheduleLoading.value = false;
  }
};

const buildPayload = (): ProductPayload => ({
  name: productForm.name.trim(),
  description: productForm.description,
  status: productForm.status,
  trip_date: productForm.trip_date || undefined,
  date_is_flexible: productForm.date_is_flexible,
  inventory_strategy: productForm.inventory_strategy,
  total_slots: productForm.total_slots,
  available_slots: productForm.available_slots,
  allow_oversell: productForm.allow_oversell,
  template_contract_id: productForm.template_contract_id ?? undefined,
  checkout_banner_url: productForm.checkout_banner_url || undefined,
  checkout_product_image_url: productForm.checkout_product_image_url || undefined,
  schedule_mode: productForm.schedule_mode,
  timezone: productForm.schedule_mode === "recurring" ? productForm.timezone || undefined : undefined,
  variations: productForm.variations.map(variation => ({
    public_id: variation.public_id || undefined,
    name: variation.name.trim(),
    description: variation.description,
    price_cents: Math.round((variation.price || 0) * 100),
    currency: "BRL",
    people_included: variation.people_included || 1,
    status: variation.status,
    stock_mode: variation.stock_mode,
    has_accommodation: variation.has_accommodation,
    accommodation_mode: variation.has_accommodation ? variation.accommodation_mode : "private",
    room_capacity: variation.has_accommodation ? Math.max(1, variation.room_capacity || 1) : 1,
    slots_per_unit: variation.has_accommodation ? Math.max(1, variation.slots_per_unit || 1) : 1,
    total_slots: variation.stock_mode === "variant" ? variation.total_slots ?? undefined : undefined,
    available_slots: variation.stock_mode === "variant" ? variation.available_slots ?? undefined : undefined,
    child_policy_enabled: variation.child_policy_enabled,
    child_pricing_rules: variation.child_policy_enabled
      ? (variation.child_pricing_rules || []).map(serializeRuleForm)
      : [],
  })),
  boarding_locations: [...productForm.boarding_locations],
  has_rooms: productForm.variations.some(variation => variation.has_accommodation),
  is_road_trip: productForm.is_road_trip,
  allowed_payment_methods: productForm.allowed_payment_methods,
  rooms: [],
});

const scheduleAutoSave = () => {
  if (isCreate.value) return;
  autoSaveState.value = "dirty";
  if (typeof window === "undefined") return;
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
  }
  autoSaveTimer = window.setTimeout(async () => {
    await runAutoSave();
  }, 800);
};

const runAutoSave = async () => {
  if (!productPublicId.value) return;
  autoSaveState.value = "saving";
  try {
    const payload = buildPayload();
    const { data } = await updateProduct(productPublicId.value, payload);
    mapDetailToForm(data);
    if (productForm.schedule_mode === "recurring") {
      await loadScheduleState();
    }
    autoSaveState.value = "saved";
    lastSavedAt.value = new Date();
  } catch (err) {
    console.error("Erro ao salvar automaticamente", err);
    autoSaveState.value = "error";
  }
};

const openDrawer = (key: DrawerKey) => {
  drawerState[key] = true;
};

const closeDrawer = (key: DrawerKey) => {
  drawerState[key] = false;
};

const openPackageDrawer = (variation?: ProductVariationForm, index?: number) => {
  if (variation) {
    editingVariation.value = {
      ...variation,
      child_pricing_rules: (variation.child_pricing_rules || []).map(rule => ({ ...rule })),
    };
    editingVariationIndex.value = typeof index === "number" ? index : null;
  } else {
    const fresh = defaultVariation();
    editingVariation.value = {
      ...fresh,
      child_pricing_rules: fresh.child_pricing_rules.map(rule => ({ ...rule })),
    };
    editingVariationIndex.value = null;
  }
  openDrawer("package");
};

const saveVariation = (variation: ProductVariationForm) => {
  const normalized: ProductVariationForm = {
    ...variation,
    child_pricing_rules: (variation.child_pricing_rules || []).map(rule => ({ ...rule })),
  };
  if (editingVariationIndex.value === null) {
    productForm.variations.push(normalized);
  } else {
    productForm.variations.splice(editingVariationIndex.value, 1, normalized);
  }
  scheduleAutoSave();
  closeDrawer("package");
};

const removeVariation = () => {
  if (editingVariationIndex.value === null) {
    closeDrawer("package");
    return;
  }
  if (productForm.variations.length === 1) return;
  productForm.variations.splice(editingVariationIndex.value, 1);
  scheduleAutoSave();
  closeDrawer("package");
};

const duplicateVariation = (variation: ProductVariationForm) => {
  const copy: ProductVariationForm = {
    ...variation,
    public_id: null,
    name: `${variation.name} (copia)`,
  };
  productForm.variations.push(copy);
  scheduleAutoSave();
};

const removeVariationAt = (index: number) => {
  if (productForm.variations.length === 1) return;
  productForm.variations.splice(index, 1);
  scheduleAutoSave();
};

const manageChildPolicies = () => {
  const entries = childRuleEntries.value;
  if (!entries.length) {
    openPackageDrawer();
    return;
  }
  const target = entries.find(entry => entry.enabled) || entries[0];
  openChildrenDrawer({
    variationIndex: target.variationIndex,
    variationName: target.variationName,
    key: target.key as ChildRuleKey,
    label: target.label,
    min_age: target.min_age,
    max_age: target.max_age,
    pricing_mode: target.pricing_mode,
    extra_amount: target.extra_amount,
    max_quantity: target.max_quantity,
    counts_towards_capacity: target.counts_towards_capacity,
    counts_as_passenger: target.counts_as_passenger,
    enabled: target.enabled,
  });
};

const openTransportDrawer = () => {
  openDrawer("transport");
};

const saveTransport = async (payload: {
  is_road_trip: boolean;
  allow_oversell: boolean;
  inventory_strategy: "manual" | "unlimited";
  total_slots: number;
  available_slots: number;
}) => {
  productForm.is_road_trip = payload.is_road_trip;
  productForm.allow_oversell = payload.allow_oversell;
  productForm.inventory_strategy = payload.inventory_strategy;
  productForm.total_slots = payload.total_slots;
  productForm.available_slots = payload.available_slots;
  scheduleAutoSave();
  closeDrawer("transport");
};

const openBoardingDrawer = async () => {
  openDrawer("boarding");
  if (!productPublicId.value) return;
  boardingLoading.value = true;
  try {
    const { data } = await getProductDetail(productPublicId.value);
    productForm.boarding_locations = data.boarding_locations ? [...data.boarding_locations] : [];
  } catch (err) {
    console.error("Erro ao carregar locais de embarque", err);
  } finally {
    boardingLoading.value = false;
  }
};

const saveBoardingLocations = async (locations: string[]) => {
  if (isCreate.value || !productPublicId.value) {
    productForm.boarding_locations = [...locations];
    closeDrawer("boarding");
    return;
  }
  boardingSaving.value = true;
  try {
    await updateProductBoardingLocations(productPublicId.value, { locations });
    productForm.boarding_locations = [...locations];
    closeDrawer("boarding");
  } catch (err) {
    console.error("Erro ao salvar locais de embarque", err);
  } finally {
    boardingSaving.value = false;
  }
};

type ChildRuleViewPayload = {
  variationIndex: number;
  variationName: string;
  key: string;
  label: string;
  min_age: number;
  max_age: number;
  pricing_mode: "free" | "extra";
  extra_amount: number;
  max_quantity: number | null;
  counts_towards_capacity: boolean;
  counts_as_passenger: boolean;
  enabled: boolean;
};

const openChildrenDrawer = (payload: ChildRuleViewPayload) => {
  childDrawerTarget.variationIndex = payload.variationIndex;
  childDrawerTarget.variationName = payload.variationName;
  childDrawerTarget.rule = {
    key: payload.key as ChildRuleKey,
    label: payload.label,
    min_age: payload.min_age,
    max_age: payload.max_age,
    pricing_mode: payload.pricing_mode,
    extra_amount: payload.extra_amount,
    max_quantity: payload.max_quantity,
    counts_towards_capacity: payload.counts_towards_capacity,
    counts_as_passenger: payload.counts_as_passenger,
    enabled: payload.enabled,
  };
  openDrawer("childRule");
};

const saveChildRule = (rule: ChildRuleForm) => {
  const index = childDrawerTarget.variationIndex;
  if (index < 0 || index >= productForm.variations.length) {
    closeDrawer("childRule");
    return;
  }
  const variation = productForm.variations[index];
  variation.child_policy_enabled = true;
  variation.child_pricing_rules = variation.child_pricing_rules.map(existing =>
    existing.key === rule.key ? { ...rule } : existing,
  );
  scheduleAutoSave();
  closeDrawer("childRule");
};

const openMediaDrawer = () => {
  openDrawer("media");
};

const saveMedia = async (payload: { banner: string | null; product: string | null }) => {
  productForm.checkout_banner_url = payload.banner;
  productForm.checkout_product_image_url = payload.product;
  if (!productPublicId.value) {
    closeDrawer("media");
    return;
  }
  mediaSaving.value = true;
  try {
    await runAutoSave();
    closeDrawer("media");
  } finally {
    mediaSaving.value = false;
  }
};

const loadContractTemplates = async () => {
  if (contractTemplatesLoading.value) return;
  contractTemplatesLoading.value = true;
  try {
    const { data } = await listLegalTemplates();
    contractTemplates.value = data.items || [];
  } catch (err) {
    console.error("Erro ao carregar templates de contrato", err);
  } finally {
    contractTemplatesLoading.value = false;
  }
};

const openContractDrawer = async () => {
  if (!contractTemplates.value.length) {
    await loadContractTemplates();
  }
  openDrawer("contract");
};

const saveContractTemplate = async (templateId: number | null) => {
  productForm.template_contract_id = templateId;
  const template = contractTemplates.value.find(item => item.id === templateId);
  productForm.template_contract_name = template?.name || null;
  if (!productPublicId.value) {
    closeDrawer("contract");
    return;
  }
  contractSaving.value = true;
  try {
    await runAutoSave();
    closeDrawer("contract");
  } finally {
    contractSaving.value = false;
  }
};

const viewCurrentTemplate = () => {
  if (!productForm.template_contract_id) return;
  router.push({ name: "legal", query: { templateId: productForm.template_contract_id.toString() } });
};

const goToContractManagement = () => {
  router.push({ name: "legal" });
};

const saveGeneral = async (payload?: Partial<ProductFormState>) => {
  if (payload) {
    Object.assign(productForm, payload);
  }
  await runAutoSave();
  closeDrawer("general");
};

const normalizeScheduleTemplatePayload = (raw: ScheduleTemplatePayload): ScheduleTemplatePayload | null => {
  const timezone = (raw.timezone || productForm.timezone || "America/Sao_Paulo").trim();
  const startDate = (raw.start_date || "").trim();
  const endDateRaw = typeof raw.end_date === "string" ? raw.end_date.trim() : raw.end_date;

  if (!startDate) {
    console.error("Template inválido: start_date ausente.");
    return null;
  }
  if (!timezone) {
    console.error("Template inválido: timezone ausente.");
    return null;
  }

  if (raw.template_type === "weekday") {
    const defaultCapacity = Math.max(0, Number(productForm.total_slots || raw.default_capacity || 0));
    const weekdays = (raw.weekdays || []).map(entry => ({
      weekday: Number(entry.weekday),
      is_enabled: !!entry.is_enabled,
    }));
    const enabledWeekdays = weekdays.filter(entry => entry.is_enabled);
    const times = (raw.times || [])
      .map((entry, idx) => ({
        time: String(entry.time || "").trim(),
        capacity_override: null,
        price_override: null,
        sort_order: idx,
        is_active: entry.is_active !== false,
      }))
      .filter(entry => entry.time.length > 0);

    if (!enabledWeekdays.length) {
      console.error("Template inválido: nenhum dia da semana ativo.");
      return null;
    }
    if (!times.length) {
      console.error("Template inválido: nenhum horário válido.");
      return null;
    }

    return {
      ...raw,
      template_type: "weekday",
      start_date: startDate,
      end_date: endDateRaw ? String(endDateRaw) : null,
      timezone,
      default_capacity: defaultCapacity,
      default_price: null,
      weekdays,
      times,
      calendar_dates: [],
    };
  }

  const calendarDates = (raw.calendar_dates || [])
    .map(entry => ({
      date: String(entry.date || "").trim(),
      is_active: entry.is_active !== false,
      times: (entry.times || [])
        .map(time => ({
          time: String(time.time || "").trim(),
          capacity_override: null,
          price_override: null,
          is_active: time.is_active !== false,
        }))
        .filter(time => time.time.length > 0),
    }))
    .filter(entry => entry.date.length > 0 && entry.times.length > 0);

  if (!calendarDates.length) {
    console.error("Template inválido: calendário sem datas/horários válidos.");
    return null;
  }

  return {
    ...raw,
    template_type: "calendar",
    start_date: startDate,
    end_date: endDateRaw ? String(endDateRaw) : null,
    timezone,
    default_capacity: Math.max(0, Number(productForm.total_slots || raw.default_capacity || 0)),
    default_price: null,
    weekdays: [],
    times: [],
    calendar_dates: calendarDates,
  };
};

const saveScheduleTemplate = async (payload: ScheduleTemplatePayload) => {
  if (!productPublicId.value) return;
  if (productForm.schedule_mode !== "recurring") return;
  const normalizedPayload = normalizeScheduleTemplatePayload(payload);
  if (!normalizedPayload) {
    console.error("Template recorrente não enviado por dados inválidos.");
    return;
  }
  scheduleLoading.value = true;
  try {
    if (scheduleTemplateId.value) {
      const { data } = await updateScheduleTemplate(productPublicId.value, scheduleTemplateId.value, normalizedPayload);
      applyScheduleTemplate(data);
    } else {
      const { data } = await createScheduleTemplate(productPublicId.value, normalizedPayload);
      applyScheduleTemplate(data);
    }
  } catch (err) {
    const detail = (err as any)?.response?.data?.detail;
    console.error("Erro ao salvar template recorrente", detail || err);
  } finally {
    scheduleLoading.value = false;
  }
};

const generateDeparturesPreview = async () => {
  if (!productPublicId.value) return;
  scheduleLoading.value = true;
  try {
    await generateScheduleDepartures(productPublicId.value);
    const { data } = await listScheduleDepartures(
      productPublicId.value,
      new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString().slice(0, 10),
      new Date(Date.now() + 1000 * 60 * 60 * 24 * 90).toISOString().slice(0, 10),
    );
    scheduleDepartures.value = data.items || [];
  } catch (err) {
    console.error("Erro ao gerar saídas recorrentes", err);
  } finally {
    scheduleLoading.value = false;
  }
};

const toggleProductStatus = async () => {
  if (!productPublicId.value) return;
  productForm.status = productForm.status === "active" ? "draft" : "active";
  await runAutoSave();
};

const duplicateProduct = async () => {
  if (!productPublicId.value) return;
  saving.value = true;
  try {
    const payload = buildPayload();
    const { data } = await createProduct(payload);
    router.push({ name: "product-detail", params: { productId: data.public_id } });
  } finally {
    saving.value = false;
  }
};

const startNewSale = () => {
  if (!productPublicId.value) return;
  router.push({ name: "sales", query: { product: productPublicId.value } });
};

const goToSeatMap = () => {
  if (!productPublicId.value) return;
  router.push({ name: "product-seats", params: { productId: productPublicId.value } });
};

const goToRoomingList = () => {
  if (!productPublicId.value) return;
  router.push({ name: "product-rooming-list", params: { productId: productPublicId.value } });
};

const createNewProduct = async () => {
  saving.value = true;
  try {
    const payload = buildPayload();
    const { data } = await createProduct(payload);
    router.push({ name: "product-detail", params: { productId: data.public_id } });
  } catch (err) {
    console.error("Erro ao criar produto", err);
  } finally {
    saving.value = false;
  }
};

const openPaymentLinkFlow = () => {
  if (!productPublicId.value) return;
  router.push({ name: "sales", query: { product: productPublicId.value, action: "payment-link" } });
};

const handleQuickAction = (action: string) => {
  if (action === "passengers" && productPublicId.value) {
    router.push({ name: "product-passengers", params: { productId: productPublicId.value } });
    return;
  }
  if (action === "rooming") {
    goToRoomingList();
    return;
  }
  if (action === "seatmap") {
    goToSeatMap();
    return;
  }
  if (action === "payment-link") {
    openPaymentLinkFlow();
  }
};

const loadProduct = async () => {
  loading.value = true;
  if (!productPublicId.value) {
    resetForm();
    applyScheduleTemplate(null);
    scheduleDepartures.value = [];
    drawerState.general = true;
    loading.value = false;
    return;
  }
  try {
    const { data } = await getProductDetail(productPublicId.value);
    mapDetailToForm(data);
    await loadScheduleState();
  } catch (err) {
    console.error("Erro ao carregar produto", err);
  } finally {
    loading.value = false;
  }
};

watch(
  () => route.params.productId,
  () => {
    loadProduct();
  },
  { immediate: true },
);
</script>

<style scoped>
.product-page {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
  padding-bottom: 4rem;
}
.package-report-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.45rem 1.55rem;
  border-radius: 1.75rem;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.72);
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
}
.package-report-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.package-report-section__eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}
.package-report-section__header h2 {
  margin: 0;
  font-size: 1.12rem;
  font-weight: 700;
  color: #0f172a;
}
.package-report-section__total {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.12rem;
  text-align: right;
}
.package-report-section__total span,
.package-report-section__total small {
  color: #94a3b8;
}
.package-report-section__total strong {
  font-size: 1.08rem;
  color: #0f172a;
}
.package-report-section__list {
  display: grid;
  gap: 0.75rem;
}
.package-report-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(226, 232, 240, 0.78);
}
.package-report-item:first-child {
  padding-top: 0;
  border-top: none;
}
.package-report-item strong {
  color: #0f172a;
}
.package-report-item p,
.package-report-item__meta span {
  margin: 0.22rem 0 0;
  font-size: 0.84rem;
  color: #64748b;
}
.package-report-item__meta {
  text-align: right;
}
.package-report-item__meta strong {
  display: block;
  margin-top: 0.2rem;
}
.product-hero {
  display: grid;
  gap: 2rem;
  grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  align-items: center;
}
.hero-info {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.hero-topline {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  font-size: 0.9rem;
  color: #475569;
}
.hero-info h1 {
  font-size: clamp(2.2rem, 4vw, 3rem);
  font-weight: 700;
  color: #0f172a;
}
.hero-description {
  font-size: 1rem;
  color: #475569;
  max-width: 60ch;
}
.hero-meta.row,
.hero-metrics.row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  color: #475569;
  font-size: 0.95rem;
}
.hero-metrics strong {
  font-size: 1.2rem;
  color: #0f172a;
  margin-right: 0.25rem;
}
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.hero-media img {
  width: 100%;
  border-radius: 1.5rem;
  object-fit: cover;
  box-shadow: 0 25px 60px -35px rgba(15, 23, 42, 0.4);
}
.product-layout {
  display: grid;
  gap: 2rem;
}
.summary-section,
.status-section,
.packages-section,
.child-policy-section,
.checkout-preview-section,
.contract-section {
  background: white;
  border-radius: 1.25rem;
  border: 1px solid #e2e8f0;
  padding: 1.5rem;
}
.summary-section header,
.status-section header,
.packages-section header,
.child-policy-section header,
.checkout-preview-section header,
.contract-section header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.summary-text {
  font-size: 1rem;
  color: #475569;
  margin-bottom: 0.75rem;
}
.summary-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 1rem 2rem;
  color: #475569;
}
.status-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.status-section li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0;
  color: #475569;
}
.status-section li::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: currentColor;
}
.status-section li.ok {
  color: #10b981;
}
.status-section li.warn {
  color: #f59e0b;
}
.status-section li.mute {
  color: #94a3b8;
}
.packages-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.child-policy-section p {
  margin: 0;
  color: #475569;
}
.checkout-preview-section,
.contract-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.btn-primary {
  border-radius: 999px;
  background: #0f172a;
  color: white;
  padding: 0.55rem 1.25rem;
  font-weight: 600;
  border: none;
}
.btn-ghost {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.15);
  padding: 0.5rem 1.1rem;
  font-weight: 600;
  background: transparent;
  color: #0f172a;
}
.btn-primary:disabled,
.btn-ghost:disabled {
  opacity: 0.4;
}
.w-full {
  width: 100%;
  text-align: center;
}
.text-button {
  border: none;
  background: transparent;
  color: #0f172a;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0;
  cursor: pointer;
}
.pill {
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.15);
  padding: 0.3rem 0.9rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #0f172a;
  background: #f8fafc;
}
.product-loader {
  min-height: 40vh;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
}

.product-page {
  gap: 2.35rem;
}

.product-layout {
  gap: 2rem;
}

.product-main {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.recurring-panel {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-shell {
  display: flex;
  flex-direction: column;
  gap: 1.55rem;
  padding: 1.6rem;
  border-radius: 1.75rem;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.7);
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
  margin-top: 0;
}

.packages-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem;
}

.section-kicker {
  margin: 0 0 0.45rem;
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.packages-header h2 {
  margin: 0;
  font-size: 1.56rem;
  letter-spacing: -0.045em;
  color: #0f172a;
}

.packages-header p:last-child {
  margin: 0.55rem 0 0;
  max-width: 42rem;
  font-size: 0.96rem;
  color: #64748b;
  line-height: 1.6;
}

.section-button {
  min-height: 2.95rem;
  padding: 0.78rem 1.15rem;
  border-radius: 1rem;
  border: 1px solid rgba(15, 23, 42, 0.05);
  background: linear-gradient(180deg, #111827, #0f172a);
  color: #fff;
  font-weight: 700;
  box-shadow: 0 18px 34px -26px rgba(15, 23, 42, 0.45);
}

@media (max-width: 720px) {
  .product-page {
    gap: 1.5rem;
  }

  .package-report-section {
    padding: 1.2rem;
  }

  .package-report-section__header,
  .package-report-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .package-report-section__total,
  .package-report-item__meta {
    align-items: flex-start;
    text-align: left;
  }

  .section-shell {
    padding: 1.25rem;
  }

  .packages-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>


