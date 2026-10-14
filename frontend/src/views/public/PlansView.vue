<template>
  <div class="plans-view">
    <div class="pv-wrap">
      <header class="pv-head">
        <h1 class="pv-title">{{ t(copy.title) }}</h1>
        <p class="pv-sub">{{ t(copy.subtitle) }}</p>
      </header>

      <div v-if="trialBlocked" class="pv-alert is-danger">
        <p class="pv-alert-title">{{ t(copy.trialBlockedTitle) }}</p>
        <p>{{ t(copy.trialBlockedText) }}</p>
      </div>
      <div v-else-if="trialPlanActive" class="pv-alert is-success">
        <p class="pv-alert-title">{{ t(copy.trialActiveTitle) }}</p>
        <p>
          {{ t(copy.trialActiveText) }}
          <span v-if="trialEndsAtText">{{ t(copy.until) }} {{ trialEndsAtText }}.</span>
        </p>
      </div>

      <!-- Downgrade agendado antes do plano único (clientes dos planos antigos). -->
      <div v-if="billingInfo?.scheduled_downgrade_plan" class="pv-alert is-warning pv-alert-row">
        <p>
          Downgrade para <strong>{{ getPlanLabel(billingInfo.scheduled_downgrade_plan) }}</strong> agendado para o fim do ciclo.
        </p>
        <button
          type="button"
          class="pv-btn-ghost"
          :disabled="loadingKey === 'cancel-scheduled-downgrade'"
          @click="cancelScheduledDowngrade"
        >
          {{ loadingKey === "cancel-scheduled-downgrade" ? "Cancelando..." : "Cancelar downgrade" }}
        </button>
      </div>

      <!-- Plano antigo (Profissional ou Agência): continua valendo; aqui ele vê o que ganha assinando. -->
      <div v-if="isLegacyPlan" class="pv-alert is-info">
        <p class="pv-alert-title">{{ t(copy.legacyTitle) }} {{ getPlanLabel(activePlan) }}</p>
        <p>{{ t(copy.legacyText) }}</p>
      </div>

      <section id="planos" class="pv-offer">
        <div class="pv-incl">
          <p class="pv-incl-title">{{ t(copy.includedTitle) }}</p>
          <ul>
            <li v-for="item in included" :key="item"><Check :size="15" aria-hidden="true" />{{ item }}</li>
          </ul>
          <p class="pv-incl-foot">{{ t(copy.sameSubscription) }}</p>
        </div>

        <div class="pv-price-box" :class="{ 'is-current': isCurrentCycle }">
          <span v-if="isScaleActive" class="pv-current">
            <span class="pv-dot" aria-hidden="true"></span>{{ t(copy.yourSubscription) }} · {{ cycleLabel(currentCycle) }}
          </span>
          <div v-if="salesPlan.monthly && salesPlan.annual" class="pv-cycle" role="tablist" :aria-label="t(copy.howToPay)">
            <button type="button" role="tab" :aria-selected="cycle === 'monthly'" :class="{ on: cycle === 'monthly' }" @click="cycle = 'monthly'">
              {{ cycleLabel("monthly") }}
            </button>
            <button type="button" role="tab" :aria-selected="cycle === 'annual'" :class="{ on: cycle === 'annual' }" @click="cycle = 'annual'">
              {{ cycleLabel("annual") }}<span v-if="math && math.savingsPercent > 0" class="pv-off">-{{ math.savingsPercent }}%</span>
            </button>
          </div>

          <template v-if="currentOffer">
            <p v-if="cycle === 'annual' && math && math.savings > 0" class="pv-anchor">
              {{ t(copy.from) }} <s>{{ formatBRL(math.twelveMonths) }}</s> {{ t(copy.for) }}
            </p>
            <p v-else-if="promoAmount" class="pv-anchor">
              {{ t(copy.from) }} <s>{{ formatBRL(currentOffer.amount) }}</s> {{ t(copy.for) }}
            </p>
            <!-- Anual parcelado: a parcela em destaque e o valor à vista embaixo. -->
            <div v-if="annualInstallment" class="pv-price">
              <span class="cur">{{ annualInstallment.count }}x de R$</span><span class="val">{{ formatBRL(annualInstallment.value, { cents: "always" }).replace(/^R\$\s*/, "") }}</span>
            </div>
            <div v-else class="pv-price">
              <span class="cur">R$</span><span class="val">{{ priceNumber(promoAmount || currentOffer.amount) }}</span>
              <span class="per">{{ promoAmount ? t(copy.firstMonth) : cycle === "annual" ? t(copy.perYear) : t(copy.perMonth) }}</span>
            </div>
            <p v-if="annualInstallment" class="pv-eq">
              {{ t(copy.or) }} <b>{{ formatBRL(currentOffer.amount) }} {{ t(copy.upfront) }}</b>
            </p>
            <p v-else-if="cycle === 'annual' && math" class="pv-eq">
              {{ t(copy.equals) }} <b>{{ formatBRL(math.perMonth, { cents: "always" }) }} {{ t(copy.aMonth) }}</b>
            </p>
            <p v-else-if="promoAmount" class="pv-eq">
              {{ t(copy.thenMonthly) }} <b>{{ formatBRL(currentOffer.amount) }}{{ t(copy.perMonth) }}</b>. {{ t(copy.noLockIn) }}
            </p>
            <p v-else class="pv-eq">{{ t(copy.monthlyNote) }}</p>
            <p v-if="cycle === 'annual' && math && math.savings > 0" class="pv-save">
              {{ t(copy.save) }} {{ formatBRL(math.savings) }} · {{ t(copy.lessThan) }} {{ math.lessThanMonths }} {{ t(copy.monthsOfMonthly) }}
            </p>

            <button type="button" class="pv-btn" :disabled="ctaDisabled || loadingKey === cycle" @click="goToCheckout">
              <span>{{ loadingKey === cycle ? t(copy.redirecting) : ctaLabel }}</span>
              <ArrowRight v-if="!ctaDisabled && loadingKey !== cycle" :size="18" aria-hidden="true" />
            </button>
            <p v-if="ctaHint" class="pv-hint">{{ ctaHint }}</p>
          </template>
          <p v-else-if="!salesPlanLoading" class="pv-eq">{{ t(copy.unavailable) }}</p>

          <p class="pv-guarantee"><ShieldCheck :size="15" aria-hidden="true" />{{ t(copy.guarantee) }}</p>
          <p v-if="errorMessage" class="pv-msg is-error">{{ errorMessage }}</p>
          <p v-if="successMessage" class="pv-msg is-success">{{ successMessage }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowRight, Check, ShieldCheck } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
import api from "../../services/api";
import { getPublicSalesPlan, type SalesPlan } from "../../services/checkout";
import { useAuthStore } from "../../store/useAuthStore";
import { getPlanLabel } from "../../utils/planLabels";
import { formatBRL, salesPlanMath } from "../../utils/salesPlan";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import type { LocalizedString, SupportedLanguage } from "../../utils/i18n";

/**
 * Assinatura do Roteiro Online dentro do painel: plano único (interno: Escala), pago por mês
 * ou por ano. Os valores e as ofertas vêm de Admin Master › Ofertas e checkout (as mesmas da
 * página de vendas). Clientes dos planos antigos continuam neles até assinarem.
 */
const currentLanguage = getCurrentLanguage();
const t = createLocalizer(currentLanguage);
const localeByLanguage: Record<SupportedLanguage, string> = { pt: "pt-BR", es: "es-ES" };
const dateLocale = localeByLanguage[currentLanguage] || "pt-BR";

const L = (pt: string, es: string): LocalizedString => ({ pt, es });
const copy = {
  title: L("Sua assinatura do Roteiro Online", "Tu suscripción de Roteiro Online"),
  subtitle: L("Um plano único com tudo incluso. Escolha pagar por mês ou por ano.", "Un plan único con todo incluido. Elige pagar por mes o por año."),
  trialBlockedTitle: L("Trial encerrado", "Trial finalizado"),
  trialBlockedText: L(
    "Seu período de teste terminou e o painel foi bloqueado. Assine para liberar suas páginas e voltar a publicar.",
    "Tu período de prueba terminó y el panel fue bloqueado. Suscríbete para liberar tus páginas y volver a publicar."
  ),
  trialActiveTitle: L("Trial ativo", "Trial activo"),
  trialActiveText: L("Você está no período de teste com até 3 páginas, seções e pixels ilimitados", "Estás en el período de prueba con hasta 3 páginas, secciones y píxeles ilimitados"),
  until: L("até", "hasta"),
  legacyTitle: L("Seu plano atual:", "Tu plan actual:"),
  legacyText: L(
    "Ele continua valendo do jeito que está. Assinando, você passa a ter roteiros ilimitados, Módulo Leads, domínio próprio e notificações inteligentes.",
    "Sigue vigente tal como está. Al suscribirte, tienes itinerarios ilimitados, Módulo Leads, dominio propio y notificaciones inteligentes."
  ),
  includedTitle: L("O que vem na assinatura", "Qué incluye la suscripción"),
  sameSubscription: L("Mensal ou anual, é a mesma assinatura: muda só a forma de pagar.", "Mensual o anual, es la misma suscripción: cambia solo la forma de pago."),
  yourSubscription: L("Sua assinatura", "Tu suscripción"),
  howToPay: L("Forma de pagamento", "Forma de pago"),
  monthly: L("Mensal", "Mensual"),
  annual: L("Anual", "Anual"),
  from: L("de", "de"),
  for: L("por", "por"),
  perYear: L("/ano", "/año"),
  perMonth: L("/mês", "/mes"),
  equals: L("equivale a", "equivale a"),
  aMonth: L("por mês", "por mes"),
  monthlyNote: L("Renova todo mês. Sem fidelidade.", "Se renueva cada mes. Sin permanencia."),
  or: L("ou", "o"),
  upfront: L("à vista", "al contado"),
  firstMonth: L("no 1º mês", "el 1er mes"),
  thenMonthly: L("Depois,", "Después,"),
  noLockIn: L("Sem fidelidade.", "Sin permanencia."),
  save: L("Economize", "Ahorra"),
  lessThan: L("1 ano por menos de", "1 año por menos de"),
  monthsOfMonthly: L("meses do mensal", "meses del mensual"),
  subscribe: L("Assinar agora", "Suscribirme ahora"),
  renew: L("Renovar assinatura", "Renovar suscripción"),
  reactivate: L("Reativar assinatura", "Reactivar suscripción"),
  switchToAnnual: L("Mudar para o anual", "Cambiar al anual"),
  alreadyAnnual: L("Você já está no anual", "Ya estás en el anual"),
  alreadyAnnualHint: L("A assinatura anual já inclui tudo. Ela renova no fim do ciclo.", "La suscripción anual ya incluye todo. Se renueva al final del ciclo."),
  redirecting: L("Redirecionando...", "Redirigiendo..."),
  unavailable: L("A assinatura não está disponível no momento. Fale com o suporte.", "La suscripción no está disponible por el momento. Habla con soporte."),
  guarantee: L("7 dias de garantia: não gostou, devolvemos 100%.", "7 días de garantía: si no te gusta, devolvemos el 100%."),
  checkoutError: L("Não foi possível iniciar o checkout. Tente novamente.", "No fue posible iniciar el checkout. Intenta nuevamente.")
};

// O que vem na assinatura (o mesmo da página de vendas).
const included = [
  L("Roteiros ilimitados no ar", "Itinerarios ilimitados publicados"),
  L("Editor visual com seções prontas", "Editor visual con secciones listas"),
  L("Assistente de IA para montar páginas", "Asistente de IA para armar páginas"),
  L("Criativos para anúncios e stories", "Creativos para anuncios y stories"),
  L("Módulo Leads e funil de vendas", "Módulo Leads y embudo de ventas"),
  L("Notificações inteligentes", "Notificaciones inteligentes"),
  L("Domínio próprio da agência", "Dominio propio de la agencia"),
  L("Pixels Meta e Google", "Píxeles de Meta y Google"),
  L("Equipe com até 5 usuários", "Equipo con hasta 5 usuarios"),
  L("Duplicar páginas em um clique", "Duplicar páginas con un clic")
].map(item => t(item));

type BillingCycle = "monthly" | "annual";
interface BillingInfo {
  plan: string;
  status: string;
  valid_until?: string;
  billing_cycle?: string;
  scheduled_downgrade_plan?: string | null;
  scheduled_downgrade_at?: string | null;
}

const authStore = useAuthStore();
const trialBlocked = computed(() => Boolean(authStore.user?.trial_blocked));
const trialPlanActive = computed(() => authStore.user?.trial_plan === "trial");
const trialEndsAtText = computed(() => {
  const endsAt = authStore.user?.trial_ends_at;
  return endsAt ? new Date(endsAt).toLocaleDateString(dateLocale) : null;
});

const billingInfo = ref<BillingInfo | null>(null);
const salesPlan = ref<SalesPlan>({ monthly: null, annual: null });
const salesPlanLoading = ref(true);
const cycle = ref<BillingCycle>("monthly");
const loadingKey = ref<string | null>(null);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);

const normalizedPlanKey = (value?: string | null) => {
  const raw = String(value || "").trim().toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  if (!raw) return "free";
  if (["growth", "agencia", "agency"].includes(raw)) return "growth";
  if (["essencial", "profissional", "professional", "starter"].includes(raw)) return "essencial";
  if (["infinity", "escala", "scale"].includes(raw)) return "infinity";
  if (["free", "gratuito", "trial", "teste"].includes(raw)) return "free";
  return raw;
};
const activePlan = computed(() => normalizedPlanKey(billingInfo.value?.plan || authStore.user?.plan || "free"));
const isSubscriptionInactive = computed(() =>
  new Set(["inactive", "cancelled", "cancelled_admin", "past_due"]).has(String(billingInfo.value?.status || "").trim().toLowerCase())
);
const isLegacyPlan = computed(() => ["essencial", "growth"].includes(activePlan.value) && !isSubscriptionInactive.value);
const isScale = computed(() => activePlan.value === "infinity");
const isScaleActive = computed(() => isScale.value && !isSubscriptionInactive.value);
const currentCycle = computed<BillingCycle>(() => (billingInfo.value?.billing_cycle === "annual" ? "annual" : "monthly"));
const isCurrentCycle = computed(() => isScaleActive.value && cycle.value === currentCycle.value);

const math = computed(() => salesPlanMath(salesPlan.value.monthly?.amount, salesPlan.value.annual?.amount));
const currentOffer = computed(() => salesPlan.value[cycle.value] || salesPlan.value.monthly || salesPlan.value.annual);
// Anual no cartão em até 12x (valor da parcela vem do Admin Master).
const annualInstallment = computed(() => {
  const offer = currentOffer.value;
  if (!offer || offer.billing_cycle !== "annual" || (offer.max_installments || 1) <= 1 || !offer.installment_value) return null;
  return { count: offer.max_installments || 1, value: offer.installment_value };
});
// Promoção da 1ª mensalidade: só para quem ainda não paga um plano (o checkout confirma).
const promoAmount = computed(() => {
  const offer = currentOffer.value;
  if (!offer || offer.billing_cycle !== "monthly" || !offer.first_payment_amount) return "";
  if (isLegacyPlan.value || isScale.value) return "";
  return offer.first_payment_amount;
});
const cycleLabel = (value: BillingCycle) => (value === "annual" ? t(copy.annual) : t(copy.monthly));
const priceNumber = (amount: string) => formatBRL(amount).replace(/^R\$\s*/, "");

// Quem já assina o anual não troca para o mensal no meio do ciclo.
const ctaDisabled = computed(() => isScaleActive.value && currentCycle.value === "annual" && cycle.value === "monthly");
const ctaLabel = computed(() => {
  if (isScale.value && isSubscriptionInactive.value) return t(copy.reactivate);
  if (ctaDisabled.value) return t(copy.alreadyAnnual);
  if (isCurrentCycle.value) return t(copy.renew);
  if (isScaleActive.value && cycle.value === "annual") return t(copy.switchToAnnual);
  return t(copy.subscribe);
});
const ctaHint = computed(() => (ctaDisabled.value ? t(copy.alreadyAnnualHint) : ""));

// O checkout de upgrade/renovação exige login (Bearer token no localStorage).
// O localStorage é por domínio, então precisa abrir no mesmo domínio do app,
// e não em roteiroonline.com (onde o usuário não está logado e a API devolve 401).
const checkoutBaseOrigin = computed(() => {
  if (typeof window === "undefined") return "";
  return window.location.origin;
});

const goToCheckout = () => {
  const offer = currentOffer.value;
  if (!offer || ctaDisabled.value) return;
  loadingKey.value = cycle.value;
  errorMessage.value = null;
  try {
    window.location.href = `${checkoutBaseOrigin.value}/checkout/${encodeURIComponent(offer.key)}?upgrade=1`;
  } catch (err) {
    console.error(err);
    errorMessage.value = t(copy.checkoutError);
    loadingKey.value = null;
  }
};

const cancelScheduledDowngrade = async () => {
  loadingKey.value = "cancel-scheduled-downgrade";
  errorMessage.value = null;
  successMessage.value = null;
  try {
    const { data } = await api.post<BillingInfo>("/billing/cancel-scheduled-downgrade");
    billingInfo.value = data;
    successMessage.value = "Downgrade agendado cancelado com sucesso.";
  } catch {
    errorMessage.value = t(copy.checkoutError);
  } finally {
    loadingKey.value = null;
  }
};

onMounted(async () => {
  const [billing, plan] = await Promise.allSettled([api.get<BillingInfo>("/billing/me"), getPublicSalesPlan()]);
  if (billing.status === "fulfilled") billingInfo.value = billing.value.data;
  if (plan.status === "fulfilled") salesPlan.value = plan.value;
  salesPlanLoading.value = false;
  // Abre no ciclo de quem já assina; senão no mensal (no anual só se não houver mensal).
  if (isScaleActive.value) cycle.value = currentCycle.value;
  else if (!salesPlan.value.monthly && salesPlan.value.annual) cycle.value = "annual";
});
</script>

<style scoped>
.plans-view {
  min-height: 100%;
  background: var(--background);
  color: var(--foreground);
}
.pv-wrap {
  max-width: 1040px;
  margin: 0 auto;
  padding: 20px 16px 32px;
}
.pv-head {
  margin-bottom: 18px;
  text-align: center;
}
.pv-title {
  font-family: var(--font-display);
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.pv-sub {
  margin-top: 6px;
  color: var(--muted-foreground);
  font-size: 15px;
}
.pv-alert {
  margin: 0 auto 12px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}
.pv-alert-title {
  font-weight: 700;
}
.pv-alert-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.pv-alert.is-danger {
  background: var(--status-danger);
  color: var(--status-danger-foreground);
}
.pv-alert.is-success {
  background: var(--status-success);
  color: var(--status-success-foreground);
}
.pv-alert.is-warning {
  background: var(--status-warning);
  color: var(--status-warning-foreground);
}
.pv-alert.is-info {
  background: var(--status-info);
  color: var(--status-info-foreground);
}
.pv-offer {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
  gap: 16px;
}
.pv-incl {
  display: flex;
  flex-direction: column;
  padding: 22px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--card);
  box-shadow: var(--shadow-card);
}
.pv-incl-title {
  margin-bottom: 12px;
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
}
.pv-incl ul {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.pv-incl li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  line-height: 1.4;
}
.pv-incl li svg {
  margin-top: 2px;
  padding: 2px;
  border-radius: 50%;
  background: var(--primary);
  color: var(--primary-foreground);
}
.pv-incl-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  color: var(--muted-foreground);
  font-size: 13px;
}
.pv-price-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 22px;
  border: 2px solid var(--primary);
  border-radius: 16px;
  background: var(--card);
  box-shadow: var(--shadow-elegant);
  text-align: center;
}
.pv-current {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--status-success);
  color: var(--status-success-foreground);
  font-size: 12px;
  font-weight: 700;
}
.pv-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}
.pv-cycle {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--border);
  border-radius: 999px;
}
.pv-cycle button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  color: var(--muted-foreground);
  font-size: 14px;
  font-weight: 700;
}
.pv-cycle button.on {
  background: var(--foreground);
  color: var(--background);
}
.pv-off {
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--primary);
  color: var(--primary-foreground);
  font-size: 11px;
}
.pv-anchor,
.pv-eq {
  color: var(--muted-foreground);
  font-size: 14px;
}
.pv-eq b {
  color: var(--foreground);
}
.pv-price {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.pv-price .cur {
  font-size: 17px;
  font-weight: 700;
}
.pv-price .val {
  font-family: var(--font-display);
  font-size: 44px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
}
.pv-price .per {
  color: var(--muted-foreground);
  font-size: 14px;
  font-weight: 600;
}
.pv-save {
  color: var(--status-success-foreground);
  font-size: 13px;
  font-weight: 700;
}
.pv-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 46px;
  margin-top: 4px;
  border-radius: 12px;
  background: var(--primary);
  color: var(--primary-foreground);
  font-size: 15px;
  font-weight: 700;
  transition: opacity 0.2s ease;
}
.pv-btn:disabled {
  cursor: default;
  opacity: 0.55;
}
.pv-btn-ghost {
  padding: 6px 12px;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.pv-hint {
  color: var(--muted-foreground);
  font-size: 12.5px;
}
.pv-guarantee {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
}
.pv-guarantee svg {
  color: var(--primary);
}
.pv-msg {
  font-size: 12.5px;
  font-weight: 600;
}
.pv-msg.is-error {
  color: var(--destructive);
}
.pv-msg.is-success {
  color: var(--status-success-foreground);
}
@media (max-width: 860px) {
  .pv-offer {
    grid-template-columns: 1fr;
  }
  .pv-price-box {
    order: -1;
  }
}
@media (max-width: 520px) {
  .pv-incl ul {
    grid-template-columns: 1fr;
  }
}
</style>
