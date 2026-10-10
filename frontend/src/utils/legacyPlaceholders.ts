import type { LocalizedString } from "./i18n";

/**
 * Textos de exemplo que as seções antigas gravavam mas nunca mostravam na página. No visual
 * novo esses campos aparecem, então o texto de exemplo conta como vazio (não "vaza" na página).
 * Comparados já normalizados (ver `normalize`): sem HTML, acentos, caixa e ponto final.
 */
const NEVER_SHOWN: Record<string, Record<string, RegExp[]>> = {
  banner_card: {
    subtitle: [
      /^um banner compacto e elegante para reforcar a principal promessa ou proxima campanha$/,
      /^un banner compacto y elegante para reforzar la principal promesa o (la )?proxima campana$/
    ]
  }
};

// O mesmo texto chega gravado de vários jeitos: puro, dentro de <p> (editor de texto), com
// &nbsp; ou espaços a mais, com ou sem ponto final.
const normalize = (value: string) =>
  value
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;|&#160;| /gi, " ")
    .replace(/&amp;/gi, "&")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[\s.!…]+$/, "");

// Texto traduzido ({ pt, es }): é exemplo quando todas as versões preenchidas são exemplo.
const versions = (value: LocalizedString | undefined | null) =>
  (typeof value === "string" ? [value] : value && typeof value === "object" ? Object.values(value) : [])
    .filter((item): item is string => typeof item === "string")
    .map(normalize)
    .filter(Boolean);

export const isNeverShownPlaceholder = (type: string, field: string, value: LocalizedString | undefined | null) => {
  const patterns = NEVER_SHOWN[type]?.[field];
  if (!patterns) return false;
  const texts = versions(value);
  return texts.length > 0 && texts.every(current => patterns.some(pattern => pattern.test(current)));
};

/** Tira de uma seção os textos de exemplo que nunca apareceram (para o editor mostrar o campo vazio). */
export const withoutNeverShownPlaceholders = <T extends Record<string, any>>(section: T): T => {
  const fields = NEVER_SHOWN[section?.type];
  if (!fields) return section;
  const cleaned: Record<string, any> = { ...section };
  for (const field of Object.keys(fields)) {
    if (isNeverShownPlaceholder(section.type, field, section[field])) cleaned[field] = "";
  }
  return cleaned as T;
};
