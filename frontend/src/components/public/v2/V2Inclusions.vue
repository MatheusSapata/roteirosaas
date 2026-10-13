<template>
  <V2Section type="inclusions" :background="section.backgroundColor" fallback-background="#FFFFFF" :anchor-id="section.anchorId">
    <template #default="{ tone }">
      <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" :align="align" />
      <div class="v2-inc" :class="{ 'is-dark': tone.dark, 'is-single': !excluded.length || !included.length }">
        <article v-if="included.length" class="v2-card v2-inc-card v2-in v2-d3">
          <header class="v2-inc-head">
            <span class="v2-inc-tile" aria-hidden="true"><CheckIcon :size="24" :stroke-width="2.4" /></span>
            <h3>{{ includedTitle }}</h3>
          </header>
          <ul class="v2-inc-list">
            <li v-for="(item, idx) in included" :key="idx">
              <span class="v2-inc-mark" aria-hidden="true"><CheckIcon :size="14" :stroke-width="3" /></span>
              <div>
                <span>{{ item.title }}</span>
                <ul v-if="item.details.length" class="v2-inc-sub">
                  <li v-for="(line, i) in item.details" :key="i">{{ line }}</li>
                </ul>
              </div>
            </li>
          </ul>
        </article>
        <article v-if="excluded.length" class="v2-card v2-inc-card is-no v2-in v2-d4">
          <header class="v2-inc-head">
            <span class="v2-inc-tile" aria-hidden="true"><XIcon :size="24" :stroke-width="2.4" /></span>
            <h3>{{ excludedTitle }}</h3>
          </header>
          <ul class="v2-inc-list">
            <li v-for="(item, idx) in excluded" :key="idx">
              <span class="v2-inc-mark" aria-hidden="true"><XIcon :size="14" :stroke-width="3" /></span>
              <div>
                <span>{{ item.title }}</span>
                <ul v-if="item.details.length" class="v2-inc-sub">
                  <li v-for="(line, i) in item.details" :key="i">{{ line }}</li>
                </ul>
              </div>
            </li>
          </ul>
        </article>
      </div>
    </template>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import { CheckIcon, XIcon } from "lucide-vue-next";
import type { InclusionItem, InclusionsSection } from "../../../types/page";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import { text, useHeading } from "./useHeading";

const props = defineProps<{ section: InclusionsSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml, align } = useHeading(toRef(props, "section"), "inclusions");

// Cada linha de "details" vira um subitem; linhas vazias somem.
const normalize = (items?: InclusionItem[]) =>
  (items || [])
    .map(item => ({
      title: text(item.title),
      details: text(item.details)
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(Boolean)
    }))
    .filter(item => item.title);

const included = computed(() => normalize(props.section.included));
const excluded = computed(() => normalize(props.section.excluded));
const includedTitle = computed(() => text(props.section.includedTitle) || "Seu pacote inclui");
const excludedTitle = computed(() => text(props.section.excludedTitle) || "Não inclui");
</script>

<style scoped>
.v2-inc {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
  gap: 16px;
  max-width: 1000px;
  margin: 0 auto;
}
.v2-inc.is-single {
  grid-template-columns: minmax(0, 1fr);
  max-width: 560px;
}
@container (max-width: 700px) {
  .v2-inc {
    grid-template-columns: minmax(0, 1fr);
  }
}
.v2-inc-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
  padding: 26px;
}
@container (max-width: 560px) {
  .v2-inc-card {
    padding: 22px 20px;
  }
}
.v2-inc-head {
  display: flex;
  align-items: center;
  gap: 14px;
}
.v2-inc-head h3 {
  margin: 0;
  font-size: 19px;
  font-weight: 700;
}
.v2-inc-tile {
  display: grid;
  place-items: center;
  flex: none;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  transform: rotate(-4deg);
}
.is-no .v2-inc-tile {
  background: var(--v2-ink);
  color: var(--v2-bg);
}
.v2-inc-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.v2-inc-list > li {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr);
  gap: 12px;
  font-size: 16px;
  line-height: 1.4;
  overflow-wrap: anywhere;
}
.v2-inc-list > li > div > span {
  font-weight: 600;
}
.is-no .v2-inc-list > li > div > span {
  font-weight: 500;
  color: var(--v2-muted);
}
.v2-inc-mark {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
}
.is-no .v2-inc-mark {
  background: rgba(214, 69, 69, 0.14);
  color: #d64545;
}
.is-dark .is-no .v2-inc-mark {
  background: rgba(240, 129, 123, 0.18);
  color: #f0817b;
}
.v2-inc-sub {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  font-size: 14.5px;
  color: var(--v2-muted);
}
.v2-inc-sub li {
  position: relative;
  padding-left: 14px;
}
.v2-inc-sub li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.62em;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--v2-accent);
}
</style>
