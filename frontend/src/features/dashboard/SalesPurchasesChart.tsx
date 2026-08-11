import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { SalesPurchasesPoint } from "@/types/dashboard";
import { formatMoney, formatShortDate, toNumber } from "@/utils/format";

type Props = {
  series: SalesPurchasesPoint[];
  loading?: boolean;
};

export function SalesPurchasesChart({ series, loading }: Props) {
  const data = series.map((row) => ({
    label: formatShortDate(row.date),
    sales: toNumber(row.sales),
    purchases: toNumber(row.purchases),
  }));

  return (
    <section className="rounded-2xl border border-line bg-surface p-5 shadow-[0_10px_30px_-24px_rgba(20,32,29,0.45)]">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-ink">Sales vs purchases</h3>
        <p className="text-xs text-muted">Daily totals for the selected range</p>
      </div>
      <div className="h-72 w-full">
        {loading ? (
          <div className="flex h-full items-center justify-center text-sm text-muted">
            Loading chart…
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#e5ebe8" strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fill: "#5b6b66", fontSize: 11 }} />
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
              <Legend />
              <Line
                type="monotone"
                dataKey="sales"
                name="Sales"
                stroke="#0f766e"
                strokeWidth={2.2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="purchases"
                name="Purchases"
                stroke="#475569"
                strokeWidth={2.2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
