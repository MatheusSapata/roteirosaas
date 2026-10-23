<template>
  <transition name="fade">
    <div
      v-if="open"
      class="app-modal-overlay fixed inset-0 z-[70] flex items-center justify-center overflow-y-auto px-4 py-6"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
    >
      <div class="rn-modal">
        <div class="rn-head">
          <h3 :id="titleId">{{ step === "pix" ? copy.pixTitle : copy.title }}</h3>
          <button type="button" class="rn-x" :aria-label="copy.close" @click="close">×</button>
        </div>

        <div v-if="loading" class="rn-center"><span class="rn-spin" aria-hidden="true"></span>{{ copy.loading }}</div>
        <p v-else-if="loadError" class="rn-error" role="alert">{{ loadError }}</p>

        <template v-else-if="step === 'offer' && offer">
          <p class="rn-sub">{{ copy.subtitle }}</p>
          <div class="rn-offer">
            <p>{{ copy.yourPlan }}</p>
            <b>{{ offer.title }} · {{ cycleLabel }} · {{ formatBRL(offer.amount) }}</b>
            <small>{{ copy.sameContract }}</small>
          </div>

          <p class="rn-lbl">{{ copy.payWith }}</p>
          <div class="rn-opts" role="radiogroup" :aria-label="copy.payWith">
            <button type="button" role="radio" :aria-checked="method === 'pix'" class="rn-opt" :class="{ on: method === 'pix' }" @click="method = 'pix'">
              {{ copy.pixAutomatic }}
            </button>
            <button type="button" role="radio" :aria-checked="method === 'card'" class="rn-opt" :class="{ on: method === 'card' }" @click="method = 'card'">
              {{ copy.card }}
            </button>
          </div>

          <div v-if="method === 'card'" class="rn-card">
            <label>
              <span>{{ copy.holder }}</span>
              <input v-model="card.holder_name" type="text" autocomplete="cc-name" />
            </label>
            <label>
              <span>{{ copy.number }}</span>
              <input v-model="card.card_number" type="text" inputmode="numeric" autocomplete="cc-number" placeholder="0000 0000 0000 0000" />
            </label>
            <div class="rn-card-row">
              <label>
                <span>{{ copy.month }}</span>
                <input v-model="card.expiry_month" type="text" inputmode="numeric" autocomplete="cc-exp-month" placeholder="MM" />
              </label>
              <label>
                <span>{{ copy.year }}</span>
                <input v-model="card.expiry_year" type="text" inputmode="numeric" autocomplete="cc-exp-year" placeholder="AAAA" />
              </label>
              <label>
                <span>CVV</span>
                <input v-model="card.ccv" type="password" inputmode="numeric" autocomplete="cc-csc" />
              </label>
            </div>
          </div>

          <div class="rn-sum">
            <div><span>{{ todayLabel }}</span><b>{{ formatBRL(offer.amount) }}</b></div>
            <div><span>{{ copy.afterwards }}</span><b>{{ formatBRL(offer.amount) }}</b></div>
          </div>
          <p v-if="invoice" class="rn-warn">{{ copy.replaceWarning(invoiceMonth) }}</p>
          <p v-if="actionError" class="rn-error" role="alert">{{ actionError }}</p>

          <div class="rn-actions">
            <button type="button" class="rn-line" @click="close">{{ copy.cancel }}</button>
            <button type="button" class="rn-main" :disabled="submitting" @click="submit">
              {{ submitting ? copy.processing : method === "pix" ? copy.generateQr : copy.payNow }}
            </button>
          </div>
        </template>

        <template v-else-if="step === 'pix'">
          <p class="rn-sub">{{ copy.pixSubtitle }}</p>
          <div class="rn-qr">
            <img v-if="qrSrc" :src="qrSrc" :alt="copy.qrAlt" width="200" height="200" />
            <span v-else>{{ copy.qrMissing }}</span>
          </div>
          <div class="rn-copy">
            <label class="sr-only" :for="codeId">{{ copy.copyPaste }}</label>
            <input :id="codeId" type="text" :value="session?.pix_copy_paste || ''" readonly />
            <button type="button" class="rn-line" @click="copyCode">{{ copied ? copy.copied : copy.copy }}</button>
          </div>
          <ol class="rn-steps">
            <li>{{ copy.step1 }}</li>
            <li>{{ copy.step2(formatBRL(offer?.amount ?? 0)) }}</li>
            <li>{{ copy.step3 }}</li>
          </ol>
          <div class="rn-wait" role="status"><span class="rn-spin blue" aria-hidden="true"></span>{{ copy.waiting }}</div>
          <p class="rn-note">{{ copy.replacedNote }}</p>
        </template>

        <template v-else-if="step === 'done'">
          <div class="rn-done" role="status">
            <b>{{ copy.doneTitle }}</b>
            <p>{{ copy.doneText }}</p>
          </div>
          <div class="rn-actions">
            <button type="button" class="rn-main" @click="finish">{{ copy.finish }}</button>
          </div>
        </template>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import {
  createLegacyRenewalCheckoutSession,
  getLegacyRenewalCheckoutConfig,
  refreshCheckoutSession,
  startCardCheckout,
  startPixCheckout,
  type CheckoutOffer,
  type CheckoutSession
} from "../../../services/checkout";
import { formatBRL, invoiceMonthName, type BillingInvoice } from "../../../services/billing";
import { useAuthStore } from "../../../store/useAuthStore";
import { createAdminLocalizer } from "../../../utils/adminI18n";

const props = defineProps<{
  open: boolean;
  /** Fatura em aberto que esta renovação substitui (aparece no resumo e no aviso). */
  invoice?: BillingInvoice | null;
  initialMethod?: "pix" | "card";
}>();
const emit = defineEmits<{ (e: "close"): void; (e: "paid"): void }>();

const t = createAdminLocalizer();
const auth = useAuthStore();

const copy = {
  title: t({ pt: "Renovar assinatura", es: "Renovar suscripción" }),
  pixTitle: t({ pt: "Autorize o Pix Automático", es: "Autoriza el Pix Automático" }),
  close: t({ pt: "Fechar", es: "Cerrar" }),
  loading: t({ pt: "Carregando a sua renovação...", es: "Cargando tu renovación..." }),
  subtitle: t({
    pt: "Você continua no seu plano, no mesmo valor. Escolha só como quer pagar.",
    es: "Sigues en tu plan, con el mismo valor. Elige solo cómo quieres pagar."
  }),
  yourPlan: t({ pt: "Seu plano", es: "Tu plan" }),
  sameContract: t({ pt: "Mesmo plano e valor do seu contrato atual", es: "Mismo plan y valor de tu contrato actual" }),
  payWith: t({ pt: "Forma de pagamento", es: "Forma de pago" }),
  pixAutomatic: t({ pt: "Pix Automático", es: "Pix Automático" }),
  card: t({ pt: "Cartão", es: "Tarjeta" }),
  holder: t({ pt: "Nome impresso", es: "Nombre en la tarjeta" }),
  number: t({ pt: "Número do cartão", es: "Número de la tarjeta" }),
  month: t({ pt: "Mês", es: "Mes" }),
  year: t({ pt: "Ano", es: "Año" }),
  afterwards: t({ pt: "Depois, a cada renovação", es: "Después, en cada renovación" }),
  replaceWarning: (month: string) =>
    t({
      pt: `A fatura${month ? ` de ${month}` : ""} em aberto será cancelada no Asaas e trocada por este pagamento, para você não pagar duas vezes.`,
      es: `La factura${month ? ` de ${month}` : ""} pendiente se cancelará en Asaas y se reemplazará por este pago, para que no pagues dos veces.`
    }),
  cancel: t({ pt: "Cancelar", es: "Cancelar" }),
  generateQr: t({ pt: "Gerar QR Code", es: "Generar código QR" }),
  payNow: t({ pt: "Pagar e renovar", es: "Pagar y renovar" }),
  processing: t({ pt: "Processando...", es: "Procesando..." }),
  pixSubtitle: t({
    pt: "Um QR Code só: paga a fatura de hoje e autoriza os próximos meses.",
    es: "Un solo código QR: paga la factura de hoy y autoriza los próximos meses."
  }),
  qrAlt: t({ pt: "QR Code do Pix Automático", es: "Código QR del Pix Automático" }),
  qrMissing: t({ pt: "QR Code indisponível. Use o código abaixo.", es: "Código QR no disponible. Usa el código de abajo." }),
  copyPaste: t({ pt: "Código Pix copia e cola", es: "Código Pix copia y pega" }),
  copy: t({ pt: "Copiar", es: "Copiar" }),
  copied: t({ pt: "Copiado", es: "Copiado" }),
  step1: t({ pt: "Abra o app do banco e leia o QR Code (ou cole o código).", es: "Abre la app del banco y lee el código QR (o pega el código)." }),
  step2: (amount: string) =>
    t({ pt: `Confirme o Pix Automático de ${amount} por ciclo.`, es: `Confirma el Pix Automático de ${amount} por ciclo.` }),
  step3: t({ pt: "Pronto: a edição volta na hora.", es: "Listo: la edición vuelve al instante." }),
  waiting: t({ pt: "Aguardando a autorização no banco…", es: "Esperando la autorización en el banco…" }),
  replacedNote: t({
    pt: "Quando esta autorização ficar ativa, a anterior é cancelada.",
    es: "Cuando esta autorización quede activa, la anterior se cancela."
  }),
  doneTitle: t({ pt: "Assinatura renovada", es: "Suscripción renovada" }),
  doneText: t({ pt: "Pagamento recebido. Suas páginas e a edição já estão liberadas.", es: "Pago recibido. Tus páginas y la edición ya están habilitadas." }),
  finish: t({ pt: "Continuar", es: "Continuar" }),
  required: t({ pt: "Preencha todos os dados do cartão.", es: "Completa todos los datos de la tarjeta." }),
  genericError: t({ pt: "Não foi possível renovar agora. Tente de novo em instantes.", es: "No fue posible renovar ahora. Inténtalo de nuevo en unos instantes." }),
  cardRefused: t({ pt: "O cartão não foi aprovado. Confira os dados ou use outro cartão.", es: "La tarjeta no fue aprobada. Revisa los datos o usa otra tarjeta." })
};

const uid = Math.random().toString(36).slice(2, 8);
const titleId = `rn-title-${uid}`;
const codeId = `rn-code-${uid}`;

const step = ref<"offer" | "pix" | "done">("offer");
const method = ref<"pix" | "card">("pix");
const loading = ref(false);
const loadError = ref("");
const actionError = ref("");
const submitting = ref(false);
const copied = ref(false);
const offer = ref<CheckoutOffer | null>(null);
const session = ref<CheckoutSession | null>(null);
const card = reactive({ holder_name: "", card_number: "", expiry_month: "", expiry_year: "", ccv: "" });
let pollTimer: ReturnType<typeof setInterval> | null = null;

const invoiceMonth = computed(() => invoiceMonthName(props.invoice?.due_date));
const cycleLabel = computed(() => (offer.value?.billing_cycle === "annual" ? t({ pt: "Anual", es: "Anual" }) : t({ pt: "Mensal", es: "Mensual" })));
const todayLabel = computed(() =>
  props.invoice
    ? t({ pt: `Hoje (fatura${invoiceMonth.value ? ` de ${invoiceMonth.value}` : ""})`, es: `Hoy (factura${invoiceMonth.value ? ` de ${invoiceMonth.value}` : ""})` })
    : t({ pt: "Hoje", es: "Hoy" })
);
const qrSrc = computed(() => {
  const raw = String(session.value?.pix_qr_code_base64 || "").trim();
  if (raw) return raw.startsWith("data:image") ? raw : `data:image/png;base64,${raw}`;
  const payload = String(session.value?.pix_copy_paste || "").trim();
  return payload ? `https://api.qrserver.com/v1/create-qr-code/?size=320x320&data=${encodeURIComponent(payload)}` : "";
});

const apiDetail = (err: any, fallback: string) => {
  const detail = err?.response?.data?.detail;
  return typeof detail === "string" && detail ? detail : fallback;
};

const stopPolling = () => {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
};

const markPaid = async () => {
  stopPolling();
  step.value = "done";
  try {
    await auth.fetchProfile();
  } catch (err) {
    console.error("Erro ao recarregar o usuário depois da renovação", err);
  }
  emit("paid");
};

const startPolling = () => {
  stopPolling();
  pollTimer = setInterval(async () => {
    if (!session.value) return;
    try {
      session.value = await refreshCheckoutSession(session.value.token);
      if (session.value.status === "paid") await markPaid();
    } catch (err) {
      console.error("Erro ao conferir a renovação", err);
    }
  }, 5000);
};

const reset = () => {
  stopPolling();
  step.value = "offer";
  method.value = props.initialMethod ?? "pix";
  loadError.value = "";
  actionError.value = "";
  session.value = null;
  copied.value = false;
  Object.assign(card, { holder_name: "", card_number: "", expiry_month: "", expiry_year: "", ccv: "" });
};

const load = async () => {
  reset();
  loading.value = true;
  try {
    offer.value = (await getLegacyRenewalCheckoutConfig()).offer;
  } catch (err) {
    console.error(err);
    offer.value = null;
    loadError.value = apiDetail(err, copy.genericError);
  } finally {
    loading.value = false;
  }
};

const submit = async () => {
  actionError.value = "";
  if (method.value === "card" && !(card.holder_name && card.card_number && card.expiry_month && card.expiry_year && card.ccv)) {
    actionError.value = copy.required;
    return;
  }
  submitting.value = true;
  try {
    // Reaproveita a sessão se a pessoa voltou do passo do QR Code.
    session.value = session.value ?? (await createLegacyRenewalCheckoutSession());
    if (method.value === "pix") {
      session.value = await startPixCheckout(session.value.token);
      step.value = "pix";
      startPolling();
      return;
    }
    session.value = await startCardCheckout(session.value.token, {
      token: session.value.token,
      holder_name: card.holder_name,
      card_number: card.card_number.replace(/\s+/g, ""),
      expiry_month: card.expiry_month,
      expiry_year: card.expiry_year,
      ccv: card.ccv,
      installment_count: 1
    });
    if (session.value.status === "paid") {
      await markPaid();
    } else if (session.value.status === "failed" || session.value.status === "refused") {
      session.value = null;
      actionError.value = copy.cardRefused;
    } else {
      step.value = "pix";
      startPolling();
    }
  } catch (err) {
    console.error(err);
    actionError.value = apiDetail(err, copy.genericError);
  } finally {
    submitting.value = false;
  }
};

const copyCode = async () => {
  const code = session.value?.pix_copy_paste;
  if (!code) return;
  try {
    await navigator.clipboard.writeText(code);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch (err) {
    console.error(err);
  }
};

const close = () => {
  stopPolling();
  emit("close");
};

const finish = () => {
  stopPolling();
  emit("close");
};

watch(
  () => props.open,
  isOpen => {
    if (isOpen) void load();
    else stopPolling();
  },
  { immediate: true }
);

onBeforeUnmount(stopPolling);
</script>

<style scoped>
.rn-modal { width: 100%; max-width: 460px; box-sizing: border-box; border-radius: 24px; background: var(--card, #fff); padding: 24px; color: var(--foreground, #1e293b); box-shadow: 0 25px 50px -12px rgba(6, 78, 59, 0.2); }
.rn-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.rn-head h3 { font-size: 18px; line-height: 28px; font-weight: 600; }
.rn-x { border: 0; background: none; font-size: 24px; line-height: 1; color: var(--muted-foreground, #94a3b8); min-width: 44px; min-height: 44px; }
.rn-sub { margin-top: 8px; font-size: 14px; line-height: 20px; color: var(--muted-foreground, #475569); }
.rn-center { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 32px 0; font-size: 14px; color: var(--muted-foreground, #64748b); }
.rn-offer { margin-top: 16px; border-radius: 14px; background: var(--muted, #f1f5f9); padding: 12px 14px; }
.rn-offer p { font-size: 12px; color: var(--muted-foreground, #64748b); }
.rn-offer b { display: block; margin-top: 2px; font-size: 15px; font-weight: 600; }
.rn-offer small { display: block; margin-top: 4px; font-size: 12px; color: var(--muted-foreground, #64748b); }
.rn-lbl { margin-top: 16px; font-size: 12px; font-weight: 600; color: var(--muted-foreground, #64748b); }
.rn-opts { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px; }
.rn-opt { min-height: 44px; border-radius: 999px; border: 1px solid var(--border, #e2e8f0); background: var(--card, #fff); padding: 8px 16px; font-size: 14px; font-weight: 600; color: var(--muted-foreground, #475569); }
.rn-opt.on { border-color: #10b981; background: #ecfdf5; color: #047857; }
.rn-card { margin-top: 14px; display: flex; flex-direction: column; gap: 10px; }
.rn-card label { display: flex; flex-direction: column; gap: 4px; min-width: 0; flex: 1; }
.rn-card label span { font-size: 12px; font-weight: 600; color: var(--muted-foreground, #64748b); }
.rn-card input { height: 44px; box-sizing: border-box; border: 1px solid var(--border, #e2e8f0); border-radius: 10px; padding: 0 12px; font-size: 14px; background: var(--background, #fff); color: var(--foreground, #1e293b); }
.rn-card-row { display: flex; gap: 10px; }
.rn-sum { margin-top: 16px; display: flex; flex-direction: column; gap: 8px; font-size: 13.5px; }
.rn-sum div { display: flex; justify-content: space-between; gap: 12px; }
.rn-sum span { color: var(--muted-foreground, #64748b); }
.rn-sum b { font-weight: 600; font-variant-numeric: tabular-nums; }
.rn-warn { margin-top: 16px; border-radius: 12px; background: var(--status-warning, #fff6dd); color: #8a5a12; padding: 10px 12px; font-size: 12.5px; line-height: 18px; }
.rn-error { margin-top: 12px; border-radius: 12px; background: var(--status-danger, #feecec); color: var(--status-danger-foreground, #b42318); padding: 10px 12px; font-size: 13px; }
.rn-actions { margin-top: 20px; display: flex; justify-content: flex-end; gap: 8px; }
.rn-line { min-height: 44px; border-radius: 999px; border: 1px solid var(--border, #e2e8f0); background: var(--card, #fff); padding: 0 16px; font-size: 14px; font-weight: 600; color: var(--muted-foreground, #475569); }
.rn-main { min-height: 44px; border: 0; border-radius: 999px; background: var(--primary, #12b981); padding: 0 18px; font-size: 14px; font-weight: 600; color: #fff; }
.rn-main:disabled { opacity: 0.6; cursor: not-allowed; }
.rn-qr { margin-top: 16px; display: grid; place-items: center; min-height: 200px; border-radius: 16px; border: 1px dashed var(--border, #cbd5e1); background: var(--muted, #f8fafc); font-size: 13px; color: var(--muted-foreground, #64748b); padding: 12px; text-align: center; }
.rn-qr img { width: 200px; height: 200px; object-fit: contain; }
.rn-copy { margin-top: 12px; display: flex; gap: 8px; }
.rn-copy input { flex: 1; min-width: 0; height: 44px; box-sizing: border-box; border: 1px solid var(--border, #e2e8f0); border-radius: 8px; padding: 0 12px; font: 13px ui-monospace, Menlo, monospace; color: var(--muted-foreground, #475569); background: var(--background, #fff); }
.rn-steps { margin-top: 14px; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; font-size: 13px; line-height: 18px; color: var(--muted-foreground, #475569); }
.rn-wait { margin-top: 14px; display: flex; align-items: center; gap: 10px; border-radius: 12px; background: var(--status-info, #eaf4ff); color: var(--status-info-foreground, #2563eb); padding: 10px 12px; font-size: 13px; font-weight: 600; }
.rn-note { margin-top: 12px; font-size: 12.5px; line-height: 18px; color: var(--muted-foreground, #64748b); }
.rn-done { margin-top: 16px; border-radius: 14px; background: var(--status-success, #e8fbf3); color: var(--status-success-foreground, #0b7a5b); padding: 14px; }
.rn-done b { display: block; font-size: 15px; }
.rn-done p { margin-top: 4px; font-size: 13px; }
.rn-spin { width: 14px; height: 14px; flex-shrink: 0; border-radius: 999px; border: 3px solid var(--border, #e2e8f0); border-top-color: var(--primary, #12b981); animation: rn-spin 0.9s linear infinite; }
.rn-spin.blue { border-color: #cfe0f7; border-top-color: #2563eb; }
@keyframes rn-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .rn-spin { animation-duration: 3s; } }
@media (max-width: 480px) { .rn-card-row { flex-direction: column; } }
</style>
