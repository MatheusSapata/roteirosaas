<template>
  <div class="brand-header">
    <div class="brand-block">
      <div v-if="agencyLogo" class="brand-logo">
        <img :src="agencyLogo" :alt="`Logotipo ${agencyName || 'Agência'}`" />
      </div>
      <div v-else class="brand-logo brand-logo--fallback">
        <span>{{ agencyInitials }}</span>
      </div>
      <div class="brand-meta">
        <p class="brand-eyebrow">Documento emitido por</p>
        <p class="brand-title">{{ agencyName || "Agência emissora" }}</p>
      </div>
    </div>
    <div class="brand-divider" aria-hidden="true"></div>
    <div class="brand-block brand-block--platform">
      <div class="brand-logo">
        <img :src="platformLogo" :alt="platformName" />
      </div>
      <div class="brand-meta">
        <p class="brand-eyebrow">Verificado via</p>
        <p class="brand-title">{{ platformName }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  agencyName?: string | null;
  agencyLogo?: string | null;
  platformName: string;
  platformLogo: string;
}>();

const agencyInitials = computed(() => {
  const source = props.agencyName || "Agência";
  const parts = source.trim().split(/\s+/);
  const initials = parts.slice(0, 2).map(part => part[0]?.toUpperCase() ?? "");
  return initials.join("") || "AG";
});
</script>

<style scoped>
.brand-header {
  @apply flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-100 bg-white/80 p-5 shadow-sm;
}
.brand-block {
  @apply flex items-center gap-3;
}
.brand-block--platform .brand-eyebrow {
  @apply text-emerald-500;
}
.brand-logo {
  @apply flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm;
}
.brand-logo img {
  @apply max-h-[56px] max-w-[72px];
}
.brand-block--platform .brand-logo {
  @apply h-[88px] w-[88px];
}
.brand-block--platform .brand-logo img {
  @apply max-h-[76px] max-w-[140px];
}
.brand-logo--fallback {
  @apply bg-slate-900 text-white;
}
.brand-logo--fallback span {
  @apply text-lg font-semibold;
}
.brand-meta {
  @apply leading-tight;
}
.brand-eyebrow {
  @apply text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.brand-title {
  @apply text-base font-semibold text-slate-900;
}
.brand-divider {
  @apply hidden h-10 w-px bg-slate-200 md:block;
}
</style>
