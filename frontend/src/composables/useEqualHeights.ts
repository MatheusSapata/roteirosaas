import { nextTick, onBeforeUnmount, onMounted, watch, type Ref, type WatchSource } from "vue";

/**
 * Todos os cards do contêiner com a mesma altura (a do mais alto), em qualquer número de linhas
 * e também no celular, quando ficam um embaixo do outro. Grava a altura em `--equal-h` no
 * contêiner; cada card usa `min-height: var(--equal-h)`. Mede de novo quando a largura muda,
 * quando a lista muda (`deps`) e quando as fontes terminam de carregar.
 */
export const useEqualHeights = (container: Ref<HTMLElement | null>, selector: string, deps?: WatchSource) => {
  let observer: ResizeObserver | null = null;
  let lastWidth = -1;
  let frame = 0;

  const measure = () => {
    const el = container.value;
    if (!el) return;
    el.style.removeProperty("--equal-h");
    const cards = Array.from(el.querySelectorAll<HTMLElement>(selector));
    if (cards.length < 2) return;
    // offsetHeight ignora o transform da animação de entrada.
    const tallest = Math.max(...cards.map(card => card.offsetHeight));
    if (tallest > 0) el.style.setProperty("--equal-h", `${Math.ceil(tallest)}px`);
  };
  const schedule = () => {
    if (typeof window === "undefined") return;
    window.cancelAnimationFrame(frame);
    frame = window.requestAnimationFrame(measure);
  };

  const observe = (el: HTMLElement | null) => {
    observer?.disconnect();
    observer = null;
    lastWidth = -1;
    if (!el || typeof ResizeObserver === "undefined") return;
    // Só a largura interessa: a altura muda pela própria medida e não deve medir de novo.
    observer = new ResizeObserver(entries => {
      const width = Math.round(entries[0]?.contentRect.width || 0);
      if (width === lastWidth) return;
      lastWidth = width;
      schedule();
    });
    observer.observe(el);
  };

  onMounted(() => {
    observe(container.value);
    schedule();
    if (typeof document !== "undefined") document.fonts?.ready.then(schedule).catch(() => {});
  });
  watch(container, el => {
    observe(el);
    schedule();
  });
  if (deps) watch(deps, () => nextTick(schedule), { deep: true });
  onBeforeUnmount(() => {
    observer?.disconnect();
    if (typeof window !== "undefined") window.cancelAnimationFrame(frame);
  });

  return { refresh: schedule };
};
