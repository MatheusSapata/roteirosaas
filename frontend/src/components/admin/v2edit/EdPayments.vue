<template>
  <EdGroup title="Formas de pagamento" kind="action">
    <EdToggle :model-value="enabled" label="Mostrar formas de pagamento e bandeiras" @update:model-value="setEnabled" />
    <template v-if="enabled">
      <div class="ved-field">
        <span class="ved-label">Formas</span>
        <div class="edp-chips">
          <button v-for="item in methods" :key="item.id" type="button" class="edp-chip" :class="{ on: selected.includes(item.id) }" :aria-pressed="selected.includes(item.id)" @click="toggle(item.id)">
            {{ item.label }}
          </button>
        </div>
      </div>
      <div class="ved-field">
        <span class="ved-label">Bandeiras</span>
        <div class="edp-chips">
          <button v-for="item in brands" :key="item.id" type="button" class="edp-chip is-brand" :class="{ on: selected.includes(item.id) }" :aria-pressed="selected.includes(item.id)" :title="item.label" @click="toggle(item.id)">
            <img :src="item.logo" :alt="item.label" />
          </button>
        </div>
      </div>
      <EdText :model-value="note" label="Condição" placeholder="Em até 12x sem juros no cartão" hint="Opcional. Aparece logo abaixo das bandeiras." @update:model-value="emit('patch', { paymentNote: $event })" />
    </template>
  </EdGroup>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { DEFAULT_PAYMENT_METHODS, PAYMENT_METHODS } from "../../../utils/paymentMethods";
import EdGroup from "./EdGroup.vue";
import EdText from "./EdText.vue";
import EdToggle from "./EdToggle.vue";

/** Liga a faixa de formas de pagamento da seção e escolhe o que aparece nela. */
const props = defineProps<{ value: { showPayments?: boolean; paymentMethods?: string[]; paymentNote?: string } }>();
const emit = defineEmits<{ (e: "patch", changes: Record<string, any>): void }>();

const enabled = computed(() => !!props.value.showPayments);
const selected = computed(() => props.value.paymentMethods || []);
const note = computed(() => props.value.paymentNote || "");
const methods = PAYMENT_METHODS.filter(item => item.kind === "method");
const brands = PAYMENT_METHODS.filter(item => item.kind === "brand");

const setEnabled = (on: boolean) =>
  emit("patch", on && !props.value.paymentMethods?.length ? { showPayments: on, paymentMethods: [...DEFAULT_PAYMENT_METHODS] } : { showPayments: on });
const toggle = (id: string) => {
  const next = selected.value.includes(id) ? selected.value.filter(item => item !== id) : [...selected.value, id];
  emit("patch", { paymentMethods: PAYMENT_METHODS.map(item => item.id).filter(item => next.includes(item)) });
};
</script>

<style scoped>
.edp-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.edp-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--muted, #f1f4f0);
  color: var(--muted-foreground, #5b6761);
  font-size: 13px;
  font-weight: 600;
  box-shadow: inset 0 0 0 1px transparent;
  transition: box-shadow 0.15s ease, color 0.15s ease, opacity 0.15s ease;
}
.edp-chip.on {
  color: var(--foreground, #0f1713);
  box-shadow: inset 0 0 0 1.5px var(--primary, #12b981);
}
.edp-chip.is-brand {
  width: 58px;
  padding: 0;
  border-radius: 10px;
  background: #fff;
  opacity: 0.45;
}
.edp-chip.is-brand.on {
  opacity: 1;
}
.edp-chip.is-brand img {
  max-width: 40px;
  max-height: 22px;
  object-fit: contain;
}
</style>
