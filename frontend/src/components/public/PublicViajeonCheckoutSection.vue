<template>
  <section class="viajeon-checkout-section px-4 py-14 md:px-8 md:py-20" :style="sectionStyle">
    <div class="mx-auto max-w-6xl">
      <header class="mx-auto max-w-3xl text-center">
        <h2 class="text-3xl font-extrabold md:text-4xl">{{ localized(section.title) || checkout?.name || "Escolha seu pacote" }}</h2>
        <p class="mt-3 text-base opacity-75 md:text-lg">{{ localized(section.subtitle) || checkout?.subtitle }}</p>
      </header>

      <div v-if="loading" class="state-card mt-10">Carregando pacotes disponíveis...</div>
      <div v-else-if="errorMessage" class="state-card error mt-10">{{ errorMessage }}</div>
      <div v-else-if="!packages.length" class="state-card mt-10">Nenhum pacote está disponível neste momento.</div>

      <div v-else class="checkout-layout mt-10">
        <div class="package-list">
          <article v-for="item in packages" :key="item.id" class="package-card" :style="cardStyle">
            <div class="min-w-0 flex-1">
              <h3 class="text-lg font-bold">{{ item.name }}</h3>
              <p v-if="item.description" class="mt-1 text-sm opacity-70">{{ item.description }}</p>
              <p class="mt-4 text-xl font-extrabold" :style="{ color: accentColor }">{{ formatMoney(item.price) }}</p>
            </div>
            <div class="quantity-control" :style="{ borderColor: accentColor }">
              <button type="button" :aria-label="`Remover ${item.name}`" :disabled="quantity(item.id) === 0" @click="decrement(item)">−</button>
              <span>{{ quantity(item.id) }}</span>
              <button type="button" :aria-label="`Adicionar ${item.name}`" :disabled="quantity(item.id) >= item.max_quantity" @click="increment(item)">+</button>
            </div>
          </article>
        </div>

        <aside class="checkout-summary" :style="cardStyle">
          <div class="summary-items">
            <p v-if="!selectedPackages.length" class="summary-empty">Nenhum pacote selecionado.</p>
            <div v-for="item in selectedPackages" :key="item.id" class="summary-item">
              <div class="min-w-0">
                <strong>{{ item.name }}</strong>
                <span>{{ item.quantity }} {{ item.quantity === 1 ? "pacote" : "pacotes" }}</span>
              </div>
              <strong>{{ formatMoney(item.subtotal) }}</strong>
            </div>
          </div>
          <div>
            <span class="text-sm opacity-65">Total selecionado</span>
            <strong class="mt-1 block text-3xl font-extrabold" :style="{ color: accentColor }">{{ formatMoney(total) }}</strong>
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

const props = defineProps<{
  section: ViajeonCheckoutSection;
  pageId?: number | null;
  platformHost?: boolean;
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
  color: props.section.textColor || "#0F172A"
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

const loadCheckout = async () => {
  if (props.section.checkoutSnapshot?.packages?.length) {
    checkout.value = props.section.checkoutSnapshot;
    errorMessage.value = "";
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
.checkout-layout { display:grid; grid-template-columns:minmax(0,1.6fr) minmax(280px,.8fr); align-items:start; gap:24px; }
.package-list { display:grid; gap:16px; }
.package-card { display:flex; align-items:center; gap:20px; border:1px solid color-mix(in srgb,currentColor 12%,transparent); border-radius:18px; padding:20px; box-shadow:0 8px 28px rgba(15,23,42,.06); }
.quantity-control { display:grid; grid-template-columns:36px 40px 36px; align-items:center; flex:0 0 auto; overflow:hidden; border:1px solid; border-radius:12px; }
.quantity-control button { height:38px; font-size:20px; font-weight:700; background:transparent; color:inherit; }
.quantity-control button:disabled { opacity:.28; cursor:not-allowed; }
.quantity-control span { text-align:center; font-weight:800; }
.checkout-summary { position:sticky; top:24px; display:grid; gap:28px; border:1px solid color-mix(in srgb,currentColor 12%,transparent); border-radius:18px; padding:24px; box-shadow:0 8px 28px rgba(15,23,42,.06); }
.summary-items { display:grid; gap:12px; border-block:1px solid color-mix(in srgb,currentColor 12%,transparent); padding-block:16px; }
.summary-item { display:flex; align-items:center; justify-content:space-between; gap:16px; font-size:14px; }
.summary-item > div { display:grid; gap:2px; }
.summary-item span, .summary-empty { font-size:12px; opacity:.65; }
.checkout-button { width:100%; min-height:48px; border-radius:13px; padding:12px 24px; font-size:15px; font-weight:800; transition:filter .15s,transform .15s; }
.checkout-button:not(:disabled):hover { filter:brightness(1.05); transform:translateY(-1px); }
.checkout-button:disabled { cursor:not-allowed; opacity:.45; }
.state-card { border:1px solid color-mix(in srgb,currentColor 14%,transparent); border-radius:16px; padding:22px; text-align:center; opacity:.75; }
.state-card.error { color:#dc2626; opacity:1; }
@media(max-width:767px){ .checkout-layout{grid-template-columns:1fr}.checkout-summary{position:static}.package-card{align-items:flex-start;flex-direction:column}.quantity-control{align-self:stretch;grid-template-columns:1fr 54px 1fr} }
</style>
