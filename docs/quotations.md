# Quotations (Phase 12)

## Workflow

`draft` → `sent` → `accepted` / `rejected` / `expired`

- Edit only while **draft**
- **Accept** then **convert-to-sale** creates a draft `SalesOrder` and links it
- Past `valid_until` auto-marks **expired** on retrieve/workflow actions

## Endpoints

Base: `/api/v1/quotations/`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/quotations/` | List / create |
| GET/PATCH | `/quotations/{id}/` | Detail / update draft |
| POST | `.../send/` | Mark sent |
| POST | `.../accept/` | Accept |
| POST | `.../reject/` | Reject |
| POST | `.../convert-to-sale/` | Create linked sale |
| GET | `.../print/` | JSON print payload |
| GET | `.../pdf/` | Download PDF |
| POST | `.../email/` | Email PDF (`to_email` optional) |

## Totals

- Line total = `qty * unit_price - discount + tax`
- `grand_total` = sum(line totals) − header discount + header tax

## Permissions

`CanManageQuotations` — same write roles as sales.
