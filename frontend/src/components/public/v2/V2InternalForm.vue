<template>
  <PublicInternalFormSection :section="themed" />
</template>

<script setup lang="ts">
// Raiz = componente atual: props extras (pageId, platformHost…) e eventos passam direto.
import { computed } from "vue";
import type { InternalFormSection } from "../../../types/page";
import PublicInternalFormSection from "../PublicInternalFormSection.vue";
import { usePageDesignContext } from "./designContext";
import { computeSectionTone } from "./useSectionTone";
import { useThemedTone } from "./useThemedSection";
import "./v2.css";

const props = defineProps<{ section: InternalFormSection }>();
const design = usePageDesignContext();
// Foto só conta quando existe: "foto" sem imagem virava um fundo cinza (o escurecimento) com texto
// branco apagado. Sem foto, o fundo é a cor escolhida (ou o claro padrão) e o texto segue o tom dela;
// no degradê das páginas antigas, o tom vem da cor inicial.
const hasPhoto = computed(() => props.section.backgroundType === "image" && !!props.section.backgroundImage);
const isGradient = computed(() => props.section.backgroundType === "gradient");
const tone = useThemedTone(
  computed(() => (hasPhoto.value ? null : isGradient.value ? props.section.gradientStart : props.section.backgroundColor)),
  "#F2F4F1"
);
const themed = computed<InternalFormSection>(() => ({
  ...props.section,
  ...(hasPhoto.value || isGradient.value ? {} : { backgroundType: "solid" as const, backgroundColor: tone.value.bg }),
  // Sobre a foto escurecida o texto é branco.
  textColor: hasPhoto.value ? "#FFFFFF" : tone.value.ink,
  // O botão fica dentro do cartão branco do formulário: destaque da página, legível no branco.
  buttonColor: computeSectionTone("#FFFFFF", design.value.accent).accent
}));
</script>
