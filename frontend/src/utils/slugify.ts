export const slugify = (value: string | undefined | null, fallbackPrefix = "item"): string => {
  const normalized =
    (value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .substring(0, 60) || "";

  if (normalized) return normalized;
  return `${fallbackPrefix}-${Date.now()}`;
};

export const slugMatchesValue = (
  value: string | undefined | null,
  slug: string | undefined | null,
  fallbackPrefix = "item"
) => {
  if (!value) return !slug;
  const normalized = slugify(value, fallbackPrefix);
  return normalized === (slug || "");
};
