<template>
  <div class="lp public-tokens">
    <!-- 01 Capa: texto à esquerda, vídeo quadrado à direita (no celular, o vídeo fica entre o texto e os botões). -->
    <section class="lp-sec lp-hero">
      <div class="lp-wrap lp-hero-grid">
        <div class="lp-hero-copy">
          <img :src="logo" alt="Roteiro Online" class="lp-logo" width="240" height="72" />
          <span class="lp-pill"><Sparkles :size="14" aria-hidden="true" />Aumente a sua conversão!</span>
          <h1 class="lp-h1">Seu cliente não compra o que <span class="is-brand">não consegue imaginar!</span></h1>
          <p class="lp-lead">
            Crie páginas profissionais em minutos e faça seu cliente
            <strong>sentir o valor antes mesmo de saber o preço.</strong>
          </p>
        </div>
        <div class="lp-hero-video">
          <iframe
            :src="HERO_VIDEO"
            title="Roteiro Online em funcionamento"
            allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture"
            allowfullscreen
            loading="lazy"
          ></iframe>
        </div>
        <div class="lp-hero-actions">
          <div class="lp-ctas">
            <a href="#planos" class="lp-btn" @click.prevent="goToPlans">Quero ver os planos <ArrowRight :size="18" aria-hidden="true" /></a>
            <a :href="DEMO_URL" class="lp-btn-ghost" target="_blank" rel="noopener">Agendar demonstração</a>
          </div>
          <p class="lp-note"><ShieldCheck :size="15" aria-hidden="true" /><span>7 dias de garantia · Sem fidelidade<span class="lp-hide-sm"> · Cancele quando quiser</span></span></p>
        </div>
      </div>
    </section>

    <!-- 02 Números -->
    <section class="lp-sec lp-metrics-sec">
      <div class="lp-wrap lp-metrics">
        <div v-for="metric in METRICS" :key="metric.label" class="lp-metric">
          <div class="lp-metric-num">{{ metric.value }}</div>
          <div class="lp-metric-lbl">{{ metric.label }}</div>
        </div>
      </div>
    </section>

    <!-- 03 Dores -->
    <section class="lp-sec is-soft">
      <div class="lp-wrap">
        <h2 class="lp-h2">
          É sério... mandando <span class="is-red">textão no WhatsApp,</span><br />
          é bem provável que...
        </h2>
        <div class="lp-pains">
          <div v-for="pain in PAINS" :key="pain.title" class="lp-pain">
            <span class="lp-pain-ico" aria-hidden="true"><component :is="pain.icon" :size="20" /></span>
            <div>
              <h3>{{ pain.title }}</h3>
              <p>{{ pain.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 04 Funcionalidades -->
    <section class="lp-sec">
      <div class="lp-wrap">
        <p class="lp-kicker">Funcionalidades</p>
        <h2 class="lp-h2"><span class="is-brand">Crie páginas profissionais</span> mesmo sem saber nada de design</h2>
        <p class="lp-swipe" aria-hidden="true">Arraste para o lado para ver mais</p>
        <div class="lp-feats lp-rail">
          <div v-for="feat in FEATURES" :key="feat.title" class="lp-feat">
            <div class="lp-feat-head">
              <span class="lp-ico" aria-hidden="true"><component :is="feat.icon" :size="18" /></span>
              <h3>{{ feat.title }}</h3>
            </div>
            <p>{{ feat.text }}</p>
            <span v-if="feat.tag" class="lp-tag">{{ feat.tag }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 05 Exemplos reais -->
    <section class="lp-sec is-soft">
      <div class="lp-wrap">
        <p class="lp-kicker">Exemplos reais</p>
        <h2 class="lp-h2">Roteiros criados por <span class="is-brand">pessoas como você!</span></h2>
        <p class="lp-sub">Sem designer, sem programação. Clique e veja o roteiro completo do mesmo jeito que o passageiro recebe.</p>
        <p class="lp-swipe" aria-hidden="true">Arraste para o lado para ver mais</p>
        <div class="lp-exs lp-rail">
          <article v-for="example in EXAMPLES" :key="example.title" class="lp-ex">
            <img :src="example.image" :alt="`Roteiro ${example.title}`" loading="lazy" decoding="async" width="760" height="384" />
            <div class="lp-ex-body">
              <p class="lp-ex-meta"><span class="lp-ex-badge">{{ example.badge }}</span>{{ example.agency }}</p>
              <h3 class="lp-ex-title">{{ example.title }}</h3>
              <p class="lp-ex-desc">{{ example.text }}</p>
              <p class="lp-ex-quote">“{{ example.quote }}”</p>
              <a :href="example.url" class="lp-ex-link" target="_blank" rel="noopener">Abrir roteiro <ArrowUpRight :size="16" aria-hidden="true" /></a>
            </div>
          </article>
        </div>
        <p class="lp-closer">A sua apresentação pode ter o mesmo nível em poucos minutos.</p>
      </div>
    </section>

    <!-- 06 Como funciona -->
    <section class="lp-sec">
      <div class="lp-wrap">
        <p class="lp-kicker">Como funciona</p>
        <h2 class="lp-h2">Onboarding em <span class="is-brand">menos de 3 minutos</span></h2>
        <div class="lp-steps">
          <div v-for="(step, index) in STEPS" :key="step.title" class="lp-step">
            <span class="lp-step-num">{{ index + 1 }}</span>
            <div>
              <h3>{{ step.title }}</h3>
              <p>{{ step.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 07 Mais fácil que o Canva -->
    <section class="lp-sec is-soft">
      <div class="lp-wrap">
        <h2 class="lp-h2">Mais fácil que <span class="is-brand">editar no Canva!</span></h2>
        <p class="lp-sub lp-canva-sub">Veja o editor em 40 segundos: escolher uma seção, editar, conferir no celular e publicar.</p>
        <div class="lp-canva">
          <div class="lp-canva-visual">
            <!-- Gravado do editor de verdade por tools/help-media/lp-editor.mjs. -->
            <video
              ref="editorVideo"
              :poster="editorPoster"
              autoplay
              muted
              loop
              playsinline
              preload="metadata"
              aria-label="Animação do editor: escolher uma seção pronta, editar o texto, trocar o visual, ver no celular, pedir ao Assistente IA e publicar"
            >
              <source :src="editorWebm" type="video/webm" />
              <source :src="editorMp4" type="video/mp4" />
            </video>
          </div>
          <ul class="lp-checks">
            <li v-for="item in EASIER" :key="item"><span class="lp-check" aria-hidden="true"><Check :size="14" /></span>{{ item }}</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 08 Planos -->
    <section id="planos" class="lp-sec lp-sec-plans">
      <div class="lp-wrap">
        <p class="lp-kicker">Escolha seu plano</p>
        <h2 class="lp-h2">Comece agora e publique seu <span class="is-brand">primeiro roteiro hoje</span></h2>
        <p class="lp-sub">
          Todos os planos têm <strong>7 dias de garantia incondicional</strong>. Sem fidelidade, sem letras miúdas.
        </p>
        <p class="lp-swipe" aria-hidden="true">Arraste para o lado para ver os outros planos</p>
        <div class="lp-plans lp-rail">
          <article v-for="plan in PLANS" :key="plan.name" class="lp-plan" :class="{ 'is-feat': plan.featured }">
            <span class="lp-plan-tag">{{ plan.tag }}</span>
            <h3 class="lp-plan-name">{{ plan.name }}</h3>
            <p class="lp-plan-pitch">{{ plan.pitch }}</p>
            <div class="lp-plan-price">
              <span class="cur">R$</span><span class="val">{{ plan.price }}</span><span class="per">/mês</span>
            </div>
            <p class="lp-plan-per">{{ plan.perItinerary }}</p>
            <ul class="lp-plan-feats">
              <li v-for="item in plan.features" :key="item"><Check :size="14" aria-hidden="true" />{{ item }}</li>
              <li v-for="mod in plan.modules" :key="mod.title" class="is-mod">
                <Sparkles :size="14" aria-hidden="true" /><span><strong>{{ mod.title }}:</strong> {{ mod.text }}</span>
              </li>
            </ul>
            <RouterLink :to="`/checkout/${plan.offer}`" class="lp-plan-cta">{{ plan.cta }}</RouterLink>
          </article>
        </div>
        <p class="lp-note">Pague no cartão ou com Pix automático · Sem fidelidade · Cancele quando quiser · Reembolso em até 7 dias</p>
      </div>
    </section>

    <!-- 09 Garantia -->
    <section class="lp-sec is-soft lp-sec-guarantee">
      <div class="lp-wrap lp-guarantee">
        <span class="lp-guarantee-ico" aria-hidden="true"><ShieldCheck :size="30" /></span>
        <div>
          <p class="lp-kicker">Garantia de 7 dias</p>
          <h3>Teste sem risco</h3>
          <p>
            Você entra, usa, cria seu primeiro roteiro e valida na prática. Se entender que não é para o seu momento, a gente
            devolve 100% do valor. Sem burocracia, sem letras miúdas, sem justificativa obrigatória.
          </p>
        </div>
      </div>
    </section>

    <!-- 10 Perguntas -->
    <section class="lp-sec lp-sec-faq">
      <div class="lp-wrap">
        <p class="lp-kicker">Ainda tem dúvida?</p>
        <h2 class="lp-h2">Perguntas que a gente <span class="is-brand">mais escuta</span></h2>
        <div class="lp-faq" :class="{ 'is-all': faqAll }">
          <details v-for="item in FAQ" :key="item.q">
            <summary>{{ item.q }}<ChevronDown :size="18" aria-hidden="true" /></summary>
            <p>
              {{ item.a }}
              <template v-if="item.strong"><strong>{{ item.strong }}</strong> {{ item.after }}</template>
              <template v-if="item.demo">
                <a :href="DEMO_URL" target="_blank" rel="noopener">Agende uma demonstração aqui</a> {{ item.after }}
              </template>
            </p>
          </details>
        </div>
        <button v-if="!faqAll" type="button" class="lp-faq-more" @click="faqAll = true">
          Ver todas as perguntas <ChevronDown :size="16" aria-hidden="true" />
        </button>
      </div>
    </section>

    <!-- 11 Chamada final -->
    <section class="lp-sec lp-final">
      <div class="lp-wrap lp-final-inner">
        <h2 class="lp-h2 lp-final-title">Publique hoje mesmo o seu <span class="is-mint">primeiro roteiro.</span></h2>
        <p class="lp-final-sub">
          Escolha seu plano, entre na plataforma e publique em menos de 30 minutos. Se não gostar, devolvemos 100% do valor em 7 dias.
        </p>
        <div class="lp-ctas">
          <a href="#planos" class="lp-btn lp-btn-mint" @click.prevent="goToPlans">Quero ver os planos <ArrowRight :size="18" aria-hidden="true" /></a>
          <a :href="DEMO_URL" class="lp-btn-ghost lp-btn-ghost-dark" target="_blank" rel="noopener">Agendar demonstração</a>
        </div>
        <p class="lp-final-note">Sem fidelidade · 7 dias de garantia · Cancelamento simples</p>
        <RouterLink to="/login" class="lp-login">Já é cliente? Entrar</RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  ChartColumn,
  Check,
  ChevronDown,
  Copy,
  CreditCard,
  EyeOff,
  Ghost,
  Globe,
  Images,
  Link,
  Magnet,
  MessageCircle,
  MousePointerClick,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Timer,
  TrendingDown
} from "lucide-vue-next";
import logo from "../../assets/lp/logo.webp";
import editorMp4 from "../../assets/lp/editor.mp4";
import editorWebm from "../../assets/lp/editor.webm";
import editorPoster from "../../assets/lp/editor-poster.webp";
import exemploAbrolhos from "../../assets/lp/exemplo-abrolhos.webp";
import exemploFoz from "../../assets/lp/exemplo-foz.webp";
import exemploItalia from "../../assets/lp/exemplo-italia.webp";

/**
 * Página de vendas do Roteiro Online, trazida do Elementor (viajeon.com/roteiroonline1)
 * para dentro do sistema. Os planos levam direto ao checkout próprio (/checkout/:offerKey).
 */
const HERO_VIDEO = "https://player-vz-19330b59-441.tv.pandavideo.com.br/embed/?v=13897fe0-22c6-420f-ad7c-523e37f8fd7f";
const DEMO_URL = "https://cal.com/viajeon/roteiro-online";
const META_PIXEL_ID = "1584327072834789";
const PAGE_TITLE = "Roteiro Online | Páginas de roteiro que vendem";
const PAGE_DESCRIPTION =
  "Crie páginas profissionais de roteiro em minutos e faça seu cliente sentir o valor antes mesmo de saber o preço.";

const METRICS = [
  { value: "+200", label: "Agências ativas" },
  { value: "+800", label: "Páginas criadas" },
  { value: "3 min", label: "Pra se cadastrar" },
  { value: "7 dias", label: "Garantia total" }
];

const PAINS = [
  {
    icon: Ghost,
    title: "suas cotações estejam sumindo",
    text: "O lead pede, você manda, ele some. Sem página profissional, a cotação vira só mais uma mensagem perdida no WhatsApp."
  },
  {
    icon: EyeOff,
    title: "seu cliente não vê o real valor",
    text: "Quando o passageiro vê só o preço, compara por preço. Quando enxerga a experiência completa, compra a experiência."
  },
  {
    icon: TrendingDown,
    title: "você esteja concorrendo por preço",
    text: "Se a apresentação não sustenta o valor, o único argumento que sobra é desconto. Apresente melhor, venda pelo preço certo."
  }
];

const FEATURES = [
  {
    icon: MousePointerClick,
    title: "Editor intuitivo, visual e prático",
    text: "Blocos prontos de hero, itinerário, inclusos, investimento e CTA. Não precisa de conhecimento técnico pra usar."
  },
  {
    icon: CalendarDays,
    title: "Itinerário dia a dia interativo",
    text: "Cada dia vira uma aba clicável. O passageiro abre só o que quer ver, como um app de viagem."
  },
  {
    icon: MessageCircle,
    title: "Botão WhatsApp onde você quiser",
    text: "Você pode adicionar em qualquer seção, com mensagem pronta e o nome do roteiro. O lead chega no seu WhatsApp já contextualizado."
  },
  {
    icon: Images,
    title: "Galeria com carrossel",
    text: "Fotos do destino, da hospedagem e dos passeios com thumb navegável — sem peso de PDF."
  },
  {
    icon: CreditCard,
    title: "Cards de investimento flexíveis",
    text: "Adulto, criança, apto individual, duplo, triplo, categoria especial. Tantas categorias de preço quanto você precisar."
  },
  {
    icon: Timer,
    title: "Contagem regressiva automática",
    text: "Cria urgência real até a data da viagem. Sem precisar editar nada manualmente."
  },
  {
    icon: ChartColumn,
    title: "Pixel Meta e Google integrados",
    text: "Faça tráfego pago para a página e retargete quem não fechou.",
    tag: "a partir de 1 no plano profissional"
  },
  {
    icon: Magnet,
    title: "Módulo Leads",
    text: "Formulário de captação dentro do roteiro. Cada passageiro interessado vira oportunidade futura.",
    tag: "Nos planos Agência e Escala"
  },
  {
    icon: Copy,
    title: "Duplicação com um clique",
    text: "Copiou a estrutura do último roteiro? Troque o destino e publique em minutos.",
    tag: "nos planos Agência e Escala"
  },
  {
    icon: Globe,
    title: "Domínio próprio",
    text: "Publique seus roteiros no endereço da sua agência. Marca branca completa.",
    tag: "Exclusivo do plano Escala"
  },
  {
    icon: Smartphone,
    title: "100% responsivo no celular",
    text: "A maior parte dos clientes abre pelo WhatsApp. A página é pensada para o mobile primeiro."
  },
  {
    icon: Link,
    title: "Compartilhe por link, não por arquivo",
    text: "Um link. Cola no WhatsApp, no Instagram, no anúncio, no e-mail. O passageiro sempre vê a versão atualizada."
  }
];

const EXAMPLES = [
  {
    image: exemploAbrolhos,
    badge: "Ecoturismo",
    agency: "Ecoar Ecoturismo",
    title: "Abrolhos",
    text: "Expedição embarcada com baleias jubarte, mergulho e corais.",
    quote: "Arrasaram demais. Nunca pensei que pudesse ser tão fácil ter um site com todos os detalhes das nossas viagens.",
    url: "https://roteiroonline.com/ecoar-ecoturismo/abrolhos"
  },
  {
    image: exemploFoz,
    badge: "Excursão nacional",
    agency: "Status Viajar",
    title: "Foz do Iguaçu",
    text: "Roteiro completo com Cataratas, Parque das Aves e programação do grupo.",
    quote: "Antes o roteiro ficava perdido na galeria. Agora o passageiro tem uma página que pode revisitar a qualquer momento.",
    url: "https://roteiroonline.com/status/foz-do-iguacu"
  },
  {
    image: exemploItalia,
    badge: "Grupo internacional",
    agency: "Beth Tur",
    title: "Itália Magnífica",
    text: "Apresentação premium que valoriza a experiência e sustenta o ticket.",
    quote: "Agora posso apresentar meus grupos de uma forma que as pessoas entendam o valor agregado. Ficaram lindos.",
    url: "https://roteiroonline.com/beth-tur/itaia-magnifica"
  }
];

const STEPS = [
  {
    title: "Comece do zero ou use um modelo",
    text: "Cadastro em menos de 3 minutos. Comece uma página do zero ou parta de um dos nossos modelos prontos."
  },
  {
    title: "Monte seu primeiro roteiro",
    text: "Use o modelo padrão, troque fotos, textos e valores. Adicione itinerário dia a dia e botão de WhatsApp."
  },
  {
    title: "Copie o link e divulgue",
    text: "Cole no WhatsApp, no Instagram, no anúncio. Um link único que o passageiro abre, revisita e compartilha."
  }
];

const EASIER = [
  "Blocos prontos, é só trocar o conteúdo",
  "Não precisa de conhecimento técnico",
  "Publica com um clique em domínio seguro",
  "Alterou? Atualiza pra todo mundo na hora",
  "Funciona no navegador, sem instalar nada"
];

const PLANS = [
  {
    tag: "Para começar",
    name: "Profissional",
    pitch: "Para quem quer parar de mandar textão no WhatsApp para o cliente.",
    price: "49,99",
    perItinerary: "≈ R$16,66 por roteiro",
    features: [
      "Até 3 roteiros online ativos",
      "Seções ilimitadas por roteiro",
      "Modelo padrão para reutilizar",
      "1 pixel conectado (Meta ou Google)",
      "Botão de WhatsApp em cada seção",
      "Galeria de fotos com carrossel"
    ],
    modules: [],
    offer: "profissional_lp",
    cta: "Começar com o Profissional",
    featured: false
  },
  {
    tag: "Mais escolhido",
    name: "Agência",
    pitch: "Para agências que usam o roteiro online como ferramenta recorrente de vendas.",
    price: "89,99",
    perItinerary: "≈ R$8,99 por roteiro",
    features: [
      "Até 10 roteiros online ativos",
      "Duplicação rápida de páginas",
      "Até 3 pixels conectados",
      "Todos os recursos do Profissional"
    ],
    modules: [
      { title: "Módulo Leads", text: "Formulário de captação dentro do roteiro. Cada passageiro pode virar oportunidade futura." }
    ],
    offer: "agencia_lp",
    cta: "Assinar o plano Agência",
    featured: true
  },
  {
    tag: "Operação avançada",
    name: "Escala",
    pitch: "Para agências com vários grupos, campanhas e múltiplos destinos em andamento.",
    price: "129,99",
    perItinerary: "Roteiros ilimitados",
    features: ["Roteiros ilimitados", "Múltiplos destinos simultâneos", "Todos os recursos anteriores"],
    modules: [
      { title: "Módulo Leads", text: "Formulário de captação com gestão de oportunidades integrada." },
      { title: "Domínio personalizado", text: "Publique no endereço da sua própria agência. Exclusivo deste plano." }
    ],
    offer: "escala_lp",
    cta: "Começar com o Escala",
    featured: false
  }
];

type FaqItem = { q: string; a: string; strong?: string; after?: string; demo?: boolean };
const FAQ: FaqItem[] = [
  {
    q: "Preciso saber programar ou contratar um designer?",
    a: "Não. O editor é 100% visual, com blocos prontos de hero, itinerário, inclusos e investimento. É mais fácil que editar no Canva. Se você consegue mandar um textão no WhatsApp, consegue montar o roteiro."
  },
  {
    q: "Quanto tempo leva para publicar o primeiro roteiro?",
    a: "Em média 15 a 30 minutos para o primeiro. A partir do segundo, com a duplicação de páginas, você cria um novo em menos de 5 minutos trocando destino, fotos e valores."
  },
  {
    q: "Posso cancelar quando quiser?",
    a: "Pode. Não existe fidelidade. Você assina mensal, cancela mensal. E tem 7 dias de garantia: se não gostar, devolvemos 100% do valor sem justificativa obrigatória."
  },
  {
    q: "E se eu for agência de receptivo, guia ou operadora, funciona pra mim?",
    a: "Funciona. A plataforma foi desenhada para agências de excursão, operadoras, receptivos, guias e agentes de viagem. Também é usada por hotéis com day use, pousadas com roteiros para hóspedes e operadores de experiência (gastronomia, aventura, cultural, corporativo)."
  },
  {
    q: "Posso usar nos anúncios do Facebook/Instagram/Google?",
    a: "Sim. Cada roteiro tem pixel Meta e Google integrados. No plano Profissional você conecta 1 pixel. No Agência e Escala, até 3 pixels. Ideal para retargetear quem abriu o roteiro e não fechou."
  },
  {
    q: "Como o passageiro recebe o roteiro?",
    a: "Por um link único que você cola no WhatsApp, Instagram, e-mail ou anúncio. A página abre direto no navegador do celular, sem download, sem app, sem login."
  },
  {
    q: "E se eu quiser mudar o roteiro depois de publicar?",
    a: "Altera direto no editor e o link continua o mesmo. Todo mundo que já tem o link vai abrir a versão atualizada automaticamente."
  },
  {
    q: "Posso publicar no domínio da minha agência?",
    a: "Sim, no plano Escala. Você conecta seu domínio próprio e os roteiros ficam em",
    strong: "seusite.com.br/roteiros",
    after: "ou no formato que preferir."
  },
  {
    q: "O que acontece se eu ultrapassar o limite de roteiros do meu plano?",
    a: "Você é avisado e pode fazer upgrade a qualquer momento. A diferença é cobrada proporcional ao tempo restante do mês. Sem multa, sem bloqueio surpresa."
  },
  {
    q: "Consigo falar com alguém antes de assinar?",
    a: "Consegue.",
    demo: true,
    after: "e a gente mostra a plataforma na prática, tira dúvidas e valida se faz sentido para o seu modelo de operação."
  }
];

// No celular a lista começa com 6 perguntas, para a seção caber na tela.
const faqAll = ref(false);
// Quem pede menos movimento no sistema vê a animação parada, com os controles para tocar.
const editorVideo = ref<HTMLVideoElement | null>(null);

const goToPlans = () => {
  document.getElementById("planos")?.scrollIntoView({ behavior: "smooth", block: "start" });
};

// Mesmo pixel da Meta que a página no WordPress usava (PixelYourSite).
type Fbq = ((...args: unknown[]) => void) & { callMethod?: (...args: unknown[]) => void; queue: unknown[][]; loaded: boolean; version: string; push: unknown };
const trackPageView = () => {
  const w = window as unknown as { fbq?: Fbq; _fbq?: Fbq };
  if (!w.fbq) {
    const fbq = function (...args: unknown[]) {
      if (fbq.callMethod) fbq.callMethod(...args);
      else fbq.queue.push(args);
    } as Fbq;
    fbq.push = fbq;
    fbq.loaded = true;
    fbq.version = "2.0";
    fbq.queue = [];
    w.fbq = fbq;
    if (!w._fbq) w._fbq = fbq;
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://connect.facebook.net/en_US/fbevents.js";
    document.head.appendChild(script);
  }
  w.fbq("init", META_PIXEL_ID);
  w.fbq("track", "PageView");
};

const setMeta = (name: string, content: string) => {
  let tag = document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`);
  if (!tag) {
    tag = document.createElement("meta");
    tag.name = name;
    document.head.appendChild(tag);
  }
  const previous = tag.content;
  tag.content = content;
  return () => {
    if (tag) tag.content = previous;
  };
};

let restoreDescription: (() => void) | null = null;
let previousTitle = "";

onMounted(() => {
  previousTitle = document.title;
  document.title = PAGE_TITLE;
  restoreDescription = setMeta("description", PAGE_DESCRIPTION);
  if (editorVideo.value && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    editorVideo.value.autoplay = false;
    editorVideo.value.pause();
    editorVideo.value.controls = true;
  }
  trackPageView();
});

onBeforeUnmount(() => {
  document.title = previousTitle;
  restoreDescription?.();
});
</script>

<style scoped>
/* Página de vendas no design system do painel: Inter no texto, Sora nos títulos, verde primário
   e tokens claros fixos (.public-tokens), mesmo com o painel no tema escuro.
   Cada seção cabe numa tela (1366×768, 1440×900 e 390×844): tamanhos limitados pela altura da
   tela e, no celular, listas longas viram trilhos de arrastar para o lado. */
.lp {
  --lp-pad-y: clamp(32px, 6svh, 64px);
  --lp-pad-x: 24px;
  --lp-ink: var(--foreground);
  --lp-muted: var(--muted-foreground);
  --lp-line: var(--border);
  --lp-soft: var(--background);
  --lp-mint: var(--primary-accent);
  min-height: 100vh;
  overflow-x: clip;
  background: var(--surface);
  color: var(--lp-ink);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}
.lp *,
.lp *::before,
.lp *::after {
  box-sizing: border-box;
}
.lp h1,
.lp h2,
.lp h3,
.lp p {
  margin: 0;
}

/* Seções */
.lp-sec {
  padding: var(--lp-pad-y) var(--lp-pad-x);
  background: var(--surface);
}
.lp-sec.is-soft {
  background: var(--lp-soft);
}
.lp-wrap {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
}
.lp-kicker {
  margin-bottom: 8px !important;
  color: var(--brand-dark);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-align: center;
  text-transform: uppercase;
}
.lp-h1 {
  color: var(--lp-ink);
  font-size: clamp(30px, min(3.4vw, 5.8svh), 48px);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.03em;
}
.lp-h2 {
  max-width: 820px;
  margin: 0 auto !important;
  color: var(--lp-ink);
  font-size: clamp(24px, min(2.5vw, 4.4svh), 34px);
  font-weight: 700;
  line-height: 1.18;
  text-align: center;
}
.is-brand {
  color: var(--brand-dark);
}
.is-red {
  color: var(--destructive);
}
.is-mint {
  color: var(--lp-mint);
}
.lp-sub {
  max-width: 700px;
  margin: 10px auto 0 !important;
  color: var(--lp-muted);
  font-size: 15px;
  line-height: 1.55;
  text-align: center;
}
.lp-sub strong {
  color: var(--lp-ink);
}
.lp-note {
  margin-top: 14px !important;
  color: var(--lp-muted);
  font-size: 13px;
  text-align: center;
}
.lp-note svg {
  display: inline-block;
  margin-right: 2px;
  color: var(--brand-dark);
  vertical-align: -3px;
}
.lp-swipe {
  display: none;
}

/* Botões */
.lp-ctas {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.lp-btn,
.lp-btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 48px;
  padding: 0 22px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}
.lp-btn {
  background: var(--primary);
  color: var(--primary-foreground);
  box-shadow: 0 12px 24px -12px rgba(18, 185, 129, 0.75);
}
.lp-btn:hover {
  background: var(--brand-dark);
  transform: translateY(-1px);
}
.lp-btn-ghost {
  border: 1px solid var(--lp-line);
  background: var(--surface);
  color: var(--lp-ink);
}
.lp-btn-ghost:hover {
  border-color: var(--primary);
  color: var(--brand-dark);
}

/* 01 Capa */
.lp-hero {
  padding-top: clamp(20px, 4svh, 40px);
  padding-bottom: clamp(24px, 5svh, 48px);
  background:
    radial-gradient(ellipse 60% 70% at 88% 12%, rgba(29, 233, 160, 0.16), transparent 70%),
    var(--surface);
}
.lp-hero-grid {
  display: grid;
  grid-template-areas:
    ". video"
    "copy video"
    "actions video"
    ". video";
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-rows: 1fr auto auto 1fr;
  column-gap: clamp(32px, 4vw, 56px);
  row-gap: 24px;
}
.lp-hero-copy {
  display: flex;
  grid-area: copy;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
}
.lp-logo {
  width: 168px;
  height: auto;
}
.lp-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--accent);
  color: var(--accent-foreground);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.lp-lead {
  max-width: 520px;
  color: var(--lp-muted);
  font-size: clamp(16px, 1.35vw, 19px);
  line-height: 1.55;
}
.lp-lead strong {
  color: var(--lp-ink);
}
/* Vídeo quadrado, do tamanho que cabe na altura da tela. */
.lp-hero-video {
  position: relative;
  grid-area: video;
  align-self: center;
  width: min(42vw, calc(100vh - 96px), 560px);
  width: min(42vw, calc(100svh - 96px), 560px);
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 20px;
  background: #0c100e;
  box-shadow: var(--shadow-elegant), 0 0 0 1px var(--lp-line);
}
.lp-hero-video iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.lp-hero-actions {
  grid-area: actions;
}
.lp-hero .lp-note {
  text-align: left;
}

/* 02 Números */
.lp-metrics-sec {
  padding-top: 20px;
  padding-bottom: 20px;
  border-block: 1px solid var(--lp-line);
}
.lp-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
}
.lp-metric {
  padding: 4px 12px;
  text-align: center;
}
.lp-metric + .lp-metric {
  border-left: 1px solid var(--lp-line);
}
.lp-metric-num {
  color: var(--brand-dark);
  font-family: var(--font-display);
  font-size: clamp(24px, 2.4vw, 32px);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
}
.lp-metric-lbl {
  margin-top: 4px;
  color: var(--lp-muted);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* Cartões (base comum) */
.lp-pain,
.lp-feat,
.lp-ex,
.lp-step,
.lp-plan {
  border: 1px solid var(--lp-line);
  border-radius: 16px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}
.lp-ico,
.lp-pain-ico {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

/* 03 Dores */
.lp-pains {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 28px;
}
.lp-pain {
  display: flex;
  gap: 14px;
  padding: 20px;
}
.lp-pain-ico {
  width: 40px;
  height: 40px;
  background: var(--status-danger);
  color: var(--status-danger-foreground);
}
.lp-pain h3 {
  color: var(--lp-ink);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
}
.lp-pain h3::first-letter {
  text-transform: uppercase;
}
.lp-pain p {
  margin-top: 6px !important;
  color: var(--lp-muted);
  font-size: 14px;
  line-height: 1.5;
}

/* 04 Funcionalidades */
.lp-sec .lp-feats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 24px;
}
.lp-feat {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 16px;
  transition: border-color 0.2s ease;
}
.lp-feat:hover {
  border-color: rgba(18, 185, 129, 0.5);
}
.lp-feat-head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.lp-ico {
  width: 32px;
  height: 32px;
  background: var(--accent);
  color: var(--brand-dark);
}
.lp-feat h3 {
  color: var(--lp-ink);
  font-size: 14.5px;
  font-weight: 700;
  line-height: 1.3;
}
.lp-feat p {
  margin-top: 8px !important;
  color: var(--lp-muted);
  font-size: 13px;
  line-height: 1.45;
}
.lp-tag {
  display: inline-block;
  margin-top: auto;
  padding: 3px 9px;
  border-radius: 999px;
  background: var(--accent);
  color: var(--accent-foreground);
  font-size: 11.5px;
  font-weight: 600;
  line-height: 1.35;
}
.lp-tag::first-letter {
  text-transform: uppercase;
}
.lp-feat p + .lp-tag {
  margin-top: 10px;
}

/* 05 Exemplos */
.lp-sec .lp-exs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 24px;
}
.lp-ex {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: border-color 0.2s ease;
}
.lp-ex:hover {
  border-color: rgba(18, 185, 129, 0.5);
}
.lp-ex img {
  display: block;
  width: 100%;
  height: clamp(120px, 19svh, 190px);
  object-fit: cover;
}
.lp-ex-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
}
.lp-ex-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: var(--lp-muted);
  font-size: 12px;
  font-weight: 600;
}
.lp-ex-badge {
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--accent);
  color: var(--accent-foreground);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.lp-ex-title {
  color: var(--lp-ink);
  font-size: 18px;
  font-weight: 700;
}
.lp-ex-desc {
  color: var(--lp-muted);
  font-size: 13.5px;
  line-height: 1.45;
}
.lp-ex-quote {
  padding: 10px 12px;
  border-left: 3px solid var(--primary);
  border-radius: 8px;
  background: var(--lp-soft);
  color: var(--lp-ink);
  font-size: 13px;
  font-style: italic;
  line-height: 1.45;
}
.lp-ex-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 40px;
  margin-top: auto;
  border: 1px solid var(--primary);
  border-radius: 10px;
  color: var(--brand-dark);
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  transition: background-color 0.2s ease, color 0.2s ease;
}
.lp-ex-link:hover {
  background: var(--primary);
  color: var(--primary-foreground);
}
.lp-closer {
  margin-top: 20px !important;
  color: var(--lp-ink);
  font-size: 15px;
  font-weight: 600;
  text-align: center;
}

/* 06 Como funciona */
.lp-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 24px;
}
.lp-step {
  display: flex;
  gap: 14px;
  padding: 20px;
}
.lp-step-num {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: var(--primary-foreground);
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 0 0 5px var(--accent);
}
.lp-step h3 {
  color: var(--lp-ink);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
}
.lp-step p {
  margin-top: 6px !important;
  color: var(--lp-muted);
  font-size: 14px;
  line-height: 1.5;
}

/* 07 Mais fácil que o Canva */
.lp-canva {
  display: grid;
  grid-template-columns: 1.35fr 0.65fr;
  align-items: center;
  gap: 28px;
  margin-top: 22px;
}
.lp-canva-visual {
  overflow: hidden;
  border: 1px solid var(--lp-line);
  border-radius: 16px;
  background: var(--surface);
  box-shadow: var(--shadow-elegant);
}
.lp-canva-visual video {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 10;
}
.lp-checks {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.lp-checks li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--lp-line);
  border-radius: 12px;
  background: var(--surface);
  color: var(--lp-ink);
  font-size: 15px;
  font-weight: 600;
}
.lp-check {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--primary);
  color: var(--primary-foreground);
}

/* 08 Planos */
.lp-sec .lp-plans {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  align-items: stretch;
  gap: 16px;
  margin-top: 24px;
}
.lp-plan {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 22px;
}
.lp-plan.is-feat {
  border: 2px solid var(--primary);
  background: linear-gradient(180deg, var(--accent) 0%, var(--surface) 38%);
  box-shadow: var(--shadow-elegant);
}
.lp-plan-tag {
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--accent);
  color: var(--accent-foreground);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.lp-plan.is-feat .lp-plan-tag {
  background: var(--primary);
  color: var(--primary-foreground);
}
.lp-plan-name {
  color: var(--lp-ink);
  font-size: 21px;
  font-weight: 700;
}
.lp-plan-pitch {
  min-height: 39px;
  color: var(--lp-muted);
  font-size: 13.5px;
  line-height: 1.45;
}
.lp-plan-price {
  display: flex;
  align-items: baseline;
  gap: 4px;
  color: var(--lp-ink);
}
.lp-plan-price .cur {
  font-size: 15px;
  font-weight: 700;
}
.lp-plan-price .val {
  font-family: var(--font-display);
  font-size: clamp(32px, 5svh, 40px);
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
}
.lp-plan-price .per {
  color: var(--lp-muted);
  font-size: 13px;
  font-weight: 600;
}
.lp-plan-per {
  margin-top: -4px !important;
  color: var(--brand-dark);
  font-size: 12.5px;
  font-weight: 700;
}
.lp-plan-feats {
  display: flex;
  flex-direction: column;
  gap: 7px;
  width: 100%;
  margin: 4px 0 0;
  padding: 12px 0 0;
  border-top: 1px solid var(--lp-line);
  list-style: none;
}
.lp-plan-feats li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--lp-ink);
  font-size: 13.5px;
  font-weight: 500;
  line-height: 1.4;
}
.lp-plan-feats li svg {
  margin-top: 2px;
  color: var(--brand-dark);
}
.lp-plan-feats li.is-mod {
  color: var(--lp-muted);
  font-size: 12.5px;
}
.lp-plan-feats li.is-mod strong {
  color: var(--accent-foreground);
}
.lp-plan-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 46px;
  margin-top: auto;
  border: 1px solid var(--primary);
  border-radius: 12px;
  color: var(--brand-dark);
  font-size: 14.5px;
  font-weight: 700;
  text-decoration: none;
  transition: background-color 0.2s ease, color 0.2s ease;
}
.lp-plan.is-feat .lp-plan-cta,
.lp-plan-cta:hover {
  background: var(--primary);
  color: var(--primary-foreground);
}
.lp-plan.is-feat .lp-plan-cta:hover {
  background: var(--brand-dark);
}

/* 09 Garantia */
.lp-guarantee {
  display: flex;
  align-items: center;
  gap: 24px;
  max-width: 860px;
  padding: 24px 28px;
  border: 1px solid rgba(18, 185, 129, 0.45);
  border-radius: 20px;
  background: var(--surface);
  box-shadow: var(--shadow-elegant);
}
.lp-guarantee-ico {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--brand-dark);
}
.lp-guarantee .lp-kicker {
  margin-bottom: 4px !important;
  text-align: left;
}
.lp-guarantee h3 {
  color: var(--lp-ink);
  font-size: 22px;
  font-weight: 700;
}
.lp-guarantee p:not(.lp-kicker) {
  margin-top: 6px !important;
  color: var(--lp-muted);
  font-size: 15px;
  line-height: 1.55;
}

/* 10 Perguntas: duas colunas no computador; abrir uma não estica a vizinha. */
.lp-faq {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  align-items: start;
  gap: 10px 14px;
  margin-top: 24px;
}
.lp-faq details {
  padding: 0 16px;
  border: 1px solid var(--lp-line);
  border-radius: 12px;
  background: var(--surface);
  transition: border-color 0.2s ease;
}
.lp-faq details[open] {
  border-color: rgba(18, 185, 129, 0.5);
  box-shadow: var(--shadow-card);
}
.lp-faq summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 0;
  color: var(--lp-ink);
  font-size: 14.5px;
  font-weight: 600;
  line-height: 1.35;
  list-style: none;
  cursor: pointer;
}
.lp-faq summary::-webkit-details-marker {
  display: none;
}
.lp-faq summary svg {
  color: var(--brand-dark);
  transition: transform 0.2s ease;
}
.lp-faq details[open] summary svg {
  transform: rotate(180deg);
}
.lp-faq p {
  padding-bottom: 14px;
  color: var(--lp-muted);
  font-size: 14px;
  line-height: 1.55;
}
.lp-faq p strong {
  color: var(--lp-ink);
}
.lp-faq a {
  color: var(--brand-dark);
  font-weight: 700;
}

/* 11 Chamada final (tons do tema escuro do design system) */
.lp-final {
  background:
    radial-gradient(ellipse 70% 90% at 50% 0%, rgba(18, 185, 129, 0.32), transparent 70%),
    #0c100e;
}
.lp-final-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.lp-final-title {
  color: #fff;
}
.lp-final-sub {
  max-width: 640px;
  margin-top: 14px !important;
  color: #c4ccc8;
  font-size: 17px;
  line-height: 1.55;
}
.lp-final .lp-ctas {
  justify-content: center;
  margin-top: 24px;
}
.lp-btn-mint {
  background: var(--lp-mint);
  color: #071613;
  box-shadow: 0 12px 28px -12px rgba(29, 233, 160, 0.6);
}
.lp-btn-mint:hover {
  background: #34d399;
}
.lp-btn-ghost-dark {
  border-color: rgba(255, 255, 255, 0.22);
  background: transparent;
  color: #fff;
}
.lp-btn-ghost-dark:hover {
  border-color: var(--lp-mint);
  color: var(--lp-mint);
}
.lp-final-note {
  margin-top: 18px !important;
  color: #9aa39e;
  font-size: 13px;
}
.lp-login {
  margin-top: 12px;
  color: #c4ccc8;
  font-size: 13px;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.lp-final .lp-btn:focus-visible,
.lp-final a:focus-visible {
  outline-color: var(--lp-mint);
}

.lp-faq-more {
  display: none;
}

/* Telas baixas (notebook com a barra do navegador, celular com a barra aberta): sai o que é
   secundário, para cada seção continuar cabendo numa tela. */
@media (max-height: 760px) {
  .lp-plan-pitch,
  .lp-sec-plans .lp-note,
  .lp-ex-desc,
  .lp-closer {
    display: none;
  }
}
@media (min-width: 861px) and (max-height: 760px) {
  .lp-sec .lp-feats {
    gap: 10px;
    margin-top: 20px;
  }
  .lp-feat {
    padding: 14px;
  }
  .lp-feat p {
    margin-top: 6px !important;
    font-size: 12.5px;
  }
  .lp-plan {
    gap: 8px;
    padding: 18px 20px;
  }
  .lp-plan-feats {
    gap: 5px;
  }
}

/* Tablet */
@media (max-width: 960px) {
  .lp-sec .lp-feats {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Celular e tablet estreito: capa empilhada e listas longas em trilhos de arrastar. */
@media (max-width: 860px) {
  .lp {
    --lp-pad-y: clamp(28px, 4.5svh, 44px);
    --lp-pad-x: 20px;
  }
  .lp-hero-grid {
    grid-template-areas:
      "copy"
      "video"
      "actions";
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto;
    row-gap: 14px;
  }
  .lp-hero-copy {
    align-items: center;
    gap: 10px;
    text-align: center;
  }
  .lp-logo {
    width: 136px;
  }
  .lp-lead {
    font-size: 16px;
  }
  .lp-hero-video {
    justify-self: center;
    width: min(100%, 35vh);
    width: min(100%, 35svh);
    border-radius: 16px;
  }
  .lp-h1 {
    font-size: clamp(23px, 3.6svh, 30px);
  }
  .lp-hero-actions .lp-ctas {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  /* Na capa do celular, "Agendar demonstração" vira link, para a capa caber na tela. */
  .lp-hero-actions .lp-btn-ghost {
    height: 32px;
    border: 0;
    background: none;
    color: var(--brand-dark);
    text-decoration: underline;
    text-underline-offset: 3px;
  }
  .lp-hide-sm {
    display: none;
  }
  .lp-hero .lp-note {
    margin-top: 10px !important;
    font-size: 12px;
    text-align: center;
  }
  .lp-swipe {
    display: block;
    margin-top: 8px !important;
    color: var(--lp-muted);
    font-size: 12.5px;
    text-align: center;
  }
  .lp-swipe::after {
    content: " →";
  }
  .lp-sec .lp-rail {
    position: relative;
    grid-auto-columns: 84%;
    grid-auto-flow: column;
    grid-template-columns: none;
    margin-top: 16px;
    margin-inline: calc(-1 * var(--lp-pad-x));
    padding: 2px var(--lp-pad-x) 6px;
    overflow-x: auto;
    overscroll-behavior-x: contain;
    scroll-padding-inline: var(--lp-pad-x);
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
  }
  .lp-sec .lp-rail::-webkit-scrollbar {
    display: none;
  }
  .lp-rail > * {
    scroll-snap-align: start;
  }
  .lp-sec .lp-feats.lp-rail {
    grid-template-rows: repeat(3, auto);
  }
  .lp-canva {
    grid-template-columns: 1fr;
    gap: 16px;
    margin-top: 18px;
  }
  /* No celular a própria animação explica; a linha de apoio fica só no computador. */
  .lp-canva-sub {
    display: none;
  }
  .lp-faq {
    grid-template-columns: 1fr;
    gap: 6px;
    margin-top: 18px;
  }
  .lp-faq:not(.is-all) details:nth-child(n + 7) {
    display: none;
  }
  .lp-faq-more {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    width: 100%;
    height: 42px;
    margin-top: 8px;
    border: 1px dashed var(--lp-line);
    border-radius: 12px;
    background: transparent;
    color: var(--brand-dark);
    font: inherit;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
  }
}
/* Celular com pouca altura (barra do navegador aberta, aparelhos menores). */
@media (max-width: 860px) and (max-height: 700px) {
  .lp-swipe {
    display: none !important;
  }
  .lp-sec .lp-feats.lp-rail {
    grid-template-rows: repeat(2, auto);
  }
  .lp-ex img {
    height: max(96px, 15svh);
  }
  .lp-checks {
    gap: 6px;
  }
  .lp-checks li {
    padding: 6px 10px;
    font-size: 13px;
  }
  .lp-checks li:nth-child(n + 5) {
    display: none;
  }
  .lp-plan {
    gap: 8px;
    padding: 14px 16px;
  }
  .lp-plan-feats {
    gap: 4px;
  }
  .lp-plan-feats li {
    font-size: 13px;
  }
  .lp-pains {
    gap: 8px;
  }
  .lp-pain p,
  .lp-step p {
    font-size: 13px;
  }
  .lp-sub {
    font-size: 14px;
  }
  .lp-hero {
    padding-bottom: 22px;
  }
  .lp-hero-video {
    width: min(100%, 32svh);
  }
  .lp-lead {
    font-size: 15px;
  }
  .lp-canva {
    gap: 12px;
  }
  .lp-checks li {
    font-size: 13.5px;
  }
  .lp-pain {
    padding: 14px;
  }
}
/* Celulares estreitos e baixos (360 px). */
@media (max-width: 380px) and (max-height: 700px) {
  .lp-h2 {
    font-size: 21px;
  }
  .lp-checks {
    gap: 6px;
  }
  .lp-checks li {
    padding: 7px 10px;
    font-size: 13px;
  }
  .lp-pain h3 {
    font-size: 15px;
  }
  .lp-pain p {
    margin-top: 4px !important;
  }
}
/* Aparelhos bem baixos: a garantia dos planos fica para a seção seguinte, que é sobre ela. */
@media (max-width: 860px) and (max-height: 660px) {
  .lp-sec-plans .lp-sub {
    display: none;
  }
}
@media (max-width: 767px) {
  .lp-metrics {
    grid-template-columns: repeat(2, 1fr);
    row-gap: 14px;
  }
  .lp-metric:nth-child(3) {
    border-left: 0;
  }
  .lp-pains,
  .lp-steps {
    grid-template-columns: 1fr;
    gap: 10px;
    margin-top: 18px;
  }
  .lp-pain,
  .lp-step {
    padding: 16px;
  }
  .lp-pain p,
  .lp-step p {
    font-size: 13.5px;
  }
  .lp-plan {
    padding: 18px;
  }
  .lp-checks li {
    padding: 10px 12px;
    font-size: 14px;
  }
  .lp-guarantee {
    flex-direction: column;
    gap: 12px;
    padding: 22px 20px;
    text-align: center;
  }
  .lp-guarantee .lp-kicker {
    text-align: center;
  }
  .lp-faq summary {
    padding: 11px 0;
    font-size: 14px;
  }
  .lp-final-sub {
    font-size: 15.5px;
  }
  .lp-final .lp-ctas {
    flex-direction: column;
    align-items: stretch;
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .lp-btn,
  .lp-feat,
  .lp-ex,
  .lp-faq summary svg {
    transition: none;
  }
  .lp-btn:hover {
    transform: none;
  }
}
</style>
