<template>
  <!-- Preço no padrão das artes de agência: "De" riscado, prefixo, "12x R$ 155,00" grande e o total. -->
  <div v-if="parts.has" class="pz" :class="[`pz-${align || 'left'}`]">
    <span v-if="data.oldPrice" class="pz-old">De: <s>{{ data.oldPrice }}</s></span>
    <span v-if="data.pricePrefix && !hidePrefix" class="pz-prefix">{{ data.oldPrice ? "Por:" : data.pricePrefix }}</span>
    <span class="pz-main">
      <span class="pz-lead">
        <small v-if="parts.count">{{ parts.count }}</small>
        <small>R$</small>
      </span>
      <b>{{ parts.whole }}</b>
      <small v-if="parts.cents" class="pz-cents">{{ parts.cents }}</small>
    </span>
    <span v-if="foot && !hideFoot" class="pz-foot">{{ foot }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { priceParts, type CreativeData } from "./creativeData";

const props = defineProps<{ data: CreativeData; align?: "left" | "center" | "right"; hidePrefix?: boolean; hideFoot?: boolean; cashLabel?: boolean }>();

const parts = computed(() => priceParts(props.data));
// Parcelado: mostra o total ("Total R$ 1.860 por pessoa" ou "ou à vista por R$ 1.690").
const foot = computed(() => {
  if (!parts.value.count) return props.data.priceSuffix;
  const total = props.cashLabel ? `ou à vista por ${parts.value.total}` : `Total ${parts.value.total}`;
  return [total, props.data.priceSuffix].filter(Boolean).join(" ");
});
</script>

<style scoped>
/* Tamanho pelo --pz-size (altura do número grande); cor do número em --pz-accent. */
.pz {
  --size: var(--pz-size, 150px);
  display: flex;
  flex-direction: column;
  line-height: 1;
}
.pz-center {
  align-items: center;
  text-align: center;
}
.pz-right {
  align-items: flex-end;
  text-align: right;
}
.pz-old {
  margin-bottom: calc(var(--size) * 0.08);
  font-size: calc(var(--size) * 0.22);
  font-weight: 600;
  opacity: 0.85;
}
.pz-old s {
  text-decoration-thickness: 3px;
}
.pz-prefix {
  margin-bottom: calc(var(--size) * 0.04);
  font-size: calc(var(--size) * 0.22);
  font-weight: 700;
}
.pz-main {
  display: inline-flex;
  align-items: flex-start;
  gap: calc(var(--size) * 0.06);
  color: var(--pz-accent, currentColor);
}
.pz-lead {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding-top: calc(var(--size) * 0.1);
  font-family: Sora, Inter, sans-serif;
  font-weight: 800;
  line-height: 0.95;
}
.pz-lead small {
  font-size: calc(var(--size) * 0.3);
}
.pz-main b {
  font-family: Sora, Inter, sans-serif;
  font-size: var(--size);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 0.9;
}
.pz-cents {
  padding-top: calc(var(--size) * 0.08);
  font-family: Sora, Inter, sans-serif;
  font-size: calc(var(--size) * 0.3);
  font-weight: 800;
}
.pz-foot {
  margin-top: calc(var(--size) * 0.12);
  font-size: calc(var(--size) * 0.19);
  font-weight: 600;
  opacity: 0.92;
}
</style>
