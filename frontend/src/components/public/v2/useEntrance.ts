import { onBeforeUnmount, onMounted, ref, type Ref } from "vue";

/**
 * Animação de entrada das seções do visual novo. A seção só é "armada" (conteúdo escondido
 * até aparecer) quando há JS e IntersectionObserver, então sem eles tudo fica visível.
 * Dispara uma vez, quando o topo da seção entra na tela (inclusive as que já estão na
 * primeira tela ao abrir a página, como o Banner). Com "reduzir movimento", não anima.
 */
export const useEntrance = (root: Ref<HTMLElement | null>) => {
  const armed = ref(false);
  const shown = ref(false);
  let observer: IntersectionObserver | null = null;

  onMounted(() => {
    if (typeof window === "undefined" || !("IntersectionObserver" in window) || !root.value) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    armed.value = true;
    // Qualquer pedaço visível acima dos 10% de baixo da tela já conta: seção muito alta não
    // fica esperando 15% dela aparecer de uma vez (antes podia nunca acontecer).
    observer = new IntersectionObserver(
      entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          shown.value = true;
          observer?.disconnect();
        }
      },
      { threshold: 0, rootMargin: "0px 0px -10% 0px" }
    );
    observer.observe(root.value);
  });

  onBeforeUnmount(() => observer?.disconnect());

  return { armed, shown };
};
