# Reports UI (Phase 22)

Filtered report viewer and file exports wired to Phase 16 APIs.

## Endpoints

| UI action | API |
|-----------|-----|
| Catalog (types + formats) | `GET /api/v1/reports/` |
| On-screen report | `GET /api/v1/reports/{type}/?date_from=&date_to=` |
| Download | `GET /api/v1/reports/{type}/export/?export_format=csv\|xlsx\|pdf` |

## Report types

`sales`, `purchases`, `invoices`, `payments`, `expenses`, `inventory`

`inventory` is a stock snapshot — date filters are hidden and not sent.

## Features

- Report type switcher
- Date range filter with Apply (default last 30 days)
- Summary cards from `summary`
- Dynamic table from `columns` + `rows`
- CSV / Excel / PDF download via blob response + `Content-Disposition` filename
- Money and status formatting aligned with the rest of the app

## Frontend files

- `frontend/src/pages/ReportsPage.tsx`
- `frontend/src/api/reports.ts`
- `frontend/src/types/reports.ts`

## Run

Sign in, open `/reports`, pick a type, apply dates, then export.
