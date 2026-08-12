import { api } from "@/api/client";
import type { ApiSuccess } from "@/types/api";
import type {
  ExportFormat,
  ReportCatalog,
  ReportPayload,
  ReportType,
} from "@/types/reports";

export type ReportQuery = {
  date_from?: string;
  date_to?: string;
};

export async function fetchReportCatalog() {
  const { data } = await api.get<ApiSuccess<ReportCatalog>>("/reports/");
  return data.data;
}

export async function fetchReport(reportType: ReportType, query: ReportQuery = {}) {
  const { data } = await api.get<ApiSuccess<ReportPayload>>(
    `/reports/${reportType}/`,
    {
      params:
        reportType === "inventory"
          ? undefined
          : {
              date_from: query.date_from || undefined,
              date_to: query.date_to || undefined,
            },
    },
  );
  return data.data;
}

function filenameFromDisposition(header: string | undefined, fallback: string) {
  if (!header) return fallback;
  const match = /filename="?([^";]+)"?/i.exec(header);
  return match?.[1]?.trim() || fallback;
}

export async function downloadReportExport(
  reportType: ReportType,
  exportFormat: ExportFormat,
  query: ReportQuery = {},
) {
  const response = await api.get(`/reports/${reportType}/export/`, {
    params: {
      export_format: exportFormat,
      ...(reportType === "inventory"
        ? {}
        : {
            date_from: query.date_from || undefined,
            date_to: query.date_to || undefined,
          }),
    },
    responseType: "blob",
  });

  const contentType = response.headers["content-type"];
  const blob = new Blob([response.data], {
    type: typeof contentType === "string" ? contentType : "application/octet-stream",
  });
  const disposition = response.headers["content-disposition"];
  const fallback = `${reportType}.${exportFormat === "xlsx" ? "xlsx" : exportFormat}`;
  const filename = filenameFromDisposition(
    typeof disposition === "string" ? disposition : undefined,
    fallback,
  );

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
