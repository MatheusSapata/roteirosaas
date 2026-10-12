<template>
  <!-- Carrossel "Roteiro em páginas": páginas na cor da marca e brancas, como um roteiro impresso.
       Títulos e listas se ajustam à área (FitText): pouco texto fica grande, muito texto encolhe. -->
  <div class="rt" :class="[`rt-${slide.kind}`, `rt-${format}`, { 'rt-light': light }]" :style="rootStyle">
    <!-- Capa: foto em cima, bloco da marca com data, destino e logo -->
    <template v-if="slide.kind === 'cover'">
      <div class="rt-photo rt-cover-photo" :style="bgOf(0)"></div>
      <FitText class="rt-ribbon" :max="38" :min="20" line>{{ data.badge && !data.campaign ? data.badge : "Seu roteiro chegou," }} <em>confira agora!</em></FitText>
      <div class="rt-cover-body">
        <FitText v-if="data.dates" class="rt-date" :max="46" :min="24" line><CalendarDaysIcon />{{ data.dates }}</FitText>
        <FitText class="rt-huge" :max="190" :min="64" :lines="2" :line-height="0.92">{{ headline }}</FitText>
        <FitText v-if="tagline" class="rt-tagline" :max="46" :min="24" :lines="2" :line-height="1.25">{{ tagline }}</FitText>
        <img v-if="logo" :src="logo" class="rt-logo rt-logo-chip" alt="" />
      </div>
    </template>

    <!-- Apresentação: texto na cor da marca, foto embaixo e uma polaroide inclinada -->
    <template v-else-if="slide.kind === 'intro'">
      <div class="rt-intro-top">
        <FitText class="rt-head" :max="120" :min="60" :lines="2" :line-height="0.95">você vai se encantar...</FitText>
        <FitText class="rt-text" :max="58" :min="22" fill>{{ data.subtitle }}</FitText>
      </div>
      <div class="rt-photo rt-intro-photo" :style="bgOf(0)"></div>
      <div class="rt-polaroid rt-polaroid-intro"><div class="rt-photo" :style="bgOf(1)"></div></div>
    </template>

    <!-- Cronograma: página branca com linha do tempo e faixa de foto embaixo -->
    <template v-else-if="slide.kind === 'itinerary'">
      <div class="rt-page rt-page-timeline">
        <span class="rt-spaced">{{ slide.part > 1 ? "Ainda não acabou..." : "Cronograma completo" }}</span>
        <FitText class="rt-head rt-head-brand" :max="110" :min="56" :lines="2" :line-height="0.95">{{ slide.part > 1 ? "tem mais!" : "nosso roteiro será assim..." }}</FitText>
        <FitText class="rt-timeline-fit" :max="60" :min="20" fill>
          <ol class="rt-timeline">
            <li v-for="(day, index) in days" :key="index">
              <b>{{ day.title || day.day }}</b><span> /// {{ day.day || `Dia ${slide.from + index + 1}` }}</span>
              <p v-if="day.description">{{ day.description }}</p>
            </li>
          </ol>
        </FitText>
      </div>
      <div class="rt-photo rt-strip" :style="bgOf(0)"></div>
    </template>

    <!-- Detalhes: fotos em fileira, o que inclui e voos -->
    <template v-else-if="slide.kind === 'details'">
      <div class="rt-page">
        <FitText class="rt-head" :max="110" :min="56" :lines="2" :line-height="0.95">detalhes da viagem</FitText>
        <div class="rt-row">
          <div v-for="n in 3" :key="n" class="rt-photo" :style="bgOf(n - 1)"></div>
        </div>
        <FitText class="rt-boxes" :max="46" :min="16" fill>
          <div v-if="included.length" class="rt-box">
            <h3>o que inclui</h3>
            <ul>
              <li v-for="item in included" :key="item"><component :is="iconFor(item)" />{{ item }}</li>
            </ul>
          </div>
          <div v-if="data.flights.length" class="rt-box">
            <h3>voos</h3>
            <ul>
              <li v-for="(flight, index) in data.flights" :key="index">
                <PlaneIcon />
                <span><b>{{ [flight.label, flight.date].filter(Boolean).join(" · ") }}</b> {{ flight.route }}<small v-if="flight.details"> · {{ flight.details }}</small></span>
              </li>
            </ul>
          </div>
        </FitText>
      </div>
    </template>

    <!-- Vamos nessa?: resumo, o que inclui, pacotes e observações -->
    <template v-else>
      <div class="rt-page rt-final">
        <FitText class="rt-final-fit" :max="54" :min="16" fill>
          <span class="rt-f-head">vamos nessa?</span>
          <span class="rt-f-text">Confira o resumo e garanta o seu lugar nessa experiência.</span>
          <span v-if="data.dates" class="rt-f-date"><CalendarDaysIcon />{{ data.dates }}</span>
          <span class="rt-f-huge">{{ headline }}</span>
          <template v-if="included.length && format === 'story'">
            <i class="rt-bar"></i>
            <span class="rt-f-sub">o que inclui?</span>
            <ul class="rt-bullets">
              <li v-for="item in included.slice(0, 6)" :key="item">{{ item }}</li>
            </ul>
          </template>
          <template v-if="packages.length">
            <i class="rt-bar"></i>
            <span class="rt-f-sub">{{ packages.length > 1 ? "pacotes" : "investimento" }}</span>
            <span class="rt-packages">
              <span v-for="(item, index) in packages" :key="index" class="rt-package">
                <span class="rt-package-title">{{ item.title || "Pacote" }}</span>
                <span v-if="index === 0 && data.oldPrice" class="rt-package-old"><s>de {{ data.oldPrice }}</s> por</span>
                <b>{{ item.value }}</b>
                <small v-if="item.installment">{{ item.installment }}</small>
              </span>
            </span>
          </template>
          <span v-if="data.disclaimer" class="rt-fine">• {{ data.disclaimer }}</span>
        </FitText>
        <div v-if="logo || cta || data.contact" class="rt-final-foot">
          <img v-if="logo" :src="logo" class="rt-logo rt-logo-chip" alt="" />
          <span v-if="cta" class="rt-cta">{{ cta }}</span>
          <FitText v-if="data.contact" class="rt-contact" :max="32" :min="18" line>WhatsApp {{ data.contact }}</FitText>
        </div>
      </div>
      <template v-if="format === 'story'">
        <div class="rt-polaroid rt-polaroid-a"><div class="rt-photo" :style="bgOf(0)"></div></div>
        <div class="rt-polaroid rt-polaroid-b"><div class="rt-photo" :style="bgOf(1)"></div></div>
      </template>
    </template>

    <CreativeTapes v-if="data.tapes && slide.kind === 'cover'" :text="tapeLabel" />
    <div class="rt-pager" aria-hidden="true">
      <span class="rt-dots"><i v-for="dot in total" :key="dot" :class="{ on: dot === index + 1 }"></i></span>
      <span v-if="index + 1 < total" class="rt-next"><ArrowRightIcon /></span>
    </div>
  </div>
</template>

<script setup lang="ts">
/** Um slide do carrossel "Roteiro em páginas" em tamanho real (o PNG sai deste elemento). */
import { computed } from "vue";
import { ArrowRightIcon, CalendarDaysIcon, PlaneIcon } from "lucide-vue-next";
import "./creativeFonts";
import { FORMAT_SIZES, effectiveColors, formatMoney, parseMoney, readableOn, tapeText, type CreativeData, type CreativeFormat } from "./creativeData";
import { inclusionIcon } from "./creativeIcons";
import CreativeTapes from "./CreativeTapes.vue";
import FitText from "./FitText.vue";
import type { CarouselSlide } from "./carousel";

const props = defineProps<{
  slide: CarouselSlide;
  format: CreativeFormat;
  data: CreativeData;
  /** Foto principal do slide e as seguintes (para fileiras e polaroides). */
  photos: string[];
  /** Foto principal (já é a primeira de photos). */
  photo?: string;
  index: number;
  total: number;
  showLogo?: boolean;
}>();

const size = computed(() => FORMAT_SIZES[props.format]);
const logo = computed(() => (props.showLogo === false ? "" : props.data.logoUrl));
const cta = computed(() => (props.data.ctaEnabled ? props.data.cta.trim() : ""));
const light = computed(() => props.slide.kind === "itinerary");
const headline = computed(() => (props.data.destination || props.data.title).trim());
// O que sobra do título depois do destino ("fervedouros, dunas e cachoeiras").
const tagline = computed(() => {
  const rest = props.data.title.replace(props.data.destination, "").replace(/^[\s:|–—-]+/, "").trim();
  return rest || props.data.duration;
});
const tapeLabel = computed(() => tapeText(props.data));
const included = computed(() => props.data.benefits.filter(Boolean));
const days = computed(() => (props.slide.kind === "itinerary" ? props.data.itinerary.slice(props.slide.from, props.slide.to) : []));
const iconFor = inclusionIcon;

/** Pacotes: valor de cada opção de preço e a parcela ("ou 12x de R$ 83,25"). */
const packages = computed(() => {
  const count = parseInt(props.data.installmentCount, 10) || 0;
  const list = props.data.prices.length
    ? props.data.prices
    : props.data.priceValue
      ? [{ title: props.data.priceSuffix || "Por pessoa", prefix: "", value: props.data.priceValue, note: "" }]
      : [];
  return list.slice(0, props.format === "story" ? 2 : 2).map(item => {
    const total = parseMoney(item.value);
    return { title: item.title, value: item.value, installment: count > 1 && total ? `ou ${count}x de ${formatMoney(total / count)}` : "" };
  });
});

const rootStyle = computed(() => {
  const colors = effectiveColors(props.data);
  return {
    width: `${size.value.width}px`,
    height: `${size.value.height}px`,
    "--c1": colors.primary,
    "--c2": colors.secondary,
    "--on1": readableOn(colors.primary),
    "--on2": readableOn(colors.secondary)
  };
});
const bgOf = (offset: number) => {
  const list = props.photos.filter(Boolean);
  const url = list.length ? list[offset % list.length] : "";
  return url ? { backgroundImage: `url("${url}")` } : {};
};
</script>

<style scoped>
.rt {
  position: relative;
  overflow: hidden;
  background: var(--c1);
  color: var(--on1);
  font-family: "Montserrat", sans-serif;
  -webkit-font-smoothing: antialiased;
  /* Áreas livres: no Stories a interface do Instagram cobre o topo e a base. */
  --pad: 90px;
  --top: 70px;
  --foot: 48px;
}
.rt-story {
  --pad: 100px;
  --top: 220px;
  --foot: 220px;
}
.rt-square {
  --pad: 72px;
  --top: 52px;
  --foot: 40px;
}
.rt * {
  box-sizing: border-box;
}
.rt :deep(svg) {
  flex: none;
}
.rt-light {
  background: #fff;
  color: #111827;
}
.rt-photo {
  background-color: color-mix(in srgb, var(--c1) 70%, #000);
  background-position: center;
  background-size: cover;
}
.rt-head {
  font-weight: 900;
  letter-spacing: -0.04em;
}
.rt-head-brand {
  color: var(--c1);
}
.rt-huge {
  font-weight: 900;
  letter-spacing: -0.04em;
  text-wrap-style: balance;
}
.rt-date {
  display: flex;
  align-items: center;
  gap: 0.4em;
  margin-bottom: 0.3em;
  font-weight: 600;
}
.rt-date :deep(svg) {
  width: 1.2em;
  height: 1.2em;
}
.rt-logo {
  display: block;
  max-width: 300px;
  max-height: 120px;
  object-fit: contain;
}
.rt-logo-chip {
  padding: 14px 20px;
  border-radius: 20px;
  background: #fff;
}

/* ---------- Capa ---------- */
.rt-cover-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: 50%;
}
.rt-story .rt-cover-photo {
  height: 58%;
}
.rt-ribbon {
  position: absolute;
  top: var(--top);
  right: var(--pad);
  left: var(--pad);
  z-index: 2;
  padding: 0.45em 0.8em;
  border-radius: 999px;
  background: var(--c1);
  color: var(--on1);
  font-weight: 800;
  text-align: center;
}
.rt-ribbon em {
  font-style: normal;
  font-weight: 500;
}
.rt-cover-body {
  position: absolute;
  top: 50%;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  padding: 56px var(--pad) calc(var(--foot) + 110px);
}
.rt-story .rt-cover-body {
  top: 58%;
}
.rt-tagline {
  margin-top: 0.35em;
  font-weight: 500;
}
.rt-cover-body .rt-logo {
  align-self: center;
  margin-top: auto;
}

/* ---------- Apresentação ---------- */
.rt-intro-top {
  position: absolute;
  inset: 0 0 auto 0;
  display: flex;
  height: 56%;
  flex-direction: column;
  gap: 30px;
  padding: calc(var(--top) + 30px) var(--pad) 50px;
}
.rt-story .rt-intro-top {
  height: 58%;
}
.rt-text {
  max-width: 600px;
  font-weight: 500;
  line-height: 1.4;
}
.rt-intro-photo {
  position: absolute;
  inset: 56% 0 0 0;
}
.rt-story .rt-intro-photo {
  inset: 58% 0 0 0;
}
.rt-polaroid {
  position: absolute;
  z-index: 2;
  padding: 26px 26px 70px;
  background: #fafafa;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
}
.rt-polaroid .rt-photo {
  width: 100%;
  height: 100%;
}
.rt-polaroid-intro {
  top: 40%;
  right: -60px;
  width: 400px;
  height: 480px;
  transform: rotate(5deg);
}
.rt-square .rt-polaroid-intro {
  top: 30%;
  width: 300px;
  height: 360px;
}
.rt-polaroid-a {
  top: calc(var(--top) + 10px);
  right: -80px;
  width: 400px;
  height: 440px;
  transform: rotate(4deg);
}
.rt-polaroid-b {
  top: calc(var(--top) + 430px);
  right: -60px;
  width: 400px;
  height: 440px;
  transform: rotate(-9deg);
}

/* ---------- Páginas de conteúdo ---------- */
.rt-page {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  padding: calc(var(--top) + 20px) var(--pad) calc(var(--foot) + 110px);
}
.rt-spaced {
  margin-bottom: 14px;
  font-size: 32px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}
/* Cronograma: a página termina onde começa a faixa de foto. */
.rt-page-timeline {
  bottom: 22%;
  padding-bottom: 40px;
}
.rt-story .rt-page-timeline {
  bottom: 24%;
}
.rt-timeline-fit {
  margin-top: 0.9em;
}
.rt-timeline {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1em;
  margin: 0;
  padding: 0 0 0 1.7em;
  list-style: none;
}
/* A linha do tempo continua por baixo da foto. */
.rt-timeline::before {
  content: "";
  position: absolute;
  top: 0.25em;
  bottom: -40em;
  left: 0.35em;
  width: 0.14em;
  background: #4b5563;
}
.rt-timeline li {
  position: relative;
  line-height: 1.2;
}
.rt-timeline li::before {
  content: "";
  position: absolute;
  top: 0.2em;
  left: -1.7em;
  width: 0.84em;
  height: 0.84em;
  border-radius: 50%;
  background: var(--c1);
}
.rt-timeline b {
  color: var(--c1);
  font-weight: 800;
  letter-spacing: -0.02em;
}
.rt-timeline span {
  color: var(--c1);
  font-weight: 500;
}
.rt-timeline p {
  margin: 0.3em 0 0;
  color: #1f2937;
  font-size: 0.75em;
  font-weight: 500;
  line-height: 1.4;
}
.rt-strip {
  position: absolute;
  inset: auto 0 0 0;
  z-index: 1;
  height: 22%;
}
.rt-story .rt-strip {
  height: 24%;
}
.rt-row {
  display: grid;
  flex: none;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  height: 240px;
  margin: 36px calc(-1 * var(--pad)) 0;
}
.rt-story .rt-row {
  height: 330px;
}
.rt-square .rt-row {
  height: 190px;
}
.rt-row .rt-photo {
  border-radius: 24px;
}
.rt-boxes {
  display: flex;
  flex-direction: column;
  gap: 0.9em;
  margin-top: 36px;
}
.rt-feed .rt-boxes,
.rt-square .rt-boxes {
  flex-direction: row;
}
.rt-box {
  flex: 1;
  min-width: 0;
  padding: 1em 1.15em;
  background: color-mix(in srgb, var(--c1) 82%, #fff);
}
.rt-box h3 {
  margin: 0 0 0.5em;
  font-size: 1.6em;
  font-weight: 900;
  letter-spacing: -0.03em;
}
.rt-box ul {
  display: flex;
  flex-direction: column;
  gap: 0.45em;
  margin: 0;
  padding: 0;
  list-style: none;
  font-weight: 600;
}
.rt-box li {
  display: flex;
  align-items: flex-start;
  gap: 0.5em;
  line-height: 1.25;
}
.rt-box li :deep(svg) {
  width: 1.2em;
  height: 1.2em;
  color: var(--c2);
}
.rt-box small {
  opacity: 0.85;
}

/* ---------- Vamos nessa? ---------- */
.rt-final-fit {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.rt-f-head,
.rt-f-huge {
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -0.04em;
}
.rt-f-head {
  font-size: 2.6em;
}
.rt-f-text {
  margin-top: 0.5em;
  font-size: 0.8em;
  font-weight: 500;
  line-height: 1.35;
}
.rt-f-date {
  display: flex;
  align-items: center;
  gap: 0.4em;
  margin-top: 0.9em;
  font-size: 0.85em;
  font-weight: 600;
}
.rt-f-date :deep(svg) {
  width: 1.2em;
  height: 1.2em;
}
.rt-f-huge {
  margin-top: 0.12em;
  font-size: 2.2em;
  text-wrap-style: balance;
}
/* No Stories as polaroides ficam à direita: o texto de cima ocupa a parte esquerda. */
.rt-story .rt-f-head,
.rt-story .rt-f-text,
.rt-story .rt-f-huge {
  max-width: 62%;
}
.rt-bar {
  display: block;
  width: 2.2em;
  height: 0.34em;
  margin-top: 1em;
  border-radius: 999px;
  background: #fff;
}
.rt-f-sub {
  margin-top: 0.35em;
  font-size: 1.5em;
  font-weight: 900;
  letter-spacing: -0.03em;
}
.rt-bullets {
  margin: 0.35em 0 0;
  padding-left: 0.9em;
  font-size: 0.75em;
  font-weight: 500;
  line-height: 1.45;
}
.rt-packages {
  display: grid;
  width: 100%;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65em;
  margin-top: 0.65em;
}
.rt-package {
  display: flex;
  flex-direction: column;
  padding: 0.8em 0.9em;
  border-radius: 1em;
  background: color-mix(in srgb, var(--c1) 82%, #fff);
}
.rt-package-title {
  font-size: 0.75em;
  font-weight: 700;
}
.rt-package-old {
  margin-top: 0.25em;
  font-size: 0.75em;
}
.rt-package b {
  font-size: 1.6em;
  font-weight: 900;
  letter-spacing: -0.03em;
}
.rt-package small {
  font-size: 0.65em;
}
.rt-fine {
  margin-top: 0.8em;
  font-size: 0.62em;
  opacity: 0.9;
}
.rt-final-foot {
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  margin-top: 28px;
}
.rt-cta {
  padding: 24px 52px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 36px;
  font-weight: 800;
}
.rt-contact {
  font-weight: 700;
}

/* ---------- Base: pontinhos e seta ---------- */
.rt-pager {
  position: absolute;
  right: 64px;
  bottom: var(--foot);
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 26px;
}
.rt-dots {
  display: flex;
  gap: 12px;
}
.rt-dots i {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.35;
}
.rt-dots i.on {
  width: 48px;
  background: var(--c2);
  opacity: 1;
}
.rt-light .rt-dots i.on {
  background: var(--c1);
}
.rt-next {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--c2);
  color: var(--on2);
}
.rt-light .rt-next {
  background: var(--c1);
  color: var(--on1);
}
.rt-next :deep(svg) {
  width: 36px;
  height: 36px;
}
/* Na apresentação e no cronograma a base fica sobre a foto: pontinhos brancos. */
.rt-intro .rt-pager,
.rt-itinerary .rt-pager {
  color: #fff;
}
</style>
