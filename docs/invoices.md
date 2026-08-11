# Invoices (Phase 13)

## Workflow

`draft` → `sent` → `partially_paid` / `paid` / `overdue` → `cancelled`

- Edit only while **draft**
- **Send** stamps `sent_at`
- Payments update `paid_amount`, `balance`, and status
- Past due with remaining balance → **overdue** (via `mark-overdue` or refresh)
- Cancel blocked if any amount has been paid

## Endpoints

Base: `/api/v1/invoices/`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/invoices/` | List / create |
| GET/PATCH | `/invoices/{id}/` | Detail / update draft |
| POST | `/invoices/from-sale/` | Create from sale (`sale_id`, optional `due_days`) |
| POST | `.../send/` | Mark sent |
| POST | `.../cancel/` | Cancel unpaid invoice |
| POST | `/invoices/mark-overdue/` | Bulk overdue refresh |
| GET | `.../print/` | JSON print payload |
| GET | `.../pdf/` | Download PDF |
| POST | `.../email/` | Email PDF (`to_email` optional) |

Numbers: `INV-####`

## Totals

- Line total = `qty * unit_price - discount + tax`
- Header `total` = sum(line totals) − header discount + header tax
- `balance` = `total - paid_amount` (never negative)

## Outstanding (customers)

`opening + uninvoiced sale dues + invoice balances − unallocated receipts`

Once a sale has an active invoice, that sale’s due is excluded so we do not double-count.

## Permissions

`CanManageInvoices` — accountants write; sales staff can create/send customer invoices per RBAC.
