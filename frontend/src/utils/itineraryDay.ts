import type { ItineraryDay, ItinerarySection } from "../types/page";
import { addDays, formatDayMonth, formatMonthShort, formatWeekday, parseTripDate } from "./tripDates";

type Read = (value: ItineraryDay["day"]) => string;

export interface ItineraryDayParts {
  /** Faixa de cima do calendário. Vazia: o calendário fica de uma cor só. */
  badge: string;
  /** Número grande do calendário. */
  number: string;
  /** Texto pequeno embaixo do número. */
  note: string;
  /** Texto acima do título. */
  kicker: string;
  /** Posição do dia na lista (1, 2, 3...). */
  position: string;
  /** Algum desses textos foi escrito à mão neste dia. */
  custom: boolean;
  /** Data calculada (só para os dias antigos, que ainda não têm os textos próprios). */
  shortDate: string;
}

const isSet = (value: unknown) => value !== undefined && value !== null;

/**
 * Os cinco textos do calendário de cada dia. O que foi escrito à mão vale como está
 * (inclusive vazio); o que nunca foi escrito segue a conta antiga por data, então
 * os roteiros já salvos continuam iguais.
 */
export const itineraryDayParts = (
  section: Pick<ItinerarySection, "days" | "startDate" | "layout">,
  tripStartDate: string | undefined,
  dayWord: string,
  dayPrefix: string,
  read: Read
): ItineraryDayParts[] => {
  const start = parseTripDate(section.startDate) || parseTripDate(tripStartDate);
  const isTimeline = section.layout !== "journey" && section.layout !== "cards" && section.layout !== "steps";
  let previous: Date | null = null;
  return (section.days || []).map((day, idx) => {
    const date = parseTripDate(day.date) || (previous ? addDays(previous, 1) : start ? addDays(start, idx) : null);
    previous = date;
    const label = read(day.day).trim() || `${dayPrefix} ${idx + 1}`;
    const position = label.match(/\d+/)?.[0] ?? String(idx + 1);
    const badge = isSet(day.badge) ? read(day.badge as string) : date || !isTimeline ? `${dayWord} ${position}` : dayWord;
    const kickerAuto = date ? (isTimeline ? `${label} · ${formatWeekday(date)}` : formatWeekday(date)) : label;
    return {
      badge: badge.trim(),
      number: isSet(day.number) ? read(day.number as string).trim() : date ? String(date.getDate()) : position,
      note: isSet(day.numberNote) ? read(day.numberNote as string).trim() : date ? formatMonthShort(date) : "",
      kicker: isSet(day.kicker) ? read(day.kicker as string).trim() : kickerAuto,
      position,
      custom: isSet(day.badge) || isSet(day.number) || isSet(day.numberNote) || isSet(day.kicker),
      shortDate: date ? formatDayMonth(date) : ""
    };
  });
};
