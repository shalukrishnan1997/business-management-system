export type ReportType =
  | "sales"
  | "purchases"
  | "invoices"
  | "payments"
  | "expenses"
  | "inventory";

export type ExportFormat = "csv" | "xlsx" | "pdf";

export type ReportCatalog = {
  reports: ReportType[];
  export_formats: ExportFormat[];
};

export type ReportPeriod = {
  from: string | null;
  to: string | null;
};

export type ReportPayload = {
  report: ReportType;
  period: ReportPeriod;
  summary: Record<string, string | number>;
  rows: Record<string, unknown>[];
  columns: string[];
};
