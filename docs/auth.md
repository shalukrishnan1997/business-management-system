# Auth API (Phase 4)

Base: `/api/v1/auth/`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/register/` | No | Create user (default role: Viewer) + tokens |
| POST | `/login/` | No | Email + password → JWT + user |
| POST | `/logout/` | Yes | Blacklist refresh token |
| POST | `/token/refresh/` | No | New access (and rotated refresh) |
| GET | `/me/` | Yes | Current profile |
| PATCH | `/me/` | Yes | Update name, phone, profile image |
| POST | `/change-password/` | Yes | Change password |
| POST | `/forgot-password/` | No | Email reset link (DEBUG also returns uid/token) |
| POST | `/reset-password/` | No | Set new password with uid + token |

## Login body

```json
{ "email": "admin@bms.local", "password": "Admin@12345" }
```

## Demo admin

```powershell
python manage.py create_demo_admin
```

Default: `admin@bms.local` / `Admin@12345`
