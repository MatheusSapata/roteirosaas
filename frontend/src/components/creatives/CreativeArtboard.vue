<template>
  <div class="cr" :class="[`cr-t-${template}`, `cr-${format}`, { 'cr-has-tapes': tapes && !isBlack }]" :style="rootStyle">
    <!-- 1. Oferta em bloco (CVC Porto Seguro): fita, bloco da marca com destino, incluso e preço, faixa de saída -->
    <template v-if="template === 'oferta'">
      <div class="cr-photo of-photo" :style="bg(0)"></div>
      <div class="of-area">
        <div class="of-card">
          <FitText v-if="badge" class="of-ribbon" :max="38" :min="18" line><MegaphoneIcon />{{ badge }}</FitText>
          <FitText class="of-title" :max="230" :min="60" fill>{{ headline }}</FitText>
          <FitText v-if="inclusions.length" class="of-dur" :max="42" :min="20" line>{{ data.duration ? `${data.duration} incluindo` : "Pacote incluindo" }}</FitText>
          <FitText v-if="inclusions.length" class="of-inc" :max="36" :min="18" :lines="format === 'square' ? 2 : 3" :line-height="1.18">{{ inclusionLine(3) }}</FitText>
          <FitText v-if="price.has" class="of-price" :max="128" :min="56" fill><CreativePrice :data="data" variant="side" align="center" /></FitText>
          <FitText v-if="data.disclaimer && format !== 'square'" class="cr-fine of-fine" :max="21" :min="14" :lines="2" :line-height="1.3">{{ data.disclaimer }}</FitText>
          <span v-if="discount" class="of-stamp"><small>até</small><b>{{ discount }}</b><small>off</small></span>
        </div>
        <FitText v-if="data.departure" class="of-bar" :max="44" :min="20" line><PlaneTakeoffIcon />{{ data.departure }}</FitText>
        <span v-if="cta" class="cr-cta of-cta">{{ cta }}</span>
      </div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip cr-logo-br" alt="" />
    </template>

    <!-- 2. Foto e dois blocos (Porto de Galinhas): foto em cima; destino com ícones à esquerda, preço à direita -->
    <template v-else-if="template === 'dividido'">
      <div class="cr-photo dv-photo" :style="bg(0)"></div>
      <div v-if="ribbon" class="cr-corner cr-corner-left">{{ badge }}</div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip dv-logo" alt="" />
      <div class="dv-grid">
        <div class="dv-left">
          <FitText class="dv-title" :max="180" :min="48" fill>{{ headline }}</FitText>
          <FitText v-if="subLine" class="dv-sub" :max="44" :min="20" :lines="2" :line-height="1.15">{{ subLine }}</FitText>
          <FitText v-if="facts.length" class="dv-facts" :max="40" :min="18" fill>
            <ul>
              <li v-for="item in facts.slice(0, format === 'square' ? 2 : 3)" :key="item.label"><component :is="item.icon" /><span>{{ item.label }}</span></li>
            </ul>
          </FitText>
        </div>
        <div class="dv-right">
          <FitText v-if="price.has" class="dv-price" :max="140" :min="56" fill><CreativePrice :data="data" variant="stack" align="center" cash-label /></FitText>
          <span v-if="cta" class="cr-cta dv-cta">{{ cta }}</span>
        </div>
      </div>
    </template>

    <!-- 3. Cartão claro (Azul Viagens): cartão translúcido com destino e datas, caixa de preço da marca -->
    <template v-else-if="template === 'vidro'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="cr-scrim-top"></div>
      <div class="vd-area">
        <div class="vd-card">
          <div class="vd-text">
            <FitText class="vd-title" :max="170" :min="48" :lines="3" :line-height="0.95">{{ headline }}</FitText>
            <FitText v-if="data.dates" class="vd-dates" :max="54" :min="22" line>{{ data.dates }}</FitText>
            <FitText v-if="details" class="vd-details" :max="32" :min="16" :lines="3" :line-height="1.3">{{ details }}</FitText>
          </div>
          <div v-if="logo" class="vd-brand"><img :src="logo" alt="" /></div>
        </div>
        <div v-if="price.has" class="vd-price">
          <FitText :max="100" :min="48"><CreativePrice :data="data" variant="side" /></FitText>
          <FitText v-if="data.disclaimer" class="cr-fine" :max="20" :min="13" :lines="3" :line-height="1.3">{{ data.disclaimer }}</FitText>
        </div>
        <span v-if="cta" class="cr-cta">{{ cta }}</span>
      </div>
      <FitText v-if="!logo && data.agencyName" class="vd-agency" :max="64" :min="28" line>{{ data.agencyName }}</FitText>
    </template>

    <!-- 4. Destino em destaque (França): destino no alto, base recortada com preço e contato -->
    <template v-else-if="template === 'destino'">
      <div class="cr-photo ds-photo" :style="bg(0)"></div>
      <div class="ds-box">
        <svg class="ds-path" viewBox="0 0 220 60" fill="none" aria-hidden="true">
          <path d="M6 52 C 60 8, 130 70, 196 16" stroke="currentColor" stroke-width="3" stroke-dasharray="7 9" stroke-linecap="round" />
          <path d="M188 9 l20 4 -14 14z" fill="currentColor" />
        </svg>
        <FitText class="ds-pre" :max="40" :min="20" line>{{ badge || "viaje para" }}</FitText>
        <FitText class="ds-title" :max="210" :min="56" :lines="3" :line-height="0.92">{{ headline }}</FitText>
      </div>
      <div class="ds-panel">
        <div v-if="tagLine || data.priceSuffix" class="ds-row">
          <span v-if="tagLine" class="ds-chip">{{ tagLine }}</span>
          <span v-if="data.priceSuffix" class="ds-note">*valor {{ data.priceSuffix }}</span>
        </div>
        <div v-if="price.has" class="ds-price"><FitText :max="100" :min="48"><CreativePrice :data="data" variant="side" hide-foot /></FitText></div>
        <div class="ds-foot">
          <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip ds-logo" alt="" />
          <FitText v-else-if="data.agencyName" class="ds-agency" :max="42" :min="20" line>{{ data.agencyName }}</FitText>
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

    <!-- 5. Manchete (Rio de Janeiro): destino enorme, data em tag, preço em caixa e o que inclui ao lado -->
    <template v-else-if="template === 'manchete'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="mc-shade"></div>
      <div class="mc-area">
        <FitText v-if="badge" class="mc-label" :max="50" :min="22" line>{{ badge }}</FitText>
        <FitText class="mc-title" :max="200" :min="80" fill>{{ headline }}</FitText>
        <FitText v-if="data.dates" class="mc-date" :max="46" :min="22" line><CalendarDaysIcon />{{ data.dates }}</FitText>
        <div class="mc-bottom">
          <div v-if="price.has" class="mc-price">
            <FitText class="mc-price-label" :max="30" :min="16" line>{{ data.priceSuffix || data.pricePrefix || "A partir de" }}</FitText>
            <FitText :max="100" :min="48"><CreativePrice :data="data" variant="side" hide-foot /></FitText>
            <FitText v-if="price.installmentText || price.count" class="mc-price-note" :max="24" :min="14" line>{{ price.count ? `Total de ${price.total}` : `${price.installmentText} sem juros` }}</FitText>
          </div>
          <FitText v-if="inclusions.length" class="mc-inc" :max="30" :min="15" fill>
            <ul><li v-for="item in inclusions.slice(0, format === 'square' ? 3 : 4)" :key="item.label">{{ item.label }}</li></ul>
          </FitText>
        </div>
        <FitText v-if="!cta && (data.contact || data.agencyName)" class="mc-foot" :max="34" :min="16" line>
          {{ data.contact ? `Chame no WhatsApp ${data.contact}` : data.agencyName }}
        </FitText>
        <span v-if="cta" class="cr-cta mc-cta">{{ cta }}</span>
      </div>
      <img v-if="logo && !tapes" :src="logo" class="cr-logo cr-logo-chip cr-logo-tl" alt="" />
    </template>

    <!-- 6. Campanha com ícones (CVC mês do consumidor): faixa dividida com campanha e destino, foto embaixo -->
    <template v-else-if="template === 'campanha'">
      <div class="cr-photo cp-photo" :style="bg(0)"></div>
      <div class="cp-band">
        <div class="cp-left">
          <FitText class="cp-head" :max="110" :min="40" fill>{{ badge || "Oferta especial" }}</FitText>
          <FitText v-if="data.departure || data.dates" class="cp-tag" :max="30" :min="16" line>{{ data.departure || data.dates }}</FitText>
        </div>
        <div class="cp-right">
          <FitText class="cp-title" :max="150" :min="44" :lines="3" :line-height="0.92">{{ headline }}</FitText>
          <FitText v-if="data.duration" class="cp-dur" :max="40" :min="20" line>{{ data.duration }} incluindo:</FitText>
          <FitText v-if="inclusions.length" class="cp-icons" :max="26" :min="14" line>
            <span v-for="item in inclusions.slice(0, 4)" :key="item.label"><component :is="item.icon" /><small>{{ shortLabel(item.label) }}</small></span>
          </FitText>
          <FitText v-if="price.has" class="cp-price" :max="104" :min="48" fill><CreativePrice :data="data" variant="stack" /></FitText>
          <FitText v-if="data.disclaimer" class="cr-fine" :max="19" :min="12" :lines="2" :line-height="1.3">{{ data.disclaimer }}</FitText>
        </div>
      </div>
      <span v-if="cta" class="cr-cta cp-cta">{{ cta }}</span>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip cr-logo-br" alt="" />
    </template>

    <!-- 7. Preço em destaque: foto num círculo grande e o valor enorme -->
    <template v-else-if="template === 'price-hero'">
      <div class="cr-photo ph-photo" :style="bg(0)"></div>
      <div class="ph-area">
        <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip ph-logo" alt="" />
        <span v-if="badge" class="cr-tag">{{ badge }}</span>
        <FitText class="ph-dest" :max="130" :min="44" :lines="3" :line-height="0.95">{{ headline }}</FitText>
        <FitText v-if="price.has" class="ph-price" :max="170" :min="70"><CreativePrice :data="data" variant="stack" /></FitText>
        <FitText v-if="data.dates || data.departure" class="ph-meta" :max="36" :min="18" line>
          {{ [data.dates, data.departure].filter(Boolean).join(" · ") }}
        </FitText>
        <span v-if="cta" class="cr-cta ph-cta">{{ cta }}</span>
      </div>
    </template>

    <!-- 8. Black Friday economia (Salvador): preto e amarelo, destino enorme, De/Por, economia e selo -->
    <template v-else-if="template === 'black-economia'">
      <CreativeTapes :text="tapeLabel" variant="yellow" position="corner" />
      <div class="be-area">
        <!-- 1em = tamanho do destino; o resto é proporcional e o bloco todo cabe na área. -->
        <FitText class="be-text" :max="190" :min="48" fill>
          <span v-if="fromCity" class="be-from">De {{ fromCity }} para</span>
          <span class="be-title">{{ headline }}</span>
          <span v-if="data.dates" class="be-date"><CalendarDaysIcon />{{ data.dates }}</span>
          <span v-if="price.has" class="be-price"><CreativePrice :data="data" variant="total" hide-foot /></span>
          <span v-if="saving" class="be-save">Economize {{ saving }}</span>
          <span v-if="price.installmentText" class="be-inst">{{ price.installmentText }} sem juros</span>
        </FitText>
        <span v-if="cta" class="cr-cta be-cta">{{ cta }}</span>
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

    <!-- 9. Black Friday faixa (Punta Cana): foto com fitas, faixa amarela com destino, cartão e preço preto -->
    <template v-else-if="template === 'black-faixa'">
      <div class="cr-photo bf-photo" :style="bg(0)"></div>
      <CreativeTapes :text="tapeLabel" variant="yellow" position="top" />
      <div class="bf-stack" :class="{ 'bf-stack-full': !(logo || data.agencyName || cta) }">
        <div class="bf-band">
          <span v-if="badge" class="bf-badge">{{ badge }}</span>
          <FitText class="bf-title" :max="136" :min="56" line>{{ headline }}</FitText>
        </div>
        <!-- Cartão do pacote: o que inclui e quando em cima, preço numa barra preta embaixo. -->
        <div class="bf-card">
          <div class="bf-top">
            <span class="bf-tag">Pacote inclui:</span>
            <FitText v-if="data.departure" class="bf-pill" :max="28" :min="14" line><MapPinIcon />{{ data.departure }}</FitText>
          </div>
          <div class="bf-cols">
            <FitText class="bf-list" :max="32" :min="14" fill>
              <ul><li v-for="item in inclusions.slice(0, format === 'story' ? 5 : 4)" :key="item.label">{{ item.label }}</li></ul>
            </FitText>
            <FitText v-if="data.dates || data.duration" class="bf-when" :max="34" :min="14" fill>
              <span v-if="data.dates" class="bf-dates">{{ data.dates }}</span>
              <b v-if="data.duration" class="bf-dur">{{ data.duration }}</b>
            </FitText>
          </div>
          <div v-if="price.has" class="bf-price">
            <FitText class="bf-price-fit" :max="96" :min="34" fill><CreativePrice :data="data" variant="side" hide-foot /></FitText>
            <FitText v-if="price.count" class="bf-total" :max="34" :min="14" fill><small>Valor total</small><b>{{ price.total }}</b></FitText>
          </div>
          <FitText v-if="data.disclaimer && format === 'story'" class="cr-fine bf-fine" :max="18" :min="12" line>{{ data.disclaimer }}</FitText>
        </div>
      </div>
      <div v-if="logo || data.agencyName || cta" class="bf-foot">
        <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip bf-logo" alt="" />
        <FitText v-else-if="data.agencyName" class="bf-agency" :max="44" :min="20" line>{{ data.agencyName }}</FitText>
        <span v-if="cta" class="cr-cta">{{ cta }}</span>
      </div>
    </template>

    <!-- 10. Lista do que inclui -->
    <template v-else-if="template === 'benefits'">
      <div class="cr-photo bn-photo" :style="bg(0)"></div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip cr-logo-tl" alt="" />
      <div v-if="ribbon" class="cr-corner">{{ badge }}</div>
      <div class="bn-body">
        <FitText v-if="data.dates" class="bn-eyebrow" :max="30" :min="16" line>{{ data.dates }}</FitText>
        <FitText class="bn-title" :max="140" :min="44" :lines="2" :line-height="0.95">{{ headline }}</FitText>
        <FitText v-if="inclusions.length" class="bn-list" :max="36" :min="16">
          <ul class="cr-icons-list">
            <li v-for="item in inclusions.slice(0, maxList)" :key="item.label"><i><component :is="item.icon" /></i>{{ item.label }}</li>
          </ul>
        </FitText>
        <div class="bn-foot">
          <FitText v-if="price.has" class="bn-price" :max="88" :min="44"><CreativePrice :data="data" variant="side" /></FitText>
          <div v-if="cta || data.contact" class="cr-side">
            <span v-if="cta" class="cr-cta">{{ cta }}</span>
            <span v-if="data.contact" class="cr-contact"><PhoneIcon />{{ data.contact }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- 11. Cartão com tudo -->
    <!-- Vidro fosco: a parte da foto atrás do cartão aparece desfocada (cópia da foto com blur,
         alinhada pela base; funciona no download, ao contrário do backdrop-filter). -->
    <template v-else-if="template === 'card'">
      <div class="cr-photo cr-fill" :style="bg(0)"></div>
      <div class="cd-shade"></div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip cr-logo-tl" alt="" />
      <div v-if="ribbon" class="cr-corner">{{ badge }}</div>
      <div class="cd-card">
        <div class="cr-photo cd-glass" :style="bg(0)"></div>
        <div class="cd-inner">
          <FitText v-if="data.dates" class="cd-dates" :max="30" :min="16" line>{{ data.dates }}</FitText>
          <FitText class="cd-title" :max="150" :min="44" fill>{{ headline }}</FitText>
          <FitText v-if="inclusions.length" class="cd-inc" :max="30" :min="16" :lines="2" :line-height="1.25">{{ inclusionLine(4, " · ") }}</FitText>
          <div class="cd-foot">
            <FitText v-if="price.has" class="cd-price" :max="84" :min="40"><CreativePrice :data="data" variant="side" /></FitText>
            <div v-if="cta || data.contact" class="cr-side">
              <span v-if="cta" class="cr-cta">{{ cta }}</span>
              <span v-if="data.contact" class="cr-contact cd-contact"><PhoneIcon />{{ data.contact }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 12. Colagem de 2 fotos -->
    <template v-else-if="template === 'collage-2'">
      <div class="cl-grid">
        <div class="cr-photo" :style="bg(0)"></div>
        <div class="cr-photo" :style="bg(1)"></div>
      </div>
      <div v-if="ribbon" class="cr-corner">{{ badge }}</div>
      <div class="cl-band">
        <div class="cl-text">
          <FitText v-if="data.dates" class="cl-eyebrow" :max="30" :min="16" line>{{ data.dates }}</FitText>
          <FitText class="cl-title" :max="140" :min="44" :lines="2" :line-height="0.95">{{ headline }}</FitText>
          <FitText v-if="subLine" class="cl-sub" :max="30" :min="16" line>{{ subLine }}</FitText>
        </div>
        <div v-if="price.has || cta" class="cl-aside">
          <div v-if="price.has" class="cl-price"><FitText :max="80" :min="40"><CreativePrice :data="data" variant="stack" /></FitText></div>
          <span v-if="cta" class="cr-cta cl-cta">{{ cta }}</span>
        </div>
      </div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip cr-logo-tl" alt="" />
    </template>

    <!-- 13. Mosaico de 3 fotos -->
    <template v-else-if="template === 'mosaic-3'">
      <div class="ms-grid">
        <div class="cr-photo ms-big" :style="bg(0)"></div>
        <div class="cr-photo" :style="bg(1)"></div>
        <div class="cr-photo" :style="bg(2)"></div>
      </div>
      <div v-if="ribbon" class="cr-corner">{{ badge }}</div>
      <div class="ms-band">
        <div class="ms-text">
          <FitText v-if="data.dates" class="cl-eyebrow" :max="30" :min="16" line>{{ data.dates }}</FitText>
          <FitText class="cl-title" :max="136" :min="42" :lines="2" :line-height="0.95">{{ headline }}</FitText>
          <FitText v-if="inclusions.length && format !== 'square'" class="cl-sub" :max="28" :min="15" :lines="2" :line-height="1.25">{{ inclusionLine(4, " · ") }}</FitText>
        </div>
        <div v-if="price.has || cta" class="cl-aside">
          <div v-if="price.has" class="ms-price"><FitText :max="78" :min="40"><CreativePrice :data="data" variant="stack" /></FitText></div>
          <span v-if="cta" class="cr-cta cl-cta">{{ cta }}</span>
        </div>
      </div>
      <img v-if="logo" :src="logo" class="cr-logo cr-logo-chip cr-logo-tl" alt="" />
    </template>

    <CreativeTapes v-if="tapes && !isBlack" :text="tapeLabel" />
  </div>
</template>

<script setup lang="ts">
/**
 * Um criativo em tamanho real (1080 px de largura). A tela mostra reduzido com transform e o
 * download (html-to-image) usa este mesmo elemento, então o que se vê é o que se baixa.
 *
 * Cada modelo é montado em regiões com proporção fixa; os textos e o preço usam FitText para
 * ocupar a região sem estourar (título curto fica grande, longo encolhe). O conteúdo respeita
 * as áreas seguras de cada formato (no Stories, topo e base ficam livres para a interface).
 */
import { computed } from "vue";
import { CalendarDaysIcon, MapPinIcon, MegaphoneIcon, PhoneIcon, PlaneTakeoffIcon } from "lucide-vue-next";
import "./creativeFonts";
import { BLACK_TEMPLATES } from "./creativeTemplates";
import { CAMPAIGNS, FORMAT_SIZES, PHOTO_SIZE_VARS, effectiveColors, formatMoney, parseMoney, priceParts, readableOn, tapeText, type CreativeData, type CreativeFormat } from "./creativeData";
import { inclusionIcon } from "./creativeIcons";
import CreativePrice from "./CreativePrice.vue";
import CreativeTapes from "./CreativeTapes.vue";
import FitText from "./FitText.vue";

const props = defineProps<{
  template: string;
  format: CreativeFormat;
  data: CreativeData;
  /** Fotos já prontas para uso (endereços locais/blob), na ordem escolhida. */
  photos: string[];
  showLogo?: boolean;
}>();

const SAFE: Record<CreativeFormat, { pad: number; top: number; bottom: number }> = {
  feed: { pad: 64, top: 64, bottom: 64 },
  square: { pad: 56, top: 52, bottom: 52 },
  // Stories: o Instagram desenha a barra de progresso e o perfil em cima e o campo de resposta embaixo.
  story: { pad: 72, top: 210, bottom: 280 }
};

const size = computed(() => FORMAT_SIZES[props.format]);
const logo = computed(() => (props.showLogo === false ? "" : props.data.logoUrl));
const cta = computed(() => (props.data.ctaEnabled ? props.data.cta.trim() : ""));
const price = computed(() => priceParts(props.data));
const isBlack = computed(() => BLACK_TEMPLATES.has(props.template));
const tapes = computed(() => props.data.tapes || isBlack.value);
const tapeLabel = computed(() => tapeText(props.data));
const badge = computed(() => (props.data.badge || (props.data.campaign ? CAMPAIGNS[props.data.campaign].badge : "")).trim());
// Faixa diagonal no canto: opcional e escondida quando as fitas cruzadas estão no topo.
const ribbon = computed(() => Boolean(badge.value) && props.data.ribbon !== false && !(tapes.value && !isBlack.value));
const headline = computed(() => (props.data.destination || props.data.title).trim());
const inclusions = computed(() => props.data.benefits.filter(Boolean).map(label => ({ label, icon: inclusionIcon(label) })));
const inclusionLine = (count: number, separator = " + ") => inclusions.value.slice(0, count).map(item => item.label).join(separator);
const subLine = computed(() => inclusionLine(2));
// "Hospedagem inclusa" → "Hospedagem" (legenda curta embaixo do ícone).
const shortLabel = (label: string) => label.split(/\s+/).slice(0, label.length > 14 ? 1 : 2).join(" ");
const maxList = computed(() => ({ square: 3, feed: 5, story: 7 })[props.format]);
const tagLine = computed(() => props.data.duration || inclusions.value[0]?.label || "");
const details = computed(() => [props.data.departure, ...inclusions.value.slice(0, 4).map(item => item.label)].filter(Boolean).join(", "));
// Datas, saída e o que inclui, cada um com seu ícone (lista do modelo "Foto e dois blocos").
const facts = computed(() => [
  ...(props.data.dates ? [{ label: props.data.dates, icon: CalendarDaysIcon }] : []),
  ...(props.data.departure ? [{ label: props.data.departure, icon: MapPinIcon }] : []),
  ...inclusions.value.slice(2)
]);
// "Saída de Goiânia" → "Goiânia" (para "De Goiânia para").
const fromCity = computed(() => props.data.departure.replace(/^sa[ií](da|ndo) (de|do|da)\s+/i, "").trim());
const saving = computed(() => {
  const diff = parseMoney(props.data.oldPrice) - parseMoney(props.data.priceValue);
  return diff > 0 ? formatMoney(diff) : "";
});
const discount = computed(() => {
  const old = parseMoney(props.data.oldPrice);
  const now = parseMoney(props.data.priceValue);
  return old > now && now > 0 ? `${Math.round((1 - now / old) * 100)}%` : "";
});

const rootStyle = computed(() => {
  // Modelos de Black Friday: sempre preto e amarelo.
  const colors = isBlack.value ? { primary: CAMPAIGNS.black_friday.primary, secondary: CAMPAIGNS.black_friday.secondary } : effectiveColors(props.data);
  const onAccent = readableOn(colors.secondary);
  const safe = SAFE[props.format];
  return {
    width: `${size.value.width}px`,
    height: `${size.value.height}px`,
    "--c1": colors.primary,
    "--c2": colors.secondary,
    "--on1": readableOn(colors.primary),
    "--on2": onAccent,
    // Texto sobre a cor de destaque: a cor da marca quando o destaque é claro.
    "--ink2": onAccent === "#111827" ? colors.primary : "#ffffff",
    "--pad": `${safe.pad}px`,
    // Com as fitas no topo, o conteúdo de cima desce para não ficar coberto.
    "--top": `${safe.top + (tapes.value && !isBlack.value ? 170 : 0)}px`,
    "--bot": `${safe.bottom}px`,
    "--W": `${size.value.width}px`,
    "--H": `${size.value.height}px`,
    // Tamanho da foto escolhido no editor: move a divisão foto/conteúdo.
    "--ph-shift": PHOTO_SIZE_VARS[props.data.photoSize || "md"].shift,
    "--ph-k": String(PHOTO_SIZE_VARS[props.data.photoSize || "md"].k)
  };
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
  font-family: "Montserrat", sans-serif;
  -webkit-font-smoothing: antialiased;
}
.cr * {
  box-sizing: border-box;
}
.cr :deep(svg) {
  flex: none;
}
.cr ul {
  margin: 0;
  padding: 0;
  list-style: none;
}
.cr-photo {
  background-color: color-mix(in srgb, var(--c1) 60%, #000);
  background-position: center;
  background-size: cover;
}
.cr-fill {
  position: absolute;
  inset: 0;
}
.cr-scrim-top {
  position: absolute;
  inset: 0 0 auto 0;
  height: 40%;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0));
}
.cr-fine {
  font-weight: 500;
  opacity: 0.8;
}
.cr-tag {
  display: inline-block;
  align-self: flex-start;
  padding: 8px 18px;
  border-radius: 8px;
  background: var(--c2);
  color: var(--on2);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
/* Fita diagonal no canto superior direito. */
/*
 * Faixa a 45° cortando o canto de borda a borda: o centro fica na diagonal do canto, a uma
 * distância --rb das bordas, e o comprimento passa das duas bordas (nunca aparece a ponta).
 * No Stories ela desce para sair de baixo da barra do Instagram.
 */
.cr-corner {
  position: absolute;
  top: calc(var(--rb) / 2);
  right: calc(var(--rb) / 2);
  z-index: 4;
  width: calc(var(--rb) * 2.4);
  padding: 16px 0;
  background: var(--c2);
  color: var(--ink2);
  font-size: 28px;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-align: center;
  text-transform: uppercase;
  white-space: nowrap;
  transform: translate(50%, -50%) rotate(45deg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  --rb: 300px;
}
.cr-story .cr-corner {
  --rb: 460px;
}
.cr-corner-left {
  right: auto;
  left: calc(var(--rb) / 2);
  transform: translate(-50%, -50%) rotate(-45deg);
}
.cr-logo {
  position: relative;
  z-index: 3;
  display: block;
  max-width: 320px;
  max-height: 120px;
  object-fit: contain;
}
.cr-logo-chip {
  padding: 14px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}
.cr-logo-br {
  position: absolute;
  right: var(--pad);
  bottom: var(--bot);
}
.cr-logo-tl {
  position: absolute;
  top: var(--top);
  left: var(--pad);
}
/* O único "botão" da arte: só quando a chamada está ligada. */
.cr-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
  padding: 24px 46px;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-size: 34px;
  font-weight: 800;
  white-space: nowrap;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.2);
}
.cr-side {
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: flex-end;
  gap: 14px;
}
.cr-contact {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 28px;
  font-weight: 700;
}
.cr-contact :deep(svg) {
  width: 30px;
  height: 30px;
}
/* Lista com ícone num círculo na cor de destaque (em "em": cresce com o bloco). */
.cr-icons-list {
  display: flex;
  flex-direction: column;
  gap: 0.45em;
  font-weight: 700;
}
.cr-icons-list li {
  display: flex;
  align-items: center;
  gap: 0.55em;
  line-height: 1.15;
}
.cr-icons-list i {
  display: grid;
  flex: none;
  place-items: center;
  width: 1.6em;
  height: 1.6em;
  border-radius: 50%;
  background: var(--c2);
  color: var(--on2);
}
.cr-icons-list i :deep(svg) {
  width: 0.9em;
  height: 0.9em;
}

/* Nome do roteiro: linhas equilibradas ("JALAPÃO / 6 DIAS" em vez de "JALAPÃO 6 / DIAS"). */
.of-title,
.dv-title,
.vd-title,
.ds-title,
.mc-title,
.cp-title,
.ph-dest,
.bf-title,
.bn-title,
.cd-title,
.cl-title {
  text-wrap-style: balance;
}

/* ================= 1. Oferta em bloco ================= */
.cr-t-oferta {
  background: color-mix(in srgb, var(--c1) 72%, #000);
}
/* A foto ocupa o espaço abaixo do bloco (entra um pouco por trás dele). */
.of-photo {
  position: absolute;
  inset: calc(var(--top) + 64% - var(--ph-shift) - 180px) 0 0 0;
}
.cr-story .of-photo {
  inset: calc(var(--top) + 52% - var(--ph-shift) - 180px) 0 0 0;
}
.cr-square .of-photo {
  inset: calc(var(--top) + 74% - var(--ph-shift) - 180px) 0 0 0;
}
.of-photo::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 240px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--c1) 72%, #000), transparent);
}
.of-area {
  position: absolute;
  top: var(--top);
  right: var(--pad);
  left: var(--pad);
  z-index: 2;
  display: flex;
  height: calc(64% - var(--ph-shift));
  flex-direction: column;
  align-items: center;
}
.cr-story .of-area {
  height: calc(52% - var(--ph-shift));
}
.cr-square .of-area {
  height: calc(74% - var(--ph-shift));
}
.of-card {
  position: relative;
  display: flex;
  width: 100%;
  min-height: 0;
  flex: 1 1 auto;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 74px 52px 70px;
  border-radius: 48px;
  background: var(--c1);
  color: var(--on1);
  text-align: center;
  box-shadow: 0 30px 70px rgba(0, 0, 0, 0.35);
  --pz-accent: var(--c2);
}
.cr-square .of-card {
  gap: 10px;
  padding: 64px 44px 60px;
}
.of-ribbon {
  position: absolute;
  top: -34px;
  left: 50%;
  display: inline-flex !important;
  align-items: center;
  gap: 0.4em;
  max-width: 86% !important;
  padding: 0.42em 1.1em;
  border-radius: 0.5em;
  background: #e3262f;
  color: #fff;
  font-weight: 900;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  transform: translateX(-50%) rotate(-2deg);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.3);
}
.of-ribbon :deep(svg) {
  width: 1.1em;
  height: 1.1em;
}
.of-title {
  display: flex;
  flex: 1.8 1 0;
  height: auto !important;
  min-height: 0;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -0.02em;
  text-transform: uppercase;
}
.of-dur {
  width: 100%;
  font-weight: 600;
}
.of-inc {
  width: 100%;
  color: var(--c2);
  font-weight: 800;
}
.of-price {
  display: flex;
  flex: 1 1 0;
  height: auto !important;
  min-height: 0;
  align-items: center;
  justify-content: center;
}
.of-fine {
  width: 100%;
}
.of-stamp {
  position: absolute;
  top: -50px;
  right: -36px;
  display: flex;
  width: 150px;
  height: 150px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 6px solid #fff;
  border-radius: 50%;
  background: var(--c2);
  color: var(--ink2);
  line-height: 1;
  transform: rotate(-12deg);
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.3);
}
.of-stamp small {
  font-size: 20px;
  font-weight: 800;
  text-transform: uppercase;
}
.of-stamp b {
  font-size: 44px;
  font-weight: 900;
}
.of-bar {
  position: relative;
  z-index: 2;
  display: inline-flex !important;
  flex: none;
  align-items: center;
  justify-content: center;
  gap: 0.5em;
  width: auto !important;
  max-width: 84% !important;
  margin-top: -36px;
  padding: 0.5em 1.3em;
  border-radius: 0.5em;
  background: var(--c2);
  color: var(--ink2);
  font-weight: 900;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.3);
}
.of-bar :deep(svg) {
  width: 1.1em;
  height: 1.1em;
}
.of-cta {
  align-self: center;
  margin-top: 28px;
}

/* ================= 2. Foto e dois blocos ================= */
.dv-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: calc(52% + var(--ph-shift));
}
.cr-story .dv-photo {
  height: calc(52% + var(--ph-shift));
}
.cr-square .dv-photo {
  height: calc(50% + var(--ph-shift));
}
.dv-logo {
  position: absolute;
  top: var(--top);
  right: var(--pad);
}
.dv-grid {
  position: absolute;
  inset: calc(52% + var(--ph-shift)) 0 0 0;
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, 0.75fr);
}
.cr-square .dv-grid {
  inset: calc(50% + var(--ph-shift)) 0 0 0;
}
.dv-left {
  position: relative;
  display: flex;
  min-height: 0;
  flex-direction: column;
  gap: 18px;
  padding: 56px 40px var(--bot) var(--pad);
  background: var(--c2);
  color: var(--ink2);
}
.cr-square .dv-left {
  gap: 10px;
  padding-top: 40px;
}
/* Aba triangular saindo do bloco, como na referência. */
.dv-left::before {
  content: "";
  position: absolute;
  top: -46px;
  left: 110px;
  border-right: 70px solid transparent;
  border-bottom: 46px solid var(--c2);
  border-left: 70px solid transparent;
}
.dv-title {
  display: flex;
  flex: 1.5 1 0;
  height: auto !important;
  min-height: 0;
  align-items: flex-end;
  font-weight: 900;
  line-height: 0.98;
  letter-spacing: -0.02em;
}
.dv-sub {
  font-weight: 600;
}
.dv-facts {
  flex: 1 1 0;
  height: auto !important;
  min-height: 0;
}
.dv-facts ul {
  display: flex;
  flex-direction: column;
  gap: 0.55em;
  font-weight: 700;
}
.dv-facts li {
  display: flex;
  align-items: center;
  gap: 0.55em;
  line-height: 1.1;
}
.dv-facts :deep(svg) {
  width: 1.35em;
  height: 1.35em;
  stroke-width: 1.6;
}
.dv-right {
  display: flex;
  min-height: 0;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 56px 40px var(--bot);
  background: var(--c1);
  color: var(--on1);
  text-align: center;
  --pz-accent: var(--c2);
}
.dv-price {
  display: flex;
  flex: 1 1 0;
  height: auto !important;
  min-height: 0;
  align-items: center;
  justify-content: center;
}
.dv-cta {
  align-self: center;
}

/* ================= 3. Cartão claro ================= */
.vd-area {
  position: absolute;
  top: var(--top);
  right: var(--pad);
  left: var(--pad);
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 26px;
}
.vd-card {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 36px;
  padding: 52px 52px 48px;
  border-radius: 36px;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.2);
}
.vd-text {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 14px;
}
.vd-title {
  color: var(--c1);
  font-weight: 900;
  letter-spacing: -0.02em;
  text-transform: uppercase;
}
.vd-dates {
  color: var(--c1);
  font-weight: 800;
}
.vd-details {
  color: #374151;
  font-weight: 500;
}
.vd-brand {
  display: flex;
  flex: none;
  align-items: center;
  align-self: stretch;
  padding-left: 32px;
  border-left: 3px solid rgba(17, 24, 39, 0.12);
}
.vd-brand img {
  display: block;
  max-width: 200px;
  max-height: 150px;
  object-fit: contain;
}
.vd-price {
  display: flex;
  width: 54%;
  flex-direction: column;
  gap: 14px;
  padding: 36px 42px;
  border-radius: 28px;
  background: var(--c1);
  color: var(--on1);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.3);
}
.cr-square .vd-price {
  width: 58%;
  padding: 28px 34px;
}
.vd-agency {
  position: absolute !important;
  right: var(--pad);
  bottom: var(--bot);
  max-width: 60% !important;
  color: #fff;
  font-weight: 900;
  text-align: right;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
}

/* ================= 4. Destino em destaque ================= */
/* Painel de baixo com a altura do conteúdo; a foto ocupa todo o resto e entra por baixo da
   ponta recortada do painel. */
.cr-t-destino {
  display: flex;
  flex-direction: column;
}
.ds-photo {
  position: relative;
  min-height: 40%;
  flex: 1 1 auto;
  margin-bottom: -100px;
}
.ds-box {
  position: absolute;
  top: 0;
  left: var(--pad);
  z-index: 2;
  display: flex;
  width: 58%;
  flex-direction: column;
  padding: calc(var(--top) + 24px) 46px 46px;
  border-radius: 0 0 40px 40px;
  background: var(--c1);
  color: var(--on1);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
}
.ds-path {
  width: 200px;
  margin-bottom: 14px;
  color: var(--c2);
}
.ds-pre {
  font-weight: 600;
}
.ds-title {
  margin-top: 6px;
  color: var(--c2);
  font-weight: 900;
  letter-spacing: -0.01em;
  text-transform: uppercase;
}
.ds-panel {
  position: relative;
  z-index: 2;
  display: flex;
  flex: none;
  flex-direction: column;
  gap: 28px;
  padding: 120px var(--pad) var(--bot);
  background: linear-gradient(180deg, color-mix(in srgb, var(--c1) 82%, #fff) 0%, var(--c1) 42%, color-mix(in srgb, var(--c1) 80%, #000) 100%);
  clip-path: polygon(0 80px, 50% 0, 100% 80px, 100% 100%, 0 100%);
  color: var(--on1);
}
.cr-square .ds-panel {
  gap: 18px;
  padding-top: 100px;
}
.ds-row {
  display: flex;
  align-items: center;
  gap: 20px;
}
.ds-chip {
  padding: 14px 32px;
  border-radius: 18px;
  background: #fff;
  color: var(--c1);
  font-size: 36px;
  font-weight: 800;
}
.ds-note {
  font-size: 26px;
  font-style: italic;
  opacity: 0.9;
}
.ds-price {
  width: 64%;
  padding: 28px 42px;
  border-radius: 28px;
  background: var(--c2);
  color: var(--on2);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.25);
}
.ds-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
.ds-logo {
  max-height: 112px;
}
.ds-agency {
  width: 45% !important;
  font-weight: 800;
}
.ds-contact {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}
.ds-contact small {
  font-size: 24px;
  opacity: 0.9;
}
.ds-contact b {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--c2);
  font-size: 44px;
  font-weight: 900;
}
.ds-contact :deep(svg) {
  width: 38px;
  height: 38px;
}

/* ================= 5. Manchete ================= */
.mc-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0.08) 40%, rgba(0, 0, 0, 0.15) 60%, rgba(0, 0, 0, 0.6) 100%);
}
.mc-area {
  position: absolute;
  inset: var(--top) var(--pad) var(--bot);
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 22px;
  text-align: center;
}
.mc-label {
  width: auto !important;
  max-width: 92% !important;
  padding: 0.3em 0.9em;
  border-radius: 0.45em;
  background: var(--c2);
  color: var(--on2);
  font-family: "Anton", "Montserrat", sans-serif;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.mc-title {
  display: flex;
  flex: 1 1 0;
  height: auto !important;
  min-height: 0;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-family: "Anton", "Montserrat", sans-serif;
  line-height: 0.9;
  text-transform: uppercase;
  text-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
}
.mc-date {
  display: inline-flex !important;
  align-items: center;
  gap: 0.45em;
  width: auto !important;
  max-width: 90% !important;
  padding: 0.35em 0.9em;
  border-radius: 999px;
  background: var(--c2);
  color: var(--on2);
  font-weight: 900;
  text-transform: uppercase;
  transform: rotate(-3deg);
}
.mc-date :deep(svg) {
  width: 1.1em;
  height: 1.1em;
}
.mc-bottom {
  display: flex;
  width: 100%;
  flex: 0.8 1 0;
  min-height: 0;
  align-items: center;
  margin-top: 10px;
}
.mc-price {
  position: relative;
  z-index: 2;
  display: flex;
  width: 44%;
  flex: none;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 28px 30px;
  border-radius: 30px;
  background: var(--c2);
  color: var(--on2);
  text-align: left;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
}
.mc-price-label {
  font-weight: 900;
  text-transform: uppercase;
}
.mc-price-note {
  font-weight: 600;
}
.mc-inc {
  height: 78% !important;
  flex: 1 1 0;
  margin-left: -30px;
  padding: 0.9em 0.9em 0.9em 1.9em;
  border-radius: 0 0.9em 0.9em 0;
  background: #fff;
  color: #111827;
  text-align: left;
}
.mc-inc ul {
  display: flex;
  flex-direction: column;
  gap: 0.35em;
  font-weight: 600;
  line-height: 1.2;
}
.mc-inc li::before {
  content: "• ";
  color: var(--c2);
  font-weight: 900;
}
.mc-foot {
  color: #fff;
  font-weight: 900;
  text-transform: uppercase;
  text-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}
.mc-cta {
  align-self: center;
}

/* ================= 6. Campanha com ícones ================= */
.cp-photo {
  position: absolute;
  inset: calc(54% - var(--ph-shift)) 0 0 0;
}
.cr-story .cp-photo {
  inset: calc(52% - var(--ph-shift)) 0 0 0;
}
.cr-square .cp-photo {
  inset: calc(58% - var(--ph-shift)) 0 0 0;
}
.cp-band {
  position: absolute;
  inset: 0 0 auto 0;
  display: grid;
  height: calc(54% - var(--ph-shift));
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
}
.cr-story .cp-band {
  height: calc(52% - var(--ph-shift));
}
.cr-square .cp-band {
  height: calc(58% - var(--ph-shift));
}
.cp-left {
  display: flex;
  min-height: 0;
  flex-direction: column;
  gap: 22px;
  padding: var(--top) 34px 52px var(--pad);
  background: var(--c1);
  color: var(--on1);
}
.cp-head {
  display: flex;
  align-items: center;
  font-weight: 900;
  line-height: 0.98;
  letter-spacing: -0.02em;
  text-transform: uppercase;
}
.cp-tag {
  width: auto !important;
  align-self: flex-start;
  padding: 0.35em 0.7em;
  border-radius: 0.4em;
  background: var(--c2);
  color: var(--ink2);
  font-weight: 800;
  text-transform: uppercase;
}
.cp-right {
  display: flex;
  min-height: 0;
  flex-direction: column;
  gap: 12px;
  padding: var(--top) var(--pad) 46px 44px;
  background: var(--c2);
  color: var(--ink2);
}
.cp-title {
  font-weight: 900;
  letter-spacing: -0.02em;
  text-transform: uppercase;
}
.cp-dur {
  font-weight: 800;
}
/* Ícones do que inclui com legenda curta embaixo (em "em": encolhem juntos). */
.cp-icons {
  display: flex;
  gap: 1.1em;
  margin: 0.2em 0;
}
.cp-icons span {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35em;
}
.cp-icons :deep(svg) {
  width: 2.1em;
  height: 2.1em;
  stroke-width: 1.7;
}
.cp-icons small {
  font-size: 1em;
  font-weight: 700;
}
.cp-price {
  display: flex;
  flex: 1 1 0;
  height: auto !important;
  min-height: 0;
  align-items: flex-end;
}
.cp-cta {
  position: absolute;
  bottom: var(--bot);
  left: var(--pad);
}

/* ================= 7. Preço em destaque ================= */
.ph-photo {
  position: absolute;
  top: -10%;
  right: -18%;
  width: calc(96% * var(--ph-k));
  aspect-ratio: 1;
  border: 22px solid var(--c2);
  border-radius: 50%;
}
.cr-story .ph-photo {
  top: -6%;
  right: -24%;
  width: calc(118% * var(--ph-k));
}
.cr-square .ph-photo {
  top: -18%;
  right: -16%;
  width: calc(72% * var(--ph-k));
}
.ph-area {
  position: absolute;
  right: var(--pad);
  bottom: var(--bot);
  left: var(--pad);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  --pz-accent: var(--c2);
}
.cr-square .ph-area {
  right: 46%;
}
.ph-logo {
  max-height: 112px;
  margin-bottom: 10px;
}
.ph-dest {
  font-weight: 800;
  text-transform: uppercase;
}
.ph-meta {
  padding-left: 0.6em;
  border-left: 0.25em solid var(--c2);
  font-weight: 700;
}
.ph-cta {
  margin-top: 10px;
}

/* ================= 8. Black Friday economia ================= */
.be-area {
  position: absolute;
  inset: calc(var(--top) + 150px) var(--pad) calc(var(--bot) + 120px);
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
  color: #fff;
  text-align: center;
  --pz-accent: #fff;
}
/* No Stories as fitas de baixo já ficam dentro da área livre da interface. */
.cr-story .be-area {
  inset: calc(var(--top) + 90px) var(--pad) calc(var(--bot) + 10px);
}
/* No quadrado as fitas ocupam mais da altura: o texto fica entre elas. */
.cr-square .be-area {
  inset: 200px var(--pad) 250px;
}
/* Bloco de texto: 1em = destino; tudo proporcional. */
.be-text {
  display: flex;
  flex: 1.45 1 0;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.1em;
}
.be-from {
  font-size: 0.32em;
  font-weight: 900;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.be-title {
  color: var(--c2);
  font-weight: 900;
  line-height: 0.92;
  letter-spacing: -0.03em;
  text-transform: uppercase;
  text-wrap-style: balance;
}
.be-date {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4em;
  margin-top: 0.25em;
  font-size: 0.24em;
  font-weight: 700;
  text-transform: uppercase;
}
.be-date :deep(svg) {
  width: 1em;
  height: 1em;
}
.be-price {
  margin-top: 0.22em;
  font-size: 0.48em;
}
.be-save {
  margin-top: 0.1em;
  color: var(--c2);
  font-size: 0.44em;
  font-weight: 900;
  line-height: 1.05;
  text-transform: uppercase;
}
.be-inst {
  font-size: 0.36em;
  font-weight: 900;
  text-transform: uppercase;
}
.be-cta {
  align-self: center;
}
.be-photo {
  position: relative;
  width: 100%;
  min-height: 0;
  flex-grow: calc(1.3 * var(--ph-k));
  flex-shrink: 1;
  flex-basis: 0;
  border-radius: 46px;
}
.cr-square .be-photo {
  display: none;
}
/* Selo estourado (estrela de 16 pontas). */
.be-burst {
  position: absolute;
  top: -18px;
  right: -22px;
  z-index: 3;
  display: flex;
  width: 250px;
  height: 250px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--c2);
  color: #0b0b0b;
  clip-path: polygon(50% 0%, 59% 9%, 69% 3%, 74% 14%, 85% 12%, 86% 24%, 97% 27%, 93% 38%, 100% 50%, 93% 62%, 97% 73%, 86% 76%, 85% 88%, 74% 86%, 69% 97%, 59% 91%, 50% 100%, 41% 91%, 31% 97%, 26% 86%, 15% 88%, 14% 76%, 3% 73%, 7% 62%, 0% 50%, 7% 38%, 3% 27%, 14% 24%, 15% 12%, 26% 14%, 31% 3%, 41% 9%);
  text-align: center;
  transform: rotate(-12deg);
}
.be-burst small {
  font-size: 20px;
  font-weight: 900;
  text-transform: uppercase;
}
.be-burst b {
  max-width: 180px;
  font-size: 42px;
  font-weight: 900;
  line-height: 1;
}
.be-logo {
  position: absolute;
  bottom: calc(var(--bot) + 130px);
  left: calc(var(--pad) + 26px);
  max-height: 80px;
}
.cr-square .be-logo {
  display: none;
}

/* ================= 9. Black Friday faixa ================= */
.bf-photo {
  position: absolute;
  inset: 0 0 auto 0;
  height: calc(54% + var(--ph-shift));
}
.cr-square .bf-photo {
  height: calc(46% + var(--ph-shift));
}
.bf-stack {
  position: absolute;
  top: calc(50% + var(--ph-shift));
  right: 0;
  bottom: calc(var(--bot) + 120px);
  left: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
}
.bf-stack-full {
  bottom: var(--bot);
}
.cr-square .bf-stack {
  top: calc(40% + var(--ph-shift));
  bottom: var(--bot);
}
.bf-band {
  position: relative;
  padding: 24px var(--pad) 18px;
  background: var(--c2);
  color: #0b0b0b;
}
.bf-badge {
  position: absolute;
  top: -42px;
  left: var(--pad);
  padding: 8px 20px;
  background: #dc2626;
  color: #fff;
  font-size: 26px;
  font-weight: 900;
  text-transform: uppercase;
}
.bf-title {
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.02em;
}
.bf-card {
  display: flex;
  min-height: 0;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 16px;
  margin: 0 var(--pad);
  padding: 30px 34px 30px;
  border-radius: 0 0 30px 30px;
  background: #fff;
  color: #111827;
}
.bf-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.bf-tag {
  flex: none;
  padding: 8px 24px 8px 18px;
  border-radius: 0 16px 16px 0;
  background: var(--c2);
  color: #0b0b0b;
  font-size: 26px;
  font-style: italic;
  font-weight: 900;
}
.bf-pill {
  display: flex;
  align-items: center;
  gap: 0.4em;
  padding: 0.35em 0.85em;
  border-radius: 999px;
  background: #0b0b0b;
  color: #fff;
  font-weight: 800;
}
.bf-pill :deep(svg) {
  width: 1.1em;
  height: 1.1em;
  color: var(--c2);
}
.bf-cols {
  display: flex;
  min-height: 0;
  flex: 1 1 0;
  gap: 24px;
}
.bf-list {
  flex: 1.35 1 0;
}
.bf-list ul {
  display: flex;
  flex-direction: column;
  gap: 0.35em;
  font-weight: 600;
  line-height: 1.2;
}
.bf-list li::before {
  content: "• ";
  font-weight: 900;
}
.bf-when {
  display: flex;
  flex: 1 1 0;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 0.35em;
  text-align: right;
}
.bf-dates {
  padding: 0.25em 0.5em;
  white-space: nowrap;
  background: var(--c2);
  color: #0b0b0b;
  font-size: 0.8em;
  font-weight: 800;
}
.bf-dur {
  color: #dc2626;
  font-weight: 900;
  text-transform: uppercase;
}
.bf-price {
  display: flex;
  min-height: 0;
  flex: 0.85 1 0;
  overflow: hidden;
  border-radius: 22px;
  background: #0b0b0b;
  color: #fff;
  --pz-accent: #fff;
}
.bf-price-fit {
  display: flex;
  flex: 1.5 1 0;
  align-items: center;
  justify-content: center;
  padding: 0.12em 0.2em;
}
.bf-total {
  display: flex;
  flex: 1 1 0;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.15em;
  padding: 0 0.5em;
  background: var(--c2);
  color: #0b0b0b;
  line-height: 1;
  text-align: center;
}
.bf-total small {
  font-size: 0.6em;
  font-weight: 800;
  text-transform: uppercase;
}
.bf-total b {
  font-weight: 900;
}
.bf-fine {
  text-align: right;
}
.bf-foot {
  position: absolute;
  right: var(--pad);
  bottom: var(--bot);
  left: var(--pad);
  z-index: 2;
  display: flex;
  height: 100px;
  align-items: center;
  justify-content: center;
  gap: 30px;
  color: var(--c2);
}
.cr-square .bf-foot {
  display: none;
}
.bf-logo {
  max-height: 112px;
}
.bf-agency {
  width: auto !important;
  font-weight: 900;
}

/*
 * Modelos com foto em cima e faixa de conteúdo embaixo (lista, colagem, mosaico): a faixa tem a
 * altura do próprio conteúdo e a foto ocupa todo o resto. Pouco conteúdo = mais foto, sem bloco
 * vazio sobrando.
 */
.cr-t-benefits,
.cr-t-collage-2,
.cr-t-mosaic-3 {
  display: flex;
  flex-direction: column;
}

/* ================= 10. Lista do que inclui ================= */
.bn-photo {
  position: relative;
  min-height: 30%;
  flex: 1 1 auto;
}
.bn-body {
  position: relative;
  display: flex;
  max-height: 70%;
  flex: none;
  flex-direction: column;
  gap: 18px;
  overflow: hidden;
  padding: 52px var(--pad) var(--bot);
  --pz-accent: var(--c2);
}
.cr-square .bn-body {
  gap: 12px;
  padding-top: 36px;
}
.bn-eyebrow {
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.85;
}
.bn-title {
  font-weight: 900;
  letter-spacing: -0.02em;
}
.bn-list {
  padding-top: 8px;
}
.bn-foot,
.cd-foot {
  display: flex;
  flex: none;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}
.bn-price,
.cd-price {
  width: auto !important;
  min-width: 0;
  flex: 1 1 auto;
}

/* ================= 11. Cartão de vidro ================= */
.cd-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.28), rgba(0, 0, 0, 0) 30%, rgba(0, 0, 0, 0) 50%, rgba(0, 0, 0, 0.35));
}
.cd-card {
  position: absolute;
  right: var(--pad);
  bottom: var(--bot);
  left: var(--pad);
  z-index: 2;
  height: calc(44% - var(--ph-shift));
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-radius: 44px;
  color: #fff;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
  --pz-accent: #fff;
}
.cr-story .cd-card {
  height: calc(36% - var(--ph-shift));
}
.cr-square .cd-card {
  height: calc(58% - var(--ph-shift));
}
/* Cópia da foto do tamanho da arte, alinhada pela base do cartão, desfocada. */
.cd-glass {
  position: absolute;
  bottom: calc(-1 * var(--bot));
  left: calc(-1 * var(--pad));
  width: var(--W);
  height: var(--H);
  filter: blur(26px) saturate(1.25);
}
.cd-card::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 1;
  /* Vidro escurecido: texto branco legível mesmo sobre areia e céu claros. */
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.16), rgba(0, 0, 0, 0.22) 40%, rgba(0, 0, 0, 0.42));
}
.cd-inner {
  position: relative;
  z-index: 2;
  display: flex;
  height: 100%;
  flex-direction: column;
  gap: 14px;
  padding: 46px 52px;
  text-shadow: 0 2px 14px rgba(0, 0, 0, 0.22);
}
.cr-square .cd-inner {
  gap: 10px;
  padding: 36px 44px;
}
.cd-dates {
  padding-left: 0.6em;
  border-left: 0.25em solid var(--c2);
  font-weight: 800;
}
.cd-title {
  display: flex;
  align-items: center;
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -0.02em;
}
.cd-inc {
  font-weight: 600;
  opacity: 0.95;
}
.cd-contact {
  color: rgba(255, 255, 255, 0.92);
}

/* ================= 12 e 13. Colagem e mosaico ================= */
.cl-grid,
.ms-grid {
  position: relative;
  display: grid;
  min-height: 34%;
  flex: 1 1 auto;
  gap: 10px;
  background: #fff;
}
.cl-grid {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}
.cr-story .cl-grid {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr 1fr;
}
.ms-grid {
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  grid-template-rows: 1fr 1fr;
}
.ms-big {
  grid-row: span 2;
}
.cl-band,
.ms-band {
  position: relative;
  display: flex;
  max-height: 60%;
  flex: none;
  align-items: center;
  gap: 32px;
  padding: 44px var(--pad) var(--bot);
}
.cl-text,
.ms-text {
  display: flex;
  min-width: 0;
  flex: 1 1 0;
  flex-direction: column;
  gap: 12px;
}
.cl-eyebrow {
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.85;
}
.cl-title {
  font-weight: 900;
  letter-spacing: -0.02em;
}
.cl-sub {
  font-weight: 600;
  opacity: 0.9;
}
/* Preço e botão empilhados à direita da faixa. */
.cl-aside {
  display: flex;
  width: 36%;
  flex: none;
  flex-direction: column;
  align-items: stretch;
  gap: 18px;
}
.cl-price,
.ms-price {
  padding: 28px 30px;
  border-radius: 28px;
  background: var(--c2);
  color: var(--on2);
}
.cl-cta {
  align-self: center;
}
</style>
