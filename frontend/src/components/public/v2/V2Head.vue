<template>
  <header v-if="label || title || subtitleHtml" class="v2-head" :class="`v2-head--${align}`" :style="headStyle">
    <span v-if="label" class="v2-eyebrow v2-in"><span aria-hidden="true"></span>{{ label }}</span>
    <h2 v-if="title" class="v2-title v2-in v2-d1">{{ title }}</h2>
    <div v-if="subtitleHtml" class="v2-lead v2-in v2-d2" v-html="subtitleHtml"></div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { titleScaleFor } from "./useCopyFit";

// frame: largura do conteúdo da seção (ex.: lista de dúvidas), para o título alinhado
// à esquerda começar junto com ele; sem frame, começa na borda da seção.
const props = withDefaults(defineProps<{ label?: string; title?: string; subtitleHtml?: string; align?: "center" | "start"; frame?: string }>(), {
  label: "",
  title: "",
  subtitleHtml: "",
  align: "center",
  frame: ""
});
// Título longo: a letra diminui e o bloco alarga um pouco, em vez de virar muitas linhas.
const headStyle = computed(() => {
  const scale = titleScaleFor(props.title);
  return {
    ...(props.frame ? { "--v2-head-frame": props.frame } : {}),
    ...(scale < 1 ? { "--v2-title-scale": String(scale), "--v2-head-grow": scale < 0.8 ? "160px" : "80px" } : {})
  };
});
</script>
