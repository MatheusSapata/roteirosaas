export const isWhatsappLink = (link?: string | null) => {
  if (!link) return false;
  const normalized = link.toLowerCase();
  return normalized.includes("wa.me") || normalized.includes("whatsapp");
};
