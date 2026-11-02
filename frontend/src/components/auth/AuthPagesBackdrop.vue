<template>
  <!--
    Fundo da tela de acesso: verde da marca Roteiro Online com desenhos simples de
    páginas (página de viagem, roteiro, preços, formulário e celular) em traço
    branco, flutuando devagar e ligados por linhas pontilhadas, como as páginas
    ligadas pela seção Links/Roteiros. Só decoração (aria-hidden). Com "reduzir
    movimento" ligado no aparelho, fica parado.
  -->
  <div class="apb" aria-hidden="true">
    <span class="apb-glow apb-glow-a"></span>
    <span class="apb-glow apb-glow-b"></span>

    <svg class="apb-defs" width="0" height="0" focusable="false">
      <defs>
        <!-- Página de viagem: capa com foto, título, texto, botão e cards -->
        <g id="apb-landing">
          <rect class="apb-sheet" width="240" height="320" rx="14" />
          <path class="apb-line" d="M 0 30 H 240" />
          <circle class="apb-dot" cx="16" cy="15" r="3.5" />
          <circle class="apb-dot" cx="28" cy="15" r="3.5" />
          <circle class="apb-dot" cx="40" cy="15" r="3.5" />
          <rect class="apb-block" x="16" y="44" width="208" height="92" rx="8" />
          <path class="apb-line" d="M 44 118 L 86 82 L 112 104 L 138 76 L 196 118" />
          <circle class="apb-line" cx="180" cy="66" r="9" />
          <rect class="apb-bar" x="16" y="150" width="150" height="10" rx="5" />
          <rect class="apb-bar is-soft" x="16" y="168" width="200" height="6" rx="3" />
          <rect class="apb-bar is-soft" x="16" y="180" width="176" height="6" rx="3" />
          <rect class="apb-pill" x="16" y="196" width="86" height="22" rx="11" />
          <rect class="apb-block" x="16" y="232" width="64" height="72" rx="7" />
          <rect class="apb-block" x="88" y="232" width="64" height="72" rx="7" />
          <rect class="apb-block" x="160" y="232" width="64" height="72" rx="7" />
        </g>
        <!-- Roteiro dia a dia -->
        <g id="apb-roteiro">
          <rect class="apb-sheet" width="220" height="260" rx="14" />
          <rect class="apb-bar" x="18" y="20" width="110" height="10" rx="5" />
          <path class="apb-line" d="M 34 56 V 236" />
          <circle class="apb-node" cx="34" cy="60" r="8" />
          <rect class="apb-bar" x="54" y="54" width="90" height="8" rx="4" />
          <rect class="apb-bar is-soft" x="54" y="68" width="140" height="6" rx="3" />
          <circle class="apb-node" cx="34" cy="118" r="8" />
          <rect class="apb-bar" x="54" y="112" width="70" height="8" rx="4" />
          <rect class="apb-bar is-soft" x="54" y="126" width="130" height="6" rx="3" />
          <circle class="apb-node" cx="34" cy="176" r="8" />
          <rect class="apb-bar" x="54" y="170" width="100" height="8" rx="4" />
          <rect class="apb-bar is-soft" x="54" y="184" width="120" height="6" rx="3" />
          <circle class="apb-node" cx="34" cy="232" r="8" />
          <rect class="apb-bar" x="54" y="226" width="80" height="8" rx="4" />
        </g>
        <!-- Preços e pacotes -->
        <g id="apb-precos">
          <rect class="apb-sheet" width="280" height="240" rx="14" />
          <rect class="apb-bar" x="80" y="20" width="120" height="10" rx="5" />
          <rect class="apb-block" x="16" y="48" width="76" height="172" rx="9" />
          <rect class="apb-block is-strong" x="102" y="40" width="76" height="186" rx="9" />
          <rect class="apb-block" x="188" y="48" width="76" height="172" rx="9" />
          <rect class="apb-bar" x="30" y="66" width="48" height="12" rx="6" />
          <rect class="apb-bar" x="116" y="60" width="48" height="14" rx="7" />
          <rect class="apb-bar" x="202" y="66" width="48" height="12" rx="6" />
          <path class="apb-check" d="M 28 100 l 5 5 l 9 -10 M 28 124 l 5 5 l 9 -10 M 28 148 l 5 5 l 9 -10" />
          <path class="apb-check" d="M 114 96 l 5 5 l 9 -10 M 114 120 l 5 5 l 9 -10 M 114 144 l 5 5 l 9 -10 M 114 168 l 5 5 l 9 -10" />
          <path class="apb-check" d="M 200 100 l 5 5 l 9 -10 M 200 124 l 5 5 l 9 -10" />
          <rect class="apb-pill" x="24" y="190" width="60" height="18" rx="9" />
          <rect class="apb-pill is-solid" x="110" y="196" width="60" height="18" rx="9" />
          <rect class="apb-pill" x="196" y="190" width="60" height="18" rx="9" />
        </g>
        <!-- Formulário de interesse -->
        <g id="apb-form">
          <rect class="apb-sheet" width="240" height="220" rx="14" />
          <rect class="apb-bar" x="20" y="22" width="130" height="10" rx="5" />
          <rect class="apb-bar is-soft" x="20" y="40" width="180" height="6" rx="3" />
          <rect class="apb-field" x="20" y="62" width="200" height="28" rx="7" />
          <rect class="apb-field" x="20" y="100" width="200" height="28" rx="7" />
          <rect class="apb-field" x="20" y="138" width="96" height="28" rx="7" />
          <rect class="apb-field" x="124" y="138" width="96" height="28" rx="7" />
          <rect class="apb-pill is-solid" x="20" y="180" width="200" height="24" rx="12" />
        </g>
        <!-- Celular com a página aberta -->
        <g id="apb-phone">
          <rect class="apb-sheet" width="140" height="260" rx="22" />
          <rect class="apb-bar is-soft" x="52" y="12" width="36" height="6" rx="3" />
          <rect class="apb-block" x="12" y="30" width="116" height="80" rx="10" />
          <path class="apb-line" d="M 26 98 L 52 74 L 70 88 L 88 68 L 116 98" />
          <rect class="apb-bar" x="12" y="122" width="90" height="9" rx="4.5" />
          <rect class="apb-bar is-soft" x="12" y="138" width="116" height="6" rx="3" />
          <rect class="apb-bar is-soft" x="12" y="150" width="100" height="6" rx="3" />
          <rect class="apb-pill is-solid" x="12" y="168" width="116" height="22" rx="11" />
          <rect class="apb-block" x="12" y="200" width="54" height="44" rx="7" />
          <rect class="apb-block" x="74" y="200" width="54" height="44" rx="7" />
        </g>
        <!-- Depoimento -->
        <g id="apb-depo">
          <rect class="apb-sheet" width="180" height="110" rx="14" />
          <circle class="apb-node" cx="34" cy="34" r="14" />
          <rect class="apb-bar" x="56" y="26" width="80" height="8" rx="4" />
          <path class="apb-check" d="M 56 46 h 54" />
          <rect class="apb-bar is-soft" x="20" y="62" width="140" height="6" rx="3" />
          <rect class="apb-bar is-soft" x="20" y="74" width="120" height="6" rx="3" />
          <rect class="apb-bar is-soft" x="20" y="86" width="96" height="6" rx="3" />
        </g>
      </defs>
    </svg>

    <!-- Telas largas: páginas pelos lados -->
    <svg class="apb-art is-wide" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">
      <!-- Ligações entre as páginas -->
      <g class="apb-links">
        <path d="M 250 380 C 330 520, 230 600, 300 700" />
        <path d="M 1150 300 C 1060 420, 1220 520, 1130 640" />
        <path d="M 360 160 C 600 60, 840 70, 1060 150" />
        <path d="M 420 800 C 640 880, 860 870, 1040 790" />
      </g>

      <use href="#apb-landing" class="apb-page apb-float-a" transform="translate(90 70) rotate(-6 120 160)" />
      <use href="#apb-roteiro" class="apb-page apb-float-b" transform="translate(150 610) rotate(5 110 130)" />
      <use href="#apb-precos" class="apb-page apb-float-c" transform="translate(1080 40) rotate(7 140 120)" />
      <use href="#apb-form" class="apb-page apb-float-a" transform="translate(1090 620) rotate(-5 120 110)" />
      <use href="#apb-phone" class="apb-page apb-float-b" transform="translate(1270 330) rotate(4 70 130)" />
      <use href="#apb-depo" class="apb-page apb-float-c" transform="translate(40 420) rotate(-3 90 55)" />
    </svg>

    <!-- Celular: páginas nos cantos de cima e de baixo -->
    <svg class="apb-art is-tall" viewBox="0 0 390 844" preserveAspectRatio="xMidYMid slice">
      <g class="apb-links">
        <path d="M 60 190 C 120 120, 260 120, 330 60" />
        <path d="M 40 760 C 140 700, 260 820, 360 720" />
      </g>
      <use href="#apb-landing" class="apb-page apb-float-a" transform="translate(-70 -70) rotate(-8 120 160) scale(0.82)" />
      <use href="#apb-phone" class="apb-page apb-float-b" transform="translate(300 -40) rotate(9 70 130) scale(0.8)" />
      <use href="#apb-roteiro" class="apb-page apb-float-c" transform="translate(-60 700) rotate(6 110 130) scale(0.8)" />
      <use href="#apb-form" class="apb-page apb-float-a" transform="translate(250 690) rotate(-7 120 110) scale(0.8)" />
    </svg>
  </div>
</template>

<style scoped>
.apb {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  /* Verde da marca na maior parte da tela; só as bordas escurecem um pouco. */
  background:
    radial-gradient(120% 90% at 50% 40%, #41ce5f 0%, #2fb552 45%, #1e9444 78%, #157236 100%);
}
.apb-glow {
  position: absolute;
  border-radius: 9999px;
  filter: blur(80px);
  will-change: transform;
}
.apb-glow-a {
  width: 56vmax;
  height: 56vmax;
  left: -16vmax;
  top: -20vmax;
  background: radial-gradient(closest-side, rgba(196, 255, 206, 0.55), transparent);
  animation: apb-glow-a 26s ease-in-out infinite alternate;
}
.apb-glow-b {
  width: 60vmax;
  height: 60vmax;
  right: -22vmax;
  bottom: -28vmax;
  background: radial-gradient(closest-side, rgba(10, 99, 52, 0.55), transparent);
  animation: apb-glow-b 32s ease-in-out infinite alternate;
}
.apb-defs {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}
.apb-art {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.apb-art.is-tall {
  display: none;
}

/* Traço branco simples, como um rascunho. */
.apb-sheet {
  fill: rgba(255, 255, 255, 0.1);
  stroke: rgba(255, 255, 255, 0.55);
  stroke-width: 1.5;
}
.apb-line,
.apb-check {
  fill: none;
  stroke: rgba(255, 255, 255, 0.55);
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.apb-dot {
  fill: rgba(255, 255, 255, 0.5);
}
.apb-block {
  fill: rgba(255, 255, 255, 0.08);
  stroke: rgba(255, 255, 255, 0.45);
  stroke-width: 1.2;
}
.apb-block.is-strong {
  fill: rgba(255, 255, 255, 0.16);
  stroke: rgba(255, 255, 255, 0.7);
}
.apb-bar {
  fill: rgba(255, 255, 255, 0.5);
}
.apb-bar.is-soft {
  fill: rgba(255, 255, 255, 0.26);
}
.apb-pill {
  fill: none;
  stroke: rgba(255, 255, 255, 0.6);
  stroke-width: 1.4;
}
.apb-pill.is-solid {
  fill: rgba(255, 255, 255, 0.55);
  stroke: none;
}
.apb-field {
  fill: rgba(255, 255, 255, 0.06);
  stroke: rgba(255, 255, 255, 0.4);
  stroke-width: 1.2;
}
.apb-node {
  fill: rgba(255, 255, 255, 0.14);
  stroke: rgba(255, 255, 255, 0.6);
  stroke-width: 1.4;
}
.apb-links path {
  fill: none;
  stroke: rgba(255, 255, 255, 0.45);
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-dasharray: 2 12;
  animation: apb-flow 40s linear infinite;
}
.apb-links path:nth-child(2n) {
  animation-direction: reverse;
  animation-duration: 54s;
}

/* As páginas flutuam devagar, cada grupo num ritmo. */
.apb-page {
  transform-box: fill-box;
}
.apb-float-a {
  animation: apb-float-a 14s ease-in-out infinite alternate;
}
.apb-float-b {
  animation: apb-float-b 18s ease-in-out infinite alternate;
}
.apb-float-c {
  animation: apb-float-c 16s ease-in-out infinite alternate;
}
@keyframes apb-float-a {
  to {
    translate: 0 -14px;
  }
}
@keyframes apb-float-b {
  to {
    translate: 10px 12px;
  }
}
@keyframes apb-float-c {
  to {
    translate: -8px -10px;
  }
}
@keyframes apb-flow {
  to {
    stroke-dashoffset: -560;
  }
}
@keyframes apb-glow-a {
  to {
    transform: translate(12vmax, 8vmax) scale(1.1);
  }
}
@keyframes apb-glow-b {
  to {
    transform: translate(-10vmax, -6vmax) scale(0.94);
  }
}

/* No celular os desenhos ficam mais discretos para o formulário respirar. */
@media (max-width: 640px) {
  .apb-art.is-wide {
    display: none;
  }
  .apb-art.is-tall {
    display: block;
    opacity: 0.8;
  }
}
@media (prefers-reduced-motion: reduce) {
  .apb-glow,
  .apb-links path,
  .apb-page {
    animation: none;
  }
}
</style>
