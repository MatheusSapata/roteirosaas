import { computed, ref, type Ref } from "vue";

export type SortDir = "asc" | "desc";
/** Valor usado para ordenar: número, texto ou vazio (vazio vai sempre para o fim). */
export type SortValue = number | string | null | undefined;

/**
 * Ordenação por coluna das tabelas do Admin Master. Clicar na mesma coluna inverte a ordem;
 * em coluna nova começa pela direção mais útil dela (ex.: "mais tempo" primeiro).
 */
export function useTableSort<T>(
  rows: Ref<T[]>,
  getters: Record<string, (row: T) => SortValue>,
  initial: { key: string; dir: SortDir },
  firstDir: Record<string, SortDir> = {}
) {
  const sortKey = ref(initial.key);
  const sortDir = ref<SortDir>(initial.dir);

  const setSort = (key: string) => {
    if (sortKey.value === key) {
      sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
      return;
    }
    sortKey.value = key;
    sortDir.value = firstDir[key] || "asc";
  };

  const sorted = computed(() => {
    const get = getters[sortKey.value];
    if (!get) return rows.value;
    const factor = sortDir.value === "asc" ? 1 : -1;
    return [...rows.value].sort((a, b) => {
      const left = get(a);
      const right = get(b);
      const leftEmpty = left === null || left === undefined || left === "";
      const rightEmpty = right === null || right === undefined || right === "";
      if (leftEmpty || rightEmpty) return leftEmpty === rightEmpty ? 0 : leftEmpty ? 1 : -1;
      if (typeof left === "number" && typeof right === "number") return (left - right) * factor;
      return String(left).localeCompare(String(right), "pt-BR", { sensitivity: "base" }) * factor;
    });
  });

  const arrow = (key: string) => (sortKey.value === key ? (sortDir.value === "asc" ? "↑" : "↓") : "↕");
  const ariaSort = (key: string) => (sortKey.value === key ? (sortDir.value === "asc" ? "ascending" : "descending") : "none");

  return { sortKey, sortDir, setSort, sorted, arrow, ariaSort };
}

/** Seleção de linhas para ações em massa. */
export function useSelection<T extends { id: number }>(visible: Ref<T[]>) {
  const selected = ref<number[]>([]);
  const isSelected = (row: T) => selected.value.includes(row.id);
  const toggle = (row: T) => {
    selected.value = isSelected(row) ? selected.value.filter(id => id !== row.id) : [...selected.value, row.id];
  };
  const allVisibleSelected = computed(() => visible.value.length > 0 && visible.value.every(isSelected));
  const toggleAll = () => {
    const ids = visible.value.map(row => row.id);
    selected.value = allVisibleSelected.value
      ? selected.value.filter(id => !ids.includes(id))
      : [...new Set([...selected.value, ...ids])];
  };
  const clear = () => {
    selected.value = [];
  };
  return { selected, isSelected, toggle, allVisibleSelected, toggleAll, clear };
}
