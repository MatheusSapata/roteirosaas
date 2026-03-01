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
          Comece grátis com 1 roteiro. Faça upgrade só quando precisar de mais roteiros e recursos.
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

      <section class="mx-auto max-w-5xl pb-10">
        <div class="rounded-3xl border border-slate-100 bg-white/95 p-6 shadow-lg">
          <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">Plano atual</p>
              <h3 class="text-2xl font-bold text-slate-900">
                {{ planNames[billingInfo?.plan || activePlan] }}
              </h3>
              <p class="text-sm text-slate-500">
                Status:
                <span :class="statusBadgeClass">{{ statusLabel }}</span>
                <span v-if="billingInfo?.valid_until" class="ml-2 text-slate-400">
                  Renovação: {{ formatDate(billingInfo.valid_until) }}
                </span>
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <button
                v-if="billingInfo?.plan !== 'free'"
                type="button"
                class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                :disabled="actionLoading"
                @click="cancelSubscription"
              >
                Cancelar renovação
              </button>

              <button
                v-if="billingInfo?.plan !== 'free'"
                type="button"
                class="rounded-full bg-red-50 px-4 py-2 text-sm font-semibold text-red-600 ring-1 ring-red-100 hover:bg-red-100 disabled:opacity-60"
                :disabled="actionLoading"
                @click="downgradeToFree"
              >
                Voltar ao plano gratuito
              </button>

              <span v-if="!billingInfo" class="text-sm text-slate-400">Carregando cobrança...</span>
            </div>
          </div>

          <p
            v-if="actionMessage"
            class="mt-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700"
          >
            {{ actionMessage }}
          </p>

          <p v-if="actionError" class="mt-3 rounded-xl bg-red-50 px-3 py-2 text-sm font-semibold text-red-600">
            {{ actionError }}
          </p>
        </div>
      </section>

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

        <div class="grid gap-8 md:grid-cols-2 xl:grid-cols-4">
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

const billingCycle = ref<BillingCycle>("annual");
const billingCycleDescriptions: Record<BillingCycle, string> = {
  monthly: "Pague mês a mês",
  annual: "Economize escolhendo o plano anual"
};

const loadingPlan = ref<string | null>(null);
const errorMessage = ref<string | null>(null);

const billingInfo = ref<BillingInfo | null>(null);

const actionLoading = ref(false);
const actionMessage = ref("");
const actionError = ref("");

const activePlan = computed(() => billingInfo.value?.plan || authStore.user?.plan || "free");

const planNames: Record<string, string> = {
  free: `Plano ${planLabels.free}`,
  essencial: `Plano ${planLabels.essencial}`,
  growth: `Plano ${planLabels.growth}`,
  infinity: `Plano ${planLabels.infinity}`
};

const planDefinitions: PlanDefinition[] = [
  {
    key: "free",
    tier: "Começo",
    name: "Plano Começo",
    subtitle: "Para quem está começando a organizar seus roteiros online",
    highlight: "Ideal para dar os primeiros passos",
    features: ["1 roteiro online publicado", "Editor simples e fácil de usar", "Layout pronto para agência", "Relatório básico de cliques"],
    cta: "Criar meu primeiro roteiro",
    note: "Publique seu primeiro roteiro sem custos.",
    ctaClass: "bg-slate-900 hover:bg-slate-800",
    prices: {
      monthly: { value: 0, period: "/mês" },
      annual: { value: 0, period: "/ano" }
    }
  },
  {
    key: "essencial",
    tier: "Profissional",
    name: "Plano Profissional",
    subtitle: "Para quem já vende excursões e quer mais presença online",
    highlight: "Para quem quer vender mais roteiros",
    features: [
      "Até 5 roteiros online ativos",
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
      annual: { value: 499.0, period: "/ano", detail: "Equivalente a R$ 41,58/mês" }
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
      monthly: { value: 79.9, period: "/mês" },
      annual: { value: 799.0, period: "/ano", detail: "Economize quase 2 meses" }
    }
  },
  {
    key: "infinity",
    tier: "Escala",
    name: "Plano Escala",
    subtitle: "Para agências que operam múltiplos grupos e querem dominar sua região",
    highlight: "Para dominar sua região",
    features: [
      "Até 15 roteiros online ativos",
      "Todos os recursos dos planos anteriores",
      "Ideal para múltiplos destinos simultâneos",
      "Página adicional: R$ 20,00 por roteiro extra"
    ],
    badge: "Para operação avançada",
    badgeTone: "bg-indigo-50 text-indigo-700 ring-indigo-100",
    cta: "Quero estruturar minha escala",
    note: "Pensado para agências com vários grupos ativos.",
    ctaClass: "bg-indigo-600 hover:bg-indigo-500",
    prices: {
      monthly: { value: 129.9, period: "/mês" },
      annual: { value: 1299.0, period: "/ano", detail: "Ideal para operação contínua" }
    }
  }
] as const;

const formatPrice = (value: number) =>
  value.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 2 });

const plans = computed<PlanCard[]>(() =>
  planDefinitions.map(def => {
    const priceInfo = def.prices[billingCycle.value] || def.prices.monthly;
    const oldAnnualValue =
      billingCycle.value === "annual" && def.prices.monthly.value > 0
        ? def.prices.monthly.value * 12
        : undefined;
    return {
      ...def,
      price: formatPrice(priceInfo.value),
      period: priceInfo.period,
      detail: priceInfo.detail,
      oldPrice: oldAnnualValue ? formatPrice(oldAnnualValue) : undefined,
      isCurrent: def.key === activePlan.value
    };
  })
);

const goToCheckout = async (planKey: string) => {
  if (planKey === activePlan.value) return;

  loadingPlan.value = planKey;
  errorMessage.value = null;

  try {
    const res = await api.post<{ init_point: string }>("/billing/checkout", {
      plan: planKey,
      cycle: billingCycle.value
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

const statusLabel = computed(() => {
  const status = billingInfo.value?.status || "inactive";
  if (status === "active") return "Ativo";
  if (status === "cancelled") return "Cancelado";
  if (status === "cancel_at_period_end") return "Cancelará no fim do ciclo";
  if (status === "past_due") return "Pagamento pendente";
  return "Inativo";
});

const statusBadgeClass = computed(() => {
  const status = billingInfo.value?.status || "inactive";
  if (status === "active") return "rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700";
  if (status === "cancelled") return "rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600";
  if (status === "cancel_at_period_end") return "rounded-full bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700";
  if (status === "past_due") return "rounded-full bg-red-50 px-2 py-1 text-xs font-semibold text-red-700";
  return "rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-500";
});

const formatDate = (value?: string) => {
  if (!value) return "";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium" }).format(new Date(value));
};

const loadBilling = async () => {
  actionError.value = "";
  try {
    const res = await api.get<BillingInfo>("/billing/me");
    billingInfo.value = res.data;
    if (res.data.billing_cycle === "annual" || res.data.billing_cycle === "monthly") {
      billingCycle.value = res.data.billing_cycle;
    }
  } catch (err) {
    console.error(err);
    actionError.value = "Não foi possível carregar os dados de cobrança.";
  }
};

const cancelSubscription = async () => {
  if (!billingInfo.value || billingInfo.value.plan === "free") return;

  const ok = window.confirm("Cancelar a renovação ao fim do ciclo? Você continuará com acesso até a data já paga.");
  if (!ok) return;

  actionLoading.value = true;
  actionError.value = "";
  actionMessage.value = "";

  try {
    await api.post("/billing/cancel");
    await loadBilling();
    actionMessage.value = "Renovação cancelada. Você manterá o acesso até o fim do ciclo atual.";
  } catch (err) {
    console.error(err);
    actionError.value = "Não foi possível cancelar a assinatura. Tente novamente.";
  } finally {
    actionLoading.value = false;
  }
};

const downgradeToFree = async () => {
  if (!billingInfo.value || billingInfo.value.plan === "free") return;

  const ok = window.confirm("Deseja voltar imediatamente ao plano gratuito? Os recursos dos planos pagos serão removidos.");
  if (!ok) return;

  actionLoading.value = true;
  actionError.value = "";
  actionMessage.value = "";

  try {
    await api.post("/billing/change-plan", { plan: "free" });
    await authStore.fetchProfile();
    await loadBilling();
    actionMessage.value = "Downgrade concluído. Agora você está no plano gratuito.";
  } catch (err) {
    console.error(err);
    actionError.value = "Não foi possível realizar o downgrade. Tente novamente.";
  } finally {
    actionLoading.value = false;
  }
};

onMounted(() => {
  loadBilling();
});
</script>
