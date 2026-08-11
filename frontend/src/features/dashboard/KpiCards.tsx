import type { DashboardKpis } from "@/types/dashboard";
import { formatMoney } from "@/utils/format";

type KpiCardsProps = {
  data?: DashboardKpis;
  loading?: boolean;
};

const moneyCards = [
  { key: "sales_today" as const, label: "Sales today", hint: "Non-cancelled" },
  { key: "sales_month" as const, label: "Sales this month", hint: "Month to date" },
  {
    key: "purchases_month" as const,
    label: "Purchases this month",
    hint: "Month to date",
  },
  { key: "receivables" as const, label: "Receivables", hint: "Open invoice balances" },
  { key: "expenses_month" as const, label: "Expenses this month", hint: "Recorded only" },
];

export function KpiCards({ data, loading }: KpiCardsProps) {
  const counts = data?.counts;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {moneyCards.map((card, index) => (
          <article
            key={card.key}
            className="rounded-2xl border border-line bg-surface p-5 shadow-[0_10px_30px_-24px_rgba(20,32,29,0.5)] transition duration-200 hover:-translate-y-0.5 hover:border-brand/30"
            style={{ animationDelay: `${index * 35}ms` }}
          >
            <p className="text-sm font-medium text-ink">{card.label}</p>
            <p className="mt-5 text-2xl font-semibold tracking-tight text-brand tabular-nums">
              {loading ? "…" : formatMoney(data?.money[card.key])}
            </p>
            <p className="mt-2 text-xs text-muted">{card.hint}</p>
          </article>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-6">
        {[
          { label: "Customers", value: counts?.customers },
          { label: "Suppliers", value: counts?.suppliers },
          { label: "Products", value: counts?.products },
          { label: "Low stock", value: counts?.low_stock, warn: true },
          { label: "Employees", value: counts?.employees },
          { label: "Overdue invoices", value: counts?.overdue_invoices, warn: true },
        ].map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-line bg-surface/80 px-4 py-3"
          >
            <p className="text-xs text-muted">{item.label}</p>
            <p
              className={`mt-1 text-lg font-semibold tabular-nums ${
                item.warn && (item.value ?? 0) > 0 ? "text-warn" : "text-ink"
              }`}
            >
              {loading ? "…" : (item.value ?? 0)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
