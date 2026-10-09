import type { LocalizedString } from "./i18n";

/**
 * Textos de exemplo que as seções antigas gravavam mas nunca mostravam na página. No visual
 * novo esses campos aparecem, então o texto de exemplo conta como vazio (não "vaza" na página).
 */
const NEVER_SHOWN: Record<string, Record<string, string[]>> = {
  banner_card: {
    subtitle: ["Um banner compacto e elegante para reforçar a principal promessa ou próxima campanha."]
  }
};

const asText = (value: LocalizedString | undefined | null) =>
  typeof value === "string" ? value : value && typeof value === "object" ? Object.values(value).join(" ") : "";

export const isNeverShownPlaceholder = (type: string, field: string, value: LocalizedString | undefined | null) => {
  const texts = NEVER_SHOWN[type]?.[field];
  if (!texts) return false;
  const current = asText(value).trim();
  return !!current && texts.includes(current);
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
