<template>
  <img
    ref="el"
    v-bind="$attrs"
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
  <V2PhotoCredit v-if="credit && !small" :src="src" />
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
import V2PhotoCredit from "./V2PhotoCredit.vue";

// Duas raízes (foto + crédito): os atributos (class, alt, @click) vão para a foto.
defineOptions({ inheritAttrs: false });

const props = withDefaults(
  defineProps<{
    src: string;
    sizes?: string;
    /** Primeira dobra (Banner Inicial): baixa antes das outras imagens. */
    priority?: boolean;
    loading?: "lazy" | "eager";
    /** Mostra o "©" com o crédito, se a foto for de um banco gratuito. */
    credit?: boolean;
  }>(),
  { sizes: "100vw", priority: false, loading: "lazy", credit: true }
);
// Miniaturas e avatares (até 200px) não levam o "©".
const small = computed(() => /^\d+px$/.test(props.sizes.trim()) && parseInt(props.sizes, 10) <= 200);

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
