<template>
  <V2Section v-if="!isFull" type="photo" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <figure v-if="image" class="v2-photo">
      <img :src="image" :alt="caption" class="v2-reveal" loading="lazy" />
      <figcaption v-if="caption">{{ caption }}</figcaption>
    </figure>
  </V2Section>
  <V2Section v-else type="photo" :background="section.backgroundColor" :anchor-id="section.anchorId" full>
    <figure v-if="image" class="v2-photo v2-photo--full">
      <img :src="image" :alt="caption" class="v2-reveal" loading="lazy" />
      <figcaption v-if="caption">{{ caption }}</figcaption>
    </figure>
  </V2Section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PhotoSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import { text } from "./useHeading";

const props = defineProps<{ section: PhotoSection; previewDevice?: "desktop" | "mobile" }>();
const isFull = computed(() => props.section.layout === "full");
const image = computed(() => resolveMediaUrl(props.section.image) || "");
const caption = computed(() => text(props.section.altText));
</script>

<style scoped>
.v2-photo {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}
.v2-photo img {
  display: block;
  width: 100%;
  max-height: 680px;
  object-fit: cover;
  border-radius: 24px;
}
.v2-photo figcaption {
  font-size: 14px;
  text-align: center;
  color: var(--v2-muted);
}
.v2-photo--full img {
  max-height: 80vh;
  border-radius: 0;
}
.v2-photo--full figcaption {
  padding: 0 20px 16px;
}
</style>
