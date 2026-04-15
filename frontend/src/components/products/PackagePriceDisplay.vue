<template>
  <div class="package-price" :class="{ 'package-price--compact': compact }">
    <span>A partir de</span>
    <strong>{{ formatCurrency(price) }}</strong>
    <small>/ pessoa</small>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    price: number;
    compact?: boolean;
  }>(),
  {
    compact: false,
  },
);

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
</script>

<style scoped>
.package-price {
  display: flex;
  min-width: 0;
  flex-direction: column;
  align-items: flex-end;
  text-align: right;
}

.package-price span,
.package-price small {
  display: block;
}

.package-price span {
  margin-bottom: 0.32rem;
  font-size: 0.67rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.package-price strong {
  display: block;
  font-size: clamp(2.4rem, 3.8vw, 3.15rem);
  line-height: 0.94;
  letter-spacing: -0.07em;
  color: #0f172a;
}

.package-price small {
  margin-top: 0.34rem;
  font-size: 0.76rem;
  color: #94a3b8;
}

.package-price--compact strong {
  font-size: clamp(1.55rem, 2vw, 2.05rem);
  line-height: 1;
}

.package-price--compact span {
  margin-bottom: 0.22rem;
}

@media (max-width: 720px) {
  .package-price,
  .package-price--compact {
    align-items: flex-start;
    text-align: left;
  }

  .package-price strong,
  .package-price--compact strong {
    font-size: 2.1rem;
  }
}
</style>
