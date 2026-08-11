# MVP vs Advanced Features

## MVP (core product)

Must ship for a portfolio-ready commercial demo:

- Custom user, JWT, 7 roles, RBAC
- Company settings
- Customers & suppliers
- Products, categories, inventory ledger + low stock
- Purchases (receive updates stock)
- Sales (complete updates stock)
- Quotations + convert to sale
- Invoices + payments (partial/full)
- Expenses + light employees
- Dashboard + core reports + exports
- Notifications + audit log
- Seed data, README, OpenAPI, backend tests
- React admin UI for all core modules

## Advanced (after core)

| Feature | Notes |
|---------|--------|
| Multi-company / multi-branch | Tenancy redesign |
| Multi-warehouse | Extra stock dimension |
| Product variants | Catalog complexity |
| Full sales/purchase returns | Beyond cancel/reverse |
| Stripe / Razorpay | Gateways + webhooks |
| SMS / WhatsApp | Third-party providers |
| WebSocket notifications | Django Channels |
| Barcode scanning / QR | Hardware + UX |
| Recurring invoices | Celery Beat |
| Full payroll | Separate domain |
| Redis caching | Optimize dashboard |
| Docker + CI/CD + cloud | After app stability |

## Role matrix (MVP)

| Module | Super Admin | Admin | Manager | Accountant | Sales | Inventory | Viewer |
|--------|:-----------:|:-----:|:-------:|:----------:|:-----:|:---------:|:------:|
| Users | RW | RW* | — | — | — | — | — |
| Company | RW | RW | R | R | — | — | R |
| Customers | RW | RW | RW | R | RW | R | R |
| Suppliers | RW | RW | RW | R | R | RW | R |
| Products | RW | RW | RW | R | R | RW | R |
| Inventory adjust | RW | RW | R | — | — | RW | R |
| Purchases | RW | RW | RW | R | — | RW | R |
| Sales / quotes | RW | RW | RW | R | RW | R | R |
| Invoices / payments | RW | RW | R | RW | RW** | — | R |
| Expenses | RW | RW | R | RW | — | — | R |
| Employees | RW | RW | R | — | — | — | R |
| Reports / dashboard | RW | RW | R | RW | R | R | R |
| Audit | R | R | — | — | — | — | — |

\*Admin cannot elevate to Super Admin without explicit rules we will encode.  
\*\*Sales staff: customer receipts tied to sales/invoices.
