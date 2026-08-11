# Auth UI (Phase 19)

## What shipped

- Login form (React Hook Form + Zod) → `POST /api/v1/auth/login/`
- Session bootstrap via `GET /api/v1/auth/me/`
- JWT access/refresh in `localStorage`
- Axios refresh on 401 → `POST /api/v1/auth/token/refresh/`
- Protected app routes + guest-only `/login`
- Sign out (blacklist refresh + clear session)

## Try it

```powershell
# Terminal 1 — API
cd backend
.\venv\Scripts\python.exe manage.py create_demo_admin
.\venv\Scripts\python.exe manage.py runserver

# Terminal 2 — UI
cd frontend
npm run dev
```

Open http://localhost:5173 → redirected to `/login`.

Demo: `admin@bms.local` / `Admin@12345`

## Route rules

| Path | Access |
|------|--------|
| `/login` | Guests only |
| `/` and modules | Authenticated only |

Unauthenticated visits to app routes bounce to `/login` and return to the original path after success.
