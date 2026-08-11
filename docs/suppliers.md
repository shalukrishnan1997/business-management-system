# Suppliers module (Phase 7)

## Model

`Supplier` with auto `SUP-0001` codes, Decimal opening balance (payable), soft status, `created_by` + timestamps.

Opening balance convention: **positive = we owe the supplier**.

## Endpoints

Base: `/api/v1/suppliers/`

| Method | Path | Access |
|--------|------|--------|
| GET | `/suppliers/` | suppliers read |
| POST | `/suppliers/` | suppliers write |
| GET | `/suppliers/{id}/` | read |
| PUT/PATCH | `/suppliers/{id}/` | write |
| DELETE | `/suppliers/{id}/` | write (soft deactivate) |
| POST | `/suppliers/{id}/activate/` | write |
| GET | `/suppliers/{id}/outstanding/` | read |
| GET | `/suppliers/{id}/statement/?date_from=&date_to=` | read |
| GET | `/suppliers/{id}/purchase-history/` | read (stub until Purchases) |
| GET | `/suppliers/{id}/payment-history/` | read |

## Query params

- `search` — code, name, company, email, phone, tax, city
- `status`, `city`, `country`
- `created_from`, `created_to`
- `has_opening_balance`
- `ordering` — name, supplier_code, created_at, opening_balance

## Permissions

Uses `CanManageSuppliers`:

- **Write:** Super Admin, Admin, Manager, Inventory Staff
- **Read:** those roles plus Accountant, Sales Staff, Viewer
