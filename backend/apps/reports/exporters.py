"""
Report exporters — CSV, Excel (openpyxl), PDF (ReportLab).
"""
import csv
from io import BytesIO, StringIO

from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _filename(report: dict, ext: str) -> str:
    name = report.get("report", "report")
    period = report.get("period") or {}
    start = period.get("from") or "all"
    end = period.get("to") or "all"
    return f"{name}_{start}_{end}.{ext}"


def export_csv(report: dict) -> HttpResponse:
    columns = report.get("columns") or []
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in report.get("rows") or []:
        writer.writerow([row.get(col, "") for col in columns])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{_filename(report, "csv")}"'
    )
    return response


def export_xlsx(report: dict) -> HttpResponse:
    columns = report.get("columns") or []
    wb = Workbook()
    ws = wb.active
    ws.title = (report.get("report") or "Report")[:31]
    ws.append(columns)
    for row in report.get("rows") or []:
        ws.append([row.get(col, "") for col in columns])

    # Summary sheet
    summary = report.get("summary") or {}
    if summary:
        ws2 = wb.create_sheet("Summary")
        ws2.append(["key", "value"])
        for key, value in summary.items():
            ws2.append([key, value])
        period = report.get("period") or {}
        ws2.append(["from", period.get("from")])
        ws2.append(["to", period.get("to")])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{_filename(report, "xlsx")}"'
    )
    return response


def export_pdf(report: dict) -> HttpResponse:
    columns = report.get("columns") or []
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    title = (report.get("report") or "Report").replace("_", " ").title()
    period = report.get("period") or {}
    story = [
        Paragraph(title, styles["Title"]),
        Paragraph(
            f"Period: {period.get('from') or '—'} to {period.get('to') or '—'}",
            styles["Normal"],
        ),
        Spacer(1, 8),
    ]
    summary = report.get("summary") or {}
    if summary:
        bits = " | ".join(f"{k}: {v}" for k, v in summary.items())
        story.append(Paragraph(bits, styles["Normal"]))
        story.append(Spacer(1, 8))

    table_data = [columns]
    for row in (report.get("rows") or [])[:200]:
        table_data.append([str(row.get(col, ""))[:40] for col in columns])

    if len(table_data) == 1:
        table_data.append(["—"] * len(columns) if columns else ["No data"])

    col_width = max(40, int(700 / max(len(columns), 1)))
    table = Table(table_data, colWidths=[col_width] * len(columns) if columns else None)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ]
        )
    )
    story.append(table)
    doc.build(story)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{_filename(report, "pdf")}"'
    )
    return response


EXPORTERS = {
    "csv": export_csv,
    "xlsx": export_xlsx,
    "excel": export_xlsx,
    "pdf": export_pdf,
}
