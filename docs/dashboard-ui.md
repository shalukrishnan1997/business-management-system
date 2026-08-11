# Dashboard UI (Phase 20)

Live admin overview wired to Phase 16 APIs.

## Endpoints used

| UI block | API |
|----------|-----|
| KPI money + counts | `GET /api/v1/dashboard/` |
| Charts | `GET /api/v1/dashboard/charts/?days=` |
| Recent activity | `GET /api/v1/dashboard/recent/?limit=` |

## Features

- Money KPI cards (sales, purchases, receivables, expenses)
- Count strip (customers, low stock, overdue, …)
- Sales vs purchases line chart (7 / 14 / 30 / 90 day range)
- Expenses by category bar chart
- Invoices by status donut + legend
- Recent activity feed with module links
- Loading and error states via TanStack Query

## Run

Sign in (Phase 19), then open `/`. Ensure Django is running so the Vite proxy can reach the API.
