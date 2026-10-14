<template>
  <div class="lp public-tokens">
    <!-- Faixa da promoção da 1ª mensalidade (só enquanto ela vale; a data vem do Admin Master). -->
    <a v-if="monthlyPromo" href="#planos" class="lp-promo-bar" @click.prevent="goToPlans('monthly')">
      <span class="lp-promo-tag">Oferta por tempo limitado</span>
      <span>1ª mensalidade por <b>{{ formatBRL(monthlyPromo.amount, { cents: "auto" }) }}</b><span class="lp-hide-sm"> no plano mensal</span></span>
      <span v-if="promoCountdown" class="lp-promo-time">termina em {{ promoCountdown }}</span>
    </a>

    <!-- 01 Capa (escura): texto à esquerda, vídeo quadrado à direita (no celular, o vídeo fica entre o texto e os botões). -->
    <section class="lp-sec is-night lp-hero">
      <div class="lp-wrap lp-hero-grid">
        <div class="lp-hero-copy">
          <img :src="logoWhite" alt="Roteiro Online" class="lp-logo" width="240" height="72" />
          <span class="lp-pill"><Sparkles :size="14" aria-hidden="true" />Aumente a sua conversão!</span>
          <h1 class="lp-h1">Seu cliente não compra o que <span class="is-brand">não consegue imaginar!</span></h1>
          <p class="lp-lead">
            Crie páginas profissionais em minutos e faça seu cliente
            <strong>sentir o valor antes mesmo de saber o preço.</strong>
          </p>
        </div>
        <div class="lp-hero-media">
          <div class="lp-hero-video">
            <iframe
              :src="HERO_VIDEO"
              title="Roteiro Online em funcionamento"
              allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture"
              allowfullscreen
              loading="lazy"
            ></iframe>
          </div>
          <div class="lp-float lp-float-a" aria-hidden="true">
            <span class="lp-float-ico"><Check :size="15" /></span>
            <span><b>Roteiro publicado</b><small>Link pronto para o WhatsApp</small></span>
          </div>
          <div class="lp-float lp-float-b" aria-hidden="true">
            <span class="lp-float-ico is-whats"><MessageCircle :size="15" /></span>
            <span><b>Novo contato</b><small>“Quero reservar 2 lugares”</small></span>
          </div>
        </div>
        <div class="lp-hero-actions">
          <div class="lp-ctas">
            <a href="#planos" class="lp-btn" @click.prevent="goToPlans()">Quero assinar <ArrowRight :size="18" aria-hidden="true" /></a>
            <a :href="DEMO_URL" class="lp-btn-ghost" target="_blank" rel="noopener">Agendar demonstração</a>
          </div>
          <p class="lp-note"><ShieldCheck :size="15" aria-hidden="true" /><span>Plano único com tudo incluso · 7 dias de garantia<span class="lp-hide-sm"> · Sem fidelidade</span></span></p>
        </div>
      </div>
    </section>

    <!-- 02 Números (faixa verde) -->
    <section class="lp-sec is-green lp-metrics-sec">
      <div class="lp-wrap lp-metrics">
        <div v-for="metric in METRICS" :key="metric.label" class="lp-metric">
          <div class="lp-metric-num">{{ metric.value }}</div>
          <div class="lp-metric-lbl">{{ metric.label }}</div>
        </div>
      </div>
    </section>

    <!-- 03 Assistente IA (escura): a página sai pronta a partir do que a agência já tem -->
    <section class="lp-sec is-night lp-sec-ai">
      <div class="lp-wrap lp-ai">
        <div class="lp-ai-copy">
          <p class="lp-kicker">Assistente de IA</p>
          <h2 class="lp-h2">Descreva a viagem. <span class="is-brand">A IA monta a página.</span></h2>
          <p class="lp-sub">
            Mande o roteiro do jeito que você tem. O assistente escreve os textos e organiza o dia a dia, o que está incluso,
            os preços e as dúvidas. Você só revisa e publica.
          </p>
          <ol class="lp-ai-steps">
            <li v-for="(step, index) in AI_STEPS" :key="step.title">
              <span class="lp-ai-num" aria-hidden="true">{{ index + 1 }}</span>
              <div>
                <h3>{{ step.title }}</h3>
                <p>{{ step.text }}</p>
              </div>
            </li>
          </ol>
          <div class="lp-ai-chips" aria-label="O que você pode mandar">
            <span v-for="chip in AI_INPUTS" :key="chip.label"><component :is="chip.icon" :size="14" aria-hidden="true" />{{ chip.label }}</span>
          </div>
        </div>
        <div class="lp-ai-visual">
          <div class="lp-canva-bar" aria-hidden="true"><i></i><i></i><i></i><span>Assistente IA do Roteiro Online</span></div>
          <!-- Gravado do editor de verdade por tools/help-media/lp-assistente.mjs. -->
          <video
            ref="aiVideo"
            :poster="assistantPoster"
            autoplay
            muted
            loop
            playsinline
            preload="metadata"
            aria-label="Animação do Assistente IA: a agência descreve a viagem, a IA monta a página com banner, roteiro dia a dia, inclusos, preços e dúvidas, e a página é aplicada com um clique"
          >
            <source :src="assistantWebm" type="video/webm" />
            <source :src="assistantMp4" type="video/mp4" />
          </video>
        </div>
      </div>
    </section>

    <!-- 04 Dores -->
    <section class="lp-sec is-mist">
      <div class="lp-wrap">
        <h2 class="lp-h2">
          É sério... mandando <span class="is-red">textão no WhatsApp,</span><br />
          é bem provável que...
        </h2>
        <div class="lp-pains">
          <div v-for="(pain, index) in PAINS" :key="pain.title" class="lp-pain">
            <span class="lp-pain-ico" aria-hidden="true"><component :is="pain.icon" :size="22" /></span>
            <div>
              <span class="lp-pain-num" aria-hidden="true">0{{ index + 1 }}</span>
              <h3>{{ pain.title }}</h3>
              <p>{{ pain.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 04 Antes e depois (escura) -->
    <section class="lp-sec is-night">
      <div class="lp-wrap">
        <p class="lp-kicker">Saia disso</p>
        <h2 class="lp-h2">Do textão para uma <span class="is-brand">página que vende</span></h2>
        <div class="lp-compare">
          <div class="lp-cmp is-before">
            <div class="lp-cmp-mock" aria-hidden="true">
              <div class="lp-chat">
                <div class="lp-chat-bubble">
                  <span v-for="width in CHAT_LINES" :key="width" class="lp-skel" :style="{ width: `${width}%` }"></span>
                  <small>14:32 ✓✓</small>
                </div>
                <div class="lp-chat-file"><FileText :size="16" /><span>roteiro-final-v3.pdf</span><small>12 MB</small></div>
              </div>
            </div>
            <p class="lp-cmp-label"><CircleX :size="18" aria-hidden="true" />Do jeito de sempre</p>
            <ul class="lp-cmp-list">
              <li v-for="item in BEFORE" :key="item"><X :size="14" aria-hidden="true" />{{ item }}</li>
            </ul>
          </div>
          <span class="lp-cmp-arrow" aria-hidden="true"><ArrowRight :size="20" /></span>
          <div class="lp-cmp is-after">
            <div class="lp-cmp-mock" aria-hidden="true">
              <div class="lp-phone">
                <img :src="exemploFoz" alt="" loading="lazy" decoding="async" />
                <span class="lp-phone-title">Foz do Iguaçu</span>
                <span class="lp-skel"></span>
                <span class="lp-skel is-short"></span>
                <span class="lp-phone-btn"><MessageCircle :size="10" />Quero reservar</span>
              </div>
              <div class="lp-link-chip"><Link :size="13" /><span>roteiroonline.com/<b>sua-agencia</b></span></div>
            </div>
            <p class="lp-cmp-label"><CircleCheck :size="18" aria-hidden="true" />Com o Roteiro Online</p>
            <ul class="lp-cmp-list">
              <li v-for="item in AFTER" :key="item"><Check :size="14" aria-hidden="true" />{{ item }}</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- 05 Funcionalidades: cada cartão com uma mini-tela do que a função faz -->
    <section class="lp-sec is-mist">
      <div class="lp-wrap">
        <p class="lp-kicker">Funcionalidades</p>
        <h2 class="lp-h2"><span class="is-brand">Crie páginas profissionais</span> mesmo sem saber nada de design</h2>
        <p class="lp-swipe" aria-hidden="true">Arraste para o lado para ver mais</p>
        <div class="lp-feats lp-rail">
          <article v-for="feat in FEATURES" :key="feat.title" class="lp-feat" :class="`is-${feat.tone}`">
            <div class="lp-fx" aria-hidden="true">
              <div v-if="feat.visual === 'editor'" class="fx-editor">
                <span class="fx-block"></span>
                <span class="fx-block is-on"><span class="fx-tag">Itinerário</span></span>
                <span class="fx-block"></span>
                <MousePointer2 class="fx-cursor" :size="20" />
              </div>
              <div v-else-if="feat.visual === 'days'" class="fx-days">
                <span v-for="(day, index) in FX_DAYS" :key="day" class="fx-day" :class="{ 'is-open': index === 0 }">
                  <b>Dia {{ index + 1 }}</b>{{ day }}<ChevronDown v-if="index === 0" :size="13" /><ChevronRight v-else :size="13" />
                </span>
              </div>
              <div v-else-if="feat.visual === 'whats'" class="fx-whats">
                <span class="fx-bubble">Olá! Quero saber mais sobre o roteiro <b>Foz do Iguaçu</b>.</span>
                <span class="fx-wbtn"><MessageCircle :size="14" />Falar no WhatsApp</span>
              </div>
              <div v-else-if="feat.visual === 'prices'" class="fx-prices">
                <span class="fx-price"><small>Adulto</small><b>R$ 1.290</b><em>ou 10x de R$ 129</em></span>
                <span class="fx-price is-alt"><small>Criança</small><b>R$ 890</b><em>ou 10x de R$ 89</em></span>
              </div>
              <div v-else-if="feat.visual === 'count'" class="fx-count">
                <small>A saída é em</small>
                <span class="fx-count-row">
                  <span v-for="part in countdownParts" :key="part.label"><b>{{ part.value }}</b>{{ part.label }}</span>
                </span>
              </div>
              <div v-else-if="feat.visual === 'chart'" class="fx-chart">
                <span class="fx-bars">
                  <span v-for="(height, index) in FX_BARS" :key="index" :style="{ height: `${height}%` }"></span>
                </span>
                <span class="fx-chart-tags"><span>Meta</span><span>Google</span></span>
              </div>
              <div v-else-if="feat.visual === 'form'" class="fx-form">
                <span class="fx-input">Nome</span>
                <span class="fx-input">WhatsApp</span>
                <span class="fx-submit">Quero reservar</span>
                <span class="fx-toast"><UserRound :size="12" />+1 lead</span>
              </div>
            </div>
            <div class="lp-feat-body">
              <h3><span class="lp-feat-ico" aria-hidden="true"><component :is="feat.icon" :size="15" /></span>{{ feat.title }}</h3>
              <p>{{ feat.text }}</p>
            </div>
          </article>
          <article class="lp-feat lp-feat-more">
            <h3>E ainda, na mesma assinatura</h3>
            <ul>
              <li v-for="item in MORE_FEATURES" :key="item.label"><component :is="item.icon" :size="15" aria-hidden="true" />{{ item.label }}</li>
            </ul>
          </article>
        </div>
      </div>
    </section>

    <!-- 06 Exemplos reais (escura) -->
    <section class="lp-sec is-night">
      <div class="lp-wrap">
        <p class="lp-kicker">Exemplos reais</p>
        <h2 class="lp-h2">Roteiros criados por <span class="is-brand">pessoas como você!</span></h2>
        <p class="lp-sub">Sem designer, sem programação. Clique e veja o roteiro completo do mesmo jeito que o passageiro recebe.</p>
        <p class="lp-swipe" aria-hidden="true">Arraste para o lado para ver mais</p>
        <div class="lp-exs lp-rail">
          <article v-for="example in EXAMPLES" :key="example.title" class="lp-ex">
            <div class="lp-ex-img">
              <img :src="example.image" :alt="`Roteiro ${example.title}`" loading="lazy" decoding="async" width="760" height="384" />
              <span class="lp-ex-badge">{{ example.badge }}</span>
            </div>
            <div class="lp-ex-body">
              <p class="lp-ex-meta">{{ example.agency }}</p>
              <h3 class="lp-ex-title">{{ example.title }}</h3>
              <p class="lp-ex-desc">{{ example.text }}</p>
              <p class="lp-ex-quote"><Quote :size="16" aria-hidden="true" />{{ example.quote }}</p>
              <a :href="example.url" class="lp-ex-link" target="_blank" rel="noopener">Abrir roteiro <ArrowUpRight :size="16" aria-hidden="true" /></a>
            </div>
          </article>
        </div>
        <p class="lp-closer">A sua apresentação pode ter o mesmo nível em poucos minutos.</p>
      </div>
    </section>

    <!-- 07 Como funciona (verde) -->
    <section class="lp-sec is-green">
      <div class="lp-wrap">
        <p class="lp-kicker">Como funciona</p>
        <h2 class="lp-h2">Onboarding em <span class="is-brand">menos de 3 minutos</span></h2>
        <div class="lp-steps">
          <div v-for="(step, index) in STEPS" :key="step.title" class="lp-step">
            <span class="lp-step-num">0{{ index + 1 }}</span>
            <div>
              <h3>{{ step.title }}</h3>
              <p>{{ step.text }}</p>
            </div>
          </div>
        </div>
        <div class="lp-steps-cta">
          <a href="#planos" class="lp-btn" @click.prevent="goToPlans()">Quero começar agora <ArrowRight :size="18" aria-hidden="true" /></a>
        </div>
      </div>
    </section>

    <!-- 08 Mais fácil que o Canva -->
    <section class="lp-sec is-mist">
      <div class="lp-wrap">
        <h2 class="lp-h2">Mais fácil que <span class="is-brand">editar no Canva!</span></h2>
        <p class="lp-sub lp-canva-sub">Veja o editor em 40 segundos: escolher uma seção, editar, conferir no celular e publicar.</p>
        <div class="lp-canva">
          <div class="lp-canva-visual">
            <div class="lp-canva-bar" aria-hidden="true"><i></i><i></i><i></i><span>Editor do Roteiro Online</span></div>
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

    <!-- 09 Para quem é (escura) -->
    <section class="lp-sec is-night">
      <div class="lp-wrap">
        <p class="lp-kicker">Para quem é</p>
        <h2 class="lp-h2">Feito para quem <span class="is-brand">vende viagem e experiência</span></h2>
        <div class="lp-audience">
          <div v-for="item in AUDIENCE" :key="item.title" class="lp-aud" :class="`is-${item.tone}`">
            <span class="lp-aud-ico" aria-hidden="true"><component :is="item.icon" :size="20" /></span>
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 10 Faixa: tudo o que vem na assinatura -->
    <section class="lp-sec is-green lp-marquee-sec" aria-label="O que vem na assinatura">
      <div class="lp-marquee">
        <div class="lp-marquee-track">
          <span v-for="(item, index) in marqueeItems" :key="index" :aria-hidden="index >= INCLUDED.length ? 'true' : undefined">
            <Sparkles :size="16" aria-hidden="true" />{{ item.short }}
          </span>
        </div>
      </div>
    </section>

    <!-- 11 Assinatura (escura): plano único, mensal ou anual (ofertas do Admin Master) -->
    <section id="planos" class="lp-sec is-night lp-sec-plans">
      <div class="lp-wrap">
        <p class="lp-kicker">Assinatura</p>
        <h2 class="lp-h2">Uma assinatura. <span class="is-brand">Tudo incluso.</span></h2>
        <p class="lp-sub lp-offer-sub">Sem plano básico e sem recurso bloqueado: você usa tudo desde o primeiro dia.</p>
        <div class="lp-offer">
          <div class="lp-offer-incl">
            <p class="lp-offer-title">O que vem na assinatura</p>
            <ul class="lp-incl">
              <li v-for="item in INCLUDED" :key="item.full">
                <Check :size="15" aria-hidden="true" /><span class="lp-incl-full">{{ item.full }}</span><span class="lp-incl-short">{{ item.short }}</span>
              </li>
            </ul>
            <div class="lp-offer-trust">
              <span v-for="item in TRUST" :key="item.label"><component :is="item.icon" :size="18" aria-hidden="true" />{{ item.label }}</span>
            </div>
            <p class="lp-offer-foot"><Sparkles :size="15" aria-hidden="true" />Mensal ou anual, é a mesma assinatura: muda só a forma de pagar.</p>
          </div>
          <div class="lp-price-box" :class="{ 'is-loading': salesPlanLoading }">
            <span v-if="cycle === 'annual' && salesMath && salesMath.savings > 0 && currentOffer" class="lp-best">Melhor escolha</span>
            <span v-else-if="cycle === 'monthly' && monthlyPromo" class="lp-best is-urgent">Oferta por tempo limitado</span>
            <div v-if="salesPlan.monthly && salesPlan.annual" class="lp-cycle" role="tablist" aria-label="Forma de pagamento">
              <button type="button" role="tab" :aria-selected="cycle === 'monthly'" :class="{ on: cycle === 'monthly' }" @click="cycle = 'monthly'">Mensal</button>
              <button type="button" role="tab" :aria-selected="cycle === 'annual'" :class="{ on: cycle === 'annual' }" @click="cycle = 'annual'">
                Anual<span v-if="salesMath && salesMath.savingsPercent > 0" class="lp-cycle-off">-{{ salesMath.savingsPercent }}%</span>
              </button>
            </div>
            <template v-if="currentOffer">
              <p v-if="cycle === 'monthly' && monthlyPromo && promoCountdown" class="lp-promo-clock">
                <Timer :size="14" aria-hidden="true" />termina em <b>{{ promoCountdown }}</b>
              </p>
              <p v-if="cycle === 'annual' && salesMath && salesMath.savings > 0" class="lp-anchor">
                de <s>{{ formatBRL(salesMath.twelveMonths) }}</s> por
              </p>
              <p v-else-if="cycle === 'monthly' && monthlyPromo" class="lp-anchor">
                de <s>{{ formatBRL(currentOffer.amount) }}</s> por
              </p>
              <!-- Anual: a parcela em destaque (ex.: 12x de R$ 97) e o valor à vista embaixo. -->
              <div v-if="annualInstallment" class="lp-price">
                <span class="cur">{{ annualInstallment.count }}x de R$</span><span class="val">{{ centsNumber(annualInstallment.value) }}</span>
              </div>
              <div v-else-if="cycle === 'monthly' && monthlyPromo" class="lp-price">
                <span class="cur">R$</span><span class="val">{{ priceNumber(monthlyPromo.amount) }}</span><span class="per">no 1º mês</span>
              </div>
              <div v-else class="lp-price">
                <span class="cur">R$</span><span class="val">{{ priceNumber(currentOffer.amount) }}</span><span class="per">{{ cycle === "annual" ? "/ano" : "/mês" }}</span>
              </div>
              <p v-if="annualInstallment" class="lp-price-eq">ou <b>{{ formatBRL(currentOffer.amount) }} à vista</b></p>
              <p v-else-if="cycle === 'annual' && salesMath" class="lp-price-eq">
                equivale a <b>{{ formatBRL(salesMath.perMonth, { cents: "always" }) }} por mês</b>
              </p>
              <p v-else-if="monthlyPromo" class="lp-price-eq">Depois, <b>{{ formatBRL(currentOffer.amount) }}/mês</b>. Sem fidelidade.</p>
              <p v-else class="lp-price-eq">Renova todo mês. <b>Sem fidelidade.</b></p>
              <p v-if="cycle === 'annual' && salesMath && salesMath.savings > 0" class="lp-price-save">
                Economize {{ formatBRL(salesMath.savings) }}<span class="lp-hide-sm">: 1 ano por menos de {{ salesMath.lessThanMonths }} meses do mensal</span>
              </p>
              <p v-if="perDay" class="lp-price-day">
                <Zap :size="14" aria-hidden="true" /><span>Menos de R$ {{ perDay }} por dia<span class="lp-hide-sm">: uma venda a mais já paga a assinatura</span>.</span>
              </p>
              <RouterLink :to="`/checkout/${currentOffer.key}`" class="lp-btn lp-btn-block">Quero assinar agora <ArrowRight :size="18" aria-hidden="true" /></RouterLink>
            </template>
            <template v-else-if="!salesPlanLoading">
              <p class="lp-price-eq">Fale com a gente para assinar.</p>
              <a :href="DEMO_URL" class="lp-btn lp-btn-block" target="_blank" rel="noopener">Falar com a equipe <ArrowRight :size="18" aria-hidden="true" /></a>
            </template>
            <p class="lp-price-guarantee"><ShieldCheck :size="15" aria-hidden="true" /><span>7 dias de garantia<span class="lp-hide-sm">: não gostou, devolvemos 100%</span>.</span></p>
            <p class="lp-price-pay">Cartão de crédito ou Pix automático</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 12 Garantia (verde) -->
    <section class="lp-sec is-green lp-sec-guarantee">
      <div class="lp-wrap lp-guarantee">
        <div class="lp-seal" aria-hidden="true">
          <ShieldCheck :size="26" />
          <b>7 dias</b>
          <small>de garantia</small>
        </div>
        <div>
          <p class="lp-kicker">Garantia incondicional</p>
          <h3>Teste sem risco</h3>
          <p>
            Você entra, usa, cria seu primeiro roteiro e valida na prática. Se entender que não é para o seu momento, a gente
            devolve 100% do valor. Sem burocracia, sem letras miúdas, sem justificativa obrigatória.
          </p>
        </div>
      </div>
    </section>

    <!-- 13 Perguntas -->
    <section class="lp-sec is-mist lp-sec-faq">
      <div class="lp-wrap">
        <p class="lp-kicker">Ainda tem dúvida?</p>
        <h2 class="lp-h2">Perguntas que a gente <span class="is-brand">mais escuta</span></h2>
        <div class="lp-faq" :class="{ 'is-all': faqAll }">
          <details v-for="item in faqItems" :key="item.q">
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

    <!-- 14 Chamada final (escura) -->
    <section class="lp-sec is-night lp-final">
      <div class="lp-wrap lp-final-inner">
        <img :src="logoWhite" alt="" class="lp-final-logo" width="240" height="72" aria-hidden="true" />
        <h2 class="lp-h2 lp-final-title">Publique hoje mesmo o seu <span class="is-brand">primeiro roteiro.</span></h2>
        <p class="lp-final-sub">
          Assine, entre na plataforma e publique em menos de 30 minutos. Se não gostar, devolvemos 100% do valor em 7 dias.
        </p>
        <div class="lp-ctas">
          <a href="#planos" class="lp-btn" @click.prevent="goToPlans()">Quero assinar <ArrowRight :size="18" aria-hidden="true" /></a>
          <a :href="DEMO_URL" class="lp-btn-ghost" target="_blank" rel="noopener">Agendar demonstração</a>
        </div>
        <p class="lp-final-note">Sem fidelidade · 7 dias de garantia · Cancelamento simples</p>
        <RouterLink to="/login" class="lp-login">Já é cliente? Entrar</RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  Briefcase,
  Bus,
  CalendarDays,
  ChartColumn,
  Check,
  ChevronDown,
  ChevronRight,
  CircleCheck,
  CircleX,
  Copy,
  CreditCard,
  EyeOff,
  FileText,
  Ghost,
  Mic,
  Globe,
  Hotel,
  Images,
  Link,
  Magnet,
  MapPinned,
  Megaphone,
  MessageCircle,
  MousePointer2,
  MousePointerClick,
  Quote,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Timer,
  TrendingDown,
  UserRound,
  UsersRound,
  Wine,
  X,
  Zap
} from "lucide-vue-next";
import { getPublicSalesPlan, type SalesPlan } from "../../services/checkout";
import { formatBRL, salesPlanMath } from "../../utils/salesPlan";
import logoWhite from "../../assets/lp/logo-branco.webp";
import editorMp4 from "../../assets/lp/editor.mp4";
import editorWebm from "../../assets/lp/editor.webm";
import editorPoster from "../../assets/lp/editor-poster.webp";
import assistantMp4 from "../../assets/lp/assistente.mp4";
import assistantWebm from "../../assets/lp/assistente.webm";
import assistantPoster from "../../assets/lp/assistente-poster.webp";
import exemploAbrolhos from "../../assets/lp/exemplo-abrolhos.webp";
import exemploFoz from "../../assets/lp/exemplo-foz.webp";
import exemploItalia from "../../assets/lp/exemplo-italia.webp";

/**
 * Página de vendas do Roteiro Online, trazida do Elementor (viajeon.com/roteiroonline1)
 * para dentro do sistema. A assinatura leva direto ao checkout próprio (/checkout/:offerKey).
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
    title: "seus clientes não vejam valor",
    text: "Quando o passageiro vê só o preço, compara por preço. Quando enxerga a experiência completa, compra a experiência."
  },
  {
    icon: TrendingDown,
    title: "você esteja concorrendo por preço",
    text: "Se a apresentação não sustenta o valor, o único argumento que sobra é desconto. Apresente melhor, venda pelo preço certo."
  }
];

// Assistente IA: como a página sai pronta e o que a agência pode mandar.
const AI_STEPS = [
  { title: "Conte a viagem do seu jeito", text: "Escreva, grave um áudio ou mande o PDF e os prints que você já tem." },
  { title: "A IA monta a página inteira", text: "Banner, roteiro dia a dia, inclusos, preços e dúvidas, com fotos." },
  { title: "Revise e publique", text: "Ajuste o que quiser no editor e mande o link no WhatsApp." }
];
const AI_INPUTS = [
  { icon: MessageCircle, label: "Texto" },
  { icon: Mic, label: "Áudio" },
  { icon: FileText, label: "PDF" },
  { icon: Images, label: "Prints e fotos" }
];

// Antes e depois. As linhas do "textão" são só a largura de cada linha cinza da bolha.
const CHAT_LINES = [96, 88, 100, 72, 94, 84, 60];
const BEFORE = [
  "Textão que ninguém lê até o fim",
  "PDF pesado que não abre no celular",
  "Arte do Canva para refazer a cada mudança",
  "Cliente compara só o preço"
];
const AFTER = [
  "Página bonita que abre em qualquer celular",
  "Um link só, sempre atualizado",
  "Botão de WhatsApp com mensagem pronta",
  "Cliente enxerga o valor antes do preço"
];

// visual: a mini-tela desenhada no topo do cartão; tone: a cor dela.
const FEATURES = [
  {
    icon: MousePointerClick,
    visual: "editor",
    tone: "green",
    title: "Editor visual e prático",
    text: "Seções prontas de capa, itinerário, inclusos e preços. É só trocar o conteúdo, sem conhecimento técnico."
  },
  {
    icon: CalendarDays,
    visual: "days",
    tone: "blue",
    title: "Itinerário dia a dia",
    text: "Cada dia vira uma aba clicável. O passageiro abre só o que quer ver, como num app de viagem."
  },
  {
    icon: MessageCircle,
    visual: "whats",
    tone: "whats",
    title: "Botão de WhatsApp",
    text: "Em qualquer seção, com mensagem pronta. O lead chega no seu WhatsApp já sabendo o roteiro."
  },
  {
    icon: CreditCard,
    visual: "prices",
    tone: "amber",
    title: "Cards de investimento",
    text: "Adulto, criança, apto duplo, triplo: quantas categorias de preço você precisar."
  },
  {
    icon: Timer,
    visual: "count",
    tone: "red",
    title: "Contagem regressiva",
    text: "Cria urgência real até a data da saída, sem precisar editar nada à mão."
  },
  {
    icon: ChartColumn,
    visual: "chart",
    tone: "violet",
    title: "Pixel Meta e Google",
    text: "Anuncie para a página e faça remarketing com quem viu e não fechou."
  },
  {
    icon: Magnet,
    visual: "form",
    tone: "pink",
    title: "Módulo Leads",
    text: "Formulário dentro do roteiro: cada interessado vira uma oportunidade de venda."
  }
];

const MORE_FEATURES = [
  { icon: Images, label: "Galeria com carrossel" },
  { icon: Copy, label: "Duplicar roteiro em um clique" },
  { icon: Globe, label: "Domínio próprio da agência" },
  { icon: Smartphone, label: "100% pensado para o celular" },
  { icon: Bot, label: "Assistente de IA" },
  { icon: Megaphone, label: "Criativos para anúncios" }
];

const FX_DAYS = ["Chegada e city tour", "Cataratas do Iguaçu", "Parque das Aves"];
const FX_BARS = [28, 42, 36, 58, 50, 74, 92];

// Contagem da mini-tela: corre de verdade (volta ao início quando chega a zero).
const COUNTDOWN_START = 12 * 86400 + 8 * 3600 + 45 * 60 + 30;
const countdownLeft = ref(COUNTDOWN_START);
const countdownParts = computed(() => {
  const s = countdownLeft.value;
  return [
    { value: Math.floor(s / 86400), label: "dias" },
    { value: Math.floor((s % 86400) / 3600), label: "horas" },
    { value: Math.floor((s % 3600) / 60), label: "min" },
    { value: s % 60, label: "seg" }
  ].map(part => ({ ...part, value: String(part.value).padStart(2, "0") }));
});
let countdownTimer: number | undefined;

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

// Para quem é (perfis atendidos pela plataforma).
const AUDIENCE = [
  { icon: Bus, tone: "green", title: "Agências de excursão", text: "Grupos, bate-volta e excursões com saídas confirmadas." },
  { icon: Briefcase, tone: "blue", title: "Agentes e operadoras", text: "Pacotes nacionais e internacionais com roteiro completo." },
  { icon: MapPinned, tone: "amber", title: "Receptivos e guias", text: "Passeios, transfers e roteiros no destino." },
  { icon: Hotel, tone: "violet", title: "Hotéis e pousadas", text: "Day use e roteiros para apresentar aos hóspedes." },
  { icon: Wine, tone: "pink", title: "Experiências", text: "Gastronomia, enoturismo, aventura, cultura e corporativo." },
  { icon: UsersRound, tone: "whats", title: "Times de vendas", text: "Equipe vendendo com o mesmo padrão de apresentação." }
];

// O que vem na assinatura: tudo o que a plataforma libera (plano interno Escala).
// short: a versão curta, em etiquetas, no celular e na faixa.
const INCLUDED = [
  { full: "Roteiros ilimitados no ar", short: "Roteiros ilimitados" },
  { full: "Editor visual com seções prontas", short: "Editor visual" },
  { full: "Assistente de IA para montar páginas", short: "Assistente de IA" },
  { full: "Criativos para anúncios e stories", short: "Criativos" },
  { full: "Módulo Leads e funil de vendas", short: "Módulo Leads" },
  { full: "Caixa de entrada do WhatsApp", short: "WhatsApp" },
  { full: "Domínio próprio da agência", short: "Domínio próprio" },
  { full: "Pixels Meta e Google", short: "Pixels Meta e Google" },
  { full: "Equipe com até 5 usuários", short: "Equipe (5 usuários)" },
  { full: "Duplicar páginas em um clique", short: "Duplicar páginas" }
];
// Selos no pé do cartão do que vem na assinatura (só no computador).
const TRUST = [
  { icon: ShieldCheck, label: "7 dias de garantia" },
  { icon: CalendarDays, label: "Mensal sem fidelidade" },
  { icon: CircleCheck, label: "Cancelamento simples" }
];
// A faixa corre em laço: a lista vai duas vezes (a cópia fica escondida do leitor de tela).
const marqueeItems = [...INCLUDED, ...INCLUDED];

// Plano único: oferta mensal e anual configuradas em Admin Master › Ofertas e checkout.
const salesPlan = ref<SalesPlan>({ monthly: null, annual: null });
const salesPlanLoading = ref(true);
const cycle = ref<"monthly" | "annual">("annual");
const salesMath = computed(() => salesPlanMath(salesPlan.value.monthly?.amount, salesPlan.value.annual?.amount));
const currentOffer = computed(() => salesPlan.value[cycle.value] || salesPlan.value.monthly || salesPlan.value.annual);
const priceNumber = (amount: string) => formatBRL(amount, { cents: "auto" }).replace(/^R\$\s*/, "");
const centsNumber = (amount: string) => formatBRL(amount, { cents: "always" }).replace(/^R\$\s*/, "");
// Anual parcelado no cartão (ex.: 12x de R$ 97,00), configurado na oferta no Admin Master.
const annualInstallment = computed(() => {
  const offer = currentOffer.value;
  if (cycle.value !== "annual" || !offer || offer.billing_cycle !== "annual" || (offer.max_installments || 1) <= 1 || !offer.installment_value) return null;
  return { count: offer.max_installments || 1, value: offer.installment_value };
});
// Promoção da 1ª mensalidade (só enquanto vale; o servidor já tira a que acabou).
const nowMs = ref(Date.now());
const monthlyPromo = computed(() => {
  const offer = salesPlan.value.monthly;
  if (!offer?.first_payment_amount) return null;
  const endsAt = offer.first_payment_ends_at ? new Date(offer.first_payment_ends_at).getTime() : null;
  if (endsAt !== null && endsAt <= nowMs.value) return null;
  return { amount: offer.first_payment_amount, endsAt };
});
const promoCountdown = computed(() => {
  const endsAt = monthlyPromo.value?.endsAt;
  if (!endsAt) return "";
  const total = Math.max(0, Math.floor((endsAt - nowMs.value) / 1000));
  const days = Math.floor(total / 86400);
  const pad = (value: number) => String(value).padStart(2, "0");
  const clock = `${pad(Math.floor((total % 86400) / 3600))}:${pad(Math.floor((total % 3600) / 60))}:${pad(total % 60)}`;
  return days > 0 ? `${days}d ${clock}` : clock;
});
// "Menos de R$ X por dia": o próximo real inteiro acima do valor diário.
const perDay = computed(() => {
  const offer = currentOffer.value;
  const amount = Number(offer?.amount);
  if (!offer || !Number.isFinite(amount) || amount <= 0) return null;
  return Math.floor(amount / (offer.billing_cycle === "annual" ? 365 : 30)) + 1;
});
const loadSalesPlan = async () => {
  try {
    salesPlan.value = await getPublicSalesPlan();
    // Abre no anual (melhor valor); sem anual, no mensal.
    if (!salesPlan.value.annual) cycle.value = "monthly";
  } catch {
    salesPlan.value = { monthly: null, annual: null };
  } finally {
    salesPlanLoading.value = false;
  }
};

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
    a: "Pode. No mensal não existe fidelidade: cancelou, não renova. No anual, cancelar impede a renovação do ano seguinte. E nos dois você tem 7 dias de garantia: se não gostar, devolvemos 100% do valor sem justificativa obrigatória."
  },
  {
    q: "E se eu for agência de receptivo, guia ou operadora, funciona pra mim?",
    a: "Funciona. A plataforma foi desenhada para agências de excursão, operadoras, receptivos, guias e agentes de viagem. Também é usada por hotéis com day use, pousadas com roteiros para hóspedes e operadores de experiência (gastronomia, aventura, cultural, corporativo)."
  },
  {
    q: "Posso usar nos anúncios do Facebook/Instagram/Google?",
    a: "Sim. Você conecta os pixels da Meta e do Google e acompanha quem abriu cada roteiro. Ideal para fazer remarketing com quem viu e não fechou."
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
    a: "Sim, já vem na assinatura. Você conecta seu domínio próprio e os roteiros ficam em",
    strong: "seusite.com.br/roteiros",
    after: "ou no formato que preferir."
  },
  {
    q: "Tem limite de roteiros?",
    a: "Não. A assinatura inclui roteiros ilimitados no ar, com todos os recursos liberados, do primeiro ao último."
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
const aiVideo = ref<HTMLVideoElement | null>(null);

// "Mensal ou anual?" com os valores do admin; sem eles, a resposta sem números.
const faqItems = computed<FaqItem[]>(() => {
  const m = salesPlan.value.monthly;
  const a = salesPlan.value.annual;
  const math = salesMath.value;
  const promo = monthlyPromo.value;
  const installments =
    a && (a.max_installments || 1) > 1 && a.installment_value
      ? ` à vista ou em ${a.max_installments}x de ${formatBRL(a.installment_value, { cents: "always" })} no cartão`
      : "";
  const promoNote = promo ? ` Por tempo limitado, a 1ª mensalidade sai por ${formatBRL(promo.amount, { cents: "auto" })}.` : "";
  const cycleAnswer =
    m && a && math && math.savings > 0
      ? `Nenhuma nos recursos: é a mesma assinatura, com tudo incluso. No mensal você paga ${formatBRL(m.amount)} por mês, sem fidelidade.${promoNote} No anual paga ${formatBRL(a.amount)}${installments} pelos 12 meses e economiza ${formatBRL(math.savings)} frente a 12 mensalidades.`
      : "Nenhuma nos recursos: é a mesma assinatura, com tudo incluso. Muda só a forma de pagar: mês a mês, sem fidelidade, ou o ano inteiro com desconto.";
  const items = [...FAQ];
  items.splice(2, 0, { q: "Qual a diferença entre o mensal e o anual?", a: cycleAnswer });
  return items;
});

const goToPlans = (target?: "monthly" | "annual") => {
  if (target && salesPlan.value[target]) cycle.value = target;
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
  void loadSalesPlan();
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  for (const video of [editorVideo.value, aiVideo.value]) {
    if (video && reducedMotion) {
      video.autoplay = false;
      video.pause();
      video.controls = true;
    }
  }
  if (!reducedMotion) {
    countdownTimer = window.setInterval(() => {
      countdownLeft.value = countdownLeft.value > 0 ? countdownLeft.value - 1 : COUNTDOWN_START;
      nowMs.value = Date.now();
    }, 1000);
  }
  trackPageView();
});

onBeforeUnmount(() => {
  document.title = previousTitle;
  restoreDescription?.();
  window.clearInterval(countdownTimer);
});
</script>

<style scoped>
/* Página de vendas no design system do painel (Inter no texto, Sora nos títulos, verde da marca),
   com seções que se alternam entre escura, clara e verde. As cores são fixas: a página fica igual
   com o painel no tema claro ou escuro.
   Cada seção cabe numa tela (de 1920×940 a 360×640): tamanhos limitados pela altura da tela e,
   no celular, listas longas viram trilhos de arrastar para o lado. */
.lp {
  --lp-pad-y: clamp(32px, 6svh, 64px);
  --lp-pad-x: 24px;
  --ink: #0b1712;
  --muted: #55665e;
  --line: #dbe6e0;
  --mist: #eef6f2;
  --night: #07130e;
  --night-card: #0f2119;
  --green: #12b981;
  --green-dark: #0b7a5b;
  --green-deep: #064e3b;
  --mint: #1de9a0;
  --red: #e5484d;
  --whats: #22c55e;
  --blue: #3b82f6;
  --amber: #f59e0b;
  --violet: #8b5cf6;
  --pink: #ec4899;
  min-height: 100vh;
  overflow-x: clip;
  background: #fff;
  color: var(--ink);
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

/* Seções e seus temas: cada um define as cores que os componentes de dentro usam. */
.lp-sec {
  --t-ink: var(--ink);
  --t-muted: var(--muted);
  --t-card: #fff;
  --t-line: var(--line);
  --t-accent: var(--green-dark);
  --t-btn: var(--green);
  --t-btn-ink: #fff;
  --t-btn-hover: var(--green-dark);
  position: relative;
  padding: var(--lp-pad-y) var(--lp-pad-x);
  background: #fff;
  color: var(--t-ink);
}
.lp-sec.is-mist {
  background: var(--mist);
}
.lp-sec.is-night {
  --t-ink: #f2f7f4;
  --t-muted: #a3b8ae;
  --t-card: var(--night-card);
  --t-line: rgba(255, 255, 255, 0.09);
  --t-accent: var(--mint);
  --t-btn: var(--mint);
  --t-btn-ink: #05170f;
  --t-btn-hover: #5ff3bd;
  background:
    radial-gradient(ellipse 55% 60% at 100% 0%, rgba(29, 233, 160, 0.1), transparent 70%),
    var(--night);
}
.lp-sec.is-green {
  --t-ink: #fff;
  --t-muted: rgba(255, 255, 255, 0.85);
  --t-line: rgba(255, 255, 255, 0.22);
  --t-accent: #d1fae5;
  --t-btn: #fff;
  --t-btn-ink: var(--green-deep);
  --t-btn-hover: #ecfdf5;
  background:
    radial-gradient(ellipse 60% 80% at 90% 0%, rgba(29, 233, 160, 0.35), transparent 70%),
    linear-gradient(135deg, var(--green-dark) 0%, #0f9e70 55%, var(--green) 100%);
}
.lp-wrap {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
}
.lp-kicker {
  margin-bottom: 8px !important;
  color: var(--t-accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-align: center;
  text-transform: uppercase;
}
.lp-h1 {
  color: var(--t-ink);
  font-size: clamp(30px, min(3.4vw, 5.8svh), 50px);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.03em;
}
.lp-h2 {
  max-width: 820px;
  margin: 0 auto !important;
  color: var(--t-ink);
  font-size: clamp(24px, min(2.6vw, 4.5svh), 36px);
  font-weight: 700;
  line-height: 1.16;
  letter-spacing: -0.02em;
  text-align: center;
}
.is-brand {
  color: var(--t-accent);
}
/* No fundo verde, o destaque vira um marca-texto escuro (verde sobre verde não aparece). */
.is-green .is-brand {
  padding: 0 0.18em;
  border-radius: 8px;
  background: rgba(4, 47, 34, 0.42);
  color: #fff;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}
.is-red {
  color: var(--red);
}
.lp-sub {
  max-width: 700px;
  margin: 10px auto 0 !important;
  color: var(--t-muted);
  font-size: 15px;
  line-height: 1.55;
  text-align: center;
}
.lp-note {
  margin-top: 14px !important;
  color: var(--t-muted);
  font-size: 13px;
  text-align: center;
}
.lp-note svg {
  display: inline-block;
  margin-right: 2px;
  color: var(--t-accent);
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
  height: 50px;
  padding: 0 24px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}
.lp-btn {
  background: var(--t-btn);
  color: var(--t-btn-ink);
  box-shadow: 0 14px 28px -14px rgba(18, 185, 129, 0.8);
}
.lp-btn:hover {
  background: var(--t-btn-hover);
  transform: translateY(-1px);
}
.lp-btn-ghost {
  border: 1px solid var(--t-line);
  background: transparent;
  color: var(--t-ink);
}
.lp-btn-ghost:hover {
  border-color: var(--t-accent);
  color: var(--t-accent);
}
.lp .lp-btn:focus-visible,
.lp .lp-btn-ghost:focus-visible {
  outline: 2px solid var(--t-accent);
  outline-offset: 3px;
}

/* Cartões: base sólida comum */
.lp-pain,
.lp-cmp,
.lp-feat,
.lp-ex,
.lp-step,
.lp-aud,
.lp-offer-incl {
  border: 1px solid var(--t-line);
  border-radius: 18px;
  background: var(--t-card);
}
.is-mist .lp-pain,
.is-mist .lp-feat {
  box-shadow: 0 1px 2px rgba(11, 23, 18, 0.04), 0 12px 28px -18px rgba(11, 23, 18, 0.28);
}

/* 01 Capa */
.lp-hero {
  padding-top: clamp(20px, 4svh, 40px);
  padding-bottom: clamp(24px, 5svh, 48px);
  background:
    radial-gradient(ellipse 45% 60% at 82% 30%, rgba(29, 233, 160, 0.22), transparent 70%),
    radial-gradient(ellipse 40% 55% at 0% 100%, rgba(18, 185, 129, 0.16), transparent 70%),
    var(--night);
}
/* Grade sutil no fundo da capa. */
.lp-hero::before {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
  background-size: 48px 48px;
  content: "";
  -webkit-mask-image: radial-gradient(ellipse 70% 70% at 60% 40%, #000 30%, transparent 75%);
  mask-image: radial-gradient(ellipse 70% 70% at 60% 40%, #000 30%, transparent 75%);
  pointer-events: none;
}
.lp-hero-grid {
  position: relative;
  display: grid;
  grid-template-areas:
    ". video"
    "copy video"
    "actions video"
    ". video";
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-rows: 1fr auto auto 1fr;
  column-gap: clamp(32px, 4vw, 64px);
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
  border: 1px solid rgba(29, 233, 160, 0.35);
  border-radius: 999px;
  background: rgba(29, 233, 160, 0.12);
  color: var(--mint);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.lp-lead {
  max-width: 520px;
  color: var(--t-muted);
  font-size: clamp(16px, 1.35vw, 19px);
  line-height: 1.55;
}
.lp-lead strong {
  color: var(--t-ink);
}
/* Vídeo quadrado, do tamanho que cabe na altura da tela, com dois avisos flutuando. */
.lp-hero-media {
  position: relative;
  grid-area: video;
  align-self: center;
  width: min(42vw, calc(100vh - 96px), 560px);
  width: min(42vw, calc(100svh - 96px), 560px);
}
.lp-hero-video {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 22px;
  background: #0c100e;
  box-shadow: 0 0 0 1px rgba(29, 233, 160, 0.35), 0 0 0 8px rgba(29, 233, 160, 0.07), 0 30px 80px -30px rgba(29, 233, 160, 0.45);
}
.lp-hero-video iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.lp-float {
  position: absolute;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px 10px 10px;
  border-radius: 14px;
  background: #fff;
  color: var(--ink);
  box-shadow: 0 18px 40px -16px rgba(0, 0, 0, 0.55);
  pointer-events: none;
}
.lp-float b {
  display: block;
  font-size: 13px;
  line-height: 1.2;
}
.lp-float small {
  display: block;
  color: var(--muted);
  font-size: 11.5px;
  line-height: 1.3;
}
.lp-float-ico {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--green);
  color: #fff;
}
.lp-float-ico.is-whats {
  background: var(--whats);
}
.lp-float-a {
  top: 9%;
  left: -34px;
  animation: lp-bob 5s ease-in-out infinite;
}
.lp-float-b {
  right: -22px;
  bottom: 10%;
  animation: lp-bob 5s ease-in-out 2.5s infinite;
}
@keyframes lp-bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}
.lp-hero-actions {
  grid-area: actions;
}
.lp-hero .lp-note {
  text-align: left;
}

/* Faixa da promoção da 1ª mensalidade */
.lp-promo-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px 14px;
  min-height: 40px;
  padding: 7px 16px;
  background: linear-gradient(90deg, #ff7a2f, #ff9b3d);
  color: #2a1203;
  font-size: 14px;
  text-align: center;
  text-decoration: none;
}
.lp-promo-bar b {
  font-weight: 800;
}
.lp-promo-tag {
  padding: 3px 9px;
  border-radius: 999px;
  background: #2a1203;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.lp-promo-time {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

/* 02 Números */
.lp-metrics-sec {
  padding-top: 22px;
  padding-bottom: 22px;
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
  border-left: 1px solid var(--t-line);
}
.lp-metric-num {
  color: #fff;
  font-family: var(--font-display);
  font-size: clamp(26px, 2.6vw, 36px);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
}
.lp-metric-lbl {
  margin-top: 4px;
  color: var(--t-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* 03 Assistente IA: texto e passos à esquerda, a animação à direita. */
.lp-ai {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  align-items: center;
  gap: clamp(24px, 4vw, 48px);
}
.lp-ai-copy .lp-kicker,
.lp-ai-copy .lp-h2,
.lp-ai-copy .lp-sub {
  margin-inline: 0 !important;
  text-align: left;
}
.lp-ai-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 20px 0 0;
  padding: 0;
  list-style: none;
}
.lp-ai-steps li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--t-line);
  border-radius: 14px;
  background: var(--t-card);
}
.lp-ai-num {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--mint);
  color: #05170f;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 800;
}
.lp-ai-steps h3 {
  color: var(--t-ink);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.3;
}
.lp-ai-steps p {
  margin-top: 2px !important;
  color: var(--t-muted);
  font-size: 13.5px;
  line-height: 1.45;
}
.lp-ai-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 14px;
}
.lp-ai-chips span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border: 1px solid rgba(29, 233, 160, 0.3);
  border-radius: 999px;
  background: rgba(29, 233, 160, 0.08);
  color: var(--mint);
  font-size: 12.5px;
  font-weight: 600;
}
.lp-ai-visual {
  overflow: hidden;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 0 0 1px rgba(29, 233, 160, 0.35), 0 30px 70px -30px rgba(29, 233, 160, 0.5);
}
.lp-ai-visual video {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 10;
}

/* 04 Dores: cartões brancos com faixa vermelha no topo. */
.lp-pains {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 28px;
}
.lp-pain {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
  padding: 24px 22px 22px;
}
.lp-pain::before {
  position: absolute;
  inset: 0 0 auto;
  height: 4px;
  background: var(--red);
  content: "";
}
.lp-pain-ico {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: var(--red);
  color: #fff;
  box-shadow: 0 10px 20px -10px rgba(229, 72, 77, 0.8);
}
.lp-pain-num {
  display: block;
  margin-bottom: 4px;
  color: var(--red);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.1em;
}
.lp-pain h3 {
  color: var(--t-ink);
  font-size: 17px;
  font-weight: 700;
  line-height: 1.3;
}
.lp-pain h3::first-letter {
  text-transform: uppercase;
}
.lp-pain p {
  margin-top: 6px !important;
  color: var(--t-muted);
  font-size: 14px;
  line-height: 1.5;
}

/* 04 Antes e depois */
.lp-compare {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 16px;
  max-width: 980px;
  margin: 26px auto 0;
}
.lp-cmp {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 18px 20px 20px;
}
.lp-cmp.is-after {
  border-color: transparent;
  background: linear-gradient(160deg, var(--green) 0%, var(--green-dark) 100%);
  box-shadow: 0 24px 60px -30px rgba(29, 233, 160, 0.6);
}
.lp-cmp-mock {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  height: clamp(112px, 19svh, 156px);
  margin-bottom: 14px;
  overflow: hidden;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
}
.is-after .lp-cmp-mock {
  background: rgba(4, 47, 34, 0.25);
}
.lp-chat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  width: min(78%, 280px);
}
.lp-chat-bubble {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%;
  padding: 10px 12px 6px;
  border-radius: 12px 12px 2px 12px;
  background: #1f3b2f;
}
.lp-skel {
  display: block;
  height: 6px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.22);
}
.lp-chat-bubble small {
  align-self: flex-end;
  color: rgba(255, 255, 255, 0.45);
  font-size: 9.5px;
}
.lp-chat-file {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 10px;
  background: #1f3b2f;
  color: #fca5a5;
  font-size: 11px;
}
.lp-chat-file span {
  color: rgba(255, 255, 255, 0.75);
}
.lp-chat-file small {
  color: rgba(255, 255, 255, 0.45);
}
.lp-phone {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100px;
  height: 150px;
  padding: 5px 5px 8px;
  border: 3px solid #0b1712;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 14px 30px -12px rgba(0, 0, 0, 0.5);
  transform: translateY(18px);
}
.lp-phone img {
  width: 100%;
  height: 52px;
  border-radius: 9px;
  object-fit: cover;
}
.lp-phone-title {
  color: var(--ink);
  font-family: var(--font-display);
  font-size: 9px;
  font-weight: 700;
}
.lp-phone .lp-skel {
  height: 4px;
  background: #dbe6e0;
}
.lp-phone .lp-skel.is-short {
  width: 64%;
}
.lp-phone-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  margin-top: 2px;
  padding: 4px 0;
  border-radius: 6px;
  background: var(--whats);
  color: #fff;
  font-size: 7.5px;
  font-weight: 700;
  white-space: nowrap;
}
.lp-link-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 11px;
  border-radius: 999px;
  background: #fff;
  color: var(--muted);
  font-size: 11.5px;
  white-space: nowrap;
  box-shadow: 0 10px 24px -12px rgba(0, 0, 0, 0.45);
}
.lp-link-chip svg {
  color: var(--green);
}
.lp-link-chip b {
  color: var(--ink);
}
.lp-cmp-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px !important;
  color: var(--t-ink);
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
}
.is-before .lp-cmp-label svg {
  color: var(--red);
}
.is-after .lp-cmp-label {
  color: #fff;
}
.lp-cmp-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.lp-cmp-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--t-muted);
  font-size: 14.5px;
  line-height: 1.4;
}
.lp-cmp-list svg {
  flex: none;
  margin-top: 2px;
  padding: 2px;
  border-radius: 50%;
  background: rgba(229, 72, 77, 0.18);
  color: #ff8a8d;
}
.is-after .lp-cmp-list li {
  color: #fff;
  font-weight: 600;
}
.is-after .lp-cmp-list svg {
  background: #fff;
  color: var(--green-dark);
}
.lp-cmp-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--mint);
  color: #05170f;
  box-shadow: 0 0 0 6px rgba(29, 233, 160, 0.14);
}

/* 05 Funcionalidades: cartão com mini-tela colorida em cima e o texto embaixo. */
.lp-sec .lp-feats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 24px;
}
.lp-feat {
  --tone: var(--green);
  --tone-soft: #e3f8ef;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.lp-feat:hover {
  transform: translateY(-3px);
}
.lp-feat.is-blue {
  --tone: var(--blue);
  --tone-soft: #e6effe;
}
.lp-feat.is-whats {
  --tone: #16a34a;
  --tone-soft: #e3f7e9;
}
.lp-feat.is-amber {
  --tone: #d97706;
  --tone-soft: #fef3dc;
}
.lp-feat.is-red {
  --tone: var(--red);
  --tone-soft: #fde8e8;
}
.lp-feat.is-violet {
  --tone: var(--violet);
  --tone-soft: #efe9fe;
}
.lp-feat.is-pink {
  --tone: #db2777;
  --tone-soft: #fde7f1;
}
.lp-fx {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: clamp(84px, 14svh, 124px);
  padding: 12px 14px;
  overflow: hidden;
  background:
    radial-gradient(circle at 85% 15%, rgba(255, 255, 255, 0.9), transparent 55%),
    var(--tone-soft);
}
.lp-feat-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px 16px;
}
.lp-feat h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--t-ink);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.25;
}
.lp-feat-ico {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: var(--tone);
  color: #fff;
}
.lp-feat p {
  color: var(--t-muted);
  font-size: 13px;
  line-height: 1.45;
}
/* Mini-telas */
.fx-editor {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 78%;
}
.fx-block {
  position: relative;
  display: block;
  height: 16px;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(11, 23, 18, 0.08);
}
.fx-block.is-on {
  height: 24px;
  outline: 2px solid var(--tone);
  outline-offset: 1px;
}
.fx-tag {
  position: absolute;
  top: -9px;
  left: 8px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--tone);
  color: #fff;
  font-size: 9.5px;
  font-weight: 700;
}
.fx-cursor {
  position: absolute;
  right: 10%;
  bottom: -6px;
  color: var(--ink);
  fill: #fff;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.25));
}
.fx-days {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 88%;
}
.fx-day {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 7px;
  background: #fff;
  color: var(--muted);
  font-size: 10.5px;
  white-space: nowrap;
}
.fx-day b {
  color: var(--tone);
  font-size: 10.5px;
}
.fx-day svg {
  margin-left: auto;
  color: var(--muted);
}
.fx-day.is-open {
  padding-block: 8px;
  color: var(--ink);
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--tone);
}
.fx-whats {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  width: 86%;
}
.fx-bubble {
  max-width: 92%;
  padding: 7px 10px;
  border-radius: 10px 10px 10px 2px;
  background: #fff;
  color: var(--ink);
  font-size: 10.5px;
  line-height: 1.35;
  box-shadow: 0 1px 2px rgba(11, 23, 18, 0.08);
}
.fx-wbtn {
  display: inline-flex;
  align-self: flex-end;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border-radius: 999px;
  background: var(--whats);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  box-shadow: 0 8px 16px -8px rgba(34, 197, 94, 0.9);
}
.fx-prices {
  display: flex;
  gap: 8px;
}
.fx-price {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 8px 10px;
  border-top: 3px solid var(--tone);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(11, 23, 18, 0.08);
}
.fx-price small {
  color: var(--muted);
  font-size: 9.5px;
  font-weight: 600;
  text-transform: uppercase;
}
.fx-price b {
  color: var(--ink);
  font-family: var(--font-display);
  font-size: 15px;
}
.fx-price em {
  color: var(--muted);
  font-size: 9px;
  font-style: normal;
}
.fx-price.is-alt {
  transform: translateY(8px);
}
.fx-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.fx-count small {
  color: var(--tone);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.fx-count-row {
  display: flex;
  gap: 5px;
}
.fx-count-row > span {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 38px;
  padding: 5px 4px 4px;
  border-radius: 8px;
  background: var(--ink);
  color: rgba(255, 255, 255, 0.6);
  font-size: 8.5px;
}
.fx-count-row b {
  color: #fff;
  font-family: var(--font-display);
  font-size: 17px;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}
.fx-chart {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
  width: 80%;
  height: 100%;
}
.fx-bars {
  display: flex;
  flex: 1;
  align-items: flex-end;
  gap: 6px;
  padding: 0 4px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.3);
}
.fx-bars span {
  flex: 1;
  border-radius: 4px 4px 0 0;
  background: linear-gradient(180deg, var(--tone), rgba(139, 92, 246, 0.55));
}
.fx-chart-tags {
  display: flex;
  gap: 5px;
}
.fx-chart-tags span {
  padding: 2px 8px;
  border-radius: 999px;
  background: #fff;
  color: var(--tone);
  font-size: 9.5px;
  font-weight: 700;
}
.fx-form {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 70%;
}
.fx-input {
  padding: 5px 8px;
  border: 1px solid #e5d3dd;
  border-radius: 6px;
  background: #fff;
  color: #9a8a92;
  font-size: 9.5px;
}
.fx-submit {
  padding: 6px 8px;
  border-radius: 6px;
  background: var(--tone);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  text-align: center;
}
.fx-toast {
  position: absolute;
  top: -6px;
  right: -26%;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--ink);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  box-shadow: 0 8px 16px -8px rgba(0, 0, 0, 0.6);
}
/* Último cartão: o que mais vem na assinatura. */
.lp-feat-more {
  justify-content: center;
  padding: 18px;
  border-color: transparent;
  background:
    radial-gradient(ellipse 80% 60% at 100% 0%, rgba(29, 233, 160, 0.25), transparent 70%),
    var(--night);
  color: #fff;
}
.lp-feat-more h3 {
  color: #fff;
  font-size: 16px;
}
.lp-feat-more ul {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
}
.lp-feat-more li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #d5e3dc;
  font-size: 13px;
  font-weight: 500;
}
.lp-feat-more li svg {
  flex: none;
  color: var(--mint);
}

/* 06 Exemplos */
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
  transition: border-color 0.2s ease, transform 0.2s ease;
}
.lp-ex:hover {
  border-color: rgba(29, 233, 160, 0.45);
  transform: translateY(-3px);
}
.lp-ex-img {
  position: relative;
}
.lp-ex img {
  display: block;
  width: 100%;
  height: clamp(120px, 19svh, 190px);
  object-fit: cover;
}
.lp-ex-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 4px 9px;
  border-radius: 999px;
  background: var(--mint);
  color: #05170f;
  font-size: 10.5px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.lp-ex-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
}
.lp-ex-meta {
  color: var(--t-muted);
  font-size: 12px;
  font-weight: 600;
}
.lp-ex-title {
  color: var(--t-ink);
  font-size: 18px;
  font-weight: 700;
}
.lp-ex-desc {
  color: var(--t-muted);
  font-size: 13.5px;
  line-height: 1.45;
}
.lp-ex-quote {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(29, 233, 160, 0.07);
  color: #e3eee9;
  font-size: 13px;
  font-style: italic;
  line-height: 1.45;
}
.lp-ex-quote svg {
  flex: none;
  color: var(--mint);
  fill: var(--mint);
}
.lp-ex-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 40px;
  margin-top: auto;
  border: 1px solid rgba(29, 233, 160, 0.5);
  border-radius: 10px;
  color: var(--mint);
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  transition: background-color 0.2s ease, color 0.2s ease;
}
.lp-ex-link:hover {
  background: var(--mint);
  color: #05170f;
}
.lp-closer {
  margin-top: 20px !important;
  color: var(--t-ink);
  font-size: 15px;
  font-weight: 600;
  text-align: center;
}

/* 07 Como funciona: cartões brancos sobre o verde. */
.lp-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 26px;
}
.lp-step {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 22px;
  border-color: transparent;
  background: #fff;
  box-shadow: 0 24px 40px -26px rgba(4, 47, 34, 0.7);
}
.lp-step-num {
  color: var(--green);
  font-family: var(--font-display);
  font-size: clamp(30px, 5svh, 40px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
}
.lp-step h3 {
  color: var(--ink);
  font-size: 17px;
  font-weight: 700;
  line-height: 1.3;
}
.lp-step p {
  margin-top: 6px !important;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.5;
}
.lp-steps-cta {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 08 Mais fácil que o Canva */
.lp-canva {
  display: grid;
  grid-template-columns: 1.35fr 0.65fr;
  align-items: center;
  gap: 28px;
  margin-top: 22px;
}
.lp-canva-visual {
  overflow: hidden;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 0 0 1px var(--line), 0 30px 60px -30px rgba(11, 23, 18, 0.45);
}
.lp-canva-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 12px;
  background: var(--night);
}
.lp-canva-bar i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #ff5f57;
}
.lp-canva-bar i:nth-child(2) {
  background: #febc2e;
}
.lp-canva-bar i:nth-child(3) {
  background: #28c840;
}
.lp-canva-bar span {
  margin-left: 8px;
  color: #a3b8ae;
  font-size: 11.5px;
  font-weight: 600;
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
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  color: var(--ink);
  font-size: 15px;
  font-weight: 600;
  box-shadow: 0 10px 22px -18px rgba(11, 23, 18, 0.35);
}
.lp-check {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--green);
  color: #fff;
}

/* 09 Para quem é: ícones coloridos em cartões escuros. */
.lp-audience {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 24px;
}
.lp-aud {
  --tone: var(--green);
  display: flex;
  gap: 14px;
  padding: 20px;
  transition: border-color 0.2s ease;
}
.lp-aud:hover {
  border-color: var(--tone);
}
.lp-aud.is-blue {
  --tone: var(--blue);
}
.lp-aud.is-amber {
  --tone: var(--amber);
}
.lp-aud.is-violet {
  --tone: var(--violet);
}
.lp-aud.is-pink {
  --tone: var(--pink);
}
.lp-aud.is-whats {
  --tone: var(--whats);
}
.lp-aud-ico {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--tone);
  color: #fff;
}
.lp-aud h3 {
  color: var(--t-ink);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
}
.lp-aud p {
  margin-top: 4px !important;
  color: var(--t-muted);
  font-size: 13.5px;
  line-height: 1.45;
}

/* 10 Faixa que corre */
.lp-marquee-sec {
  padding: 0;
}
.lp-marquee {
  overflow: hidden;
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent);
  mask-image: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent);
}
.lp-marquee-track {
  display: flex;
  width: max-content;
  animation: lp-marquee 40s linear infinite;
}
.lp-marquee-track span {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 22px;
  color: #fff;
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}
.lp-marquee-track svg {
  color: var(--t-accent);
}
@keyframes lp-marquee {
  to {
    transform: translateX(-50%);
  }
}

/* 11 Assinatura: o que vem nela à esquerda, o preço (cartão branco) à direita. */
.lp-sec-plans {
  background:
    radial-gradient(ellipse 50% 60% at 75% 55%, rgba(29, 233, 160, 0.16), transparent 70%),
    var(--night);
}
.lp-offer {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
  align-items: stretch;
  gap: 16px;
  max-width: 980px;
  margin: 24px auto 0;
}
.lp-offer-incl {
  display: flex;
  flex-direction: column;
  padding: 24px;
}
.lp-offer-title {
  margin-bottom: 14px !important;
  color: var(--t-ink);
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
}
.lp-incl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.lp-incl li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--t-ink);
  font-size: 14.5px;
  font-weight: 500;
  line-height: 1.4;
}
.lp-incl li svg {
  display: block;
  flex: none;
  margin-top: 1px;
  padding: 2px;
  border-radius: 50%;
  background: var(--mint);
  color: #05170f;
}
.lp-incl-short {
  display: none;
}
.lp-offer-trust {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: auto;
  padding-top: 18px;
}
.lp-offer-trust span {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(29, 233, 160, 0.08);
  color: var(--t-ink);
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.3;
}
.lp-offer-trust svg {
  color: var(--mint);
}
.lp-offer-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px !important;
  padding-top: 14px;
  border-top: 1px solid var(--t-line);
  color: var(--t-muted);
  font-size: 13.5px;
}
.lp-offer-foot svg {
  flex: none;
  color: var(--mint);
}
/* O cartão do preço é claro, com as cores do tema claro. */
.lp-price-box {
  --t-ink: var(--ink);
  --t-muted: var(--muted);
  --t-line: var(--line);
  --t-accent: var(--green-dark);
  --t-btn: var(--green);
  --t-btn-ink: #fff;
  --t-btn-hover: var(--green-dark);
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-height: 360px;
  padding: 26px 24px 22px;
  border-radius: 20px;
  background: linear-gradient(180deg, #e3f8ef 0%, #fff 42%);
  box-shadow: 0 0 0 2px var(--mint), 0 30px 70px -30px rgba(29, 233, 160, 0.55);
  color: var(--ink);
  text-align: center;
}
.lp-price-box.is-loading {
  opacity: 0.6;
}
.lp-best {
  position: absolute;
  top: -13px;
  left: 50%;
  padding: 5px 12px;
  border-radius: 999px;
  background: var(--mint);
  color: #05170f;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
  transform: translateX(-50%);
}
.lp-cycle {
  display: inline-flex;
  gap: 4px;
  margin-bottom: 6px;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
}
.lp-cycle button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}
.lp-cycle button.on {
  background: var(--ink);
  color: #fff;
}
.lp-cycle-off {
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--green);
  color: #fff;
  font-size: 11px;
}
.lp-anchor {
  color: var(--muted);
  font-size: 14px;
}
/* Urgência (laranja só aqui): selo e contagem da promoção da 1ª mensalidade. */
.lp-best.is-urgent {
  background: #ff7a2f;
  color: #2a1203;
}
.lp-promo-clock {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #fff1e6;
  color: #9a3412;
  font-size: 12.5px;
  font-variant-numeric: tabular-nums;
}
.lp-price {
  display: flex;
  align-items: baseline;
  gap: 4px;
  color: var(--ink);
}
.lp-price .cur {
  font-size: 18px;
  font-weight: 700;
}
.lp-price .val {
  font-family: var(--font-display);
  font-size: clamp(42px, 7.4svh, 58px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
}
.lp-price .per {
  color: var(--muted);
  font-size: 15px;
  font-weight: 600;
}
.lp-price-eq {
  color: var(--muted);
  font-size: 14.5px;
}
.lp-price-eq b {
  color: var(--ink);
}
.lp-price-save {
  padding: 3px 10px;
  border-radius: 10px;
  background: #e3f8ef;
  color: var(--green-dark);
  font-size: 13px;
  font-weight: 700;
}
.lp-price-day {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ink);
  font-size: 13px;
  font-weight: 600;
}
.lp-price-day svg {
  flex: none;
  color: var(--amber);
  fill: var(--amber);
}
.lp-btn-block {
  width: 100%;
  margin-top: 6px;
}
.lp-price-guarantee {
  margin-top: 4px !important;
  color: var(--ink);
  font-size: 13px;
  font-weight: 600;
}
.lp-price-guarantee svg {
  display: inline-block;
  margin-right: 4px;
  color: var(--green-dark);
  vertical-align: -3px;
}
.lp-price-pay {
  color: var(--muted);
  font-size: 12.5px;
}

/* 12 Garantia: selo e texto sobre o verde. */
.lp-guarantee {
  display: flex;
  align-items: center;
  gap: 32px;
  max-width: 880px;
}
.lp-seal {
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 132px;
  height: 132px;
  border: 3px dashed rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  background: #fff;
  background-clip: content-box;
  padding: 6px;
  color: var(--green-deep);
  box-shadow: 0 20px 40px -20px rgba(4, 47, 34, 0.8);
  text-align: center;
}
.lp-seal svg {
  color: var(--green);
}
.lp-seal b {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  line-height: 1.05;
}
.lp-seal small {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.lp-guarantee .lp-kicker {
  margin-bottom: 4px !important;
  text-align: left;
}
.lp-guarantee h3 {
  color: #fff;
  font-size: clamp(24px, 4svh, 30px);
  font-weight: 700;
}
.lp-guarantee p:not(.lp-kicker) {
  margin-top: 8px !important;
  color: var(--t-muted);
  font-size: 15.5px;
  line-height: 1.6;
}

/* 13 Perguntas: duas colunas no computador; abrir uma não estica a vizinha. */
.lp-faq {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  align-items: start;
  gap: 10px 14px;
  margin-top: 24px;
}
.lp-faq details {
  padding: 0 16px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 8px 18px -16px rgba(11, 23, 18, 0.35);
  transition: border-color 0.2s ease;
}
.lp-faq details[open] {
  border-color: var(--green);
  box-shadow: inset 3px 0 0 var(--green), 0 12px 24px -18px rgba(11, 23, 18, 0.4);
}
.lp-faq summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 0;
  color: var(--ink);
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
  flex: none;
  color: var(--green-dark);
  transition: transform 0.2s ease;
}
.lp-faq details[open] summary svg {
  transform: rotate(180deg);
}
.lp-faq p {
  padding-bottom: 14px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.55;
}
.lp-faq p strong {
  color: var(--ink);
}
.lp-faq a {
  color: var(--green-dark);
  font-weight: 700;
}
.lp-faq-more {
  display: none;
}

/* 14 Chamada final */
.lp-final {
  background:
    radial-gradient(ellipse 70% 90% at 50% 0%, rgba(18, 185, 129, 0.34), transparent 70%),
    var(--night);
}
.lp-final-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.lp-final-logo {
  width: 150px;
  height: auto;
  margin-bottom: 20px;
  opacity: 0.9;
}
.lp-final-sub {
  max-width: 640px;
  margin-top: 14px !important;
  color: var(--t-muted);
  font-size: 17px;
  line-height: 1.55;
}
.lp-final .lp-ctas {
  justify-content: center;
  margin-top: 24px;
}
.lp-final-note {
  margin-top: 18px !important;
  color: var(--t-muted);
  font-size: 13px;
}
.lp-login {
  margin-top: 12px;
  color: #c4d3cc;
  font-size: 13px;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* Telas baixas (notebook com a barra do navegador, celular com a barra aberta): sai o que é
   secundário, para cada seção continuar cabendo numa tela. */
@media (max-height: 760px) {
  .lp-ex-desc,
  .lp-closer {
    display: none;
  }
}
@media (min-width: 861px) and (max-height: 760px) {
  .lp-sec .lp-feats {
    gap: 12px;
    margin-top: 20px;
  }
  .lp-feat-body {
    gap: 4px;
    padding: 12px 14px 14px;
  }
  .lp-feat p {
    font-size: 12.5px;
  }
  .lp-feat-more li {
    font-size: 12.5px;
  }
  .lp-feat-more ul {
    gap: 6px;
  }
  .lp-offer-incl {
    padding: 20px;
  }
  .lp-incl {
    gap: 9px 14px;
  }
  .lp-price-box {
    min-height: 330px;
    padding: 22px 22px 18px;
  }
  .lp-steps-cta {
    margin-top: 18px;
  }
  .lp-step {
    padding: 18px;
  }
}
@media (min-width: 861px) and (max-height: 700px) {
  .lp-canva-bar,
  .lp-offer-trust {
    display: none;
  }
}

/* Tablet */
@media (max-width: 1100px) {
  .lp-float-a {
    left: -16px;
  }
  .lp-float-b {
    right: -8px;
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
  .lp-hero-media {
    justify-self: center;
    width: min(100%, 35vh);
    width: min(100%, 35svh);
  }
  .lp-hero-video {
    border-radius: 16px;
  }
  .lp-float {
    display: none;
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
    color: var(--mint);
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
    color: var(--t-muted);
    font-size: 12.5px;
    text-align: center;
  }
  .lp-swipe::after {
    content: " →";
  }
  .lp-sec .lp-rail {
    position: relative;
    grid-auto-columns: 80%;
    grid-auto-flow: column;
    grid-template-columns: none;
    margin-top: 16px;
    margin-inline: calc(-1 * var(--lp-pad-x));
    padding: 2px var(--lp-pad-x) 10px;
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
  .lp-feat:hover,
  .lp-ex:hover {
    transform: none;
  }
  /* Antes e depois: um embaixo do outro, sem as mini-telas. */
  .lp-compare {
    grid-template-columns: 1fr;
    gap: 10px;
    margin-top: 18px;
  }
  .lp-cmp-mock,
  .lp-cmp-arrow {
    display: none;
  }
  .lp-cmp {
    padding: 16px;
  }
  .lp-cmp-label {
    font-size: 16px;
  }
  .lp-cmp-list {
    gap: 6px;
  }
  .lp-cmp-list li {
    font-size: 14px;
  }
  .lp-steps-cta .lp-btn {
    width: 100%;
  }
  .lp-canva {
    grid-template-columns: 1fr;
    gap: 16px;
    margin-top: 18px;
  }
  /* No celular a própria animação explica; a linha de apoio fica só no computador. */
  .lp-canva-sub,
  .lp-canva-bar {
    display: none;
  }
  .lp-audience {
    grid-template-columns: repeat(2, 1fr);
  }
  .lp-marquee-track span {
    padding: 13px 16px;
    font-size: 13px;
  }
  /* Assinatura: o preço primeiro, a lista do que vem nela embaixo. */
  .lp-offer {
    grid-template-columns: 1fr;
    gap: 12px;
    margin-top: 18px;
  }
  .lp-price-box {
    order: -1;
    min-height: 0;
    padding: 18px;
  }
  .lp-offer-incl {
    padding: 16px;
  }
  .lp-offer-title {
    margin-bottom: 10px !important;
    font-size: 16px;
  }
  /* No celular, o que vem na assinatura vira etiquetas curtas. */
  .lp-incl {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .lp-incl li {
    align-items: center;
    gap: 4px;
    padding: 4px 9px 4px 5px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    font-size: 12px;
    font-weight: 600;
  }
  .lp-incl li svg {
    width: 14px;
    height: 14px;
    margin-top: 0;
  }
  .lp-price-pay,
  .lp-incl-full,
  .lp-offer-trust {
    display: none;
  }
  .lp-incl-short {
    display: inline;
  }
  /* A aba Anual já mostra o desconto: o selo e o rótulo da seção saem no celular. */
  .lp-offer-sub,
  .lp-offer-foot,
  .lp-best,
  .lp-sec-plans .lp-kicker {
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
    border: 1px dashed #b7cdc2;
    border-radius: 12px;
    background: transparent;
    color: var(--green-dark);
    font: inherit;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
  }
  .lp-final-logo {
    width: 120px;
    margin-bottom: 14px;
  }
}
/* Celular: o Assistente IA vira título, animação e passos, nessa ordem; a faixa da promoção encolhe. */
@media (max-width: 860px) {
  .lp-ai {
    grid-template-columns: minmax(0, 1fr);
    gap: 0;
  }
  .lp-ai-copy {
    display: contents;
  }
  .lp-ai-copy .lp-kicker,
  .lp-ai-copy .lp-h2 {
    margin-inline: auto !important;
    text-align: center;
  }
  .lp-ai-copy .lp-sub,
  .lp-ai-chips {
    display: none;
  }
  .lp-ai-visual {
    order: 1;
    margin-top: 16px;
    border-radius: 12px;
  }
  .lp-ai-steps {
    order: 2;
    gap: 8px;
    margin-top: 14px;
  }
  .lp-ai-steps li {
    padding: 10px 12px;
  }
  .lp-promo-bar {
    gap: 2px 10px;
    min-height: 0;
    padding: 6px 12px;
    font-size: 13px;
  }
  .lp-promo-tag {
    display: none;
  }
}
@media (max-width: 860px) and (max-height: 700px) {
  .lp-ai-steps p {
    display: none;
  }
}
@media (max-width: 380px) {
  .lp-promo-bar {
    font-size: 12px;
    letter-spacing: -0.01em;
  }
}

/* Celular com pouca altura (barra do navegador aberta, aparelhos menores). */
@media (max-width: 860px) and (max-height: 700px) {
  .lp-swipe {
    display: none !important;
  }
  .lp-fx {
    height: 86px;
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
  .lp-price-pay,
  .lp-anchor,
  .lp-offer-title,
  .lp-price-day {
    display: none;
  }
  .lp-price-box {
    gap: 6px;
    padding: 14px 16px;
  }
  .lp-price .val {
    font-size: 40px;
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
  .lp-hero-media {
    width: min(100%, 32svh);
  }
  .lp-lead {
    font-size: 15px;
  }
  .lp-canva {
    gap: 12px;
  }
  .lp-pain {
    padding: 14px;
  }
  .lp-step {
    padding: 14px;
  }
  .lp-steps-cta {
    margin-top: 14px;
  }
  .lp-cmp-list li {
    font-size: 13.5px;
  }
  .lp-final-logo {
    display: none;
  }
}
/* Celulares estreitos e baixos (360 px). */
@media (max-width: 380px) and (max-height: 700px) {
  .lp-h2 {
    font-size: 21px;
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
  .lp-steps-cta {
    display: none;
  }
  /* Mais específico que a regra de 767 px, que vem depois. */
  .lp-audience .lp-aud {
    gap: 6px;
    padding: 10px;
  }
  .lp-audience .lp-aud p {
    font-size: 12px;
  }
}
/* Aparelhos bem baixos: a garantia da assinatura fica para a seção seguinte, que é sobre ela. */
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
  /* Dores e passos: cartões deitados (ícone ou número à esquerda), um embaixo do outro. */
  .lp-pains,
  .lp-steps {
    grid-template-columns: 1fr;
    gap: 10px;
    margin-top: 18px;
  }
  .lp-pain,
  .lp-step {
    flex-direction: row;
    align-items: flex-start;
    padding: 16px;
  }
  .lp-pain::before {
    inset: 0 auto 0 0;
    width: 4px;
    height: auto;
  }
  .lp-pain-ico {
    width: 40px;
    height: 40px;
    border-radius: 12px;
  }
  .lp-pain-num {
    display: none;
  }
  .lp-step-num {
    min-width: 40px;
    font-size: 28px;
  }
  .lp-pain h3,
  .lp-step h3 {
    font-size: 16px;
  }
  .lp-pain p,
  .lp-step p {
    font-size: 13.5px;
  }
  .lp-audience {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 18px;
  }
  .lp-aud {
    flex-direction: column;
    gap: 8px;
    padding: 12px;
  }
  .lp-aud-ico {
    width: 36px;
    height: 36px;
    border-radius: 10px;
  }
  .lp-aud h3 {
    font-size: 14px;
  }
  .lp-aud p {
    font-size: 12.5px;
  }
  .lp-checks li {
    padding: 10px 12px;
    font-size: 14px;
  }
  .lp-guarantee {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  .lp-seal {
    width: 112px;
    height: 112px;
  }
  .lp-seal b {
    font-size: 21px;
  }
  .lp-seal small {
    font-size: 9.5px;
    letter-spacing: 0.03em;
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
  .lp-btn:hover,
  .lp-feat:hover,
  .lp-ex:hover {
    transform: none;
  }
  .lp-float {
    animation: none;
  }
  /* Sem movimento, a faixa vira uma linha parada, quebrando em mais de uma se precisar. */
  .lp-marquee {
    -webkit-mask-image: none;
    mask-image: none;
  }
  .lp-marquee-track {
    flex-wrap: wrap;
    justify-content: center;
    width: auto;
    animation: none;
  }
  .lp-marquee-track span[aria-hidden="true"] {
    display: none;
  }
}
</style>
