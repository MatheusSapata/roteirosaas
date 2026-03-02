<template>
  <div class="bg-white text-slate-900">
    <section class="relative overflow-hidden bg-[#061d1d] text-white">
  <div class="absolute inset-0">
    <div class="absolute inset-0 bg-gradient-to-br from-emerald-700/95 via-emerald-500/90 to-cyan-500/80"></div>
    <img
      class="h-full w-full object-cover opacity-25 mix-blend-overlay"
      src="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80"
      alt="Mapa ilustrativo"
    />
  </div>

  <div class="relative mx-auto flex max-w-6xl flex-col gap-10 px-6 py-20 sm:py-24 lg:flex-row lg:items-center">
    
    <div class="flex-1">
      <p class="text-sm font-semibold uppercase tracking-[0.45em] text-emerald-100">
        Roteiro Online
      </p>

      <h1 class="mt-4 text-4xl font-black leading-tight sm:text-5xl lg:text-6xl">
        Domine as campanhas mais agressivas do seu nicho.
      </h1>

      <p class="mt-5 max-w-xl text-lg text-white/85">
        Coloque no ar novas coleções, páginas e ofertas em minutos, com alertas de performance e integrações de mídia prontas.
      </p>

      <ul class="mt-6 grid gap-3 text-sm text-white/90 sm:grid-cols-2">
        <li v-for="bullet in heroBullets" :key="bullet" class="flex items-center gap-2">
          <span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-white/20 text-emerald-200">
            <svg class="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 8l3 3 7-7" />
            </svg>
          </span>
          <span>{{ bullet }}</span>
        </li>
      </ul>

      <div class="mt-8 flex flex-wrap items-center gap-4">
        <RouterLink
          to="/register"
          class="rounded-full bg-white px-10 py-3 text-base font-semibold text-emerald-700 shadow-xl shadow-emerald-900/30 transition hover:-translate-y-0.5 hover:bg-emerald-50"
        >
          Começar agora
        </RouterLink>

        <RouterLink
          to="/admin/planos"
          class="rounded-full border border-white/40 px-10 py-3 text-base font-semibold text-white transition hover:bg-white/10"
        >
          Ver painel ao vivo
        </RouterLink>
      </div>
    </div>

    <div class="flex-1">
      <div class="rounded-[36px] border border-white/15 bg-white/5 p-6 shadow-2xl shadow-emerald-900/30 backdrop-blur">
        <div class="flex items-center justify-between border-b border-white/10 pb-4">
          <p class="text-sm font-semibold uppercase tracking-[0.4em] text-white/70">
            Resultados reais
          </p>
          <span class="text-xs text-white/60">Últimos 30 dias</span>
        </div>

        <div class="mt-6 grid gap-4 sm:grid-cols-3">
          <div
            v-for="metric in heroMetrics"
            :key="metric.label"
            class="rounded-2xl border border-white/20 bg-gradient-to-b from-white/15 to-white/5 px-4 py-5 text-center"
          >
            <p class="text-2xl font-semibold text-white">
              {{ metric.value }}
            </p>
            <p class="mt-2 text-[11px] font-semibold uppercase tracking-[0.3em] text-white/70">
              {{ metric.label }}
            </p>
          </div>
        </div>

      </div>
    </div>

  </div>
</section>

    <section class="relative overflow-hidden bg-slate-50">
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-b from-white via-transparent to-white opacity-70"></div>
      <div class="relative mx-auto max-w-6xl px-6 py-20">
        <div class="grid gap-10 lg:grid-cols-2">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Por que assinar</p>
            <h2 class="mt-3 text-4xl font-bold leading-snug text-slate-900">
              Tudo o que uma agência moderna precisa para vender roteiros online.
            </h2>
            <p class="mt-4 text-base text-slate-600">
              Enquanto outras equipes dependem de designers, planilhas e dezenas de ferramentas, você centraliza editor,
              métricas e integrações em um único painel. Mais tempo para vender, menos complicação operacional.
            </p>
            <div class="mt-8 grid gap-4 sm:grid-cols-2">
              <div
                v-for="stat in advantageStats"
                :key="stat.label"
                class="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-lg shadow-emerald-100/40 backdrop-blur"
              >
                <p class="text-3xl font-black text-slate-900">{{ stat.value }}</p>
                <p class="text-sm text-slate-500">{{ stat.label }}</p>
              </div>
            </div>
          </div>
          <div class="grid gap-5 sm:grid-cols-2">
            <article
              v-for="item in advantages"
              :key="item.title"
              class="rounded-3xl border border-slate-100 bg-white p-5 shadow-md shadow-slate-200/60 transition hover:-translate-y-1 hover:border-emerald-200"
            >
              <div class="flex items-center gap-3">
                <div :class="['rounded-2xl p-3 text-emerald-700', item.accent]">
                  <svg
                    v-if="item.icon === 'layout'"
                    class="h-6 w-6"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                  >
                    <rect x="3" y="3" width="7" height="7" rx="2" />
                    <rect x="14" y="3" width="7" height="4" rx="2" />
                    <rect x="14" y="9" width="7" height="12" rx="2" />
                    <rect x="3" y="12" width="7" height="9" rx="2" />
                  </svg>
                  <svg
                    v-else-if="item.icon === 'chart'"
                    class="h-6 w-6"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                  >
                    <path d="M4 19V5" />
                    <path d="M9 19V9" />
                    <path d="M14 19V3" />
                    <path d="M19 19v-8" />
                  </svg>
                  <svg
                    v-else-if="item.icon === 'integrations'"
                    class="h-6 w-6"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                  >
                    <circle cx="7" cy="12" r="3" />
                    <circle cx="17" cy="5" r="3" />
                    <circle cx="17" cy="19" r="3" />
                    <path d="M9.5 10.5l5-4" />
                    <path d="M9.5 13.5l5 4" />
                  </svg>
                  <svg
                    v-else
                    class="h-6 w-6"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                  >
                    <path d="M12 2v20" />
                    <path d="M17 7H9.5a4.5 4.5 0 0 0 0 9H17" />
                  </svg>
                </div>
                <div>
                  <p class="text-lg font-semibold text-slate-900">{{ item.title }}</p>
                  <p class="text-sm text-slate-500">{{ item.caption }}</p>
                </div>
              </div>
              <p class="mt-4 text-sm text-slate-600">{{ item.description }}</p>
              <div class="mt-4 flex items-center gap-2 text-xs font-semibold text-emerald-600">
                <span class="inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                {{ item.highlight }}
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>

    <section class="relative overflow-hidden bg-slate-50">
      <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.08),_transparent_55%)]"></div>
      <div class="relative mx-auto max-w-6xl px-6 py-20">
        <div class="flex flex-col gap-4 text-center">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Agilidade e qualidade</p>
          <h2 class="text-3xl font-bold">Veja o que ganha ao criar roteiros dentro do Roteiro Online</h2>
        </div>
        <div class="mt-10 grid gap-6 lg:grid-cols-2">
          <div class="rounded-[32px] border border-emerald-200 bg-white p-8 shadow-xl shadow-emerald-100/50">
            <div class="flex items-center gap-3">
              <span class="rounded-full bg-emerald-100 px-4 py-1 text-xs font-semibold text-emerald-700">Vantagens</span>
              <p class="text-sm text-emerald-600">Por que as agências escolhem o Roteiro Online</p>
            </div>
            <ul class="mt-6 space-y-4">
              <li v-for="pro in pros" :key="pro" class="flex items-start gap-3 text-sm text-slate-700">
                <span class="mt-1 inline-flex h-3 w-3 items-center justify-center rounded-full bg-emerald-500">
                  <svg class="h-2 w-2 text-white" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 8l3 3 7-7" />
                  </svg>
                </span>
                <span>{{ pro }}</span>
              </li>
            </ul>
          </div>
          <div class="rounded-[32px] border border-rose-200 bg-white p-8 shadow-xl shadow-rose-100/40">
            <div class="flex items-center gap-3">
              <span class="rounded-full bg-rose-100 px-4 py-1 text-xs font-semibold text-rose-600">Sem o Roteiro</span>
              <p class="text-sm text-rose-500">Riscos e custos do caminho manual</p>
            </div>
            <ul class="mt-6 space-y-4">
              <li v-for="con in cons" :key="con" class="flex items-start gap-3 text-sm text-slate-700">
                <span class="mt-1 inline-flex h-3 w-3 items-center justify-center rounded-full bg-rose-500">
                  <svg class="h-2 w-2 text-white" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 4l8 8M12 4l-8 8" />
                  </svg>
                </span>
                <span>{{ con }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section class="relative overflow-hidden bg-gradient-to-b from-emerald-50 via-white to-white">
      <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.15),_transparent_55%)]"></div>
      <div class="relative mx-auto max-w-6xl px-6 py-20">
        <div class="flex flex-col gap-4 text-center">
          <p class="text-xs font-semibold uppercase tracking-[0.4em] text-emerald-500">Biblioteca completa</p>
          <h2 class="text-3xl font-bold text-slate-900">Seções profissionais para cada etapa do funil.</h2>
          <p class="text-sm text-slate-600">
            Construa narrativas completas: apresentação, prova social, argumentação de preço e fechamento.
          </p>
        </div>
        <div class="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <article
            v-for="(section, index) in builderSections"
            :key="section.title"
            class="relative rounded-[28px] border border-emerald-100 bg-white p-6 shadow-lg shadow-emerald-100 transition hover:-translate-y-1 hover:shadow-2xl"
          >
            <div class="flex items-center gap-4">
              <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
                <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path :d="section.icon" />
                </svg>
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">
                  {{ section.badge }}
                </p>
                <p class="text-lg font-semibold text-slate-900">{{ section.title }}</p>
              </div>
            </div>
            <p class="mt-4 text-sm text-slate-600">{{ section.description }}</p>
            <span class="absolute right-6 top-6 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-600">
              #{{ index + 1 }}
            </span>
          </article>
        </div>
      </div>
    </section>

    <section class="bg-slate-50">
      <div class="mx-auto max-w-6xl px-6 py-20">
        <div class="flex flex-col gap-4 text-center">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Planos para cada fase</p>
          <h2 class="text-3xl font-bold">Escolha o plano ideal e economize no anual.</h2>
        </div>
        <div class="mt-8 flex justify-center">
          <div class="inline-flex rounded-full bg-slate-100 p-1 text-xs font-semibold text-slate-500 shadow-inner">
            <button
              type="button"
              class="rounded-full px-5 py-2 transition"
              :class="billingPeriod === 'monthly' ? 'bg-white text-slate-900 shadow' : ''"
              @click="billingPeriod = 'monthly'"
            >
              Mensal
            </button>
            <button
              type="button"
              class="rounded-full px-5 py-2 transition"
              :class="billingPeriod === 'annual' ? 'bg-white text-slate-900 shadow' : ''"
              @click="billingPeriod = 'annual'"
            >
              Anual
            </button>
          </div>
        </div>
        <p class="mt-3 text-center text-sm text-slate-500">Economize escolhendo o plano anual</p>
        <div class="mt-10 grid gap-5 lg:grid-cols-4">
          <article
            v-for="plan in displayPlans"
            :key="plan.name"
            :class="[
            'flex h-full flex-col rounded-[32px] border bg-white p-6 shadow-sm transition',
            plan.highlight ? 'border-emerald-300 shadow-lg ring-2 ring-emerald-100' : 'border-slate-100'
          ]"
        >
          <span
            class="inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wide"
            :class="plan.tagColor"
          >
            {{ plan.tag }}
          </span>
          <div class="mt-4 text-xs font-semibold uppercase tracking-[0.4em] text-slate-400">
            {{ plan.category }}
          </div>
          <h3 class="mt-1 text-2xl font-bold text-slate-900">{{ plan.name }}</h3>
          <p class="mt-1 text-sm text-slate-500">{{ plan.description }}</p>
          <div class="mt-6 text-3xl font-black text-slate-900">
            <span v-if="plan.oldPrice" class="mr-2 text-base font-medium text-slate-400 line-through">{{ plan.oldPrice }}</span>
            {{ plan.price }}
            <span class="text-base font-normal text-slate-500">/{{ billingPeriod === 'annual' ? "ano" : "mês" }}</span>
          </div>
          <p class="mt-1 text-sm font-semibold text-emerald-600" v-if="plan.savings">{{ plan.savings }}</p>
          <p class="text-sm text-slate-500" v-else>{{ plan.tagline }}</p>
          <ul class="mt-6 flex flex-1 flex-col space-y-3 text-sm text-slate-700">
            <li v-for="feature in plan.features" :key="feature" class="flex items-start gap-2">
              <svg class="mt-1 h-4 w-4 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 13l4 4L19 7" />
              </svg>
              <span>{{ feature }}</span>
            </li>
          </ul>
          <RouterLink
            to="/register"
            class="mt-8 flex items-center justify-center rounded-full px-6 py-3 text-center text-sm font-semibold transition"
            :class="plan.ctaColor"
          >
            {{ plan.cta }}
          </RouterLink>
          <p class="mt-2 text-center text-xs text-slate-400">{{ plan.footer }}</p>
        </article>
        </div>
      </div>
    </section>

    <section class="bg-slate-50">
      <div class="mx-auto max-w-5xl px-6 py-20">
        <div class="flex flex-col gap-4 text-center">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">FAQ</p>
          <h2 class="text-3xl font-bold">Dúvidas frequentes</h2>
          <p class="text-sm text-slate-600">Transparência total antes do seu cadastro.</p>
        </div>
        <dl class="mt-12 space-y-4">
          <div v-for="item in faq" :key="item.question" class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
            <dt class="text-base font-semibold text-slate-900">{{ item.question }}</dt>
            <dd class="mt-2 text-sm text-slate-600">{{ item.answer }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <section class="relative overflow-hidden">
      <div class="absolute inset-0">
        <div class="absolute inset-0 bg-gradient-to-br from-emerald-700 via-emerald-600 to-emerald-500"></div>
        <img
          class="h-full w-full object-cover opacity-20 mix-blend-overlay"
          src="https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1400&q=80"
          alt="Equipe planejando viagens"
        />
      </div>
      <div class="relative mx-auto max-w-5xl px-6 py-20 text-white">
        <div class="rounded-[36px] border border-white/10 bg-white/10 p-10 shadow-2xl shadow-emerald-900/40 backdrop-blur">
          <div class="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div class="max-w-2xl">
              <p class="text-xs font-semibold uppercase tracking-[0.4em] text-emerald-100">Hora da virada</p>
              <h2 class="mt-3 text-3xl font-bold lg:text-4xl">Publique seu próximo roteiro antes da concorrência.</h2>
              <p class="mt-3 text-base text-white/80">
                Cadastre-se agora, importe seus ativos e tenha uma landing page pronta ainda hoje. Cada clique é
                monitorado, cada teste A/B fica documentado e todos os times visualizam os resultados em um único lugar.
              </p>
            </div>
            <RouterLink
              to="/register"
              class="inline-flex items-center justify-center rounded-full bg-white px-10 py-3 text-lg font-semibold text-emerald-700 shadow-xl shadow-emerald-900/40 transition hover:-translate-y-0.5 hover:bg-emerald-50"
            >
              Criar conta gratuita
            </RouterLink>
          </div>
          <div class="mt-8 grid gap-4 sm:grid-cols-3">
            <div v-for="metric in heroMetrics" :key="`cta-${metric.label}`" class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-2xl font-black">{{ metric.value }}</p>
              <p class="text-sm text-white/80">{{ metric.label }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

const heroMetrics = [
  { label: "Campanhas montadas por mês", value: "2x mais rápidas" },
  { label: "Economia média em ferramentas", value: "Até 45%" },
  { label: "Satisfação dos viajantes", value: "NPS 92" }
];

const heroBullets = [
  "Editor visual com templates agressivos",
  "Alertas automáticos de queda e alta de performance",
  "Integrações Meta, GA e WhatsApp nativas",
  "Checkout e billing integrados ao painel"
];

const advantageStats = [
  { label: "Tempo médio para publicar um roteiro completo", value: "15 min" },
  { label: "Agências que migraram em busca de agilidade", value: "+320" },
  { label: "Leads captados pelos clientes nos últimos 30 dias", value: "18k+" },
  { label: "Economia em ferramentas extras", value: "até 45%" }
];

const advantages = [
  {
    title: "Editor visual completo",
    caption: "Layouts premium com blocos inteligentes",
    description: "Monte seções como itinerário, depoimentos, preços e FAQ com blocos responsivos e personalizáveis.",
    highlight: "Adicione CTA, mídia e cores em segundos.",
    icon: "layout",
    accent: "bg-emerald-50"
  },
  {
    title: "Métricas em tempo real",
    caption: "Veja o que converte na hora",
    description: "Descubra visitas, cliques e conversões por página e faça ajustes antes da concorrência.",
    highlight: "Alertas mostram tendência de queda ou crescimento.",
    icon: "chart",
    accent: "bg-lime-50"
  },
  {
    title: "Integrações nativas",
    caption: "Pixels, WhatsApp e automações",
    description: "Ative pixels Meta/Google e monitore CTAs. O sistema envia os eventos sem plugins externos.",
    highlight: "Crie campanhas de remarketing com 1 clique.",
    icon: "integrations",
    accent: "bg-cyan-50"
  },
  {
    title: "Planos flexíveis",
    caption: "Escale apenas quando precisar",
    description: "Comece grátis, teste o trial premium e faça upgrade quando sua carteira exigir.",
    highlight: "Downgrade e cancelamento direto no painel.",
    icon: "switch",
    accent: "bg-emerald-50"
  }
];

const pros = [
  "Páginas consistentes com a identidade da sua agência.",
  "Duplicação rápida de roteiros para novas campanhas.",
  "Dashboard com alertas de performance e tendência.",
  "Checkout integrado para controlar seus planos e custos."
];

const cons = [
  "Perder tempo com designers/freelancers a cada campanha.",
  "Ter métricas espalhadas em planilhas e sem precisão.",
  "Dificuldade para manter o mesmo padrão visual em vários roteiros.",
  "Custos somados de diversas ferramentas isoladas."
];

type Plan = {
  tag: string;
  tagColor: string;
  category: string;
  name: string;
  description: string;
  price: string;
  oldPrice?: string;
  savings?: string;
  tagline?: string;
  features: string[];
  cta: string;
  ctaColor: string;
  footer: string;
  highlight?: boolean;
};

const billingPeriod = ref<"monthly" | "annual">("annual");

const planMatrix: Record<"monthly" | "annual", Plan[]> = {
  annual: [
    {
      tag: "Seu plano atual",
      tagColor: "bg-emerald-50 text-emerald-600 border border-emerald-100",
      category: "Começo",
      name: "Plano Começo",
      description: "Para quem está começando a organizar seus roteiros online",
      price: "R$ 0,00",
      tagline: "Ideal para dar os primeiros passos",
      features: [
        "1 roteiro online publicado",
        "Editor simples e fácil de usar",
        "Layout pronto para a agência",
        "Relatório básico de cliques"
      ],
      cta: "Plano atual",
      ctaColor: "bg-slate-200 text-slate-700 hover:bg-slate-300",
      footer: "Publique seu primeiro roteiro sem custos."
    },
    {
      tag: "Recomendado para crescer",
      tagColor: "bg-emerald-50 text-emerald-600 border border-emerald-100",
      category: "Profissional",
      name: "Plano Profissional",
      description: "Para quem já vende excursões e quer mais presença online",
      oldPrice: "R$ 598,80",
      price: "R$ 499,00",
      savings: "Equivalente a R$ 41,58/mês",
      features: [
        "Até 5 roteiros online ativos",
        "Seções ilimitadas dentro de cada roteiro",
        "Salvar modelo padrão para copiar em novas viagens",
        "Conectar 1 pixel (Facebook ou Google)",
        "Componentes extras (depoimentos, contagem regressiva, FAQ)"
      ],
      cta: "Quero organizar minhas viagens",
      ctaColor: "bg-emerald-600 text-white hover:bg-emerald-700",
      footer: "Perfeito para quem já tem grupos rodando.",
      highlight: true
    },
    {
      tag: "Mais popular",
      tagColor: "bg-orange-50 text-orange-600 border border-orange-200",
      category: "Agência",
      name: "Plano Agência",
      description: "Para agências que querem vender todos os meses com previsibilidade",
      oldPrice: "R$ 958,80",
      price: "R$ 799,00",
      savings: "Economize quase 2 meses",
      features: [
        "Até 10 roteiros online ativos",
        "Conectar até 3 pixels",
        "Duplicação rápida de páginas",
        "Todos os recursos do Profissional"
      ],
      cta: "Quero escalar minhas vendas",
      ctaColor: "bg-orange-500 text-white hover:bg-orange-600",
      footer: "Mantenha vários destinos ativos ao mesmo tempo."
    },
    {
      tag: "Para operação avançada",
      tagColor: "bg-indigo-50 text-indigo-600 border border-indigo-200",
      category: "Escala",
      name: "Plano Escala",
      description: "Para agências que operam múltiplos grupos e querem dominar sua região",
      oldPrice: "R$ 1.558,80",
      price: "R$ 1.299,00",
      tagline: "Ideal para operação contínua",
      features: [
        "Até 15 roteiros online ativos",
        "Todos os recursos dos planos anteriores",
        "Ideal para múltiplos destinos simultâneos",
        "Página adicional: R$ 20,00 por roteiro extra"
      ],
      cta: "Quero estruturar minha escala",
      ctaColor: "bg-indigo-600 text-white hover:bg-indigo-700",
      footer: "Pensado para agências com vários grupos ativos."
    }
  ],
  monthly: [
    {
      tag: "Seu plano atual",
      tagColor: "bg-emerald-50 text-emerald-600 border border-emerald-100",
      category: "Começo",
      name: "Plano Começo",
      description: "Para quem está começando a organizar seus roteiros online",
      price: "R$ 0,00",
      tagline: "Ideal para dar os primeiros passos",
      features: [
        "1 roteiro online publicado",
        "Editor simples e fácil de usar",
        "Layout pronto para a agência",
        "Relatório básico de cliques"
      ],
      cta: "Plano atual",
      ctaColor: "bg-slate-200 text-slate-700 hover:bg-slate-300",
      footer: "Publique seu primeiro roteiro sem custos."
    },
    {
      tag: "Recomendado para crescer",
      tagColor: "bg-emerald-50 text-emerald-600 border border-emerald-100",
      category: "Profissional",
      name: "Plano Profissional",
      description: "Para quem já vende excursões e quer mais presença online",
      price: "R$ 59,90",
      tagline: "Mais recursos com pagamento mensal",
      features: [
        "Até 5 roteiros online ativos",
        "Seções ilimitadas dentro de cada roteiro",
        "Salvar modelo padrão para copiar em novas viagens",
        "Conectar 1 pixel (Facebook ou Google)",
        "Componentes extras (depoimentos, contagem regressiva, FAQ)"
      ],
      cta: "Quero organizar minhas viagens",
      ctaColor: "bg-emerald-600 text-white hover:bg-emerald-700",
      footer: "Perfeito para quem já tem grupos rodando.",
      highlight: true
    },
    {
      tag: "Mais popular",
      tagColor: "bg-orange-50 text-orange-600 border border-orange-200",
      category: "Agência",
      name: "Plano Agência",
      description: "Para agências que querem vender todos os meses com previsibilidade",
      price: "R$ 89,90",
      tagline: "Mais usado pelas agências",
      features: [
        "Até 10 roteiros online ativos",
        "Conectar até 3 pixels",
        "Duplicação rápida de páginas",
        "Todos os recursos do Profissional"
      ],
      cta: "Quero escalar minhas vendas",
      ctaColor: "bg-orange-500 text-white hover:bg-orange-600",
      footer: "Mantenha vários destinos ativos ao mesmo tempo."
    },
    {
      tag: "Para operação avançada",
      tagColor: "bg-indigo-50 text-indigo-600 border border-indigo-200",
      category: "Escala",
      name: "Plano Escala",
      description: "Para agências que operam múltiplos grupos e querem dominar sua região",
      price: "R$ 139,90",
      tagline: "Ideal para operação contínua",
      features: [
        "Até 15 roteiros online ativos",
        "Todos os recursos dos planos anteriores",
        "Ideal para múltiplos destinos simultâneos",
        "Página adicional: R$ 20,00 por roteiro extra"
      ],
      cta: "Quero estruturar minha escala",
      ctaColor: "bg-indigo-600 text-white hover:bg-indigo-700",
      footer: "Pensado para agências com vários grupos ativos."
    }
  ]
};

const displayPlans = computed(() => planMatrix[billingPeriod.value]);

const faq = [
  {
    question: "Posso testar antes de contratar?",
    answer: "Sim. Crie sua conta gratuita e, quando quiser, faça o upgrade para o plano que mais se encaixar a sua necessidade."
  },
  {
    question: "Preciso de desenvolvedor para publicar?",
    answer: "Não. O editor cuida de toda a montagem. Basta escrever o conteúdo e clicar em Publicar."
  },
  {
    question: "É possível integrar com meus anúncios?",
    answer: "Sim. Os planos pagos liberam pixels Meta e Google. O sistema dispara pageviews e eventos de CTA automaticamente."
  }
];

const builderSections = [
  {
    title: "Hero c/ headline",
    badge: "Topo",
    description: "Bloco inicial com vídeo, imagem ou carrossel de destaques. Inclui CTA duplo, selo de confiança e contagem regressiva opcional.",
    icon: "M4 12h16M12 4v16"
  },
  {
    title: "Estrutura de roteiro",
    badge: "Conteúdo",
    description: "Monte o itinerário dia a dia com cards expansivos, ícones de transporte e notas de operação.",
    icon: "M4 6h16M4 12h10M4 18h7"
  },
  {
    title: "Matriz de preços",
    badge: "Conversão",
    description: "Tabela integrada com CTA para WhatsApp e checkout, alternância mensal/anual e destaque do plano mais vendido.",
    icon: "M4 4h16v16H4z M4 10h16"
  },
  {
    title: "Histórias & depoimentos",
    badge: "Prova social",
    description: "Slides com foto do viajante, avaliação, e CTA para compartilhar experiências em tempo real.",
    icon: "M4 6h16l-4 6 4 6H4z"
  },
  {
    title: "FAQ + contatos",
    badge: "Suporte",
    description: "Acordeões com respostas curtas, CTA para WhatsApp e links para documentos de viagem.",
    icon: "M12 5v14M5 12h14"
  },
  {
    title: "CTA final multicanal",
    badge: "Fechamento",
    description: "Bloco de fechamento com CTA principal, botão secundário e pixels prontos para medir o clique.",
    icon: "M4 5h16M4 12h16M4 19h16"
  }
];
</script>



