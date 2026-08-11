# Notifications & Audit (Phase 17)

In-app alerts, append-only audit trail, and Celery jobs (eager by default).

## Notifications

Model: user, title, message, type, link, `is_read`, module, object_id

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/notifications/` | Own notifications |
| GET | `/api/v1/notifications/unread-count/` | Badge count |
| POST | `/api/v1/notifications/mark-read/` | Body `{ "ids": [1,2] }` or omit for all |
| POST | `/api/v1/notifications/mark-all-read/` | Mark all read |
| GET/DELETE | `/api/v1/notifications/{id}/` | Detail / delete own |
| POST | `/api/v1/notifications/jobs/low-stock/` | Admin: run low-stock Celery job |
| POST | `/api/v1/notifications/jobs/overdue-invoices/` | Admin: overdue + notify |

## Audit

Append-only `AuditLog` — written by middleware on mutating `/api/v1/` calls (after JWT is resolved).

| Method | Path | Access |
|--------|------|--------|
| GET | `/api/v1/audit-logs/` | Admin / Super Admin |
| GET | `/api/v1/audit-logs/{id}/` | Admin / Super Admin |

Filters: `user`, `action`, `module`, `method`, `status_code`, `date_from`, `date_to`, `search`

## Celery

Default: `CELERY_TASK_ALWAYS_EAGER=True` (tasks run inline — no Redis required).

To use a real worker:

1. Start Redis
2. Set `CELERY_TASK_ALWAYS_EAGER=False` in `.env`
3. Run:
   ```powershell
   cd backend
   .\venv\Scripts\celery.exe -A config worker -l info
   .\venv\Scripts\celery.exe -A config beat -l info
   ```

Beat schedule (when Beat is running):

- 01:00 — mark overdue invoices + notify finance roles
- 08:00 — low-stock check + notify inventory/admin roles

## Design choices

- **No Django signals** for domain events — call `create_notification` / Celery tasks explicitly (or use the job endpoints / Beat).
- **Middleware audit** covers all write APIs without editing every service.
- JWT is authenticated early (`JWTAuthenticationMiddleware`) so audit rows include `user`.
