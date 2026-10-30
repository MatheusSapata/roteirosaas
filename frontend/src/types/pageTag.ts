export type TagColor = "blue" | "amber" | "rose" | "violet" | "teal" | "orange" | "slate" | "green";

export interface PageTagBrief {
  id: number;
  name: string;
  color: TagColor;
}

/** Tag com o uso: quantas páginas têm a tag e quais seções por tag a mostram. */
export interface PageTag extends PageTagBrief {
  page_count: number;
  sections: { page_id: number; page_title: string }[];
}

export const TAG_COLORS: { value: TagColor; label: string }[] = [
  { value: "blue", label: "Azul" },
  { value: "amber", label: "Amarelo" },
  { value: "rose", label: "Rosa" },
  { value: "violet", label: "Roxo" },
  { value: "teal", label: "Turquesa" },
  { value: "orange", label: "Laranja" },
  { value: "slate", label: "Cinza" },
  { value: "green", label: "Verde" }
];

/** Variáveis de cor da tag (definidas em styles/main.css), para usar em :style. */
export const tagStyle = (color?: string) => ({
  "--tag-bg": `var(--tag-${color || "slate"}-bg)`,
  "--tag-fg": `var(--tag-${color || "slate"}-fg)`
});

export const slugifyTag = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
