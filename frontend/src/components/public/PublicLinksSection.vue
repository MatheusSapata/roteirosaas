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
        <div ref="track" class="links-track" @scroll="updateArrows">
          <article v-for="(item, index) in items" :key="item.id || `${item.url}-${index}`" class="link-card" :style="cardStyle">
            <a class="image-link" :href="item.url" :target="item.openInNewTab === false ? '_self' : '_blank'" rel="noopener noreferrer">
              <img v-if="item.image" :src="resolveMediaUrl(item.image)" :alt="localize(item.title)" loading="lazy" />
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
import { computed, nextTick, onMounted, ref, watch } from "vue";
import type { LinksSection } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import { resolveMediaUrl } from "../../utils/media";
import SectionHeadingChip from "./SectionHeadingChip.vue";

const props = defineProps<{ section: LinksSection }>();
const localize = createLocalizer(getCurrentLanguage());
const track = ref<HTMLElement | null>(null);
const canGoBack = ref(false);
const canGoForward = ref(false);
const items = computed(() => Array.isArray(props.section.items) ? props.section.items.filter(item => item?.url) : []);
const heading = computed(() => localize(props.section.headingLabel));
const title = computed(() => localize(props.section.title));
const subtitle = computed(() => localize(props.section.subtitle));
const sectionStyle = computed(() => ({ backgroundColor: props.section.backgroundColor || "#f8fafc", color: props.section.textColor || "#111827" }));
const cardStyle = computed(() => ({ backgroundColor: props.section.cardBackgroundColor || "#ffffff" }));
const buttonStyle = computed(() => ({ backgroundColor: props.section.buttonColor || "#6df56d", color: props.section.buttonTextColor || "#071107" }));

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
.links-section{padding:72px 24px}.links-inner{max-width:1180px;margin:auto}.links-header{text-align:center;max-width:760px;margin:0 auto 34px}.links-header h2{font-size:clamp(2rem,4vw,3rem);line-height:1.08;font-weight:800;margin:14px 0 10px}.links-header p{font-size:1.05rem;opacity:.72}.carousel-shell{position:relative}.links-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;padding:6px 2px 18px}.links-track::-webkit-scrollbar{display:none}.link-card{flex:0 0 min(390px,85vw);scroll-snap-align:start;border-radius:24px;overflow:hidden;box-shadow:0 14px 36px rgba(15,23,42,.11);display:flex;flex-direction:column}.image-link{display:block;aspect-ratio:16/9;background:#e2e8f0}.image-link img{width:100%;height:100%;object-fit:cover}.image-placeholder{height:100%;display:grid;place-items:center;font-size:3rem}.card-content{padding:22px;display:flex;flex:1;flex-direction:column}.card-content h3{font-size:1.35rem;line-height:1.2;font-weight:800;margin:0 0 10px}.card-content p{line-height:1.55;opacity:.74;margin:0 0 22px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.card-button{margin-top:auto;display:block;padding:13px 18px;text-align:center;border-radius:999px;font-weight:800;text-decoration:none;transition:transform .2s,filter .2s}.card-button:hover{transform:translateY(-1px);filter:brightness(.96)}.arrow{position:absolute;z-index:2;top:45%;width:44px;height:44px;border:0;border-radius:50%;background:#fff;box-shadow:0 6px 20px rgba(15,23,42,.18);font-size:30px;line-height:1;cursor:pointer}.arrow-left{left:-20px}.arrow-right{right:-20px}@media(max-width:700px){.links-section{padding:52px 18px}.link-card{flex-basis:88vw}.arrow{display:none}}
</style>
