<template>
  <V2Section type="faq" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" :align="align" :frame="isSplit ? '' : '820px'" />
    <div class="v2-faq" :class="{ 'v2-faq--split': isSplit }">
      <div v-for="(item, idx) in items" :key="idx" class="v2-faq-item v2-card v2-in" :class="[`v2-d${Math.min(idx + 3, 7)}`, { 'is-open': openIndex === idx }]">
        <button type="button" class="v2-faq-q" :aria-expanded="openIndex === idx" @click="toggle(idx)">
          <span>{{ item.question }}</span>
          <span class="v2-faq-sign" aria-hidden="true">{{ openIndex === idx ? "−" : "+" }}</span>
        </button>
        <div v-show="openIndex === idx" class="v2-faq-a v2-rich" v-html="item.answerHtml"></div>
      </div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, ref, toRef } from "vue";
import type { FaqSection } from "../../../types/page";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import { html, text, useHeading } from "./useHeading";

const props = defineProps<{ section: FaqSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml, align } = useHeading(toRef(props, "section"), "faq");
const isSplit = computed(() => props.section.layout === "split");
const items = computed(() => (props.section.items || []).map(item => ({ question: text(item.question), answerHtml: html(item.answer) })));
const openIndex = ref<number | null>(0);
const toggle = (idx: number) => {
  openIndex.value = openIndex.value === idx ? null : idx;
};
</script>

<style scoped>
.v2-faq {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 820px;
  margin: 0 auto;
}
.v2-faq--split {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr));
  align-items: start;
  max-width: none;
}
.v2-faq-item {
  border-radius: 18px;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px transparent;
  transition: box-shadow 0.2s ease;
}
.v2-faq-item.is-open {
  box-shadow: inset 0 0 0 1.5px var(--v2-accent);
}
.v2-faq-q {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  min-height: 64px;
  padding: 16px 20px;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  font-size: 17px;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}
.v2-faq-sign {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
  font-size: 20px;
  font-weight: 700;
}
.is-open .v2-faq-sign {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.v2-faq-a {
  padding: 0 20px 20px;
  color: var(--v2-muted);
}
</style>
