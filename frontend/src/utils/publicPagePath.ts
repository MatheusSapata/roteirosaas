export const buildPublicPagePath = (
  pageSlug: string,
  agencySlug: string | null | undefined,
  customDomain: string | null | undefined
) => {
  const normalizedPageSlug = pageSlug.trim().replace(/^\/+|\/+$/g, "");
  if (!normalizedPageSlug) return "";

  if (customDomain?.trim()) return `/${normalizedPageSlug}`;

  const normalizedAgencySlug = agencySlug?.trim().replace(/^\/+|\/+$/g, "") || "";
  return normalizedAgencySlug ? `/${normalizedAgencySlug}/${normalizedPageSlug}` : `/${normalizedPageSlug}`;
};
