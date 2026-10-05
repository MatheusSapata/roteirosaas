<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Checkout">
        <label class="ved-field">
          <span class="ved-label">Checkout da ViajeOn</span>
          <select class="ved-select" :value="modelValue.checkoutId || ''" :disabled="loading" @change="selectCheckout(($event.target as HTMLSelectElement).value)">
            <option value="">{{ loading ? "Carregando…" : "Escolher checkout…" }}</option>
            <option v-for="checkout in checkouts" :key="checkout.checkout_id" :value="checkout.checkout_id">{{ checkout.name }}</option>
          </select>
          <span class="ved-hint">Os pacotes e os preços vêm da ViajeOn.</span>
        </label>
        <p v-if="selected" class="ved-info">{{ selected.packages?.length || 0 }} {{ selected.packages?.length === 1 ? "pacote ativo" : "pacotes ativos" }} neste checkout.</p>
        <p v-if="errorMessage" class="ved-hint">{{ errorMessage }}</p>
        <button type="button" class="ved-inline-btn" :disabled="loading" @click="loadCheckouts(true)">Atualizar lista da ViajeOn</button>
      </EdGroup>
      <EdHeading :value="modelValue" type="viajeon_checkout" title-placeholder="Monte sua reserva" @patch="patch" />
      <EdGroup title="Botão">
        <EdText :model-value="readText(modelValue.buttonLabel)" label="Texto do botão" placeholder="Ir para o pagamento" @update:model-value="patch({ buttonLabel: writeText(modelValue.buttonLabel, $event) })" />
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import api from "../../../../services/api";
import type { ViajeonCheckoutSection, ViajeonCheckoutSnapshot } from "../../../../types/page";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: ViajeonCheckoutSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ViajeonCheckoutSection): void }>();
const { patch } = useDraft(props, emit);

const loading = ref(false);
const errorMessage = ref("");
const checkouts = ref<ViajeonCheckoutSnapshot[]>([]);
const selected = computed(() => checkouts.value.find(item => item.checkout_id === props.modelValue.checkoutId) || props.modelValue.checkoutSnapshot || null);

// Guarda nome e uma cópia do checkout, como o formulário antigo, para a página abrir rápido.
const selectCheckout = (id: string) => {
  const checkout = checkouts.value.find(item => item.checkout_id === id) || null;
  patch({ checkoutId: id, checkoutName: checkout?.name || "", checkoutSnapshot: checkout });
};

const loadCheckouts = async (force = false) => {
  loading.value = true;
  errorMessage.value = "";
  try {
    if (force) await api.post("/integrations/viajeon/test");
    const response = await api.get("/integrations/viajeon/checkouts");
    checkouts.value = Array.isArray(response.data?.checkouts) ? response.data.checkouts : [];
    if (!checkouts.value.length && props.modelValue.checkoutSnapshot?.checkout_id) checkouts.value = [props.modelValue.checkoutSnapshot];
    if (props.modelValue.checkoutId && !checkouts.value.some(item => item.checkout_id === props.modelValue.checkoutId)) {
      patch({ checkoutId: "", checkoutName: "", checkoutSnapshot: null });
      errorMessage.value = "O checkout escolhido não está mais ativo. Escolha outro.";
    }
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não deu para carregar os checkouts da ViajeOn.";
  } finally {
    loading.value = false;
  }
};
onMounted(() => loadCheckouts());
</script>
