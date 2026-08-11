# API Module List

Base path: `/api/v1/`

OpenAPI UI (after backend setup): `/api/docs/`

| Module | Prefix | Capabilities |
|--------|--------|----------------|
| Auth | `/auth/` | register, login, logout, refresh, me, change/forgot/reset password |
| Users | `/users/` | admin user management (role-gated) |
| Company | `/company/` | get/update settings, logo |
| Customers | `/customers/` | CRUD, search/filter, statement, histories, outstanding |
| Suppliers | `/suppliers/` | CRUD, statement, purchase/payment history, outstanding |
| Categories | `/categories/` | CRUD |
| Products | `/products/` | CRUD, low-stock, SKU/barcode lookup |
| Inventory | `/inventory/` | transactions, adjustments, product history |
| Purchases | `/purchases/` | drafts, receive, cancel, print payload |
| Sales | `/sales/` | drafts, confirm/complete, cancel |
| Quotations | `/quotations/` | CRUD, status transitions, convert-to-sale, PDF |
| Invoices | `/invoices/` | CRUD, PDF, email, overdue handling |
| Payments | `/payments/` | receipts/payments, apply to invoice, history |
| Expenses | `/expenses/` | categories + expenses |
| Employees | `/employees/` | departments, designations, employees |
| Dashboard | `/dashboard/` | KPI cards, chart series, recent activity |
| Reports | `/reports/` | filtered reports + CSV/Excel/PDF export |
| Notifications | `/notifications/` | list, unread count, mark read |
| Audit | `/audit/` | filtered audit trail (admin) |

## Response envelope (standard)

Success:

```json
{
  "success": true,
  "message": "OK",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Insufficient stock",
  "errors": {
    "quantity": ["Only 5 units available"]
  }
}
```

## Cross-cutting

- JWT authentication (access + refresh)
- django-filter, search, ordering, pagination
- Role permission classes
- Throttling on sensitive auth routes
