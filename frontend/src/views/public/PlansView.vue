<template>
  <div class="min-h-screen bg-white text-slate-900">
    <div class="relative px-4 pb-16 lg:px-12">
      <header class="relative mx-auto max-w-6xl pt-10 pb-10 text-center">
        <div
          class="mx-auto inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-500 shadow-sm ring-1 ring-amber-100"
        >
          <span>{{ heroChipLabel }}</span>
          <span class="h-1 w-1 rounded-full bg-amber-400"></span>
          <span>{{ heroChipDetail }}</span>
        </div>

        <h1 class="mt-6 text-4xl font-black tracking-tight text-slate-900 md:text-5xl">
          {{ heroTitle }}
        </h1>

        <p class="mx-auto mt-4 max-w-2xl text-base text-slate-600 md:text-lg">
          {{ heroDescription }}
        </p>

        <div class="mt-6 flex flex-wrap items-center justify-center gap-3 text-sm text-slate-600">
          <div class="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">✓</span>
            <span>{{ heroHighlights.upgrade }}</span>
          </div>

          <div class="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100 text-amber-600">⚡</span>
            <span>{{ heroHighlights.setup }}</span>
          </div>

          <div class="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">↻</span>
            <span>{{ heroHighlights.downgrade }}</span>
          </div>
        </div>
      </header>

      <div
        v-if="trialBlocked"
        class="mx-auto mb-8 max-w-4xl rounded-3xl border border-rose-200 bg-rose-50 p-5 text-rose-900 shadow-sm"
      >
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">{{ trialBlockedTitle }}</p>
        <p class="mt-2 text-sm">{{ trialBlockedDescription }}</p>
      </div>
      <div
        v-else-if="trialPlanActive"
        class="mx-auto mb-8 max-w-4xl rounded-3xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900 shadow-sm"
      >
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">{{ trialActiveTitle }}</p>
        <p class="mt-2 text-sm">
          {{ trialActiveDescription }}
          <span v-if="trialEndsAtText">{{ trialActiveUntilLabel }} {{ trialEndsAtText }}.</span>
        </p>
      </div>

      <section id="planos" class="relative mx-auto max-w-7xl pb-16">
        <div class="mb-8 flex flex-col items-center gap-2">
          <div class="inline-flex rounded-full bg-slate-100 p-1 text-sm font-semibold text-slate-500 shadow-inner">
            <button
              type="button"
              class="rounded-full px-4 py-2 transition"
              :class="billingCycle === 'monthly' ? 'bg-white text-slate-900 shadow' : ''"
              @click="billingCycle = 'monthly'"
            >
              {{ billingCycleLabels.monthly }}
            </button>
            <button
              type="button"
              class="rounded-full px-4 py-2 transition"
              :class="billingCycle === 'annual' ? 'bg-white text-slate-900 shadow' : ''"
              @click="billingCycle = 'annual'"
            >
              {{ billingCycleLabels.annual }}
            </button>
          </div>
          <p class="text-xs text-slate-500">{{ billingCycleDescriptions[billingCycle] }}</p>
        </div>

        <div class="mx-auto grid max-w-6xl gap-8 md:grid-cols-2 xl:grid-cols-3 justify-items-center">
          <article
            v-for="plan in plans"
            :key="plan.key"
            class="group relative flex h-full w-full flex-col gap-6 overflow-visible rounded-3xl border bg-white p-7 pt-9 shadow-[0_16px_50px_-30px_rgba(15,23,42,0.35)] transition duration-200 hover:-translate-y-1 hover:shadow-[0_26px_80px_-40px_rgba(15,23,42,0.45)]"
            :class="plan.isCurrent ? 'border-emerald-300 ring-2 ring-emerald-100' : 'border-slate-100'"
          >
            <div
              v-if="plan.badge || plan.isCurrent"
              class="pointer-events-none absolute -top-5 left-0 right-0 flex justify-center gap-2"
            >
              <span
                v-if="plan.isCurrent"
                class="inline-flex items-center gap-2 whitespace-nowrap rounded-full bg-emerald-100 px-3 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-emerald-800 shadow-sm ring-1 ring-emerald-200"
              >
                <span class="h-2 w-2 rounded-full bg-emerald-500"></span>
                {{ currentPlanBadgeLabel }}
              </span>

              <span
                v-if="!plan.isCurrent && plan.badge"
                class="inline-flex items-center gap-2 whitespace-nowrap rounded-full bg-white px-3 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-amber-700 shadow-sm ring-1 ring-amber-200"
                :class="plan.badgeTone"
              >
                <span>★</span>
                <span>{{ plan.badge }}</span>
              </span>
            </div>

            <div class="relative space-y-2">
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ plan.tier }}</p>
              <h3 class="text-2xl font-bold text-slate-900">{{ plan.name }}</h3>
              <p class="text-sm text-slate-600">{{ plan.subtitle }}</p>

              <div v-if="plan.oldPrice" class="text-sm text-slate-500 line-through">
                {{ plan.oldPrice }}
              </div>

              <div class="flex items-baseline gap-2">
                <p class="text-3xl font-black text-slate-900 md:text-4xl">{{ plan.price }}</p>
                <span class="text-sm font-semibold text-amber-600">{{ plan.period }}</span>
              </div>
              <p v-if="plan.detail" class="text-xs font-semibold text-indigo-600">{{ plan.detail }}</p>

              <p class="text-sm font-medium text-emerald-600">{{ plan.highlight }}</p>
            </div>

            <ul class="relative space-y-3 text-sm text-slate-700">
              <li v-for="feature in plan.features" :key="feature" class="flex items-start gap-3">
                <span
                  class="mt-0.5 flex h-6 w-6 flex-none items-center justify-center rounded-full bg-emerald-100 text-emerald-600 shadow-inner"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                    <path
                      fill-rule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-7.25 7.25a1 1 0 01-1.414 0l-3.25-3.25a1 1 0 111.414-1.414l2.543 2.543 6.543-6.543a1 1 0 011.414 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </span>
                <span>{{ feature }}</span>
              </li>
            </ul>

            <div class="relative mt-auto flex flex-col gap-3">
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl disabled:opacity-60"
                :class="plan.ctaClass"
                :disabled="plan.isCurrent || loadingPlan === plan.key"
                @click="handlePlanClick(plan.key)"
              >
                <span v-if="plan.isCurrent">{{ planButtonLabels.current }}</span>
                <span v-else-if="loadingPlan === plan.key">{{ planButtonLabels.redirecting }}</span>
                <span v-else>{{ plan.cta }}</span>
                <span v-if="!plan.isCurrent && loadingPlan !== plan.key" aria-hidden="true">→</span>
              </button>

              <p class="text-xs text-slate-500">{{ plan.note }}</p>

              <p v-if="errorMessage && loadingPlan === null" class="text-xs font-semibold text-rose-600">
                {{ errorMessage }}
              </p>
            </div>
          </article>
        </div>

        <div
          class="mt-10 flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-white px-6 py-5 shadow-[0_16px_50px_-35px_rgba(15,23,42,0.45)] ring-1 ring-slate-100"
        >
          <div>
            <p class="text-sm font-semibold text-amber-600">{{ transparencyTitle }}</p>
            <p class="text-sm text-slate-600">
              {{ transparencyDescription }}
            </p>
          </div>

          <div class="flex items-center gap-2 text-sm text-slate-600">
            <span class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
              24/7
            </span>
            <div>
              <p class="font-semibold text-slate-900">{{ supportTitle }}</p>
              <p class="text-xs text-slate-500">{{ supportDescription }}</p>
            </div>
          </div>
        </div>

        <!-- <div class="mt-10 rounded-3xl border border-emerald-100 bg-emerald-50/50 p-6 shadow-sm">
          <div class="space-y-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Plano teste</p>
              <h3 class="text-2xl font-bold text-slate-900">Checkout rápido para validações</h3>
              <p class="text-sm text-slate-600">
                Use os botões abaixo para disparar o checkout com o plano de teste. Ele replica todos os benefícios do plano
                Escala, mas com valores reduzidos só para homologação.
              </p>
            </div>

            <ul class="grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
              <li v-for="feature in testPlanFeatures" :key="feature" class="flex items-start gap-2">
                <span class="mt-1 text-emerald-600">✓</span>
                <span>{{ feature }}</span>
              </li>
            </ul>

            <div class="flex flex-wrap gap-3">
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow transition hover:bg-emerald-500 disabled:opacity-60"
                :disabled="loadingPlan === 'teste-monthly'"
                @click="startTestCheckout('monthly')"
              >
                <span v-if="loadingPlan === 'teste-monthly'">Redirecionando...</span>
                <span v-else>Testar mensal (R$ 5,00)</span>
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-full bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow transition hover:bg-indigo-500 disabled:opacity-60"
                :disabled="loadingPlan === 'teste-annual'"
                @click="startTestCheckout('annual')"
              >
                <span v-if="loadingPlan === 'teste-annual'">Redirecionando...</span>
                <span v-else>Testar anual (R$ 6,00)</span>
              </button>
            </div>

            <p v-if="errorMessage && loadingPlan === null" class="text-xs font-semibold text-rose-600">
              {{ errorMessage }}
            </p>
          </div>
        </div>
      -->

      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import api from "../../services/api";
import { CHECKOUT_SESSION_STORAGE_KEY, createCaktoCheckoutSession } from "../../services/cakto";
import { useAuthStore } from "../../store/useAuthStore";
import { planLabels } from "../../utils/planLabels";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import type { LocalizedString, SupportedLanguage } from "../../utils/i18n";

const currentLanguage = getCurrentLanguage();
const localize = createLocalizer(currentLanguage);
const localeByLanguage: Record<SupportedLanguage, string> = {
  pt: "pt-BR",
  es: "es-ES"
};
const dateLocale = localeByLanguage[currentLanguage] || "pt-BR";

const viewCopy = {
  hero: {
    chipLabel: { pt: "Planos", es: "Planes" },
    chipDetail: { pt: "Escolha o melhor para você", es: "Elige el mejor para ti" },
    title: { pt: "Planos pensados para crescer com sua agência", es: "Planes pensados para crecer con tu agencia" },
    description: {
      pt: "Comece grátis com uma página. Faça upgrade só quando precisar de mais páginas e recursos.",
      es: "Empieza gratis con una página. Haz upgrade solo cuando necesites más páginas y recursos."
    },
    highlights: {
      upgrade: { pt: "Upgrade instantâneo", es: "Upgrade instantáneo" },
      setup: { pt: "Sem taxas de setup", es: "Sin tarifas de configuración" },
      downgrade: { pt: "Downgrade quando quiser", es: "Baja de plan cuando quieras" }
    }
  },
  trial: {
    blockedTitle: { pt: "Trial encerrado", es: "Trial finalizado" },
    blockedDescription: {
      pt: "Seu período trial terminou e o painel foi bloqueado. Ative um plano para liberar novamente suas páginas e retomar as publicações.",
      es: "Tu período de prueba terminó y el panel fue bloqueado. Activa un plan para liberar tus páginas otra vez y retomar las publicaciones."
    },
    activeTitle: { pt: "Trial ativo", es: "Trial activo" },
    activeDescription: {
      pt: "Você está aproveitando o plano Trial com até 3 páginas, seções e pixels ilimitados",
      es: "Estás aprovechando el plan Trial con hasta 3 páginas, secciones y píxeles ilimitados"
    },
    activeUntil: { pt: "até", es: "hasta" }
  },
  billing: {
    monthlyLabel: { pt: "Mensal", es: "Mensual" },
    annualLabel: { pt: "Anual", es: "Anual" },
    monthlyDescription: { pt: "Pague mês a mês", es: "Paga mes a mes" },
    annualDescription: { pt: "Economize escolhendo o plano anual", es: "Ahorra eligiendo el plan anual" }
  },
  badges: {
    currentPlan: { pt: "Seu plano atual", es: "Tu plan actual" }
  },
  buttons: {
    currentPlan: { pt: "Plano atual", es: "Plan actual" },
    redirecting: { pt: "Redirecionando...", es: "Redirigiendo..." }
  },
  transparency: {
    title: { pt: "Transparência total", es: "Transparencia total" },
    description: {
      pt: "Sem taxas de cancelamento ou contratos longos. Troque ou cancele com 1 clique.",
      es: "Sin tasas de cancelación ni contratos largos. Cambia o cancela con 1 clic."
    },
    supportTitle: { pt: "Suporte prioritário", es: "Soporte prioritario" },
    supportDescription: {
      pt: "Atendimento em português via chat e WhatsApp.",
      es: "Atención en portugués por chat y WhatsApp."
    }
  },
  checkoutError: {
    pt: "Não foi possível iniciar o checkout. Tente novamente.",
    es: "No fue posible iniciar el checkout. Intenta nuevamente."
  }
} as const;

const heroChipLabel = localize(viewCopy.hero.chipLabel);
const heroChipDetail = localize(viewCopy.hero.chipDetail);
const heroTitle = localize(viewCopy.hero.title);
const heroDescription = localize(viewCopy.hero.description);
const heroHighlights = {
  upgrade: localize(viewCopy.hero.highlights.upgrade),
  setup: localize(viewCopy.hero.highlights.setup),
  downgrade: localize(viewCopy.hero.highlights.downgrade)
};
const trialBlockedTitle = localize(viewCopy.trial.blockedTitle);
const trialBlockedDescription = localize(viewCopy.trial.blockedDescription);
const trialActiveTitle = localize(viewCopy.trial.activeTitle);
const trialActiveDescription = localize(viewCopy.trial.activeDescription);
const trialActiveUntilLabel = localize(viewCopy.trial.activeUntil);
const currentPlanBadgeLabel = localize(viewCopy.badges.currentPlan);
const planButtonLabels = {
  current: localize(viewCopy.buttons.currentPlan),
  redirecting: localize(viewCopy.buttons.redirecting)
};
const transparencyTitle = localize(viewCopy.transparency.title);
const transparencyDescription = localize(viewCopy.transparency.description);
const supportTitle = localize(viewCopy.transparency.supportTitle);
const supportDescription = localize(viewCopy.transparency.supportDescription);
const checkoutErrorMessage = localize(viewCopy.checkoutError);

interface PlanCard {
  key: string;
  tier: string;
  name: string;
  subtitle: string;
  price: string;
  oldPrice?: string;
  period: string;
  detail?: string;
  highlight: string;
  features: string[];
  badge?: string;
  badgeTone?: string;
  cta: string;
  note: string;
  ctaClass: string;
  isCurrent?: boolean;
}

interface PlanDefinition {
  key: string;
  tier: LocalizedString;
  name: LocalizedString;
  subtitle: LocalizedString;
  highlight: LocalizedString;
  features: LocalizedString[];
  badge?: LocalizedString;
  badgeTone?: string;
  cta: LocalizedString;
  note: LocalizedString;
  ctaClass: string;
  prices: Record<BillingCycle, { value: number; period: LocalizedString; detail?: LocalizedString }>;
}

type BillingCycle = "monthly" | "annual";

interface BillingInfo {
  plan: string;
  status: string;
  valid_until?: string;
  failed_attempts: number;
  preapproval_id?: string;
  provider?: string;
  billing_cycle?: string;
}

const billingCycleLabels: Record<BillingCycle, string> = {
  monthly: localize(viewCopy.billing.monthlyLabel),
  annual: localize(viewCopy.billing.annualLabel)
};

const billingCycleDescriptions: Record<BillingCycle, string> = {
  monthly: localize(viewCopy.billing.monthlyDescription),
  annual: localize(viewCopy.billing.annualDescription)
};

const authStore = useAuthStore();
const trialBlocked = computed(() => Boolean(authStore.user?.trial_blocked));
const trialPlanActive = computed(() => authStore.user?.trial_plan === "trial");
const trialEndsAtText = computed(() => {
  const endsAt = authStore.user?.trial_ends_at;
  if (!endsAt) return null;
  return new Date(endsAt).toLocaleDateString(dateLocale);
});

const billingCycle = ref<BillingCycle>("annual");

const loadingPlan = ref<string | null>(null);
const errorMessage = ref<string | null>(null);

const billingInfo = ref<BillingInfo | null>(null);

const activePlan = computed(() => billingInfo.value?.plan || authStore.user?.plan || "free");

const planNames: Record<string, string> = {
  free: `Plano ${planLabels.free}`,
  essencial: `Plano ${planLabels.essencial}`,
  growth: `Plano ${planLabels.growth}`,
  infinity: `Plano ${planLabels.infinity}`,
  teste: `Plano ${planLabels.teste}`
};

const directCheckoutLinks: Record<string, Partial<Record<BillingCycle, string>>> = {
  essencial: {
    monthly: "https://pay.cakto.com.br/7o7zrup_800651",
    annual: "https://pay.cakto.com.br/nxc42uz"
  },
  growth: {
    monthly: "https://pay.cakto.com.br/n7vnc73_800688",
    annual: "https://pay.cakto.com.br/32uvp8b"
  },
  infinity: {
    monthly: "https://pay.cakto.com.br/iexkakw_800692",
    annual: "https://pay.cakto.com.br/pxzgp5s"
  }
};

const pricePeriods: Record<BillingCycle, LocalizedString> = {
  monthly: { pt: "/mês", es: "/mes" },
  annual: { pt: "/ano", es: "/año" }
};

const planDefinitions: PlanDefinition[] = [
  {
    key: "essencial",
    tier: { pt: "Profissional", es: "Profesional" },
    name: { pt: "Plano Profissional", es: "Plan Profesional" },
    subtitle: {
      pt: "Para quem já vende excursões e quer mais presença online",
      es: "Para quienes ya venden excursiones y quieren más presencia online"
    },
    highlight: { pt: "Para quem quer vender mais roteiros", es: "Para quien quiere vender más itinerarios" },
    features: [
      { pt: "Até 3 roteiros online ativos", es: "Hasta 3 itinerarios online activos" },
      { pt: "Seções ilimitadas dentro de cada roteiro", es: "Secciones ilimitadas dentro de cada itinerario" },
      { pt: "Salvar modelo padrão para copiar em novas viagens", es: "Guardar un modelo base para copiar en nuevos viajes" },
      { pt: "Conectar 1 pixel (Facebook ou Google)", es: "Conectar 1 píxel (Facebook o Google)" },
      { pt: "Componentes extras (depoimentos, contagem regressiva, FAQ)", es: "Componentes extra (testimonios, cuenta regresiva, FAQ)" }
    ],
    badge: { pt: "Recomendado para crescer", es: "Recomendado para crecer" },
    badgeTone: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    cta: { pt: "Quero organizar minhas viagens", es: "Quiero organizar mis viajes" },
    note: { pt: "Perfeito para quem já tem grupos rodando.", es: "Perfecto para quienes ya tienen grupos en marcha." },
    ctaClass: "bg-emerald-600 hover:bg-emerald-500",
    prices: {
      monthly: { value: 49.99, period: pricePeriods.monthly },
      annual: { value: 479.88, period: pricePeriods.annual }
    }
  },
  {
    key: "growth",
    tier: { pt: "Agência", es: "Agencia" },
    name: { pt: "Plano Agência", es: "Plan Agencia" },
    subtitle: {
      pt: "Para agências que querem vender todos os meses com previsibilidade",
      es: "Para agencias que quieren vender todos los meses con previsibilidad"
    },
    highlight: { pt: "Mais usado pelas agências", es: "El más usado por las agencias" },
    features: [
      { pt: "Até 10 roteiros online ativos", es: "Hasta 10 itinerarios online activos" },
      { pt: "Conectar até 3 pixels", es: "Conectar hasta 3 píxeles" },
      { pt: "Duplicação rápida de páginas", es: "Duplicación rápida de páginas" },
      { pt: "Todos os recursos do Profissional", es: "Todos los recursos del Profesional" }
    ],
    badge: { pt: "Mais popular", es: "Más popular" },
    badgeTone: "bg-amber-100 text-amber-800 ring-amber-200",
    cta: { pt: "Quero escalar minhas vendas", es: "Quiero escalar mis ventas" },
    note: { pt: "Mantenha vários destinos ativos o ano todo.", es: "Mantén varios destinos activos todo el año." },
    ctaClass: "bg-amber-500 hover:bg-amber-400",
    prices: {
      monthly: { value: 89.99, period: pricePeriods.monthly },
      annual: { value: 839.88, period: pricePeriods.annual }
    }
  },
  {
    key: "infinity",
    tier: { pt: "Escala", es: "Escala" },
    name: { pt: "Plano Escala", es: "Plan Escala" },
    subtitle: {
      pt: "Para agências que operam múltiplos grupos e querem dominar sua região",
      es: "Para agencias que operan múltiples grupos y quieren dominar su región"
    },
    highlight: { pt: "Para dominar sua região", es: "Para dominar tu región" },
    features: [
      { pt: "Roteiros ilimitados", es: "Itinerarios ilimitados" },
      { pt: "Todos os recursos dos planos anteriores", es: "Todos los recursos de los planes anteriores" },
      { pt: "Ideal para múltiplos destinos simultâneos", es: "Ideal para múltiples destinos simultáneos" }
    ],
    badge: { pt: "Para operação avançada", es: "Para operación avanzada" },
    badgeTone: "bg-indigo-50 text-indigo-700 ring-indigo-100",
    cta: { pt: "Quero estruturar minha escala", es: "Quiero estructurar mi escala" },
    note: { pt: "Pensado para agências com vários grupos ativos.", es: "Pensado para agencias con varios grupos activos." },
    ctaClass: "bg-indigo-600 hover:bg-indigo-500",
    prices: {
      monthly: { value: 129.99, period: pricePeriods.monthly },
      annual: { value: 1199.88, period: pricePeriods.annual }
    }
  }
];

const testPlanFeatures =
  planDefinitions.find(plan => plan.key === "infinity")?.features.map(feature => localize(feature)) ?? [];

const formatPrice = (value: number) =>
  value.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 2 });

const formatAnnualSavingsDetail = (formattedValue: string) =>
  currentLanguage === "es" ? `Ahorra ${formattedValue} por año` : `Economize ${formattedValue} por ano`;

const formatAnnualTotalDetail = (formattedValue: string) =>
  currentLanguage === "es" ? `Total anual de ${formattedValue}` : `Total anual de ${formattedValue}`;

const plans = computed<PlanCard[]>(() =>
  planDefinitions.map(def => {
    const cycle = billingCycle.value;
    const priceInfo = def.prices[cycle] || def.prices.monthly;
    const isAnnual = cycle === "annual";
    const monthlyPrice = def.prices.monthly.value;

    let displayValue = priceInfo.value;
    let period = localize(priceInfo.period);
    let detail = localize(priceInfo.detail).trim();
    detail = detail.length ? detail : undefined;
    const annualSavings = monthlyPrice * 12 - priceInfo.value;

    if (isAnnual) {
      displayValue = priceInfo.value > 0 ? priceInfo.value / 12 : 0;
      period = localize(def.prices.monthly.period);
      if (annualSavings > 0) {
        detail = formatAnnualSavingsDetail(formatPrice(annualSavings));
      } else if (!detail) {
        detail = formatAnnualTotalDetail(formatPrice(priceInfo.value));
      }
    }

    const oldAnnualValue = isAnnual && monthlyPrice > 0 ? monthlyPrice * 12 : undefined;
    const badge = localize(def.badge).trim();

    return {
      key: def.key,
      tier: localize(def.tier),
      name: localize(def.name),
      subtitle: localize(def.subtitle),
      highlight: localize(def.highlight),
      features: def.features.map(feature => localize(feature)),
      badge: badge.length ? badge : undefined,
      badgeTone: def.badgeTone,
      cta: localize(def.cta),
      note: localize(def.note),
      ctaClass: def.ctaClass,
      price: formatPrice(displayValue),
      period,
      detail,
      oldPrice: oldAnnualValue ? formatPrice(oldAnnualValue) : undefined,
      isCurrent: def.key === activePlan.value
    };
  })
);

const goToCheckout = async (
  planKey: string,
  cycleOverride?: BillingCycle,
  force = false,
  loadingKey?: string
) => {
  if (!force && planKey === activePlan.value) return;

  loadingPlan.value = loadingKey ?? planKey;
  errorMessage.value = null;

  try {
    const cycle = cycleOverride ?? billingCycle.value;
    const { data } = await createCaktoCheckoutSession(planKey, cycle);
    localStorage.setItem(CHECKOUT_SESSION_STORAGE_KEY, data.token);
    const directLink = directCheckoutLinks[planKey]?.[cycle];
    const checkoutUrl = directLink
      ? `${directLink}${directLink.includes("?") ? "&" : "?"}sck=${data.token}`
      : data.checkout_url;
    window.location.href = checkoutUrl;
  } catch (err) {
    console.error(err);
    errorMessage.value = checkoutErrorMessage;
  } finally {
    loadingPlan.value = null;
  }
};

const handlePlanClick = (planKey: string) => {
  if (planKey === activePlan.value) return;
  goToCheckout(planKey);
};

const startTestCheckout = (cycle: BillingCycle) => {
  goToCheckout("teste", cycle, true, `teste-${cycle}`);
};

const loadBilling = async () => {
  try {
    const res = await api.get<BillingInfo>("/billing/me");
    billingInfo.value = res.data;
    if (res.data.billing_cycle === "annual" || res.data.billing_cycle === "monthly") {
      billingCycle.value = res.data.billing_cycle;
    }
  } catch (err) {
    console.error(err);
  }
};

onMounted(() => {
  loadBilling();
});
</script>
