# Business Management System

Production-style business management application for small and medium businesses.

Manage customers, suppliers, products, inventory, purchases, sales, quotations, invoices, payments, expenses, employees, analytics, and role-based access — built as a commercial-quality full-stack system.

---

## Overview

| Layer | Stack |
|-------|--------|
| Backend | Python 3, Django, Django REST Framework, JWT, MySQL, Celery + Redis |
| Frontend | React, Vite, React Router, TanStack Query, React Hook Form, Zod, Tailwind CSS |
| Docs | OpenAPI (drf-spectacular), README, architecture docs |
| Quality | Service-layer business rules, RBAC, tests, seed data |

> **Status:** Phase 20 — Dashboard UI ready. Next: Phase 21 (CRUD pages).

---

## Features (planned)

- JWT authentication with custom user model and 7 roles
- Company / business settings for invoices and reports
- Customers, suppliers, products, categories
- Inventory ledger (no silent stock changes)
- Purchases, sales, quotations, invoices, payments
- Expenses and light employee management
- Dashboard analytics and filtered reports (CSV / Excel / PDF)
- Notifications and audit logging
- Professional admin dashboard UI

---

## Architecture

See detailed design documents:

- [Architecture](docs/architecture.md)
- [Database & ER](docs/database.md)
- [API modules](docs/api-modules.md)
- [Development phases](docs/phases.md)
- [MVP vs advanced](docs/mvp-vs-advanced.md)

```
Browser (React)
    │  JWT Bearer
    ▼
Django REST API  (/api/v1/)
    │
    ├── Domain apps + service layer
    ├── Celery workers (async jobs)
    └── MySQL
```

---

## Repository structure

```
business-management-system/
├── backend/          # Django + DRF API
├── frontend/         # React + Vite SPA
├── docs/             # Architecture & planning
├── .gitignore
└── README.md
```

---

## Requirements

- Python 3.11+ (3.12 recommended; verify package support on newer versions)
- Node.js 20+ LTS
- MySQL 8.x
- Redis (optional until background jobs; Celery can run eager in early phases)
- Git

---

## Quick start

### Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
.\scripts\start-mysql.ps1
python manage.py migrate
python manage.py runserver
```

### MySQL setup

See [docs/mysql-setup.md](docs/mysql-setup.md).

```env
USE_MYSQL=True
DB_NAME=bms_db
DB_USER=bms_user
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

App: `http://localhost:5173` (proxies `/api` → Django `:8000`)

### API documentation

- Swagger UI: `http://127.0.0.1:8000/api/docs/`

---

## Environment variables

Documented fully in Phase 2 / 3. Core MySQL variables:

```
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
```

Never commit `.env` files.

---

## Demo users

Seed command and default credentials will be added with sample data (later phase).

---

## Tests

```bash
# Backend (after test suite exists)
cd backend
pytest
```

---

## Development approach

This project is built **phase by phase**. Do not skip ahead without confirming each phase works.

Current phase: **Phase 20 complete — ready for Phase 21 (CRUD pages)**

---

## License

Private / portfolio project — adjust as needed for your use.

---

## Portfolio

Screenshots and a short project description will be added in Phase 25.
