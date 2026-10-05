<template>
  <V2Section type="story" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <div class="v2-story" :class="{ 'is-left': imageLeft }">
      <div class="v2-story-copy">
        <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" align="start" />
        <div v-if="cta.enabled.value" class="v2-in v2-d3">
          <V2Button :attrs="cta.attrs.value">{{ ctaLabel }}</V2Button>
        </div>
      </div>
      <div v-if="media.length" class="v2-story-media v2-in v2-d2">
        <div class="v2-story-stage">
          <template v-for="(item, idx) in media" :key="item.url">
            <iframe
              v-if="item.type === 'video' && idx === active"
              :src="item.url"
              :title="copy.video"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen
              loading="lazy"
            ></iframe>
            <img v-else-if="idx === active" :src="item.url" :alt="copy.image" />
          </template>
          <span v-if="media.length > 1" class="v2-story-count">{{ active + 1 }} / {{ media.length }}</span>
          <div v-if="media.length > 1" class="v2-story-nav">
            <button type="button" :aria-label="copy.prev" @click="go(active - 1)">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6" /></svg>
            </button>
            <button type="button" :aria-label="copy.next" @click="go(active + 1)">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
            </button>
          </div>
        </div>
        <div v-if="media.length > 1" class="v2-story-thumbs">
          <button
            v-for="(item, idx) in media"
            :key="`t-${item.url}`"
            type="button"
            :aria-label="`${copy.show} ${idx + 1}`"
            :aria-current="idx === active"
            :class="{ 'is-on': idx === active }"
            @click="go(idx)"
          >
            <img v-if="item.thumb" :src="item.thumb" alt="" loading="lazy" />
            <span v-else class="v2-story-vthumb" aria-hidden="true">▶</span>
          </button>
        </div>
      </div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, ref, toRef, watch } from "vue";
import type { StorySection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import { extractYoutubeId, normalizeYoutubeEmbedUrl } from "../../../utils/video";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import V2Button from "./V2Button.vue";
import { useCta } from "./useCta";
import { localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: StorySection; previewDevice?: "desktop" | "mobile" }>();
const section = toRef(props, "section");
const heading = useHeading(
  computed(() => ({ ...props.section, headingLabel: props.section.headingLabel ?? (text(props.section.badge) || undefined) })),
  "story",
  { pt: "Nossa história", es: "Nuestra historia" }
);
const { label, title, subtitleHtml } = heading;
const copy = {
  video: localize({ pt: "Vídeo", es: "Video" }),
  image: localize({ pt: "Foto da viagem", es: "Foto del viaje" }),
  prev: localize({ pt: "Foto anterior", es: "Foto anterior" }),
  next: localize({ pt: "Próxima foto", es: "Siguiente foto" }),
  show: localize({ pt: "Mostrar mídia", es: "Mostrar medio" })
};
const imageLeft = computed(() => props.section.imagePosition === "left");
const media = computed(() => {
  const videos = [...(Array.isArray(props.section.videoUrls) ? props.section.videoUrls : [])];
  const single = (props.section.videoUrl || "").trim();
  if (single && !videos.includes(single)) videos.unshift(single);
  const videoItems = videos
    .map(url => (typeof url === "string" ? url.trim() : ""))
    .filter(Boolean)
    .map(url => {
      const embed = normalizeYoutubeEmbedUrl(url);
      const id = extractYoutubeId(url);
      return embed ? { type: "video" as const, url: embed, thumb: id ? `https://img.youtube.com/vi/${id}/hqdefault.jpg` : "" } : null;
    })
    .filter((item): item is { type: "video"; url: string; thumb: string } => !!item);
  const images = (props.section.images || [])
    .map(img => resolveMediaUrl(img) || img)
    .filter(Boolean)
    .map(url => ({ type: "image" as const, url, thumb: url }));
  return [...videoItems, ...images];
});
const active = ref(0);
const go = (idx: number) => {
  const total = media.value.length;
  if (!total) return;
  active.value = ((idx % total) + total) % total;
};
watch(() => media.value.length, () => go(Math.min(active.value, Math.max(0, media.value.length - 1))));
const cta = useCta(section);
const ctaLabel = computed(() => text(props.section.ctaLabel) || localize({ pt: "Saiba mais", es: "Saber más" }));
</script>

<style scoped>
.v2-story {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: clamp(28px, 5cqi, 64px);
}
.v2-story.is-left {
  flex-direction: row-reverse;
}
.v2-story-copy {
  flex: 1 1 380px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.v2-story-copy :deep(.v2-head) {
  margin-bottom: 20px;
}
.v2-story-media {
  flex: 1 1 420px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.v2-story-stage {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  background: var(--v2-card);
  aspect-ratio: 4 / 4.2;
  max-height: 560px;
}
.v2-story-stage img,
.v2-story-stage iframe {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
  object-fit: cover;
}
.v2-story-count {
  position: absolute;
  top: 14px;
  left: 14px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(8, 14, 11, 0.6);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.v2-story-nav {
  position: absolute;
  right: 14px;
  bottom: 14px;
  display: flex;
  gap: 8px;
}
.v2-story-nav button {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: #0f1713;
  cursor: pointer;
}
.v2-story-thumbs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 2px 2px 6px;
  scrollbar-width: thin;
}
.v2-story-thumbs button {
  flex: 0 0 72px;
  height: 54px;
  padding: 0;
  overflow: hidden;
  border: 0;
  border-radius: 10px;
  background: var(--v2-card);
  opacity: 0.6;
  cursor: pointer;
  transition: opacity 0.2s ease, box-shadow 0.2s ease;
}
.v2-story-thumbs button.is-on {
  opacity: 1;
  box-shadow: 0 0 0 2px var(--v2-bg), 0 0 0 4px var(--v2-accent);
}
.v2-story-thumbs img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.v2-story-vthumb {
  display: grid;
  place-items: center;
  height: 100%;
  color: var(--v2-ink);
}
</style>
