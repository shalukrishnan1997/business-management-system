import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import {
  fetchDashboardCharts,
  fetchDashboardKpis,
  fetchRecentActivity,
} from "@/api/dashboard";
import { getApiErrorMessage } from "@/api/client";
import { ExpensesByCategoryChart } from "@/features/dashboard/ExpensesByCategoryChart";
import { InvoiceStatusChart } from "@/features/dashboard/InvoiceStatusChart";
import { KpiCards } from "@/features/dashboard/KpiCards";
import { RecentActivityList } from "@/features/dashboard/RecentActivityList";
import { SalesPurchasesChart } from "@/features/dashboard/SalesPurchasesChart";
import { cn } from "@/utils/cn";

const DAY_OPTIONS = [7, 14, 30, 90] as const;

export function DashboardPage() {
  const [days, setDays] = useState<(typeof DAY_OPTIONS)[number]>(30);

  const kpisQuery = useQuery({
    queryKey: ["dashboard", "kpis"],
    queryFn: fetchDashboardKpis,
  });

  const chartsQuery = useQuery({
    queryKey: ["dashboard", "charts", days],
    queryFn: () => fetchDashboardCharts(days),
  });

  const recentQuery = useQuery({
    queryKey: ["dashboard", "recent"],
    queryFn: () => fetchRecentActivity(12),
  });

  const error =
    kpisQuery.error || chartsQuery.error || recentQuery.error
      ? getApiErrorMessage(
          kpisQuery.error || chartsQuery.error || recentQuery.error,
          "Could not load dashboard.",
        )
      : null;

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">
            Overview
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-ink">
            Operations at a glance
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            Live KPIs from{" "}
            <code className="rounded bg-brand-soft px-1.5 py-0.5 text-brand-deep">
              /api/v1/dashboard/
            </code>
            {kpisQuery.data?.as_of ? ` · as of ${kpisQuery.data.as_of}` : null}
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-xl border border-line bg-surface p-1">
          {DAY_OPTIONS.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setDays(option)}
              className={cn(
                "rounded-lg px-3 py-1.5 text-xs font-medium transition",
                days === option
                  ? "bg-brand text-white"
                  : "text-muted hover:bg-canvas hover:text-ink",
              )}
            >
              {option}d
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-danger/20 bg-danger/5 px-4 py-3 text-sm text-danger"
        >
          {error}
        </div>
      )}

      <KpiCards data={kpisQuery.data} loading={kpisQuery.isLoading} />

      <div className="grid gap-4 xl:grid-cols-2">
        <SalesPurchasesChart
          series={chartsQuery.data?.sales_vs_purchases ?? []}
          loading={chartsQuery.isLoading}
        />
        <ExpensesByCategoryChart
          rows={chartsQuery.data?.expenses_by_category ?? []}
          loading={chartsQuery.isLoading}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <InvoiceStatusChart
          rows={chartsQuery.data?.invoices_by_status ?? []}
          loading={chartsQuery.isLoading}
        />
        <RecentActivityList
          items={recentQuery.data?.results ?? []}
          loading={recentQuery.isLoading}
        />
      </div>
    </section>
  );
}
