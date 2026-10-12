<template>
  <!-- Carrossel "Roteiro em páginas": páginas na cor da marca e brancas, como um roteiro impresso. -->
  <div class="rt" :class="[`rt-${slide.kind}`, `rt-${format}`, { 'rt-light': light }]" :style="rootStyle">
    <!-- Capa: foto em cima, bloco da marca com data, destino e logo -->
    <template v-if="slide.kind === 'cover'">
      <div class="rt-photo rt-cover-photo" :style="bgOf(0)"></div>
      <span class="rt-ribbon">{{ data.badge && !data.campaign ? data.badge : "Seu roteiro chegou," }} <em>confira agora!</em></span>
      <div class="rt-cover-body">
        <p v-if="data.dates" class="rt-date"><CalendarDaysIcon />{{ data.dates }}</p>
        <h1 class="rt-huge" :style="hugeStyle">{{ headline }}</h1>
        <p v-if="tagline" class="rt-tagline">{{ tagline }}</p>
        <img v-if="logo" :src="logo" class="rt-logo" alt="" />
      </div>
    </template>

    <!-- Apresentação: texto na cor da marca, foto embaixo e uma polaroide inclinada -->
    <template v-else-if="slide.kind === 'intro'">
      <div class="rt-intro-top">
        <h2 class="rt-head">você vai se encantar...</h2>
        <p class="rt-text">{{ data.subtitle }}</p>
      </div>
      <div class="rt-photo rt-intro-photo" :style="bgOf(0)"></div>
      <div class="rt-polaroid rt-polaroid-intro"><div class="rt-photo" :style="bgOf(1)"></div></div>
    </template>

    <!-- Cronograma: página branca com linha do tempo e faixa de foto embaixo -->
    <template v-else-if="slide.kind === 'itinerary'">
      <div class="rt-page">
        <span class="rt-spaced">{{ slide.part > 1 ? "Ainda não acabou..." : "Cronograma completo" }}</span>
        <h2 class="rt-head rt-head-brand">{{ slide.part > 1 ? "tem mais!" : "nosso roteiro será assim..." }}</h2>
        <ol class="rt-timeline">
          <li v-for="(day, index) in days" :key="index">
            <b>{{ day.title || day.day }}</b><span> /// {{ day.day || `Dia ${slide.from + index + 1}` }}</span>
            <p v-if="day.description">{{ day.description }}</p>
          </li>
        </ol>
      </div>
      <div class="rt-photo rt-strip" :style="bgOf(0)"></div>
    </template>

    <!-- Detalhes: fotos em fileira, o que inclui e voos -->
    <template v-else-if="slide.kind === 'details'">
      <div class="rt-page">
        <h2 class="rt-head">detalhes da viagem</h2>
        <div class="rt-row">
          <div v-for="n in 3" :key="n" class="rt-photo" :style="bgOf(n - 1)"></div>
        </div>
        <div class="rt-boxes">
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
        </div>
      </div>
    </template>

    <!-- Vamos nessa?: resumo, o que inclui, pacotes e observações -->
    <template v-else>
      <div class="rt-page rt-final">
        <h2 class="rt-head">vamos nessa?</h2>
        <p class="rt-text rt-text-sm">Confira o resumo e garanta o seu lugar nessa experiência.</p>
        <p v-if="data.dates" class="rt-date rt-date-sm"><CalendarDaysIcon />{{ data.dates }}</p>
        <h1 class="rt-huge rt-huge-sm" :style="hugeSmallStyle">{{ headline }}</h1>
        <template v-if="included.length && format === 'story'">
          <i class="rt-bar"></i>
          <h3 class="rt-sub">o que inclui?</h3>
          <ul class="rt-bullets">
            <li v-for="item in included.slice(0, format === 'story' ? 6 : 4)" :key="item">{{ item }}</li>
          </ul>
        </template>
        <template v-if="packages.length">
          <i class="rt-bar"></i>
          <h3 class="rt-sub">{{ packages.length > 1 ? "pacotes" : "investimento" }}</h3>
          <div class="rt-packages">
            <div v-for="(item, index) in packages" :key="index" class="rt-package">
              <span class="rt-package-title">{{ item.title || "Pacote" }}</span>
              <span v-if="index === 0 && data.oldPrice" class="rt-package-old"><s>de {{ data.oldPrice }}</s> por</span>
              <b>{{ item.value }}</b>
              <small v-if="item.installment">{{ item.installment }}</small>
            </div>
          </div>
        </template>
        <p v-if="data.disclaimer" class="rt-fine">• {{ data.disclaimer }}</p>
        <div class="rt-final-foot">
          <img v-if="logo" :src="logo" class="rt-logo" alt="" />
          <span v-if="cta" class="rt-cta">{{ cta }}</span>
          <p v-if="data.contact" class="rt-contact">WhatsApp {{ data.contact }}</p>
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
import { FORMAT_SIZES, effectiveColors, formatMoney, parseMoney, readableOn, tapeText, type CreativeData, type CreativeFormat } from "./creativeData";
import { inclusionIcon } from "./creativeIcons";
import CreativeTapes from "./CreativeTapes.vue";
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
const hugeStyle = computed(() => {
  const length = headline.value.length;
  const base = props.format === "square" ? 0.8 : 1;
  const px = length > 22 ? 110 : length > 14 ? 140 : 170;
  return { fontSize: `${Math.round(px * base)}px` };
});
const hugeSmallStyle = computed(() => ({ fontSize: `${Math.round(parseInt(hugeStyle.value.fontSize, 10) * 0.7)}px` }));
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
  font-family: Inter, system-ui, sans-serif;
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
  margin: 0;
  font-family: Sora, Inter, sans-serif;
  font-size: 110px;
  font-weight: 800;
  line-height: 0.95;
  letter-spacing: -0.04em;
}
.rt-square .rt-head {
  font-size: 84px;
}
.rt-head-brand {
  color: var(--c1);
}
.rt-huge {
  margin: 0;
  font-family: Sora, Inter, sans-serif;
  font-weight: 800;
  line-height: 0.92;
  letter-spacing: -0.04em;
}
.rt-text {
  margin: 34px 0 0;
  max-width: 640px;
  font-size: 40px;
  line-height: 1.4;
}
.rt-text-sm {
  max-width: 620px;
  margin-top: 20px;
  font-size: 32px;
}
.rt-date {
  display: flex;
  align-items: center;
  gap: 18px;
  margin: 0 0 18px;
  font-size: 46px;
}
.rt-date :deep(svg) {
  width: 56px;
  height: 56px;
}
.rt-date-sm {
  margin-top: 30px;
  font-size: 34px;
}
.rt-date-sm :deep(svg) {
  width: 42px;
  height: 42px;
}
.rt-logo {
  display: block;
  max-width: 280px;
  max-height: 110px;
  object-fit: contain;
}

/* Capa */
.rt-cover-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: 62%;
}
.rt-square .rt-cover-photo,
.rt-feed .rt-cover-photo {
  height: 50%;
}
.rt-ribbon {
  position: absolute;
  top: 120px;
  right: 90px;
  left: 90px;
  z-index: 2;
  padding: 18px 30px;
  border-radius: 999px;
  background: var(--c1);
  color: var(--on1);
  font-size: 38px;
  font-weight: 800;
  text-align: center;
}
.rt-square .rt-ribbon,
.rt-feed .rt-ribbon {
  top: 60px;
}
.rt-ribbon em {
  font-style: normal;
  font-weight: 500;
}
.rt-cover-body {
  position: absolute;
  inset: 62% 0 0 0;
  display: flex;
  flex-direction: column;
  padding: 70px 120px 90px;
}
.rt-square .rt-cover-body,
.rt-feed .rt-cover-body {
  inset: 50% 0 0 0;
  padding: 50px 90px 140px;
}
.rt-tagline {
  margin: 12px 0 0;
  font-size: 46px;
}
.rt-square .rt-tagline,
.rt-feed .rt-tagline {
  font-size: 36px;
}
.rt-cover-body .rt-logo {
  align-self: center;
  margin-top: auto;
}

/* Apresentação */
.rt-intro-top {
  position: absolute;
  inset: 0 0 auto 0;
  height: 58%;
  padding: 150px 140px 0;
}
.rt-feed .rt-intro-top,
.rt-square .rt-intro-top {
  height: 56%;
  padding: 90px 100px 0;
}
.rt-square .rt-text {
  font-size: 32px;
}
.rt-intro-photo {
  position: absolute;
  inset: 58% 0 0 0;
}
.rt-feed .rt-intro-photo,
.rt-square .rt-intro-photo {
  inset: 56% 0 0 0;
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
  top: 110px;
  right: -80px;
  width: 420px;
  height: 460px;
  transform: rotate(4deg);
}
.rt-polaroid-b {
  top: 540px;
  right: -60px;
  width: 420px;
  height: 460px;
  transform: rotate(-9deg);
}

/* Páginas de conteúdo */
.rt-page {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  padding: 120px 100px 130px;
}
.rt-feed .rt-page,
.rt-square .rt-page {
  padding: 80px 80px 120px;
}
.rt-spaced {
  margin-bottom: 14px;
  font-size: 34px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}
.rt-timeline {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 50px;
  margin: 60px 0 0;
  padding: 0 0 0 70px;
  list-style: none;
}
.rt-feed .rt-timeline,
.rt-square .rt-timeline {
  gap: 34px;
  margin-top: 44px;
}
.rt-timeline::before {
  content: "";
  position: absolute;
  top: 10px;
  bottom: -400px;
  left: 14px;
  width: 6px;
  background: #4b5563;
}
.rt-timeline li {
  position: relative;
  font-size: 40px;
  line-height: 1.2;
}
.rt-timeline li::before {
  content: "";
  position: absolute;
  top: 8px;
  left: -70px;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--c1);
}
.rt-timeline b {
  color: var(--c1);
  letter-spacing: -0.02em;
}
.rt-timeline span {
  color: var(--c1);
}
.rt-timeline p {
  margin: 14px 0 0;
  color: #1f2937;
  font-size: 30px;
  line-height: 1.4;
}
.rt-strip {
  position: absolute;
  inset: auto 0 0 0;
  z-index: 1;
  height: 26%;
}
.rt-square .rt-strip,
.rt-feed .rt-strip {
  height: 22%;
}
.rt-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  height: 330px;
  margin: 56px -100px 0;
}
.rt-feed .rt-row,
.rt-square .rt-row {
  height: 240px;
  margin: 40px -80px 0;
}
.rt-row .rt-photo {
  border-radius: 24px;
}
.rt-boxes {
  display: flex;
  flex-direction: column;
  gap: 30px;
  margin-top: 56px;
}
.rt-feed .rt-boxes,
.rt-square .rt-boxes {
  flex-direction: row;
  gap: 24px;
  margin-top: 40px;
}
.rt-box {
  flex: 1;
  min-width: 0;
  padding: 36px 40px;
  background: color-mix(in srgb, var(--c1) 82%, #fff);
}
.rt-box h3 {
  margin: 0 0 18px;
  font-family: Sora, Inter, sans-serif;
  font-size: 54px;
  font-weight: 800;
  letter-spacing: -0.03em;
}
.rt-box ul {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 32px;
}
.rt-feed .rt-box ul,
.rt-square .rt-box ul {
  font-size: 26px;
}
.rt-box li {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.rt-box li :deep(svg) {
  width: 38px;
  height: 38px;
  color: var(--c2);
}
.rt-box small {
  opacity: 0.85;
}

/* Vamos nessa? */
.rt-final .rt-head {
  max-width: 640px;
}
.rt-story .rt-final .rt-head,
.rt-story .rt-final .rt-huge,
.rt-story .rt-final .rt-text {
  max-width: 560px;
}
.rt-huge-sm {
  margin-top: 6px;
}
.rt-bar {
  display: block;
  width: 90px;
  height: 14px;
  margin-top: 40px;
  border-radius: 999px;
  background: #fff;
}
.rt-feed .rt-bar,
.rt-square .rt-bar {
  margin-top: 26px;
}
.rt-sub {
  margin: 14px 0 0;
  font-family: Sora, Inter, sans-serif;
  font-size: 64px;
  font-weight: 800;
  letter-spacing: -0.03em;
}
.rt-feed .rt-sub,
.rt-square .rt-sub {
  font-size: 48px;
}
.rt-bullets {
  margin: 14px 0 0;
  padding-left: 36px;
  font-size: 30px;
  line-height: 1.45;
}
.rt-packages {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 26px;
  margin-top: 26px;
}
.rt-package {
  display: flex;
  flex-direction: column;
  padding: 32px 36px;
  border-radius: 40px;
  background: color-mix(in srgb, var(--c1) 82%, #fff);
}
.rt-package-title {
  font-size: 30px;
  font-weight: 700;
}
.rt-package-old {
  margin-top: 10px;
  font-size: 30px;
}
.rt-package b {
  font-family: Sora, Inter, sans-serif;
  font-size: 68px;
  font-weight: 800;
  letter-spacing: -0.03em;
}
.rt-feed .rt-package b,
.rt-square .rt-package b {
  font-size: 54px;
}
.rt-package small {
  font-size: 26px;
}
.rt-fine {
  margin: 30px 0 0;
  font-size: 26px;
  opacity: 0.9;
}
.rt-final-foot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  margin-top: auto;
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
  margin: 0;
  font-size: 32px;
  font-weight: 700;
}

/* Base: pontinhos e seta */
.rt-pager {
  position: absolute;
  right: 64px;
  bottom: 48px;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 26px;
}
.rt-story .rt-pager {
  bottom: 80px;
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
/* Na capa e na apresentação a base fica sobre a foto: pontinhos brancos. */
.rt-intro .rt-pager,
.rt-itinerary .rt-pager {
  color: #fff;
}
</style>
