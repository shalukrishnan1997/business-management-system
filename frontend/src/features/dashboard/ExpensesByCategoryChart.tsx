import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DashboardCharts } from "@/types/dashboard";
import { formatMoney, toNumber } from "@/utils/format";

type Props = {
  rows: DashboardCharts["expenses_by_category"];
  loading?: boolean;
};

export function ExpensesByCategoryChart({ rows, loading }: Props) {
  const data = rows.slice(0, 8).map((row) => ({
    category: row.category,
    total: toNumber(row.total),
  }));

  return (
    <section className="rounded-2xl border border-line bg-surface p-5 shadow-[0_10px_30px_-24px_rgba(20,32,29,0.45)]">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-ink">Expenses by category</h3>
        <p className="text-xs text-muted">Top categories in range</p>
      </div>
      <div className="h-72 w-full">
        {loading ? (
          <div className="flex h-full items-center justify-center text-sm text-muted">
            Loading chart…
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-muted">
            No expenses in this period
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 24 }}>
              <CartesianGrid stroke="#e5ebe8" strokeDasharray="3 3" />
              <XAxis
                dataKey="category"
                tick={{ fill: "#5b6b66", fontSize: 10 }}
                interval={0}
                angle={-20}
                textAnchor="end"
                height={50}
              />
              <YAxis
                tick={{ fill: "#5b6b66", fontSize: 11 }}
                tickFormatter={(v) =>
                  new Intl.NumberFormat("en-IN", {
                    notation: "compact",
                    maximumFractionDigits: 1,
                  }).format(Number(v))
                }
              />
              <Tooltip
                formatter={(value) => formatMoney(Number(value ?? 0))}
                contentStyle={{
                  borderRadius: 12,
                  borderColor: "#d7e0dc",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="total" name="Total" fill="#0f766e" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
