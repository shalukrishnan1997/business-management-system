# Dashboard & Reports (Phase 16)

Read-only analytics over live business data. No new tables — aggregates from existing modules.

## Dashboard

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/dashboard/` | KPI cards (counts + money) |
| GET | `/api/v1/dashboard/charts/?days=30` | Sales vs purchases series, expenses by category, invoice status |
| GET | `/api/v1/dashboard/recent/?limit=15` | Mixed recent activity feed |

### KPI money fields

- `sales_today` / `sales_month` — non-cancelled sales
- `purchases_month` — non-cancelled purchases
- `receivables` — open invoice balances
- `expenses_month` — recorded expenses this calendar month

## Reports

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/reports/` | List available report types + export formats |
| GET | `/api/v1/reports/{type}/?date_from=&date_to=` | JSON report (`summary` + `rows`) |
| GET | `/api/v1/reports/{type}/export/?export_format=csv\|xlsx\|pdf` | File download |

### Report types

`sales`, `purchases`, `invoices`, `payments`, `expenses`, `inventory`

`inventory` ignores date filters (current stock snapshot).

Default date range when omitted: last 30 days through today.

## Permissions

- Dashboard: `CanAccessDashboard` (read for most roles)
- Reports: `CanAccessReports` (read broadly; write reserved for admin/accountant for future scheduled exports)

## Design notes

- Service layer builds dict payloads so the React UI (Phase 20/22) can bind charts without reshaping.
- Exports reuse the same builders — CSV/Excel/PDF stay consistent with on-screen data.
- PDF export caps at 200 rows for readability; use Excel for full dumps.
