<template>
  <div class="cs" :class="[`cs-${slide.kind}`, `cs-${format}`, { 'cs-cover-like': coverLike }]" :style="rootStyle">
    <!-- Capa e chamada final: foto inteira com o texto por cima -->
    <template v-if="coverLike">
      <div class="cs-photo cs-fill" :style="bg"></div>
      <div class="cs-shade"></div>
      <img v-if="logo" :src="logo" class="cs-logo cs-logo-top" alt="" />
      <div class="cs-over">
        <template v-if="slide.kind === 'cover'">
          <FitText v-if="data.dates" class="cs-tag" :max="34" :min="20" line>{{ data.dates }}</FitText>
          <FitText class="cs-title" :max="150" :min="56" :lines="3" :line-height="0.98">{{ headline }}</FitText>
          <FitText v-if="subline" class="cs-sub" :max="38" :min="22" :lines="3" :line-height="1.3">{{ subline }}</FitText>
        </template>
        <template v-else>
          <FitText v-if="data.agencyName" class="cs-eyebrow" :max="30" :min="18" line>{{ data.agencyName }}</FitText>
          <FitText class="cs-title" :max="130" :min="52" :lines="2" :line-height="0.98">{{ headline }}</FitText>
          <FitText v-if="price.has" class="cs-price" :max="118" :min="56"><CreativePrice :data="data" variant="side" /></FitText>
          <span v-if="cta" class="cs-cta">{{ cta }}</span>
          <FitText v-if="data.contact" class="cs-contact" :max="34" :min="20" line>WhatsApp {{ data.contact }}</FitText>
        </template>
      </div>
    </template>

    <!-- Slides de conteúdo: a foto ocupa o espaço que o texto não usa; o texto fica embaixo, com
         a sombra só atrás dele. Muito texto = a fonte diminui até caber (nada some ou corta). -->
    <template v-else>
      <div class="cs-photo cs-top-photo" :style="bg"></div>
      <div class="cs-body">
        <span class="cs-eyebrow">{{ eyebrow }}</span>
        <FitText class="cs-heading" :max="80" :min="44" :lines="2" :line-height="1.02">{{ heading }}</FitText>

        <FitText class="cs-list" :max="format === 'story' ? 56 : 46" :min="20" fill>
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
            <li v-for="item in included" :key="item.label"><i><component :is="item.icon" /></i>{{ item.label }}</li>
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
            <p v-if="installmentText" class="cs-note">{{ installmentText }}</p>
          </div>
        </FitText>
      </div>
    </template>

    <!-- Base do carrossel: logo, um ponto por slide (o atual alongado) e a seta para o próximo. -->
    <CreativeTapes v-if="data.tapes && slide.kind === 'cover'" :text="tapeLabel" />
    <div class="cs-foot">
      <img v-if="logo && !coverLike" :src="logo" class="cs-logo cs-logo-foot" alt="" />
      <span v-else-if="!coverLike && data.agencyName" class="cs-agency">{{ data.agencyName }}</span>
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
import "./creativeFonts";
import { FORMAT_SIZES, effectiveColors, priceParts, readableOn, tapeText, type CreativeData, type CreativeFormat } from "./creativeData";
import { inclusionIcon } from "./creativeIcons";
import CreativePrice from "./CreativePrice.vue";
import CreativeTapes from "./CreativeTapes.vue";
import FitText from "./FitText.vue";
import { pricesPerSlide, type CarouselSlide } from "./carousel";

const props = defineProps<{
  slide: CarouselSlide;
  format: CreativeFormat;
  data: CreativeData;
  photo: string;
  /** Usado só pelo estilo em páginas; aqui fica ignorado. */
  photos?: string[];
  index: number;
  total: number;
  showLogo?: boolean;
}>();

// Áreas livres de cada formato (no Stories, a interface do Instagram cobre topo e base).
const SAFE: Record<CreativeFormat, { pad: number; top: number; foot: number }> = {
  feed: { pad: 64, top: 64, foot: 52 },
  square: { pad: 56, top: 52, foot: 44 },
  story: { pad: 72, top: 210, foot: 220 }
};

const size = computed(() => FORMAT_SIZES[props.format]);
const coverLike = computed(() => props.slide.kind === "cover" || props.slide.kind === "final");
const cta = computed(() => (props.data.ctaEnabled ? props.data.cta.trim() : ""));
const logo = computed(() => (props.showLogo === false ? "" : props.data.logoUrl));
const colors = computed(() => effectiveColors(props.data));
const rootStyle = computed(() => {
  const safe = SAFE[props.format];
  return {
    width: `${size.value.width}px`,
    height: `${size.value.height}px`,
    "--c1": colors.value.primary,
    "--c2": colors.value.secondary,
    "--on1": readableOn(colors.value.primary),
    "--on2": readableOn(colors.value.secondary),
    "--pad": `${safe.pad}px`,
    "--top": `${safe.top}px`,
    "--foot": `${safe.foot}px`
  };
});
const price = computed(() => priceParts(props.data));
const installmentText = computed(() => price.value.installmentText);
const tapeLabel = computed(() => tapeText(props.data));
const bg = computed(() => (props.photo ? { backgroundImage: `url("${props.photo}")` } : {}));
// Capa: o nome curto em destaque; o resto do título (depois de ":") vira a linha de apoio.
const headline = computed(() => (props.data.destination || props.data.title).trim());
const subline = computed(() => {
  const rest = props.data.title.trim().slice(headline.value.length).replace(/^[\s:|–—-]+/, "");
  return rest || props.data.subtitle;
});

const days = computed(() => (props.slide.kind === "itinerary" ? props.data.itinerary.slice(props.slide.from, props.slide.to) : []));
const included = computed(() =>
  props.data.benefits
    .filter(Boolean)
    .slice(0, props.format === "story" ? 8 : 6)
    .map(label => ({ label, icon: inclusionIcon(label) }))
);
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
  display: flex;
  overflow: hidden;
  flex-direction: column;
  background: var(--c1);
  color: var(--on1);
  font-family: "Montserrat", sans-serif;
  -webkit-font-smoothing: antialiased;
}
.cs * {
  box-sizing: border-box;
}
.cs :deep(svg) {
  flex: none;
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
  top: var(--top);
  left: var(--pad);
  z-index: 2;
  max-width: 320px;
  max-height: 120px;
  padding: 14px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}

/* ---------- Capa e final ---------- */
.cs-over {
  position: absolute;
  right: var(--pad);
  bottom: calc(var(--foot) + 120px);
  left: var(--pad);
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 22px;
  color: #fff;
  --pz-accent: var(--c2);
}
.cs-tag {
  padding: 0.12em 0 0.12em 0.6em;
  border-left: 0.24em solid var(--c2);
  font-weight: 700;
}
.cs-title {
  width: 100%;
  font-weight: 900;
  letter-spacing: -0.02em;
  text-wrap-style: balance;
  text-shadow: 0 6px 30px rgba(0, 0, 0, 0.3);
}
.cs-sub {
  width: 100%;
  font-weight: 500;
  opacity: 0.92;
}
.cs-eyebrow {
  display: block;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.85;
}
.cs-price {
  margin-top: 6px;
}
/* O único "botão" do carrossel: só com Saiba mais / Garanta agora. */
.cs-cta {
  padding: 26px 52px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 38px;
  font-weight: 800;
  white-space: nowrap;
}
.cs-contact {
  font-weight: 700;
}

/* ---------- Slides de conteúdo ---------- */
/* A foto ocupa o que sobra em cima e entra um pouco por baixo da sombra do texto. */
.cs-top-photo {
  min-height: 24%;
  flex: 1 1 auto;
  margin-bottom: -200px;
}
.cs-body {
  position: relative;
  z-index: 1;
  display: flex;
  max-height: calc(100% - var(--top) - 40px);
  flex: none;
  flex-direction: column;
  padding: 220px var(--pad) calc(var(--foot) + 110px);
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--c1) 0%, transparent) 0,
    color-mix(in srgb, var(--c1) 72%, transparent) 130px,
    var(--c1) 230px
  );
}
.cs-body > .cs-eyebrow {
  margin-bottom: 12px;
}
.cs-heading {
  margin-bottom: 0.45em;
  font-weight: 900;
  letter-spacing: -0.02em;
}
/* Lista: altura do próprio conteúdo; se o bloco bater no limite, a fonte diminui até caber. */
.cs-list {
  height: auto;
  flex: 0 1 auto;
}
.cs-days,
.cs-checks {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  list-style: none;
}
.cs-days {
  gap: 0.75em;
}
.cs-days li {
  display: flex;
  gap: 0.65em;
}
.cs-days i,
.cs-checks i {
  display: grid;
  flex: none;
  place-items: center;
  width: 1.5em;
  height: 1.5em;
  border-radius: 50%;
  background: var(--c2);
  color: var(--on2);
  font-size: 0.85em;
  font-style: normal;
  font-weight: 800;
}
.cs-days b {
  display: block;
  font-weight: 800;
  line-height: 1.2;
}
.cs-days p {
  margin: 0.2em 0 0;
  font-size: 0.72em;
  font-weight: 500;
  line-height: 1.35;
  opacity: 0.85;
}
.cs-checks {
  gap: 0.6em;
}
.cs-checks li {
  display: flex;
  align-items: center;
  gap: 0.6em;
  font-weight: 700;
  line-height: 1.2;
}
.cs-checks i :deep(svg) {
  width: 0.62em;
  height: 0.62em;
}
.cs-flights {
  display: flex;
  flex-direction: column;
  gap: 0.8em;
}
.cs-flight {
  padding-left: 0.6em;
  border-left: 0.2em solid var(--c2);
}
.cs-flight-label {
  display: block;
  font-size: 0.7em;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.85;
}
.cs-flight b {
  display: block;
  margin-top: 0.15em;
  font-weight: 800;
  line-height: 1.2;
}
.cs-flight p {
  margin: 0.15em 0 0;
  font-size: 0.75em;
  opacity: 0.9;
}
.cs-prices {
  display: flex;
  flex-direction: column;
}
.cs-price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8em;
  padding: 0.55em 0;
  border-bottom: 2px solid color-mix(in srgb, var(--on1) 22%, transparent);
}
.cs-price-row b {
  font-weight: 800;
}
.cs-price-row p {
  margin: 0.15em 0 0;
  font-size: 0.7em;
  opacity: 0.85;
}
.cs-price-value {
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: flex-end;
}
.cs-price-value small {
  font-size: 0.62em;
  opacity: 0.85;
}
.cs-price-value strong {
  color: var(--c2);
  font-size: 1.5em;
  font-weight: 900;
  letter-spacing: -0.02em;
}
.cs-note {
  margin: 0.6em 0 0;
  font-size: 0.8em;
  font-weight: 600;
}

/* ---------- Base ---------- */
.cs-foot {
  position: absolute;
  right: var(--pad);
  bottom: var(--foot);
  left: var(--pad);
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  min-height: 72px;
}
.cs-cover-like .cs-foot {
  color: #fff;
}
.cs-logo-foot {
  max-width: 240px;
  max-height: 72px;
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
