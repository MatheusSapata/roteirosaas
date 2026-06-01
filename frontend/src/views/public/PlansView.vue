<template>
  <div class="min-h-screen bg-white text-slate-900">
    <div class="plans-content-scale relative px-4 pb-16 lg:px-8 2xl:px-10">
      <header class="relative mx-auto max-w-[96rem] pt-10 pb-10 text-center">
        <h1 class="text-4xl font-black tracking-tight text-slate-900 md:text-5xl">
          {{ heroTitle }}
        </h1>

        <p class="mx-auto mt-4 max-w-none text-sm text-slate-600 md:text-base md:whitespace-nowrap">
          {{ heroDescription }}
        </p>
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

      <section id="planos" class="relative mx-auto max-w-[98rem] pb-16">
        <div
          v-if="billingInfo?.scheduled_downgrade_plan"
          class="mx-auto mb-6 flex max-w-4xl items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3"
        >
          <p class="text-sm font-medium text-amber-900">
            Downgrade para <strong>{{ planNames[billingInfo.scheduled_downgrade_plan] || billingInfo.scheduled_downgrade_plan }}</strong>
            agendado para o fim do ciclo.
          </p>
          <button
            type="button"
            class="rounded-full bg-white px-4 py-2 text-xs font-semibold text-amber-800 ring-1 ring-amber-300 hover:bg-amber-100 disabled:opacity-60"
            :disabled="loadingPlan === 'cancel-scheduled-downgrade'"
            @click="cancelScheduledDowngrade"
          >
            {{ loadingPlan === "cancel-scheduled-downgrade" ? "Cancelando..." : "Cancelar downgrade" }}
          </button>
        </div>

        <div class="mx-auto grid max-w-[92rem] gap-8 md:grid-cols-2 xl:grid-cols-3 justify-items-center">
          <article
            v-for="plan in plans"
            :key="plan.key"
            class="group relative flex h-full w-full flex-col gap-6 overflow-visible rounded-3xl border bg-white p-7 pt-9 shadow-[0_16px_50px_-30px_rgba(15,23,42,0.35)] transition duration-200 hover:-translate-y-1 hover:shadow-[0_26px_80px_-40px_rgba(15,23,42,0.45)]"
            :class="plan.isCurrent ? 'border-emerald-400 bg-gradient-to-b from-emerald-50 to-white ring-1 ring-emerald-200' : 'border-slate-100'"
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
              <h3 class="text-[2rem] font-extrabold leading-tight text-slate-900">{{ plan.name }}</h3>
              <p class="text-sm text-slate-600">{{ plan.subtitle }}</p>

              <div v-if="plan.oldPrice" class="text-sm text-slate-500 line-through">
                {{ plan.oldPrice }}
              </div>

              <div class="flex items-baseline gap-2">
                <p class="text-3xl font-black text-slate-900 md:text-4xl">{{ plan.price }}</p>
                <span class="text-sm font-semibold text-amber-600">{{ plan.period }}</span>
              </div>
              <p v-if="plan.detail" class="text-xs font-semibold text-indigo-600">{{ plan.detail }}</p>
              <p class="text-base font-bold text-emerald-700">{{ plan.priceHint }}</p>
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

            <div v-if="plan.spotlightBoxes.length" class="space-y-3">
              <div
                v-for="box in plan.spotlightBoxes"
                :key="box.title"
                class="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-4"
              >
                <p class="text-[0.92rem] font-extrabold uppercase tracking-[0.11em] text-emerald-700">{{ box.title }}</p>
                <p class="mt-1 text-[0.92rem] text-slate-700">{{ box.description }}</p>
              </div>
            </div>

            <div class="relative mt-auto flex flex-col gap-3">
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl disabled:opacity-60"
                :class="plan.isCurrent ? 'bg-slate-300 text-slate-600' : (plan.isLowerThanCurrent ? 'bg-amber-500 hover:bg-amber-400' : plan.ctaClass)"
                :disabled="!plan.isActionable || loadingPlan === plan.key"
                @click="handlePlanClick(plan.key)"
              >
                <span v-if="plan.isCurrent">{{ planButtonLabels.current }}</span>
                <span v-else-if="loadingPlan === plan.key">{{ planButtonLabels.redirecting }}</span>
                <span v-else>{{ planCtaLabel(plan) }}</span>
                <span v-if="plan.isActionable && loadingPlan !== plan.key" aria-hidden="true">→</span>
              </button>

              <p class="text-xs text-slate-500">{{ plan.note }}</p>

              <p v-if="errorMessage && loadingPlan === null" class="text-xs font-semibold text-rose-600">
                {{ errorMessage }}
              </p>
              <p v-if="successMessage && loadingPlan === null" class="text-xs font-semibold text-emerald-700">
                {{ successMessage }}
              </p>
            </div>
          </article>
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
import { createUpgradeCheckoutSession } from "../../services/checkout";
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
    title: { pt: "Evolua seu plano e acelere seus resultados", es: "Sube de plan y acelera tus resultados" },
    description: {
      pt: "Desbloqueie mais recursos, aumente sua operação e transforme visitas em vendas com mais consistência.",
      es: "Desbloquea más recursos, amplía tu operación y convierte visitas en ventas con más consistencia."
    },
    highlights: {
      upgrade: { pt: "Ativação imediata", es: "Activación inmediata" },
      setup: { pt: "Sem burocracia", es: "Sin burocracia" },
      downgrade: { pt: "Mais conversão por lead", es: "Más conversión por lead" }
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
    redirecting: { pt: "Redirecionando...", es: "Redirigiendo..." },
    reactivate: { pt: "Reativar plano", es: "Reactivar plan" }
  },
  checkoutError: {
    pt: "Não foi possível iniciar o checkout. Tente novamente.",
    es: "No fue posible iniciar el checkout. Intenta nuevamente."
  }
} as const;

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
  redirecting: localize(viewCopy.buttons.redirecting),
  reactivate: localize(viewCopy.buttons.reactivate)
};
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
  priceHint?: string;
  highlight: string;
  features: string[];
  spotlightBoxes: { title: string; description: string }[];
  badge?: string;
  badgeTone?: string;
  cta: string;
  note: string;
  ctaClass: string;
  isCurrent?: boolean;
  isHigherThanCurrent?: boolean;
  isLowerThanCurrent?: boolean;
  isActionable?: boolean;
}

interface PlanDefinition {
  key: string;
  tier: LocalizedString;
  name: LocalizedString;
  subtitle: LocalizedString;
  priceHint: LocalizedString;
  highlight: LocalizedString;
  features: LocalizedString[];
  spotlightBoxes?: { title: LocalizedString; description: LocalizedString }[];
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
  scheduled_downgrade_plan?: string | null;
  scheduled_downgrade_at?: string | null;
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

const billingCycle = ref<BillingCycle>("monthly");

const loadingPlan = ref<string | null>(null);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);

const billingInfo = ref<BillingInfo | null>(null);
const currentSubscriptionProvider = computed(() =>
  String(billingInfo.value?.provider || "").trim().toLowerCase()
);

const normalizedPlanKey = (value?: string | null) => {
  const raw = String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  if (!raw) return "free";
  if (["growth", "agencia", "agência", "agency"].includes(raw)) return "growth";
  if (["essencial", "profissional", "professional", "starter"].includes(raw)) return "essencial";
  if (["infinity", "escala", "scale"].includes(raw)) return "infinity";
  if (["free", "gratuito", "trial", "teste"].includes(raw)) return "free";
  return raw;
};

const activePlan = computed(() => normalizedPlanKey(billingInfo.value?.plan || authStore.user?.plan || "free"));
const isSubscriptionInactive = computed(() => {
  const status = String(billingInfo.value?.status || "").trim().toLowerCase();
  return new Set(["inactive", "cancelled", "cancelled_admin", "past_due"]).has(status);
});

const planNames: Record<string, string> = {
  free: `Plano ${planLabels.free}`,
  essencial: `Plano ${planLabels.essencial}`,
  growth: `Plano ${planLabels.growth}`,
  infinity: `Plano ${planLabels.infinity}`,
  teste: `Plano ${planLabels.teste}`
};

const pricePeriods: Record<BillingCycle, LocalizedString> = {
  monthly: { pt: "/mês", es: "/mes" },
  annual: { pt: "/ano", es: "/año" }
};

const planDefinitions: PlanDefinition[] = [
  {
    key: "essencial",
    tier: { pt: "Para começar", es: "Para comenzar" },
    name: { pt: "Profissional", es: "Profesional" },
    subtitle: {
      pt: "Para quem quer parar de mandar textão no WhatsApp para o cliente.",
      es: "Para quien quiere dejar de enviar textos largos por WhatsApp."
    },
    priceHint: { pt: "≈ R$16,66 por roteiro", es: "≈ R$16,66 por itinerario" },
    highlight: { pt: "Plano base para vender com organização", es: "Plan base para vender con organización" },
    features: [
      { pt: "Até 3 roteiros online ativos", es: "Hasta 3 itinerarios online activos" },
      { pt: "Seções ilimitadas por roteiro", es: "Secciones ilimitadas por itinerario" },
      { pt: "Modelo padrão para reutilizar", es: "Modelo base para reutilizar" },
      { pt: "1 pixel conectado (Meta ou Google)", es: "1 píxel conectado (Meta o Google)" },
      { pt: "Botão de WhatsApp em cada seção", es: "Botón de WhatsApp en cada sección" },
      { pt: "Galeria de fotos com carrossel", es: "Galería de fotos con carrusel" }
    ],
    badge: { pt: "Para começar", es: "Para comenzar" },
    badgeTone: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    cta: { pt: "Começar com o Profissional", es: "Empezar con Profesional" },
    note: { pt: "Perfeito para quem já tem grupos rodando.", es: "Perfecto para quienes ya tienen grupos en marcha." },
    ctaClass: "bg-emerald-600 hover:bg-emerald-500",
    prices: {
      monthly: { value: 49.99, period: pricePeriods.monthly },
      annual: { value: 479.88, period: pricePeriods.annual }
    }
  },
  {
    key: "growth",
    tier: { pt: "Mais escolhido", es: "Más elegido" },
    name: { pt: "Agência", es: "Agencia" },
    subtitle: {
      pt: "Para agências que usam o roteiro online como ferramenta recorrente de vendas.",
      es: "Para agencias que usan la plataforma como herramienta recurrente de ventas."
    },
    priceHint: { pt: "≈ R$8,99 por roteiro", es: "≈ R$8,99 por itinerario" },
    highlight: { pt: "Mais usado pelas agências", es: "El más usado por las agencias" },
    features: [
      { pt: "Até 10 roteiros online ativos", es: "Hasta 10 itinerarios online activos" },
      { pt: "Duplicação rápida de páginas", es: "Duplicación rápida de páginas" },
      { pt: "Até 3 pixels conectados", es: "Hasta 3 píxeles conectados" },
      { pt: "Todos os recursos do Profissional", es: "Todos los recursos del Profesional" }
    ],
    spotlightBoxes: [
      {
        title: { pt: "Módulo Leads", es: "Módulo Leads" },
        description: {
          pt: "Formulário de captação dentro do roteiro. Cada passageiro pode virar oportunidade futura.",
          es: "Formulario de captación dentro del itinerario. Cada pasajero puede convertirse en oportunidad."
        }
      }
    ],
    badge: { pt: "Mais escolhido", es: "Más elegido" },
    badgeTone: "bg-emerald-100 text-emerald-800 ring-emerald-200",
    cta: { pt: "Assinar o plano Agência", es: "Suscribir plan Agencia" },
    note: { pt: "Mantenha vários destinos ativos o ano todo.", es: "Mantén varios destinos activos todo el año." },
    ctaClass: "bg-emerald-600 hover:bg-emerald-500",
    prices: {
      monthly: { value: 89.99, period: pricePeriods.monthly },
      annual: { value: 839.88, period: pricePeriods.annual }
    }
  },
  {
    key: "infinity",
    tier: { pt: "Operação avançada", es: "Operación avanzada" },
    name: { pt: "Escala", es: "Escala" },
    subtitle: {
      pt: "Para agências com vários grupos, campanhas e múltiplos destinos em andamento.",
      es: "Para agencias con múltiples grupos, campañas y destinos en paralelo."
    },
    priceHint: { pt: "Roteiros ilimitados", es: "Itinerarios ilimitados" },
    highlight: { pt: "Operação completa e ilimitada", es: "Operación completa e ilimitada" },
    features: [
      { pt: "Roteiros ilimitados", es: "Itinerarios ilimitados" },
      { pt: "Múltiplos destinos simultâneos", es: "Múltiples destinos simultáneos" },
      { pt: "Todos os recursos anteriores", es: "Todos los recursos anteriores" }
    ],
    spotlightBoxes: [
      {
        title: { pt: "Módulo Leads", es: "Módulo Leads" },
        description: {
          pt: "Formulário de captação com gestão de oportunidades integrada.",
          es: "Formulario de captación con gestión de oportunidades integrada."
        }
      },
      {
        title: { pt: "Domínio personalizado", es: "Dominio personalizado" },
        description: {
          pt: "Publique no endereço da sua própria agência. Exclusivo deste plano.",
          es: "Publica con el dominio de tu agencia. Exclusivo de este plan."
        }
      }
    ],
    badge: { pt: "Para operação avançada", es: "Para operación avanzada" },
    badgeTone: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    cta: { pt: "Começar com o Escala", es: "Empezar con Escala" },
    note: { pt: "Pensado para agências com vários grupos ativos.", es: "Pensado para agencias con varios grupos activos." },
    ctaClass: "bg-emerald-600 hover:bg-emerald-500",
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

    const planOrder: Record<string, number> = { free: 0, essencial: 1, growth: 2, infinity: 3 };
    const currentOrder = planOrder[activePlan.value] ?? 0;
    const thisOrder = planOrder[def.key] ?? 0;
    const isCurrent = !isSubscriptionInactive.value && def.key === activePlan.value;
    const isHigherThanCurrent = thisOrder > currentOrder;
    const isLowerThanCurrent = thisOrder < currentOrder;

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
      priceHint: localize(def.priceHint),
      oldPrice: oldAnnualValue ? formatPrice(oldAnnualValue) : undefined,
      spotlightBoxes: (def.spotlightBoxes || []).map(item => ({
        title: localize(item.title),
        description: localize(item.description)
      })),
      isCurrent,
      isHigherThanCurrent,
      isLowerThanCurrent,
      isActionable: isSubscriptionInactive.value ? true : !isCurrent
    };
  })
);

const planCtaLabel = (plan: PlanCard) => {
  if (plan.isCurrent) return planButtonLabels.current;
  if (isSubscriptionInactive.value && plan.key === activePlan.value) return planButtonLabels.reactivate;
  if (plan.isLowerThanCurrent) {
    return currentLanguage === "es" ? `Hacer downgrade a ${plan.name}` : `Fazer downgrade para ${plan.name}`;
  }
  return currentLanguage === "es" ? `Hacer upgrade a ${plan.name}` : `Fazer upgrade para ${plan.name}`;
};

const internalCheckoutPaths: Record<string, string> = {
  essencial: "/checkout/profissional",
  growth: "/checkout/agencia",
  infinity: "/checkout/escala"
};

const checkoutBaseOrigin = computed(() => {
  if (typeof window === "undefined") return "";
  if (import.meta.env.PROD) return "https://roteiroonline.com";
  return window.location.origin;
});

const goToCheckout = async (
  planKey: string,
  cycleOverride?: BillingCycle,
  force = false,
  loadingKey?: string
) => {
  if (!force && !isSubscriptionInactive.value && planKey === activePlan.value) return;

  loadingPlan.value = loadingKey ?? planKey;
  errorMessage.value = null;

  try {
    const cycle = cycleOverride ?? billingCycle.value;
    const keyToOffer: Record<string, string> = {
      essencial: "profissional",
      growth: "agencia",
      infinity: "escala",
    };
    const offerKey = keyToOffer[planKey];
    if (!offerKey && planKey !== "teste") throw new Error("Plano inválido para checkout.");

    if (currentSubscriptionProvider.value === "cakto") {
      const { data } = await createCaktoCheckoutSession(planKey, cycle);
      localStorage.setItem(CHECKOUT_SESSION_STORAGE_KEY, data.token);
      const checkoutUrl = String(data.checkout_url || "").trim();
      if (!checkoutUrl) throw new Error("Checkout Cakto indisponível.");
      window.location.href = checkoutUrl;
      return;
    }

    const session = await createUpgradeCheckoutSession(offerKey);
    const internalPath = internalCheckoutPaths[planKey];
    const checkoutUrl = internalPath
      ? `${checkoutBaseOrigin.value}${internalPath}?upgrade=1&token=${encodeURIComponent(session.token)}`
      : `${checkoutBaseOrigin.value}/checkout/${encodeURIComponent(offerKey)}?upgrade=1&token=${encodeURIComponent(session.token)}`;
    window.location.href = checkoutUrl;
  } catch (err) {
    console.error(err);
    errorMessage.value = checkoutErrorMessage;
  } finally {
    loadingPlan.value = null;
  }
};

const handlePlanClick = (planKey: string) => {
  if (!isSubscriptionInactive.value && planKey === activePlan.value) return;
  const planOrder: Record<string, number> = { free: 0, essencial: 1, growth: 2, infinity: 3 };
  const currentOrder = planOrder[activePlan.value] ?? 0;
  const targetOrder = planOrder[planKey] ?? 0;

  if (targetOrder < currentOrder) {
    loadingPlan.value = planKey;
    errorMessage.value = null;
    successMessage.value = null;
    api
      .post<BillingInfo>("/billing/schedule-downgrade", { plan: planKey })
      .then(({ data }) => {
        billingInfo.value = data;
        const until = data.valid_until ? new Date(data.valid_until).toLocaleDateString(dateLocale) : "";
        successMessage.value = until
          ? (currentLanguage === "es"
              ? `Downgrade programado para ${until}.`
              : `Downgrade programado para ${until}.`)
          : (currentLanguage === "es"
              ? "Downgrade programado para el fin del ciclo actual."
              : "Downgrade programado para o fim do ciclo atual.");
      })
      .catch(() => {
        errorMessage.value = checkoutErrorMessage;
      })
      .finally(() => {
        loadingPlan.value = null;
      });
    return;
  }

  goToCheckout(planKey);
};

const cancelScheduledDowngrade = async () => {
  loadingPlan.value = "cancel-scheduled-downgrade";
  errorMessage.value = null;
  successMessage.value = null;
  try {
    const { data } = await api.post<BillingInfo>("/billing/cancel-scheduled-downgrade");
    billingInfo.value = data;
    successMessage.value = "Downgrade agendado cancelado com sucesso.";
  } catch {
    errorMessage.value = checkoutErrorMessage;
  } finally {
    loadingPlan.value = null;
  }
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

<style scoped>
@media (min-width: 1024px) and (max-width: 1919px) {
  .plans-content-scale {
    transform: scale(0.75);
    transform-origin: top center;
  }
}

@media (min-width: 1920px) {
  .plans-content-scale {
    transform: scale(0.9);
    transform-origin: top center;
  }
}
</style>
