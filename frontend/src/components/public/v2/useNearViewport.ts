import { inject, onBeforeUnmount, onMounted, ref, type Ref } from "vue";
import { STATIC_RENDER_KEY } from "./useEntrance";

/**
 * Vira `true` quando o elemento chega perto da tela (a `margin` px de distância) e fica assim.
 * Serve para adiar o que é pesado de baixo da página, como o mapa do Google. Sem
 * IntersectionObserver, ou na renderização estática (criativos), já nasce `true`.
 */
export const useNearViewport = (target: Ref<HTMLElement | null>, margin = 300) => {
  const near = ref(false);
  if (inject(STATIC_RENDER_KEY, false) || typeof window === "undefined" || !("IntersectionObserver" in window)) {
    near.value = true;
    return near;
  }
  let observer: IntersectionObserver | null = null;
  onMounted(() => {
    if (!target.value) {
      near.value = true;
      return;
    }
    observer = new IntersectionObserver(
      entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          near.value = true;
          observer?.disconnect();
        }
      },
      { rootMargin: `${margin}px 0px` }
    );
    observer.observe(target.value);
  });
  onBeforeUnmount(() => observer?.disconnect());
  return near;
};
