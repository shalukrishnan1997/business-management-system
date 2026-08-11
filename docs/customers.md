# Customers module (Phase 6)

## Model

`Customer` with auto `CUS-0001` codes, Decimal money fields, soft status, `created_by` + timestamps.

## Endpoints

Base: `/api/v1/customers/`

| Method | Path | Access |
|--------|------|--------|
| GET | `/customers/` | customers read |
| POST | `/customers/` | customers write |
| GET | `/customers/{id}/` | read |
| PUT/PATCH | `/customers/{id}/` | write |
| DELETE | `/customers/{id}/` | write (soft deactivate) |
| POST | `/customers/{id}/activate/` | write |
| GET | `/customers/{id}/outstanding/` | read |
| GET | `/customers/{id}/statement/?date_from=&date_to=` | read |
| GET | `/customers/{id}/sales-history/` | read |
| GET | `/customers/{id}/invoice-history/` | read |
| GET | `/customers/{id}/payment-history/` | read |

## Query params

- `search` — code, name, company, email, phone, tax, city
- `status`, `city`, `state`, `country`
- `created_from`, `created_to`
- `credit_limit_min`, `credit_limit_max`
- `has_opening_balance`
- `ordering` — name, customer_code, created_at, …

## Permissions

Uses `CanManageCustomers` (see RBAC matrix).
