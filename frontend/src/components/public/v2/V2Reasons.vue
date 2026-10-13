<template>
  <V2Section type="reasons" :background="section.backgroundColor" fallback-background="#F2F4F1" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" :align="align" />
    <div
      ref="grid"
      class="v2-reasons v2-flow"
      :class="{ 'is-center': align === 'center', 'is-compact': compact }"
      :style="{ '--v2-cols': columns }"
    >
      <article v-for="(item, idx) in items" :key="idx" class="v2-card v2-reason v2-in" :class="`v2-d${Math.min(idx + 3, 7)}`">
        <span v-if="item.icon" class="v2-reason-icon" aria-hidden="true"><TravelIcon v-if="item.isIcon" :name="item.icon" :size="24" stroke-width="1.8" /><template v-else>{{ item.icon }}</template></span>
        <h3>{{ item.title }}</h3>
        <div v-if="item.descriptionHtml" class="v2-rich" v-html="item.descriptionHtml"></div>
      </article>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, ref, toRef } from "vue";
import type { ReasonsSection } from "../../../types/page";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import TravelIcon from "../../shared/TravelIcon.vue";
import { iconValueName } from "../../../utils/travelIcons";
import { hasText, html, text, useHeading } from "./useHeading";
import { balancedColumns } from "./balancedColumns";
import { useEqualHeights } from "../../../composables/useEqualHeights";

const props = defineProps<{ section: ReasonsSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml, align } = useHeading(toRef(props, "section"), "reasons");
const items = computed(() =>
  (props.section.items || []).map(item => ({
    icon: (item.icon || "").trim(),
    isIcon: !!iconValueName((item.icon || "").trim()),
    title: text(item.title),
    descriptionHtml: hasText(item.description) ? html(item.description) : ""
  }))
);
const columns = computed(() => balancedColumns(items.value.length));
// Nenhum item com descrição: cards mais enxutos (só ícone e título).
const compact = computed(() => items.value.length > 0 && items.value.every(item => !item.descriptionHtml));
// Todos os cards do mesmo tamanho, tenham ou não descrição, em todas as linhas e no celular.
const grid = ref<HTMLElement | null>(null);
useEqualHeights(grid, ".v2-reason", items);
</script>

<style scoped>
.v2-reason {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 26px;
  min-height: var(--equal-h, 0px);
}
/* Nenhum item com descrição: menos respiro, para o card não sobrar em volta do título. */
.is-compact .v2-reason {
  padding: 22px 24px;
}
/* Os cards seguem o alinhamento da seção (um controle só, igual no computador e no celular). */
.is-center .v2-reason {
  align-items: center;
  text-align: center;
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
