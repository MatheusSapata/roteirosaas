<template>
  <PublicInternalFormSection :section="themed" />
</template>

<script setup lang="ts">
// Raiz = componente atual: props extras (pageId, platformHost…) e eventos passam direto.
import { computed } from "vue";
import type { InternalFormSection } from "../../../types/page";
import PublicInternalFormSection from "../PublicInternalFormSection.vue";
import { useThemedTone } from "./useThemedSection";
import "./v2.css";

const props = defineProps<{ section: InternalFormSection }>();
const tone = useThemedTone(computed(() => (props.section.backgroundType === "solid" || !props.section.backgroundType ? props.section.backgroundColor : null)), "#F2F4F1");
const themed = computed<InternalFormSection>(() => ({
  ...props.section,
  textColor: props.section.backgroundType && props.section.backgroundType !== "solid" ? props.section.textColor : tone.value.ink,
  buttonColor: tone.value.accent
}));
</script>
