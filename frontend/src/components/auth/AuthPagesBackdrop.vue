<template>
  <!--
    Fundo da tela de acesso, nas cores da marca Viaje On: gradiente animado do
    Verde Viaje (#0A6346) e do Verde Trilha (#15915C) até o Noite (#0A110E),
    puxando para o verde, com luz do Verde On (#90EE8F). Por cima, um único
    desenho grande de página de viagem (como um banner), em traço claro, atrás
    do cartão de login. Só decoração (aria-hidden). Com "reduzir movimento"
    ligado no aparelho, fica parado.
  -->
  <div class="apb" aria-hidden="true">
    <span class="apb-glow apb-glow-a"></span>
    <span class="apb-glow apb-glow-b"></span>
    <span class="apb-glow apb-glow-c"></span>

    <!-- Telas largas: página inteira na horizontal -->
    <svg class="apb-banner is-wide" viewBox="0 0 1200 760" preserveAspectRatio="xMidYMid meet">
      <rect class="apb-sheet" x="1" y="1" width="1198" height="758" rx="26" />
      <!-- Barra do navegador -->
      <path class="apb-line" d="M 1 54 H 1199" />
      <circle class="apb-dot" cx="30" cy="28" r="6" />
      <circle class="apb-dot" cx="52" cy="28" r="6" />
      <circle class="apb-dot" cx="74" cy="28" r="6" />
      <rect class="apb-field" x="380" y="16" width="440" height="24" rx="12" />
      <!-- Menu do topo -->
      <circle class="apb-node" cx="58" cy="94" r="14" />
      <rect class="apb-bar" x="80" y="88" width="96" height="12" rx="6" />
      <rect class="apb-bar is-soft" x="660" y="90" width="70" height="8" rx="4" />
      <rect class="apb-bar is-soft" x="752" y="90" width="70" height="8" rx="4" />
      <rect class="apb-bar is-soft" x="844" y="90" width="70" height="8" rx="4" />
      <rect class="apb-pill is-solid" x="1020" y="80" width="140" height="30" rx="15" />
      <!-- Capa: foto da viagem com montanhas, sol e a rota do passeio -->
      <rect class="apb-hero" x="40" y="132" width="1120" height="360" rx="20" />
      <path class="apb-mountain" d="M 40 470 L 250 300 L 380 400 L 560 230 L 760 420 L 900 330 L 1160 470" />
      <circle class="apb-sun" cx="980" cy="210" r="34" />
      <path class="apb-route" d="M 120 440 C 260 380, 330 460, 470 380 S 700 300, 820 360 S 1000 300, 1080 250" />
      <circle class="apb-pin" cx="120" cy="440" r="7" />
      <circle class="apb-pin" cx="1080" cy="250" r="7" />
      <rect class="apb-bar is-strong" x="88" y="176" width="420" height="26" rx="13" />
      <rect class="apb-bar" x="88" y="214" width="320" height="14" rx="7" />
      <rect class="apb-bar is-soft" x="88" y="240" width="280" height="10" rx="5" />
      <rect class="apb-pill is-solid" x="88" y="270" width="170" height="40" rx="20" />
      <!-- Cards dos roteiros -->
      <g v-for="(x, i) in [40, 420, 800]" :key="i">
        <rect class="apb-block" :x="x" y="520" width="360" height="210" rx="16" />
        <rect class="apb-photo" :x="x + 14" y="534" width="332" height="104" rx="10" />
        <rect class="apb-bar" :x="x + 18" y="654" width="190" height="12" rx="6" />
        <rect class="apb-bar is-soft" :x="x + 18" y="676" width="250" height="8" rx="4" />
        <rect class="apb-pill" :x="x + 236" y="694" width="110" height="24" rx="12" />
      </g>
    </svg>

    <!-- Celular: a mesma página na vertical -->
    <svg class="apb-banner is-tall" viewBox="0 0 360 760" preserveAspectRatio="xMidYMid meet">
      <rect class="apb-sheet" x="1" y="1" width="358" height="758" rx="36" />
      <rect class="apb-bar is-soft" x="150" y="16" width="60" height="8" rx="4" />
      <circle class="apb-node" cx="34" cy="56" r="12" />
      <rect class="apb-bar" x="52" y="51" width="80" height="10" rx="5" />
      <rect class="apb-bar is-soft" x="296" y="46" width="34" height="5" rx="2.5" />
      <rect class="apb-bar is-soft" x="296" y="56" width="34" height="5" rx="2.5" />
      <rect class="apb-bar is-soft" x="296" y="66" width="34" height="5" rx="2.5" />
      <rect class="apb-hero" x="18" y="88" width="324" height="300" rx="20" />
      <path class="apb-mountain" d="M 18 370 L 100 270 L 160 320 L 240 220 L 342 360" />
      <circle class="apb-sun" cx="286" cy="150" r="22" />
      <path class="apb-route" d="M 50 350 C 110 300, 160 350, 220 300 S 300 250, 310 200" />
      <rect class="apb-bar is-strong" x="40" y="120" width="190" height="18" rx="9" />
      <rect class="apb-bar is-soft" x="40" y="148" width="150" height="9" rx="4.5" />
      <rect class="apb-block" x="18" y="408" width="324" height="160" rx="16" />
      <rect class="apb-photo" x="30" y="420" width="300" height="80" rx="10" />
      <rect class="apb-bar" x="32" y="514" width="150" height="10" rx="5" />
      <rect class="apb-bar is-soft" x="32" y="534" width="210" height="7" rx="3.5" />
      <rect class="apb-block" x="18" y="584" width="324" height="160" rx="16" />
      <rect class="apb-photo" x="30" y="596" width="300" height="80" rx="10" />
      <rect class="apb-bar" x="32" y="690" width="130" height="10" rx="5" />
      <rect class="apb-bar is-soft" x="32" y="710" width="190" height="7" rx="3.5" />
    </svg>
  </div>
</template>

<style scoped>
.apb {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  /* Gradiente que se move devagar: verde na maior parte, com o Noite nas pontas. */
  background: linear-gradient(
    125deg,
    #0a110e 0%,
    #0f2219 14%,
    #0a6346 34%,
    #15915c 52%,
    #0a6346 70%,
    #0b3d2a 86%,
    #0a110e 100%
  );
  background-size: 260% 260%;
  animation: apb-gradient 22s ease-in-out infinite alternate;
}
.apb-glow {
  position: absolute;
  border-radius: 9999px;
  filter: blur(90px);
  will-change: transform;
}
.apb-glow-a {
  width: 52vmax;
  height: 52vmax;
  left: -14vmax;
  top: -18vmax;
  background: radial-gradient(closest-side, rgba(144, 238, 143, 0.38), transparent);
  animation: apb-glow-a 24s ease-in-out infinite alternate;
}
.apb-glow-b {
  width: 58vmax;
  height: 58vmax;
  right: -20vmax;
  bottom: -26vmax;
  background: radial-gradient(closest-side, rgba(10, 17, 14, 0.7), transparent);
  animation: apb-glow-b 30s ease-in-out infinite alternate;
}
.apb-glow-c {
  width: 34vmax;
  height: 34vmax;
  right: 8vmax;
  top: 6vmax;
  background: radial-gradient(closest-side, rgba(21, 145, 92, 0.6), transparent);
  animation: apb-glow-c 20s ease-in-out infinite alternate;
}

/* Um único desenho grande, atrás do cartão. */
.apb-banner {
  position: absolute;
  top: 50%;
  left: 50%;
  width: min(1240px, 92vw);
  height: auto;
  max-height: 88vh;
  translate: -50% -50%;
  rotate: -2deg;
  animation: apb-float 16s ease-in-out infinite alternate;
}
.apb-banner.is-tall {
  display: none;
}
.apb-sheet {
  fill: rgba(230, 242, 234, 0.05);
  stroke: rgba(184, 245, 183, 0.5);
  stroke-width: 1.6;
}
.apb-line,
.apb-mountain {
  fill: none;
  stroke: rgba(184, 245, 183, 0.45);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.apb-hero {
  fill: rgba(144, 238, 143, 0.07);
  stroke: rgba(184, 245, 183, 0.4);
  stroke-width: 1.4;
}
.apb-sun {
  fill: rgba(144, 238, 143, 0.16);
  stroke: rgba(184, 245, 183, 0.55);
  stroke-width: 1.4;
}
.apb-route {
  fill: none;
  stroke: #90ee8f;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-dasharray: 3 14;
  opacity: 0.75;
  animation: apb-route 24s linear infinite;
}
.apb-pin {
  fill: #90ee8f;
  opacity: 0.85;
}
.apb-dot {
  fill: rgba(184, 245, 183, 0.45);
}
.apb-node {
  fill: rgba(144, 238, 143, 0.12);
  stroke: rgba(184, 245, 183, 0.55);
  stroke-width: 1.4;
}
.apb-block {
  fill: rgba(230, 242, 234, 0.04);
  stroke: rgba(184, 245, 183, 0.35);
  stroke-width: 1.4;
}
.apb-photo {
  fill: rgba(144, 238, 143, 0.08);
}
.apb-field {
  fill: rgba(230, 242, 234, 0.05);
  stroke: rgba(184, 245, 183, 0.3);
  stroke-width: 1.2;
}
.apb-bar {
  fill: rgba(230, 242, 234, 0.32);
}
.apb-bar.is-soft {
  fill: rgba(230, 242, 234, 0.16);
}
.apb-bar.is-strong {
  fill: rgba(230, 242, 234, 0.45);
}
.apb-pill {
  fill: none;
  stroke: rgba(184, 245, 183, 0.5);
  stroke-width: 1.4;
}
.apb-pill.is-solid {
  fill: rgba(144, 238, 143, 0.4);
  stroke: none;
}

@keyframes apb-gradient {
  0% {
    background-position: 0% 30%;
  }
  100% {
    background-position: 100% 70%;
  }
}
@keyframes apb-float {
  to {
    translate: -50% calc(-50% - 12px);
    rotate: -1deg;
  }
}
@keyframes apb-route {
  to {
    stroke-dashoffset: -680;
  }
}
@keyframes apb-glow-a {
  to {
    transform: translate(14vmax, 10vmax) scale(1.12);
  }
}
@keyframes apb-glow-b {
  to {
    transform: translate(-12vmax, -8vmax) scale(0.92);
  }
}
@keyframes apb-glow-c {
  to {
    transform: translate(-16vmax, 18vmax) scale(1.1);
  }
}

@media (max-width: 640px) {
  .apb-banner.is-wide {
    display: none;
  }
  .apb-banner.is-tall {
    display: block;
    width: min(360px, 90vw);
    max-height: 92vh;
  }
}
@media (prefers-reduced-motion: reduce) {
  .apb,
  .apb-glow,
  .apb-banner,
  .apb-route {
    animation: none;
  }
}
</style>
