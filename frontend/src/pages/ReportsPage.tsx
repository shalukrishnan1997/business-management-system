import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import {
  downloadReportExport,
  fetchReport,
  fetchReportCatalog,
} from "@/api/reports";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { FieldLabel, TextInput } from "@/components/ui/Field";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { ExportFormat, ReportType } from "@/types/reports";
import { cn } from "@/utils/cn";
import { formatMoney } from "@/utils/format";

const FALLBACK_TYPES: ReportType[] = [
  "sales",
  "purchases",
  "invoices",
  "payments",
  "expenses",
  "inventory",
];

const MONEY_KEYS = new Set([
  "grand_total",
  "paid_amount",
  "due_amount",
  "total",
  "balance",
  "amount",
  "selling_price",
  "receipts",
  "supplier_payments",
  "total_amount",
]);

const STATUS_KEYS = new Set([
  "status",
  "payment_status",
  "purchase_status",
]);

function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function defaultRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 29);
  return { date_from: isoDate(from), date_to: isoDate(to) };
}

function labelize(key: string) {
  return key.replaceAll("_", " ");
}

function cellValue(key: string, value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (MONEY_KEYS.has(key)) return formatMoney(String(value));
  if (STATUS_KEYS.has(key)) return <StatusBadge value={String(value)} />;
  if (key === "payment_type" || key === "payment_method") {
    return String(value).replaceAll("_", " ");
  }
  return String(value);
}

export function ReportsPage() {
  const defaults = useMemo(() => defaultRange(), []);
  const [reportType, setReportType] = useState<ReportType>("sales");
  const [dateFrom, setDateFrom] = useState(defaults.date_from);
  const [dateTo, setDateTo] = useState(defaults.date_to);
  const [applied, setApplied] = useState(defaults);
  const [exportError, setExportError] = useState<string | null>(null);

  const catalogQuery = useQuery({
    queryKey: ["reports", "catalog"],
    queryFn: fetchReportCatalog,
  });

  const reportTypes = (catalogQuery.data?.reports ?? FALLBACK_TYPES) as ReportType[];
  const exportFormats = (catalogQuery.data?.export_formats ?? [
    "csv",
    "xlsx",
    "pdf",
  ]) as ExportFormat[];

  const queryParams =
    reportType === "inventory"
      ? {}
      : { date_from: applied.date_from, date_to: applied.date_to };

  const reportQuery = useQuery({
    queryKey: ["reports", reportType, queryParams],
    queryFn: () => fetchReport(reportType, queryParams),
  });

  const exportMutation = useMutation({
    mutationFn: (fmt: ExportFormat) =>
      downloadReportExport(reportType, fmt, queryParams),
    onSuccess: () => setExportError(null),
    onError: (err) => setExportError(getApiErrorMessage(err, "Export failed.")),
  });

  const columns: Column<Record<string, unknown>>[] = useMemo(() => {
    const keys = reportQuery.data?.columns ?? [];
    return keys.map((key) => ({
      key,
      header: labelize(key),
      render: (row) => cellValue(key, row[key]),
    }));
  }, [reportQuery.data?.columns]);

  const summaryEntries = Object.entries(reportQuery.data?.summary ?? {});
  const error = reportQuery.error
    ? getApiErrorMessage(reportQuery.error, "Could not load report.")
    : exportError;

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">
            Analytics
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-ink">
            Reports
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            Filtered JSON views with CSV, Excel, and PDF export from the same
            builders.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {exportFormats.map((fmt) => (
            <Button
              key={fmt}
              variant="secondary"
              disabled={exportMutation.isPending || reportQuery.isLoading}
              onClick={() => exportMutation.mutate(fmt)}
            >
              Export {fmt.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-1 rounded-xl border border-line bg-surface p-1">
        {reportTypes.map((type) => (
          <button
            key={type}
            type="button"
            onClick={() => setReportType(type)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition",
              reportType === type
                ? "bg-brand text-white"
                : "text-muted hover:bg-canvas hover:text-ink",
            )}
          >
            {type}
          </button>
        ))}
      </div>

      {reportType !== "inventory" ? (
        <div className="flex flex-col gap-3 rounded-2xl border border-line bg-surface p-4 sm:flex-row sm:items-end">
          <div className="min-w-[10rem] flex-1">
            <FieldLabel htmlFor="date_from">From</FieldLabel>
            <TextInput
              id="date_from"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="min-w-[10rem] flex-1">
            <FieldLabel htmlFor="date_to">To</FieldLabel>
            <TextInput
              id="date_to"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <Button
            onClick={() => setApplied({ date_from: dateFrom, date_to: dateTo })}
          >
            Apply
          </Button>
        </div>
      ) : (
        <p className="text-sm text-muted">
          Inventory is a current stock snapshot — date filters do not apply.
        </p>
      )}

      {error ? (
        <div
          role="alert"
          className="rounded-xl border border-danger/20 bg-danger/5 px-4 py-3 text-sm text-danger"
        >
          {error}
        </div>
      ) : null}

      {reportQuery.data?.period?.from || reportQuery.data?.period?.to ? (
        <p className="text-xs text-muted">
          Period{" "}
          <span className="font-medium text-ink">
            {reportQuery.data.period.from || "—"} →{" "}
            {reportQuery.data.period.to || "—"}
          </span>
          {reportQuery.isFetching ? " · refreshing…" : null}
        </p>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {reportQuery.isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-2xl border border-line bg-surface"
              />
            ))
          : summaryEntries.map(([key, value]) => (
              <div
                key={key}
                className="rounded-2xl border border-line bg-surface px-4 py-4"
              >
                <p className="text-xs font-medium uppercase tracking-wide text-muted">
                  {labelize(key)}
                </p>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-ink">
                  {MONEY_KEYS.has(key)
                    ? formatMoney(String(value))
                    : String(value)}
                </p>
              </div>
            ))}
      </div>

      <DataTable
        columns={columns}
        rows={reportQuery.data?.rows ?? []}
        rowKey={(row) => String(row.id ?? Object.values(row).slice(0, 3).join("-"))}
        loading={reportQuery.isLoading}
        empty="No rows for this period."
      />
    </section>
  );
}
