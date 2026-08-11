# Sales (Phase 11)

## Workflow

`draft` → `confirmed` (optional) → `completed` **or** `cancelled`

- **Complete** → stock ↓ via `StockTransactionType.SALE` (validates available stock + active product)
- **Cancel after complete** → stock ↑ via `SALE_RETURN`
- Edit allowed only for `draft` / `confirmed`

## Endpoints

Base: `/api/v1/sales/`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/sales/` | List / create draft |
| GET/PATCH | `/sales/{id}/` | Detail / update draft|confirmed |
| DELETE or POST | `.../cancel/` | Cancel |
| POST | `/sales/{id}/confirm/` | Draft → confirmed |
| POST | `/sales/{id}/complete/` | Complete + stock out |
| GET | `/sales/{id}/print/` | Printable sale payload |

## Totals

- Line total = `qty * unit_price - discount + tax`
- `subtotal` = sum(`qty * unit_price`)
- `grand_total` = sum(line totals) − header discount + header tax + shipping
- `due_amount` = grand_total − paid_amount

## Customer impact

- Outstanding receivable includes non-cancelled sale `due_amount`
- `/api/v1/customers/{id}/sales-history/` returns real sales

## Permissions

`CanManageSales` — Sales Staff can write.
