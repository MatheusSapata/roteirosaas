<template>
  <div class="viajeon-form-shell">
    <aside class="viajeon-form-nav">
      <button type="button" class="viajeon-nav-item" :class="{ active: activePanel === 'content' }" @click="activePanel = 'content'">
        <span class="viajeon-nav-icon">V</span>
        <span>Conteúdo<small>Checkout e textos</small></span>
      </button>
      <button type="button" class="viajeon-nav-item" :class="{ active: activePanel === 'colors' }" @click="activePanel = 'colors'">
        <span class="viajeon-nav-icon">●</span>
        <span>Cores<small>Identidade visual</small></span>
      </button>
    </aside>

    <section class="viajeon-editor">
      <div class="section-head">
        <div>
          <h2>{{ activePanel === "content" ? "Checkout ViajeOn" : "Cores da seção" }}</h2>
          <p>{{ activePanel === "content" ? "Escolha o checkout e personalize os textos exibidos na página." : "Ajuste apenas as cores desta seção." }}</p>
        </div>
        <button type="button" class="refresh-btn" :disabled="loading" @click="loadCheckouts(true)">
          {{ loading ? "Atualizando..." : "Atualizar operações" }}
        </button>
      </div>

      <div v-if="activePanel === 'content'" class="content-area">
        <div v-if="errorMessage" class="status-box error">{{ errorMessage }}</div>
        <div v-else-if="!loading && !checkouts.length" class="status-box">
          Nenhum checkout ativo foi encontrado no Viajeon.
        </div>

        <label class="field">
          <span>Checkout/operação</span>
          <select v-model="local.checkoutId" :disabled="loading || !checkouts.length" @change="selectCheckout">
            <option value="">Selecione um checkout</option>
            <option v-for="checkout in checkouts" :key="checkout.checkout_id" :value="checkout.checkout_id">
              {{ checkout.name }} — {{ checkout.packages.length }} pacote(s)
            </option>
          </select>
        </label>

        <div class="grid-2">
          <label class="field">
            <span>Título da seção</span>
            <input v-model="local.title" placeholder="Escolha seu pacote" />
          </label>
          <label class="field">
            <span>Subtítulo</span>
            <input v-model="local.subtitle" placeholder="Selecione as quantidades" />
          </label>
        </div>

        <label class="field">
          <span>Texto do botão</span>
          <input v-model="local.buttonLabel" placeholder="Continuar para o checkout" />
        </label>

        <div v-if="selectedCheckout" class="checkout-summary">
          <strong>{{ selectedCheckout.name }}</strong>
          <span>{{ selectedCheckout.packages.length }} pacote(s) ativo(s)</span>
          <small>As imagens da operação não serão exibidas nesta seção.</small>
        </div>
      </div>

      <div v-else class="content-area colors-grid">
        <ColorField label="Fundo da seção" v-model="local.backgroundColor" />
        <ColorField label="Título e subtítulo" v-model="local.textColor" />
        <ColorField label="Destaques e controles" v-model="local.accentColor" />
        <ColorField label="Fundo dos pacotes" v-model="local.cardBackgroundColor" />
        <ColorField label="Texto dos pacotes" v-model="local.cardTextColor" />
        <ColorField label="Fundo do botão" v-model="local.buttonColor" />
        <ColorField label="Texto do botão" v-model="local.buttonTextColor" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";
import type { ViajeonCheckoutSection, ViajeonCheckoutSnapshot } from "../../types/page";

const ColorField = defineComponent({
  props: { label: { type: String, required: true }, modelValue: { type: String, default: "#000000" } },
  emits: ["update:modelValue"],
  setup(props, { emit }) {
    return () => h("label", { class: "color-field" }, [
      h("span", props.label),
      h("div", { class: "color-row" }, [
        h("input", { type: "color", value: props.modelValue, onInput: (event: Event) => emit("update:modelValue", (event.target as HTMLInputElement).value) }),
        h("input", { value: props.modelValue, onInput: (event: Event) => emit("update:modelValue", (event.target as HTMLInputElement).value) })
      ])
    ]);
  }
});

const props = defineProps<{ modelValue: ViajeonCheckoutSection }>();
const emit = defineEmits<{ (event: "update:modelValue", value: ViajeonCheckoutSection): void }>();
const activePanel = ref<"content" | "colors">("content");
const loading = ref(false);
const errorMessage = ref("");
const checkouts = ref<ViajeonCheckoutSnapshot[]>([]);
const local = reactive<ViajeonCheckoutSection>({
  ...props.modelValue,
  checkoutId: props.modelValue.checkoutId || "",
  title: props.modelValue.title || "Escolha seu pacote",
  subtitle: props.modelValue.subtitle || "Selecione as quantidades e continue para o pagamento.",
  buttonLabel: props.modelValue.buttonLabel || "Continuar para o checkout",
  backgroundColor: props.modelValue.backgroundColor || "#F8FAFC",
  textColor: props.modelValue.textColor || "#0F172A",
  accentColor: props.modelValue.accentColor || "#12B981",
  cardBackgroundColor: props.modelValue.cardBackgroundColor || "#FFFFFF",
  cardTextColor: props.modelValue.cardTextColor || "#0F172A",
  buttonColor: props.modelValue.buttonColor || "#12B981",
  buttonTextColor: props.modelValue.buttonTextColor || "#FFFFFF"
});
const selectedCheckout = computed(() => checkouts.value.find(item => item.checkout_id === local.checkoutId) || local.checkoutSnapshot || null);
let syncing = false;

const selectCheckout = () => {
  const checkout = checkouts.value.find(item => item.checkout_id === local.checkoutId) || null;
  local.checkoutName = checkout?.name || "";
  local.checkoutSnapshot = checkout;
};

const loadCheckouts = async (force = false) => {
  loading.value = true;
  errorMessage.value = "";
  try {
    if (force) await api.post("/integrations/viajeon/test");
    const response = await api.get("/integrations/viajeon/checkouts");
    checkouts.value = Array.isArray(response.data?.checkouts) ? response.data.checkouts : [];
    if (!checkouts.value.length && local.checkoutSnapshot?.checkout_id) {
      checkouts.value = [local.checkoutSnapshot];
    }
    if (local.checkoutId) {
      const checkoutStillActive = checkouts.value.some(item => item.checkout_id === local.checkoutId);
      if (checkoutStillActive) {
        selectCheckout();
      } else {
        local.checkoutId = "";
        local.checkoutName = "";
        local.checkoutSnapshot = null;
        errorMessage.value = "O checkout selecionado não está mais ativo. Escolha outra operação.";
      }
    }
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível carregar os checkouts do Viajeon.";
  } finally {
    loading.value = false;
  }
};

watch(
  () => props.modelValue,
  value => {
    syncing = true;
    Object.assign(local, value);
    nextTick(() => { syncing = false; });
  },
  { deep: true }
);
watch(
  local,
  value => {
    if (!syncing) emit("update:modelValue", { ...value } as ViajeonCheckoutSection);
  },
  { deep: true }
);
onMounted(() => loadCheckouts());
</script>

<style scoped>
.viajeon-form-shell { display:grid; grid-template-columns:190px 1fr; min-height:100%; background:var(--background); color:var(--foreground); }
.viajeon-form-nav { padding:16px 12px; border-right:1px solid var(--border); background:var(--card); display:flex; flex-direction:column; gap:8px; }
.viajeon-nav-item { display:flex; align-items:center; gap:10px; border:1px solid var(--border); border-radius:14px; padding:9px; background:var(--muted); color:var(--foreground); text-align:left; }
.viajeon-nav-item.active { background:var(--primary); border-color:var(--primary); color:var(--primary-foreground); }
.viajeon-nav-icon { width:24px; height:24px; border-radius:8px; display:grid; place-items:center; background:color-mix(in srgb, white 70%, transparent); color:#0f172a; font-size:12px; font-weight:900; }
.viajeon-nav-item > span:last-child { display:flex; flex-direction:column; font-size:14px; font-weight:800; }
.viajeon-nav-item small { font-size:11px; opacity:.62; }
.viajeon-editor { min-width:0; background:var(--background); }
.section-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding:16px; border-bottom:1px solid var(--border); }
.section-head h2 { margin:0; font-size:18px; font-weight:800; }
.section-head p { margin:5px 0 0; color:var(--muted-foreground); font-size:13px; }
.refresh-btn { border:1px solid var(--border); border-radius:10px; padding:8px 10px; color:var(--foreground); font-size:12px; font-weight:700; background:var(--card); }
.content-area { padding:16px; display:grid; gap:14px; }
.field, .color-field { display:grid; gap:6px; }
.field > span, .color-field > span { color:var(--muted-foreground); font-size:11px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
input, select { width:100%; border:1px solid var(--input); border-radius:11px; padding:9px 11px; color:var(--foreground); background:var(--card); font-size:14px; }
.grid-2, .colors-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
.checkout-summary, .status-box { display:grid; gap:4px; border:1px solid var(--border); border-radius:12px; padding:12px; background:var(--muted); font-size:13px; }
.checkout-summary span, .checkout-summary small { color:var(--muted-foreground); }
.status-box.error { border-color:color-mix(in srgb, var(--destructive) 40%, var(--border)); color:var(--destructive); }
.color-row { display:grid; grid-template-columns:46px 1fr; gap:8px; }
.color-row input[type="color"] { height:40px; padding:3px; }
@media(max-width:800px){ .viajeon-form-shell{grid-template-columns:1fr}.viajeon-form-nav{border-right:0;flex-direction:row}.viajeon-nav-item{flex:1}.grid-2,.colors-grid{grid-template-columns:1fr} }
</style>
