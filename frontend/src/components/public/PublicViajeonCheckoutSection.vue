<template>
  <!-- O layout segue a largura da seção (container queries), e não a da tela: fica igual na página
       publicada e na prévia de celular do editor. -->
  <section class="viajeon-checkout-section" :class="{ 'is-v2': v2 }" :style="sectionStyle">
    <div class="vc-wrap">
      <header class="vc-head">
        <h2 class="vc-title">{{ localized(section.title) || checkout?.name || "Escolha seu pacote" }}</h2>
        <p v-if="subtitle" class="vc-lead">{{ subtitle }}</p>
      </header>

      <div v-if="loading" class="state-card">Carregando pacotes disponíveis...</div>
      <div v-else-if="errorMessage" class="state-card error">{{ errorMessage }}</div>
      <div v-else-if="!packages.length" class="state-card">Nenhum pacote está disponível neste momento.</div>

      <div v-else class="checkout-layout">
        <div class="package-list">
          <article
            v-for="item in packages"
            :key="item.id"
            class="package-card"
            :class="{ 'is-picked': quantity(item.id) > 0 }"
            :style="cardStyle"
          >
            <div class="package-info">
              <h3>{{ item.name }}</h3>
              <p v-if="item.description">{{ item.description }}</p>
            </div>
            <p class="package-price">{{ formatMoney(item.price) }}</p>
            <div class="quantity-control">
              <button type="button" :aria-label="`Remover ${item.name}`" :disabled="quantity(item.id) === 0" @click="decrement(item)">−</button>
              <span aria-live="polite">{{ quantity(item.id) }}</span>
              <button type="button" :aria-label="`Adicionar ${item.name}`" :disabled="quantity(item.id) >= item.max_quantity" @click="increment(item)">+</button>
            </div>
          </article>
        </div>

        <aside class="checkout-summary" :style="cardStyle">
          <div class="summary-items">
            <p v-if="!selectedPackages.length" class="summary-empty">Nenhum pacote selecionado.</p>
            <div v-for="item in selectedPackages" :key="item.id" class="summary-item">
              <div>
                <strong>{{ item.name }}</strong>
                <span>{{ item.quantity }} {{ item.quantity === 1 ? "pacote" : "pacotes" }}</span>
              </div>
              <strong class="summary-subtotal">{{ formatMoney(item.subtotal) }}</strong>
            </div>
          </div>
          <div class="summary-footer">
            <div class="summary-total">
              <span>Total selecionado</span>
              <strong>{{ formatMoney(total) }}</strong>
            </div>
            <button
              type="button"
              class="checkout-button"
              :style="buttonStyle"
              :disabled="submitting || selectedItems.length === 0"
              @click="continueToCheckout"
            >
              {{ submitting ? "Preparando checkout..." : localized(section.buttonLabel) || "Continuar para o checkout" }}
            </button>
          </div>
          <V2Payments v-if="section.showPayments" :ids="section.paymentMethods" :note="section.paymentNote" align="left" />
        </aside>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import api from "../../services/api";
import platformApi from "../../services/platformApi";
import type { ViajeonCheckoutSection, ViajeonCheckoutSnapshot, ViajeonPackage } from "../../types/page";
import { getCurrentLanguage, getLocalizedValue } from "../../utils/i18n";
import V2Payments from "./v2/V2Payments.vue";

const props = defineProps<{
  section: ViajeonCheckoutSection;
  pageId?: number | null;
  platformHost?: boolean;
  /** Visual novo: fontes e título no padrão das outras seções v2. */
  v2?: boolean;
}>();
const route = useRoute();
const language = getCurrentLanguage();
const checkout = ref<ViajeonCheckoutSnapshot | null>(props.section.checkoutSnapshot || null);
const loading = ref(false);
const submitting = ref(false);
const errorMessage = ref("");
const quantities = reactive<Record<string, number>>({});
const client = computed(() => props.platformHost ? platformApi : api);
const packages = computed(() => (checkout.value?.packages || []).filter(item => item.active !== false));
const accentColor = computed(() => props.section.accentColor || props.section.buttonColor || "#12B981");
const sectionStyle = computed(() => ({
  backgroundColor: props.section.backgroundColor || "#F8FAFC",
  color: props.section.textColor || "#0F172A",
  "--vc-accent": accentColor.value
}));
const cardStyle = computed(() => ({
  backgroundColor: props.section.cardBackgroundColor || "#FFFFFF",
  color: props.section.cardTextColor || props.section.textColor || "#0F172A"
}));
const buttonStyle = computed(() => ({
  backgroundColor: props.section.buttonColor || accentColor.value,
  color: props.section.buttonTextColor || "#FFFFFF"
}));
const localized = (value: any) => getLocalizedValue(value, language);
const subtitle = computed(() => localized(props.section.subtitle) || checkout.value?.subtitle || "");
const quantity = (id: string) => quantities[id] || 0;
const selectedItems = computed(() => packages.value
  .filter(item => quantity(item.id) > 0)
  .map(item => ({ package_id: item.id, quantity: quantity(item.id) }))
);
const selectedPackages = computed(() => packages.value
  .filter(item => quantity(item.id) > 0)
  .map(item => ({
    id: item.id,
    name: item.name,
    quantity: quantity(item.id),
    subtotal: item.price * quantity(item.id)
  }))
);
const total = computed(() => packages.value.reduce((sum, item) => sum + item.price * quantity(item.id), 0));
const formatMoney = (value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);
const increment = (item: ViajeonPackage) => {
  const current = quantity(item.id);
  if (current >= item.max_quantity) return;
  quantities[item.id] = current === 0 ? Math.max(1, item.min_quantity || 1) : current + 1;
};
const decrement = (item: ViajeonPackage) => {
  const current = quantity(item.id);
  if (current <= 0) return;
  const next = current - 1;
  quantities[item.id] = next > 0 && next < (item.min_quantity || 1) ? 0 : next;
};

// A cópia salva aparece na hora; na página publicada, os pacotes e preços são
// atualizados com a ViajeOn em seguida. Se a consulta falhar, a cópia continua valendo.
const refreshFromViajeon = async () => {
  if (!props.pageId || !props.section.anchorId) return;
  try {
    const response = await client.value.get(
      `/public/integrations/viajeon/pages/${props.pageId}/sections/${encodeURIComponent(props.section.anchorId)}`
    );
    const live = response.data?.checkout as ViajeonCheckoutSnapshot | undefined;
    if (live?.packages?.length) checkout.value = live;
  } catch {
    /* sem integração ou ViajeOn fora do ar: segue com a cópia salva */
  }
};

const loadCheckout = async () => {
  if (props.section.checkoutSnapshot?.packages?.length) {
    checkout.value = props.section.checkoutSnapshot;
    errorMessage.value = "";
    void refreshFromViajeon();
    return;
  }
  if (!props.pageId || !props.section.anchorId) {
    checkout.value = props.section.checkoutSnapshot || null;
    return;
  }
  loading.value = true;
  errorMessage.value = "";
  try {
    const response = await client.value.get(
      `/public/integrations/viajeon/pages/${props.pageId}/sections/${encodeURIComponent(props.section.anchorId)}`
    );
    checkout.value = response.data?.checkout || null;
  } catch (error: any) {
    if (props.section.checkoutSnapshot?.packages?.length) {
      checkout.value = props.section.checkoutSnapshot;
    } else {
      errorMessage.value = error?.response?.data?.detail || "Não foi possível carregar os pacotes agora.";
    }
  } finally {
    loading.value = false;
  }
};

const buildViajeonCheckoutUrl = () => {
  const current = checkout.value;
  if (!current) throw new Error("missing-checkout");
  const rawUrl = current.checkout_url || (current.slug ? `https://app.viajeon.com/checkout/${current.slug}` : "");
  const url = new URL(rawUrl);
  if (url.protocol !== "https:" || url.hostname !== "app.viajeon.com" || !url.pathname.startsWith("/checkout/")) {
    throw new Error("invalid-checkout-url");
  }
  const qty = Object.fromEntries(selectedItems.value.map(item => [item.package_id, item.quantity]));
  url.searchParams.set("prefill", btoa(JSON.stringify({ qty })));
  for (const key of ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]) {
    const raw = route.query[key];
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (typeof value === "string" && value.trim()) url.searchParams.set(key, value.trim().slice(0, 255));
  }
  return url.toString();
};

const continueToCheckout = async () => {
  if (!selectedItems.value.length) return;
  submitting.value = true;
  errorMessage.value = "";
  try {
    window.location.assign(buildViajeonCheckoutUrl());
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível abrir o checkout. Tente novamente.";
    submitting.value = false;
  }
};

watch(() => [props.pageId, props.section.checkoutId, props.section.anchorId], loadCheckout);
onMounted(loadCheckout);
</script>

<style scoped>
.viajeon-checkout-section { container-type:inline-size; }
.vc-wrap { max-width:1152px; margin:0 auto; padding:clamp(48px,7cqi,80px) clamp(16px,4cqi,32px); }
.vc-head { max-width:768px; margin:0 auto clamp(28px,4cqi,40px); text-align:center; }
.vc-title { margin:0; font-size:clamp(26px,4cqi,36px); font-weight:800; line-height:1.15; text-wrap:balance; overflow-wrap:anywhere; }
.vc-lead { margin:12px 0 0; font-size:clamp(15px,1.8cqi,18px); line-height:1.5; opacity:.75; }
/* Visual novo: mesmas fontes e título das outras seções v2. */
.is-v2 { font-family:Figtree,system-ui,sans-serif; }
.is-v2 .vc-title { font-family:"Bricolage Grotesque",Figtree,sans-serif; font-weight:650; font-size:clamp(28px,4.2cqi,48px); line-height:1.05; letter-spacing:-.025em; }
.is-v2 :is(.package-price,.summary-total strong) { font-family:"Bricolage Grotesque",Figtree,sans-serif; letter-spacing:-.02em; }

/* Celular e tablet: uma coluna, resumo depois dos pacotes. Computador: resumo fixo ao lado. */
.checkout-layout { display:grid; grid-template-columns:minmax(0,1fr); gap:16px; }
.package-list { display:grid; gap:12px; }
.package-card { display:grid; grid-template-columns:minmax(0,1fr) auto; grid-template-areas:"info qty" "price qty"; align-items:center; column-gap:20px; row-gap:8px; border:1px solid color-mix(in srgb,currentColor 12%,transparent); border-radius:18px; padding:18px 20px; box-shadow:0 8px 28px rgba(15,23,42,.06); transition:border-color .15s,box-shadow .15s; }
.package-card.is-picked { border-color:var(--vc-accent); box-shadow:0 0 0 1px var(--vc-accent),0 8px 28px rgba(15,23,42,.06); }
.package-info { grid-area:info; min-width:0; }
.package-info h3 { margin:0; font-size:17px; font-weight:700; line-height:1.3; overflow-wrap:anywhere; }
.package-info p { margin:4px 0 0; font-size:14px; line-height:1.45; opacity:.7; }
.package-price { grid-area:price; margin:0; color:var(--vc-accent); font-size:20px; font-weight:800; line-height:1.2; white-space:nowrap; }
.quantity-control { grid-area:qty; display:grid; grid-template-columns:40px 36px 40px; align-items:center; overflow:hidden; border:1px solid var(--vc-accent); border-radius:12px; }
.quantity-control button { height:40px; font-size:20px; font-weight:700; background:transparent; color:inherit; touch-action:manipulation; }
.quantity-control button:disabled { opacity:.28; cursor:not-allowed; }
.quantity-control span { text-align:center; font-weight:800; font-variant-numeric:tabular-nums; }
.checkout-summary { display:grid; gap:20px; border:1px solid color-mix(in srgb,currentColor 12%,transparent); border-radius:18px; padding:22px; box-shadow:0 8px 28px rgba(15,23,42,.06); }
.summary-items { display:grid; gap:12px; border-bottom:1px solid color-mix(in srgb,currentColor 12%,transparent); padding-bottom:16px; }
.summary-item { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; font-size:14px; }
.summary-item > div { display:grid; gap:2px; min-width:0; overflow-wrap:anywhere; }
.summary-subtotal { white-space:nowrap; }
.summary-item span, .summary-empty { margin:0; font-size:12px; opacity:.65; }
.summary-footer { display:grid; gap:16px; }
.summary-total span { display:block; font-size:14px; opacity:.65; }
.summary-total strong { display:block; margin-top:2px; color:var(--vc-accent); font-size:clamp(26px,3.4cqi,32px); font-weight:800; line-height:1.1; white-space:nowrap; }
.checkout-button { width:100%; min-height:52px; border-radius:13px; padding:12px 24px; font-size:15px; font-weight:800; line-height:1.25; transition:filter .15s,transform .15s; }
.checkout-button:not(:disabled):hover { filter:brightness(1.05); transform:translateY(-1px); }
.checkout-button:disabled { cursor:not-allowed; opacity:.45; }
.state-card { border:1px solid color-mix(in srgb,currentColor 14%,transparent); border-radius:16px; padding:22px; text-align:center; opacity:.75; }
.state-card.error { color:#dc2626; opacity:1; }

/* Tablet: total e botão dividem a linha. */
@container (min-width:600px) and (max-width:879px) {
  .summary-footer { grid-template-columns:minmax(0,1fr) minmax(240px,auto); align-items:center; gap:20px; }
}
@container (min-width:880px) {
  .checkout-layout { grid-template-columns:minmax(0,1.6fr) minmax(300px,.8fr); align-items:start; gap:24px; }
  /* Abaixo do menu fixo do topo, quando a página tem um. */
  .checkout-summary { position:sticky; top:88px; }
}
/* Celular: nome e descrição em cima; preço e quantidade lado a lado, com botões maiores para o dedo. */
@container (max-width:520px) {
  .package-card { grid-template-areas:"info info" "price qty"; row-gap:14px; padding:16px; }
  .package-price { font-size:clamp(17px,5cqi,20px); }
  .quantity-control { grid-template-columns:44px 34px 44px; }
  .quantity-control button { height:44px; }
  .checkout-summary { padding:18px; }
  .checkout-button { padding:12px 16px; }
}
</style>
