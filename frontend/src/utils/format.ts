const DEFAULT_LOCALE = "pt-BR";

const parseDate = (value?: string | Date | null): Date | null => {
  if (!value) return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
};

export const formatDateBR = (value?: string | Date | null, fallback = "-") => {
  const date = parseDate(value);
  return date ? new Intl.DateTimeFormat(DEFAULT_LOCALE).format(date) : fallback;
};

export const formatDateTimeBR = (value?: string | Date | null, fallback = "-") => {
  const date = parseDate(value);
  return date
    ? new Intl.DateTimeFormat(DEFAULT_LOCALE, {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      }).format(date)
    : fallback;
};

export const formatCurrencyBRL = (value?: number | null, fallback = "R$ 0,00") => {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback;
  return new Intl.NumberFormat(DEFAULT_LOCALE, { style: "currency", currency: "BRL" }).format(value);
};

export const formatCurrencyCentsBRL = (value?: number | null, fallback = "R$ 0,00") =>
  formatCurrencyBRL((value || 0) / 100, fallback);

export const onlyDigits = (value?: string | number | null) => String(value ?? "").replace(/\D/g, "");

export const formatCpfBR = (value?: string | null) => {
  const digits = onlyDigits(value).slice(0, 11);
  return digits
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
};

export const formatCnpjBR = (value?: string | null) => {
  const digits = onlyDigits(value).slice(0, 14);
  return digits
    .replace(/^(\d{2})(\d)/, "$1.$2")
    .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1/$2")
    .replace(/(\d{4})(\d{1,2})$/, "$1-$2");
};

export const formatPhoneBR = (value?: string | null) => {
  const digits = onlyDigits(value).replace(/^55(?=\d{10,11}$)/, "").slice(0, 11);
  if (digits.length <= 10) {
    return digits.replace(/^(\d{2})(\d)/, "($1) $2").replace(/(\d{4})(\d{1,4})$/, "$1-$2");
  }
  return digits.replace(/^(\d{2})(\d)/, "($1) $2").replace(/(\d{5})(\d{1,4})$/, "$1-$2");
};
