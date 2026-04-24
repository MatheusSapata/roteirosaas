<template>
  <div :class="wrapperClass">
    <div v-if="showSkeleton" class="absolute inset-0 animate-pulse rounded-[inherit] bg-slate-200/70"></div>
    <img
      v-if="activeSrc"
      :src="activeSrc"
      :alt="altText"
      loading="lazy"
      decoding="async"
      class="h-full w-full bg-transparent object-contain"
      @load="handleLoad"
      @error="handleError"
    />
    <div
      v-else
      class="flex h-full w-full items-center justify-center rounded-[inherit] border border-slate-200 bg-slate-50 text-[10px] font-bold uppercase tracking-wide text-slate-600"
      :title="badgeText"
    >
      {{ badgeText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    airlineIata?: string | null;
    airlineName?: string | null;
    customUrl?: string | null;
    sizeClass?: string;
  }>(),
  {
    airlineIata: null,
    airlineName: null,
    customUrl: null,
    sizeClass: "h-8 w-8"
  }
);

const normalizedIata = computed(() => String(props.airlineIata || "").trim().toUpperCase());
const badgeText = computed(() => normalizedIata.value || "---");
const altText = computed(() => {
  const name = String(props.airlineName || "").trim();
  if (name) return `Logo ${name}`;
  if (normalizedIata.value) return `Logo ${normalizedIata.value}`;
  return "Logo companhia";
});

const sourceList = computed(() => {
  const urls = [
    String(props.customUrl || "").trim(),
    normalizedIata.value ? `https://images.kiwi.com/airlines/128/${normalizedIata.value}.png` : "",
    normalizedIata.value ? `https://content.airhex.com/content/logos/airlines_${normalizedIata.value}_200_200_s.png` : ""
  ].filter(Boolean);
  return Array.from(new Set(urls));
});

const sourceIndex = ref(0);
const isLoaded = ref(false);

watch(
  sourceList,
  () => {
    sourceIndex.value = 0;
    isLoaded.value = false;
  },
  { immediate: true }
);

const activeSrc = computed(() => sourceList.value[sourceIndex.value] || null);
const showSkeleton = computed(() => Boolean(activeSrc.value) && !isLoaded.value);
const wrapperClass = computed(
  () =>
    `relative shrink-0 overflow-hidden rounded-md bg-transparent ${props.sizeClass}`
);

const handleLoad = () => {
  isLoaded.value = true;
};

const handleError = () => {
  isLoaded.value = false;
  if (sourceIndex.value < sourceList.value.length - 1) {
    sourceIndex.value += 1;
    return;
  }
  sourceIndex.value = sourceList.value.length;
};
</script>
