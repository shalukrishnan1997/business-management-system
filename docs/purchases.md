# Purchases (Phase 10)

## Workflow

`draft` → `ordered` (optional) → `received` **or** `cancelled`

- **Receive** → stock ↑ via `StockTransactionType.PURCHASE`
- **Cancel after receive** → stock ↓ via `PURCHASE_RETURN`
- Edit allowed only for `draft` / `ordered`

## Endpoints

Base: `/api/v1/purchases/`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/purchases/` | List / create draft |
| GET/PATCH | `/purchases/{id}/` | Detail / update draft|ordered |
| DELETE or POST | `/purchases/{id}/` or `.../cancel/` | Cancel |
| POST | `/purchases/{id}/mark-ordered/` | Draft → ordered |
| POST | `/purchases/{id}/receive/` | Receive + stock in |
| GET | `/purchases/{id}/print/` | Printable PO payload |

## Totals

- Line total = `qty * unit_price - discount + tax`
- `subtotal` = sum(`qty * unit_price`)
- `grand_total` = sum(line totals) − header discount + header tax + shipping
- `due_amount` = grand_total − paid_amount

## Supplier impact

- Outstanding payable includes non-cancelled purchase `due_amount`
- `/api/v1/suppliers/{id}/purchase-history/` returns real purchases

## Permissions

`CanManagePurchases` — Inventory Staff can write.
