<template>
  <a v-if="href" :href="href" class="logo-home-link" aria-label="Ir para a página principal"><slot /></a>
  <slot v-else />
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import { LOGO_HOME_PATH_KEY } from "./v2/livePage";

const homePath = inject(LOGO_HOME_PATH_KEY, null);
const href = computed(() => homePath?.value || "");
</script>

<style scoped>
.logo-home-link { display: contents; }
</style>
