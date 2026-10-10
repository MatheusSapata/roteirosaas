<template>
  <V2Reveal>
    <PublicFlightDetailsSection :section="themed" :preview-device="previewDevice" />
  </V2Reveal>
</template>

<script setup lang="ts">
import V2Reveal from "./V2Reveal.vue";
// Raiz = componente atual: props extras (pageId, platformHost…) e eventos passam direto.
import { computed } from "vue";
import type { FlightDetailsSection } from "../../../types/page";
import PublicFlightDetailsSection from "../PublicFlightDetailsSection.vue";
import { useThemedTone } from "./useThemedSection";
import "./v2.css";

const props = defineProps<{ section: FlightDetailsSection; previewDevice?: "desktop" | "mobile" }>();
const tone = useThemedTone(computed(() => props.section.backgroundColor), "#0E1A15");
const themed = computed<FlightDetailsSection>(() => ({
  ...props.section,
  backgroundColor: props.section.backgroundColor || "#0E1A15",
  ctaColor: tone.value.accent,
  textColor: tone.value.ink
}));
</script>
