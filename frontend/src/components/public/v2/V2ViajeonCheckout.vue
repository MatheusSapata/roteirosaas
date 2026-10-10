<template>
  <V2Reveal>
    <PublicViajeonCheckoutSection :section="themed" />
  </V2Reveal>
</template>

<script setup lang="ts">
import V2Reveal from "./V2Reveal.vue";
// Raiz = componente atual: props extras (pageId, platformHost…) e eventos passam direto.
import { computed } from "vue";
import type { ViajeonCheckoutSection } from "../../../types/page";
import PublicViajeonCheckoutSection from "../PublicViajeonCheckoutSection.vue";
import { useThemedTone } from "./useThemedSection";
import "./v2.css";

const props = defineProps<{ section: ViajeonCheckoutSection }>();
const tone = useThemedTone(computed(() => props.section.backgroundColor), "#F2F4F1");
const themed = computed<ViajeonCheckoutSection>(() => ({
  ...props.section,
  backgroundColor: tone.value.bg,
  textColor: tone.value.ink,
  accentColor: tone.value.accent,
  buttonColor: tone.value.accent,
  buttonTextColor: tone.value.onAccent,
  cardBackgroundColor: tone.value.dark ? "rgba(255,255,255,0.08)" : "#FFFFFF",
  cardTextColor: tone.value.ink
}));
</script>
