<template>
  <RouterLink :to="`/admin/ajuda/${article.id}`" class="hac">
    <span v-if="showModule" class="hac-module">{{ getModule(article.modulo).titulo }}</span>
    <b class="hac-title">{{ article.titulo }}</b>
    <span class="hac-text">{{ article.resumo }}</span>
    <span class="hac-tags">
      <span v-if="tour" class="hac-tag is-demo"><MousePointerClickIcon aria-hidden="true" />Interativo</span>
      <span v-if="tour?.video" class="hac-tag"><PlayIcon aria-hidden="true" />Vídeo</span>
      <span class="hac-tag is-date">Atualizado em {{ formatDate(article.atualizado) }}</span>
    </span>
  </RouterLink>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { MousePointerClickIcon, PlayIcon } from "lucide-vue-next";
import { formatDate, getModule, type HelpArticle } from "../../help";
import { getTour } from "../../help/media";

const props = defineProps<{ article: HelpArticle; showModule?: boolean }>();
const tour = computed(() => getTour(props.article.demo || props.article.id));
</script>

<style scoped>
.hac { display: flex; flex-direction: column; gap: 6px; padding: 16px; border-radius: 18px; background: var(--card); box-shadow: var(--shadow-card); color: var(--foreground); text-decoration: none; transition: transform 0.2s ease, box-shadow 0.2s ease; }
.hac:hover { transform: translateY(-2px); box-shadow: var(--shadow-card), 0 0 0 1px color-mix(in srgb, var(--primary) 35%, transparent); }
.hac:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; }
.hac-module { font-size: 11.5px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: var(--primary); }
.hac-title { font-size: 15px; font-weight: 700; }
.hac-text { font-size: 13.5px; line-height: 1.5; color: var(--muted-foreground); }
.hac-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: auto; padding-top: 6px; }
.hac-tag { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 999px; background: var(--muted); font-size: 11.5px; font-weight: 600; color: var(--muted-foreground); }
.hac-tag svg { width: 12px; height: 12px; }
.hac-tag.is-demo { background: color-mix(in srgb, var(--primary) 12%, var(--card)); color: var(--primary); }
.hac-tag.is-date { background: transparent; padding-left: 0; font-weight: 500; }
</style>
