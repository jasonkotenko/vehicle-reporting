export function formatDisplayDate(
  iso: string | null | undefined,
  timeZone: string,
): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-PH", {
    timeZone,
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
  }).format(new Date(iso));
}

export function dateToApiStart(date: string): string {
  return `${date}T00:00:00`;
}

export function dateToApiEnd(date: string): string {
  return `${date}T23:59:59`;
}

export function todayDateInput(): string {
  return new Date().toISOString().slice(0, 10);
}
