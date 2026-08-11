# Development Phases

Build order. **Do not skip confirmation** between major phases.

| Phase | Name | Deliverable |
|-------|------|-------------|
| 1 | Architecture & planning | Docs + repo scaffold (current) |
| 2 | Backend environment | Django project, deps, settings split, runserver |
| 3 | MySQL setup | Env-based DB config, migrations on MySQL |
| 4 | Custom user + JWT | Register/login/refresh/profile |
| 5 | Permissions & roles | Reusable RBAC classes |
| 6 | Customers | Full CRUD API + tests |
| 7 | Suppliers | Full CRUD API |
| 8 | Products | Categories + products |
| 9 | Inventory | StockTransaction service |
| 10 | Purchases | Receive → stock increase |
| 11 | Sales | Complete → stock decrease |
| 12 | Quotations | Convert to sale |
| 13 | Invoices & payments | Balances, partial payments |
| 14 | Expenses | Categories + expenses |
| 15 | Employees | Departments, designations, employees |
| 16 | Dashboard & reports | Analytics + exports |
| 17 | Notifications & audit | In-app alerts, Celery jobs |
| 18 | React setup | Vite app, layout shell, Tailwind |
| 19 | Auth UI | Login, protected routes |
| 20 | Dashboard UI | Cards + charts |
| 21 | CRUD pages | All core module UIs |
| 22 | Reports UI | Filters + export |
| 23 | Testing | Harden unit/API/integration tests |
| 24 | Deployment | Notes + optional Docker |
| 25 | Portfolio | Screenshots + description |

## Phase checklist (every phase)

1. Explain what we build and why
2. Show structure
3. Give exact commands
4. Provide complete code
5. Explain the code
6. How to test + expected output
7. Wait for confirmation
