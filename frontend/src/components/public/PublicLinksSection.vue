<template>
  <section class="links-section" :style="sectionStyle">
    <div class="links-inner">
      <header v-if="heading || title || subtitle" class="links-header">
        <SectionHeadingChip v-if="heading" :text="heading" :style-type="section.headingLabelStyle || 'outline'" />
        <h2 v-if="title">{{ title }}</h2>
        <p v-if="subtitle">{{ subtitle }}</p>
      </header>

      <div v-if="items.length" class="carousel-shell" :class="{ 'no-controls': !carouselEnabled || items.length <= 4 }">
        <button v-if="carouselEnabled && items.length >= 5" class="arrow arrow-left" :style="carouselButtonStyle" type="button" aria-label="Links anteriores" @click="scroll(-1)">‹</button>
        <div ref="track" class="links-track" :class="trackClasses">
          <article v-for="(item, index) in items" :key="item.id || `${item.url}-${index}`" class="link-card" :style="cardStyle">
            <div class="image-link">
              <template v-if="item.image">
                <img class="image-main" :class="{ 'fit-entire': imageFitsEntire(item, index) }" :src="resolveMediaUrl(item.image)" :alt="localize(item.title)" loading="lazy" @load="detectImageFit(item, index, $event)" />
              </template>
              <div v-else class="image-placeholder">🔗</div>
            </div>
            <div class="card-content" :class="{ 'without-details': hasAnyDetails && !hasDates(item) && !hasPrice(item) }">
              <h3>{{ localize(item.title) }}</h3>
              <p v-if="localize(item.description)">{{ localize(item.description) }}</p>
              <div v-if="hasDates(item)" class="card-detail card-dates">
                <div :class="{ 'single-date': !(item.departureDate && item.returnDate) }">
                  <section v-if="item.departureDate" class="date-column">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg>
                    <span><small>Saída</small><strong>{{ formatTravelDate(item.departureDate) }}</strong></span>
                  </section>
                  <section v-if="item.returnDate" class="date-column">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg>
                    <span><small>Retorno</small><strong>{{ formatTravelDate(item.returnDate) }}</strong></span>
                  </section>
                </div>
              </div>
              <div v-if="hasPrice(item)" class="card-detail card-price">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.6 13.6 12 22l-9-9V4h9l8.6 8.6a.7.7 0 0 1 0 1Z"/><circle cx="8" cy="9" r="1.5"/></svg>
                <div class="price-copy">
                  <span v-if="localize(item.pricePrefix)" class="price-affix">{{ localize(item.pricePrefix) }}</span>
                  <strong v-if="item.priceValue" :style="detailAccentStyle">{{ item.priceValue }}</strong>
                  <span v-if="localize(item.priceSuffix)" class="price-affix">{{ localize(item.priceSuffix) }}</span>
                </div>
              </div>
              <a class="card-button hero-cta-shimmer hero-cta-desktop-hover" :style="buttonStyle" :href="item.url" :target="item.openInNewTab === false ? '_self' : '_blank'" rel="noopener noreferrer">
                {{ localize(item.buttonLabel) || 'Abrir link' }}
              </a>
            </div>
          </article>
        </div>
        <button v-if="carouselEnabled && items.length >= 5" class="arrow arrow-right" :style="carouselButtonStyle" type="button" aria-label="Próximos links" @click="scroll(1)">›</button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import type { LinkCardItem, LinksSection } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import { resolveMediaUrl } from "../../utils/media";
import { getReadableTextColor, normalizeHexColor } from "../../utils/colorContrast";
import SectionHeadingChip from "./SectionHeadingChip.vue";

const props = defineProps<{ section: LinksSection }>();
const localize = createLocalizer(getCurrentLanguage());
const track = ref<HTMLElement | null>(null);
const entireImageFit = reactive<Record<string, boolean>>({});
const items = computed(() => Array.isArray(props.section.items) ? props.section.items.filter(item => item?.url) : []);
const hasAnyDetails = computed(() => items.value.some(item => hasDates(item) || hasPrice(item)));
const carouselEnabled = computed(() => props.section.carouselEnabled !== false);
const trackClasses = computed(() => ({
  centered: carouselEnabled.value && items.value.length <= 4,
  "three-columns": carouselEnabled.value && items.value.length === 3,
  "four-columns": carouselEnabled.value && items.value.length >= 4,
  "grid-mode": !carouselEnabled.value,
  "grid-three": !carouselEnabled.value && (items.value.length === 3 || (items.value.length >= 5 && items.value.length <= 6)),
  "grid-four": !carouselEnabled.value && (items.value.length === 4 || items.value.length >= 7)
}));
const heading = computed(() => localize(props.section.headingLabel));
const title = computed(() => localize(props.section.title));
const subtitle = computed(() => localize(props.section.subtitle));
const sectionStyle = computed(() => ({ backgroundColor: props.section.backgroundColor || "#ffffff", color: props.section.textColor || "#111827" }));
const mixWithWhite = (value:string, amount=.1) => {
  const hex=normalizeHexColor(value) || "#ffffff";
  const channels=[1,3,5].map(index => parseInt(hex.slice(index,index+2),16));
  const mixed=channels.map(channel => Math.round(channel+(255-channel)*amount).toString(16).padStart(2,"0"));
  return `#${mixed.join("")}`;
};
const surfaceColor = computed(() => mixWithWhite(props.section.backgroundColor || "#ffffff",.1));
const surfaceTextColor = computed(() => getReadableTextColor(surfaceColor.value));
const cardStyle = computed(() => ({ backgroundColor:surfaceColor.value, color:surfaceTextColor.value }));
const carouselButtonStyle = computed(() => ({ backgroundColor:surfaceColor.value, color:surfaceTextColor.value }));
const buttonStyle = computed(() => {
  const backgroundColor = props.section.buttonColor || "#6df56d";
  return { backgroundColor, color: getReadableTextColor(backgroundColor) };
});
const detailAccentStyle = computed(() => ({ color: props.section.buttonColor || "#6df56d" }));
const hasDates = (item:LinkCardItem) => item.showDates === true && !!(item.departureDate || item.returnDate);
const hasPrice = (item:LinkCardItem) => item.showPrice === true && !!(localize(item.pricePrefix) || item.priceValue || localize(item.priceSuffix));
const formatTravelDate = (value?:string) => {
  if (!value) return "";
  const match=value.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) return `${match[3]}/${match[2]}/${match[1]}`;
  const parsed=new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString("pt-BR");
};
const imageKey = (item:LinkCardItem, index:number) => item.id || `${item.url}-${index}`;
const imageFitsEntire = (item:LinkCardItem, index:number) => entireImageFit[imageKey(item,index)] === true;
const detectImageFit = (item:LinkCardItem, index:number, event:Event) => {
  const image=event.target as HTMLImageElement;
  if(!image.naturalWidth || !image.naturalHeight)return;
  const imageRatio=image.naturalWidth/image.naturalHeight;
  const targetRatio=16/9;
  const ratioDifference=Math.abs(imageRatio-targetRatio)/targetRatio;
  entireImageFit[imageKey(item,index)]=ratioDifference <= .02;
};

const scroll = (direction: number) => {
  const el=track.value;
  if(!el)return;
  const firstCard=el.querySelector<HTMLElement>(".link-card");
  const step=(firstCard?.offsetWidth || Math.max(280,el.clientWidth*.78))+20;
  const maxScroll=Math.max(0,el.scrollWidth-el.clientWidth);
  const atStart=el.scrollLeft <= 4;
  const atEnd=el.scrollLeft >= maxScroll-4;
  if(direction < 0 && atStart){ el.scrollTo({left:maxScroll,behavior:"smooth"}); return; }
  if(direction > 0 && atEnd){ el.scrollTo({left:0,behavior:"smooth"}); return; }
  el.scrollBy({left:direction*step,behavior:"smooth"});
};
</script>

<style scoped>
.links-section{padding:72px 24px}.links-inner{max-width:1180px;margin:auto}.links-header{text-align:center;max-width:760px;margin:0 auto 34px}.links-header h2{font-size:clamp(2rem,4vw,3rem);line-height:1.08;font-weight:800;margin:14px 0 10px}.links-header p{font-size:1.05rem;opacity:.72}.carousel-shell{position:relative;min-width:0;padding:0 56px}.links-track{display:flex;align-items:stretch;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;padding:6px 0 8px;-webkit-overflow-scrolling:touch;touch-action:pan-x}.links-track::-webkit-scrollbar{display:none}.link-card{flex:0 0 min(390px,100%);min-width:0;scroll-snap-align:start;border-radius:24px;overflow:hidden;box-shadow:0 3px 10px rgba(15,23,42,.06);display:grid;grid-template-rows:auto 1fr}.three-columns .link-card{flex-basis:calc((100% - 40px)/3)}.four-columns .link-card{flex-basis:calc((100% - 60px)/4)}.image-link{position:relative;display:flex;align-items:flex-start;justify-content:center;width:100%;aspect-ratio:16/9;background:#f1f5f9;overflow:hidden}.image-main{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}.image-main.fit-entire{object-fit:contain}.image-placeholder{width:100%;height:100%;display:grid;place-items:center;font-size:3rem}.card-content{box-sizing:border-box;min-height:0;padding:22px;display:flex;flex-direction:column;overflow:hidden}.card-content h3{font-size:1.35rem;line-height:1.2;font-weight:800;margin:0 0 10px}.card-content p{line-height:1.55;opacity:.74;margin:0 0 18px;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}.card-detail{display:flex;align-items:center;gap:11px;margin-top:0;padding:11px 12px;border-radius:13px;background:rgba(127,127,127,.09)}.card-detail+.card-detail{margin-top:10px}.card-detail:last-of-type{margin-bottom:14px}.card-detail>svg{flex:0 0 20px;width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;opacity:.8}.card-dates>div{display:flex;flex-wrap:wrap;gap:8px 18px}.card-dates span{display:flex;flex-direction:column;font-size:.85rem;font-weight:750;line-height:1.2}.card-dates small{margin-bottom:4px;font-size:.66rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;opacity:.6}.price-copy{display:flex;min-width:0;align-items:baseline;flex-wrap:wrap;gap:3px 6px}.price-copy strong{font-size:1.18rem;line-height:1.1}.price-affix{font-size:.78rem;opacity:.7}.card-button{margin-top:auto;padding:13px 18px;text-align:center;border-radius:999px;font-weight:800;text-decoration:none;transition:transform .2s,filter .2s}.card-button:hover{transform:translateY(-1px);filter:brightness(.96)}.arrow{position:absolute;z-index:2;top:50%;transform:translateY(-50%);width:44px;height:44px;border:0;border-radius:50%;background:#fff;box-shadow:0 6px 20px rgba(15,23,42,.18);font-size:30px;line-height:1;cursor:pointer}.arrow-left{left:0}.arrow-right{right:0}@media(max-width:700px){.links-section{padding:52px 18px}.carousel-shell{padding:0}.card-content{padding:22px 20px 20px}.link-card,.three-columns .link-card,.four-columns .link-card{flex-basis:calc(83.333% - 16.667px);grid-template-rows:auto 1fr}.arrow{display:none}}
@media(min-width:701px) and (max-width:1023px){.three-columns .link-card,.four-columns .link-card{flex-basis:calc((100% - 20px)/2)}}
.image-link{align-items:flex-start}
.card-content.without-details>p{margin-top:auto;margin-bottom:auto}
.card-dates{display:block}.card-dates>div{display:grid;width:100%;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card-dates>div.single-date{grid-template-columns:1fr}.date-column{display:flex;min-width:0;align-items:center;gap:9px}.date-column>svg{flex:0 0 19px;width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;opacity:.8}.date-column>span{display:flex;min-width:0;flex-direction:column;line-height:1.2}.date-column small{margin-bottom:4px;font-size:.66rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;opacity:.6}.date-column strong{font-size:.85rem;white-space:nowrap}.single-date .date-column strong{font-size:1rem}.single-date .date-column>svg{width:21px;height:21px;flex-basis:21px}
.single-date .date-column>span{flex-direction:row;align-items:baseline;gap:8px}.single-date .date-column small{margin-bottom:0;font-size:.72rem}.single-date .date-column strong{font-size:1rem}
.price-copy{row-gap:1px;line-height:1.15}.price-affix{line-height:1.15}
.carousel-shell.no-controls{padding-left:0;padding-right:0}@media(min-width:1024px){.links-track.centered{justify-content:center;overflow-x:hidden}}
.links-track.grid-mode{display:flex;flex-wrap:wrap;justify-content:center;overflow:visible;scroll-snap-type:none}.grid-mode .link-card{flex-basis:min(390px,100%)}.grid-mode.grid-three .link-card{flex-basis:calc((100% - 40px)/3)}.grid-mode.grid-four .link-card{flex-basis:calc((100% - 60px)/4)}@media(max-width:1023px){.grid-mode.grid-three .link-card,.grid-mode.grid-four .link-card{flex-basis:calc((100% - 20px)/2)}}@media(max-width:700px){.links-track.grid-mode{gap:14px}.grid-mode .link-card,.grid-mode.grid-three .link-card,.grid-mode.grid-four .link-card{flex-basis:100%}}
</style>
