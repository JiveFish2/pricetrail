const formatters = new Map<string, Intl.NumberFormat>();

export function money(value: string | number | null | undefined, currency: string): string {
  if (value === null || value === undefined) return "—";
  let formatter = formatters.get(currency);
  if (!formatter) {
    formatter = new Intl.NumberFormat(currency === "BRL" ? "pt-BR" : "en-US", {
      style: "currency",
      currency,
    });
    formatters.set(currency, formatter);
  }
  return formatter.format(Number(value));
}

export function discount(price: string | null, listPrice: string | null): number | null {
  if (!price || !listPrice) return null;
  const p = Number(price);
  const l = Number(listPrice);
  if (!(l > p)) return null;
  return Math.round((1 - p / l) * 100);
}

export function shortDate(day: string): string {
  const [y, m, d] = day.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

// Percentage change from the previous observation; negative means a drop.
export function change(price: string | null, previous: string | null): number | null {
  if (!price || !previous) return null;
  const p = Number(price);
  const b = Number(previous);
  if (!(b > 0) || p === b) return null;
  return Math.round(((p - b) / b) * 100);
}
