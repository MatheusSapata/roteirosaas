<template>
  <V2Reveal>
    <PublicViajeonCheckoutSection v-bind="$attrs" :section="themed" v2 />
  </V2Reveal>
</template>

<script setup lang="ts">
import V2Reveal from "./V2Reveal.vue";
// A raiz é a animação de entrada: as props extras (pageId, platformHost) vão direto para o componente
// de dentro, e não para a <div> dela. Sem o pageId, os preços não eram atualizados com a ViajeOn.
import { computed } from "vue";
import type { ViajeonCheckoutSection } from "../../../types/page";
import PublicViajeonCheckoutSection from "../PublicViajeonCheckoutSection.vue";
import { useThemedTone } from "./useThemedSection";
import "./v2.css";

defineOptions({ inheritAttrs: false });

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
