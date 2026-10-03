<template>
  <article class="am-kpi">
    <p class="am-kpi-label">
      <span class="am-tile" :class="`am-tone-${tone}`"><AmIcon :name="icon" /></span>
      {{ label }}
    </p>
    <p class="am-kpi-value"><slot name="value">{{ value }}</slot></p>
    <p v-if="hint || $slots.hint" class="am-kpi-hint"><slot name="hint">{{ hint }}</slot></p>
  </article>
</template>

<script setup lang="ts">
import AmIcon from "./AmIcon.vue";

withDefaults(
  defineProps<{
    icon: string;
    label: string;
    value?: string | number;
    hint?: string;
    tone?: "success" | "warning" | "info" | "danger" | "neutral" | "violet";
  }>(),
  { value: "—", hint: "", tone: "neutral" }
);
</script>
