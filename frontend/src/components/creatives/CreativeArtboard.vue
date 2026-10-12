<template>
  <div class="cr" :class="[`cr-t-${template}`, `cr-${format}`, { 'cr-has-tapes': tapes }]" :style="rootStyle">
    <!-- Oferta em bloco: bloco da marca sobre a foto, fita com a tag e faixa de saída -->
    <template v-if="template === 'oferta'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="of-wrap">
        <span v-if="badge" class="of-ribbon">{{ badge }}</span>
        <div class="of-box">
          <h1 class="cr-title of-title" :style="headStyle(1.05)">{{ headline }}</h1>
          <p v-if="inclusions.length" class="of-dur">{{ data.duration ? `${data.duration} incluindo` : "Incluindo" }}</p>
          <p v-if="inclusions.length" class="of-inc">{{ inclusions.slice(0, format === "square" ? 3 : 5).map(item => item.label).join(" + ") }}</p>
          <CreativePrice v-if="price.has" class="of-price" :data="data" align="center" />
          <p v-if="data.disclaimer" class="cr-fine">{{ data.disclaimer }}</p>
        </div>
        <div v-if="data.departure" class="of-bar">{{ data.departure }}</div>
        <span v-if="cta" class="cr-cta of-cta">{{ cta }}</span>
      </div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip of-logo" alt="" />
    </template>

    <!-- Foto e dois blocos: destino com ícones de um lado, preço grande do outro -->
    <template v-else-if="template === 'dividido'">
      <div class="cr-photo dv-photo" :style="bg(0)"></div>
      <div v-if="badge" class="dv-ribbon"><span v-for="n in 4" :key="n">{{ badge }}</span></div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip dv-logo" alt="" />
      <div class="dv-grid">
        <div class="dv-left">
          <h1 class="cr-title" :style="headStyle(0.78)">{{ headline }}</h1>
          <p v-if="inclusions.length" class="dv-sub">{{ inclusions.slice(0, 2).map(item => item.label).join(" + ") }}</p>
          <ul class="dv-list">
            <li v-if="data.dates"><CalendarDaysIcon />{{ data.dates }}</li>
            <li v-if="data.departure"><MapPinIcon />{{ data.departure }}</li>
            <li v-for="item in inclusions.slice(2, { square: 2, feed: 3, story: 4 }[format])" :key="item.label"><component :is="item.icon" />{{ item.label }}</li>
          </ul>
        </div>
        <div class="dv-right">
          <CreativePrice v-if="price.has" :data="data" align="center" cash-label />
          <span v-if="cta" class="cr-cta dv-cta">{{ cta }}</span>
          <p v-if="data.disclaimer" class="cr-fine">{{ data.disclaimer }}</p>
        </div>
      </div>
    </template>

    <!-- Cartão claro: cartão translúcido com destino e caixa de preço na cor da marca -->
    <template v-else-if="template === 'vidro'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="vd-shade"></div>
      <div class="vd-stack">
        <div class="vd-card">
          <div class="vd-text">
            <span v-if="badge" class="cr-tag">{{ badge }}</span>
            <h1 class="cr-title vd-title" :style="headStyle(0.82)">{{ headline }}</h1>
            <p v-if="data.dates" class="vd-dates">{{ data.dates }}</p>
            <p v-if="details" class="vd-details">{{ details }}</p>
          </div>
          <img v-if="logo" :src="logo" class="cr-logo vd-logo" alt="" />
        </div>
        <div v-if="price.has" class="vd-price">
          <CreativePrice :data="data" />
          <p v-if="data.disclaimer" class="cr-fine">{{ data.disclaimer }}</p>
        </div>
        <span v-if="cta" class="cr-cta">{{ cta }}</span>
      </div>
      <p v-if="!logo && data.agencyName" class="vd-agency">{{ data.agencyName }}</p>
    </template>

    <!-- Destino em destaque: nome do destino no alto, base recortada com preço e contato -->
    <template v-else-if="template === 'destino'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="ds-box">
        <svg class="ds-path" viewBox="0 0 200 60" fill="none" aria-hidden="true">
          <path d="M8 50 C 60 10, 120 70, 186 14" stroke="currentColor" stroke-width="3" stroke-dasharray="6 8" stroke-linecap="round" />
          <path d="M178 8 l14 4 -10 10z" fill="currentColor" />
        </svg>
        <span class="ds-pre">{{ badge || "viaje para" }}</span>
        <h1 class="cr-title ds-title" :style="headStyle(0.9)">{{ headline }}</h1>
      </div>
      <div class="ds-panel">
        <div class="ds-row">
          <span v-if="data.duration || inclusions[0]" class="ds-chip">{{ data.duration || inclusions[0]?.label }}</span>
          <span v-if="data.priceSuffix" class="ds-note">*valor {{ data.priceSuffix }}</span>
        </div>
        <div v-if="price.has" class="ds-price"><CreativePrice :data="data" /></div>
        <div class="ds-foot">
          <img v-if="logo" :src="logo" class="cr-logo ds-logo" alt="" />
          <b v-else-if="data.agencyName" class="ds-agency">{{ data.agencyName }}</b>
          <div class="ds-contact">
            <span v-if="cta" class="cr-cta">{{ cta }}</span>
            <template v-else-if="data.contact">
              <small>Fale com a gente e faça sua reserva</small>
              <b><PhoneIcon />{{ data.contact }}</b>
            </template>
          </div>
        </div>
      </div>
    </template>

    <!-- Manchete: destino enorme sobre a foto, data em tag, preço em caixa e o que inclui ao lado -->
    <template v-else-if="template === 'manchete'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="mc-shade"></div>
      <div class="mc-top">
        <span v-if="badge" class="mc-label">{{ badge }}</span>
        <h1 class="cr-title mc-title" :style="headStyle(1.35)">{{ headline }}</h1>
        <span v-if="data.dates" class="mc-date"><CalendarDaysIcon />{{ data.dates }}</span>
      </div>
      <div class="mc-bottom">
        <div v-if="price.has" class="mc-price">
          <small>{{ data.priceSuffix || data.pricePrefix }}</small>
          <CreativePrice :data="data" hide-prefix />
        </div>
        <ul v-if="inclusions.length" class="mc-inc">
          <li v-for="item in inclusions.slice(0, format === 'square' ? 3 : 4)" :key="item.label">{{ item.label }}</li>
        </ul>
      </div>
      <p class="mc-foot">
        <span v-if="cta" class="cr-cta">{{ cta }}</span>
        <template v-else-if="data.contact">Chame no WhatsApp {{ data.contact }}</template>
      </p>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip mc-logo" alt="" />
    </template>

    <!-- Campanha com ícones: faixa dividida com campanha e destino, foto embaixo -->
    <template v-else-if="template === 'campanha'">
      <div class="cr-photo cp-photo" :style="bg(0)"></div>
      <div class="cp-band">
        <div class="cp-left">
          <h2 class="cp-head">{{ badge || "Oferta especial" }}</h2>
          <p v-if="data.departure || data.subtitle" class="cp-tagline">{{ data.departure || data.subtitle }}</p>
          <img v-if="logo" :src="logo" class="cr-logo cp-logo" alt="" />
        </div>
        <div class="cp-right">
          <h1 class="cr-title cp-title" :style="headStyle(0.7)">{{ headline }}</h1>
          <p v-if="data.duration" class="cp-dur">{{ data.duration }} incluindo:</p>
          <div v-if="inclusions.length" class="cp-icons">
            <component :is="item.icon" v-for="item in inclusions.slice(0, 5)" :key="item.label" />
          </div>
          <CreativePrice v-if="price.has" :data="data" />
          <p v-if="data.disclaimer" class="cr-fine">{{ data.disclaimer }}</p>
          <span v-if="cta" class="cr-cta cp-cta">{{ cta }}</span>
        </div>
      </div>
    </template>

    <!-- Preço em destaque: valor bem grande e a foto num círculo -->
    <template v-else-if="template === 'price-hero'">
      <div class="cr-photo ph-photo" :style="bg(0)"></div>
      <div class="ph-body">
        <img v-if="logo" :src="logo" class="cr-logo ph-logo" alt="" />
        <span v-if="badge" class="cr-tag">{{ badge }}</span>
        <span class="cr-eyebrow">{{ data.title }}</span>
        <CreativePrice v-if="price.has" class="ph-price" :data="data" />
        <h1 v-else class="cr-title" :style="titleStyle(1)">{{ data.title }}</h1>
        <span v-if="data.dates || data.departure" class="cr-pill">{{ [data.dates, data.departure].filter(Boolean).join(" · ") }}</span>
        <span v-if="cta" class="cr-cta cr-cta-gap">{{ cta }}</span>
      </div>
    </template>

    <!-- Black Friday economia: preto e amarelo, destino enorme, De/Por, economia e selo estourado -->
    <template v-else-if="template === 'black-economia'">
      <CreativeTapes :text="tapeLabel" variant="yellow" />
      <div class="be-wrap">
      <div class="be-top">
        <p v-if="fromCity" class="be-from">De {{ fromCity }} para</p>
        <h1 class="cr-title be-title" :style="headStyle(1.25)">{{ headline }}</h1>
        <p v-if="data.dates" class="be-date"><CalendarDaysIcon />{{ data.dates }}</p>
        <div v-if="price.has" class="be-price">
          <div v-if="data.oldPrice" class="be-was"><s>De {{ data.oldPrice }}</s><span>por apenas</span></div>
          <b>{{ price.total }}</b>
        </div>
        <p v-if="saving" class="be-save">Economize {{ saving }}</p>
        <p v-if="price.installmentText" class="be-inst">{{ price.installmentText }} sem juros</p>
        <span v-if="cta" class="cr-cta be-cta">{{ cta }}</span>
      </div>
      <div class="cr-photo be-photo" :style="bg(0)">
        <div v-if="saving || badge" class="be-burst">
          <small v-if="saving">Economize</small>
          <b>{{ saving || badge }}</b>
          <small v-if="saving && badge">{{ badge }}</small>
        </div>
      </div>
      </div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip be-logo" alt="" />
      <CreativeTapes :text="tapeLabel" variant="yellow" position="bottom" />
    </template>

    <!-- Black Friday faixa: foto com fitas, faixa amarela com o destino, cartão do pacote e preço -->
    <template v-else-if="template === 'black-faixa'">
      <div class="cr-photo bf-photo" :style="bg(0)"></div>
      <CreativeTapes :text="tapeLabel" variant="yellow" />
      <div class="bf-stack">
      <div class="bf-band">
        <span v-if="badge" class="bf-badge">{{ badge }}</span>
        <h1 class="cr-title bf-title" :style="headStyle(1.05)">{{ headline }}</h1>
      </div>
      <div class="bf-card">
        <div class="bf-cols">
          <div class="bf-inc">
            <span class="bf-tag">Pacote inclui:</span>
            <ul>
              <li v-for="item in inclusions.slice(0, format === 'square' ? 3 : 5)" :key="item.label">{{ item.label }}</li>
            </ul>
          </div>
          <div class="bf-side">
            <span v-if="data.departure" class="bf-pill"><MapPinIcon />{{ data.departure }}</span>
            <span v-if="data.dates" class="bf-dates">{{ data.dates }}</span>
            <b v-if="data.duration" class="bf-dur">{{ data.duration }}</b>
          </div>
        </div>
        <div v-if="price.has" class="bf-price">
          <CreativePrice :data="data" />
        </div>
        <p v-if="data.disclaimer" class="cr-fine bf-fine">{{ data.disclaimer }}</p>
      </div>
      </div>
      <div class="bf-foot">
        <img v-if="logo" :src="logo" class="cr-logo bf-logo" alt="" />
        <b v-else-if="data.agencyName">{{ data.agencyName }}</b>
        <span v-if="cta" class="cr-cta">{{ cta }}</span>
      </div>
    </template>

    <!-- Lista do que inclui -->
    <template v-else-if="template === 'benefits'">
      <div class="cr-photo bn-photo" :style="bg(0)">
        <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip bn-logo" alt="" />
      </div>
      <div class="bn-body">
        <span v-if="data.dates" class="cr-eyebrow">{{ data.dates }}</span>
        <h1 class="cr-title" :style="titleStyle(0.9)">{{ data.title }}</h1>
        <ul v-if="inclusions.length" class="cr-checks">
          <li v-for="item in inclusions.slice(0, maxList)" :key="item.label"><i><component :is="item.icon" /></i>{{ item.label }}</li>
        </ul>
        <div class="cr-foot">
          <CreativePrice v-if="price.has" :data="data" />
          <div v-if="cta || data.contact" class="cr-side">
            <span v-if="cta" class="cr-cta">{{ cta }}</span>
            <span v-if="data.contact" class="cr-contact">WhatsApp {{ data.contact }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Cartão com tudo -->
    <template v-else-if="template === 'card'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="cd-shade"></div>
      <div class="cd-card">
        <div class="cd-head">
          <img v-if="logo" :src="logo" class="cr-logo cd-logo" alt="" />
          <span v-if="badge" class="cr-tag">{{ badge }}</span>
        </div>
        <span v-if="data.dates" class="cr-pill cd-pill">{{ data.dates }}</span>
        <h1 class="cr-title cd-title" :style="titleStyle(0.85)">{{ data.title }}</h1>
        <ul v-if="inclusions.length" class="cr-checks cd-checks">
          <li v-for="item in inclusions.slice(0, format === 'square' ? 3 : 5)" :key="item.label"><i><component :is="item.icon" /></i>{{ item.label }}</li>
        </ul>
        <div class="cr-foot">
          <CreativePrice v-if="price.has" class="cd-price" :data="data" />
          <div v-if="cta || data.contact" class="cr-side">
            <span v-if="cta" class="cr-cta">{{ cta }}</span>
            <span v-if="data.contact" class="cr-contact cd-contact">WhatsApp {{ data.contact }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Colagem de 2 fotos -->
    <template v-else-if="template === 'collage-2'">
      <div class="cl-grid">
        <div class="cr-photo" :style="bg(0)"></div>
        <div class="cr-photo" :style="bg(1)"></div>
      </div>
      <div class="cl-band">
        <img v-if="logo" :src="logo" class="cr-logo cl-logo" alt="" />
        <h1 class="cr-title" :style="titleStyle(0.9)">{{ data.title }}</h1>
        <div class="cl-row">
          <span v-if="data.dates" class="cr-pill">{{ data.dates }}</span>
          <CreativePrice v-if="price.has" :data="data" align="right" />
        </div>
        <span v-if="cta" class="cr-cta cr-cta-gap">{{ cta }}</span>
      </div>
      <div v-if="badge" class="cr-corner">{{ badge }}</div>
    </template>

    <!-- Mosaico de 3 fotos -->
    <template v-else-if="template === 'mosaic-3'">
      <div class="ms-grid">
        <div class="cr-photo ms-big" :style="bg(0)"></div>
        <div class="cr-photo" :style="bg(1)"></div>
        <div class="cr-photo" :style="bg(2)"></div>
      </div>
      <div class="ms-body">
        <div class="ms-text">
          <span v-if="data.dates" class="cr-eyebrow">{{ data.dates }}</span>
          <h1 class="cr-title" :style="titleStyle(0.85)">{{ data.title }}</h1>
          <p v-if="inclusions.length && format !== 'square'" class="cr-small">{{ inclusions.slice(0, 4).map(item => item.label).join(" · ") }}</p>
        </div>
        <div v-if="price.has" class="ms-price"><CreativePrice :data="data" /></div>
      </div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip ms-logo" alt="" />
      <div v-if="badge" class="cr-corner">{{ badge }}</div>
    </template>

    <CreativeTapes v-if="tapes && !isBlack" :text="tapeLabel" />
  </div>
</template>

<script setup lang="ts">
/**
 * Um criativo em tamanho real (1080 px de largura). A tela mostra reduzido com transform e o
 * download (html-to-image) usa este mesmo elemento, então o que se vê é o que se baixa.
 */
import { computed } from "vue";
import { CalendarDaysIcon, MapPinIcon, PhoneIcon } from "lucide-vue-next";
import { BLACK_TEMPLATES } from "./creativeTemplates";
import { CAMPAIGNS, FORMAT_SIZES, effectiveColors, formatMoney, parseMoney, priceParts, readableOn, tapeText, type CreativeData, type CreativeFormat } from "./creativeData";
import { inclusionIcon } from "./creativeIcons";
import CreativePrice from "./CreativePrice.vue";
import CreativeTapes from "./CreativeTapes.vue";

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
const cta = computed(() => (props.data.ctaEnabled ? props.data.cta.trim() : ""));
const price = computed(() => priceParts(props.data));
const isBlack = computed(() => BLACK_TEMPLATES.has(props.template));
const tapes = computed(() => props.data.tapes || isBlack.value);
// "Saída de Goiânia" → "Goiânia" (para "De Goiânia para").
const fromCity = computed(() => props.data.departure.replace(/^sa[ií](da|ndo) (de|do|da)\s+/i, "").trim());
const saving = computed(() => {
  const diff = parseMoney(props.data.oldPrice) - parseMoney(props.data.priceValue);
  return diff > 0 ? formatMoney(diff) : "";
});
const tapeLabel = computed(() => tapeText(props.data));
const badge = computed(() => (props.data.badge || (props.data.campaign ? CAMPAIGNS[props.data.campaign].badge : "")).trim());
const inclusions = computed(() => props.data.benefits.filter(Boolean).map(label => ({ label, icon: inclusionIcon(label) })));
const maxList = computed(() => ({ square: 3, feed: 4, story: 7 })[props.format]);
const details = computed(() => props.data.subtitle || inclusions.value.slice(0, 4).map(item => item.label).join(", "));

const rootStyle = computed(() => {
  // Modelos de Black Friday: sempre preto e amarelo.
  const colors = isBlack.value ? { primary: CAMPAIGNS.black_friday.primary, secondary: CAMPAIGNS.black_friday.secondary } : effectiveColors(props.data);
  const onAccent = readableOn(colors.secondary);
  return {
    width: `${size.value.width}px`,
    height: `${size.value.height}px`,
    "--c1": colors.primary,
    "--c2": colors.secondary,
    "--on1": readableOn(colors.primary),
    "--on2": onAccent,
    // Título sobre a cor de destaque: a cor da marca quando o destaque é claro.
    "--ink2": onAccent === "#111827" ? colors.primary : "#ffffff",
    // Com as fitas, o que fica no topo desce para não ficar coberto.
    "--top-gap": tapes.value && !isBlack.value ? "190px" : "0px"
  };
});

// Título encolhe com o tamanho do texto, para nunca estourar.
const headline = computed(() => (props.data.destination || props.data.title).trim());
const titleStyle = (scale: number, value = props.data.title) => {
  const length = value.length;
  const base = props.format === "square" ? 0.86 : 1;
  const px = length > 60 ? 64 : length > 42 ? 76 : length > 26 ? 92 : length > 14 ? 108 : 124;
  return { fontSize: `${Math.round(px * base * scale)}px` };
};
const headStyle = (scale: number) => titleStyle(scale, headline.value);
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
.cr :deep(svg) {
  flex: none;
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
.cr-title {
  margin: 0;
  font-family: Sora, Inter, sans-serif;
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: -0.02em;
}
.cr-eyebrow {
  display: block;
  margin-bottom: 18px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.85;
}
.cr-small {
  margin: 16px 0 0;
  font-size: 28px;
  opacity: 0.9;
}
.cr-fine {
  margin: 18px 0 0;
  font-size: 20px;
  line-height: 1.35;
  opacity: 0.78;
}
/* Datas: etiqueta com filete na cor de destaque. */
.cr-pill {
  display: inline-block;
  padding: 4px 0 4px 20px;
  border-left: 8px solid var(--c2);
  font-size: 30px;
  font-weight: 700;
}
/* Tag (Oferta, Últimos lugares): etiqueta retangular, não botão. */
.cr-tag {
  display: inline-block;
  align-self: flex-start;
  margin-bottom: 18px;
  padding: 8px 18px;
  border-radius: 8px;
  background: var(--c2);
  color: var(--on2);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
/* Fita diagonal no canto. */
.cr-corner {
  position: absolute;
  top: calc(var(--top-gap) + 56px);
  right: -96px;
  z-index: 4;
  width: 420px;
  padding: 14px 0;
  background: var(--c2);
  color: var(--on2);
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-align: center;
  text-transform: uppercase;
  transform: rotate(35deg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}
.cr-logo {
  position: relative;
  z-index: 3;
  display: block;
  max-width: 280px;
  max-height: 110px;
  object-fit: contain;
}
.cr-logo-chip {
  padding: 14px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}
/* O único "botão" da arte: só quando a chamada está ligada. */
.cr-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
  padding: 24px 44px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 34px;
  font-weight: 800;
  white-space: nowrap;
}
.cr-cta-gap {
  margin-top: 30px;
}
.cr-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 14px;
}
.cr-side .cr-cta {
  align-self: flex-end;
}
.cr-contact {
  font-size: 28px;
  font-weight: 700;
  opacity: 0.9;
}
.cr-foot {
  display: flex;
  flex: none;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-top: auto;
  padding-top: 28px;
  --pz-size: 120px;
  --pz-accent: var(--c2);
}
/* Lista com ícones; o que não cabe inteiro vai para fora da arte (nunca aparece cortado). */
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
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--c2);
  color: var(--on2);
}
.cr-checks i :deep(svg) {
  width: 30px;
  height: 30px;
}

/* ---------- Oferta em bloco ---------- */
.of-wrap {
  position: absolute;
  top: calc(var(--top-gap) + 70px);
  right: 64px;
  left: 64px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.cr-story .of-wrap {
  top: calc(var(--top-gap) + 150px);
}
.cr-square .of-wrap {
  top: calc(var(--top-gap) + 44px);
}
.of-ribbon {
  position: relative;
  z-index: 2;
  margin-bottom: -34px;
  padding: 16px 44px;
  border-radius: 18px;
  background: var(--c2);
  color: var(--on2);
  font-size: 34px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  transform: rotate(-2deg);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}
.of-box {
  width: 100%;
  padding: 72px 56px 70px;
  border-radius: 44px;
  background: var(--c1);
  color: var(--on1);
  text-align: center;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.3);
  --pz-size: 150px;
  --pz-accent: var(--c2);
}
.cr-square .of-box {
  padding: 60px 48px 56px;
  --pz-size: 110px;
}
.of-title {
  text-transform: uppercase;
}
.of-dur {
  margin: 14px 0 6px;
  font-size: 34px;
  font-weight: 600;
}
.of-inc {
  margin: 0 auto;
  max-width: 860px;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.3;
}
.of-price {
  margin-top: 30px;
}
.of-bar {
  margin-top: -30px;
  padding: 22px 56px;
  border-radius: 18px;
  background: var(--c2);
  color: var(--on2);
  font-size: 36px;
  font-weight: 800;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}
.of-cta {
  align-self: center;
  margin-top: 30px;
}
.of-logo {
  position: absolute;
  right: 56px;
  bottom: 56px;
}

/* ---------- Foto e dois blocos ---------- */
.dv-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: 54%;
}
.cr-square .dv-photo {
  height: 48%;
}
.cr-story .dv-photo {
  height: 56%;
}
.dv-ribbon {
  position: absolute;
  top: calc(var(--top-gap) + 70px);
  left: -150px;
  z-index: 3;
  display: flex;
  gap: 18px;
  width: 640px;
  padding: 14px 0;
  overflow: hidden;
  background: var(--c2);
  color: var(--on2);
  font-size: 28px;
  font-weight: 800;
  text-transform: uppercase;
  white-space: nowrap;
  transform: rotate(-35deg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}
.dv-logo {
  position: absolute;
  top: calc(var(--top-gap) + 48px);
  right: 48px;
}
.dv-grid {
  position: absolute;
  inset: 54% 0 0 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
}
.cr-square .dv-grid {
  inset: 48% 0 0 0;
}
.cr-story .dv-grid {
  inset: 56% 0 0 0;
}
.dv-left {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 50px 40px 50px 64px;
  background: var(--c2);
  color: var(--ink2);
}
.dv-sub {
  margin: 10px 0 0;
  font-size: 34px;
  font-weight: 600;
}
.dv-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin: 34px 0 0;
  padding: 0;
  list-style: none;
  font-size: 30px;
  font-weight: 700;
}
.dv-list li {
  display: flex;
  align-items: center;
  gap: 18px;
}
.dv-list :deep(svg) {
  width: 44px;
  height: 44px;
}
.dv-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: var(--c1);
  color: var(--on1);
  text-align: center;
  --pz-size: 170px;
  --pz-accent: var(--c2);
}
.cr-square .dv-right {
  --pz-size: 130px;
}
.dv-cta {
  align-self: center;
  margin-top: 28px;
}

/* ---------- Cartão claro ---------- */
.vd-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0) 45%, rgba(0, 0, 0, 0.35));
}
.vd-stack {
  position: absolute;
  top: calc(var(--top-gap) + 64px);
  right: 56px;
  left: 56px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 26px;
}
.cr-story .vd-stack {
  top: calc(var(--top-gap) + 140px);
}
.vd-card {
  display: flex;
  align-items: center;
  gap: 32px;
  width: 100%;
  padding: 52px 50px;
  border-radius: 36px;
  background: rgba(255, 255, 255, 0.93);
  color: #111827;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.18);
}
.vd-text {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
}
.vd-title {
  color: var(--c1);
  text-transform: uppercase;
}
.vd-dates {
  margin: 16px 0 0;
  color: var(--c1);
  font-size: 40px;
  font-weight: 700;
}
.vd-details {
  margin: 14px 0 0;
  color: #374151;
  font-size: 28px;
  line-height: 1.35;
}
.vd-logo {
  max-width: 220px;
  max-height: 140px;
}
.vd-price {
  max-width: 72%;
  padding: 36px 44px;
  border-radius: 28px;
  background: var(--c1);
  color: var(--on1);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
  --pz-size: 130px;
}
.cr-square .vd-price {
  --pz-size: 100px;
  padding: 28px 36px;
}
.vd-agency {
  position: absolute;
  right: 56px;
  bottom: 48px;
  margin: 0;
  color: #fff;
  font-family: Sora, Inter, sans-serif;
  font-size: 54px;
  font-weight: 800;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

/* ---------- Destino em destaque ---------- */
.ds-box {
  position: absolute;
  top: var(--top-gap);
  left: 64px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  max-width: 640px;
  padding: 60px 52px 50px;
  border-radius: 0 0 40px 40px;
  background: var(--c1);
  color: var(--on1);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
}
.ds-path {
  width: 220px;
  margin-bottom: 18px;
  color: var(--c2);
}
.ds-pre {
  font-size: 34px;
  font-weight: 600;
}
.ds-title {
  margin-top: 6px;
  color: var(--c2);
  text-transform: uppercase;
}
.ds-panel {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 26px;
  padding: 170px 64px 64px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--c1) 92%, #fff) 0%, var(--c1) 70%);
  clip-path: polygon(0 90px, 50% 0, 100% 90px, 100% 100%, 0 100%);
  color: var(--on1);
}
.cr-square .ds-panel {
  gap: 18px;
  padding-top: 130px;
}
.ds-row {
  display: flex;
  align-items: center;
  gap: 20px;
}
.ds-chip {
  padding: 14px 30px;
  border-radius: 16px;
  background: #fff;
  color: var(--c1);
  font-size: 34px;
  font-weight: 800;
}
.ds-note {
  font-size: 26px;
  font-style: italic;
  opacity: 0.9;
}
.ds-price {
  align-self: flex-start;
  padding: 28px 40px;
  border-radius: 28px;
  background: var(--c2);
  color: var(--on2);
  --pz-size: 120px;
}
.cr-square .ds-price {
  --pz-size: 90px;
  padding: 20px 32px;
}
.ds-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
.ds-logo {
  max-height: 90px;
}
.ds-agency {
  font-size: 36px;
}
.ds-contact {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}
.ds-contact small {
  font-size: 24px;
  opacity: 0.9;
}
.ds-contact b {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 40px;
}
.ds-contact :deep(svg) {
  width: 36px;
  height: 36px;
  color: var(--c2);
}

/* ---------- Manchete ---------- */
.mc-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.05) 45%, rgba(0, 0, 0, 0.55));
}
.mc-top {
  position: absolute;
  top: calc(var(--top-gap) + 90px);
  right: 64px;
  left: 64px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.cr-square .mc-top {
  top: calc(var(--top-gap) + 56px);
}
.cr-story .mc-top {
  top: calc(var(--top-gap) + 180px);
}
.mc-label {
  padding: 16px 40px;
  border-radius: 20px;
  background: var(--c2);
  color: var(--on2);
  font-family: Sora, Inter, sans-serif;
  font-size: 40px;
  font-weight: 800;
  text-transform: uppercase;
}
.mc-title {
  margin-top: 26px;
  color: #fff;
  line-height: 0.92;
  letter-spacing: -0.04em;
  text-transform: uppercase;
  text-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
}
.mc-date {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  margin-top: 26px;
  padding: 14px 30px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 34px;
  font-weight: 800;
  text-transform: uppercase;
  transform: rotate(-3deg);
}
.mc-date :deep(svg) {
  width: 38px;
  height: 38px;
}
.mc-bottom {
  position: absolute;
  right: 64px;
  bottom: 150px;
  left: 64px;
  z-index: 2;
  display: flex;
  align-items: center;
}
.cr-story .mc-bottom {
  bottom: 220px;
}
.mc-price {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 32px 40px;
  border-radius: 30px;
  background: var(--c2);
  color: var(--on2);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  --pz-size: 140px;
}
.cr-square .mc-price {
  --pz-size: 100px;
}
.mc-price > small {
  font-size: 28px;
  font-weight: 800;
  text-transform: uppercase;
}
.mc-inc {
  flex: 1;
  margin: 0 0 0 -30px;
  padding: 34px 34px 34px 70px;
  border-radius: 0 30px 30px 0;
  background: #fff;
  color: #111827;
  font-size: 27px;
  font-weight: 600;
  line-height: 1.35;
  list-style: disc;
  list-style-position: inside;
}
.mc-foot {
  position: absolute;
  right: 64px;
  bottom: 60px;
  left: 64px;
  z-index: 2;
  display: flex;
  justify-content: center;
  margin: 0;
  color: #fff;
  font-size: 32px;
  font-weight: 800;
  text-align: center;
  text-transform: uppercase;
}
.cr-story .mc-foot {
  bottom: 110px;
}
.mc-foot .cr-cta {
  align-self: center;
}
.mc-logo {
  position: absolute;
  top: calc(var(--top-gap) + 40px);
  left: 48px;
  max-height: 90px;
}
.cr-has-tapes .mc-logo {
  display: none;
}

/* ---------- Campanha com ícones ---------- */
.cp-photo {
  position: absolute;
  inset: 0;
}
.cp-band {
  position: absolute;
  top: var(--top-gap);
  right: 0;
  left: 0;
  display: grid;
  grid-template-columns: 0.85fr 1.15fr;
  min-height: 52%;
}
.cr-square .cp-band {
  min-height: 58%;
}
.cr-story .cp-band {
  min-height: 44%;
}
.cp-left {
  display: flex;
  flex-direction: column;
  padding: 64px 40px 50px 56px;
  background: var(--c1);
  color: var(--on1);
}
.cp-head {
  margin: 0;
  font-family: Sora, Inter, sans-serif;
  font-size: 70px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
  text-transform: uppercase;
}
.cp-tagline {
  margin: 18px 0 0;
  font-size: 28px;
  font-weight: 700;
  text-transform: uppercase;
  opacity: 0.92;
}
.cp-logo {
  margin-top: auto;
  max-height: 100px;
  padding: 12px 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.94);
}
.cp-right {
  display: flex;
  flex-direction: column;
  padding: 56px 56px 50px 50px;
  background: var(--c2);
  color: var(--ink2);
  --pz-size: 120px;
}
.cr-square .cp-right {
  --pz-size: 92px;
}
.cp-title {
  text-transform: uppercase;
}
.cp-dur {
  margin: 10px 0 0;
  font-size: 34px;
  font-weight: 800;
}
.cp-icons {
  display: flex;
  gap: 22px;
  margin: 22px 0 28px;
}
.cp-icons :deep(svg) {
  width: 60px;
  height: 60px;
}
.cp-cta {
  margin-top: 24px;
  background: var(--c1);
  color: var(--on1);
}

/* ---------- Preço em destaque ---------- */
.ph-photo {
  position: absolute;
  top: -10%;
  right: -18%;
  width: 96%;
  aspect-ratio: 1;
  border: 22px solid var(--c2);
  border-radius: 50%;
}
.cr-story .ph-photo {
  top: -6%;
  right: -24%;
  width: 118%;
}
.cr-square .ph-photo {
  top: -18%;
  right: -16%;
  width: 72%;
}
.ph-body {
  position: absolute;
  inset: auto 72px 80px 72px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  --pz-size: 190px;
  --pz-accent: var(--c2);
}
.cr-square .ph-body {
  --pz-size: 150px;
}
.ph-logo {
  max-height: 96px;
  margin-bottom: 28px;
}
.ph-price {
  margin: 10px 0 36px;
}

/* ---------- Lista do que inclui ---------- */
.bn-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: 38%;
}
.cr-square .bn-photo {
  height: 34%;
}
.bn-logo {
  position: absolute;
  top: calc(var(--top-gap) + 48px);
  left: 56px;
}
.bn-body {
  position: absolute;
  inset: 38% 0 0 0;
  display: flex;
  flex-direction: column;
  padding: 56px 72px 64px;
}
.cr-square .bn-body {
  inset: 34% 0 0 0;
  padding-top: 44px;
}

/* ---------- Cartão com tudo ---------- */
.cd-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0.1) 40%, rgba(0, 0, 0, 0.45));
}
.cd-card {
  position: absolute;
  right: 56px;
  bottom: 56px;
  left: 56px;
  display: flex;
  flex-direction: column;
  max-height: calc(100% - 112px - var(--top-gap));
  padding: 52px 56px;
  border-radius: 44px;
  background: #fff;
  color: #111827;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.3);
}
.cd-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.cd-head .cr-tag {
  margin-bottom: 0;
}
.cd-logo {
  max-height: 84px;
  max-width: 260px;
}
.cd-pill {
  align-self: flex-start;
  margin: 24px 0 18px;
}
.cd-title {
  color: #111827;
}
.cd-checks {
  color: #1f2937;
}
.cd-price {
  --pz-accent: var(--c1);
}
.cd-contact {
  color: #374151;
}

/* ---------- Colagem de 2 ---------- */
.cl-grid {
  position: absolute;
  inset: 0 0 auto 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  height: 58%;
  background: #fff;
}
.cr-story .cl-grid {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr 1fr;
  height: 62%;
}
.cl-band {
  position: absolute;
  inset: auto 0 0 0;
  min-height: 42%;
  padding: 56px 72px 64px;
  --pz-size: 110px;
  --pz-accent: var(--c2);
}
.cr-story .cl-band {
  min-height: 38%;
}
.cl-logo {
  max-height: 90px;
  margin-bottom: 24px;
}
.cl-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-top: 28px;
}

/* ---------- Mosaico de 3 ---------- */
.ms-grid {
  position: absolute;
  inset: 0 0 auto 0;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 12px;
  height: 60%;
  background: #fff;
}
.ms-big {
  grid-row: span 2;
}
.cr-story .ms-grid {
  height: 64%;
}
.ms-body {
  position: absolute;
  inset: auto 0 0 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 30px;
  min-height: 40%;
  padding: 52px 64px 60px;
}
.ms-text {
  flex: 1;
  min-width: 0;
}
.ms-price {
  flex: none;
  padding: 26px 32px;
  border-radius: 28px;
  background: var(--c2);
  color: var(--on2);
  --pz-size: 96px;
}
.ms-logo {
  position: absolute;
  top: calc(var(--top-gap) + 40px);
  left: 40px;
  max-height: 90px;
}

/* ---------- Black Friday economia ---------- */
.be-wrap {
  position: absolute;
  inset: 200px 56px 130px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 34px;
}
.cr-story .be-wrap {
  inset: 290px 56px 200px;
}
.cr-square .be-wrap {
  inset: 210px 56px 170px;
}
.cr-square .be-title {
  font-size: 84px !important;
}
.be-top {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #fff;
  text-align: center;
}
.be-from {
  margin: 0;
  font-family: Sora, Inter, sans-serif;
  font-size: 46px;
  font-weight: 800;
  text-transform: uppercase;
}
.be-title {
  color: var(--c2);
  line-height: 0.95;
  letter-spacing: -0.03em;
  text-transform: uppercase;
}
.be-date {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 14px 0 0;
  font-size: 40px;
  font-weight: 700;
  text-transform: uppercase;
}
.be-date :deep(svg) {
  width: 44px;
  height: 44px;
}
.be-price {
  display: flex;
  align-items: center;
  gap: 30px;
  margin-top: 30px;
}
.be-was {
  display: flex;
  flex-direction: column;
  font-size: 34px;
  font-weight: 600;
  line-height: 1.15;
  text-transform: uppercase;
}
.be-was s {
  text-decoration-color: var(--c2);
  text-decoration-thickness: 4px;
}
.be-price b {
  font-family: Sora, Inter, sans-serif;
  font-size: 128px;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
}
.cr-square .be-price b {
  font-size: 100px;
}
.be-save {
  margin: 18px 0 0;
  color: var(--c2);
  font-family: Sora, Inter, sans-serif;
  font-size: 62px;
  font-weight: 800;
  text-transform: uppercase;
}
.be-inst {
  margin: 4px 0 0;
  font-family: Sora, Inter, sans-serif;
  font-size: 50px;
  font-weight: 800;
  text-transform: uppercase;
}
.cr-square .be-save,
.cr-square .be-inst {
  font-size: 42px;
}
.be-cta {
  align-self: center;
  margin-top: 26px;
}
.be-photo {
  position: relative;
  flex: 1 1 auto;
  min-height: 160px;
  border-radius: 48px;
}
.cr-square .be-photo {
  display: none;
}
/* Selo estourado (estrela de 16 pontas). */
.be-burst {
  position: absolute;
  top: -110px;
  right: -20px;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 300px;
  height: 300px;
  background: var(--c2);
  color: #0b0b0b;
  clip-path: polygon(50% 0%, 59% 9%, 69% 3%, 74% 14%, 85% 12%, 86% 24%, 97% 27%, 93% 38%, 100% 50%, 93% 62%, 97% 73%, 86% 76%, 85% 88%, 74% 86%, 69% 97%, 59% 91%, 50% 100%, 41% 91%, 31% 97%, 26% 86%, 15% 88%, 14% 76%, 3% 73%, 7% 62%, 0% 50%, 7% 38%, 3% 27%, 14% 24%, 15% 12%, 26% 14%, 31% 3%, 41% 9%);
  text-align: center;
  transform: rotate(-12deg);
}

.be-burst small {
  font-size: 24px;
  font-weight: 800;
  text-transform: uppercase;
}
.be-burst b {
  max-width: 220px;
  font-family: Sora, Inter, sans-serif;
  font-size: 50px;
  font-weight: 800;
  line-height: 1;
}
.be-logo {
  position: absolute;
  left: 80px;
  bottom: 160px;
  z-index: 3;
  max-height: 80px;
}
.cr-square .be-logo {
  display: none;
}

/* ---------- Black Friday faixa ---------- */
.bf-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: 46%;
}
.cr-square .bf-photo {
  height: 40%;
}
.bf-stack {
  position: absolute;
  top: 44%;
  right: 0;
  left: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
}
.cr-square .bf-stack {
  top: 38%;
}
.bf-band {
  position: relative;
  padding: 26px 56px 22px;
  background: var(--c2);
  color: #0b0b0b;
}
.bf-badge {
  position: absolute;
  top: -44px;
  left: 56px;
  padding: 10px 20px;
  background: #dc2626;
  color: #fff;
  font-size: 26px;
  font-weight: 800;
  text-transform: uppercase;
}
.bf-title {
  color: #0b0b0b;
}
.bf-card {
  display: flex;
  margin: 0 56px;
  flex-direction: column;
  padding: 44px 44px 36px;
  border-radius: 0 0 30px 30px;
  background: #fff;
  color: #111827;
}
.cr-square .bf-card {
  padding: 30px 36px 26px;
}
.bf-cols {
  display: flex;
  justify-content: space-between;
  gap: 24px;
}
.bf-inc ul {
  margin: 18px 0 0;
  padding-left: 30px;
  font-size: 28px;
  line-height: 1.45;
}
.bf-tag {
  display: inline-block;
  padding: 10px 26px;
  border-radius: 0 18px 18px 0;
  background: var(--c2);
  color: #0b0b0b;
  font-size: 28px;
  font-style: italic;
  font-weight: 800;
}
.bf-side {
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: flex-end;
  gap: 14px;
}
.bf-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 22px;
  border-radius: 999px;
  background: #0b0b0b;
  color: #fff;
  font-size: 24px;
  font-weight: 700;
}
.bf-pill :deep(svg) {
  width: 28px;
  height: 28px;
  color: var(--c2);
}
.bf-dates {
  padding: 8px 18px;
  background: var(--c2);
  color: #0b0b0b;
  font-size: 26px;
  font-weight: 700;
}
.bf-dur {
  color: #dc2626;
  font-size: 28px;
}
.bf-price {
  align-self: flex-end;
  margin-top: 26px;
  padding: 28px 40px;
  border-radius: 28px;
  background: #0b0b0b;
  color: #fff;
  --pz-size: 110px;
  --pz-accent: #fff;
}
.cr-square .bf-price {
  margin-top: 16px;
  --pz-size: 76px;
}
.bf-fine {
  align-self: flex-end;
}
.bf-foot {
  position: absolute;
  right: 56px;
  bottom: 56px;
  left: 56px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 30px;
  color: var(--c2);
  font-size: 40px;
}
.cr-square .bf-foot {
  display: none;
}
.bf-logo {
  max-height: 100px;
}
</style>
