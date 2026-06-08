export const isWhatsappLink = (link?: string | null) => {
  if (!link) return false;
  const normalized = link.toLowerCase();
  return normalized.includes("wa.me") || normalized.includes("whatsapp");
};

export const normalizeExternalLink = (link?: string | null) => {
  if (!link) return "";

  const trimmed = link.trim();
  if (!trimmed) return "";

  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed) || trimmed.startsWith("//") || trimmed.startsWith("/") || trimmed.startsWith("#")) {
    return trimmed;
  }

  return `https://${trimmed}`;
};
