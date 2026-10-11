<template>
  <img
    ref="el"
    v-bind="{ ...$attrs, ...scopeAttrs }"
    :src="src"
    :srcset="srcset || undefined"
    :sizes="srcset ? sizes : undefined"
    :loading="priority ? 'eager' : loading"
    :fetchpriority="priority ? 'high' : undefined"
    decoding="async"
    :class="{ 'v2-img-wait': waiting, 'v2-img-in': revealed }"
    @load="settle(), placeCredit()"
    @error="settle"
  />
  <V2PhotoCredit v-if="showCredit" :src="src" :style="creditStyle" />
</template>

<script setup lang="ts">
/**
 * Imagem das seções do visual novo. Enquanto baixa, fica escondida (nada de aparecer em
 * faixas, de cima para baixo) e surge esmaecendo quando termina; se já estava no cache,
 * aparece na hora. Imagens enviadas com versões leves ganham srcset: o navegador baixa só
 * a largura que a tela precisa (`sizes` diz quanto da tela a imagem ocupa).
 */
import { computed, getCurrentInstance, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { responsiveSrcset } from "../../../utils/media";
import V2PhotoCredit from "./V2PhotoCredit.vue";
import { usePhotoCredit } from "./photoCredits";

// Duas raízes (foto + crédito): os atributos (class, alt, @click) vão para a foto.
defineOptions({ inheritAttrs: false });
// Com duas raízes o Vue não passa o escopo do CSS da seção para a foto, e regras como
// `.v2-story-stage img { object-fit: cover; height: 100% }` deixariam de valer. Passa à mão.
const scopeId = getCurrentInstance()?.vnode.scopeId;
const scopeAttrs = scopeId ? { [scopeId]: "" } : {};

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

// O "©" fica no canto de baixo da foto, qualquer que seja a seção: em vez de depender de
// cada seção posicionar o contêiner da foto, mede onde a foto está (os dois têm o mesmo
// elemento de referência, por serem irmãos) e se acomoda quando o tamanho muda.
const photoCredit = usePhotoCredit(() => props.src);
const showCredit = computed(() => props.credit && !small.value && Boolean(photoCredit.value));
const creditStyle = ref<Record<string, string>>({});
const placeCredit = () => {
  const img = el.value;
  if (!img || !showCredit.value) return;
  const gap = 10;
  creditStyle.value = {
    left: `${img.offsetLeft + gap}px`,
    top: `${img.offsetTop + img.offsetHeight - gap}px`,
    bottom: "auto",
    transform: "translateY(-100%)",
    maxWidth: `${Math.max(0, img.offsetWidth - gap * 2)}px`
  };
};
let observer: ResizeObserver | null = null;
const watchSize = () => {
  observer?.disconnect();
  observer = null;
  const img = el.value;
  if (!img || !showCredit.value || typeof ResizeObserver === "undefined") return;
  observer = new ResizeObserver(placeCredit);
  observer.observe(img);
  if (img.parentElement) observer.observe(img.parentElement);
  placeCredit();
};

onMounted(() => {
  check();
  watchSize();
  window.addEventListener("resize", placeCredit);
});
onBeforeUnmount(() => {
  observer?.disconnect();
  window.removeEventListener("resize", placeCredit);
});
watch(
  () => props.src,
  () => nextTick(check)
);
watch(showCredit, () => nextTick(watchSize));
</script>
