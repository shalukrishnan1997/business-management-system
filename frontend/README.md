# Frontend

React + Vite SPA for the Business Management System admin dashboard.

## Status

**Phase 20 complete** — Live dashboard KPIs + charts.

Next: **Phase 21 — CRUD pages** (module UIs).

## Stack

| Lib | Role |
|-----|------|
| React 19 + Vite 8 | App runtime / bundler |
| TypeScript | Types |
| Tailwind CSS v4 | Styling |
| React Router | Routes + shell layout |
| TanStack Query | Server state (wired in App) |
| Axios | API client + JWT refresh stub |
| Zustand | Auth session store |
| React Hook Form + Zod | Installed for Phase 19+ forms |

## Run

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API calls to `/api/*` proxy to Django on `:8000`.

## Structure

```
src/
├── api/           # Axios client
├── components/    # Shared UI (grows in later phases)
├── features/      # Domain feature modules (later)
├── hooks/
├── layouts/       # AppShell, Sidebar, Topbar
├── pages/         # Route screens
├── routes/        # Router + nav config
├── store/         # Zustand (auth)
├── types/
├── utils/
└── validations/   # Zod schemas (Phase 19+)
```
