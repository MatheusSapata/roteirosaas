const BRAZIL_COUNTRY_CODE = "55";
const LOCAL_PHONE_LENGTHS = new Set([10, 11]);

export const sanitizeDigits = (value?: string | null) => (value || "").replace(/\D/g, "");

const stripLeadingZeros = (digits: string) => digits.replace(/^0+(?=\d)/, "");

export const normalizeWhatsappDigits = (value?: string | null) => {
  const digitsOnly = stripLeadingZeros(sanitizeDigits(value));
  if (!digitsOnly) return "";
  if (digitsOnly.startsWith(BRAZIL_COUNTRY_CODE)) return digitsOnly;
  if (LOCAL_PHONE_LENGTHS.has(digitsOnly.length)) {
    return `${BRAZIL_COUNTRY_CODE}${digitsOnly}`;
  }
  return digitsOnly;
};

export const buildWhatsappLink = (digits: string, title: string) => {
  const normalizedDigits = normalizeWhatsappDigits(digits);
  if (!normalizedDigits) return "";
  const message = `Oi, tenho interesse no roteiro: ${title || "Roteiro"}`;
  return `https://wa.me/${normalizedDigits}?text=${encodeURIComponent(message)}`;
};
