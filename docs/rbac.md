# Role-based access control (MVP)

## Roles

1. Super Admin
2. Admin
3. Manager
4. Accountant
5. Sales Staff
6. Inventory Staff
7. Viewer

## Implementation (Phase 5)

### Source of truth

- Role stored on `accounts.User.role`
- Matrix: `apps/common/rbac.py` → `MODULE_PERMISSIONS`
- Permission classes: `apps/common/permissions.py`

### Permission classes

| Class | Purpose |
|-------|---------|
| `IsAuthenticatedAndActive` | JWT user must be active + status=active |
| `IsSuperAdmin` | Super Admin only |
| `IsAdminOrAbove` | Admin or Super Admin |
| `HasRole` | `view.allowed_roles = [...]` |
| `IsReadOnly` | SAFE methods only |
| `HasModuleAccess` | Uses `view.module` + matrix |
| `CanManageCustomers` etc. | Module shortcuts |

### Endpoints added

| Method | Path | Who |
|--------|------|-----|
| GET | `/api/v1/rbac/me/` | Any authenticated user — effective permissions |
| GET/POST | `/api/v1/rbac/demo/customers/` | Demo of customers read/write matrix |
| CRUD | `/api/v1/users/` | Admin / Super Admin user management |

### User management rules

- Only Super Admin can assign `super_admin`
- Admins cannot list/edit Super Admin accounts
- DELETE soft-deactivates (`status=inactive`)
- Users cannot deactivate themselves

### Frontend note (Phase 19)

Call `GET /api/v1/rbac/me/` after login and gate routes/menus with `permissions[module].read|write`.

See also [mvp-vs-advanced.md](mvp-vs-advanced.md).
