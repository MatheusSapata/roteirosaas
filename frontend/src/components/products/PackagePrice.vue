<template>
  <div class="package-price" :class="{ 'package-price--compact': compact, 'package-price--muted': muted }">
    <p class="package-price__eyebrow">{{ eyebrow }}</p>
    <div class="package-price__value">
      <span>{{ formattedPrice }}</span>
    </div>
    <p v-if="suffix" class="package-price__suffix">{{ suffix }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    value: number;
    compact?: boolean;
    muted?: boolean;
    eyebrow?: string;
    suffix?: string;
  }>(),
  {
    compact: false,
    muted: false,
    eyebrow: "A partir de",
    suffix: "/ pessoa",
  },
);

const formattedPrice = computed(() =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(props.value),
);
</script>

<style scoped>
.package-price {
  display: flex;
  min-width: 0;
  flex-direction: column;
  align-items: flex-end;
  text-align: right;
}

.package-price__eyebrow,
.package-price__suffix {
  margin: 0;
}

.package-price__eyebrow {
  margin-bottom: 0.28rem;
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.package-price__value {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  gap: 0.25rem;
}

.package-price__value span {
  font-size: 1.34rem;
  line-height: 1;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: #020617;
}

.package-price__suffix {
  margin-top: 0.22rem;
  font-size: 0.76rem;
  color: #94a3b8;
}

.package-price--compact .package-price__value span {
  font-size: clamp(1.92rem, 2.25vw, 2.45rem);
}

.package-price--muted .package-price__value span {
  font-size: 1.02rem;
  letter-spacing: -0.03em;
}

.package-price--muted .package-price__eyebrow {
  color: #cbd5e1;
}

.package-price--muted .package-price__suffix {
  font-size: 0.74rem;
}

@media (max-width: 900px) {
  .package-price,
  .package-price--compact,
  .package-price--muted {
    align-items: flex-start;
    text-align: left;
  }

  .package-price__value {
    justify-content: flex-start;
  }
}
</style>
