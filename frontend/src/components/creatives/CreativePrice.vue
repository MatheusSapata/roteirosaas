<template>
  <!--
    Preço das artes, todo em "em": o tamanho vem do FitText em volta (1em = altura do número grande).
    stack: rótulos em cima, "12x / R$" empilhados ao lado do número, total embaixo (Porto de Galinhas).
    side:  coluna à esquerda com De/Por e "12x R$", número grande à direita (CVC Porto Seguro, Azul).
    total: só o valor cheio, com "De ... por apenas" ao lado (Black Friday).
  -->
  <div v-if="parts.has" class="pz" :class="[`pz-${variant}`, `pz-${align}`]">
    <template v-if="variant === 'stack'">
      <span v-if="data.oldPrice" class="pz-old">De <s>{{ data.oldPrice }}</s> por</span>
      <span v-else-if="prefix" class="pz-prefix">{{ prefix }}</span>
      <span class="pz-main">
        <span class="pz-lead">
          <small v-if="parts.count">{{ parts.count }}</small>
          <small>R$</small>
        </span>
        <b>{{ parts.whole }}</b>
        <small v-if="parts.cents" class="pz-cents">{{ parts.cents }}</small>
      </span>
    </template>

    <template v-else-if="variant === 'side'">
      <span class="pz-main">
        <span class="pz-col">
          <span v-if="data.oldPrice" class="pz-old">De: <s>{{ data.oldPrice }}</s></span>
          <span v-if="data.oldPrice || prefix" class="pz-prefix">{{ data.oldPrice ? "Por:" : prefix }}</span>
          <span class="pz-unit">{{ [parts.count, "R$"].filter(Boolean).join(" ") }}</span>
        </span>
        <b>{{ parts.whole }}</b>
        <small v-if="parts.cents" class="pz-cents">{{ parts.cents }}</small>
      </span>
    </template>

    <template v-else>
      <span class="pz-main">
        <span v-if="data.oldPrice" class="pz-col pz-col-was">
          <s>De {{ data.oldPrice }}</s>
          <span>por apenas</span>
        </span>
        <b>{{ parts.total.replace(/\s/g, "") }}</b>
      </span>
    </template>

    <span v-if="foot && !hideFoot" class="pz-foot">{{ foot }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { priceParts, type CreativeData } from "./creativeData";

const props = withDefaults(
  defineProps<{
    data: CreativeData;
    variant?: "stack" | "side" | "total";
    align?: "left" | "center" | "right";
    hideFoot?: boolean;
    /** "ou à vista por R$ X" em vez de "Total R$ X". */
    cashLabel?: boolean;
  }>(),
  { variant: "stack", align: "left", hideFoot: false, cashLabel: false }
);

const parts = computed(() => priceParts(props.data));
const prefix = computed(() => props.data.pricePrefix.trim());
const foot = computed(() => {
  if (props.variant === "total") return parts.value.installmentText ? `${parts.value.installmentText} sem juros` : props.data.priceSuffix;
  if (!parts.value.count) return props.data.priceSuffix;
  const total = props.cashLabel ? `ou à vista por ${parts.value.total}` : `Total de ${parts.value.total}`;
  return [total, props.data.priceSuffix].filter(Boolean).join(" ");
});
</script>

<style scoped>
/* Bloco (não inline) para não ficar preso à linha de base do texto em volta. */
.pz {
  display: flex;
  width: fit-content;
  max-width: 100%;
  flex-direction: column;
  line-height: 1;
  white-space: nowrap;
}
.pz-center {
  align-items: center;
  margin-inline: auto;
  text-align: center;
}
.pz-right {
  align-items: flex-end;
  margin-left: auto;
  text-align: right;
}
.pz-old,
.pz-prefix {
  font-size: 0.2em;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.pz-old s {
  text-decoration-thickness: 0.12em;
}
.pz-stack .pz-old,
.pz-stack .pz-prefix {
  margin-bottom: 0.12em;
}
.pz-main {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.06em;
  color: var(--pz-accent, currentColor);
}
.pz-main b {
  font-family: var(--pz-font, "Montserrat", sans-serif);
  font-size: 1em;
  font-weight: 900;
  letter-spacing: -0.045em;
  line-height: 0.82;
}
.pz-lead {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.04em;
  padding-top: 0.06em;
  font-family: var(--pz-font, "Montserrat", sans-serif);
  font-weight: 900;
  line-height: 0.95;
}
.pz-lead small {
  font-size: 0.3em;
}
.pz-cents {
  padding-top: 0.04em;
  font-family: var(--pz-font, "Montserrat", sans-serif);
  font-size: 0.3em;
  font-weight: 900;
}
/* Coluna à esquerda do número (De/Por e "12x R$"). */
.pz-col {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-end;
  align-self: stretch;
  gap: 0.05em;
  margin-right: 0.06em;
  padding-bottom: 0.04em;
  color: var(--pz-label, currentColor);
  text-align: left;
}
.pz-col .pz-old,
.pz-col .pz-prefix {
  font-size: 0.17em;
}
.pz-unit {
  font-family: var(--pz-font, "Montserrat", sans-serif);
  font-size: 0.26em;
  font-weight: 900;
}
.pz-col-was {
  justify-content: center;
  gap: 0.08em;
  font-size: 0.22em;
  font-weight: 800;
  text-transform: uppercase;
}
.pz-col-was s {
  text-decoration-color: var(--pz-accent, currentColor);
  text-decoration-thickness: 0.12em;
}
.pz-total .pz-main {
  align-items: center;
  gap: 0.18em;
}
.pz-foot {
  margin-top: 0.14em;
  font-size: 0.16em;
  font-weight: 600;
  letter-spacing: 0.01em;
  opacity: 0.92;
}
</style>
