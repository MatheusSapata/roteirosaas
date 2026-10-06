<template>
  <div class="lp">
    <!-- 01 Capa -->
    <section class="lp-sec lp-hero">
      <img :src="logo" alt="Roteiro Online" class="lp-logo" width="240" height="72" />
      <span class="lp-pill">Aumente a sua conversão!</span>
      <h1 class="lp-h1">Seu cliente não compra o que não consegue imaginar!</h1>
      <p class="lp-lead">
        Crie páginas profissionais em minutos e faça seu cliente
        <strong>sentir o valor antes mesmo de saber o preço.</strong>
      </p>
      <div class="lp-hero-video">
        <iframe
          :src="HERO_VIDEO"
          title="Roteiro Online em funcionamento"
          allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture"
          allowfullscreen
          loading="lazy"
        ></iframe>
      </div>
      <div class="lp-ctas">
        <a href="#planos" class="lp-btn" @click.prevent="goToPlans">Quero ver os planos →</a>
        <a :href="DEMO_URL" class="lp-btn-ghost" target="_blank" rel="noopener">Agendar demonstração</a>
      </div>
      <p class="lp-note">⭐ 7 dias de garantia · Sem fidelidade · Cancele quando quiser</p>
    </section>

    <!-- 02 Números -->
    <section class="lp-sec lp-metrics-sec">
      <div class="lp-metrics">
        <div v-for="metric in METRICS" :key="metric.label" class="lp-metric">
          <div class="lp-metric-num">{{ metric.value }}</div>
          <div class="lp-metric-lbl">{{ metric.label }}</div>
        </div>
      </div>
    </section>

    <!-- 03 Dores -->
    <section class="lp-sec is-soft">
      <h2 class="lp-h2">
        É sério... mandando <span class="is-red">textão no WhatsApp,</span><br />
        é bem provável que...
      </h2>
      <div class="lp-pains">
        <div v-for="pain in PAINS" :key="pain.title" class="lp-pain">
          <div class="lp-pain-ico" aria-hidden="true">{{ pain.icon }}</div>
          <h3>{{ pain.title }}</h3>
          <p>{{ pain.text }}</p>
        </div>
      </div>
    </section>

    <!-- 04 Funcionalidades -->
    <section class="lp-sec is-soft lp-sec-feats">
      <p class="lp-kicker">Funcionalidades</p>
      <h2 class="lp-h2">
        <span class="is-green">Crie páginas profissionais</span><br />
        mesmo sem saber nada de design
      </h2>
      <div class="lp-feats">
        <div v-for="feat in FEATURES" :key="feat.title" class="lp-feat">
          <div class="lp-feat-ico" aria-hidden="true">{{ feat.icon }}</div>
          <h3>{{ feat.title }}</h3>
          <p>{{ feat.text }}</p>
          <span v-if="feat.tag" class="lp-tag">{{ feat.tag }}</span>
        </div>
      </div>
    </section>

    <!-- 05 Exemplos reais -->
    <section class="lp-sec">
      <p class="lp-kicker">Exemplos reais</p>
      <h2 class="lp-h2">Roteiros criados por <span class="is-green">pessoas como você!</span></h2>
      <p class="lp-sub">Sem designer, sem programação. Clique e veja o roteiro completo do mesmo jeito que o passageiro recebe.</p>
      <div class="lp-exs">
        <article v-for="example in EXAMPLES" :key="example.title" class="lp-ex">
          <img :src="example.image" :alt="`Roteiro ${example.title}`" loading="lazy" decoding="async" width="760" height="420" />
          <div class="lp-ex-body">
            <span class="lp-ex-badge">{{ example.badge }}</span>
            <p class="lp-ex-agency">{{ example.agency }}</p>
            <h3 class="lp-ex-title">{{ example.title }}</h3>
            <p class="lp-ex-desc">{{ example.text }}</p>
            <p class="lp-ex-quote">{{ example.quote }}</p>
            <a :href="example.url" class="lp-ex-link" target="_blank" rel="noopener">Abrir roteiro</a>
          </div>
        </article>
      </div>
      <p class="lp-closer">A sua apresentação pode ter o mesmo nível em poucos minutos.</p>
    </section>

    <!-- 06 Como funciona -->
    <section class="lp-sec lp-sec-steps">
      <p class="lp-kicker">Como funciona</p>
      <h2 class="lp-h2">Onboarding em <span class="is-green">menos de 3 minutos</span></h2>
      <div class="lp-steps">
        <div v-for="(step, index) in STEPS" :key="step.title" class="lp-step">
          <div class="lp-step-num">{{ index + 1 }}</div>
          <h3>{{ step.title }}</h3>
          <p>{{ step.text }}</p>
        </div>
      </div>
    </section>

    <!-- 07 Mais fácil que o Canva -->
    <section class="lp-sec is-soft">
      <h2 class="lp-h2">Mais fácil que <span class="is-green">editar no Canva!</span></h2>
      <div class="lp-canva">
        <div class="lp-canva-visual">
          <video :poster="editorPoster" autoplay muted loop playsinline preload="metadata" aria-label="Editor do Roteiro Online">
            <source :src="editorWebm" type="video/webm" />
            <source :src="editorMp4" type="video/mp4" />
          </video>
        </div>
        <ul class="lp-checks">
          <li v-for="item in EASIER" :key="item">{{ item }}</li>
        </ul>
      </div>
    </section>

    <!-- 08 Planos -->
    <section id="planos" class="lp-sec is-soft lp-sec-plans">
      <p class="lp-kicker">Escolha seu plano</p>
      <h2 class="lp-h2">Comece agora e publique seu <span class="is-green">primeiro roteiro hoje</span></h2>
      <p class="lp-sub">
        Todos os planos têm <strong>7 dias de garantia incondicional</strong>. Sem fidelidade, sem letras miúdas.
      </p>
      <div class="lp-plans">
        <article v-for="plan in PLANS" :key="plan.name" class="lp-plan" :class="{ 'is-feat': plan.featured }">
          <span class="lp-plan-tag">{{ plan.tag }}</span>
          <h3 class="lp-plan-name">{{ plan.name }}</h3>
          <p class="lp-plan-pitch">{{ plan.pitch }}</p>
          <div class="lp-plan-price">
            <span class="cur">R$</span><span class="val">{{ plan.price }}</span><span class="per">/mês</span>
          </div>
          <p class="lp-plan-per">{{ plan.perItinerary }}</p>
          <ul class="lp-plan-feats">
            <li v-for="item in plan.features" :key="item">{{ item }}</li>
          </ul>
          <div v-for="mod in plan.modules" :key="mod.title" class="lp-plan-mod">
            <strong>{{ mod.title }}</strong>
            <p>{{ mod.text }}</p>
          </div>
          <RouterLink :to="`/checkout/${plan.offer}`" class="lp-plan-cta">{{ plan.cta }}</RouterLink>
          <p class="lp-plan-guarantee">⭐ 7 dias de garantia</p>
        </article>
      </div>
      <p class="lp-note">Pague no cartão ou com Pix automático · Sem fidelidade · Cancele quando quiser · Reembolso em até 7 dias</p>
    </section>

    <!-- 09 Garantia -->
    <section class="lp-sec lp-sec-guarantee">
      <div class="lp-guarantee">
        <div class="lp-guarantee-pill">🛡️ Garantia de 7 dias</div>
        <h3>Teste sem risco</h3>
        <p>
          Você entra, usa, cria seu primeiro roteiro e valida na prática. Se entender que não é para o seu momento, a gente
          devolve 100% do valor. Sem burocracia, sem letras miúdas, sem justificativa obrigatória.
        </p>
      </div>
    </section>

    <!-- 10 Perguntas -->
    <section class="lp-sec is-soft lp-sec-faq">
      <p class="lp-kicker">Ainda tem dúvida?</p>
      <h2 class="lp-h2 lp-h2-sm">Perguntas que a gente <span class="is-green">mais escuta</span></h2>
      <div class="lp-faq">
        <details v-for="item in FAQ" :key="item.q">
          <summary>{{ item.q }}</summary>
          <p>
            {{ item.a }}
            <template v-if="item.strong"><strong>{{ item.strong }}</strong> {{ item.after }}</template>
            <template v-if="item.demo">
              <a :href="DEMO_URL" target="_blank" rel="noopener">Agende uma demonstração aqui</a> {{ item.after }}
            </template>
          </p>
        </details>
      </div>
    </section>

    <!-- 11 Chamada final -->
    <section class="lp-sec lp-final">
      <h2 class="lp-h2 lp-final-title">Publique hoje mesmo o seu <span class="is-neon">primeiro roteiro.</span></h2>
      <p class="lp-final-sub">
        Escolha seu plano, entre na plataforma e publique em menos de 30 minutos. Se não gostar, devolvemos 100% do valor em 7 dias.
      </p>
      <div class="lp-ctas">
        <a href="#planos" class="lp-btn lp-btn-lg" @click.prevent="goToPlans">Quero ver os planos →</a>
        <a :href="DEMO_URL" class="lp-btn-ghost lp-btn-ghost-dark" target="_blank" rel="noopener">Agendar demonstração</a>
      </div>
      <p class="lp-final-note">Sem fidelidade · 7 dias de garantia · Cancelamento simples</p>
      <RouterLink to="/login" class="lp-login">Já é cliente? Entrar</RouterLink>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from "vue";
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
    icon: "🕳️",
    title: "suas cotações estejam sumindo",
    text: "O lead pede, você manda, ele some. Sem página profissional, a cotação vira só mais uma mensagem perdida no WhatsApp."
  },
  {
    icon: "💎",
    title: "seu cliente não vê o real valor",
    text: "Quando o passageiro vê só o preço, compara por preço. Quando enxerga a experiência completa, compra a experiência."
  },
  {
    icon: "📉",
    title: "você esteja concorrendo por preço",
    text: "Se a apresentação não sustenta o valor, o único argumento que sobra é desconto. Apresente melhor, venda pelo preço certo."
  }
];

const FEATURES = [
  {
    icon: "🎯",
    title: "Editor intuitivo, visual e prático",
    text: "Blocos prontos de hero, itinerário, inclusos, investimento e CTA. Não precisa de conhecimento técnico pra usar."
  },
  {
    icon: "📆",
    title: "Itinerário dia a dia interativo",
    text: "Cada dia vira uma aba clicável. O passageiro abre só o que quer ver, como um app de viagem."
  },
  {
    icon: "💚",
    title: "Botão WhatsApp onde você quiser",
    text: "Você pode adicionar em qualquer seção, com mensagem pronta e o nome do roteiro. O lead chega no seu WhatsApp já contextualizado."
  },
  {
    icon: "📸",
    title: "Galeria com carrossel",
    text: "Fotos do destino, da hospedagem e dos passeios com thumb navegável — sem peso de PDF."
  },
  {
    icon: "💳",
    title: "Cards de investimento flexíveis",
    text: "Adulto, criança, apto individual, duplo, triplo, categoria especial. Tantas categorias de preço quanto você precisar."
  },
  {
    icon: "⏳",
    title: "Contagem regressiva automática",
    text: "Cria urgência real até a data da viagem. Sem precisar editar nada manualmente."
  },
  {
    icon: "📊",
    title: "Pixel Meta e Google integrados",
    text: "Faça tráfego pago para a página e retargete quem não fechou.",
    tag: "a partir de 1 no plano profissional"
  },
  {
    icon: "🧲",
    title: "Módulo Leads",
    text: "Formulário de captação dentro do roteiro. Cada passageiro interessado vira oportunidade futura.",
    tag: "Nos planos Agência e Escala"
  },
  {
    icon: "🧬",
    title: "Duplicação com um clique",
    text: "Copiou a estrutura do último roteiro? Troque o destino e publique em minutos.",
    tag: "nos planos Agência e Escala"
  },
  {
    icon: "🌐",
    title: "Domínio próprio",
    text: "Publique seus roteiros no endereço da sua agência. Marca branca completa.",
    tag: "Exclusivo do plano Escala"
  },
  {
    icon: "📱",
    title: "100% responsivo no celular",
    text: "A maior parte dos clientes abre pelo WhatsApp. A página é pensada para o mobile primeiro."
  },
  {
    icon: "🔗",
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

const goToPlans = () => {
  document.getElementById("planos")?.scrollIntoView({ behavior: "smooth", block: "start" });
};

const FONT_HREF = "https://fonts.googleapis.com/css2?family=Roboto:wght@400;600;700;800&display=swap";
const ensureFont = () => {
  if (document.querySelector(`link[href="${FONT_HREF}"]`)) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = FONT_HREF;
  document.head.appendChild(link);
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
  ensureFont();
  trackPageView();
});

onBeforeUnmount(() => {
  document.title = previousTitle;
  restoreDescription?.();
});
</script>

<style scoped>
.lp {
  --lp-neon: #29ff60;
  --lp-green: #1a8a3c;
  --lp-ink: #05140b;
  --lp-text: #2b3d31;
  --lp-soft: #f5fbf6;
  --lp-neon-soft: rgba(41, 255, 96, 0.18);
  --lp-red: #d43f3a;
  min-height: 100vh;
  overflow-x: hidden;
  background: #fff;
  color: var(--lp-text);
  font-family: Roboto, -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
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
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 100px;
  background: #fff;
}
.lp-sec.is-soft {
  background: var(--lp-soft);
}
.lp-sec-feats {
  padding-top: 20px;
}
.lp-sec-steps {
  padding-top: 20px;
  padding-bottom: 72px;
}
.lp-sec-guarantee,
.lp-sec-faq {
  padding-left: 20px;
  padding-right: 20px;
}
.lp-kicker {
  margin-bottom: 12px !important;
  color: var(--lp-green);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 2px;
  text-align: center;
  text-transform: uppercase;
}
.lp-h1 {
  max-width: 1036px;
  padding: 0 50px;
  color: var(--lp-ink);
  font-size: 48px;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.8px;
  text-align: center;
}
.lp-h2 {
  color: var(--lp-ink);
  font-size: 36px;
  font-weight: 800;
  line-height: 1.2;
  text-align: center;
}
.lp-h2-sm {
  font-size: 34px;
}
.is-green {
  color: var(--lp-green);
}
.is-red {
  color: var(--lp-red);
}
.is-neon {
  color: var(--lp-neon);
}
.lp-sub {
  max-width: 680px;
  margin-top: 16px !important;
  font-size: 16px;
  line-height: 1.55;
  text-align: center;
}
.lp-note {
  margin-top: 16px !important;
  font-size: 13px;
  text-align: center;
}

/* 01 Capa */
.lp-hero {
  gap: 20px;
  padding-top: 20px;
  padding-bottom: 0;
}
.lp-logo {
  width: 240px;
  height: auto;
  margin: 20px 0 0;
}
.lp-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 18px;
  border-radius: 999px;
  background: var(--lp-neon-soft);
  color: var(--lp-green);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}
.lp-lead {
  max-width: 780px;
  color: var(--lp-text);
  font-size: 20px;
  line-height: 1.55;
  text-align: center;
}
.lp-lead strong {
  color: var(--lp-ink);
}
.lp-hero-video {
  position: relative;
  width: 100%;
  max-width: 996px;
  aspect-ratio: 1;
  max-height: 596px;
  overflow: hidden;
  border-radius: 24px;
  background: var(--lp-ink);
}
.lp-hero-video iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.lp-ctas {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 8px;
}
.lp-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 16px 28px;
  border-radius: 999px;
  background: var(--lp-neon);
  color: var(--lp-ink);
  font-size: 16px;
  font-weight: 800;
  text-decoration: none;
  box-shadow: 0 10px 30px rgba(41, 255, 96, 0.35);
  transition: transform 0.2s ease, background-color 0.2s ease;
}
.lp-btn:hover {
  transform: translateY(-2px);
}
.lp-btn-lg {
  padding: 18px 32px;
  font-size: 17px;
  box-shadow: 0 20px 40px rgba(41, 255, 96, 0.35);
}
.lp-btn-ghost {
  padding: 14px 26px;
  border: 2px solid rgba(41, 255, 96, 0.5);
  border-radius: 999px;
  color: var(--lp-green);
  font-size: 16px;
  font-weight: 700;
  text-decoration: none;
  transition: background-color 0.2s ease;
}
.lp-btn-ghost:hover {
  background: var(--lp-neon-soft);
}
.lp-btn-ghost-dark {
  padding: 16px 30px;
  border-color: rgba(41, 255, 96, 0.6);
  color: #fff;
  font-size: 17px;
}

/* 02 Números */
.lp-metrics-sec {
  padding: 40px 20px;
}
.lp-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  width: 100%;
  max-width: 1040px;
}
.lp-metric {
  padding: 20px 12px;
  border: 1px solid rgba(41, 255, 96, 0.25);
  border-radius: 20px;
  background: var(--lp-soft);
  text-align: center;
}
.lp-metric-num {
  color: var(--lp-green);
  font-size: 34px;
  font-weight: 800;
  line-height: 1;
}
.lp-metric-lbl {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* 03 Dores */
.lp-pains {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  width: 100%;
  max-width: 1040px;
  margin-top: 28px;
}
.lp-pain {
  padding: 22px;
  border: 1px solid rgba(212, 63, 58, 0.18);
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(25, 61, 32, 0.05);
}
.lp-pain-ico {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  margin-bottom: 12px;
  border-radius: 50%;
  background: rgba(212, 63, 58, 0.1);
  font-size: 22px;
}
.lp-pain h3,
.lp-feat h3 {
  margin-bottom: 6px !important;
  color: var(--lp-ink);
  font-size: 17px;
  font-weight: 800;
}
.lp-pain p,
.lp-feat p {
  font-size: 14px;
  line-height: 1.5;
}

/* 04 Funcionalidades */
.lp-feats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  width: 100%;
  max-width: 1140px;
  margin-top: 32px;
}
.lp-feat {
  padding: 24px;
  border: 1px solid rgba(25, 61, 32, 0.1);
  border-radius: 24px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(25, 61, 32, 0.06);
  transition: transform 0.25s ease, border-color 0.25s ease;
}
.lp-feat:hover,
.lp-ex:hover {
  transform: translateY(-4px);
  border-color: rgba(41, 255, 96, 0.45);
}
.lp-feat h3 {
  font-size: 18px;
}
.lp-feat p {
  line-height: 1.55;
}
.lp-feat-ico {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  margin-bottom: 14px;
  border-radius: 14px;
  background: var(--lp-neon-soft);
  font-size: 24px;
}
.lp-tag {
  display: inline-block;
  margin-top: 10px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--lp-neon-soft);
  color: var(--lp-green);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

/* 05 Exemplos */
.lp-exs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  width: 100%;
  max-width: 1140px;
  margin-top: 32px;
}
.lp-ex {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(25, 61, 32, 0.1);
  border-radius: 24px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(25, 61, 32, 0.08);
  transition: transform 0.25s ease, border-color 0.25s ease;
}
.lp-ex img {
  display: block;
  width: 100%;
  height: 220px;
  object-fit: cover;
}
.lp-ex-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
}
.lp-ex-badge {
  align-self: flex-start;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--lp-neon-soft);
  color: var(--lp-green);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.lp-ex-agency {
  color: var(--lp-green);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.lp-ex-title {
  color: var(--lp-ink);
  font-size: 19px;
  font-weight: 800;
}
.lp-ex-desc {
  font-size: 14px;
  line-height: 1.5;
}
.lp-ex-quote {
  padding: 12px 14px;
  border-left: 3px solid var(--lp-neon);
  border-radius: 12px;
  background: var(--lp-soft);
  font-size: 13px;
  font-style: italic;
  line-height: 1.5;
}
.lp-ex-link {
  margin-top: auto;
  padding: 12px 16px;
  border-radius: 999px;
  background: var(--lp-neon);
  color: var(--lp-ink);
  font-size: 14px;
  font-weight: 800;
  text-align: center;
  text-decoration: none;
  transition: background-color 0.2s ease, color 0.2s ease;
}
.lp-ex-link:hover,
.lp-plan-cta:hover {
  background: var(--lp-green);
  color: #fff;
}
.lp-closer {
  margin-top: 36px !important;
  color: var(--lp-ink);
  font-size: 17px;
  font-weight: 700;
  text-align: center;
}

/* 06 Como funciona */
.lp-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  width: 100%;
  max-width: 1040px;
  margin-top: 32px;
}
.lp-step {
  padding: 28px;
  border: 1px solid rgba(41, 255, 96, 0.3);
  border-radius: 24px;
  background: var(--lp-soft);
}
.lp-step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  margin-bottom: 16px;
  border-radius: 50%;
  background: var(--lp-neon);
  color: var(--lp-ink);
  font-size: 20px;
  font-weight: 800;
  box-shadow: 0 0 0 6px var(--lp-neon-soft);
}
.lp-step h3 {
  margin-bottom: 8px !important;
  color: var(--lp-ink);
  font-size: 20px;
  font-weight: 800;
}
.lp-step p {
  font-size: 15px;
  line-height: 1.55;
}

/* 07 Mais fácil que o Canva */
.lp-canva {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  align-items: center;
  gap: 28px;
  width: 100%;
  max-width: 1080px;
  margin-top: 24px;
}
.lp-canva-visual {
  overflow: hidden;
  border: 1px solid rgba(41, 255, 96, 0.35);
  border-radius: 28px;
  background: #fff;
  box-shadow: 0 20px 50px rgba(25, 61, 32, 0.12);
}
.lp-canva-visual video {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 1166 / 640;
}
.lp-checks {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.lp-checks li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(41, 255, 96, 0.25);
  border-radius: 18px;
  background: #fff;
  color: var(--lp-ink);
  font-size: 16px;
  font-weight: 600;
}
.lp-checks li::before,
.lp-plan-feats li::before {
  content: "";
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--lp-neon)
    url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2305140b' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'/></svg>")
    center / 14px 14px no-repeat;
  box-shadow: 0 0 0 4px var(--lp-neon-soft);
}

/* 08 Planos */
.lp-plans {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  align-items: stretch;
  gap: 20px;
  width: 100%;
  max-width: 1160px;
  margin-top: 32px;
}
.lp-plan {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 32px 28px;
  border: 1px solid rgba(25, 61, 32, 0.12);
  border-radius: 28px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(25, 61, 32, 0.08);
  transition: transform 0.25s ease, border-color 0.25s ease;
}
.lp-plan:hover {
  transform: translateY(-6px);
  border-color: rgba(41, 255, 96, 0.5);
}
.lp-plan.is-feat {
  border-color: rgba(41, 255, 96, 0.55);
  background: linear-gradient(180deg, rgba(41, 255, 96, 0.15) 0%, #fff 100%);
  box-shadow: 0 20px 50px rgba(25, 61, 32, 0.14);
  transform: translateY(-10px);
}
.lp-plan-tag {
  align-self: flex-start;
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--lp-neon-soft);
  color: var(--lp-green);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}
.lp-plan.is-feat .lp-plan-tag {
  background: var(--lp-neon);
  color: var(--lp-ink);
}
.lp-plan-name {
  color: var(--lp-ink);
  font-size: 24px;
  font-weight: 800;
}
.lp-plan-pitch {
  min-height: 40px;
  font-size: 14px;
  line-height: 1.5;
}
.lp-plan-price {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 4px;
  color: var(--lp-ink);
}
.lp-plan-price .cur {
  font-size: 18px;
  font-weight: 700;
}
.lp-plan-price .val {
  font-size: 48px;
  font-weight: 800;
  line-height: 1;
}
.lp-plan-price .per {
  font-size: 14px;
  font-weight: 600;
  color: var(--lp-text);
}
.lp-plan-per {
  color: var(--lp-green);
  font-size: 13px;
  font-weight: 700;
}
.lp-plan-feats {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 4px 0 0;
  padding: 0;
  list-style: none;
}
.lp-plan-feats li {
  position: relative;
  padding-left: 26px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
}
.lp-plan-feats li::before {
  position: absolute;
  top: 1px;
  left: 0;
  width: 16px;
  height: 16px;
  background-size: 10px 10px;
  box-shadow: 0 0 0 3px var(--lp-neon-soft);
}
.lp-plan-mod {
  padding: 12px 14px;
  border: 1px dashed rgba(41, 255, 96, 0.4);
  border-radius: 14px;
  background: var(--lp-soft);
}
.lp-plan-mod strong {
  display: block;
  margin-bottom: 4px;
  color: var(--lp-green);
  font-size: 13px;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.lp-plan-mod p {
  font-size: 13px;
  line-height: 1.5;
}
.lp-plan-cta {
  margin-top: auto;
  padding: 16px 20px;
  border-radius: 999px;
  background: var(--lp-neon);
  color: var(--lp-ink);
  font-size: 15px;
  font-weight: 800;
  text-align: center;
  text-decoration: none;
  box-shadow: 0 10px 24px rgba(41, 255, 96, 0.3);
  transition: background-color 0.25s ease, color 0.25s ease;
}
.lp-plan-guarantee {
  font-size: 12px;
  text-align: center;
}
.lp-sec-plans > .lp-note {
  margin-top: 28px !important;
}

/* 09 Garantia */
.lp-guarantee {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  width: 100%;
  max-width: 780px;
  padding: 36px 28px;
  border: 1px solid rgba(41, 255, 96, 0.5);
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(41, 255, 96, 0.14) 0%, #fff 100%);
  box-shadow: 0 20px 50px rgba(25, 61, 32, 0.12);
  text-align: center;
}
.lp-guarantee-pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border-radius: 999px;
  background: var(--lp-neon);
  color: var(--lp-ink);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}
.lp-guarantee h3 {
  color: var(--lp-ink);
  font-size: 28px;
  font-weight: 800;
}
.lp-guarantee p {
  max-width: 620px;
  font-size: 16px;
  line-height: 1.6;
}

/* 10 Perguntas */
.lp-faq {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 860px;
  margin-top: 32px;
}
.lp-faq details {
  padding: 2px 20px;
  border: 1px solid rgba(25, 61, 32, 0.1);
  border-radius: 18px;
  background: #fff;
  transition: border-color 0.25s ease;
}
.lp-faq details[open] {
  border-color: rgba(41, 255, 96, 0.45);
  box-shadow: 0 10px 24px rgba(25, 61, 32, 0.06);
}
.lp-faq summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 0;
  color: var(--lp-ink);
  font-size: 16px;
  font-weight: 700;
  list-style: none;
  cursor: pointer;
}
.lp-faq summary::-webkit-details-marker {
  display: none;
}
.lp-faq summary::after {
  content: "+";
  flex: 0 0 auto;
  color: var(--lp-green);
  font-size: 24px;
  font-weight: 800;
}
.lp-faq details[open] summary::after {
  content: "−";
}
.lp-faq p {
  margin-bottom: 18px !important;
  font-size: 15px;
  line-height: 1.6;
}
.lp-faq a {
  color: var(--lp-green);
  font-weight: 700;
  text-decoration: none;
}

/* 11 Chamada final */
.lp-final {
  padding: 56px 20px 40px;
  background: linear-gradient(180deg, var(--lp-green) 0%, var(--lp-ink) 100%);
}
.lp-final-title {
  color: #fff;
  font-size: 42px;
  line-height: 1.15;
}
.lp-final-sub {
  max-width: 680px;
  margin-top: 16px !important;
  color: #d7efdd;
  font-size: 18px;
  line-height: 1.55;
  text-align: center;
}
.lp-final .lp-ctas {
  margin-top: 28px;
}
.lp-final-note {
  margin-top: 24px !important;
  color: #98b3a2;
  font-size: 13px;
  text-align: center;
}
.lp-login {
  margin-top: 18px;
  color: #d7efdd;
  font-size: 13px;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* Tablet */
@media (max-width: 1024px) {
  .lp-h1 {
    font-size: 36px;
  }
  .lp-h2 {
    font-size: 28px;
  }
  .lp-h2-sm {
    font-size: 26px;
  }
  .lp-final-title {
    font-size: 32px;
  }
}
@media (max-width: 900px) {
  .lp-plans {
    grid-template-columns: 1fr;
    max-width: 440px;
  }
  .lp-plan.is-feat {
    transform: none;
  }
}

/* Celular */
@media (max-width: 767px) {
  .lp-sec {
    padding: 40px 20px;
  }
  .lp-sec-guarantee,
  .lp-sec-faq {
    padding: 30px 16px;
  }
  .lp-hero {
    padding-top: 24px;
    padding-bottom: 8px;
  }
  .lp-logo {
    width: 180px;
    margin-top: 0;
  }
  .lp-h1 {
    padding: 0;
    font-size: 28px;
  }
  .lp-h2,
  .lp-h2-sm {
    font-size: 22px;
  }
  .lp-lead {
    font-size: 17px;
  }
  .lp-metrics-sec {
    padding-top: 24px;
  }
  .lp-metrics {
    grid-template-columns: 1fr 1fr;
  }
  .lp-metric-num {
    font-size: 26px;
  }
  .lp-pains,
  .lp-feats,
  .lp-exs,
  .lp-steps,
  .lp-canva {
    grid-template-columns: 1fr;
  }
  .lp-final {
    padding: 48px 20px 40px;
  }
  .lp-final-title {
    font-size: 26px;
  }
  .lp-final-sub {
    font-size: 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .lp-btn,
  .lp-feat,
  .lp-ex,
  .lp-plan {
    transition: none;
  }
  .lp-btn:hover,
  .lp-feat:hover,
  .lp-ex:hover,
  .lp-plan:hover {
    transform: none;
  }
}
</style>
