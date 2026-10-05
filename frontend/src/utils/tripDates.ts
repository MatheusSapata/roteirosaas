import { getCurrentLanguage } from "./i18n";

/** Lê "AAAA-MM-DD" como data local (sem fuso), ou null se inválida. */
export const parseTripDate = (value?: string | null): Date | null => {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || "").trim());
  if (!match) return null;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  return Number.isNaN(date.getTime()) ? null : date;
};

export const addDays = (date: Date, days: number) => new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);

const locale = () => (getCurrentLanguage() === "es" ? "es" : "pt-BR");

const clean = (value: string) => value.replace(/\./g, "").trim();

/** "12 jun" */
export const formatDayMonth = (date: Date) => {
  const day = date.getDate();
  const month = clean(date.toLocaleDateString(locale(), { month: "short" }));
  return `${day} ${month}`;
};

/** "jun" */
export const formatMonthShort = (date: Date) => clean(date.toLocaleDateString(locale(), { month: "short" }));

/** "sábado" */
export const formatWeekday = (date: Date) => date.toLocaleDateString(locale(), { weekday: "long" });

/** Dias contando saída e volta (12 → 18 = 7 dias). */
export const tripLengthInDays = (start: Date, end: Date) =>
  Math.round((Date.UTC(end.getFullYear(), end.getMonth(), end.getDate()) - Date.UTC(start.getFullYear(), start.getMonth(), start.getDate())) / 86400000) + 1;
