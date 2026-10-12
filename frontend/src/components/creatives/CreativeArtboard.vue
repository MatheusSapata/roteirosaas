<template>
  <div class="cr" :class="[`cr-t-${template}`, `cr-${format}`]" :style="rootStyle">
    <!-- 1. Foto cheia -->
    <template v-if="template === 'full-photo'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="cr-shade"></div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-top" alt="" />
      <div class="cr-bottom">
        <span v-if="data.dates" class="cr-pill">{{ data.dates }}</span>
        <h1 class="cr-title cr-light" :style="titleStyle">{{ data.title }}</h1>
        <p v-if="data.subtitle && format !== 'square'" class="cr-sub cr-light">{{ data.subtitle }}</p>
        <div v-if="data.priceValue" class="cr-price-badge">
          <small>{{ data.pricePrefix }}</small>
          <b>{{ data.priceValue }}</b>
          <small>{{ data.priceSuffix }}</small>
        </div>
      </div>
    </template>

    <!-- 2. Faixa colorida -->
    <template v-else-if="template === 'color-band'">
      <div class="cr-photo cr-band-photo" :style="bg(0)"></div>
      <div class="cr-band">
        <img v-if="logo" :src="logo" class="cr-logo cr-logo-band" alt="" />
        <span v-if="data.dates" class="cr-eyebrow">{{ data.dates }}</span>
        <h1 class="cr-title" :style="titleStyle">{{ data.title }}</h1>
        <div v-if="data.priceValue" class="cr-price-line">
          <span>{{ data.pricePrefix }}</span>
          <b>{{ data.priceValue }}</b>
          <span>{{ data.priceSuffix }}</span>
        </div>
        <p v-if="data.installments" class="cr-small">{{ data.installments }}</p>
      </div>
    </template>

    <!-- 3. Moldura -->
    <template v-else-if="template === 'frame'">
      <div class="cr-frame-wrap">
        <img v-if="logo" :src="logo" class="cr-logo cr-logo-center" alt="" />
        <div class="cr-photo cr-frame-photo" :style="bg(0)"></div>
        <h1 class="cr-title cr-center" :style="titleStyle">{{ data.title }}</h1>
        <p v-if="data.dates" class="cr-center cr-dates">{{ data.dates }}</p>
        <div v-if="data.priceValue" class="cr-price-chip">{{ data.pricePrefix }} <b>{{ data.priceValue }}</b> {{ data.priceSuffix }}</div>
      </div>
    </template>

    <!-- 4. Preço em destaque -->
    <template v-else-if="template === 'price-hero'">
      <div class="cr-photo cr-ph-photo" :style="bg(0)"></div>
      <div class="cr-ph-body">
        <img v-if="logo" :src="logo" class="cr-logo cr-logo-band" alt="" />
        <span class="cr-eyebrow">{{ data.title }}</span>
        <template v-if="data.priceValue">
          <span class="cr-ph-prefix">{{ data.pricePrefix || "A partir de" }}</span>
          <b class="cr-ph-value">{{ data.priceValue }}</b>
          <span class="cr-ph-suffix">{{ [data.priceSuffix, data.installments].filter(Boolean).join(" · ") }}</span>
        </template>
        <h1 v-else class="cr-title" :style="titleStyle">{{ data.title }}</h1>
        <span v-if="data.dates" class="cr-pill cr-pill-dark">{{ data.dates }}</span>
      </div>
    </template>

    <!-- 5. Lista de benefícios -->
    <template v-else-if="template === 'benefits'">
      <div class="cr-photo cr-bn-photo" :style="bg(0)">
        <img v-if="logo" :src="logo" class="cr-logo cr-logo-top" alt="" />
      </div>
      <div class="cr-bn-body">
        <span v-if="data.dates" class="cr-eyebrow">{{ data.dates }}</span>
        <h1 class="cr-title" :style="titleStyle">{{ data.title }}</h1>
        <ul v-if="benefits.length" class="cr-checks">
          <li v-for="item in benefits" :key="item"><i>✓</i>{{ item }}</li>
        </ul>
        <div class="cr-bn-foot">
          <div v-if="data.priceValue" class="cr-price-stack">
            <small>{{ data.pricePrefix }}</small>
            <b>{{ data.priceValue }}</b>
            <small>{{ [data.priceSuffix, data.installments].filter(Boolean).join(" · ") }}</small>
          </div>
          <div class="cr-cta">{{ data.cta }}<small v-if="data.contact">{{ data.contact }}</small></div>
        </div>
      </div>
    </template>

    <!-- 6. Cartão com tudo -->
    <template v-else-if="template === 'card'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="cr-shade cr-shade-soft"></div>
      <div class="cr-card">
        <div class="cr-card-head">
          <img v-if="logo" :src="logo" class="cr-logo cr-logo-card" alt="" />
          <span v-if="data.dates" class="cr-pill cr-pill-brand">{{ data.dates }}</span>
        </div>
        <h1 class="cr-title cr-dark" :style="titleStyle">{{ data.title }}</h1>
        <p v-if="data.subtitle && format !== 'square'" class="cr-sub cr-dark">{{ data.subtitle }}</p>
        <ul v-if="benefits.length" class="cr-checks cr-checks-dark">
          <li v-for="item in benefits.slice(0, format === 'square' ? 3 : 5)" :key="item"><i>✓</i>{{ item }}</li>
        </ul>
        <div class="cr-card-foot">
          <div v-if="data.priceValue" class="cr-price-stack cr-dark">
            <small>{{ data.pricePrefix }}</small>
            <b class="cr-brand-text">{{ data.priceValue }}</b>
            <small>{{ [data.priceSuffix, data.installments].filter(Boolean).join(" · ") }}</small>
          </div>
          <div class="cr-cta">{{ data.cta }}<small v-if="data.contact">{{ data.contact }}</small></div>
        </div>
      </div>
    </template>

    <!-- 7. Colagem de 2 fotos -->
    <template v-else-if="template === 'collage-2'">
      <div class="cr-collage2">
        <div class="cr-photo" :style="bg(0)"></div>
        <div class="cr-photo" :style="bg(1)"></div>
      </div>
      <div class="cr-c2-band">
        <img v-if="logo" :src="logo" class="cr-logo cr-logo-band" alt="" />
        <h1 class="cr-title" :style="titleStyle">{{ data.title }}</h1>
        <div class="cr-c2-row">
          <span v-if="data.dates" class="cr-pill cr-pill-dark">{{ data.dates }}</span>
          <div v-if="data.priceValue" class="cr-price-line"><span>{{ data.pricePrefix }}</span><b>{{ data.priceValue }}</b></div>
        </div>
      </div>
    </template>

    <!-- 8. Mosaico de 3 fotos -->
    <template v-else-if="template === 'mosaic-3'">
      <div class="cr-mosaic">
        <div class="cr-photo cr-m-big" :style="bg(0)"></div>
        <div class="cr-photo" :style="bg(1)"></div>
        <div class="cr-photo" :style="bg(2)"></div>
      </div>
      <div class="cr-m-body">
        <div class="cr-m-text">
          <span v-if="data.dates" class="cr-eyebrow">{{ data.dates }}</span>
          <h1 class="cr-title" :style="titleStyle">{{ data.title }}</h1>
          <p v-if="benefits.length && format !== 'square'" class="cr-small">{{ benefits.slice(0, 4).join(" · ") }}</p>
        </div>
        <div v-if="data.priceValue" class="cr-price-stack cr-price-box">
          <small>{{ data.pricePrefix }}</small>
          <b>{{ data.priceValue }}</b>
          <small>{{ data.priceSuffix }}</small>
        </div>
      </div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-corner" alt="" />
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Um criativo em tamanho real (1080 px de largura). A tela mostra reduzido com transform e o
 * download (html-to-image) usa este mesmo elemento, então o que se vê é o que se baixa.
 */
import { computed } from "vue";
import { FORMAT_SIZES, readableOn, type CreativeData, type CreativeFormat } from "./creativeData";

const props = defineProps<{
  template: string;
  format: CreativeFormat;
  data: CreativeData;
  /** Fotos já prontas para uso (endereços locais/blob), na ordem escolhida. */
  photos: string[];
  showLogo?: boolean;
}>();

const size = computed(() => FORMAT_SIZES[props.format]);
const logo = computed(() => (props.showLogo === false ? "" : props.data.logoUrl));
// Quantos benefícios cabem sem empurrar o preço para fora da arte.
const benefits = computed(() => props.data.benefits.filter(Boolean).slice(0, { square: 3, feed: 4, story: 6 }[props.format]));
const rootStyle = computed(() => ({
  width: `${size.value.width}px`,
  height: `${size.value.height}px`,
  "--c1": props.data.primary,
  "--c2": props.data.secondary,
  "--on1": readableOn(props.data.primary),
  "--on2": readableOn(props.data.secondary)
}));
// Título encolhe com o tamanho do texto, para nunca estourar.
const titleStyle = computed(() => {
  const length = props.data.title.length;
  const base = props.format === "square" ? 0.86 : 1;
  const px = length > 60 ? 64 : length > 42 ? 76 : length > 26 ? 92 : 108;
  return { fontSize: `${Math.round(px * base)}px` };
});
const bg = (index: number) => {
  const url = props.photos[index] || props.photos[0] || "";
  return url ? { backgroundImage: `url("${url}")` } : {};
};
</script>

<style scoped>
.cr {
  position: relative;
  overflow: hidden;
  background: var(--c1);
  color: var(--on1);
  font-family: Inter, system-ui, sans-serif;
}
.cr * {
  box-sizing: border-box;
}
.cr-photo {
  background-color: color-mix(in srgb, var(--c1) 70%, #000);
  background-position: center;
  background-size: cover;
}
.cr-fill {
  position: absolute;
  inset: 0;
}
.cr-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.35) 0%, rgba(0, 0, 0, 0) 30%, rgba(0, 0, 0, 0.15) 50%, rgba(0, 0, 0, 0.82) 100%);
}
.cr-shade-soft {
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0.1) 40%, rgba(0, 0, 0, 0.45));
}
.cr-title {
  margin: 0;
  font-family: Sora, Inter, sans-serif;
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: -0.02em;
}
.cr-light {
  color: #fff;
}
.cr-dark {
  color: #111827;
}
.cr-center {
  text-align: center;
}
.cr-sub {
  margin: 18px 0 0;
  font-size: 34px;
  line-height: 1.3;
  opacity: 0.92;
}
.cr-small {
  margin: 16px 0 0;
  font-size: 30px;
  opacity: 0.9;
}
.cr-eyebrow {
  display: block;
  margin-bottom: 18px;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.85;
}
.cr-pill {
  display: inline-block;
  padding: 12px 26px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 30px;
  font-weight: 700;
}
.cr-pill-dark {
  background: rgba(0, 0, 0, 0.22);
  color: inherit;
}
.cr-pill-brand {
  background: var(--c1);
  color: var(--on1);
}
.cr-logo {
  position: relative;
  z-index: 2;
  display: block;
  max-width: 300px;
  max-height: 120px;
  object-fit: contain;
}
.cr-logo-top {
  position: absolute;
  top: 56px;
  left: 64px;
  filter: drop-shadow(0 4px 16px rgba(0, 0, 0, 0.35));
}
.cr-logo-band {
  max-height: 96px;
  margin-bottom: 28px;
}
.cr-logo-center {
  margin: 0 auto 36px;
  max-height: 100px;
}
.cr-logo-card {
  max-height: 84px;
  max-width: 260px;
}
.cr-logo-corner {
  position: absolute;
  top: 48px;
  right: 48px;
  max-height: 90px;
  padding: 14px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.92);
}

/* 1. Foto cheia */
.cr-bottom {
  position: absolute;
  right: 64px;
  bottom: 72px;
  left: 64px;
  z-index: 2;
}
.cr-bottom .cr-pill {
  margin-bottom: 26px;
}
.cr-price-badge {
  display: inline-flex;
  align-items: baseline;
  gap: 14px;
  margin-top: 36px;
  padding: 22px 34px;
  border-radius: 28px;
  background: var(--c2);
  color: var(--on2);
}
.cr-price-badge b {
  font-family: Sora, sans-serif;
  font-size: 72px;
  font-weight: 800;
}
.cr-price-badge small {
  font-size: 28px;
  font-weight: 600;
}

/* 2. Faixa colorida */
.cr-band-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: 58%;
}
.cr-band {
  position: absolute;
  inset: auto 0 0 0;
  min-height: 42%;
  padding: 64px 72px 72px;
  border-radius: 56px 56px 0 0;
  background: var(--c1);
}
.cr-story .cr-band-photo {
  height: 62%;
}
.cr-story .cr-band {
  min-height: 38%;
}
.cr-price-line {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-top: 28px;
  font-size: 30px;
  font-weight: 600;
}
.cr-price-line b {
  color: var(--c2);
  font-family: Sora, sans-serif;
  font-size: 76px;
  font-weight: 800;
}

/* 3. Moldura */
.cr-frame-wrap {
  display: flex;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 72px;
}
.cr-frame-photo {
  width: 100%;
  flex: 1 1 auto;
  max-height: 62%;
  margin-bottom: 44px;
  border: 14px solid #fff;
  border-radius: 40px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.25);
}
.cr-dates {
  margin: 18px 0 0;
  font-size: 32px;
  font-weight: 600;
  opacity: 0.9;
}
.cr-price-chip {
  margin-top: 30px;
  padding: 18px 40px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 32px;
  font-weight: 600;
}
.cr-price-chip b {
  font-family: Sora, sans-serif;
  font-size: 54px;
  font-weight: 800;
}

/* 4. Preço em destaque */
.cr-ph-photo {
  position: absolute;
  top: -12%;
  right: -22%;
  width: 78%;
  aspect-ratio: 1;
  border: 18px solid var(--c2);
  border-radius: 50%;
}
.cr-square .cr-ph-photo {
  top: -16%;
  width: 62%;
}
.cr-ph-body {
  position: absolute;
  inset: auto 72px 80px 72px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.cr-ph-prefix {
  font-size: 44px;
  font-weight: 600;
}
.cr-ph-value {
  margin: 4px 0 6px;
  font-family: Sora, sans-serif;
  font-size: 170px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--c2);
}
.cr-square .cr-ph-value {
  font-size: 140px;
}
.cr-ph-suffix {
  margin-bottom: 36px;
  font-size: 34px;
  opacity: 0.9;
}

/* 5. Lista de benefícios */
.cr-bn-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: 38%;
}
.cr-square .cr-bn-photo {
  height: 34%;
}
.cr-bn-body {
  position: absolute;
  inset: 38% 0 0 0;
  display: flex;
  flex-direction: column;
  padding: 56px 72px 64px;
}
.cr-square .cr-bn-body {
  inset: 34% 0 0 0;
  padding-top: 44px;
}
/* Benefício que não cabe inteiro vai para uma "coluna" fora da arte (nunca aparece cortado). */
.cr-checks {
  display: flex;
  flex: 0 1 auto;
  flex-direction: column;
  flex-wrap: wrap;
  column-gap: 2000px;
  min-height: 0;
  overflow: hidden;
  margin: 30px 0 0;
  padding: 0;
  list-style: none;
  font-size: 32px;
  font-weight: 600;
}
.cr-checks li {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 16px;
}
.cr-checks i {
  display: grid;
  flex: none;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: var(--c2);
  color: var(--on2);
  font-size: 26px;
  font-style: normal;
}
.cr-checks-dark {
  color: #1f2937;
}
.cr-bn-foot,
.cr-card-foot {
  flex: none;
  padding-top: 28px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-top: auto;
}
.cr-price-stack {
  display: flex;
  flex-direction: column;
}
.cr-price-stack small {
  font-size: 26px;
  font-weight: 600;
  opacity: 0.85;
}
.cr-price-stack b {
  font-family: Sora, sans-serif;
  font-size: 80px;
  font-weight: 800;
  line-height: 1.05;
}
.cr-brand-text {
  color: var(--c1);
}
.cr-cta {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 34px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 32px;
  font-weight: 800;
  text-align: center;
}
.cr-cta small {
  font-size: 24px;
  font-weight: 600;
}

/* 6. Cartão */
.cr-card {
  position: absolute;
  right: 56px;
  bottom: 56px;
  left: 56px;
  display: flex;
  flex-direction: column;
  max-height: calc(100% - 112px);
  padding: 52px 56px;
  border-radius: 44px;
  background: #fff;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.3);
}
.cr-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 30px;
}
.cr-card .cr-sub {
  font-size: 30px;
}
.cr-card-foot {
  margin-top: 30px;
}

/* 7. Colagem de 2 */
.cr-collage2 {
  position: absolute;
  inset: 0 0 auto 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  height: 60%;
  background: #fff;
}
.cr-story .cr-collage2 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr 1fr;
  height: 64%;
}
.cr-c2-band {
  position: absolute;
  inset: auto 0 0 0;
  min-height: 40%;
  padding: 56px 72px 64px;
}
.cr-story .cr-c2-band {
  min-height: 36%;
}
.cr-c2-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-top: 28px;
}
.cr-c2-row .cr-price-line {
  margin-top: 0;
}

/* 8. Mosaico de 3 */
.cr-mosaic {
  position: absolute;
  inset: 0 0 auto 0;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 12px;
  height: 62%;
  background: #fff;
}
.cr-m-big {
  grid-row: span 2;
}
.cr-story .cr-mosaic {
  height: 66%;
}
.cr-m-body {
  position: absolute;
  inset: auto 0 0 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 30px;
  min-height: 38%;
  padding: 52px 64px 60px;
}
.cr-m-text {
  flex: 1;
  min-width: 0;
}
.cr-price-box {
  flex: none;
  padding: 24px 30px;
  border-radius: 28px;
  background: var(--c2);
  color: var(--on2);
}
.cr-price-box b {
  font-size: 64px;
}
</style>
