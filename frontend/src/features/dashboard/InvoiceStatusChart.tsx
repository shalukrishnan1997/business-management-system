import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { DashboardCharts } from "@/types/dashboard";
import { formatMoney, titleCaseStatus, toNumber } from "@/utils/format";

const COLORS = ["#0f766e", "#115e59", "#475569", "#b45309", "#b91c1c", "#64748b"];

type Props = {
  rows: DashboardCharts["invoices_by_status"];
  loading?: boolean;
};

export function InvoiceStatusChart({ rows, loading }: Props) {
  const data = rows.map((row) => ({
    name: titleCaseStatus(row.status),
    value: row.count,
    balance: toNumber(row.balance),
    total: toNumber(row.total),
  }));

  return (
    <section className="rounded-2xl border border-line bg-surface p-5 shadow-[0_10px_30px_-24px_rgba(20,32,29,0.45)]">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-ink">Invoices by status</h3>
        <p className="text-xs text-muted">Open document mix (excl. cancelled)</p>
      </div>
      <div className="flex h-72 flex-col gap-4 sm:flex-row sm:items-center">
        {loading ? (
          <div className="flex h-full w-full items-center justify-center text-sm text-muted">
            Loading chart…
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-full w-full items-center justify-center text-sm text-muted">
            No invoices yet
          </div>
        ) : (
          <>
            <div className="h-56 w-full sm:w-1/2">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={48}
                    outerRadius={80}
                    paddingAngle={2}
                  >
                    {data.map((entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={COLORS[index % COLORS.length]}
                        stroke="#fff"
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, _name, item) => [
                      `${value} invoices`,
                      String(item?.payload?.name ?? ""),
                    ]}
                    contentStyle={{
                      borderRadius: 12,
                      borderColor: "#d7e0dc",
                      fontSize: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="w-full space-y-2 sm:w-1/2">
              {data.map((row, index) => (
                <li
                  key={row.name}
                  className="flex items-center justify-between gap-3 text-sm"
                >
                  <span className="flex items-center gap-2 text-ink">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ background: COLORS[index % COLORS.length] }}
                    />
                    <span className="capitalize">{row.name}</span>
                  </span>
                  <span className="tabular-nums text-muted">
                    {row.value} · {formatMoney(row.balance)} due
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </section>
  );
}
