<template>
  <div class="product-page" v-if="!loading && productReady">
    <section class="product-hero">
      <div class="hero-info">
        <div class="hero-topline">
          <span class="pill">{{ statusLabel }}</span>
          <span class="hero-meta">{{ heroMeta }}</span>
        </div>
        <h1>{{ productForm.name || "Produto sem nome" }}</h1>
        <p class="hero-description">{{ heroSubtitle }}</p>
        <div class="hero-meta row">
          <span>{{ tripDateDisplay }}</span>
          <span v-if="productForm.is_road_trip">· Operacao rodoviaria</span>
          <span>· {{ inventoryStrategyLabel }}</span>
        </div>
        <div class="hero-actions">
          <template v-if="isCreate">
            <button type="button" class="btn-primary" @click="createNewProduct" :disabled="saving">
              {{ saving ? "Criando..." : "Criar produto" }}
            </button>
          </template>
          <template v-else>
            <button type="button" class="btn-primary" @click="startNewSale">Nova venda</button>
            <button type="button" class="btn-ghost" @click="duplicateProduct" :disabled="saving">Duplicar</button>
            <button type="button" class="btn-ghost" @click="toggleProductStatus" :disabled="saving">
              {{ productForm.status === "active" ? "Desativar" : "Ativar" }}
            </button>
          </template>
        </div>
        <div class="hero-metrics row">
          <span><strong>{{ sidebarMetrics.available }}</strong> vagas livres</span>
          <span><strong>{{ sidebarMetrics.sold }}</strong> vendidas</span>
          <span><strong>{{ sidebarMetrics.occupancy.toFixed(0) }}%</strong> ocupacao</span>
        </div>
      </div>
      <div class="hero-media" v-if="heroImage">
        <img :src="heroImage" alt="" />
      </div>
    </section>

    <div class="product-layout">
      <main class="product-main">
        <section class="summary-section">
          <header>
            <h2>Visao geral</h2>
            <button type="button" class="text-button" @click="openDrawer('general')">Editar dados</button>
          </header>
          <p class="summary-text">{{ summaryText }}</p>
          <ul class="summary-list">
            <li>Status: <strong>{{ statusLabel }}</strong></li>
            <li>Estrategia: <strong>{{ inventoryStrategyLabel }}</strong></li>
            <li>Overbooking: <strong>{{ productForm.allow_oversell ? "habilitado" : "desativado" }}</strong></li>
            <li>Rodoviario: <strong>{{ productForm.is_road_trip ? "habilitado" : "desativado" }}</strong></li>
          </ul>
        </section>

        <section class="status-section">
          <header>
            <h2>Operacao em tempo real</h2>
            <button type="button" class="text-button" @click="openTransportDrawer">Ajustar transporte</button>
          </header>
          <ul>
            <li :class="transportReady ? 'ok' : 'warn'">
              <span>{{ transportReady ? "Transporte pronto para alocar passageiros." : "Defina layouts e embarques." }}</span>
            </li>
            <li :class="productForm.boarding_locations.length ? 'ok' : 'warn'">
              <span v-if="productForm.boarding_locations.length">
                {{ productForm.boarding_locations.length }} locais de embarque publicados.
              </span>
              <span v-else>Nenhum local de embarque informado.</span>
            </li>
            <li :class="hasAccommodation ? 'ok' : 'mute'">
              <span>{{ hasAccommodation ? "Hospedagem configurada nos pacotes." : "Sem hospedagem ligada aos pacotes." }}</span>
            </li>
          </ul>
        </section>

        <section class="packages-section">
          <header>
            <h2>Pacotes e tarifas</h2>
            <button type="button" class="text-button" @click="openPackageDrawer()">Adicionar pacote</button>
          </header>
          <div class="packages-list">
            <PackageCard
              v-for="(variation, index) in productForm.variations"
              :key="variation.public_id || index"
              :variation="variation"
              @edit="openPackageDrawer(variation, index)"
              @duplicate="duplicateVariation(variation)"
              @remove="removeVariationAt(index)"
            />
          </div>
        </section>

        <section class="child-policy-section">
          <header>
            <div>
              <h2>Politica infantil</h2>
              <p>{{ childPolicySummary }}</p>
            </div>
            <button type="button" class="text-button" @click="manageChildPolicies">Gerenciar faixas</button>
          </header>
        </section>

        <section class="checkout-preview-section">
          <header>
            <h2>Preview do checkout</h2>
            <button type="button" class="text-button" @click="openMediaDrawer">Atualizar midia</button>
          </header>
          <ProductCheckoutMediaSection
            :banner-url="productForm.checkout_banner_url"
            :product-image-url="productForm.checkout_product_image_url"
            @edit="openMediaDrawer"
          />
        </section>

        <section class="contract-section">
          <header>
            <h2>Contrato e documentos</h2>
            <button type="button" class="text-button" @click="openContractDrawer">
              {{ productForm.template_contract_id ? "Alterar template" : "Vincular template" }}
            </button>
          </header>
          <p>{{ contractSummary }}</p>
        </section>
      </main>

      <aside class="insight-panel">
        <div class="panel-row">
          <h3>Situacao</h3>
          <p>{{ statusLabel }} · {{ sidebarMetrics.sold }} vendas · {{ sidebarMetrics.available }} vagas livres</p>
        </div>
        <div class="panel-row actions">
          <button type="button" class="btn-primary w-full" @click="startNewSale" :disabled="!productPublicId">
            Nova venda
          </button>
          <button type="button" class="btn-ghost w-full" @click="openPaymentLinkFlow" :disabled="!productPublicId">
            Link de pagamento
          </button>
          <button type="button" class="btn-ghost w-full" @click="openTransportDrawer">Ajustar operacao</button>
        </div>
        <div class="panel-row save-status">
          <SaveStatusIndicator :state="autoSaveState" :updated-at="lastSavedAt" />
        </div>
      </aside>
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
import SaveStatusIndicator from "../../components/products/SaveStatusIndicator.vue";
import PackageCard from "../../components/products/PackageCard.vue";
import PackageDrawer from "../../components/products/PackageDrawer.vue";
import ProductGeneralDrawer from "../../components/products/ProductGeneralDrawer.vue";
import ProductCheckoutMediaSection from "../../components/products/ProductCheckoutMediaSection.vue";
import TransportConfigDrawer from "../../components/products/TransportConfigDrawer.vue";
import BoardingLocationsDrawer from "../../components/products/BoardingLocationsDrawer.vue";
import ChildrenRuleDrawer from "../../components/products/ChildrenRuleDrawer.vue";
import CheckoutMediaDrawer from "../../components/products/CheckoutMediaDrawer.vue";
import ContractDrawer from "../../components/products/ContractDrawer.vue";
import { createProduct, getProductDetail, updateProduct, updateProductBoardingLocations } from "../../services/finance";
import { listLegalTemplates } from "../../services/legal";
import type { ChildPricingRule, ChildPricingRulePayload, ProductDetail, ProductPayload } from "../../types/finance";
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
  card_interest_mode: "merchant" | "customer";
  template_contract_id: number | null;
  template_contract_name: string | null;
  checkout_banner_url: string | null;
  checkout_product_image_url: string | null;
  variations: ProductVariationForm[];
  boarding_locations: string[];
  is_road_trip: boolean;
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
  stock_mode: "product",
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
  card_interest_mode: "merchant",
  template_contract_id: null,
  template_contract_name: null,
  checkout_banner_url: null,
  checkout_product_image_url: null,
  variations: [],
  boarding_locations: [],
  is_road_trip: false,
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
const summaryText = computed(() =>
  productForm.description
    ? productForm.description
    : "Adicione uma descricao envolvente para apresentar este produto aos clientes.",
);
const statusLabel = computed(() => {
  if (productForm.status === "active") return "Ativo";
  if (productForm.status === "archived") return "Arquivado";
  return "Rascunho";
});
const statusBadgeClass = computed(() => {
  if (productForm.status === "active") return "badge-success";
  if (productForm.status === "archived") return "badge-muted";
  return "badge-warning";
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
const sidebarMetrics = computed(() => {
  const total = Math.max(0, productForm.total_slots);
  const available = Math.max(0, Math.min(productForm.available_slots, total));
  const reserved = Math.max(0, total - available);
  const sold = productForm.variations.reduce((sum, variation) => sum + (variation.sold_slots || 0), 0);
  const occupancy = total > 0 ? ((total - available) / total) * 100 : 0;
  return { total, available, reserved, sold, occupancy };
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
const contractSummary = computed(() => {
  if (!productForm.template_contract_id) return "Nenhum template vinculado · contratos nao sao enviados automaticamente.";
  return `Template ${currentTemplateName.value || "definido"} enviado automaticamente apos confirmacao.`;
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
  productForm.card_interest_mode = "merchant";
  productForm.template_contract_id = null;
  productForm.template_contract_name = null;
  productForm.checkout_banner_url = null;
  productForm.checkout_product_image_url = null;
  productForm.boarding_locations = [];
  productForm.is_road_trip = false;
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
  productForm.card_interest_mode = detail.card_interest_mode || "merchant";
  productForm.template_contract_id = detail.template_contract_id ?? null;
  productForm.template_contract_name = detail.template_contract_name ?? null;
  productForm.checkout_banner_url = detail.checkout_banner_url ?? null;
  productForm.checkout_product_image_url = detail.checkout_product_image_url ?? null;
  productForm.boarding_locations = detail.boarding_locations ? [...detail.boarding_locations] : [];
  productForm.is_road_trip = detail.is_road_trip;
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
  card_interest_mode: productForm.card_interest_mode,
  template_contract_id: productForm.template_contract_id ?? undefined,
  checkout_banner_url: productForm.checkout_banner_url || undefined,
  checkout_product_image_url: productForm.checkout_product_image_url || undefined,
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

const saveContractTemplate = async (templateId: number) => {
  productForm.template_contract_id = templateId;
  const template = contractTemplates.value.find(item => item.id === templateId);
  productForm.template_contract_name = template?.name || productForm.template_contract_name;
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

const handleSidebarAction = (action: string) => {
  if (action === "sale") {
    startNewSale();
    return;
  }
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
    return;
  }
  if (action === "inventory") {
    openDrawer("general");
  }
};

const loadProduct = async () => {
  loading.value = true;
  if (!productPublicId.value) {
    resetForm();
    loading.value = false;
    return;
  }
  try {
    const { data } = await getProductDetail(productPublicId.value);
    mapDetailToForm(data);
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
@media (min-width: 1024px) {
  .product-layout {
    grid-template-columns: minmax(0, 3fr) minmax(260px, 1fr);
  }
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
.insight-panel {
  position: sticky;
  top: 4rem;
  align-self: start;
  border: 1px solid #e2e8f0;
  border-radius: 1.5rem;
  padding: 1.25rem;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.panel-row h3 {
  margin: 0 0 0.25rem;
  font-size: 1rem;
  color: #0f172a;
}
.panel-row p {
  margin: 0;
  color: #475569;
  font-size: 0.9rem;
}
.panel-row.actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.panel-row.save-status {
  border-top: 1px solid #e2e8f0;
  padding-top: 0.75rem;
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
</style>

