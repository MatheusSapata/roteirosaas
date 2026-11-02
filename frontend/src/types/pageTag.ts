/** Cor pronta (nome) ou cor personalizada em #rrggbb. */
export type TagPresetColor = "blue" | "amber" | "rose" | "violet" | "teal" | "orange" | "slate" | "green";
export type TagColor = TagPresetColor | `#${string}`;

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

/** Cores prontas: a própria cor, viva, igual no tema claro e no escuro. */
export const TAG_COLORS: { value: TagPresetColor; label: string; hex: string }[] = [
  { value: "blue", label: "Azul", hex: "#2563eb" },
  { value: "amber", label: "Amarelo", hex: "#f59e0b" },
  { value: "rose", label: "Rosa", hex: "#e11d48" },
  { value: "violet", label: "Roxo", hex: "#7c3aed" },
  { value: "teal", label: "Turquesa", hex: "#0d9488" },
  { value: "orange", label: "Laranja", hex: "#ea580c" },
  { value: "slate", label: "Cinza", hex: "#475569" },
  { value: "green", label: "Verde", hex: "#16a34a" }
];

const HEX = /^#[0-9a-f]{6}$/i;
export const isCustomTagColor = (color?: string | null) => !!color && HEX.test(color);

/** Hex da cor da tag (cor pronta ou personalizada). Sem cor válida, cinza. */
export const tagHex = (color?: string | null) => {
  if (isCustomTagColor(color)) return (color as string).toLowerCase();
  return TAG_COLORS.find(item => item.value === color)?.hex || "#475569";
};

/** Texto branco ou escuro, o que tiver mais contraste com a cor (WCAG). */
export const tagInk = (color?: string | null) => {
  const hex = tagHex(color);
  const channel = (i: number) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  const lum = 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5);
  const contrastWhite = 1.05 / (lum + 0.05);
  const contrastDark = (lum + 0.05) / 0.0536; // #111814
  return contrastWhite >= contrastDark ? "#ffffff" : "#111814";
};

/**
 * Variáveis de cor da tag, para usar em :style:
 * --tag (a cor), --tag-bg (fundo sólido, a própria cor) e --tag-fg (texto sobre ela).
 */
export const tagStyle = (color?: string | null) => {
  const hex = tagHex(color);
  return { "--tag": hex, "--tag-bg": hex, "--tag-fg": tagInk(color) };
};

export const slugifyTag = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
