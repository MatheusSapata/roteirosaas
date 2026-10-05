import type { PageConfig } from "../types/page";

export type PageDesign = "legacy" | "v2";

/**
 * Visual efetivo das seções públicas.
 * O visual novo só vale quando a plataforma liberou para a agência
 * (`design_v2_enabled`, decidido no backend) e a página não pediu o visual antigo.
 */
export const resolvePageDesign = (designV2Enabled: boolean | undefined, config?: Pick<PageConfig, "design"> | null): PageDesign =>
  designV2Enabled && config?.design !== "legacy" ? "v2" : "legacy";
