<template>
  <section class="ved-group">
    <div v-if="title" class="ved-group-head">
      <h3>{{ title }}</h3>
      <span v-if="count" class="ved-group-count">{{ count }}</span>
      <span v-if="extra" class="ved-group-extra">Extra</span>
    </div>
    <slot />
  </section>
</template>

<script setup lang="ts">
defineProps<{ title?: string; count?: string; extra?: boolean }>();
</script>
