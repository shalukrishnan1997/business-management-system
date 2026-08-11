# Expenses (Phase 14)

## Models

- **ExpenseCategory** — name, description, active/inactive
- **Expense** — `EXP-####`, category, title, amount, date, payment method, vendor, soft cancel

## Workflow

`recorded` → `cancelled`

- Edit while recorded
- Cancel is soft (keeps audit trail); cancelled rows are excluded from summaries
- Categories with expenses cannot be hard-deleted — deactivate instead
- New expenses require an **active** category

## Endpoints

### Categories — `/api/v1/expense-categories/`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/expense-categories/` | List / create |
| GET/PATCH | `/expense-categories/{id}/` | Detail / update |
| DELETE | `/expense-categories/{id}/` | Soft deactivate (empty only) |
| POST | `.../activate/` | Reactivate |

### Expenses — `/api/v1/expenses/`

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/expenses/` | List / record |
| GET/PATCH | `/expenses/{id}/` | Detail / update |
| POST | `.../cancel/` | Soft cancel |
| GET | `/expenses/summary/?date_from=&date_to=&category=` | Totals by category |

## Filters

- `category`, `status`, `payment_method`
- `date_from`, `date_to`, `amount_min`, `amount_max`
- `search` — number, title, vendor, reference, category name

## Permissions

`CanManageExpenses` — Admin/Accountant write; Manager/Viewer read (see RBAC matrix).
