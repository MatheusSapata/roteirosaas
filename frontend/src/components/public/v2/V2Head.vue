<template>
  <header v-if="label || title || subtitleHtml" class="v2-head" :class="`v2-head--${align}`">
    <span v-if="label" class="v2-eyebrow v2-in"><span aria-hidden="true"></span>{{ label }}</span>
    <h2 v-if="title" class="v2-title v2-in v2-d1">{{ title }}</h2>
    <div v-if="subtitleHtml" class="v2-lead v2-in v2-d2" v-html="subtitleHtml"></div>
  </header>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ label?: string; title?: string; subtitleHtml?: string; align?: "center" | "start" }>(), {
  label: "",
  title: "",
  subtitleHtml: "",
  align: "center"
});
</script>
