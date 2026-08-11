import { Link } from "react-router-dom";

import type { RecentActivityItem } from "@/types/dashboard";
import { formatDateTime, formatMoney, titleCaseStatus } from "@/utils/format";

const typeToPath: Record<string, string> = {
  sale: "/sales",
  purchase: "/purchases",
  invoice: "/invoices",
  payment: "/payments",
  expense: "/expenses",
};

type Props = {
  items: RecentActivityItem[];
  loading?: boolean;
};

export function RecentActivityList({ items, loading }: Props) {
  return (
    <section className="rounded-2xl border border-line bg-surface p-5 shadow-[0_10px_30px_-24px_rgba(20,32,29,0.45)]">
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-ink">Recent activity</h3>
          <p className="text-xs text-muted">Latest documents across modules</p>
        </div>
      </div>

      {loading ? (
        <p className="py-8 text-center text-sm text-muted">Loading activity…</p>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted">
          No recent documents yet. Create a sale, purchase, or expense to see activity.
        </p>
      ) : (
        <ul className="divide-y divide-line">
          {items.map((item) => (
            <li key={`${item.type}-${item.reference}-${item.at}`} className="py-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">{item.title}</p>
                  <p className="mt-0.5 text-xs text-muted">
                    <span className="uppercase tracking-wide">{item.type}</span>
                    {" · "}
                    {item.reference}
                    {" · "}
                    <span className="capitalize">{titleCaseStatus(item.status)}</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">{formatDateTime(item.at)}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold tabular-nums text-brand">
                    {formatMoney(item.amount)}
                  </p>
                  <Link
                    to={typeToPath[item.type] || "/"}
                    className="mt-1 inline-block text-xs font-medium text-brand hover:text-brand-deep"
                  >
                    Open module
                  </Link>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
