# Architecture

## Purpose

A production-style **Business Management System** for SMBs: customers, suppliers, catalog, inventory, purchases, sales, quotations, invoices, payments, expenses, employees, dashboard, reports, notifications, and audit — with JWT auth and role-based access.

## System diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                         │
│  React + Vite + TanStack Query + React Router + Tailwind        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS / JWT (Bearer)
┌────────────────────────────▼────────────────────────────────────┐
│                    Django + DRF  (/api/v1/)                       │
│  JWT · Permissions · Throttling · Filters · Pagination · OpenAPI │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼─────┐ ┌─────▼─────────────┐
│ Domain Apps │ │  Services  │ │   Celery  │ │  Media / Static   │
│             │ │ (business  │ │  + Redis  │ │  logos, PDFs,     │
│             │ │  logic)    │ │           │ │  attachments      │
└──────┬──────┘ └─────┬──────┘ └─────┬─────┘ └───────────────────┘
       └──────────────┴──────────────┘
                      │
               ┌──────▼──────┐
               │    MySQL    │
               └─────────────┘
```

## Design principles

1. **Thin views, fat services** — HTTP in views/serializers; money and stock rules in `services.py`.
2. **Atomic operations** — Purchases, sales, payments, and stock use `transaction.atomic()`.
3. **Stock ledger** — Never change `Product.current_stock` without a `StockTransaction`.
4. **Soft cancel** — Prefer status `Cancelled` over hard-deleting financial documents.
5. **Decimal money** — No floats for currency fields.
6. **RBAC everywhere** — Backend permissions are source of truth; frontend routes mirror them.
7. **Config via environment** — Secrets and DB credentials via env files (never Git).
8. **Signals sparingly** — Prefer explicit service calls for audit/notifications when clarity matters.

## Defaults chosen for this project

| Decision | Choice | Reason |
|----------|--------|--------|
| Repo layout | Monorepo (`backend/` + `frontend/`) | One clone, one portfolio repo |
| MySQL driver | PyMySQL | Easier on Windows than mysqlclient |
| PDF | ReportLab | Reliable install; good enough for invoices |
| Celery early | Eager mode | Redis deferred until notifications/jobs phase |
| Auth | SimpleJWT | Access + refresh tokens |
| API docs | drf-spectacular | OpenAPI 3 + Swagger UI |

## Backend layout (target)

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── config/
│   ├── settings/          # base, development, production
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
└── apps/
    ├── common/            # shared exceptions, pagination, mixins
    ├── accounts/
    ├── companies/
    ├── customers/
    ├── suppliers/
    ├── products/
    ├── inventory/
    ├── purchases/
    ├── sales/
    ├── quotations/
    ├── invoices/
    ├── payments/
    ├── expenses/
    ├── employees/
    ├── reports/
    ├── notifications/
    └── audit/
```

## Frontend layout (target)

```
frontend/src/
├── api/
├── routes/
├── layouts/
├── components/
├── features/              # auth, customers, sales, …
├── hooks/
├── services/
├── store/
├── utils/
├── validations/
└── types/
```

## Request flow example (complete sale)

1. Client: `POST /api/v1/sales/{id}/complete/` with JWT.
2. Permission class checks role.
3. `SalesService.complete_sale()` runs inside `atomic()`.
4. Validate stock → write `StockTransaction`s → update product stock → update dues → audit + notify.
5. Return consistent JSON envelope.

## Security baseline

- JWT + hashed passwords
- Role and object-level permissions where needed
- CORS configured for the SPA origin
- Throttling on auth endpoints
- Validated uploads (images/documents)
- ORM only (no raw SQL for user input)
- No secrets in repository

## Related docs

- [Database & ER](database.md)
- [API modules](api-modules.md)
- [Phases](phases.md)
- [MVP vs advanced](mvp-vs-advanced.md)
