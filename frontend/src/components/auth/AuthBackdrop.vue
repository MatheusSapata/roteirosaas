<template>
  <!--
    Fundo da tela de acesso, nas cores da marca Viaje On: gradiente animado do
    Verde Viaje (#0A6346) e do Verde Trilha (#15915C) até o Noite (#0A110E),
    puxando para o verde, com luzes do Verde On (#90EE8F) e do Verde Trilha
    que se movem devagar. Só decoração (aria-hidden). Com "reduzir movimento"
    ligado no aparelho, fica parado.
  -->
  <div class="apb" aria-hidden="true">
    <span class="apb-glow apb-glow-a"></span>
    <span class="apb-glow apb-glow-b"></span>
    <span class="apb-glow apb-glow-c"></span>
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

@keyframes apb-gradient {
  0% {
    background-position: 0% 30%;
  }
  100% {
    background-position: 100% 70%;
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

@media (prefers-reduced-motion: reduce) {
  .apb,
  .apb-glow {
    animation: none;
  }
}
</style>
