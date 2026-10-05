<template>
  <V2Section type="featured_video" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" />
    <div class="v2-fv v2-in v2-d3">
      <iframe
        v-if="video"
        :src="video"
        :title="title"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
        loading="lazy"
      ></iframe>
      <p v-else class="v2-fv-empty">{{ copy.empty }}</p>
    </div>
    <div v-if="cta.enabled.value" class="v2-actions">
      <V2Button :attrs="cta.attrs.value">{{ ctaLabel }}</V2Button>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import type { FeaturedVideoSection } from "../../../types/page";
import { normalizeYoutubeEmbedUrl } from "../../../utils/video";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import V2Button from "./V2Button.vue";
import { useCta } from "./useCta";
import { localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: FeaturedVideoSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml } = useHeading(toRef(props, "section"), "featured_video", { pt: "Vídeo em destaque", es: "Video destacado" });
const copy = { empty: localize({ pt: "Adicione um link de vídeo para aparecer aqui.", es: "Agrega un enlace de video para mostrar aquí." }) };
const video = computed(() => normalizeYoutubeEmbedUrl(props.section.videoUrl));
const cta = useCta(toRef(props, "section"));
const ctaLabel = computed(() => text(props.section.ctaLabel) || localize({ pt: "Assistir agora", es: "Ver ahora" }));
</script>

<style scoped>
.v2-fv {
  max-width: 960px;
  margin: 0 auto;
  overflow: hidden;
  border-radius: 24px;
  aspect-ratio: 16 / 9;
  background: var(--v2-card);
  box-shadow: 0 30px 60px -36px rgba(6, 12, 9, 0.55);
}
.v2-fv iframe {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}
.v2-fv-empty {
  display: grid;
  place-items: center;
  height: 100%;
  margin: 0;
  padding: 24px;
  text-align: center;
  color: var(--v2-muted);
}
</style>
