const moneyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

export function formatMoney(value: string | number | null | undefined): string {
  const n = typeof value === "number" ? value : Number(value ?? 0);
  if (Number.isNaN(n)) return moneyFormatter.format(0);
  return moneyFormatter.format(n);
}

export function toNumber(value: string | number | null | undefined): number {
  const n = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isNaN(n) ? 0 : n;
}

export function formatShortDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function titleCaseStatus(value: string): string {
  return value.replaceAll("_", " ");
}
