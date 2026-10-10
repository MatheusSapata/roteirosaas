<template>
  <div ref="root" :class="{ 'v2-armed': armed, 'v2-on': shown }">
    <div class="v2-in"><slot /></div>
  </div>
</template>

<script setup lang="ts">
/** Entrada animada para seções do visual novo que reaproveitam o componente antigo por dentro. */
import { ref } from "vue";
import { useEntrance } from "./useEntrance";
import "./v2.css";

const root = ref<HTMLElement | null>(null);
const { armed, shown } = useEntrance(root);
</script>
