<template>
  <V2Section type="reasons" :background="section.backgroundColor" fallback-background="#F2F4F1" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" />
    <div class="v2-reasons">
      <article v-for="(item, idx) in items" :key="idx" class="v2-card v2-reason v2-in" :class="`v2-d${Math.min(idx + 3, 7)}`">
        <span class="v2-reason-icon" aria-hidden="true">{{ item.icon || "★" }}</span>
        <h3>{{ item.title }}</h3>
        <div v-if="item.descriptionHtml" class="v2-rich" v-html="item.descriptionHtml"></div>
      </article>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import type { ReasonsSection } from "../../../types/page";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import { html, text, useHeading } from "./useHeading";

const props = defineProps<{ section: ReasonsSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml } = useHeading(toRef(props, "section"), "reasons", { pt: "Motivos para escolher", es: "Motivos para elegir" });
const items = computed(() =>
  (props.section.items || []).map(item => ({
    icon: (item.icon || "").trim(),
    title: text(item.title),
    descriptionHtml: text(item.description) ? html(item.description) : ""
  }))
);
</script>

<style scoped>
.v2-reasons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));
  gap: 16px;
}
.v2-reason {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 26px;
}
.v2-reason-icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  font-size: 22px;
  transform: rotate(-4deg);
}
.v2-reason h3 {
  margin: 0;
  font-size: 19px;
  font-weight: 700;
}
.v2-reason .v2-rich {
  color: var(--v2-muted);
  line-height: 1.55;
}
</style>
