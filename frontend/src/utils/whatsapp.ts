export const sanitizeDigits = (value?: string | null) => (value || "").replace(/\D/g, "");

export const buildWhatsappLink = (digits: string, title: string) => {
  if (!digits) return "";
  const message = `Oi, tenho interesse no roteiro: ${title || "Roteiro"}`;
  return `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
};
