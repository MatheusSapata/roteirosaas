<template>
  <section class="links-section" :style="sectionStyle">
    <div class="links-inner">
      <header v-if="heading || title || subtitle" class="links-header">
        <SectionHeadingChip v-if="heading" :text="heading" :style-type="section.headingLabelStyle || 'outline'" />
        <h2 v-if="title">{{ title }}</h2>
        <p v-if="subtitle">{{ subtitle }}</p>
      </header>

      <div v-if="items.length" class="carousel-shell">
        <button v-if="canGoBack" class="arrow arrow-left" type="button" aria-label="Links anteriores" @click="scroll(-1)">‹</button>
        <div ref="track" class="links-track" :class="{ 'three-columns': items.length >= 3 }" @scroll="updateArrows">
          <article v-for="(item, index) in items" :key="item.id || `${item.url}-${index}`" class="link-card" :style="cardStyle">
            <a class="image-link" :href="item.url" :target="item.openInNewTab === false ? '_self' : '_blank'" rel="noopener noreferrer">
              <template v-if="item.image">
                <img class="image-main" :class="{ 'fit-entire': imageFitsEntire(item, index) }" :src="resolveMediaUrl(item.image)" :alt="localize(item.title)" loading="lazy" @load="detectImageFit(item, index, $event)" />
              </template>
              <div v-else class="image-placeholder">🔗</div>
            </a>
            <div class="card-content">
              <h3>{{ localize(item.title) }}</h3>
              <p v-if="localize(item.description)">{{ localize(item.description) }}</p>
              <a class="card-button" :style="buttonStyle" :href="item.url" :target="item.openInNewTab === false ? '_self' : '_blank'" rel="noopener noreferrer">
                {{ localize(item.buttonLabel) || 'Abrir link' }}
              </a>
            </div>
          </article>
        </div>
        <button v-if="canGoForward" class="arrow arrow-right" type="button" aria-label="Próximos links" @click="scroll(1)">›</button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import type { LinkCardItem, LinksSection } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import { resolveMediaUrl } from "../../utils/media";
import { getReadableTextColor } from "../../utils/colorContrast";
import SectionHeadingChip from "./SectionHeadingChip.vue";

const props = defineProps<{ section: LinksSection }>();
const localize = createLocalizer(getCurrentLanguage());
const track = ref<HTMLElement | null>(null);
const canGoBack = ref(false);
const canGoForward = ref(false);
const entireImageFit = reactive<Record<string, boolean>>({});
const items = computed(() => Array.isArray(props.section.items) ? props.section.items.filter(item => item?.url) : []);
const heading = computed(() => localize(props.section.headingLabel));
const title = computed(() => localize(props.section.title));
const subtitle = computed(() => localize(props.section.subtitle));
const sectionStyle = computed(() => ({ backgroundColor: props.section.backgroundColor || "#ffffff", color: props.section.textColor || "#111827" }));
const cardStyle = computed(() => ({ backgroundColor: props.section.cardBackgroundColor || "#ffffff" }));
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

const updateArrows = () => {
  const el = track.value;
  if (!el) return;
  canGoBack.value = el.scrollLeft > 4;
  canGoForward.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 4;
};
const scroll = (direction: number) => track.value?.scrollBy({ left: direction * Math.max(280, track.value.clientWidth * .78), behavior: "smooth" });
onMounted(() => nextTick(updateArrows));
watch(items, () => nextTick(updateArrows), { deep: true });
</script>

<style scoped>
.links-section{padding:72px 24px}.links-inner{max-width:1180px;margin:auto}.links-header{text-align:center;max-width:760px;margin:0 auto 34px}.links-header h2{font-size:clamp(2rem,4vw,3rem);line-height:1.08;font-weight:800;margin:14px 0 10px}.links-header p{font-size:1.05rem;opacity:.72}.carousel-shell{position:relative;min-width:0}.links-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;padding:6px 0 8px}.links-track::-webkit-scrollbar{display:none}.link-card{flex:0 0 min(390px,100%);min-width:0;height:560px;scroll-snap-align:start;border-radius:24px;overflow:hidden;box-shadow:0 3px 10px rgba(15,23,42,.06);display:flex;flex-direction:column}.three-columns .link-card{flex-basis:calc((100% - 40px)/3)}.image-link{position:relative;display:flex;align-items:flex-start;justify-content:center;flex:0 0 50%;height:50%;min-height:0;background:#f1f5f9;overflow:hidden}.image-main{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}.image-main.fit-entire{object-fit:contain}.image-placeholder{width:100%;height:100%;display:grid;place-items:center;font-size:3rem}.card-content{box-sizing:border-box;height:50%;min-height:0;padding:22px;display:flex;flex:0 0 50%;flex-direction:column;overflow:hidden}.card-content h3{font-size:1.35rem;line-height:1.2;font-weight:800;margin:0 0 10px}.card-content p{line-height:1.55;opacity:.74;margin:0 0 18px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.card-button{margin-top:auto;display:block;padding:13px 18px;text-align:center;border-radius:999px;font-weight:800;text-decoration:none;transition:transform .2s,filter .2s}.card-button:hover{transform:translateY(-1px);filter:brightness(.96)}.arrow{position:absolute;z-index:2;top:45%;width:44px;height:44px;border:0;border-radius:50%;background:#fff;box-shadow:0 6px 20px rgba(15,23,42,.18);font-size:30px;line-height:1;cursor:pointer}.arrow-left{left:-20px}.arrow-right{right:-20px}@media(max-width:700px){.links-section{padding:52px 18px}.link-card,.three-columns .link-card{height:520px;flex-basis:88vw}.arrow{display:none}}
</style>
