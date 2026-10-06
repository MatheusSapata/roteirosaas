<template>
  <div v-if="methods.length || brands.length || note" class="v2-pay" :class="{ 'is-left': align === 'left' }">
    <span class="v2-pay-title">{{ copy.title }}</span>
    <ul v-if="methods.length" class="v2-pay-methods">
      <li v-for="item in methods" :key="item.id" class="v2-pay-method">
        <svg v-if="item.id === 'pix'" viewBox="0 0 24 24" aria-hidden="true"><path :d="pixPath" fill="currentColor" /></svg>
        <svg v-else-if="item.id === 'boleto'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 6v12M7 6v12M10 6v12M14 6v12M17 6v12M20 6v12" /></svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></svg>
        {{ item.label }}
      </li>
    </ul>
    <ul v-if="brands.length" class="v2-pay-brands">
      <li v-for="item in brands" :key="item.id" class="v2-pay-brand" :title="item.label">
        <img :src="item.logo" :alt="item.label" loading="lazy" />
      </li>
    </ul>
    <span v-if="note" class="v2-pay-note">{{ note }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { siPix } from "simple-icons";
import { paymentOptionsFor } from "../../../utils/paymentMethods";
import { localize } from "./useHeading";

/** Faixa "Formas de pagamento": métodos (Pix, boleto, cartão) e bandeiras aceitas. */
const props = defineProps<{ ids?: string[] | null; note?: string; align?: "center" | "left" }>();
const copy = { title: localize({ pt: "Formas de pagamento", es: "Formas de pago" }) };
const pixPath = siPix.path;
const options = computed(() => paymentOptionsFor(props.ids));
const methods = computed(() => options.value.filter(item => item.kind === "method"));
const brands = computed(() => options.value.filter(item => item.kind === "brand"));
</script>

<style scoped>
.v2-pay {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px 14px;
  max-width: 960px;
  margin: 24px auto 0;
  color: var(--v2-muted, currentColor);
  font-size: 14px;
}
.v2-pay.is-left {
  justify-content: flex-start;
  margin: 16px 0 0;
}
.v2-pay-title {
  flex-basis: 100%;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.is-left .v2-pay-title {
  text-align: left;
}
.v2-pay-methods,
.v2-pay-brands {
  display: flex;
  flex-wrap: wrap;
  justify-content: inherit;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.v2-pay-method {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--v2-card, rgba(15, 23, 19, 0.06));
  color: var(--v2-ink, inherit);
  font-weight: 600;
}
.v2-pay-method svg {
  width: 16px;
  height: 16px;
  color: var(--v2-accent-text, currentColor);
}
.v2-pay-brand {
  display: grid;
  place-items: center;
  width: 52px;
  height: 32px;
  border-radius: 8px;
  background: #fff;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 19, 0.08);
}
.v2-pay-brand img {
  max-width: 38px;
  max-height: 20px;
  object-fit: contain;
}
.v2-pay-note {
  flex-basis: 100%;
  text-align: center;
  font-weight: 600;
  color: var(--v2-ink, inherit);
}
.is-left .v2-pay-note {
  text-align: left;
}
</style>
