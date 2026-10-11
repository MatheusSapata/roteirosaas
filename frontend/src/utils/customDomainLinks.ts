/**
 * Em domínio próprio da agência, links internos precisam ser `/slug-da-pagina`,
 * nunca `/slug-da-agencia/slug-da-pagina`. Links salvos antes de o domínio ser
 * ativado (ou de o domínio carregar no editor) ainda trazem o slug da agência;
 * aqui eles são corrigidos na hora de exibir a página.
 */
const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export const stripAgencySlugFromLink = (value: string, agencySlug: string, platformHosts: string[]): string => {
  const slug = agencySlug.trim().replace(/^\/+|\/+$/g, "");
  if (!slug || typeof value !== "string" || /\s/.test(value)) return value;
  const hosts = platformHosts.map(escapeRegExp).join("|");
  const prefix = hosts ? `(?:https?:\\/\\/(?:${hosts})(?::\\d+)?)?` : "";
  const pattern = new RegExp(`^${prefix}\\/(?:p\\/)?${escapeRegExp(slug)}(?=[/?#]|$)(\\/?)`, "i");
  const match = value.match(pattern);
  if (!match) return value;
  const rest = value.slice(match[0].length);
  return `/${rest}`;
};

export const rewriteAgencyLinks = <T>(node: T, agencySlug: string, platformHosts: string[]): T => {
  if (typeof node === "string") return stripAgencySlugFromLink(node, agencySlug, platformHosts) as unknown as T;
  if (Array.isArray(node)) return node.map(item => rewriteAgencyLinks(item, agencySlug, platformHosts)) as unknown as T;
  if (node && typeof node === "object") {
    const result: Record<string, unknown> = {};
    Object.entries(node as Record<string, unknown>).forEach(([key, value]) => {
      result[key] = rewriteAgencyLinks(value, agencySlug, platformHosts);
    });
    return result as T;
  }
  return node;
};
