# Frontend setup (Phase 18)

Vite + React + TypeScript admin shell with Tailwind.

## Commands

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # production bundle
```

Run Django alongside (`backend` → `runserver`) so the Vite proxy can reach `/api/v1/`.

## What shipped

- App shell: sidebar + topbar + `<Outlet />`
- Placeholder routes for every major module
- Axios client with JWT header + refresh retry stub
- Zustand auth store (hydrates from `localStorage`)
- TanStack Query provider
- Design tokens: teal brand on cool canvas (DM Sans)

## Intentionally deferred

| Phase | Work |
|-------|------|
| 21 | CRUD module screens |
| 22 | Reports filters + export UI |
