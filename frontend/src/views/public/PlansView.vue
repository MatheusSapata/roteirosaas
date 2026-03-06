<template>
  <div class="min-h-screen bg-white text-slate-900">
    <div class="relative px-4 pb-16 lg:px-12">
      <header class="relative mx-auto max-w-6xl pt-10 pb-10 text-center">
        <div
          class="mx-auto inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-500 shadow-sm ring-1 ring-amber-100"
        >
          <span>Planos</span>
          <span class="h-1 w-1 rounded-full bg-amber-400"></span>
          <span>Escolha o melhor para você</span>
        </div>

        <h1 class="mt-6 text-4xl font-black tracking-tight text-slate-900 md:text-5xl">
          Planos pensados para crescer com sua agência
        </h1>

        <p class="mx-auto mt-4 max-w-2xl text-base text-slate-600 md:text-lg">
          Comece grátis com uma página. Faça upgrade só quando precisar de mais páginas e recursos.
        </p>

        <div class="mt-6 flex flex-wrap items-center justify-center gap-3 text-sm text-slate-600">
          <div class="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">✓</span>
            <span>Upgrade instantâneo</span>
          </div>

          <div class="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100 text-amber-600">⚡</span>
            <span>Sem taxas de setup</span>
          </div>

          <div class="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">↻</span>
            <span>Downgrade quando quiser</span>
          </div>
        </div>
      </header>

      <div
        v-if="trialBlocked"
        class="mx-auto mb-8 max-w-4xl rounded-3xl border border-rose-200 bg-rose-50 p-5 text-rose-900 shadow-sm"
      >
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">Trial encerrado</p>
        <p class="mt-2 text-sm">
          Seu período trial terminou e o painel foi bloqueado. Ative um plano para liberar novamente suas páginas e retomar as publicações.
        </p>
      </div>
      <div
        v-else-if="trialPlanActive"
        class="mx-auto mb-8 max-w-4xl rounded-3xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900 shadow-sm"
      >
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Trial ativo</p>
        <p class="mt-2 text-sm">
          Você está aproveitando o plano Trial com até 3 páginas, seções e pixels ilimitados
          <span v-if="trialEndsAtText">até {{ trialEndsAtText }}.</span>
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
              Mensal
            </button>
            <button
              type="button"
              class="rounded-full px-4 py-2 transition"
              :class="billingCycle === 'annual' ? 'bg-white text-slate-900 shadow' : ''"
              @click="billingCycle = 'annual'"
            >
              Anual
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
                Seu plano atual
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
                <span v-if="plan.isCurrent">Plano atual</span>
                <span v-else-if="loadingPlan === plan.key">Redirecionando...</span>
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
            <p class="text-sm font-semibold text-amber-600">Transparência total</p>
            <p class="text-sm text-slate-600">
              Sem taxas de cancelamento ou contratos longos. Troque ou cancele com 1 clique.
            </p>
          </div>

          <div class="flex items-center gap-2 text-sm text-slate-600">
            <span class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
              24/7
            </span>
            <div>
              <p class="font-semibold text-slate-900">Suporte prioritário</p>
              <p class="text-xs text-slate-500">Atendimento em português via chat e WhatsApp.</p>
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
import { useAuthStore } from "../../store/useAuthStore";
import { planLabels } from "../../utils/planLabels";

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

interface PlanDefinition extends Omit<PlanCard, "price" | "period" | "detail" | "isCurrent"> {
  prices: Record<BillingCycle, { value: number; period: string; detail?: string }>;
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

const authStore = useAuthStore();
const trialBlocked = computed(() => Boolean(authStore.user?.trial_blocked));
const trialPlanActive = computed(() => authStore.user?.trial_plan === "trial");
const trialEndsAtText = computed(() => {
  const endsAt = authStore.user?.trial_ends_at;
  if (!endsAt) return null;
  return new Date(endsAt).toLocaleDateString("pt-BR");
});

const billingCycle = ref<BillingCycle>("annual");
const billingCycleDescriptions: Record<BillingCycle, string> = {
  monthly: "Pague mês a mês",
  annual: "Economize escolhendo o plano anual"
};

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

const planDefinitions: PlanDefinition[] = [
  {
    key: "essencial",
    tier: "Profissional",
    name: "Plano Profissional",
    subtitle: "Para quem já vende excursões e quer mais presença online",
    highlight: "Para quem quer vender mais roteiros",
    features: [
      "Até 3 roteiros online ativos",
      "Seções ilimitadas dentro de cada roteiro",
      "Salvar modelo padrão para copiar em novas viagens",
      "Conectar 1 pixel (Facebook ou Google)",
      "Componentes extras (depoimentos, contagem regressiva, FAQ)"
    ],
    badge: "Recomendado para crescer",
    badgeTone: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    cta: "Quero organizar minhas viagens",
    note: "Perfeito para quem já tem grupos rodando.",
    ctaClass: "bg-emerald-600 hover:bg-emerald-500",
    prices: {
      monthly: { value: 49.9, period: "/mês" },
      annual: { value: 479.88, period: "/ano" }
    }
  },
  {
    key: "growth",
    tier: "Agência",
    name: "Plano Agência",
    subtitle: "Para agências que querem vender todos os meses com previsibilidade",
    highlight: "Mais usado pelas agências",
    features: ["Até 10 roteiros online ativos", "Conectar até 3 pixels", "Duplicação rápida de páginas", "Todos os recursos do Profissional"],
    badge: "Mais popular",
    badgeTone: "bg-amber-100 text-amber-800 ring-amber-200",
    cta: "Quero escalar minhas vendas",
    note: "Mantenha vários destinos ativos o ano todo.",
    ctaClass: "bg-amber-500 hover:bg-amber-400",
    prices: {
      monthly: { value: 89.99, period: "/mês" },
      annual: { value: 839.88, period: "/ano" }
    }
  },
  {
    key: "infinity",
    tier: "Escala",
    name: "Plano Escala",
    subtitle: "Para agências que operam múltiplos grupos e querem dominar sua região",
    highlight: "Para dominar sua região",
    features: [
      "Roteiros ilimitados",
      "Todos os recursos dos planos anteriores",
      "Ideal para múltiplos destinos simultâneos"
    ],
    badge: "Para operação avançada",
    badgeTone: "bg-indigo-50 text-indigo-700 ring-indigo-100",
    cta: "Quero estruturar minha escala",
    note: "Pensado para agências com vários grupos ativos.",
    ctaClass: "bg-indigo-600 hover:bg-indigo-500",
    prices: {
      monthly: { value: 129.9, period: "/mês" },
      annual: { value: 1199.88, period: "/ano" }
    }
  }
] as const;

const testPlanFeatures = planDefinitions.find(plan => plan.key === "infinity")?.features ?? [];

const formatPrice = (value: number) =>
  value.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 2 });

const plans = computed<PlanCard[]>(() =>
  planDefinitions.map(def => {
    const cycle = billingCycle.value;
    const priceInfo = def.prices[cycle] || def.prices.monthly;
    const isAnnual = cycle === "annual";
    const monthlyPrice = def.prices.monthly.value;

    let displayValue = priceInfo.value;
    let period = priceInfo.period;
    let detail = priceInfo.detail;
    const annualSavings = monthlyPrice * 12 - priceInfo.value;

    if (isAnnual) {
      displayValue = priceInfo.value > 0 ? priceInfo.value / 12 : 0;
      period = "/mês";
      if (annualSavings > 0) {
        detail = `Economize ${formatPrice(annualSavings)} por ano`;
      } else if (!detail) {
        detail = `Total anual de ${formatPrice(priceInfo.value)}`;
      }
    }

    const oldAnnualValue = isAnnual && monthlyPrice > 0 ? monthlyPrice * 12 : undefined;

    return {
      ...def,
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
    const res = await api.post<{ init_point: string }>("/billing/checkout", {
      plan: planKey,
      cycle: cycleOverride ?? billingCycle.value
    });
    window.location.href = res.data.init_point;
  } catch (err) {
    console.error(err);
    errorMessage.value = "Não foi possível iniciar o checkout. Tente novamente.";
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
