/**
 * Fotos do Banner por tela. Sem a foto do computador, a do celular vale nas duas telas (e
 * vice-versa): uma página com só a foto do celular não fica com o computador sem foto.
 *
 * O encaixe ("x% y%", o ponto da foto que não pode ficar de fora quando a tela corta as bordas)
 * é de cada foto e vai junto com ela para a outra tela.
 */
export type HeroPhotoFields = {
  backgroundImage?: string;
  mobileBackgroundImage?: string;
  backgroundFocus?: string;
  mobileBackgroundFocus?: string;
};

export type HeroPhoto = { src: string; focus: string };
export type FocusPoint = { x: number; y: number };

const FOCUS_RE = /^(\d+(?:\.\d+)?)% (\d+(?:\.\d+)?)%$/;
const clamp = (value: number) => Math.min(100, Math.max(0, Math.round(value)));

export const parseFocus = (value?: string | null): FocusPoint | null => {
  const match = FOCUS_RE.exec(String(value || "").trim());
  return match ? { x: clamp(Number(match[1])), y: clamp(Number(match[2])) } : null;
};

/** "x% y%" pronto para object-position / background-position; vazio sem encaixe escolhido. */
export const focusCss = (value?: string | null): string => {
  const point = parseFocus(value);
  return point ? `${point.x}% ${point.y}%` : "";
};

export const formatFocus = (point: FocusPoint): string => `${clamp(point.x)}% ${clamp(point.y)}%`;

export const heroPhoto = (section: HeroPhotoFields, screen: "desktop" | "mobile"): HeroPhoto => {
  const desktop = { src: String(section.backgroundImage || "").trim(), focus: focusCss(section.backgroundFocus) };
  const mobile = { src: String(section.mobileBackgroundImage || "").trim(), focus: focusCss(section.mobileBackgroundFocus) };
  const [own, other] = screen === "desktop" ? [desktop, mobile] : [mobile, desktop];
  return own.src ? own : other;
};
