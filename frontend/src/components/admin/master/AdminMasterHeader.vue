<template>
  <header class="am-head">
    <div class="min-w-0">
      <p class="am-eyebrow">{{ eyebrowText }}</p>
      <h1 class="am-title">{{ title }}</h1>
      <p v-if="subtitle" class="am-sub">{{ subtitle }}</p>
    </div>
    <div class="am-actions"><slot /></div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { adminMasterGroupOf } from "./nav";

const props = withDefaults(defineProps<{ title: string; subtitle?: string; eyebrow?: string }>(), {
  subtitle: "",
  eyebrow: ""
});

const route = useRoute();
const eyebrowText = computed(() => {
  if (props.eyebrow) return props.eyebrow;
  const group = adminMasterGroupOf(route.path);
  return group ? `Admin master · ${group}` : "Admin master";
});
</script>
