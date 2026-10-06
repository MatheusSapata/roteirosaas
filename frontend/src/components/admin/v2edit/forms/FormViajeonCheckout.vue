<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="viajeon_checkout" title-placeholder="Monte sua reserva" @patch="patch" />
      <EdGroup title="Checkout">
        <div v-if="connected === false" class="ved-info ved-warn">
          <b>A ViajeOn está desconectada.</b>
          {{ modelValue.checkoutSnapshot?.packages?.length
            ? "A página segue mostrando a última cópia dos pacotes. Para trocar o checkout ou atualizar os preços, conecte de novo."
            : "Conecte sua conta para escolher um checkout e mostrar os pacotes nesta seção." }}
          <button type="button" class="ved-inline-btn" @click="goIntegration">Conectar ViajeOn</button>
        </div>
        <label v-if="connected !== false" class="ved-field">
          <span class="ved-label">Checkout da ViajeOn</span>
          <select class="ved-select" :value="modelValue.checkoutId || ''" :disabled="loading" @change="selectCheckout(($event.target as HTMLSelectElement).value)">
            <option value="">{{ loading ? "Carregando…" : "Escolher checkout…" }}</option>
            <option v-for="checkout in checkouts" :key="checkout.checkout_id" :value="checkout.checkout_id">{{ checkout.name }}</option>
          </select>
          <span class="ved-hint">Os pacotes e os preços vêm da ViajeOn.</span>
        </label>
        <p v-if="selected" class="ved-info">{{ selected.packages?.length || 0 }} {{ selected.packages?.length === 1 ? "pacote ativo" : "pacotes ativos" }} neste checkout.</p>
        <p v-if="errorMessage && connected !== false" class="ved-hint">{{ errorMessage }}</p>
        <button v-if="connected !== false" type="button" class="ved-inline-btn" :disabled="loading" @click="loadCheckouts(true)">Atualizar lista da ViajeOn</button>
      </EdGroup>
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
import { useRouter } from "vue-router";
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

const router = useRouter();
const loading = ref(false);
// null enquanto consulta; false quando a integração não está conectada.
const connected = ref<boolean | null>(null);
const goIntegration = () => router.push({ name: "integrations-viajeon" });
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
onMounted(async () => {
  try {
    const response = await api.get("/integrations/viajeon");
    connected.value = response.data?.connected === true;
  } catch {
    connected.value = null;
  }
  if (connected.value !== false) await loadCheckouts();
});
</script>
