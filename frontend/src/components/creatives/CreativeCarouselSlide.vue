<template>
  <div class="cs" :class="[`cs-${slide.kind}`, `cs-${format}`]" :style="rootStyle">
    <!-- Capa e chamada final: foto inteira com o texto por cima -->
    <template v-if="slide.kind === 'cover' || slide.kind === 'final'">
      <div class="cs-photo cs-fill" :style="bg"></div>
      <div class="cs-shade"></div>
      <img v-if="logo" :src="logo" class="cs-logo cs-logo-top" alt="" />
      <div class="cs-over">
        <template v-if="slide.kind === 'cover'">
          <span v-if="data.dates" class="cs-tag">{{ data.dates }}</span>
          <h1 class="cs-title" :style="titleStyle">{{ data.title }}</h1>
          <p v-if="data.subtitle" class="cs-sub">{{ data.subtitle }}</p>
        </template>
        <template v-else>
          <span v-if="data.agencyName" class="cs-eyebrow">{{ data.agencyName }}</span>
          <h1 class="cs-title" :style="titleStyle">{{ data.title }}</h1>
          <div v-if="data.priceValue" class="cs-price">
            <small>{{ data.pricePrefix }}</small>
            <b>{{ data.priceValue }}</b>
            <small>{{ [data.priceSuffix, data.installments].filter(Boolean).join(" · ") }}</small>
          </div>
          <span v-if="cta" class="cs-cta">{{ cta }}</span>
          <p v-if="data.contact" class="cs-contact">WhatsApp {{ data.contact }}</p>
        </template>
      </div>
    </template>

    <!-- Slides de conteúdo: foto no slide todo e o texto acomodado embaixo; a sombra fica só
         atrás do texto e cresce junto com ele (pouco conteúdo = mais foto). -->
    <template v-else>
      <div class="cs-photo cs-fill" :style="bg"></div>
      <div class="cs-body">
        <span class="cs-eyebrow">{{ eyebrow }}</span>
        <h2 class="cs-heading">{{ heading }}</h2>

        <ol v-if="slide.kind === 'itinerary'" class="cs-days">
          <li v-for="(day, index) in days" :key="index">
            <i>{{ slide.from + index + 1 }}</i>
            <div>
              <b>{{ day.title || day.day }}</b>
              <p v-if="day.description">{{ day.description }}</p>
            </div>
          </li>
        </ol>

        <ul v-else-if="slide.kind === 'included'" class="cs-checks">
          <li v-for="item in included" :key="item"><i>✓</i>{{ item }}</li>
        </ul>

        <div v-else-if="slide.kind === 'flights'" class="cs-flights">
          <div v-for="(flight, index) in data.flights" :key="index" class="cs-flight">
            <span class="cs-flight-label">{{ [flight.label, flight.date].filter(Boolean).join(" · ") }}</span>
            <b>{{ flight.route }}</b>
            <p>{{ [flight.times, flight.details].filter(Boolean).join(" · ") }}</p>
          </div>
        </div>

        <div v-else-if="slide.kind === 'prices'" class="cs-prices">
          <div v-for="(item, index) in prices" :key="index" class="cs-price-row">
            <div>
              <b>{{ item.title || "Valor" }}</b>
              <p v-if="item.note">{{ item.note }}</p>
            </div>
            <div class="cs-price-value">
              <small v-if="item.prefix">{{ item.prefix }}</small>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
          <p v-if="data.installments" class="cs-note">{{ data.installments }}</p>
        </div>
      </div>
    </template>

    <!-- Base do carrossel: logo, um ponto por slide (o atual alongado) e a seta para o próximo. -->
    <div class="cs-foot">
      <img v-if="logo && slide.kind !== 'cover' && slide.kind !== 'final'" :src="logo" class="cs-logo cs-logo-foot" alt="" />
      <span v-else-if="slide.kind !== 'cover' && slide.kind !== 'final' && data.agencyName" class="cs-agency">{{ data.agencyName }}</span>
      <div class="cs-pager">
        <span class="cs-dots" aria-hidden="true">
          <i v-for="dot in total" :key="dot" :class="{ on: dot === index + 1 }"></i>
        </span>
        <span v-if="index + 1 < total" class="cs-next" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/** Um slide do carrossel em tamanho real; o PNG é gerado deste mesmo elemento. */
import { computed } from "vue";
import { FORMAT_SIZES, readableOn, type CreativeData, type CreativeFormat } from "./creativeData";
import { pricesPerSlide, type CarouselSlide } from "./carousel";

const props = defineProps<{
  slide: CarouselSlide;
  format: CreativeFormat;
  data: CreativeData;
  photo: string;
  index: number;
  total: number;
  showLogo?: boolean;
}>();

const size = computed(() => FORMAT_SIZES[props.format]);
const cta = computed(() => (props.data.ctaEnabled ? props.data.cta.trim() : ""));
const logo = computed(() => (props.showLogo === false ? "" : props.data.logoUrl));
const rootStyle = computed(() => ({
  width: `${size.value.width}px`,
  height: `${size.value.height}px`,
  "--c1": props.data.primary,
  "--c2": props.data.secondary,
  "--on1": readableOn(props.data.primary),
  "--on2": readableOn(props.data.secondary)
}));
const bg = computed(() => (props.photo ? { backgroundImage: `url("${props.photo}")` } : {}));
const titleStyle = computed(() => {
  const length = props.data.title.length;
  const px = length > 60 ? 70 : length > 42 ? 84 : length > 26 ? 100 : 116;
  return { fontSize: `${Math.round(px * (props.format === "square" ? 0.86 : 1))}px` };
});

const days = computed(() => (props.slide.kind === "itinerary" ? props.data.itinerary.slice(props.slide.from, props.slide.to) : []));
const included = computed(() => props.data.benefits.filter(Boolean).slice(0, props.format === "story" ? 8 : 6));
const prices = computed(() => props.data.prices.slice(0, pricesPerSlide(props.format)));

const eyebrow = computed(() => {
  const slide = props.slide;
  if (slide.kind === "itinerary") return slide.parts > 1 ? `Roteiro · parte ${slide.part} de ${slide.parts}` : "Roteiro";
  if (slide.kind === "included") return "Incluso";
  if (slide.kind === "flights") return "Voos";
  if (slide.kind === "prices") return "Valores";
  return "";
});
const heading = computed(() => {
  const kind = props.slide.kind;
  if (kind === "itinerary") return "Dia a dia da viagem";
  if (kind === "included") return "O que está incluso";
  if (kind === "flights") return props.data.flights.length > 1 ? "Ida e volta" : "Voo";
  if (kind === "prices") return props.data.prices.length > 1 ? "Opções de valores" : "Investimento";
  return "";
});
</script>

<style scoped>
.cs {
  position: relative;
  overflow: hidden;
  background: var(--c1);
  color: var(--on1);
  font-family: Inter, system-ui, sans-serif;
}
.cs * {
  box-sizing: border-box;
}
.cs-photo {
  background-color: color-mix(in srgb, var(--c1) 70%, #000);
  background-position: center;
  background-size: cover;
}
.cs-fill {
  position: absolute;
  inset: 0;
}
.cs-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0) 28%, rgba(0, 0, 0, 0.2) 48%, rgba(0, 0, 0, 0.86) 100%);
}
.cs-logo {
  display: block;
  object-fit: contain;
}
.cs-logo-top {
  position: absolute;
  top: 56px;
  left: 64px;
  z-index: 2;
  max-width: 300px;
  max-height: 120px;
  filter: drop-shadow(0 4px 16px rgba(0, 0, 0, 0.35));
}
.cs-over {
  position: absolute;
  right: 64px;
  bottom: 150px;
  left: 64px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  color: #fff;
}
.cs-story .cs-over {
  bottom: 200px;
}
.cs-tag {
  margin-bottom: 26px;
  padding: 4px 0 4px 20px;
  border-left: 8px solid var(--c2);
  font-size: 32px;
  font-weight: 700;
}
.cs-title {
  margin: 0;
  font-family: Sora, Inter, sans-serif;
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: -0.02em;
}
.cs-sub {
  margin: 22px 0 0;
  font-size: 36px;
  line-height: 1.3;
  opacity: 0.92;
}
.cs-eyebrow {
  display: block;
  margin-bottom: 16px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.85;
}
.cs-price {
  display: flex;
  flex-direction: column;
  margin-top: 34px;
}
.cs-price small {
  font-size: 30px;
  font-weight: 600;
  opacity: 0.9;
}
.cs-price b {
  color: var(--c2);
  font-family: Sora, sans-serif;
  font-size: 104px;
  font-weight: 800;
  line-height: 1.05;
}
/* O único "botão" do carrossel: só com Saiba mais / Garanta agora. */
.cs-cta {
  margin-top: 36px;
  padding: 26px 52px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 38px;
  font-weight: 800;
}
.cs-contact {
  margin: 26px 0 0;
  font-size: 32px;
  font-weight: 700;
}

/* Bloco de texto preso embaixo: só tem a altura do conteúdo, e a sombra (degradê para a cor
   de fundo) nasce um pouco acima dele. Com muito texto ele sobe até perto do topo. */
.cs-body {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  max-height: calc(100% - 90px);
  padding: 220px 72px 170px;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--c1) 0%, transparent) 0,
    color-mix(in srgb, var(--c1) 72%, transparent) 130px,
    var(--c1) 230px
  );
}
.cs-story .cs-body {
  padding-bottom: 210px;
}
.cs-heading {
  margin: 0 0 34px;
  font-family: Sora, Inter, sans-serif;
  font-size: 68px;
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.02em;
}
.cs-square .cs-heading {
  margin-bottom: 24px;
  font-size: 56px;
}

/* Itens que não cabem inteiros vão para uma "coluna" fora da arte (nunca aparecem cortados). */
.cs-days,
.cs-checks,
.cs-flights,
.cs-prices {
  display: flex;
  flex: 0 1 auto;
  flex-direction: column;
  flex-wrap: wrap;
  column-gap: 2000px;
  min-height: 0;
  overflow: hidden;
  margin: 0;
  padding: 0;
  list-style: none;
}
.cs-days li {
  display: flex;
  gap: 26px;
  width: 100%;
  margin-bottom: 30px;
}
.cs-days i,
.cs-checks i {
  display: grid;
  flex: none;
  place-items: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--c2);
  color: var(--on2);
  font-size: 30px;
  font-style: normal;
  font-weight: 800;
}
.cs-days b {
  display: block;
  font-size: 36px;
  line-height: 1.2;
}
.cs-days p {
  margin: 8px 0 0;
  font-size: 27px;
  line-height: 1.35;
  opacity: 0.85;
}
.cs-checks li {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 26px;
  font-size: 38px;
  font-weight: 600;
}
.cs-checks i {
  width: 54px;
  height: 54px;
  font-size: 28px;
}
.cs-flight {
  width: 100%;
  margin-bottom: 34px;
  padding-left: 26px;
  border-left: 8px solid var(--c2);
}
.cs-flight-label {
  display: block;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.85;
}
.cs-flight b {
  display: block;
  margin-top: 8px;
  font-size: 40px;
  line-height: 1.2;
}
.cs-flight p {
  margin: 8px 0 0;
  font-size: 30px;
  opacity: 0.9;
}
.cs-price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 30px;
  width: 100%;
  padding: 24px 0;
  border-bottom: 2px solid color-mix(in srgb, var(--on1) 22%, transparent);
}
.cs-price-row b {
  font-size: 36px;
}
.cs-price-row p {
  margin: 6px 0 0;
  font-size: 26px;
  opacity: 0.85;
}
.cs-price-value {
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: flex-end;
}
.cs-price-value small {
  font-size: 24px;
  opacity: 0.85;
}
.cs-price-value strong {
  color: var(--c2);
  font-family: Sora, sans-serif;
  font-size: 58px;
  font-weight: 800;
}
.cs-note {
  width: 100%;
  margin: 24px 0 0;
  font-size: 30px;
  font-weight: 600;
}

.cs-foot {
  position: absolute;
  right: 64px;
  bottom: 52px;
  left: 64px;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  min-height: 72px;
}
.cs-cover .cs-foot,
.cs-final .cs-foot {
  color: #fff;
}
.cs-story .cs-foot {
  bottom: 84px;
}
.cs-logo-foot {
  max-width: 220px;
  max-height: 64px;
}
.cs-agency {
  font-size: 28px;
  font-weight: 700;
}
.cs-pager {
  display: flex;
  align-items: center;
  gap: 28px;
  margin-left: auto;
}
.cs-dots {
  display: flex;
  align-items: center;
  gap: 12px;
}
.cs-dots i {
  display: block;
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.35;
}
.cs-dots i.on {
  width: 48px;
  background: var(--c2);
  opacity: 1;
}
.cs-next {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--c2);
  color: var(--on2);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}
.cs-next svg {
  width: 36px;
  height: 36px;
}
</style>
