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
            <div class="card-content">
              <h3>{{ localize(item.title) }}</h3>
              <p v-if="localize(item.description)">{{ localize(item.description) }}</p>
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
const imageKey = (item:LinkCardItem, index:number) => item.id || `${item.url}-${index}`;
const imageFitsEntire = (item:LinkCardItem, index:number) => entireImageFit[imageKey(item,index)] === true;
const detectImageFit = (item:LinkCardItem, index:number, event:Event) => {
  const image=event.target as HTMLImageElement;
  const frame=image.parentElement;
  if(!image.naturalWidth || !image.naturalHeight || !frame)return;
  const imageRatio=image.naturalWidth/image.naturalHeight;
  const frameRatio=frame.clientWidth/frame.clientHeight;
  entireImageFit[imageKey(item,index)]=imageRatio <= frameRatio * 1.1;
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
.links-section{padding:72px 24px}.links-inner{max-width:1180px;margin:auto}.links-header{text-align:center;max-width:760px;margin:0 auto 34px}.links-header h2{font-size:clamp(2rem,4vw,3rem);line-height:1.08;font-weight:800;margin:14px 0 10px}.links-header p{font-size:1.05rem;opacity:.72}.carousel-shell{position:relative;min-width:0;padding:0 56px}.links-track{display:flex;align-items:stretch;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;padding:6px 0 8px;-webkit-overflow-scrolling:touch;touch-action:pan-x}.links-track::-webkit-scrollbar{display:none}.link-card{flex:0 0 min(390px,100%);min-width:0;scroll-snap-align:start;border-radius:24px;overflow:hidden;box-shadow:0 3px 10px rgba(15,23,42,.06);display:grid;grid-template-rows:auto 1fr}.three-columns .link-card{flex-basis:calc((100% - 40px)/3)}.four-columns .link-card{flex-basis:calc((100% - 60px)/4)}.image-link{position:relative;display:flex;align-items:flex-start;justify-content:center;width:100%;aspect-ratio:16/9;background:#f1f5f9;overflow:hidden}.image-main{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}.image-main.fit-entire{object-fit:contain}.image-placeholder{width:100%;height:100%;display:grid;place-items:center;font-size:3rem}.card-content{box-sizing:border-box;min-height:0;padding:22px;display:flex;flex-direction:column;overflow:hidden}.card-content h3{font-size:1.35rem;line-height:1.2;font-weight:800;margin:0 0 10px}.card-content p{line-height:1.55;opacity:.74;margin:0 0 10px;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}.card-button{margin-top:auto;display:block;padding:13px 18px;text-align:center;border-radius:999px;font-weight:800;text-decoration:none;transition:transform .2s,filter .2s}.card-button:hover{transform:translateY(-1px);filter:brightness(.96)}.arrow{position:absolute;z-index:2;top:50%;transform:translateY(-50%);width:44px;height:44px;border:0;border-radius:50%;background:#fff;box-shadow:0 6px 20px rgba(15,23,42,.18);font-size:30px;line-height:1;cursor:pointer}.arrow-left{left:0}.arrow-right{right:0}@media(max-width:700px){.links-section{padding:52px 18px}.carousel-shell{padding:0}.link-card,.three-columns .link-card,.four-columns .link-card{flex-basis:calc(83.333% - 16.667px);grid-template-rows:auto 1fr}.arrow{display:none}}
@media(min-width:701px) and (max-width:1023px){.three-columns .link-card,.four-columns .link-card{flex-basis:calc((100% - 20px)/2)}}
.carousel-shell.no-controls{padding-left:0;padding-right:0}@media(min-width:1024px){.links-track.centered{justify-content:center;overflow-x:hidden}}
.links-track.grid-mode{display:flex;flex-wrap:wrap;justify-content:center;overflow:visible;scroll-snap-type:none}.grid-mode .link-card{flex-basis:min(390px,100%)}.grid-mode.grid-three .link-card{flex-basis:calc((100% - 40px)/3)}.grid-mode.grid-four .link-card{flex-basis:calc((100% - 60px)/4)}@media(max-width:1023px){.grid-mode.grid-three .link-card,.grid-mode.grid-four .link-card{flex-basis:calc((100% - 20px)/2)}}@media(max-width:700px){.links-track.grid-mode{gap:14px}.grid-mode .link-card,.grid-mode.grid-three .link-card,.grid-mode.grid-four .link-card{flex-basis:100%}}
</style>
