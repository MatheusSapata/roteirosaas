const hexPattern = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i;

const expandHex = (value: string) => value.replace(/[0-9a-f]/gi, char => char + char);

export const normalizeHexColor = (input?: string | null): string | null => {
  if (typeof input !== "string") return null;
  const trimmed = input.trim();
  if (!hexPattern.test(trimmed)) return null;
  const hex = trimmed.startsWith("#") ? trimmed.slice(1) : trimmed;
  const normalized = hex.length === 3 ? expandHex(hex) : hex;
  return `#${normalized.toLowerCase()}`;
};

const channelToLinear = (channel: number) => {
  const c = channel / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
};

export const getRelativeLuminance = (hex?: string | null): number => {
  const normalized = normalizeHexColor(hex);
  if (!normalized) return 1;
  const r = parseInt(normalized.slice(1, 3), 16);
  const g = parseInt(normalized.slice(3, 5), 16);
  const b = parseInt(normalized.slice(5, 7), 16);
  const rLin = channelToLinear(r);
  const gLin = channelToLinear(g);
  const bLin = channelToLinear(b);
  return 0.2126 * rLin + 0.7152 * gLin + 0.0722 * bLin;
};

export const isDarkColor = (hex?: string | null): boolean => {
  const luminance = getRelativeLuminance(hex);
  return luminance < 0.55;
};

const DEFAULT_DARK_TEXT = "#0f172a";
const DEFAULT_LIGHT_TEXT = "#ffffff";

export const getReadableTextColor = (background?: string | null): string => {
  if (!background) return DEFAULT_DARK_TEXT;
  return isDarkColor(background) ? DEFAULT_LIGHT_TEXT : DEFAULT_DARK_TEXT;
};

export interface SectionTextPalette {
  primary: string;
  secondary: string;
  muted: string;
  subtle: string;
  inverted: string;
  isLight: boolean;
}

export const deriveTextPalette = (textColor?: string | null): SectionTextPalette => {
  const normalized = normalizeHexColor(textColor);
  const primary = normalized || DEFAULT_DARK_TEXT;
  const isLight = getRelativeLuminance(primary) > 0.7;

  if (isLight) {
    return {
      primary,
      secondary: "rgba(255,255,255,0.88)",
      muted: "rgba(255,255,255,0.75)",
      subtle: "rgba(255,255,255,0.55)",
      inverted: DEFAULT_DARK_TEXT,
      isLight: true
    };
  }

  return {
    primary,
    secondary: "#1f2937",
    muted: "#475569",
    subtle: "#94a3b8",
    inverted: DEFAULT_LIGHT_TEXT,
    isLight: false
  };
};
