import { computed, type Ref } from "vue";
import { usePageDesignContext } from "./designContext";

const INK_DARK = "#0F1713";
const INK_LIGHT = "#FFFFFF";

const toHex = (value?: string | null): string | null => {
  if (!value) return null;
  const raw = value.trim().replace("#", "");
  if (/^[0-9a-f]{3}$/i.test(raw)) return `#${raw.split("").map(c => c + c).join("")}`.toUpperCase();
  if (/^[0-9a-f]{6}$/i.test(raw)) return `#${raw}`.toUpperCase();
  if (/^[0-9a-f]{8}$/i.test(raw)) return `#${raw.slice(0, 6)}`.toUpperCase();
  return null;
};

export const luminance = (hex: string) => {
  const h = hex.replace("#", "");
  const ch = [0, 2, 4].map(i => {
    const c = parseInt(h.substr(i, 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
};

export const contrast = (a: string, b: string) => {
  const la = luminance(a);
  const lb = luminance(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
};

export interface SectionTone {
  bg: string;
  ink: string;
  muted: string;
  line: string;
  card: string;
  soft: string;
  dark: boolean;
  accent: string;
  onAccent: string;
  accentSoft: string;
  accentText: string;
}

/**
 * Cores de uma seção a partir do fundo escolhido e da cor de destaque da página.
 * Qualquer fundo funciona: texto claro ou escuro pelo contraste, cards como uma
 * camada translúcida e o destaque cai para a cor do texto quando some no fundo.
 */
export const computeSectionTone = (background: string | null | undefined, accentInput: string | null | undefined, fallbackBg = "#FFFFFF"): SectionTone => {
  const bg = toHex(background) || fallbackBg;
  const rawAccent = toHex(accentInput) || "#12B981";
  const dark = contrast(INK_LIGHT, bg) >= contrast(INK_DARK, bg);
  const ink = dark ? INK_LIGHT : INK_DARK;
  const nearWhite = luminance(bg) > 0.95;
  const accent = contrast(rawAccent, bg) >= 1.9 ? rawAccent : ink;
  const onAccent = contrast(INK_LIGHT, accent) >= contrast(INK_DARK, accent) ? INK_LIGHT : INK_DARK;
  return {
    bg,
    ink,
    dark,
    muted: dark ? "rgba(255,255,255,0.76)" : "rgba(15,23,19,0.72)",
    line: dark ? "rgba(255,255,255,0.16)" : "rgba(15,23,19,0.12)",
    card: dark ? "rgba(255,255,255,0.08)" : nearWhite ? "rgba(15,23,19,0.045)" : "rgba(255,255,255,0.62)",
    soft: dark ? "rgba(255,255,255,0.06)" : nearWhite ? "rgba(15,23,19,0.035)" : "rgba(255,255,255,0.45)",
    accent,
    onAccent,
    accentSoft: `color-mix(in srgb, ${accent} ${dark ? 24 : 16}%, transparent)`,
    accentText: contrast(accent, bg) >= 4.5 ? accent : ink
  };
};

/** Variáveis CSS usadas pelas seções v2 (`--v2-bg`, `--v2-ink`…). */
export const toneVars = (tone: SectionTone): Record<string, string> => ({
  "--v2-bg": tone.bg,
  "--v2-ink": tone.ink,
  "--v2-muted": tone.muted,
  "--v2-line": tone.line,
  "--v2-card": tone.card,
  "--v2-soft": tone.soft,
  "--v2-accent": tone.accent,
  "--v2-on-accent": tone.onAccent,
  "--v2-accent-soft": tone.accentSoft,
  "--v2-accent-text": tone.accentText
});

export const useSectionTone = (background: Ref<string | null | undefined>, fallbackBg = "#FFFFFF") => {
  const design = usePageDesignContext();
  const tone = computed(() => computeSectionTone(background.value, design.value.accent, fallbackBg));
  const vars = computed(() => toneVars(tone.value));
  return { tone, vars, design };
};
