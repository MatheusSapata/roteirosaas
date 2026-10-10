<template>
  <img
    ref="el"
    :src="src"
    :srcset="srcset || undefined"
    :sizes="srcset ? sizes : undefined"
    :loading="priority ? 'eager' : loading"
    :fetchpriority="priority ? 'high' : undefined"
    decoding="async"
    :class="{ 'v2-img-wait': waiting, 'v2-img-in': revealed }"
    @load="settle"
    @error="settle"
  />
</template>

<script setup lang="ts">
/**
 * Imagem das seções do visual novo. Enquanto baixa, fica escondida (nada de aparecer em
 * faixas, de cima para baixo) e surge esmaecendo quando termina; se já estava no cache,
 * aparece na hora. Imagens enviadas com versões leves ganham srcset: o navegador baixa só
 * a largura que a tela precisa (`sizes` diz quanto da tela a imagem ocupa).
 */
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { responsiveSrcset } from "../../../utils/media";

const props = withDefaults(
  defineProps<{
    src: string;
    sizes?: string;
    /** Primeira dobra (Banner Inicial): baixa antes das outras imagens. */
    priority?: boolean;
    loading?: "lazy" | "eager";
  }>(),
  { sizes: "100vw", priority: false, loading: "lazy" }
);

const el = ref<HTMLImageElement | null>(null);
const waiting = ref(false);
const revealed = ref(false);
const srcset = computed(() => responsiveSrcset(props.src));

const check = () => {
  const img = el.value;
  if (!img) return;
  // Já pronta (cache): aparece sem animação. Ainda baixando: esconde até o load.
  waiting.value = !(img.complete && img.naturalWidth > 0);
  revealed.value = false;
};
const settle = () => {
  if (waiting.value) revealed.value = true;
  waiting.value = false;
};

onMounted(check);
watch(
  () => props.src,
  () => nextTick(check)
);
</script>
