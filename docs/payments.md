# Payments (Phase 13)

## Types

| `payment_type` | Party | Typical reference |
|----------------|-------|-------------------|
| `customer_receipt` | Customer | `invoice` or `manual` |
| `supplier_payment` | Supplier | `purchase` or `manual` |

Numbers: `PAY-####`

Methods: `cash`, `bank_transfer`, `card`, `upi`, `cheque`, `other`

## Endpoints

Base: `/api/v1/payments/`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/payments/` | List / record payment |
| GET | `/payments/{id}/` | Detail |
| GET | `.../receipt/` | Printable receipt payload |

Payments are append-only (no update/delete in MVP).

## Applying amounts

- `reference_type=invoice` + `reference_id` → reduces invoice balance (and linked sale paid/due)
- `reference_type=purchase` + `reference_id` → reduces purchase due
- `manual` / no document → recorded only; counted as unallocated against party outstanding

Cannot overpay an invoice or purchase balance.

## Histories

- Customer: `GET /customers/{id}/payment-history/`
- Supplier: `GET /suppliers/{id}/payment-history/`

## Permissions

`CanManagePayments` — accountants write; sales staff for customer receipts per RBAC.
