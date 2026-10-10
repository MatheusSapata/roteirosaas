<template>
  <V2Section type="hero" :background="textBg" :anchor-id="section.anchorId" full>
    <!-- Imersivo (padrão): foto inteira atrás do texto; no celular a foto fica quase
         quadrada no topo e o texto assenta na cor de fundo, que sobe em degradê. -->
    <div v-if="layout === 'immersive'" class="v2-hero v2-hero--imm" :class="{ 'has-logo': topLogo }" :style="heroVars">
      <div class="v2-hero-media" aria-hidden="true">
        <iframe v-if="video" :src="video" title="" tabindex="-1" allow="autoplay; encrypted-media"></iframe>
        <picture v-else-if="image">
          <source v-if="mobileImage" :srcset="responsiveSrcset(mobileImage) || mobileImage" sizes="100vw" media="(max-width: 640px)" />
          <V2Img :src="image" alt="" priority />
        </picture>
      </div>
      <div class="v2-hero-fade" aria-hidden="true"></div>
      <div class="v2-hero-spacer" aria-hidden="true"></div>
      <div class="v2-hero-inner">
        <HeroContent v-bind="contentProps" />
      </div>
      <div v-if="topLogo" class="v2-hero-logo"><img :src="logo" :alt="agencyName" :style="logoStyle" v-bind="logoAttrs" /></div>
    </div>

    <div v-else-if="layout === 'classic'" class="v2-hero v2-hero--classic" :class="{ 'has-logo': topLogo }" :style="heroVars">
      <div class="v2-hero-media" aria-hidden="true">
        <iframe v-if="video" :src="video" title="" tabindex="-1" allow="autoplay; encrypted-media"></iframe>
        <V2Img v-else-if="image" :src="image" alt="" priority />
      </div>
      <div class="v2-hero-veil" aria-hidden="true"></div>
      <div class="v2-hero-inner is-center">
        <HeroContent v-bind="contentProps" centered />
      </div>
      <div v-if="topLogo" class="v2-hero-logo"><img :src="logo" :alt="agencyName" :style="logoStyle" v-bind="logoAttrs" /></div>
    </div>

    <div v-else-if="layout === 'split'" class="v2-hero v2-hero--split" :class="{ 'has-logo': topLogo }" :style="heroVars">
      <div v-if="topLogo" class="v2-hero-split-top"><img :src="logo" :alt="agencyName" :style="logoStyle" class="v2-hero-logo-inline" v-bind="logoAttrs" /></div>
      <div class="v2-hero-split">
        <div class="v2-hero-split-copy">
          <HeroContent v-bind="contentProps" light />
        </div>
        <div class="v2-hero-split-media">
          <V2Img v-if="image" :src="image" :alt="title" sizes="(max-width: 640px) 100vw, 50vw" priority />
        </div>
      </div>
    </div>

    <div v-else class="v2-hero v2-hero--card" :class="{ 'has-logo': topLogo }" :style="heroVars">
      <div class="v2-hero-media" aria-hidden="true"><V2Img v-if="image" :src="image" alt="" priority /></div>
      <div class="v2-hero-card-spacer" aria-hidden="true"></div>
      <div class="v2-hero-inner">
        <div class="v2-hero-card">
          <HeroContent v-bind="contentProps" light />
        </div>
      </div>
      <div v-if="topLogo" class="v2-hero-logo"><img :src="logo" :alt="agencyName" :style="logoStyle" v-bind="logoAttrs" /></div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, toRef } from "vue";
import type { HeroSection } from "../../../types/page";
import { resolveMediaUrl, responsiveSrcset } from "../../../utils/media";
import { normalizeYoutubeEmbedUrl } from "../../../utils/video";
import V2Section from "./V2Section.vue";
import V2Img from "./V2Img.vue";
import { useCta } from "./useCta";
import { html, localize, text } from "./useHeading";
import { contrast, WHITE_TEXT_MIN_CONTRAST } from "./useSectionTone";
import { useCopyFit } from "./useCopyFit";
import TravelIcon from "../../shared/TravelIcon.vue";
import { formatDayMonth, parseTripDate, tripLengthInDays } from "../../../utils/tripDates";

interface HeroChip {
  label: string;
  icon: string;
}
interface HeroDates {
  departure: string;
  back: string;
  tag: string;
}

const props = defineProps<{
  section: HeroSection;
  branding?: Record<string, any>;
  previewDevice?: "desktop" | "mobile";
  hideLogo?: boolean;
}>();

const layout = computed(() => props.section.layout || "immersive");
const textBg = computed(() => (props.section.gradientColor || "").trim() || "#0B1410");
const title = computed(() => text(props.section.title));
const subtitleHtml = computed(() => (text(props.section.subtitle) ? html(props.section.subtitle) : ""));
const chips = computed<HeroChip[]>(() =>
  (props.section.chips || [])
    .map((chip, index) => ({ label: text(chip), icon: props.section.chipIcons?.[index] || "" }))
    .filter(chip => chip.label)
);
const dates = computed<HeroDates | null>(() => {
  const start = parseTripDate(props.section.departureDate);
  if (!start) return null;
  const end = parseTripDate(props.section.returnDate);
  const valid = end && end >= start ? end : null;
  const days = valid ? tripLengthInDays(start, valid) : 0;
  const daysLabel = days ? localize({ pt: `${days} ${days === 1 ? "dia" : "dias"}`, es: `${days} ${days === 1 ? "día" : "días"}` }) : "";
  return {
    departure: formatDayMonth(start),
    back: valid ? formatDayMonth(valid) : "",
    tag: [daysLabel, String(start.getFullYear())].filter(Boolean).join(" · ")
  };
});
const image = computed(() => resolveMediaUrl(props.section.backgroundImage) || "");
const mobileImage = computed(() => resolveMediaUrl(props.section.mobileBackgroundImage) || "");
const video = computed(() => {
  const embed = normalizeYoutubeEmbedUrl(props.section.videoUrl);
  if (!embed) return "";
  const id = embed.split("/").pop()?.split("?")[0] || "";
  const join = embed.includes("?") ? "&" : "?";
  return `${embed}${join}autoplay=1&mute=1&loop=1&controls=0&playsinline=1&playlist=${id}`;
});
const agencyName = computed(() => String(props.branding?.agency_name || ""));
// Logo só quando a página não tem Menu do topo (o PublicPageView avisa com hideLogo).
const logo = computed(() => (props.hideLogo ? "" : resolveMediaUrl(props.section.logoUrl) || resolveMediaUrl(props.branding?.logo_url) || ""));
const logoHeight = computed(() => Math.max(32, Math.min(props.section.logoSize ?? 64, 160)));
// Altura do logo para as capas reservarem o espaço do "cabeçalho" no topo.
const logoVars = computed(() => ({ "--v2-logo-h": `${logoHeight.value}px` }));
const copyFit = useCopyFit(title, computed(() => localize(props.section.subtitle)));
const heroVars = computed(() => ({ ...logoVars.value, ...copyFit.vars.value }));
// Logo é o selo de confiança da página: baixa junto com a foto, na versão leve (até 160 px de
// altura cabe na de 640 px), e o servidor já o pede no HTML.
const logoAttrs = computed(() => {
  const srcset = responsiveSrcset(logo.value);
  return { srcset: srcset || undefined, sizes: srcset ? "320px" : undefined, fetchpriority: "high" as const, decoding: "async" as const };
});
const logoStyle = computed(() => ({
  height: `${logoHeight.value}px`,
  borderRadius: `${props.section.logoBorderRadius ?? 0}px`
}));
const cta = useCta(toRef(props, "section"));
const ctaLabel = computed(() => text(props.section.ctaLabel) || localize({ pt: "Quero falar agora", es: "Quiero hablar ahora" }));
const darkText = computed(() => contrast("#FFFFFF", textBg.value) < WHITE_TEXT_MIN_CONTRAST);

// Padrão: com destaques, o logo fica no topo da capa; sem eles, vem junto ao conteúdo, acima do título.
// A posição escolhida no editor (logoPosition) vale com ou sem destaques.
const topLogo = computed(() => !!logo.value && (props.section.logoPosition ? props.section.logoPosition === "top" : chips.value.length > 0));
const contentProps = computed(() => ({
  logo: topLogo.value ? "" : logo.value,
  logoAlt: agencyName.value,
  logoStyle: logoStyle.value,
  logoAttrs: logoAttrs.value,
  title: title.value,
  subtitleHtml: subtitleHtml.value,
  chips: chips.value,
  dates: dates.value,
  ctaEnabled: cta.enabled.value,
  ctaAttrs: cta.attrs.value,
  ctaLabel: ctaLabel.value,
  darkText: darkText.value
}));

const HeroContent = defineComponent({
  name: "V2HeroContent",
  props: {
    logo: { type: String, default: "" },
    logoAlt: { type: String, default: "" },
    logoStyle: { type: Object, default: () => ({}) },
    logoAttrs: { type: Object, default: () => ({}) },
    title: { type: String, default: "" },
    subtitleHtml: { type: String, default: "" },
    chips: { type: Array as () => HeroChip[], default: () => [] },
    dates: { type: Object as () => HeroDates | null, default: null },
    ctaEnabled: Boolean,
    ctaAttrs: { type: Object, default: () => ({}) },
    ctaLabel: { type: String, default: "" },
    darkText: Boolean,
    centered: Boolean,
    // "light" e não "onLight": nomes "on" + maiúscula viram evento no Vue e a opção se perdia.
    light: Boolean
  },
  setup(p) {
    const check = () =>
      h("svg", { width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2.6, "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" }, [h("path", { d: "m5 12 5 5 9-10" })]);
    const arrow = () =>
      h("svg", { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2.2, "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" }, [h("path", { d: "M5 12h14M13 6l6 6-6 6" })]);
    const calendar = () =>
      h("svg", { width: 22, height: 22, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" }, [
        h("rect", { x: 3, y: 4, width: 18, height: 18, rx: 3 }),
        h("path", { d: "M16 2v4M8 2v4M3 10h18" })
      ]);
    const dateCol = (label: string, value: string) => h("span", { class: "v2-hero-date-col" }, [h("span", label), h("b", value)]);
    const dateCard = (d: HeroDates) =>
      h("div", { class: "v2-hero-dates v2-in v2-d3" }, [
        h("span", { class: "v2-hero-dates-ico" }, [calendar()]),
        dateCol(localize({ pt: "SAÍDA", es: "SALIDA" }), d.departure),
        d.back
          ? h("span", { class: "v2-hero-dates-arrow", "aria-hidden": "true" }, [
              h("span"),
              h("svg", { width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2.6, "stroke-linecap": "round", "stroke-linejoin": "round" }, [h("path", { d: "m9 6 6 6-6 6" })])
            ])
          : null,
        d.back ? dateCol(localize({ pt: "VOLTA", es: "REGRESO" }), d.back) : null,
        d.tag ? h("span", { class: "v2-hero-dates-tag" }, d.tag) : null
      ]);
    return () =>
      h("div", { class: ["v2-hero-content", { "is-center": p.centered, "on-light": p.light, "dark-text": p.darkText && !p.light }] }, [
        p.logo ? h("img", { class: "v2-hero-logo-inline v2-hero-logo-lead v2-in", src: p.logo, alt: p.logoAlt, style: p.logoStyle, ...p.logoAttrs }) : null,
        p.chips.length
          ? h(
              "ul",
              { class: "v2-hero-chips v2-in", "aria-label": localize({ pt: "Destaques da viagem", es: "Destacados del viaje" }) },
              p.chips.map(chip =>
                h("li", [h("span", { class: "v2-hero-chip-ico" }, [chip.icon ? h(TravelIcon, { name: chip.icon, size: 14, strokeWidth: 2.2 }) : check()]), chip.label])
              )
            )
          : null,
        p.title ? h("h1", { class: "v2-hero-title v2-in v2-d1" }, p.title) : null,
        p.subtitleHtml ? h("div", { class: "v2-hero-sub v2-in v2-d2", innerHTML: p.subtitleHtml }) : null,
        p.dates || p.ctaEnabled
          ? h("div", { class: "v2-hero-actions" }, [
              p.dates ? dateCard(p.dates) : null,
              p.ctaEnabled ? h("div", { class: "v2-in v2-d3" }, [h("a", { class: "v2-btn v2-hero-btn", ...p.ctaAttrs }, [h("span", p.ctaLabel), arrow()])]) : null
            ])
          : null
      ]);
  }
});
</script>

<style>
.v2-hero {
  position: relative;
  overflow: hidden;
  color: #fff;
}
.v2-hero-media {
  position: absolute;
  inset: 0;
}
.v2-hero-media img,
.v2-hero-media picture,
.v2-hero-media iframe {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
  object-fit: cover;
  /* Mesmo enquadramento da capa antiga: foto alinhada pelo topo. */
  object-position: center top;
}
.v2-hero-media iframe {
  pointer-events: none;
  transform: scale(1.35);
}
.v2-hero-inner {
  position: relative;
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 clamp(20px, 5cqi, 40px) clamp(32px, 6cqi, 72px);
}
/* Como na capa antiga: 90% da altura da tela, compensando o zoom da página pública (--page-zoom),
   com o conteúdo inteiro visível; no celular a foto fica quase quadrada em cima. */
.v2-hero--imm {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-height: calc(90svh / var(--page-zoom, 1));
}
.v2-hero--imm .v2-hero-media,
.v2-hero--imm .v2-hero-fade {
  bottom: auto;
  height: min(100%, 112cqi);
}
/* Computador: a sombra fica do lado do texto (esquerda e base), e a direita da foto fica limpa. */
.v2-hero-fade {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(
      90deg,
      color-mix(in srgb, var(--v2-bg) 82%, transparent) 0%,
      color-mix(in srgb, var(--v2-bg) 62%, transparent) 30%,
      color-mix(in srgb, var(--v2-bg) 22%, transparent) 55%,
      transparent 72%
    ),
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--v2-bg) 22%, transparent) 0%,
      transparent 18%,
      transparent 62%,
      color-mix(in srgb, var(--v2-bg) 45%, transparent) 100%
    );
}
.v2-hero-spacer {
  position: relative;
  display: none;
  height: min(calc(112cqi - 150px), 340px);
}
.v2-hero--imm .v2-hero-inner {
  padding-top: clamp(96px, 10cqi, 140px);
}
.v2-hero-logo {
  position: absolute;
  top: clamp(16px, 3cqi, 28px);
  left: 0;
  right: 0;
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 clamp(20px, 5cqi, 40px);
}
/* A largura máxima acompanha o tamanho escolhido, para logos largos também crescerem. */
.v2-hero-logo img,
.v2-hero-logo-inline {
  display: block;
  flex-shrink: 0;
  width: auto;
  max-width: min(100%, calc(var(--v2-logo-h, 64px) * 4));
  object-fit: contain;
}
.v2-hero-logo img {
  filter: drop-shadow(0 1px 10px rgba(0, 0, 0, 0.35));
}
/* Logo junto ao conteúdo: acima dos destaques e do título, no fluxo do texto (centralizado no Clássico). */
.v2-hero-logo-lead {
  align-self: flex-start;
  margin-bottom: 2px;
}
.v2-hero-content.is-center .v2-hero-logo-lead {
  align-self: center;
}
.v2-hero--imm .v2-hero-logo-lead,
.v2-hero--classic .v2-hero-logo-lead {
  filter: drop-shadow(0 1px 10px rgba(0, 0, 0, 0.35));
}
.v2-hero-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: calc(820px + var(--v2-card-grow, 0px) / 2);
  color: var(--v2-ink);
}
.v2-hero--imm .v2-hero-content,
.v2-hero--classic .v2-hero-content {
  color: #fff;
}
.v2-hero--imm .v2-hero-content.dark-text {
  color: #0f1713;
}
.v2-hero-content.is-center {
  align-items: center;
  margin: 0 auto;
  text-align: center;
}
.v2-hero-content.on-light {
  color: #0f1713;
}
.v2-hero-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.is-center .v2-hero-chips {
  justify-content: center;
}
.v2-hero-chips li {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px 5px 5px;
  border-radius: 999px;
  /* Fundo escuro translúcido: o destaque continua legível mesmo sobre céu claro. */
  background: rgba(6, 12, 9, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(10px);
  font-size: 14px;
  font-weight: 650;
  line-height: 1.2;
}
.dark-text .v2-hero-chips li,
.on-light .v2-hero-chips li {
  background: rgba(15, 23, 19, 0.06);
  border-color: transparent;
}
.v2-hero-chip-ico {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.v2-hero-title {
  margin: 0;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-weight: 700;
  /* Acompanha a largura e também a altura da tela, para caber em monitores largos e baixos. */
  /* Título longo encolhe (--v2-title-scale, de useCopyFit) em vez de esticar a capa. */
  font-size: max(24px, calc(clamp(32px, min(5.2cqi, calc(7.5svh / var(--page-zoom, 1))), 68px) * var(--v2-title-scale, 1)));
  line-height: 0.98;
  letter-spacing: -0.035em;
  text-wrap: balance;
}
.v2-hero-sub {
  max-width: calc(640px + var(--v2-card-grow, 0px));
  font-size: max(15px, calc(clamp(17px, 1.8cqi, 20px) * var(--v2-sub-scale, 1)));
  line-height: 1.5;
  opacity: 0.88;
}
.v2-hero-sub p {
  margin: 0;
}
.v2-hero-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px 16px;
  margin-top: 4px;
}
.is-center .v2-hero-actions {
  justify-content: center;
}
.v2-hero-dates {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
  padding: 10px 18px 10px 10px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 18px 40px -22px rgba(6, 12, 9, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
}
.dark-text .v2-hero-dates,
.on-light .v2-hero-dates {
  background: rgba(255, 255, 255, 0.55);
  border-color: rgba(255, 255, 255, 0.8);
  box-shadow: 0 18px 40px -26px rgba(6, 12, 9, 0.35);
}
.v2-hero-dates-ico {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.v2-hero-date-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.v2-hero-date-col span {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  opacity: 0.78;
}
.v2-hero-date-col b {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: 24px;
  line-height: 1;
  letter-spacing: -0.02em;
}
.v2-hero-dates-arrow {
  display: flex;
  align-items: center;
  gap: 4px;
}
.v2-hero-dates-arrow span {
  width: 22px;
  height: 2px;
  border-radius: 2px;
  background: currentColor;
}
.v2-hero-dates-tag {
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  font-size: 14px;
  font-weight: 700;
}
.on-light .v2-hero-dates-tag {
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
}
.v2-hero-btn {
  --v2-btn-h: 56px;
  padding: 14px 28px;
  font-size: 17px;
}
.v2-hero--classic {
  display: grid;
  place-items: center;
  min-height: clamp(560px, 56cqi, 760px);
}
.v2-hero-veil {
  position: absolute;
  inset: 0;
  background: rgba(6, 12, 9, 0.5);
}
.v2-hero--classic .v2-hero-inner {
  padding-top: 72px;
  padding-bottom: 72px;
}
/* O logo fica no topo, no mesmo lugar em todas as aparências de capa; o conteúdo abre espaço para ele. */
.v2-hero--classic.has-logo .v2-hero-inner {
  padding-top: calc(var(--v2-logo-h) + 72px);
}
@container (min-width: 641px) {
  .v2-hero--card.has-logo .v2-hero-inner {
    padding-top: calc(var(--v2-logo-h) + 56px);
  }
  .v2-hero--imm.has-logo .v2-hero-inner {
    padding-top: max(clamp(96px, 10cqi, 140px), calc(var(--v2-logo-h) + 64px));
  }
}
.v2-hero-split-top {
  max-width: 1240px;
  margin: 0 auto;
  padding: clamp(16px, 3cqi, 28px) clamp(16px, 5cqi, 40px) 0;
}
.v2-hero--split.has-logo .v2-hero-split {
  padding-top: clamp(16px, 3cqi, 32px);
}
.v2-hero-inner.is-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.v2-hero--split {
  background: color-mix(in srgb, var(--v2-accent) 10%, #fbfcfa);
  color: #0f1713;
}
.v2-hero-split {
  display: flex;
  flex-wrap: wrap-reverse;
  align-items: center;
  gap: clamp(24px, 5cqi, 64px);
  max-width: 1240px;
  margin: 0 auto;
  padding: clamp(16px, 4cqi, 48px) clamp(16px, 5cqi, 40px);
}
.v2-hero-split-copy {
  flex: 1 1 420px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.v2-hero-split-media {
  flex: 1 1 420px;
  min-width: 0;
}
@container (max-width: 640px) {
  .v2-hero--imm {
    min-height: 0;
  }
  .v2-hero-fade {
    background: linear-gradient(
      180deg,
      color-mix(in srgb, var(--v2-bg) 18%, transparent) 0%,
      transparent 22%,
      transparent 40%,
      color-mix(in srgb, var(--v2-bg) 78%, transparent) 70%,
      var(--v2-bg) 94%
    );
  }
  .v2-hero-spacer {
    display: block;
  }
  .v2-hero--imm .v2-hero-inner {
    padding-top: 0;
  }
  .v2-hero-title {
    font-size: max(24px, calc(clamp(30px, 9cqi, 40px) * var(--v2-title-scale, 1)));
  }
}
.v2-hero-split-media img {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 5;
  max-height: 680px;
  object-fit: cover;
  border-radius: 28px;
}
.v2-hero--card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: clamp(560px, 56cqi, 740px);
}
.v2-hero-card-spacer {
  position: relative;
  height: min(340px, max(0px, calc(900px - 100cqi)));
}
.v2-hero--card .v2-hero-inner {
  padding-top: 24px;
  padding-bottom: 40px;
}
.v2-hero-card {
  display: flex;
  flex-direction: column;
  gap: 18px;
  /* Com texto longo o cartão alarga (--v2-card-grow) em vez de ficar comprido. */
  max-width: calc(520px + var(--v2-card-grow, 0px));
  padding: clamp(24px, 4cqi, 40px);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 24px 60px -24px rgba(6, 12, 9, 0.5);
}
.v2-hero--card .v2-hero-title,
.v2-hero--split .v2-hero-title {
  font-size: max(24px, calc(clamp(32px, 4.6cqi, 60px) * var(--v2-title-scale, 1)));
}
</style>
